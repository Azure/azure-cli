# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
from knack.log import get_logger
from knack.util import CLIError

from .util import resource_to_scopes, _normalize_scopes, build_sdk_access_token

logger = get_logger(__name__)

ACCESS_TOKEN = "access_token"


class CredentialAdaptor:
    def __init__(self, credential, resource=None, auxiliary_credentials=None):
        """
        Credential adaptor for bridging MSAL credential with SDK credential.

        It supports 2 version of SDKs:
        - Track 1: msrest.authentication.Authentication, which exposes signed_session
        - Track 2: azure.core.credentials.TokenCredential, which exposes get_token

        :param credential: MSAL credential from ._msal_credentials
        :param resource: AAD resource for Track 1 only
        :param auxiliary_credentials: MSAL credentials from ._msal_credentials for cross-tenant authentication.
            Details about cross-tenant authentication:
            https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/authenticate-multi-tenant
        """

        self._credential = credential
        self._auxiliary_credentials = auxiliary_credentials
        self._resource = resource

    def signed_session(self, session=None):
        """Protocol for Track 1 SDK token acquisition.
        It should be dropped once Track 1 SDK support is dropped.
        """
        logger.debug("CredentialAdaptor.signed_session")
        session = session or requests.Session()

        scopes = resource_to_scopes(self._resource)

        # Authorization header
        token = self._credential.acquire_token(scopes)
        authorization_value = "{} {}".format('Bearer', token[ACCESS_TOKEN])
        session.headers['Authorization'] = authorization_value

        # x-ms-authorization-auxiliary header
        if self._auxiliary_credentials:
            external_tenant_tokens = [cred.acquire_token(scopes) for cred in self._auxiliary_credentials]
            authorization_aux_value = ';'.join(
                ['{} {}'.format('Bearer', t[ACCESS_TOKEN]) for t in external_tenant_tokens])
            session.headers['x-ms-authorization-auxiliary'] = authorization_aux_value

        return session

    def get_token(self, *scopes, **kwargs):
        """Protocol for Track 2 SDK token acquisition.

        :returns: AccessToken
        """
        logger.debug("CredentialAdaptor.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        # SDK azure-keyvault-keys 4.5.0b5 passes tenant_id as kwargs, but we don't support tenant_id for now,
        # so discard it.
        kwargs.pop('tenant_id', None)

        scopes = _normalize_scopes(scopes)
        msal_token = self._credential.acquire_token(list(scopes), **kwargs)
        return build_sdk_access_token(msal_token)

    def get_auxiliary_tokens(self, *scopes, **kwargs):
        """A workaround to support cross-tenant authentication. It should only be called by a client factory.
        The result is fed into x-ms-authorization-auxiliary header.

        :returns: list[AccessToken]
        """
        # To test cross-tenant authentication, see https://github.com/Azure/azure-cli/issues/16691
        if self._auxiliary_credentials:
            return [build_sdk_access_token(cred.acquire_token(list(scopes), **kwargs))
                    for cred in self._auxiliary_credentials]
        return None

    def get_token_info(self, *scopes, options=None):
        """New protocol for Track 2 SDK token acquisition.
        """
        from azure.core.credentials import AccessTokenInfo
        msal_token = self._credential.acquire_token(list(scopes))
        import time
        return AccessTokenInfo(msal_token[ACCESS_TOKEN], int(time.time()) + msal_token["expires_in"])
