# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Control(Model):
    """Control.

    :param contribution: Contribution for the control.
    :type contribution: :class:`WitContribution <work-item-tracking.v4_1.models.WitContribution>`
    :param control_type: Type of the control.
    :type control_type: str
    :param height: Height of the control, for html controls.
    :type height: int
    :param id: The id for the layout node.
    :type id: str
    :param inherited: A value indicating whether this layout node has been inherited from a parent layout.  This is expected to only be only set by the combiner.
    :type inherited: bool
    :param is_contribution: A value indicating if the layout node is contribution or not.
    :type is_contribution: bool
    :param label: Label for the field
    :type label: str
    :param metadata: Inner text of the control.
    :type metadata: str
    :param order:
    :type order: int
    :param overridden: A value indicating whether this layout node has been overridden by a child layout.
    :type overridden: bool
    :param read_only: A value indicating if the control is readonly.
    :type read_only: bool
    :param visible: A value indicating if the control should be hidden or not.
    :type visible: bool
    :param watermark: Watermark text for the textbox.
    :type watermark: str
    """

    _attribute_map = {
        'contribution': {'key': 'contribution', 'type': 'WitContribution'},
        'control_type': {'key': 'controlType', 'type': 'str'},
        'height': {'key': 'height', 'type': 'int'},
        'id': {'key': 'id', 'type': 'str'},
        'inherited': {'key': 'inherited', 'type': 'bool'},
        'is_contribution': {'key': 'isContribution', 'type': 'bool'},
        'label': {'key': 'label', 'type': 'str'},
        'metadata': {'key': 'metadata', 'type': 'str'},
        'order': {'key': 'order', 'type': 'int'},
        'overridden': {'key': 'overridden', 'type': 'bool'},
        'read_only': {'key': 'readOnly', 'type': 'bool'},
        'visible': {'key': 'visible', 'type': 'bool'},
        'watermark': {'key': 'watermark', 'type': 'str'}
    }

    def __init__(self, contribution=None, control_type=None, height=None, id=None, inherited=None, is_contribution=None, label=None, metadata=None, order=None, overridden=None, read_only=None, visible=None, watermark=None):
        super(Control, self).__init__()
        self.contribution = contribution
        self.control_type = control_type
        self.height = height
        self.id = id
        self.inherited = inherited
        self.is_contribution = is_contribution
        self.label = label
        self.metadata = metadata
        self.order = order
        self.overridden = overridden
        self.read_only = read_only
        self.visible = visible
        self.watermark = watermark
