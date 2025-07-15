#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from azure.cli.command_modules.migrate._powershell_utils import get_powershell_executor

def test_powershell_executor():
    try:
        executor = get_powershell_executor()
        print(f'PowerShell executor created successfully')
        print(f'Platform: {executor.platform}')
        print(f'PowerShell command: {executor.powershell_cmd}')
        
        # Test simple command
        result = executor.execute_script('Write-Host "Hello from PowerShell"')
        print(f'PowerShell script executed successfully')
        print(f'Output: {result["stdout"]}')
        
        # Test prerequisites check
        prereqs = executor.check_migration_prerequisites()
        print(f'Prerequisites check successful: {prereqs}')
        
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

if __name__ == '__main__':
    success = test_powershell_executor()
    sys.exit(0 if success else 1)
