# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import shutil
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
    def test_appservice_clipboard_passes_password_on_stdin(self, resolve, run):
        clip_path = r'C:\Windows\System32\clip.exe'
        resolve.return_value = clip_path
        password = 'TestPassword123!&|^<>%"'

        custom._copy_string_to_clipboard(password)

        resolve.assert_called_once_with('clip.exe')
        run.assert_called_once_with([clip_path], input=password.encode(), check=True)

    @mock.patch('subprocess.run')
    @mock.patch('azure.cli.core.util.get_safe_executable_path', return_value=None)
    def test_appservice_clipboard_missing_executable_fails_closed(self, resolve, run):
        with self.assertRaisesRegex(ValidationError, 'Unable to locate clip.exe to copy'):
            custom._copy_string_to_clipboard('TestPassword123!')

        resolve.assert_called_once_with('clip.exe')
        run.assert_not_called()

    @mock.patch('subprocess.run')
    @mock.patch('azure.cli.core.util.get_safe_executable_path')
    def test_appservice_clipboard_reports_execution_failure(self, resolve, run):
        clip_path = r'C:\Windows\System32\clip.exe'
        resolve.return_value = clip_path
        password = 'TestPassword123'

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
        password = 'TestPassword123!'
        with tempfile.TemporaryDirectory(prefix='safe executable ') as system_root:
            system_dir = os.path.join(system_root, 'System32')
            working_dir = os.path.join(system_root, 'working')
            os.mkdir(system_dir)
            os.mkdir(working_dir)
            clip_path = os.path.join(system_dir, 'clip.exe')
            decoy_paths = [os.path.join(working_dir, name) for name in ('cmd.exe', 'clip.exe', 'clip.cmd')]
            for path in [clip_path] + decoy_paths:
                with open(path, 'wb'):
                    pass

            with mock.patch.dict(os.environ, {'SystemRoot': system_root, 'PATH': working_dir}):
                try:
                    os.chdir(working_dir)
                    custom._copy_string_to_clipboard(password)
                finally:
                    os.chdir(original_cwd)

            run.assert_called_once_with([clip_path], input=password.encode(), check=True)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows only')
    def test_appservice_clipboard_handles_executable_path_with_ampersand(self):
        actual_run = subprocess.run
        system_dir = os.path.join(os.environ['SystemRoot'], 'System32')
        with tempfile.TemporaryDirectory(prefix='safe-executable-') as directory:
            tool_dir = os.path.join(directory, 'Tools&Utilities')
            os.mkdir(tool_dir)
            clip_path = os.path.join(tool_dir, 'clip.exe')
            # Use a harmless stdin consumer instead of modifying the clipboard.
            shutil.copyfile(os.path.join(system_dir, 'sort.exe'), clip_path)
            resolved_paths = {'cmd.exe': os.path.join(system_dir, 'cmd.exe'), 'clip.exe': clip_path}
            results = []

            def capture(args, **kwargs):
                kwargs.update(capture_output=True, timeout=10, cwd=directory)
                result = actual_run(args, **kwargs)
                results.append(result)
                return result

            with mock.patch('azure.cli.core.util.get_safe_executable_path', side_effect=resolved_paths.get), \
                    mock.patch('subprocess.run', side_effect=capture) as run:
                custom._copy_string_to_clipboard('TestPassword123')

            self.assertEqual(results[0].returncode, 0, results[0].stderr)
            self.assertEqual(results[0].stdout.rstrip(b'\r\n'), b'TestPassword123')
            run.assert_called_once_with([clip_path], input=b'TestPassword123', check=True)


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
        show_password.return_value.return_value = {'rdpPassword': 'TestPassword123'}

        def copy_before_success_message(_):
            logger.warning.assert_not_called()
            run_az.assert_not_called()

        copy_password.side_effect = copy_before_success_message
        custom.connect_to_plan_instance(cmd, 'rg', 'plan', 'worker', 'bastion')

        copy_password.assert_called_once_with('TestPassword123')
        logger.warning.assert_any_call('RDP password: [copied to clipboard]')
        run_az.assert_called_once_with([
            'az', 'network', 'bastion', 'rdp', '--name', 'bastion',
            '--resource-group', 'rg', '--target-ip-address', '10.0.0.1'
        ])

        for error in (ValidationError('Unable to locate clip.exe'), CLIInternalError('Clipboard copy failed')):
            with self.subTest(error=type(error).__name__):
                logger.reset_mock()
                run_az.reset_mock()
                copy_password.side_effect = error

                with self.assertRaises(type(error)):
                    custom.connect_to_plan_instance(cmd, 'rg', 'plan', 'worker', 'bastion')

                logger.warning.assert_not_called()
                run_az.assert_not_called()
