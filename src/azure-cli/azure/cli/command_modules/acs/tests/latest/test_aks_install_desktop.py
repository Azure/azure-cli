# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile
import tempfile
from unittest import mock

from azure.cli.core.azclierror import ClientRequestError, InvalidArgumentValueError
from azure.cli.testsdk import ScenarioTest


class AKSInstallDesktopScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        self.sandbox = tempfile.TemporaryDirectory()
        # DummyCli otherwise creates its random config under the real global profile.
        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', self.sandbox.name):
            super().__init__(method_name, random_config_dir=True)
        # Test discovery constructs all cases before running them. Do not leave their
        # config environment patches nested until tearDown.
        self.cli_ctx.env_patch.stop()
        self.original_env = os.environ.copy()

    def setUp(self):
        self.addCleanup(self.sandbox.cleanup)
        self.home = Path(self.sandbox.name, 'home')
        self.home.mkdir()
        self.downloads = Path(self.sandbox.name, 'downloads')
        self.downloads.mkdir()
        self._patch(mock.patch.dict(os.environ, {
            'HOME': str(self.home),
            'USERPROFILE': str(self.home),
            'AZURE_CONFIG_DIR': self.cli_ctx.config.config_dir,
            'AZURE_EXTENSION_DIR': str(self.home / 'extensions'),
            'AZURE_CORE_COLLECT_TELEMETRY': '0',
            'GH_TOKEN': '',
        }))
        super().setUp()
        # Extension roots are cached at import time, before the environment patch.
        self._patch(mock.patch('azure.cli.core.extension.EXTENSIONS_DIR', str(self.home / 'extensions')))
        self._patch(mock.patch('azure.cli.core.extension.EXTENSIONS_SYS_DIR', str(self.home / 'system-extensions')))
        self._patch(mock.patch('azure.cli.core.extension.DEV_EXTENSION_SOURCES', []))

        # Any missed transport stub must fail, including DNS or swallowed requests.
        for target in ('socket.getaddrinfo', 'socket.socket.connect', 'socket.socket.connect_ex'):
            guard = self._patch(mock.patch(target, side_effect=AssertionError('Unexpected network access')))
            self.addCleanup(guard.assert_not_called)
        self._patch(mock.patch('tempfile.tempdir', str(self.downloads)))
        self._patch(mock.patch('platform.system', return_value='Linux'))
        self._patch(mock.patch('platform.machine', return_value='aarch64'))
        self.popen = self._patch(mock.patch('subprocess.Popen'))
        # A cold runtime may probe network interfaces during CLI initialization.
        # Include those calls so launch assertions cannot depend on probe caches.
        self.popen(('/usr/sbin/ip', 'link'))
        self.popen(('/usr/sbin/ifconfig',))
        self.run = self._patch(mock.patch('subprocess.run', side_effect=AssertionError('Unexpected installer launch')))
        self.addCleanup(self.run.assert_not_called)

        content = io.BytesIO()
        with tarfile.open(fileobj=content, mode='w') as archive:
            executable = tarfile.TarInfo('app/aks-desktop')
            executable.mode = 0o755
            executable.size = len(b'fixture')
            archive.addfile(executable, io.BytesIO(b'fixture'))
        self.archive_bytes = gzip.compress(content.getvalue(), mtime=0)
        self.asset = {
            'name': 'aks-desktop-0.9.1-linux-arm64.tar.gz',
            'browser_download_url': (
                'https://github.com/Azure/aks-desktop/releases/download/v0.9.1/'
                'aks-desktop-0.9.1-linux-arm64.tar.gz'),
            'digest': 'sha256:' + hashlib.sha256(self.archive_bytes).hexdigest(),
        }
        self.release = {'tag_name': 'v0.9.1', 'assets': [self.asset]}
        self.metadata = self._patch(mock.patch(
            'azure.cli.command_modules.acs.custom.urlopen',
            side_effect=lambda *args, **kwargs: io.BytesIO(json.dumps(self.release).encode('utf-8'))))
        self.opener = self._patch(mock.patch('urllib.request.build_opener')).return_value
        self.opener.open.side_effect = self._open_download
        self.installer_path = None

    def _patch(self, patcher):
        patched = patcher.start()
        self.addCleanup(patcher.stop)
        return patched

    def _open_download(self, request):
        self.assertEqual(request.full_url, self.asset['browser_download_url'])
        self.assertIsNone(request.get_header('Authorization'))
        # The real command has created the directory, but has not opened its output yet.
        installer_dirs = list(self.downloads.glob('aks-desktop-*'))
        self.assertEqual(len(installer_dirs), 1)
        self.installer_path = installer_dirs[0] / self.asset['name']
        return io.BytesIO(self.archive_bytes)

    def _desktop_launch_calls(self):
        return [call for call in self.popen.call_args_list
                if call.args and isinstance(call.args[0], (list, tuple)) and call.args[0]
                and os.path.basename(call.args[0][0]) == 'aks-desktop']

    def _assert_archive_installed(self, endpoint, token=None):
        self.metadata.assert_called_once()
        request = self.metadata.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.github.com/repos/Azure/aks-desktop/releases/' + endpoint)
        self.assertEqual(request.get_header('Authorization'), 'Bearer ' + token if token else None)
        self.opener.open.assert_called_once()
        executable = self.home / '.local' / 'share' / 'aks-desktop' / '0.9.1' / 'app' / 'aks-desktop'
        self.assertEqual(executable.read_bytes(), b'fixture')
        if os.name != 'nt':
            self.assertEqual(stat.S_IMODE(executable.stat().st_mode), 0o755)
        self.assertEqual(self._desktop_launch_calls(), [mock.call([str(executable)])])
        self.assertIsNotNone(self.installer_path)
        self.assertFalse(self.installer_path.exists())
        self.assertFalse(self.installer_path.parent.exists())
        self.assertEqual(list(self.downloads.iterdir()), [])

    def test_install_desktop_specific_version(self):
        with mock.patch.dict(os.environ, {'GH_TOKEN': 'unused-environment-token'}):
            self.cmd('aks install-desktop --version 0.9.1 --gh-token fake-test-token')
        self._assert_archive_installed('tags/v0.9.1', token='fake-test-token')

    def test_install_desktop_environment_token_is_not_in_debug_logs(self):
        token = 'test-environment-token-not-in-argv'
        with mock.patch.dict(os.environ, {'GH_TOKEN': token}):
            with self.assertLogs(level='DEBUG') as root_logs, self.assertLogs('cli', level='DEBUG') as logs:
                self.cmd('aks install-desktop --version 0.9.1 --debug')
        self._assert_archive_installed('tags/v0.9.1', token=token)
        output = '\n'.join(root_logs.output + logs.output)
        self.assertIn('Command arguments:', output)
        self.assertNotIn(token, output)

    def test_install_desktop_rejects_malformed_environment_token(self):
        token = 'malformed-environment-token'
        with mock.patch.dict(os.environ, {'GH_TOKEN': token + '\n'}):
            with self.assertRaises(InvalidArgumentValueError) as error:
                self.cmd('aks install-desktop')
        self.assertNotIn(token, str(error.exception))
        self.metadata.assert_not_called()
        self.opener.open.assert_not_called()
        self.assertEqual(self._desktop_launch_calls(), [])

    def test_install_desktop_latest(self):
        self.cmd('aks install-desktop')
        self._assert_archive_installed('latest')

    def test_install_desktop_without_tar_data_filter(self):
        with mock.patch.object(tarfile, 'data_filter', None, create=True):
            self.cmd('aks install-desktop --version 0.9.1')
        self._assert_archive_installed('tags/v0.9.1')

    def test_install_desktop_rejects_invalid_and_empty_version(self):
        for version in ('invalid', ''):
            with self.subTest(version=version):
                with self.assertRaises(InvalidArgumentValueError) as error:
                    self.cmd('aks install-desktop --version "{}"'.format(version))
                self.assertIn("version '{}' is invalid".format(version), str(error.exception))
                self.metadata.assert_not_called()
                self.opener.open.assert_not_called()
                self.assertEqual(self._desktop_launch_calls(), [])
                self.assertFalse((self.home / '.local').exists())
                self.assertEqual(list(self.downloads.iterdir()), [])

    def test_install_desktop_rejects_mismatched_digest(self):
        self.asset['digest'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(ClientRequestError, 'did not match.*SHA-256'):
            self.cmd('aks install-desktop --version 0.9.1')
        self.opener.open.assert_called_once()
        self.assertEqual(self._desktop_launch_calls(), [])
        self.assertFalse((self.home / '.local').exists())
        self.assertIsNotNone(self.installer_path)
        self.assertFalse(self.installer_path.exists())
        self.assertFalse(self.installer_path.parent.exists())
        self.assertEqual(list(self.downloads.iterdir()), [])
