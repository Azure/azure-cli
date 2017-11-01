# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.sdk.util import CliCommandType

import azure.cli.command_modules.component._help  # pylint: disable=unused-import


class ComponentCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        component_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.component.custom#{}')
        super(ComponentCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                      custom_command_type=component_custom)
        self.module_name = __name__

    def load_command_table(self, args):
        super(ComponentCommandsLoader, self).load_command_table(args)
        from azure.cli.command_modules.component.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        super(ComponentCommandsLoader, self).load_arguments(command)
        from azure.cli.command_modules.component._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ComponentCommandsLoader
