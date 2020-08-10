# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemBehavior(Model):
    """WorkItemBehavior.

    :param abstract:
    :type abstract: bool
    :param color:
    :type color: str
    :param description:
    :type description: str
    :param fields:
    :type fields: list of :class:`WorkItemBehaviorField <work-item-tracking.v4_1.models.WorkItemBehaviorField>`
    :param id:
    :type id: str
    :param inherits:
    :type inherits: :class:`WorkItemBehaviorReference <work-item-tracking.v4_1.models.WorkItemBehaviorReference>`
    :param name:
    :type name: str
    :param overriden:
    :type overriden: bool
    :param rank:
    :type rank: int
    :param url:
    :type url: str
    """

    _attribute_map = {
        'abstract': {'key': 'abstract', 'type': 'bool'},
        'color': {'key': 'color', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'fields': {'key': 'fields', 'type': '[WorkItemBehaviorField]'},
        'id': {'key': 'id', 'type': 'str'},
        'inherits': {'key': 'inherits', 'type': 'WorkItemBehaviorReference'},
        'name': {'key': 'name', 'type': 'str'},
        'overriden': {'key': 'overriden', 'type': 'bool'},
        'rank': {'key': 'rank', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, abstract=None, color=None, description=None, fields=None, id=None, inherits=None, name=None, overriden=None, rank=None, url=None):
        super(WorkItemBehavior, self).__init__()
        self.abstract = abstract
        self.color = color
        self.description = description
        self.fields = fields
        self.id = id
        self.inherits = inherits
        self.name = name
        self.overriden = overriden
        self.rank = rank
        self.url = url
