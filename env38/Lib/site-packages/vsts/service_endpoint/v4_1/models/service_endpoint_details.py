# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointDetails(Model):
    """ServiceEndpointDetails.

    :param authorization: Gets or sets the authorization of service endpoint.
    :type authorization: :class:`EndpointAuthorization <service-endpoint.v4_1.models.EndpointAuthorization>`
    :param data: Gets or sets the data of service endpoint.
    :type data: dict
    :param type: Gets or sets the type of service endpoint.
    :type type: str
    :param url: Gets or sets the connection url of service endpoint.
    :type url: str
    """

    _attribute_map = {
        'authorization': {'key': 'authorization', 'type': 'EndpointAuthorization'},
        'data': {'key': 'data', 'type': '{str}'},
        'type': {'key': 'type', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, authorization=None, data=None, type=None, url=None):
        super(ServiceEndpointDetails, self).__init__()
        self.authorization = authorization
        self.data = data
        self.type = type
        self.url = url
