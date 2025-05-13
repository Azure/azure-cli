# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from unittest import mock, TestCase

from azure.cli.core.mock import DummyCli
from azure.cli.core.util import run_cmd


class ArgcompleteScenarioTest(TestCase):

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
        import os
        import sys

        from azure.cli.core.parser import AzCompletionFinder

        if sys.platform == 'win32':
            self.skipTest('Skip argcomplete test on Windows')

        run_cmd(['az'], env=self.argcomplete_env('az account sh', '13'))
        with open('argcomplete.out') as f:
            self.assertEqual(f.read(), 'show ')
        os.remove('argcomplete.out')

        run_cmd(['az'], capture_output=True, env=self.argcomplete_env('az account s', '12'))
        with open('argcomplete.out') as f:
            self.assertEqual(f.read(), 'set show')
        os.remove('argcomplete.out')

        run_cmd(['az'], env=self.argcomplete_env('az account szzz', '15'))
        with open('argcomplete.out') as f:
            self.assertFalse(f.read())
        os.remove('argcomplete.out')

        class MockCompletionFinder(AzCompletionFinder):
            def __call__(self, *args, **kwargs):
                import sys
                return super().__call__(*args, exit_method=sys.exit, **kwargs)

        def dummy_completor(*args, **kwargs):
            return ['dummystorage']

        cli = DummyCli()
        # argcomplete uses os._exit to exit, which is also used by pytest. Patch AzCompletionFinder to use sys.exit
        # There is no recording for this test case, as completer is mocked.
        with mock.patch('azure.cli.core.parser.AzCompletionFinder', MockCompletionFinder):
            with mock.patch('azure.cli.core.commands.parameters.get_resource_name_completion_list', lambda _: dummy_completor):
                env = self.argcomplete_env('az storage blob list -c test --account-name dumm', '48')
                with mock.patch.dict(os.environ, env):
                    self.assertRaises(SystemExit, cli.invoke, ['az'])
        with open('argcomplete.out') as f:
            self.assertEqual(f.read(), 'dummystorage ')
        os.remove('argcomplete.out')
