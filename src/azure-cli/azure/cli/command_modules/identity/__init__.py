# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.identity._help  # pylint: disable=unused-import
from azure.cli.core import AzCommandsLoader


class IdentityCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        identity_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.identity.custom#{}')
        super(IdentityCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                     custom_command_type=identity_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.identity.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.identity._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = IdentityCommandsLoader
