# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.apim._help import helps  # pylint: disable=unused-import


class ApimCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.apim._client_factory import _apim_client_factory
        apim_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.apim.custom#{}',
            client_factory=_apim_client_factory)
        super(ApimCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                  custom_command_type=apim_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.apim.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.apim._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ApimCommandsLoader
