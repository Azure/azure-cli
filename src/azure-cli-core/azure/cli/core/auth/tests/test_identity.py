# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest
from unittest import mock

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
        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        test_file = os.path.join(os.path.dirname(__file__), "test.json")
        with open(test_file, 'w') as f:
            json.dump([test_sp], f)

        build_persistence_mock.return_value = FilePersistence(test_file)
        secret_store = MsalSecretStore(test_file)
        entry = secret_store.load_credential("myapp", "mytenant")
        self.assertEqual(entry['secret'], "Secret")

        try:
            os.remove(test_file)
        except:
            pass

    @mock.patch('azure.cli.core.auth.persistence.build_persistence', autospec=True)
    def test_save_service_principal_secret(self, build_persistence_mock):
        test_sp = {
            'servicePrincipalId': 'myapp',
            'servicePrincipalTenant': 'mytenant',
            'secret': 'Secret'
        }

        test_file = os.path.join(os.path.dirname(__file__), "test.json")
        build_persistence_mock.return_value = FilePersistence(test_file)
        secret_store = MsalSecretStore(test_file)
        secret_store.save_credential(test_sp)

        with open(test_file, 'r') as f:
            result = json.load(f)
        assert result[0] == test_sp

        try:
            os.remove(test_file)
        except:
            pass


if __name__ == '__main__':
    unittest.main()
