# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader

import azure.cli.command_modules.sqlvm._help  # pylint: disable=unused-import


class SqlVmCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core import ModExtensionSuppress
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType

        sqlvm_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.sqlvm.custom#{}')
        super().__init__(cli_ctx=cli_ctx,
                         custom_command_type=sqlvm_custom,
                         resource_type=ResourceType.MGMT_SQLVM,
                         suppress_extension=ModExtensionSuppress(__name__, 'sqlvm-preview', '0.1.0',
                                                                 reason='These commands are now in the CLI.',
                                                                 recommend_remove=True))

    def load_command_table(self, args):
        from azure.cli.command_modules.sqlvm.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.sqlvm._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = SqlVmCommandsLoader
