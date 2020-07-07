# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskGroupRevision(Model):
    """TaskGroupRevision.

    :param changed_by:
    :type changed_by: :class:`IdentityRef <task-agent.v4_1.models.IdentityRef>`
    :param changed_date:
    :type changed_date: datetime
    :param change_type:
    :type change_type: object
    :param comment:
    :type comment: str
    :param file_id:
    :type file_id: int
    :param revision:
    :type revision: int
    :param task_group_id:
    :type task_group_id: str
    """

    _attribute_map = {
        'changed_by': {'key': 'changedBy', 'type': 'IdentityRef'},
        'changed_date': {'key': 'changedDate', 'type': 'iso-8601'},
        'change_type': {'key': 'changeType', 'type': 'object'},
        'comment': {'key': 'comment', 'type': 'str'},
        'file_id': {'key': 'fileId', 'type': 'int'},
        'revision': {'key': 'revision', 'type': 'int'},
        'task_group_id': {'key': 'taskGroupId', 'type': 'str'}
    }

    def __init__(self, changed_by=None, changed_date=None, change_type=None, comment=None, file_id=None, revision=None, task_group_id=None):
        super(TaskGroupRevision, self).__init__()
        self.changed_by = changed_by
        self.changed_date = changed_date
        self.change_type = change_type
        self.comment = comment
        self.file_id = file_id
        self.revision = revision
        self.task_group_id = task_group_id
