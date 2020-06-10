# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
# pylint: disable=too-many-statements

from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.cosmosdb._client_factory import (
    cf_db_accounts,
    cf_db_private_endpoint_connections,
    cf_db_private_link_resources,
    cf_sql_resources,
    cf_mongo_db_resources,
    cf_cassandra_resources,
    cf_gremlin_resources,
    cf_table_resources
)

from azure.cli.command_modules.cosmosdb._format import (
    database_output,
    list_database_output,
    collection_output,
    list_collection_output,
    list_connection_strings_output
)

from ._validators import (
    validate_private_endpoint_connection_id
)

DATABASE_DEPRECATION_INFO = 'cosmosdb sql database, cosmosdb mongodb database, cosmosdb cassandra keyspace or cosmosdb gremlin database'

COLLECTION_DEPRECATON_INFO = 'cosmosdb sql container, cosmosdb mongodb collection, cosmosdb cassandra table, cosmosdb gremlin graph or cosmosdb table'


def load_command_table(self, _):

    cosmosdb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#DatabaseAccountsOperations.{}',
        client_factory=cf_db_accounts)

    cosmosdb_private_endpoint_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=cf_db_private_endpoint_connections)

    cosmosdb_private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#PrivateLinkResourcesOperations.{}',
        client_factory=cf_db_private_link_resources)

    cosmosdb_sql_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#SqlResourcesOperations.{}',
        client_factory=cf_sql_resources)

    cosmosdb_mongo_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#MongoDBResourcesOperations.{}',
        client_factory=cf_mongo_db_resources)

    cosmosdb_cassandra_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#CassandraResourcesOperations.{}',
        client_factory=cf_cassandra_resources)

    cosmosdb_gremlin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#GremlinResourcesOperations.{}',
        client_factory=cf_gremlin_resources)

    cosmosdb_table_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#TableResourcesOperations.{}',
        client_factory=cf_table_resources)

    with self.command_group('cosmosdb', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.show_command('show', 'get')
        g.command('list-keys', 'list_keys', deprecate_info=g.deprecate(redirect='cosmosdb keys list', hide=True))
        g.command('list-read-only-keys', 'list_read_only_keys', deprecate_info=g.deprecate(redirect='cosmosdb keys list --type read-only-keys', hide=True))
        g.command('list-connection-strings', 'list_connection_strings', table_transformer=list_connection_strings_output, deprecate_info=g.deprecate(redirect='cosmosdb keys list --type connection-strings', hide=True))
        g.command('regenerate-key', 'regenerate_key', deprecate_info=g.deprecate(redirect='cosmosdb keys regenerate', hide=True))
        g.command('check-name-exists', 'check_name_exists')
        g.command('delete', 'delete', confirmation=True)
        g.command('failover-priority-change', 'failover_priority_change')
        g.custom_command('create', 'cli_cosmosdb_create')
        g.custom_command('update', 'cli_cosmosdb_update')
        g.custom_command('list', 'cli_cosmosdb_list')

    with self.command_group('cosmosdb private-endpoint-connection',
                            cosmosdb_private_endpoint_connections_sdk,
                            client_factory=cf_db_private_endpoint_connections) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.command('delete', 'delete', validator=validate_private_endpoint_connection_id)
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)

    with self.command_group('cosmosdb private-link-resource',
                            cosmosdb_private_link_resources_sdk,
                            client_factory=cf_db_private_link_resources) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.show_command('list', 'list_by_database_account', transform=gen_dict_to_list_transform(key='values'))

    # SQL api
    with self.command_group('cosmosdb sql', is_preview=True):
        pass
    with self.command_group('cosmosdb sql database', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_database_create')
        g.command('list', 'list_sql_databases')
        g.command('show', 'get_sql_database')
        g.command('delete', 'delete_sql_database', confirmation=True)

    with self.command_group('cosmosdb sql container', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_container_create')
        g.custom_command('update', 'cli_cosmosdb_sql_container_update')
        g.command('list', 'list_sql_containers')
        g.command('show', 'get_sql_container')
        g.command('delete', 'delete_sql_container', confirmation=True)

    with self.command_group('cosmosdb sql stored-procedure', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_stored_procedure_create_update')
        g.custom_command('update', 'cli_cosmosdb_sql_stored_procedure_create_update')
        g.command('list', 'list_sql_stored_procedures')
        g.command('show', 'get_sql_stored_procedure')
        g.command('delete', 'delete_sql_stored_procedure', confirmation=True)

    with self.command_group('cosmosdb sql trigger', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_trigger_create')
        g.custom_command('update', 'cli_cosmosdb_sql_trigger_update')
        g.command('list', 'list_sql_triggers')
        g.command('show', 'get_sql_trigger')
        g.command('delete', 'delete_sql_trigger', confirmation=True)

    with self.command_group('cosmosdb sql user-defined-function', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_user_defined_function_create_update')
        g.custom_command('update', 'cli_cosmosdb_sql_user_defined_function_create_update')
        g.command('list', 'list_sql_user_defined_functions')
        g.command('show', 'get_sql_user_defined_function')
        g.command('delete', 'delete_sql_user_defined_function', confirmation=True)

    # MongoDB api
    with self.command_group('cosmosdb mongodb', is_preview=True):
        pass
    with self.command_group('cosmosdb mongodb database', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_database_create')
        g.command('list', 'list_mongo_db_databases')
        g.command('show', 'get_mongo_db_database')
        g.command('delete', 'delete_mongo_db_database', confirmation=True)

    with self.command_group('cosmosdb mongodb collection', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_collection_create')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_update')
        g.command('list', 'list_mongo_db_collections')
        g.command('show', 'get_mongo_db_collection')
        g.command('delete', 'delete_mongo_db_collection', confirmation=True)

    # Cassandra api
    with self.command_group('cosmosdb cassandra', is_preview=True):
        pass
    with self.command_group('cosmosdb cassandra keyspace', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_keyspace_create')
        g.command('list', 'list_cassandra_keyspaces')
        g.command('show', 'get_cassandra_keyspace')
        g.command('delete', 'delete_cassandra_keyspace', confirmation=True)

    with self.command_group('cosmosdb cassandra table', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_table_create')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_update')
        g.command('list', 'list_cassandra_tables')
        g.command('show', 'get_cassandra_table')
        g.command('delete', 'delete_cassandra_table', confirmation=True)

    # Gremlin api
    with self.command_group('cosmosdb gremlin', is_preview=True):
        pass
    with self.command_group('cosmosdb gremlin database', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_database_create')
        g.command('list', 'list_gremlin_databases')
        g.command('show', 'get_gremlin_database')
        g.command('delete', 'delete_gremlin_database', confirmation=True)

    with self.command_group('cosmosdb gremlin graph', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_graph_create')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_update')
        g.command('list', 'list_gremlin_graphs')
        g.command('show', 'get_gremlin_graph')
        g.command('delete', 'delete_gremlin_graph', confirmation=True)

    # Table api
    with self.command_group('cosmosdb table', cosmosdb_table_sdk, client_factory=cf_table_resources, is_preview=True) as g:
        g.custom_command('create', 'cli_cosmosdb_table_create')
        g.command('list', 'list_tables')
        g.command('show', 'get_table')
        g.command('delete', 'delete_table', confirmation=True)

    # Offer throughput
    with self.command_group('cosmosdb sql database throughput', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.command('show', 'get_sql_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_sql_database_throughput_update')

    with self.command_group('cosmosdb sql container throughput', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.command('show', 'get_sql_container_throughput')
        g.custom_command('update', 'cli_cosmosdb_sql_container_throughput_update')

    with self.command_group('cosmosdb mongodb database throughput', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.command('show', 'get_mongo_db_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_database_throughput_update')

    with self.command_group('cosmosdb mongodb collection throughput', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.command('show', 'get_mongo_db_collection_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_throughput_update')

    with self.command_group('cosmosdb cassandra keyspace throughput', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.command('show', 'get_cassandra_keyspace_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_keyspace_throughput_update')

    with self.command_group('cosmosdb cassandra table throughput', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.command('show', 'get_cassandra_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_throughput_update')

    with self.command_group('cosmosdb gremlin database throughput', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.command('show', 'get_gremlin_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_database_throughput_update')

    with self.command_group('cosmosdb gremlin graph throughput', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.command('show', 'get_gremlin_graph_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_throughput_update')

    with self.command_group('cosmosdb table throughput', cosmosdb_table_sdk, client_factory=cf_table_resources) as g:
        g.command('show', 'get_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_table_throughput_update')

    # virtual network rules
    with self.command_group('cosmosdb network-rule', None, client_factory=cf_db_accounts) as g:
        g.custom_command('list', 'cli_cosmosdb_network_rule_list')
        g.custom_command('add', 'cli_cosmosdb_network_rule_add')
        g.custom_command('remove', 'cli_cosmosdb_network_rule_remove')

    # key operations
    with self.command_group('cosmosdb keys', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('list', 'cli_cosmosdb_keys', table_transformer=list_connection_strings_output)
        g.command('regenerate', 'regenerate_key')

    # # database operations
    with self.command_group('cosmosdb database', deprecate_info=self.deprecate(redirect=DATABASE_DEPRECATION_INFO, hide=True)) as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_database_show', table_transformer=database_output)
        g.cosmosdb_custom('list', 'cli_cosmosdb_database_list', table_transformer=list_database_output)
        g.cosmosdb_custom('exists', 'cli_cosmosdb_database_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_database_create', table_transformer=database_output)
        g.cosmosdb_custom('delete', 'cli_cosmosdb_database_delete', confirmation=True)

    # collection operations
    with self.command_group('cosmosdb collection', deprecate_info=self.deprecate(redirect=COLLECTION_DEPRECATON_INFO, hide=True)) as g:
        g.cosmosdb_custom('show', 'cli_cosmosdb_collection_show', table_transformer=collection_output)
        g.cosmosdb_custom('list', 'cli_cosmosdb_collection_list', table_transformer=list_collection_output)
        g.cosmosdb_custom('exists', 'cli_cosmosdb_collection_exists')
        g.cosmosdb_custom('create', 'cli_cosmosdb_collection_create', table_transformer=collection_output)
        g.cosmosdb_custom('delete', 'cli_cosmosdb_collection_delete', confirmation=True)
        g.cosmosdb_custom('update', 'cli_cosmosdb_collection_update')
