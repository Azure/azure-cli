# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-lines

from enum import Enum
from knack.log import get_logger
from knack.util import CLIError
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.cli.core.util import sdk_no_wait

from azure.mgmt.cosmosdb.models import (
    ConsistencyPolicy,
    DatabaseAccountCreateUpdateParameters,
    DatabaseAccountUpdateParameters,
    DatabaseAccountRegenerateKeyParameters,
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
    PeriodicModeProperties,
    SqlRoleAssignmentCreateUpdateParameters,
    SqlRoleDefinitionCreateUpdateParameters,
    AnalyticalStorageConfiguration,
    RestoreParameters,
    ContinuousModeBackupPolicy,
    ContinuousBackupRestoreLocation,
    CreateMode,
    Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties,
    ClusterResource,
    ClusterResourceProperties,
    CommandPostBody,
    DataCenterResource,
    DataCenterResourceProperties,
    ManagedCassandraManagedServiceIdentity
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
def cli_cosmosdb_create(cmd,
                        client,
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
                        backup_redundancy=None,
                        assign_identity=None,
                        default_identity=None,
                        analytical_storage_schema_type=None,
                        backup_policy_type=None,
                        databases_to_restore=None,
                        is_restore_request=None,
                        restore_source=None,
                        restore_timestamp=None):
    """Create a new Azure Cosmos DB database account."""

    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)

    rg = resource_client.resource_groups.get(resource_group_name)
    resource_group_location = rg.location  # pylint: disable=no-member

    restore_timestamp_utc = None
    if restore_timestamp is not None:
        restore_timestamp_utc = _convert_to_utc_timestamp(
            restore_timestamp).isoformat()

    return _create_database_account(client=client,
                                    resource_group_name=resource_group_name,
                                    account_name=account_name,
                                    locations=locations,
                                    tags=tags,
                                    kind=kind,
                                    default_consistency_level=default_consistency_level,
                                    max_staleness_prefix=max_staleness_prefix,
                                    max_interval=max_interval,
                                    ip_range_filter=ip_range_filter,
                                    enable_automatic_failover=enable_automatic_failover,
                                    capabilities=capabilities,
                                    enable_virtual_network=enable_virtual_network,
                                    virtual_network_rules=virtual_network_rules,
                                    enable_multiple_write_locations=enable_multiple_write_locations,
                                    disable_key_based_metadata_write_access=disable_key_based_metadata_write_access,
                                    key_uri=key_uri,
                                    enable_public_network=enable_public_network,
                                    enable_analytical_storage=enable_analytical_storage,
                                    enable_free_tier=enable_free_tier,
                                    server_version=server_version,
                                    network_acl_bypass=network_acl_bypass,
                                    network_acl_bypass_resource_ids=network_acl_bypass_resource_ids,
                                    is_restore_request=is_restore_request,
                                    restore_source=restore_source,
                                    restore_timestamp=restore_timestamp_utc,
                                    analytical_storage_schema_type=analytical_storage_schema_type,
                                    backup_policy_type=backup_policy_type,
                                    backup_interval=backup_interval,
                                    backup_redundancy=backup_redundancy,
                                    assign_identity=assign_identity,
                                    default_identity=default_identity,
                                    backup_retention=backup_retention,
                                    databases_to_restore=databases_to_restore,
                                    arm_location=resource_group_location)


# pylint: disable=too-many-statements
# pylint: disable=too-many-branches
def _create_database_account(client,
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
                             backup_redundancy=None,
                             assign_identity=None,
                             default_identity=None,
                             backup_policy_type=None,
                             analytical_storage_schema_type=None,
                             databases_to_restore=None,
                             is_restore_request=None,
                             restore_source=None,
                             restore_timestamp=None,
                             arm_location=None):

    consistency_policy = None
    if default_consistency_level is not None:
        consistency_policy = ConsistencyPolicy(default_consistency_level=default_consistency_level,
                                               max_staleness_prefix=max_staleness_prefix,
                                               max_interval_in_seconds=max_interval)

    if not locations:
        locations = []
        locations.append(Location(location_name=arm_location, failover_priority=0, is_zone_redundant=False))

    public_network_access = None
    if enable_public_network is not None:
        public_network_access = 'Enabled' if enable_public_network else 'Disabled'

    managed_service_identity = None
    SYSTEM_ID = '[system]'
    enable_system = False
    if assign_identity is not None:
        if assign_identity == [] or (len(assign_identity) == 1 and assign_identity[0] == '[system]'):
            enable_system = True
            managed_service_identity = ManagedServiceIdentity(type=ResourceIdentityType.system_assigned.value)
        else:
            user_identities = {}
            for x in assign_identity:
                if x != SYSTEM_ID:
                    user_identities[x] = Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties()  # pylint: disable=line-too-long
                else:
                    enable_system = True
            if enable_system:
                managed_service_identity = ManagedServiceIdentity(
                    type=ResourceIdentityType.system_assigned_user_assigned.value,
                    user_assigned_identities=user_identities
                )
            else:
                managed_service_identity = ManagedServiceIdentity(
                    type=ResourceIdentityType.user_assigned.value,
                    user_assigned_identities=user_identities
                )

    api_properties = {}
    if kind == DatabaseAccountKind.mongo_db.value:
        api_properties['ServerVersion'] = server_version
    elif server_version is not None:
        raise CLIError('server-version is a valid argument only when kind is MongoDB.')

    backup_policy = None
    if backup_policy_type is not None:
        if backup_policy_type.lower() == 'periodic':
            backup_policy = PeriodicModeBackupPolicy()
            if backup_interval is not None or backup_retention is not None or backup_redundancy is not None:
                periodic_mode_properties = PeriodicModeProperties(
                    backup_interval_in_minutes=backup_interval,
                    backup_retention_interval_in_hours=backup_retention,
                    backup_storage_redundancy=backup_redundancy
                )
            backup_policy.periodic_mode_properties = periodic_mode_properties
        elif backup_policy_type.lower() == 'continuous':
            backup_policy = ContinuousModeBackupPolicy()
        else:
            raise CLIError('backup-policy-type argument is invalid.')
    elif backup_interval is not None or backup_retention is not None:
        backup_policy = PeriodicModeBackupPolicy()
        periodic_mode_properties = PeriodicModeProperties(
            backup_interval_in_minutes=backup_interval,
            backup_retention_interval_in_hours=backup_retention
        )
        backup_policy.periodic_mode_properties = periodic_mode_properties

    analytical_storage_configuration = None
    if analytical_storage_schema_type is not None:
        analytical_storage_configuration = AnalyticalStorageConfiguration()
        analytical_storage_configuration.schema_type = analytical_storage_schema_type

    create_mode = CreateMode.restore.value if is_restore_request else CreateMode.default.value
    params = None
    restore_parameters = None
    if create_mode == 'Restore':
        if restore_source is None or restore_timestamp is None:
            raise CLIError('restore-source and restore-timestamp should be provided for a restore request.')

        restore_parameters = RestoreParameters(
            restore_mode='PointInTime',
            restore_source=restore_source,
            restore_timestamp_in_utc=restore_timestamp
        )

        if databases_to_restore is not None:
            restore_parameters.databases_to_restore = databases_to_restore

    params = DatabaseAccountCreateUpdateParameters(
        location=arm_location,
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
        identity=managed_service_identity,
        default_identity=default_identity,
        analytical_storage_configuration=analytical_storage_configuration,
        create_mode=create_mode,
        restore_parameters=restore_parameters
    )

    async_docdb_create = client.begin_create_or_update(resource_group_name, account_name, params)
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
                        backup_redundancy=None,
                        default_identity=None,
                        analytical_storage_schema_type=None,
                        backup_policy_type=None):
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
    if backup_interval is not None or backup_retention is not None or backup_redundancy is not None:
        if isinstance(existing.backup_policy, PeriodicModeBackupPolicy):
            if backup_policy_type is not None and backup_policy_type.lower() == 'continuous':
                raise CLIError('backup-interval and backup-retention can only be set with periodic backup policy.')
            periodic_mode_properties = PeriodicModeProperties(
                backup_interval_in_minutes=backup_interval,
                backup_retention_interval_in_hours=backup_retention,
                backup_storage_redundancy=backup_redundancy
            )
            backup_policy = existing.backup_policy
            backup_policy.periodic_mode_properties = periodic_mode_properties
        else:
            raise CLIError(
                'backup-interval, backup-retention and backup_redundancy can only be set for accounts with periodic backup policy.')  # pylint: disable=line-too-long
    elif backup_policy_type is not None and backup_policy_type.lower() == 'continuous':
        if isinstance(existing.backup_policy, PeriodicModeBackupPolicy):
            backup_policy = ContinuousModeBackupPolicy()

    analytical_storage_configuration = None
    if analytical_storage_schema_type is not None:
        analytical_storage_configuration = AnalyticalStorageConfiguration()
        analytical_storage_configuration.schema_type = analytical_storage_schema_type

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
        default_identity=default_identity,
        analytical_storage_configuration=analytical_storage_configuration)

    async_docdb_update = client.begin_update(resource_group_name, account_name, params)
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


def cli_cosmosdb_regenerate_key(client, resource_group_name, account_name, key_kind):
    key_to_regenerate = DatabaseAccountRegenerateKeyParameters(key_kind=key_kind)
    return client.begin_regenerate_key(resource_group_name, account_name, key_to_regenerate)


def _handle_exists_exception(http_response_error):
    if http_response_error.status_code == 404:
        return False
    raise http_response_error


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

    return client.begin_create_update_sql_database(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_sql_container(resource_group_name,
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

    return client.begin_create_update_sql_container(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_sql_stored_procedure(resource_group_name,
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

    return client.begin_create_update_sql_user_defined_function(resource_group_name,
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

    return client.begin_create_update_sql_trigger(resource_group_name,
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

    return client.begin_create_update_sql_trigger(resource_group_name,
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

    return client.begin_create_update_gremlin_database(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_gremlin_graph(resource_group_name,
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

    return client.begin_create_update_gremlin_graph(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_mongo_db_database(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_mongo_db_collection(resource_group_name,
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

    return client.begin_create_update_mongo_db_collection(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_cassandra_keyspace(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_cassandra_table(resource_group_name,
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

    return client.begin_create_update_cassandra_table(resource_group_name,
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
    except HttpResponseError as ex:
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

    return client.begin_create_update_table(resource_group_name, account_name, table_name, table)


def cli_cosmosdb_table_exists(client,
                              resource_group_name,
                              account_name,
                              table_name):
    """Checks if an Azure Cosmos DB table exists"""
    try:
        client.get_table(resource_group_name, account_name, table_name)
    except HttpResponseError as ex:
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
    return client.begin_update_sql_database_throughput(resource_group_name,
                                                       account_name,
                                                       database_name,
                                                       throughput_update_resource)


def cli_cosmosdb_sql_database_throughput_migrate(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 throughput_type):
    if throughput_type == "autoscale":
        return client.begin_migrate_sql_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.begin_migrate_sql_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_sql_container_throughput_update(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 container_name,
                                                 throughput=None,
                                                 max_throughput=None):
    """Update an Azure Cosmos DB SQL container throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_sql_container_throughput(resource_group_name,
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
        return client.begin_migrate_sql_container_to_autoscale(resource_group_name, account_name,
                                                               database_name, container_name)
    return client.begin_migrate_sql_container_to_manual_throughput(resource_group_name, account_name,
                                                                   database_name, container_name)


def cli_cosmosdb_mongodb_database_throughput_update(client,
                                                    resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    throughput=None,
                                                    max_throughput=None):
    """Update an Azure Cosmos DB MongoDB database throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_mongo_db_database_throughput(resource_group_name,
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
        return client.begin_migrate_mongo_db_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.begin_migrate_mongo_db_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_mongodb_collection_throughput_update(client,
                                                      resource_group_name,
                                                      account_name,
                                                      database_name,
                                                      collection_name,
                                                      throughput=None,
                                                      max_throughput=None):
    """Update an Azure Cosmos DB MongoDB collection throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_mongo_db_collection_throughput(resource_group_name,
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
        return client.begin_migrate_mongo_db_collection_to_autoscale(resource_group_name, account_name,
                                                                     database_name, collection_name)
    return client.begin_migrate_mongo_db_collection_to_manual_throughput(resource_group_name, account_name,
                                                                         database_name, collection_name)


def cli_cosmosdb_cassandra_keyspace_throughput_update(client,
                                                      resource_group_name,
                                                      account_name,
                                                      keyspace_name,
                                                      throughput=None,
                                                      max_throughput=None):
    """Update an Azure Cosmos DB Cassandra keyspace throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_cassandra_keyspace_throughput(resource_group_name,
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
        return client.begin_migrate_cassandra_keyspace_to_autoscale(resource_group_name, account_name, keyspace_name)
    return client.begin_migrate_cassandra_keyspace_to_manual_throughput(resource_group_name,
                                                                        account_name, keyspace_name)


def cli_cosmosdb_cassandra_table_throughput_update(client,
                                                   resource_group_name,
                                                   account_name,
                                                   keyspace_name,
                                                   table_name,
                                                   throughput=None,
                                                   max_throughput=None):
    """Update an Azure Cosmos DB Cassandra table throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_cassandra_table_throughput(resource_group_name,
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
        return client.begin_migrate_cassandra_table_to_autoscale(resource_group_name, account_name,
                                                                 keyspace_name, table_name)
    return client.begin_migrate_cassandra_table_to_manual_throughput(resource_group_name, account_name,
                                                                     keyspace_name, table_name)


def cli_cosmosdb_gremlin_database_throughput_update(client,
                                                    resource_group_name,
                                                    account_name,
                                                    database_name,
                                                    throughput=None,
                                                    max_throughput=None):
    """Update an Azure Cosmos DB Gremlin database throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_gremlin_database_throughput(resource_group_name,
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
        return client.begin_migrate_gremlin_database_to_autoscale(resource_group_name, account_name, database_name)
    return client.begin_migrate_gremlin_database_to_manual_throughput(resource_group_name, account_name, database_name)


def cli_cosmosdb_gremlin_graph_throughput_update(client,
                                                 resource_group_name,
                                                 account_name,
                                                 database_name,
                                                 graph_name,
                                                 throughput=None,
                                                 max_throughput=None):
    """Update an Azure Cosmos DB Gremlin graph throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_gremlin_graph_throughput(resource_group_name,
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
        return client.begin_migrate_gremlin_graph_to_autoscale(resource_group_name, account_name,
                                                               database_name, graph_name)
    return client.begin_migrate_gremlin_graph_to_manual_throughput(resource_group_name, account_name,
                                                                   database_name, graph_name)


def cli_cosmosdb_table_throughput_update(client,
                                         resource_group_name,
                                         account_name,
                                         table_name,
                                         throughput=None,
                                         max_throughput=None):
    """Update an Azure Cosmos DB table throughput"""
    throughput_update_resource = _get_throughput_settings_update_parameters(throughput, max_throughput)
    return client.begin_update_table_throughput(resource_group_name, account_name, table_name,
                                                throughput_update_resource)


def cli_cosmosdb_table_throughput_migrate(client,
                                          resource_group_name,
                                          account_name,
                                          table_name,
                                          throughput_type):
    """Migrate an Azure Cosmos DB table throughput"""
    if throughput_type == "autoscale":
        return client.begin_migrate_table_to_autoscale(resource_group_name, account_name, table_name)
    return client.begin_migrate_table_to_manual_throughput(resource_group_name, account_name, table_name)


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
                                 account_name,
                                 identities=None):
    """ Update the identities associated with a Cosmos DB account """

    existing = client.get(resource_group_name, account_name)

    SYSTEM_ID = '[system]'
    enable_system = identities is None or SYSTEM_ID in identities
    new_user_identities = []
    if identities is not None:
        new_user_identities = [x for x in identities if x != SYSTEM_ID]

    only_enabling_system = enable_system and len(new_user_identities) == 0
    system_already_added = existing.identity.type == ResourceIdentityType.system_assigned or existing.identity.type == ResourceIdentityType.system_assigned_user_assigned
    all_new_users_already_added = new_user_identities and existing.identity and existing.identity.user_assigned_identities and all(x in existing.identity.user_assigned_identities for x in new_user_identities)
    if only_enabling_system and system_already_added:
        return existing.identity
    if (not enable_system) and all_new_users_already_added:
        return existing.identity
    if enable_system and system_already_added and all_new_users_already_added:
        return existing.identity

    if existing.identity and existing.identity.type == ResourceIdentityType.system_assigned_user_assigned:
        identity_type = ResourceIdentityType.system_assigned_user_assigned
    elif existing.identity and existing.identity.type == ResourceIdentityType.system_assigned and new_user_identities:
        identity_type = ResourceIdentityType.system_assigned_user_assigned
    elif existing.identity and existing.identity.type == ResourceIdentityType.user_assigned and enable_system:
        identity_type = ResourceIdentityType.system_assigned_user_assigned
    elif new_user_identities and enable_system:
        identity_type = ResourceIdentityType.system_assigned_user_assigned
    elif new_user_identities:
        identity_type = ResourceIdentityType.user_assigned
    else:
        identity_type = ResourceIdentityType.system_assigned

    if identity_type in [ResourceIdentityType.system_assigned, ResourceIdentityType.none]:
        new_identity = ManagedServiceIdentity(type=identity_type.value)
    else:
        new_assigned_identities = existing.identity.user_assigned_identities or {}
        for identity in new_user_identities:
            new_assigned_identities[identity] = Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties()

        new_identity = ManagedServiceIdentity(type=identity_type.value, user_assigned_identities=new_assigned_identities)

    params = DatabaseAccountUpdateParameters(identity=new_identity)
    async_cosmos_db_update = client.begin_update(resource_group_name, account_name, params)
    cosmos_db_account = async_cosmos_db_update.result()
    return cosmos_db_account.identity


def cli_cosmosdb_identity_remove(client,
                                 resource_group_name,
                                 account_name,
                                 identities=None):
    """ Remove the identities associated with a Cosmos DB account """

    existing = client.get(resource_group_name, account_name)

    SYSTEM_ID = '[system]'
    remove_system_assigned_identity = False
    if not identities:
        remove_system_assigned_identity = True
    elif SYSTEM_ID in identities:
        remove_system_assigned_identity = True
        identities.remove(SYSTEM_ID)

    if existing.identity is None:
        return ManagedServiceIdentity(type=ResourceIdentityType.none.value)
    if existing.identity.user_assigned_identities:
        existing_identities = existing.identity.user_assigned_identities.keys()
    else:
        existing_identities = []
    if identities:
        identities_to_remove = identities
    else:
        identities_to_remove = []
    non_existing = [x for x in identities_to_remove if x not in set(existing_identities)]

    if non_existing:
        raise CLIError("'{}' are not associated with '{}'".format(','.join(non_existing), account_name))
    identities_remaining = [x for x in existing_identities if x not in set(identities_to_remove)]
    if remove_system_assigned_identity and ((not existing.identity) or (existing.identity and existing.identity.type in [ResourceIdentityType.none, ResourceIdentityType.user_assigned])):
        raise CLIError("System-assigned identity is not associated with '{}'".format(account_name))

    if identities_remaining and not remove_system_assigned_identity and existing.identity.type == ResourceIdentityType.system_assigned_user_assigned:
        set_type = ResourceIdentityType.system_assigned_user_assigned
    elif identities_remaining and remove_system_assigned_identity and existing.identity.type == ResourceIdentityType.system_assigned_user_assigned:
        set_type = ResourceIdentityType.user_assigned
    elif identities_remaining and not remove_system_assigned_identity and existing.identity.type == ResourceIdentityType.user_assigned:
        set_type = ResourceIdentityType.user_assigned
    elif not identities_remaining and not remove_system_assigned_identity and existing.identity.type == ResourceIdentityType.system_assigned_user_assigned:
        set_type = ResourceIdentityType.system_assigned
    elif not identities_remaining and not remove_system_assigned_identity and existing.identity.type == ResourceIdentityType.system_assigned:
        set_type = ResourceIdentityType.system_assigned
    else:
        set_type = ResourceIdentityType.none

    new_user_identities = {}
    for identity in identities_remaining:
        new_user_identities[identity] = Components1Jq1T4ISchemasManagedserviceidentityPropertiesUserassignedidentitiesAdditionalproperties()
    if set_type in [ResourceIdentityType.system_assigned_user_assigned, ResourceIdentityType.user_assigned]:
        for removed_identity in identities_to_remove:
            new_user_identities[removed_identity] = None
    if not new_user_identities:
        new_user_identities = None

    params = DatabaseAccountUpdateParameters(identity=ManagedServiceIdentity(type=set_type, user_assigned_identities=new_user_identities))
    async_cosmos_db_update = client.begin_update(resource_group_name, account_name, params)
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
                               ignore_missing_v_net_service_endpoint=rule.ignore_missing_v_net_service_endpoint))
        if rule.id == subnet:
            rule_already_exists = True
            logger.warning("The rule exists and will be overwritten")

    if not rule_already_exists:
        virtual_network_rules.append(
            VirtualNetworkRule(id=subnet,
                               ignore_missing_v_net_service_endpoint=ignore_missing_vnet_service_endpoint))

    params = DatabaseAccountUpdateParameters(virtual_network_rules=virtual_network_rules)

    async_docdb_update = client.begin_update(resource_group_name, account_name, params)
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
                                   ignore_missing_v_net_service_endpoint=rule.ignore_missing_v_net_service_endpoint))
        else:
            rule_removed = True
    if not rule_removed:
        raise CLIError("This rule does not exist for the Cosmos DB account")

    params = DatabaseAccountUpdateParameters(virtual_network_rules=virtual_network_rules)

    async_docdb_update = client.begin_update(resource_group_name, account_name, params)
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

    return client.begin_create_or_update(resource_group_name=resource_group_name,
                                         account_name=account_name,
                                         private_endpoint_connection_name=private_endpoint_connection_name,
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


# pylint: disable=too-many-statements
def cli_cosmosdb_restore(cmd,
                         client,
                         resource_group_name,
                         account_name,
                         target_database_account_name,
                         restore_timestamp,
                         location,
                         databases_to_restore=None):
    from azure.cli.command_modules.cosmosdb._client_factory import cf_restorable_database_accounts
    restorable_database_accounts_client = cf_restorable_database_accounts(cmd.cli_ctx, [])
    restorable_database_accounts = restorable_database_accounts_client.list()
    restorable_database_accounts_list = list(restorable_database_accounts)
    target_restorable_account = None
    restore_timestamp_datetime_utc = _convert_to_utc_timestamp(restore_timestamp)

    # If restore timestamp is timezone aware, get the utcnow as timezone aware as well
    from datetime import datetime, timezone
    current_dateTime = datetime.utcnow()
    if restore_timestamp_datetime_utc.tzinfo is not None and restore_timestamp_datetime_utc.tzinfo.utcoffset(restore_timestamp_datetime_utc) is not None:
        current_dateTime = datetime.now(timezone.utc)

    # Fail if provided restoretimesamp is greater than current timestamp
    if restore_timestamp_datetime_utc > current_dateTime:
        raise CLIError("Restore timestamp {} should be less than current timestamp {}".format(restore_timestamp_datetime_utc, current_dateTime))

    is_source_restorable_account_deleted = False
    for account in restorable_database_accounts_list:
        if account.account_name == account_name:
            if account.deletion_time is not None:
                if account.deletion_time >= restore_timestamp_datetime_utc >= account.creation_time:
                    target_restorable_account = account
                    is_source_restorable_account_deleted = True
                    break
            else:
                if restore_timestamp_datetime_utc >= account.creation_time:
                    target_restorable_account = account
                    break

    if target_restorable_account is None:
        raise CLIError("Cannot find a database account with name {} that is online at {}".format(account_name, restore_timestamp))

    # Validate if source account is empty only for live account restores. For deleted account restores the api will not work
    if not is_source_restorable_account_deleted:
        restorable_resources = None
        if target_restorable_account.api_type.lower() == "sql":
            try:
                from azure.cli.command_modules.cosmosdb._client_factory import cf_restorable_sql_resources
                restorable_sql_resources_client = cf_restorable_sql_resources(cmd.cli_ctx, [])
                restorable_resources = restorable_sql_resources_client.list(
                    target_restorable_account.location,
                    target_restorable_account.name,
                    location,
                    restore_timestamp_datetime_utc)
            except ResourceNotFoundError:
                raise CLIError("Cannot find a database account with name {} that is online at {} in location {}".format(account_name, restore_timestamp, location))
        elif target_restorable_account.api_type.lower() == "mongodb":
            try:
                from azure.cli.command_modules.cosmosdb._client_factory import cf_restorable_mongodb_resources
                restorable_mongodb_resources_client = cf_restorable_mongodb_resources(cmd.cli_ctx, [])
                restorable_resources = restorable_mongodb_resources_client.list(
                    target_restorable_account.location,
                    target_restorable_account.name,
                    location,
                    restore_timestamp_datetime_utc)
            except ResourceNotFoundError:
                raise CLIError("Cannot find a database account with name {} that is online at {} in location {}".format(account_name, restore_timestamp, location))
        else:
            raise CLIError("Provided API Type {} is not supported for account {}".format(target_restorable_account.api_type, account_name))

        if restorable_resources is None or not any(restorable_resources):
            raise CLIError("Database account {} contains no restorable resources in location {} at given restore timestamp {}".format(target_restorable_account, location, restore_timestamp_datetime_utc))

    # Trigger restore
    locations = []
    locations.append(Location(location_name=location, failover_priority=0))

    return _create_database_account(client,
                                    resource_group_name=resource_group_name,
                                    account_name=target_database_account_name,
                                    locations=locations,
                                    is_restore_request=True,
                                    restore_source=target_restorable_account.id,
                                    restore_timestamp=restore_timestamp_datetime_utc.isoformat(),
                                    databases_to_restore=databases_to_restore,
                                    arm_location=target_restorable_account.location)


def _convert_to_utc_timestamp(timestamp_string):
    import dateutil
    import datetime
    import dateutil.parser
    timestamp_datetime = dateutil.parser.parse(timestamp_string)
    timestamp_datetime_utc = None
    # Convert to utc only if timezone aware
    if timestamp_datetime.tzinfo is not None and timestamp_datetime.tzinfo.utcoffset(timestamp_datetime) is not None:
        timestamp_datetime_utc = timestamp_datetime.astimezone(datetime.timezone.utc)
    else:
        timestamp_datetime_utc = timestamp_datetime
    return timestamp_datetime_utc


def cli_cosmosdb_restorable_database_account_list(client,
                                                  location=None,
                                                  account_name=None):
    restorable_database_accounts = None
    if location is not None:
        restorable_database_accounts = client.list_by_location(location)
    else:
        restorable_database_accounts = client.list()

    if account_name is None:
        return restorable_database_accounts

    matching_restorable_accounts = []
    restorable_database_accounts_list = list(restorable_database_accounts)
    for account in restorable_database_accounts_list:
        if account.account_name == account_name:
            matching_restorable_accounts.append(account)
    return matching_restorable_accounts


def cli_sql_retrieve_latest_backup_time(client,
                                        resource_group_name,
                                        account_name,
                                        database_name,
                                        container_name,
                                        location):
    try:
        client.get_sql_database(resource_group_name, account_name, database_name)
    except Exception as ex:
        if ex.error.code == "NotFound":
            raise CLIError("(NotFound) Database with name '{}' could not be found.".format(database_name))
        raise CLIError("{}".format(str(ex)))

    try:
        client.get_sql_container(resource_group_name, account_name, database_name, container_name)
    except Exception as ex:
        if ex.error.code == "NotFound":
            raise CLIError("(NotFound) Container with name '{}' under database '{}' could not be found.".format(container_name, database_name))
        raise CLIError("{}".format(str(ex)))

    restoreLocation = ContinuousBackupRestoreLocation(
        location=location
    )

    asyc_backupInfo = client.begin_retrieve_continuous_backup_information(resource_group_name,
                                                                          account_name,
                                                                          database_name,
                                                                          container_name,
                                                                          restoreLocation)
    return asyc_backupInfo.result()


def cli_mongo_db_retrieve_latest_backup_time(client,
                                             resource_group_name,
                                             account_name,
                                             database_name,
                                             collection_name,
                                             location):
    try:
        client.get_mongo_db_database(resource_group_name, account_name, database_name)
    except Exception as ex:
        if ex.error.code == "NotFound":
            raise CLIError("(NotFound) Database with name '{}' could not be found.".format(database_name))
        raise CLIError("{}".format(str(ex)))

    try:
        client.get_mongo_db_collection(resource_group_name, account_name, database_name, collection_name)
    except Exception as ex:
        if ex.error.code == "NotFound":
            raise CLIError("(NotFound) Collection with name '{}' under database '{}' could not be found.".format(collection_name, database_name))
        raise CLIError("{}".format(str(ex)))

    restoreLocation = ContinuousBackupRestoreLocation(
        location=location
    )

    asyc_backupInfo = client.begin_retrieve_continuous_backup_information(resource_group_name,
                                                                          account_name,
                                                                          database_name,
                                                                          collection_name,
                                                                          restoreLocation)
    return asyc_backupInfo.result()


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


def cli_cosmosdb_sql_role_definition_create(client,
                                            resource_group_name,
                                            account_name,
                                            role_definition_body,
                                            no_wait=False):
    '''Creates an Azure Cosmos DB SQL Role Definition '''
    role_definition_create_resource = SqlRoleDefinitionCreateUpdateParameters(
        role_name=role_definition_body['RoleName'],
        type=role_definition_body['Type'],
        assignable_scopes=role_definition_body['AssignableScopes'],
        permissions=role_definition_body['Permissions'])

    return sdk_no_wait(no_wait, client.begin_create_update_sql_role_definition, role_definition_body['Id'], resource_group_name, account_name, role_definition_create_resource)


def cli_cosmosdb_sql_role_definition_update(client,
                                            resource_group_name,
                                            account_name,
                                            role_definition_body,
                                            no_wait=False):
    '''Update an existing Azure Cosmos DB Sql Role Definition'''
    logger.debug('reading SQL role definition')
    role_definition = client.get_sql_role_definition(role_definition_body['Id'], resource_group_name, account_name)

    if role_definition_body['RoleName'] is not None:
        role_definition.role_name = role_definition_body['RoleName']

    if role_definition_body['AssignableScopes'] is not None:
        role_definition.assignable_scopes = role_definition_body['AssignableScopes']

    if role_definition_body['Permissions'] is not None:
        role_definition.permissions = role_definition_body['Permissions']

    role_definition_update_resource = SqlRoleDefinitionCreateUpdateParameters(
        role_name=role_definition.role_name,
        type=role_definition_body['Type'],
        assignable_scopes=role_definition.assignable_scopes,
        permissions=role_definition.permissions)

    return sdk_no_wait(no_wait, client.begin_create_update_sql_role_definition, role_definition_body['Id'], resource_group_name, account_name, role_definition_update_resource)


def cli_cosmosdb_sql_role_definition_exists(client,
                                            resource_group_name,
                                            account_name,
                                            role_definition_id):
    """Checks if an Azure Cosmos DB Sql Role Definition exists"""
    try:
        client.get_sql_role_definition(role_definition_id, resource_group_name, account_name)
    except ResourceNotFoundError:
        return False

    return True


def cli_cosmosdb_sql_role_assignment_create(client,
                                            resource_group_name,
                                            account_name,
                                            scope,
                                            principal_id,
                                            role_assignment_id=None,
                                            role_definition_name=None,
                                            role_definition_id=None,
                                            no_wait=False):
    """Creates an Azure Cosmos DB Sql Role Assignment"""

    if role_definition_id is not None and role_definition_name is not None:
        raise CLIError('Can only provide one out of role_definition_id and role_definition_name.')

    if role_definition_id is None and role_definition_name is None:
        raise CLIError('Providing one out of role_definition_id and role_definition_name is required.')

    if role_definition_name is not None:
        role_definition_id = get_associated_role_definition_id(client, resource_group_name, account_name, role_definition_name)

    sql_role_assignment_create_update_parameters = SqlRoleAssignmentCreateUpdateParameters(
        role_definition_id=role_definition_id,
        scope=scope,
        principal_id=principal_id)

    return sdk_no_wait(no_wait, client.begin_create_update_sql_role_assignment, role_assignment_id, resource_group_name, account_name, sql_role_assignment_create_update_parameters)


def cli_cosmosdb_sql_role_assignment_update(client,
                                            resource_group_name,
                                            account_name,
                                            role_assignment_id,
                                            scope=None,
                                            principal_id=None,
                                            role_definition_name=None,
                                            role_definition_id=None,
                                            no_wait=False):
    """Updates an Azure Cosmos DB Sql Role Assignment"""

    if role_definition_id is not None and role_definition_name is not None:
        raise CLIError('Can only provide one out of role_definition_id and role_definition_name.')

    logger.debug('reading Sql Role Assignment')
    role_assignment = client.get_sql_role_assignment(role_assignment_id, resource_group_name, account_name)

    logger.debug('replacing Sql Role Assignment')

    if role_definition_name is not None:
        role_definition_id = get_associated_role_definition_id(client, resource_group_name, account_name, role_definition_name)

    sql_role_assignment_create_update_parameters = SqlRoleAssignmentCreateUpdateParameters(
        role_definition_id=role_definition_id if role_definition_id is not None else role_assignment.role_definition_id,
        scope=scope if scope is not None else role_assignment.scope,
        principal_id=principal_id if principal_id is not None else role_assignment.principal_id)

    return sdk_no_wait(no_wait, client.begin_create_update_sql_role_assignment, role_assignment_id, resource_group_name, account_name, sql_role_assignment_create_update_parameters)


def cli_cosmosdb_sql_role_assignment_exists(client,
                                            resource_group_name,
                                            account_name,
                                            role_assignment_id):
    """Checks if an Azure Cosmos DB Sql Role Assignment exists"""
    try:
        client.get_sql_role_assignment(role_assignment_id, resource_group_name, account_name)
    except ResourceNotFoundError:
        return False

    return True


def get_associated_role_definition_id(client,
                                      resource_group_name,
                                      account_name,
                                      role_definition_name=None):
    logger.debug('reading Sql Role Definition')

    role_definitions = client.list_sql_role_definitions(resource_group_name, account_name)
    matching_role_definition = next((role_definition for role_definition in role_definitions if role_definition.role_name.lower() == role_definition_name.lower()), None)
    if matching_role_definition is None:
        raise CLIError('No Role Definition found with name [{}].'.format(role_definition_name))

    return matching_role_definition.id


def cli_cosmosdb_managed_cassandra_cluster_create(client,
                                                  resource_group_name,
                                                  cluster_name,
                                                  location,
                                                  delegated_management_subnet_id,
                                                  tags=None,
                                                  identity_type='None',
                                                  cluster_name_override=None,
                                                  initial_cassandra_admin_password=None,
                                                  client_certificates=None,
                                                  external_gossip_certificates=None,
                                                  external_seed_nodes=None,
                                                  restore_from_backup_id=None,
                                                  cassandra_version=None,
                                                  authentication_method=None,
                                                  hours_between_backups=None,
                                                  repair_enabled=None):

    """Creates an Azure Managed Cassandra Cluster"""

    if authentication_method != 'None' and initial_cassandra_admin_password is None and external_gossip_certificates is None:
        raise CLIError('At least one out of the Initial Cassandra Admin Password or External Gossip Certificates is required.')

    if initial_cassandra_admin_password is not None and external_gossip_certificates is not None:
        raise CLIError('Only one out of the Initial Cassandra Admin Password or External Gossip Certificates has to be specified.')

    cluster_properties = ClusterResourceProperties(
        delegated_management_subnet_id=delegated_management_subnet_id,
        cluster_name_override=cluster_name_override,
        initial_cassandra_admin_password=initial_cassandra_admin_password,
        client_certificates=client_certificates,
        external_gossip_certificates=external_gossip_certificates,
        external_seed_nodes=external_seed_nodes,
        restore_from_backup_id=restore_from_backup_id,
        cassandra_version=cassandra_version,
        authentication_method=authentication_method,
        hours_between_backups=hours_between_backups,
        repair_enabled=repair_enabled)

    managed_service_identity_parameter = ManagedCassandraManagedServiceIdentity(
        type=identity_type
    )

    cluster_resource_create_update_parameters = ClusterResource(
        location=location,
        tags=tags,
        identity=managed_service_identity_parameter,
        properties=cluster_properties)

    return client.begin_create_update(resource_group_name, cluster_name, cluster_resource_create_update_parameters)


def cli_cosmosdb_managed_cassandra_cluster_update(client,
                                                  resource_group_name,
                                                  cluster_name,
                                                  tags=None,
                                                  identity_type=None,
                                                  client_certificates=None,
                                                  external_gossip_certificates=None,
                                                  external_seed_nodes=None,
                                                  cassandra_version=None,
                                                  authentication_method=None,
                                                  hours_between_backups=None,
                                                  repair_enabled=None):

    """Updates an Azure Managed Cassandra Cluster"""

    cluster_resource = client.get(resource_group_name, cluster_name)

    if client_certificates is None:
        client_certificates = cluster_resource.properties.client_certificates

    if external_gossip_certificates is None:
        external_gossip_certificates = cluster_resource.properties.external_gossip_certificates

    if external_seed_nodes is None:
        external_seed_nodes = cluster_resource.properties.external_seed_nodes

    if cassandra_version is None:
        cassandra_version = cluster_resource.properties.cassandra_version

    if authentication_method is None:
        authentication_method = cluster_resource.properties.authentication_method

    if hours_between_backups is None:
        hours_between_backups = cluster_resource.properties.hours_between_backups

    if repair_enabled is None:
        repair_enabled = cluster_resource.properties.repair_enabled

    if tags is None:
        tags = cluster_resource.tags

    identity = cluster_resource.identity

    if identity_type is not None:
        identity = ManagedCassandraManagedServiceIdentity(type=identity_type)

    cluster_properties = ClusterResourceProperties(
        provisioning_state=cluster_resource.properties.provisioning_state,
        restore_from_backup_id=cluster_resource.properties.restore_from_backup_id,
        delegated_management_subnet_id=cluster_resource.properties.delegated_management_subnet_id,
        cassandra_version=cassandra_version,
        cluster_name_override=cluster_resource.properties.cluster_name_override,
        authentication_method=authentication_method,
        initial_cassandra_admin_password=cluster_resource.properties.initial_cassandra_admin_password,
        hours_between_backups=hours_between_backups,
        repair_enabled=repair_enabled,
        client_certificates=client_certificates,
        external_gossip_certificates=external_gossip_certificates,
        gossip_certificates=cluster_resource.properties.gossip_certificates,
        external_seed_nodes=external_seed_nodes,
        seed_nodes=cluster_resource.properties.seed_nodes
    )

    cluster_resource_create_update_parameters = ClusterResource(
        location=cluster_resource.location,
        tags=tags,
        identity=identity,
        properties=cluster_properties)

    return client.begin_create_update(resource_group_name, cluster_name, cluster_resource_create_update_parameters)


def cli_cosmosdb_managed_cassandra_cluster_list(client,
                                                resource_group_name=None):

    """List Azure Managed Cassandra Clusters by resource group and subscription."""

    if resource_group_name is None:
        return client.list_by_subscription()

    return client.list_by_resource_group(resource_group_name)


def cli_cosmosdb_managed_cassandra_cluster_invoke_command(client,
                                                          resource_group_name,
                                                          cluster_name,
                                                          command_name,
                                                          host,
                                                          arguments=None,
                                                          cassandra_stop_start=None,
                                                          readwrite=None):

    """Invokes a command in Azure Managed Cassandra Cluster host"""

    cluster_invoke_command = CommandPostBody(
        command=command_name,
        host=host,
        arguments=arguments,
        cassandra_stop_start=cassandra_stop_start,
        readwrite=readwrite
    )

    return client.begin_invoke_command(resource_group_name, cluster_name, cluster_invoke_command)


def cli_cosmosdb_managed_cassandra_cluster_status(client,
                                                  resource_group_name,
                                                  cluster_name):

    """Get Azure Managed Cassandra Cluster Node Status"""

    return client.status(resource_group_name, cluster_name)


def cli_cosmosdb_managed_cassandra_cluster_deallocate(client,
                                                      resource_group_name,
                                                      cluster_name):

    """Deallocate Azure Managed Cassandra Cluster"""

    return client.begin_deallocate(resource_group_name, cluster_name)


def cli_cosmosdb_managed_cassandra_cluster_start(client,
                                                 resource_group_name,
                                                 cluster_name):

    """Start Azure Managed Cassandra Cluster"""

    return client.begin_start(resource_group_name, cluster_name)


def cli_cosmosdb_managed_cassandra_datacenter_create(client,
                                                     resource_group_name,
                                                     cluster_name,
                                                     data_center_name,
                                                     data_center_location,
                                                     delegated_subnet_id,
                                                     node_count,
                                                     base64_encoded_cassandra_yaml_fragment=None,
                                                     managed_disk_customer_key_uri=None,
                                                     backup_storage_customer_key_uri=None,
                                                     sku=None,
                                                     disk_sku=None,
                                                     disk_capacity=None,
                                                     availability_zone=None):

    """Creates an Azure Managed Cassandra Datacenter"""

    data_center_properties = DataCenterResourceProperties(
        data_center_location=data_center_location,
        delegated_subnet_id=delegated_subnet_id,
        node_count=node_count,
        base64_encoded_cassandra_yaml_fragment=base64_encoded_cassandra_yaml_fragment,
        sku=sku,
        disk_sku=disk_sku,
        disk_capacity=disk_capacity,
        availability_zone=availability_zone,
        managed_disk_customer_key_uri=managed_disk_customer_key_uri,
        backup_storage_customer_key_uri=backup_storage_customer_key_uri
    )

    data_center_resource = DataCenterResource(
        properties=data_center_properties
    )

    return client.begin_create_update(resource_group_name, cluster_name, data_center_name, data_center_resource)


def cli_cosmosdb_managed_cassandra_datacenter_update(client,
                                                     resource_group_name,
                                                     cluster_name,
                                                     data_center_name,
                                                     node_count=None,
                                                     base64_encoded_cassandra_yaml_fragment=None,
                                                     managed_disk_customer_key_uri=None,
                                                     backup_storage_customer_key_uri=None):

    """Updates an Azure Managed Cassandra DataCenter"""

    data_center_resource = client.get(resource_group_name, cluster_name, data_center_name)

    if node_count is None:
        node_count = data_center_resource.properties.node_count

    if base64_encoded_cassandra_yaml_fragment is None:
        base64_encoded_cassandra_yaml_fragment = data_center_resource.properties.base64_encoded_cassandra_yaml_fragment

    if managed_disk_customer_key_uri is None:
        managed_disk_customer_key_uri = data_center_resource.properties.managed_disk_customer_key_uri

    if backup_storage_customer_key_uri is None:
        backup_storage_customer_key_uri = data_center_resource.properties.backup_storage_customer_key_uri

    data_center_properties = DataCenterResourceProperties(
        data_center_location=data_center_resource.properties.data_center_location,
        delegated_subnet_id=data_center_resource.properties.delegated_subnet_id,
        node_count=node_count,
        seed_nodes=data_center_resource.properties.seed_nodes,
        base64_encoded_cassandra_yaml_fragment=base64_encoded_cassandra_yaml_fragment,
        managed_disk_customer_key_uri=managed_disk_customer_key_uri,
        backup_storage_customer_key_uri=backup_storage_customer_key_uri
    )

    data_center_resource = DataCenterResource(
        properties=data_center_properties
    )

    return client.begin_create_update(resource_group_name, cluster_name, data_center_name, data_center_resource)
