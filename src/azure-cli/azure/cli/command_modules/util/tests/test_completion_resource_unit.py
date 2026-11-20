# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pathlib import Path
import shutil
import tempfile
from unittest import mock, SkipTest, TestCase

from azure.cli.command_modules.util.tests.latest import test_completion


class CompletionResourceTest(TestCase):

    def setUp(self):
        if not shutil.which('bash'):
            self.skipTest('Bash is not installed')
        if not shutil.which('az') and not shutil.which('az.cmd'):
            self.skipTest('Azure CLI is not installed')
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.site_packages = self.root / 'lib' / 'python3' / 'site-packages'
        self.test_file = self.site_packages / 'azure/cli/command_modules/util/tests/latest/test_completion.py'
        self.cwd = self.root / 'checkout'
        self.cwd.mkdir()
        patcher = mock.patch.object(test_completion, '__file__', str(self.test_file))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(Path, 'cwd', return_value=self.cwd)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_resource_loaded(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        completion = directory / 'az.completion'
        completion.write_text('TEST_COMPLETION_RESOURCE=found\n', encoding='utf-8')
        output = test_completion.CompletionTest._complete(self, 'printf "%s\\n" "$TEST_COMPLETION_RESOURCE"')
        self.assertEqual(output, 'found\n')

    def test_installed_resource(self):
        self.assert_resource_loaded(self.site_packages)

    def test_resource_beside_installed_test(self):
        self.assert_resource_loaded(self.test_file.parent)

    def test_installed_tests_with_checkout_cwd(self):
        self.assert_resource_loaded(self.cwd)

    def test_checkout_backed_test_path(self):
        test_file = self.cwd / 'src/azure-cli/azure/cli/command_modules/util/tests/latest/test_completion.py'
        with mock.patch.object(test_completion, '__file__', str(test_file)), \
                mock.patch.object(Path, 'cwd', return_value=self.root / 'outside-checkout'):
            self.assert_resource_loaded(self.cwd)

    def test_missing_resource_skips(self):
        with self.assertRaisesRegex(SkipTest, r'az\.completion.*not available'):
            test_completion.CompletionTest._complete(self, '')

    def test_resource_directory_skips(self):
        (self.cwd / 'az.completion').mkdir()
        with self.assertRaisesRegex(SkipTest, r'az\.completion.*not available'):
            test_completion.CompletionTest._complete(self, '')
