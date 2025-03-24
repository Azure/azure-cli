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
        """Get an access token from the main credential."""
        logger.debug("CredentialAdaptor.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        # Discard unsupported kwargs: tenant_id, enable_cae
        filtered_kwargs = {}
        if 'data' in kwargs:
            filtered_kwargs['data'] = kwargs['data']

        return build_sdk_access_token(self._credential.acquire_token(list(scopes), **filtered_kwargs))

    def get_auxiliary_tokens(self, *scopes, **kwargs):
        """Get access tokens from auxiliary credentials."""
        # To test cross-tenant authentication, see https://github.com/Azure/azure-cli/issues/16691
        if self._auxiliary_credentials:
            return [build_sdk_access_token(cred.acquire_token(list(scopes), **kwargs))
                    for cred in self._auxiliary_credentials]
        return None
