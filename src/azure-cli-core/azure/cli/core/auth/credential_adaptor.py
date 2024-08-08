# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from .util import _normalize_scopes

logger = get_logger(__name__)


class CredentialAdaptor:
    def __init__(self, credential, auxiliary_credentials=None):
        """
        Cross-tenant credential adaptor. It takes a main credential and auxiliary credentials.

        It implements Track 2 SDK's azure.core.credentials.TokenCredential by exposing get_token.

        :param credential: Main credential from .msal_authentication
        :param auxiliary_credentials: Credentials from .msal_authentication for cross tenant authentication.
            Details about cross tenant authentication:
            https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/authenticate-multi-tenant
        """

        self._credential = credential
        self._auxiliary_credentials = auxiliary_credentials

    def get_token(self, *scopes, **kwargs):
        """Get an access token from the main credential."""
        logger.debug("CredentialAdaptor.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        # SDK azure-keyvault-keys 4.5.0b5 passes tenant_id as kwargs, but we don't support tenant_id for now,
        # so discard it.
        kwargs.pop('tenant_id', None)

        scopes = _normalize_scopes(scopes)
        return self._credential.get_token(*scopes, **kwargs)

    def get_auxiliary_tokens(self, *scopes, **kwargs):
        """Get access tokens from auxiliary credentials."""
        # To test cross-tenant authentication, see https://github.com/Azure/azure-cli/issues/16691
        if self._auxiliary_credentials:
            return [cred.get_token(*scopes, **kwargs) for cred in self._auxiliary_credentials]
        return None
