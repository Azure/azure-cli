# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import shell_safe_json_parse


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

        from azure.mgmt.redis.models import ScheduleEntry

        if value[0] in ("'", '"') and value[-1] == value[0]:
            # Remove leading and trailing quotes for dos/cmd.exe users
            value = value[1:-1]
        dictval = shell_safe_json_parse(value)
        self.extend([ScheduleEntry(day_of_week=row['dayOfWeek'],
                                   start_hour_utc=int(row['startHourUtc']),
                                   maintenance_window=row.get('maintenanceWindow', None)) for row in dictval])
