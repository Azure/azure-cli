# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function
import os
import logging
import unittest
import mock
from six import StringIO
import sys

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand, CliCommandType

from azure.cli.core.mock import DummyCli

from knack.config import CLIConfig


# a dummy callback for arg-parse
def load_params(_):
    pass


class TestCommandWithConfiguredDefaults(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure initialization has occurred correctly
        logging.basicConfig(level=logging.DEBUG)

    @classmethod
    def tearDownClass(cls):
        logging.shutdown()

    def set_up_command_table(self, required_arg=False):

        class TestCommandsLoader(AzCommandsLoader):

            def sample_vm_list(resource_group_name):
                return str(resource_group_name)
            setattr(sys.modules[__name__], sample_vm_list.__name__, sample_vm_list)

            def load_command_table(self, args):
                test_type = CliCommandType(operations_tmpl='{}#{{}}'.format(__name__))
                with self.command_group('test', test_type) as g:
                    g.command('sample-vm-list', 'sample_vm_list')
                return self.command_table

            def load_arguments(self, command):
                self.command_table[command].load_arguments()  # this loads the arguments via reflection
                with self.argument_context('test') as c:
                    c.argument('resource_group_name', options_list=['--resource-group-name', '-g'],
                               configured_default='group', required=required_arg)
                self._update_command_definitions()  # pylint: disable=protected-access
        return DummyCli(commands_loader_cls=TestCommandsLoader)

    @mock.patch.dict(os.environ, {'AZURE_DEFAULTS_GROUP': 'myRG'})
    def test_apply_configured_defaults_on_required_arg(self):
        io = StringIO()
        cli = self.set_up_command_table(required_arg=True)
        cli.invoke('test sample-vm-list'.split(), out_file=io)
        result = io.getvalue()
        self.assertTrue('myRG' in result)

    @mock.patch.dict(os.environ, {'AZURE_DEFAULTS_GROUP': 'myRG'})
    def test_apply_configured_defaults_on_optional_arg(self):
        io = StringIO()
        cli = self.set_up_command_table(required_arg=False)
        cli.invoke('test sample-vm-list'.split(), out_file=io)
        result = io.getvalue()
        self.assertTrue('myRG' in result)


if __name__ == '__main__':
    unittest.main()
