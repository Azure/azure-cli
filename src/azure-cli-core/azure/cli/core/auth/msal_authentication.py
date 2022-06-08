# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials defined in this module are alternative implementations of credentials provided by Azure Identity.

These credentials implement azure.core.credentials.TokenCredential by exposing get_token method for Track 2
SDK invocation.
"""

from knack.log import get_logger
from knack.util import CLIError
from msal import PublicClientApplication, ConfidentialClientApplication

from .util import check_result, build_sdk_access_token

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

    def __init__(self, client_id, username, **kwargs):
        """User credential implementing get_token interface.

        :param client_id: Client ID of the CLI.
        :param username: The username for user credential.
        """
        super().__init__(client_id, allow_broker=True, **kwargs)

        # Make sure username is specified, otherwise MSAL returns all accounts
        assert username, "username must be specified, got {!r}".format(username)

        accounts = self.get_accounts(username)

        # Usernames are usually unique. We are collecting corner cases to better understand its behavior.
        if len(accounts) > 1:
            raise CLIError(f"Found multiple accounts with the same username '{username}': {accounts}\n"
                           "Please report to us via Github: https://github.com/Azure/azure-cli/issues/20168")

        if not accounts:
            raise CLIError("User '{}' does not exist in MSAL token cache. Run `az login`.".format(username))

        self._account = accounts[0]

    def get_token(self, *scopes, **kwargs):
        # scopes = ['https://pas.windows.net/CheckMyAccess/Linux/.default']
        logger.debug("UserCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        result = self.acquire_token_silent_with_error(list(scopes), self._account, **kwargs)

        from azure.cli.core.azclierror import AuthenticationError
        try:
            # Check if an access token is returned.
            check_result(result, scopes=scopes)
        except AuthenticationError as ex:
            # For VM SSH ('data' is passed), if getting access token fails because
            # Conditional Access MFA step-up or compliance check is required, re-launch
            # web browser and do auth code flow again.
            # We assume the `az ssh` command is run on a system with GUI where a web
            # browser is available.
            if 'data' in kwargs:
                logger.warning(ex)
                logger.warning("\nThe default web browser has been opened at %s for scope '%s'. "
                               "Please continue the login in the web browser.",
                               self.authority.authorization_endpoint, ' '.join(scopes))

                from .util import read_response_templates
                success_template, error_template = read_response_templates()

                result = self.acquire_token_interactive(
                    list(scopes), login_hint=self._account['username'], port=8400 if self.authority.is_adfs else None,
                    success_template=success_template, error_template=error_template, **kwargs)
                check_result(result)

            # For other scenarios like Storage Conditional Access MFA step-up, do not
            # launch browser, but show the error message and `az login` command instead.
            else:
                raise
        return build_sdk_access_token(result)


class ServicePrincipalCredential(ConfidentialClientApplication):

    def __init__(self, service_principal_auth, **kwargs):
        """Service principal credential implementing get_token interface.

        :param service_principal_auth: An instance of ServicePrincipalAuth.
        """
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
        return build_sdk_access_token(result)
