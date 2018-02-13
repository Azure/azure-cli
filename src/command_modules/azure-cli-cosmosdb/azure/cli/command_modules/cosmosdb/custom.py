# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.cosmosdb.models import (
    ConsistencyPolicy,
    DatabaseAccountCreateUpdateParameters,
    Location
)
from azure.mgmt.cosmosdb.models.cosmos_db_enums import DatabaseAccountKind


logger = get_logger(__name__)


DEFAULT_INDEXING_POLICY = """{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*",
      "indexes": [
        {
          "kind": "Range",
          "dataType": "String",
          "precision": -1
        },
        {
          "kind": "Range",
          "dataType": "Number",
          "precision": -1
        }
      ]
    }
  ]
}"""


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
                        capabilities=None):
    """Create a new Azure Cosmos DB database account."""
    consistency_policy = None
    if default_consistency_level is not None:
        consistency_policy = ConsistencyPolicy(default_consistency_level, max_staleness_prefix,
                                               max_interval)

    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    resource_client = get_mgmt_service_client(cmd.cli_ctx, ResourceManagementClient)
    rg = resource_client.resource_groups.get(resource_group_name)
    resource_group_location = rg.location  # pylint: disable=no-member

    if not locations:
        locations.append(Location(location_name=resource_group_location, failover_priority=0))

    params = DatabaseAccountCreateUpdateParameters(
        resource_group_location,
        locations,
        tags=tags,
        kind=kind,
        consistency_policy=consistency_policy,
        ip_range_filter=ip_range_filter,
        enable_automatic_failover=enable_automatic_failover,
        capabilities=capabilities)

    async_docdb_create = client.create_or_update(resource_group_name, account_name, params)
    docdb_account = async_docdb_create.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


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
                        capabilities=None):
    """Update an existing Azure Cosmos DB database account. """
    existing = client.get(resource_group_name, account_name)

    # Workaround until PATCH support for all properties
    # pylint: disable=too-many-boolean-expressions
    if capabilities is not None:
        if locations or \
           default_consistency_level is not None or \
           max_staleness_prefix is not None or \
           max_interval is not None or \
           ip_range_filter is not None or \
           enable_automatic_failover is not None:
            raise CLIError("Cannot set capabilities and update properties at the same time. {0}".format(locations))

        else:
            async_docdb_create = client.patch(resource_group_name, account_name, tags=tags, capabilities=capabilities)
            docdb_account = async_docdb_create.result()
            docdb_account = client.get(resource_group_name, account_name)
            return docdb_account

    # Workaround until PATCH support for all properties
    # pylint: disable=too-many-boolean-expressions
    if tags is not None:
        if not locations and\
           default_consistency_level is None and\
           max_staleness_prefix is None and\
           max_interval is None and\
           ip_range_filter is None and\
           enable_automatic_failover is None:

            async_docdb_create = client.patch(resource_group_name, account_name, tags=tags, capabilities=capabilities)
            docdb_account = async_docdb_create.result()
            docdb_account = client.get(resource_group_name, account_name)
            return docdb_account

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
        consistency_policy = ConsistencyPolicy(default_consistency_level, max_staleness_prefix,
                                               max_interval)
    else:
        consistency_policy = existing.consistency_policy

    if not locations:
        for loc in existing.read_locations:
            locations.append(
                Location(location_name=loc.location_name, failover_priority=loc.failover_priority))

    if ip_range_filter is None:
        ip_range_filter = existing.ip_range_filter

    if enable_automatic_failover is None:
        enable_automatic_failover = existing.enable_automatic_failover

    if tags is None:
        tags = existing.tags

    params = DatabaseAccountCreateUpdateParameters(
        existing.location,
        locations,
        tags=tags,
        kind=existing.kind,
        consistency_policy=consistency_policy,
        ip_range_filter=ip_range_filter,
        enable_automatic_failover=enable_automatic_failover,
        capabilities=existing.capabilities)

    async_docdb_create = client.create_or_update(resource_group_name, account_name, params)
    docdb_account = async_docdb_create.result()
    docdb_account = client.get(resource_group_name, account_name)  # Workaround
    return docdb_account


def cli_cosmosdb_list(client, resource_group_name=None):
    """ Lists all Azure Cosmos DB database accounts within a given resource group or subscription. """
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


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


def cli_cosmosdb_database_create(client, database_id):
    """Creates an Azure Cosmos DB database """
    return client.CreateDatabase({'id': database_id})


def cli_cosmosdb_database_delete(client, database_id):
    """Deletes an Azure Cosmos DB database """
    client.DeleteDatabase(_get_database_link(database_id))


# collection operations

def cli_cosmosdb_collection_exists(client, database_id, collection_id):
    """Returns a boolean indicating whether the collection exists """
    return len(list(client.QueryCollections(
        _get_database_link(database_id),
        {'query': 'SELECT * FROM root r WHERE r.id=@id',
         'parameters': [{'name': '@id', 'value': collection_id}]}))) > 0


def cli_cosmosdb_collection_show(client, database_id, collection_id):
    """Shows an Azure Cosmos DB collection and its offer """
    collection = client.ReadCollection(_get_collection_link(database_id, collection_id))
    offer = _find_offer(client, collection['_self'])
    return {'collection': collection, 'offer': offer}


def cli_cosmosdb_collection_list(client, database_id):
    """Lists all Azure Cosmos DB collections """
    return list(client.ReadCollections(_get_database_link(database_id)))


def cli_cosmosdb_collection_delete(client, database_id, collection_id):
    """Deletes an Azure Cosmos DB collection """
    client.DeleteCollection(_get_collection_link(database_id, collection_id))


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

    created_collection = client.CreateCollection(_get_database_link(database_id), collection,
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
    collection = client.ReadCollection(_get_collection_link(database_id, collection_id))
    result = {}

    if (_populate_collection_definition(collection,
                                        None,
                                        default_ttl,
                                        indexing_policy)):
        logger.debug('replacing collection')
        result['collection'] = client.ReplaceCollection(
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
