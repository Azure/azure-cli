# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.webpubsub._help import helps  # pylint: disable=unused-import


class WebpubsubCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.webpubsub._client_factory import cf_webpubsub
        webpubsub_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.webpubsub.custom#{}',
            client_factory=cf_webpubsub)
        super(WebpubsubCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                  custom_command_type=webpubsub_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.webpubsub.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.webpubsub._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = WebpubsubCommandsLoader
