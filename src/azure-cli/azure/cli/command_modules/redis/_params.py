# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import get_three_state_flag


def load_arguments(self, _):  # pylint: disable=too-many-statements
    from azure.mgmt.redis.models import RebootType, RedisKeyType, SkuName, TlsVersion, ReplicationRole, UpdateChannel, ZonalAllocationPolicy
    from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList
    from azure.cli.command_modules.redis.custom import allowed_c_family_sizes, allowed_p_family_sizes, allowed_auth_methods
    from azure.cli.core.commands.parameters import get_enum_type, tags_type, zones_type
    from azure.cli.core.commands.parameters import get_resource_name_completion_list

    system_identity_type = CLIArgumentType(action='store_true', help='Flag to specify system assigned identity')
    user_identity_type = CLIArgumentType(nargs='+', help='One or more space separated resource IDs of user assigned identities')

    with self.argument_context('redis') as c:
        cache_name = CLIArgumentType(options_list=['--name', '-n'], help='Name of the Redis cache.', id_part='name',
                                     completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        format_type = CLIArgumentType(options_list=['--file-format'], help='Format of the blob (Currently rdb is the only supported format, with other formats expected in the future)')

        c.argument('name', arg_type=cache_name)
        c.argument('redis_configuration', help='JSON encoded configuration settings. Use @{file} to load from a file.',
                   type=JsonString)
        c.argument('reboot_type', arg_type=get_enum_type(RebootType), help='Which Redis node(s) to reboot. Depending on this value data loss is possible.')
        c.argument('key_type', arg_type=get_enum_type(RedisKeyType), help='The Redis access key to regenerate.')
        c.argument('files', help='SAS url for blobs that needs to be imported', nargs='+')
        c.argument('format', arg_type=format_type)
        c.argument('file_format', arg_type=format_type)
        c.argument('container', help='SAS url for container where data needs to be exported to')
        c.argument('prefix', help='Prefix to use for exported files')
        c.argument('preferred_data_archive_auth_method', options_list=['--preferred-data-archive-auth-method', '--auth-method'], arg_type=get_enum_type(allowed_auth_methods), help='Preferred auth method to communicate to storage account used for data archive, default value is SAS')
        c.argument('cache_name', arg_type=cache_name)
        c.argument('shard_count', type=int, help='The number of shards to be created on a Premium Cluster Cache.')
        c.argument('subnet_id', help='The full resource ID of a subnet in a virtual network to deploy the redis cache in. Example format /subscriptions/{subid}/resourceGroups/{resourceGroupName}/providers/Microsoft.{Network|ClassicNetwork}/virtualNetworks/vnet1/subnets/subnet1')
        c.argument('static_ip', help='Specify a static ip if required for the VNET. If you do not specify a static IP then an IP address is chosen automatically')
        c.argument('tenant_settings', arg_type=tags_type, help='Space-separated tenant settings in key[=value] format')
        c.argument('tags', arg_type=tags_type)
        c.argument('zones', arg_type=zones_type)
        c.argument('shard_id', type=int)
        c.argument('sku', help='Type of Redis cache.', arg_type=get_enum_type(SkuName))
        c.argument('minimum_tls_version', help='Specifies the TLS version required by clients to connect to cache', arg_type=get_enum_type(TlsVersion))
        c.argument('vm_size', arg_type=get_enum_type(allowed_c_family_sizes + allowed_p_family_sizes), help='Size of Redis cache to deploy. Basic and Standard Cache sizes start with C. Premium Cache sizes start with P')
        c.argument('enable_non_ssl_port', action='store_true', help='If specified, then the non-ssl redis server port (6379) will be enabled.')
        c.argument('replicas_per_master', help='The number of replicas to be created per master.')
        c.argument('redis_version', help='Redis version. This should be in the form \'major[.minor]\' (only \'major\' is required) or the value \'latest\' which refers to the latest stable Redis version that is available. Supported versions: 4.0, 6.0 (latest). Default value is \'latest\'.')
        c.argument('mi_system_assigned', arg_type=system_identity_type)
        c.argument('mi_user_assigned', arg_type=user_identity_type)
        c.argument('update_channel', arg_type=get_enum_type(UpdateChannel), help='Specifies the update channel for the monthly Redis updates your Redis Cache will receive. Caches using "Preview" update channel get latest Redis updates at least 4 weeks ahead of "Stable" channel caches. Default value is "Stable".')
        c.argument('storage_subscription_id', options_list=['--storage-subscription-id', '--storage-sub-id'], help='SubscriptionId of the storage account')
        c.argument('disable_access_key_authentication', arg_type=get_three_state_flag(), options_list=['--disable-access-keys'], help='Authentication to Redis through access keys is disabled when set as true')
        c.argument('zonal_allocation_policy', options_list=['--zonal-allocation-policy', '--zonal-allocation'], arg_type=get_enum_type(ZonalAllocationPolicy), help='Specifies how availability zones are allocated to the Redis cache. "Automatic" enables zone redundancy and Azure will automatically select zones based on regional availability and capacity. "UserDefined" will select availability zones passed in by you using the "zones" parameter. "NoZones" will produce a non-zonal cache. If "zonal-allocation-policy" is not passed, it will be set to "UserDefined" when zones are passed in, otherwise, it will be set to "Automatic in regions where zones are supported and "NoZones" in regions where zones are not supported.')

    with self.argument_context('redis firewall-rules list') as c:
        c.argument('cache_name', arg_type=cache_name, id_part=None)
        c.argument('rule_name', help='Name of the firewall rule')

    with self.argument_context('redis firewall-rules') as c:
        c.argument('end_ip', help='Highest IP address included in the range.')
        c.argument('rule_name', help='The name of the firewall rule.')
        c.argument('start_ip', help='Lowest IP address included in the range.')

    with self.argument_context('redis access-policy') as c:
        c.argument('access_policy_name', help='The name of the access policy that is being assigned')
        c.argument('permissions', help='Permissions for the access policy. Learn how to configure permissions at '
                                       'https://aka.ms/redis/AADPreRequisites')

    with self.argument_context('redis access-policy list') as c:
        c.argument('cache_name', arg_type=cache_name, id_part=None)

    with self.argument_context('redis access-policy-assignment') as c:
        c.argument('access_policy_assignment_name', options_list=['--policy-assignment-name'],
                   help='The name of the access policy assignment')
        c.argument('object_id', help='Object Id to assign access policy to')
        c.argument('object_id_alias', help='User friendly name for object id. Also represents username for token '
                                           'based authentication')
        c.argument('access_policy_name', help='The name of the access policy that is being assigned')

    with self.argument_context('redis access-policy-assignment list') as c:
        c.argument('cache_name', arg_type=cache_name, id_part=None)

    with self.argument_context('redis force-reboot') as c:
        c.argument('shard_id', help='If clustering is enabled, the ID of the shard to be rebooted.')

    with self.argument_context('redis server-link') as c:
        c.argument('name', arg_type=cache_name, id_part=None)
        c.argument('server_to_link', help='Resource ID or name of the redis cache to be linked')
        c.argument('replication_role', help='Role of the redis cache to be linked', arg_type=get_enum_type(ReplicationRole))
        c.argument('linked_server_name', help='Name of the linked redis cache')

    with self.argument_context('redis patch-schedule') as c:
        c.argument('name', arg_type=cache_name, id_part=None)
        c.argument('schedule_entries', help="List of Patch schedule entries. Example Value:[{\"dayOfWeek\":\"Monday\",\"startHourUtc\":\"00\",\"maintenanceWindow\":\"PT5H\"}]", type=ScheduleEntryList)

    with self.argument_context('redis identity') as c:
        c.argument('name', arg_type=cache_name, id_part=None)
        c.argument('mi_system_assigned', arg_type=system_identity_type)
        c.argument('mi_user_assigned', arg_type=user_identity_type)

    # hide --no-wait from customer usage, only use for functional tests to get LRO result
    with self.argument_context('redis update') as c:
        c.extra('no_wait', arg_type=get_three_state_flag(), help="Specify as false to wait for result of long running operation", deprecate_info=c.deprecate(hide=True))
