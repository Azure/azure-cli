# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemTypeModel(Model):
    """WorkItemTypeModel.

    :param behaviors:
    :type behaviors: list of :class:`WorkItemTypeBehavior <work-item-tracking.v4_1.models.WorkItemTypeBehavior>`
    :param class_:
    :type class_: object
    :param color:
    :type color: str
    :param description:
    :type description: str
    :param icon:
    :type icon: str
    :param id:
    :type id: str
    :param inherits: Parent WIT Id/Internal ReferenceName that it inherits from
    :type inherits: str
    :param is_disabled:
    :type is_disabled: bool
    :param layout:
    :type layout: :class:`FormLayout <work-item-tracking.v4_1.models.FormLayout>`
    :param name:
    :type name: str
    :param states:
    :type states: list of :class:`WorkItemStateResultModel <work-item-tracking.v4_1.models.WorkItemStateResultModel>`
    :param url:
    :type url: str
    """

    _attribute_map = {
        'behaviors': {'key': 'behaviors', 'type': '[WorkItemTypeBehavior]'},
        'class_': {'key': 'class', 'type': 'object'},
        'color': {'key': 'color', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'icon': {'key': 'icon', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'inherits': {'key': 'inherits', 'type': 'str'},
        'is_disabled': {'key': 'isDisabled', 'type': 'bool'},
        'layout': {'key': 'layout', 'type': 'FormLayout'},
        'name': {'key': 'name', 'type': 'str'},
        'states': {'key': 'states', 'type': '[WorkItemStateResultModel]'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, behaviors=None, class_=None, color=None, description=None, icon=None, id=None, inherits=None, is_disabled=None, layout=None, name=None, states=None, url=None):
        super(WorkItemTypeModel, self).__init__()
        self.behaviors = behaviors
        self.class_ = class_
        self.color = color
        self.description = description
        self.icon = icon
        self.id = id
        self.inherits = inherits
        self.is_disabled = is_disabled
        self.layout = layout
        self.name = name
        self.states = states
        self.url = url
