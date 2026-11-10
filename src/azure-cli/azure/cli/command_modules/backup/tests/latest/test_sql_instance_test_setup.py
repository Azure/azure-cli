# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import shlex
import unittest
from unittest.mock import Mock, patch

from .sql_instance_test_setup import SqlInstanceSnapshotEnvironment


class SqlInstanceSnapshotEnvironmentTests(unittest.TestCase):

    def test_vm_password_arguments(self):
        for vm_prefix, sql_prefix in (('', ''), ('-', ''), ('', '-'), ('-', '-'), ('_', '_')):
            for seed in (True, False):
                with self.subTest(vm_prefix=vm_prefix, sql_prefix=sql_prefix, seed=seed):
                    self.get_subscription_id = Mock(return_value='sub')
                    self.create_random_name = Mock(return_value='sqlsnap')
                    self.recording_processors = []
                    with patch('azure.cli.command_modules.backup.tests.latest.sql_instance_test_setup.'
                               'secrets.token_urlsafe',
                               side_effect=[vm_prefix + 'vm-token', sql_prefix + 'sql-token']):
                        environment = SqlInstanceSnapshotEnvironment(self)
                    environment.run_sql = Mock()
                    parsed_commands = {}

                    def execute(command):
                        args = shlex.split(command)
                        if args[:2] == ['vm', 'create']:
                            parser = argparse.ArgumentParser()
                            parser.add_argument('--admin-password', required=True)
                            parsed_commands['vm'], _ = parser.parse_known_args(args[2:])
                            return Mock()
                        if args[:3] == ['vm', 'identity', 'show']:
                            return Mock(get_output_in_json=Mock(return_value={
                                'principalId': 'system-principal',
                                'userAssignedIdentities': {'identity-id': {}},
                            }))
                        self.assertEqual(args[:3], ['sql', 'vm', 'create'])
                        parser = argparse.ArgumentParser()
                        parser.add_argument('--sql-auth-update-pwd', required=True)
                        parsed_commands['sql'], _ = parser.parse_known_args(args[3:])
                        return Mock()

                    self.cmd = Mock(side_effect=execute)
                    self.assertEqual('sqlsnap', environment._vm(
                        'rg', 'eastus2', {'id': 'identity-id'}, seed=seed))
                    self.assertEqual(environment.password, parsed_commands['vm'].admin_password)
                    self.assertEqual(environment.sql_password, parsed_commands['sql'].sql_auth_update_pwd)
                    environment.run_sql.assert_called_once_with(
                        'rg', 'sqlsnap', 'Seed' if seed else 'Target')
                    self.assertEqual(3, self.cmd.call_count)
