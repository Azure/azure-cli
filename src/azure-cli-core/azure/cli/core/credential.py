# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Tuple, List

import json
import requests
from azure.cli.core._identity import resource_to_scopes
from azure.cli.core.util import in_cloud_console
from azure.core.credentials import AccessToken
from azure.identity import CredentialUnavailableError, AuthenticationRequiredError

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def _convert_token_entry(token):
    import datetime
    return {'accessToken': token.token,
            'expiresOn': datetime.datetime.fromtimestamp(token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")}


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
        except CLIError as err:
            if in_cloud_console():
                CredentialAdaptor._log_hostname()
            raise err
        except AuthenticationRequiredError as err:
            err_dict = json.loads(err.response.text())
            aad_error_handler(err_dict, scopes=err.scopes, claims=err.claims)
        except CredentialUnavailableError as err:
            err_dict = json.loads(err.response.text())
            aad_error_handler(err_dict)
        except requests.exceptions.SSLError as err:
            from .util import SSLERROR_TEMPLATE
            raise CLIError(SSLERROR_TEMPLATE.format(str(err)))
        except requests.exceptions.ConnectionError as err:
            raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))

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

    def get_all_tokens(self, *scopes):
        # type: (*str) -> Tuple[AccessToken, List[AccessToken]]
        # TODO: Track 2 SDK should support external credentials.
        return self._get_token(scopes)

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


def _generate_login_command(scopes=None, claims=None):
    login_command = ['az login']

    if scopes:
        login_command.append('--scope {}'.format(' '.join(scopes)))

    if claims:
        import base64
        try:
            base64.urlsafe_b64decode(claims)
            is_base64 = True
        except ValueError:
            is_base64 = False

        if not is_base64:
            claims = base64.urlsafe_b64encode(claims.encode()).decode()

        login_command.append('--claims {}'.format(claims))

    return ' '.join(login_command)


def _generate_login_message(**kwargs):
    login_command = _generate_login_command(**kwargs)
    login_command = 'az logout\naz login'
    msg = "To re-authenticate, please {}" \
          "If the problem persists, please contact your tenant administrator.".format(
              "refresh Azure Portal." if in_cloud_console() else "run:\n{}\n".format(login_command))

    return msg


def aad_error_handler(error, scopes=None, claims=None):
    """ Handle the error from AAD server returned by ADAL or MSAL. """

    # https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error
    msg = error.get('error_description')
    login_message = _generate_login_message(scopes=scopes, claims=claims)

    from azure.cli.core.azclierror import AuthenticationError
    raise AuthenticationError(msg, recommendation=login_message)
