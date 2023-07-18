# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.appconfig._help  # pylint: disable=unused-import


class AppconfigCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core import ModExtensionSuppress
        configstore_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.appconfig.custom#{}')
        super(AppconfigCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            suppress_extension=ModExtensionSuppress(__name__, 'appconfig', '0.5.0',
                                                    reason='These commands are now in the CLI.',
                                                    recommend_remove=True),
            custom_command_type=configstore_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.appconfig.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.appconfig._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = AppconfigCommandsLoader
