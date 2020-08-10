# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RuleActionModel(Model):
    """RuleActionModel.

    :param action_type:
    :type action_type: str
    :param target_field:
    :type target_field: str
    :param value:
    :type value: str
    """

    _attribute_map = {
        'action_type': {'key': 'actionType', 'type': 'str'},
        'target_field': {'key': 'targetField', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, action_type=None, target_field=None, value=None):
        super(RuleActionModel, self).__init__()
        self.action_type = action_type
        self.target_field = target_field
        self.value = value
