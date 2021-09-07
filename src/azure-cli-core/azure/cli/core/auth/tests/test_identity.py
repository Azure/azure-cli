# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.core.auth.identity import Identity, ServicePrincipalAuth, ServicePrincipalStore
from knack.util import CLIError


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

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_load_credential(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        secret_store = ServicePrincipalStore(None)
        store._content = [test_sp]

        entry = secret_store.load_credential("myapp", "mytenant")
        self.assertEqual(entry['secret'], "Secret")

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_credential(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        secret_store = ServicePrincipalStore(None)
        secret_store.save_credential(test_sp)

        assert store._content == [test_sp]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_credential_add_new(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

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

        store._content = [test_sp]
        secret_store = ServicePrincipalStore(None)
        secret_store.save_credential(test_sp2)
        assert store._content == [test_sp, test_sp2]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_save_credential_update_existing(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }

        store._content = [test_sp]
        new_creds = test_sp.copy()
        new_creds['accessToken'] = 'Secret2'

        secret_store = ServicePrincipalStore(None)
        secret_store.save_credential(new_creds)
        assert store._content == [new_creds]

    @mock.patch('azure.cli.core.auth.persistence.load_secret_store')
    def test_remove_credential(self, load_secret_store_mock):
        store = MemoryStore()
        load_secret_store_mock.return_value = store

        test_sp = {
            "servicePrincipalId": "myapp",
            "servicePrincipalTenant": "mytenant",
            "accessToken": "Secret"
        }

        store._content = [test_sp]
        secret_store = ServicePrincipalStore(None)
        secret_store.remove_credential('myapp')
        assert store._content == []


class MemoryStore:

    def __init__(self):
        self._content = []

    def save(self, content):
        self._content = content

    def load(self):
        return self._content


if __name__ == '__main__':
    unittest.main()
