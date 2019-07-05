# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.security._help import helps  # pylint: disable=unused-import
from azure.cli.core import AzCommandsLoader


class SecurityCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType

        security_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.security.custom#{}')

        super(SecurityCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            custom_command_type=security_custom)

    def load_command_table(self, args):
        from .commands import load_command_table
        load_command_table(self, args)

        return self.command_table

    def load_arguments(self, command):
        from ._params import load_arguments

        load_arguments(self, command)


COMMAND_LOADER_CLS = SecurityCommandsLoader
