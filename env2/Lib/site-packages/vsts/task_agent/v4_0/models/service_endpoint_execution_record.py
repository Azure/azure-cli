# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointExecutionRecord(Model):
    """ServiceEndpointExecutionRecord.

    :param data:
    :type data: :class:`ServiceEndpointExecutionData <task-agent.v4_0.models.ServiceEndpointExecutionData>`
    :param endpoint_id:
    :type endpoint_id: str
    """

    _attribute_map = {
        'data': {'key': 'data', 'type': 'ServiceEndpointExecutionData'},
        'endpoint_id': {'key': 'endpointId', 'type': 'str'}
    }

    def __init__(self, data=None, endpoint_id=None):
        super(ServiceEndpointExecutionRecord, self).__init__()
        self.data = data
        self.endpoint_id = endpoint_id
