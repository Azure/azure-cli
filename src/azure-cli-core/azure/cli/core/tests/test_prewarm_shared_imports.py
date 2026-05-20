# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

import azure.cli.core as core


class PrewarmSharedImportsTest(unittest.TestCase):

    def setUp(self):
        # Reset the idempotency flag so each test exercises the full loop.
        core._prewarm_done = False

    def tearDown(self):
        core._prewarm_done = False

    def test_imports_all_modules_on_first_call(self):
        with mock.patch('importlib.import_module') as m:
            core._prewarm_shared_imports()
        imported = [c.args[0] for c in m.call_args_list]
        for name in core._REQUIRED_PREWARM_MODULES + core._OPTIONAL_PREWARM_MODULES:
            self.assertIn(name, imported)
        self.assertTrue(core._prewarm_done)

    def test_idempotent(self):
        with mock.patch('importlib.import_module') as m:
            core._prewarm_shared_imports()
            first_count = m.call_count
            core._prewarm_shared_imports()
            self.assertEqual(m.call_count, first_count)

    def test_missing_optional_module_is_suppressed(self):
        optional = core._OPTIONAL_PREWARM_MODULES[0]

        def fake_import(name):
            if name == optional:
                raise ModuleNotFoundError(f"No module named '{optional}'", name=optional)
            return mock.MagicMock()

        with mock.patch('importlib.import_module', side_effect=fake_import):
            # Must not raise.
            core._prewarm_shared_imports()
        self.assertTrue(core._prewarm_done)

    def test_missing_required_module_propagates(self):
        required = core._REQUIRED_PREWARM_MODULES[0]

        def fake_import(name):
            if name == required:
                raise ModuleNotFoundError(f"No module named '{required}'", name=required)
            return mock.MagicMock()

        with mock.patch('importlib.import_module', side_effect=fake_import):
            with self.assertRaises(ModuleNotFoundError):
                core._prewarm_shared_imports()
        # Flag should not be set when prewarm failed.
        self.assertFalse(core._prewarm_done)

    def test_unrelated_module_not_found_inside_optional_propagates(self):
        # ModuleNotFoundError raised from inside an installed optional module
        # (e.g. its own missing dep) must NOT be silently swallowed.
        optional = core._OPTIONAL_PREWARM_MODULES[0]

        def fake_import(name):
            if name == optional:
                # Simulate an installed module whose import fails because one of
                # its own deps is missing.
                raise ModuleNotFoundError("No module named 'some_unrelated_dep'",
                                          name='some_unrelated_dep')
            return mock.MagicMock()

        with mock.patch('importlib.import_module', side_effect=fake_import):
            with self.assertRaises(ModuleNotFoundError):
                core._prewarm_shared_imports()


if __name__ == '__main__':
    unittest.main()
