# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InputFilterCondition(Model):
    """InputFilterCondition.

    :param case_sensitive: Whether or not to do a case sensitive match
    :type case_sensitive: bool
    :param input_id: The Id of the input to filter on
    :type input_id: str
    :param input_value: The "expected" input value to compare with the actual input value
    :type input_value: str
    :param operator: The operator applied between the expected and actual input value
    :type operator: object
    """

    _attribute_map = {
        'case_sensitive': {'key': 'caseSensitive', 'type': 'bool'},
        'input_id': {'key': 'inputId', 'type': 'str'},
        'input_value': {'key': 'inputValue', 'type': 'str'},
        'operator': {'key': 'operator', 'type': 'object'}
    }

    def __init__(self, case_sensitive=None, input_id=None, input_value=None, operator=None):
        super(InputFilterCondition, self).__init__()
        self.case_sensitive = case_sensitive
        self.input_id = input_id
        self.input_value = input_value
        self.operator = operator
