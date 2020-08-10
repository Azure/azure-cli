# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ServiceEndpointAuthenticationScheme(Model):
    """ServiceEndpointAuthenticationScheme.

    :param authorization_headers:
    :type authorization_headers: list of :class:`AuthorizationHeader <task-agent.v4_0.models.AuthorizationHeader>`
    :param display_name:
    :type display_name: str
    :param input_descriptors:
    :type input_descriptors: list of :class:`InputDescriptor <task-agent.v4_0.models.InputDescriptor>`
    :param scheme:
    :type scheme: str
    """

    _attribute_map = {
        'authorization_headers': {'key': 'authorizationHeaders', 'type': '[AuthorizationHeader]'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'scheme': {'key': 'scheme', 'type': 'str'}
    }

    def __init__(self, authorization_headers=None, display_name=None, input_descriptors=None, scheme=None):
        super(ServiceEndpointAuthenticationScheme, self).__init__()
        self.authorization_headers = authorization_headers
        self.display_name = display_name
        self.input_descriptors = input_descriptors
        self.scheme = scheme
