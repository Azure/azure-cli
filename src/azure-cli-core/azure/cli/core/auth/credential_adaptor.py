# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
from knack.log import get_logger
from knack.util import CLIError

from .util import resource_to_scopes

logger = get_logger(__name__)


class CredentialAdaptor:
    """Adaptor to both
      - Track 1: msrest.authentication.Authentication, which exposes signed_session
      - Track 2: azure.core.credentials.TokenCredential, which exposes get_token
    """

    def __init__(self, credential, resource=None, external_credentials=None):
        self._credential = credential
        # _external_credentials and _resource are only needed in Track1 SDK
        self._external_credentials = external_credentials
        self._resource = resource

    def _get_token(self, scopes=None, **kwargs):
        external_tenant_tokens = []
        # If scopes is not provided, use CLI-managed resource
        scopes = scopes or resource_to_scopes(self._resource)
        try:
            token = self._credential.get_token(*scopes, **kwargs)
            if self._external_credentials:
                external_tenant_tokens = [cred.get_token(*scopes) for cred in self._external_credentials]
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
        if self._external_credentials:
            return [cred.get_token(*scopes, **kwargs) for cred in self._external_credentials]
        return None

    @staticmethod
    def _log_hostname():
        import socket
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())


def _normalize_scopes(scopes):
    """Normalize scopes to workaround some SDK issues."""

    # Track 2 SDKs generated before https://github.com/Azure/autorest.python/pull/239 don't maintain
    # credential_scopes and call `get_token` with empty scopes.
    # As a workaround, return None so that the CLI-managed resource is used.
    if not scopes:
        logger.debug("No scope is provided by the SDK, use the CLI-managed resource.")
        return None

    # Track 2 SDKs generated before https://github.com/Azure/autorest.python/pull/745 extend default
    # credential_scopes with custom credential_scopes. Instead, credential_scopes should be replaced by
    # custom credential_scopes. https://github.com/Azure/azure-sdk-for-python/issues/12947
    # As a workaround, remove the first one if there are multiple scopes provided.
    if len(scopes) > 1:
        logger.debug("Multiple scopes are provided by the SDK, discarding the first one: %s", scopes[0])
        return scopes[1:]

    return scopes
