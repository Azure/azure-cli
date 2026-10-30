# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shlex
import unittest
from unittest.mock import patch

from . import test_sql_commands as sql_tests


class SqlServerPreparerTest(unittest.TestCase):

    def test_default_uses_a_test_owned_entra_administrator_without_sql_credentials(self):
        preparer = sql_tests.SqlServerPreparer()

        with patch.object(sql_tests, 'execute') as execute:
            execute.return_value.get_output_in_json.return_value = {
                'name': 'test-server-admin', 'principalId': 'test-principal'}
            result = preparer.create_resource('test-server', resource_group='test-group')

        self.assertEqual(result, {'server': 'test-server'})
        self.assertEqual(shlex.split(execute.call_args_list[0].args[1]), [
            'az', 'identity', 'create', '-g', 'test-group', '-n', 'test-server-admin', '-l', preparer.location])
        self.assertEqual(execute.call_count, 2)
        command = shlex.split(execute.call_args.args[1])
        self.assertIn('--enable-ad-only-auth', command)
        self.assertEqual(command[command.index('--external-admin-name') + 1], 'test-server-admin')
        self.assertEqual(command[command.index('--external-admin-sid') + 1], 'test-principal')
        self.assertEqual(command[command.index('--external-admin-principal-type') + 1], 'Application')
        self.assertNotIn('-u', command)
        self.assertNotIn('-p', command)


class ManagedInstancePreparerTest(unittest.TestCase):

    def test_entra_only_is_default_and_local_authentication_remains_opt_in(self):
        for entra_only in (False, True):
            with self.subTest(entra_only=entra_only):
                preparer = sql_tests.ManagedInstancePreparer(
                    **({} if entra_only else {'enable_ad_only_auth': False}))
                with patch.object(sql_tests, 'execute') as execute:
                    execute.return_value.get_output_in_json.return_value = {
                        'name': 'test-managed-instance-admin', 'principalId': 'test-principal'}
                    preparer.create_resource('test-managed-instance')

                command = shlex.split(execute.call_args.args[1])
                self.assertEqual(command[command.index('-u') + 1], preparer.admin_user)
                self.assertEqual(command[command.index('-p') + 1], preparer.admin_password)
                self.assertEqual('--enable-ad-only-auth' in command, entra_only)
                self.assertEqual(execute.call_count, 2 if entra_only else 1)
                if entra_only:
                    self.assertEqual(command[command.index('--external-admin-sid') + 1], 'test-principal')

    def test_memory_scenarios_use_their_own_hardware_and_storage_parameters(self):
        preparer = sql_tests.ManagedInstancePreparer(
            family='Gen8IM', storage=128, v_core=8,
            otherParams='--gpv2 true --memory 56 --iops 1000')

        with patch.object(sql_tests, 'execute') as execute:
            execute.return_value.get_output_in_json.return_value = {
                'name': 'test-managed-instance-admin', 'principalId': 'test-principal'}
            result = preparer.create_resource('test-managed-instance')

        self.assertEqual(result, {
            'mi': 'test-managed-instance', 'rg': sql_tests.ManagedInstancePreparer.group})
        command = shlex.split(execute.call_args.args[1])
        for argument, value in (
                ('--family', 'Gen8IM'), ('--storage', '128'), ('--capacity', '8'),
                ('--gpv2', 'true'), ('--memory', '56'), ('--iops', '1000')):
            self.assertEqual(command[command.index(argument) + 1], value)
        self.assertEqual(sql_tests.ManagedInstancePreparer().family, 'Gen5')
        self.assertEqual(sql_tests.ManagedInstancePreparer().storage, 32)
