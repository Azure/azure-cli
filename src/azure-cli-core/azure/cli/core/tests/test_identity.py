# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import unittest
from unittest import mock

from azure.cli.core._identity import Identity


class TestIdentity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @mock.patch('azure.cli.core._identity.MsalSecretStore.save_service_principal_cred', autospec=True)
    @mock.patch('azure.cli.core._identity.Identity._build_persistent_msal_app', autospec=True)
    @mock.patch('azure.cli.core._identity.AdalCredentialCache._load_tokens_from_file', autospec=True)
    def test_migrate_tokens(self, load_tokens_from_file_mock, build_persistent_msal_app_mock,
                            save_service_principal_cred_mock):
        adal_tokens = [
            {
                "tokenType": "Bearer",
                "expiresOn": "2020-08-03 19:00:36.784501",
                "resource": "https://management.core.windows.net/",
                "userId": "test_user@microsoft.com",
                "accessToken": "test_access_token",
                "refreshToken": "test_refresh_token",
                "_clientId": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
                "_authority": "https://login.microsoftonline.com/00000001-0000-0000-0000-000000000000",
                "isMRRT": True,
                "expiresIn": 3599
            },
            {
                "servicePrincipalId": "00000002-0000-0000-0000-000000000000",
                "servicePrincipalTenant": "00000001-0000-0000-0000-000000000000",
                "accessToken": "test_sp_secret"
            }
        ]
        load_tokens_from_file_mock.return_value = adal_tokens

        identity = Identity()
        identity.migrate_tokens()
        msal_app_mock = build_persistent_msal_app_mock.return_value
        msal_app_mock.acquire_token_by_refresh_token.assert_called_with(
            'test_refresh_token', ['https://management.core.windows.net/.default'])
        save_service_principal_cred_mock.assert_called_with(mock.ANY, adal_tokens[1])


if __name__ == '__main__':
    unittest.main()
