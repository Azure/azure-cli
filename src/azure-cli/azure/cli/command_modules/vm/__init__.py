# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

import azure.cli.command_modules.vm._help  # pylint: disable=unused-import


class ComputeCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        compute_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.vm.custom#{}',
            operation_group='virtual_machines'
        )
        super(ComputeCommandsLoader, self).__init__(cli_ctx=cli_ctx,
                                                    resource_type=ResourceType.MGMT_COMPUTE,
                                                    operation_group='virtual_machines',
                                                    custom_command_type=compute_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.vm.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.vm._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = ComputeCommandsLoader
