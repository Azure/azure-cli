#!/usr/bin/env python3
"""Test to debug the exact issue with set_azure_context"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch, Mock

def test_azure_context_issue():
    """Debug the set_azure_context issue"""
    from test_framework import create_mock_powershell_executor
    
    # Create the mock exactly as the framework does
    mock_executor = create_mock_powershell_executor()
    print(f"Mock executor type: {type(mock_executor)}")
    print(f"Has execute_script_interactive: {hasattr(mock_executor, 'execute_script_interactive')}")
    
    # Test the interactive method directly
    result = mock_executor.execute_script_interactive("test script")
    print(f"Direct interactive call result: {result}")
    print(f"Direct interactive call result type: {type(result)}")
    
    # Test with a patch
    with patch('azure.cli.command_modules.migrate.custom.get_powershell_executor') as mock_get_ps:
        mock_get_ps.return_value = mock_executor
        
        # Import the function
        from azure.cli.command_modules.migrate.custom import set_azure_context
        
        # Get the PowerShell executor to check what it actually returns
        from azure.cli.command_modules.migrate.custom import get_powershell_executor
        ps_exec = get_powershell_executor()
        print(f"PowerShell executor from function: {ps_exec}")
        print(f"Type: {type(ps_exec)}")
        
        # Test the interactive method on the returned executor
        interactive_result = ps_exec.execute_script_interactive("test")
        print(f"Interactive result from get_powershell_executor: {interactive_result}")
        print(f"Type: {type(interactive_result)}")

if __name__ == "__main__":
    test_azure_context_issue()
