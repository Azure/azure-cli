# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time

from datetime import datetime, timezone
from time import sleep
from azure.cli.core.util import parse_proxy_resource_id
from dateutil import parser
from dateutil.tz import tzutc
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckNotExists,
    NoneCheck,
    ResourceGroupPreparer,
    KeyVaultPreparer,
    ScenarioTest,
    StringContainCheck,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from azure.core.exceptions import HttpResponseError
from ..._client_factory import cf_postgres_flexible_private_dns_zone_suffix_operations
from ...flexible_server_virtual_network import prepare_private_network, prepare_private_dns_zone, DEFAULT_VNET_ADDRESS_PREFIX, DEFAULT_SUBNET_ADDRESS_PREFIX
from ...flexible_server_custom_postgres import DbContext as PostgresDbContext
from ..._util import retryable_method

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
    postgres_backup_location = 'westus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_flexible_server_ssdv2_mgmt(self, resource_group):
        self._test_flexible_server_ssdv2_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_restore_mgmt(self, resource_group):
        self._test_flexible_server_restore_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_georestore_mgmt(self, resource_group):
        self._test_flexible_server_georestore_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus2euap')
    def test_flexible_server_ssdv2_restore_mgmt(self, resource_group):
        self._test_flexible_server_ssdv2_restore_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='vault_name', location=postgres_location, additional_params='--enable-purge-protection true --retention-days 90')
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='backup_vault_name', location=postgres_backup_location, additional_params='--enable-purge-protection true --retention-days 90')
    def test_postgres_flexible_server_byok_mgmt(self, resource_group, vault_name, backup_vault_name):
        self._test_flexible_server_byok_mgmt(resource_group, vault_name, backup_vault_name)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='vault_name', location=postgres_location, additional_params='--enable-purge-protection true --retention-days 90')
    @KeyVaultPreparer(name_prefix='rdbmsvault', parameter_name='backup_vault_name', location=postgres_backup_location, additional_params='--enable-purge-protection true --retention-days 90')
    def test_postgres_flexible_server_public_revivedropped_mgmt(self, resource_group, vault_name, backup_vault_name):
        self._test_flexible_server_revivedropped_mgmt(resource_group, vault_name, backup_vault_name)

    def _test_flexible_server_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        version = '16'
        storage_size = 128
        location = self.postgres_location
        sku_name = 'Standard_D2s_v3'
        memory_optimized_sku = 'Standard_E2ds_v4'
        tier = 'GeneralPurpose'
        backup_retention = 7
        database_name = 'testdb'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        ha_value = 'ZoneRedundant'

        self.cmd('{} flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --database-name {} --high-availability {} \
                  --public-access None'.format(database_engine, resource_group, server_name, backup_retention,
                                               sku_name, tier, storage_size, 'dbadmin', version, database_name, ha_value))

        basic_info = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size)
        self.assertEqual(basic_info['backup']['backupRetentionDays'], backup_retention)

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'
                    .format(database_engine, resource_group, server_name, database_name), checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server update -g {} -n {} -p randompw321##@!'
                 .format(database_engine, resource_group, server_name))

        self.cmd('{} flexible-server update -g {} -n {} --storage-size 256'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 256 )])

        self.cmd('{} flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.autoGrow', "Enabled" )])

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'
                 .format(database_engine, resource_group, server_name, backup_retention + 10),
                 checks=[JMESPathCheck('backup.backupRetentionDays', backup_retention + 10)])

        tier = 'MemoryOptimized'
        sku_name = memory_optimized_sku
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

        self.cmd('{} flexible-server update -g {} -n {} --storage-auto-grow Disabled'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.autoGrow', "Disabled" )])

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


    def _test_flexible_server_ssdv2_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        version = '15'
        storage_size = 200
        location = self.postgres_location
        sku_name = 'Standard_D2s_v3'
        tier = 'GeneralPurpose'
        storage_type = 'PremiumV2_LRS'
        iops = 3000
        throughput = 125
        backup_retention = 7
        database_name = 'testdb'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        # test create
        self.cmd('{} flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --database-name {} --storage-type {} \
                  --iops {} --throughput {} --public-access None'.format(database_engine, resource_group, server_name,
                                                                                    backup_retention, sku_name, tier, storage_size,
                                                                                    'dbadmin', version, database_name, storage_type,
                                                                                    iops, throughput))

        basic_info = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size)
        self.assertEqual(basic_info['storage']['type'], storage_type)
        self.assertEqual(basic_info['storage']['iops'], iops)
        self.assertEqual(basic_info['storage']['throughput'], throughput)
        self.assertEqual(basic_info['backup']['backupRetentionDays'], backup_retention)

        # test updates
        self.cmd('{} flexible-server update -g {} -n {} --storage-size 300'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 300 )])

        self.cmd('{} flexible-server update -g {} -n {} --iops 3500'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.iops', 3500 )])

        self.cmd('{} flexible-server update -g {} -n {} --throughput 400'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.throughput', 400 )])

        # test failures
        self.cmd('{} flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(database_engine, resource_group, server_name),
                 expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --high-availability SameZone'
                 .format(database_engine, resource_group, server_name),
                 expect_failure=True)

        replica_name = 'rep-ssdv2-' + server_name
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replica_name, basic_info['id']),
                 expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())


    def _test_flexible_server_restore_mgmt(self, database_engine, resource_group):

        private_dns_param = 'privateDnsZoneArmResourceId'
        location = self.postgres_location

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

        # to different vnet and private dns zone
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24 --default-outbound false'.format(
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

        private_dns_param = 'privateDnsZoneArmResourceId'
        location = self.postgres_location
        target_location = self.postgres_backup_location

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

        # vnet -> vnet without network parameters fail
        self.cmd('{} flexible-server geo-restore -g {} -l {} --name {} --source-server {} '
                 .format(database_engine, resource_group, target_location, target_server_default, source_server), expect_failure=True)

        # vnet to different vnet
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, target_location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24 --default-outbound false'.format(
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

        # public to public
        restore_result = retryable_method(retries=10, interval_sec=360 if os.environ.get(ENV_LIVE_TEST, False) else 0, exception_type=HttpResponseError,
                                          condition=lambda ex: 'GeoBackupsNotAvailable' in ex.message)(self.cmd)(
                                              '{} flexible-server geo-restore -g {} -l {} --name {} --source-server {}'.format(
                                              database_engine, resource_group, target_location, target_server_public_access_2, source_server_2)
                                         ).get_output_in_json()

        #self.assertEqual(restore_result['network']['publicNetworkAccess'], 'Enabled')
        self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), target_location)

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


    def _test_flexible_server_ssdv2_restore_mgmt(self, database_engine, resource_group):

        location = 'eastus2euap'
        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        source_ssdv2_server = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-', 40)
        target_server_ssdv2_migration = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-migrate-', 40)
        target_server_ssdv2 = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-restore-', 40)
        storage_type = 'PremiumV2_LRS'
        iops = 3000
        throughput = 125

        # Restore to ssdv2
        self.cmd('{} flexible-server create -g {} -n {} -l {} --public-access None --yes'.format(
                 database_engine, resource_group, source_server, location))

        # Restore to ssdv2
        self.cmd('{} flexible-server create -g {} -n {} -l {} --storage-type {} --iops {} --throughput {} --public-access None --yes'.format(
                 database_engine, resource_group, source_ssdv2_server, location, storage_type, iops, throughput))

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # Restore to ssdv2
        restore_migration_result = self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --storage-type {}'
                                  .format(database_engine, resource_group, target_server_ssdv2_migration, source_server, storage_type)).get_output_in_json()
        self.assertEqual(restore_migration_result['storage']['type'], storage_type)

        # Restore ssdv2 server
        restore_ssdv2_result = self.cmd('{} flexible-server restore -g {} --name {} --source-server {}'
                                  .format(database_engine, resource_group, target_server_ssdv2, source_ssdv2_server)).get_output_in_json()
        self.assertEqual(restore_ssdv2_result['storage']['type'], storage_type)

        # Delete servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, source_server), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, source_ssdv2_server), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_ssdv2_migration), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_ssdv2), checks=NoneCheck())


    def _test_flexible_server_byok_mgmt(self, resource_group, vault_name, backup_vault_name=None):
        live_test = False
        key_name = self.create_random_name('rdbmskey', 32)
        identity_name = self.create_random_name('identity', 32)
        backup_key_name = self.create_random_name('rdbmskey', 32)
        backup_identity_name = self.create_random_name('identity', 32)
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_with_geo_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        backup_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        geo_backup_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        key_2_name = self.create_random_name('rdbmskey', 32)
        identity_2_name = self.create_random_name('identity', 32)
        server_2_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        tier = 'GeneralPurpose'
        sku_name = 'Standard_D2s_v3'
        location = self.postgres_location
        backup_location = self.postgres_backup_location
        replication_role = 'AsyncReplica'
        scope = '/subscriptions/{}/resourceGroups/{}'.format(self.get_subscription_id(), resource_group)

        # Create identity and assign role
        key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                       .format(key_name, vault_name)).get_output_in_json()

        identity = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, identity_name, location)).get_output_in_json()
        if (live_test):
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Crypto User" --scope {}'.format( identity['principalId'], scope))
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Certificate User" --scope {}'.format( identity['principalId'], scope))

        # Create backup identity and assign role
        backup_key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                                  .format(backup_key_name, backup_vault_name)).get_output_in_json()

        backup_identity = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, backup_identity_name, backup_location)).get_output_in_json()
        if (live_test):
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Crypto User" --scope {}'.format( backup_identity['principalId'], scope))
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Certificate User" --scope {}'.format( backup_identity['principalId'], scope))

        # Create identity 2 and assign role
        key_2 = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                            .format(key_2_name, vault_name)).get_output_in_json()

        identity_2 = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, identity_2_name, location)).get_output_in_json()
        if (live_test):
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Crypto User" --scope {}'.format( identity_2['principalId'], scope))
            self.cmd('role assignment create --assignee-object-id {} --assignee-principal-type ServicePrincipal --role "Key Vault Certificate User" --scope {}'.format( identity_2['principalId'], scope))

        def invalid_input_tests():
            # key or identity only
            self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {}'.format(
                resource_group,
                server_name,
                tier,
                sku_name,
                key['key']['kid']
            ), expect_failure=True)

            self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --identity {}'.format(
                resource_group,
                server_name,
                tier,
                sku_name,
                identity['id'],
            ), expect_failure=True)

            # geo-redundant server with data encryption needs backup_key and backup_identity
            self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} --geo-redundant-backup Enabled'.format(
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
            primary_server_name = server_with_geo_name if geo_redundant_backup else server_name
            # create primary flexible server with data encryption
            self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} {} --location {} --geo-redundant-backup {}'.format(
                        resource_group,
                        primary_server_name,
                        tier,
                        sku_name,
                        key['key']['kid'],
                        identity['id'],
                        backup_key_id_flags,
                        location,
                        geo_redundant_backup_enabled
                    ))

            # should fail because we can't remove identity used for data encryption
            self.cmd('postgres flexible-server identity remove -g {} -s {} -n {} --yes'
                     .format(resource_group, primary_server_name, identity['id']),
                     expect_failure=True)

            main_checks = [
                JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
                JMESPathCheck('dataEncryption.primaryKeyUri', key['key']['kid']),
                JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', identity['id'])
            ]

            geo_checks = []
            if geo_redundant_backup:
                geo_checks = [
                    JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(backup_identity['id'])),
                    JMESPathCheck('dataEncryption.geoBackupKeyUri', backup_key['key']['kid']),
                    JMESPathCheck('dataEncryption.geoBackupUserAssignedIdentityId', backup_identity['id'])
                ]

            result = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, primary_server_name),
                    checks=main_checks + geo_checks).get_output_in_json()

            # create replica 1 with data encryption            
            replica_1_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

            self.cmd('postgres flexible-server replica create -g {} --replica-name {} --source-server {} --key {} --identity {}'.format(
                        resource_group,
                        replica_1_name,
                        primary_server_name,
                        key['key']['kid'],
                        identity['id']
            ), checks=main_checks + [JMESPathCheck('replicationRole', replication_role)])

            # update different key and identity in primary server
            self.cmd('postgres flexible-server update -g {} -n {} --key {} --identity {}'.format(
                        resource_group,
                        primary_server_name,
                        key_2['key']['kid'],
                        identity_2['id']
            ), checks=[
                JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity_2['id'])),
                JMESPathCheck('dataEncryption.primaryKeyUri', key_2['key']['kid']),
                JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', identity_2['id'])
            ])

            # restore backup
            current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
            earliest_restore_time = result['backup']['earliestRestoreDate']
            seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
            sleep(max(0, seconds_to_wait))

            # By default, Geo-redundant backup is disabled for restore hence no need to pass backup-key and backup-identity
            data_encryption_key_id_flag = '--key {} --identity {}'.format(key['key']['kid'], identity['id'])

            restore_result = self.cmd('postgres flexible-server {} -g {} --name {} --source-server {} {}'.format(
                     'restore',
                     resource_group,
                     backup_name,
                     primary_server_name,
                     data_encryption_key_id_flag
            ), checks=main_checks).get_output_in_json()

            # geo-restore backup
            if geo_redundant_backup:
                current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
                earliest_restore_time = result['backup']['earliestRestoreDate']
                seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
                sleep(max(0, seconds_to_wait))

                data_encryption_key_id_flag = '--key {} --identity {} --backup-key {} --backup-identity {}'.format(backup_key['key']['kid'], backup_identity['id'], key['key']['kid'], identity['id'])

                # By default, Geo-redundant backup is disabled for geo-restore hence explicitly need to set georedundant backup Enabled
                restore_result = retryable_method(retries=10,
                                                  interval_sec=360 if os.environ.get(ENV_LIVE_TEST, False) else 0,
                                                  exception_type=HttpResponseError,
                                                  condition=lambda ex: \
                                                            'GeoBackupsNotAvailable' \
                                                            in ex.message)(self.cmd)('postgres \
                                                                                      flexible-server {} \
                                                                                      -g {} --name {} \
                                                                                      --source-server {} \
                                                                                      --geo-redundant-backup Enabled \
                                                                                      {}'.format(
                                                                                        'geo-restore --location {}'.format(backup_location),
                                                                                        resource_group,
                                                                                        geo_backup_name,
                                                                                        primary_server_name,
                                                                                        data_encryption_key_id_flag
                                                                                    ), checks=[
                                                                                        JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(backup_identity['id'])),
                                                                                        JMESPathCheck('dataEncryption.primaryKeyUri', backup_key['key']['kid']),
                                                                                        JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', backup_identity['id']),
                                                                                        JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
                                                                                        JMESPathCheck('dataEncryption.geoBackupKeyUri', key['key']['kid']),
                                                                                        JMESPathCheck('dataEncryption.geoBackupUserAssignedIdentityId', identity['id'])
                                                                                    ]).get_output_in_json()
                self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), backup_location)

                self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, geo_backup_name))

            # delete all servers
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, replica_1_name))
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, backup_name))
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, primary_server_name))

        invalid_input_tests()
        main_tests(False)
        main_tests(True)

        # try to update key and identity in a server without data encryption
        self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --location {}'.format(
                resource_group,
                server_2_name,
                tier,
                sku_name,
                location
            ))
        
        self.cmd('postgres flexible-server update -g {} -n {} --key {} --identity {}'
                .format(
                resource_group,
                server_2_name,
                key['key']['kid'],
                identity['id']),
            expect_failure=True)

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, server_2_name))


    def _test_flexible_server_revivedropped_private_access_mgmt(self, database_engine, resource_group):

        private_dns_param = 'privateDnsZoneArmResourceId'
        location = self.postgres_location

        source_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        target_server_diff_vnet = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        source_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        source_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        new_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        new_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} --vnet {} --subnet {} -l {} --yes'.format(
                 database_engine, resource_group, source_server, source_vnet, source_subnet, location))
        result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, source_server)).get_output_in_json()

        # Wait until snapshot is created
        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = result['backup']['earliestRestoreDate']
        seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
        os.environ.get(ENV_LIVE_TEST, False) and sleep(max(0, seconds_to_wait) + 240)

        # Delete the server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, source_server), checks=NoneCheck())
        os.environ.get(ENV_LIVE_TEST, False) and sleep(240)

        # default vnet resources
        revive_dropped_server_1 = self.cmd('{} flexible-server revive-dropped -g {} --name {} --source-server {} --vnet {} --subnet {} -l {} --private-dns-zone {}'
                                  .format(database_engine, resource_group, target_server_default, source_server, source_vnet, source_subnet, location, result['network'][private_dns_param])).get_output_in_json()

        self.assertEqual(revive_dropped_server_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, source_vnet, source_subnet))
        self.assertEqual(revive_dropped_server_1['network'][private_dns_param],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, '{}.private.{}.database.azure.com'.format(source_server, database_engine)))

        # to different vnet and private dns zone
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes 172.1.0.0/16'.format(
                 resource_group, location, new_vnet))

        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes 172.1.0.0/24 --default-outbound false'.format(
                          resource_group, new_subnet, new_vnet)).get_output_in_json()

        private_dns_zone = '{}.private.{}.database.azure.com'.format(target_server_diff_vnet, database_engine)
        self.cmd('network private-dns zone create -g {} --name {}'.format(resource_group, private_dns_zone))

        revive_dropped_server_2 = self.cmd('{} flexible-server revive-dropped -l {} -g {} -n {} --source-server {} --subnet {} --private-dns-zone {}'.format(
                                  database_engine, location, resource_group, target_server_diff_vnet, source_server, subnet["id"], private_dns_zone)).get_output_in_json()

        self.assertEqual(revive_dropped_server_2['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, new_vnet, new_subnet))

        self.assertEqual(revive_dropped_server_2['network'][private_dns_param],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone))

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_default), checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, target_server_diff_vnet), checks=NoneCheck())


    def _test_flexible_server_revivedropped_mgmt(self, resource_group, vault_name, backup_vault_name=None):
        key_name = self.create_random_name('rdbmskey', 32)
        identity_name = self.create_random_name('identity', 32)
        backup_key_name = self.create_random_name('rdbmskey', 32)
        backup_identity_name = self.create_random_name('identity', 32)
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_with_geo_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        backup_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        backup_name_with_geo = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        tier = 'GeneralPurpose'
        sku_name = 'Standard_D2s_v3'
        location = self.postgres_location
        backup_location = self.postgres_backup_location

        key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                       .format(key_name, vault_name)).get_output_in_json()

        identity = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, identity_name, location)).get_output_in_json()

        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                 .format(resource_group, vault_name, identity['principalId']))

        backup_key = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                                  .format(backup_key_name, backup_vault_name)).get_output_in_json()

        backup_identity = self.cmd('identity create -g {} --name {} --location {}'.format(resource_group, backup_identity_name, backup_location)).get_output_in_json()

        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                    .format(resource_group, backup_vault_name, backup_identity['principalId']))
        
        def main_tests(geo_redundant_backup):
            geo_redundant_backup_enabled = 'Enabled' if geo_redundant_backup else 'Disabled'
            backup_key_id_flags = '--backup-key {} --backup-identity {}'.format(backup_key['key']['kid'], backup_identity['id']) if geo_redundant_backup else ''
            primary_server_name = server_with_geo_name if geo_redundant_backup else server_name
            # create primary flexible server with data encryption
            self.cmd('postgres flexible-server create -g {} -n {} --public-access none --tier {} --sku-name {} --key {} --identity {} {} --location {} --geo-redundant-backup {}'.format(
                        resource_group,
                        primary_server_name,
                        tier,
                        sku_name,
                        key['key']['kid'],
                        identity['id'],
                        backup_key_id_flags,
                        location,
                        geo_redundant_backup_enabled
                    ))

            main_checks = [
                JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity['id'])),
                JMESPathCheck('dataEncryption.primaryKeyUri', key['key']['kid']),
                JMESPathCheck('dataEncryption.primaryUserAssignedIdentityId', identity['id'])
            ]

            geo_checks = []
            if geo_redundant_backup:
                geo_checks = [
                    JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(backup_identity['id'])),
                    JMESPathCheck('dataEncryption.geoBackupKeyUri', backup_key['key']['kid']),
                    JMESPathCheck('dataEncryption.geoBackupUserAssignedIdentityId', backup_identity['id'])
                ]

            result = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, primary_server_name),
                    checks=main_checks + geo_checks).get_output_in_json()

            # Wait until snapshot is created
            current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
            earliest_restore_time = result['backup']['earliestRestoreDate']
            seconds_to_wait = (parser.isoparse(earliest_restore_time) - parser.isoparse(current_time)).total_seconds()
            os.environ.get(ENV_LIVE_TEST, False) and sleep(max(0, seconds_to_wait) + 240)

            # Delete the server
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, primary_server_name))
            os.environ.get(ENV_LIVE_TEST, False) and sleep(240)

            # By default, Geo-redundant backup is disabled for restore hence no need to pass backup-key and backup-identity
            # Revive Dropped server
            revive_dropped_server_1 = self.cmd('postgres \
                                               flexible-server {} \
                                               -l {} -g {} \
                                               --name {} \
                                               --source-server {} \
                                               --key {} --identity {}'.format(
                                                'revive-dropped',
                                                location,
                                                resource_group,
                                                backup_name,
                                                result['id'],
                                                key['key']['kid'],
                                                identity['id'],
                                        ), checks=main_checks).get_output_in_json()
            self.assertEqual(str(revive_dropped_server_1['location']).replace(' ', '').lower(), location)

            """ # Revive dropped server with geo-redundant backup enabled. Since operation is revive dropped, it has to be done in same location as the source server
            if geo_redundant_backup:
                # By default, Geo-redundant backup is disabled for restore hence explicitly need to set geo-redundant backup Enabled
                revive_dropped_server_2 = self.cmd('postgres \
                                                        flexible-server {} \
                                                        -g {} --name {} \
                                                        --source-server {} \
                                                        --geo-redundant-backup Enabled \
                                                        --key {} --identity {} \
                                                        {}'.format(
                                                        'revive-dropped --location {}'.format(location),
                                                        resource_group,
                                                        backup_name_with_geo,
                                                        result['id'],
                                                        key['key']['kid'],
                                                        identity['id'],
                                                        backup_key_id_flags
                                                    ), checks=main_checks + geo_checks).get_output_in_json()
                self.assertEqual(str(revive_dropped_server_2['location']).replace(' ', '').lower(), location)

                self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, backup_name_with_geo)) """

            # delete all servers
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, backup_name))
            self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, primary_server_name))

        main_tests(False)
        main_tests(True)



class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('postgres', resource_group, server)
        self._test_parameter_mgmt('postgres', resource_group, server)
        self._test_database_mgmt('postgres', resource_group, server)

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

    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_create_validator(self, resource_group):
        self._test_mgmt_create_validator('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_update_validator(self, resource_group):
        self._test_mgmt_update_validator('postgres', resource_group)

    def _test_mgmt_create_validator(self, database_engine, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 30
        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        ha_value = 'ZoneRedundant'

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

        invalid_storage_size = 60
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
        version = 16
        storage_size = 128
        location = self.postgres_location
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

        ha_value = 'ZoneRedundant'
        self.cmd('{} flexible-server update -g {} -n {} --high-availability {}'.format(
                 database_engine, resource_group, server_name, ha_value),
                 expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(
                 database_engine, resource_group, server_name), checks=NoneCheck())


class FlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('postgres', resource_group, True)
        self._test_flexible_server_replica_mgmt('postgres', resource_group, False)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_auto_grow_replica_validator(self, resource_group):
        self._test_flexible_server_replica_validator('postgres', resource_group, "Enabled")

    def _test_flexible_server_replica_validator(self, database_engine, resource_group, source_server_auto_grow):
        location = self.postgres_location
        primary_role = 'Primary'
        public_access_arg = ''
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none --tier GeneralPurpose --sku-name Standard_D2s_v3 --yes --storage-auto-grow {}'
                 .format(database_engine, resource_group, master_server, location, 256, source_server_auto_grow))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[
                              JMESPathCheck('replica.role', primary_role),
                              JMESPathCheck('storage.autoGrow', source_server_auto_grow)]).get_output_in_json()
        
        # test replica create
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --zone 2 {}'
                 .format(database_engine, resource_group, replicas[0], result['id'], public_access_arg),
                 expect_failure=True)
        
    def _test_flexible_server_replica_mgmt(self, database_engine, resource_group, vnet_enabled):
        location = self.postgres_location
        primary_role = 'Primary'
        replica_role = 'AsyncReplica'
        public_access_arg = ''
        public_access_check = []
        virtual_endpoint_name = self.create_random_name(F'virtual-endpoint', 32)
        read_write_endpoint_type = 'ReadWrite'
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(3)]

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
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} {} --tier GeneralPurpose --sku-name Standard_D2s_v3 --yes'
                 .format(database_engine, resource_group, master_server, location, 256, master_vnet_args))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replica.role', primary_role)] + master_vnet_check).get_output_in_json()
        
        # test replica create
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} --zone 2 {} {}'
                 .format(database_engine, resource_group, replicas[0], result['id'], replica_vnet_args[0], public_access_arg),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('replica.capacity', '0')] + replica_vnet_check[0] + public_access_check)
        
        # test storage auto-grow not allowed for replica server update
        self.cmd('{} flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(database_engine, resource_group, replicas[0]),
                 expect_failure=True)

        # test replica list
        self.cmd('{} flexible-server replica list -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test replica stop-replication
        self.cmd('{} flexible-server replica stop-replication -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replica.capacity', result['replica']['capacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None'),
                     JMESPathCheck('replica.capacity', result['replica']['capacity'])])

        # test delete master server
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {} {}'
                .format(database_engine, resource_group, replicas[1], result['id'], replica_vnet_args[1]),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('sku.name', result['sku']['name']),
                    JMESPathCheck('replica.role', replica_role),
                    JMESPathCheck('sourceServerResourceId', result['id']),
                    JMESPathCheck('replica.capacity', '0')] + replica_vnet_check[1])

        # in postgres we can't delete master server if it has replicas
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                    .format(database_engine, resource_group, master_server),
                    expect_failure=True)

        # test virtual-endpoint
        if not vnet_enabled:
            self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                    .format(database_engine, resource_group, replicas[2], result['id']),
                    checks=[
                        JMESPathCheck('name', replicas[2]),
                        JMESPathCheck('replica.role', replica_role),
                        JMESPathCheck('sourceServerResourceId', result['id'])])

            # test virtual-endpoint create
            self.cmd('{} flexible-server virtual-endpoint create -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                    .format(database_engine, resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, master_server),
                    checks=[
                        JMESPathCheck('endpointType', read_write_endpoint_type),
                        JMESPathCheck('name', virtual_endpoint_name),
                        JMESPathCheck('length(virtualEndpoints)', 2)])

            # test virtual-endpoint update
            update_result = self.cmd('{} flexible-server virtual-endpoint update -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                    .format(database_engine, resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, replicas[2]),
                    checks=[JMESPathCheck('length(members)', 2)]).get_output_in_json()

            # test virtual-endpoint show
            self.cmd('{} flexible-server virtual-endpoint show -g {} --server-name {} --name {}'
                    .format(database_engine, resource_group, master_server, virtual_endpoint_name),
                    checks=[JMESPathCheck('members', update_result['members'])])

            # test replica switchover planned
            switchover_result = self.cmd('{} flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option planned --yes'
                    .format(database_engine, resource_group, replicas[2]),
                    checks=[
                        JMESPathCheck('name', replicas[2]),
                        JMESPathCheck('replica.role', primary_role),
                        JMESPathCheck('sourceServerResourceId', 'None'),
                        JMESPathCheck('replica.capacity', result['replica']['capacity'])]).get_output_in_json()

            # test show server with replication info, master became replica server
            self.cmd('{} flexible-server show -g {} --name {}'
                    .format(database_engine, resource_group, master_server),
                    checks=[
                        JMESPathCheck('replica.role',replica_role),
                        JMESPathCheck('sourceServerResourceId', switchover_result['id']),
                        JMESPathCheck('replica.capacity', '0')])

            # test replica switchover forced
            self.cmd('{} flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option forced --yes'
                    .format(database_engine, resource_group, master_server),
                    checks=[
                        JMESPathCheck('name', master_server),
                        JMESPathCheck('replica.role', primary_role),
                        JMESPathCheck('sourceServerResourceId', 'None'),
                        JMESPathCheck('replica.capacity', result['replica']['capacity'])])

            # test promote replica standalone forced
            self.cmd('{} flexible-server replica promote -g {} --name {} --promote-mode standalone --promote-option forced --yes'
                    .format(database_engine, resource_group, replicas[2]),
                    checks=[
                        JMESPathCheck('name',replicas[2]),
                        JMESPathCheck('replica.role', primary_role),
                        JMESPathCheck('sourceServerResourceId', 'None'),
                        JMESPathCheck('replica.capacity', result['replica']['capacity'])])

            # test virtual-endpoint delete
            self.cmd('{} flexible-server virtual-endpoint delete -g {} --server-name {} --name {} --yes'
                    .format(database_engine, resource_group, master_server, virtual_endpoint_name))

            # test virtual-endpoint list
            self.cmd('{} flexible-server virtual-endpoint list -g {} --server-name {}'
                    .format(database_engine, resource_group, master_server),
                    checks=[JMESPathCheck('length(@)', 0)])

            # delete standalone server
            self.cmd('{} flexible-server delete -g {} --name {} --yes'
                        .format(database_engine, resource_group, replicas[2]))


        # delete replica server first
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                    .format(database_engine, resource_group, replicas[1]))

        # now we can delete master server
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                    .format(database_engine, resource_group, master_server))

        # clean up servers
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())


class FlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('postgres', resource_group_1, resource_group_2)

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
            self.cmd('config param-persist off')

        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"

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
            self.cmd('config param-persist off')

        vnet_name = 'clitestvnet3'
        subnet_name = 'clitestsubnet3'
        vnet_name_2 = 'clitestvnet4'
        address_prefix = '13.0.0.0/16'
        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"

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
            self.cmd('config param-persist off')

        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"
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
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1, subnet_name, vnet_name))
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
        self.cmd('network vnet subnet create -g {} -n {} --address-prefixes {} --vnet-name {} --default-outbound false'.format(
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
                 resource_group, 'westus', vnet_name), # location of vnet and server are different
                 expect_failure=True)

        # delegated to different service
        subnet = self.cmd('network vnet subnet create -g {} -n {} --vnet-name {} --address-prefixes {} --delegations {} --default-outbound false'.format(
                          resource_group, subnet_name, vnet_name, subnet_prefix, "Microsoft.DBforMySQL/flexibleServers")).get_output_in_json()

        self.cmd('postgres flexible-server create -g {} -l {} --subnet {} --yes'.format(
                 resource_group, 'eastus', subnet["id"]), # Delegated to different service
                 expect_failure=True)


class FlexibleServerPrivateDnsZoneScenarioTest(ScenarioTest):
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    def test_postgres_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        self._test_flexible_server_existing_private_dns_zone('postgres', server_resource_group, vnet_resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='dns_resource_group')
    def test_postgres_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        self._test_flexible_server_new_private_dns_zone('postgres', server_resource_group, vnet_resource_group, dns_resource_group)


    def _test_flexible_server_existing_private_dns_zone(self, database_engine, server_resource_group, vnet_resource_group):
        server_names = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        location = self.postgres_location
        delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
        private_dns_zone_key = "privateDnsZoneArmResourceId"
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
        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"
        db_context = PostgresDbContext(cmd=self,
                                           cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
                                           command_group='postgres')

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
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[0], None, server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_names[0] + ".private." + database_engine + ".database.azure.com"))

        # no input, vnet in vnet rg
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[1], None, vnet_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, server_names[1] + ".private." + database_engine + ".database.azure.com"))

        # new private dns zone, zone name (vnet in same rg)
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[2], private_dns_zone_names[0],
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)


    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location

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
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_upgrade_mgmt(self, resource_group):
        self._test_flexible_server_upgrade_mgmt('postgres', resource_group, False)
        self._test_flexible_server_upgrade_mgmt('postgres', resource_group, True)

    
    def _test_flexible_server_upgrade_mgmt(self, database_engine, resource_group, public_access):
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        current_version = '13'
        new_version = '16'
        location = self.postgres_location

        create_command = '{} flexible-server create -g {} -n {} --tier GeneralPurpose --sku-name {} --location {} --version {} --yes'.format(
            database_engine, resource_group, server_name, "Standard_D2s_v3", location, current_version)
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

        # should fail because we can't upgrade replica
        self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, replica_name, new_version),
                    expect_failure=True)

        # should fail because we can't upgrade primary server with existing replicas
        self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, server_name, new_version),
                    expect_failure=True)

        # delete replica
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, replica_name))

        # upgrade primary server
        result = self.cmd('{} flexible-server upgrade -g {} -n {} --version {} --yes'.format(database_engine, resource_group, server_name, new_version)).get_output_in_json()
        self.assertTrue(result['version'].startswith(new_version))


class FlexibleServerBackupsMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_backups_mgmt(self, resource_group, server):
        self._test_backups_mgmt('postgres', resource_group, server)


    def _test_backups_mgmt(self, database_engine, resource_group, server):
        attempts = 0
        while attempts < 10:
            backups = self.cmd('{} flexible-server backup list -g {} -n {}'
                            .format(database_engine, resource_group, server)).get_output_in_json()
            attempts += 1
            if len(backups) > 0:
                break
            os.environ.get(ENV_LIVE_TEST, False) and sleep(60)

        self.assertTrue(len(backups) == 1)

        automatic_backup = self.cmd('{} flexible-server backup show -g {} -n {} --backup-name {}'
                                    .format(database_engine, resource_group, server, backups[0]['name'])).get_output_in_json()

        self.assertDictEqual(automatic_backup, backups[0])


class FlexibleServerIdentityAADAdminMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgresql_flexible_server_identity_aad_admin_mgmt(self, resource_group):
        self._test_identity_aad_admin_mgmt('postgres', resource_group, 'enabled')

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgresql_flexible_server_identity_aad_admin_only_mgmt(self, resource_group):
        self._test_identity_aad_admin_mgmt('postgres', resource_group, 'disabled')

    def _test_identity_aad_admin_mgmt(self, database_engine, resource_group, password_auth, location=postgres_location):
        login = 'alanenriqueo@microsoft.com'
        sid = '894ef8da-7971-4f68-972c-f561441eb329'
        auth_args = '--password-auth {} --active-directory-auth enabled'.format(password_auth)
        admin_id_arg = '-i {}'.format(sid) if database_engine == 'postgres' else ''
        server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        replica = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) for _ in range(2)]

        # create server
        self.cmd('{} flexible-server create --location {} -g {} -n {} --public-access none --tier {} --sku-name {} {}'
                 .format(database_engine, location, resource_group, server, 'GeneralPurpose', 'Standard_D2s_v3', auth_args))

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

        if database_engine == 'postgres':
            # assign identity 1 to replica 1
            self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                     .format(database_engine, resource_group, replica[0], identity_id[0]))

        self.cmd('{} flexible-server identity list -g {} -s {}'
                 .format(database_engine, resource_group, replica[0]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        admins = self.cmd('{} flexible-server ad-admin list -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(0, len(admins))

        # add identity 1 to replica 1
        self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                    .format(database_engine, resource_group, replica[0], identity_id[0]),
                    checks=[
                        JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0]))])

        # add identity 2 to replica 1 and primary server
        for server_name in [replica[0], server]:
            self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                        .format(database_engine, resource_group, server_name, identity_id[1]),
                        checks=[
                            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        # try to add AAD admin to replica 1
        self.cmd('{} flexible-server ad-admin create -g {} -s {} -u {} -i {}'
                    .format(database_engine, resource_group, replica[0], login, sid),
                    expect_failure=True)
        
        # add AAD admin to primary server
        admin_checks = [JMESPathCheck('principalType', 'User'),
                        JMESPathCheck('principalName', login),
                        JMESPathCheck('objectId', sid)]

        self.cmd('{} flexible-server ad-admin create -g {} -s {} -u {} -i {}'
                    .format(database_engine, resource_group, server, login, sid))

        for server_name in [server, replica[0]]:
            self.cmd('{} flexible-server ad-admin show -g {} -s {} {}'
                    .format(database_engine, resource_group, server_name, admin_id_arg),
                    checks=admin_checks)

            self.cmd('{} flexible-server identity list -g {} -s {}'
                    .format(database_engine, resource_group, server_name),
                    checks=[
                        JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                        JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        # create replica 2
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replica[1], server))

        if database_engine == 'postgres':
            # assign identities 1 and 2 to replica 2
            self.cmd('{} flexible-server identity assign -g {} -s {} -n {} {}'
                     .format(database_engine, resource_group, replica[1], identity_id[0], identity_id[1]))

        self.cmd('{} flexible-server identity list -g {} -s {}'
                 .format(database_engine, resource_group, replica[1]),
                 checks=[
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                     JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[1]))])

        self.cmd('{} flexible-server ad-admin show -g {} -s {} {}'
                    .format(database_engine, resource_group, replica[1], admin_id_arg),
                    checks=admin_checks)

        # verify that authConfig.activeDirectoryAuth=enabled and authConfig.passwordAuth=disabled in primary server and all replicas
        for server_name in [server, replica[0], replica[1]]:
            list_checks = [JMESPathCheck('authConfig.activeDirectoryAuth', 'enabled', False),
                        JMESPathCheck('authConfig.passwordAuth', password_auth, False)]
            self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name), checks=list_checks)

        # try to remove AAD admin from replica 2
        self.cmd('{} flexible-server ad-admin delete -g {} -s {} {} --yes'
                 .format(database_engine, resource_group, replica[1], admin_id_arg),
                 expect_failure=True)

        # remove AAD admin from primary server
        self.cmd('{} flexible-server ad-admin delete -g {} -s {} {} --yes'
                 .format(database_engine, resource_group, server, admin_id_arg))

        for server_name in [server, replica[0], replica[1]]:
            admins = self.cmd('{} flexible-server ad-admin list -g {} -s {}'
                              .format(database_engine, resource_group, server_name)).get_output_in_json()
            self.assertEqual(0, len(admins))

        # add identity 3 to primary server
        self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                 .format(database_engine, resource_group, server, identity_id[2]))
        if database_engine == 'postgres':
            # add identity 3 to replica 1 and 2
            for server_name in [replica[0], replica[1]]:
                self.cmd('{} flexible-server identity assign -g {} -s {} -n {}'
                         .format(database_engine, resource_group, server_name, identity_id[2]))

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
        if database_engine == 'postgres':
            # remove identities 1 and 2 from replica 1 and 2
            for server_name in [replica[0], replica[1]]:
                self.cmd('{} flexible-server identity remove -g {} -s {} -n {} {} --yes'
                         .format(database_engine, resource_group, server_name, identity_id[0], identity_id[1]))

        for server_name in [server, replica[0], replica[1]]:
            self.cmd('{} flexible-server identity list -g {} -s {}'
                     .format(database_engine, resource_group, server_name),
                     checks=[
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[0])),
                         JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity_id[1])),
                         JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id[2]))])

        # delete everything
        for server_name in [replica[0], replica[1], server]:
            self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))


class FlexibleServerAdvancedThreatProtectionSettingMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_advanced_threat_protection_setting_mgmt(self, resource_group):
        self._test_advanced_threat_protection_setting_mgmt('postgres', resource_group)


    def _test_advanced_threat_protection_setting_mgmt(self, database_engine, resource_group):
        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, 32)

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none '
                 '--tier GeneralPurpose --sku-name Standard_D2s_v3 --yes'
                 .format(database_engine, resource_group, server_name, location, 128))
        
        # show advanced threat protection setting for server
        self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('state', "Disabled")]).get_output_in_json()
        
        # Enable advanced threat protection setting for server
        self.cmd('{} flexible-server advanced-threat-protection-setting update -g {} --server-name {} --state Enabled'
                    .format(database_engine, resource_group, server_name))

        os.environ.get(ENV_LIVE_TEST, False) and sleep(2 * 60)
        
        # show advanced threat protection setting for server
        self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('state', "Enabled")]).get_output_in_json()
        
        # Disable advanced threat protection setting for server
        self.cmd('{} flexible-server advanced-threat-protection-setting update -g {} --server-name {} --state Disabled'
                    .format(database_engine, resource_group, server_name))

        os.environ.get(ENV_LIVE_TEST, False) and sleep(2 * 60)

        # show advanced threat protection setting for server
        self.cmd('{} flexible-server advanced-threat-protection-setting show -g {} --server-name {} '
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('state', "Disabled")]).get_output_in_json()

        # delete everything
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))


class FlexibleServerLogsMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_logs_mgmt(self, resource_group):
        self._test_server_logs_mgmt('postgres', resource_group)


    def _test_server_logs_mgmt(self, database_engine, resource_group):
        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, 32)

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none '
                 '--tier GeneralPurpose --sku-name Standard_D2s_v3 --yes'
                 .format(database_engine, resource_group, server_name, location, 128))
        
        # enable server logs for server
        self.cmd('{} flexible-server parameter set -g {} --server-name {} --name logfiles.download_enable --value on'
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('value', "on"),
                            JMESPathCheck('name', "logfiles.download_enable")]).get_output_in_json()
        
        # set retention period for server logs for server
        self.cmd('{} flexible-server parameter set -g {} --server-name {} --name logfiles.retention_days --value 1'
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('value', "1"),
                            JMESPathCheck('name', "logfiles.retention_days")]).get_output_in_json()

        if os.environ.get(ENV_LIVE_TEST, True):
            return

        # wait for around 30 min to allow log files to be generated
        sleep(30*60)

        # list server log files
        server_log_files = self.cmd('{} flexible-server server-logs list -g {} --server-name {} '
                                    .format(database_engine, resource_group, server_name)).get_output_in_json()
        
        self.assertGreater(len(server_log_files), 0, "Server logFiles are not yet created")
        
        # download server log files
        self.cmd('{} flexible-server server-logs download -g {} --server-name {} --name {}'
                    .format(database_engine, resource_group, server_name, server_log_files[0]['name']),
                    checks=NoneCheck())
        
        # disable server logs for server
        self.cmd('{} flexible-server parameter set -g {} --server-name {} --name logfiles.download_enable --value off'
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('value', "off"),
                            JMESPathCheck('name', "logfiles.download_enable")]).get_output_in_json()

        # delete everything
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name))



class FlexibleServerPrivateEndpointsMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_private_endpoint_mgmt(self, resource_group, server):
        self._test_private_endpoint_connection('postgres', resource_group, server)
        self._test_private_link_resource('postgres', resource_group, server, 'postgresqlServer')

    def _test_private_endpoint_connection(self, database_engine, resource_group, server_name):
        loc = self.postgres_location
        vnet = self.create_random_name('cli-vnet-', 24)
        subnet = self.create_random_name('cli-subnet-', 24)
        pe_name_auto = self.create_random_name('cli-pe-', 24)
        pe_name_manual_approve = self.create_random_name('cli-pe-', 24)
        pe_name_manual_reject = self.create_random_name('cli-pe-', 24)
        pe_connection_name_auto = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_approve = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_reject = self.create_random_name('cli-pec-', 24)

        result = self.cmd('{} flexible-server show -n {} -g {}'.format(database_engine, server_name, resource_group),
                               checks=[JMESPathCheck('resourceGroup', resource_group),
                                       JMESPathCheck('name', server_name)]).get_output_in_json()
        self.assertEqual(''.join(result['location'].lower().split()), self.postgres_location)

        # Prepare network and disable network policies
        self.cmd('network vnet create -n {} -g {} -l {} --subnet-name {}'
                 .format(vnet, resource_group, loc, subnet),
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {} --vnet-name {} -g {} '
                 '--disable-private-endpoint-network-policies true'
                 .format(subnet, vnet, resource_group),
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Get Server Id and Group Id
        result = self.cmd('{} flexible-server show -g {} -n {}'
                          .format(database_engine, resource_group, server_name)).get_output_in_json()
        server_id = result['id']
        group_id = 'postgresqlServer'

        approval_description = 'You are approved!'
        rejection_description = 'You are rejected!'

        # Testing Auto-Approval workflow
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {}'
                                    .format(resource_group, pe_name_auto, vnet, subnet, loc, pe_connection_name_auto,
                                            server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_auto)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], pe_connection_name_auto)
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} flexible-server show -g {} -n {}'
                          .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Approved')
                 ])
        
        self.cmd('{} flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server_name, resource_group, server_pec_name, approval_description))

        self.cmd('{} flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server_name, resource_group, server_pec_name, rejection_description))

        self.cmd('{} flexible-server private-endpoint-connection delete --server-name {} -g {} --id {}'
                 .format(database_engine, server_name, resource_group, server_pec_id))

        # Testing Manual-Approval workflow [Approval]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request'
                                    .format(resource_group, pe_name_manual_approve, vnet, subnet, loc,
                                            pe_connection_name_manual_approve, server_id,
                                            group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_approve)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_approve)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} flexible-server show -g {} -n {}'
                          .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('{} flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                 .format(database_engine, server_name, resource_group, server_pec_name, approval_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', approval_description),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('{} flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server_name, resource_group, server_pec_name, rejection_description))

        self.cmd('{} flexible-server private-endpoint-connection delete --server-name {} -g {}  --id {}'
                 .format(database_engine, server_name, resource_group, server_pec_id))

        # Testing Manual-Approval workflow [Rejection]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request true'
                                    .format(resource_group, pe_name_manual_reject, vnet, subnet, loc,
                                            pe_connection_name_manual_reject, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_reject)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_reject)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} flexible-server show -g {} -n {}'
                          .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} flexible-server private-endpoint-connection list -g {} --server-name {}'.format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 1)])

        self.cmd('{} flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('{} flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                 .format(database_engine, server_name, resource_group, server_pec_name, rejection_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', rejection_description),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('{} flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server_name, resource_group, server_pec_name, approval_description), expect_failure=True)

        self.cmd('{} flexible-server private-endpoint-connection delete --server-name {} -g {}  --id {}'
                 .format(database_engine, server_name, resource_group, server_pec_id))
        result = self.cmd('{} flexible-server show -g {} -n {}'
                          .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 0)

    def _test_private_link_resource(self, database_engine, resource_group, server, group_id):
        result = self.cmd('{} flexible-server private-link-resource list -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(result[0]['groupId'], group_id)

        result = self.cmd('{} flexible-server private-link-resource show -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(result['groupId'], group_id)
