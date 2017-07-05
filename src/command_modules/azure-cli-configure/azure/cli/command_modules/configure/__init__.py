# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.configure._help  # pylint: disable=unused-import

class ConfigureCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        super().load_command_table(args)
        self.cli_command(__name__, 'configure', 'azure.cli.command_modules.configure.custom#handle_configure')
        return self.command_table

    def load_arguments(self, command):
        self.register_cli_argument('configure', 'defaults', nargs='+', options_list=('--defaults', '-d'))
        super().load_arguments(command)
