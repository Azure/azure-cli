# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials defined in this module are alternative implementations of credentials provided by Azure Identity.

These credentials implements azure.core.credentials.TokenCredential by exposing get_token method for Track 2
SDK invocation.
"""

from azure.core.credentials import AccessToken
from knack.log import get_logger
from knack.util import CLIError
from msal import PublicClientApplication, ConfidentialClientApplication

from .util import check_result

# OAuth 2.0 client credentials flow parameter
# https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow
_TENANT = 'tenant'
_CLIENT_ID = 'client_id'
_CLIENT_SECRET = 'client_secret'
_CERTIFICATE = 'certificate'
_CLIENT_ASSERTION = 'client_assertion'
_USE_CERT_SN_ISSUER = 'use_cert_sn_issuer'

logger = get_logger(__name__)


class UserCredential(PublicClientApplication):

    def __init__(self, client_id, username=None, **kwargs):
        super().__init__(client_id, **kwargs)
        if username:
            accounts = self.get_accounts(username)

            if not accounts:
                raise CLIError("User {} doesn't exist in the credential cache. The user could have been logged out by "
                               "another application that uses Single Sign-On. "
                               "Please run `az login` to re-login.".format(username))

            if len(accounts) > 1:
                raise CLIError("Found multiple accounts with the same username. Please report to us via Github: "
                               "https://github.com/Azure/azure-cli/issues/new")

            account = accounts[0]
            self.account = account
        else:
            self.account = None

    def get_token(self, *scopes, **kwargs):
        # scopes = ['https://pas.windows.net/CheckMyAccess/Linux/.default']
        logger.debug("UserCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        result = self.acquire_token_silent_with_error(list(scopes), self.account, **kwargs)
        check_result(result, scopes=scopes)
        return _build_sdk_access_token(result)


class ServicePrincipalCredential(ConfidentialClientApplication):

    def __init__(self, service_principal_auth, **kwargs):

        client_credential = None

        # client_secret
        client_secret = getattr(service_principal_auth, _CLIENT_SECRET, None)
        if client_secret:
            client_credential = client_secret

        # certificate
        certificate = getattr(service_principal_auth, _CERTIFICATE, None)
        if certificate:
            client_credential = {
                "private_key": getattr(service_principal_auth, 'certificate_string'),
                "thumbprint": getattr(service_principal_auth, 'thumbprint')
            }
            public_certificate = getattr(service_principal_auth, 'public_certificate', None)
            if public_certificate:
                client_credential['public_certificate'] = public_certificate

        # client_assertion
        client_assertion = getattr(service_principal_auth, _CLIENT_ASSERTION, None)
        if client_assertion:
            client_credential = {'client_assertion': client_assertion}

        super().__init__(service_principal_auth.client_id, client_credential=client_credential, **kwargs)

    def get_token(self, *scopes, **kwargs):
        logger.debug("ServicePrincipalCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        scopes = list(scopes)
        result = self.acquire_token_silent(scopes, None, **kwargs)
        if not result:
            result = self.acquire_token_for_client(scopes, **kwargs)
        check_result(result)
        return _build_sdk_access_token(result)


def _build_sdk_access_token(token_entry):
    import time
    request_time = int(time.time())

    return AccessToken(token_entry["access_token"], request_time + token_entry["expires_in"])
