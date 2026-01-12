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
    cf_table_resources,
    cf_restorable_database_accounts,
    cf_restorable_sql_databases,
    cf_restorable_sql_containers,
    cf_restorable_sql_resources,
    cf_restorable_mongodb_databases,
    cf_restorable_mongodb_collections,
    cf_restorable_mongodb_resources,
    cf_restorable_gremlin_databases,
    cf_restorable_gremlin_graphs,
    cf_restorable_gremlin_resources,
    cf_restorable_tables,
    cf_restorable_table_resources,
    cf_db_locations,
    cf_cassandra_cluster,
    cf_cassandra_data_center,
    cf_service,
    cf_fleet,
    cf_fleetspace,
    cf_fleetspace_account
)

from azure.cli.command_modules.cosmosdb._format import (
    database_output,
    list_database_output,
    collection_output,
    list_collection_output,
    list_connection_strings_output,
    mc_cluster_status_output_table,
)

from azure.cli.command_modules.cosmosdb._transformers import (
    transform_network_rule_list_output,
    transform_db_account_json_output,
    transform_db_account_list_output
)

from ._validators import (
    validate_private_endpoint_connection_id
)

DATABASE_DEPRECATION_INFO = 'cosmosdb sql database, cosmosdb mongodb database, cosmosdb cassandra keyspace or cosmosdb gremlin database'

COLLECTION_DEPRECATON_INFO = 'cosmosdb sql container, cosmosdb mongodb collection, cosmosdb cassandra table, cosmosdb gremlin graph or cosmosdb table'


# pylint: disable=too-many-statements,line-too-long,too-many-locals
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

    cosmosdb_restorable_database_accounts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableDatabaseAccountsOperations.{}',
        client_factory=cf_restorable_database_accounts)

    cosmosdb_sql_restorable_database_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableSqlDatabasesOperations.{}',
        client_factory=cf_restorable_sql_databases)

    cosmosdb_sql_restorable_container_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableSqlContainersOperations.{}',
        client_factory=cf_restorable_sql_containers)

    cosmosdb_sql_restorable_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableSqlResourcesOperations.{}',
        client_factory=cf_restorable_sql_resources)

    cosmosdb_mongodb_restorable_database_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableMongodbDatabasesOperations.{}',
        client_factory=cf_restorable_mongodb_databases)

    cosmosdb_mongodb_restorable_collection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableMongodbCollectionsOperations.{}',
        client_factory=cf_restorable_mongodb_collections)

    cosmosdb_mongodb_restorable_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableMongodbResourcesOperations.{}',
        client_factory=cf_restorable_mongodb_resources)

    cosmosdb_restorable_gremlin_databases_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableGremlinDatabasesOperations.{}',
        client_factory=cf_restorable_gremlin_databases)

    cosmosdb_restorable_gremlin_graphs_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableGremlinGraphsOperations.{}',
        client_factory=cf_restorable_gremlin_graphs)

    cosmosdb_restorable_gremlin_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableGremlinResourcesOperations.{}',
        client_factory=cf_restorable_gremlin_resources)

    cosmosdb_restorable_tables_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableTablesOperations.{}',
        client_factory=cf_restorable_tables)

    cosmosdb_restorable_table_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#RestorableTableResourcesOperations.{}',
        client_factory=cf_restorable_table_resources)

    cosmosdb_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#LocationsOperations.{}',
        client_factory=cf_db_locations)

    cosmosdb_managed_cassandra_cluster_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#CassandraClustersOperations.{}',
        client_factory=cf_cassandra_cluster)

    cosmosdb_managed_cassandra_datacenter_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#CassandraDataCentersOperations.{}',
        client_factory=cf_cassandra_data_center)

    cosmosdb_service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#ServiceOperations.{}',
        client_factory=cf_service)

    with self.command_group('cosmosdb', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.show_command('show', 'get', transform=transform_db_account_json_output)
        g.command('list-keys', 'list_keys', deprecate_info=g.deprecate(redirect='cosmosdb keys list', hide=True))
        g.command('list-read-only-keys', 'list_read_only_keys', deprecate_info=g.deprecate(redirect='cosmosdb keys list --type read-only-keys', hide=True))
        g.command('list-connection-strings', 'list_connection_strings', table_transformer=list_connection_strings_output, deprecate_info=g.deprecate(redirect='cosmosdb keys list --type connection-strings', hide=True))
        g.custom_command('regenerate-key', 'cli_cosmosdb_regenerate_key', deprecate_info=g.deprecate(redirect='cosmosdb keys regenerate', hide=True))
        g.command('check-name-exists', 'check_name_exists')
        g.custom_command('delete', 'cli_cosmosdb_delete', confirmation=True, supports_no_wait=True)
        g.command('failover-priority-change', 'begin_failover_priority_change')
        g.custom_command('offline-region', 'cli_offline_region')
        g.custom_command('create', 'cli_cosmosdb_create', transform=transform_db_account_json_output)
        g.custom_command('update', 'cli_cosmosdb_update', transform=transform_db_account_json_output)
        g.custom_command('list', 'cli_cosmosdb_list', transform=transform_db_account_list_output)
        g.custom_command('restore', 'cli_cosmosdb_restore', transform=transform_db_account_json_output)

    with self.command_group('cosmosdb private-endpoint-connection',
                            cosmosdb_private_endpoint_connections_sdk,
                            client_factory=cf_db_private_endpoint_connections) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'reject_private_endpoint_connection',
                         validator=validate_private_endpoint_connection_id)
        g.command('delete', 'begin_delete', validator=validate_private_endpoint_connection_id)
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)

    with self.command_group('cosmosdb private-link-resource',
                            cosmosdb_private_link_resources_sdk,
                            client_factory=cf_db_private_link_resources) as g:
        from azure.cli.core.commands.transform import gen_dict_to_list_transform
        g.show_command('list', 'list_by_database_account', transform=gen_dict_to_list_transform(key='values'))

    # SQL api
    with self.command_group('cosmosdb sql'):
        pass
    with self.command_group('cosmosdb sql database', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_database_create')
        g.custom_command('exists', 'cli_cosmosdb_sql_database_exists')
        g.command('list', 'list_sql_databases')
        g.show_command('show', 'get_sql_database')
        g.command('delete', 'begin_delete_sql_database', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_sql_database_restore')

    with self.command_group('cosmosdb sql container', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_container_create')
        g.custom_command('update', 'cli_cosmosdb_sql_container_update')
        g.custom_command('exists', 'cli_cosmosdb_sql_container_exists')
        g.command('list', 'list_sql_containers')
        g.show_command('show', 'get_sql_container')
        g.command('delete', 'begin_delete_sql_container', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_sql_container_restore')

    with self.command_group('cosmosdb sql stored-procedure', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_stored_procedure_create_update')
        g.custom_command('update', 'cli_cosmosdb_sql_stored_procedure_create_update')
        g.command('list', 'list_sql_stored_procedures')
        g.show_command('show', 'get_sql_stored_procedure')
        g.command('delete', 'begin_delete_sql_stored_procedure', confirmation=True)

    with self.command_group('cosmosdb sql trigger', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_trigger_create')
        g.custom_command('update', 'cli_cosmosdb_sql_trigger_update')
        g.command('list', 'list_sql_triggers')
        g.show_command('show', 'get_sql_trigger')
        g.command('delete', 'begin_delete_sql_trigger', confirmation=True)

    with self.command_group('cosmosdb sql user-defined-function', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_user_defined_function_create_update')
        g.custom_command('update', 'cli_cosmosdb_sql_user_defined_function_create_update')
        g.command('list', 'list_sql_user_defined_functions')
        g.show_command('show', 'get_sql_user_defined_function')
        g.command('delete', 'begin_delete_sql_user_defined_function', confirmation=True)

    # MongoDB api
    with self.command_group('cosmosdb mongodb'):
        pass
    with self.command_group('cosmosdb mongodb database', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_database_create')
        g.custom_command('exists', 'cli_cosmosdb_mongodb_database_exists')
        g.command('list', 'list_mongo_db_databases')
        g.show_command('show', 'get_mongo_db_database')
        g.command('delete', 'begin_delete_mongo_db_database', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_mongodb_database_restore')

    with self.command_group('cosmosdb mongodb collection', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongodb_collection_create')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_update')
        g.custom_command('exists', 'cli_cosmosdb_mongodb_collection_exists')
        g.command('list', 'list_mongo_db_collections')
        g.show_command('show', 'get_mongo_db_collection')
        g.command('delete', 'begin_delete_mongo_db_collection', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_mongodb_collection_restore')

    # Cassandra api
    with self.command_group('cosmosdb cassandra'):
        pass
    with self.command_group('cosmosdb cassandra keyspace', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_keyspace_create')
        g.custom_command('exists', 'cli_cosmosdb_cassandra_keyspace_exists')
        g.command('list', 'list_cassandra_keyspaces')
        g.show_command('show', 'get_cassandra_keyspace')
        g.command('delete', 'begin_delete_cassandra_keyspace', confirmation=True)

    with self.command_group('cosmosdb cassandra table', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_cassandra_table_create')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_update')
        g.custom_command('exists', 'cli_cosmosdb_cassandra_table_exists')
        g.command('list', 'list_cassandra_tables')
        g.show_command('show', 'get_cassandra_table')
        g.command('delete', 'begin_delete_cassandra_table', confirmation=True)

    # Gremlin api
    with self.command_group('cosmosdb gremlin'):
        pass
    with self.command_group('cosmosdb gremlin database', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_database_create')
        g.custom_command('exists', 'cli_cosmosdb_gremlin_database_exists')
        g.command('list', 'list_gremlin_databases')
        g.show_command('show', 'get_gremlin_database')
        g.command('delete', 'begin_delete_gremlin_database', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_gremlin_database_restore')

    with self.command_group('cosmosdb gremlin graph', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_gremlin_graph_create')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_update')
        g.custom_command('exists', 'cli_cosmosdb_gremlin_graph_exists')
        g.command('list', 'list_gremlin_graphs')
        g.show_command('show', 'get_gremlin_graph')
        g.command('delete', 'begin_delete_gremlin_graph', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_gremlin_graph_restore')

    # Table api
    with self.command_group('cosmosdb table', cosmosdb_table_sdk, client_factory=cf_table_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_table_create')
        g.custom_command('exists', 'cli_cosmosdb_table_exists')
        g.command('list', 'list_tables')
        g.show_command('show', 'get_table')
        g.command('delete', 'begin_delete_table', confirmation=True)
        g.custom_command('restore', 'cli_cosmosdb_table_restore')

    # Offer throughput
    with self.command_group('cosmosdb sql database throughput', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.show_command('show', 'get_sql_database_throughput')
        g.custom_command('migrate', 'cli_cosmosdb_sql_database_throughput_migrate')
        g.custom_command('update', 'cli_cosmosdb_sql_database_throughput_update')

    with self.command_group('cosmosdb sql container throughput', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.show_command('show', 'get_sql_container_throughput')
        g.custom_command('update', 'cli_cosmosdb_sql_container_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_sql_container_throughput_migrate')

    with self.command_group('cosmosdb mongodb database throughput', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.show_command('show', 'get_mongo_db_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_database_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_mongodb_database_throughput_migrate')

    with self.command_group('cosmosdb mongodb collection throughput', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.show_command('show', 'get_mongo_db_collection_throughput')
        g.custom_command('update', 'cli_cosmosdb_mongodb_collection_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_mongodb_collection_throughput_migrate')

    with self.command_group('cosmosdb cassandra keyspace throughput', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.show_command('show', 'get_cassandra_keyspace_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_keyspace_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_cassandra_keyspace_throughput_migrate')

    with self.command_group('cosmosdb cassandra table throughput', cosmosdb_cassandra_sdk, client_factory=cf_cassandra_resources) as g:
        g.show_command('show', 'get_cassandra_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_cassandra_table_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_cassandra_table_throughput_migrate')

    with self.command_group('cosmosdb gremlin database throughput', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.show_command('show', 'get_gremlin_database_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_database_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_gremlin_database_throughput_migrate')

    with self.command_group('cosmosdb gremlin graph throughput', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.show_command('show', 'get_gremlin_graph_throughput')
        g.custom_command('update', 'cli_cosmosdb_gremlin_graph_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_gremlin_graph_throughput_migrate')

    with self.command_group('cosmosdb table throughput', cosmosdb_table_sdk, client_factory=cf_table_resources) as g:
        g.show_command('show', 'get_table_throughput')
        g.custom_command('update', 'cli_cosmosdb_table_throughput_update')
        g.custom_command('migrate', 'cli_cosmosdb_table_throughput_migrate')

    with self.command_group('cosmosdb identity', client_factory=cf_db_accounts, is_preview=True) as g:
        g.custom_show_command('show', 'cli_cosmosdb_identity_show')
        g.custom_command('assign', 'cli_cosmosdb_identity_assign')
        g.custom_command('remove', 'cli_cosmosdb_identity_remove')

    # virtual network rules
    with self.command_group('cosmosdb network-rule', None, client_factory=cf_db_accounts) as g:
        g.custom_command('list', 'cli_cosmosdb_network_rule_list', transform=transform_network_rule_list_output)
        g.custom_command('add', 'cli_cosmosdb_network_rule_add', transform=transform_db_account_json_output)
        g.custom_command('remove', 'cli_cosmosdb_network_rule_remove', transform=transform_db_account_json_output)

    # key operations
    with self.command_group('cosmosdb keys', cosmosdb_sdk, client_factory=cf_db_accounts) as g:
        g.custom_command('list', 'cli_cosmosdb_keys', table_transformer=list_connection_strings_output)
        g.custom_command('regenerate', 'cli_cosmosdb_regenerate_key')

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

    # Mongo role definition operations
    with self.command_group('cosmosdb mongodb role definition', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongo_role_definition_create')
        g.custom_command('update', 'cli_cosmosdb_mongo_role_definition_update')
        g.custom_command('exists', 'cli_cosmosdb_mongo_role_definition_exists')
        g.command('list', 'list_mongo_role_definitions')
        g.show_command('show', 'get_mongo_role_definition')
        g.command('delete', 'begin_delete_mongo_role_definition', confirmation=True)

    # Mongo user definition operations
    with self.command_group('cosmosdb mongodb user definition', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_mongo_user_definition_create')
        g.custom_command('update', 'cli_cosmosdb_mongo_user_definition_update')
        g.custom_command('exists', 'cli_cosmosdb_mongo_user_definition_exists')
        g.command('list', 'list_mongo_user_definitions')
        g.show_command('show', 'get_mongo_user_definition')
        g.command('delete', 'begin_delete_mongo_user_definition', confirmation=True)

    # SQL role definition operations
    with self.command_group('cosmosdb sql role definition', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_role_definition_create', supports_no_wait=True)
        g.custom_command('update', 'cli_cosmosdb_sql_role_definition_update', supports_no_wait=True)
        g.custom_command('exists', 'cli_cosmosdb_sql_role_definition_exists')
        g.command('list', 'list_sql_role_definitions')
        g.show_command('show', 'get_sql_role_definition')
        g.command('delete', 'begin_delete_sql_role_definition', confirmation=True, supports_no_wait=True)
        g.wait_command('wait', 'get_sql_role_definition')

    # SQL role assignment operations
    with self.command_group('cosmosdb sql role assignment', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('create', 'cli_cosmosdb_sql_role_assignment_create', supports_no_wait=True)
        g.custom_command('update', 'cli_cosmosdb_sql_role_assignment_update', supports_no_wait=True)
        g.custom_command('exists', 'cli_cosmosdb_sql_role_assignment_exists')
        g.command('list', 'list_sql_role_assignments')
        g.show_command('show', 'get_sql_role_assignment')
        g.command('delete', 'begin_delete_sql_role_assignment', confirmation=True, supports_no_wait=True)
        g.wait_command('wait', 'get_sql_role_assignment')

    with self.command_group('cosmosdb restorable-database-account', cosmosdb_restorable_database_accounts_sdk, client_factory=cf_restorable_database_accounts) as g:
        g.show_command('show', 'get_by_location')
        g.custom_command('list', 'cli_cosmosdb_restorable_database_account_list')

    with self.command_group('cosmosdb sql restorable-database', cosmosdb_sql_restorable_database_sdk, client_factory=cf_restorable_sql_databases) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb sql restorable-container', cosmosdb_sql_restorable_container_sdk, client_factory=cf_restorable_sql_containers) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb sql restorable-resource', cosmosdb_sql_restorable_resources_sdk, client_factory=cf_restorable_sql_resources) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb mongodb restorable-database', cosmosdb_mongodb_restorable_database_sdk, client_factory=cf_restorable_mongodb_databases) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb mongodb restorable-collection', cosmosdb_mongodb_restorable_collection_sdk, client_factory=cf_restorable_mongodb_collections) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb mongodb restorable-resource', cosmosdb_mongodb_restorable_resources_sdk, client_factory=cf_restorable_mongodb_resources) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb gremlin restorable-database', cosmosdb_restorable_gremlin_databases_sdk, client_factory=cf_restorable_gremlin_databases) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb gremlin restorable-graph', cosmosdb_restorable_gremlin_graphs_sdk, client_factory=cf_restorable_gremlin_graphs) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb gremlin restorable-resource', cosmosdb_restorable_gremlin_resources_sdk, client_factory=cf_restorable_gremlin_resources) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb table restorable-table', cosmosdb_restorable_tables_sdk, client_factory=cf_restorable_tables) as g:
        g.command('list', 'list')

    with self.command_group('cosmosdb table restorable-resource', cosmosdb_restorable_table_resources_sdk, client_factory=cf_restorable_table_resources) as g:
        g.command('list', 'list')

    # Get account locations
    with self.command_group('cosmosdb locations', cosmosdb_locations_sdk, client_factory=cf_db_locations) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')

    # Retrieve backup info for sql
    with self.command_group('cosmosdb sql', cosmosdb_sql_sdk, client_factory=cf_sql_resources) as g:
        g.custom_command('retrieve-latest-backup-time', 'cli_sql_retrieve_latest_backup_time')

    # Retrieve backup info for mongodb
    with self.command_group('cosmosdb mongodb', cosmosdb_mongo_sdk, client_factory=cf_mongo_db_resources) as g:
        g.custom_command('retrieve-latest-backup-time', 'cli_mongo_db_retrieve_latest_backup_time')

    # Retrieve backup info for gremlin
    with self.command_group('cosmosdb gremlin', cosmosdb_gremlin_sdk, client_factory=cf_gremlin_resources) as g:
        g.custom_command('retrieve-latest-backup-time', 'cli_gremlin_retrieve_latest_backup_time')

    # Retrieve backup info for table
    with self.command_group('cosmosdb table', cosmosdb_table_sdk, client_factory=cf_table_resources) as g:
        g.custom_command('retrieve-latest-backup-time', 'cli_table_retrieve_latest_backup_time')

    # managed cassandra cluster
    with self.command_group('managed-cassandra cluster', cosmosdb_managed_cassandra_cluster_sdk, client_factory=cf_cassandra_cluster) as g:
        g.custom_command('create', 'cli_cosmosdb_managed_cassandra_cluster_create', supports_no_wait=True)
        g.custom_command('update', 'cli_cosmosdb_managed_cassandra_cluster_update', supports_no_wait=True)
        g.custom_command('deallocate', 'cli_cosmosdb_managed_cassandra_cluster_deallocate', supports_no_wait=True)
        g.custom_command('invoke-command', 'cli_cosmosdb_managed_cassandra_cluster_invoke_command', supports_no_wait=True)
        g.custom_command('start', 'cli_cosmosdb_managed_cassandra_cluster_start', supports_no_wait=True)
        g.custom_command('status', 'cli_cosmosdb_managed_cassandra_cluster_status', table_transformer=mc_cluster_status_output_table)
        g.custom_command('list', 'cli_cosmosdb_managed_cassandra_cluster_list')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)

    # managed cassandra datacenter
    with self.command_group('managed-cassandra datacenter', cosmosdb_managed_cassandra_datacenter_sdk, client_factory=cf_cassandra_data_center) as g:
        g.custom_command('create', 'cli_cosmosdb_managed_cassandra_datacenter_create', supports_no_wait=True)
        g.custom_command('update', 'cli_cosmosdb_managed_cassandra_datacenter_update', supports_no_wait=True)
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)

    # ComputeV2 services
    with self.command_group('cosmosdb service', cosmosdb_service_sdk, client_factory=cf_service) as g:
        g.custom_command('create', 'cli_cosmosdb_service_create', supports_no_wait=True)
        g.custom_command('update', 'cli_cosmosdb_service_update', supports_no_wait=True)
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)

    setup_fleet_commands(self)


def setup_fleet_commands(self):
    # Fleet operations
    cosmosdb_fleet_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#FleetOperations.{}',
        client_factory=cf_fleet)

    # Fleetspace operations
    cosmosdb_fleetspace_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#FleetspaceOperations.{}',
        client_factory=cf_fleetspace)

    # Fleetspace account operations
    cosmosdb_fleetspace_account_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cosmosdb.operations#FleetspaceAccountOperations.{}',
        client_factory=cf_fleetspace_account)

    with self.command_group('cosmosdb fleet', cosmosdb_fleet_sdk, client_factory=cf_fleet, is_preview=True) as g:
        g.custom_command('create', 'cli_cosmosdb_fleet_create')
        g.custom_command('list', 'cli_list_cosmosdb_fleets')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('cosmosdb fleetspace', cosmosdb_fleetspace_sdk, client_factory=cf_fleetspace, is_preview=True) as g:
        g.custom_command('create', 'cli_cosmosdb_fleetspace_create')
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.custom_command('update', 'cli_cosmosdb_fleetspace_update')
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('cosmosdb fleetspace account', cosmosdb_fleetspace_account_sdk, client_factory=cf_fleetspace_account, is_preview=True) as g:
        g.custom_command('create', 'cli_cosmosdb_fleetspace_account_create')
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
