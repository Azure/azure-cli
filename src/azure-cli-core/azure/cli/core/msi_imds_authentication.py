# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from knack.log import get_logger
from knack.util import CLIError
from msrest.authentication import BasicTokenAuthentication

logger = get_logger(__name__)


class MSIImdsAuthentication(BasicTokenAuthentication):
    """Credentials object for MSI authentication through VM IMDS endpoint

    Optional kwargs may include:
    - client_id: Identifies, by Azure AD client id, a specific explicit identity to
    use when authenticating to Azure AD. Mutually exclusive with object_id and msi_res_id.
    - object_id: Identifies, by Azure AD object id, a specific explicit identity to
    use when authenticating to Azure AD. Mutually exclusive with client_id and msi_res_id.
    - msi_res_id: Identifies, by ARM resource id, a specific explicit identity to use
    when authenticating to Azure AD. Mutually exclusive with client_id and object_id.
    - cloud_environment (msrestazure.azure_cloud.Cloud): A targeted cloud environment
    - resource (str): Alternative authentication resource, default
      is 'https://management.core.windows.net/'.
    """

    def __init__(self, **kwargs):
        super(MSIImdsAuthentication, self).__init__(None)

        self.identity_type, self.identity_id = None, None
        temp = {k: v for k, v in kwargs.items() if k in ["client_id", "object_id", "msi_res_id"]}
        if len(temp.keys()) > 1:
            raise ValueError('"client_id", "object_id", "msi_res_id" are mutually exclusive')
        elif len(temp.keys()) == 1:
            self.identity_type, self.identity_id = next(iter(temp.items()))

        self.cache = {}
        self.resource = kwargs.get('resource')

    def _set_token(self):
        token_entry = self.get_token()
        self.scheme, self.token = token_entry['token_type'], token_entry

    def get_token(self):
        import datetime
        # let us hit the cache first
        token_entry = self.cache.get(self.resource, None)
        if token_entry:
            expires_on = int(token_entry['expires_on'])
            expires_on_datetime = datetime.datetime.fromtimestamp(expires_on)
            expiration_margin = 5  # in minutes
            if datetime.datetime.now() + datetime.timedelta(minutes=expiration_margin) <= expires_on_datetime:
                logger.info("MSI: token is found in cache.")
                return token_entry
            logger.info("MSI: cache is found but expired within %s minutes, so getting a new one.", expiration_margin)
            self.cache.pop(self.resource)

        token_entry = self._retrieve_token_from_imds_with_retry()
        self.cache[self.resource] = token_entry
        return token_entry

    def signed_session(self):
        self._set_token()
        return super(MSIImdsAuthentication, self).signed_session()

    def _retrieve_token_from_imds_with_retry(self):
        import random
        import requests
        import time

        request_uri = 'http://169.254.169.254/metadata/identity/oauth2/token'
        payload = {
            'resource': self.resource,
            'api-version': '2018-02-01'
        }
        if self.identity_id:
            payload[self.identity_type] = self.identity_id

        retry, max_retry = 1, 20
        # simplified version of https://en.wikipedia.org/wiki/Exponential_backoff
        slots = [100 * ((2 << x) - 1) / 1000 for x in range(max_retry)]
        while retry <= max_retry:
            result = requests.get(request_uri, params=payload, headers={'Metadata': 'true'})
            logger.debug("MSI: Retrieving a token from %s, with payload %s", request_uri, payload)
            if result.status_code == 429:
                wait = random.choice(slots[:retry])
                logger.warning("MSI: Wait: %ss and retry: %s", wait, retry)
                time.sleep(wait)
                retry += 1
            elif result.status_code != 200:
                raise ValueError("MSI: Failed to retrieve a token from '{}' with an error of '{}'".format(
                    request_uri, result.text))
            else:
                break

        if retry >= max_retry:
            raise CLIError('MSI: Failed to acquire tokens after {} times'.format(max_retry))
        else:
            logger.debug('MSI: Token retrieved')

        token_entry = json.loads(result.content.decode())
        return token_entry
