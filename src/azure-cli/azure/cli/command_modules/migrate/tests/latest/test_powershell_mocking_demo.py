#!/usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Simple demonstration of PowerShell cmdlet mocking for Azure Migrate CLI tests.
This shows how to mock specific PowerShell commands with realistic responses.
"""

import unittest
from unittest.mock import patch
from powershell_mock import create_mock_powershell_executor

# Import with comprehensive mocking
with patch('azure.cli.command_modules.migrate.custom.get_powershell_executor') as mock_get_ps:
    mock_get_ps.return_value = create_mock_powershell_executor()
    from azure.cli.command_modules.migrate.custom import check_migration_prerequisites


class TestPowerShellMocking(unittest.TestCase):
    """Demonstrate PowerShell mocking with specific cmdlet responses."""

    def setUp(self):
        """Set up test with mocked PowerShell executor."""
        self.mock_ps_executor = create_mock_powershell_executor()
        
        # Patch all PowerShell executor calls
        self.ps_patcher = patch('azure.cli.command_modules.migrate.custom.get_powershell_executor', 
                               return_value=self.mock_ps_executor)
        self.ps_patcher.start()

    def tearDown(self):
        """Clean up patches."""
        self.ps_patcher.stop()

    def test_powershell_version_check(self):
        """Test that PowerShell version check returns mocked response."""
        result = self.mock_ps_executor.execute_script('$PSVersionTable.PSVersion.ToString()')
        self.assertEqual(result['stdout'], '7.3.4')
        self.assertEqual(result['exit_code'], 0)

    def test_azure_module_check(self):
        """Test that Azure module check returns mocked response."""
        result = self.mock_ps_executor.execute_script('Get-Module -ListAvailable Az.Migrate')
        self.assertIn('Az.Migrate', result['stdout'])
        self.assertEqual(result['exit_code'], 0)

    def test_azure_connection(self):
        """Test that Azure connection returns mocked response."""
        result = self.mock_ps_executor.execute_script('Connect-AzAccount')
        self.assertIn('user@contoso.com', result['stdout'])
        self.assertEqual(result['exit_code'], 0)

    @patch('platform.system', return_value='Windows')
    @patch('platform.version', return_value='10.0.19041')
    @patch('platform.python_version', return_value='3.9.7')
    def test_check_migration_prerequisites_with_mocked_powershell(self, mock_python_ver, mock_platform_ver, mock_platform):
        """Test the full migration prerequisites check with mocked PowerShell."""
        from unittest.mock import Mock
        
        cmd = Mock()
        result = check_migration_prerequisites(cmd)
        
        # Verify the result contains expected data
        self.assertEqual(result['platform'], 'Windows')
        self.assertEqual(result['python_version'], '3.9.7')
        self.assertTrue(result['powershell_available'])
        # Note: azure_powershell_available depends on the specific mocking in the function

    def test_custom_cmdlet_response(self):
        """Test that unknown cmdlets get default response."""
        result = self.mock_ps_executor.execute_script('Get-CustomMigrationData')
        self.assertIn('Mock PowerShell command executed successfully', result['stdout'])
        self.assertEqual(result['exit_code'], 0)


if __name__ == '__main__':
    # Run just these demonstration tests
    unittest.main(verbosity=2)
