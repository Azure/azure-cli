# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Group(Model):
    """Group.

    :param contribution: Contribution for the group.
    :type contribution: :class:`WitContribution <work-item-tracking.v4_1.models.WitContribution>`
    :param controls: Controls to be put in the group.
    :type controls: list of :class:`Control <work-item-tracking.v4_1.models.Control>`
    :param height: The height for the contribution.
    :type height: int
    :param id: The id for the layout node.
    :type id: str
    :param inherited: A value indicating whether this layout node has been inherited from a parent layout.  This is expected to only be only set by the combiner.
    :type inherited: bool
    :param is_contribution: A value indicating if the layout node is contribution are not.
    :type is_contribution: bool
    :param label: Label for the group.
    :type label: str
    :param order: Order in which the group should appear in the section.
    :type order: int
    :param overridden: A value indicating whether this layout node has been overridden by a child layout.
    :type overridden: bool
    :param visible: A value indicating if the group should be hidden or not.
    :type visible: bool
    """

    _attribute_map = {
        'contribution': {'key': 'contribution', 'type': 'WitContribution'},
        'controls': {'key': 'controls', 'type': '[Control]'},
        'height': {'key': 'height', 'type': 'int'},
        'id': {'key': 'id', 'type': 'str'},
        'inherited': {'key': 'inherited', 'type': 'bool'},
        'is_contribution': {'key': 'isContribution', 'type': 'bool'},
        'label': {'key': 'label', 'type': 'str'},
        'order': {'key': 'order', 'type': 'int'},
        'overridden': {'key': 'overridden', 'type': 'bool'},
        'visible': {'key': 'visible', 'type': 'bool'}
    }

    def __init__(self, contribution=None, controls=None, height=None, id=None, inherited=None, is_contribution=None, label=None, order=None, overridden=None, visible=None):
        super(Group, self).__init__()
        self.contribution = contribution
        self.controls = controls
        self.height = height
        self.id = id
        self.inherited = inherited
        self.is_contribution = is_contribution
        self.label = label
        self.order = order
        self.overridden = overridden
        self.visible = visible
