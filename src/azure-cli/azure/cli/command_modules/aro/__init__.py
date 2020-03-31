# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.command_modules.aro._client_factory import cf_aro
from azure.cli.command_modules.aro._params import load_arguments
from azure.cli.command_modules.aro.commands import load_command_table
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import CliCommandType

import azure.cli.command_modules.aro._help  # pylint: disable=unused-import

class AroCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        aro_custom = CliCommandType(operations_tmpl='azure.command_modules.aro.custom#{}')
        super(AroCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                custom_command_type=aro_custom)

    def load_command_table(self, args):
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        load_arguments(self, command)


COMMAND_LOADER_CLS = AroCommandsLoader
