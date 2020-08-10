# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Section(Model):
    """Section.

    :param groups:
    :type groups: list of :class:`Group <work-item-tracking.v4_0.models.Group>`
    :param id: The id for the layout node.
    :type id: str
    :param overridden: A value indicating whether this layout node has been overridden by a child layout.
    :type overridden: bool
    """

    _attribute_map = {
        'groups': {'key': 'groups', 'type': '[Group]'},
        'id': {'key': 'id', 'type': 'str'},
        'overridden': {'key': 'overridden', 'type': 'bool'}
    }

    def __init__(self, groups=None, id=None, overridden=None):
        super(Section, self).__init__()
        self.groups = groups
        self.id = id
        self.overridden = overridden
