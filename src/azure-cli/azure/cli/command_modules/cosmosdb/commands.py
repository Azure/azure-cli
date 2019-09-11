# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.cosmosdb._client_factory import cf_db_accounts

from azure.cli.command_modules.cosmosdb._format import (
    database_output,
    list_database_output,
    collection_output,
    list_collection_output,
    list_connection_strings_output
)


def load_command_table(self, _):

    cosmosdb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#DatabaseAccountsOperations.{}',
        client_factory=cf_db_accounts)

    cosmosdb_custom_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.cosmosdb.custom#{}',
        client_factory=cf_db_accounts
    )

    with self.command_group('cosmosdb', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.show_command('show', 'get')
        g.command('list-keys', 'list_keys', deprecate_info=g.deprecate(redirect='cosmosdb keys list', hide=True))
        g.command('list-read-only-keys', 'list_read_only_keys')
        g.command('list-connection-strings', 'list_connection_strings', table_transformer=list_connection_strings_output)
        g.command('regenerate-key', 'regenerate_key')
        g.command('check-name-exists', 'check_name_exists')
        g.command('delete', 'delete')
        g.command('failover-priority-change', 'failover_priority_change')
        g.custom_command('create', 'cli_cosmosdb_create')
        g.custom_command('update', 'cli_cosmosdb_update')
        g.custom_command('list', 'cli_cosmosdb_list')

    # SQL api
    with self.command_group('cosmosdb sql', is_preview=True):
        pass
    with self.command_group('cosmosdb sql database', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_database_create')
        g.command('list', 'list_sql_databases')
        g.command('show', 'get_sql_database')
        g.command('delete', 'delete_sql_database')

    with self.command_group('cosmosdb sql container', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_container_create')
        g.custom_command('update', 'cli_cosmosdb_sql_container_update')
        g.command('list', 'list_sql_containers')
        g.command('show', 'get_sql_container')
        g.command('delete', 'delete_sql_container')

    # MongoDB api
    with self.command_group('cosmosdb mongodb', is_preview=True):
        pass
    with self.command_group('cosmosdb mongodb database', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_database_create')
        g.command('list', 'list_mongo_db_databases')
        g.command('show', 'get_mongo_db_database')
        g.command('delete', 'delete_mongo_db_database')

    with self.command_group('cosmosdb mongodb collection', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_collection_create')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_update')
        g.command('list', 'list_mongo_db_collections')
        g.command('show', 'get_mongo_db_collection')
        g.command('delete', 'delete_mongo_db_collection')

    # Cassandra api
    with self.command_group('cosmosdb cassandra', is_preview=True):
        pass
    with self.command_group('cosmosdb cassandra keyspace', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_keyspace_create')
        g.command('list', 'list_cassandra_keyspaces')
        g.command('show', 'get_cassandra_keyspace')
        g.command('delete', 'delete_cassandra_keyspace')

    with self.command_group('cosmosdb cassandra table', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_table_create')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_update')
        g.command('list', 'list_cassandra_tables')
        g.command('show', 'get_cassandra_table')
        g.command('delete', 'delete_cassandra_table')

    # Gremlin api
    with self.command_group('cosmosdb gremlin', is_preview=True):
        pass
    with self.command_group('cosmosdb gremlin database', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_database_create')
        g.command('list', 'list_gremlin_databases')
        g.command('show', 'get_gremlin_database')
        g.command('delete', 'delete_gremlin_database')

    with self.command_group('cosmosdb gremlin graph', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_graph_create')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_update')
        g.command('list', 'list_gremlin_graphs')
        g.command('show', 'get_gremlin_graph')
        g.command('delete', 'delete_gremlin_graph')

    # Table api
    with self.command_group('cosmosdb table', cosmosdb_sdk, client_factory=cf_db_accounts, is_preview=True) as g:
        g.custom_command('create', 'cli_cosmosdb_table_create')
        g.command('list', 'list_tables')
        g.command('show', 'get_table')
        g.command('delete', 'delete_table')

    # Offer throughput
    with self.command_group('cosmosdb sql database throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_sql_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_sql_database_throughput_update')

    with self.command_group('cosmosdb sql container throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_sql_container_throughput')
        g.custom_command('update', 'cli_cosmosdb_sql_container_throughput_update')

    with self.command_group('cosmosdb mongodb database throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_mongo_db_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_database_throughput_update')

    with self.command_group('cosmosdb mongodb collection throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_mongo_db_collection_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_throughput_update')

    with self.command_group('cosmosdb cassandra keyspace throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_cassandra_keyspace_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_keyspace_throughput_update')

    with self.command_group('cosmosdb cassandra table throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_cassandra_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_throughput_update')

    with self.command_group('cosmosdb gremlin database throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_gremlin_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_database_throughput_update')

    with self.command_group('cosmosdb gremlin graph throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_gremlin_graph_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_throughput_update')

    with self.command_group('cosmosdb table throughput', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.command('show', 'get_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_table_throughput_update')

    # virtual network rules
    with self.command_group('cosmosdb network-rule', cosmosdb_custom_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('list', 'cli_cosmosdb_network_rule_list')
        g.custom_command('add', 'cli_cosmosdb_network_rule_add')
        g.custom_command('remove', 'cli_cosmosdb_network_rule_remove')

    # key operations
    with self.command_group('cosmosdb keys', cosmosdb_sdk) as g:
        g.command('list', 'list_keys')

    # # database operations
    with self.command_group('cosmosdb database') as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_database_show', table_transformer=database_output)
        g.cosmosdb_custom('list', 'cli_cosmosdb_database_list', table_transformer=list_database_output)
        g.cosmosdb_custom('exists', 'cli_cosmosdb_database_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_database_create', table_transformer=database_output)
        g.cosmosdb_custom('delete', 'cli_cosmosdb_database_delete')

    # collection operations
    with self.command_group('cosmosdb collection') as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_collection_show', table_transformer=collection_output)
        g.cosmosdb_custom('list', 'cli_cosmosdb_collection_list', table_transformer=list_collection_output)
        g.cosmosdb_custom('exists', 'cli_cosmosdb_collection_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_collection_create', table_transformer=collection_output)
        g.cosmosdb_custom('delete', 'cli_cosmosdb_collection_delete')
        g.cosmosdb_custom('update', 'cli_cosmosdb_collection_update')
