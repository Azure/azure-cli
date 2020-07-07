# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemStateColor(Model):
    """WorkItemStateColor.

    :param category: Category of state
    :type category: str
    :param color: Color value
    :type color: str
    :param name: Work item type state name
    :type name: str
    """

    _attribute_map = {
        'category': {'key': 'category', 'type': 'str'},
        'color': {'key': 'color', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, category=None, color=None, name=None):
        super(WorkItemStateColor, self).__init__()
        self.category = category
        self.color = color
        self.name = name
