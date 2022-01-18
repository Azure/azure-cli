# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import requests
from knack.log import get_logger
from msrestazure.azure_active_directory import MSIAuthentication

from .util import _normalize_scopes, scopes_to_resource, AccessToken

logger = get_logger(__name__)


class MSIAuthenticationWrapper(MSIAuthentication):
    # This method is exposed for Azure Core. Add *scopes, **kwargs to fit azure.core requirement
    # pylint: disable=line-too-long
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
        # VM managed identity endpoint 2018-02-01 token entry sample:
        # curl "http://169.254.169.254:80/metadata/identity/oauth2/token?resource=https://management.core.windows.net/&api-version=2018-02-01" -H "Metadata: true"
        # {
        #     "access_token": "eyJ0eXAiOiJKV...",
        #     "client_id": "da95e381-d7ab-4fdc-8047-2457909c723b",
        #     "expires_in": "86386",
        #     "expires_on": "1605238724",
        #     "ext_expires_in": "86399",
        #     "not_before": "1605152024",
        #     "resource": "https://management.core.windows.net/",
        #     "token_type": "Bearer"
        # }

        # App Service managed identity endpoint 2017-09-01 token entry sample:
        # curl "${MSI_ENDPOINT}?resource=https://management.core.windows.net/&api-version=2017-09-01" -H "secret: ${MSI_SECRET}"
        # {
        #     "access_token": "eyJ0eXAiOiJKV...",
        #     "expires_on":"11/05/2021 15:18:31 +00:00",
        #     "resource":"https://management.core.windows.net/",
        #     "token_type":"Bearer",
        #     "client_id":"df45d93a-de31-47ca-acef-081ca60d1a83"
        # }
        return AccessToken(self.token['access_token'], _normalize_expires_on(self.token['expires_on']))

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


def _normalize_expires_on(expires_on):
    """
    The expires_on field returned by managed identity differs on Azure VM (epoch str) and App Service (datetime str).
    Normalize to epoch int.
    """
    try:
        # Treat as epoch string "1605238724"
        expires_on_epoch_int = int(expires_on)
    except ValueError:
        import datetime

        # Python 3.6 doesn't recognize timezone as +00:00.
        # These lines can be dropped after Python 3.6 is dropped.
        # https://stackoverflow.com/questions/30999230/how-to-parse-timezone-with-colon
        if expires_on[-3] == ":":
            expires_on = expires_on[:-3] + expires_on[-2:]

        # Treat as datetime string "11/05/2021 15:18:31 +00:00"
        expires_on_epoch_int = int(datetime.datetime.strptime(expires_on, '%m/%d/%Y %H:%M:%S %z').timestamp())

    logger.debug("Normalize expires_on: %r -> %r", expires_on, expires_on_epoch_int)
    return expires_on_epoch_int
