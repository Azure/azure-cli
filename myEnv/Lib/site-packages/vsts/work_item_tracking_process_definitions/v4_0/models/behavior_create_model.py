# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class BehaviorCreateModel(Model):
    """BehaviorCreateModel.

    :param color: Color
    :type color: str
    :param inherits: Parent behavior id
    :type inherits: str
    :param name: Name of the behavior
    :type name: str
    """

    _attribute_map = {
        'color': {'key': 'color', 'type': 'str'},
        'inherits': {'key': 'inherits', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'}
    }

    def __init__(self, color=None, inherits=None, name=None):
        super(BehaviorCreateModel, self).__init__()
        self.color = color
        self.inherits = inherits
        self.name = name
