# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.dls._client_factory import (
    cf_dls_account,
    cf_dls_account_firewall,
    cf_dls_account_trusted_provider)


# pylint: disable=too-many-statements
def load_command_table(self, _):
    adls_format_path = 'azure.mgmt.datalake.store.operations#{}.{{}}'

    dls_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.dls.custom#{}')

    dls_account_sdk = CliCommandType(
        operations_tmpl=adls_format_path.format('AccountsOperations'),
        client_factory=cf_dls_account
    )

    dls_firewall_sdk = CliCommandType(
        operations_tmpl=adls_format_path.format('FirewallRulesOperations'),
        client_factory=cf_dls_account
    )

    dls_provider_sdk = CliCommandType(
        operations_tmpl=adls_format_path.format('TrustedIdProvidersOperations'),
        client_factory=cf_dls_account_trusted_provider
    )

    # account operations
    with self.command_group('dls account', dls_account_sdk, client_factory=cf_dls_account) as g:
        g.custom_command('create', 'create_adls_account')
        g.custom_command('update', 'update_adls_account')
        g.custom_command('list', 'list_adls_account')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('enable-key-vault', 'enable_key_vault')

    # account firewall operations
    with self.command_group('dls account firewall', dls_firewall_sdk, client_factory=cf_dls_account_firewall) as g:
        g.custom_command('create', 'add_adls_firewall_rule')
        g.custom_command('update', 'update_adls_firewall_rule')
        g.command('list', 'list_by_account')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    # account trusted id provider operations
    with self.command_group('dls account trusted-provider', dls_provider_sdk, client_factory=cf_dls_account_trusted_provider) as g:
        g.custom_command('create', 'add_trusted_provider_rule')
        g.custom_command('update', 'update_trusted_provider_rule')
        g.command('list', 'list_by_account')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    # filesystem operations
    with self.command_group('dls fs', dls_custom) as g:
        g.show_command('show', 'get_adls_item')
        g.command('list', 'list_adls_items')
        g.command('create', 'create_adls_item')
        g.command('append', 'append_adls_item')
        g.command('delete', 'remove_adls_item')
        g.command('upload', 'upload_to_adls')
        g.command('download', 'download_from_adls')
        g.command('download', 'download_from_adls')
        g.command('test', 'test_adls_item')
        g.command('preview', 'preview_adls_item')
        g.command('join', 'join_adls_items')
        g.command('move', 'move_adls_item')
        g.command('set-expiry', 'set_adls_item_expiry')
        g.command('remove-expiry', 'remove_adls_item_expiry')

    # filesystem permission operations
    with self.command_group('dls fs access', dls_custom) as g:
        g.command('set-permission', 'set_adls_item_permissions')
        g.command('set-owner', 'set_adls_item_owner')
        g.show_command('show', 'get_adls_item_acl')
        g.command('set-entry', 'set_adls_item_acl_entry')
        g.command('set', 'set_adls_item_acl')
        g.command('remove-entry', 'remove_adls_item_acl_entry')
        g.command('remove-all', 'remove_adls_item_acl')

    with self.command_group('dls', is_preview=True):
        pass
