# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAttachment(Model):
    """TaskAttachment.

    :param _links:
    :type _links: :class:`ReferenceLinks <task.v4_1.models.ReferenceLinks>`
    :param created_on:
    :type created_on: datetime
    :param last_changed_by:
    :type last_changed_by: str
    :param last_changed_on:
    :type last_changed_on: datetime
    :param name:
    :type name: str
    :param record_id:
    :type record_id: str
    :param timeline_id:
    :type timeline_id: str
    :param type:
    :type type: str
    """

    _attribute_map = {
        '_links': {'key': '_links', 'type': 'ReferenceLinks'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'last_changed_by': {'key': 'lastChangedBy', 'type': 'str'},
        'last_changed_on': {'key': 'lastChangedOn', 'type': 'iso-8601'},
        'name': {'key': 'name', 'type': 'str'},
        'record_id': {'key': 'recordId', 'type': 'str'},
        'timeline_id': {'key': 'timelineId', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'}
    }

    def __init__(self, _links=None, created_on=None, last_changed_by=None, last_changed_on=None, name=None, record_id=None, timeline_id=None, type=None):
        super(TaskAttachment, self).__init__()
        self._links = _links
        self.created_on = created_on
        self.last_changed_by = last_changed_by
        self.last_changed_on = last_changed_on
        self.name = name
        self.record_id = record_id
        self.timeline_id = timeline_id
        self.type = type
