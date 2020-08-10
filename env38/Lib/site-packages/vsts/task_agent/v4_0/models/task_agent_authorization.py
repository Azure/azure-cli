# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class TaskAgentAuthorization(Model):
    """TaskAgentAuthorization.

    :param authorization_url: Gets or sets the endpoint used to obtain access tokens from the configured token service.
    :type authorization_url: str
    :param client_id: Gets or sets the client identifier for this agent.
    :type client_id: str
    :param public_key: Gets or sets the public key used to verify the identity of this agent.
    :type public_key: :class:`TaskAgentPublicKey <task-agent.v4_0.models.TaskAgentPublicKey>`
    """

    _attribute_map = {
        'authorization_url': {'key': 'authorizationUrl', 'type': 'str'},
        'client_id': {'key': 'clientId', 'type': 'str'},
        'public_key': {'key': 'publicKey', 'type': 'TaskAgentPublicKey'}
    }

    def __init__(self, authorization_url=None, client_id=None, public_key=None):
        super(TaskAgentAuthorization, self).__init__()
        self.authorization_url = authorization_url
        self.client_id = client_id
        self.public_key = public_key
