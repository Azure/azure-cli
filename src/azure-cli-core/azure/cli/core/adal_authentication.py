# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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
            scheme, token, token_entry = self._token_retriever(sdk_resource)
            if self._external_tenant_token_retriever:
                external_tenant_tokens = self._external_tenant_token_retriever(sdk_resource)
        except CLIError as err:
            if in_cloud_console():
                AdalAuthentication._log_hostname()
            raise err
        except adal.AdalError as err:
            if in_cloud_console():
                AdalAuthentication._log_hostname()
            adal_error_handler(err)
        except requests.exceptions.SSLError as err:
            from .util import SSLERROR_TEMPLATE
            raise CLIError(SSLERROR_TEMPLATE.format(str(err)))
        except requests.exceptions.ConnectionError as err:
            raise CLIError('Please ensure you have network connection. Error detail: ' + str(err))

        # scheme: str. The token scheme. Should always be 'Bearer'.
        # token: str. The raw access token.
        # token_entry: dict. The full token entry.
        # external_tenant_tokens: [(scheme: str, token: str, token_entry: dict), ...]
        return scheme, token, token_entry, external_tenant_tokens

    def get_all_tokens(self, *scopes):
        return self._get_token(_try_scopes_to_resource(scopes))

    # This method is exposed for Azure Core.
    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        logger.debug("AdalAuthentication.get_token invoked by Track 2 SDK with scopes=%s", scopes)

        _, token, token_entry, _ = self._get_token(_try_scopes_to_resource(scopes))

        # NEVER use expiresIn (expires_in) as the token is cached and expiresIn will be already out-of date
        # when being retrieved.

        # User token entry sample:
        # {
        #     "tokenType": "Bearer",
        #     "expiresOn": "2020-11-13 14:44:42.492318",
        #     "resource": "https://management.core.windows.net/",
        #     "userId": "test@azuresdkteam.onmicrosoft.com",
        #     "accessToken": "eyJ0eXAiOiJKV...",
        #     "refreshToken": "0.ATcAImuCVN...",
        #     "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        #     "_authority": "https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a",
        #     "isMRRT": True,
        #     "expiresIn": 3599
        # }

        # Service Principal token entry sample:
        # {
        #     "tokenType": "Bearer",
        #     "expiresIn": 3599,
        #     "expiresOn": "2020-11-12 13:50:47.114324",
        #     "resource": "https://management.core.windows.net/",
        #     "accessToken": "eyJ0eXAiOiJKV...",
        #     "isMRRT": True,
        #     "_clientId": "22800c35-46c2-4210-b8a7-d8c3ec3b526f",
        #     "_authority": "https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a"
        # }
        if 'expiresOn' in token_entry:
            import datetime
            expires_on_timestamp = int(_timestamp(
                datetime.datetime.strptime(token_entry['expiresOn'], '%Y-%m-%d %H:%M:%S.%f')))
            return AccessToken(token, expires_on_timestamp)

        # Cloud Shell (Managed Identity) token entry sample:
        # {
        #     "access_token": "eyJ0eXAiOiJKV...",
        #     "refresh_token": "",
        #     "expires_in": "2106",
        #     "expires_on": "1605686811",
        #     "not_before": "1605682911",
        #     "resource": "https://management.core.windows.net/",
        #     "token_type": "Bearer"
        # }
        if 'expires_on' in token_entry:
            return AccessToken(token, int(token_entry['expires_on']))

        from azure.cli.core.azclierror import CLIInternalError
        raise CLIInternalError("No expiresOn or expires_on is available in the token entry.")

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
        # Managed Identity token entry sample:
        # {
        #     "access_token": "eyJ0eXAiOiJKV...",
        #     "client_id": "da95e381-d7ab-4fdc-8047-2457909c723b",
        #     "expires_in": "86386",
        #     "expires_on": "1605238724",
        #     "ext_expires_in": "86399",
        #     "not_before": "1605152024",
        #     "resource": "https://management.azure.com/",
        #     "token_type": "Bearer"
        # }
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


class BasicTokenCredential:
    # pylint:disable=too-few-public-methods
    """A Track 2 implementation of msrest.authentication.BasicTokenAuthentication.
    This credential shouldn't be used by any command module, expect azure-cli-core.
    """
    def __init__(self, access_token):
        self.access_token = access_token

    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        # Because get_token can't refresh the access token, always mark the token as unexpired
        import time
        return AccessToken(self.access_token, int(time.time() + 3600))


def _timestamp(dt):
    # datetime.datetime can't be patched:
    #   TypeError: can't set attributes of built-in/extension type 'datetime.datetime'
    # So we wrap datetime.datetime.timestamp with this function.
    # https://docs.python.org/3/library/unittest.mock-examples.html#partial-mocking
    # https://williambert.online/2011/07/how-to-unit-testing-in-django-with-mocking-and-patching/
    return dt.timestamp()


def aad_error_handler(error: dict):
    """ Handle the error from AAD server returned by ADAL or MSAL. """
    login_message = ("To re-authenticate, please {}. If the problem persists, "
                     "please contact your tenant administrator."
                     .format("refresh Azure Portal" if in_cloud_console() else "run `az login`"))

    # https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-aadsts-error-codes
    # Search for an error code at https://login.microsoftonline.com/error
    msg = error.get('error_description')

    from azure.cli.core.azclierror import AuthenticationError
    raise AuthenticationError(msg, login_message)


def adal_error_handler(err: adal.AdalError):
    """ Handle AdalError. """
    try:
        aad_error_handler(err.error_response)
    except AttributeError:
        # In case of AdalError created as
        #   AdalError('More than one token matches the criteria. The result is ambiguous.')
        # https://github.com/Azure/azure-cli/issues/15320
        from azure.cli.core.azclierror import UnknownError
        raise UnknownError(str(err), recommendation="Please run `az account clear`, then `az login`.")
