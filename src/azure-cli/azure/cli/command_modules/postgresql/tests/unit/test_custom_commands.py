# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, create_autospec, patch

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.mock import DummyCli
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.command_modules.postgresql import PostgreSQLCommandsLoader
from azure.cli.command_modules.postgresql.commands import custom_commands
from azure.mgmt.postgresqlflexibleservers.models import Network, Server
from azure.mgmt.postgresqlflexibleservers.operations import ServersOperations


class FlexibleServerFipsModeTest(unittest.TestCase):

    def setUp(self):
        self.client = Mock()
        self.server = Server({
            'id': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg/'
                  'providers/Microsoft.DBforPostgreSQL/flexibleServers/test-server',
            'name': 'test-server',
            'location': 'eastus2',
            'sku': {'name': 'Standard_D2s_v3', 'tier': 'GeneralPurpose'},
            'properties': {
                'administratorLogin': 'testadmin',
                'fullyQualifiedDomainName': 'test-server.postgres.database.azure.com',
                'version': '17',
                'storage': {'storageSizeGB': 128, 'type': 'Premium_LRS'},
                'backup': {'backupRetentionDays': 7},
                'network': {'publicNetworkAccess': 'Disabled'},
                'authConfig': {'passwordAuth': 'Enabled', 'activeDirectoryAuth': 'Disabled'},
                'maintenanceWindow': {'customWindow': 'Disabled'},
                'fipsMode': 'Enabled',
            },
        })
        self.client.get.return_value = self.server
        self.client.begin_create_or_update.return_value = self.server
        self.client.begin_update.return_value = self.server
        patches = [
            patch('azure.cli.command_modules.postgresql.flexible_server_commands.cf_postgres_flexible_servers',
                  return_value=self.client),
            patch('azure.cli.command_modules.postgresql.commands.custom_commands.generate_missing_parameters',
                  return_value=('eastus2', 'test-rg', 'test-server')),
            patch('azure.cli.command_modules.postgresql.commands.custom_commands.get_postgres_location_capability_info',
                  return_value={}),
            patch('azure.cli.command_modules.postgresql.commands.custom_commands.get_postgres_server_capability_info',
                  return_value={}),
            patch('azure.cli.command_modules.postgresql.commands.custom_commands.pg_arguments_validator'),
            patch('azure.cli.command_modules.postgresql.commands.custom_commands.build_network_configuration',
                  return_value=(Network(public_network_access='Disabled'), -1, -1)),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _invoke(self, action, *options):
        cli = DummyCli(random_config_dir=True)
        self.addCleanup(cli.env_patch.stop)
        output = StringIO()
        args = ['postgres', 'flexible-server', action, '--resource-group', 'test-rg', '--name', 'test-server',
                '--output', 'json']
        if action == 'create':
            args += ['--location', 'eastus2', '--sku-name', 'Standard_D2s_v3', '--version', '17',
                     '--admin-user', 'testadmin', '--admin-password', 'Test-password-123!', '--yes']
        exit_code = cli.invoke(args + list(options), out_file=output)
        self.assertEqual(exit_code, 0)
        return output.getvalue()

    def test_postgres_flexible_server_create_fips_mode(self):
        for value, expected in [('Enabled', 'Enabled'), ('Disabled', 'Disabled'), ('enabled', 'Enabled')]:
            with self.subTest(value=value):
                self.client.reset_mock()
                self._invoke('create', '--fips-mode', value)
                self.client.begin_create_or_update.assert_called_once()
                resource_group, server_name, parameters = self.client.begin_create_or_update.call_args.args
                self.assertEqual((resource_group, server_name), ('test-rg', 'test-server'))
                self.assertEqual(parameters.as_dict()['properties']['fipsMode'], expected)

    def test_postgres_flexible_server_create_fips_mode_omitted(self):
        self._invoke('create')
        parameters = self.client.begin_create_or_update.call_args.args[2]
        self.assertNotIn('fipsMode', parameters.as_dict()['properties'])

    def test_postgres_flexible_server_update_fips_mode(self):
        for value, expected in [('Enabled', 'Enabled'), ('Disabled', 'Disabled'), ('DISABLED', 'Disabled')]:
            with self.subTest(value=value):
                self.server.fips_mode = 'Disabled' if expected == 'Enabled' else 'Enabled'
                self.client.reset_mock()
                self._invoke('update', '--fips-mode', value)
                self.client.begin_update.assert_called_once()
                resource_group, server_name, parameters = self.client.begin_update.call_args.args
                self.assertEqual((resource_group, server_name), ('test-rg', 'test-server'))
                self.assertEqual(parameters.as_dict()['properties']['fipsMode'], expected)

    def test_postgres_flexible_server_update_fips_mode_omitted(self):
        self._invoke('update', '--tags', 'environment=test')
        parameters = self.client.begin_update.call_args.args[2]
        self.assertEqual(parameters.tags, {'environment': 'test'})
        self.assertNotIn('fipsMode', parameters.as_dict()['properties'])
        self.assertEqual(self.server.fips_mode, 'Enabled')

    def test_postgres_flexible_server_fips_mode_rejects_invalid_values(self):
        for action in ['create', 'update']:
            with self.subTest(action=action):
                with self.assertRaises(SystemExit) as error:
                    self._invoke(action, '--fips-mode', 'invalid')
                self.assertEqual(error.exception.code, 2)
        self.client.get.assert_not_called()
        self.client.begin_create_or_update.assert_not_called()
        self.client.begin_update.assert_not_called()

    def test_postgres_flexible_server_show_fips_mode_query(self):
        for value in ['Enabled', 'Disabled']:
            with self.subTest(value=value):
                self.server.fips_mode = value
                with patch.object(ServersOperations, 'get', autospec=True, return_value=self.server) as get_server:
                    output = self._invoke('show', '--query', 'fipsMode')
                self.assertEqual(json.loads(output), value)
                get_server.assert_called_once()


class FlexibleServerCreateTest(unittest.TestCase):

    def test_create_immutable_backup_payload(self):
        for value, cluster_size in ((None, None), ('Enabled', None), ('Disabled', None),
                                    (None, 3), ('Disabled', 3)):
            with self.subTest(immutable_backup=value, cluster_size=cluster_size):
                client = MagicMock()
                db_context = SimpleNamespace(server_client=client, logging_name='PostgreSQL')
                with patch.multiple(
                    custom_commands,
                    check_resource_group=MagicMock(return_value=True),
                    generate_missing_parameters=MagicMock(
                        return_value=('canadacentral', 'test-rg', 'test-server')),
                    DbContext=MagicMock(return_value=db_context),
                    get_postgres_location_capability_info=MagicMock(return_value={}),
                    pg_arguments_validator=create_autospec(custom_commands.pg_arguments_validator),
                    build_network_configuration=MagicMock(return_value=(None, -1, -1)),
                    build_identity_and_data_encryption=MagicMock(return_value=(None, None)),
                    validate_resource_group=MagicMock(),
                    resolve_poller=MagicMock(),
                    _update_local_contexts=MagicMock()
                ):
                    custom_commands.flexible_server_create(
                        MagicMock(), client, resource_group_name='test-rg', server_name='test-server',
                        location='canadacentral', sku_name='Standard_D2s_v3', tier='GeneralPurpose',
                        storage_gb=64, version='16', backup_retention=25,
                        geo_redundant_backup='Disabled', immutable_backup=value, cluster_size=cluster_size)

                client.begin_create_or_update.assert_called_once()
                properties = client.begin_create_or_update.call_args.args[2].as_dict()['properties']
                expected_backup = {'backupRetentionDays': 25, 'geoRedundantBackup': 'Disabled'}
                if value is not None:
                    expected_backup['immutableBackup'] = value
                self.assertEqual(properties['backup'], expected_backup)
                if cluster_size is not None:
                    self.assertEqual(properties['cluster']['clusterSize'], cluster_size)
                else:
                    self.assertNotIn('cluster', properties)


class FlexibleServerCreateArgumentsTest(unittest.TestCase):
    command = 'postgres flexible-server create'

    def setUp(self):
        cli = DummyCli(commands_loader_cls=PostgreSQLCommandsLoader)
        loader = PostgreSQLCommandsLoader(cli)
        cli.invocation = MagicMock()
        cli.invocation.commands_loader = loader
        loader.command_name = self.command
        loader.load_command_table(None)
        loader.command_table = {self.command: loader.command_table[self.command]}
        loader.command_table[self.command].load_arguments()
        with loader.argument_context('') as context:
            context.ignore('cmd')
        loader.load_arguments(self.command)
        loader._update_command_definitions()
        self.validator = loader.command_table[self.command].arguments['immutable_backup'].validator
        self.parser = AzCliCommandParser(cli_ctx=cli)
        self.parser.load_command_table(loader)

    def _parse(self, *args):
        namespace = self.parser.parse_args(self.command.split() + list(args))
        if self.validator:
            self.validator(namespace)
        return namespace

    def test_immutable_backup_is_optional(self):
        self.assertIsNone(self._parse().immutable_backup)

    def test_immutable_backup_accepts_case_insensitive_values(self):
        for value, expected in (('Enabled', 'Enabled'), ('enabled', 'Enabled'),
                                ('Disabled', 'Disabled'), ('disabled', 'Disabled')):
            with self.subTest(value=value):
                self.assertEqual(self._parse('--immutable-backup', value).immutable_backup, expected)

    def test_immutable_backup_rejects_unknown_value(self):
        with self.assertRaises(SystemExit) as error:
            self._parse('--immutable-backup', 'invalid')
        self.assertEqual(error.exception.code, 2)

    def test_immutable_backup_enabled_rejects_cluster(self):
        for node_count in ('0', '3'):
            with self.subTest(node_count=node_count):
                with self.assertRaisesRegex(MutuallyExclusiveArgumentError, '--node-count'):
                    self._parse('--immutable-backup', 'enabled', '--node-count', node_count)

    def test_cluster_without_immutable_backup_enabled_is_accepted(self):
        for args in ((), ('--immutable-backup', 'Disabled')):
            with self.subTest(args=args):
                self.assertEqual(self._parse('--node-count', '3', *args).cluster_size, 3)
