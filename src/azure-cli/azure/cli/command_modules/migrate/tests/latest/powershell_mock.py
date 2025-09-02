# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
PowerShell Mock System for Azure Migrate CLI Tests
This module provides comprehensive mocking for PowerShell cmdlets with realistic responses.
"""

import re
import json
from unittest.mock import Mock


class PowerShellCmdletMocker:
    """Mock system that provides realistic responses for specific PowerShell cmdlets."""
    
    def __init__(self):
        self.cmdlet_responses = {
            # PowerShell version and system info
            '$PSVersionTable.PSVersion.ToString()': {
                'stdout': '7.3.4',
                'stderr': '',
                'exit_code': 0
            },
            '$PSVersionTable.PSVersion.Major': {
                'stdout': '7',
                'stderr': '',
                'exit_code': 0
            },
            
            # Azure module checks
            'Get-Module -ListAvailable Az.*': {
                'stdout': 'Az.Accounts    2.15.1\nAz.Migrate     2.1.0\nAz.Resources   6.5.3',
                'stderr': '',
                'exit_code': 0
            },
            'Get-Module -ListAvailable Az.Migrate': {
                'stdout': 'ModuleType Version    Name                                ExportedCommands\n' +
                         'Manifest   2.1.0      Az.Migrate                          {Get-AzMigrateProject, New-AzMigrateProject...}',
                'stderr': '',
                'exit_code': 0
            },
            
            # Azure authentication
            'Connect-AzAccount': {
                'stdout': 'Account                 SubscriptionName        TenantId\n' +
                         'user@contoso.com        My Subscription         12345678-1234-1234-1234-123456789012',
                'stderr': '',
                'exit_code': 0
            },
            'Disconnect-AzAccount': {
                'stdout': 'Disconnected from Azure account.',
                'stderr': '',
                'exit_code': 0
            }
        }

    def get_response(self, script_content):
        """Get mock response for a PowerShell script."""
        # Clean up the script content
        clean_script = script_content.strip()
        
        # Check for exact matches first
        if clean_script in self.cmdlet_responses:
            return self.cmdlet_responses[clean_script]
        
        # Handle Azure cmdlets
        if any(cmdlet in clean_script for cmdlet in ['Connect-Az', 'Set-Az', 'Get-Az', 'New-Az']):
            return {
                'stdout': 'Azure operation completed successfully',
                'stderr': '',
                'exit_code': 0
            }
        
        # Default response for unknown cmdlets
        return {
            'stdout': 'Mock PowerShell command executed successfully',
            'stderr': '',
            'exit_code': 0
        }


def create_mock_powershell_executor():
    """Create a fully mocked PowerShell executor for testing."""
    mocker = PowerShellCmdletMocker()
    
    # Create the mock executor
    mock_executor = Mock()
    mock_executor.platform = 'windows'
    mock_executor.powershell_cmd = 'powershell'
    
    # Mock availability check
    mock_executor.check_powershell_availability.return_value = (True, 'powershell')
    
    # Mock script execution with smart responses
    def mock_execute_script(script_content, parameters=None):
        return mocker.get_response(script_content)
    
    def mock_execute_script_interactive(script_content, parameters=None):
        result = mock_execute_script(script_content, parameters)
        return result
    
    mock_executor.execute_script.side_effect = mock_execute_script
    mock_executor.execute_script_interactive.side_effect = mock_execute_script_interactive
    
    return mock_executor


if __name__ == '__main__':
    # Test the mock system
    mock_ps = create_mock_powershell_executor()
    
    # Test various cmdlets
    test_scripts = [
        '$PSVersionTable.PSVersion.ToString()',
        'Get-Module -ListAvailable Az.Migrate',
        'Connect-AzAccount'
    ]
    
    print("Testing PowerShell Mock System:")
    print("=" * 50)
    
    for script in test_scripts:
        print(f"\nScript: {script}")
        result = mock_ps.execute_script(script)
        print(f"Result: {result['stdout'][:100]}")
        print(f"Exit Code: {result['exit_code']}")