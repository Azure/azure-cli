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
from msal import PublicClientApplication, ConfidentialClientApplication

from .constants import AZURE_CLI_CLIENT_ID
from .util import check_result, build_sdk_access_token

logger = get_logger(__name__)


class UserCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, client_id, username, **kwargs):
        """User credential implementing get_token interface.

        :param client_id: Client ID of the CLI.
        :param username: The username for user credential.
        """
        self._msal_app = PublicClientApplication(client_id, **kwargs)

        # Make sure username is specified, otherwise MSAL returns all accounts
        assert username, "username must be specified, got {!r}".format(username)

        accounts = self._msal_app.get_accounts(username)

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
                           self._msal_app.authority.tenant, claims)
        result = self._msal_app.acquire_token_silent_with_error(list(scopes), self._account, claims_challenge=claims,
                                                                **kwargs)

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
                               self._msal_app.authority.authorization_endpoint, ' '.join(scopes))

                from .util import read_response_templates
                success_template, error_template = read_response_templates()

                result = self._msal_app.acquire_token_interactive(
                    list(scopes), login_hint=self._account['username'],
                    port=8400 if self._msal_app.authority.is_adfs else None,
                    success_template=success_template, error_template=error_template, **kwargs)
                check_result(result)

            # For other scenarios like Storage Conditional Access MFA step-up, do not
            # launch browser, but show the error message and `az login` command instead.
            else:
                raise
        return build_sdk_access_token(result)


class ServicePrincipalCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, client_id, client_credential, **kwargs):
        """Service principal credential implementing get_token interface.

        :param client_id: The service principal's client ID.
        :param client_credential: client_credential that will be passed to MSAL.
        """
        self._msal_app = ConfidentialClientApplication(client_id, client_credential, **kwargs)

    def get_token(self, *scopes, **kwargs):
        logger.debug("ServicePrincipalCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)

        result = self._msal_app.acquire_token_for_client(list(scopes), **kwargs)
        check_result(result)
        return build_sdk_access_token(result)


class CloudShellCredential:  # pylint: disable=too-few-public-methods
    # Cloud Shell acts as a "broker" to obtain access token for the user account, so even though it uses
    # managed identity protocol, it returns a user token.
    # That's why MSAL uses acquire_token_interactive to retrieve an access token in Cloud Shell.
    # See https://github.com/Azure/azure-cli/pull/29637

    def __init__(self):
        self._msal_app = PublicClientApplication(
            AZURE_CLI_CLIENT_ID,  # Use a real client_id, so that cache would work
            # TODO: We currently don't maintain an MSAL token cache as Cloud Shell already has its own token cache.
            #   Ideally we should also use an MSAL token cache.
            #   token_cache=...
        )

    def get_token(self, *scopes, **kwargs):
        logger.debug("CloudShellCredential.get_token: scopes=%r, kwargs=%r", scopes, kwargs)
        # kwargs is already sanitized by CredentialAdaptor, so it can be safely passed to MSAL
        result = self._msal_app.acquire_token_interactive(list(scopes), prompt="none", **kwargs)
        check_result(result, scopes=scopes)
        return build_sdk_access_token(result)
