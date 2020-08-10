# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ExpressionFilterClause(Model):
    """ExpressionFilterClause.

    :param field_name:
    :type field_name: str
    :param index: The order in which this clause appeared in the filter query
    :type index: int
    :param logical_operator: Logical Operator 'AND', 'OR' or NULL (only for the first clause in the filter)
    :type logical_operator: str
    :param operator:
    :type operator: str
    :param value:
    :type value: str
    """

    _attribute_map = {
        'field_name': {'key': 'fieldName', 'type': 'str'},
        'index': {'key': 'index', 'type': 'int'},
        'logical_operator': {'key': 'logicalOperator', 'type': 'str'},
        'operator': {'key': 'operator', 'type': 'str'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, field_name=None, index=None, logical_operator=None, operator=None, value=None):
        super(ExpressionFilterClause, self).__init__()
        self.field_name = field_name
        self.index = index
        self.logical_operator = logical_operator
        self.operator = operator
        self.value = value
