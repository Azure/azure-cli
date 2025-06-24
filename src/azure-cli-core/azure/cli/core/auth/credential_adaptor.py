# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from .util import build_sdk_access_token

logger = get_logger(__name__)


class CredentialAdaptor:
    def __init__(self, credential, auxiliary_credentials=None):
        """Credential adaptor between MSAL credential and SDK credential.
        It implements Track 2 SDK's azure.core.credentials.TokenCredential by exposing get_token.

        :param credential: MSAL credential from ._msal_credentials
        :param auxiliary_credentials: MSAL credentials for cross-tenant authentication.
            Details about cross-tenant authentication:
            https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/authenticate-multi-tenant
        """

        self._credential = credential
        self._auxiliary_credentials = auxiliary_credentials

    def get_token(self, *scopes, **kwargs):
        """Implement the old SDK token protocol azure.core.credentials.TokenCredential
        Return azure.core.credentials.AccessToken
        """
        logger.debug("CredentialAdaptor.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        msal_kwargs = _prepare_msal_kwargs(kwargs)
        msal_result = self._credential.acquire_token(list(scopes), **msal_kwargs)
        return build_sdk_access_token(msal_result)

    def get_token_info(self, *scopes, options=None):
        """Implement the new SDK token protocol azure.core.credentials.SupportsTokenInfo
        Return azure.core.credentials.AccessTokenInfo
        """
        logger.debug("CredentialAdaptor.get_token_info: scopes=%r, options=%r", scopes, options)

        msal_kwargs = _prepare_msal_kwargs(options)
        msal_result = self._credential.acquire_token(list(scopes), **msal_kwargs)
        return _build_sdk_access_token_info(msal_result)

    def get_auxiliary_tokens(self, *scopes, **kwargs):
        """Get access tokens from auxiliary credentials."""
        # To test cross-tenant authentication, see https://github.com/Azure/azure-cli/issues/16691
        if self._auxiliary_credentials:
            return [build_sdk_access_token(cred.acquire_token(list(scopes), **kwargs))
                    for cred in self._auxiliary_credentials]
        return None


def _prepare_msal_kwargs(options=None):
    # Preserve supported options and discard unsupported options (tenant_id, enable_cae).
    # Both get_token's kwargs and get_token_info's options are accepted as their schema is the same (at least for now).
    msal_kwargs = {}
    if options:
        # For VM SSH. 'data' support is a CLI-specific extension.
        # SDK doesn't support 'data': https://github.com/Azure/azure-sdk-for-python/pull/16397
        if 'data' in options:
            msal_kwargs['data'] = options['data']
        # For CAE
        if 'claims' in options:
            msal_kwargs['claims_challenge'] = options['claims']
    return msal_kwargs


def _build_sdk_access_token_info(token_entry):
    # MSAL token entry sample:
    # {
    #     'access_token': 'eyJ0eXAiOiJKV...',
    #     'token_type': 'Bearer',
    #     'expires_in': 1618,
    #     'token_source': 'cache'
    # }
    from .constants import ACCESS_TOKEN, EXPIRES_IN
    from .util import now_timestamp
    from azure.core.credentials import AccessTokenInfo

    return AccessTokenInfo(token_entry[ACCESS_TOKEN], now_timestamp() + token_entry[EXPIRES_IN])
