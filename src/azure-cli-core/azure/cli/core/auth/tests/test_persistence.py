# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import tempfile
import unittest
from unittest import mock

from azure.cli.core.auth.persistence import AzureCliTokenCache, SecretStore, build_persistence


class TestAzureCliTokenCache(unittest.TestCase):

    def _make_persistence(self, tmp_path):
        """Build a FilePersistence from a .json tmp file path."""
        # build_persistence appends the .json extension, so strip it first
        return build_persistence(tmp_path.replace('.json', ''), encrypt=False)

    def test_reload_if_necessary_handles_json_decode_error(self):
        """Test that a corrupted (invalid JSON) token cache file is handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write corrupted JSON (extra data after valid JSON, as described in the issue)
            f.write('{}extra')
            tmp_path = f.name

        try:
            persistence = self._make_persistence(tmp_path)
            cache = AzureCliTokenCache(persistence)

            # Use float('inf') so that the condition `_last_sync < time_last_modified()` is
            # always True, forcing a reload on every call to _reload_if_necessary.
            with mock.patch.object(type(cache._persistence), 'time_last_modified', return_value=float('inf')):
                # Should not raise JSONDecodeError
                cache._reload_if_necessary()
        finally:
            os.unlink(tmp_path)

    def test_reload_if_necessary_handles_valid_json(self):
        """Test that a valid (but empty) token cache file is loaded without error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            tmp_path = f.name

        try:
            persistence = self._make_persistence(tmp_path)
            cache = AzureCliTokenCache(persistence)

            # Use float('inf') so that the condition `_last_sync < time_last_modified()` is
            # always True, forcing a reload on every call to _reload_if_necessary.
            with mock.patch.object(type(cache._persistence), 'time_last_modified', return_value=float('inf')):
                # Should not raise
                cache._reload_if_necessary()
        finally:
            os.unlink(tmp_path)


class TestSecretStore(unittest.TestCase):

    def _make_persistence(self, tmp_path):
        """Build a FilePersistence from a .json tmp file path."""
        # build_persistence appends the .json extension, so strip it first
        return build_persistence(tmp_path.replace('.json', ''), encrypt=False)

    def test_load_handles_json_decode_error(self):
        """Test that corrupted service principal entries are handled gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Write corrupted JSON
            f.write('[{"client_id": "test"}]extra_data')
            tmp_path = f.name

        try:
            persistence = self._make_persistence(tmp_path)
            store = SecretStore(persistence)

            # load should not raise and should return empty list
            result = store.load()
            self.assertEqual(result, [])
        finally:
            os.unlink(tmp_path)

    def test_load_valid_entries(self):
        """Test that valid service principal entries are loaded correctly."""
        entries = [{'client_id': 'test_sp', 'tenant': 'test_tenant', 'client_secret': 'secret'}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(entries, f)
            tmp_path = f.name

        try:
            persistence = self._make_persistence(tmp_path)
            store = SecretStore(persistence)

            result = store.load()
            self.assertEqual(result, entries)
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
