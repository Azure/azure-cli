# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BacklogLevelWorkItems(Model):
    """BacklogLevelWorkItems.

    :param work_items: A list of work items within a backlog level
    :type work_items: list of :class:`WorkItemLink <work.v4_1.models.WorkItemLink>`
    """

    _attribute_map = {
        'work_items': {'key': 'workItems', 'type': '[WorkItemLink]'}
    }

    def __init__(self, work_items=None):
        super(BacklogLevelWorkItems, self).__init__()
        self.work_items = work_items
