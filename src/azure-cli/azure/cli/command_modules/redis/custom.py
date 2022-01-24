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
    return client.begin_export_data(resource_group_name, name, parameters)


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
        instance.redis_configuration.maxmemory_reserved = None
        instance.redis_configuration.maxfragmentationmemory_reserved = None
        instance.redis_configuration.maxmemory_delta = None
        properties = instance.redis_configuration.additional_properties
        for memory_config in memory_configs:
            if properties is not None and memory_config in properties:
                instance.redis_configuration.additional_properties.pop(memory_config, None)
    # trim RDB and AOF connection strings and zonal-configuration
    removable_keys = [
        'rdb-storage-connection-string',
        'aof-storage-connection-string-0',
        'aof-storage-connection-string-1',
        'zonal-configuration']
    instance.redis_configuration.rdb_storage_connection_string = None
    instance.redis_configuration.aof_storage_connection_string0 = None
    instance.redis_configuration.aof_storage_connection_string1 = None
    properties = instance.redis_configuration.additional_properties
    for key in removable_keys:
        if properties is not None and key in properties:
            instance.redis_configuration.additional_properties.pop(key, None)
    # pylint: disable=too-many-function-args
    update_params = RedisUpdateParameters(
        redis_configuration=instance.redis_configuration,
        enable_non_ssl_port=instance.enable_non_ssl_port,
        tenant_settings=instance.tenant_settings,
        shard_count=instance.shard_count,
        minimum_tls_version=instance.minimum_tls_version,
        redis_version=instance.redis_version,
        sku=instance.sku,
        tags=instance.tags
    )
    return update_params


# pylint: disable=unused-argument
# pylint: disable=too-many-locals
def cli_redis_create(cmd, client,
                     resource_group_name, name, location, sku, vm_size, tags=None,
                     redis_configuration=None, enable_non_ssl_port=None, tenant_settings=None,
                     shard_count=None, minimum_tls_version=None, subnet_id=None, static_ip=None,
                     zones=None, replicas_per_master=None, redis_version=None, mi_system_assigned=None,
                     mi_user_assigned=None):
    # pylint:disable=line-too-long
    if ((sku.lower() in ['standard', 'basic'] and vm_size.lower() not in allowed_c_family_sizes) or (sku.lower() in ['premium'] and vm_size.lower() not in allowed_p_family_sizes)):
        raise wrong_vmsize_error
    tenant_settings_in_json = {}
    if tenant_settings is not None:
        for item in tenant_settings:
            tenant_settings_in_json.update(get_key_value_pair(item))
    from azure.mgmt.redis.models import RedisCreateParameters, Sku, RedisCommonPropertiesRedisConfiguration
    identity=build_identity(mi_system_assigned, mi_user_assigned)
    if (identity.type == "None"):
        identity = None
    # pylint: disable=too-many-function-args
    params = RedisCreateParameters(
        sku=Sku(name=sku, family=vm_size[0], capacity=vm_size[1:]),
        location=location,
        redis_configuration=RedisCommonPropertiesRedisConfiguration(additional_properties=redis_configuration),
        enable_non_ssl_port=enable_non_ssl_port,
        replicas_per_master=replicas_per_master,
        tenant_settings=tenant_settings_in_json,
        shard_count=shard_count,
        minimum_tls_version=minimum_tls_version,
        subnet_id=subnet_id,
        static_ip=static_ip,
        zones=zones,
        redis_version=redis_version,
        identity=identity,
        public_network_access=None,
        tags=tags)
    return client.begin_create(resource_group_name, name, params)


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
    return client.begin_create(resource_group_name, name, cache_to_link.name, params)


def cli_redis_patch_schedule_create_or_update(client, resource_group_name, name, schedule_entries):
    from azure.mgmt.redis.models import RedisPatchSchedule
    param = RedisPatchSchedule(schedule_entries=schedule_entries)
    return client.create_or_update(resource_group_name, name, "default", param)


def cli_redis_patch_schedule_get(client, resource_group_name, name):
    return client.get(resource_group_name, name, "default")


def cli_redis_patch_schedule_delete(client, resource_group_name, name):
    return client.delete(resource_group_name, name, "default")


def cli_redis_list_cache(client, resource_group_name=None):
    cache_list = client.list_by_resource_group(resource_group_name=resource_group_name) \
        if resource_group_name else client.list_by_subscription()
    return list(cache_list)


def get_cache_from_resource_id(client, cache_resource_id):
    from msrestazure.tools import parse_resource_id
    id_comps = parse_resource_id(cache_resource_id)
    return client.get(id_comps['resource_group'], id_comps['name'])


def cli_redis_firewall_create(client, resource_group_name, name, rule_name, start_ip, end_ip):
    from azure.mgmt.redis.models import RedisFirewallRule
    param = RedisFirewallRule(start_ip=start_ip, end_ip=end_ip)
    return client.create_or_update(resource_group_name, name, rule_name, param)


def cli_redis_regenerate_key(client, resource_group_name, name, key_type):
    from azure.mgmt.redis.models import RedisRegenerateKeyParameters
    return client.regenerate_key(resource_group_name, name, RedisRegenerateKeyParameters(key_type=key_type))


def cli_redis_import(client, resource_group_name, name, files, file_format=None):
    from azure.mgmt.redis.models import ImportRDBParameters
    return client.begin_import_data(resource_group_name, name, ImportRDBParameters(files=files, format=file_format))


def cli_redis_force_reboot(client, resource_group_name, name, reboot_type, shard_id=None):
    from azure.mgmt.redis.models import RedisRebootParameters
    param = RedisRebootParameters(reboot_type=reboot_type, shard_id=shard_id)
    return client.force_reboot(resource_group_name, name, param)


def cli_redis_identity_show(client, resource_group_name, cache_name):
    from azure.mgmt.redis.models import ManagedServiceIdentityType, ManagedServiceIdentity
    redis_resourse = client.get(resource_group_name, cache_name)
    if redis_resourse.identity is None:
        redis_resourse.identity = ManagedServiceIdentity(
            type=ManagedServiceIdentityType.NONE.value,
        )
    return redis_resourse.identity


def cli_redis_identity_assign(client, resource_group_name, cache_name, mi_system_assigned=None, mi_user_assigned=None):
    from azure.mgmt.redis.models import RedisUpdateParameters, ManagedServiceIdentityType
    redis_resourse = client.get(resource_group_name, cache_name)
    identity = redis_resourse.identity
    if identity is not None:
        if ManagedServiceIdentityType.SYSTEM_ASSIGNED.value in identity.type:
            mi_system_assigned = True
        if ManagedServiceIdentityType.USER_ASSIGNED.value in identity.type:
            old_user_identity = list(identity.user_assigned_identities)
            if mi_user_assigned is None:
                mi_user_assigned = []
            for user_id in old_user_identity:
                mi_user_assigned.append(user_id)
    update_params = RedisUpdateParameters(
        identity=build_identity(mi_system_assigned, mi_user_assigned))
    redis_resourse = client.update(resource_group_name, cache_name, update_params)
    return redis_resourse.identity


def cli_redis_identity_remove(client, resource_group_name, cache_name, mi_system_assigned=None, mi_user_assigned=None):
    from azure.mgmt.redis.models import RedisUpdateParameters, ManagedServiceIdentityType, ManagedServiceIdentity
    redis_resourse = client.get(resource_group_name, cache_name)
    identity = redis_resourse.identity
    system_assigned = None
    none_identity = ManagedServiceIdentity(
        type=ManagedServiceIdentityType.NONE.value)
    if identity is None:
        return none_identity
    if (identity.type == ManagedServiceIdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED.value or
            identity.type == ManagedServiceIdentityType.SYSTEM_ASSIGNED.value):
        system_assigned = True
    if mi_system_assigned is not None:
        system_assigned = None
    user_assigned = None
    if identity.user_assigned_identities is not None:
        user_assigned = list(identity.user_assigned_identities)
    if mi_user_assigned is not None and user_assigned is not None:
        for mi_user_id in mi_user_assigned:
            try:
                user_assigned.remove(mi_user_id)
            except ValueError:
                pass
        if len(user_assigned) == 0:
            user_assigned = None
    update_params = RedisUpdateParameters(
        identity=build_identity(system_assigned, user_assigned)
    )
    updated_resourse = client.update(resource_group_name, cache_name, update_params)
    if updated_resourse.identity is None:
        updated_resourse.identity = none_identity
    return updated_resourse.identity


def build_identity(mi_system_assigned, mi_user_assigned):
    from azure.mgmt.redis.models import ManagedServiceIdentity, ManagedServiceIdentityType, UserAssignedIdentity
    identityType = ManagedServiceIdentityType.NONE
    userIdentities = None
    if mi_system_assigned is not None:
        identityType = ManagedServiceIdentityType.SYSTEM_ASSIGNED
    if mi_user_assigned is not None and len(mi_user_assigned) > 0:
        userIdentities = {id: UserAssignedIdentity() for id in mi_user_assigned}
        if identityType == ManagedServiceIdentityType.NONE:
            identityType = ManagedServiceIdentityType.USER_ASSIGNED
        else:
            identityType = ManagedServiceIdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED
    return ManagedServiceIdentity(
        type=identityType.value,
        user_assigned_identities=userIdentities)

# endregion
