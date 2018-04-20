# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=unused-import
import azure.cli.command_modules.dms._help

from azure.cli.core import AzCommandsLoader


class DmsCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.dms.commands import dms_api_exception_handler
        dms_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.dms.custom#{}',
                                    exception_handler=dms_api_exception_handler)
        super(DmsCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                min_profile='2017-03-10-profile',
                                                custom_command_type=dms_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.dms.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.dms._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = DmsCommandsLoader
