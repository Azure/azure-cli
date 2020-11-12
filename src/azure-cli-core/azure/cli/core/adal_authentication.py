# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import datetime
import time
import requests
import adal

from msrest.authentication import Authentication
from msrestazure.azure_active_directory import MSIAuthentication
from azure.core.credentials import AccessToken
from azure.cli.core.util import in_cloud_console, scopes_to_resource

from knack.util import CLIError
from knack.log import get_logger

logger = get_logger(__name__)


class AdalAuthentication(Authentication):  # pylint: disable=too-few-public-methods

    def __init__(self, token_retriever, external_tenant_token_retriever=None):
        # DO NOT call _token_retriever from outside azure-cli-core. It is only available for user or
        # Service Principal credential (AdalAuthentication), but not for Managed Identity credential
        # (MSIAuthenticationWrapper).
        # To retrieve a raw token, either call
        #   - Profile.get_raw_token, which is more direct
        #   - AdalAuthentication.get_token, which is designed for Track 2 SDKs
        self._token_retriever = token_retriever
        self._external_tenant_token_retriever = external_tenant_token_retriever

    def _get_token(self, sdk_resource=None):
        """
        :param sdk_resource: `resource` converted from Track 2 SDK's `scopes`
        """
        external_tenant_tokens = None
        try:
            scheme, token, full_token = self._token_retriever(sdk_resource)
            if self._external_tenant_token_retriever:
                external_tenant_tokens = self._external_tenant_token_retriever(sdk_resource)
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
        logger.debug("AdalAuthentication.get_token invoked by Track 2 SDK with scopes=%s", scopes)

        _, token, full_token, _ = self._get_token(_try_scopes_to_resource(scopes))

        if 'expiresOn' in full_token:
            try:
                return AccessToken(token, int(
                    datetime.datetime.strptime(full_token['expiresOn'], '%Y-%m-%d %H:%M:%S.%f').timestamp()))
            except:  # pylint: disable=bare-except
                pass  # To avoid crashes due to some unexpected token formats

        try:
            return AccessToken(token, int(full_token['expiresIn'] + time.time()))
        except KeyError:  # needed to deal with differing unserialized MSI token payload
            return AccessToken(token, int(full_token['expires_on']))

    # This method is exposed for msrest.
    def signed_session(self, session=None):  # pylint: disable=arguments-differ
        logger.debug("AdalAuthentication.signed_session invoked by Track 1 SDK")
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
        logger.warning("A Cloud Shell credential problem occurred. When you report the issue with the error "
                       "below, please mention the hostname '%s'", socket.gethostname())


class MSIAuthenticationWrapper(MSIAuthentication):
    # This method is exposed for Azure Core. Add *scopes, **kwargs to fit azure.core requirement
    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        logger.debug("MSIAuthenticationWrapper.get_token invoked by Track 2 SDK with scopes=%s", scopes)
        resource = _try_scopes_to_resource(scopes)
        if resource:
            # If available, use resource provided by SDK
            self.resource = resource
        self.set_token()
        return AccessToken(self.token['access_token'], int(self.token['expires_on']))

    def set_token(self):
        import traceback
        from azure.cli.core.azclierror import AzureConnectionError, AzureResponseError
        try:
            super(MSIAuthenticationWrapper, self).set_token()
        except requests.exceptions.ConnectionError as err:
            logger.debug('throw requests.exceptions.ConnectionError when doing MSIAuthentication: \n%s',
                         traceback.format_exc())
            raise AzureConnectionError('Failed to connect to MSI. Please make sure MSI is configured correctly '
                                       'and check the network connection.\nError detail: {}'.format(str(err)))
        except requests.exceptions.HTTPError as err:
            logger.debug('throw requests.exceptions.HTTPError when doing MSIAuthentication: \n%s',
                         traceback.format_exc())
            try:
                raise AzureResponseError('Failed to connect to MSI. Please make sure MSI is configured correctly.\n'
                                         'Get Token request returned http error: {}, reason: {}'
                                         .format(err.response.status, err.response.reason))
            except AttributeError:
                raise AzureResponseError('Failed to connect to MSI. Please make sure MSI is configured correctly.\n'
                                         'Get Token request returned: {}'.format(err.response))
        except TimeoutError as err:
            logger.debug('throw TimeoutError when doing MSIAuthentication: \n%s',
                         traceback.format_exc())
            raise AzureConnectionError('MSI endpoint is not responding. Please make sure MSI is configured correctly.\n'
                                       'Error detail: {}'.format(str(err)))

    def signed_session(self, session=None):
        logger.debug("MSIAuthenticationWrapper.signed_session invoked by Track 1 SDK")
        super().signed_session(session)


def _try_scopes_to_resource(scopes):
    """Wrap scopes_to_resource to workaround some SDK issues."""

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
        return scopes_to_resource(scopes[1:])

    # Exactly only one scope is provided
    return scopes_to_resource(scopes)
