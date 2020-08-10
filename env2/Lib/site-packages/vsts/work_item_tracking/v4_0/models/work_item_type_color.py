# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeColor(Model):
    """WorkItemTypeColor.

    :param primary_color:
    :type primary_color: str
    :param secondary_color:
    :type secondary_color: str
    :param work_item_type_name:
    :type work_item_type_name: str
    """

    _attribute_map = {
        'primary_color': {'key': 'primaryColor', 'type': 'str'},
        'secondary_color': {'key': 'secondaryColor', 'type': 'str'},
        'work_item_type_name': {'key': 'workItemTypeName', 'type': 'str'}
    }

    def __init__(self, primary_color=None, secondary_color=None, work_item_type_name=None):
        super(WorkItemTypeColor, self).__init__()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.work_item_type_name = work_item_type_name
