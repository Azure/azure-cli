# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.serviceconnector._help import helps  # pylint: disable=unused-import


class MicrosoftServiceConnectorCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.serviceconnector._client_factory import cf_connection_cl
        connection_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.serviceconnector.custom#{}',
            client_factory=cf_connection_cl)
        parent = super(MicrosoftServiceConnectorCommandsLoader, self)
        parent.__init__(cli_ctx=cli_ctx, custom_command_type=connection_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.serviceconnector.commands import load_command_table as load_command_table_manual
        load_command_table_manual(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.serviceconnector._params import load_arguments as load_arguments_manual
        load_arguments_manual(self, command)


COMMAND_LOADER_CLS = MicrosoftServiceConnectorCommandsLoader
