# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

class DmsCommandsLoader(AzCommandsLoader):

    def load_command_table(self, args):
        from azure.cli.command_modules.dms.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

COMMAND_LOADER_CLS = DmsCommandsLoader