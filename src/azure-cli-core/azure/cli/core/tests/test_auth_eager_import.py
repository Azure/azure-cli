# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Regression test: azure.cli.core.auth.identity must eagerly import requests and msal.

Python 3.14 raises _DeadlockError when two threads race to initialise a module
whose import-lock ordering creates a cycle (e.g. requests.structures).  The fix
is to pre-load requests (and msal) on the main thread before any background
thread can trigger the same import lazily.  This test guards against the eager
import being removed in the future.
"""

import sys
import unittest

# Modules that azure.cli.core.auth.identity must eagerly pre-load.
_EAGER_MODULES = ('requests', 'requests.structures', 'msal')

# All modules that must be evicted from sys.modules to make the test
# independent of import order within the test session.
_EVICT_PREFIXES = (
    'azure.cli.core.auth',
    'requests',
    'msal',
)


def _evict_modules():
    """Remove all cached copies of identity and the packages it should eagerly load."""
    for key in list(sys.modules):
        for prefix in _EVICT_PREFIXES:
            if key == prefix or key.startswith(prefix + '.'):
                del sys.modules[key]
                break


class TestEagerImport(unittest.TestCase):

    def setUp(self):
        # Evict modules so the import inside each test re-executes the module
        # body, which is the only way to reliably detect a missing eager import.
        _evict_modules()

    def tearDown(self):
        # Leave sys.modules clean so other tests are not affected.
        _evict_modules()

    def test_requests_in_sys_modules_after_identity_import(self):
        """After importing azure.cli.core.auth.identity, requests must already be
        present in sys.modules so that no background thread can trigger a lazy
        import that would race with Python 3.14 per-module import locks."""
        import azure.cli.core.auth.identity  # noqa: F401

        self.assertIn(
            'requests',
            sys.modules,
            "requests must be eagerly imported by azure.cli.core.auth.identity "
            "to prevent Python 3.14 module-lock deadlocks in background threads.",
        )
        self.assertIn(
            'requests.structures',
            sys.modules,
            "requests.structures must be present in sys.modules after importing "
            "azure.cli.core.auth.identity.",
        )

    def test_msal_in_sys_modules_after_identity_import(self):
        """msal must be eagerly imported by azure.cli.core.auth.identity."""
        import azure.cli.core.auth.identity  # noqa: F401

        self.assertIn(
            'msal',
            sys.modules,
            "msal must be eagerly imported by azure.cli.core.auth.identity.",
        )


if __name__ == '__main__':
    unittest.main()
