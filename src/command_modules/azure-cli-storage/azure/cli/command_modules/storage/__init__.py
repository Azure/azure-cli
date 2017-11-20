# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

import azure.cli.command_modules.storage._help  # pylint: disable=unused-import


class StorageCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.sdk.util import CliCommandType
        from azure.cli.command_modules.storage._command_type import _StorageCommandGroup

        storage_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.storage.custom#{}')
        super(StorageCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    resource_type=ResourceType.DATA_STORAGE,
                                                    custom_command_type=storage_custom,
                                                    command_group_cls=_StorageCommandGroup)
        self.module_name = __name__

    def load_command_table(self, args):
        super(StorageCommandsLoader, self).load_command_table(args)
        from azure.cli.command_modules.storage.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        super(StorageCommandsLoader, self).load_arguments(command)
        from azure.cli.command_modules.storage._params import load_arguments
        load_arguments(self, command)

COMMAND_LOADER_CLS = StorageCommandsLoader
