# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.azclierror import InvalidArgumentValueError

from azure.mgmt.cosmosdb.models import (
    ConsistencyPolicy,
    DatabaseAccountCreateUpdateParameters,
    DatabaseAccountUpdateParameters,
    Location,
    DatabaseAccountKind,
    VirtualNetworkRule,
    SqlDatabaseResource,
    SqlDatabaseCreateUpdateParameters,
    SqlContainerResource,
    SqlContainerCreateUpdateParameters,
    ContainerPartitionKey,
    ResourceIdentityType,
    SqlStoredProcedureResource,
    SqlStoredProcedureCreateUpdateParameters,
    SqlTriggerResource,
    SqlTriggerCreateUpdateParameters,
    SqlUserDefinedFunctionResource,
    SqlUserDefinedFunctionCreateUpdateParameters,
    TableResource,
    TableCreateUpdateParameters,
    ManagedServiceIdentity,
    MongoDBDatabaseResource,
    MongoDBDatabaseCreateUpdateParameters,
    MongoDBCollectionResource,
    MongoDBCollectionCreateUpdateParameters,
    CassandraKeyspaceResource,
    CassandraKeyspaceCreateUpdateParameters,
    CassandraTableResource,
    CassandraTableCreateUpdateParameters,
    GremlinDatabaseResource,
    GremlinDatabaseCreateUpdateParameters,
    GremlinGraphResource,
    GremlinGraphCreateUpdateParameters,
    ThroughputSettingsResource,
    ThroughputSettingsUpdateParameters,
    AutoscaleSettings,
    PeriodicModeBackupPolicy,
    PeriodicModeProperties
)

logger = get_logger(__name__)


class CosmosKeyTypes(Enum):
    keys = "keys"
    read_only_keys = "read-only-keys"
    connection_strings = "connection-strings"


DEFAULT_INDEXING_POLICY = """{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/\\"_etag\\"/?"
    }
  ]
}"""


# pylint: disable=too-many-locals
def cli_cosmosdb_create(cmd, client,
                        resource_group_name,
                        account_name,
                        locations=None,
                        tags=None,
                        kind=DatabaseAccountKind.global_document_db.value,
                        default_consistency_level=None,
                        max_staleness_prefix=100,
                        max_interval=5,
                        ip_range_filter=None,
                        enable_automatic_failover=None,
                        capabilities=None,
                        enable_virtual_network=None,
                        virtual_network_rules=None,
                        enable_multiple_write_locations=None,
                        disable_key_based_metadata_write_access=None,
                        key_uri=None,
                        enable_public_network=None,
                        enable_analytical_storage=None,
                        enable_free_tier=None,
                        server_version=None,
                        network_acl_bypass=None,
                        network_acl_bypass_resource_ids=None,
                        backup_interval=None,
                        backup_retention=None,
                        assign_identity=None,
                        default_identity=None):
    """Create a new Azure Cosmos DB database account."""
    consistency_policy = None
    if default_consistency_level is not None:
        consistency_policy = ConsistencyPolicy(default_consistency_level=default_consistency_level,
                                               max_staleness_prefix=max_staleness_prefix,
                                               max_interval_in_seconds=max_interval)

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

    rg = resource_client.resource_groups.get(resource_group_name)
    resource_group_location = rg.location  # pylint: disable=no-member

    if not locations:
        locations = []
        locations.append(Location(location_name=resource_group_location, failover_priority=0, is_zone_redundant=False))

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = 'Enabled' if enable_public_network else 'Disabled'

    system_assigned_identity = None
    if assign_identity is not None:
        if assign_identity == [] or (len(assign_identity) == 1 and assign_identity[0] == '[system]'):
            system_assigned_identity = ManagedServiceIdentity(type=ResourceIdentityType.system_assigned.value)
        else:
            raise InvalidArgumentValueError("Only '[system]' is supported right now for command '--assign-identity'.")

    api_properties = {}
    if kind == DatabaseAccountKind.mongo_db.value:
        api_properties['ServerVersion'] = server_version
    elif server_version is not None:
        raise CLIError('server-version is a valid argument only when kind is MongoDB.')

    backup_policy = None
    if backup_interval is not None or backup_retention is not None:
        backup_policy = PeriodicModeBackupPolicy()
        periodic_mode_properties = PeriodicModeProperties(
            backup_interval_in_minutes=backup_interval,
            backup_retention_interval_in_hours=backup_retention
        )
        backup_policy.periodic_mode_properties = periodic_mode_properties

    params = DatabaseAccountCreateUpdateParameters(
        location=resource_group_location,
        locations=locations,
        tags=tags,
        kind=kind,
        consistency_policy=consistency_policy,
        ip_rules=ip_range_filter,
        is_virtual_network_filter_enabled=enable_virtual_network,
        enable_automatic_failover=enable_automatic_failover,
        capabilities=capabilities,
        virtual_network_rules=virtual_network_rules,
        enable_multiple_write_locations=enable_multiple_write_locations,
        disable_key_based_metadata_write_access=disable_key_based_metadata_write_access,
        key_vault_key_uri=key_uri,
        public_network_access=public_network_access,
        api_properties=api_properties,
        enable_analytical_storage=enable_analytical_storage,
        enable_free_tier=enable_free_tier,
        network_acl_bypass=network_acl_bypass,
        network_acl_bypass_resource_ids=network_acl_bypass_resource_ids,
        backup_policy=backup_policy,
        identity=system_assigned_identity,
        default_identity=default_identity)

    async_docdb_create = client.create_or_update(resource_group_name, account_name, params)
    docdb_account = async_docdb_create.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


# pylint: disable=too-many-branches
def cli_cosmosdb_update(client,
                        resource_group_name,
                        account_name,
                        locations=None,
                        tags=None,
                        default_consistency_level=None,
                        max_staleness_prefix=None,
                        max_interval=None,
                        ip_range_filter=None,
                        enable_automatic_failover=None,
                        capabilities=None,
                        enable_virtual_network=None,
                        virtual_network_rules=None,
                        enable_multiple_write_locations=None,
                        disable_key_based_metadata_write_access=None,
                        enable_public_network=None,
                        enable_analytical_storage=None,
                        network_acl_bypass=None,
                        network_acl_bypass_resource_ids=None,
                        server_version=None,
                        backup_interval=None,
                        backup_retention=None,
                        default_identity=None):
    """Update an existing Azure Cosmos DB database account. """
    existing = client.get(resource_group_name, account_name)

    update_consistency_policy = False
    if max_interval is not None or \
            max_staleness_prefix is not None or \
            default_consistency_level is not None:
        update_consistency_policy = True

    if max_staleness_prefix is None:
        max_staleness_prefix = existing.consistency_policy.max_staleness_prefix

    if max_interval is None:
        max_interval = existing.consistency_policy.max_interval_in_seconds

    if default_consistency_level is None:
        default_consistency_level = existing.consistency_policy.default_consistency_level

    consistency_policy = None
    if update_consistency_policy:
        consistency_policy = ConsistencyPolicy(default_consistency_level=default_consistency_level,
                                               max_staleness_prefix=max_staleness_prefix,
                                               max_interval_in_seconds=max_interval)

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = 'Enabled' if enable_public_network else 'Disabled'

    api_properties = {'ServerVersion': server_version}

    backup_policy = None
    if backup_interval is not None or backup_retention is not None:
        if isinstance(existing.backup_policy, PeriodicModeBackupPolicy):
            periodic_mode_properties = PeriodicModeProperties(
                backup_interval_in_minutes=backup_interval,
                backup_retention_interval_in_hours=backup_retention
            )
            backup_policy = existing.backup_policy
            backup_policy.periodic_mode_properties = periodic_mode_properties
        else:
            raise CLIError(
                'backup-interval and backup-retention can only be set for accounts with periodic backup policy.')

    params = DatabaseAccountUpdateParameters(
        locations=locations,
        tags=tags,
        consistency_policy=consistency_policy,
        ip_rules=ip_range_filter,
        is_virtual_network_filter_enabled=enable_virtual_network,
        enable_automatic_failover=enable_automatic_failover,
        capabilities=capabilities,
        virtual_network_rules=virtual_network_rules,
        enable_multiple_write_locations=enable_multiple_write_locations,
        disable_key_based_metadata_write_access=disable_key_based_metadata_write_access,
        public_network_access=public_network_access,
        enable_analytical_storage=enable_analytical_storage,
        network_acl_bypass=network_acl_bypass,
        network_acl_bypass_resource_ids=network_acl_bypass_resource_ids,
        api_properties=api_properties,
        backup_policy=backup_policy,
        default_identity=default_identity)

    async_docdb_update = client.update(resource_group_name, account_name, params)
    docdb_account = async_docdb_update.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


def cli_cosmosdb_list(client, resource_group_name=None):
    """ Lists all Azure Cosmos DB database accounts within a given resource group or subscription. """
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


# pylint: disable=line-too-long
def cli_cosmosdb_keys(client, resource_group_name, account_name, key_type=CosmosKeyTypes.keys.value):
    if key_type == CosmosKeyTypes.keys.value:
        return client.list_keys(resource_group_name, account_name)
    if key_type == CosmosKeyTypes.read_only_keys.value:
        return client.list_read_only_keys(resource_group_name, account_name)
    if key_type == CosmosKeyTypes.connection_strings.value:
        return client.list_connection_strings(resource_group_name, account_name)
    raise CLIError("az cosmosdb keys list: '{0}' is not a valid value for '--type'. See 'az cosmosdb keys list --help'.".format(key_type))


def _handle_exists_exception(cloud_error):
    if cloud_error.status_code == 404:
        return False
    raise cloud_error


def cli_cosmosdb_sql_database_create(client,
                                     resource_group_name,
                                     account_name,
                                     database_name,
                                     throughput=None,
                                     max_throughput=None):
    """Creates an Azure Cosmos DB SQL database"""
    options = _get_options(throughput, max_throughput)

    sql_database_resource = SqlDatabaseCreateUpdateParameters(
        resource=SqlDatabaseResource(id=database_name),
        options=options)

    return client.create_update_sql_database(resource_group_name,
                                             account_name,
                                             database_name,
                                             sql_database_resource)


def cli_cosmosdb_sql_database_exists(client,
                                     resource_group_name,
                                     account_name,
                                     database_name):
    """Checks if an Azure Cosmos DB SQL database exists"""
    try:
        client.get_sql_database(resource_group_name, account_name, database_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def _populate_sql_container_definition(sql_container_resource,
                                       partition_key_path,
                                       default_ttl,
                                       indexing_policy,
                                       unique_key_policy,
                                       partition_key_version,
                                       conflict_resolution_policy,
                                       analytical_storage_ttl):
    if all(arg is None for arg in
           [partition_key_path, partition_key_version, default_ttl, indexing_policy, unique_key_policy, conflict_resolution_policy]):
        return False

    if partition_key_path is not None:
        container_partition_key = ContainerPartitionKey()
        container_partition_key.paths = [partition_key_path]
        container_partition_key.kind = 'Hash'
        if partition_key_version is not None:
            container_partition_key.version = partition_key_version
        sql_container_resource.partition_key = container_partition_key

    if default_ttl is not None:
        sql_container_resource.default_ttl = default_ttl

    if indexing_policy is not None:
        sql_container_resource.indexing_policy = indexing_policy

    if unique_key_policy is not None:
        sql_container_resource.unique_key_policy = unique_key_policy

    if conflict_resolution_policy is not None:
        sql_container_resource.conflict_resolution_policy = conflict_resolution_policy

    if analytical_storage_ttl is not None:
        sql_container_resource.analytical_storage_ttl = analytical_storage_ttl

    return True


def cli_cosmosdb_sql_container_create(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      container_name,
                                      partition_key_path,
                                      partition_key_version=None,
                                      default_ttl=None,
                                      indexing_policy=DEFAULT_INDEXING_POLICY,
                                      throughput=None,
                                      max_throughput=None,
                                      unique_key_policy=None,
                                      conflict_resolution_policy=None,
                                      analytical_storage_ttl=None):
    """Creates an Azure Cosmos DB SQL container """
    sql_container_resource = SqlContainerResource(id=container_name)

    _populate_sql_container_definition(sql_container_resource,
                                       partition_key_path,
                                       default_ttl,
                                       indexing_policy,
                                       unique_key_policy,
                                       partition_key_version,
                                       conflict_resolution_policy,
                                       analytical_storage_ttl)

    options = _get_options(throughput, max_throughput)

    sql_container_create_update_resource = SqlContainerCreateUpdateParameters(
        resource=sql_container_resource,
        options=options)

    return client.create_update_sql_container(resource_group_name,
                                              account_name,
                                              database_name,
                                              container_name,
                                              sql_container_create_update_resource)


def cli_cosmosdb_sql_container_update(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      container_name,
                                      default_ttl=None,
                                      indexing_policy=None,
                                      analytical_storage_ttl=None):
    """Updates an Azure Cosmos DB SQL container """
    logger.debug('reading SQL container')
    sql_container = client.get_sql_container(resource_group_name, account_name, database_name, container_name)

    sql_container_resource = SqlContainerResource(id=container_name)
    sql_container_resource.partition_key = sql_container.resource.partition_key
    sql_container_resource.indexing_policy = sql_container.resource.indexing_policy
    sql_container_resource.default_ttl = sql_container.resource.default_ttl
    sql_container_resource.unique_key_policy = sql_container.resource.unique_key_policy
    sql_container_resource.conflict_resolution_policy = sql_container.resource.conflict_resolution_policy

    if _populate_sql_container_definition(sql_container_resource,
                                          None,
                                          default_ttl,
                                          indexing_policy,
                                          None,
                                          None,
                                          None,
                                          analytical_storage_ttl):
        logger.debug('replacing SQL container')

    sql_container_create_update_resource = SqlContainerCreateUpdateParameters(
        resource=sql_container_resource,
        options={})

    return client.create_update_sql_container(resource_group_name,
                                              account_name,
                                              database_name,
                                              container_name,
                                              sql_container_create_update_resource)


def cli_cosmosdb_sql_container_exists(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      container_name):
    """Checks if an Azure Cosmos DB SQL container exists"""
    try:
        client.get_sql_container(resource_group_name, account_name, database_name, container_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def cli_cosmosdb_sql_stored_procedure_create_update(client,
                                                    resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    container_name,
                                                    stored_procedure_name,
                                                    stored_procedure_body):

    """Creates or Updates an Azure Cosmos DB SQL stored procedure """
    sql_stored_procedure_resource = SqlStoredProcedureResource(id=stored_procedure_name)
    sql_stored_procedure_resource.body = stored_procedure_body

    sql_stored_procedure_create_update_resource = SqlStoredProcedureCreateUpdateParameters(
        resource=sql_stored_procedure_resource,
        options={})

    return client.create_update_sql_stored_procedure(resource_group_name,
                                                     account_name,
                                                     database_name,
                                                     container_name,
                                                     stored_procedure_name,
                                                     sql_stored_procedure_create_update_resource)


def cli_cosmosdb_sql_user_defined_function_create_update(client,
                                                         resource_group_name,
                                                         account_name,
                                                         database_name,
                                                         container_name,
                                                         user_defined_function_name,
                                                         user_defined_function_body):

    """Creates or Updates an Azure Cosmos DB SQL user defined function """
    sql_user_defined_function_resource = SqlUserDefinedFunctionResource(id=user_defined_function_name)
    sql_user_defined_function_resource.body = user_defined_function_body

    sql_user_defined_function_create_update_resource = SqlUserDefinedFunctionCreateUpdateParameters(
        resource=sql_user_defined_function_resource,
        options={})

    return client.create_update_sql_user_defined_function(resource_group_name,
                                                          account_name,
                                                          database_name,
                                                          container_name,
                                                          user_defined_function_name,
                                                          sql_user_defined_function_create_update_resource)


def _populate_sql_trigger_definition(sql_trigger_resource,
                                     trigger_body,
                                     trigger_operation,
                                     trigger_type):
    if all(arg is None for arg in
           [trigger_body, trigger_operation, trigger_type]):
        return False

    if trigger_body is not None:
        sql_trigger_resource.body = trigger_body

    if trigger_operation is not None:
        sql_trigger_resource.trigger_operation = trigger_operation

    if trigger_type is not None:
        sql_trigger_resource.trigger_type = trigger_type

    return True


def cli_cosmosdb_sql_trigger_create(client,
                                    resource_group_name,
                                    account_name,
                                    database_name,
                                    container_name,
                                    trigger_name,
                                    trigger_body,
                                    trigger_type=None,
                                    trigger_operation=None):

    """Creates an Azure Cosmos DB SQL trigger """
    if trigger_operation is None:
        trigger_operation = "All"

    if trigger_type is None:
        trigger_type = "Pre"

    sql_trigger_resource = SqlTriggerResource(id=trigger_name)
    sql_trigger_resource.body = trigger_body
    sql_trigger_resource.trigger_type = trigger_type
    sql_trigger_resource.trigger_operation = trigger_operation

    sql_trigger_create_update_resource = SqlTriggerCreateUpdateParameters(
        resource=sql_trigger_resource,
        options={})

    return client.create_update_sql_trigger(resource_group_name,
                                            account_name,
                                            database_name,
                                            container_name,
                                            trigger_name,
                                            sql_trigger_create_update_resource)


def cli_cosmosdb_sql_trigger_update(client,
                                    resource_group_name,
                                    account_name,
                                    database_name,
                                    container_name,
                                    trigger_name,
                                    trigger_body=None,
                                    trigger_type=None,
                                    trigger_operation=None):

    """Updates an Azure Cosmos DB SQL trigger """
    logger.debug('reading SQL trigger')
    sql_trigger = client.get_sql_trigger(resource_group_name, account_name, database_name, container_name, trigger_name)

    sql_trigger_resource = SqlTriggerResource(id=trigger_name)
    sql_trigger_resource.body = sql_trigger.resource.body
    sql_trigger_resource.trigger_operation = sql_trigger.resource.trigger_operation
    sql_trigger_resource.trigger_type = sql_trigger.resource.trigger_type

    if _populate_sql_trigger_definition(sql_trigger_resource,
                                        trigger_body,
                                        trigger_operation,
                                        trigger_type):
        logger.debug('replacing SQL trigger')

    sql_trigger_create_update_resource = SqlTriggerCreateUpdateParameters(
        resource=sql_trigger_resource,
        options={})

    return client.create_update_sql_trigger(resource_group_name,
                                            account_name,
                                            database_name,
                                            container_name,
                                            trigger_name,
                                            sql_trigger_create_update_resource)


def cli_cosmosdb_gremlin_database_create(client,
                                         resource_group_name,
                                         account_name,
                                         database_name,
                                         throughput=None,
                                         max_throughput=None):
    """Creates an Azure Cosmos DB Gremlin database"""
    options = _get_options(throughput, max_throughput)

    gremlin_database_resource = GremlinDatabaseCreateUpdateParameters(
        resource=GremlinDatabaseResource(id=database_name),
        options=options)

    return client.create_update_gremlin_database(resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 gremlin_database_resource)


def cli_cosmosdb_gremlin_database_exists(client,
                                         resource_group_name,
                                         account_name,
                                         database_name):
    """Checks if an Azure Cosmos DB Gremlin database exists"""
    try:
        client.get_gremlin_database(resource_group_name, account_name, database_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def _populate_gremlin_graph_definition(gremlin_graph_resource,
                                       partition_key_path,
                                       default_ttl,
                                       indexing_policy,
                                       conflict_resolution_policy):
    if all(arg is None for arg in [partition_key_path, default_ttl, indexing_policy, conflict_resolution_policy]):
        return False

    if partition_key_path is not None:
        graph_partition_key = ContainerPartitionKey()
        graph_partition_key.paths = [partition_key_path]
        graph_partition_key.kind = 'Hash'
        gremlin_graph_resource.partition_key = graph_partition_key

    if default_ttl is not None:
        gremlin_graph_resource.default_ttl = default_ttl

    if indexing_policy is not None:
        gremlin_graph_resource.indexing_policy = indexing_policy

    if conflict_resolution_policy is not None:
        gremlin_graph_resource.conflict_resolution_policy = conflict_resolution_policy

    return True


def cli_cosmosdb_gremlin_graph_create(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      graph_name,
                                      partition_key_path,
                                      default_ttl=None,
                                      indexing_policy=DEFAULT_INDEXING_POLICY,
                                      throughput=None,
                                      max_throughput=None,
                                      conflict_resolution_policy=None):
    """Creates an Azure Cosmos DB Gremlin graph """
    gremlin_graph_resource = GremlinGraphResource(id=graph_name)

    _populate_gremlin_graph_definition(gremlin_graph_resource,
                                       partition_key_path,
                                       default_ttl,
                                       indexing_policy,
                                       conflict_resolution_policy)

    options = _get_options(throughput, max_throughput)

    gremlin_graph_create_update_resource = GremlinGraphCreateUpdateParameters(
        resource=gremlin_graph_resource,
        options=options)

    return client.create_update_gremlin_graph(resource_group_name,
                                              account_name,
                                              database_name,
                                              graph_name,
                                              gremlin_graph_create_update_resource)


def cli_cosmosdb_gremlin_graph_update(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      graph_name,
                                      default_ttl=None,
                                      indexing_policy=None):
    """Updates an Azure Cosmos DB Gremlin graph """
    logger.debug('reading Gremlin graph')
    gremlin_graph = client.get_gremlin_graph(resource_group_name, account_name, database_name, graph_name)

    gremlin_graph_resource = GremlinGraphResource(id=graph_name)
    gremlin_graph_resource.partition_key = gremlin_graph.resource.partition_key
    gremlin_graph_resource.indexing_policy = gremlin_graph.resource.indexing_policy
    gremlin_graph_resource.default_ttl = gremlin_graph.resource.default_ttl
    gremlin_graph_resource.unique_key_policy = gremlin_graph.resource.unique_key_policy
    gremlin_graph_resource.conflict_resolution_policy = gremlin_graph.resource.conflict_resolution_policy

    if _populate_gremlin_graph_definition(gremlin_graph_resource,
                                          None,
                                          default_ttl,
                                          indexing_policy,
                                          None):
        logger.debug('replacing Gremlin graph')

    gremlin_graph_create_update_resource = GremlinGraphCreateUpdateParameters(
        resource=gremlin_graph_resource,
        options={})

    return client.create_update_gremlin_graph(resource_group_name,
                                              account_name,
                                              database_name,
                                              graph_name,
                                              gremlin_graph_create_update_resource)


def cli_cosmosdb_gremlin_graph_exists(client,
                                      resource_group_name,
                                      account_name,
                                      database_name,
                                      graph_name):
    """Checks if an Azure Cosmos DB Gremlin graph exists"""
    try:
        client.get_gremlin_graph(resource_group_name, account_name, database_name, graph_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def cli_cosmosdb_mongodb_database_create(client,
                                         resource_group_name,
                                         account_name,
                                         database_name,
                                         throughput=None,
                                         max_throughput=None):
    """Create an Azure Cosmos DB MongoDB database"""
    options = _get_options(throughput, max_throughput)

    mongodb_database_resource = MongoDBDatabaseCreateUpdateParameters(
        resource=MongoDBDatabaseResource(id=database_name),
        options=options)

    return client.create_update_mongo_db_database(resource_group_name,
                                                  account_name,
                                                  database_name,
                                                  mongodb_database_resource)


def cli_cosmosdb_mongodb_database_exists(client,
                                         resource_group_name,
                                         account_name,
                                         database_name):
    """Checks if an Azure Cosmos DB MongoDB database exists"""
    try:
        client.get_mongo_db_database(resource_group_name, account_name, database_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def _populate_mongodb_collection_definition(mongodb_collection_resource, shard_key_path, indexes, analytical_storage_ttl):
    if all(arg is None for arg in [shard_key_path, indexes]):
        return False

    if shard_key_path is not None:
        mongodb_collection_resource.shard_key = {shard_key_path: "Hash"}

    if indexes is not None:
        mongodb_collection_resource.indexes = indexes

    if analytical_storage_ttl is not None:
        mongodb_collection_resource.analytical_storage_ttl = analytical_storage_ttl

    return True


def cli_cosmosdb_mongodb_collection_create(client,
                                           resource_group_name,
                                           account_name,
                                           database_name,
                                           collection_name,
                                           shard_key_path=None,
                                           indexes=None,
                                           throughput=None,
                                           max_throughput=None,
                                           analytical_storage_ttl=None):
    """Create an Azure Cosmos DB MongoDB collection"""
    mongodb_collection_resource = MongoDBCollectionResource(id=collection_name)

    _populate_mongodb_collection_definition(mongodb_collection_resource, shard_key_path, indexes, analytical_storage_ttl)

    options = _get_options(throughput, max_throughput)

    mongodb_collection_create_update_resource = MongoDBCollectionCreateUpdateParameters(
        resource=mongodb_collection_resource,
        options=options)

    return client.create_update_mongo_db_collection(resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    collection_name,
                                                    mongodb_collection_create_update_resource)


def cli_cosmosdb_mongodb_collection_update(client,
                                           resource_group_name,
                                           account_name,
                                           database_name,
                                           collection_name,
                                           indexes=None,
                                           analytical_storage_ttl=None):
    """Updates an Azure Cosmos DB MongoDB collection """
    logger.debug('reading MongoDB collection')
    mongodb_collection = client.get_mongo_db_collection(resource_group_name,
                                                        account_name,
                                                        database_name,
                                                        collection_name)
    mongodb_collection_resource = MongoDBCollectionResource(id=collection_name)
    mongodb_collection_resource.shard_key = mongodb_collection.resource.shard_key
    mongodb_collection_resource.indexes = mongodb_collection.resource.indexes
    mongodb_collection_resource.analytical_storage_ttl = mongodb_collection.resource.analytical_storage_ttl

    if _populate_mongodb_collection_definition(mongodb_collection_resource, None, indexes, analytical_storage_ttl):
        logger.debug('replacing MongoDB collection')

    mongodb_collection_create_update_resource = MongoDBCollectionCreateUpdateParameters(
        resource=mongodb_collection_resource,
        options={})

    return client.create_update_mongo_db_collection(resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    collection_name,
                                                    mongodb_collection_create_update_resource)


def cli_cosmosdb_mongodb_collection_exists(client,
                                           resource_group_name,
                                           account_name,
                                           database_name,
                                           collection_name):
    """Checks if an Azure Cosmos DB MongoDB collection exists"""
    try:
        client.get_mongo_db_collection(resource_group_name, account_name, database_name, collection_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def cli_cosmosdb_cassandra_keyspace_create(client,
                                           resource_group_name,
                                           account_name,
                                           keyspace_name,
                                           throughput=None,
                                           max_throughput=None):
    """Create an Azure Cosmos DB Cassandra keyspace"""
    options = _get_options(throughput, max_throughput)

    cassandra_keyspace_resource = CassandraKeyspaceCreateUpdateParameters(
        resource=CassandraKeyspaceResource(id=keyspace_name),
        options=options)

    return client.create_update_cassandra_keyspace(resource_group_name,
                                                   account_name,
                                                   keyspace_name,
                                                   cassandra_keyspace_resource)


def cli_cosmosdb_cassandra_keyspace_exists(client,
                                           resource_group_name,
                                           account_name,
                                           keyspace_name):
    """Checks if an Azure Cosmos DB Cassandra keyspace exists"""
    try:
        client.get_cassandra_keyspace(resource_group_name, account_name, keyspace_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def _populate_cassandra_table_definition(cassandra_table_resource, default_ttl, schema, analytical_storage_ttl):
    if all(arg is None for arg in [default_ttl, schema, analytical_storage_ttl]):
        return False

    if default_ttl is not None:
        cassandra_table_resource.default_ttl = default_ttl

    if schema is not None:
        cassandra_table_resource.schema = schema

    if analytical_storage_ttl is not None:
        cassandra_table_resource.analytical_storage_ttl = analytical_storage_ttl

    return True


def cli_cosmosdb_cassandra_table_create(client,
                                        resource_group_name,
                                        account_name,
                                        keyspace_name,
                                        table_name,
                                        schema,
                                        default_ttl=None,
                                        throughput=None,
                                        max_throughput=None,
                                        analytical_storage_ttl=None):
    """Create an Azure Cosmos DB Cassandra table"""
    cassandra_table_resource = CassandraTableResource(id=table_name)

    _populate_cassandra_table_definition(cassandra_table_resource, default_ttl, schema, analytical_storage_ttl)

    options = _get_options(throughput, max_throughput)

    cassandra_table_create_update_resource = CassandraTableCreateUpdateParameters(
        resource=cassandra_table_resource,
        options=options)

    return client.create_update_cassandra_table(resource_group_name,
                                                account_name,
                                                keyspace_name,
                                                table_name,
                                                cassandra_table_create_update_resource)


def cli_cosmosdb_cassandra_table_update(client,
                                        resource_group_name,
                                        account_name,
                                        keyspace_name,
                                        table_name,
                                        default_ttl=None,
                                        schema=None,
                                        analytical_storage_ttl=None):
    """Update an Azure Cosmos DB Cassandra table"""
    logger.debug('reading Cassandra table')
    cassandra_table = client.get_cassandra_table(resource_group_name, account_name, keyspace_name, table_name)

    cassandra_table_resource = CassandraTableResource(id=table_name)
    cassandra_table_resource.default_ttl = cassandra_table.resource.default_ttl
    cassandra_table_resource.schema = cassandra_table.resource.schema
    cassandra_table_resource.analytical_storage_ttl = cassandra_table.resource.analytical_storage_ttl

    if _populate_cassandra_table_definition(cassandra_table_resource, default_ttl, schema, analytical_storage_ttl):
        logger.debug('replacing Cassandra table')

    cassandra_table_create_update_resource = CassandraTableCreateUpdateParameters(
        resource=cassandra_table_resource,
        options={})

    return client.create_update_cassandra_table(resource_group_name,
                                                account_name,
                                                keyspace_name,
                                                table_name,
                                                cassandra_table_create_update_resource)


def cli_cosmosdb_cassandra_table_exists(client,
                                        resource_group_name,
                                        account_name,
                                        keyspace_name,
                                        table_name):
    """Checks if an Azure Cosmos DB Cassandra table exists"""
    try:
        client.get_cassandra_table(resource_group_name, account_name, keyspace_name, table_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def cli_cosmosdb_table_create(client,
                              resource_group_name,
                              account_name,
                              table_name,
                              throughput=None,
                              max_throughput=None):
    """Create an Azure Cosmos DB table"""
    options = _get_options(throughput, max_throughput)

    table = TableCreateUpdateParameters(
        resource=TableResource(id=table_name),
        options=options)

    return client.create_update_table(resource_group_name, account_name, table_name, table)


def cli_cosmosdb_table_exists(client,
                              resource_group_name,
                              account_name,
                              table_name):
    """Checks if an Azure Cosmos DB table exists"""
    try:
        client.get_table(resource_group_name, account_name, table_name)
    except CloudError as ex:
        return _handle_exists_exception(ex)

    return True


def cli_cosmosdb_sql_database_throughput_update(client,
                                                resource_group_name,
                                                account_name,
                                                database_name,
                                                throughput=None,
                                                max_throughput=None):
    """Update an Azure Cosmos DB SQL database throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_sql_database_throughput(resource_group_name, account_name, database_name, throughput_update_resource)


def cli_cosmosdb_sql_database_throughput_migrate(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 throughput_type):
    if throughput_type == "autoscale":
        return client.migrate_sql_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.migrate_sql_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_sql_container_throughput_update(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 container_name,
                                                 throughput=None,
                                                 max_throughput=None):
    """Update an Azure Cosmos DB SQL container throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_sql_container_throughput(resource_group_name,
                                                  account_name,
                                                  database_name,
                                                  container_name,
                                                  throughput_update_resource)


def cli_cosmosdb_sql_container_throughput_migrate(client,
                                                  resource_group_name,
                                                  account_name,
                                                  database_name,
                                                  container_name,
                                                  throughput_type):
    """Migrate an Azure Cosmos DB SQL container throughput"""
    if throughput_type == "autoscale":
        return client.migrate_sql_container_to_autoscale(resource_group_name, account_name, database_name, container_name)
    return client.migrate_sql_container_to_manual_throughput(resource_group_name, account_name, database_name, container_name)


def cli_cosmosdb_mongodb_database_throughput_update(client,
                                                    resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    throughput=None,
                                                    max_throughput=None):
    """Update an Azure Cosmos DB MongoDB database throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_mongo_db_database_throughput(resource_group_name,
                                                      account_name,
                                                      database_name,
                                                      throughput_update_resource)


def cli_cosmosdb_mongodb_database_throughput_migrate(client,
                                                     resource_group_name,
                                                     account_name,
                                                     database_name,
                                                     throughput_type):
    """Migrate an Azure Cosmos DB MongoDB database throughput"""
    if throughput_type == "autoscale":
        return client.migrate_mongo_db_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.migrate_mongo_db_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_mongodb_collection_throughput_update(client,
                                                      resource_group_name,
                                                      account_name,
                                                      database_name,
                                                      collection_name,
                                                      throughput=None,
                                                      max_throughput=None):
    """Update an Azure Cosmos DB MongoDB collection throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_mongo_db_collection_throughput(resource_group_name,
                                                        account_name,
                                                        database_name,
                                                        collection_name,
                                                        throughput_update_resource)


def cli_cosmosdb_mongodb_collection_throughput_migrate(client,
                                                       resource_group_name,
                                                       account_name,
                                                       database_name,
                                                       collection_name,
                                                       throughput_type):
    """Migrate an Azure Cosmos DB MongoDB collection throughput"""
    if throughput_type == "autoscale":
        return client.migrate_mongo_db_collection_to_autoscale(resource_group_name, account_name, database_name, collection_name)
    return client.migrate_mongo_db_collection_to_manual_throughput(resource_group_name, account_name, database_name, collection_name)


def cli_cosmosdb_cassandra_keyspace_throughput_update(client,
                                                      resource_group_name,
                                                      account_name,
                                                      keyspace_name,
                                                      throughput=None,
                                                      max_throughput=None):
    """Update an Azure Cosmos DB Cassandra keyspace throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_cassandra_keyspace_throughput(resource_group_name,
                                                       account_name,
                                                       keyspace_name,
                                                       throughput_update_resource)


def cli_cosmosdb_cassandra_keyspace_throughput_migrate(client,
                                                       resource_group_name,
                                                       account_name,
                                                       keyspace_name,
                                                       throughput_type):
    """Migrate an Azure Cosmos DB Cassandra keyspace throughput"""
    if throughput_type == "autoscale":
        return client.migrate_cassandra_keyspace_to_autoscale(resource_group_name, account_name, keyspace_name)
    return client.migrate_cassandra_keyspace_to_manual_throughput(resource_group_name, account_name, keyspace_name)


def cli_cosmosdb_cassandra_table_throughput_update(client,
                                                   resource_group_name,
                                                   account_name,
                                                   keyspace_name,
                                                   table_name,
                                                   throughput=None,
                                                   max_throughput=None):
    """Update an Azure Cosmos DB Cassandra table throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_cassandra_table_throughput(resource_group_name,
                                                    account_name,
                                                    keyspace_name,
                                                    table_name,
                                                    throughput_update_resource)


def cli_cosmosdb_cassandra_table_throughput_migrate(client,
                                                    resource_group_name,
                                                    account_name,
                                                    keyspace_name,
                                                    table_name,
                                                    throughput_type):
    """Migrate an Azure Cosmos DB Cassandra table throughput"""
    if throughput_type == "autoscale":
        return client.migrate_cassandra_table_to_autoscale(resource_group_name, account_name, keyspace_name, table_name)
    return client.migrate_cassandra_table_to_manual_throughput(resource_group_name, account_name, keyspace_name, table_name)


def cli_cosmosdb_gremlin_database_throughput_update(client,
                                                    resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    throughput=None,
                                                    max_throughput=None):
    """Update an Azure Cosmos DB Gremlin database throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_gremlin_database_throughput(resource_group_name,
                                                     account_name,
                                                     database_name,
                                                     throughput_update_resource)


def cli_cosmosdb_gremlin_database_throughput_migrate(client,
                                                     resource_group_name,
                                                     account_name,
                                                     database_name,
                                                     throughput_type):
    """Migrate an Azure Cosmos DB Gremlin database throughput"""
    if throughput_type == "autoscale":
        return client.migrate_gremlin_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.migrate_gremlin_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_gremlin_graph_throughput_update(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 graph_name,
                                                 throughput=None,
                                                 max_throughput=None):
    """Update an Azure Cosmos DB Gremlin graph throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_gremlin_graph_throughput(resource_group_name,
                                                  account_name,
                                                  database_name,
                                                  graph_name,
                                                  throughput_update_resource)


def cli_cosmosdb_gremlin_graph_throughput_migrate(client,
                                                  resource_group_name,
                                                  account_name,
                                                  database_name,
                                                  graph_name,
                                                  throughput_type):
    """Migrate an Azure Cosmos DB Gremlin database throughput"""
    if throughput_type == "autoscale":
        return client.migrate_gremlin_graph_to_autoscale(resource_group_name, account_name, database_name, graph_name)
    return client.migrate_gremlin_graph_to_manual_throughput(resource_group_name, account_name, database_name, graph_name)


def cli_cosmosdb_table_throughput_update(client,
                                         resource_group_name,
                                         account_name,
                                         table_name,
                                         throughput=None,
                                         max_throughput=None):
    """Update an Azure Cosmos DB table throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.update_table_throughput(resource_group_name, account_name, table_name, throughput_update_resource)


def cli_cosmosdb_table_throughput_migrate(client,
                                          resource_group_name,
                                          account_name,
                                          table_name,
                                          throughput_type):
    """Migrate an Azure Cosmos DB table throughput"""
    if throughput_type == "autoscale":
        return client.migrate_table_to_autoscale(resource_group_name, account_name, table_name)
    return client.migrate_table_to_manual_throughput(resource_group_name, account_name, table_name)


def _get_throughput_settings_update_parameters(throughput=None, max_throughput=None):

    if throughput and max_throughput:
        raise CLIError("Please provide max-throughput if your resource is autoscale enabled otherwise provide throughput.")
    if throughput:
        throughput_resource = ThroughputSettingsResource(throughput=throughput)
    elif max_throughput:
        throughput_resource = ThroughputSettingsResource(autoscale_settings=AutoscaleSettings(max_throughput=max_throughput))

    return ThroughputSettingsUpdateParameters(resource=throughput_resource)


def cli_cosmosdb_network_rule_list(client, resource_group_name, account_name):
    """ Lists the virtual network accounts associated with a Cosmos DB account """
    cosmos_db_account = client.get(resource_group_name, account_name)
    return cosmos_db_account.virtual_network_rules


def cli_cosmosdb_identity_show(client, resource_group_name, account_name):
    """ Show the identity associated with a Cosmos DB account """

    cosmos_db_account = client.get(resource_group_name, account_name)
    return cosmos_db_account.identity


def cli_cosmosdb_identity_assign(client,
                                 resource_group_name,
                                 account_name):
    """ Show the identity associated with a Cosmos DB account """

    existing = client.get(resource_group_name, account_name)

    if ResourceIdentityType.system_assigned.value in existing.identity.type:
        return existing.identity

    if existing.identity.type == ResourceIdentityType.user_assigned.value:
        identity = ManagedServiceIdentity(type=ResourceIdentityType.system_assigned_user_assigned.value)
    else:
        identity = ManagedServiceIdentity(type=ResourceIdentityType.system_assigned.value)
    params = DatabaseAccountUpdateParameters(identity=identity)
    async_cosmos_db_update = client.update(resource_group_name, account_name, params)
    cosmos_db_account = async_cosmos_db_update.result()
    return cosmos_db_account.identity


def cli_cosmosdb_identity_remove(client,
                                 resource_group_name,
                                 account_name):
    """ Remove the SystemAssigned identity associated with a Cosmos DB account """

    existing = client.get(resource_group_name, account_name)

    if ResourceIdentityType.system_assigned.value not in existing.identity.type:
        return existing.identity

    if ResourceIdentityType.user_assigned.value in existing.identity.type:
        identity = ManagedServiceIdentity(type=ResourceIdentityType.user_assigned.value)
    else:
        identity = ManagedServiceIdentity(type=ResourceIdentityType.none.value)
    params = DatabaseAccountUpdateParameters(identity=identity)
    async_cosmos_db_update = client.update(resource_group_name, account_name, params)
    cosmos_db_account = async_cosmos_db_update.result()
    return cosmos_db_account.identity


def _get_virtual_network_id(cmd, resource_group_name, subnet, virtual_network):
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if not is_valid_resource_id(subnet):
        if virtual_network is None:
            raise CLIError("usage error: --subnet ID | --subnet NAME --vnet-name NAME")
        subnet = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Network', type='virtualNetworks',
            name=virtual_network, child_type_1='subnets', child_name_1=subnet
        )
    return subnet


def cli_cosmosdb_network_rule_add(cmd,
                                  client,
                                  resource_group_name,
                                  account_name,
                                  subnet,
                                  virtual_network=None,
                                  ignore_missing_vnet_service_endpoint=False):
    """ Adds a virtual network rule to an existing Cosmos DB database account """
    subnet = _get_virtual_network_id(cmd, resource_group_name, subnet, virtual_network)
    existing = client.get(resource_group_name, account_name)

    virtual_network_rules = []
    rule_already_exists = False
    for rule in existing.virtual_network_rules:
        virtual_network_rules.append(
            VirtualNetworkRule(id=rule.id,
                               ignore_missing_vnet_service_endpoint=rule.ignore_missing_vnet_service_endpoint))
        if rule.id == subnet:
            rule_already_exists = True
            logger.warning("The rule exists and will be overwritten")

    if not rule_already_exists:
        virtual_network_rules.append(
            VirtualNetworkRule(id=subnet,
                               ignore_missing_vnet_service_endpoint=ignore_missing_vnet_service_endpoint))

    params = DatabaseAccountUpdateParameters(virtual_network_rules=virtual_network_rules)

    async_docdb_update = client.update(resource_group_name, account_name, params)
    docdb_account = async_docdb_update.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


def cli_cosmosdb_network_rule_remove(cmd,
                                     client,
                                     resource_group_name,
                                     account_name,
                                     subnet,
                                     virtual_network=None):
    """ Adds a virtual network rule to an existing Cosmos DB database account """
    subnet = _get_virtual_network_id(cmd, resource_group_name, subnet, virtual_network)
    existing = client.get(resource_group_name, account_name)

    virtual_network_rules = []
    rule_removed = False
    for rule in existing.virtual_network_rules:
        if rule.id != subnet:
            virtual_network_rules.append(
                VirtualNetworkRule(id=rule.id,
                                   ignore_missing_vnet_service_endpoint=rule.ignore_missing_vnet_service_endpoint))
        else:
            rule_removed = True
    if not rule_removed:
        raise CLIError("This rule does not exist for the Cosmos DB account")

    params = DatabaseAccountUpdateParameters(virtual_network_rules=virtual_network_rules)

    async_docdb_update = client.update(resource_group_name, account_name, params)
    docdb_account = async_docdb_update.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


def _update_private_endpoint_connection_status(client, resource_group_name, account_name,
                                               private_endpoint_connection_name, is_approved=True, description=None):
    private_endpoint_connection = client.get(resource_group_name=resource_group_name, account_name=account_name,
                                             private_endpoint_connection_name=private_endpoint_connection_name)

    new_status = "Approved" if is_approved else "Rejected"
    private_endpoint_connection.private_link_service_connection_state.status = new_status
    private_endpoint_connection.private_link_service_connection_state.description = description

    return client.create_or_update(resource_group_name=resource_group_name,
                                   account_name=account_name,
                                   private_endpoint_connection_name=private_endpoint_connection_name,
                                   private_link_service_connection_state=private_endpoint_connection.private_link_service_connection_state,
                                   parameters=private_endpoint_connection)


def approve_private_endpoint_connection(client, resource_group_name, account_name, private_endpoint_connection_name,
                                        description=None):
    """Approve a private endpoint connection request for Azure Cosmos DB."""

    return _update_private_endpoint_connection_status(
        client, resource_group_name, account_name, private_endpoint_connection_name, is_approved=True,
        description=description
    )


def reject_private_endpoint_connection(client, resource_group_name, account_name, private_endpoint_connection_name,
                                       description=None):
    """Reject a private endpoint connection request for Azure Cosmos DB."""

    return _update_private_endpoint_connection_status(
        client, resource_group_name, account_name, private_endpoint_connection_name, is_approved=False,
        description=description
    )


def _get_options(throughput=None, max_throughput=None):
    options = {}
    if throughput and max_throughput:
        raise CLIError("Please provide max-throughput if your resource is autoscale enabled otherwise provide throughput.")
    if throughput:
        options['throughput'] = throughput
    if max_throughput:
        options['autoscaleSettings'] = AutoscaleSettings(max_throughput=max_throughput)
    return options


######################
# data plane APIs
######################

# database operations

def _get_database_link(database_id):
    return 'dbs/{}'.format(database_id)


def _get_collection_link(database_id, collection_id):
    return 'dbs/{}/colls/{}'.format(database_id, collection_id)


def _get_offer_link(database_id, offer_id):
    return 'dbs/{}/colls/{}'.format(database_id, offer_id)


def cli_cosmosdb_database_exists(client, database_id):
    """Returns a boolean indicating whether the database exists """
    return len(list(client.QueryDatabases(
        {'query': 'SELECT * FROM root r WHERE r.id=@id',
         'parameters': [{'name': '@id', 'value': database_id}]}))) > 0


def cli_cosmosdb_database_show(client, database_id):
    """Shows an Azure Cosmos DB database """
    return client.ReadDatabase(_get_database_link(database_id))


def cli_cosmosdb_database_list(client):
    """Lists all Azure Cosmos DB databases """
    return list(client.ReadDatabases())


def cli_cosmosdb_database_create(client, database_id, throughput=None):
    """Creates an Azure Cosmos DB database """
    return client.CreateDatabase({'id': database_id}, {'offerThroughput': throughput})


def cli_cosmosdb_database_delete(client, database_id):
    """Deletes an Azure Cosmos DB database """
    client.DeleteDatabase(_get_database_link(database_id))


# collection operations

def cli_cosmosdb_collection_exists(client, database_id, collection_id):
    """Returns a boolean indicating whether the collection exists """
    return len(list(client.QueryContainers(
        _get_database_link(database_id),
        {'query': 'SELECT * FROM root r WHERE r.id=@id',
         'parameters': [{'name': '@id', 'value': collection_id}]}))) > 0


def cli_cosmosdb_collection_show(client, database_id, collection_id):
    """Shows an Azure Cosmos DB collection and its offer """
    collection = client.ReadContainer(_get_collection_link(database_id, collection_id))
    offer = _find_offer(client, collection['_self'])
    return {'collection': collection, 'offer': offer}


def cli_cosmosdb_collection_list(client, database_id):
    """Lists all Azure Cosmos DB collections """
    return list(client.ReadContainers(_get_database_link(database_id)))


def cli_cosmosdb_collection_delete(client, database_id, collection_id):
    """Deletes an Azure Cosmos DB collection """
    client.DeleteContainer(_get_collection_link(database_id, collection_id))


def _populate_collection_definition(collection,
                                    partition_key_path=None,
                                    default_ttl=None,
                                    indexing_policy=None):
    if all(arg is None for arg in [partition_key_path, default_ttl, indexing_policy]):
        return False

    if partition_key_path is not None:
        if 'partitionKey' not in collection:
            collection['partitionKey'] = {}
        collection['partitionKey'] = {'paths': [partition_key_path], 'kind': 'Hash'}

    if default_ttl is not None:
        if default_ttl == 0 and "defaultTtl" in collection:
            del collection['defaultTtl']
        elif default_ttl != 0:
            collection['defaultTtl'] = default_ttl

    if indexing_policy is not None:
        collection['indexingPolicy'] = indexing_policy

    return True


def cli_cosmosdb_collection_create(client,
                                   database_id,
                                   collection_id,
                                   throughput=None,
                                   partition_key_path=None,
                                   default_ttl=None,
                                   indexing_policy=DEFAULT_INDEXING_POLICY):
    """Creates an Azure Cosmos DB collection """
    collection = {'id': collection_id}

    options = {}
    if throughput:
        options['offerThroughput'] = throughput

    _populate_collection_definition(collection,
                                    partition_key_path,
                                    default_ttl,
                                    indexing_policy)

    created_collection = client.CreateContainer(_get_database_link(database_id), collection,
                                                options)
    offer = _find_offer(client, created_collection['_self'])
    return {'collection': created_collection, 'offer': offer}


def _find_offer(client, collection_self_link):
    logger.debug('finding offer')
    offers = client.ReadOffers()
    for o in offers:
        if o['resource'] == collection_self_link:
            return o
    return None


def cli_cosmosdb_collection_update(client,
                                   database_id,
                                   collection_id,
                                   throughput=None,
                                   default_ttl=None,
                                   indexing_policy=None):
    """Updates an Azure Cosmos DB collection """
    logger.debug('reading collection')
    collection = client.ReadContainer(_get_collection_link(database_id, collection_id))
    result = {}

    if (_populate_collection_definition(collection,
                                        None,
                                        default_ttl,
                                        indexing_policy)):
        logger.debug('replacing collection')
        result['collection'] = client.ReplaceContainer(
            _get_collection_link(database_id, collection_id), collection)

    if throughput:
        logger.debug('updating offer')
        offer = _find_offer(client, collection['_self'])

        if offer is None:
            raise CLIError("Cannot find offer for collection {}".format(collection_id))

        if 'content' not in offer:
            offer['content'] = {}
        offer['content']['offerThroughput'] = throughput

        result['offer'] = client.ReplaceOffer(offer['_self'], offer)
    return result
