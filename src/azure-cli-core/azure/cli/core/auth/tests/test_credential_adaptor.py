# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import unittest
from collections import namedtuple
from unittest import mock

from ..credential_adaptor import CredentialAdaptor


MOCK_ACCESS_TOKEN = "mock_access_token"
MOCK_DATA = {"test_data": "value1"}
MOCK_CLAIMS = {"test_claims": "value2"}

class MsalCredentialStub:

    def __init__(self, *args, **kwargs):
        self.acquire_token_scopes = None
        self.acquire_token_kwargs = None
        super().__init__()

    def acquire_token(self, scopes, **kwargs):
        self.acquire_token_scopes = scopes
        self.acquire_token_kwargs = kwargs
        return {
            'access_token': MOCK_ACCESS_TOKEN,
            'token_type': 'Bearer',
            'expires_in': 1800,
            'token_source': 'cache'
        }

def _now_timestamp_mock():
    # 2021-09-06 08:55:23
    return 1630918523


class TestCredentialAdaptor(unittest.TestCase):

    @mock.patch('azure.cli.core.auth.util._now_timestamp', new=_now_timestamp_mock)
    def test_get_token(self):
        msal_cred = MsalCredentialStub()
        sdk_cred = CredentialAdaptor(msal_cred)
        access_token = sdk_cred.get_token('https://management.core.windows.net//.default')
        assert msal_cred.acquire_token_scopes == ['https://management.core.windows.net//.default']

        from ..util import AccessToken
        assert isinstance(access_token, AccessToken)
        assert access_token.token == MOCK_ACCESS_TOKEN
        assert access_token.expires_on == 1630920323

        sdk_cred.get_token('https://management.core.windows.net//.default', data=MOCK_DATA)
        assert msal_cred.acquire_token_kwargs['data'] == MOCK_DATA

        sdk_cred.get_token('https://management.core.windows.net//.default', claims=MOCK_CLAIMS)
        assert msal_cred.acquire_token_kwargs['claims'] == MOCK_CLAIMS


    @mock.patch('azure.cli.core.auth.util._now_timestamp', new=_now_timestamp_mock)
    def test_get_token_info(self):
        msal_cred = MsalCredentialStub()
        sdk_cred = CredentialAdaptor(msal_cred)
        access_token_info = sdk_cred.get_token_info('https://management.core.windows.net//.default')

        from azure.core.credentials import AccessTokenInfo
        assert isinstance(access_token_info, AccessTokenInfo)
        assert access_token_info.token == MOCK_ACCESS_TOKEN
        assert access_token_info.expires_on == 1630920323
        assert access_token_info.token_type == 'Bearer'

        assert msal_cred.acquire_token_scopes == ['https://management.core.windows.net//.default']

        # Actually, TokenRequestOptions doesn't support 'data'.
        sdk_cred.get_token_info('https://management.core.windows.net//.default', options={'data': MOCK_DATA})
        assert msal_cred.acquire_token_kwargs['data'] == MOCK_DATA

        sdk_cred.get_token_info('https://management.core.windows.net//.default', options={'claims': MOCK_CLAIMS})
        assert msal_cred.acquire_token_kwargs['claims'] == MOCK_CLAIMS


if __name__ == '__main__':
    unittest.main()
