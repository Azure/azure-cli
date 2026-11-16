# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch

from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.postgresql.commands import custom_commands
from azure.cli.command_modules.postgresql.utils import validators
from azure.mgmt.postgresqlflexibleservers.models import Server


class StorageAutoGrowTest(unittest.TestCase):

    def setUp(self):
        self.cmd = MagicMock()
        self.client = MagicMock()
        capabilities = {
            'sku_info': {
                'GeneralPurpose': {
                    'skus': ['Standard_D2ds_v4'],
                    'storage_sizes': [128, 256, 512],
                    'supported_storageV2_size': 6,
                    'supported_storageV2_size_max': 65536,
                    'supported_storageV2_iops': 3000,
                    'supported_storageV2_iops_max': 80000,
                    'supported_storageV2_throughput': 125,
                    'supported_storageV2_throughput_max': 1200,
                },
            },
            'single_az': False,
            'geo_backup_supported': True,
            'server_versions': ['16'],
        }
        patches = [
            patch.object(custom_commands, 'get_postgres_location_capability_info', return_value=capabilities),
            patch.object(custom_commands, 'get_postgres_server_capability_info', return_value=capabilities),
            patch.object(custom_commands, 'generate_missing_parameters',
                         return_value=('eastus', 'test-rg', 'test-server')),
            patch.object(custom_commands, 'build_network_configuration', return_value=(None, -1, -1)),
            patch.object(custom_commands, 'resolve_poller', return_value=self._server()),
            patch.object(custom_commands, '_update_local_contexts'),
            patch.object(validators, 'validate_server_name'),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def _server(storage_type='PremiumV2_LRS', auto_grow='Enabled'):
        return Server({
            'id': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg/'
                  'providers/Microsoft.DBforPostgreSQL/flexibleServers/test-server',
            'location': 'eastus',
            'sku': {'name': 'Standard_D2ds_v4', 'tier': 'GeneralPurpose'},
            'properties': {
                'version': '16',
                'fullyQualifiedDomainName': 'test-server.postgres.database.azure.com',
                'storage': {
                    'type': storage_type,
                    'autoGrow': auto_grow,
                    'storageSizeGB': 128,
                    'iops': 3000,
                    'throughput': 125,
                    'autoGrowMaxThresholdMb': 262144,
                    'autoGrowIncrementPercent': 10,
                },
                'backup': {'geoRedundantBackup': 'Disabled'},
                'authConfig': {'passwordAuth': 'Enabled', 'activeDirectoryAuth': 'Disabled'},
            },
        })

    def _create(self, **kwargs):
        arguments = {
            'resource_group_name': 'test-rg',
            'server_name': 'test-server',
            'location': 'eastus',
            'tier': 'GeneralPurpose',
            'sku_name': 'Standard_D2ds_v4',
            'version': '16',
            'storage_gb': 128,
            'storage_type': 'PremiumV2_LRS',
            'auto_grow': 'Enabled',
            'iops': 3000,
            'throughput': 125,
        }
        arguments.update(kwargs)
        return custom_commands.flexible_server_create(self.cmd, self.client, **arguments)

    def test_postgresql_storage_auto_grow_create_serializes_options(self):
        self._create(auto_grow_max_threshold_mb=131072, auto_grow_increment_percent=101)
        storage = self.client.begin_create_or_update.call_args.args[2].as_dict()['properties']['storage']
        self.assertEqual(storage['autoGrow'], 'Enabled')
        self.assertEqual(storage['autoGrowMaxThresholdMb'], 131072)
        self.assertEqual(storage['autoGrowIncrementPercent'], 101)

    def test_postgresql_storage_auto_grow_create_with_storage_size(self):
        self._create(storage_gb=128, auto_grow_max_threshold_mb=131072)
        storage = self.client.begin_create_or_update.call_args.args[2].as_dict()['properties']['storage']
        self.assertEqual(storage['storageSizeGB'], 128)
        self.assertEqual(storage['type'], 'PremiumV2_LRS')
        self.assertEqual(storage['autoGrow'], 'Enabled')
        self.assertEqual(storage['autoGrowMaxThresholdMb'], 131072)

    def test_postgresql_storage_auto_grow_create_without_storage_size(self):
        self._create(storage_gb=None, auto_grow_max_threshold_mb=131072, auto_grow_increment_percent=10)
        storage = self.client.begin_create_or_update.call_args.args[2].as_dict()['properties']['storage']
        self.assertNotIn('storageSizeGB', storage)
        self.assertEqual(storage['type'], 'PremiumV2_LRS')
        self.assertEqual(storage['autoGrow'], 'Enabled')
        self.assertEqual(storage['autoGrowMaxThresholdMb'], 131072)
        self.assertEqual(storage['autoGrowIncrementPercent'], 10)
        self.assertEqual(storage['iops'], 3000)
        self.assertEqual(storage['throughput'], 125)

    def test_postgresql_storage_auto_grow_create_rejects_invalid_options(self):
        cases = [
            {'storage_type': 'Premium_LRS', 'iops': None, 'throughput': None,
             'auto_grow_increment_percent': 10},
            {'auto_grow': 'Disabled', 'auto_grow_max_threshold_mb': 262144},
            {'auto_grow': None, 'auto_grow_increment_percent': 10},
            {'auto_grow_max_threshold_mb': 131071},
            {'auto_grow_max_threshold_mb': 0},
            {'auto_grow_increment_percent': 0},
            {'auto_grow_increment_percent': -1},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), self.assertRaises(ValidationError):
                self._create(**arguments)
        self.client.begin_create_or_update.assert_not_called()

    def test_postgresql_storage_auto_grow_update_serializes_options(self):
        parameters = custom_commands.flexible_server_update_custom_func(
            self.cmd, self.client, self._server(), storage_gb=256,
            auto_grow_max_threshold_mb=262144, auto_grow_increment_percent=20)
        storage = parameters.as_dict()['properties']['storage']
        self.assertEqual(storage['storageSizeGB'], 256)
        self.assertEqual(storage['autoGrowMaxThresholdMb'], 262144)
        self.assertEqual(storage['autoGrowIncrementPercent'], 20)

    def test_postgresql_storage_auto_grow_update_preserves_omitted_options(self):
        for arguments, maximum, increment in [
                ({}, 262144, 10),
                ({'auto_grow_increment_percent': 101}, 262144, 101),
                ({'storage_gb': 256}, 262144, 10),
                ({'storage_gb': 256, 'auto_grow_increment_percent': 20}, 262144, 20),
                ({'storage_gb': 512, 'auto_grow_max_threshold_mb': 524288}, 524288, 10),
                ({'auto_grow_max_threshold_mb': 524288}, 524288, 10)]:
            with self.subTest(arguments=arguments):
                parameters = custom_commands.flexible_server_update_custom_func(
                    self.cmd, self.client, self._server(), **arguments)
                storage = parameters.as_dict()['properties']['storage']
                self.assertEqual(storage['autoGrowMaxThresholdMb'], maximum)
                self.assertEqual(storage['autoGrowIncrementPercent'], increment)

    def test_postgresql_storage_auto_grow_update_rejects_ineligible_servers(self):
        for storage_type, auto_grow, arguments in [
                ('Premium_LRS', 'Enabled', {}),
                (None, 'Enabled', {}),
                ('PremiumV2_LRS', None, {}),
                ('PremiumV2_LRS', 'Disabled', {}),
                ('PremiumV2_LRS', 'Disabled', {'auto_grow': 'Enabled'}),
                ('PremiumV2_LRS', 'Enabled', {'auto_grow': 'Disabled'})]:
            with self.subTest(storage_type=storage_type, auto_grow=auto_grow, arguments=arguments):
                with self.assertRaises(ValidationError):
                    custom_commands.flexible_server_update_custom_func(
                        self.cmd, self.client, self._server(storage_type, auto_grow),
                        auto_grow_increment_percent=10, **arguments)

    def test_postgresql_storage_auto_grow_update_validates_current_and_requested_size(self):
        for arguments in [
                {'auto_grow_max_threshold_mb': 131071},
                {'storage_gb': 256, 'auto_grow_max_threshold_mb': 262143},
                {'storage_gb': 512},
                {'storage_gb': 512, 'auto_grow_increment_percent': 20},
                {'storage_gb': 512, 'auto_grow_max_threshold_mb': 262144},
                {'auto_grow_increment_percent': 0},
                {'auto_grow_increment_percent': -1}]:
            with self.subTest(arguments=arguments), self.assertRaises(ValidationError):
                custom_commands.flexible_server_update_custom_func(
                    self.cmd, self.client, self._server(), **arguments)

    def test_postgresql_storage_size_update_without_autogrow_options(self):
        for storage_type, auto_grow, maximum, storage_gb in [
                ('Premium_LRS', 'Enabled', 262144, 512),
                ('PremiumV2_LRS', 'Disabled', 262144, 512),
                ('PremiumV2_LRS', 'Enabled', None, 512)]:
            with self.subTest(storage_type=storage_type, auto_grow=auto_grow, maximum=maximum):
                server = self._server(storage_type, auto_grow)
                server.storage.auto_grow_max_threshold_mb = maximum
                parameters = custom_commands.flexible_server_update_custom_func(
                    self.cmd, self.client, server, storage_gb=storage_gb)
                self.assertEqual(parameters.storage.storage_size_gb, storage_gb)
                self.assertEqual(parameters.storage.auto_grow_max_threshold_mb, maximum)

    def test_postgresql_storage_size_update_while_disabling_autogrow(self):
        parameters = custom_commands.flexible_server_update_custom_func(
            self.cmd, self.client, self._server(), storage_gb=512, auto_grow='Disabled')
        self.assertEqual(parameters.storage.storage_size_gb, 512)
        self.assertEqual(parameters.storage.auto_grow, 'Disabled')
        self.assertEqual(parameters.storage.auto_grow_max_threshold_mb, 262144)

    def test_postgresql_storage_auto_grow_can_be_enabled_without_options(self):
        self._create()
        storage = self.client.begin_create_or_update.call_args.args[2].as_dict()['properties']['storage']
        self.assertNotIn('autoGrowMaxThresholdMb', storage)
        self.assertNotIn('autoGrowIncrementPercent', storage)
        parameters = custom_commands.flexible_server_update_custom_func(
            self.cmd, self.client, self._server(auto_grow='Disabled'), auto_grow='Enabled')
        self.assertEqual(parameters.storage.auto_grow, 'Enabled')
