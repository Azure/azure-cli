# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.maps._client_factory import cf_accounts, cf_map, cf_creator


def load_command_table(self, _):
    mgmt_type = CliCommandType(
        operations_tmpl='azure.mgmt.maps.operations._accounts_operations#AccountsOperations.{}',
        client_factory=cf_accounts)

    with self.command_group('maps account', mgmt_type) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_accounts')
        g.custom_command('create', 'maps_account_create')
        g.command('delete', 'delete')
        g.custom_command('update', 'maps_account_update')

    with self.command_group('maps account keys', mgmt_type) as g:
        g.custom_command('renew', 'maps_account_regenerate_key')
        g.custom_command('list', 'maps_account_list_key')

    maps_map = CliCommandType(
        operations_tmpl='azure.mgmt.maps.operations._maps_operations#MapsOperations.{}',
        client_factory=cf_map)

    with self.command_group('maps map', maps_map, client_factory=cf_map) as g:
        g.custom_command('list-operation', 'maps_map_list_operation')

    maps_creator = CliCommandType(
        operations_tmpl='azure.mgmt.maps.operations._creators_operations#CreatorsOperations.{}',
        client_factory=cf_creator)
    with self.command_group('maps creator', maps_creator, client_factory=cf_creator) as g:
        g.custom_command('list', 'maps_creator_list')
        g.custom_show_command('show', 'maps_creator_show')
        g.custom_command('create', 'maps_creator_create')
        g.custom_command('update', 'maps_creator_update')
        g.custom_command('delete', 'maps_creator_delete', confirmation=True)
