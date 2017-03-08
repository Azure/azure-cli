# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

from azure.cli.core.commands import cli_command
from azure.cli.command_modules.datalake.store._client_factory import (cf_datalake_store_account,
                                                                      cf_datalake_store_account_firewall,
                                                                      cf_datalake_store_account_trusted_provider)
adls_format_path = 'azure.mgmt.datalake.store.operations.{}#{}.{}'
adls_custom_format_path = 'azure.cli.command_modules.datalake.store.custom#{}'

# account operations
cli_command(__name__, 'datalake store account create', adls_custom_format_path.format('create_adls_account'), cf_datalake_store_account)
cli_command(__name__, 'datalake store account update', adls_custom_format_path.format('update_adls_account'), cf_datalake_store_account)
cli_command(__name__, 'datalake store account list', adls_custom_format_path.format('list_adls_account'), cf_datalake_store_account)
cli_command(__name__, 'datalake store account delete', adls_format_path.format('account_operations', 'AccountOperations', 'delete'), cf_datalake_store_account)
cli_command(__name__, 'datalake store account show', adls_format_path.format('account_operations', 'AccountOperations', 'get'), cf_datalake_store_account)

# account firewall operations
cli_command(__name__, 'datalake store account firewall create', adls_custom_format_path.format('add_adls_firewall_rule'), cf_datalake_store_account_firewall)
cli_command(__name__, 'datalake store account firewall update', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'update'), cf_datalake_store_account_firewall)
cli_command(__name__, 'datalake store account firewall list', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'list_by_account'), cf_datalake_store_account_firewall)
cli_command(__name__, 'datalake store account firewall show', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'get'), cf_datalake_store_account_firewall)
cli_command(__name__, 'datalake store account firewall delete', adls_format_path.format('firewall_rules_operations', 'FirewallRulesOperations', 'delete'), cf_datalake_store_account_firewall)

# account trusted id provider operations
cli_command(__name__, 'datalake store account trusted-provider create', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'create_or_update'), cf_datalake_store_account_trusted_provider)
cli_command(__name__, 'datalake store account trusted-provider update', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'update'), cf_datalake_store_account_trusted_provider)
cli_command(__name__, 'datalake store account trusted-provider list', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'list_by_account'), cf_datalake_store_account_trusted_provider)
cli_command(__name__, 'datalake store account trusted-provider show', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'get'), cf_datalake_store_account_trusted_provider)
cli_command(__name__, 'datalake store account trusted-provider delete', adls_format_path.format('trusted_id_providers_operations', 'TrustedIdProvidersOperations', 'delete'), cf_datalake_store_account_trusted_provider)

# filesystem operations
cli_command(__name__, 'datalake store file show', adls_custom_format_path.format('get_adls_item'))
cli_command(__name__, 'datalake store file list', adls_custom_format_path.format('list_adls_items'))
cli_command(__name__, 'datalake store file create', adls_custom_format_path.format('create_adls_item'))
cli_command(__name__, 'datalake store file append', adls_custom_format_path.format('append_adls_item'))
cli_command(__name__, 'datalake store file delete', adls_custom_format_path.format('remove_adls_item'))
cli_command(__name__, 'datalake store file upload', adls_custom_format_path.format('upload_to_adls'))
cli_command(__name__, 'datalake store file download', adls_custom_format_path.format('download_from_adls'))
cli_command(__name__, 'datalake store file download', adls_custom_format_path.format('download_from_adls'))
cli_command(__name__, 'datalake store file test', adls_custom_format_path.format('test_adls_item'))
cli_command(__name__, 'datalake store file preview', adls_custom_format_path.format('preview_adls_item'))
cli_command(__name__, 'datalake store file join', adls_custom_format_path.format('join_adls_items'))
cli_command(__name__, 'datalake store file move', adls_custom_format_path.format('move_adls_item'))
# todo implement set expiry when it is available

# filesystem permission operations
# todo: implement acl CRUD when available
cli_command(__name__, 'datalake store file set-permission', adls_custom_format_path.format('set_adls_item_permissions'))
cli_command(__name__, 'datalake store file set-owner', adls_custom_format_path.format('set_adls_item_owner'))
