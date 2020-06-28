# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class ProxyAuthorization(Model):
    """ProxyAuthorization.

    :param authorization_url: Gets or sets the endpoint used to obtain access tokens from the configured token service.
    :type authorization_url: str
    :param client_id: Gets or sets the client identifier for this proxy.
    :type client_id: str
    :param identity: Gets or sets the user identity to authorize for on-prem.
    :type identity: :class:`str <core.v4_1.models.str>`
    :param public_key: Gets or sets the public key used to verify the identity of this proxy. Only specify on hosted.
    :type public_key: :class:`PublicKey <core.v4_1.models.PublicKey>`
    """

    _attribute_map = {
        'authorization_url': {'key': 'authorizationUrl', 'type': 'str'},
        'client_id': {'key': 'clientId', 'type': 'str'},
        'identity': {'key': 'identity', 'type': 'str'},
        'public_key': {'key': 'publicKey', 'type': 'PublicKey'}
    }

    def __init__(self, authorization_url=None, client_id=None, identity=None, public_key=None):
        super(ProxyAuthorization, self).__init__()
        self.authorization_url = authorization_url
        self.client_id = client_id
        self.identity = identity
        self.public_key = public_key
