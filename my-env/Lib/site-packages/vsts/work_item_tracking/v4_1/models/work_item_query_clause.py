# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class WorkItemQueryClause(Model):
    """WorkItemQueryClause.

    :param clauses: Child clauses if the current clause is a logical operator
    :type clauses: list of :class:`WorkItemQueryClause <work-item-tracking.v4_1.models.WorkItemQueryClause>`
    :param field: Field associated with condition
    :type field: :class:`WorkItemFieldReference <work-item-tracking.v4_1.models.WorkItemFieldReference>`
    :param field_value: Right side of the condition when a field to field comparison
    :type field_value: :class:`WorkItemFieldReference <work-item-tracking.v4_1.models.WorkItemFieldReference>`
    :param is_field_value: Determines if this is a field to field comparison
    :type is_field_value: bool
    :param logical_operator: Logical operator separating the condition clause
    :type logical_operator: object
    :param operator: The field operator
    :type operator: :class:`WorkItemFieldOperation <work-item-tracking.v4_1.models.WorkItemFieldOperation>`
    :param value: Right side of the condition when a field to value comparison
    :type value: str
    """

    _attribute_map = {
        'clauses': {'key': 'clauses', 'type': '[WorkItemQueryClause]'},
        'field': {'key': 'field', 'type': 'WorkItemFieldReference'},
        'field_value': {'key': 'fieldValue', 'type': 'WorkItemFieldReference'},
        'is_field_value': {'key': 'isFieldValue', 'type': 'bool'},
        'logical_operator': {'key': 'logicalOperator', 'type': 'object'},
        'operator': {'key': 'operator', 'type': 'WorkItemFieldOperation'},
        'value': {'key': 'value', 'type': 'str'}
    }

    def __init__(self, clauses=None, field=None, field_value=None, is_field_value=None, logical_operator=None, operator=None, value=None):
        super(WorkItemQueryClause, self).__init__()
        self.clauses = clauses
        self.field = field
        self.field_value = field_value
        self.is_field_value = is_field_value
        self.logical_operator = logical_operator
        self.operator = operator
        self.value = value
