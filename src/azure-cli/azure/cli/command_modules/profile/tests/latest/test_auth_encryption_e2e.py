# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Live tests for credential persistence encryption, using service principal authentication.

These tests exercise the real OS credential store (Windows DPAPI, macOS Keychain, Linux libsecret),
so they cannot be recorded. On Linux they need a working D-Bus session and an unlocked keyring;
where that is unavailable the CLI falls back to plaintext and the encryption tests are skipped.

Required environment variables:
    AZURE_CLI_TEST_DEV_SP_NAME      service principal app ID
    AZURE_CLI_TEST_DEV_SP_PASSWORD  service principal secret
    AZURE_CLI_TEST_DEV_SP_TENANT    tenant ID of the service principal
"""

import json
import os
import unittest

from azure.cli.core._environment import get_config_dir
from azure.cli.core.auth.persistence import (file_extension_encrypted, file_extension_plaintext,
                                             file_extension_signal)
from azure.cli.testsdk import LiveScenarioTest

TOKEN_CACHE = 'msal_token_cache'
SECRET_STORE = 'service_principal_entries'

SP_NAME = os.environ.get('AZURE_CLI_TEST_DEV_SP_NAME')
SP_PASSWORD = os.environ.get('AZURE_CLI_TEST_DEV_SP_PASSWORD')
SP_TENANT = os.environ.get('AZURE_CLI_TEST_DEV_SP_TENANT')

sp_configured = unittest.skipUnless(
    SP_NAME and SP_PASSWORD and SP_TENANT,
    'Set AZURE_CLI_TEST_DEV_SP_NAME/PASSWORD/TENANT to run service principal live tests')


def _path(name, extension):
    return os.path.join(get_config_dir(), name + extension)


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


class CredentialEncryptionScenarioTest(LiveScenarioTest):
    """Covers encryption-by-default, the persistence file extensions, and the isolation between
    the token cache and the secret store."""

    def setUp(self):
        super().setUp()
        self.cmd('az account clear')
        self._remove_persistence_files()
        self._reset_persistence_cache()

    def tearDown(self):
        # account clear rather than logout: it is idempotent, so it also works for the tests that
        # skipped before logging in.
        self.cmd('az account clear')
        self.cmd('az config unset core.encrypt_token_cache')
        self._remove_persistence_files()
        super().tearDown()

    def _remove_persistence_files(self):
        for name in (TOKEN_CACHE, SECRET_STORE):
            for extension in (file_extension_encrypted, file_extension_plaintext, file_extension_signal):
                try:
                    os.remove(_path(name, extension))
                except FileNotFoundError:
                    pass

    @staticmethod
    def _reset_persistence_cache():
        """Drop the persistence singletons that Identity holds in class attributes.

        Each real CLI invocation is a new process that re-reads the credential store. These tests run
        in one process, so without this the first test's persistence would be reused by the rest,
        hiding both decryption failures and config changes.
        """
        from azure.cli.core.auth.identity import Identity
        Identity._msal_token_cache = None
        Identity._service_principal_store_instance = None

    def _login_sp(self):
        self.kwargs.update({'sp': SP_NAME, 'password': SP_PASSWORD, 'tenant': SP_TENANT})
        self.cmd('az login --service-principal -u {sp} -p {password} --tenant {tenant}')

    @staticmethod
    def _encryption_available():
        """Ask the persistence layer whether the OS credential store can be used.

        build_persistence falls back to plaintext FilePersistence when the store is unavailable
        (no D-Bus session, locked keyring, missing gir1.2-secret-1), so is_encrypted reports the
        real outcome. Probing beats inferring from which file appeared, because it also works
        before a login has happened.
        """
        from azure.cli.core.auth.persistence import build_persistence
        probe = os.path.join(get_config_dir(), 'encryption_probe')
        try:
            return build_persistence(probe, True).is_encrypted
        finally:
            for extension in (file_extension_encrypted, file_extension_plaintext, file_extension_signal):
                try:
                    os.remove(probe + extension)
                except FileNotFoundError:
                    pass

    def _skip_without_encryption(self):
        if not self._encryption_available():
            self.skipTest('OS credential store unavailable, CLI falls back to plaintext')

    @sp_configured
    def test_sp_login_encrypts_credentials_by_default(self):
        """Encryption is on by default, and neither the access token nor the SP secret is
        readable on disk."""
        self._skip_without_encryption()
        self._login_sp()

        # Windows keeps the ciphertext in a file; macOS/Linux keep only a signal file, because the
        # payload lives in Keychain/libsecret.
        if os.name == 'nt':
            cache_file = _path(TOKEN_CACHE, file_extension_encrypted)
            secret_file = _path(SECRET_STORE, file_extension_encrypted)
        else:
            cache_file = _path(TOKEN_CACHE, file_extension_signal)
            secret_file = _path(SECRET_STORE, file_extension_signal)
            self.assertEqual(os.path.getsize(cache_file), 0, 'signal file must not hold any payload')
            self.assertEqual(os.path.getsize(secret_file), 0, 'signal file must not hold any payload')

        self.assertTrue(os.path.isfile(cache_file))
        self.assertTrue(os.path.isfile(secret_file))

        # No plaintext persistence should have been created alongside.
        self.assertFalse(os.path.isfile(_path(TOKEN_CACHE, file_extension_plaintext)))
        self.assertFalse(os.path.isfile(_path(SECRET_STORE, file_extension_plaintext)))

        # The SP secret and a live access token must not appear anywhere in the config dir.
        access_token = self.cmd('az account get-access-token').get_output_in_json()['accessToken']
        for secret in (SP_PASSWORD, access_token):
            for name in (TOKEN_CACHE, SECRET_STORE):
                for extension in (file_extension_encrypted, file_extension_signal):
                    path = _path(name, extension)
                    if os.path.isfile(path):
                        self.assertNotIn(secret.encode(), _read(path))

    @sp_configured
    def test_encrypted_credentials_survive_new_process(self):
        """The credentials written to the OS store are readable back by a separate CLI process,
        proving encrypt and decrypt both work end to end."""
        self._skip_without_encryption()
        self._login_sp()

        # Reads the persisted token cache from a new process, without re-authenticating.
        self._reset_persistence_cache()
        first = self.cmd('az account get-access-token').get_output_in_json()
        self.assertTrue(first['accessToken'])

        # Reads the persisted SP entry: refreshing a SP token requires the stored secret, so this
        # fails if the secret store cannot be decrypted, or if it was overwritten by the token cache.
        self._reset_persistence_cache()
        self.cmd('az account get-access-token --scope https://graph.microsoft.com/.default')

        accounts = self.cmd('az account list').get_output_in_json()
        self.assertTrue(any(a['user']['name'] == SP_NAME for a in accounts))

    @sp_configured
    def test_token_cache_and_secret_store_do_not_collide(self):
        """Regression test: the token cache and the secret store must occupy distinct entries in the
        OS credential store. Sharing one entry made the secret store return the token cache JSON,
        which surfaced as a TypeError on the next command."""
        self._skip_without_encryption()
        self._login_sp()

        from azure.cli.core.auth.persistence import load_persisted_token_cache, load_secret_store

        cache = load_persisted_token_cache(os.path.join(get_config_dir(), TOKEN_CACHE), True)
        store = load_secret_store(os.path.join(get_config_dir(), SECRET_STORE), True)

        # Each store must return its own schema: a list of SP entries vs. MSAL access tokens.
        entries = store.load()
        self.assertIsInstance(entries, list)
        self.assertTrue(entries, 'service principal entry was not persisted')
        for entry in entries:
            self.assertIsInstance(entry, dict, 'secret store returned token cache content')
        self.assertTrue(any(e.get('client_id') == SP_NAME for e in entries))

        self.assertTrue(cache.find(cache.CredentialType.ACCESS_TOKEN),
                        'token cache returned no access token')

    @sp_configured
    def test_opt_out_of_encryption(self):
        """core.encrypt_token_cache=false keeps the legacy plaintext JSON persistence."""
        self.cmd('az config set core.encrypt_token_cache=false')
        self._remove_persistence_files()
        self._reset_persistence_cache()
        self._login_sp()

        cache_file = _path(TOKEN_CACHE, file_extension_plaintext)
        self.assertTrue(os.path.isfile(cache_file))
        self.assertTrue(json.loads(_read(cache_file)), 'plaintext token cache should be valid JSON')

        self.assertFalse(os.path.isfile(_path(TOKEN_CACHE, file_extension_encrypted)))
        self.assertFalse(os.path.isfile(_path(TOKEN_CACHE, file_extension_signal)))

        self.cmd('az account get-access-token')


if __name__ == '__main__':
    unittest.main()
