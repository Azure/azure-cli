# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

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

    def test_warning_shown_at_sign_in(self):
        # Token cache and secret store both fall back, but sign-in warns once.
        self._build_with_libsecret_unavailable()
        self._build_with_libsecret_unavailable()

        with mock.patch.object(persistence.logger, 'warning') as warning_mock:
            persistence.warn_if_encryption_unavailable()

        warning_mock.assert_called_once_with(persistence.ENCRYPTION_FALLBACK_WARNING)

    def test_no_warning_without_fallback(self):
        with mock.patch.object(persistence.logger, 'warning') as warning_mock:
            persistence.warn_if_encryption_unavailable()

        warning_mock.assert_not_called()

    def test_no_warning_when_encryption_opted_out(self):
        with mock.patch.object(persistence.sys, 'platform', 'linux'):
            store = persistence.build_persistence('/tmp/test_persistence', False, type='Token cache')

        self.assertIsInstance(store, persistence.FilePersistence)
        self.assertFalse(persistence._encryption_fallback)


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
