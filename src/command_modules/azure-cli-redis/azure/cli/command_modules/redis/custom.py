#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.redis.models import (
    ImportRDBParameters,
    ExportRDBParameters,
    RedisCreateOrUpdateParameters,
    Sku,
)

def cli_redis_export(client, resource_group_name, name, prefix, container, file_format=None):
    # pylint:disable=too-many-arguments
    parameters = ExportRDBParameters(prefix, container, file_format)
    return client.export(resource_group_name, name, parameters)

def cli_redis_import_method(client, resource_group_name, name, file_format, files):
    parameters = ImportRDBParameters(files, file_format)
    return client.import_method(resource_group_name, name, files, parameters)

def cli_redis_update_settings(client, resource_group_name, name, redis_configuration):
    existing = client.get(resource_group_name, name)
    existing.redis_configuration.update(redis_configuration)

    # Due to swagger/mgmt SDK quirkiness, we have to manually copy over
    # the resource retrieved to a create_or_update_parameters object
    update_params = RedisCreateOrUpdateParameters(
        existing.location,
        existing.sku,
        existing.tags,
        existing.redis_version,
        existing.redis_configuration,
        existing.enable_non_ssl_port,
        existing.tenant_settings,
        existing.shard_count,
        existing.subnet_id,
        existing.static_ip,
        )
    return client.create_or_update(resource_group_name, name, parameters=update_params)

def cli_redis_create(client, resource_group_name, name, location, sku_name, # pylint:disable=too-many-arguments
                     sku_family, sku_capacity, tags=None, redis_configuration=None,
                     enable_non_ssl_port=None, tenant_settings=None, shard_count=None,
                     subnet_id=None, static_ip=None):
    # pylint:disable=line-too-long
    """Create new Redis Cache instance
    :param resource_group_name: Name of resource group
    :param name: Name of redis cache
    :param location: Location
    :param sku_name: What type of redis cache to deploy. Valid values: (Basic, Standard, Premium).
    :param sku_family: Which family to use. Valid values: (C, P).
    :param sku_capacity: What size of redis cache to deploy. Valid values for C family (0, 1, 2, 3, 4, 5, 6), for P family (1, 2, 3, 4)
    :param redis_configuration: All Redis Settings. Few possible keys rdb-backup-enabled, rdb-storage-connection-string, rdb-backup-frequency, maxmemory-delta, maxmemory-policy, notify-keyspace-events, maxmemory-samples, slowlog-log-slower-than, slowlog-max-len, list-max-ziplist-entries, list-max-ziplist-value, hash-max-ziplist-entries, hash-max-ziplist-value, set-max-intset-entries, zset-max-ziplist-entries, zset-max-ziplist-value etc.
    :param enable_non_ssl_port: If the value is true, then the non-ssl redis server port (6379) will be enabled.
    :param tenant_settings: Json dictionary with tenant settings
    :param shard_count: The number of shards to be created on a Premium Cluster Cache.
    :param subnet_id: The full resource ID of a subnet in a virtual network to deploy the redis cache in. Example format /subscriptions/{subid}/resourceGroups/{resourceGroupName}/Microsoft.{Network|ClassicNetwork}/VirtualNetworks/vnet1/subnets/subnet1
    :param static_ip: Required when deploying a redis cache inside an existing Azure Virtual Network.
    """
    params = RedisCreateOrUpdateParameters(
        location,
        Sku(sku_name, sku_family, sku_capacity),
        tags,
        None, # Version is deprecated and ignored
        redis_configuration,
        enable_non_ssl_port,
        tenant_settings,
        shard_count,
        subnet_id,
        static_ip)

    return client.create_or_update(resource_group_name, name, params)

