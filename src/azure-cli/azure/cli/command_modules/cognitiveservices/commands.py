# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.cognitiveservices._client_factory import cf_accounts, cf_resource_skus


def load_command_table(self, _):
    mgmt_type = CliCommandType(
        operations_tmpl='azure.mgmt.cognitiveservices.operations#AccountsOperations.{}',
        client_factory=cf_accounts
    )

    with self.command_group('cognitiveservices account', mgmt_type) as g:
        g.custom_command('create', 'create')
        g.command('delete', 'delete')
        g.show_command('show', 'get_properties')
        g.custom_command('update', 'update')
        g.custom_command('list', 'list_resources')
        g.custom_command('list-skus', 'list_skus')
        g.custom_command('list-usage', 'list_usages')
        g.custom_command('list-kinds', 'list_kinds', client_factory=cf_resource_skus)

    with self.command_group('cognitiveservices account keys', mgmt_type) as g:
        g.command('regenerate', 'regenerate_key')
        g.command('list', 'list_keys')

    # deprecating this
    with self.command_group('cognitiveservices') as g:
        g.custom_command('list', 'list_resources',
                         deprecate_info=g.deprecate(redirect='az cognitiveservices account list', hide=True))

    with self.command_group('cognitiveservices account network-rule', mgmt_type, client_factory=cf_accounts) as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('list', 'list_network_rules')
        g.custom_command('remove', 'remove_network_rule')

    with self.command_group('cognitiveservices account identity', mgmt_type, client_factory=cf_accounts) as g:
        g.custom_command('assign', 'identity_assign')
        g.custom_command('remove', 'identity_remove')
        g.custom_show_command('show', 'identity_show')
