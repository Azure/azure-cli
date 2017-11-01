# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import json
import shlex
import unittest

import sys

import six
from nose import with_setup
from six import StringIO

from azure.cli.command_modules.find.custom import _purge


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


def execute(cmd):
    cmd_list = shlex.split(cmd)
    with capture() as out:
        cli_main(cmd_list)

    return out[0]


class SearchIndexTest(unittest.TestCase):
    def setUp(self):
        _purge()

    def test_search_index(self):
        six.assertRegex(
            self,
            execute('find -q keyvault list'),
            'az keyvault list')

    def test_search_reindex(self):
        six.assertRegex(
            self,
            execute('find -q keyvault list --reindex'),
            'az keyvault list')
