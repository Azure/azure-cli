# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands.parameters import (
    get_resource_name_completion_list,
    enum_choice_list,
    name_type)
from azure.cli.core.commands import register_cli_argument
import azure.cli.core.commands.arm # pylint: disable=unused-import
# from azure.mgmt.documentdb.models.documentdb_management_client_enums import (
#     RebootType,
#     documentdbKeyType,
#     SkuFamily,
#     SkuName)

# from azure.mgmt.documentdb.models import (
#     ScheduleEntry,
# )

# class JsonString(dict):

#     def __init__(self, value):
#         super(JsonString, self).__init__()
#         import json
#         if value[0] in ("'", '"') and value[-1] == value[0]:
#             # Remove leading and trailing quotes for dos/cmd.exe users
#             value = value[1:-1]
#         dictval = json.loads(value)
#         self.update(dictval)

# class ScheduleEntryList(list):
#     def __init__(self, value):
#         super(ScheduleEntryList, self).__init__()
#         import json
#         if value[0] in ("'", '"') and value[-1] == value[0]:
#             # Remove leading and trailing quotes for dos/cmd.exe users
#             value = value[1:-1]
#         dictval = json.loads(value)
#         self.extend([ScheduleEntry(
#             row['dayOfWeek'],
#             int(row['startHourUtc']),
#             row.get('maintenanceWindow', None))
#                      for row in dictval])

# register_cli_argument('documentdb', 'name', arg_type=name_type, help='Name of the documentdb cache.', completer=get_resource_name_completion_list('Microsoft.DocumentDb/databaseAccounts'), id_part='name')
# register_cli_argument('documentdb', 'documentdb_configuration', type=JsonString)
# register_cli_argument('documentdb', 'reboot_type', **enum_choice_list(RebootType))
# register_cli_argument('documentdb', 'key_type', **enum_choice_list(documentdbKeyType))
# register_cli_argument('documentdb', 'shard_id', type=int)
# register_cli_argument('documentdb import-method', 'files', nargs='+')

# register_cli_argument('documentdb patch-schedule set', 'schedule_entries', type=ScheduleEntryList)

# register_cli_argument('documentdb create', 'name', arg_type=name_type, completer=None)
# register_cli_argument('documentdb create', 'sku_name', **enum_choice_list(SkuName))
# register_cli_argument('documentdb create', 'sku_family', **enum_choice_list(SkuFamily))
# register_cli_argument('documentdb create', 'sku_capacity', choices=[str(n) for n in range(0, 7)])
# register_cli_argument('documentdb create', 'enable_non_ssl_port', action='store_true')
# register_cli_argument('documentdb create', 'tenant_settings', type=JsonString)
# register_cli_argument('documentdb create', 'shard_count', type=int)
# register_cli_argument('documentdb create', 'subnet_id') # TODO: Create generic id completer similar to name
