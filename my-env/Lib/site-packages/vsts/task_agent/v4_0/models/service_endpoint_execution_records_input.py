# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointExecutionRecordsInput(Model):
    """ServiceEndpointExecutionRecordsInput.

    :param data:
    :type data: :class:`ServiceEndpointExecutionData <task-agent.v4_0.models.ServiceEndpointExecutionData>`
    :param endpoint_ids:
    :type endpoint_ids: list of str
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': 'ServiceEndpointExecutionData'},
        'endpoint_ids': {'key': 'endpointIds', 'type': '[str]'}
    }

    def __init__(self, data=None, endpoint_ids=None):
        super(ServiceEndpointExecutionRecordsInput, self).__init__()
        self.data = data
        self.endpoint_ids = endpoint_ids
