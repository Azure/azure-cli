# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .timeline_reference import TimelineReference


class Timeline(TimelineReference):
    """Timeline.

    :param change_id:
    :type change_id: int
    :param id:
    :type id: str
    :param location:
    :type location: str
    :param last_changed_by:
    :type last_changed_by: str
    :param last_changed_on:
    :type last_changed_on: datetime
    :param records:
    :type records: list of :class:`TimelineRecord <task.v4_0.models.TimelineRecord>`
    """

    _attribute_map = {
        'change_id': {'key': 'changeId', 'type': 'int'},
        'id': {'key': 'id', 'type': 'str'},
        'location': {'key': 'location', 'type': 'str'},
        'last_changed_by': {'key': 'lastChangedBy', 'type': 'str'},
        'last_changed_on': {'key': 'lastChangedOn', 'type': 'iso-8601'},
        'records': {'key': 'records', 'type': '[TimelineRecord]'}
    }

    def __init__(self, change_id=None, id=None, location=None, last_changed_by=None, last_changed_on=None, records=None):
        super(Timeline, self).__init__(change_id=change_id, id=id, location=location)
        self.last_changed_by = last_changed_by
        self.last_changed_on = last_changed_on
        self.records = records
