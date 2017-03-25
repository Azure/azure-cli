# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# coding: utf-8
# pylint: skip-file
from msrest.serialization import Model


class Schedule(Model):
    """A schedule.

    :param status: The status of the schedule (i.e. Enabled, Disabled).
     Possible values include: 'Enabled', 'Disabled'
    :type status: str or :class:`EnableStatus
     <azure.mgmt.devtestlabs.models.EnableStatus>`
    :param task_type: The task type of the schedule (e.g. LabVmsShutdownTask,
     LabVmAutoStart).
    :type task_type: str
    :param weekly_recurrence: If the schedule will occur only some days of the
     week, specify the weekly recurrence.
    :type weekly_recurrence: :class:`WeekDetails
     <azure.mgmt.devtestlabs.models.WeekDetails>`
    :param daily_recurrence: If the schedule will occur once each day of the
     week, specify the daily recurrence.
    :type daily_recurrence: :class:`DayDetails
     <azure.mgmt.devtestlabs.models.DayDetails>`
    :param hourly_recurrence: If the schedule will occur multiple times a day,
     specify the hourly recurrence.
    :type hourly_recurrence: :class:`HourDetails
     <azure.mgmt.devtestlabs.models.HourDetails>`
    :param time_zone_id: The time zone ID (e.g. Pacific Standard time).
    :type time_zone_id: str
    :param notification_settings: Notification settings.
    :type notification_settings: :class:`NotificationSettings
     <azure.mgmt.devtestlabs.models.NotificationSettings>`
    :param created_date: The creation date of the schedule.
    :type created_date: datetime
    :param target_resource_id: The resource ID to which the schedule belongs
    :type target_resource_id: str
    :param provisioning_state: The provisioning status of the resource.
    :type provisioning_state: str
    :param unique_identifier: The unique immutable identifier of a resource
     (Guid).
    :type unique_identifier: str
    :param id: The identifier of the resource.
    :type id: str
    :param name: The name of the resource.
    :type name: str
    :param type: The type of the resource.
    :type type: str
    :param location: The location of the resource.
    :type location: str
    :param tags: The tags of the resource.
    :type tags: dict
    """

    _attribute_map = {
        'status': {'key': 'properties.status', 'type': 'str'},
        'task_type': {'key': 'properties.taskType', 'type': 'str'},
        'weekly_recurrence': {'key': 'properties.weeklyRecurrence', 'type': 'WeekDetails'},
        'daily_recurrence': {'key': 'properties.dailyRecurrence', 'type': 'DayDetails'},
        'hourly_recurrence': {'key': 'properties.hourlyRecurrence', 'type': 'HourDetails'},
        'time_zone_id': {'key': 'properties.timeZoneId', 'type': 'str'},
        'notification_settings': {'key': 'properties.notificationSettings', 'type': 'NotificationSettings'},
        'created_date': {'key': 'properties.createdDate', 'type': 'iso-8601'},
        'target_resource_id': {'key': 'properties.targetResourceId', 'type': 'str'},
        'provisioning_state': {'key': 'properties.provisioningState', 'type': 'str'},
        'unique_identifier': {'key': 'properties.uniqueIdentifier', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'tags': {'key': 'tags', 'type': '{str}'},
    }

    def __init__(self, status=None, task_type=None, weekly_recurrence=None, daily_recurrence=None, hourly_recurrence=None, time_zone_id=None, notification_settings=None, created_date=None, target_resource_id=None, provisioning_state=None, unique_identifier=None, id=None, name=None, type=None, location=None, tags=None):
        self.status = status
        self.task_type = task_type
        self.weekly_recurrence = weekly_recurrence
        self.daily_recurrence = daily_recurrence
        self.hourly_recurrence = hourly_recurrence
        self.time_zone_id = time_zone_id
        self.notification_settings = notification_settings
        self.created_date = created_date
        self.target_resource_id = target_resource_id
        self.provisioning_state = provisioning_state
        self.unique_identifier = unique_identifier
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.tags = tags
