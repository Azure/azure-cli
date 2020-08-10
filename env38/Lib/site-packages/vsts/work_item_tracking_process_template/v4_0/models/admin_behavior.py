# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AdminBehavior(Model):
    """AdminBehavior.

    :param abstract:
    :type abstract: bool
    :param color:
    :type color: str
    :param custom:
    :type custom: bool
    :param description:
    :type description: str
    :param fields:
    :type fields: list of :class:`AdminBehaviorField <work-item-tracking-process-template.v4_0.models.AdminBehaviorField>`
    :param id:
    :type id: str
    :param inherits:
    :type inherits: str
    :param name:
    :type name: str
    :param overriden:
    :type overriden: bool
    :param rank:
    :type rank: int
    """

    _attribute_map = {
        'abstract': {'key': 'abstract', 'type': 'bool'},
        'color': {'key': 'color', 'type': 'str'},
        'custom': {'key': 'custom', 'type': 'bool'},
        'description': {'key': 'description', 'type': 'str'},
        'fields': {'key': 'fields', 'type': '[AdminBehaviorField]'},
        'id': {'key': 'id', 'type': 'str'},
        'inherits': {'key': 'inherits', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'overriden': {'key': 'overriden', 'type': 'bool'},
        'rank': {'key': 'rank', 'type': 'int'}
    }

    def __init__(self, abstract=None, color=None, custom=None, description=None, fields=None, id=None, inherits=None, name=None, overriden=None, rank=None):
        super(AdminBehavior, self).__init__()
        self.abstract = abstract
        self.color = color
        self.custom = custom
        self.description = description
        self.fields = fields
        self.id = id
        self.inherits = inherits
        self.name = name
        self.overriden = overriden
        self.rank = rank
