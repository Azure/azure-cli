# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import uuid
import unittest

from datetime import datetime, timedelta
from time import sleep
from dateutil import parser
from dateutil.tz import tzutc
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk.preparers import AbstractPreparer, SingleValueReplacer, StorageAccountPreparer
from azure.core.exceptions import HttpResponseError
from ..._client_factory import cf_mysql_flexible_private_dns_zone_suffix_operations
from ..._network import prepare_private_dns_zone
from ...custom import DbContext as MysqlDbContext, _determine_iops
from ..._util import get_mysql_list_skus_info, retryable_method
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckNotExists,
    NoneCheck,
    ResourceGroupPreparer,
    KeyVaultPreparer,
    ScenarioTest,
    StringContainCheck,
    live_only,
    record_only)

from azure.mgmt.sql.models import AdvancedThreatProtectionState


# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20
DEFAULT_LOCATION = "northeurope"
DEFAULT_PAIRED_LOCATION = "westeurope"
DEFAULT_GENERAL_PURPOSE_SKU = "Standard_D2ds_v4"
DEFAULT_MEMORY_OPTIMIZED_SKU = "Standard_E4ads_v5"
RESOURCE_RANDOM_NAME = "clirecording"
STORAGE_ACCOUNT_PREFIX = "storageaccount"
STORAGE_ACCOUNT_NAME_MAX_LENGTH = 20

class ServerPreparer(AbstractPreparer, SingleValueReplacer):

    def __init__(self, engine_type, location, engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server',
                 resource_group_parameter_name='resource_group'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.engine_type = engine_type
        self.engine_parameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} flexible-server create -l {} -g {} -n {} --public-access none'
        execute(self.cli_ctx, template.format(self.engine_type,
                                              self.location,
                                              group, name))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    def remove_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        execute(self.cli_ctx, 'az {} flexible-server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)


class FlexibleServerMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_iops_mgmt(self, resource_group):
        self._test_flexible_server_iops_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_paid_iops_mgmt(self, resource_group):
        self._test_flexible_server_paid_iops_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('mysql', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @unittest.skip("Currently blocked due to creation of 'Azure Database for MySQL - Single Server' no longer supported on March 19 2024.")
    def test_mysql_flexible_server_import_create(self, resource_group):
        self._test_mysql_flexible_server_import_create_mgmt('mysql', resource_group)

    # To run this test live, make sure that your role excludes the permission 'Microsoft.DBforMySQL/locations/checkNameAvailability/action'
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_check_name_availability_fallback_mgmt(self, resource_group):
        self._test_flexible_server_check_name_availability_fallback_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_restore_mgmt(self, resource_group):
        self._test_flexible_server_restore_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_georestore_mgmt(self, resource_group):
        self._test_flexible_server_georestore_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_georestore_update_mgmt(self, resource_group):
        self._test_flexible_server_georestore_update_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_gtid_reset(self, resource_group):
        self._test_flexible_server_gtid_reset('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='vault_name', location=DEFAULT_PAIRED_LOCATION, additional_params='--enable-purge-protection true --retention-days 90 --enable-rbac-authorization false')
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='backup_vault_name', location=DEFAULT_LOCATION, additional_params='--enable-purge-protection true --retention-days 90 --enable-rbac-authorization false')
    def test_mysql_flexible_server_byok_mgmt(self, resource_group, vault_name, backup_vault_name):
        self._test_flexible_server_byok_mgmt('mysql', resource_group, vault_name, backup_vault_name)


    def _test_flexible_server_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        storage_size = 32
        version = '5.7'
        location = DEFAULT_LOCATION
        sku_name = DEFAULT_GENERAL_PURPOSE_SKU
        memory_optimized_sku = DEFAULT_MEMORY_OPTIMIZED_SKU
        tier = 'GeneralPurpose'
        backup_retention = 7
        database_name = 'testdb'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --database-name {} --public-access None'
                 .format(database_engine, resource_group, server_name, backup_retention, sku_name, tier, storage_size, 'dbadmin', version, database_name))

        basic_info = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size)
        self.assertEqual(basic_info['storage']['logOnDisk'], "Disabled")
        self.assertEqual(basic_info['backup']['backupRetentionDays'], backup_retention)

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'
                    .format(database_engine, resource_group, server_name, database_name), checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server update -g {} -n {} -p randompw321##@!'
                 .format(database_engine, resource_group, server_name))

        self.cmd('{} flexible-server update -g {} -n {} --storage-size 256'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 256 )])

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'
                 .format(database_engine, resource_group, server_name, backup_retention + 10),
                 checks=[JMESPathCheck('backup.backupRetentionDays', backup_retention + 10)])

        tier = 'MemoryOptimized'
        sku_name = memory_optimized_sku
        accelerated_logs = "Enabled"
        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {} --accelerated-logs {}'
                 .format(database_engine, resource_group, server_name, tier, sku_name, accelerated_logs),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name),
                         JMESPathCheck('storage.logOnDisk', accelerated_logs)])

        self.cmd('{} flexible-server update -g {} -n {} --tags keys=3'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('tags.keys', '3')])

        self.cmd('{} flexible-server restart -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server stop -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server start -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server list -g {}'.format(database_engine, resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])

        restore_server_name = 'restore-' + server_name
        self.cmd('{} flexible-server restore -g {} --name {} --source-server {}'
                 .format(database_engine, resource_group, restore_server_name, server_name),
                 checks=[JMESPathCheck('name', restore_server_name)])

        connection_string = self.cmd('{} flexible-server show-connection-string -s {}'
                                     .format(database_engine, server_name)).get_output_in_json()

        self.assertIn('jdbc', connection_string['connectionStrings'])
        self.assertIn('node.js', connection_string['connectionStrings'])
        self.assertIn('php', connection_string['connectionStrings'])
        self.assertIn('python', connection_string['connectionStrings'])
        self.assertIn('ado.net', connection_string['connectionStrings'])

        self.cmd('{} flexible-server list-skus -l {}'.format(database_engine, location),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, restore_server_name), checks=NoneCheck())

    def _test_mysql_flexible_server_import_create_mgmt(self, database_engine, resource_group):
        # single server which will be used for import
        ss_server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        location = 'westus2'
        ss_storage_size = 51200
        ss_version = '5.7'
        source_sku_name = 'GP_Gen5_4'
        source_public_network_access = 'Disabled'
        source_backup_retention_days = 10 
        source_geo_redundant_backup = 'Enabled'
        source_admin_login = 'mysqluser'
        source_auto_grow = 'Enabled'

        self.cmd('{} server create -g {} -n {} -l {} --storage-size {} --version {} --sku-name {} \
                  --public-network-access {} --backup-retention {} --geo-redundant-backup {} --auto-grow {} -u {}'
                 .format(database_engine, resource_group, ss_server_name, location,
                         ss_storage_size, ss_version, source_sku_name, source_public_network_access,
                         source_backup_retention_days, source_geo_redundant_backup, source_auto_grow, source_admin_login))

        # flexible server details
        storage_size_gb = 50
        version = '5.7'
        sku_name = 'Standard_D4ds_v4'
        tier = 'GeneralPurpose'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        data_source_type = 'mysql_single'
        data_source = ss_server_name
        mode = 'Offline'
        target_public_network_access = 'Disabled'
        target_backup_retention_days = 10 
        target_geo_redundant_backup = 'Enabled'
        target_admin_login = 'mysqluser'
        target_auto_grow = 'Enabled'

        self.cmd('{} flexible-server import create -g {} -n {} --data-source-type {} --data-source {} --mode {}'
                 .format(database_engine, resource_group, server_name, data_source_type, data_source, mode))

        basic_info = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size_gb)
        self.assertEqual(basic_info['network']['publicNetworkAccess'], target_public_network_access)
        self.assertEqual(basic_info['storage']['autoGrow'], target_auto_grow)
        self.assertEqual(basic_info['backup']['backupRetentionDays'], target_backup_retention_days)
        self.assertEqual(basic_info['backup']['geoRedundantBackup'], target_geo_redundant_backup)
        self.assertEqual(basic_info['administratorLogin'], target_admin_login)

        # deletion of flexible server created
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())

        # size for flex server is less than single server
        invalid_storage_size_gb = 20
        self.cmd('{} flexible-server import create -g {} -n {} --storage-size {} \
                 --data-source-type {} --data-source {} --mode {}'.format(database_engine, resource_group, server_name, invalid_storage_size_gb,
                                                                          data_source_type, data_source, mode),
                                                                          expect_failure=True)

        # version for flex server given is different from single server version
        invalid_version = '8.0.21'
        self.cmd('{} flexible-server import create -g {} -n {} --version {} \
                 --data-source-type {} --data-source {} --mode {}'.format(database_engine, resource_group, server_name,
                                                                          invalid_version, data_source_type, data_source, mode),
                                                                          expect_failure=True)

        # resource group passed does not exist
        invalid_resource_group = self.create_random_name('rg', 10)
        self.cmd('{} flexible-server import create -g {} -n {} --data-source-type {} \
                  --data-source {} --mode {}'.format(database_engine, invalid_resource_group, server_name, data_source_type,
                                                     data_source, mode),
                                                     expect_failure=True)

        # single server name passed does not exist in the resource group passed
        invalid_data_source_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        self.cmd('{} flexible-server import create -g {} -n {} --data-source-type {} --data-source {} --mode {}'.format(database_engine,
                                                                                                                        resource_group, server_name,
                                                                                                                        data_source_type, invalid_data_source_name, mode),
                                                                                                                        expect_failure=True)

        # single server resource id passed is invalid or does not exist
        invalid_data_source_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforMySQL/servers/{}'.format(
            self.get_subscription_id(), invalid_resource_group, invalid_data_source_name
        )
        self.cmd('{} flexible-server import create -g {} -n {} --data-source-type {} --data-source {} --mode {}'.format(database_engine,
                                                                                                                        resource_group, server_name, data_source_type,
                                                                                                                        invalid_data_source_resource_id, mode),
                                                                                                                        expect_failure=True)

        # deletion of single server created
        self.cmd('{} server delete -g {} -n {} --yes'.format(database_engine, resource_group, ss_server_name), checks=NoneCheck())

    def _test_flexible_server_check_name_availability_fallback_mgmt(self, database_engine, resource_group):
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} --public-access None --tier GeneralPurpose --sku-name {}'
                 .format(database_engine, resource_group, server_name, DEFAULT_GENERAL_PURPOSE_SKU))
        
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))
    
    def _test_flexible_server_iops_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = DEFAULT_LOCATION
        list_skus_info = get_mysql_list_skus_info(self, location)
        iops_info = list_skus_info['iops_info']

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        server_name_3 = self.create_random_name(SERVER_NAME_PREFIX + '3', SERVER_NAME_MAX_LENGTH)

        # IOPS passed is within limit of max allowed by SKU but smaller than storage*3
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 200 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name, location))

        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                          checks=[JMESPathCheck('storage.iops', 400)]).get_output_in_json()

        # SKU upgraded and IOPS value set smaller than free iops, max iops for the sku

        iops = 400
        iops_result = _determine_iops(storage_gb=result["storage"]["storageSizeGb"],
                                      iops_info=iops_info,
                                      iops_input=iops,
                                      tier="Burstable",
                                      sku_name="Standard_B1ms")
        self.assertEqual(iops_result, 640)

        # SKU downgraded and IOPS not specified
        iops = result["storage"]["iops"]
        iops_result = _determine_iops(storage_gb=result["storage"]["storageSizeGb"],
                                      iops_info=iops_info,
                                      iops_input=iops,
                                      tier="Burstable",
                                      sku_name="Standard_B1s")
        self.assertEqual(iops_result, 400)

        # IOPS passed is within limit of max allowed by SKU but smaller than default
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 30 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name_2, location))

        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name_2),
                          checks=[JMESPathCheck('storage.iops', 390)]).get_output_in_json()

        iops = 700
        iops_result = _determine_iops(storage_gb=result["storage"]["storageSizeGb"],
                                      iops_info=iops_info,
                                      iops_input=iops,
                                      tier="Burstable",
                                      sku_name="Standard_B1ms")
        self.assertEqual(iops_result, 640)

        # IOPS passed is within limit of max allowed by SKU and bigger than default
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 40 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name_3, location))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name_3),
                 checks=[JMESPathCheck('storage.iops', 400)])

        iops = 500
        iops_result = _determine_iops(storage_gb=300,
                                      iops_info=iops_info,
                                      iops_input=iops,
                                      tier="Burstable",
                                      sku_name="Standard_B1ms")
        self.assertEqual(iops_result, 640)

    def _test_flexible_server_paid_iops_mgmt(self, database_engine, resource_group):
        
        location = DEFAULT_LOCATION
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 64 --sku-name {} --tier GeneralPurpose'
                 .format(database_engine, resource_group, server_name, location, DEFAULT_GENERAL_PURPOSE_SKU))
        
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                          checks=[JMESPathCheck('storage.autoIoScaling', 'Disabled')]).get_output_in_json()

        self.cmd('{} flexible-server update -g {} -n {} --auto-scale-iops Enabled'
                 .format(database_engine, resource_group, server_name))
        
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                          checks=[JMESPathCheck('storage.autoIoScaling', 'Enabled')]).get_output_in_json()
        
        self.cmd('{} flexible-server update -g {} -n {} --auto-scale-iops Disabled'
                 .format(database_engine, resource_group, server_name))
        
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                          checks=[JMESPathCheck('storage.autoIoScaling', 'Disabled')]).get_output_in_json()

        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --auto-scale-iops Enabled --storage-size 64 --sku-name {} --tier GeneralPurpose'
                 .format(database_engine, resource_group, server_name_2, location, DEFAULT_GENERAL_PURPOSE_SKU))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name_2),
                          checks=[JMESPathCheck('storage.autoIoScaling', 'Enabled')]).get_output_in_json()

    def _test_flexible_server_restore_mgmt(self, database_engine, resource_group):

        private_dns_param = 'privateDnsZoneResourceId'
        location = DEFAULT_LOCATION

        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_config = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        source_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        source_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        new_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        new_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        new_vnet_2 = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        new_subnet_2 = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} --vnet {} --subnet {} -l {} --yes'.format(
                 database_engine, resource_group, source_server, source_vnet, source_subnet, location))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, source_server)).get_output_in_json()

        # Wait until snapshot is created
        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = result['backup']['earliestRestoreDate']
        seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
        os.environ.get(ENV_LIVE_TEST, False) and sleep(max(0, seconds_to_wait) + 180)

        # default vnet resources
        restore_result = self.cmd('{} flexible-server restore -g {} --name {} --source-server {} '
                                  .format(database_engine, resource_group, target_server_default, source_server)).get_output_in_json()

        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, source_vnet, source_subnet))
        self.assertEqual(restore_result['network'][private_dns_param],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, '{}.private.{}.database.azure.com'.format(source_server, database_engine)))

        # MYSQL only - vnet to public access
        restore_result = self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --public-access Enabled'
                                .format(database_engine, resource_group, target_server_public_access, source_server)).get_output_in_json()

        # to different vnet and private dns zone
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'.format(
                          resource_group, new_subnet, new_vnet)).get_output_in_json()

        private_dns_zone = '{}.private.{}.database.azure.com'.format(target_server_diff_vnet, database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(resource_group, private_dns_zone))

        restore_result = self.cmd('{} flexible-server restore -g {} -n {} --source-server {} --subnet {} --private-dns-zone {}'.format(
                                  database_engine, resource_group, target_server_diff_vnet, source_server, subnet["id"], private_dns_zone)).get_output_in_json()

        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, new_vnet, new_subnet))

        self.assertEqual(restore_result['network'][private_dns_param],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone))

        # public access to vnet
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
        resource_group, location, new_vnet_2))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'.format(
                        resource_group, new_subnet_2, new_vnet_2)).get_output_in_json()

        private_dns_zone = '{}.private.{}.database.azure.com'.format(target_server_diff_vnet_2, database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(resource_group, private_dns_zone))

        restore_result = self.cmd('{} flexible-server restore -g {} -n {} --source-server {} --subnet {} --private-dns-zone {}'.format(
                                database_engine, resource_group, target_server_diff_vnet_2, target_server_public_access, subnet["id"], private_dns_zone)).get_output_in_json()

        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                            self.get_subscription_id(), resource_group, new_vnet_2, new_subnet_2))

        self.assertEqual(restore_result['network'][private_dns_param],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group, private_dns_zone))
            
        # take params tier, storage-size, sku-name, storage-auto-grow, backup-retention and geo-redundant-backup
        restore_result = self.cmd('{} flexible-server restore -g {} -n {} --source-server {} --storage-size 64 --tier GeneralPurpose --storage-auto-grow Enabled --sku-name {} --backup-retention 9  --geo-redundant-backup Enabled'.format(
                                database_engine, resource_group, target_server_config, source_server, DEFAULT_GENERAL_PURPOSE_SKU)).get_output_in_json()
        
        self.assertEqual(restore_result['backup']['backupRetentionDays'], 9)
        self.assertEqual(restore_result['backup']['geoRedundantBackup'], "Enabled")
        self.assertEqual(restore_result['sku']['name'], DEFAULT_GENERAL_PURPOSE_SKU)
        self.assertEqual(restore_result['sku']['tier'], "GeneralPurpose")
        self.assertEqual(restore_result['storage']['storageSizeGb'], 64)
        self.assertEqual(restore_result['storage']['autoGrow'], "Enabled")
        self.assertEqual(restore_result['storage']['logOnDisk'], "Disabled")

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, source_server), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_default), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_diff_vnet), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_diff_vnet_2), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_public_access), checks=NoneCheck())
        
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_config), checks=NoneCheck())

    def _test_flexible_server_georestore_mgmt(self, database_engine, resource_group):

        private_dns_param = 'privateDnsZoneResourceId'
        location = DEFAULT_LOCATION
        target_location = DEFAULT_PAIRED_LOCATION

        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        source_server_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_config = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        source_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        source_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        new_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        new_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        new_vnet_2 = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        new_subnet_2 = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} --vnet {} --subnet {} -l {} --geo-redundant-backup Enabled --yes'.format(
                 database_engine, resource_group, source_server, source_vnet, source_subnet, location))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, source_server)).get_output_in_json()
        self.assertEqual(result['backup']['geoRedundantBackup'], 'Enabled')

        self.cmd('{} flexible-server create -g {} -n {} --public-access None -l {} --geo-redundant-backup Enabled'.format(
                 database_engine, resource_group, source_server_2, location))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, source_server_2)).get_output_in_json()
        self.assertEqual(result['backup']['geoRedundantBackup'], 'Enabled')
        self.assertEqual(result['network']['publicNetworkAccess'], 'Enabled')

        # 1. vnet -> vnet without network parameters fail
        self.cmd('{} flexible-server geo-restore -g {} -l {} --name {} --source-server {} '
                 .format(database_engine, resource_group, target_location, target_server_default, source_server), expect_failure=True)

        # 2. vnet to public access
        restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} --name {} --source-server {} --public-access enabled'
                                .format(database_engine, resource_group, target_location, target_server_public_access, source_server)).get_output_in_json()

        #self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')
        self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), target_location)

        # 3. vnet to different vnet
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, target_location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'.format(
                          resource_group, new_subnet, new_vnet)).get_output_in_json()

        restore_result = retryable_method(retries=10, interval_sec=360 if os.environ.get(ENV_LIVE_TEST, False) else 0, exception_type=HttpResponseError,
                                          condition=lambda ex: 'GeoBackupsNotAvailable' in ex.message)(self.cmd)(
                                              '{} flexible-server geo-restore -g {} -l {} -n {} --source-server {} --subnet {} --yes'.format(
                                              database_engine, resource_group, target_location, target_server_diff_vnet, source_server, subnet["id"])
                                          ).get_output_in_json()

        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, new_vnet, new_subnet))

        self.assertEqual(restore_result['network'][private_dns_param],  # private dns zone needs to be created
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, '{}.private.{}.database.azure.com'.format(target_server_diff_vnet, database_engine)))

        # 4. public access to vnet
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
        resource_group, target_location, new_vnet_2))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'.format(
                        resource_group, new_subnet_2, new_vnet_2)).get_output_in_json()

        private_dns_zone = '{}.private.{}.database.azure.com'.format(target_server_diff_vnet_2, database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(resource_group, private_dns_zone))

        restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} -n {} --source-server {} --subnet {} --private-dns-zone {} --public-access disabled --yes'.format(
                                database_engine, resource_group, target_location, target_server_diff_vnet_2, source_server_2, subnet["id"], private_dns_zone)).get_output_in_json()

        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                            self.get_subscription_id(), resource_group, new_vnet_2, new_subnet_2))

        self.assertEqual(restore_result['network'][private_dns_param],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group, private_dns_zone))

        # 5. public to public
        restore_result = retryable_method(retries=10, interval_sec=360 if os.environ.get(ENV_LIVE_TEST, False) else 0, exception_type=HttpResponseError,
                                          condition=lambda ex: 'GeoBackupsNotAvailable' in ex.message)(self.cmd)(
                                              '{} flexible-server geo-restore -g {} -l {} --name {} --source-server {}'.format(
                                              database_engine, resource_group, target_location, target_server_public_access_2, source_server_2)
                                         ).get_output_in_json()

        #self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')
        self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), target_location)

        # 6. take params tier, storage-size, sku-name, storage-auto-grow, backup-retention and geo-redundant-backup
        restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} -n {} --source-server {} --public-access enabled --storage-size 64 --tier GeneralPurpose --storage-auto-grow Enabled --sku-name {} --backup-retention 9  --geo-redundant-backup Enabled'.format(
                                database_engine, resource_group, target_location, target_server_config, source_server, DEFAULT_GENERAL_PURPOSE_SKU)).get_output_in_json()
        
        self.assertEqual(restore_result['backup']['backupRetentionDays'], 9)
        self.assertEqual(restore_result['backup']['geoRedundantBackup'], "Enabled")
        self.assertEqual(restore_result['sku']['name'], DEFAULT_GENERAL_PURPOSE_SKU)
        self.assertEqual(restore_result['sku']['tier'], "GeneralPurpose")
        self.assertEqual(restore_result['storage']['storageSizeGb'], 64)
        self.assertEqual(restore_result['storage']['autoGrow'], "Enabled")
        self.assertEqual(restore_result['storage']['logOnDisk'], "Disabled")

        # Delete servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, source_server), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_diff_vnet), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_diff_vnet_2), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_public_access), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_config), checks=NoneCheck())

    def _test_flexible_server_georestore_update_mgmt(self, database_engine, resource_group):
        location = 'eastus'
        target_location = 'westus'

        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --public-access none --tier {} --sku-name {}'
                 .format(database_engine, resource_group, source_server, location, 'GeneralPurpose', DEFAULT_GENERAL_PURPOSE_SKU))

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, source_server),
                 checks=[JMESPathCheck('backup.geoRedundantBackup', 'Disabled')])

        result = self.cmd('{} flexible-server update -g {} -n {} --geo-redundant-backup Enabled'
                          .format(database_engine, resource_group, source_server),
                          checks=[JMESPathCheck('backup.geoRedundantBackup', 'Enabled')]).get_output_in_json()

        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = result['backup']['earliestRestoreDate']
        seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
        os.environ.get(ENV_LIVE_TEST, False) and sleep(max(0, seconds_to_wait) + 180)

        self.cmd('{} flexible-server geo-restore -g {} -l {} -n {} --source-server {}'
                 .format(database_engine, resource_group, target_location, target_server, source_server),
                 checks=[JMESPathCheck('backup.geoRedundantBackup', 'Enabled')])

        self.cmd('{} flexible-server update -g {} -n {} --geo-redundant-backup Disabled'
                 .format(database_engine, resource_group, source_server),
                 checks=[JMESPathCheck('backup.geoRedundantBackup', 'Disabled')])

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, source_server))
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, target_server))


    def _test_flexible_server_byok_mgmt(self, database_engine, resource_group, vault_name, backup_vault_name=None):
        key_name = self.create_random_name('rdbmskey', 32)
        identity_name = self.create_random_name('identity', 32)
        backup_key_name = self.create_random_name('rdbmskey', 32)
        backup_identity_name = self.create_random_name('identity', 32)
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica_1_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica_2_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        backup_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        tier = 'GeneralPurpose'
        sku_name = DEFAULT_GENERAL_PURPOSE_SKU
        location = DEFAULT_LOCATION
        backup_location = DEFAULT_PAIRED_LOCATION
        replication_role = 'Replica'

        user = self.cmd('ad signed-in-user show').get_output_in_json()

        self.cmd('keyvault set-policy --name {} --object-id {} --key-permissions all'.format(vault_name, user['id']))

        key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                       .format(key_name, vault_name)).get_output_in_json()

        identity = self.cmd('identity create -g {} --name {} --location {}'
                            .format(resource_group, identity_name, location)).get_output_in_json()

        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                 .format(resource_group, vault_name, identity['principalId']))

        backup_key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                              .format(backup_key_name, backup_vault_name)).get_output_in_json()

        backup_identity = self.cmd('identity create -g {} --name {} --location {}'
                                   .format(resource_group, backup_identity_name, backup_location)).get_output_in_json()

        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                 .format(resource_group, backup_vault_name, backup_identity['principalId']))

        def invalid_input_tests():
            # key or identity only
            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {}'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                key['key']['kid']
            ), expect_failure=True)

            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --identity {}'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                identity['id'],
            ), expect_failure=True)

            # backup key or backup identity only
            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} --backup-key {} --geo-redundant-backup Enabled'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                key['key']['kid'],
                identity['id'],
                backup_key['key']['kid']
            ), expect_failure=True)

            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} --backup-identity {} --geo-redundant-backup Enabled'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                key['key']['kid'],
                identity['id'],
                backup_identity['id'],
            ), expect_failure=True)

            # backup key without principal key
            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --backup-key {} --backup-identity {}'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                backup_key['key']['kid'],
                backup_identity['id']
            ), expect_failure=True)

            # geo-redundant server without backup-key
            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} --geo-redundant-backup Enabled'.format(
                database_engine,
                resource_group,
                server_name,
                tier,
                sku_name,
                key['key']['kid'],
                identity['id'],
            ), expect_failure=True)

        def main_tests(geo_redundant_backup):
            geo_redundant_backup_enabled = 'Enabled' if geo_redundant_backup else 'Disabled'
            backup_key_id_flags = '--backup-key {} --backup-identity {}'.format(backup_key['key']['kid'], backup_identity['id']) if geo_redundant_backup else ''
            restore_type = 'geo-restore --location {}'.format(backup_location) if geo_redundant_backup else 'restore'

            # create primary flexible server with data encryption
            self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} {} --location {} --geo-redundant-backup {}'.format(
                        database_engine,
                        resource_group,
                        server_name,
                        tier,
                        sku_name,
                        key['key']['kid'],
                        identity['id'],
                        backup_key_id_flags,
                        location,
                        geo_redundant_backup_enabled
                    ))

            # should fail because we can't remove identity used for data encryption
            self.cmd('{} flexible-server identity remove -g {} -s {} -n {} --yes'
                     .format(database_engine, resource_group, server_name, identity['id']),
                     expect_failure=True)

            if geo_redundant_backup:
                self.cmd('{} flexible-server identity remove -g {} -s {} -n {} --yes'
                         .format(database_engine, resource_group, server_name, backup_identity['id']),
                         expect_failure=True)

            main_checks = [
                JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
                JMESPathCheck('dataEncryption.primaryKeyUri', key['key']['kid']),
                JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', identity['id'])
            ]

            if geo_redundant_backup:
                main_checks += [
                    JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(backup_identity['id'])),
                    JMESPathCheck('dataEncryption.geoBackupKeyUri', backup_key['key']['kid']),
                    JMESPathCheck('dataEncryption.geoBackupUserAssignedIdentityId', backup_identity['id'])
                ]

            result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                    checks=main_checks).get_output_in_json()

            # should fail because disable-data-encryption and key for data encryption are provided at the same time
            self.cmd('{} flexible-server update -g {} -n {} --key {} --identity {} --disable-data-encryption'.format(
                database_engine,
                resource_group,
                server_name,
                key['key']['kid'],
                identity['id']
            ), expect_failure=True)

            # disable data encryption in primary server
            self.cmd('{} flexible-server update -g {} -n {} --disable-data-encryption'.format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('dataEncryption', None)])

            # create replica 1, it shouldn't have data encryption
            self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'.format(
                        database_engine,
                        resource_group,
                        replica_1_name,
                        server_name
            ), checks=[
                JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
                JMESPathCheck('dataEncryption', None),
                JMESPathCheck('replicationRole', replication_role)
            ] + ([JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(backup_identity['id']))] if geo_redundant_backup else []))

            # enable data encryption again in primary server
            self.cmd('{} flexible-server update -g {} -n {} --key {} --identity {} {}'.format(
                        database_engine,
                        resource_group,
                        server_name,
                        key['key']['kid'],
                        identity['id'],
                        backup_key_id_flags
            ), checks=main_checks)

            # replica 1 now should have data encryption as well
            self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, replica_1_name),
                        checks=main_checks)

            # create replica 2
            self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'.format(
                        database_engine,
                        resource_group,
                        replica_2_name,
                        server_name
            ), checks=main_checks + [JMESPathCheck('replicationRole', replication_role)])

            # should fail because modifying data encryption on replica server is not allowed
            self.cmd('{} flexible-server update -g {} -n {} --disable-data-encryption'
                    .format(database_engine, resource_group, replica_2_name),
                expect_failure=True)

            # restore backup
            current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
            earliest_restore_time = result['backup']['earliestRestoreDate']
            seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
            sleep(max(0, seconds_to_wait))

            restore_result = self.cmd('{} flexible-server {} -g {} --name {} --source-server {}'.format(
                     database_engine,
                     restore_type,
                     resource_group,
                     backup_name,
                     server_name
            ), checks=main_checks).get_output_in_json()

            if geo_redundant_backup:
                self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), backup_location)

            # disable data encryption in primary server
            self.cmd('{} flexible-server update -g {} -n {} --disable-data-encryption'.format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('dataEncryption', None)])

            # none of the replica servers should have data encryption now
            self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, replica_1_name),
                checks=[JMESPathCheck('dataEncryption', None)])

            self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, replica_2_name),
                checks=[JMESPathCheck('dataEncryption', None)])

            # delete all servers
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, replica_1_name))
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, replica_2_name))
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, backup_name))
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))

        invalid_input_tests()
        main_tests(False)


    def _test_flexible_server_gtid_reset(self, database_engine, resource_group):
        location = DEFAULT_LOCATION
        general_purpose_sku = DEFAULT_GENERAL_PURPOSE_SKU

        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --public-access none --tier {} --sku-name {}'
                 .format(database_engine, resource_group, source_server, location, 'GeneralPurpose', general_purpose_sku))
        
        # update server paramters to enable gtid
        source = 'user-override'
        parameter_name = 'enforce_gtid_consistency'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'
                 .format(database_engine, parameter_name, 'ON', source, source_server, resource_group),
                 checks=[JMESPathCheck('value', 'ON'), JMESPathCheck('source', source), JMESPathCheck('name', parameter_name)])

        parameter_name = 'gtid_mode'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'
                 .format(database_engine, parameter_name, 'OFF_PERMISSIVE', source, source_server, resource_group),
                 checks=[JMESPathCheck('value', 'OFF_PERMISSIVE'), JMESPathCheck('source', source), JMESPathCheck('name', parameter_name)])
        
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'
                 .format(database_engine, parameter_name, 'ON_PERMISSIVE', source, source_server, resource_group),
                 checks=[JMESPathCheck('value', 'ON_PERMISSIVE'), JMESPathCheck('source', source), JMESPathCheck('name', parameter_name)])
        
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'
                 .format(database_engine, parameter_name, 'ON', source, source_server, resource_group),
                 checks=[JMESPathCheck('value', 'ON'), JMESPathCheck('source', source), JMESPathCheck('name', parameter_name)])
        
        self.cmd('{} flexible-server gtid reset --resource-group {} --server-name {} --gtid-set {} --yes'
                 .format(database_engine, resource_group, source_server, str(uuid.uuid4()).upper() + ":1"), expect_failure=False)
        
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, source_server))


class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @ServerPreparer(engine_type='mysql', location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('mysql', resource_group, server)
        self._test_parameter_mgmt('mysql', resource_group, server)
        self._test_database_mgmt('mysql', resource_group, server)
        self._test_log_file_mgmt('mysql', resource_group, server)

    def _test_firewall_rule_mgmt(self, database_engine, resource_group, server):

        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]

        self.cmd('{} flexible-server firewall-rule create -g {} --name {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule show -g {} --name {} --rule-name {} '
                 .format(database_engine, resource_group, server, firewall_rule_name),
                 checks=firewall_rule_checks)

        new_start_ip_address = '9.9.9.9'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --start-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_start_ip_address),
                 checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])

        new_end_ip_address = '13.13.13.13'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --end-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_end_ip_address))

        new_firewall_rule_name = 'firewall_test_rule2'
        firewall_rule_checks = [JMESPathCheck('name', new_firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        self.cmd('{} flexible-server firewall-rule create -g {} -n {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, new_firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} flexible-server firewall-rule delete --rule-name {} -g {} --name {} --yes'
                 .format(database_engine, firewall_rule_name, resource_group, server), checks=NoneCheck())

        self.cmd('{} flexible-server firewall-rule list -g {} --name {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 1)])

        self.cmd('{} flexible-server firewall-rule delete -g {} -n {} --rule-name {} --yes'
                 .format(database_engine, resource_group, server, new_firewall_rule_name))

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_parameter_mgmt(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server parameter list -g {} -s {}'.format(database_engine, resource_group, server), checks=[JMESPathCheck('type(@)', 'array')])

        parameter_name = 'wait_timeout'
        default_value = '28800'
        value = '30000'

        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {} -g {} -s {}'.format(database_engine, parameter_name, resource_group, server),
                 checks=[JMESPathCheck('defaultValue', default_value),
                         JMESPathCheck('source', source)])

        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])
        
        args = "auto_increment_offset=2 explicit_defaults_for_timestamp=ON ft_query_expansion_limit=18"
        self.cmd('{} flexible-server parameter set-batch -s {} -g {} --args {}'.format(database_engine, server, resource_group, args),
                 checks=[JMESPathCheck('status', 'Succeeded')])
        
        self.cmd('{} flexible-server parameter show --name auto_increment_offset -g {} -s {}'.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('currentValue', 2)])
        
        self.cmd('{} flexible-server parameter show --name explicit_defaults_for_timestamp -g {} -s {}'.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('currentValue', 'ON')])
        
        self.cmd('{} flexible-server parameter show --name ft_query_expansion_limit -g {} -s {}'.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('currentValue', 18)])


    def _test_database_mgmt(self, database_engine, resource_group, server):

        database_name = self.create_random_name('database', 20)

        self.cmd('{} flexible-server db create -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
                 checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('{} flexible-server db list -g {} -s {} '.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('{} flexible-server db delete -g {} -s {} -d {} --yes'.format(database_engine, resource_group, server, database_name),
                 checks=NoneCheck())

    def _test_log_file_mgmt(self, database_engine, resource_group, server):
        # enable logs to be written to a file
        self.cmd('{} flexible-server parameter set -g {} -s {} -n log_output --value FILE'
                    .format(database_engine, resource_group, server))

        # enable slow query log
        config_name = 'slow_query_log'
        new_value = 'ON'

        self.cmd('{} flexible-server parameter set -g {} -s {} -n {} --value {}'
                    .format(database_engine, resource_group, server, config_name, new_value),
                    checks=[
                        JMESPathCheck('name', config_name),
                        JMESPathCheck('value', new_value)])

        # retrieve logs filenames
        result = self.cmd('{} flexible-server server-logs list -g {} -s {} --file-last-written 43800'
                            .format(database_engine, resource_group, server),
                            checks=[
                                JMESPathCheck('length(@)', 1),
                                JMESPathCheck('type(@)', 'array')]).get_output_in_json()

        name = result[0]['name']
        self.assertIsNotNone(name)

        # download log
        if name:
            self.cmd('{} flexible-server server-logs download -g {} -s {} -n {}'
                        .format(database_engine, resource_group, server, name))
            
            # assert that log file was downloaded successfully and delete it
            self.assertTrue(os.path.isfile(name))
            os.remove(name)


class FlexibleServerValidatorScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_mgmt_create_validator(self, resource_group):
        self._test_mgmt_create_validator('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_mgmt_update_validator(self, resource_group):
        self._test_mgmt_update_validator('mysql', resource_group)

    def _test_mgmt_create_validator(self, database_engine, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 30
        location = DEFAULT_LOCATION
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        ha_value = 'ZoneRedundant'

        # Create
        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {}'.format(
                 database_engine, resource_group, server_name, location, invalid_tier),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --version {}'.format(
                 database_engine, resource_group, server_name, location, invalid_version),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --sku-name {}'.format(
                 database_engine, resource_group, server_name, location, valid_tier, invalid_sku_name),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --backup-retention {}'.format(
                 database_engine, resource_group, server_name, location, invalid_backup_retention),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l centraluseuap --high-availability {} '.format(
                 database_engine, resource_group, server_name, ha_value),
                 expect_failure=True)

        # high availability validator
        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier Burstable --sku-name Standard_B1ms --high-availability {}'.format(
                 database_engine, resource_group, server_name, location, ha_value),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l centraluseuap --tier GeneralPurpose --sku-name Standard_D2s_v3 --high-availability {}'.format(
                 database_engine, resource_group, server_name, ha_value), # single availability zone location
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --high-availability {} --zone 1 --standby-zone 1'.format(
                 database_engine, resource_group, server_name, location, ha_value), # single availability zone location
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --high-availability {} --storage-auto-grow Disabled'.format(
                database_engine, resource_group, server_name, location, ha_value), # auto grow must be enabled for high availability server
                expect_failure=True)

        # Network
        self.cmd('{} flexible-server create -g {} -n {} -l {} --vnet testvnet --subnet testsubnet --public-access All'.format(
                 database_engine, resource_group, server_name, location),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --subnet testsubnet'.format(
                 database_engine, resource_group, server_name, location),
                 expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --public-access 12.0.0.0-10.0.0.0.0'.format(
                 database_engine, resource_group, server_name, location),
                 expect_failure=True)

        invalid_storage_size = 10
        self.cmd('{} flexible-server create -g {} -l {} --storage-size {} --public-access none'.format(
                 database_engine, resource_group, location, invalid_storage_size),
                 expect_failure=True)

    def _test_mgmt_update_validator(self, database_engine, resource_group):
        RANDOM_VARIABLE_MAX_LENGTH = 30
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        version = 5.7
        storage_size = 32
        location = DEFAULT_LOCATION
        tier = 'Burstable'
        sku_name = 'Standard_B1ms'
        backup_retention = 10

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storage.storageSizeGb', storage_size),
                       JMESPathCheck('backup.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --version {} --sku-name {} --storage-size {} --backup-retention {} --public-access none'
                 .format(database_engine, resource_group, server_name, location, tier, version, sku_name, storage_size, backup_retention))
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name), checks=list_checks)

        invalid_tier = 'GeneralPurpose'
        self.cmd('{} flexible-server update -g {} -n {} --tier {}'.format(
                 database_engine, resource_group, server_name, invalid_tier), # can't update to this tier because of the instance's sku name
                 expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'.format(
                 database_engine, resource_group, server_name, valid_tier, invalid_sku_name),
                 expect_failure=True)

        invalid_storage_size = 30
        self.cmd('{} flexible-server update -g {} -n {} --storage-size {}'.format(
                 database_engine, resource_group, server_name, invalid_storage_size), #cannot update to smaller size
                 expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'.format(
                 database_engine, resource_group, server_name, invalid_backup_retention),
                 expect_failure=True)

        ha_value = 'ZoneRedundant'
        self.cmd('{} flexible-server update -g {} -n {} --high-availability {}'.format(
                 database_engine, resource_group, server_name, ha_value),
                 expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, server_name), checks=NoneCheck())

class FlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('mysql', resource_group, False)

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_mysql_flexible_server_cross_region_replica_mgmt(self, resource_group):
        self._test_flexible_server_cross_region_replica_mgmt('mysql', resource_group)
    
    def _test_flexible_server_cross_region_replica_mgmt(self, database_engine, resource_group):
        # create a server
        master_location = DEFAULT_LOCATION
        replica_location = 'eastus'
        primary_role = 'None'
        replica_role = 'Replica'
        private_dns_param = 'privateDnsZoneResourceId'

        master_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --tier GeneralPurpose --sku-name {} --public-access none'
                 .format(database_engine, resource_group, master_server, master_location, 256, DEFAULT_GENERAL_PURPOSE_SKU))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', primary_role)]).get_output_in_json()

        # test replica create for public access
        replica_result = self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --location {}'
                 .format(database_engine, resource_group, replicas[0], result['id'], replica_location),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')]).get_output_in_json()
                     #JMESPathCheck('network.publicNetworkAccess', 'Enabled')]).get_output_in_json()
        self.assertEqual(str(replica_result['location']).replace(' ', '').lower(), replica_location)

        # test replica create for private access
        replica_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        replica_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        private_dns_zone = '{}.private.{}.database.azure.com'.format(replicas[1], database_engine)

        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'
                 .format(resource_group, replica_location, replica_vnet))
        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'
                          .format(resource_group, replica_subnet, replica_vnet)).get_output_in_json()
        self.cmd('network private-dns zone create -g {} --name {}'.format(resource_group, private_dns_zone))

        replica_result = self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --location {} --subnet {} --private-dns-zone {}'
                 .format(database_engine, resource_group, replicas[1], result['id'], replica_location, subnet["id"], private_dns_zone),
                 checks=[
                     JMESPathCheck('name', replicas[1]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replicaCapacity', '0'),
                     #JMESPathCheck('network.publicNetworkAccess', 'Disabled'),
                     JMESPathCheck('network.delegatedSubnetResourceId', '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'
                                   .format(self.get_subscription_id(), resource_group, replica_vnet, replica_subnet)),
                     JMESPathCheck('network.{}'.format(private_dns_param), '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'
                                   .format(self.get_subscription_id(), resource_group, private_dns_zone))]).get_output_in_json()
        self.assertEqual(str(replica_result['location']).replace(' ', '').lower(), replica_location)

        # test replica list
        self.cmd('{} flexible-server replica list -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 2)])

        # clean up servers
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                    .format(database_engine, resource_group, master_server), checks=NoneCheck())


    def _test_flexible_server_replica_mgmt(self, database_engine, resource_group, vnet_enabled):
        location = DEFAULT_LOCATION
        primary_role = 'None'
        replica_role = 'Replica'
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]

        if vnet_enabled:
            master_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
            master_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
            master_vnet_args = F'--vnet {master_vnet} --subnet {master_subnet} --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.0.0/24'
            master_vnet_check = [JMESPathCheck('network.delegatedSubnetResourceId', F'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{master_vnet}/subnets/{master_subnet}')]
            replica_subnet = [self.create_random_name(F'SUBNET{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]
            replica_vnet_args = [F'--vnet {master_vnet} --subnet {replica_subnet[i]} --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.{i+1}.0/24 --yes' for i in range(2)]
            replica_vnet_check = [[JMESPathCheck('network.delegatedSubnetResourceId', F'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{master_vnet}/subnets/{replica_subnet[i]}')] for i in range(2)]
        else:
            master_vnet_args = '--public-access none'
            master_vnet_check = []
            replica_vnet_args = [''] * 2
            replica_vnet_check = [[]] * 2

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} {} --tier GeneralPurpose --sku-name {} --yes'
                 .format(database_engine, resource_group, master_server, location, 256, master_vnet_args, DEFAULT_GENERAL_PURPOSE_SKU))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', primary_role)] + master_vnet_check).get_output_in_json()
        
        # test replica create
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --zone 2 --public-access Disabled {}'
                 .format(database_engine, resource_group, replicas[0], result['id'], replica_vnet_args[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replicaCapacity', '0'),
                     JMESPathCheck('network.publicNetworkAccess', 'Disabled')] + replica_vnet_check[0])

        # test replica list
        self.cmd('{} flexible-server replica list -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # autogrow disable fail for replica server
        self.cmd('{} flexible-server update -g {} -n {} --storage-auto-grow Disabled'.format(
                database_engine, resource_group, master_server),
                expect_failure=True)

        # test replica stop
        self.cmd('{} flexible-server replica stop-replication -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replicationRole', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[
                     JMESPathCheck('replicationRole', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test delete master server
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} {}'
                .format(database_engine, resource_group, replicas[1], result['id'], replica_vnet_args[1]),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('sku.name', result['sku']['name']),
                    JMESPathCheck('replicationRole', replica_role),
                    JMESPathCheck('sourceServerResourceId', result['id']),
                    JMESPathCheck('replicaCapacity', '0')] + replica_vnet_check[1])

        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                .format(database_engine, resource_group, master_server), checks=NoneCheck())

        self.cmd('{} flexible-server wait -g {} --name {} --custom "{}"'
                .format(database_engine, resource_group, replicas[1], F"replicationRole=='{primary_role}'"))

        # test show server with replication info, replica was auto stopped after master server deleted
        self.cmd('{} flexible-server show -g {} --name {}'.format(database_engine, resource_group, replicas[1]),
                checks=[
                    JMESPathCheck('replicationRole', primary_role),
                    JMESPathCheck('sourceServerResourceId', 'None'),
                    JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # clean up servers
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())


class FlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='resource_group_2')
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('mysql', resource_group_1, resource_group_2)
  
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_public_access_custom(self, resource_group):
        self._test_mysql_flexible_server_public_access_custom('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_public_access_restore(self, resource_group):
        self._test_mysql_flexible_server_public_access_restore('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_public_access_georestore(self, resource_group):
        self._test_mysql_flexible_server_public_access_georestore('mysql', resource_group)
    
    def _test_mysql_flexible_server_public_access_georestore(self, database_engine, resource_group):
        location = DEFAULT_LOCATION
        paired_location = DEFAULT_PAIRED_LOCATION
        server_name_soure_restore = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_target_restore = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        api_version = '2022-09-30-preview'

         #Test restore server
        result = self.cmd('{} flexible-server create --geo-redundant-backup Enabled --public-access Enabled -g {} -n {} -l {} --iops 50 --storage-size 100 --sku-name Standard_B1ms --tier Burstable'
                 .format(database_engine, resource_group, server_name_soure_restore, location)).get_output_in_json()
        
        restore_server = self.cmd('resource show --id {} --api-version {}'.format(result['id'], api_version)).get_output_in_json()
        
        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = restore_server['properties']['backup']['earliestRestoreDate']
        seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
        time.sleep(max(0, seconds_to_wait) + 180)

        target_server = self.cmd('{} flexible-server geo-restore -g {} -n {} --source-server {} --public-access Disabled --location {}'
                 .format(database_engine, resource_group, server_name_target_restore, server_name_soure_restore, paired_location)).get_output_in_json()

        self.cmd('resource show --id {} --api-version {}'.format(target_server['id'], api_version),
                          checks=[JMESPathCheck('properties.network.publicNetworkAccess', 'Disabled')])

    def _test_mysql_flexible_server_public_access_restore(self, database_engine, resource_group):
        location = DEFAULT_LOCATION
        server_name_soure_restore = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_target_restore = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        api_version = '2022-09-30-preview'

         #Test restore server
        result = self.cmd('{} flexible-server create --public-access Enabled -g {} -n {} -l {} --iops 50 --storage-size 100 --sku-name Standard_B1ms --tier Burstable'
                 .format(database_engine, resource_group, server_name_soure_restore, location)).get_output_in_json()
        
        restore_server = self.cmd('resource show --id {} --api-version {}'.format(result['id'], api_version)).get_output_in_json()
        
        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = restore_server['properties']['backup']['earliestRestoreDate']
        seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
        print(current_time)
        print(seconds_to_wait)
        time.sleep(max(0, seconds_to_wait) + 180)

        target_server = self.cmd('{} flexible-server restore -g {} -n {} --source-server {} --public-access Disabled'
                 .format(database_engine, resource_group, server_name_target_restore, server_name_soure_restore)).get_output_in_json()

        self.cmd('resource show --id {} --api-version {}'.format(target_server['id'], api_version),
                          checks=[JMESPathCheck('properties.network.publicNetworkAccess', 'Disabled')])

    def _test_mysql_flexible_server_public_access_custom(self, database_engine, resource_group):

        location = DEFAULT_PAIRED_LOCATION
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        api_version = '2022-09-30-preview'

        #Test create server with public access enabled
        result = self.cmd('{} flexible-server create --public-access Enabled -g {} -n {} -l {} --iops 50 --storage-size 100 --sku-name Standard_B1ms --tier Burstable'
                 .format(database_engine, resource_group, server_name, location)).get_output_in_json()

        self.cmd('resource show --id {} --api-version {}'.format(result['id'], api_version),
                          checks=[JMESPathCheck('properties.network.publicNetworkAccess', 'Enabled')])

        #Test create server with public access disabled
        result = self.cmd('{} flexible-server create --public-access Disabled -g {} -n {} -l {} --iops 50 --storage-size 100 --sku-name Standard_B1ms --tier Burstable'
                 .format(database_engine, resource_group, server_name_2, location)).get_output_in_json()

        self.cmd('resource show --id {} --api-version {}'.format(result['id'], api_version),
                          checks=[JMESPathCheck('properties.network.publicNetworkAccess', 'Disabled')])
        
        #Test update server
        self.cmd('{} flexible-server update -g {} -n {} --public-access Enabled'
                 .format(database_engine, resource_group, server_name_2))
        
        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name_2))

    def _test_flexible_server_vnet_mgmt_existing_supplied_subnetid(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')
        
        location = DEFAULT_LOCATION
        private_dns_zone_key = "privateDnsZoneResourceId"

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone0.private.{}.database.azure.com".format(database_engine)

        # Scenario : Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        vnet_name = 'testvnet'
        subnet_name = 'testsubnet'
        address_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group, location, vnet_name, address_prefix, subnet_name, subnet_prefix))
        subnet_id = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(resource_group, subnet_name, vnet_name)).get_output_in_json()['id']

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(database_engine, resource_group, server_name, subnet_id, location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'], subnet_id)
        
        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        vnet_name = 'clitestvnet3'
        subnet_name = 'clitestsubnet3'
        vnet_name_2 = 'clitestvnet4'
        address_prefix = '13.0.0.0/16'
        location = DEFAULT_LOCATION
        private_dns_zone_key = "privateDnsZoneResourceId"

        # flexible-servers
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) + database_engine, self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) + database_engine]
        private_dns_zone_1 = "testdnszone3.private.{}.database.azure.com".format(database_engine)
        private_dns_zone_2 = "testdnszone4.private.{}.database.azure.com".format(database_engine)
        # Case 1 : Provision a server with supplied Vname and subnet name that exists.

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format(vnet_name, resource_group, location, address_prefix))

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {} -l {} --subnet {} --private-dns-zone {} --yes'
                 .format(database_engine, resource_group, servers[0], vnet_name, location, subnet_name, private_dns_zone_1))

        # Case 2 : Provision a server with a supplied Vname and subnet name that does not exist.
        self.cmd('{} flexible-server create -g {} -n {} -l {} --vnet {} --private-dns-zone {} --yes'
                 .format(database_engine, resource_group, servers[1], location, vnet_name_2, private_dns_zone_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name, subnet_name))

        self.assertEqual(show_result_2['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1]))

        # Case 3 : Detach server vnet
        self.cmd('{} flexible-server detach-vnet -g {} -n {} --public-network-access Disabled --yes'
                 .format(database_engine, resource_group, servers[0], vnet_name, location, subnet_name, private_dns_zone_1))
        
        show_result_3 = self.cmd('{} flexible-server show -g {} -n {}'
                            .format(database_engine, resource_group, servers[0])).get_output_in_json()
        self.assertEqual(show_result_3['network']['delegatedSubnetResourceId'], None)


        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, database_engine, resource_group_1, resource_group_2):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = DEFAULT_LOCATION
        vnet_name = 'clitestvnet5'
        subnet_name = 'clitestsubnet5'
        address_prefix = '10.10.0.0/16'
        subnet_prefix = '10.10.0.0/24'

        # flexible-servers
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone5.private.{}.database.azure.com".format(database_engine)

        # Case 1 : Provision a server with supplied subnetid that exists in a different RG

        # create vnet and subnet.
        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group_1, location, address_prefix, subnet_name,
                    subnet_prefix)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(database_engine, resource_group_2, server_name, vnet_result['newVNet']['subnets'][0]['id'], location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group_2, server_name)).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_1, vnet_name, subnet_name))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, server_name),
                 checks=NoneCheck())

        # time.sleep(15 * 60)

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1, subnet_name, vnet_name))
        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_1, vnet_name))


class FlexibleServerPrivateDnsZoneScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='vnet_resource_group')
    def test_mysql_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        self._test_flexible_server_existing_private_dns_zone('mysql', server_resource_group, vnet_resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='vnet_resource_group')
    @ResourceGroupPreparer(location=DEFAULT_LOCATION, parameter_name='dns_resource_group')
    def test_mysql_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        self._test_flexible_server_new_private_dns_zone('mysql', server_resource_group, vnet_resource_group, dns_resource_group)

    def _test_flexible_server_existing_private_dns_zone(self, database_engine, server_resource_group, vnet_resource_group):
        server_names = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        
        location = DEFAULT_LOCATION
        delegation_service_name = "Microsoft.DBforMySQL/flexibleServers"
        private_dns_zone_key = "privateDnsZoneResourceId"
        server_group_vnet_name = 'servergrouptestvnet'
        server_group_subnet_name = 'servergrouptestsubnet'
        vnet_group_vnet_name = 'vnetgrouptestvnet'
        vnet_group_subnet_name = 'vnetgrouptestsubnet'
        vnet_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 server_resource_group, location, server_group_vnet_name, vnet_prefix, server_group_subnet_name, subnet_prefix))
        server_group_vnet = self.cmd('network vnet show -g {} -n {}'.format(
                                     server_resource_group, server_group_vnet_name)).get_output_in_json()
        server_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       server_resource_group, server_group_subnet_name, server_group_vnet_name)).get_output_in_json()
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 vnet_resource_group, location, vnet_group_vnet_name, vnet_prefix, vnet_group_subnet_name, subnet_prefix))
        vnet_group_vnet = self.cmd('network vnet show -g {} -n {}'.format(
                                   vnet_resource_group, vnet_group_vnet_name)).get_output_in_json()
        vnet_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       vnet_resource_group, vnet_group_subnet_name, vnet_group_vnet_name)).get_output_in_json()

        # FQDN validator
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --vnet {} --subnet {} --yes'.format(
                 database_engine, server_resource_group, server_names[0], location, server_names[0] + '.' + database_engine + '.database.azure.com', server_group_vnet_name, server_group_subnet_name),
                 expect_failure=True)

        # validate wrong suffix
        dns_zone_incorrect_suffix = 'clitestincorrectsuffix.database.{}.azure.com'.format(database_engine)
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
            database_engine, server_resource_group, server_names[0], location, dns_zone_incorrect_suffix, server_group_subnet["id"]),
            expect_failure=True)

        # existing private dns zone in server group, no link
        unlinked_dns_zone = 'clitestunlinked.{}.database.azure.com'.format(database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(
                 server_resource_group, unlinked_dns_zone))

        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
            database_engine, server_resource_group, server_names[0], location, unlinked_dns_zone, server_group_subnet["id"]))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, server_resource_group, server_names[0])).get_output_in_json()

        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_group_vnet_name, server_group_subnet_name))
        self.cmd('network vnet show --id {}'.format(server_group_vnet['id']),
                 checks=[StringContainCheck(vnet_prefix)])
        self.cmd('network vnet subnet show --id {}'.format(server_group_subnet['id']),
                 checks=[JMESPathCheck('addressPrefix', subnet_prefix),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # exisitng private dns zone in vnet group
        vnet_group_dns_zone = 'clitestvnetgroup.{}.database.azure.com'.format(database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(
                 vnet_resource_group, vnet_group_dns_zone))
        self.cmd('network private-dns link vnet create -g {} -n MyLinkName -z {} -v {} -e False'.format(
                 vnet_resource_group, vnet_group_dns_zone, vnet_group_vnet['id']
        ))
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 database_engine, server_resource_group, server_names[1], location, vnet_group_dns_zone, vnet_group_subnet["id"]))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, server_resource_group, server_names[1])).get_output_in_json()

        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, vnet_group_vnet_name, vnet_group_subnet_name))
        self.cmd('network vnet show --id {}'.format(vnet_group_vnet['id']),
                 checks=[StringContainCheck(vnet_prefix)])
        self.cmd('network vnet subnet show --id {}'.format(vnet_group_subnet['id']),
                 checks=[JMESPathCheck('addressPrefix', subnet_prefix),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_new_private_dns_zone(self, database_engine, server_resource_group, vnet_resource_group, dns_resource_group):
        server_names = ['clitest-private-dns-zone-test-3', 'clitest-private-dns-zone-test-4',
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        private_dns_zone_names = ["clitestdnszone1.private.{}.database.azure.com".format(database_engine),
                                  "clitestdnszone2.private.{}.database.azure.com".format(database_engine),
                                  "clitestdnszone3.private.{}.database.azure.com".format(database_engine)]
        
        location = DEFAULT_LOCATION
        db_context = MysqlDbContext(cmd=self, cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations, command_group='mysql')
        private_dns_zone_key = "privateDnsZoneResourceId"
        server_group_vnet_name = 'servergrouptestvnet'
        server_group_subnet_name = 'servergrouptestsubnet'
        vnet_group_vnet_name = 'vnetgrouptestvnet'
        vnet_group_subnet_name = 'vnetgrouptestsubnet'
        vnet_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'

        # vnet in server rg
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 server_resource_group, location, server_group_vnet_name, vnet_prefix, server_group_subnet_name, subnet_prefix))
        server_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       server_resource_group, server_group_subnet_name, server_group_vnet_name)).get_output_in_json()

        # vnet in vnet rg
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 vnet_resource_group, location, vnet_group_vnet_name, vnet_prefix, vnet_group_subnet_name, subnet_prefix))
        vnet_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       vnet_resource_group, vnet_group_subnet_name, vnet_group_vnet_name)).get_output_in_json()

        # no input, vnet in server rg
        dns_zone = prepare_private_dns_zone(db_context, database_engine, server_resource_group, server_names[0], None, server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_names[0] + ".private." + database_engine + ".database.azure.com"))

        # no input, vnet in vnet rg
        dns_zone = prepare_private_dns_zone(db_context, database_engine, vnet_resource_group, server_names[1], None, vnet_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, server_names[1] + ".private." + database_engine + ".database.azure.com"))

        # new private dns zone, zone name (vnet in same rg)
        dns_zone = prepare_private_dns_zone(db_context, database_engine, server_resource_group, server_names[2], private_dns_zone_names[0],
                                            server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, private_dns_zone_names[0]))

        # new private dns zone in dns rg, zone id (vnet in diff rg)
        dns_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                 self.get_subscription_id(), dns_resource_group, private_dns_zone_names[1])
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 database_engine, server_resource_group, server_names[3], location, dns_id, vnet_group_subnet["id"]))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, server_resource_group, server_names[3])).get_output_in_json()
        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, vnet_group_vnet_name, vnet_group_subnet_name))

        # new private dns zone, zone id vnet server same rg, zone diff rg
        dns_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                 self.get_subscription_id(), dns_resource_group, private_dns_zone_names[2])
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 database_engine, server_resource_group, server_names[4], location, dns_id, server_group_subnet["id"]))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, server_resource_group, server_names[4])).get_output_in_json()
        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_group_vnet_name, server_group_subnet_name))

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[3]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[4]),
                 checks=NoneCheck())

        time.sleep(15 * 60)


class FlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @live_only()
    def test_mysql_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)

    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')
        
        location = DEFAULT_LOCATION

        # flexible-servers
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]

        # Case 1 : Provision a server with public access all
        result = self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(database_engine, resource_group, servers[0], 'all', location)).get_output_in_json()

        self.cmd('{} flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(database_engine, resource_group, servers[0], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '0.0.0.0'),
                         JMESPathCheck('endIpAddress', '255.255.255.255')])

        # Case 2 : Provision a server with public access allowing all azure services
        result = self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(database_engine, resource_group, servers[1], '0.0.0.0', location)).get_output_in_json()

        self.cmd('{} flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(database_engine, resource_group, servers[1], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '0.0.0.0'),
                         JMESPathCheck('endIpAddress', '0.0.0.0')])

        # Case 3 : Provision a server with public access with rangwe
        result = self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                          .format(database_engine, resource_group, servers[2], '10.0.0.0-12.0.0.0', location)).get_output_in_json()

        self.cmd('{} flexible-server firewall-rule show -g {} -n {} -r {}'
                 .format(database_engine, resource_group, servers[2], result["firewallName"]),
                 checks=[JMESPathCheck('startIpAddress', '10.0.0.0'),
                         JMESPathCheck('endIpAddress', '12.0.0.0')])

        # Case 3 : Provision a server with public access with rangwe
        result = self.cmd('{} flexible-server create -g {} -n {} -l {} --yes'
                          .format(database_engine, resource_group, servers[3], location)).get_output_in_json()

        firewall_rule = self.cmd('{} flexible-server firewall-rule show -g {} -n {} -r {}'
                                 .format(database_engine, resource_group, servers[3], result["firewallName"])).get_output_in_json()
        self.assertEqual(firewall_rule['startIpAddress'], firewall_rule['endIpAddress'])

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[2]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[3]),
                 checks=NoneCheck())


class FlexibleServerUpgradeMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @live_only()
    def test_mysql_flexible_server_upgrade_mgmt(self, resource_group):
        self._test_flexible_server_upgrade_mgmt('mysql', resource_group, False)
        self._test_flexible_server_upgrade_mgmt('mysql', resource_group, True)
    
    def _test_flexible_server_upgrade_mgmt(self, database_engine, resource_group, public_access):
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        current_version = '5.7'
        new_version = '8'
        location = DEFAULT_LOCATION

        create_command = '{} flexible-server create -g {} -n {} --tier GeneralPurpose --sku-name {} --location {} --version {} --yes'.format(
            database_engine, resource_group, server_name, DEFAULT_GENERAL_PURPOSE_SKU, location, current_version)
        if public_access:
            create_command += ' --public-access none'
        else:
            vnet_name = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
            subnet_name = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
            create_command += ' --vnet {} --subnet {}'.format(vnet_name, subnet_name)

        # create primary server
        self.cmd(create_command)

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('version', current_version)])

        # create replica
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replica_name, server_name),
                 checks=[JMESPathCheck('version', current_version)])

        # remove sql_mode NO_AUTO_CREATE_USER, which is incompatible with new version 8
        for server in [replica_name, server_name]:
            self.cmd('{} flexible-server parameter set -g {} -s {} -n {} -v {}'
                        .format(database_engine,
                                resource_group,
                                server,
                                'sql_mode',
                                'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO'))

        # should fail because we first need to upgrade replica
        self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, server_name, new_version),
                    expect_failure=True)

        # upgrade replica
        result = self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, replica_name, new_version)).get_output_in_json()
        self.assertTrue(result['version'].startswith(new_version))

        # upgrade primary server
        result = self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, server_name, new_version)).get_output_in_json()
        self.assertTrue(result['version'].startswith(new_version))


class FlexibleServerBackupsMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @ServerPreparer(engine_type='mysql', location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_backups_mgmt(self, resource_group, server):
        self._test_backups_mgmt('mysql', resource_group, server)

    def _test_backups_mgmt(self, database_engine, resource_group, server):
        # No need to check the first backup in mysql flexible server because first backup visibility is a probability event. 
        backup_name = self.create_random_name('backup', 20)
        self.cmd('{} flexible-server backup create -g {} -n {} --backup-name {}'
                    .format(database_engine, resource_group, server, backup_name))

        backups = self.cmd('{} flexible-server backup list -g {} -n {}'
                            .format(database_engine, resource_group, server)).get_output_in_json()

        backups = sorted(backups, key=lambda x: x['completedTime'], reverse=True)

        customer_backup = self.cmd('{} flexible-server backup show -g {} -n {} --backup-name {}'
                                    .format(database_engine, resource_group, server, backup_name)).get_output_in_json()

        self.assertEqual(backup_name, customer_backup['name'])
        self.assertDictEqual(customer_backup, backups[0])


class FlexibleServerIdentityAADAdminMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_mysql_flexible_server_identity_aad_admin_mgmt(self, resource_group):
        self._test_identity_aad_admin_mgmt('mysql', resource_group, 'enabled')

    def _test_identity_aad_admin_mgmt(self, database_engine, resource_group, password_auth):
        login = 'alanenriqueo@microsoft.com'
        sid = '894ef8da-7971-4f68-972c-f561441eb329'

        server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) for _ in range(2)]

        # create server
        self.cmd('{} flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server, 'GeneralPurpose', DEFAULT_GENERAL_PURPOSE_SKU))

        # create 3 identities
        identity = []
        identity_id = []
        for i in range(3):
            identity.append(self.create_random_name('identity', 32))
            result = self.cmd('identity create -g {} --name {}'.format(resource_group, identity[i])).get_output_in_json()
            identity_id.append(result['id'])

        # add identity 1 to primary server
        self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                 .format(database_engine, resource_group, server, identity_id[0]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        # create replica 1
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replica[0], server))

        self.cmd('{} flexible-server identity list -g {} -s {}'
                 .format(database_engine, resource_group, replica[0]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        admins = self.cmd('{} flexible-server ad-admin list -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(0, len(admins))

        # try to add identity 2 to replica 1
        self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                    .format(database_engine, resource_group, replica[0], identity_id[1]),
                    expect_failure=True)

        # try to add AAD admin with identity 2 to replica 1
        self.cmd('{} flexible-server ad-admin create -g {} -s {} -u {} -i {} --identity {}'
                    .format(database_engine, resource_group, replica[0], login, sid, identity_id[1]),
                    expect_failure=True)

        # add AAD admin with identity 2 to primary server
        admin_checks = [JMESPathCheck('identityResourceId', identity_id[1]),
                        JMESPathCheck('administratorType', 'ActiveDirectory'),
                        JMESPathCheck('name', 'ActiveDirectory'),
                        JMESPathCheck('login', login),
                        JMESPathCheck('sid', sid)]

        self.cmd('{} flexible-server ad-admin create -g {} -s {} -u {} -i {} --identity {}'
                    .format(database_engine, resource_group, server, login, sid, identity_id[1]))
        
        self.cmd('{} flexible-server ad-admin show -g {} -s {}'
                    .format(database_engine, resource_group, server),
                    checks=admin_checks)

        self.cmd('{} flexible-server identity list -g {} -s {}'
                .format(database_engine, resource_group, server),
                checks=[
                    JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                    JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        # create replica 2
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replica[1], server))

        self.cmd('{} flexible-server identity list -g {} -s {}'
                 .format(database_engine, resource_group, replica[1]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        self.cmd('{} flexible-server ad-admin show -g {} -s {}'
                    .format(database_engine, resource_group, replica[1]),
                    checks=admin_checks)

        # verify that aad_auth_only=OFF in primary server and all replicas
        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server parameter show -g {} -s {} -n aad_auth_only'
                        .format(database_engine, resource_group, server_name),
                        checks=[JMESPathCheck('value', 'OFF')])
        
        # set aad_auth_only=ON in primary server and replica 2
        for server_name in [server, replica[1]]:
            self.cmd('{} flexible-server parameter set -g {} -s {} -n aad_auth_only -v {}'
                        .format(database_engine, resource_group, server_name, 'ON'),
                        checks=[JMESPathCheck('value', 'ON')])

        # try to remove identity 2 from primary server
        self.cmd('{} flexible-server identity remove -g {} -s {} -n {} --yes'
                    .format(database_engine, resource_group, server, identity_id[1]),
                    expect_failure=True)

        # try to remove AAD admin from replica 2
        self.cmd('{} flexible-server ad-admin delete -g {} -s {} --yes'
                 .format(database_engine, resource_group, replica[1]),
                 expect_failure=True)

        # remove AAD admin from primary server
        self.cmd('{} flexible-server ad-admin delete -g {} -s {} --yes'
                 .format(database_engine, resource_group, server))

        for server_name in [server, replica[0], replica[1]]:
            admins = self.cmd('{} flexible-server ad-admin list -g {} -s {}'
                              .format(database_engine, resource_group, server_name)).get_output_in_json()
            self.assertEqual(0, len(admins))

        # verify that aad_auth_only=OFF in primary server and all replicas
        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server parameter show -g {} -s {} -n aad_auth_only'
                        .format(database_engine, resource_group, server_name),
                        checks=[JMESPathCheck('value', 'OFF')])

        # add identity 3 to primary server
        self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                 .format(database_engine, resource_group, server, identity_id[2]))

        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server identity list -g {} -s {}'
                     .format(database_engine, resource_group, server_name),
                     checks=[
                         JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                         JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1])),
                         JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[2]))])

        # remove identities 1 and 2 from primary server
        self.cmd('{} flexible-server identity remove -g {} -s {} -n {} {} --yes'
                 .format(database_engine, resource_group, server, identity_id[0], identity_id[1]))

        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server identity list -g {} -s {}'
                     .format(database_engine, resource_group, server_name),
                     checks=[
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[1])),
                         JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[2]))])

        # remove identity 3 from primary server
        self.cmd('{} flexible-server identity remove -g {} -s {} -n {} --yes'
                    .format(database_engine, resource_group, server, identity_id[2]))

        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server identity list -g {} -s {}'
                        .format(database_engine, resource_group, server_name),
                        checks=[
                            JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                            JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[1])),
                            JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[2]))])

        # delete everything
        for server_name in [replica[0], replica[1], server]:
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))


class FlexibleServerAdvancedThreatProtectionScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus2')
    @ServerPreparer(engine_type='mysql', location='eastus2')
    def test_mysql_advanced_threat_protection_mgmt(self, resource_group, server):
        self._test_advanced_threat_protection_mgmt('mysql', resource_group, server)

    def _test_advanced_threat_protection_mgmt(self, database_engine, resource_group, server):
        state_enabled = AdvancedThreatProtectionState.ENABLED.value
        state_disabled = AdvancedThreatProtectionState.DISABLED.value

        # get advanced threat protection setting
        response = self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} -n {}'
                            .format(database_engine, resource_group, server),
                            checks=[JMESPathCheck('resourceGroup', resource_group)])

        # flip the setting, if current setting is disabled, then enable it and vice versa
        new_defender_state = state_enabled if response.get_output_in_json()['state'] == state_disabled else state_disabled

        # update advanced threat protection setting
        self.cmd('{} flexible-server advanced-threat-protection-setting update -g {} -n {}'
                 ' --state {}'
                 .format(database_engine, resource_group, server, new_defender_state),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', new_defender_state)])

        # get advanced threat protection settings after the update
        response = self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} -n {}'
                            .format(database_engine, resource_group, server),
                            checks=[
                                JMESPathCheck('resourceGroup', resource_group),
                                JMESPathCheck('state', new_defender_state)])
        
        # flip the setting, if current setting is disabled, then enable it and vice versa
        new_defender_state = state_enabled if response.get_output_in_json()['state'] == state_disabled else state_disabled

        # update advanced threat protection setting one more time to again get back to the original state
        self.cmd('{} flexible-server advanced-threat-protection-setting update -g {} -n {}'
                 ' --state {}'
                 .format(database_engine, resource_group, server, new_defender_state),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', new_defender_state)])

        # get advanced threat protection settings after the update
        response = self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} -n {}'
                            .format(database_engine, resource_group, server),
                            checks=[
                                JMESPathCheck('resourceGroup', resource_group),
                                JMESPathCheck('state', new_defender_state)])


class FlexibleServerMaintenanceMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='northeurope')
    @record_only() # this test need a manually configured server.

    def test_mysql_flexible_server_maintenance_mgmt(self, resource_group):
        self._test_maintenance_mgmt('mysql', resource_group)
    
    def _test_maintenance_mgmt(self, database_engine, resource_group):
        resource_group = "reschedule-cli-test"
        server_name = "azuredbclitest-maintenance"
        maintenance_list_response = self.cmd('{} flexible-server maintenance list --resource-group {} --server-name {}'
                 .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertNotEqual(len(maintenance_list_response), 0)

        maintenance_name = maintenance_list_response[0]['name']
        maintenance_id = maintenance_list_response[0]['id']
        maintenance_read_response = self.cmd('{} flexible-server maintenance show --resource-group {} --server-name {} --maintenance-name {}'
                 .format(database_engine, resource_group, server_name, maintenance_name)).get_output_in_json()
        self.assertEqual(maintenance_id, maintenance_read_response['id'])

        reschedule_start_time = "2024-11-06T03:41Z"
        maintenance_reschedule_response = self.cmd('{} flexible-server maintenance reschedule --resource-group {} --server-name {} --maintenance-name {} --start-time {}'
                 .format(database_engine, resource_group, server_name, maintenance_name, reschedule_start_time)).get_output_in_json()
        maintenance_rescheduled_time = parser.parse(maintenance_reschedule_response['maintenanceStartTime']).strftime('%Y-%m-%dT%H:%MZ')
        self.assertEqual(reschedule_start_time, maintenance_rescheduled_time)


class MySQLExportTest(ScenarioTest):
    profile = None

    def get_current_profile(self):
        if not self.profile:
            self.profile = self.cmd('cloud show --query profile -otsv').output
        return self.profile

    def get_account_key(self, group, name):
        if self.get_current_profile() == '2017-03-09-profile':
            template = 'storage account keys list -n {} -g {} --query "key1" -otsv'
        else:
            template = 'storage account keys list -n {} -g {} --query "[0].value" -otsv'

        return self.cmd(template.format(name, group)).output

    def get_account_info(self, group, name):
        """Returns the storage account name and key in a tuple"""
        return name, self.get_account_key(group, name)
    
    def storage_cmd(self, cmd, account_info, *args):
        cmd = cmd.format(*args)
        cmd = '{} --account-name {} --account-key {}'.format(cmd, *account_info)
        return self.cmd(cmd)
    
    def create_container(self, account_info, prefix='cont', length=24):
        container_name = self.create_random_name(prefix=prefix, length=length)
        self.storage_cmd('storage container create -n {}', account_info, container_name)
        return container_name

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location="eastus")
    @ServerPreparer(engine_type='mysql', location="eastus")
    @StorageAccountPreparer(location="eastus")

    def test_mysql_export(self, resource_group, server, storage_account):
        self._test_flexible_server_export_create_mgmt('mysql', resource_group, server, storage_account)

    def _test_flexible_server_export_create_mgmt(self, database_engine, resource_group, server, storage_account):     
        backup_name = "testexport"

        target_account_info = self.get_account_info(resource_group, storage_account)

        # Create the blob container
        container = self.create_container(target_account_info)

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')

        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'container': container
        })

        connection_str = self.cmd('storage account show-connection-string -n {account}  --query connectionString '
                                  '-otsv').output.strip()
        self.kwargs['con_str'] = connection_str
        # test sas-token for a container
        sas_uri = self.cmd('storage container generate-sas -n {container} --https-only --permissions racwdxyltfmei '
                       '--connection-string {con_str} --expiry {expiry} -otsv').output.strip()

        sas_uri = "https://" + storage_account + ".blob.core.windows.net/" + container + "?" + sas_uri

        update_response=self.cmd('{} flexible-server export create -n {} -g {} -b {} -u {}'.format(database_engine, server, resource_group, backup_name, sas_uri)).get_output_in_json()

        #Test to check if export is succeeded
        self.assertEqual(update_response['status'], 'Succeeded')

        #Delete storage account
        self.cmd('storage account delete --name {} --resource-group {} --yes --output none'.format(storage_account, resource_group))

        # deletion of single server created
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server), checks=NoneCheck())
