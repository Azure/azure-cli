# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest import mock

from azure.cli.core.azclierror import CLIError
from azure.cli.command_modules.acr.custom import _validate_command_path


class TestValidateCommandPath(unittest.TestCase):
    """Tests for _validate_command_path CWD validation logic."""

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_binary_in_cwd_is_blocked(self, mock_getcwd, mock_which):
        """A docker binary located directly in CWD should be rejected."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/home/user/repo/docker'

        with self.assertRaises(CLIError) as ctx:
            _validate_command_path('docker', is_diagnostics_context=False)
        self.assertIn('Refusing to use', str(ctx.exception))

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_binary_in_system_path_is_allowed(self, mock_getcwd, mock_which):
        """A docker binary in a system directory should be allowed."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/usr/bin/docker'

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_binary_in_subdirectory_of_cwd_is_allowed(self, mock_getcwd, mock_which):
        """A docker binary in a subdirectory of CWD should be allowed (only direct CWD is blocked)."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/home/user/repo/tools/docker'

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_binary_at_root_cwd_is_allowed(self, mock_getcwd, mock_which):
        """When CWD is filesystem root, system docker should not be blocked."""
        mock_getcwd.return_value = '/'
        mock_which.return_value = '/usr/bin/docker'

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    def test_binary_not_found_is_allowed(self, mock_which):
        """When docker is not found at all, validation should pass (let downstream handle it)."""
        mock_which.return_value = None

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_diagnostics_mode_returns_true_on_unsafe(self, mock_getcwd, mock_which):
        """In diagnostics mode, should return True (unsafe) instead of raising."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/home/user/repo/docker'

        result = _validate_command_path('docker', is_diagnostics_context=True)
        self.assertTrue(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_diagnostics_mode_returns_false_on_safe(self, mock_getcwd, mock_which):
        """In diagnostics mode, should return False (safe) for system-path docker."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/usr/bin/docker'

        result = _validate_command_path('docker', is_diagnostics_context=True)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_windows_cwd_binary_is_blocked(self, mock_getcwd, mock_which):
        """A docker binary (with platform extension) in CWD should be blocked."""
        if os.name == 'nt':
            mock_getcwd.return_value = 'C:\\Users\\dev\\repo'
            mock_which.return_value = 'C:\\Users\\dev\\repo\\docker.exe'
        else:
            mock_getcwd.return_value = '/home/dev/repo'
            mock_which.return_value = '/home/dev/repo/docker'

        with self.assertRaises(CLIError):
            _validate_command_path('docker', is_diagnostics_context=False)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_windows_system_docker_is_allowed(self, mock_getcwd, mock_which):
        """Docker in a system directory (not CWD) should be allowed."""
        if os.name == 'nt':
            mock_getcwd.return_value = 'C:\\Users\\dev\\repo'
            mock_which.return_value = 'C:\\Program Files\\Docker\\docker.exe'
        else:
            mock_getcwd.return_value = '/home/dev/repo'
            mock_which.return_value = '/usr/local/bin/docker'

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_windows_root_cwd_does_not_block_system_docker(self, mock_getcwd, mock_which):
        """When CWD is the filesystem root, system docker should not be blocked."""
        if os.name == 'nt':
            mock_getcwd.return_value = 'C:\\'
            mock_which.return_value = 'C:\\Program Files\\Docker\\docker.exe'
        else:
            mock_getcwd.return_value = '/'
            mock_which.return_value = '/usr/bin/docker'

        result = _validate_command_path('docker', is_diagnostics_context=False)
        self.assertFalse(result)

    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_error_message_includes_override_instruction(self, mock_getcwd, mock_which):
        """Error message should tell user how to override with DOCKER_COMMAND."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/home/user/repo/docker'

        with self.assertRaises(CLIError) as ctx:
            _validate_command_path('docker', is_diagnostics_context=False)
        self.assertIn('DOCKER_COMMAND', str(ctx.exception))
        self.assertIn('absolute path', str(ctx.exception))

    @mock.patch('azure.cli.command_modules.acr.custom.os.path.realpath')
    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_symlink_in_cwd_pointing_to_system_binary_is_blocked(self, mock_getcwd, mock_which, mock_realpath):
        """A symlink in CWD pointing to /usr/bin/docker should still be blocked (uses abspath, not realpath)."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/home/user/repo/docker'
        mock_realpath.return_value = '/usr/bin/docker'

        with self.assertRaises(CLIError):
            _validate_command_path('docker', is_diagnostics_context=False)

    @mock.patch('azure.cli.command_modules.acr.custom.os.path.realpath')
    @mock.patch('azure.cli.command_modules.acr.custom.os.path.abspath')
    @mock.patch('azure.cli.command_modules.acr.custom.shutil.which')
    @mock.patch('azure.cli.command_modules.acr.custom.os.getcwd')
    def test_system_binary_symlink_resolving_to_cwd_is_blocked(self, mock_getcwd, mock_which, mock_abspath,
                                                               mock_realpath):
        """A binary outside CWD whose realpath resolves into the CWD should be blocked."""
        mock_getcwd.return_value = '/home/user/repo'
        mock_which.return_value = '/usr/local/bin/docker'
        mock_abspath.side_effect = lambda p: p if p != '.' else '/home/user/repo'
        mock_realpath.return_value = '/home/user/repo/docker'

        with self.assertRaises(CLIError):
            _validate_command_path('docker', is_diagnostics_context=False)
