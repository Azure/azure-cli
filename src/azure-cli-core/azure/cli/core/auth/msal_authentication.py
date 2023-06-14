# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials defined in this module are alternative implementations of credentials provided by Azure Identity.

These credentials implement azure.core.credentials.TokenCredential by exposing `get_token` method for Track 2
SDK invocation.

If you want to implement your own credential, the credential must also expose `get_token` method.

`get_token` method takes `scopes` as positional arguments and other optional `kwargs`, such as `claims`, `data`.
The return value should be a named tuple containing two elements: token (str), expires_on (int). You may simply use
azure.cli.core.auth.util.AccessToken to build the return value. See below credentials as examples.
"""

from knack.log import get_logger
from knack.util import CLIError
from msal import PublicClientApplication, ConfidentialClientApplication, ManagedIdentity

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
        super().__init__(client_id, **kwargs)

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

    def get_token(self, *scopes, claims=None, **kwargs):
        # scopes = ['https://pas.windows.net/CheckMyAccess/Linux/.default']
        logger.debug("UserCredential.get_token: scopes=%r, claims=%r, kwargs=%r", scopes, claims, kwargs)

        if claims:
            logger.warning('Acquiring new access token silently for tenant %s with claims challenge: %s',
                           self.authority.tenant, claims)
        result = self.acquire_token_silent_with_error(list(scopes), self._account, claims_challenge=claims, **kwargs)

        from azure.cli.core.azclierror import AuthenticationError
        try:
            # Check if an access token is returned.
            check_result(result, scopes=scopes, claims=claims)
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


class ManagedIdentityCredential(ManagedIdentity):

    def __init__(self, client_id=None, object_id=None, mi_res_id=None):
        import requests
        super().__init__(requests.Session(), client_id=client_id, object_id=object_id, mi_res_id=mi_res_id)

    def get_token(self, *scopes, **kwargs):
        logger.debug("ManagedIdentityCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        from .util import scopes_to_resource
        result = self.acquire_token(scopes_to_resource(scopes))
        check_result(result)
        return build_sdk_access_token(result)


class CloudShellCredential:  # pylint: disable=too-few-public-methods

    def __init__(self):
        from .identity import AZURE_CLI_CLIENT_ID
        self.msal_app = PublicClientApplication(
            AZURE_CLI_CLIENT_ID,  # Use a real client_id, so that cache would work
            # TODO: This PoC does not currently maintain a token cache;
            #   Ideally we should reuse the real MSAL app object which has cache configured.
            # token_cache=...,
        )

    def get_token(self, *scopes, **kwargs):  # pylint: disable=no-self-use
        logger.debug("CloudShellCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)
        if 'data' in kwargs:
            # Get a VM SSH certificate
            result = self.msal_app.acquire_token_interactive(list(scopes), prompt="none", data=kwargs["data"])
        else:
            # Get an access token
            result = self.msal_app.acquire_token_interactive(list(scopes), prompt="none")
        check_result(result, scopes=scopes)
        return build_sdk_access_token(result)
