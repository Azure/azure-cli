# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials to acquire tokens from MSAL.
"""

from knack.log import get_logger
from knack.util import CLIError
from msal import PublicClientApplication, ConfidentialClientApplication

from .util import check_result

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

    def acquire_token(self, scopes, claims=None, **kwargs):
        # scopes must be a list.
        # For acquiring SSH certificate, scopes is ['https://pas.windows.net/CheckMyAccess/Linux/.default']
        logger.debug("UserCredential.acquire_token: scopes=%r, claims=%r, kwargs=%r", scopes, claims, kwargs)

        if claims:
            logger.warning('Acquiring new access token silently for tenant %s with claims challenge: %s',
                           self._msal_app.authority.tenant, claims)
        result = self._msal_app.acquire_token_silent_with_error(scopes, self._account, claims_challenge=claims,
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
                    scopes, login_hint=self._account['username'],
                    port=8400 if self._msal_app.authority.is_adfs else None,
                    success_template=success_template, error_template=error_template, **kwargs)
                check_result(result)

            # For other scenarios like Storage Conditional Access MFA step-up, do not
            # launch browser, but show the error message and `az login` command instead.
            else:
                raise
        return result


class ServicePrincipalCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, client_id, client_credential, **kwargs):
        """Service principal credential implementing get_token interface.

        :param client_id: The service principal's client ID.
        :param client_credential: client_credential that will be passed to MSAL.
        """
        self._msal_app = ConfidentialClientApplication(client_id, client_credential, **kwargs)

    def acquire_token(self, scopes, **kwargs):
        # scopes must be a list
        logger.debug("ServicePrincipalCredential.acquire_token: scopes=%r, kwargs=%r", scopes, kwargs)
        result = self._msal_app.acquire_token_for_client(scopes, **kwargs)
        check_result(result)
        return result
