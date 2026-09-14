# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import re
import time
import unittest
from unittest import mock

from azure.cli.core.auth.identity import (Identity, ServicePrincipalAuth, ServicePrincipalStore,
                                          FEDERATED_IDENTITY, get_federated_id_token,
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

    def test_service_principal_auth_federated_identity(self):
        # The FEDERATED_IDENTITY sentinel is persisted like a normal client_assertion, ...
        sp_auth = ServicePrincipalAuth.build_from_credential('tenant1', 'sp_id1',
                                                             {'client_assertion': FEDERATED_IDENTITY})
        assert sp_auth.client_assertion == FEDERATED_IDENTITY

        # Verify persist entry keeps the sentinel so later processes can rebuild the callback
        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_assertion': FEDERATED_IDENTITY
        }

        # ... but get_msal_client_credential resolves the sentinel to the refreshing callback (not a string),
        # so MSAL fetches a fresh ID token on every acquisition.
        client_credential = sp_auth.get_msal_client_credential()
        assert client_credential == {'client_assertion': get_federated_id_token}
        assert callable(client_credential['client_assertion'])

    def test_service_principal_auth_federated_token_callback(self):
        # The callback command is persisted so later `az` processes can rebuild the callable.
        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': 'my-get-token-command'})
        assert sp_auth.client_assertion_callback == 'my-get-token-command'

        entry = sp_auth.get_entry_to_persist()
        assert entry == {
            'client_id': 'sp_id1',
            'tenant': 'tenant1',
            'client_assertion_callback': 'my-get-token-command'
        }

        # get_msal_client_credential wraps the command as a refreshing callable (not a static string).
        client_credential = sp_auth.get_msal_client_credential()
        assert callable(client_credential['client_assertion'])

    @mock.patch('subprocess.run')
    def test_federated_token_callback_invokes_command(self, run_mock):
        run_mock.return_value = mock.MagicMock(stdout='fresh_token\n', stderr='')
        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': 'get-token --audience x'})
        callback = sp_auth.get_msal_client_credential()['client_assertion']

        # The callable runs the user command and returns its trimmed stdout each time MSAL calls it.
        assert callback() == 'fresh_token'
        # The command is split into an argv list and run WITHOUT a shell (no shell=True kwarg).
        assert run_mock.call_args.args[0] == ['get-token', '--audience', 'x']
        assert 'shell' not in run_mock.call_args.kwargs

    def test_federated_token_callback_no_shell_interpretation(self):
        # Shell metacharacters must be treated as literal argv, never interpreted by a shell.
        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': "get-token ; rm -rf /"})
        with mock.patch('subprocess.run') as run_mock:
            run_mock.return_value = mock.MagicMock(stdout='tok\n', stderr='')
            sp_auth.get_msal_client_credential()['client_assertion']()
        assert run_mock.call_args.args[0] == ['get-token', ';', 'rm', '-rf', '/']

    def test_federated_token_callback_quoted_argument(self):
        # A quoted argument containing spaces must reach the program without the surrounding quotes.
        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': 'mytool --aud "api://x y"'})
        with mock.patch('subprocess.run') as run_mock:
            run_mock.return_value = mock.MagicMock(stdout='tok\n', stderr='')
            sp_auth.get_msal_client_credential()['client_assertion']()
        assert run_mock.call_args.args[0] == ['mytool', '--aud', 'api://x y']

    @mock.patch('subprocess.run')
    def test_federated_token_callback_empty_output(self, run_mock):
        run_mock.return_value = mock.MagicMock(stdout='   \n', stderr='')
        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': 'get-token'})
        callback = sp_auth.get_msal_client_credential()['client_assertion']
        with self.assertRaisesRegex(CLIError, 'produced no output'):
            callback()

    def test_federated_token_callback_is_thread_safe(self):
        # MSAL may invoke the callback concurrently; the command must not run overlapping.
        import threading
        concurrent = []
        active = [0]
        state_lock = threading.Lock()

        def fake_run(*args, **kwargs):
            with state_lock:
                active[0] += 1
                concurrent.append(active[0])
            time.sleep(0.02)
            with state_lock:
                active[0] -= 1
            return mock.MagicMock(stdout='tok\n', stderr='')

        sp_auth = ServicePrincipalAuth.build_from_credential(
            'tenant1', 'sp_id1', {'client_assertion_callback': 'get-token'})
        callback = sp_auth.get_msal_client_credential()['client_assertion']

        with mock.patch('subprocess.run', side_effect=fake_run):
            threads = [threading.Thread(target=callback) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # The lock must serialize invocations, so peak concurrency never exceeds 1.
        assert max(concurrent) == 1, 'callback ran concurrently: peak={}'.format(max(concurrent))

    def test_build_credential(self):
        # client_secret
        cred = ServicePrincipalAuth.build_credential(client_secret="test_secret")
        assert cred == {"client_secret": "test_secret"}

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

        # client_assertion
        cred = ServicePrincipalAuth.build_credential(client_assertion="test_jwt")
        assert cred == {"client_assertion": "test_jwt"}

        # client_assertion_callback
        cred = ServicePrincipalAuth.build_credential(client_assertion_callback="get-token")
        assert cred == {"client_assertion_callback": "get-token"}


class TestFederatedIdentity(unittest.TestCase):
    """Tests for the OIDC federated-token dispatcher used by 'az login --federated-identity'."""

    @mock.patch.dict(os.environ, {
        'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token?foo=bar',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request_token'
    }, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github(self, get_mock):
        get_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'value': 'fresh_id_token'})

        token = get_federated_id_token()

        assert token == 'fresh_id_token'
        # The audience is appended to the GitHub-provided request URL and the request token is used as bearer.
        called_url = get_mock.call_args.args[0]
        assert called_url.startswith('https://github.example/token?foo=bar&audience=')
        assert 'api%3A//AzureADTokenExchange' in called_url
        assert get_mock.call_args.kwargs['headers']['Authorization'] == 'bearer request_token'
        # A timeout is always passed so a network stall fails fast instead of hanging the CI job.
        assert get_mock.call_args.kwargs['timeout'] is not None

    @mock.patch.dict(os.environ, {
        'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request_token'
    }, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_timeout(self, get_mock):
        import requests
        get_mock.side_effect = requests.exceptions.Timeout()
        with self.assertRaisesRegex(CLIError, 'Timed out'):
            get_federated_id_token()

    @mock.patch.dict(os.environ, {
        'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request_token'
    }, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_url_without_query(self, get_mock):
        # When the request URL has no existing query string, the audience must be appended with '?', not '&'.
        get_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'value': 'fresh_id_token'})

        get_federated_id_token()

        called_url = get_mock.call_args.args[0]
        assert called_url.startswith('https://github.example/token?audience=')
        assert '&audience=' not in called_url

    @mock.patch.dict(os.environ, {
        'ACTIONS_ID_TOKEN_REQUEST_URL': 'https://github.example/token',
        'ACTIONS_ID_TOKEN_REQUEST_TOKEN': 'request_token'
    }, clear=True)
    @mock.patch('requests.get')
    def test_get_federated_id_token_github_http_error(self, get_mock):
        get_mock.return_value = mock.MagicMock(ok=False, status_code=403, reason='Forbidden')
        with self.assertRaisesRegex(CLIError, 'Failed to retrieve an ID token'):
            get_federated_id_token()

    @mock.patch.dict(os.environ, {
        'SYSTEM_OIDCREQUESTURI': 'https://vstoken.dev.azure.com/org/',
        'SYSTEM_ACCESSTOKEN': 'system_access_token',
        'ARM_OIDC_AZURE_SERVICE_CONNECTION_ID': 'sc-guid'
    }, clear=True)
    @mock.patch('requests.post')
    def test_get_federated_id_token_azure_devops(self, post_mock):
        post_mock.return_value = mock.MagicMock(ok=True, json=lambda: {'oidcToken': 'ado_id_token'})

        token = get_federated_id_token()

        assert token == 'ado_id_token'
        called_url = post_mock.call_args.args[0]
        # Trailing slash on the request URI is trimmed; api-version and service connection are appended.
        assert called_url == ('https://vstoken.dev.azure.com/org'
                              '?api-version=7.1&serviceConnectionId=sc-guid')
        headers = post_mock.call_args.kwargs['headers']
        assert headers['Authorization'] == 'bearer system_access_token'
        assert headers['X-TFS-FedAuthRedirect'] == 'Suppress'

    @mock.patch.dict(os.environ, {'SYSTEM_OIDCREQUESTURI': 'https://vstoken.dev.azure.com/org/'}, clear=True)
    def test_get_federated_id_token_azure_devops_missing_env(self):
        # Detected as Azure DevOps, but the access token and service connection ID are missing.
        with self.assertRaisesRegex(CLIError, 'ARM_OIDC_AZURE_SERVICE_CONNECTION_ID'):
            get_federated_id_token()

    @mock.patch.dict(os.environ, {'SYSTEM_TEAMFOUNDATIONCOLLECTIONURI': 'https://dev.azure.com/org'}, clear=True)
    def test_get_federated_id_token_unsupported_provider(self):
        # A DevOps collection URI without the OIDC request URI is not enough to attempt a refresh.
        with self.assertRaisesRegex(CLIError, 'no supported CI/CD OIDC provider'):
            get_federated_id_token()

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_get_federated_id_token_no_provider(self):
        with self.assertRaisesRegex(CLIError, 'no supported CI/CD OIDC provider'):
            get_federated_id_token()


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
