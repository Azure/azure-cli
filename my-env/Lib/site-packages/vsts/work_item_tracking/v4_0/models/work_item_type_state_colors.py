# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeStateColors(Model):
    """WorkItemTypeStateColors.

    :param state_colors: Work item type state colors
    :type state_colors: list of :class:`WorkItemStateColor <work-item-tracking.v4_0.models.WorkItemStateColor>`
    :param work_item_type_name: Work item type name
    :type work_item_type_name: str
    """

    _attribute_map = {
        'state_colors': {'key': 'stateColors', 'type': '[WorkItemStateColor]'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, state_colors=None, work_item_type_name=None):
        super(WorkItemTypeStateColors, self).__init__()
        self.state_colors = state_colors
        self.work_item_type_name = work_item_type_name
