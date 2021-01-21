# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


def load_arguments(self, _):
    from azure.mgmt.redis.models import RebootType, RedisKeyType, SkuName, TlsVersion, ReplicationRole
    from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList
    from azure.cli.command_modules.redis.custom import allowed_c_family_sizes, allowed_p_family_sizes
    from azure.cli.core.commands.parameters import get_enum_type, tags_type, zones_type
    from azure.cli.core.commands.parameters import get_resource_name_completion_list

    with self.argument_context('redis') as c:
        cache_name = CLIArgumentType(options_list=['--name', '-n'], help='Name of the Redis cache.', id_part='name',
                                     completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        format_type = CLIArgumentType(options_list=['--file-format'], help='Format of the blob (Currently rdb is the only supported format, with other formats expected in the future)')

        c.argument('name', arg_type=cache_name)
        c.argument('redis_configuration', help='JSON encoded configuration settings. Use @{file} to load from a file.',
                   type=JsonString)
        c.argument('reboot_type', arg_type=get_enum_type(RebootType))
        c.argument('key_type', arg_type=get_enum_type(RedisKeyType))
        c.argument('files', help='SAS url for blobs that needs to be imported', nargs='+')
        c.argument('format', arg_type=format_type)
        c.argument('file_format', arg_type=format_type)
        c.argument('container', help='SAS url for container where data needs to be exported to')
        c.argument('prefix', help='Prefix to use for exported files')
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
        c.argument('replicas_per_master', help='The number of replicas to be created per master.', is_preview=True)

    with self.argument_context('redis firewall-rules list') as c:
        c.argument('cache_name', arg_type=cache_name, id_part=None)
        c.argument('rule_name', help='Name of the firewall rule')

    with self.argument_context('redis server-link') as c:
        c.argument('name', arg_type=cache_name, id_part=None)
        c.argument('server_to_link', help='Resource ID or name of the redis cache to be linked')
        c.argument('replication_role', help='Role of the redis cache to be linked', arg_type=get_enum_type(ReplicationRole))
        c.argument('linked_server_name', help='Name of the linked redis cache')

    with self.argument_context('redis patch-schedule') as c:
        c.argument('name', arg_type=cache_name, id_part=None)
        c.argument('schedule_entries', help="List of Patch schedule entries. Example Value:[{\"dayOfWeek\":\"Monday\",\"startHourUtc\":\"00\",\"maintenanceWindow\":\"PT5H\"}]", type=ScheduleEntryList)
