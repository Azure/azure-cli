# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ReleaseSchedule(Model):
    """ReleaseSchedule.

    :param days_to_release: Days of the week to release
    :type days_to_release: object
    :param job_id: Team Foundation Job Definition Job Id
    :type job_id: str
    :param start_hours: Local time zone hour to start
    :type start_hours: int
    :param start_minutes: Local time zone minute to start
    :type start_minutes: int
    :param time_zone_id: Time zone Id of release schedule, such as 'UTC'
    :type time_zone_id: str
    """

    _attribute_map = {
        'days_to_release': {'key': 'daysToRelease', 'type': 'object'},
        'job_id': {'key': 'jobId', 'type': 'str'},
        'start_hours': {'key': 'startHours', 'type': 'int'},
        'start_minutes': {'key': 'startMinutes', 'type': 'int'},
        'time_zone_id': {'key': 'timeZoneId', 'type': 'str'}
    }

    def __init__(self, days_to_release=None, job_id=None, start_hours=None, start_minutes=None, time_zone_id=None):
        super(ReleaseSchedule, self).__init__()
        self.days_to_release = days_to_release
        self.job_id = job_id
        self.start_hours = start_hours
        self.start_minutes = start_minutes
        self.time_zone_id = time_zone_id
