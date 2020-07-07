# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class Condition(Model):
    """Condition.

    :param condition_type: Gets or sets the condition type.
    :type condition_type: object
    :param name: Gets or sets the name of the condition. e.g. 'ReleaseStarted'.
    :type name: str
    :param value: Gets or set value of the condition.
    :type value: str
    """

    _attribute_map = {
        'condition_type': {'key': 'conditionType', 'type': 'object'},
        'name': {'key': 'name', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, condition_type=None, name=None, value=None):
        super(Condition, self).__init__()
        self.condition_type = condition_type
        self.name = name
        self.value = value
