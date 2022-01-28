# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
from knack.log import get_logger
from knack.util import CLIError

from .util import resource_to_scopes, _normalize_scopes

logger = get_logger(__name__)


class CredentialAdaptor:
    def __init__(self, credential, resource=None, auxiliary_credentials=None):
        """
        Adaptor to both
        - Track 1: msrest.authentication.Authentication, which exposes signed_session
        - Track 2: azure.core.credentials.TokenCredential, which exposes get_token

        :param credential: Main credential from .msal_authentication
        :param resource: AAD resource for Track 1 only
        :param auxiliary_credentials: Credentials from .msal_authentication for cross tenant authentication.
            Details about cross tenant authentication:
            https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/authenticate-multi-tenant
        """

        self._credential = credential
        self._auxiliary_credentials = auxiliary_credentials
        self._resource = resource

    def _get_token(self, scopes=None, **kwargs):
        external_tenant_tokens = []
        # If scopes is not provided, use CLI-managed resource
        scopes = scopes or resource_to_scopes(self._resource)
        try:
            token = self._credential.get_token(*scopes, **kwargs)
            if self._auxiliary_credentials:
                external_tenant_tokens = [cred.get_token(*scopes) for cred in self._auxiliary_credentials]
            return token, external_tenant_tokens
        except requests.exceptions.SSLError as err:
            from azure.cli.core.util import SSLERROR_TEMPLATE
            raise CLIError(SSLERROR_TEMPLATE.format(str(err)))

    def signed_session(self, session=None):
        logger.debug("CredentialAdaptor.get_token")
        session = session or requests.Session()
        token, external_tenant_tokens = self._get_token()
        header = "{} {}".format('Bearer', token.token)
        session.headers['Authorization'] = header
        if external_tenant_tokens:
            aux_tokens = ';'.join(['{} {}'.format('Bearer', tokens2.token) for tokens2 in external_tenant_tokens])
            session.headers['x-ms-authorization-auxiliary'] = aux_tokens
        return session

    def get_token(self, *scopes, **kwargs):
        logger.debug("CredentialAdaptor.get_token: scopes=%r, kwargs=%r", scopes, kwargs)
        scopes = _normalize_scopes(scopes)
        token, _ = self._get_token(scopes, **kwargs)
        return token

    def get_auxiliary_tokens(self, *scopes, **kwargs):
        if self._auxiliary_credentials:
            return [cred.get_token(*scopes, **kwargs) for cred in self._auxiliary_credentials]
        return None
