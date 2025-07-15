#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

from azure.cli.command_modules.migrate import MigrateCommandsLoader
from azure.cli.core.mock import DummyCli

def test_command_loader():
    try:
        cli = DummyCli()
        loader = MigrateCommandsLoader(cli)
        
        # Load command table
        command_table = loader.load_command_table(None)
        print(f'Loaded {len(command_table)} commands:')
        for cmd_name in sorted(command_table.keys()):
            print(f'  - {cmd_name}')
        
        # Load arguments
        for cmd_name in command_table.keys():
            try:
                loader.load_arguments(cmd_name)
                print(f'Arguments loaded for: {cmd_name}')
            except Exception as e:
                print(f'Error loading arguments for {cmd_name}: {e}')
                
        return True
        
    except Exception as e:
        print(f'Error testing command loader: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_command_loader()
    sys.exit(0 if success else 1)
