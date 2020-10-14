# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
import azure.cli.command_modules.find._help  # pylint: disable=unused-import


class FindCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core import ModExtensionSuppress
        find_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.find.custom#{}')
        super(FindCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                 custom_command_type=find_custom,
                                                 suppress_extension=ModExtensionSuppress(
                                                     __name__, 'find', '0.3.0',
                                                     reason='The find command is now in CLI.',
                                                     recommend_remove=True))
        self.module_name = __name__

    def load_command_table(self, args):
        from azure.cli.command_modules.find.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.find._params import load_arguments
        with self.argument_context('find') as c:
            c.ignore('_subscription')  # hide global subscription param
        load_arguments(self, command)


COMMAND_LOADER_CLS = FindCommandsLoader
