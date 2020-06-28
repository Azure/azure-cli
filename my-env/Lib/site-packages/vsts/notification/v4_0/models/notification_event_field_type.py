# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class NotificationEventFieldType(Model):
    """NotificationEventFieldType.

    :param id: Gets or sets the unique identifier of this field type.
    :type id: str
    :param operator_constraints:
    :type operator_constraints: list of :class:`OperatorConstraint <notification.v4_0.models.OperatorConstraint>`
    :param operators: Gets or sets the list of operators that this type supports.
    :type operators: list of :class:`NotificationEventFieldOperator <notification.v4_0.models.NotificationEventFieldOperator>`
    :param subscription_field_type:
    :type subscription_field_type: object
    :param value: Gets or sets the value definition of this field like the getValuesMethod and template to display in the UI
    :type value: :class:`ValueDefinition <notification.v4_0.models.ValueDefinition>`
    """

    _attribute_map = {
        'id': {'key': 'id', 'type': 'str'},
        'operator_constraints': {'key': 'operatorConstraints', 'type': '[OperatorConstraint]'},
        'operators': {'key': 'operators', 'type': '[NotificationEventFieldOperator]'},
        'subscription_field_type': {'key': 'subscriptionFieldType', 'type': 'object'},
        'value': {'key': 'value', 'type': 'ValueDefinition'}
    }

    def __init__(self, id=None, operator_constraints=None, operators=None, subscription_field_type=None, value=None):
        super(NotificationEventFieldType, self).__init__()
        self.id = id
        self.operator_constraints = operator_constraints
        self.operators = operators
        self.subscription_field_type = subscription_field_type
        self.value = value
