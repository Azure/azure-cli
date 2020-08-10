# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from .authorization_grant import AuthorizationGrant


class RefreshTokenGrant(AuthorizationGrant):
    """RefreshTokenGrant.

    :param grant_type:
    :type grant_type: object
    :param jwt:
    :type jwt: :class:`JsonWebToken <microsoft.-visual-studio.-services.-web-api.v4_0.models.JsonWebToken>`
    """

    _attribute_map = {
        'grant_type': {'key': 'grantType', 'type': 'object'},
        'jwt': {'key': 'jwt', 'type': 'JsonWebToken'}
    }

    def __init__(self, grant_type=None, jwt=None):
        super(RefreshTokenGrant, self).__init__(grant_type=grant_type)
        self.jwt = jwt
