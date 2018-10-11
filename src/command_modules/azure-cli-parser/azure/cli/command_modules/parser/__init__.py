# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.parser._help  # pylint: disable=unused-import


class ParserCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        example_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.parser.custom#{}')

        super(ParserCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                   min_profile='2017-03-10-profile',
                                                   custom_command_type=example_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.parser.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.parser._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ParserCommandsLoader
