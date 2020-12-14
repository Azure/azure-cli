# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import datetime
import unittest
import unittest.mock as mock
from unittest.mock import MagicMock

from azure.cli.core.adal_authentication import AdalAuthentication, _try_scopes_to_resource


class TestUtils(unittest.TestCase):

    def test_try_scopes_to_resource(self):
        # Test no scopes
        self.assertIsNone(_try_scopes_to_resource(()))
        self.assertIsNone(_try_scopes_to_resource([]))
        self.assertIsNone(_try_scopes_to_resource(None))

        # Test multiple scopes, with the first one discarded
        resource = _try_scopes_to_resource(("https://management.core.windows.net//.default",
                                            "https://management.core.chinacloudapi.cn//.default"))
        self.assertEqual(resource, "https://management.core.chinacloudapi.cn/")

        # Test single scopes (the correct usage)
        resource = _try_scopes_to_resource(("https://management.core.chinacloudapi.cn//.default",))
        self.assertEqual(resource, "https://management.core.chinacloudapi.cn/")


class TestAdalAuthentication(unittest.TestCase):

    def test_get_token(self):
        user_full_token = (
            'Bearer',
            'access_token_user_mock',
            {
                'tokenType': 'Bearer',
                'expiresIn': 3599,
                'expiresOn': '2020-11-18 15:35:17.512862',  # Local time
                'resource': 'https://management.core.windows.net/',
                'accessToken': 'access_token_user_mock',
                'refreshToken': 'refresh_token_user_mock',
                'oid': '6d97229a-391f-473a-893f-f0608b592d7b', 'userId': 'rolelivetest@azuresdkteam.onmicrosoft.com',
                'isMRRT': True, '_clientId': '04b07795-8ddb-461a-bbee-02f9e1bf7b46',
                '_authority': 'https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'
            })
        cloud_shell_full_token = (
            'Bearer',
            'access_token_cloud_shell_mock',
            {
                'access_token': 'access_token_cloud_shell_mock',
                'refresh_token': '',
                'expires_in': '2732',
                'expires_on': '1605683384',
                'not_before': '1605679484',
                'resource': 'https://management.core.windows.net/',
                'token_type': 'Bearer'
            })
        token_retriever = MagicMock()
        cred = AdalAuthentication(token_retriever)

        def utc_to_timestamp(dt):
            # Obtain the POSIX timestamp from a naive datetime instance representing UTC time
            # https://docs.python.org/3/library/datetime.html#datetime.datetime.timestamp
            return dt.replace(tzinfo=datetime.timezone.utc).timestamp()

        # Test expiresOn is used and converted to epoch time
        # Force expiresOn to be treated as UTC to make the test pass on both local machine (such as UTC+8)
        # and CI (UTC).
        with mock.patch("azure.cli.core.adal_authentication._timestamp", utc_to_timestamp):
            token_retriever.return_value = user_full_token
            access_token = cred.get_token("https://management.core.windows.net//.default")
            self.assertEqual(access_token.token, "access_token_user_mock")
            self.assertEqual(access_token.expires_on, 1605713717)

        # Test expires_on is used as epoch directly
        token_retriever.return_value = cloud_shell_full_token
        access_token = cred.get_token("https://management.core.windows.net//.default")
        self.assertEqual(access_token.token, "access_token_cloud_shell_mock")
        self.assertEqual(access_token.expires_on, 1605683384)


if __name__ == '__main__':
    unittest.main()
