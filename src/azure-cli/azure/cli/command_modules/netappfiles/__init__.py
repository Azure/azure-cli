# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
# from azure.cli.command_modules.netappfiles._help import helps  # pylint: disable=unused-import


class NetAppFilesCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        netappfiles_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.netappfiles.custom#{}')
        super().__init__(cli_ctx=cli_ctx,
                         resource_type=ResourceType.MGMT_NETAPPFILES,
                         custom_command_type=netappfiles_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.netappfiles.commands import load_command_table
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
        from azure.cli.command_modules.netappfiles._params import load_arguments
        load_arguments(command)


COMMAND_LOADER_CLS = NetAppFilesCommandsLoader
