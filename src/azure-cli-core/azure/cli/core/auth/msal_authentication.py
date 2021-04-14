# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials defined in this module are alternative implementations of credentials provided by Azure Identity.

These credentials implements azure.core.credentials.TokenCredential by exposing get_token method for Track 2
SDK invocation.
"""

import os

from azure.core.credentials import AccessToken
from knack.log import get_logger
from knack.util import CLIError
from msal import PublicClientApplication, ConfidentialClientApplication

from .util import aad_error_handler

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
        logger.debug("UserCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        result = self.acquire_token_silent_with_error(list(scopes), self.account, **kwargs)
        return _convert_to_sdk_access_token(result)


class ServicePrincipalCredential(ConfidentialClientApplication):

    def __init__(self, client_id, secret_or_certificate=None, **kwargs):

        # If certificate file path is provided, transfer it to MSAL input
        if os.path.isfile(secret_or_certificate):
            cert_file = secret_or_certificate
            with open(cert_file, 'r') as f:
                cert_str = f.read()

            # Compute the thumbprint
            from OpenSSL.crypto import load_certificate, FILETYPE_PEM
            cert = load_certificate(FILETYPE_PEM, cert_str)
            thumbprint = cert.digest("sha1").decode().replace(' ', '').replace(':', '')

            client_credential = {"private_key": cert_str, "thumbprint": thumbprint}
        else:
            client_credential = secret_or_certificate

        super().__init__(client_id, client_credential=client_credential, **kwargs)

    def get_token(self, *scopes, **kwargs):
        logger.debug("ServicePrincipalCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        result = self.acquire_token_for_client(list(scopes), **kwargs)
        return _convert_to_sdk_access_token(result)


def _convert_to_sdk_access_token(token_entry):
    import time
    request_time = int(time.time())

    if token_entry and "access_token" in token_entry and "expires_in" in token_entry:
        return AccessToken(token_entry["access_token"], request_time + int(token_entry["expires_in"]))
    else:
        aad_error_handler(token_entry)
