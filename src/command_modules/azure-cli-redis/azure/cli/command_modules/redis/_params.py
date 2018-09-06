# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import azure.cli.command_modules.redis._help  # pylint: disable=unused-import


def load_arguments(self, _):
    from azure.mgmt.redis.models import RebootType, RedisKeyType, SkuName
    from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList
    from azure.cli.core.commands.parameters import get_enum_type  # TODO: Move this into Knack
    from azure.cli.core.commands.parameters import get_resource_name_completion_list, name_type, tags_type

    with self.argument_context('redis') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the Redis cache.', id_part='name',
                   completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        c.argument('redis_configuration', help='JSON encoded configuration settings. Use @{file} to load from a file.',
                   type=JsonString)
        c.argument('reboot_type', arg_type=get_enum_type(RebootType))
        c.argument('key_type', arg_type=get_enum_type(RedisKeyType))
        c.argument('shard_id', type=int)
        c.argument('sku', help='Type of Redis cache.', arg_type=get_enum_type(SkuName))
        c.argument('vm_size', help='Size of Redis cache to deploy. Example : values for C family (C0, C1, C2, C3, C4, '
                                   'C5, C6). For P family (P1, P2, P3, P4)')
        c.argument('enable_non_ssl_port', action='store_true')
        c.argument('shard_count', type=int)
        c.argument('tags', tags_type)

    for scope in ['redis import-method', 'redis import']:
        with self.argument_context(scope) as c:
            c.argument('files', nargs='+', help='Space-separated list of files to import.')
            c.argument('file_format', help='File format to import.')

    with self.argument_context('redis patch-schedule set') as c:
        c.argument('schedule_entries', type=ScheduleEntryList)

    with self.argument_context('redis create') as c:
        c.argument('name', arg_type=name_type, completer=None)
        c.argument('tenant_settings', type=JsonString)

    with self.argument_context('redis export') as c:
        c.argument('container', help='Container name to export to.')
        c.argument('prefix', help='Prefix to use for exported files.')
        c.argument('file_format', help='File format to export.')
