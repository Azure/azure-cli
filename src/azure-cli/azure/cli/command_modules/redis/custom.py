# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from knack.util import CLIError
from azure.cli.command_modules.redis._client_factory import cf_redis

logger = get_logger(__name__)

allowed_c_family_sizes = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6']
allowed_p_family_sizes = ['p1', 'p2', 'p3', 'p4', 'p5']
wrong_vmsize_error = CLIError('Invalid VM size. Example for Valid values: '
                              'For Standard Sku : (C0, C1, C2, C3, C4, C5, C6), '
                              'for Premium Sku : (P1, P2, P3, P4, P5)')

# region Custom Commands


# pylint: disable=unused-argument
def cli_redis_export(cmd, client, resource_group_name, name, prefix, container, file_format=None):
    from azure.mgmt.redis.models import ExportRDBParameters
    parameters = ExportRDBParameters(prefix=prefix, container=container, format=file_format)
    return client.export_data(resource_group_name, name, parameters)


# pylint: disable=unused-argument
def cli_redis_update(cmd, instance, sku=None, vm_size=None):
    from azure.mgmt.redis.models import RedisUpdateParameters
    if sku is not None:
        instance.sku.name = sku

    if vm_size is not None:
        instance.sku.family = vm_size[0]
        instance.sku.capacity = vm_size[1:]

    # avoid setting memory configs for basic sku
    if instance.sku.name == 'Basic':
        memory_configs = ['maxmemory-reserved', 'maxfragmentationmemory-reserved', 'maxmemory-delta']
        for memory_config in memory_configs:
            if memory_config in instance.redis_configuration:
                instance.redis_configuration.pop(memory_config)

    # trim RDB and AOF connection strings
    rdb_aof_connection_strings = ['rdb-storage-connection-string',
                                  'aof-storage-connection-string-0',
                                  'aof-storage-connection-string-1']
    for connection_string in rdb_aof_connection_strings:
        if connection_string in instance.redis_configuration:
            instance.redis_configuration.pop(connection_string)

    # Trim zonal-configuration
    if 'zonal-configuration' in instance.redis_configuration:
        instance.redis_configuration.pop('zonal-configuration')

    # pylint: disable=too-many-function-args
    update_params = RedisUpdateParameters(
        redis_configuration=instance.redis_configuration,
        enable_non_ssl_port=instance.enable_non_ssl_port,
        tenant_settings=instance.tenant_settings,
        shard_count=instance.shard_count,
        minimum_tls_version=instance.minimum_tls_version,
        sku=instance.sku,
        tags=instance.tags
    )
    return update_params


# pylint: disable=unused-argument
def cli_redis_create(cmd, client,
                     resource_group_name, name, location, sku, vm_size, tags=None,
                     redis_configuration=None, enable_non_ssl_port=None, tenant_settings=None,
                     shard_count=None, minimum_tls_version=None, subnet_id=None, static_ip=None,
                     zones=None, replicas_per_master=None):
    # pylint:disable=line-too-long
    if ((sku.lower() in ['standard', 'basic'] and vm_size.lower() not in allowed_c_family_sizes) or (sku.lower() in ['premium'] and vm_size.lower() not in allowed_p_family_sizes)):
        raise wrong_vmsize_error
    tenant_settings_in_json = {}
    if tenant_settings is not None:
        for item in tenant_settings:
            tenant_settings_in_json.update(get_key_value_pair(item))
    from azure.mgmt.redis.models import RedisCreateParameters, Sku
    # pylint: disable=too-many-function-args
    params = RedisCreateParameters(
        sku=Sku(name=sku, family=vm_size[0], capacity=vm_size[1:]),
        location=location,
        redis_configuration=redis_configuration,
        enable_non_ssl_port=enable_non_ssl_port,
        replicas_per_master=replicas_per_master,
        tenant_settings=tenant_settings_in_json,
        shard_count=shard_count,
        minimum_tls_version=minimum_tls_version,
        subnet_id=subnet_id,
        static_ip=static_ip,
        zones=zones,
        tags=tags)
    return client.create(resource_group_name, name, params)


def get_key_value_pair(string):
    result = {}
    if string:
        kvp = string.split('=', 1)
        result = {kvp[0]: kvp[1]} if len(kvp) > 1 else {string: ''}
    return result


# pylint: disable=unused-argument
def cli_redis_create_server_link(cmd, client, resource_group_name, name, server_to_link, replication_role):
    redis_client = cf_redis(cmd.cli_ctx)
    from azure.cli.core.commands.client_factory import get_subscription_id
    from msrestazure.tools import is_valid_resource_id, resource_id
    if not is_valid_resource_id(server_to_link):
        server_to_link = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=resource_group_name,
            namespace='Microsoft.Cache', type='Redis',
            name=server_to_link
        )

    cache_to_link = get_cache_from_resource_id(redis_client, server_to_link)

    from azure.mgmt.redis.models import RedisLinkedServerCreateParameters
    params = RedisLinkedServerCreateParameters(linked_redis_cache_id=cache_to_link.id,
                                               linked_redis_cache_location=cache_to_link.location,
                                               server_role=replication_role)
    return client.create(resource_group_name, name, cache_to_link.name, params)


def cli_redis_list_cache(client, resource_group_name=None):
    cache_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list()
    return list(cache_list)


def get_cache_from_resource_id(client, cache_resource_id):
    from msrestazure.tools import parse_resource_id
    id_comps = parse_resource_id(cache_resource_id)
    return client.get(id_comps['resource_group'], id_comps['name'])

# endregion
