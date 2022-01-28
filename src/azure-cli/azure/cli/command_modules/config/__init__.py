# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.config._help  # pylint: disable=unused-import


class ConfigCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(ConfigCommandsLoader, self).__init__(cli_ctx=cli_ctx)

    def load_command_table(self, args):
        from azure.cli.command_modules.config.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.config._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ConfigCommandsLoader
