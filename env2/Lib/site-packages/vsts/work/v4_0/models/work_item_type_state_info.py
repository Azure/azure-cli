# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeStateInfo(Model):
    """WorkItemTypeStateInfo.

    :param states: State name to state category map
    :type states: dict
    :param work_item_type_name: Work Item type name
    :type work_item_type_name: str
    """

    _attribute_map = {
        'states': {'key': 'states', 'type': '{str}'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, states=None, work_item_type_name=None):
        super(WorkItemTypeStateInfo, self).__init__()
        self.states = states
        self.work_item_type_name = work_item_type_name
