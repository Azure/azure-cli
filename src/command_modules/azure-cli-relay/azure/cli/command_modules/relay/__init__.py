# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import
# pylint: disable=line-too-long

from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.relay._help import helps


class relayCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        from azure.cli.core.commands import CliCommandType
        relay_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.relay.custom#{}')
        super(relayCommandsLoader, self).__init__(cli_ctx=cli_ctx, custom_command_type=relay_custom,
                                                       min_profile='2017-03-10-profile',
                                                       suppress_extension=ModExtensionSuppress(__name__, 'relay', '0.1.0',
                                                                                               reason='These commands are now in the CLI.',
                                                                                               recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.relay.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.relay._params import load_arguments_sb
        load_arguments_sb(self, command)


COMMAND_LOADER_CLS = relayCommandsLoader
