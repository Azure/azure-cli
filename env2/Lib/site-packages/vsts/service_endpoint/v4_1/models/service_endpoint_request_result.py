# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointRequestResult(Model):
    """ServiceEndpointRequestResult.

    :param error_message: Gets or sets the error message of the service endpoint request result.
    :type error_message: str
    :param result: Gets or sets the result of service endpoint request.
    :type result: :class:`object <service-endpoint.v4_1.models.object>`
    :param status_code: Gets or sets the status code of the service endpoint request result.
    :type status_code: object
    """

    _attribute_map = {
        'error_message': {'key': 'errorMessage', 'type': 'str'},
        'result': {'key': 'result', 'type': 'object'},
        'status_code': {'key': 'statusCode', 'type': 'object'}
    }

    def __init__(self, error_message=None, result=None, status_code=None):
        super(ServiceEndpointRequestResult, self).__init__()
        self.error_message = error_message
        self.result = result
        self.status_code = status_code
