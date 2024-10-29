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

# CERTIFICATE section in sp_cert.pem
PUBLIC_CERTIFICATE = """-----BEGIN CERTIFICATE-----
MIIDtTCCAp2gAwIBAgIJAPMNsT0qjg1ZMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTcwMzEwMDQ0NjEyWhcNMTgwMzEwMDQ0NjEyWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8GA1UEChMYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAxec32tnXNiPz2WBTpv7ccZvYqBR2Gr8vimQbiNgT3aHY/dzV26pYv/88
X5PbkibAr3YXJP64nGI/0MGvFWYi6c6C0Ar6QL/MgRLIGIO8JePTxKu9ZDx+5Crw
beJRQgz7nEtCWsIx5WiIx5/yjUR5AqrNwSxNWo6Ct3E1YWzGyI03gEEr82tEG9Vd
ObIRq05v1hHKTm27xln41JZI1aUMzd/K/pckb6nQLtV6OpOmzZQILMOV95SKJ8+k
1gnxfOX2t9JPgTuiVmwvgYLb1k7Hfqs1/KZt4IyIRkBaXPy2j5Guz09uR1Dg4tOc
oSPwDeN0aQQSucRsk0iaof3DXMfVLQIDAQABo4GnMIGkMB0GA1UdDgQWBBRpCyBM
VgNXHqX5MrBdAQ1Hzf8l7jB1BgNVHSMEbjBsgBRpCyBMVgNXHqX5MrBdAQ1Hzf8l
7qFJpEcwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgTClNvbWUtU3RhdGUxITAfBgNV
BAoTGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZIIJAPMNsT0qjg1ZMAwGA1UdEwQF
MAMBAf8wDQYJKoZIhvcNAQEFBQADggEBAEH/nmErQLSxsMDk3LgTpBY6ibl6xU0k
Lt1wbC+Z3sgpt82oA4BiulcJtTf3IrvBXJNRaB++ChjqRnK8O6uWbBQxvz/V8l+9
g3s49VSaX3QB74Rh1NIfKhUyYlG3yi8qBJA6tlCNNXGQoYvND9Y3gorj+LzH3Eqf
9g2oBm2jWaiPBHjuuUbd+SBS2hQn/i2huWnz1yewrtfVpRwWrQQHa1Qv3ivKDK2H
2LOdn2Xs3/ZGsi1ySfjzxjTbuPhUaEUy+ZfV2dgmqiS//BAWI5opo7TgeplrGk2P
h5Fwbt0FxaqFCNZdrPI7FRnbKZwvGx0A+Zj8ZpNjft3QjuUg+xqMKMs=
-----END CERTIFICATE-----"""


TEST_CERT = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sp_cert.pem')

with open(TEST_CERT) as f:
    CERTIFICATE_STRING = f.read()


class TestIdentity(unittest.TestCase):

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__", return_value=None)
    def test_login_with_service_principal_secret(self, init_mock, acquire_token_for_client_mock,
                                                 save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='tenant1')
        identity.login_with_service_principal("sp_id1", {"client_secret": "test_secret"}, "openid")

        assert init_mock.call_args.args == ('sp_id1',)
        assert init_mock.call_args.kwargs['client_credential'] == 'test_secret'
        assert init_mock.call_args.kwargs['authority'] == 'https://login.microsoftonline.com/tenant1'

        assert save_entry_mock.call_args.args[0] == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_secret': 'test_secret'
        }

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__", return_value=None)
    def test_login_with_service_principal_certificate(self, init_mock, acquire_token_for_client_mock,
                                                      save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='tenant1')
        identity.login_with_service_principal("sp_id1", {'certificate': TEST_CERT}, 'openid')

        assert init_mock.call_args.args == ('sp_id1',)
        assert init_mock.call_args.kwargs['client_credential'] == {
                'private_key': CERTIFICATE_STRING,
                'thumbprint': 'F06A53848BBE714A4290D69D335279C1D01073FD'
            }
        assert init_mock.call_args.kwargs['authority'] == 'https://login.microsoftonline.com/tenant1'

        assert save_entry_mock.call_args[0][0] == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': TEST_CERT
        }

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__", return_value=None)
    def test_login_with_service_principal_certificate_sn_issuer(self, init_mock, acquire_token_for_client_mock,
                                                                save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='tenant1')
        identity.login_with_service_principal("sp_id1",
                                              {
                                                  'certificate': TEST_CERT,
                                                  'use_cert_sn_issuer': True,
                                              }, "openid")

        assert init_mock.call_args.args == ('sp_id1',)
        assert init_mock.call_args.kwargs['client_credential'] == {
            "private_key": CERTIFICATE_STRING,
            "thumbprint": 'F06A53848BBE714A4290D69D335279C1D01073FD',
            "public_certificate": PUBLIC_CERTIFICATE
        }
        assert init_mock.call_args.kwargs['authority'] == 'https://login.microsoftonline.com/tenant1'

        assert save_entry_mock.call_args.args[0] == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': TEST_CERT,
            'use_cert_sn_issuer': True
        }

    def test_login_with_service_principal_certificate_cert_err(self):
        import os
        identity = Identity('https://login.microsoftonline.com')
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'err_sp_cert.pem')

        with self.assertRaisesRegex(CLIError, "Invalid certificate"):
            identity.login_with_service_principal("sp_id1", {"certificate": test_cert_file}, "openid")

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.save_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.acquire_token_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__", return_value=None)
    def test_login_with_service_principal_client_assertion(self, init_mock, acquire_token_for_client_mock,
                                                           save_entry_mock):
        acquire_token_for_client_mock.return_value = {'access_token': "test_token"}

        identity = Identity('https://login.microsoftonline.com', tenant_id='tenant1')
        identity.login_with_service_principal("sp_id1", {'client_assertion': 'test_jwt'}, "openid")

        assert init_mock.call_args.args == ('sp_id1',)
        assert init_mock.call_args.kwargs['client_credential'] == {"client_assertion": 'test_jwt'}
        assert init_mock.call_args.kwargs['authority'] == 'https://login.microsoftonline.com/tenant1'

        assert save_entry_mock.call_args.args[0] == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_assertion': 'test_jwt',
        }

    @mock.patch("msal.application.PublicClientApplication.remove_account")
    @mock.patch("msal.application.PublicClientApplication.get_accounts")
    def test_logout_user(self, get_accounts_mock, remove_account_mock):
        accounts = [
            {
                'home_account_id': '00000000-0000-0000-0000-000000000000.00000000-0000-0000-0000-000000000000',
                'environment': 'login.microsoftonline.com',
                'username': 'test@test.com',
                'account_source': 'broker',
                'authority_type': 'MSSTS',
                'local_account_id': '00000000-0000-0000-0000-000000000000',
                'realm': '00000000-0000-0000-0000-000000000000'
            }
        ]
        get_accounts_mock.return_value = accounts

        identity = Identity('https://login.microsoftonline.com')
        identity.logout_user('test@test.com')
        remove_account_mock.assert_called_with(accounts[0])

    @mock.patch("azure.cli.core.auth.identity.ServicePrincipalStore.remove_entry")
    @mock.patch("msal.application.ConfidentialClientApplication.remove_tokens_for_client")
    @mock.patch("msal.application.ConfidentialClientApplication.__init__", return_value=None)
    def test_logout_service_principal(self, init_mock, remove_tokens_for_client_mock, remove_entry_mock):
        identity = Identity('https://login.microsoftonline.com')
        client_id = 'sp_id1'
        identity.logout_service_principal(client_id)
        assert init_mock.call_args.args[0] == client_id
        remove_tokens_for_client_mock.assert_called_once()
        remove_entry_mock.assert_called_with(client_id)


class TestServicePrincipalAuth(unittest.TestCase):

    def test_service_principal_auth_client_secret(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1', {'client_secret': "test_secret"})

        # Verify persist entry
        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_secret': 'test_secret'
        }

        # Verify msal client_credential
        client_credential = sp_auth.get_msal_client_credential()
        assert client_credential == 'test_secret'

    def test_service_principal_auth_certificate(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1', {'certificate': TEST_CERT})

        # To compute the thumbprint:
        #   openssl x509 -in sp_cert.pem -noout -fingerprint
        assert sp_auth._thumbprint == 'F06A53848BBE714A4290D69D335279C1D01073FD'

        # Verify persist entry
        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': TEST_CERT
        }

        # Verify msal client_credential
        client_credential = sp_auth.get_msal_client_credential()
        assert client_credential == {
            'private_key': CERTIFICATE_STRING,
            'thumbprint': 'F06A53848BBE714A4290D69D335279C1D01073FD'
        }

    def test_service_principal_auth_certificate_sn_issuer(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1',
                                                             {
                                                                 'certificate': TEST_CERT,
                                                                 'use_cert_sn_issuer': True,
                                                             })

        # To compute the thumbprint:
        #   openssl x509 -in sp_cert.pem -noout -fingerprint
        assert sp_auth._thumbprint == 'F06A53848BBE714A4290D69D335279C1D01073FD'
        assert sp_auth._public_certificate == PUBLIC_CERTIFICATE

        # Verify persist entry
        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'certificate': TEST_CERT,
            'use_cert_sn_issuer': True,
        }

        # Verify msal client_credential
        client_credential = sp_auth.get_msal_client_credential()
        assert client_credential == {
            'private_key': CERTIFICATE_STRING,
            'thumbprint': 'F06A53848BBE714A4290D69D335279C1D01073FD',
            'public_certificate': PUBLIC_CERTIFICATE
        }

    def test_service_principal_auth_client_assertion(self):
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1',
                                                             {'client_assertion': 'test_jwt'})
        assert sp_auth.client_assertion == 'test_jwt'

        # Verify persist entry
        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_assertion': 'test_jwt'
        }

        # Verify msal client_credential
        client_credential = sp_auth.get_msal_client_credential()
        assert client_credential == {'client_assertion': 'test_jwt'}

    def test_build_credential(self):
        # secret
        cred = ServicePrincipalAuth.build_credential(secret_or_certificate="test_secret")
        assert cred == {"client_secret": "test_secret"}

        # secret with '~', which is preserved as-is
        cred = ServicePrincipalAuth.build_credential(secret_or_certificate="~test_secret")
        assert cred == {"client_secret": "~test_secret"}

        # certificate as password (deprecated)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'sp_cert.pem')
        cred = ServicePrincipalAuth.build_credential(secret_or_certificate=test_cert_file)
        assert cred == {'certificate': test_cert_file}

        # certificate
        current_dir = os.path.dirname(os.path.realpath(__file__))
        test_cert_file = os.path.join(current_dir, 'sp_cert.pem')
        cred = ServicePrincipalAuth.build_credential(certificate=test_cert_file)
        assert cred == {'certificate': test_cert_file}

        # certificate path with '~', which expands to HOME folder
        import shutil
        home = os.path.expanduser('~')
        home_cert = os.path.join(home, 'sp_cert.pem')  # C:\Users\username\sp_cert.pem
        shutil.copyfile(test_cert_file, home_cert)
        cred = ServicePrincipalAuth.build_credential(certificate=os.path.join('~', 'sp_cert.pem'))  # ~\sp_cert.pem
        assert cred == {'certificate': home_cert}
        os.remove(home_cert)

        # Certificate with use_cert_sn_issuer=True
        cred = ServicePrincipalAuth.build_credential(certificate=test_cert_file, use_cert_sn_issuer=True)
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
