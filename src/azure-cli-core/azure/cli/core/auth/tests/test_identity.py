# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from unittest import mock

import msal_extensions.persistence
from azure.cli.core.auth.identity import Identity, ServicePrincipalAuth, MsalSecretStore
from knack.util import CLIError
from msal_extensions import FilePersistence


class TestIdentity(unittest.TestCase):

    def test_login_with_service_principal_certificate_cert_err(self):
        import os
        identity = Identity()
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'err_sp_cert.pem')

        with self.assertRaisesRegex(CLIError, "Invalid certificate"):
            identity.login_with_service_principal("00000000-0000-0000-0000-000000000000", test_cert_file)


class TestServicePrincipalAuth(unittest.TestCase):

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth('tenant1', 'sp_id1', 'verySecret!')
        result = sp_auth.get_entry_to_persist()

        assert result == {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'secret': 'verySecret!'
        }

    def test_service_principal_auth_client_cert(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        sp_auth = ServicePrincipalAuth('tenant1', 'sp_id1', test_cert_file)

        result = sp_auth.get_entry_to_persist()
        # To compute the thumb print:
        #   openssl x509 -in sp_cert.pem -noout -fingerprint
        assert sp_auth.thumbprint == 'F06A53848BBE714A4290D69D335279C1D01073FD'
        assert result == {
            'servicePrincipalId': 'sp_id1',
            'servicePrincipalTenant': 'tenant1',
            'certificateFile': test_cert_file
        }


class TestMsalSecretStore(unittest.TestCase):

    @mock.patch('azure.cli.core.auth.persistence.build_persistence', autospec=True)
    def test_load_service_principal_secret(self, build_persistence_mock):
        persistence = MemoryPersistence()
        build_persistence_mock.return_value = persistence

        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        secret_store = MsalSecretStore(None)
        persistence._content = [test_sp]

        entry = secret_store.load_credential("myapp", "mytenant")
        self.assertEqual(entry['secret'], "Secret")

    @mock.patch('azure.cli.core.auth.persistence.build_persistence', autospec=True)
    def test_save_service_principal_secret(self, build_persistence_mock):
        test_file = os.path.join(os.path.dirname(__file__), "test.json")
        build_persistence_mock.return_value = FilePersistence(test_file)

        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        secret_store = MsalSecretStore(test_file)
        secret_store.save_credential(test_sp)

        with open(test_file, 'r') as f:
            result = json.load(f)
        assert result[0] == test_sp

        try:
            os.remove(test_file)
        except:
            pass

    @mock.patch('azure.cli.core.auth.persistence.build_persistence', autospec=True)
    def test_credscache_add_new_sp_creds(self, build_persistence_mock):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "secret": "Secret"
        }
        test_sp2 = {
            "servicePrincipalId": "myapp2",
            "servicePrincipalTenant": "mytenant2",
            "secret": "Secret2"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action
        creds_cache.save_credential(test_sp2)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp, test_sp2])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_add_preexisting_sp_creds(self, mock_open_for_write1, mock_open_for_write2, mock_open_for_write3,
                                                 mock_read_file1, mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action
        creds_cache.save_credential(test_sp)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [test_sp])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_add_preexisting_sp_new_secret(self, mock_open_for_write1, mock_open_for_write2,
                                                      mock_open_for_write3, mock_read_file1,
                                                      mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()
        new_creds = test_sp.copy()
        new_creds['accessToken'] = 'Secret2'
        # action
        creds_cache.save_credential(new_creds)

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [new_creds])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.save', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.save', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.save', autospec=True)
    def test_credscache_remove_creds(self, mock_open_for_write1, mock_open_for_write2, mock_open_for_write3,
                                     mock_read_file1, mock_read_file2, mock_read_file3):
        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }
        mock_open_for_write1.return_value = None
        mock_open_for_write2.return_value = None
        mock_open_for_write3.return_value = None
        mock_read_file1.return_value = json.dumps([test_sp])
        mock_read_file2.return_value = json.dumps([test_sp])
        mock_read_file3.return_value = json.dumps([test_sp])
        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # action logout a service principal
        creds_cache.remove_credential('myapp')

        # assert
        self.assertEqual(creds_cache._service_principal_creds, [])

    @mock.patch('msal_extensions.FilePersistenceWithDataProtection.load', autospec=True)
    @mock.patch('msal_extensions.LibsecretPersistence.load', autospec=True)
    @mock.patch('msal_extensions.FilePersistence.load', autospec=True)
    def test_credscache_good_error_on_file_corruption(self, mock_read_file1, mock_read_file2, mock_read_file3):
        mock_read_file1.side_effect = ValueError('a bad error for you')
        mock_read_file2.side_effect = ValueError('a bad error for you')
        mock_read_file3.side_effect = ValueError('a bad error for you')

        from azure.cli.core._identity import MsalSecretStore
        creds_cache = MsalSecretStore()

        # assert
        with self.assertRaises(CLIError) as context:
            creds_cache._load_persistence()

        self.assertTrue(re.findall(r'bad error for you', str(context.exception)))


class MemoryPersistence(msal_extensions.persistence.BasePersistence):

    def __init__(self):
        self._content = None

    def save(self, content):
        self._content = content

    def load(self):
        return self._content

    def time_last_modified(self):
        pass

    def get_location(self):
        pass


if __name__ == '__main__':
    unittest.main()
