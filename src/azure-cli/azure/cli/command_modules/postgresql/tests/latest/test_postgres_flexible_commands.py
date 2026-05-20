# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os

from time import sleep
from knack.util import CLIError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH

class PostgreSQLFlexibleServerMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt(resource_group)

    def _test_flexible_server_mgmt(self, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        version = '17'
        storage_size = 128
        location = self.postgres_location
        sku_name = 'Standard_D4ads_v5'
        memory_optimized_sku = 'Standard_E4ds_v5'
        tier = 'GeneralPurpose'
        backup_retention = 7
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        zonal_resiliency_value = 'Enabled'
        ha_value = 'ZoneRedundant'

        # List SKUs
        self.cmd('postgres flexible-server list-skus -l {}'.format(location),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Create server
        self.cmd('postgres flexible-server create -g {} -n {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --zonal-resiliency {} --location {}\
                  --public-access None'.format(resource_group, server_name, backup_retention,
                                               sku_name, tier, storage_size, 'dbadmin', version, zonal_resiliency_value, location))

        # Validate several properties of the server
        basic_info = self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(basic_info['name'], server_name)
        self.assertEqual(str(basic_info['location']).replace(' ', '').lower(), location)
        self.assertEqual(basic_info['resourceGroup'], resource_group)
        self.assertEqual(basic_info['sku']['name'], sku_name)
        self.assertEqual(basic_info['sku']['tier'], tier)
        self.assertEqual(basic_info['version'], version)
        self.assertEqual(basic_info['storage']['storageSizeGb'], storage_size)
        self.assertEqual(basic_info['backup']['backupRetentionDays'], backup_retention)
        self.assertEqual(basic_info['highAvailability']['mode'], ha_value)

        # List servers
        self.cmd('postgres flexible-server list -g {}'.format(resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # Show connection string
        connection_string = self.cmd('postgres flexible-server show-connection-string -s {}'
                                     .format(server_name)).get_output_in_json()
        self.assertIn('jdbc', connection_string['connectionStrings'])
        self.assertIn('node.js', connection_string['connectionStrings'])
        self.assertIn('php', connection_string['connectionStrings'])
        self.assertIn('python', connection_string['connectionStrings'])
        self.assertIn('ado.net', connection_string['connectionStrings'])

        # Update password
        self.cmd('postgres flexible-server update -g {} -n {} -p randompw321##@!'
                 .format(resource_group, server_name))

        # Update compute and storage
        self.cmd('postgres flexible-server update -g {} -n {} --storage-size 256 --yes'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 256 )])

        self.cmd('postgres flexible-server update -g {} -n {} --storage-auto-grow Enabled'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.autoGrow', "Enabled" )])

        self.cmd('postgres flexible-server update -g {} -n {} --storage-auto-grow Disabled'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('storage.autoGrow', "Disabled" )])

        performance_tier = 'P15'
        performance_tier_lower = performance_tier.lower()

        self.cmd('postgres flexible-server update -g {} -n {} --performance-tier {}'
                 .format(resource_group, server_name, performance_tier_lower),
                 checks=[JMESPathCheck('storage.tier', performance_tier)])

        tier = 'MemoryOptimized'
        sku_name = memory_optimized_sku
        self.cmd('postgres flexible-server update -g {} -n {} --tier {} --sku-name {} --yes'
                 .format(resource_group, server_name, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

        # Update backup retention
        self.cmd('postgres flexible-server update -g {} -n {} --backup-retention {}'
                 .format(resource_group, server_name, backup_retention + 10),
                 checks=[JMESPathCheck('backup.backupRetentionDays', backup_retention + 10)])
        
        # Update maintenance window
        maintainence_window = 'SUN'
        maintainence_window_value = 0   # Sunday is defined as 0
        
        self.cmd('postgres flexible-server update -g {} -n {} --maintenance-window {}'
                 .format(resource_group, server_name, maintainence_window),
                 checks=[JMESPathCheck('maintenanceWindow.dayOfWeek', maintainence_window_value)])

        # Update tags
        self.cmd('postgres flexible-server update -g {} -n {} --tags keys=3'
                 .format(resource_group, server_name),
                 checks=[JMESPathCheck('tags.keys', '3')])

        # Restart, stop, start server
        self.cmd('postgres flexible-server restart -g {} -n {}'
                 .format(resource_group, server_name), checks=NoneCheck())

        self.cmd('postgres flexible-server stop -g {} -n {}'
                 .format(resource_group, server_name), checks=NoneCheck())

        self.cmd('postgres flexible-server start -g {} -n {}'
                 .format(resource_group, server_name), checks=NoneCheck())
        
        # Negative tests
        replica_1_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('postgres flexible-server replica create -g "" --name {} --source-server {}'.format(
                        replica_1_name,
                        server_name
            ), expect_failure=True)
        self.cmd('postgres flexible-server replica create -g \'\' --name {} --source-server {}'.format(
                        replica_1_name,
                        server_name
            ), expect_failure=True)
        self.cmd('postgres flexible-server update -g "" -n {} -p randompw321##@!'
                 .format(server_name), expect_failure=True)
        self.cmd('postgres flexible-server update -g \'\' -n {} -p randompw321##@!'
                 .format(server_name), expect_failure=True)

        # Delete server
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, server_name), checks=NoneCheck())
        os.environ.get(ENV_LIVE_TEST, False) and sleep(300)

        # Revive dropped server
        revived_server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        source_server_id = basic_info['id']
        revive_dropped_server = self.cmd('postgres flexible-server revive-dropped -g {} -n {} --source-server {} --location {}'.format(
                                         resource_group, revived_server_name, source_server_id, location)).get_output_in_json()
        self.assertEqual(revive_dropped_server['name'], revived_server_name)


class PostgreSQLFlexibleServerValidatorScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_create_validator(self, resource_group):
        self._test_mgmt_create_validator(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_update_validator(self, resource_group):
        self._test_mgmt_update_validator(resource_group)

    def _test_mgmt_create_validator(self, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 15
        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 40
        ha_value = 'ZoneRedundant'
        valid_vnet_name = self.create_random_name('vnet', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_vnet_name = self.create_random_name('vnet(/?\\)', RANDOM_VARIABLE_MAX_LENGTH)
        valid_subnet_name = self.create_random_name('subnet', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_subnet_name = self.create_random_name('subnet(/?\\)', RANDOM_VARIABLE_MAX_LENGTH)
        valid_vnet_identifier = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resource-group/providers/Microsoft.Network/virtualNetworks/{}'.format(valid_vnet_name)
        invalid_vnet_identifier = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resource-group/providers/Microsoft.Network/virtualNetworks/{}'.format(invalid_vnet_name)
        valid_subnet_identifier = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resource-group/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(valid_vnet_name, valid_subnet_name)
        invalid_subnet_identifier = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resource-group/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(invalid_vnet_name, invalid_subnet_name)
        valid_private_dns_zone = '{}.private.postgres.database.azure.com'.format(server_name)
        invalid_private_dns_zones = ['{}.postgres.database.azure.com'.format(server_name), 'invalidprivate.dns.zone', '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/resource-group/providers/Microsoft.Network/privateDnsZones/{}.invalid(/?\\)segment.postgres.database.azure.com'.format(server_name)]

        # Create server with invalid server name.
        self.cmd('postgres flexible-server create -g {} -n Wrongserver.Name -l {}'.format(
                resource_group, location),
                expect_failure=True)

        # Create server with invalid tier.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier {}'.format(
                 resource_group, server_name, location, invalid_tier),
                 expect_failure=True)

        # Create server with invalid version.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --version {}'.format(
                 resource_group, server_name, location, invalid_version),
                 expect_failure=True)

        # Create server with invalid SKU name.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier {} --sku-name {}'.format(
                 resource_group, server_name, location, valid_tier, invalid_sku_name),
                 expect_failure=True)

        # Create server with invalid backup retention days.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --backup-retention {}'.format(
                 resource_group, server_name, location, invalid_backup_retention),
                 expect_failure=True)

        # Create server with zone redundant high availability in a location that does not support it, because it's a single zone location.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --high-availability {} '.format(
                 resource_group, server_name, location, ha_value),
                 expect_failure=True)

        # Create server with zone redundant high availability with a tier that does not support it.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier Burstable --sku-name Standard_B1ms --high-availability {}'.format(
                 resource_group, server_name, location, ha_value),
                 expect_failure=True)

        # Create server with zone redundant high availability in a location that does not support it, because it's a single zone location.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier GeneralPurpose --sku-name Standard_D4ds_v4 --high-availability {}'.format(
                 resource_group, server_name, location, ha_value),
                 expect_failure=True)

        # Create server with zone redundant high availability and forcing same zone for primary and standby.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier GeneralPurpose --sku-name Standard_D2ads_v5 --high-availability {} --zone 1 --standby-zone 1'.format(
                 resource_group, server_name, location, ha_value),
                 expect_failure=True)

        # Create server with private network arguments but without a private DNS zone.
        with self.assertRaisesRegex(CLIError, "When --vnet or --subnet is provided, --private-dns-zone is required."):
            self.cmd(
                'postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {}'.format(
                    resource_group, server_name, location, valid_vnet_name, valid_subnet_name))
        
        # Create server with public access, virtual network name, and subnet name at the same time.
        with self.assertRaisesRegex(CLIError, "The --subnet and --public-access arguments cannot be used together. Use only one of them."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --public-access All'.format(
                    resource_group, server_name, location, valid_vnet_name, valid_subnet_name))

        # Create server with an incorrectly formed virtual network identifier.
        with self.assertRaisesRegex(CLIError, "Specify either --subnet as a subnet resource identifier, --vnet as a vnet resource identifier with --subnet as a subnet name, or both --vnet and --subnet as resource names."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, invalid_vnet_identifier, valid_subnet_name, valid_private_dns_zone))

        # Create server with an incorrectly formed subnet name.
        with self.assertRaisesRegex(CLIError, "Specify either --subnet as a subnet resource identifier, --vnet as a vnet resource identifier with --subnet as a subnet name, or both --vnet and --subnet as resource names."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_vnet_name, invalid_subnet_name, valid_private_dns_zone))

        # Create server with an incorrectly formed virtual network name.
        with self.assertRaisesRegex(CLIError, "Specify either --subnet as a subnet resource identifier, --vnet as a vnet resource identifier with --subnet as a subnet name, or both --vnet and --subnet as resource names."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, invalid_vnet_name, valid_subnet_name, valid_private_dns_zone))

        # Create server with the resource identifier of a virtual network and the resource identifier of a subnet at the same time.
        with self.assertRaisesRegex(CLIError, "If you pass --vnet as a resource identifier, --subnet must be a subnet name."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_vnet_identifier, valid_subnet_identifier, valid_private_dns_zone))

        # Create server with the resource identifier of a subnet, and the name of a virtual network at the same time.
        with self.assertRaisesRegex(CLIError, "Specify either --subnet as a subnet resource identifier, --vnet as a vnet resource identifier with --subnet as a subnet name, or both --vnet and --subnet as resource names."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_vnet_name, valid_subnet_identifier, valid_private_dns_zone))

        # Create server with a private DNS zone, but without virtual network and subnet.
        with self.assertRaisesRegex(CLIError, "Private DNS zone can only be used with private access network. Use --vnet or/and --subnet parameters."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_private_dns_zone))

        # Create server with a private DNS zone and a virtual network name, but without a subnet name.
        with self.assertRaisesRegex(CLIError, "When --vnet is provided, --subnet must also be provided in the form of subnet name."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_vnet_name, valid_private_dns_zone))

        # Create server with a private DNS zone and a subnet name, but without a virtual network.
        with self.assertRaisesRegex(CLIError, "Incorrectly formed subnet identifier. If you are providing only --subnet but not --vnet, the --subnet parameter should be in resource identifier format."):
            self.cmd('postgres flexible-server create -g {} -n {} -l {} --subnet {} --private-dns-zone {}'.format(
                    resource_group, server_name, location, valid_subnet_name, valid_private_dns_zone))

        # Create server with multiple forms of invalid private DNS zones.
        messages = [
            "The private DNS zone name cannot be the same as the server's fully qualified domain name.",
            "The suffix of the private DNS zone should be '.postgres.database.azure.com'.",
            "The private DNS zone name or identifier is not in a valid format."
        ]
        for invalid_private_dns_zone in invalid_private_dns_zones:
            with self.assertRaisesRegex(CLIError, messages[invalid_private_dns_zones.index(invalid_private_dns_zone)]):
                self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --subnet {} --private-dns-zone {}'.format(
                        resource_group, server_name, location, valid_vnet_name, valid_subnet_name, invalid_private_dns_zone))

        # Create server with invalid public access value (end-ip is not a valid IPv4 address).
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --public-access 12.0.0.0-10.0.0.0.0'.format(
                 resource_group, server_name, location),
                 expect_failure=True)

        # Create server with invalid public access value (start-ip greater than end-ip).
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --public-access 12.0.0.0-10.0.0.0'.format(
                 resource_group, server_name, location),
                 expect_failure=True)

        # Create server with invalid storage size (in Premium_LRS, valid storage sizes are 32, 64, 128, 256, 512, 1024, 2048, 4095, 4096, 8192, 16384, 32768, 65536).
        invalid_storage_size = 60
        self.cmd('postgres flexible-server create -g {} -l {} --storage-size {} --public-access none'.format(
                 resource_group, location, invalid_storage_size),
                 expect_failure=True)

    def _test_mgmt_update_validator(self, resource_group):
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

        self.cmd('postgres flexible-server create -g {} -n {} -l {} --tier {} --version {} --sku-name {} --storage-size {} --backup-retention {} --public-access none'
                 .format(resource_group, server_name, location, tier, version, sku_name, storage_size, backup_retention))
        self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name), checks=list_checks)

        # Update server with invalid tier for current sku
        invalid_tier = 'GeneralPurpose'
        self.cmd('postgres flexible-server update -g {} -n {} --tier {}'.format(
                 resource_group, server_name, invalid_tier),
                 expect_failure=True)

        # Update server with invalid sku for the given tier
        self.cmd('postgres flexible-server update -g {} -n {} --tier {} --sku-name {}'.format(
                 resource_group, server_name, valid_tier, invalid_sku_name),
                 expect_failure=True)

        # Update server with smaller than current storage size
        invalid_storage_size = 64
        self.cmd('postgres flexible-server update -g {} -n {} --storage-size {}'.format(
                 resource_group, server_name, invalid_storage_size),
                 expect_failure=True)

        # Update server with invalid backup retention days
        self.cmd('postgres flexible-server update -g {} -n {} --backup-retention {}'.format(
                 resource_group, server_name, invalid_backup_retention),
                 expect_failure=True)

        # Update server with high availability on a tier that does not support it
        ha_value = 'ZoneRedundant'
        self.cmd('postgres flexible-server update -g {} -n {} --high-availability {}'.format(
                 resource_group, server_name, ha_value),
                 expect_failure=True)

        # Delete server
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, server_name), checks=NoneCheck())
