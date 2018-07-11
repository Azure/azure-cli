# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.cosmosdb._client_factory import cf_db_accounts


def load_command_table(self, _):

    cosmosdb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations.database_accounts_operations#DatabaseAccountsOperations.{}',
        client_factory=cf_db_accounts)

    with self.command_group('cosmosdb', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.show_command('show', 'get')
        g.command('list-keys', 'list_keys')
        g.command('list-read-only-keys', 'list_read_only_keys')
        g.command('list-connection-strings', 'list_connection_strings')
        g.command('regenerate-key', 'regenerate_key')
        g.command('check-name-exists', 'check_name_exists')
        g.command('delete', 'delete')
        g.command('failover-priority-change', 'failover_priority_change')
        g.custom_command('create', 'cli_cosmosdb_create')
        g.custom_command('update', 'cli_cosmosdb_update')
        g.custom_command('list', 'cli_cosmosdb_list')

    # # database operations
    with self.command_group('cosmosdb database') as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_database_show')
        g.cosmosdb_custom('list', 'cli_cosmosdb_database_list')
        g.cosmosdb_custom('exists', 'cli_cosmosdb_database_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_database_create')
        g.cosmosdb_custom('delete', 'cli_cosmosdb_database_delete')

    # collection operations
    with self.command_group('cosmosdb collection') as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_collection_show')
        g.cosmosdb_custom('list', 'cli_cosmosdb_collection_list')
        g.cosmosdb_custom('exists', 'cli_cosmosdb_collection_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_collection_create')
        g.cosmosdb_custom('delete', 'cli_cosmosdb_collection_delete')
        g.cosmosdb_custom('update', 'cli_cosmosdb_collection_update')
