# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, patch

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.core.mock import DummyCli
from azure.cli.core.parser import AzCliCommandParser
from azure.cli.command_modules.postgresql import PostgreSQLCommandsLoader
from azure.cli.command_modules.postgresql.commands import custom_commands


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
