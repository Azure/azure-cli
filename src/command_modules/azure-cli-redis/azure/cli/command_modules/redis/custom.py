# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.command_modules.redis._client_factory import cf_redis

logger = get_logger(__name__)


def wrong_vmsize_argument_exception_handler(ex):

    from msrest.exceptions import ClientException
    if isinstance(ex, ClientException):
        if ("The value of the parameter 'properties.sku.family/properties.sku.capacity' is invalid"
                in format(ex)) \
                or ("The value of the parameter 'properties.sku.family' is invalid"
                    in format(ex)):
            raise CLIError('Invalid VM size. Example for Valid values: '
                           'For C family (C0, C1, C2, C3, C4, C5, C6), '
                           'for P family (P1, P2, P3, P4)')
    raise ex


# region Custom Commands

# pylint: disable=unused-argument
def cli_redis_export(cmd, client, resource_group_name, name, prefix, container, file_format=None):
    from azure.mgmt.redis.models import ExportRDBParameters
    parameters = ExportRDBParameters(prefix, container, file_format)
    return client.export_data(resource_group_name, name, parameters)


# pylint: disable=unused-argument
def cli_redis_import_method(cmd, client, resource_group_name, name, files, file_format=None):
    logger.warning('This command is getting deprecated. Please use "redis import" command')
    return client.import_data(resource_group_name, name, files, file_format)


# pylint: disable=unused-argument
def cli_redis_update(cmd, instance, sku=None, vm_size=None):
    from azure.mgmt.redis.models import RedisUpdateParameters
    if sku is not None:
        instance.sku.name = sku

    if vm_size is not None:
        instance.sku.family = vm_size[0]
        instance.sku.capacity = vm_size[1:]

    # pylint: disable=too-many-function-args
    update_params = RedisUpdateParameters(
        instance.redis_configuration,
        instance.enable_non_ssl_port,
        instance.tenant_settings,
        instance.shard_count,
        instance.sku,
        instance.tags
    )
    return update_params


# pylint: disable=unused-argument
def cli_redis_create(cmd, client,
                     resource_group_name, name, location, sku, vm_size, tags=None,
                     redis_configuration=None, enable_non_ssl_port=None, tenant_settings=None,
                     shard_count=None, subnet_id=None, static_ip=None, zones=None):
    # pylint:disable=line-too-long
    """Create new Redis Cache instance
    :param resource_group_name: Name of resource group
    :param name: Name of redis cache
    :param location: Location
    :param sku: What type of redis cache to deploy. Valid values: (Basic, Standard, Premium).
    :param vm_size: What size of redis cache to deploy. Valid values for C family (C0, C1, C2, C3, C4, C5, C6), for P family (P1, P2, P3, P4)
    :param redis_configuration: All Redis Settings. Few possible keys rdb-backup-enabled, rdb-storage-connection-string, rdb-backup-frequency, maxmemory-delta, maxmemory-policy, notify-keyspace-events, maxmemory-samples, slowlog-log-slower-than, slowlog-max-len, list-max-ziplist-entries, list-max-ziplist-value, hash-max-ziplist-entries, hash-max-ziplist-value, set-max-intset-entries, zset-max-ziplist-entries, zset-max-ziplist-value etc.
    :param enable_non_ssl_port: If the value is true, then the non-ssl redis server port (6379) will be enabled.
    :param tenant_settings: Json dictionary with tenant settings
    :param shard_count: The number of shards to be created on a Premium Cluster Cache.
    :param subnet_id: The full resource ID of a subnet in a virtual network to deploy the redis cache in. Example format /subscriptions/{subid}/resourceGroups/{resourceGroupName}/Microsoft.{Network|ClassicNetwork}/VirtualNetworks/vnet1/subnets/subnet1
    :param static_ip: Required when deploying a redis cache inside an existing Azure Virtual Network.
    :param zones: A list of availability zones denoting where the resource.
    """
    from azure.mgmt.redis.models import RedisCreateParameters, Sku
    params = RedisCreateParameters(
        Sku(sku, vm_size[0], vm_size[1:]),
        location,
        redis_configuration,
        enable_non_ssl_port,
        tenant_settings,
        shard_count,
        subnet_id,
        static_ip,
        zones,
        tags)
    return client.create(resource_group_name, name, params)


# pylint: disable=unused-argument
def cli_redis_create_server_link(cmd, client, resource_group_name, name, secondary_cache_name,
                                 secondary_cache_resource_group):

    redis_client = cf_redis(cmd.cli_ctx)
    secondary_cache = redis_client.get(secondary_cache_resource_group, secondary_cache_name)

    from azure.mgmt.redis.models import RedisLinkedServerCreateParameters
    params = RedisLinkedServerCreateParameters(secondary_cache.id, secondary_cache.location, 'Secondary')
    return client.create(resource_group_name, name, secondary_cache_name, params)

# endregion
