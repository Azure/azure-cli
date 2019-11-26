# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

import azure.cli.command_modules.privatedns._help  # pylint: disable=unused-import


class PrivateDnsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        from azure.cli.core.commands import CliCommandType
        privatedns_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.privatedns.custom#{}')
        super(PrivateDnsCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                       resource_type=ResourceType.MGMT_NETWORK,
                                                       custom_command_type=privatedns_custom,
                                                       suppress_extension=[
                                                           ModExtensionSuppress(__name__, 'privatedns', '0.1.1',
                                                                                reason='These commands are now in the CLI.',
                                                                                recommend_remove=True)])

    def load_command_table(self, args):
        from azure.cli.command_modules.privatedns.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.privatedns._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = PrivateDnsCommandsLoader
