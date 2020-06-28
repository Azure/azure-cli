# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ValidationItem(Model):
    """ValidationItem.

    :param is_valid: Tells whether the current input is valid or not
    :type is_valid: bool
    :param reason: Reason for input validation failure
    :type reason: str
    :param type: Type of validation item
    :type type: str
    :param value: Value to validate. The conditional expression to validate for the input for "expression" type Eg:eq(variables['Build.SourceBranch'], 'refs/heads/master');eq(value, 'refs/heads/master')
    :type value: str
    """

    _attribute_map = {
        'is_valid': {'key': 'isValid', 'type': 'bool'},
        'reason': {'key': 'reason', 'type': 'str'},
        'type': {'key': 'type', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, is_valid=None, reason=None, type=None, value=None):
        super(ValidationItem, self).__init__()
        self.is_valid = is_valid
        self.reason = reason
        self.type = type
        self.value = value
