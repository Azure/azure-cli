# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .task_log_reference import TaskLogReference


class TaskLog(TaskLogReference):
    """TaskLog.

    :param id:
    :type id: int
    :param location:
    :type location: str
    :param created_on:
    :type created_on: datetime
    :param index_location:
    :type index_location: str
    :param last_changed_on:
    :type last_changed_on: datetime
    :param line_count:
    :type line_count: long
    :param path:
    :type path: str
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'int'},
        'location': {'key': 'location', 'type': 'str'},
        'created_on': {'key': 'createdOn', 'type': 'iso-8601'},
        'index_location': {'key': 'indexLocation', 'type': 'str'},
        'last_changed_on': {'key': 'lastChangedOn', 'type': 'iso-8601'},
        'line_count': {'key': 'lineCount', 'type': 'long'},
        'path': {'key': 'path', 'type': 'str'}
    }

    def __init__(self, id=None, location=None, created_on=None, index_location=None, last_changed_on=None, line_count=None, path=None):
        super(TaskLog, self).__init__(id=id, location=location)
        self.created_on = created_on
        self.index_location = index_location
        self.last_changed_on = last_changed_on
        self.line_count = line_count
        self.path = path
