# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=unused-import
# pylint: disable=line-too-long

from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.relay._help import helps


class RelayCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        relay_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.relay.custom#{}')
        super().__init__(
            cli_ctx=cli_ctx, custom_command_type=relay_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.relay.commands import load_command_table
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
        from azure.cli.command_modules.relay._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = RelayCommandsLoader
