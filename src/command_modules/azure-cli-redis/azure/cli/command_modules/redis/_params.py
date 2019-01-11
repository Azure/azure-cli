# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.arguments import CLIArgumentType
import azure.cli.command_modules.redis._help  # pylint: disable=unused-import


def load_arguments(self, _):
    from azure.mgmt.redis.models import RebootType, RedisKeyType, SkuName
    from azure.cli.core.util import shell_safe_json_parse
    from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList
    from azure.cli.core.commands.parameters import get_enum_type  # TODO: Move this into Knack
    from azure.cli.core.commands.parameters import get_resource_name_completion_list

    with self.argument_context('redis') as c:
        cache_name = CLIArgumentType(options_list=['--name', '-n'], help='Name of the Redis cache.', id_part='name',
                                     completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        # pylint:disable=line-too-long
        cache_name_without_id_part = CLIArgumentType(options_list=['--name', '-n'], help='Name of the Redis cache.', id_part=None,
                                                     completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        format_type = CLIArgumentType(options_list=['--file-format'], help='Format of the blob (Example: rdb)')

        c.argument('name', arg_type=cache_name)
        c.argument('redis_configuration', help='JSON encoded configuration settings. Use @{file} to load from a file.',
                   type=JsonString)
        c.argument('reboot_type', arg_type=get_enum_type(RebootType))
        c.argument('key_type', arg_type=get_enum_type(RedisKeyType))
        c.argument('shard_id', type=int)
        c.argument('sku', help='Type of Redis cache.', arg_type=get_enum_type(SkuName))
        c.argument('vm_size', help='Size of Redis cache to deploy. Example : values for C family (C0, C1, C2, C3, C4, '
                                   'C5, C6). For P family (P1, P2, P3, P4, P5)')
        c.argument('enable_non_ssl_port', action='store_true')
        c.argument('shard_count', type=int)
        c.argument('files', help='SAS url for blobs that needs to be imported', nargs='+')
        c.argument('format', arg_type=format_type)
        c.argument('file_format', arg_type=format_type)
        c.argument('container', help='SAS url for container where data needs to be exported to')
        c.argument('prefix', help='Prefix to use for exported files')
        # pylint: disable=line-too-long
        c.argument('schedule_entries', help="List of Patch schedule entries. Example Value:[{\"dayOfWeek\":\"Monday\",\"startHourUtc\":\"00\",\"maintenanceWindow\":\"PT5H\"}]", type=ScheduleEntryList)
        c.argument('tenant_settings', type=JsonString)
        c.argument('tags', type=JsonString)
        c.argument('zones', type=shell_safe_json_parse)
        c.argument('linked_server_name', help='Name of the linked redis cache')
        c.argument('secondary_cache', help='Resource Id of the redis cache to be linked as Secondary')
        c.argument('primary_cache', help='Resource Id of the Primary redis cache')
        c.argument('rule_name', help='Name of the firewall rule')
        c.argument('cache_name', arg_type=cache_name)

    with self.argument_context('redis firewall-rules list') as c:
        c.argument('cache_name', arg_type=cache_name_without_id_part)

    with self.argument_context('redis server-link') as c:
        c.argument('name', arg_type=cache_name_without_id_part)
