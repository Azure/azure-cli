# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.maps._client_factory import cf_accounts


def load_command_table(self, _):
    mgmt_type = CliCommandType(
        operations_tmpl='azure.mgmt.maps.operations#AccountsOperations.{}',
        client_factory=cf_accounts)

    with self.command_group('maps account', mgmt_type) as g:
        g.show_command('show', 'get')
        g.custom_command('list', 'list_accounts')
        g.custom_command('create', 'create_account')
        g.command('delete', 'delete')
        g.generic_update_command('update',
                                 getter_name='get',
                                 setter_arg_name='maps_account_create_parameters',
                                 custom_func_name='generic_update_account')

    with self.command_group('maps account keys', mgmt_type) as g:
        g.command('renew', 'regenerate_keys')
        g.command('list', 'list_keys')
