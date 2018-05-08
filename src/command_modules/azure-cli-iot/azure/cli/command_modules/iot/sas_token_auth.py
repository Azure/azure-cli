# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC
from time import time
try:
    from urllib import (urlencode, quote)
except ImportError:
    from urllib.parse import (urlencode, quote)  # pylint: disable=import-error
from msrest.authentication import Authentication


class SasTokenAuthentication(Authentication):
    """
    Shared Access Signature authorization for Azure IoT Hub.

    :param str uri: Uri of target resource.
    :param str shared_access_policy_name: Name of shared access policy.
    :param str shared_access_key: Shared access key.
    :param int expiry: Expiry of the token to be generated.
    Input should be seconds since the epoch, in UTC. Default is an hour later from now.
    """
    def __init__(self, uri, shared_access_policy_name, shared_access_key, expiry=None):

        self.uri = quote(uri.lower(), safe='').lower()
        self.policy = shared_access_policy_name
        self.key = shared_access_key
        if expiry is None:
            self.expiry = time() + 3600  # Default expiry is an hour later
        else:
            self.expiry = expiry

    def signed_session(self, session=None):
        """Create requests session with SAS auth headers.

        :rtype: requests.Session.
        """
        session = session or super(SasTokenAuthentication, self).signed_session()
        session.headers['Authorization'] = self.generate_sas_token()
        return session

    def generate_sas_token(self):
        encoded_uri = quote(self.uri, safe='').lower()
        ttl = int(self.expiry)
        sign_key = '%s\n%d' % (encoded_uri, ttl)
        signature = b64encode(HMAC(b64decode(self.key), sign_key.encode('utf-8'), sha256).digest())

        return 'SharedAccessSignature ' + urlencode({
            'sr': self.uri,
            'sig': signature,
            'se': str(ttl),
            'skn': self.policy
        })
