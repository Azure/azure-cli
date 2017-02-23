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
from six import StringIO

from azure.cli.main import main as cli_main

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


def exec(cmd):
    cmd_list = shlex.split(cmd)
    with capture() as out:
        cli_main(cmd_list)

    return out[0]


def exec_json(cmd):
    json.loads(exec(cmd))


class SearchIndexTest(unittest.TestCase):
    def test_search_index(self):
        six.assertRegex(
            self,
            exec('search -q "keyvault list"'),
            'az keyvault certificate list-versions')

    def test_search_reindex(self):
        six.assertRegex(
            self,
            exec('search -q "keyvault list" --reindex'),
            'az keyvault certificate list-versions')
