# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class InputValuesQuery(Model):
    """InputValuesQuery.

    :param current_values:
    :type current_values: dict
    :param input_values: The input values to return on input, and the result from the consumer on output.
    :type input_values: list of :class:`InputValues <microsoft.-visual-studio.-services.-web-api.v4_1.models.InputValues>`
    :param resource: Subscription containing information about the publisher/consumer and the current input values
    :type resource: object
    """

    _attribute_map = {
        'current_values': {'key': 'currentValues', 'type': '{str}'},
        'input_values': {'key': 'inputValues', 'type': '[InputValues]'},
        'resource': {'key': 'resource', 'type': 'object'}
    }

    def __init__(self, current_values=None, input_values=None, resource=None):
        super(InputValuesQuery, self).__init__()
        self.current_values = current_values
        self.input_values = input_values
        self.resource = resource
