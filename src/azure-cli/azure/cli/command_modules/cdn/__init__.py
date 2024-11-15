# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-import
import azure.cli.command_modules.cdn._help

from azure.cli.core import AzCommandsLoader


class CdnCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        cdn_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.cdn.custom#{}')
        super().__init__(cli_ctx=cli_ctx,
                         resource_type=ResourceType.MGMT_CDN,
                         custom_command_type=cdn_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.cdn.commands import load_command_table
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
        from azure.cli.command_modules.cdn._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = CdnCommandsLoader
