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


if __name__ == '__main__':
    unittest.main()
