# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.signalr._help  # pylint: disable=unused-import


class SignalRCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        super(SignalRCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    min_profile='2017-03-10-profile')

    def load_command_table(self, args):
        from .commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from ._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = SignalRCommandsLoader
