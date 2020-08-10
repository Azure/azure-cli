# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AadOauthTokenRequest(Model):
    """AadOauthTokenRequest.

    :param refresh:
    :type refresh: bool
    :param resource:
    :type resource: str
    :param tenant_id:
    :type tenant_id: str
    :param token:
    :type token: str
    """

    _attribute_map = {
        'refresh': {'key': 'refresh', 'type': 'bool'},
        'resource': {'key': 'resource', 'type': 'str'},
        'tenant_id': {'key': 'tenantId', 'type': 'str'},
        'token': {'key': 'token', 'type': 'str'}
    }

    def __init__(self, refresh=None, resource=None, tenant_id=None, token=None):
        super(AadOauthTokenRequest, self).__init__()
        self.refresh = refresh
        self.resource = resource
        self.tenant_id = tenant_id
        self.token = token
