# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-statements
# pylint: disable=line-too-long
from enum import Enum
from argcomplete.completers import FilesCompleter

from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, name_type, get_enum_type, get_three_state_flag, tags_type, get_location_type)
from azure.cli.core.util import shell_safe_json_parse

from azure.cli.command_modules.cosmosdb._validators import (
    validate_failover_policies, validate_capabilities,
    validate_virtual_network_rules, validate_ip_range_filter,
    validate_role_definition_body,
    validate_role_definition_id,
    validate_fully_qualified_role_definition_id,
    validate_role_assignment_id,
    validate_scope,
    validate_gossip_certificates,
    validate_client_certificates,
    validate_seednodes,
    validate_node_count,
    validate_client_encryption_policy,
    validate_mongo_role_definition_body,
    validate_mongo_role_definition_id,
    validate_mongo_user_definition_body,
    validate_mongo_user_definition_id,
    validate_fleetspace_body,
    validate_fleetspaceAccount_body)

from azure.cli.command_modules.cosmosdb.actions import (
    CreateLocation, CreateDatabaseRestoreResource, CreateGremlinDatabaseRestoreResource, CreateTableRestoreResource, UtcDatetimeAction, InvokeCommandArgumentsAddAction)
from azure.cli.command_modules.cosmosdb.custom import (
    CosmosKeyTypes)
from azure.mgmt.cosmosdb.models import (
    ContinuousTier, MinimalTlsVersion, DefaultPriorityLevel)

GREMLIN_INDEXING_POLICY_EXAMPLE = """--idx "{\\"indexingMode\\": \\"consistent\\", \\"automatic\\": true, \\"includedPaths\\": [{\\"path\\": \\"/*\\"}], \\"excludedPaths\\": [{ \\"path\\": \\"/headquarters/employees/?\\"}, { \\"path\\": \\"/\\\\"_etag\\\\"/?\\"}]}"
"""
SQL_INDEXING_POLICY_EXAMPLE = """--idx "{\\"indexingMode\\": \\"consistent\\", \\"automatic\\": true, \\"includedPaths\\": [{\\"path\\": \\"/*\\"}], \\"excludedPaths\\": [{ \\"path\\": \\"/headquarters/employees/?\\"}, { \\"path\\": \\"/\\\\"_etag\\\\"/?\\"}],\\"vectorIndexes\\": [{\\"path\\": \\"/vector1\\",\\"type\\": \\"flat\\"}]}"
"""

SQL_VECTOR_EMBEDDING_POLICY_EXAMPLE = """--vector-embeddings "{\\"vectorEmbeddings\\": [{\\"path\\": \\"/vector1\\", \\"dataType\\": \\"float32\\", \\"dimensions\\": 2, \\"distanceFunction\\": \\"dotproduct\\" }]}"
"""

SQL_FULL_TEXT_SEARCH_POLICY_EXAMPLE = """--full-text-policy "{\\"fullTextPaths\\": [{\\"path\\": \\"/ftPath1\\", \\"language\\": \\"en-US\\" }]}"
"""

SQL_UNIQUE_KEY_POLICY_EXAMPLE = """--unique-key-policy "{\\"uniqueKeys\\": [{\\"paths\\": [\\"/path/to/key1\\"]}, {\\"paths\\": [\\"/path/to/key2\\"]}]}"
"""

SQL_CLIENT_ENCRYPTION_POLICY_EXAMPLE = """--cep "{\\"includedPaths\\": [{\\"path\\": \\"/path1\\",\\"clientEncryptionKeyId\\": \\"key1\\",\\"encryptionAlgorithm\\": \\"AEAD_AES_256_CBC_HMAC_SHA256\\",\\"encryptionType\\": \\"Deterministic\\"}],\\"policyFormatVersion\\": 2}"
"""

SQL_GREMLIN_CONFLICT_RESOLUTION_POLICY_EXAMPLE = """--conflict-resolution-policy "{\\"mode\\": \\"lastWriterWins\\", \\"conflictResolutionPath\\": \\"/path\\"}"
"""

MONGODB_INDEXES_EXAMPLE = """--idx "[{\\"key\\": {\\"keys\\": [\\"_ts\\"]},\\"options\\": {\\"expireAfterSeconds\\": 1000}}, {\\"key\\": {\\"keys\\": [\\"user_id\\", \\"user_address\\"]}, \\"options\\": {\\"unique\\": \\"true\\"}}]"
"""

CASSANDRA_SCHEMA_EXAMPLE = """--schema "{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"uuid\\"}, {\\"name\\": \\"columnB\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"
"""

SQL_ROLE_DEFINITION_EXAMPLE = """--body "{ \\"Id\\": \\"be79875a-2cc4-40d5-8958-566017875b39\\", \\"RoleName\\": \\"My Read Write Role\\", \\"Type\\": \\"CustomRole\\", \\"AssignableScopes\\": [ \\"/\\" ], \\"DataActions\\": [ \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/create\\", \\"Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read\\" ]}"
"""

MONGO_ROLE_DEFINITION_EXAMPLE = """--body "{\\"Id\\": \\"be79875a-2cc4-40d5-8958-566017875b39\\",\\"RoleName\\": \\"MyRWRole\\",\\"Type\\": \\"CustomRole\\"\\"DatabaseName\\": \\"MyDb\\",\\"Privileges\\": [ {\\"Resource\\": {\\"Db\\": \\"MyDB\\",\\"Collection\\": \\"MyCol\\"},\\"Actions\\": [\\"insert\\",\\"find\\"]}],\\"Roles\\": [ {\\"Role\\": \\"myInheritedRole\\",\\"Db\\": \\"MyTestDb\\"}]}"
"""

MONGO_USER_DEFINITION_EXAMPLE = """--body "{\\"Id\\": \\"be79875a-2cc4-40d5-8958-566017875b39\\",\\"UserName\\": \\"MyUserName\\",\\"Password\\": \\"MyPass\\",\\"CustomData\\": \\"MyCustomData\\",\\"Mechanisms\\": \\"SCRAM-SHA-256\\"\\"DatabaseName\\": \\"MyDb\\",\\"Roles\\": [ {\\"Role\\": \\"myReadRole\\",\\"Db\\": \\"MyDb\\"}]}"
"""

FLEETSPACE_PROPERTIES_EXAMPLE = """--body "{
    \\"properties\\": {
        \\"serviceTier\\": \\"GeneralPurpose\\",
        \\"dataRegions\\": [\\"West US 2\\"],
        \\"throughputPoolConfiguration\\": {
            \\"minThroughput\\": 100000,
            \\"maxThroughput\\": 300000
        }
    }
}"
"""

FLEETSPACE_ACCOUNT_PROPERTIES_EXAMPLE = """--body "{
    \\"properties\\": {
        \\"globalDatabaseAccountProperties\\": {
            \\"resourceId\\": \\"/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg/providers/Microsoft.DocumentDB/databaseAccounts/example-account\\",
            \\"armLocation\\": \\"East US\\"
        }
    }
}"
"""


class ThroughputTypes(str, Enum):
    autoscale = "autoscale"
    manual = "manual"


def load_arguments(self, _):
    from knack.arguments import CLIArgumentType
    from azure.mgmt.cosmosdb.models import KeyKind, DefaultConsistencyLevel, DatabaseAccountKind, TriggerType, TriggerOperation, ServerVersion, NetworkAclBypass, BackupPolicyType, AnalyticalStorageSchemaType, BackupStorageRedundancy

    with self.argument_context('cosmosdb') as c:
        c.argument('account_name', arg_type=name_type, help='Name of the Cosmos DB database account', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part='name')
        c.argument('database_id', options_list=['--db-name', '-d'], help='Database Name')

    with self.argument_context('cosmosdb create') as c:
        c.argument('account_name', completer=None)
        c.argument('enable_free_tier', arg_type=get_three_state_flag(), help="If enabled the account is free-tier.", is_preview=True)
        c.argument('assign_identity', nargs='*', help="Assign system or user assigned identities separated by spaces. Use '[system]' to refer system assigned identity.")
        c.argument('is_restore_request', options_list=['--is-restore-request', '-r'], arg_type=get_three_state_flag(), help="Restore from an existing/deleted account.", arg_group='Restore')
        c.argument('restore_source', help="The restorable-database-account Id of the source account from which the account has to be restored. Required if --is-restore-request is set to true.", arg_group='Restore')
        c.argument('restore_timestamp', action=UtcDatetimeAction, help="The timestamp to which the account has to be restored to. Required if --is-restore-request is set to true.", arg_group='Restore')
        c.argument('databases_to_restore', nargs='+', action=CreateDatabaseRestoreResource, arg_group='Restore')
        c.argument('gremlin_databases_to_restore', nargs='+', action=CreateGremlinDatabaseRestoreResource, arg_group='Restore')
        c.argument('tables_to_restore', nargs='+', action=CreateTableRestoreResource, arg_group='Restore')
        c.argument('enable_partition_merge', arg_type=get_three_state_flag(), help="Flag to enable partition merge on the account.")
        c.argument('enable_burst_capacity', arg_type=get_three_state_flag(), help="Flag to enable burst capacity on the account.")
        c.argument('enable_prpp_autoscale', arg_type=get_three_state_flag(), help="Enable or disable PerRegionPerPartitionAutoscale.")
        c.argument('key_uri', help="The URI of the key vault")

    for scope in ['cosmosdb create', 'cosmosdb update']:
        with self.argument_context(scope) as c:
            c.ignore('resource_group_location')
            c.argument('locations', nargs='+', action=CreateLocation)
            c.argument('tags', arg_type=tags_type)
            c.argument('default_consistency_level', arg_type=get_enum_type(DefaultConsistencyLevel), help="default consistency level of the Cosmos DB database account")
            c.argument('max_staleness_prefix', type=int, help="when used with Bounded Staleness consistency, this value represents the number of stale requests tolerated. Accepted range for this value is 10 - 2,147,483,647")
            c.argument('max_interval', type=int, help="when used with Bounded Staleness consistency, this value represents the time amount of staleness (in seconds) tolerated. Accepted range for this value is 5 - 86400")
            c.argument('ip_range_filter', nargs='+', options_list=['--ip-range-filter'], validator=validate_ip_range_filter, help="firewall support. Specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list of client IPs for a given database account. IP addresses/ranges must be comma-separated and must not contain any spaces")
            c.argument('kind', arg_type=get_enum_type(DatabaseAccountKind), help='The type of Cosmos DB database account to create')
            c.argument('enable_automatic_failover', arg_type=get_three_state_flag(), help='Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage. Automatic failover will result in a new write region for the account and is chosen based on the failover priorities configured for the account.')
            c.argument('capabilities', nargs='*', validator=validate_capabilities, help='set custom capabilities on the Cosmos DB database account.')
            c.argument('enable_virtual_network', arg_type=get_three_state_flag(), help='Enables virtual network on the Cosmos DB database account')
            c.argument('virtual_network_rules', nargs='+', validator=validate_virtual_network_rules, help='ACL\'s for virtual network')
            c.argument('enable_multiple_write_locations', arg_type=get_three_state_flag(), help="Enable Multiple Write Locations")
            c.argument('disable_key_based_metadata_write_access', arg_type=get_three_state_flag(), help="Disable write operations on metadata resources (databases, containers, throughput) via account keys")
            c.argument('disable_local_auth', arg_type=get_three_state_flag(), help="Disable key-based authentication on the Cosmos DB account")
            c.argument('public_network_access', options_list=['--public-network-access', '-p'], arg_type=get_enum_type(['ENABLED', 'DISABLED', 'SECUREDBYPERIMETER']), help="Sets public network access in server to either Enabled, Disabled, or SecuredByPerimeter.")
            c.argument('enable_analytical_storage', arg_type=get_three_state_flag(), help="Flag to enable log storage on the account.")
            c.argument('network_acl_bypass', arg_type=get_enum_type(NetworkAclBypass), options_list=['--network-acl-bypass'], help="Flag to enable or disable Network Acl Bypass.")
            c.argument('network_acl_bypass_resource_ids', nargs='+', options_list=['--network-acl-bypass-resource-ids', '-i'], help="List of Resource Ids to allow Network Acl Bypass.")
            c.argument('backup_interval', type=int, help="the frequency(in minutes) with which backups are taken (only for accounts with periodic mode backups)", arg_group='Backup Policy')
            c.argument('backup_retention', type=int, help="the time(in hours) for which each backup is retained (only for accounts with periodic mode backups)", arg_group='Backup Policy')
            c.argument('backup_redundancy', arg_type=get_enum_type(BackupStorageRedundancy), help="The redundancy type of the backup Storage account", arg_group='Backup Policy')
            c.argument('server_version', arg_type=get_enum_type(ServerVersion), help="Valid only for MongoDB accounts.")
            c.argument('default_identity', help="The primary identity to access key vault in CMK related features. e.g. 'FirstPartyIdentity', 'SystemAssignedIdentity' and more. User-assigned identities are specified in format `UserAssignedIdentity=<resource ID of the user-assigned identity>`.")
            c.argument('analytical_storage_schema_type', options_list=['--analytical-storage-schema-type', '--as-schema'], arg_type=get_enum_type(AnalyticalStorageSchemaType), help="Schema type for analytical storage.", arg_group='Analytical Storage Configuration')
            c.argument('backup_policy_type', arg_type=get_enum_type(BackupPolicyType), help="The type of backup policy of the account to create", arg_group='Backup Policy')
            c.argument('enable_partition_merge', arg_type=get_three_state_flag(), help="Flag to enable partition merge on the account.")
            c.argument('enable_burst_capacity', arg_type=get_three_state_flag(), help="Flag to enable burst capacity on the account.")
            c.argument('enable_prpp_autoscale', arg_type=get_three_state_flag(), help="Enable or disable PerRegionPerPartitionAutoscale.")
            c.argument('enable_pbe', arg_type=get_three_state_flag(), help="Flag to enable priority based execution on the account.")
            c.argument('default_priority_level', arg_type=get_enum_type(DefaultPriorityLevel), help="Default Priority Level of Request if not specified.")
            c.argument('continuous_tier', arg_type=get_enum_type(ContinuousTier), help="The tier of Continuous backup", arg_group='Backup Policy')
            c.argument('minimal_tls_version', arg_type=get_enum_type(MinimalTlsVersion), help="Indicates the minimum allowed TLS version")

    with self.argument_context('cosmosdb update') as c:
        c.argument('key_uri', help="The URI of the key vault", is_preview=True)

    for scope in ['cosmosdb regenerate-key', 'cosmosdb keys regenerate']:
        with self.argument_context(scope) as c:
            c.argument('key_kind', arg_type=get_enum_type(KeyKind), help="The access key to regenerate.")

    with self.argument_context('cosmosdb failover-priority-change') as c:
        c.argument('failover_parameters', options_list=['--failover-policies'], validator=validate_failover_policies,
                   help="space-separated failover policies in 'regionName=failoverPriority' format. Number of policies must match the number of regions the account is currently replicated. All regionName values must match those of the regions the account is currently replicated. All failoverPriority values must be unique. There must be one failoverPriority value zero (0) specified. All remaining failoverPriority values can be any positive integer and they don't have to be contiguos, neither written in any specific order. E.g eastus=0 westus=1", nargs='+')

    with self.argument_context('cosmosdb offline-region') as c:
        c.argument('region', help='The region to offline for the CosmosDB account.')

    with self.argument_context('cosmosdb network-rule list') as c:
        c.argument('account_name', id_part=None)

    with self.argument_context('cosmosdb keys list') as c:
        c.argument('account_name', help="Cosmosdb account name", id_part=None)
        c.argument('key_type', arg_type=get_enum_type(CosmosKeyTypes), options_list=['--type'], help="The type of account key.")

    with self.argument_context('cosmosdb network-rule add') as c:
        c.argument('subnet', help="Name or ID of the subnet")
        c.argument('virtual_network', options_list=['--vnet-name', '--virtual-network'], help="The name of the VNET, which must be provided in conjunction with the name of the subnet")
        c.argument("ignore_missing_vnet_service_endpoint", options_list=['--ignore-missing-endpoint', '--ignore-missing-vnet-service-endpoint'], arg_type=get_three_state_flag(), help="Create firewall rule before the virtual network has vnet service endpoint enabled.")

    with self.argument_context('cosmosdb network-rule remove') as c:
        c.argument('subnet', help="Name or ID of the subnet")
        c.argument('virtual_network', options_list=['--vnet-name', '--virtual-network'], help="The name of the VNET, which must be provided in conjunction with the name of the subnet")

    with self.argument_context('cosmosdb collection') as c:
        c.argument('collection_id', options_list=['--collection-name', '-c'], help='Collection Name')
        c.argument('throughput', type=int, help='Offer Throughput (RU/s)')
        c.argument('partition_key_path', help='Partition Key Path, e.g., \'/properties/name\'')
        c.argument('client_encryption_policy', options_list=['--cep'], type=shell_safe_json_parse, completer=FilesCompleter(), validator=validate_client_encryption_policy, help='Client Encryption Policy, you can enter it as a string or as a file, e.g., --cep @policy-file.json or ' + SQL_CLIENT_ENCRYPTION_POLICY_EXAMPLE)
        c.argument('vector_embedding_policy', options_list=['--vector-embeddings'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Vector Embedding Policy, you can enter it as a string or as a file, e.g., --vector-embeddings @policy-file.json or ' + SQL_VECTOR_EMBEDDING_POLICY_EXAMPLE)
        c.argument('full_text_policy', options_list=['--full-text-policy'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Full Text Policy, you can enter it as a string or as a file, e.g., --full-text-policy @policy-file.json or ' + SQL_FULL_TEXT_SEARCH_POLICY_EXAMPLE)
        c.argument('indexing_policy', type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexing Policy, you can enter it as a string or as a file, e.g., --indexing-policy @policy-file.json)')
        c.argument('default_ttl', type=int, help='Default TTL. Provide 0 to disable.')

    with self.argument_context('cosmosdb database') as c:
        c.argument('throughput', type=int, help='Offer Throughput (RU/s)')

    account_name_type = CLIArgumentType(options_list=['--account-name', '-a'], help="Cosmosdb account name.")
    database_name_type = CLIArgumentType(options_list=['--database-name', '-d'], help='Database name.')
    container_name_type = CLIArgumentType(options_list=['--container-name', '-c'], help='Container name.')
    max_throughput_type = CLIArgumentType(options_list=['--max-throughput'], help='The maximum throughput resource can scale to (RU/s). Provided when the resource is autoscale enabled. The minimum value can be 4000 (RU/s)')
    throughput_type = CLIArgumentType(options_list=['--throughput-type', '-t'], arg_type=get_enum_type(ThroughputTypes), help='The type of throughput to migrate to.')

    with self.argument_context('cosmosdb private-endpoint-connection') as c:
        c.argument('private_endpoint_connection_name', options_list=['--name', '-n'], required=False,
                   help='The name of the private endpoint connection associated with Azure Cosmos DB. '
                        'Required if --connection-id is not specified')
        c.argument('account_name', account_name_type, required=False,
                   help='Name of the Cosmos DB database account. Required if --connection-id is not specified')
        c.argument('resource_group_name', required=False,
                   help='The resource group name of specified Cosmos DB account. Required if --connection-id is not specified')

    for item in ['approve', 'reject', 'delete', 'show']:
        with self.argument_context('cosmosdb private-endpoint-connection {}'.format(item)) as c:
            c.extra('connection_id', options_list=['--id'], required=False,
                    help='The ID of the private endpoint connection associated with Azure Cosmos DB. '
                         'If specified --account-name --resource-group/-g and --name/-n, this should be omitted.')
            c.argument('description', options_list=['--description'], required=False, help='Comments for the {} operation.'.format(item))

    with self.argument_context('cosmosdb private-link-resource') as c:
        c.argument('account_name', account_name_type, required=True, help="Cosmosdb account name", id_part=None)

    with self.argument_context('cosmosdb identity assign') as c:
        c.argument('identities', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '[system]' to refer to the system assigned identity. Default: '[system]'")

    with self.argument_context('cosmosdb identity remove') as c:
        c.argument('identities', options_list=['--identities'], nargs='*', help="Space-separated identities to remove. Use '[system]' to refer to the system assigned identity. Default: '[system]'")

# SQL database
    with self.argument_context('cosmosdb sql database') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', help='The throughput of SQL database (RU/s). Default value is 400')
        c.argument('max_throughput', max_throughput_type)

# SQL container
    with self.argument_context('cosmosdb sql container') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('container_name', options_list=['--name', '-n'], help="Container name")
        c.argument('partition_key_path', options_list=['--partition-key-path', '-p'], help='Partition Key Path, e.g., \'/address/zipcode\'')
        c.argument('partition_key_version', type=int, options_list=['--partition-key-version'], help='The version of partition key.')
        c.argument('default_ttl', options_list=['--ttl'], type=int, help='Default TTL. If the value is missing or set to "-1", items don’t expire. If the value is set to "n", items will expire "n" seconds after last modified time.')
        c.argument('indexing_policy', options_list=['--idx'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexing Policy, you can enter it as a string or as a file, e.g., --idx @policy-file.json or ' + SQL_INDEXING_POLICY_EXAMPLE)
        c.argument('client_encryption_policy', options_list=['--cep'], type=shell_safe_json_parse, completer=FilesCompleter(), validator=validate_client_encryption_policy, help='Client Encryption Policy, you can enter it as a string or as a file, e.g., --cep @policy-file.json or ' + SQL_CLIENT_ENCRYPTION_POLICY_EXAMPLE)
        c.argument('vector_embedding_policy', options_list=['--vector-embeddings'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Vector Embedding Policy, you can enter it as a string or as a file, e.g., --vector-embeddings @policy-file.json or ' + SQL_VECTOR_EMBEDDING_POLICY_EXAMPLE)
        c.argument('full_text_policy', options_list=['--full-text-policy'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Full Text Policy, you can enter it as a string or as a file, e.g., --full-text-policy @policy-file.json or ' + SQL_FULL_TEXT_SEARCH_POLICY_EXAMPLE)
        c.argument('unique_key_policy', options_list=['--unique-key-policy', '-u'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Unique Key Policy, you can enter it as a string or as a file, e.g., --unique-key-policy @policy-file.json or ' + SQL_UNIQUE_KEY_POLICY_EXAMPLE)
        c.argument('conflict_resolution_policy', options_list=['--conflict-resolution-policy', '-c'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Conflict Resolution Policy, you can enter it as a string or as a file, e.g., --conflict-resolution-policy @policy-file.json or ' + SQL_GREMLIN_CONFLICT_RESOLUTION_POLICY_EXAMPLE)
        c.argument('max_throughput', max_throughput_type)
        c.argument('throughput', help='The throughput of SQL container (RU/s). Default value is 400. Omit this parameter if the database has shared throughput unless the container should have dedicated throughput.')
        c.argument('analytical_storage_ttl', options_list=['--analytical-storage-ttl', '-t'], type=int, help='Analytical TTL, when analytical storage is enabled.')

# SQL stored procedure
    with self.argument_context('cosmosdb sql stored-procedure') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('container_name', container_name_type)
        c.argument('stored_procedure_name', options_list=['--name', '-n'], help="StoredProcedure name")
        c.argument('stored_procedure_body', options_list=['--body', '-b'], completer=FilesCompleter(), help="StoredProcedure body, you can enter it as a string or as a file, e.g., --body @sprocbody-file.json")

# SQL trigger
    with self.argument_context('cosmosdb sql trigger') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('container_name', container_name_type)
        c.argument('trigger_name', options_list=['--name', '-n'], help="Trigger name")
        c.argument('trigger_body', options_list=['--body', '-b'], completer=FilesCompleter(), help="Trigger body, you can enter it as a string or as a file, e.g., --body @triggerbody-file.json")
        c.argument('trigger_type', options_list=['--type', '-t'], arg_type=get_enum_type(TriggerType), help="Trigger type")
        c.argument('trigger_operation', options_list=['--operation'], arg_type=get_enum_type(TriggerOperation), help="The operation of the trigger.")

# SQL user defined function
    with self.argument_context('cosmosdb sql user-defined-function') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('container_name', container_name_type)
        c.argument('user_defined_function_name', options_list=['--name', '-n'], help="UserDefinedFunction name")
        c.argument('user_defined_function_body', options_list=['--body', '-b'], completer=FilesCompleter(), help="UserDefinedFunction body, you can enter it as a string or as a file, e.g., --body @udfbody-file.json")

# MongoDB
    with self.argument_context('cosmosdb mongodb database') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', help='The throughput of MongoDB database (RU/s). Default value is 400')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb mongodb collection') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('collection_name', options_list=['--name', '-n'], help="Collection name")
        c.argument('shard_key_path', options_list=['--shard'], help="Sharding key path.")
        c.argument('indexes', options_list=['--idx'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexes, you can enter it as a string or as a file, e.g., --idx @indexes-file.json or ' + MONGODB_INDEXES_EXAMPLE)
        c.argument('max_throughput', max_throughput_type)
        c.argument('analytical_storage_ttl', type=int, help='Analytical TTL, when analytical storage is enabled.')
        c.argument('throughput', help='The throughput of MongoDB collection (RU/s). Default value is 400. Omit this parameter if the database has shared throughput unless the collection should have dedicated throughput.')

# Cassandra
    with self.argument_context('cosmosdb cassandra keyspace') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('keyspace_name', options_list=['--name', '-n'], help="Keyspace name")
        c.argument('throughput', help='The throughput of Cassandra keyspace (RU/s). Default value is 400')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb cassandra table') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('keyspace_name', options_list=['--keyspace-name', '-k'], help="Keyspace name")
        c.argument('table_name', options_list=['--name', '-n'], help="Table name")
        c.argument('default_ttl', options_list=['--ttl'], type=int, help='Default TTL. If the value is missing or set to "-1", items don’t expire. If the value is set to "n", items will expire "n" seconds after last modified time.')
        c.argument('schema', type=shell_safe_json_parse, completer=FilesCompleter(), help='Schema, you can enter it as a string or as a file, e.g., --schema @schema-file.json or ' + CASSANDRA_SCHEMA_EXAMPLE)
        c.argument('max_throughput', max_throughput_type)
        c.argument('analytical_storage_ttl', type=int, help='Analytical TTL, when analytical storage is enabled.')
        c.argument('throughput', help='The throughput of Cassandra table (RU/s). Default value is 400. Omit this parameter if the keyspace has shared throughput unless the table should have dedicated throughput.')

# Gremlin
    with self.argument_context('cosmosdb gremlin database') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', help='The throughput Gremlin database (RU/s). Default value is 400')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb gremlin graph') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('graph_name', options_list=['--name', '-n'], help="Graph name")
        c.argument('partition_key_path', options_list=['--partition-key-path', '-p'], help='Partition Key Path, e.g., \'/address/zipcode\'')
        c.argument('default_ttl', options_list=['--ttl'], type=int, help='Default TTL. If the value is missing or set to "-1", items don’t expire. If the value is set to "n", items will expire "n" seconds after last modified time.')
        c.argument('indexing_policy', options_list=['--idx'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexing Policy, you can enter it as a string or as a file, e.g., --idx @policy-file.json or ' + GREMLIN_INDEXING_POLICY_EXAMPLE)
        c.argument('conflict_resolution_policy', options_list=['--conflict-resolution-policy', '-c'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Conflict Resolution Policy, you can enter it as a string or as a file, e.g., --conflict-resolution-policy @policy-file.json or ' + SQL_GREMLIN_CONFLICT_RESOLUTION_POLICY_EXAMPLE)
        c.argument('max_throughput', max_throughput_type)
        c.argument('throughput', help='The throughput of Gremlin graph (RU/s). Default value is 400. Omit this parameter if the database has shared throughput unless the graph should have dedicated throughput.')
        c.argument('analytical_storage_ttl', type=int, help='Analytical TTL, when analytical storage is enabled.')

# Table
    with self.argument_context('cosmosdb table') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('table_name', options_list=['--name', '-n'], help="Table name")
        c.argument('throughput', help='The throughput of Table (RU/s). Default value is 400')
        c.argument('max_throughput', max_throughput_type)

# Throughput
    with self.argument_context('cosmosdb sql database throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', type=int, help='The throughput of SQL database (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb sql container throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('container_name', options_list=['--name', '-n'], help="Container name")
        c.argument('throughput', type=int, help='The throughput of SQL container (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb mongodb database throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', type=int, help='The throughput of MongoDB database (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb mongodb collection throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('collection_name', options_list=['--name', '-n'], help="Collection name")
        c.argument('throughput', type=int, help='The throughput of MongoDB collection (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb cassandra keyspace throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('keyspace_name', options_list=['--name', '-n'], help="Keyspace name")
        c.argument('throughput', type=int, help='The throughput of Cassandra keyspace (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb cassandra table throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('keyspace_name', options_list=['--keyspace-name', '-k'], help="Keyspace name")
        c.argument('table_name', options_list=['--name', '-n'], help="Table name")
        c.argument('throughput', type=int, help='The throughput of Cassandra table (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb gremlin database throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name")
        c.argument('throughput', type=int, help='The throughput of Gremlin database (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb gremlin graph throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('database_name', database_name_type)
        c.argument('graph_name', options_list=['--name', '-n'], help="Graph name")
        c.argument('throughput', type=int, help='The throughput Gremlin graph (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    with self.argument_context('cosmosdb table throughput') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('table_name', options_list=['--name', '-n'], help="Table name")
        c.argument('throughput', type=int, help='The throughput of Table (RU/s).')
        c.argument('max_throughput', max_throughput_type)

    for scope in ['sql database throughput migrate', 'sql container throughput migrate',
                  'gremlin database throughput migrate', 'gremlin graph throughput migrate',
                  'cassandra table throughput migrate', 'cassandra keyspace throughput migrate',
                  'mongodb collection throughput migrate', 'mongodb database throughput migrate',
                  'table throughput migrate']:
        with self.argument_context('cosmosdb {}'.format(scope)) as c:
            c.argument('throughput_type', throughput_type)

    account_name_type = CLIArgumentType(options_list=['--account-name', '-a'], help="Cosmosdb account name.")

    # SQL role definition
    with self.argument_context('cosmosdb sql role definition') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('role_definition_id', options_list=['--id', '-i'], validator=validate_role_definition_id, help="Unique ID for the Role Definition.")
        c.argument('role_definition_body', options_list=['--body', '-b'], validator=validate_role_definition_body, completer=FilesCompleter(), help="Role Definition body with Id (Optional for create), DataActions or Permissions, Type (Default is CustomRole), and AssignableScopes.  You can enter it as a string or as a file, e.g., --body @rdbody-file.json or " + SQL_ROLE_DEFINITION_EXAMPLE)

    # SQL role assignment
    with self.argument_context('cosmosdb sql role assignment') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('role_assignment_id', options_list=['--role-assignment-id', '-i'], validator=validate_role_assignment_id, help="Optional for Create. Unique ID for the Role Assignment. If not provided, a new GUID will be used.")
        c.argument('role_definition_id', options_list=['--role-definition-id', '-d'], validator=validate_fully_qualified_role_definition_id, help="Unique ID of the Role Definition that this Role Assignment refers to.")
        c.argument('role_definition_name', options_list=['--role-definition-name', '-n'], help="Unique Name of the Role Definition that this Role Assignment refers to. Eg. 'Contoso Reader Role'.")
        c.argument('scope', validator=validate_scope, options_list=['--scope', '-s'], help="Data plane resource path at which this Role Assignment is being granted.")
        c.argument('principal_id', options_list=['--principal-id', '-p'], help="AAD Object ID of the principal to which this Role Assignment is being granted.")

    with self.argument_context('cosmosdb restore') as c:
        c.argument('target_database_account_name', options_list=['--target-database-account-name', '-n'], help='Name of the new target Cosmos DB database account after the restore')
        c.argument('account_name', completer=None, options_list=['--account-name', '-a'], help='Name of the source Cosmos DB database account for the restore', id_part=None)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the account has to be restored to.")
        c.argument('location', arg_type=get_location_type(self.cli_ctx), help="This is the write region of the restored account. This is also the location of the source account where its backups are located if source_backup_location is not provided.")
        c.argument('databases_to_restore', nargs='+', action=CreateDatabaseRestoreResource)
        c.argument('gremlin_databases_to_restore', nargs='+', action=CreateGremlinDatabaseRestoreResource)
        c.argument('tables_to_restore', nargs='+', action=CreateTableRestoreResource)
        c.argument('assign_identity', nargs='*', help="Assign system or user assigned identities separated by spaces. Use '[system]' to refer system assigned identity.")
        c.argument('default_identity', help="The primary identity to access key vault in CMK related features. e.g. 'FirstPartyIdentity', 'SystemAssignedIdentity' and more.")
        c.argument('public_network_access', options_list=['--public-network-access', '-p'], arg_type=get_enum_type(['ENABLED', 'DISABLED']), help="Sets public network access in server to either Enabled or Disabled.")
        c.argument('disable_ttl', options_list=['--disable-ttl', '-d'], arg_type=get_three_state_flag(), help="Enable or disable restoring with ttl disabled.")
        c.argument('source_backup_location', help="This is the location of the source account where backups are located. Provide this value if the source and target are in different locations.")

    # Mongo role definition
    with self.argument_context('cosmosdb mongodb role definition') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('mongo_role_definition_id', options_list=['--id', '-i'], validator=validate_mongo_role_definition_id, help="Unique ID for the Mongo Role Definition.")
        c.argument('mongo_role_definition_body', options_list=['--body', '-b'], validator=validate_mongo_role_definition_body, completer=FilesCompleter(), help="Role Definition body with Id (Optional for create), Type (Default is CustomRole), DatabaseName, Privileges, Roles.  You can enter it as a string or as a file, e.g., --body @mongo-role_definition-body-file.json or " + MONGO_ROLE_DEFINITION_EXAMPLE)

    # Mongo user definition
    with self.argument_context('cosmosdb mongodb user definition') as c:
        c.argument('account_name', account_name_type, id_part=None)
        c.argument('mongo_user_definition_id', options_list=['--id', '-i'], validator=validate_mongo_user_definition_id, help="Unique ID for the Mongo User Definition.")
        c.argument('mongo_user_definition_body', options_list=['--body', '-b'], validator=validate_mongo_user_definition_body, completer=FilesCompleter(), help="User Definition body with Id (Optional for create), UserName, Password, DatabaseName, CustomData, Mechanisms, Roles.  You can enter it as a string or as a file, e.g., --body @mongo-user_definition-body-file.json or " + MONGO_USER_DEFINITION_EXAMPLE)

    # Retrive Sql Container Backup Info
    with self.argument_context('cosmosdb sql retrieve-latest-backup-time') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True, help='Name of the CosmosDB database account')
        c.argument('database_name', database_name_type, required=True, help='Name of the CosmosDB Sql database name')
        c.argument('container_name', container_name_type, required=True, help='Name of the CosmosDB Sql container name')
        c.argument('location', options_list=['--location', '-l'], help="Location of the account", required=True)

    # Retrive MongoDB Collection Backup Info
    with self.argument_context('cosmosdb mongodb retrieve-latest-backup-time') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True, help='Name of the CosmosDB database account')
        c.argument('database_name', database_name_type, required=True, help='Name of the CosmosDB MongoDB database name')
        c.argument('collection_name', options_list=['--collection-name', '-c'], required=True, help='Name of the CosmosDB MongoDB collection name')
        c.argument('location', options_list=['--location', '-l'], help="Location of the account", required=True)

    # Restorable Database Accounts
    with self.argument_context('cosmosdb restorable-database-account show') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=False)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=False)

    with self.argument_context('cosmosdb restorable-database-account list') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=False)
        c.argument('account_name', options_list=['--account-name', '-n'], help="Name of the Account", required=False, id_part=None)

    # Restorable Sql Databases
    with self.argument_context('cosmosdb sql restorable-database') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)

    # Restorable Sql Containers
    with self.argument_context('cosmosdb sql restorable-container') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restorable_sql_database_rid', options_list=['--database-rid', '-d'], help="Rid of the database", required=True)
        c.argument('start_time', options_list=['--start-time', '-s'], help="Start time of restorable Sql container event feed", required=False)
        c.argument('end_time', options_list=['--end-time', '-e'], help="End time of restorable Sql container event feed", required=False)

    # Restorable Sql Resources
    with self.argument_context('cosmosdb sql restorable-resource') as c:
        c.argument('location', options_list=['--location', '-l'], help="Azure Location of the account", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restore_location', options_list=['--restore-location', '-r'], help="The region of the restore.", required=True)
        c.argument('restore_timestamp_in_utc', options_list=['--restore-timestamp', '-t'], help="The timestamp of the restore", required=True)
        c.argument('start_time', options_list=['--start-time', '-s'], help="Start time of restorable MongoDB collections event feed", required=False)
        c.argument('end_time', options_list=['--end-time', '-e'], help="End time of restorable MongoDB collections event feed", required=False)

    # Restorable Mongodb Databases
    with self.argument_context('cosmosdb mongodb restorable-database') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)

    # Restorable Mongodb Collections
    with self.argument_context('cosmosdb mongodb restorable-collection') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restorable_mongodb_database_rid', options_list=['--database-rid', '-d'], help="Rid of the database", required=True)
        c.argument('start_time', options_list=['--start-time', '-s'], help="Start time of restorable MongoDB collections event feed", required=False)
        c.argument('end_time', options_list=['--end-time', '-e'], help="End time of restorable MongoDB collections event feed", required=False)

    # Restorable mongodb Resources
    with self.argument_context('cosmosdb mongodb restorable-resource') as c:
        c.argument('location', options_list=['--location', '-l'], help="Azure Location of the account", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restore_location', options_list=['--restore-location', '-r'], help="The region of the restore.", required=True)
        c.argument('restore_timestamp_in_utc', options_list=['--restore-timestamp', '-t'], help="The timestamp of the restore", required=True)

    # Restorable Gremlin Databases
    with self.argument_context('cosmosdb gremlin restorable-database') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)

    # Restorable Gremlin Graphs
    with self.argument_context('cosmosdb gremlin restorable-graph') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restorable_gremlin_database_rid', options_list=['--database-rid', '-d'], help="Rid of the gremlin database", required=True)
        c.argument('start_time', options_list=['--start-time', '-s'], help="Start time of restorable Gremlin graph event feed", required=False)
        c.argument('end_time', options_list=['--end-time', '-e'], help="End time of restorable Gremlin graph event feed", required=False)

    # Restorable Gremlin Resources
    with self.argument_context('cosmosdb gremlin restorable-resource') as c:
        c.argument('location', options_list=['--location', '-l'], help="Azure Location of the account", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restore_location', options_list=['--restore-location', '-r'], help="The region of the restore.", required=True)
        c.argument('restore_timestamp_in_utc', options_list=['--restore-timestamp', '-t'], help="The timestamp of the restore", required=True)

    # Restorable Tables
    with self.argument_context('cosmosdb table restorable-table') as c:
        c.argument('location', options_list=['--location', '-l'], help="Location", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('start_time', options_list=['--start-time', '-s'], help="Start time of restorable tables event feed", required=False)
        c.argument('end_time', options_list=['--end-time', '-e'], help="End time of restorable tables event feed", required=False)

    # Restorable table Resources
    with self.argument_context('cosmosdb table restorable-resource') as c:
        c.argument('location', options_list=['--location', '-l'], help="Azure Location of the account", required=True)
        c.argument('instance_id', options_list=['--instance-id', '-i'], help="InstanceId of the Account", required=True)
        c.argument('restore_location', options_list=['--restore-location', '-r'], help="The region of the restore.", required=True)
        c.argument('restore_timestamp_in_utc', options_list=['--restore-timestamp', '-t'], help="The timestamp of the restore", required=True)

    # Retrive Gremlin Graph Backup Info
    database_name_type = CLIArgumentType(options_list=['--database-name', '-d'], help='Database name.')
    with self.argument_context('cosmosdb gremlin retrieve-latest-backup-time') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True, help='Name of the CosmosDB database account')
        c.argument('database_name', database_name_type, required=True, help='Name of the CosmosDB Gremlin database name')
        c.argument('graph_name', options_list=['--graph-name', '-n'], required=True, help='Name of the CosmosDB Gremlin graph name')
        c.argument('location', options_list=['--location', '-l'], help="Location of the account", required=True)

    # Retrive Table Backup Info
    with self.argument_context('cosmosdb table retrieve-latest-backup-time') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True, help='Name of the CosmosDB database account')
        c.argument('table_name', options_list=['--table-name', '-n'], required=True, help='Name of the CosmosDB Table name')
        c.argument('location', options_list=['--location', '-l'], help="Location of the account", required=True)

    # Account locations
    with self.argument_context('cosmosdb locations show') as c:
        c.argument('location', options_list=['--location', '-l'], help="Name of the location", required=True)

    # Managed Cassandra Cluster
    for scope in [
            'managed-cassandra cluster create',
            'managed-cassandra cluster update',
            'managed-cassandra cluster show',
            'managed-cassandra cluster delete',
            'managed-cassandra cluster deallocate',
            'managed-cassandra cluster start',
            'managed-cassandra cluster status',
            'managed-cassandra cluster invoke-command']:
        with self.argument_context(scope) as c:
            c.argument('cluster_name', options_list=['--cluster-name', '-c'], help="Cluster Name", required=True)

    # Managed Cassandra Cluster
    for scope in [
            'managed-cassandra cluster create',
            'managed-cassandra cluster update']:
        with self.argument_context(scope) as c:
            c.argument('tags', arg_type=tags_type)
            c.argument('external_gossip_certificates', nargs='*', validator=validate_gossip_certificates, options_list=['--external-gossip-certificates', '-e'], help="A list of certificates that the managed cassandra data center's should accept.")
            c.argument('cassandra_version', help="The version of Cassandra chosen.")
            c.argument('authentication_method', arg_type=get_enum_type(['None', 'Cassandra']), help="Authentication mode can be None or Cassandra. If None, no authentication will be required to connect to the Cassandra API. If Cassandra, then passwords will be used.")
            c.argument('hours_between_backups', help="The number of hours between backup attempts.")
            c.argument('repair_enabled', arg_type=get_three_state_flag(), help="Enables automatic repair.")
            c.argument('client_certificates', nargs='*', validator=validate_client_certificates, help="If specified, enables client certificate authentication to the Cassandra API.")
            c.argument('gossip_certificates', help="A list of certificates that should be accepted by on-premise data centers.")
            c.argument('external_seed_nodes', nargs='*', validator=validate_seednodes, help="A list of ip addresses of the seed nodes of on-premise data centers.")
            c.argument('identity_type', options_list=['--identity-type'], arg_type=get_enum_type(['None', 'SystemAssigned']), help="Type of identity used for Customer Managed Disk Key.")

    # Managed Cassandra Cluster
    with self.argument_context('managed-cassandra cluster create') as c:
        c.argument('location', options_list=['--location', '-l'], help="Azure Location of the Cluster", required=True)
        c.argument('delegated_management_subnet_id', options_list=['--delegated-management-subnet-id', '-s'], help="The resource id of a subnet where the ip address of the cassandra management server will be allocated. This subnet must have connectivity to the delegated_subnet_id subnet of each data center.", required=True)
        c.argument('initial_cassandra_admin_password', options_list=['--initial-cassandra-admin-password', '-i'], help="The intial password to be configured when a cluster is created for authentication_method Cassandra.")
        c.argument('restore_from_backup_id', help="The resource id of a backup. If provided on create, the backup will be used to prepopulate the cluster. The cluster data center count and node counts must match the backup.")
        c.argument('cluster_name_override', help="If a cluster must have a name that is not a valid azure resource name, this field can be specified to choose the Cassandra cluster name. Otherwise, the resource name will be used as the cluster name.")

    # Managed Cassandra Cluster
    for scope in ['managed-cassandra cluster invoke-command']:
        with self.argument_context(scope) as c:
            c.argument('command_name', options_list=['--command-name'], help="The command which should be run", required=True)
            c.argument('host', options_list=['--host'], help="IP address of the cassandra host to run the command on", required=True)
            c.argument('arguments', options_list=['--arguments'], action=InvokeCommandArgumentsAddAction, nargs='+', help="The key=\"value\" of arguments for the command.")
            c.argument('cassandra_stop_start', options_list=['--cassandra-stop-start'], arg_type=get_three_state_flag(), help="If true, stops cassandra before executing the command and then start it again.")
            c.argument('readwrite', options_list=['--readwrite'], arg_type=get_three_state_flag(), help="If true, allows the command to *write* to the cassandra directory, otherwise read-only.")

    # Managed Cassandra Datacenter
    for scope in [
            'managed-cassandra datacenter create',
            'managed-cassandra datacenter update',
            'managed-cassandra datacenter show',
            'managed-cassandra datacenter delete']:
        with self.argument_context(scope) as c:
            c.argument('cluster_name', options_list=['--cluster-name', '-c'], help="Cluster Name", required=True)
            c.argument('data_center_name', options_list=['--data-center-name', '-d'], help="Datacenter Name", required=True)

    # Managed Cassandra Datacenter
    for scope in [
            'managed-cassandra datacenter create',
            'managed-cassandra datacenter update']:
        with self.argument_context(scope) as c:
            c.argument('node_count', options_list=['--node-count', '-n'], validator=validate_node_count, help="The number of Cassandra virtual machines in this data center. The minimum value is 3.")
            c.argument('sku', options_list=['--sku'], help="Virtual Machine SKU used for data centers. Default value is Standard_DS14_v2")
            c.argument('base64_encoded_cassandra_yaml_fragment', options_list=['--base64-encoded-cassandra-yaml-fragment', '-b'], help="This is a Base64 encoded yaml file that is a subset of cassandra.yaml.  Supported fields will be honored and others will be ignored.")
            c.argument('data_center_location', options_list=['--data-center-location', '-l'], help="The region where the virtual machine for this data center will be located.")
            c.argument('delegated_subnet_id', options_list=['--delegated-subnet-id', '-s'], help="The resource id of a subnet where ip addresses of the Cassandra virtual machines will be allocated. This must be in the same region as data_center_location.")
            c.argument('managed_disk_customer_key_uri', options_list=['--managed-disk-customer-key-uri', '-k'], help="Key uri to use for encryption of managed disks. Ensure the system assigned identity of the cluster has been assigned appropriate permissions(key get/wrap/unwrap permissions) on the key.")
            c.argument('backup_storage_customer_key_uri', options_list=['--backup-storage-customer-key-uri', '-p'], help="Indicates the Key Uri of the customer key to use for encryption of the backup storage account.")

    # Managed Cassandra Datacenter
    with self.argument_context('managed-cassandra datacenter create') as c:
        c.argument('data_center_location', options_list=['--data-center-location', '-l'], help="Azure Location of the Datacenter", required=True)
        c.argument('delegated_subnet_id', options_list=['--delegated-subnet-id', '-s'], help="The resource id of a subnet where ip addresses of the Cassandra virtual machines will be allocated. This must be in the same region as data_center_location.", required=True)
        c.argument('node_count', options_list=['--node-count', '-n'], validator=validate_node_count, help="The number of Cassandra virtual machines in this data center. The minimum value is 3.", required=True)
        c.argument('disk_sku', options_list=['--disk-sku'], help="Disk SKU used for data centers. Default value is P30.")
        c.argument('disk_capacity', options_list=['--disk-capacity'], help="Number of disk used for data centers. Default value is 4.")
        c.argument('availability_zone', options_list=['--availability-zone', '-z'], arg_type=get_three_state_flag(), help="If the data center haves Availability Zone feature, apply it to the Virtual Machine ScaleSet that host the data center virtual machines.")

    # Managed Cassandra Datacenter
    with self.argument_context('managed-cassandra datacenter list') as c:
        c.argument('cluster_name', options_list=['--cluster-name', '-c'], help="Cluster Name", required=True)

    # SQL database restore
    with self.argument_context('cosmosdb sql database restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the database needs to be restored to.", required=False)

    # SQL collection restore
    with self.argument_context('cosmosdb sql container restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', database_name_type, required=True)
        c.argument('container_name', options_list=['--name', '-n'], help="Container name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the container needs to be restored to.", required=False)

    # MongoDB database restore
    with self.argument_context('cosmosdb mongodb database restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', options_list=['--name', '-n'], help="Database name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the database needs to be restored to.", required=False)

    # MongoDB collection restore
    with self.argument_context('cosmosdb mongodb collection restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', database_name_type, required=True)
        c.argument('collection_name', options_list=['--name', '-n'], help="Collection name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the collection needs to be restored to.", required=False)

    # Gremlin database restore
    with self.argument_context('cosmosdb gremlin database restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', options_list=['--name', '-n'], help="Name of the CosmosDB Gremlin database name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the database needs to be restored to.", required=False)

    # Gremlin Graph restore
    with self.argument_context('cosmosdb gremlin graph restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('database_name', database_name_type, required=True, help='Name of the CosmosDB Gremlin database name')
        c.argument('graph_name', options_list=['--name', '-n'], help="Name of the CosmosDB Gremlin graph name", required=True)
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the graph needs to be restored to.", required=False)

    # Table restore
    with self.argument_context('cosmosdb table restore') as c:
        c.argument('account_name', account_name_type, id_part=None, required=True)
        c.argument('table_name', options_list=['--table-name', '-n'], required=True, help='Name of the CosmosDB Table name')
        c.argument('restore_timestamp', options_list=['--restore-timestamp', '-t'], action=UtcDatetimeAction, help="The timestamp to which the Table needs to be restored to.", required=False)

    # ComputeV2 Services
    with self.argument_context('cosmosdb service') as c:
        c.argument('account_name', completer=None, options_list=['--account-name', '-a'], help='Name of the Cosmos DB database account.', id_part=None)
        c.argument('resource_group_name', completer=None, options_list=['--resource-group-name', '-g'], help='Name of the resource group of the database account.', id_part=None)
        c.argument('service_kind', options_list=['--kind', '-k'], help="Service kind")
        c.argument('service_name', options_list=['--name', '-n'], help="Service Name.")
        c.argument('instance_count', options_list=['--count', '-c'], help="Instance Count.")
        c.argument('instance_size', options_list=['--size'], help="Instance Size. Possible values are: Cosmos.D4s, Cosmos.D8s, Cosmos.D16s etc")
        c.argument('dedicated_gateway_type', options_list=['--gateway-type'], arg_type=get_enum_type(['IntegratedCache', 'DistributedQuery']), help="Dedicated Gateway Type. Valid only for SqlDedicatedGateway service kind")

    # Cosmos DB Fleet
    with self.argument_context('cosmosdb fleet') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Name of the resource group.', required=True)
        c.argument('fleet_name', options_list=['--fleet-name', '-n'], help='Name of the Fleet resource.', required=True)

    with self.argument_context('cosmosdb fleet create') as c:
        c.argument('location', options_list=['--location', '-l'], help='Location of the Fleet.', required=True)
        c.argument('tags', help="Tags in 'key=value key2=value2' format.")

    # Cosmos DB Fleetspace
    with self.argument_context('cosmosdb fleetspace') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Name of the resource group.', required=True)
        c.argument('fleet_name', options_list=['--fleet-name'], help='Name of the Cosmos DB Fleet.', required=True)
        c.argument('fleetspace_name', options_list=['--fleetspace-name', '-n'], help='Name of the Fleetspace resource.', required=True)

    with self.argument_context('cosmosdb fleetspace create') as c:
        c.argument('fleetspace_body', options_list=['--body', '-b'], validator=validate_fleetspace_body, completer=FilesCompleter(), help="Fleetspace body with properties.serviceTier (required), properties.dataRegions (required), and properties.throughputPoolConfiguration (fields: minThroughput, maxThroughput). You can enter it as a string or as a file, e.g., --body @fleetspace.json or " + FLEETSPACE_PROPERTIES_EXAMPLE)

    with self.argument_context('cosmosdb fleetspace update') as c:
        c.argument('fleetspace_body', options_list=['--body', '-b'], validator=validate_fleetspace_body, completer=FilesCompleter(), help="Fleetspace body with properties.serviceTier (optional), properties.dataRegions (optional), and properties.throughputPoolConfiguration (fields: minThroughput, maxThroughput). You can enter it as a string or as a file, e.g., --body @fleetspace.json or " + FLEETSPACE_PROPERTIES_EXAMPLE)

    # Cosmos DB Fleetspace account
    with self.argument_context('cosmosdb fleetspace account') as c:
        c.argument('resource_group', options_list=['--resource-group', '-g'], help='Name of the resource group.', required=True)
        c.argument('fleet_name', options_list=['--fleet-name'], help='Name of the Cosmos DB Fleet.', required=True)
        c.argument('fleetspace_name', options_list=['--fleetspace-name'], help='Name of the Fleetspace resource.', required=True)
        c.argument('fleetspace_account_name', options_list=['--fleetspace-account-name', '-n'], help='Name of the Fleetspace Account resource.', required=True)

    with self.argument_context('cosmosdb fleetspace account create') as c:
        c.argument('fleetspace_account_body', options_list=['--body', '-b'], validator=validate_fleetspaceAccount_body, completer=FilesCompleter(), help="Fleetspace Account body with properties.globalDatabaseAccountProperties (fields: armLocation, resourceId). You can enter it as a string or as a file, e.g., --body @fleetspaceAccount.json or " + FLEETSPACE_ACCOUNT_PROPERTIES_EXAMPLE)
