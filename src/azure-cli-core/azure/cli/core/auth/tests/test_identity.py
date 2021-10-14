# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.core.auth.identity import (Identity, ServicePrincipalAuth, ServicePrincipalStore,
                                          _get_authority_url)
from knack.util import CLIError


class TestIdentity(unittest.TestCase):

    def test_login_with_service_principal_certificate_cert_err(self):
        import os
        identity = Identity('https://login.microsoftonline.com')
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'err_sp_cert.pem')

        with self.assertRaisesRegex(CLIError, "Invalid certificate"):
            identity.login_with_service_principal("00000000-0000-0000-0000-000000000000",
                                                  {"certificate": test_cert_file})


class TestServicePrincipalAuth(unittest.TestCase):

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1', {'client_secret': "test_secret"})
        result = sp_auth.get_entry_to_persist()

        assert result == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_secret': 'test_secret'
        }

    def test_service_principal_auth_client_cert(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1', {'certificate': test_cert_file})

        result = sp_auth.get_entry_to_persist()
        # To compute the thumb print:
        #   openssl x509 -in sp_cert.pem -noout -fingerprint
        assert sp_auth.thumbprint == 'F06A53848BBE714A4290D69D335279C1D01073FD'
        assert result == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': test_cert_file
        }

    def test_build_credential(self):
        # secret
        cred = ServicePrincipalAuth.build_credential("test_secret")
        assert cred == {"client_secret": "test_secret"}

        # certificate
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'sp_cert.pem')
        cred = ServicePrincipalAuth.build_credential(test_cert_file)
        assert cred == {'certificate': test_cert_file}

        cred = ServicePrincipalAuth.build_credential(test_cert_file, use_cert_sn_issuer=True)
        assert cred == {'certificate': test_cert_file, 'use_cert_sn_issuer': True}

        # client assertion
        cred = ServicePrincipalAuth.build_credential(client_assertion="test_jwt")
        assert cred == {"client_assertion": "test_jwt"}


class TestMsalSecretStore(unittest.TestCase):

    test_sp = {
        'client_id': 'myapp',
        'tenant': 'mytenant',
        'client_secret': 'test_secret'
    }

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_load_entry(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        secret_store = ServicePrincipalStore(None, None)
        store._content = [self.test_sp]

        entry = secret_store.load_entry("myapp", "mytenant")
        self.assertEqual(entry['client_secret'], "test_secret")

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_entry(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        secret_store = ServicePrincipalStore(None, None)
        secret_store.save_entry(self.test_sp)

        assert store._content == [self.test_sp]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_entry_add_new(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        test_sp2 = {
            'client_id': "myapp2",
            'tenant': "mytenant2",
            'client_secret': "test_secret2"
        }

        store._content = [self.test_sp]
        secret_store = ServicePrincipalStore(None, None)
        secret_store.save_entry(test_sp2)
        assert store._content == [self.test_sp, test_sp2]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_entry_update_existing(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        store._content = [self.test_sp]
        new_creds = self.test_sp.copy()
        new_creds['client_secret'] = 'test_secret'

        secret_store = ServicePrincipalStore(None, None)
        secret_store.save_entry(new_creds)
        assert store._content == [new_creds]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_remove_entry(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        store._content = [self.test_sp]
        secret_store = ServicePrincipalStore(None, None)
        secret_store.remove_entry('myapp')
        assert store._content == []


class TestUtils(unittest.TestCase):

    def test_get_authority_url(self):
        # AAD
        # Default tenant
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com', None),
                         'https://login.microsoftonline.com/organizations')
        # Trailing slash is stripped
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com/', None),
                         'https://login.microsoftonline.com/organizations')
        # Custom tenant
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com',
                                            '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'),
                         'https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a')

        # ADFS
        # Default tenant
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs', None),
                         'https://adfs.redmond.azurestack.corp.microsoft.com/adfs')
        # Trailing slash is stripped
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs/', None),
                         'https://adfs.redmond.azurestack.corp.microsoft.com/adfs')
        # Tenant ID is discarded
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs',
                                            '601d729d-0000-0000-0000-000000000000'),
                         'https://adfs.redmond.azurestack.corp.microsoft.com/adfs')


class MemoryStore:

    def __init__(self):
        self._content = []

    def save(self, content):
        self._content = content

    def load(self):
        return self._content


if __name__ == '__main__':
    unittest.main()
