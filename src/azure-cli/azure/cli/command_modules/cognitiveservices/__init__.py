# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.cognitiveservices._help  # pylint: disable=unused-import

from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts


class CognitiveServicesCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        custom_type = CliCommandType(
            operations_tmpl='azure.cli.command_modules.cognitiveservices.custom#{}',
            client_factory=cf_accounts)
        super(CognitiveServicesCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                              custom_command_type=custom_type,
                                                              resource_type=ResourceType.MGMT_COGNITIVESERVICES)

    def load_command_table(self, args):
        from azure.cli.command_modules.cognitiveservices.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.cognitiveservices._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = CognitiveServicesCommandsLoader
