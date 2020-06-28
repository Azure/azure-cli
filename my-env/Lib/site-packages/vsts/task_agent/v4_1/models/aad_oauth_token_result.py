# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# Generated file, DO NOT EDIT
# Changes may cause incorrect behavior and will be lost if the code is regenerated.
# --------------------------------------------------------------------------------------------

from msrest.serialization import Model


class AadOauthTokenResult(Model):
    """AadOauthTokenResult.

    :param access_token:
    :type access_token: str
    :param refresh_token_cache:
    :type refresh_token_cache: str
    """

    _attribute_map = {
        'access_token': {'key': 'accessToken', 'type': 'str'},
        'refresh_token_cache': {'key': 'refreshTokenCache', 'type': 'str'}
    }

    def __init__(self, access_token=None, refresh_token_cache=None):
        super(AadOauthTokenResult, self).__init__()
        self.access_token = access_token
        self.refresh_token_cache = refresh_token_cache
