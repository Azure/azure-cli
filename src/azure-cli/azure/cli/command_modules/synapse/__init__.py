# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core import AzCommandsLoader
from azure.cli.command_modules.synapse._help import helps  # pylint: disable=unused-import


# pylint: disable=line-too-long
class SynapseCommandsLoader(AzCommandsLoader):
    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        from azure.cli.command_modules.synapse._client_factory import cf_synapse
        synapse_custom = CliCommandType(
            operations_tmpl='azure.cli.command_modules.synapse.custom#{}',
            client_factory=cf_synapse,
            operation_group='synapse')

        super(SynapseCommandsLoader, self).__init__(cli_ctx=cli_ctx, operation_group='synapse', custom_command_type=synapse_custom)

    def load_command_table(self, args):
        from azure.cli.command_modules.synapse.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.synapse._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = SynapseCommandsLoader
