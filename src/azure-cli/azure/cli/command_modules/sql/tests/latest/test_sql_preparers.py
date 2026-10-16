# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import shlex
import unittest
from unittest.mock import patch

from . import test_sql_commands as sql_tests


class SqlServerPreparerTest(unittest.TestCase):

    def test_local_authentication_remains_the_default_for_existing_scenarios(self):
        preparer = sql_tests.SqlServerPreparer(admin_user='test-user', admin_password='test-password')

        with patch.object(sql_tests, 'execute') as execute:
            preparer.create_resource('test-server', resource_group='test-group')

        execute.assert_called_once()
        command = shlex.split(execute.call_args.args[1])
        self.assertEqual(command[command.index('-u') + 1], 'test-user')
        self.assertEqual(command[command.index('-p') + 1], 'test-password')
        self.assertNotIn('--enable-ad-only-auth', command)


class ManagedInstancePreparerTest(unittest.TestCase):

    def test_local_authentication_is_default_and_entra_only_remains_opt_in(self):
        for entra_only in (False, True):
            with self.subTest(entra_only=entra_only):
                preparer = sql_tests.ManagedInstancePreparer(
                    **({'enable_ad_only_auth': True} if entra_only else {}))
                with patch.object(sql_tests, 'execute') as execute:
                    preparer.create_resource('test-managed-instance')

                command = shlex.split(execute.call_args.args[1])
                self.assertEqual(command[command.index('-u') + 1], preparer.admin_user)
                self.assertEqual(command[command.index('-p') + 1], preparer.admin_password)
                self.assertEqual('--enable-ad-only-auth' in command, entra_only)

    def test_memory_scenarios_use_their_own_hardware_and_storage_parameters(self):
        preparer = sql_tests.ManagedInstancePreparer(
            family='Gen8IM', storage=128, v_core=8,
            otherParams='--gpv2 true --memory 56 --iops 1000')

        with patch.object(sql_tests, 'execute') as execute:
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
