# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType
from azure.cli.command_modules.managedservices._help import helps  # pylint: disable=unused-import


class ManagedServicesCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        managedservices_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.managedservices.custom#{}')
        super(ManagedServicesCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                            resource_type=ResourceType.MGMT_MANAGEDSERVICES,
                                                            custom_command_type=managedservices_custom)

    def load_command_table(self, args):
        from .commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from ._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ManagedServicesCommandsLoader
