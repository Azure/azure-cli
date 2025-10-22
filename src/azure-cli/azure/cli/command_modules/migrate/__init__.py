# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
# See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType


class MigrateCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType

        migrate_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.migrate.custom#{}',
        )

        super().__init__(
            cli_ctx=cli_ctx,
            custom_command_type=migrate_custom,
            resource_type=ResourceType.MGMT_MIGRATE
        )

    def load_command_table(self, args):
        from azure.cli.command_modules.migrate.commands \
            import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.migrate._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = MigrateCommandsLoader
