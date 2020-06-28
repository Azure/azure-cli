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

    :param authorization_headers: Gets or sets the authorization headers of service endpoint authentication scheme.
    :type authorization_headers: list of :class:`AuthorizationHeader <task-agent.v4_1.models.AuthorizationHeader>`
    :param client_certificates: Gets or sets the certificates of service endpoint authentication scheme.
    :type client_certificates: list of :class:`ClientCertificate <task-agent.v4_1.models.ClientCertificate>`
    :param display_name: Gets or sets the display name for the service endpoint authentication scheme.
    :type display_name: str
    :param input_descriptors: Gets or sets the input descriptors for the service endpoint authentication scheme.
    :type input_descriptors: list of :class:`InputDescriptor <task-agent.v4_1.models.InputDescriptor>`
    :param scheme: Gets or sets the scheme for service endpoint authentication.
    :type scheme: str
    """

    _attribute_map = {
        'authorization_headers': {'key': 'authorizationHeaders', 'type': '[AuthorizationHeader]'},
        'client_certificates': {'key': 'clientCertificates', 'type': '[ClientCertificate]'},
        'display_name': {'key': 'displayName', 'type': 'str'},
        'input_descriptors': {'key': 'inputDescriptors', 'type': '[InputDescriptor]'},
        'scheme': {'key': 'scheme', 'type': 'str'}
    }

    def __init__(self, authorization_headers=None, client_certificates=None, display_name=None, input_descriptors=None, scheme=None):
        super(ServiceEndpointAuthenticationScheme, self).__init__()
        self.authorization_headers = authorization_headers
        self.client_certificates = client_certificates
        self.display_name = display_name
        self.input_descriptors = input_descriptors
        self.scheme = scheme
