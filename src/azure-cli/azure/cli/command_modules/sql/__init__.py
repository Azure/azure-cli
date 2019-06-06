# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.sql._help  # pylint: disable=unused-import


class SqlCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        sql_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.sql.custom#{}')
        super(SqlCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=sql_custom,
                                                min_profile='2017-03-10-profile')

    def load_command_table(self, args):
        from azure.cli.command_modules.sql.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.sql._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = SqlCommandsLoader
