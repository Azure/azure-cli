# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemStateResultModel(Model):
    """WorkItemStateResultModel.

    :param color: Color of the state
    :type color: str
    :param hidden: Is the state hidden
    :type hidden: bool
    :param id: The ID of the State
    :type id: str
    :param name: Name of the state
    :type name: str
    :param order: Order in which state should appear
    :type order: int
    :param state_category: Category of the state
    :type state_category: str
    :param url: Url of the state
    :type url: str
    """

    _attribute_map = {
        'color': {'key': 'color', 'type': 'str'},
        'hidden': {'key': 'hidden', 'type': 'bool'},
        'id': {'key': 'id', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'order': {'key': 'order', 'type': 'int'},
        'state_category': {'key': 'stateCategory', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, color=None, hidden=None, id=None, name=None, order=None, state_category=None, url=None):
        super(WorkItemStateResultModel, self).__init__()
        self.color = color
        self.hidden = hidden
        self.id = id
        self.name = name
        self.order = order
        self.state_category = state_category
        self.url = url
