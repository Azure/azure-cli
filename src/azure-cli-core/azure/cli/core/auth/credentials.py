# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials to acquire tokens from MSAL.
"""

from knack.log import get_logger

logger = get_logger(__name__)


class AccessTokenCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, access_token):
        self.access_token = access_token

    def acquire_token(self, scopes, **kwargs):
        logger.debug("AccessTokenCredential.acquire_token: scopes=%r, kwargs=%r", scopes, kwargs)
        return {
            'access_token': self.access_token,
            # The caller is responsible for providing a valid token
            'expires_in': 3600
        }
