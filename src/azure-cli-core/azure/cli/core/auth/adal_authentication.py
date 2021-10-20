# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
from azure.core.credentials import AccessToken
from knack.log import get_logger
from msrestazure.azure_active_directory import MSIAuthentication

from .util import _normalize_scopes, scopes_to_resource

logger = get_logger(__name__)


class MSIAuthenticationWrapper(MSIAuthentication):
    # This method is exposed for Azure Core. Add *scopes, **kwargs to fit azure.core requirement
    def get_token(self, *scopes, **kwargs):  # pylint:disable=unused-argument
        logger.debug("MSIAuthenticationWrapper.get_token invoked by Track 2 SDK with scopes=%s", scopes)

        if 'data' in kwargs:
            from azure.cli.core.azclierror import AuthenticationError
            raise AuthenticationError("VM SSH currently doesn't support managed identity or Cloud Shell.")

        resource = scopes_to_resource(_normalize_scopes(scopes))
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
