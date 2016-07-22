# pylint: disable=line-too-long
from azure.cli.commands.parameters import (
    get_resource_name_completion_list,
    get_enum_type_completion_list,
    name_type)
from azure.cli.commands import register_cli_argument, CliArgumentType
import azure.cli.commands.arm
from azure.mgmt.redis.models.redis_management_client_enums import RebootType, RedisKeyType

from azure.mgmt.redis.models import (
    ScheduleEntry,
)

class JsonString(dict):

    def __init__(self, value):
        import json
        if value[0] in ("'", '"') and value[-1] == value[0]:
            # Remove leading and trailing quotes for dos/cmd.exe users
            value = value[1:-1]
        dictval = json.loads(value)
        self.update(dictval)

class ScheduleEntryList(list):
    def __init__(self, value):
        import json
        if value[0] in ("'", '"') and value[-1] == value[0]:
            # Remove leading and trailing quotes for dos/cmd.exe users
            value = value[1:-1]
        dictval = json.loads(value)
        self.extend([ScheduleEntry(
            row['dayOfWeek'],
            int(row['startHourUtc']),
            row.get('maintenanceWindow', None))
                     for row in dictval])

register_cli_argument('redis', 'name', arg_type=name_type, completer=get_resource_name_completion_list('Microsoft.Cache/redis'), id_part='name')
register_cli_argument('redis', 'redis_configuration', type=JsonString)
register_cli_argument('redis', 'reboot_type', completer=get_enum_type_completion_list(RebootType))
register_cli_argument('redis', 'key_type', choices=[e.value for e in RedisKeyType])
register_cli_argument('redis', 'shard_id', type=int)
register_cli_argument('redis import-method', 'files', nargs='+')

register_cli_argument('redis patch-schedule set', 'schedule_entries', type=ScheduleEntryList)
