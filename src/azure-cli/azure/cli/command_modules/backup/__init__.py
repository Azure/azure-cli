# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.backup._help import helps  # pylint: disable=unused-import


class BackupCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        backup_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.backup.custom#{}')
        super(BackupCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                   resource_type=ResourceType.MGMT_BACKUP,
                                                   custom_command_type=backup_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.backup.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.backup._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = BackupCommandsLoader
