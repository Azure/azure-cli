# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import tempfile
import unittest
from unittest import mock

from azure.cli.command_modules.appservice import custom
from azure.cli.core.azclierror import ValidationError


class AppServicePlanClipboardTest(unittest.TestCase):
    @mock.patch('azure.cli.core.util.run_cmd')
    @mock.patch('azure.cli.core.util.get_safe_executable_path')
    def test_appservice_clipboard_uses_resolved_executable_paths(self, resolve, run):
        cmd_path = r'C:\Windows\System32\cmd.exe'
        clip_path = r'C:\Windows\System32\clip.exe'
        resolve.side_effect = [cmd_path, clip_path]
        password = 'TestPassword123!'

        custom._copy_string_to_clipboard(password)

        self.assertEqual(resolve.call_args_list, [mock.call('cmd.exe'), mock.call('clip.exe')])
        run.assert_called_once_with(
            [cmd_path, '/c', 'echo', '|', 'set', '/p={}|'.format(password), clip_path], check=False)

    @mock.patch('azure.cli.core.util.run_cmd')
    @mock.patch('azure.cli.core.util.get_safe_executable_path')
    def test_appservice_clipboard_missing_executable_fails_closed(self, resolve, run):
        for executable, paths in (('cmd.exe', [None]), ('clip.exe', [r'C:\Windows\System32\cmd.exe', None])):
            with self.subTest(executable=executable):
                resolve.reset_mock()
                resolve.side_effect = paths
                with self.assertRaisesRegex(ValidationError, f'Unable to locate {executable} to copy'):
                    custom._copy_string_to_clipboard('TestPassword123!')

                self.assertEqual(resolve.call_count, len(paths))
                run.assert_not_called()

    @unittest.skipUnless(sys.platform == 'win32', 'Windows only')
    @mock.patch('azure.cli.core.util.run_cmd')
    def test_appservice_clipboard_ignores_working_directory_executables(self, run):
        original_cwd = os.getcwd()
        password = 'TestPassword123!'
        with tempfile.TemporaryDirectory(prefix='safe executable ') as system_root:
            system_dir = os.path.join(system_root, 'System32')
            working_dir = os.path.join(system_root, 'working')
            os.mkdir(system_dir)
            os.mkdir(working_dir)
            cmd_path = os.path.join(system_dir, 'cmd.exe')
            clip_path = os.path.join(system_dir, 'clip.exe')
            decoy_paths = [os.path.join(working_dir, name) for name in ('cmd.exe', 'clip.exe', 'clip.cmd')]
            for path in [cmd_path, clip_path] + decoy_paths:
                with open(path, 'wb'):
                    pass

            with mock.patch.dict(os.environ, {'SystemRoot': system_root, 'PATH': working_dir}):
                try:
                    os.chdir(working_dir)
                    custom._copy_string_to_clipboard(password)
                finally:
                    os.chdir(original_cwd)

            run.assert_called_once_with(
                [cmd_path, '/c', 'echo', '|', 'set', '/p={}|'.format(password), clip_path], check=False)
