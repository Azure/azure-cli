# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TestResultDocument(Model):
    """TestResultDocument.

    :param operation_reference:
    :type operation_reference: :class:`TestOperationReference <test.v4_0.models.TestOperationReference>`
    :param payload:
    :type payload: :class:`TestResultPayload <test.v4_0.models.TestResultPayload>`
    """

    _attribute_map = {
        'operation_reference': {'key': 'operationReference', 'type': 'TestOperationReference'},
        'payload': {'key': 'payload', 'type': 'TestResultPayload'}
    }

    def __init__(self, operation_reference=None, payload=None):
        super(TestResultDocument, self).__init__()
        self.operation_reference = operation_reference
        self.payload = payload
