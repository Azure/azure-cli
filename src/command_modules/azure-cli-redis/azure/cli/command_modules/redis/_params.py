# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.parameters import get_resource_name_completion_list, name_type
import azure.cli.command_modules.redis._help  # pylint: disable=unused-import
from azure.cli.command_modules.redis._validators import JsonString, ScheduleEntryList

from azure.mgmt.redis.models.redis_management_client_enums import RebootType, RedisKeyType, SkuName

from azure.cli.core.commands.parameters import get_enum_type  # TODO: Move this into Knack


def load_arguments(self, _):

    with self.argument_context('redis') as c:
        c.argument('name', options_list=['--name', '-n'], help='Name of the redis cache.', completer=get_resource_name_completion_list('Microsoft.Cache/redis'))
        c.argument('redis_configuration', type=JsonString)
        c.argument('reboot_type', arg_type=get_enum_type(RebootType))
        c.argument('key_type', arg_type=get_enum_type(RedisKeyType))
        c.argument('shard_id', type=int)
        c.argument('sku', arg_type=get_enum_type(SkuName))
        c.argument('vm_size', help='Size of redis cache to deploy. Example : values for C family (C0, C1, C2, C3, C4, C5, C6). For P family (P1, P2, P3, P4)')
        c.argument('enable_non_ssl_port', action='store_true')
        c.argument('shard_count', type=int)

    with self.argument_context('redis import-method') as c:
        c.argument('files', nargs='+')

    with self.argument_context('redis patch-schedule set') as c:
        c.argument('schedule_entries', type=ScheduleEntryList)

    with self.argument_context('redis create') as c:
        c.argument('name', arg_type=name_type, completer=None)
        c.argument('tenant_settings', type=JsonString)
