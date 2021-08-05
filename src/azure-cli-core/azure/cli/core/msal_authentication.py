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

from knack.log import get_logger
from msal import PublicClientApplication, ConfidentialClientApplication

logger = get_logger(__name__)


class UserCredential(PublicClientApplication):

    def get_token(self, scopes, **kwargs):
        raise NotImplementedError


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

    def get_token(self, scopes, **kwargs):
        logger.debug("ServicePrincipalCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)
        return self.acquire_token_for_client(scopes=scopes, **kwargs)
