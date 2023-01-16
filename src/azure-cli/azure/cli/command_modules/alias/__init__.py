# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from .custom import process_args_with_built_in_alias


class AliasCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        alias_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.alias.custom#{}')
        super(AliasCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=alias_custom)

    def load_command_table(self, args):
        process_args_with_built_in_alias(self.cli_ctx, args)
        return self.command_table


COMMAND_LOADER_CLS = AliasCommandsLoader
