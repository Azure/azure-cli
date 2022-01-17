# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import unittest
from unittest import mock

from azure.cli.core.auth.identity import (Identity, ServicePrincipalAuth, ServicePrincipalStore,
                                          _get_authority_url)
from knack.util import CLIError


class TestIdentity(unittest.TestCase):

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__")
    def test_login_with_service_principal_secret(self, init_mock, acquire_token_for_client_mock,
                                                 save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='my-tenant')

        identity.login_with_service_principal("00000000-0000-0000-0000-000000000000",
                                              {"client_secret": "test_secret"}, "openid")

        assert init_mock.call_args[0][0] == '00000000-0000-0000-0000-000000000000'
        assert init_mock.call_args[1]['client_credential'] == 'test_secret'
        assert init_mock.call_args[1]['authority'] == 'https://login.microsoftonline.com/my-tenant'

        assert save_entry_mock.call_args[0][0] == {
            'tenant': 'my-tenant',
            'client_id': '00000000-0000-0000-0000-000000000000',
            'client_secret': 'test_secret'
        }

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__")
    def test_login_with_service_principal_certificate(self, init_mock, acquire_token_for_client_mock,
                                                      save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='my-tenant')

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')

        with open(test_cert_file) as cert_file:
            cert_file_string = cert_file.read()

        identity.login_with_service_principal("00000000-0000-0000-0000-000000000000",
                                              {'certificate': test_cert_file}, 'openid')

        assert init_mock.call_args[0][0] == '00000000-0000-0000-0000-000000000000'
        assert init_mock.call_args[1]['client_credential'] == {
                'private_key': cert_file_string,
                'thumbprint': 'F06A53848BBE714A4290D69D335279C1D01073FD'
            }
        assert init_mock.call_args[1]['authority'] == 'https://login.microsoftonline.com/my-tenant'

        assert save_entry_mock.call_args[0][0] == {
            'tenant': 'my-tenant',
            'client_id': '00000000-0000-0000-0000-000000000000',
            'certificate': test_cert_file
        }

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__")
    def test_login_with_service_principal_certificate_sn_issuer(self, init_mock, acquire_token_for_client_mock,
                                                                save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='my-tenant')

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')

        with open(test_cert_file) as cert_file:
            cert_file_string = cert_file.read()

        match = re.search(r'-+BEGIN CERTIFICATE-+(?P<public>[^-]+)-+END CERTIFICATE-+', cert_file_string, re.I)
        public_certificate = match.group().strip()

        identity.login_with_service_principal("00000000-0000-0000-0000-000000000000",
                                              {
                                                  'certificate': test_cert_file,
                                                  'use_cert_sn_issuer': True,
                                              }, "openid")

        assert init_mock.call_args[0][0] == '00000000-0000-0000-0000-000000000000'
        assert init_mock.call_args[1]['client_credential'] == {
            "private_key": cert_file_string,
            "thumbprint": 'F06A53848BBE714A4290D69D335279C1D01073FD',
            "public_certificate": public_certificate
        }
        assert init_mock.call_args[1]['authority'] == 'https://login.microsoftonline.com/my-tenant'

        assert save_entry_mock.call_args[0][0] == {
            'tenant': 'my-tenant',
            'client_id': '00000000-0000-0000-0000-000000000000',
            'certificate': test_cert_file,
            'use_cert_sn_issuer': True
        }

    def test_login_with_service_principal_certificate_cert_err(self):
        import os
        identity = Identity('https://login.microsoftonline.com')
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'err_sp_cert.pem')

        with self.assertRaisesRegex(CLIError, "Invalid certificate"):
            identity.login_with_service_principal("00000000-0000-0000-0000-000000000000",
                                                  {"certificate": test_cert_file}, "openid")


class TestServicePrincipalAuth(unittest.TestCase):

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1', {'client_secret': "test_secret"})
        result = sp_auth.get_entry_to_persist()

        assert result == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_secret': 'test_secret'
        }

    def test_service_principal_auth_certificate(self):
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

    def test_service_principal_auth_certificate_sn_issuer(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(curr_dir, 'sp_cert.pem')

        with open(test_cert_file) as cert_file:
            cert_file_string = cert_file.read()
        match = re.search(r'-+BEGIN CERTIFICATE-+(?P<public>[^-]+)-+END CERTIFICATE-+', cert_file_string, re.I)
        public_certificate = match.group().strip()

        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1',
                                                             {
                                                                 'certificate': test_cert_file,
                                                                 'use_cert_sn_issuer': True,
                                                             })

        result = sp_auth.get_entry_to_persist()
        # To compute the thumb print:
        #   openssl x509 -in sp_cert.pem -noout -fingerprint
        assert sp_auth.thumbprint == 'F06A53848BBE714A4290D69D335279C1D01073FD'
        assert sp_auth.public_certificate == public_certificate

        assert result == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': test_cert_file,
            'use_cert_sn_issuer': True,
        }

    def test_build_credential(self):
        # secret
        cred = ServicePrincipalAuth.build_credential("test_secret")
        assert cred == {"client_secret": "test_secret"}

        # secret with '~', which is preserved as-is
        cred = ServicePrincipalAuth.build_credential("~test_secret")
        assert cred == {"client_secret": "~test_secret"}

        # certificate
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'sp_cert.pem')
        cred = ServicePrincipalAuth.build_credential(test_cert_file)
        assert cred == {'certificate': test_cert_file}

        # certificate path with '~', which expands to HOME folder
        import shutil
        home = os.path.expanduser('~')
        home_cert = os.path.join(home, 'sp_cert.pem')  # C:\Users\username\sp_cert.pem
        shutil.copyfile(test_cert_file, home_cert)
        cred = ServicePrincipalAuth.build_credential(os.path.join('~', 'sp_cert.pem'))  # ~\sp_cert.pem
        assert cred == {'certificate': home_cert}
        os.remove(home_cert)

        cred = ServicePrincipalAuth.build_credential(test_cert_file, use_cert_sn_issuer=True)
        assert cred == {'certificate': test_cert_file, 'use_cert_sn_issuer': True}

        # client assertion
        cred = ServicePrincipalAuth.build_credential(client_assertion="test_jwt")
        assert cred == {"client_assertion": "test_jwt"}


class TestServicePrincipalStore(unittest.TestCase):

    test_sp = {
        'client_id': 'myapp',
        'tenant': 'mytenant',
        'client_secret': 'test_secret'
    }

    def test_load_entry(self):
        store = MemoryStore()

        secret_store = ServicePrincipalStore(store)
        store._content = [self.test_sp]

        entry = secret_store.load_entry("myapp", "mytenant")
        self.assertEqual(entry['client_secret'], "test_secret")

    def test_save_entry(self):
        store = MemoryStore()

        secret_store = ServicePrincipalStore(store)
        secret_store.save_entry(self.test_sp)

        assert store._content == [self.test_sp]

    def test_save_entry_add_new(self):
        store = MemoryStore()

        test_sp2 = {
            'client_id': "myapp2",
            'tenant': "mytenant2",
            'client_secret': "test_secret2"
        }

        store._content = [self.test_sp]
        secret_store = ServicePrincipalStore(store)
        secret_store.save_entry(test_sp2)
        assert store._content == [self.test_sp, test_sp2]

    def test_save_entry_update_existing(self):
        store = MemoryStore()

        store._content = [self.test_sp]
        new_creds = self.test_sp.copy()
        new_creds['client_secret'] = 'test_secret'

        secret_store = ServicePrincipalStore(store)
        secret_store.save_entry(new_creds)
        assert store._content == [new_creds]

    def test_remove_entry(self):
        store = MemoryStore()

        store._content = [self.test_sp]
        secret_store = ServicePrincipalStore(store)
        secret_store.remove_entry('myapp')
        assert store._content == []


class TestUtils(unittest.TestCase):

    def test_get_authority_url(self):
        # AAD
        # Default tenant
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com', None),
                         ('https://login.microsoftonline.com/organizations', False))
        # Trailing slash is stripped
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com/', None),
                         ('https://login.microsoftonline.com/organizations', False))
        # Custom tenant
        self.assertEqual(_get_authority_url('https://login.microsoftonline.com',
                                            '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'),
                         ('https://login.microsoftonline.com/54826b22-38d6-4fb2-bad9-b7b93a3e9c5a', False))

        # ADFS
        # Default tenant
        adfs_expected = ('https://adfs.redmond.azurestack.corp.microsoft.com/adfs', True)
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs', None),
                         adfs_expected)
        # Trailing slash is stripped
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs/', None),
                         adfs_expected)
        # Tenant ID is discarded
        self.assertEqual(_get_authority_url('https://adfs.redmond.azurestack.corp.microsoft.com/adfs',
                                            '601d729d-0000-0000-0000-000000000000'),
                         adfs_expected)


class MemoryStore:

    def __init__(self):
        self._content = []

    def save(self, content):
        self._content = content

    def load(self):
        return self._content


if __name__ == '__main__':
    unittest.main()
