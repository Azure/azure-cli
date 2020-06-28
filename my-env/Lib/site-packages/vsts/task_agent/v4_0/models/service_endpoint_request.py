# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointRequest(Model):
    """ServiceEndpointRequest.

    :param data_source_details:
    :type data_source_details: :class:`DataSourceDetails <task-agent.v4_0.models.DataSourceDetails>`
    :param result_transformation_details:
    :type result_transformation_details: :class:`ResultTransformationDetails <task-agent.v4_0.models.ResultTransformationDetails>`
    :param service_endpoint_details:
    :type service_endpoint_details: :class:`ServiceEndpointDetails <task-agent.v4_0.models.ServiceEndpointDetails>`
    """

    _attribute_map = {
        'data_source_details': {'key': 'dataSourceDetails', 'type': 'DataSourceDetails'},
        'result_transformation_details': {'key': 'resultTransformationDetails', 'type': 'ResultTransformationDetails'},
        'service_endpoint_details': {'key': 'serviceEndpointDetails', 'type': 'ServiceEndpointDetails'}
    }

    def __init__(self, data_source_details=None, result_transformation_details=None, service_endpoint_details=None):
        super(ServiceEndpointRequest, self).__init__()
        self.data_source_details = data_source_details
        self.result_transformation_details = result_transformation_details
        self.service_endpoint_details = service_endpoint_details
