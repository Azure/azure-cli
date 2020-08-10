# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AccessTokenResult(Model):
    """AccessTokenResult.

    :param access_token:
    :type access_token: :class:`JsonWebToken <microsoft.-visual-studio.-services.-web-api.v4_1.models.JsonWebToken>`
    :param access_token_error:
    :type access_token_error: object
    :param authorization_id:
    :type authorization_id: str
    :param error_description:
    :type error_description: str
    :param has_error:
    :type has_error: bool
    :param refresh_token:
    :type refresh_token: :class:`RefreshTokenGrant <microsoft.-visual-studio.-services.-web-api.v4_1.models.RefreshTokenGrant>`
    :param token_type:
    :type token_type: str
    :param valid_to:
    :type valid_to: datetime
    """

    _attribute_map = {
        'access_token': {'key': 'accessToken', 'type': 'JsonWebToken'},
        'access_token_error': {'key': 'accessTokenError', 'type': 'object'},
        'authorization_id': {'key': 'authorizationId', 'type': 'str'},
        'error_description': {'key': 'errorDescription', 'type': 'str'},
        'has_error': {'key': 'hasError', 'type': 'bool'},
        'refresh_token': {'key': 'refreshToken', 'type': 'RefreshTokenGrant'},
        'token_type': {'key': 'tokenType', 'type': 'str'},
        'valid_to': {'key': 'validTo', 'type': 'iso-8601'}
    }

    def __init__(self, access_token=None, access_token_error=None, authorization_id=None, error_description=None, has_error=None, refresh_token=None, token_type=None, valid_to=None):
        super(AccessTokenResult, self).__init__()
        self.access_token = access_token
        self.access_token_error = access_token_error
        self.authorization_id = authorization_id
        self.error_description = error_description
        self.has_error = has_error
        self.refresh_token = refresh_token
        self.token_type = token_type
        self.valid_to = valid_to
