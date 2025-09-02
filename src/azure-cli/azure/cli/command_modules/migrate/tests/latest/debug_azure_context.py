#!/usr/bin/env python3
"""Quick debug test for Azure context setting"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unittest.mock import patch, Mock
from test_framework import create_mock_powershell_executor

# Test the mock directly
print("=== Testing mock directly ===")
mock_executor = create_mock_powershell_executor()
result = mock_executor.execute_script_interactive("test script")
print(f"Direct mock result: {result}")
print(f"Type: {type(result)}")

# Test with patching
print("\n=== Testing with patching ===")
with patch('azure.cli.command_modules.migrate.custom.get_powershell_executor') as mock_get_ps:
    mock_get_ps.return_value = create_mock_powershell_executor()
    
    from azure.cli.command_modules.migrate.custom import set_azure_context
    
    try:
        # Create a mock cmd
        mock_cmd = Mock()
        result = set_azure_context(mock_cmd, subscription_id="test-subscription-id")
        print(f"Function result: Success")
    except Exception as e:
        print(f"Function error: {e}")
        print(f"Error type: {type(e)}")
