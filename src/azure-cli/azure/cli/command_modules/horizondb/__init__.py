# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.horizondb.utils._context import HorizonDBArgumentContext
from azure.cli.command_modules.horizondb.cluster_commands import load_command_table
from azure.cli.command_modules.horizondb._params import load_arguments
import azure.cli.command_modules.horizondb._help  # pylint: disable=unused-import


# pylint: disable=import-outside-toplevel
class HorizonDBCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):

        horizondb_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.horizondb.commands.custom_commands#{}')
        super().__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_HORIZONDB,
            custom_command_type=horizondb_custom,
            argument_context_cls=HorizonDBArgumentContext)

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


COMMAND_LOADER_CLS = HorizonDBCommandsLoader
