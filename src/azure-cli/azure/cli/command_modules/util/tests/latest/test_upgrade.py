# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import unittest
from unittest import mock

from azure.cli.command_modules.util.custom import _upgrade_on_windows

_MSI_PATH = 'C:\\temp\\azure-cli-msi\\azure-cli.msi'


class UpgradeOnWindowsTest(unittest.TestCase):

    # ------------------------------------------------------------------
    # successful upgrade — az version passes
    # ------------------------------------------------------------------

    def test_successful_upgrade_exits_zero(self):
        """When msiexec succeeds and az version passes, exit code is 0."""
        with mock.patch('platform.architecture', return_value=('64bit', '')), \
                mock.patch('azure.cli.command_modules.util.custom._download_from_url',
                           return_value=_MSI_PATH), \
                mock.patch('azure.cli.core.util.rmtree_with_retry'), \
                mock.patch('azure.cli.command_modules.util.custom.logger'), \
                mock.patch('subprocess.run',
                           return_value=mock.Mock(returncode=0)) as run_mock, \
                mock.patch('subprocess.check_output', return_value=b'{}'):
            with self.assertRaises(SystemExit) as cm:
                _upgrade_on_windows()

        self.assertEqual(cm.exception.code, 0)
        run_mock.assert_called_once_with(
            ['msiexec.exe', '/i', _MSI_PATH, '/passive'], check=False)

    # ------------------------------------------------------------------
    # WDAC blocking — az version fails after successful msiexec
    # ------------------------------------------------------------------

    def test_wdac_blocking_exits_nonzero_and_warns(self):
        """When msiexec succeeds but az version fails, exit 1 and warn about WDAC."""
        with mock.patch('platform.architecture', return_value=('64bit', '')), \
                mock.patch('azure.cli.command_modules.util.custom._download_from_url',
                           return_value=_MSI_PATH), \
                mock.patch('azure.cli.core.util.rmtree_with_retry'), \
                mock.patch('azure.cli.command_modules.util.custom.logger') as logger_mock, \
                mock.patch('subprocess.run',
                           return_value=mock.Mock(returncode=0)), \
                mock.patch('subprocess.check_output',
                           side_effect=subprocess.CalledProcessError(1, 'az version -o json')):
            with self.assertRaises(SystemExit) as cm:
                _upgrade_on_windows()

        self.assertEqual(cm.exception.code, 1)
        warning_messages = [call_args[0][0] for call_args in logger_mock.warning.call_args_list]
        self.assertTrue(
            any('Device Guard' in m and 'WDAC' in m for m in warning_messages),
            "Expected a WDAC/Device Guard warning; got: {}".format(warning_messages))

    # ------------------------------------------------------------------
    # msiexec failure
    # ------------------------------------------------------------------

    def test_msiexec_failure_exits_with_msi_exit_code(self):
        """When msiexec returns a non-success exit code, we exit with that code."""
        with mock.patch('platform.architecture', return_value=('64bit', '')), \
                mock.patch('azure.cli.command_modules.util.custom._download_from_url',
                           return_value=_MSI_PATH), \
                mock.patch('azure.cli.core.util.rmtree_with_retry'), \
                mock.patch('azure.cli.command_modules.util.custom.logger'), \
                mock.patch('subprocess.run',
                           return_value=mock.Mock(returncode=1603)):
            with self.assertRaises(SystemExit) as cm:
                _upgrade_on_windows()

        self.assertEqual(cm.exception.code, 1603)

    # ------------------------------------------------------------------
    # restart-required exit codes (1641 / 3010)
    # ------------------------------------------------------------------

    def test_restart_required_warns_and_exits_zero(self):
        """When msiexec returns 3010 (restart required) and az version succeeds, exit 0."""
        with mock.patch('platform.architecture', return_value=('64bit', '')), \
                mock.patch('azure.cli.command_modules.util.custom._download_from_url',
                           return_value=_MSI_PATH), \
                mock.patch('azure.cli.core.util.rmtree_with_retry'), \
                mock.patch('azure.cli.command_modules.util.custom.logger') as logger_mock, \
                mock.patch('subprocess.run',
                           return_value=mock.Mock(returncode=3010)), \
                mock.patch('subprocess.check_output', return_value=b'{}'):
            with self.assertRaises(SystemExit) as cm:
                _upgrade_on_windows()

        self.assertEqual(cm.exception.code, 0)
        warning_messages = [call_args[0][0] for call_args in logger_mock.warning.call_args_list]
        self.assertTrue(
            any('restart' in m.lower() for m in warning_messages),
            "Expected a restart warning for exit code 3010; got: {}".format(warning_messages))

    # ------------------------------------------------------------------
    # 32-bit architecture uses 32-bit MSI URL
    # ------------------------------------------------------------------

    def test_32bit_uses_correct_msi_url(self):
        """On a 32-bit architecture the 32-bit MSI URL is used."""
        with mock.patch('platform.architecture', return_value=('32bit', '')), \
                mock.patch('azure.cli.command_modules.util.custom._download_from_url',
                           return_value=_MSI_PATH) as download_mock, \
                mock.patch('azure.cli.core.util.rmtree_with_retry'), \
                mock.patch('azure.cli.command_modules.util.custom.logger'), \
                mock.patch('subprocess.run',
                           return_value=mock.Mock(returncode=0)), \
                mock.patch('subprocess.check_output', return_value=b'{}'):
            with self.assertRaises(SystemExit):
                _upgrade_on_windows()

        url_used = download_mock.call_args[0][0]
        self.assertIn('installazurecliwindows', url_used)
        self.assertNotIn('x64', url_used)


if __name__ == '__main__':
    unittest.main()
