# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.iotcentral._help import helps  # pylint: disable=unused-import


class IoTCentralCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        iotcentral_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.iotcentral.custom#{}')

        super(IoTCentralCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                       resource_type=ResourceType.MGMT_IOTCENTRAL,
                                                       custom_command_type=iotcentral_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.iotcentral.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.iotcentral._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = IoTCentralCommandsLoader
