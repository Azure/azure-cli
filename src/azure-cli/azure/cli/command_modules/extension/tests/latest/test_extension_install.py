# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import hashlib
from importlib.metadata import distributions
import subprocess
import sys
import unittest
from unittest import mock

from azure.cli.command_modules.extension.custom import add_extension_cmd
from azure.cli.core.extension import operations
from azure.cli.core.mock import DummyCli
from azure.cli.core.tests.extension_pip_test_utils import (
    BACKEND_MODULE,
    DEPENDENCY_MODULE,
    DEPENDENCY_NAME,
    EXTENSION_MODULE,
    EXTENSION_NAME,
    ExtensionPipFixture,
)
from azure.cli.core.util import CLIError


class TestExtensionInstall(unittest.TestCase):

    def setUp(self):
        self.fixture = ExtensionPipFixture(self)
        self.cmd = mock.Mock()
        self.cmd.cli_ctx = DummyCli()
        for patcher in (
            mock.patch.object(operations, 'IS_WINDOWS', True),
            mock.patch.object(operations, 'set_extension_management_detail'),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_indexed_system_install_prefers_binary_and_forwards_options(self):
        source = str(self.fixture.extension_wheel)
        original_wheel = self.fixture.extension_wheel.read_bytes()
        digest = hashlib.sha256(original_wheel).hexdigest()
        target = self.fixture.target(system=True)
        index_url = 'https://extensions.invalid/index.json'
        proxy = 'http://127.0.0.1:9'
        extra_index_urls = ['https://first.invalid/simple', 'https://second.invalid/simple']

        with mock.patch.object(operations, 'resolve_from_index', return_value=(source, digest)) as resolve, \
                mock.patch.object(operations, 'check_output', wraps=subprocess.check_output) as check_output, \
                mock.patch.object(operations.CommandIndex, 'invalidate') as invalidate:
            add_extension_cmd(
                self.cmd, extension_name=EXTENSION_NAME, system=True, version='1.0',
                index_url=index_url, allow_preview=True,
                pip_proxy=proxy, pip_extra_index_urls=extra_index_urls)

        resolve.assert_called_once_with(
            EXTENSION_NAME, index_url=index_url, target_version='1.0',
            cli_ctx=self.cmd.cli_ctx, allow_preview=True)
        check_output.assert_called_once_with(
            [
                sys.executable, '-m', 'pip',
                'install', '--target', str(target), str(self.fixture.extension_wheel.resolve()),
                '--prefer-binary',
                '--proxy', proxy,
                '--extra-index-url', extra_index_urls[0],
                '--extra-index-url', extra_index_urls[1],
                '--disable-pip-version-check', '--no-cache-dir',
            ],
            stderr=subprocess.STDOUT, universal_newlines=True)
        invalidate.assert_called_once_with()

        versions = {dist.metadata['Name']: dist.version for dist in distributions(path=[str(target)])}
        self.assertEqual(versions, {EXTENSION_NAME: '1.0', DEPENDENCY_NAME: '1.0'})
        self.assertTrue((target / EXTENSION_MODULE / '__init__.py').is_file())
        self.assertTrue((target / DEPENDENCY_MODULE / '__init__.py').is_file())
        self.assertFalse((target / (BACKEND_MODULE + '.py')).exists())
        self.assertFalse(self.fixture.build_log.exists())
        self.assertFalse(self.fixture.target().exists())
        self.assertEqual((target / self.fixture.extension_wheel.name).read_bytes(), original_wheel)
        self.assertEqual(self.fixture.extension_wheel.read_bytes(), original_wheel)

    def test_indexed_install_rejects_bad_checksum_before_pip(self):
        source = str(self.fixture.extension_wheel)
        original_wheel = self.fixture.extension_wheel.read_bytes()

        with mock.patch.object(operations, 'resolve_from_index', return_value=(source, '0' * 64)) as resolve, \
                mock.patch.object(operations, 'check_output', wraps=subprocess.check_output) as check_output, \
                mock.patch.object(operations.CommandIndex, 'invalidate') as invalidate:
            with self.assertRaises(CLIError) as raised:
                add_extension_cmd(self.cmd, extension_name=EXTENSION_NAME)

        self.assertEqual(
            str(raised.exception),
            'The checksum of the extension does not match the expected value. '
            'Use --debug for more information.')
        resolve.assert_called_once_with(
            EXTENSION_NAME, index_url=None, target_version=None,
            cli_ctx=self.cmd.cli_ctx, allow_preview=None)
        check_output.assert_not_called()
        invalidate.assert_not_called()
        self.assertFalse(self.fixture.target().exists())
        self.assertFalse(self.fixture.target(system=True).exists())
        self.assertEqual(self.fixture.extension_wheel.read_bytes(), original_wheel)
