# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemStateInputModel(Model):
    """WorkItemStateInputModel.

    :param color:
    :type color: str
    :param name:
    :type name: str
    :param order:
    :type order: int
    :param state_category:
    :type state_category: str
    """

    _attribute_map = {
        'color': {'key': 'color', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'order': {'key': 'order', 'type': 'int'},
        'state_category': {'key': 'stateCategory', 'type': 'str'}
    }

    def __init__(self, color=None, name=None, order=None, state_category=None):
        super(WorkItemStateInputModel, self).__init__()
        self.color = color
        self.name = name
        self.order = order
        self.state_category = state_category
