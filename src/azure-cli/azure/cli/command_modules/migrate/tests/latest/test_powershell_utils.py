# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import platform
from unittest.mock import Mock, patch, MagicMock
from knack.util import CLIError

# Mock all external dependencies at import time
with patch('azure.cli.core.util.run_cmd') as mock_run_cmd:
    mock_run_cmd.return_value = Mock(returncode=0, stdout='7.1.3', stderr='')
    from azure.cli.command_modules.migrate._powershell_utils import (
        PowerShellExecutor,
        get_powershell_executor
    )


class TestPowerShellExecutor(unittest.TestCase):
    """Test PowerShell executor functionality."""

    def setUp(self):
        self.original_platform = platform.system

    def tearDown(self):
        platform.system = self.original_platform

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_powershell_executor_windows_success(self, mock_platform, mock_run_cmd):
        """Test PowerShell executor initialization on Windows."""
        mock_platform.return_value = 'Windows'
        
        # Mock successful PowerShell detection
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '5.1.19041.1682'
        mock_run_cmd.return_value = mock_result
        
        executor = PowerShellExecutor()
        
        self.assertEqual(executor.platform, 'windows')
        self.assertIsNotNone(executor.powershell_cmd)
        mock_run_cmd.assert_called()

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_powershell_executor_linux_pwsh_available(self, mock_platform, mock_run_cmd):
        """Test PowerShell executor initialization on Linux with pwsh available."""
        mock_platform.return_value = 'Linux'
        
        # Mock successful pwsh detection
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '7.3.0'
        mock_run_cmd.return_value = mock_result
        
        executor = PowerShellExecutor()
        
        self.assertEqual(executor.platform, 'linux')
        self.assertEqual(executor.powershell_cmd, 'pwsh')

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_powershell_executor_not_available(self, mock_platform, mock_run_cmd):
        """Test PowerShell executor when PowerShell is not available."""
        mock_platform.return_value = 'Linux'
        
        # Mock PowerShell not found
        mock_run_cmd.side_effect = Exception('Command not found')
        
        with self.assertRaises(CLIError) as context:
            PowerShellExecutor()
        
        self.assertIn('PowerShell is not available', str(context.exception))

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_check_powershell_availability(self, mock_platform, mock_run_cmd):
        """Test checking PowerShell availability."""
        mock_platform.return_value = 'Windows'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '5.1.19041.1682'
        mock_run_cmd.return_value = mock_result
        
        executor = PowerShellExecutor()
        is_available, cmd = executor.check_powershell_availability()
        
        self.assertTrue(is_available)
        self.assertIsNotNone(cmd)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_script_success(self, mock_platform, mock_run_cmd):
        """Test successful PowerShell script execution."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock script execution
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = 'Script executed successfully'
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        result = executor.execute_script('Write-Host "Hello World"')
        
        self.assertEqual(result['stdout'], 'Script executed successfully')
        self.assertEqual(result['stderr'], '')
        self.assertEqual(result['returncode'], 0)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_script_with_parameters(self, mock_platform, mock_run_cmd):
        """Test PowerShell script execution with parameters."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock script execution
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = 'Parameter test passed'
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        parameters = {'Name': 'TestValue', 'Count': '5'}
        result = executor.execute_script('param($Name, $Count)', parameters)
        
        self.assertEqual(result['returncode'], 0)
        # Verify parameters were included in the command
        call_args = mock_run_cmd.call_args_list[1]
        command_args = call_args[0][0]
        self.assertIn('-Name "TestValue"', command_args[-1])
        self.assertIn('-Count "5"', command_args[-1])

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_script_failure(self, mock_platform, mock_run_cmd):
        """Test PowerShell script execution failure."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock script execution failure
        mock_execution_result = Mock()
        mock_execution_result.returncode = 1
        mock_execution_result.stdout = ''
        mock_execution_result.stderr = 'Script execution failed'
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        
        with self.assertRaises(CLIError) as context:
            executor.execute_script('throw "Error"')
        
        self.assertIn('PowerShell command failed', str(context.exception))

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_script_timeout(self, mock_platform, mock_run_cmd):
        """Test PowerShell script execution timeout."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock timeout exception
        from subprocess import TimeoutExpired
        mock_run_cmd.side_effect = [mock_detection_result, TimeoutExpired('powershell', 300)]
        
        executor = PowerShellExecutor()
        
        with self.assertRaises(TimeoutExpired):
            executor.execute_script('Start-Sleep 400')

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_azure_authenticated_script(self, mock_platform, mock_run_cmd):
        """Test Azure authenticated PowerShell script execution."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock authentication check
        mock_auth_result = Mock()
        mock_auth_result.returncode = 0
        mock_auth_result.stdout = '{"IsAuthenticated": true}'
        mock_auth_result.stderr = ''
        
        # Mock script execution
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = 'Azure script executed'
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [
            mock_detection_result,  # PowerShell detection
            mock_auth_result,       # Authentication check
            mock_execution_result   # Script execution
        ]
        
        executor = PowerShellExecutor()
        result = executor.execute_azure_authenticated_script('Get-AzContext')
        
        self.assertEqual(result['stdout'], 'Azure script executed')

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_check_azure_authentication_success(self, mock_platform, mock_run_cmd):
        """Test successful Azure authentication check."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock authentication check
        mock_auth_result = Mock()
        mock_auth_result.returncode = 0
        mock_auth_result.stdout = '{"IsAuthenticated": true, "AccountId": "test@example.com"}'
        mock_auth_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_auth_result]
        
        executor = PowerShellExecutor()
        result = executor.check_azure_authentication()
        
        self.assertTrue(result['IsAuthenticated'])
        self.assertEqual(result['AccountId'], 'test@example.com')

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_check_azure_authentication_failure(self, mock_platform, mock_run_cmd):
        """Test failed Azure authentication check."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock authentication check failure
        mock_auth_result = Mock()
        mock_auth_result.returncode = 0
        mock_auth_result.stdout = '{"IsAuthenticated": false, "Error": "No authentication context"}'
        mock_auth_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_auth_result]
        
        executor = PowerShellExecutor()
        result = executor.check_azure_authentication()
        
        self.assertFalse(result['IsAuthenticated'])
        self.assertIn('Error', result)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_execute_script_interactive(self, mock_platform, mock_run_cmd):
        """Test interactive PowerShell script execution."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock interactive execution
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = 'Interactive output'
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        result = executor.execute_script_interactive('Read-Host "Enter value"')
        
        self.assertEqual(result['returncode'], 0)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_cross_platform_detection_macos(self, mock_platform, mock_run_cmd):
        """Test PowerShell detection on macOS."""
        mock_platform.return_value = 'Darwin'
        
        # Mock successful pwsh detection on macOS
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '7.3.0'
        mock_run_cmd.return_value = mock_result
        
        executor = PowerShellExecutor()
        
        self.assertEqual(executor.platform, 'darwin')
        self.assertEqual(executor.powershell_cmd, 'pwsh')

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_installation_guidance_provided(self, mock_platform, mock_run_cmd):
        """Test that appropriate installation guidance is provided for each platform."""
        # Test Windows guidance
        mock_platform.return_value = 'Windows'
        mock_run_cmd.side_effect = Exception('Command not found')
        
        with self.assertRaises(CLIError) as context:
            PowerShellExecutor()
        
        self.assertIn('https://github.com/PowerShell/PowerShell', str(context.exception))
        
        # Test Linux guidance
        mock_platform.return_value = 'Linux'
        mock_run_cmd.side_effect = Exception('Command not found')
        
        with self.assertRaises(CLIError) as context:
            PowerShellExecutor()
        
        self.assertIn('sudo apt', str(context.exception))
        
        # Test macOS guidance
        mock_platform.return_value = 'Darwin'
        mock_run_cmd.side_effect = Exception('Command not found')
        
        with self.assertRaises(CLIError) as context:
            PowerShellExecutor()
        
        self.assertIn('brew install', str(context.exception))


class TestPowerShellExecutorFactory(unittest.TestCase):
    """Test PowerShell executor factory function."""

    @patch('azure.cli.command_modules.migrate._powershell_utils.PowerShellExecutor')
    def test_get_powershell_executor_success(self, mock_executor_class):
        """Test successful PowerShell executor creation."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        
        result = get_powershell_executor()
        
        self.assertEqual(result, mock_executor)
        mock_executor_class.assert_called_once()

    @patch('azure.cli.command_modules.migrate._powershell_utils.PowerShellExecutor')
    def test_get_powershell_executor_failure(self, mock_executor_class):
        """Test PowerShell executor creation failure."""
        mock_executor_class.side_effect = CLIError('PowerShell not available')
        
        with self.assertRaises(CLIError):
            get_powershell_executor()


class TestPowerShellExecutorEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_empty_script_execution(self, mock_platform, mock_run_cmd):
        """Test execution of empty script."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock empty script execution
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = ''
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        result = executor.execute_script('')
        
        self.assertEqual(result['stdout'], '')
        self.assertEqual(result['returncode'], 0)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_large_output_handling(self, mock_platform, mock_run_cmd):
        """Test handling of large script output."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock large output
        large_output = 'A' * 10000  # 10KB output
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = large_output
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        result = executor.execute_script('Write-Host ("A" * 10000)')
        
        self.assertEqual(result['stdout'], large_output)
        self.assertEqual(len(result['stdout']), 10000)

    @patch('azure.cli.core.util.run_cmd')
    @patch('platform.system')
    def test_special_characters_in_script(self, mock_platform, mock_run_cmd):
        """Test handling of special characters in scripts."""
        mock_platform.return_value = 'Windows'
        
        # Mock PowerShell detection
        mock_detection_result = Mock()
        mock_detection_result.returncode = 0
        mock_detection_result.stdout = '5.1.19041.1682'
        
        # Mock script with special characters
        mock_execution_result = Mock()
        mock_execution_result.returncode = 0
        mock_execution_result.stdout = 'Special chars: àáâãäå'
        mock_execution_result.stderr = ''
        
        mock_run_cmd.side_effect = [mock_detection_result, mock_execution_result]
        
        executor = PowerShellExecutor()
        result = executor.execute_script('Write-Host "Special chars: àáâãäå"')
        
        self.assertIn('àáâãäå', result['stdout'])


if __name__ == '__main__':
    unittest.main()
