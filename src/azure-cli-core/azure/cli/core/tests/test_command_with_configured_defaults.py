# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import logging
import unittest
import mock

from azure.cli.core.commands import _update_command_definitions

from azure.cli.core.commands import (command_table, CLIArgumentType, cli_command,
                                     register_cli_argument)

from knack.config import CLIConfig


# a dummy callback for arg-parse
def load_params(_):
    pass


class TestCommandWithConfiguredDefaults(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        self.argv = None
        self.application = None
        super(TestCommandWithConfiguredDefaults, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    @staticmethod
    def sample_vm_list(resource_group_name):
        return resource_group_name

    def set_up_command_table(self, required_arg=False):
        command_table.clear()

        module_name = __name__ + '.' + self._testMethodName
        cli_command(module_name, 'test sample-vm-list',
                    '{}#TestCommandWithConfiguredDefaults.sample_vm_list'.format(__name__))

        register_cli_argument('test sample-vm-list', 'resource_group_name',
                              CLIArgumentType(options_list=('--resource-group-name', '-g'),
                                              configured_default='group', required=required_arg))

        command_table['test sample-vm-list'].load_arguments()
        _update_command_definitions(command_table)

        self.argv = 'az test sample-vm-list'.split()
        config = Configuration()
        config.get_command_table = lambda argv: command_table
        self.application = Application(config)

    @mock.patch.dict(os.environ, {CLIConfig.env_var_name('defaults', 'group'): 'myRG'})
    def test_apply_configured_defaults_on_required_arg(self):
        self.set_up_command_table(required_arg=True)

        # action
        res = self.application.execute(self.argv[1:])

        # assert
        self.assertEqual(res.result, 'myRG')

    @mock.patch.dict(os.environ, {CLIConfig.env_var_name('defaults', 'group'): 'myRG'})
    def test_apply_configured_defaults_on_optional_arg(self):
        self.set_up_command_table(required_arg=False)

        # action
        res = self.application.execute(self.argv[1:])

        # assert
        self.assertEqual(res.result, 'myRG')


if __name__ == '__main__':
    unittest.main()
