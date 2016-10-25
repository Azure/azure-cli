#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os

# Determine the correct patch target for open
try:
    # python 3
    import builtins #pylint: disable=unused-import
    OPEN_PATCH_TARGET = 'builtins.open'
except ImportError:
    OPEN_PATCH_TARGET = '__builtin__.open'

import unittest
import mock

# Need to import config before we can import context
import azure.cli.core._config #pylint: disable=unused-import

from azure.cli.core.context import (get_active_context_name,
                                    set_active_context,
                                    ContextNotFoundException)

class TestContext(unittest.TestCase):

    def test_get_active_context_name_envvar(self):
        expected = 'mycontextname'
        with mock.patch.dict(os.environ, {'AZURE_CONTEXT': expected}):
            actual = get_active_context_name()
            self.assertEqual(expected, actual)

    def test_get_active_context_name_default(self):
        expected = 'default'
        actual = get_active_context_name()
        self.assertEqual(expected, actual)

    def test_get_active_context_name_from_file(self):
        expected = 'contextfromfile'
        m = mock.mock_open(read_data=expected)
        with mock.patch(OPEN_PATCH_TARGET, m, create=True):
            actual = get_active_context_name()
            self.assertEqual(expected, actual)

    def test_set_active_context_not_exists(self):
        context_name = 'mynewcontext'
        # We haven't created the context yet so it doesn't exist
        with self.assertRaises(ContextNotFoundException):
            set_active_context(context_name, skip_set_active_subsciption=True)

if __name__ == '__main__':
    unittest.main()
