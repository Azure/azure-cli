# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class DataSource(Model):
    """DataSource.

    :param authentication_scheme:
    :type authentication_scheme: :class:`AuthenticationSchemeReference <service-endpoint.v4_1.models.AuthenticationSchemeReference>`
    :param endpoint_url:
    :type endpoint_url: str
    :param headers:
    :type headers: list of :class:`AuthorizationHeader <service-endpoint.v4_1.models.AuthorizationHeader>`
    :param name:
    :type name: str
    :param resource_url:
    :type resource_url: str
    :param result_selector:
    :type result_selector: str
    """

    _attribute_map = {
        'authentication_scheme': {'key': 'authenticationScheme', 'type': 'AuthenticationSchemeReference'},
        'endpoint_url': {'key': 'endpointUrl', 'type': 'str'},
        'headers': {'key': 'headers', 'type': '[AuthorizationHeader]'},
        'name': {'key': 'name', 'type': 'str'},
        'resource_url': {'key': 'resourceUrl', 'type': 'str'},
        'result_selector': {'key': 'resultSelector', 'type': 'str'}
    }

    def __init__(self, authentication_scheme=None, endpoint_url=None, headers=None, name=None, resource_url=None, result_selector=None):
        super(DataSource, self).__init__()
        self.authentication_scheme = authentication_scheme
        self.endpoint_url = endpoint_url
        self.headers = headers
        self.name = name
        self.resource_url = resource_url
        self.result_selector = result_selector
