# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Credentials to acquire tokens from MSAL.
"""

from knack.log import get_logger
from knack.util import CLIError
from msal import (PublicClientApplication, ConfidentialClientApplication,
                  ManagedIdentityClient, SystemAssignedManagedIdentity, UserAssignedManagedIdentity)

from .constants import AZURE_CLI_CLIENT_ID
from .util import check_result

logger = get_logger(__name__)


class UserCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, client_id, username, **kwargs):
        """User credential wrapping msal.application.PublicClientApplication

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

    def acquire_token(self, scopes, claims_challenge=None, **kwargs):
        # scopes must be a list.
        # For acquiring SSH certificate, scopes is ['https://pas.windows.net/CheckMyAccess/Linux/.default']
        # kwargs is already sanitized by CredentialAdaptor, so it can be safely passed to MSAL
        logger.debug("UserCredential.acquire_token: scopes=%r, claims_challenge=%r, kwargs=%r",
                     scopes, claims_challenge, kwargs)

        if claims_challenge:
            logger.info('Acquiring new access token silently with claims challenge: %s', claims_challenge)
        result = self._msal_app.acquire_token_silent_with_error(
            scopes, self._account, claims_challenge=claims_challenge, **kwargs)

        from azure.cli.core.azclierror import AuthenticationError
        try:
            # Check if an access token is returned.
            check_result(result, tenant=self._msal_app.authority.tenant, scopes=scopes,
                         claims_challenge=claims_challenge)
        except AuthenticationError as ex:
            # For VM SSH ('data' is passed), if getting access token fails because
            # Conditional Access MFA step-up or compliance check is required, re-launch
            # web browser and do auth code flow again.
            # We assume the `az ssh` command is run on a system with GUI where a web
            # browser is available.
            if 'data' in kwargs:
                logger.warning(ex)
                result = self._acquire_token_interactive(scopes, **kwargs)
            # For other scenarios like Storage Conditional Access MFA step-up, do not
            # launch browser, but show the error message and `az login` command instead.
            else:
                raise
        return result

    def _acquire_token_interactive(self, scopes, **kwargs):
        from .util import read_response_templates
        success_template, error_template = read_response_templates()

        def _prompt_launching_ui(ui=None, **_):
            logger.warning(
                "Interactively acquiring token for scope '%s'. Continue the login in the %s.",
                ' '.join(scopes), 'web browser' if ui == 'browser' else 'pop-up window')

        result = self._msal_app.acquire_token_interactive(
            scopes, login_hint=self._account['username'],
            port=8400 if self._msal_app.authority.is_adfs else None,
            success_template=success_template, error_template=error_template,
            parent_window_handle=self._msal_app.CONSOLE_WINDOW_HANDLE,
            on_before_launching_ui=_prompt_launching_ui,
            **kwargs)
        check_result(result)
        return result


class ServicePrincipalCredential:  # pylint: disable=too-few-public-methods

    def __init__(self, client_id, client_credential, **kwargs):
        """Service principal credential wrapping msal.application.ConfidentialClientApplication.

        :param client_id: The service principal's client ID.
        :param client_credential: client_credential that will be passed to MSAL.
        """
        self._msal_app = ConfidentialClientApplication(client_id, client_credential=client_credential, **kwargs)

    def acquire_token(self, scopes, **kwargs):
        logger.debug("ServicePrincipalCredential.acquire_token: scopes=%r, kwargs=%r", scopes, kwargs)
        result = self._msal_app.acquire_token_for_client(scopes, **kwargs)
        check_result(result)
        return result


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

    def acquire_token(self, scopes, **kwargs):
        logger.debug("CloudShellCredential.acquire_token: scopes=%r, kwargs=%r", scopes, kwargs)
        result = self._msal_app.acquire_token_interactive(scopes, prompt="none", **kwargs)
        check_result(result, scopes=scopes)
        return result


class ManagedIdentityCredential:  # pylint: disable=too-few-public-methods
    """Managed identity credential implementing get_token interface.
    Currently, only Azure Arc's system-assigned managed identity is supported.
    """

    def __init__(self, client_id=None, resource_id=None, object_id=None):
        import requests
        if client_id or resource_id or object_id:
            managed_identity = UserAssignedManagedIdentity(
                client_id=client_id, resource_id=resource_id, object_id=object_id)
        else:
            managed_identity = SystemAssignedManagedIdentity()
        self._msal_client = ManagedIdentityClient(managed_identity, http_client=requests.Session())

    def acquire_token(self, scopes, **kwargs):
        logger.debug("ManagedIdentityCredential.acquire_token: scopes=%r, kwargs=%r", scopes, kwargs)

        from .util import scopes_to_resource
        result = self._msal_client.acquire_token_for_client(resource=scopes_to_resource(scopes))
        check_result(result)
        return result
