# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from datetime import datetime, timedelta, tzinfo
from time import sleep
from dateutil.tz import tzutc
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.local_context import AzCLILocalContext, ALL, LOCAL_CONTEXT_FILE
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StringContainCheck,
    VirtualNetworkPreparer,
    LocalContextScenarioTest,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from ..._client_factory import cf_mysql_flexible_private_dns_zone_suffix_operations, cf_postgres_flexible_private_dns_zone_suffix_operations
from ...flexible_server_virtual_network import prepare_private_network, prepare_private_dns_zone, prepare_public_network, DEFAULT_VNET_ADDRESS_PREFIX, DEFAULT_SUBNET_ADDRESS_PREFIX
from ...flexible_server_custom_postgres import DbContext as PostgresDbContext
from ...flexible_server_custom_mysql import DbContext as MysqlDbContext
from ...flexible_server_custom_mysql import _determine_iops
from ..._flexible_server_util import get_mysql_list_skus_info
# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20


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

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_iops_mgmt(self, resource_group):
        self._test_flexible_server_iops_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('mysql', resource_group)
    
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_restore_mgmt(self, resource_group):
        self._test_flexible_server_restore_mgmt('postgres', resource_group)
    
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_restore_mgmt(self, resource_group):
        self._test_flexible_server_restore_mgmt('mysql', resource_group)
    
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_georestore_mgmt(self, resource_group):
        self._test_flexible_server_georestore_mgmt('mysql', resource_group)

    def _test_flexible_server_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            version = '12'
            storage_size = 128
            location = self.postgres_location
            location_result = 'East US'
            sku_name = 'Standard_D2s_v3'
        elif database_engine == 'mysql':
            storage_size = 32
            version = '5.7'
            location = self.mysql_location
            location_result = 'West US 2'
            sku_name = 'Standard_D2ds_v4'
        tier = 'GeneralPurpose'        
        backup_retention = 7
        database_name = 'testdb'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        ha_value = 'Enabled' if database_engine == 'postgres' else 'ZoneRedundant'

        self.cmd('{} flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --database-name {} --high-availability {} \
                  --zone 1 --public-access None'.format(database_engine,
                  resource_group, server_name, backup_retention, sku_name, tier, storage_size, 'dbadmin', version, database_name, ha_value))

        list_checks = [JMESPathCheck('name', server_name),
                        JMESPathCheck('location', location_result),  # location should be same as rg location
                        JMESPathCheck('resourceGroup', resource_group),
                        JMESPathCheck('sku.name', sku_name),
                        JMESPathCheck('sku.tier', tier),
                        JMESPathCheck('version', version),
                        JMESPathCheck('storage.storageSizeGb', storage_size),
                        JMESPathCheck('backup.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=list_checks)

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

        if database_engine == 'postgres':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
        elif database_engine == 'mysql':
            tier = 'MemoryOptimized'
            sku_name = 'Standard_E2ds_v4'
        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server_name, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

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

    def _test_flexible_server_iops_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        location = 'westus2'
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

    def _test_flexible_server_restore_mgmt(self, database_engine, resource_group):

        private_dns_param = 'privateDnsZoneResourceId' if database_engine == 'mysql' else 'privateDnsZoneArmResourceId'
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location
        
        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

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
        date_format = '%Y-%m-%dT%H:%M:%S.%f+00:00'

        if current_time < earliest_restore_time:
            sleep((datetime.strptime(earliest_restore_time, date_format) - datetime.strptime(current_time,
                                                                                             date_format)).total_seconds())

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
        if database_engine == 'mysql':
            restore_result = self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --public-access Enabled'
                                  .format(database_engine, resource_group, target_server_public_access, source_server)).get_output_in_json()

            self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')

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
        if database_engine == 'mysql':
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

    def _test_flexible_server_georestore_mgmt(self, database_engine, resource_group):
    
        private_dns_param = 'privateDnsZoneResourceId' if database_engine == 'mysql' else 'privateDnsZoneArmResourceId'
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = 'eastus2euap'
            target_location = 'centraluseuap'
        
        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        source_server_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_public_access_2 = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

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
        if database_engine == 'mysql':
            restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} --name {} --source-server {} --public-access enabled'
                                  .format(database_engine, resource_group, target_location, target_server_public_access, source_server)).get_output_in_json()

            self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')
            self.assertEqual(restore_result['location'], 'Central US EUAP')

        # 3. vnet to different vnet
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, target_location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24'.format(
                          resource_group, new_subnet, new_vnet)).get_output_in_json()

        restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} -n {} --source-server {} --subnet {} --yes'.format(
                                  database_engine, resource_group, target_location, target_server_diff_vnet, source_server, subnet["id"])).get_output_in_json()
        
        self.assertEqual(restore_result['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, new_vnet, new_subnet))

        self.assertEqual(restore_result['network'][private_dns_param],  # private dns zone needs to be created
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, '{}.private.{}.database.azure.com'.format(target_server_diff_vnet, database_engine)))
        
        # 4. public access to vnet
        if database_engine == 'mysql':
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
        restore_result = self.cmd('{} flexible-server geo-restore -g {} -l {} --name {} --source-server {}'
                                  .format(database_engine, resource_group, target_location, target_server_public_access_2, source_server_2)).get_output_in_json()

        self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')
        self.assertEqual(restore_result['location'], 'Central US EUAP')

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
                 database_engine, resource_group, target_server_public_access_2), checks=NoneCheck())


class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('postgres', resource_group, server)
        self._test_parameter_mgmt('postgres', resource_group, server)
        self._test_database_mgmt('postgres', resource_group, server)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @ServerPreparer(engine_type='mysql', location=mysql_location)
    def test_mysql_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('mysql', resource_group, server)
        self._test_parameter_mgmt('mysql', resource_group, server)
        self._test_database_mgmt('mysql', resource_group, server)

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

        if database_engine == 'mysql':
            parameter_name = 'wait_timeout'
            default_value = '28800'
            value = '30000'
        elif database_engine == 'postgres':
            parameter_name = 'lock_timeout'
            default_value = '0'
            value = '2000'

        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {} -g {} -s {}'.format(database_engine, parameter_name, resource_group, server),
                 checks=[JMESPathCheck('defaultValue', default_value),
                         JMESPathCheck('source', source)])

        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])

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


class FlexibleServerValidatorScenarioTest(ScenarioTest):

    postgres_location = 'eastus2euap'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_create_validator(self, resource_group):
        self._test_mgmt_create_validator('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt_create_validator(self, resource_group):
        self._test_mgmt_create_validator('mysql', resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_update_validator(self, resource_group):
        self._test_mgmt_update_validator('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt_update_validator(self, resource_group):
        self._test_mgmt_update_validator('mysql', resource_group)

    def _test_mgmt_create_validator(self, database_engine, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 30
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        ha_value = 'Enabled' if database_engine == 'postgres' else 'ZoneRedundant'

        # Create
        if database_engine == 'postgres':
            self.cmd('{} flexible-server create -g {} -n Wrongserver.Name -l {}'.format(
                    database_engine, resource_group, location),
                    expect_failure=True)

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

        if database_engine == 'mysql':
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

        if database_engine == 'postgres':
            invalid_storage_size = 60
        elif database_engine == 'mysql':
            invalid_storage_size = 10
        self.cmd('{} flexible-server create -g {} -l {} --storage-size {} --public-access none'.format(
                 database_engine, resource_group, location, invalid_storage_size),
                 expect_failure=True)

    def _test_mgmt_update_validator(self, database_engine, resource_group):
        RANDOM_VARIABLE_MAX_LENGTH = 30
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        if database_engine == 'postgres':
            version = 12
            storage_size = 128
            location = self.postgres_location
        elif database_engine == 'mysql':
            version = 5.7            
            storage_size = 32
            location = self.mysql_location
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

        if database_engine == 'postgres':
            invalid_storage_size = 64
        else:
            invalid_storage_size = 30
        self.cmd('{} flexible-server update -g {} -n {} --storage-size {}'.format(
                 database_engine, resource_group, server_name, invalid_storage_size), #cannot update to smaller size
                 expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'.format(
                 database_engine, resource_group, server_name, invalid_backup_retention),
                 expect_failure=True)
        
        ha_value = 'Enabled' if database_engine == 'postgres' else 'ZoneRedundant'
        self.cmd('{} flexible-server update -g {} -n {} --high-availability {}'.format(
                 database_engine, resource_group, server_name, ha_value),
                 expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, server_name), checks=NoneCheck())


class FlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    mysql_location = 'westus2'

    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('mysql', resource_group)

    def _test_flexible_server_replica_mgmt(self, database_engine, resource_group):
        location = self.mysql_location
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none --tier GeneralPurpose --sku-name Standard_D2ds_v4'
                 .format(database_engine, resource_group, master_server, location, 256))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'None')]).get_output_in_json()

        # test replica create
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --zone 2'
                 .format(database_engine, resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

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
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test delete master server
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replicas[1], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[1]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, master_server), checks=NoneCheck())

        # test show server with replication info, replica was auto stopped after master server deleted
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, replicas[1]),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # clean up servers
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())


class FlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus2euap'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('postgres', resource_group)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('mysql', resource_group)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('postgres', resource_group)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('postgres', resource_group_1, resource_group_2)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_2')
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('mysql', resource_group_1, resource_group_2)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_vnet_mgmt_prepare_private_network_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_prepare_private_network_vname_and_subnetname(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_vnet_mgmt_prepare_private_network_vnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_prepare_private_network_vnet(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_vnet_mgmt_prepare_private_network_subnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_prepare_private_network_subnet(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_vnet_mgmt_validator(self, resource_group):
        self._test_flexible_server_vnet_mgmt_validator(resource_group)

    def _test_flexible_server_vnet_mgmt_existing_supplied_subnetid(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
            private_dns_zone_key = "privateDnsZoneArmResourceId"
        elif database_engine == 'mysql':
            location = self.mysql_location
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
        if database_engine == 'postgres':
            self.assertEqual(show_result_1['network'][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                                self.get_subscription_id(), resource_group, private_dns_zone))
        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))
        
        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        vnet_name = 'clitestvnet3'
        subnet_name = 'clitestsubnet3'
        vnet_name_2 = 'clitestvnet4'
        address_prefix = '13.0.0.0/16'

        if database_engine == 'postgres':
            location = self.postgres_location
            private_dns_zone_key = "privateDnsZoneArmResourceId"
        elif database_engine == 'mysql':
            location = self.mysql_location
            private_dns_zone_key = "privateDnsZoneResourceId"

        # flexible-servers
        servers = ['testvnetserver3' + database_engine, 'testvnetserver4' + database_engine]
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
        
        if database_engine == 'postgres':
            self.assertEqual(show_result_1['network'][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                                self.get_subscription_id(), resource_group, private_dns_zone_1))
            
            self.assertEqual(show_result_2['network'][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                                self.get_subscription_id(), resource_group, private_dns_zone_2))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, database_engine, resource_group_1, resource_group_2):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
            private_dns_zone_key = "privateDnsZoneArmResourceId"
        elif database_engine == 'mysql':
            location = self.mysql_location
            private_dns_zone_key = "privateDnsZoneResourceId"

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
        
        if database_engine == 'postgres':
            self.assertEqual(show_result_1['network'][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                                self.get_subscription_id(), resource_group_1, private_dns_zone))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, server_name),
                 checks=NoneCheck())


        # time.sleep(15 * 60)

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1,
                                                                                                         subnet_name,
                                                                                                         vnet_name))
        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_1, vnet_name))

    def _test_flexible_server_vnet_mgmt_prepare_private_network_vname_and_subnetname(self, resource_group):
        server_name = 'vnet-preparer-server'
        delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
        location = self.postgres_location
        yes = True

        #   Vnet x exist, subnet x exist, address prefixes
        vnet = 'testvnet1'
        subnet = 'testsubnet1'
        vnet_address_pref = '172.1.0.0/16'
        subnet_address_pref = '172.1.0.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, subnet))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        #   Vnet exist, subnet x exist, address prefixes 
        vnet = 'testvnet1'
        subnet = 'testsubnet2'
        vnet_address_pref = '172.1.0.0/16'
        subnet_address_pref = '172.1.1.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, subnet))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # Vnet exist, subnet x exist, x address prefixes
        vnet = 'testvnet1'
        subnet = 'testsubnet3'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, subnet, location, delegation_service_name, None, None, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, subnet))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(DEFAULT_VNET_ADDRESS_PREFIX)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', DEFAULT_SUBNET_ADDRESS_PREFIX),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # Vnet exist, subnet exist, x address prefixes
        vnet = 'testvnet1'
        subnet = 'testsubnet1'
        vnet_address_pref = '172.1.0.0/16'
        subnet_address_pref = '172.1.0.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, subnet, location, delegation_service_name, None, None, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, subnet))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # Vnet exist, subnet exist, address prefixes
        vnet = 'testvnet1'
        subnet = 'testsubnet1'
        vnet_address_pref = '173.1.0.0/16'
        subnet_address_pref = '173.2.0.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, subnet, location, delegation_service_name, None, None, yes=yes)
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck('172.1.0.0/16')])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', '172.1.0.0/24'),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

    def _test_flexible_server_vnet_mgmt_prepare_private_network_vnet(self, resource_group):
        server_name = 'vnet-preparer-server'
        resource_group_2 = self.create_random_name('clitest.rg', 20)
        delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
        location = self.postgres_location
        yes = True

        # Vnet x exist -> subnet generate with default prefix 
        vnet = 'testvnet1'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, None, location, delegation_service_name, None, None, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, 'Subnet' + server_name))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(DEFAULT_VNET_ADDRESS_PREFIX)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', DEFAULT_SUBNET_ADDRESS_PREFIX),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # Vnet x exist (id, diff rg)
        vnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(self.get_subscription_id(), resource_group_2, 'testvnet2')
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, None, location, delegation_service_name, None, None, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group_2, 'testvnet2', 'Subnet' + server_name))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(DEFAULT_VNET_ADDRESS_PREFIX)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', DEFAULT_SUBNET_ADDRESS_PREFIX),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

	    # Vnet exist (name), vnet prefix, subnet prefix
        vnet = 'testvnet3'
        vnet_address_pref = '172.0.0.0/16'
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format(vnet, resource_group, location, vnet_address_pref))
        subnet_address_pref = '172.0.10.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, None, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet, 'Subnet' + server_name))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

	    # Vnet exist (id, diff rg), vnet prefix, subnet prefix
        vnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(self.get_subscription_id(), resource_group_2, 'testvnet4')
        vnet_address_pref = '173.1.0.0/16'
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format('testvnet4', resource_group_2, location, vnet_address_pref))
        subnet_address_pref = '173.1.1.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, vnet, None, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group_2, 'testvnet4', 'Subnet' + server_name))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

    def _test_flexible_server_vnet_mgmt_prepare_private_network_subnet(self, resource_group):
        server_name = 'vnet-preparer-server'
        delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
        location = self.postgres_location
        yes = True

        #   subnet x exist
        subnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                 self.get_subscription_id(), resource_group, 'testvnet', 'testsubnet')
        vnet_address_pref = '172.1.0.0/16'
        subnet_address_pref = '172.1.0.0/24'
        subnet_id = prepare_private_network(self, resource_group, server_name, None, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, 'testvnet', 'testsubnet'))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])
        
        # subnet exist
        subnet_address_pref = '172.1.1.0/24'
        self.cmd('network vnet subnet create -g {} -n {} --address-prefixes {} --vnet-name {}'.format(
                  resource_group, 'testsubnet2', subnet_address_pref, 'testvnet'))
        subnet = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                 self.get_subscription_id(), resource_group, 'testvnet', 'testsubnet2')
        
        subnet_id = prepare_private_network(self, resource_group, server_name, None, subnet, location, delegation_service_name, vnet_address_pref, subnet_address_pref, yes=yes)
        vnet_id = subnet_id.split('/subnets/')[0]
        self.assertEqual(subnet_id,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, 'testvnet', 'testsubnet2'))
        self.cmd('network vnet show --id {}'.format(vnet_id),
                 checks=[StringContainCheck(vnet_address_pref)])
        self.cmd('network vnet subnet show --id {}'.format(subnet_id),
                 checks=[JMESPathCheck('addressPrefix', subnet_address_pref),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

    def _test_flexible_server_vnet_mgmt_validator(self, resource_group):
        # location validator
        vnet_name = 'testvnet'
        subnet_name = 'testsubnet'
        vnet_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        location = self.postgres_location
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {}'.format(
                 resource_group, location, vnet_name, vnet_prefix))
        
        self.cmd('postgres flexible-server create -g {} -l {} --vnet {} --yes'.format(
                 resource_group, 'eastus', vnet_name), # location of vnet and server are different
                 expect_failure=True)
        
        # delegated to different service
        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes {} --delegations {}'.format(
                          resource_group, subnet_name, vnet_name, subnet_prefix, "Microsoft.DBforMySQL/flexibleServers")).get_output_in_json()
        
        self.cmd('postgres flexible-server create -g {} -l {} --subnet {} --yes'.format(
                 resource_group, 'eastus', subnet["id"]), # Delegated to different service
                 expect_failure=True)
        
    def get_models(self, *attr_args, **kwargs):
        from azure.cli.core.profiles import get_sdk
        self.module_kwargs = kwargs
        resource_type = kwargs.get('resource_type', self._get_resource_type())
        operation_group = kwargs.get('operation_group', self.module_kwargs.get('operation_group', None))
        return get_sdk(self.cli_ctx, resource_type, *attr_args, mod='models', operation_group=operation_group)

    def _get_resource_type(self):
        resource_type = self.module_kwargs.get('resource_type', None)
        if not resource_type:
            command_type = self.module_kwargs.get('command_type', None)
            resource_type = command_type.settings.get('resource_type', None) if command_type else None
        return resource_type


class FlexibleServerPrivateDnsZoneScenarioTest(ScenarioTest):
    postgres_location = 'eastus2euap'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    def test_postgres_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        self._test_flexible_server_existing_private_dns_zone('postgres', server_resource_group, vnet_resource_group)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    def test_mysql_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        self._test_flexible_server_existing_private_dns_zone('mysql', server_resource_group, vnet_resource_group)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='dns_resource_group')
    def test_postgres_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        self._test_flexible_server_new_private_dns_zone('postgres', server_resource_group, vnet_resource_group, dns_resource_group)

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='dns_resource_group')
    def test_mysql_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        self._test_flexible_server_new_private_dns_zone('mysql', server_resource_group, vnet_resource_group, dns_resource_group)
    
    def _test_flexible_server_existing_private_dns_zone(self, database_engine, server_resource_group, vnet_resource_group):
        server_names = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        if database_engine == 'postgres':
            location = self.postgres_location
            delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
            private_dns_zone_key = "privateDnsZoneArmResourceId"
        else:
            location = self.mysql_location
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
        if database_engine == 'postgres':
            self.assertEqual(result["network"][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), server_resource_group, unlinked_dns_zone))
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
        if database_engine == 'postgres':
            self.assertEqual(result["network"][private_dns_zone_key],
                            '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), vnet_resource_group, vnet_group_dns_zone))
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
        if database_engine == 'postgres':
            location = self.postgres_location
            delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
            private_dns_zone_key = "privateDnsZoneArmResourceId"
            db_context = PostgresDbContext(cmd=self,
                                           cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
                                           command_group='postgres')
        else:
            location = self.mysql_location
            delegation_service_name = "Microsoft.DBforMySQL/flexibleServers"
            db_context = MysqlDbContext(cmd=self,
                                        cf_private_dns_zone_suffix=cf_mysql_flexible_private_dns_zone_suffix_operations,
                                        command_group='mysql')
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
        # no input, vnet in server rg
        dns_zone = prepare_private_dns_zone(db_context, database_engine, server_resource_group, server_names[0], None, server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_names[0] + ".private." + database_engine + ".database.azure.com"))

        # no input, vnet in vnet rg
        dns_zone = prepare_private_dns_zone(db_context, database_engine, server_resource_group, server_names[1], None, vnet_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, server_names[1] + ".private." + database_engine + ".database.azure.com"))
 
        # new private dns zone, zone name (vnet in smae rg)
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
        if database_engine == 'postgres':
            self.assertEqual(result["network"][private_dns_zone_key], dns_id)

        # new private dns zone, zone id vnet server same rg, zone diff rg
        dns_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                 self.get_subscription_id(), dns_resource_group, private_dns_zone_names[2])
        self.cmd('{} flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 database_engine, server_resource_group, server_names[4], location, dns_id, server_group_subnet["id"]))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, server_resource_group, server_names[4])).get_output_in_json()
        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_group_vnet_name, server_group_subnet_name))
        if database_engine == 'postgres':
            self.assertEqual(result["network"][private_dns_zone_key], dns_id)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[3]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, server_resource_group, server_names[4]),
                 checks=NoneCheck())

        time.sleep(15 * 60)


class FlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @live_only()
    def test_mysql_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)

    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            sku_name = 'Standard_D2s_v3'
            location = self.postgres_location
        elif database_engine == 'mysql':
            sku_name = 'Standard_B1ms'
            location = self.mysql_location

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
