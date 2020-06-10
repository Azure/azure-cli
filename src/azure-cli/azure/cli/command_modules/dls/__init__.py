# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-import

from azure.cli.core import AzCommandsLoader

from azure.cli.command_modules.dls._help import helps  # pylint: disable=unused-import


class DataLakeStoreCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.core.profiles import ResourceType
        dls_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.dls.custom#{}')
        super(DataLakeStoreCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                          resource_type=ResourceType.MGMT_DATALAKE_STORE,
                                                          custom_command_type=dls_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.dls.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.dls._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = DataLakeStoreCommandsLoader
