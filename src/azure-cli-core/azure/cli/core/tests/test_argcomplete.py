# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.core.util import run_cmd


class ArgcompleteScenarioTest(unittest.TestCase):

    def argcomplete_env(self, comp_line, comp_point):
        return {
            'COMP_LINE': comp_line,
            'COMP_POINT': comp_point,
            '_ARGCOMPLETE': '1',
            '_ARGCOMPLETE_IFS': ' ',
            '_ARGCOMPLETE_SUPPRESS_SPACE': '0',
            'ARGCOMPLETE_USE_TEMPFILES': '1',
            '_ARGCOMPLETE_STDOUT_FILENAME': './argcomplete.out', }

    def test_completion(self):
        import sys

        if sys.platform == 'win32':
            self.skipTest('Skip argcomplete test on Windows')

        run_cmd(['az'], capture_output=True, env=self.argcomplete_env('az account sh', '13'))
        with open('argcomplete.out') as f:
            assert f.read() == 'show '
        os.remove('argcomplete.out')

        run_cmd(['az'], capture_output=True, env=self.argcomplete_env('az account s', '12'))
        with open('argcomplete.out') as f:
            completion = f.read()
            self.assertEqual('set show', completion)
        os.remove('argcomplete.out')

        run_cmd(['az'], capture_output=True, env=self.argcomplete_env('az account szzz', '15'))
        with open('argcomplete.out') as f:
            completion = f.read()
            self.assertFalse(completion)
        os.remove('argcomplete.out')
