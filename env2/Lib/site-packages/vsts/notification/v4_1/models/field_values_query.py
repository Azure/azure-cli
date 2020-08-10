# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .input_values_query import InputValuesQuery


class FieldValuesQuery(InputValuesQuery):
    """FieldValuesQuery.

    :param current_values:
    :type current_values: dict
    :param resource: Subscription containing information about the publisher/consumer and the current input values
    :type resource: object
    :param input_values:
    :type input_values: list of :class:`FieldInputValues <notification.v4_1.models.FieldInputValues>`
    :param scope:
    :type scope: str
    """

    _attribute_map = {
        'current_values': {'key': 'currentValues', 'type': '{str}'},
        'resource': {'key': 'resource', 'type': 'object'},
        'input_values': {'key': 'inputValues', 'type': '[FieldInputValues]'},
        'scope': {'key': 'scope', 'type': 'str'}
    }

    def __init__(self, current_values=None, resource=None, input_values=None, scope=None):
        super(FieldValuesQuery, self).__init__(current_values=current_values, resource=resource)
        self.input_values = input_values
        self.scope = scope
