# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import requests
import adal

from msrest.authentication import Authentication
from msrestazure.azure_active_directory import MSIAuthentication
from azure.core.credentials import AccessToken
from azure.cli.core.util import in_cloud_console

from knack.util import CLIError


class AdalAuthentication(Authentication):  # pylint: disable=too-few-public-methods

    def __init__(self, token_retriever, external_tenant_token_retriever=None):
        self._token_retriever = token_retriever
        self._external_tenant_token_retriever = external_tenant_token_retriever

    def _get_token(self):
        external_tenant_tokens = None
        try:
            scheme, token, full_token = self._token_retriever()
            if self._external_tenant_token_retriever:
                external_tenant_tokens = self._external_tenant_token_retriever()
        except CLIError as err:
            if in_cloud_console():
                AdalAuthentication._log_hostname()
            raise err
        except adal.AdalError as err:
            # pylint: disable=no-member
            if in_cloud_console():
                AdalAuthentication._log_hostname()

            err = (getattr(err, 'error_response', None) or {}).get('error_description') or str(err)
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

        return scheme, token, full_token, external_tenant_tokens

    # This method is exposed for Azure Core.
    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        _, token, full_token, _ = self._get_token()
        try:
            return AccessToken(token, int(full_token['expiresIn'] + time.time()))
        except KeyError:  # needed to deal with differing unserialized MSI token payload
            return AccessToken(token, int(full_token['expires_on']))

    # This method is exposed for msrest.
    def signed_session(self, session=None):  # pylint: disable=arguments-differ
        session = session or super(AdalAuthentication, self).signed_session()

        scheme, token, _, external_tenant_tokens = self._get_token()

        header = "{} {}".format(scheme, token)
        session.headers['Authorization'] = header
        if external_tenant_tokens:
            aux_tokens = ';'.join(['{} {}'.format(scheme2, tokens2) for scheme2, tokens2, _ in external_tenant_tokens])
            session.headers['x-ms-authorization-auxiliary'] = aux_tokens
        return session

    @staticmethod
    def _log_hostname():
        import socket
        from knack.log import get_logger
        logger = get_logger(__name__)
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())


class MSIAuthenticationWrapper(MSIAuthentication):
    # This method is exposed for Azure Core. Add *scopes, **kwargs to fit azure.core requirement
    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        self.set_token()
        return AccessToken(self.token['access_token'], int(self.token['expires_on']))

    def set_token(self):
        from .azclierror import AzureConnectionError, AzureResponseError
        try:
            super(MSIAuthenticationWrapper, self).set_token()
        except requests.exceptions.ConnectionError as err:
            raise AzureConnectionError('Failed to connect to MSI. Please make sure MSI is configured correctly.\n'
                                       'Error detail: {}'.format(str(err)))
        except requests.exceptions.HTTPError as err:
            raise AzureResponseError('Failed to connect to MSI. Please make sure MSI is configured correctly.\n'
                                     'Error code: {}, reason: {}'
                                     .format(err.response.status, err.response.reason))
        except TimeoutError as err:
            raise AzureConnectionError('MSI endpoint is not responding. Please make sure MSI is configured correctly.\n'
                                       'Error detail: {}'.format(str(err)))
