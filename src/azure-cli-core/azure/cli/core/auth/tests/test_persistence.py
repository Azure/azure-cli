# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest import mock

from azure.cli.core.auth import persistence


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


class TestEraseOsCredentialStore(unittest.TestCase):
    """A clear must not leave a credential in the OS credential store.

    On Linux and macOS the payload lives in libsecret or Keychain and the file is only a signal, so
    a clear run with core.encrypt_token_cache off would remove the signal and leave the credential
    readable as soon as the setting is turned back on.
    """

    LOCATION = '/tmp/test_persistence'

    @staticmethod
    def _persistence_mock(is_encrypted, extension):
        built = mock.MagicMock()
        built.is_encrypted = is_encrypted
        built.get_location.return_value = TestEraseOsCredentialStore.LOCATION + extension
        return built

    def _erase(self, encrypt=False, platform='linux', os_store=None):
        """Run a clear with the configured persistence and the OS credential store separated."""
        plaintext = self._persistence_mock(False, persistence.file_extension_plaintext)
        encrypted = os_store if os_store is not None else \
            self._persistence_mock(True, persistence.file_extension_signal)

        def build(location, wants_encryption, type=None):  # pylint: disable=redefined-builtin
            return encrypted if wants_encryption else plaintext

        with mock.patch.object(persistence.sys, 'platform', platform), \
                mock.patch.object(persistence, 'build_persistence', side_effect=build), \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence, '_try_remove') as remove_mock, \
                mock.patch.object(persistence.logger, 'warning') as warning_mock:
            result = persistence.erase_persistence(self.LOCATION, encrypt, type='Secret store',
                                                   empty_payload='[]')
        return result, plaintext, encrypted, remove_mock, warning_mock

    def test_encrypted_payload_is_erased_when_encryption_is_off(self):
        # The case a plain 'az account clear' used to miss entirely.
        result, plaintext, encrypted, _, warning_mock = self._erase(encrypt=False)

        self.assertTrue(result)
        plaintext.save.assert_called_once_with('[]')
        encrypted.save.assert_called_once_with('[]')
        warning_mock.assert_not_called()

    def test_configured_encrypted_store_is_erased_once(self):
        # With encryption on, the configured persistence already is the OS credential store.
        result, _, encrypted, _, warning_mock = self._erase(encrypt=True)

        self.assertTrue(result)
        encrypted.save.assert_called_once_with('[]')
        warning_mock.assert_not_called()

    def test_windows_needs_no_second_pass(self):
        # The DPAPI file is the ciphertext, so removing the files is the whole of the erase.
        result, plaintext, encrypted, _, warning_mock = self._erase(encrypt=False, platform='win32')

        self.assertTrue(result)
        plaintext.save.assert_called_once_with('[]')
        encrypted.save.assert_not_called()
        warning_mock.assert_not_called()

    def test_unreachable_credential_store_is_skipped(self):
        # Falling back means the keyring cannot be reached, so there is nothing that can be done
        # about whatever it holds. The plaintext clear must still go ahead.
        fallback = self._persistence_mock(False, persistence.file_extension_plaintext)
        result, plaintext, _, remove_mock, warning_mock = self._erase(encrypt=False, os_store=fallback)

        self.assertTrue(result)
        plaintext.save.assert_called_once_with('[]')
        remove_mock.assert_called()
        warning_mock.assert_not_called()

    def test_a_failing_credential_store_does_not_fail_the_clear(self):
        # Best effort, like _try_remove: the files still have to go, and the caller still succeeds.
        encrypted = self._persistence_mock(True, persistence.file_extension_signal)
        encrypted.save.side_effect = Exception('keyring is locked')
        with mock.patch.object(persistence.logger, 'debug') as debug_mock:
            result, plaintext, _, remove_mock, warning_mock = self._erase(
                encrypt=False, os_store=encrypted)

        self.assertTrue(result)
        plaintext.save.assert_called_once_with('[]')
        remove_mock.assert_called()
        warning_mock.assert_not_called()
        self.assertTrue(any('OS credential store' in str(call) for call in debug_mock.call_args_list))

    def test_credential_store_is_erased_before_the_files_are_removed(self):
        # Keychain and libsecret touch the signal file on save, so erasing after the removal would
        # put the file back. The order is what keeps the clear from leaving one behind.
        plaintext = self._persistence_mock(False, persistence.file_extension_plaintext)
        encrypted = self._persistence_mock(True, persistence.file_extension_signal)
        calls = []
        plaintext.save.side_effect = lambda _: calls.append('save plaintext')
        encrypted.save.side_effect = lambda _: calls.append('save credential store')

        def build(location, wants_encryption, type=None):  # pylint: disable=redefined-builtin
            return encrypted if wants_encryption else plaintext

        with mock.patch.object(persistence.sys, 'platform', 'linux'), \
                mock.patch.object(persistence, 'build_persistence', side_effect=build), \
                mock.patch.object(persistence, 'CrossPlatLock'), \
                mock.patch.object(persistence, '_try_remove',
                                  side_effect=lambda path: calls.append('remove')):
            persistence.erase_persistence(self.LOCATION, False, type='Secret store')

        self.assertLess(calls.index('save credential store'), calls.index('remove'))

    def test_no_signal_file_is_left_behind(self):
        # The failure the order above prevents, reproduced end to end: a real save touches the
        # signal file, and a real _try_remove has to be the last thing that runs.
        with tempfile.TemporaryDirectory() as directory:
            location = os.path.join(directory, 'service_principal_entries')
            plaintext = self._persistence_mock(False, persistence.file_extension_plaintext)
            encrypted = self._persistence_mock(True, persistence.file_extension_signal)
            plaintext.get_location.return_value = location + persistence.file_extension_plaintext
            encrypted.get_location.return_value = location + persistence.file_extension_signal

            def touch(path):
                return lambda _: open(path, 'w').close()  # pylint: disable=consider-using-with

            plaintext.save.side_effect = touch(location + persistence.file_extension_plaintext)
            encrypted.save.side_effect = touch(location + persistence.file_extension_signal)

            def build(location_, wants_encryption, type=None):  # pylint: disable=redefined-builtin
                return encrypted if wants_encryption else plaintext

            with mock.patch.object(persistence.sys, 'platform', 'linux'), \
                    mock.patch.object(persistence, 'build_persistence', side_effect=build), \
                    mock.patch.object(persistence, 'CrossPlatLock'):
                persistence.erase_persistence(location, False, type='Secret store')

            self.assertEqual([], os.listdir(directory), 'the clear left a persistence file behind')


class TestErasePersistence(unittest.TestCase):
    """Clearing all accounts must empty the payload, not just remove the files.

    On Linux and macOS the credential is held by libsecret or Keychain and the file is only a
    modification signal, so removing files alone would leave the credential behind.
    """

    def test_payload_is_overwritten_through_the_persistence(self):
        built = mock.MagicMock()
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
