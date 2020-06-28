# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class PublishTaskGroupMetadata(Model):
    """PublishTaskGroupMetadata.

    :param comment:
    :type comment: str
    :param parent_definition_revision:
    :type parent_definition_revision: int
    :param preview:
    :type preview: bool
    :param task_group_id:
    :type task_group_id: str
    :param task_group_revision:
    :type task_group_revision: int
    """

    _attribute_map = {
        'comment': {'key': 'comment', 'type': 'str'},
        'parent_definition_revision': {'key': 'parentDefinitionRevision', 'type': 'int'},
        'preview': {'key': 'preview', 'type': 'bool'},
        'task_group_id': {'key': 'taskGroupId', 'type': 'str'},
        'task_group_revision': {'key': 'taskGroupRevision', 'type': 'int'}
    }

    def __init__(self, comment=None, parent_definition_revision=None, preview=None, task_group_id=None, task_group_revision=None):
        super(PublishTaskGroupMetadata, self).__init__()
        self.comment = comment
        self.parent_definition_revision = parent_definition_revision
        self.preview = preview
        self.task_group_id = task_group_id
        self.task_group_revision = task_group_revision
