# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests

from azure.cli.core.util import in_cloud_console
from azure.cli.core._identity import adal_resource_to_msal_scopes
from azure.core.exceptions import ClientAuthenticationError

from knack.util import CLIError


def _convert_token_entry(token):
    import datetime
    return {'accessToken': token.token,
            'expiresOn': datetime.datetime.fromtimestamp(token.expires_on).strftime("%Y-%m-%d %H:%M:%S.%f")}


class CredentialAdaptor:
    """Adaptor to both
      - Track 1: msrest.authentication.Authentication, which exposes signed_session
      - Track 2: azure.core.credentials.TokenCredential, which exposes get_token
    """

    def __init__(self, credential, resource=None, scopes=None, external_credentials=None):
        self._credential = credential
        # _external_credentials and _resource are only needed in Track1 SDK
        self._external_credentials = external_credentials
        self._resource = resource
        self._scopes = scopes

    def _get_token(self, *scopes):
        external_tenant_tokens = []
        if not scopes:
            if self._resource:
                scopes = adal_resource_to_msal_scopes(self._resource)
            else:
                raise CLIError("Unexpected error: Resource or Scope need be specified to get access token")
        try:
            token = self._credential.get_token(*scopes)
            if self._external_credentials:
                external_tenant_tokens = [cred.get_token(*scopes) for cred in self._external_credentials]
        except CLIError as err:
            if in_cloud_console():
                CredentialAdaptor._log_hostname()
            raise err
        except ClientAuthenticationError as err:
            # pylint: disable=no-member
            if in_cloud_console():
                CredentialAdaptor._log_hostname()

            err = getattr(err, 'message', None) or ''
            if 'authentication is required' in err:
                raise CLIError("Authentication is migrated to Microsoft identity platform (v2.0). {}".format(
                    "Please run 'az login' to login." if not in_cloud_console() else ''))
            if 'AADSTS70008' in err:  # all errors starting with 70008 should be creds expiration related
                raise CLIError("Credentials have expired due to inactivity. {}".format(
                    "Please run 'az login'" if not in_cloud_console() else ''))
            if 'AADSTS50079' in err:
                raise CLIError("Configuration of your account was changed. {}".format(
                    "Please run 'az login'" if not in_cloud_console() else ''))
            if 'AADSTS50173' in err:
                raise CLIError("The credential data used by CLI has been expired because you might have changed or "
                               "reset the password. {}".format(
                                   "Please clear browser's cookies and run 'az login'"
                                   if not in_cloud_console() else ''))
            raise CLIError(err)
        except requests.exceptions.SSLError as err:
            from .util import SSLERROR_TEMPLATE
            raise CLIError(SSLERROR_TEMPLATE.format(str(err)))
        except requests.exceptions.ConnectionError as err:
            raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))
        return token, external_tenant_tokens

    def signed_session(self, session=None):
        session = session or requests.Session()
        token, external_tenant_tokens = self._get_token()
        header = "{} {}".format('Bearer', token.token)
        session.headers['Authorization'] = header
        if external_tenant_tokens:
            aux_tokens = ';'.join(['{} {}'.format('Bearer', tokens2.token) for tokens2 in external_tenant_tokens])
            session.headers['x-ms-authorization-auxiliary'] = aux_tokens
        return session

    def get_token(self, *scopes):
        token, _ = self._get_token(*scopes)
        return token

    @staticmethod
    def _log_hostname():
        import socket
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())
