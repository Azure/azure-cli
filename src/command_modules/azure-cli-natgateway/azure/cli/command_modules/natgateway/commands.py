# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType


def load_command_table(self, _):
    natgateway = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NatGatewayOperations.{}',
        client_factory=cf_natgateway)

    with self.command_group('network nat-gateway', natgateway) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_natgateways')
        g.custom_command('create', 'create_natgateway')
        g.command('delete', 'delete')
