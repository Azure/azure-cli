# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader, ModExtensionSuppress
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.mysql.commands import load_command_table
from azure.cli.command_modules.mysql._params import load_arguments
from azure.cli.command_modules.mysql._util import MysqlArgumentContext
import azure.cli.command_modules.mysql._help    # pylint: disable=unused-import


class MysqlCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        mysql_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.mysql.custom#{}')
        super().__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_RDBMS,
            custom_command_type=mysql_custom,
            argument_context_cls=MysqlArgumentContext,
            suppress_extension=ModExtensionSuppress(
                __name__,
                'rdbms-vnet',
                '10.0.1',
                reason='These commands are now in the CLI.',
                recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.core.aaz import load_aaz_command_table
        try:
            from . import aaz
        except ImportError:
            aaz = None
        if aaz:
            load_aaz_command_table(
                loader=self,
                aaz_pkg_name=aaz.__name__,
                args=args
            )

        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = MysqlCommandsLoader
