# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pathlib import Path
import shutil
import tempfile
from unittest import mock, SkipTest, TestCase

from azure.cli.core.tests import test_argcomplete_shell


class ArgcompleteShellResourceTest(TestCase):

    def setUp(self):
        if not shutil.which('bash'):
            self.skipTest('Bash is not installed')
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.site_packages = self.root / 'lib' / 'python3' / 'site-packages'
        self.test_file = self.site_packages / 'azure/cli/core/tests/test_argcomplete_shell.py'
        self.cwd = self.root / 'checkout'
        self.cwd.mkdir()
        patcher = mock.patch.object(test_argcomplete_shell, '__file__', str(self.test_file))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(Path, 'cwd', return_value=self.cwd)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.shell = test_argcomplete_shell.ArgcompleteShellTest('test_bash_completion_tempfile_git_bash')
        self.addCleanup(self.shell.doCleanups)

    def assert_resource_loaded(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        completion = directory / 'az.completion'
        completion.write_text('TEST_COMPLETION_RESOURCE=found\n', encoding='utf-8')
        self.shell.setUp()
        self.assertEqual(self.shell.completion, completion)
        self.assertEqual(self.shell.run_completion('printf "%s\\n" "$TEST_COMPLETION_RESOURCE"'), 'found\n')

    def test_installed_resource(self):
        self.assert_resource_loaded(self.site_packages)

    def test_resource_beside_installed_test(self):
        self.assert_resource_loaded(self.test_file.parent)

    def test_installed_tests_with_checkout_cwd(self):
        self.assert_resource_loaded(self.cwd)

    def test_checkout_backed_test_path(self):
        test_file = self.cwd / 'src/azure-cli-core/azure/cli/core/tests/test_argcomplete_shell.py'
        with mock.patch.object(test_argcomplete_shell, '__file__', str(test_file)), \
                mock.patch.object(Path, 'cwd', return_value=self.root / 'outside-checkout'):
            self.assert_resource_loaded(self.cwd)

    def test_missing_resource_skips(self):
        with self.assertRaisesRegex(SkipTest, r'az\.completion.*not available'):
            self.shell.setUp()

    def test_resource_directory_skips(self):
        (self.cwd / 'az.completion').mkdir()
        with self.assertRaisesRegex(SkipTest, r'az\.completion.*not available'):
            self.shell.setUp()
