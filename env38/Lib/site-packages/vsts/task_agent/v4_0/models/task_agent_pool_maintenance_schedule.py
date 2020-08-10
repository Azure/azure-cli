# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentPoolMaintenanceSchedule(Model):
    """TaskAgentPoolMaintenanceSchedule.

    :param days_to_build: Days for a build (flags enum for days of the week)
    :type days_to_build: object
    :param schedule_job_id: The Job Id of the Scheduled job that will queue the pool maintenance job.
    :type schedule_job_id: str
    :param start_hours: Local timezone hour to start
    :type start_hours: int
    :param start_minutes: Local timezone minute to start
    :type start_minutes: int
    :param time_zone_id: Time zone of the build schedule (string representation of the time zone id)
    :type time_zone_id: str
    """

    _attribute_map = {
        'days_to_build': {'key': 'daysToBuild', 'type': 'object'},
        'schedule_job_id': {'key': 'scheduleJobId', 'type': 'str'},
        'start_hours': {'key': 'startHours', 'type': 'int'},
        'start_minutes': {'key': 'startMinutes', 'type': 'int'},
        'time_zone_id': {'key': 'timeZoneId', 'type': 'str'}
    }

    def __init__(self, days_to_build=None, schedule_job_id=None, start_hours=None, start_minutes=None, time_zone_id=None):
        super(TaskAgentPoolMaintenanceSchedule, self).__init__()
        self.days_to_build = days_to_build
        self.schedule_job_id = schedule_job_id
        self.start_hours = start_hours
        self.start_minutes = start_minutes
        self.time_zone_id = time_zone_id
