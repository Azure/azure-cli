# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import unittest
import mock
import sys
import six
from six import StringIO

from azure.cli.command_modules.find.custom import _purge, find
from azure.cli.testsdk import TestCli


@contextlib.contextmanager
def capture():
    oldout, olderr = sys.stdout, sys.stderr
    try:
        out = [StringIO(), StringIO()]
        sys.stdout, sys.stderr = out
        yield out
    finally:
        sys.stdout, sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()


class SearchIndexTest(unittest.TestCase):
    def setUp(self):
        _purge()
        self.loader = mock.MagicMock()
        self.loader.cli_ctx = TestCli()

    def execute(self, args, reindex=False):
        with capture() as out:
            find(self.loader, args, reindex)

        return out[0]

    def test_search_index(self):
        six.assertRegex(
            self,
            self.execute(['keyvault', 'list']),
            'az keyvault list')

    def test_search_reindex(self):
        six.assertRegex(
            self,
            self.execute(['keyvault', 'list'], reindex=True),
            'az keyvault list')
