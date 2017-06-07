# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    enum_choice_list,
    name_type)
from azure.cli.core.util import shell_safe_json_parse
from azure.cli.core.commands import register_cli_argument
import azure.cli.core.commands.arm  # pylint: disable=unused-import
from azure.mgmt.redis.models.redis_management_client_enums import (
    RebootType,
    RedisKeyType,
    SkuName)

from azure.mgmt.redis.models import (
    ScheduleEntry,
)


class JsonString(dict):
    def __init__(self, value):
        super(JsonString, self).__init__()
        if value[0] in ("'", '"') and value[-1] == value[0]:
            # Remove leading and trailing quotes for dos/cmd.exe users
            value = value[1:-1]
        dictval = shell_safe_json_parse(value)
        self.update(dictval)


class ScheduleEntryList(list):
    def __init__(self, value):
        super(ScheduleEntryList, self).__init__()
        if value[0] in ("'", '"') and value[-1] == value[0]:
            # Remove leading and trailing quotes for dos/cmd.exe users
            value = value[1:-1]
        dictval = shell_safe_json_parse(value)
        self.extend([ScheduleEntry(row['dayOfWeek'],
                                   int(row['startHourUtc']),
                                   row.get('maintenanceWindow', None)) for row in dictval])


register_cli_argument('redis', 'name', arg_type=name_type, help='Name of the redis cache.',
                      completer=get_resource_name_completion_list('Microsoft.Cache/redis'),
                      id_part='name')
register_cli_argument('redis', 'redis_configuration', type=JsonString)
register_cli_argument('redis', 'reboot_type', **enum_choice_list(RebootType))
register_cli_argument('redis', 'key_type', **enum_choice_list(RedisKeyType))
register_cli_argument('redis', 'shard_id', type=int)
register_cli_argument('redis', 'sku', **enum_choice_list(SkuName))
register_cli_argument('redis', 'vm_size',
                      help='Size of redis cache to deploy. '
                           'Example : values for C family (C0, C1, C2, C3, C4, C5, C6). '
                           'For P family (P1, P2, P3, P4)')
register_cli_argument('redis', 'enable_non_ssl_port', action='store_true')
register_cli_argument('redis', 'shard_count', type=int)
register_cli_argument('redis', 'subnet_id')

register_cli_argument('redis import-method', 'files', nargs='+')

register_cli_argument('redis patch-schedule set', 'schedule_entries', type=ScheduleEntryList)

register_cli_argument('redis create', 'name', arg_type=name_type, completer=None)
register_cli_argument('redis create', 'tenant_settings', type=JsonString)
