# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access
import os
import json
import unittest
from unittest import mock

from azure.cli.core._identity import Identity, ServicePrincipalAuth, MsalSecretStore


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

    def test_login_with_service_principal_certificate_cert_err(self):
        import os
        identity = Identity()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'err_sp_cert.pem')
        # TODO: wrap exception
        with self.assertRaisesRegex(ValueError, "Unable to load certificate."):
            identity.login_with_service_principal_certificate("00000000-0000-0000-0000-000000000000", test_cert_file)


class TestServicePrincipalAuth(unittest.TestCase):

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth('sp_id1', 'tenant1', 'verySecret!')
        result = sp_auth.get_entry_to_persist()
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'secret': 'verySecret!'
        })

    def test_service_principal_auth_client_cert(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        sp_auth = ServicePrincipalAuth('sp_id1', 'tenant1', None, test_cert_file)

        result = sp_auth.get_entry_to_persist()
        self.assertEqual(result, {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'certificateFile': test_cert_file,
        })


class TestMsalSecretStore(unittest.TestCase):

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_retrieve_secret_of_service_principal_with_secret(self, mock_read_file, mock_read_file2, mock_read_file3):
        test_sp = [{
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }]
        mock_read_file.return_value = json.dumps(test_sp)
        mock_read_file2.return_value = json.dumps(test_sp)
        mock_read_file3.return_value = json.dumps(test_sp)
        from azure.cli.core._identity import MsalSecretStore
        # action
        secret_store = MsalSecretStore()
        token, file = secret_store.retrieve_secret_of_service_principal("myapp", "mytenant")

        self.assertEqual(token, "Secret")

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_retrieve_secret_of_service_principal_with_cert(self, mock_read_file, mock_read_file2, mock_read_file3):
        test_sp = [{
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "certificateFile": 'junkcert.pem'
        }]
        mock_read_file.return_value = json.dumps(test_sp)
        mock_read_file2.return_value = json.dumps(test_sp)
        mock_read_file3.return_value = json.dumps(test_sp)
        from azure.cli.core._identity import MsalSecretStore
        # action
        creds_cache = MsalSecretStore()
        token, file = creds_cache.retrieve_secret_of_service_principal("myapp", "mytenant")

        # assert
        self.assertEqual(file, 'junkcert.pem')


if __name__ == '__main__':
    unittest.main()
