# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import _load_command_loader


class HelpTestCommandLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        compute_custom = CliCommandType(
            operations_tmpl='{}#{{}}'.format(__name__),
        )
        super(HelpTestCommandLoader, self).__init__(cli_ctx=cli_ctx,
                                                    custom_command_type=compute_custom)
        self.cmd_to_loader_map = {}

    def load_command_table(self, args):
        with self.command_group('test') as g:
            g.custom_command('alpha', 'dummy_handler')

        return self.command_table

    def load_arguments(self, command):
        with self.argument_context('test') as c:
            c.argument('arg1', options_list=['--arg1', '-a'])
            c.argument('arg2', options_list=['--arg2'], help="Help From code.")
        self._update_command_definitions()  # pylint: disable=protected-access


def dummy_handler(arg1, arg2=None, arg3=None):
    """
    Short summary here. Long summary here. Still long summary.
    :param arg1: arg1's help text
    :param arg2: arg2's help text
    :param arg3: arg3's help text
    """
    pass


def mock_load_command_loader(loader, args, name, prefix):
    return _load_command_loader(loader, args, name, "azure.cli.core.tests.")


COMMAND_LOADER_CLS = HelpTestCommandLoader
