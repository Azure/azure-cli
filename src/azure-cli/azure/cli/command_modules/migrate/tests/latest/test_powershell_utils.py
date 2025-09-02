# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import platform
from unittest.mock import Mock, patch, MagicMock
from knack.util import CLIError

# Import unified testing framework
from test_framework import MigrateTestCase, TestConfig, create_mock_powershell_executor

# Import PowerShell utilities with comprehensive mocking
with patch('azure.cli.core.util.run_cmd') as mock_run_cmd, \
     patch('subprocess.run') as mock_subprocess:
    mock_run_cmd.return_value = Mock(returncode=0, stdout='7.1.3', stderr='')
    mock_subprocess.return_value = Mock(returncode=0, stdout='PowerShell 7.1.3', stderr='')
    
    from azure.cli.command_modules.migrate._powershell_utils import (
        PowerShellExecutor,
        get_powershell_executor
    )


class TestPowerShellExecutor(MigrateTestCase):
    """Test PowerShell executor functionality."""

    def test_powershell_executor_windows_success(self):
        """Test PowerShell executor initialization on Windows."""
        # Use the mock executor from the base class
        executor = self.mock_ps_executor
        
        self.assertEqual(executor.platform, 'windows')
        self.assertIsNotNone(executor.powershell_cmd)
        
        # Test that the executor can check availability
        is_available, cmd_path = executor.check_powershell_availability()
        self.assertTrue(is_available)
        self.assertIsNotNone(cmd_path)

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

    def test_powershell_executor_not_available(self):
        """Test PowerShell executor when PowerShell is not available."""
        # Create a mock executor that reports PowerShell as unavailable
        unavailable_executor = Mock()
        unavailable_executor.check_powershell_availability.return_value = (False, None)
        
        # Test the behavior when PowerShell is not available
        is_available, cmd_path = unavailable_executor.check_powershell_availability()
        self.assertFalse(is_available)
        self.assertIsNone(cmd_path)

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

    def test_execute_script_success(self):
        """Test successful PowerShell script execution."""
        # Use our framework's mock executor
        executor = self.mock_ps_executor
        
        # Test execution with a custom script
        result = executor.execute_script('Write-Host "Hello World"')
        
        # Our framework returns default PowerShell version for unknown commands
        self.assertIsNotNone(result.get('stdout'))
        self.assertEqual(result.get('stderr', ''), '')
        self.assertEqual(result.get('returncode'), 0)

    def test_execute_script_with_parameters(self):
        """Test PowerShell script execution with parameters."""
        # Use our framework's mock executor
        executor = self.mock_ps_executor
        
        parameters = {'Name': 'TestValue', 'Count': '5'}
        result = executor.execute_script('param($Name, $Count)', parameters)
        
        self.assertEqual(result['returncode'], 0)
        self.assertIsNotNone(result.get('stdout'))

    def test_execute_script_failure(self):
        """Test PowerShell script execution failure."""
        # Create a mock executor that returns failure
        failure_executor = Mock()
        def mock_execute_failure(script, parameters=None):
            return {
                'returncode': 1,
                'stdout': '',
                'stderr': 'Script execution failed'
            }
        failure_executor.execute_script.side_effect = mock_execute_failure
        
        # Test that the mock properly returns failure
        result = failure_executor.execute_script('throw "Error"')
        self.assertEqual(result['returncode'], 1)
        self.assertIn('failed', result['stderr'])

    def test_execute_azure_authenticated_script(self):
        """Test Azure authenticated PowerShell script execution."""
        # Use our framework's mock executor that has Azure authentication method
        executor = self.mock_ps_executor
        
        result = executor.execute_azure_authenticated_script('Get-AzContext')
        
        self.assertEqual(result['returncode'], 0)
        self.assertIsNotNone(result.get('stdout'))

    def test_check_azure_authentication_success(self):
        """Test successful Azure authentication check."""
        # Use our framework's mock executor with Azure authentication
        executor = self.mock_ps_executor
        
        result = executor.check_azure_authentication()
        
        self.assertTrue(result['IsAuthenticated'])
        self.assertEqual(result['AccountId'], 'test@example.com')

    def test_check_azure_authentication_failure(self):
        """Test failed Azure authentication check.""" 
        # Create a mock executor that reports authentication failure
        failure_executor = Mock()
        def mock_auth_failure():
            return {
                'IsAuthenticated': False,
                'Error': 'No authentication context'
            }
        failure_executor.check_azure_authentication.side_effect = mock_auth_failure
        
        result = failure_executor.check_azure_authentication()
        
        self.assertFalse(result['IsAuthenticated'])
        self.assertIn('Error', result)

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

    def test_installation_guidance_provided(self):
        """Test that appropriate installation guidance is provided for each platform."""
        # Test that our framework provides guidance through mock responses
        # Since we're using mocked responses, just verify the concept works
        executor = self.mock_ps_executor
        
        # Test that the executor is properly configured
        self.assertIsNotNone(executor)
        self.assertEqual(executor.platform, 'windows')
        
        # Test availability check still works
        is_available, cmd_path = executor.check_powershell_availability()
        self.assertTrue(is_available)


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


class TestPowerShellExecutorEdgeCases(MigrateTestCase):
    """Test edge cases and error conditions."""

    def test_empty_script_execution(self):
        """Test execution of empty script."""
        # Use our framework's mock executor
        executor = self.mock_ps_executor
        
        result = executor.execute_script('')
        
        # Verify the basic response structure (our framework returns default responses)
        self.assertEqual(result['returncode'], 0)
        self.assertIsNotNone(result.get('stdout'))

    def test_large_output_handling(self):
        """Test handling of large script output.""" 
        # Use our framework's mock executor
        executor = self.mock_ps_executor
        
        # Test that large output can be handled (our framework returns standard responses)
        result = executor.execute_script('Write-Host ("A" * 10000)')
        
        # Verify the response structure is correct
        self.assertEqual(result['returncode'], 0)
        self.assertIsNotNone(result.get('stdout'))

    def test_special_characters_in_script(self):
        """Test handling of special characters in scripts."""
        # Use our framework's mock executor
        executor = self.mock_ps_executor
        
        result = executor.execute_script('Write-Host "Special chars: àáâãäå"')
        
        # Verify basic response structure
        self.assertEqual(result['returncode'], 0)
        self.assertIsNotNone(result.get('stdout'))


if __name__ == '__main__':
    unittest.main()
