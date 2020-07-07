# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class OAuthConfigurationParams(Model):
    """OAuthConfigurationParams.

    :param client_id: Gets or sets the ClientId
    :type client_id: str
    :param client_secret: Gets or sets the ClientSecret
    :type client_secret: str
    :param endpoint_type: Gets or sets the type of the endpoint.
    :type endpoint_type: str
    :param name: Gets or sets the name
    :type name: str
    :param url: Gets or sets the Url
    :type url: str
    """

    _attribute_map = {
        'client_id': {'key': 'clientId', 'type': 'str'},
        'client_secret': {'key': 'clientSecret', 'type': 'str'},
        'endpoint_type': {'key': 'endpointType', 'type': 'str'},
        'name': {'key': 'name', 'type': 'str'},
        'url': {'key': 'url', 'type': 'str'}
    }

    def __init__(self, client_id=None, client_secret=None, endpoint_type=None, name=None, url=None):
        super(OAuthConfigurationParams, self).__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.endpoint_type = endpoint_type
        self.name = name
        self.url = url
