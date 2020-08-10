# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeColorAndIcon(Model):
    """WorkItemTypeColorAndIcon.

    :param color:
    :type color: str
    :param icon:
    :type icon: str
    :param work_item_type_name:
    :type work_item_type_name: str
    """

    _attribute_map = {
        'color': {'key': 'color', 'type': 'str'},
        'icon': {'key': 'icon', 'type': 'str'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, color=None, icon=None, work_item_type_name=None):
        super(WorkItemTypeColorAndIcon, self).__init__()
        self.color = color
        self.icon = icon
        self.work_item_type_name = work_item_type_name
