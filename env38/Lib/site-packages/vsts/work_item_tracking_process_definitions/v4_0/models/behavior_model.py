# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BehaviorModel(Model):
    """BehaviorModel.

    :param abstract: Is the behavior abstract (i.e. can not be associated with any work item type)
    :type abstract: bool
    :param color: Color
    :type color: str
    :param description: Description
    :type description: str
    :param id: Behavior Id
    :type id: str
    :param inherits: Parent behavior reference
    :type inherits: :class:`WorkItemBehaviorReference <work-item-tracking.v4_0.models.WorkItemBehaviorReference>`
    :param name: Behavior Name
    :type name: str
    :param overridden: Is the behavior overrides a behavior from system process
    :type overridden: bool
    :param rank: Rank
    :type rank: int
    :param url:
    :type url: str
    """

    _attribute_map = {
        'abstract': {'key': 'abstract', 'type': 'bool'},
        'color': {'key': 'color', 'type': 'str'},
        'description': {'key': 'description', 'type': 'str'},
        'id': {'key': 'id', 'type': 'str'},
        'inherits': {'key': 'inherits', 'type': 'WorkItemBehaviorReference'},
        'name': {'key': 'name', 'type': 'str'},
        'overridden': {'key': 'overridden', 'type': 'bool'},
        'rank': {'key': 'rank', 'type': 'int'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, abstract=None, color=None, description=None, id=None, inherits=None, name=None, overridden=None, rank=None, url=None):
        super(BehaviorModel, self).__init__()
        self.abstract = abstract
        self.color = color
        self.description = description
        self.id = id
        self.inherits = inherits
        self.name = name
        self.overridden = overridden
        self.rank = rank
        self.url = url
