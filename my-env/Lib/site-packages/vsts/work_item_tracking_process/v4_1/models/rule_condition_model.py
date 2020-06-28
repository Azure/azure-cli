# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class RuleConditionModel(Model):
    """RuleConditionModel.

    :param condition_type:
    :type condition_type: str
    :param field:
    :type field: str
    :param value:
    :type value: str
    """

    _attribute_map = {
        'condition_type': {'key': 'conditionType', 'type': 'str'},
        'field': {'key': 'field', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, condition_type=None, field=None, value=None):
        super(RuleConditionModel, self).__init__()
        self.condition_type = condition_type
        self.field = field
        self.value = value
