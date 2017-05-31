# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import cli_command
from azure.cli.command_modules.dls._client_factory import (cf_dls_account,
                                                           cf_dls_account_firewall,
                                                           cf_dls_account_trusted_provider)
adls_format_path = 'azure.mgmt.datalake.store.operations.{}#{}.{}'
adls_custom_format_path = 'azure.cli.command_modules.dls.custom#{}'

# account operations
cli_command(__name__, 'dls account create', adls_custom_format_path.format('create_adls_account'), cf_dls_account)
cli_command(__name__, 'dls account update', adls_custom_format_path.format('update_adls_account'), cf_dls_account)
cli_command(__name__, 'dls account list', adls_custom_format_path.format('list_adls_account'), cf_dls_account)
cli_command(__name__, 'dls account delete', adls_format_path.format('account_operations', 'AccountOperations', 'delete'), cf_dls_account)
cli_command(__name__, 'dls account show', adls_format_path.format('account_operations', 'AccountOperations', 'get'), cf_dls_account)
cli_command(__name__, 'dls account enable-key-vault', adls_format_path.format('account_operations', 'AccountOperations', 'enable_key_vault'), cf_dls_account)

# account firewall operations
cli_command(__name__, 'dls account firewall create', adls_custom_format_path.format('add_adls_firewall_rule'), cf_dls_account_firewall)
cli_command(__name__, 'dls account firewall update', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'update'), cf_dls_account_firewall)
cli_command(__name__, 'dls account firewall list', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'list_by_account'), cf_dls_account_firewall)
cli_command(__name__, 'dls account firewall show', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'get'), cf_dls_account_firewall)
cli_command(__name__, 'dls account firewall delete', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'delete'), cf_dls_account_firewall)

# account trusted id provider operations
cli_command(__name__, 'dls account trusted-provider create', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'create_or_update'), cf_dls_account_trusted_provider)
cli_command(__name__, 'dls account trusted-provider update', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'update'), cf_dls_account_trusted_provider)
cli_command(__name__, 'dls account trusted-provider list', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'list_by_account'), cf_dls_account_trusted_provider)
cli_command(__name__, 'dls account trusted-provider show', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'get'), cf_dls_account_trusted_provider)
cli_command(__name__, 'dls account trusted-provider delete', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'delete'), cf_dls_account_trusted_provider)

# filesystem operations
cli_command(__name__, 'dls fs show', adls_custom_format_path.format('get_adls_item'))
cli_command(__name__, 'dls fs list', adls_custom_format_path.format('list_adls_items'))
cli_command(__name__, 'dls fs create', adls_custom_format_path.format('create_adls_item'))
cli_command(__name__, 'dls fs append', adls_custom_format_path.format('append_adls_item'))
cli_command(__name__, 'dls fs delete', adls_custom_format_path.format('remove_adls_item'))
cli_command(__name__, 'dls fs upload', adls_custom_format_path.format('upload_to_adls'))
cli_command(__name__, 'dls fs download', adls_custom_format_path.format('download_from_adls'))
cli_command(__name__, 'dls fs download', adls_custom_format_path.format('download_from_adls'))
cli_command(__name__, 'dls fs test', adls_custom_format_path.format('test_adls_item'))
cli_command(__name__, 'dls fs preview', adls_custom_format_path.format('preview_adls_item'))
cli_command(__name__, 'dls fs join', adls_custom_format_path.format('join_adls_items'))
cli_command(__name__, 'dls fs move', adls_custom_format_path.format('move_adls_item'))
cli_command(__name__, 'dls fs set-expiry', adls_custom_format_path.format('set_adls_item_expiry'))
cli_command(__name__, 'dls fs remove-expiry', adls_custom_format_path.format('remove_adls_item_expiry'))

# filesystem permission operations
cli_command(__name__, 'dls fs access set-permission', adls_custom_format_path.format('set_adls_item_permissions'))
cli_command(__name__, 'dls fs access set-owner', adls_custom_format_path.format('set_adls_item_owner'))
cli_command(__name__, 'dls fs access show', adls_custom_format_path.format('get_adls_item_acl'))
cli_command(__name__, 'dls fs access set-entry', adls_custom_format_path.format('set_adls_item_acl_entry'))
cli_command(__name__, 'dls fs access set', adls_custom_format_path.format('set_adls_item_acl'))
cli_command(__name__, 'dls fs access remove-entry', adls_custom_format_path.format('remove_adls_item_acl_entry'))
cli_command(__name__, 'dls fs access remove-all', adls_custom_format_path.format('remove_adls_item_acl'))
