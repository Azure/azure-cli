# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest import mock

from azure.cli.core.auth import persistence


class TestLibsecretLabel(unittest.TestCase):

    @staticmethod
    def _build(type):
        with mock.patch.object(persistence.sys, 'platform', 'linux'), \
                mock.patch.object(persistence, 'LibsecretPersistence') as libsecret_mock:
            persistence.build_persistence('/tmp/test_persistence', True, type=type)
        return libsecret_mock.call_args.kwargs

    def test_label_names_the_store(self):
        # Without it libsecret stores an empty label, which shows as a blank row in keyring viewers.
        self.assertEqual(self._build('Token cache')['label'], 'Microsoft Azure CLI - Token cache')
        self.assertEqual(self._build('Secret store')['label'], 'Microsoft Azure CLI - Secret store')

    def test_label_falls_back_to_the_schema_name(self):
        self.assertEqual(self._build(None)['label'], 'Microsoft Azure CLI')


class TestEncryptionFallbackWarning(unittest.TestCase):
    """The plaintext fallback warning is shown at sign-in, not by each persistence build."""

    def setUp(self):
        persistence._encryption_fallback = False
        self.addCleanup(setattr, persistence, '_encryption_fallback', False)

    @staticmethod
    def _build_with_libsecret_unavailable():
        with mock.patch.object(persistence.sys, 'platform', 'linux'), \
                mock.patch.object(persistence, 'LibsecretPersistence', side_effect=ImportError('no libsecret')):
            return persistence.build_persistence('/tmp/test_persistence', True, type='Token cache')

    def test_fallback_is_silent_but_recorded(self):
        with mock.patch.object(persistence.logger, 'warning') as warning_mock:
            store = self._build_with_libsecret_unavailable()

        self.assertIsInstance(store, persistence.FilePersistence)
        warning_mock.assert_not_called()
        self.assertTrue(persistence._encryption_fallback)

    def test_fallback_reason_goes_to_the_debug_log(self):
        # The warning says the credentials are in plaintext; only this says what went wrong, and
        # it is all a user has to go on when the keyring is meant to be working.
        with mock.patch.object(persistence.logger, 'debug') as debug_mock:
            self._build_with_libsecret_unavailable()

        logged = ' '.join(str(call) for call in debug_mock.call_args_list)
        self.assertIn('Failed to initialize LibsecretPersistence', logged)
        self.assertIn('no libsecret', logged)

    def test_warning_shown_at_sign_in(self):
        # Token cache and secret store both fall back, but sign-in warns once.
        self._build_with_libsecret_unavailable()
        self._build_with_libsecret_unavailable()

        # az's own CI sets TF_BUILD/GITHUB_ACTIONS, which would suppress the warning.
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            persistence.warn_if_encryption_unavailable()

        warning_mock.assert_called_once_with(persistence.ENCRYPTION_FALLBACK_WARNING)

    def test_no_warning_in_a_managed_environment(self):
        # Cloud Shell and CI agents can't have an OS credential store installed, so the advice
        # to enable encryption is unactionable there.
        for name, value in [('ACC_CLOUD', 'PROD'), ('GITHUB_ACTIONS', 'true'), ('TF_BUILD', 'True')]:
            with self.subTest(variable=name):
                self._build_with_libsecret_unavailable()

                with mock.patch.dict(os.environ, {name: value}, clear=True), \
                        mock.patch.object(persistence.logger, 'warning') as warning_mock:
                    persistence.warn_if_encryption_unavailable()

                warning_mock.assert_not_called()

    def test_no_warning_without_fallback(self):
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            persistence.warn_if_encryption_unavailable()

        warning_mock.assert_not_called()

    def test_no_warning_when_encryption_opted_out(self):
        with mock.patch.object(persistence.sys, 'platform', 'linux'):
            store = persistence.build_persistence('/tmp/test_persistence', False, type='Token cache')

        self.assertIsInstance(store, persistence.FilePersistence)
        self.assertFalse(persistence._encryption_fallback)


class TestPlaintextClear(unittest.TestCase):
    """With encryption off, clearing must not touch the OS credential store.

    Opting out of core.encrypt_token_cache opts out of the keyring prompt, and saving an empty
    payload to libsecret or Keychain is what would raise it. The signal file stays behind, so a
    later clear with encryption on still finds the payload.
    """

    LOCATION = '/tmp/test_persistence'

    def setUp(self):
        persistence._encryption_fallback = False
        self.addCleanup(setattr, persistence, '_encryption_fallback', False)

    def _erase(self, signal_file_exists=False, warn_if_credentials_may_remain=False):
        built = mock.MagicMock()
        built.is_encrypted = False
        built.get_location.return_value = self.LOCATION + persistence.file_extension_plaintext
        with mock.patch.object(persistence, 'build_persistence', return_value=built), \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence.os.path, 'exists', return_value=signal_file_exists), \
                mock.patch.object(persistence, '_try_remove') as remove_mock, \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            result = persistence.erase_persistence(
                self.LOCATION, False, type='Token cache',
                warn_if_credentials_may_remain=warn_if_credentials_may_remain)
        return result, built, remove_mock, warning_mock

    def test_credential_store_is_left_alone(self):
        result, built, _, _ = self._erase()

        self.assertTrue(result)
        built.save.assert_not_called()

    def test_signal_file_is_kept(self):
        # Removing it would orphan the payload the clear could not reach.
        _, _, remove_mock, _ = self._erase()

        self.assertNotIn(mock.call(self.LOCATION + persistence.file_extension_signal),
                         remove_mock.call_args_list)

    def test_the_other_files_are_removed(self):
        # Including a .bin written while encryption was on.
        _, _, remove_mock, _ = self._erase()

        for extension in (persistence.file_extension_plaintext, persistence.file_extension_encrypted):
            self.assertIn(mock.call(self.LOCATION + extension), remove_mock.call_args_list)

    def test_a_leftover_signal_file_warns_about_the_credential_store(self):
        _, _, _, warning_mock = self._erase(signal_file_exists=True,
                                            warn_if_credentials_may_remain=True)

        warning_mock.assert_called_once()
        message = warning_mock.call_args[0][0]
        self.assertIn('OS credential store', message)
        self.assertIn('core.encrypt_token_cache', message)

    def test_only_the_asked_location_warns(self):
        # az account clear erases two locations, but the warning is about the store, not the file.
        _, _, _, warning_mock = self._erase(signal_file_exists=True)

        warning_mock.assert_not_called()

    def test_no_warning_when_encryption_was_never_used(self):
        _, _, _, warning_mock = self._erase(signal_file_exists=False,
                                            warn_if_credentials_may_remain=True)

        warning_mock.assert_not_called()

    def test_a_fallback_is_not_told_to_enable_encryption(self):
        # Encryption is already on here; the keyring is what is broken.
        persistence._encryption_fallback = True
        _, _, _, warning_mock = self._erase(signal_file_exists=True,
                                            warn_if_credentials_may_remain=True)

        message = warning_mock.call_args[0][0]
        self.assertIn('OS credential store', message)
        self.assertNotIn('core.encrypt_token_cache', message)

    def test_encryption_on_erases_and_removes_everything(self):
        built = mock.MagicMock()
        built.is_encrypted = True
        built.get_location.return_value = self.LOCATION + persistence.file_extension_signal
        with mock.patch.object(persistence, 'build_persistence', return_value=built), \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence.os.path, 'exists', return_value=True), \
                mock.patch.object(persistence, '_try_remove') as remove_mock, \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            persistence.erase_persistence(self.LOCATION, True, type='Token cache',
                                          warn_if_credentials_may_remain=True)

        built.save.assert_called_once()
        warning_mock.assert_not_called()
        self.assertEqual(
            [mock.call(self.LOCATION + e) for e in persistence.file_extensions],
            remove_mock.call_args_list)

    def test_only_the_signal_file_is_left_behind(self):
        # End to end with a real _try_remove, whichever setting wrote the files.
        with tempfile.TemporaryDirectory() as directory:
            location = os.path.join(directory, 'msal_token_cache')
            for extension in persistence.file_extensions:
                open(location + extension, 'w').close()  # pylint: disable=consider-using-with

            with mock.patch.object(persistence.sys, 'platform', 'linux'):
                result = persistence.erase_persistence(location, False, type='Token cache')

            self.assertTrue(result)
            left = sorted(f for f in os.listdir(directory) if not f.endswith('.lockfile'))
            self.assertEqual(['msal_token_cache' + persistence.file_extension_signal], left)


class TestErasePersistence(unittest.TestCase):
    """With encryption on, clearing must empty the payload, not just remove the files.

    On Linux and macOS the credential is held by libsecret or Keychain and the file is only a
    modification signal, so removing files alone would leave the credential behind.
    """

    def test_payload_is_overwritten_through_the_persistence(self):
        built = mock.MagicMock()
        built.is_encrypted = True
        built.get_location.return_value = '/tmp/test_persistence.sig'
        with mock.patch.object(persistence, 'build_persistence', return_value=built) as build_mock, \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence, '_try_remove'):
            result = persistence.erase_persistence('/tmp/test_persistence', True,
                                                   type='Secret store', empty_payload='[]')

        self.assertTrue(result)
        build_mock.assert_called_once_with('/tmp/test_persistence', True, type='Secret store')
        built.save.assert_called_once_with('[]')

    def test_files_are_removed_under_the_same_lock_as_the_erase(self):
        # A login landing between the erase and the removal would leave a credential in the OS
        # credential store that the removed signal file no longer points at.
        built = mock.MagicMock()
        built.is_encrypted = True
        built.get_location.return_value = '/tmp/test_persistence.sig'
        calls = []
        with mock.patch.object(persistence, 'build_persistence', return_value=built), \
                mock.patch.object(persistence, 'CrossPlatLock') as lock_mock, \
                mock.patch.object(persistence, '_try_remove') as remove_mock:
            lock_mock.return_value.__enter__.side_effect = lambda: calls.append('lock')
            lock_mock.return_value.__exit__.side_effect = lambda *a: calls.append('unlock')
            built.save.side_effect = lambda _: calls.append('save')
            remove_mock.side_effect = lambda path: calls.append('remove')
            persistence.erase_persistence('/tmp/test_persistence', True, type='Token cache')

        lock_mock.assert_called_once_with('/tmp/test_persistence.sig.lockfile')
        self.assertEqual(calls[0], 'lock')
        self.assertEqual(calls[-1], 'unlock')
        # The erase must precede the removal, or the save would recreate the removed files.
        self.assertLess(calls.index('save'), calls.index('remove'))
        self.assertEqual(
            [mock.call('/tmp/test_persistence' + e) for e in persistence.file_extensions],
            remove_mock.call_args_list)

    def test_failure_to_erase_warns_and_leaves_everything_alone(self):
        # The realistic failure is another az process holding the lock. Removing the files it just
        # wrote would hide its credential instead of removing it, so the clear is all-or-nothing
        # and the user is told to retry.
        built = mock.MagicMock()
        built.is_encrypted = True
        built.get_location.return_value = '/tmp/test_persistence.sig'
        built.save.side_effect = Exception('AlreadyLocked')
        with mock.patch.object(persistence, 'build_persistence', return_value=built), \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence, '_try_remove') as remove_mock, \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            result = persistence.erase_persistence('/tmp/test_persistence', True,
                                                   type='Token cache')

        self.assertFalse(result)
        warning_mock.assert_called_once()
        remove_mock.assert_not_called()

    def test_removal_survives_a_locked_file(self):
        # On Windows, removing a file another az process holds open raises a sharing violation.
        with mock.patch.object(persistence.os, 'remove', side_effect=PermissionError('in use')):
            persistence._try_remove('/tmp/test_persistence.bin')


if __name__ == '__main__':
    unittest.main()
