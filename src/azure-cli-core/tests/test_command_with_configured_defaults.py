# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import logging
import unittest

from azure.cli.core.commands import _update_command_definitions
from azure.cli.core.commands import (
    command_table,
    CliArgumentType,
    CliCommandArgument,
    cli_command,
    register_cli_argument,
    register_extra_cli_argument)


class Test_command_registration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        import azure.cli.main
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @staticmethod
    def sample_vm_get(resource_group_name, vm_name, opt_param=None, expand=None, custom_headers={},  # pylint: disable=dangerous-default-value, too-many-arguments
                      raw=False, **operation_config):
        pass

    def test_register_cli_argument_with_configured_defaults(self):
        command_table.clear()
        cli_command(None, 'test register sample-vm-get',
                    '{}#Test_command_registration.sample_vm_get'.format(__name__))
        register_cli_argument('test register sample-vm-get', 'vm_name', CliArgumentType(
            options_list=('--wonky-name', '-n'), metavar='VMNAME', configured_default='vm',
            required=False
        ))

        command_table['test register sample-vm-get'].load_arguments()
        _update_command_definitions(command_table)

        self.assertEqual(len(command_table), 1,
                         'We expect exactly one command in the command table')
        command_metadata = command_table['test register sample-vm-get']
        self.assertEqual(len(command_metadata.arguments), 4, 'We expected exactly 4 arguments')
        some_expected_arguments = {
            'resource_group_name': CliArgumentType(dest='resource_group_name', required=True),
            'vm_name': CliArgumentType(dest='vm_name', required=False),
        }

        for probe in some_expected_arguments:
            existing = next(arg for arg in command_metadata.arguments if arg == probe)
            self.assertDictContainsSubset(some_expected_arguments[existing].settings,
                                          command_metadata.arguments[existing].options)
        self.assertEqual(command_metadata.arguments['vm_name'].options_list, ('--wonky-name', '-n'))



if __name__ == '__main__':
    unittest.main()
