# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader, ModExtensionSuppress
from azure.cli.command_modules.botservice._help import helps  # pylint: disable=unused-import
from azure.cli.command_modules.botservice._client_factory import get_botservice_management_client


class BotServiceCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):

        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        custom_type = CliCommandType(
            operations_tmpl='azure.cli.command_modules.botservice.custom#{}',
            client_factory=get_botservice_management_client)
        super(BotServiceCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                       custom_command_type=custom_type,
                                                       resource_type=ResourceType.MGMT_BOTSERVICE,
                                                       suppress_extension=ModExtensionSuppress(
                                                           __name__,
                                                           'botservice',
                                                           '0.4.3',
                                                           reason='These commands and functionality are now in the '
                                                                  'core CLI.',
                                                           recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.botservice.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.botservice._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = BotServiceCommandsLoader
