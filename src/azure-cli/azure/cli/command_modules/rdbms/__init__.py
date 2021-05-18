# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core import ModExtensionSuppress
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.rdbms._util import RdbmsArgumentContext
from azure.cli.command_modules.rdbms.commands import load_command_table
from azure.cli.command_modules.rdbms.flexible_server_commands import load_flexibleserver_command_table
from azure.cli.command_modules.rdbms._params import load_arguments
import azure.cli.command_modules.rdbms._help  # pylint: disable=unused-import
import azure.cli.command_modules.rdbms._helptext_pg  # pylint: disable=unused-import
import azure.cli.command_modules.rdbms._helptext_mysql  # pylint: disable=unused-import


# pylint: disable=import-outside-toplevel
class RdbmsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):

        rdbms_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.rdbms.custom#{}')
        super().__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_RDBMS,
            custom_command_type=rdbms_custom,
            argument_context_cls=RdbmsArgumentContext,
            suppress_extension=ModExtensionSuppress(
                __name__,
                'rdbms-vnet',
                '10.0.1',
                reason='These commands are now in the CLI.',
                recommend_remove=True))

    def load_command_table(self, args):

        load_command_table(self, args)
        load_flexibleserver_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = RdbmsCommandsLoader
