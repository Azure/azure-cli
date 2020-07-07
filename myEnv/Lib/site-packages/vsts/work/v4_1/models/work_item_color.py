# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemColor(Model):
    """WorkItemColor.

    :param icon:
    :type icon: str
    :param primary_color:
    :type primary_color: str
    :param work_item_type_name:
    :type work_item_type_name: str
    """

    _attribute_map = {
        'icon': {'key': 'icon', 'type': 'str'},
        'primary_color': {'key': 'primaryColor', 'type': 'str'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, icon=None, primary_color=None, work_item_type_name=None):
        super(WorkItemColor, self).__init__()
        self.icon = icon
        self.primary_color = primary_color
        self.work_item_type_name = work_item_type_name
