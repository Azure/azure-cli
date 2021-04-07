# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-many-statements
# pylint: disable=line-too-long
from enum import Enum
from argcomplete.completers import FilesCompleter

from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list, name_type, get_enum_type, get_three_state_flag, tags_type)
from azure.cli.core.util import shell_safe_json_parse

from azure.cli.command_modules.cosmosdb._validators import (
    validate_failover_policies, validate_capabilities,
    validate_virtual_network_rules, validate_ip_range_filter)

from azure.cli.command_modules.cosmosdb.actions import (
    CreateLocation)
from azure.cli.command_modules.cosmosdb.custom import (
    CosmosKeyTypes)


SQL_GREMLIN_INDEXING_POLICY_EXAMPLE = """--idx "{\\"indexingMode\\": \\"consistent\\", \\"automatic\\": true, \\"includedPaths\\": [{\\"path\\": \\"/*\\"}], \\"excludedPaths\\": [{ \\"path\\": \\"/headquarters/employees/?\\"}, { \\"path\\": \\"/\\\\"_etag\\\\"/?\\"}]}"
"""

SQL_UNIQUE_KEY_POLICY_EXAMPLE = """--unique-key-policy "{\\"uniqueKeys\\": [{\\"paths\\": [\\"/path/to/key1\\"]}, {\\"paths\\": [\\"/path/to/key2\\"]}]}"
"""

SQL_GREMLIN_CONFLICT_RESOLUTION_POLICY_EXAMPLE = """--conflict-resolution-policy "{\\"mode\\": \\"lastWriterWins\\", \\"conflictResolutionPath\\": \\"/path\\"}"
"""

MONGODB_INDEXES_EXAMPLE = """--idx "[{\\"key\\": {\\"keys\\": [\\"_ts\\"]},\\"options\\": {\\"expireAfterSeconds\\": 1000}}, {\\"key\\": {\\"keys\\": [\\"user_id\\", \\"user_address\\"]}, \\"options\\": {\\"unique\\": \\"true\\"}}]"
"""

CASSANDRA_SCHEMA_EXAMPLE = """--schema "{\\"columns\\": [{\\"name\\": \\"columnA\\",\\"type\\": \\"uuid\\"}, {\\"name\\": \\"columnB\\",\\"type\\": \\"Ascii\\"}],\\"partitionKeys\\": [{\\"name\\": \\"columnA\\"}]}"
"""


class ThroughputTypes(str, Enum):
    autoscale = "autoscale"
    manual = "manual"


def load_arguments(self, _):
    from knack.arguments import CLIArgumentType
    from azure.mgmt.cosmosdb.models import KeyKind, DefaultConsistencyLevel, DatabaseAccountKind, TriggerType, TriggerOperation, ServerVersion, NetworkAclBypass

    with self.argument_context('cosmosdb') as c:
        c.argument('account_name', arg_type=name_type, help='Name of the Cosmos DB database account', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part='name')
        c.argument('database_id', options_list=['--db-name', '-d'], help='Database Name')

    with self.argument_context('cosmosdb create') as c:
        c.argument('account_name', completer=None)
        c.argument('key_uri', help="The URI of the key vault", is_preview=True)
        c.argument('enable_free_tier', arg_type=get_three_state_flag(), help="If enabled the account is free-tier.", is_preview=True)
        c.argument('assign_identity', nargs='*', help="accept system or user assigned identities separated by spaces. Use '[system]' to refer system assigned identity. Currently only system assigned identity is supported.", is_preview=True)

    for scope in ['cosmosdb create', 'cosmosdb update']:
        with self.argument_context(scope) as c:
            c.ignore('resource_group_location')
            c.argument('locations', nargs='+', action=CreateLocation)
            c.argument('tags', arg_type=tags_type)
            c.argument('default_consistency_level', arg_type=get_enum_type(DefaultConsistencyLevel), help="default consistency level of the Cosmos DB database account")
            c.argument('max_staleness_prefix', type=int, help="when used with Bounded Staleness consistency, this value represents the number of stale requests tolerated. Accepted range for this value is 1 - 2,147,483,647")
            c.argument('max_interval', type=int, help="when used with Bounded Staleness consistency, this value represents the time amount of staleness (in seconds) tolerated. Accepted range for this value is 1 - 100")
            c.argument('ip_range_filter', nargs='+', options_list=['--ip-range-filter'], validator=validate_ip_range_filter, help="firewall support. Specifies the set of IP addresses or IP address ranges in CIDR form to be included as the allowed list of client IPs for a given database account. IP addresses/ranges must be comma-separated and must not contain any spaces")
            c.argument('kind', arg_type=get_enum_type(DatabaseAccountKind), help='The type of Cosmos DB database account to create')
            c.argument('enable_automatic_failover', arg_type=get_three_state_flag(), help='Enables automatic failover of the write region in the rare event that the region is unavailable due to an outage. Automatic failover will result in a new write region for the account and is chosen based on the failover priorities configured for the account.')
            c.argument('capabilities', nargs='+', validator=validate_capabilities, help='set custom capabilities on the Cosmos DB database account.')
            c.argument('enable_virtual_network', arg_type=get_three_state_flag(), help='Enables virtual network on the Cosmos DB database account')
            c.argument('virtual_network_rules', nargs='+', validator=validate_virtual_network_rules, help='ACL\'s for virtual network')
            c.argument('enable_multiple_write_locations', arg_type=get_three_state_flag(), help="Enable Multiple Write Locations")
            c.argument('disable_key_based_metadata_write_access', arg_type=get_three_state_flag(), help="Disable write operations on metadata resources (databases, containers, throughput) via account keys")
            c.argument('enable_public_network', options_list=['--enable-public-network', '-e'], arg_type=get_three_state_flag(), help="Enable or disable public network access to server.")
            c.argument('enable_analytical_storage', arg_type=get_three_state_flag(), help="Flag to enable log storage on the account.", is_preview=True)
            c.argument('network_acl_bypass', arg_type=get_enum_type(NetworkAclBypass), options_list=['--network-acl-bypass'], help="Flag to enable or disable Network Acl Bypass.")
            c.argument('network_acl_bypass_resource_ids', nargs='+', options_list=['--network-acl-bypass-resource-ids', '-i'], help="List of Resource Ids to allow Network Acl Bypass.")
            c.argument('backup_interval', type=int, help="the frequency(in minutes) with which backups are taken (only for accounts with periodic mode backups)", arg_group='Backup Policy')
            c.argument('backup_retention', type=int, help="the time(in hours) for which each backup is retained (only for accounts with periodic mode backups)", arg_group='Backup Policy')
            c.argument('server_version', arg_type=get_enum_type(ServerVersion), help="Valid only for MongoDB accounts.", is_preview=True)
            c.argument('default_identity', help="The primary identity to access key vault in CMK related features. e.g. 'FirstPartyIdentity', 'SystemAssignedIdentity' and more.", is_preview=True)

    for scope in ['cosmosdb regenerate-key', 'cosmosdb keys regenerate']:
        with self.argument_context(scope) as c:
            c.argument('key_kind', arg_type=get_enum_type(KeyKind))

    with self.argument_context('cosmosdb failover-priority-change') as c:
        c.argument('failover_policies', validator=validate_failover_policies, help="space-separated failover policies in 'regionName=failoverPriority' format. E.g eastus=0 westus=1", nargs='+')

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
        c.argument('indexing_policy', options_list=['--idx'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexing Policy, you can enter it as a string or as a file, e.g., --idx @policy-file.json or ' + SQL_GREMLIN_INDEXING_POLICY_EXAMPLE)
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
        c.argument('indexing_policy', options_list=['--idx'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Indexing Policy, you can enter it as a string or as a file, e.g., --idx @policy-file.json or ' + SQL_GREMLIN_INDEXING_POLICY_EXAMPLE)
        c.argument('conflict_resolution_policy', options_list=['--conflict-resolution-policy', '-c'], type=shell_safe_json_parse, completer=FilesCompleter(), help='Conflict Resolution Policy, you can enter it as a string or as a file, e.g., --conflict-resolution-policy @policy-file.json or ' + SQL_GREMLIN_CONFLICT_RESOLUTION_POLICY_EXAMPLE)
        c.argument('max_throughput', max_throughput_type)
        c.argument('throughput', help='The throughput of Gremlin graph (RU/s). Default value is 400. Omit this parameter if the database has shared throughput unless the graph should have dedicated throughput.')

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
