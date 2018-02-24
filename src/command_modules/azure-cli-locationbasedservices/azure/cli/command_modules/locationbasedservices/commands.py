# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.locationbasedservices._client_factory import cf_accounts


def load_command_table(self, _):
    mgmt_type = CliCommandType(
        operations_tmpl='azure.mgmt.locationbasedservices.operations.accounts_operations#AccountsOperations.{}',
        client_factory=cf_accounts)

    with self.command_group('locationbasedservices account', mgmt_type) as g:
        g.command('show', 'get')
        g.custom_command('list', 'list_accounts')
        g.custom_command('create', 'create')
        g.command('delete', 'delete')

    with self.command_group('locationbasedservices account key', mgmt_type) as g:
        g.command('regenerate', 'regenerate_keys')
        g.command('list', 'list_keys')
