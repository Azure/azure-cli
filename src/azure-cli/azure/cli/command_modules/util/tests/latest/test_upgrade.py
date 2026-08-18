# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from azure.cli.command_modules.util.custom import _upgrade_on_windows


class UpgradeOnWindowsTest(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.util.custom._download_from_url')
    @mock.patch('azure.cli.core.util.rmtree_with_retry')
    @mock.patch('subprocess.Popen')
    @mock.patch('platform.architecture')
    def test_upgrade_on_windows_warns_about_code_integrity_policies(
            self, architecture_mock, popen_mock, rmtree_mock, download_mock):
        architecture_mock.return_value = ('64bit', '')
        download_mock.return_value = 'C:\\temp\\azure-cli-msi\\azure-cli.msi'

        with self.assertRaises(SystemExit), \
                mock.patch('azure.cli.command_modules.util.custom.logger') as logger_mock:
            _upgrade_on_windows()

        popen_mock.assert_called_once_with(['msiexec.exe', '/i', 'C:\\temp\\azure-cli-msi\\azure-cli.msi'])

        warning_messages = [call_args[0][0] for call_args in logger_mock.warning.call_args_list]
        self.assertTrue(
            any('Device Guard' in message and 'WDAC' in message for message in warning_messages),
            "Expected a warning about Device Guard / WDAC code integrity policies to be logged, got: {}".format(
                warning_messages))


if __name__ == '__main__':
    unittest.main()
