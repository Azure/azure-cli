# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from azure.cli.command_modules.appservice import custom
from azure.cli.core.azclierror import CLIInternalError, ValidationError


class AppServicePlanClipboardTest(unittest.TestCase):
    @mock.patch('subprocess.run')
    @mock.patch('azure.cli.core.util.get_safe_executable_path')
    def test_appservice_clipboard_passes_password_only_on_stdin(self, resolve, run):
        clip_path = r'C:\Windows\System32\clip.exe'
        resolve.return_value = clip_path
        password = 'Test password&|^<>%!"\u00e9'

        custom._copy_string_to_clipboard(password)

        resolve.assert_called_once_with('clip.exe')
        run.assert_called_once_with([clip_path], input=password.encode('utf-16-le'), check=True)

    @mock.patch('subprocess.run')
    @mock.patch('azure.cli.core.util.get_safe_executable_path', return_value=None)
    def test_appservice_clipboard_missing_executable_fails_closed(self, resolve, run):
        with self.assertRaisesRegex(ValidationError, 'Unable to locate clip.exe'):
            custom._copy_string_to_clipboard('Test password')

        run.assert_not_called()

    @mock.patch('subprocess.run')
    @mock.patch('azure.cli.core.util.get_safe_executable_path')
    def test_appservice_clipboard_reports_execution_failure(self, resolve, run):
        clip_path = r'C:\Windows\System32\clip.exe'
        resolve.return_value = clip_path
        password = 'Test password'

        for error in (OSError('Clipboard unavailable'), subprocess.CalledProcessError(1, [clip_path])):
            with self.subTest(error=type(error).__name__):
                run.side_effect = error
                with self.assertRaisesRegex(CLIInternalError, 'Failed to copy the RDP password') as raised:
                    custom._copy_string_to_clipboard(password)
                self.assertNotIn(password, str(raised.exception))

    @unittest.skipUnless(sys.platform == 'win32', 'Windows only')
    @mock.patch('subprocess.run')
    def test_appservice_clipboard_ignores_working_directory_executables(self, run):
        original_cwd = os.getcwd()
        password = 'Test password'
        with tempfile.TemporaryDirectory() as system_root:
            system_dir = os.path.join(system_root, 'System32')
            working_dir = os.path.join(system_root, 'working')
            os.mkdir(system_dir)
            os.mkdir(working_dir)
            clip_path = os.path.join(system_dir, 'clip.exe')
            for path in [clip_path] + [os.path.join(working_dir, name)
                                       for name in ('cmd.exe', 'clip.exe', 'clip.cmd')]:
                with open(path, 'wb'):
                    pass

            with mock.patch.dict(os.environ, {'SystemRoot': system_root, 'PATH': working_dir}):
                try:
                    os.chdir(working_dir)
                    custom._copy_string_to_clipboard(password)
                finally:
                    os.chdir(original_cwd)

            run.assert_called_once_with([clip_path], input=password.encode('utf-16-le'), check=True)


class AppServicePlanInstanceConnectTest(unittest.TestCase):
    @mock.patch.object(custom, 'logger')
    @mock.patch('azure.cli.core.util.run_az_cmd')
    @mock.patch.object(custom, '_copy_string_to_clipboard')
    @mock.patch.object(custom, 'AppServicePlanManagedInstanceShowRdpPassword')
    @mock.patch.object(custom, 'AppServicePlanManagedInstanceList')
    def test_appservice_plan_connect_requires_successful_clipboard_copy(
            self, list_instances, show_password, copy_password, run_az, logger):
        cmd = mock.Mock()
        list_instances.return_value.return_value = {
            'instances': [{'instanceName': 'worker', 'ipAddress': '10.0.0.1'}]
        }
        show_password.return_value.return_value = {'rdpPassword': 'Test password'}

        def copy_before_success_message(_):
            logger.warning.assert_not_called()
            run_az.assert_not_called()

        copy_password.side_effect = copy_before_success_message
        custom.connect_to_plan_instance(cmd, 'rg', 'plan', 'worker', 'bastion')

        copy_password.assert_called_once_with('Test password')
        logger.warning.assert_any_call('RDP password: [copied to clipboard]')
        run_az.assert_called_once_with([
            'az', 'network', 'bastion', 'rdp', '--name', 'bastion',
            '--resource-group', 'rg', '--target-ip-address', '10.0.0.1'
        ])

        logger.reset_mock()
        run_az.reset_mock()
        copy_password.side_effect = CLIInternalError('Failed to copy the RDP password to the clipboard.')

        with self.assertRaises(CLIInternalError):
            custom.connect_to_plan_instance(cmd, 'rg', 'plan', 'worker', 'bastion')

        logger.warning.assert_not_called()
        run_az.assert_not_called()
