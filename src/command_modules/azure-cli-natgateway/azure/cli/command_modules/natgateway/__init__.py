# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core import AzCommandsLoader
from azure.cli.core.profiles import ResourceType

import azure.cli.command_modules.natgateway._help  # pylint: disable=unused-import


class NatGatewayCommandsLoader(AzCommandsLoader):

    def __init__(self, cli_ctx=None):
        from azure.cli.core.commands import CliCommandType
        natgateway_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.natgateway.custom#{}')
        super(NatGatewayCommandsLoader, self).__init__(
            cli_ctx=cli_ctx,
            resource_type=ResourceType.MGMT_NETWORK,
            custom_command_type=natgateway_custom
        )

    def load_command_table(self, args):
        from azure.cli.command_modules.natgateway.commands import load_command_table
        load_command_table(self, args)
        return self.command_table

    def load_arguments(self, command):
        from azure.cli.command_modules.natgateway._params import load_arguments
        load_arguments(self, command)


COMMAND_LOADER_CLS = NatGatewayCommandsLoader
