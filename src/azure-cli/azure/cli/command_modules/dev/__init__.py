# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

class AZDCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        azd_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.dev.custom#{}')
        super(AZDCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=azd_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.dev.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.dev._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = AZDCommandsLoader
