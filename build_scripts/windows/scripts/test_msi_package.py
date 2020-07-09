# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Invoke this script in Powershell with:
# & 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' test_msi_package.py

import os 
import sys
import subprocess 

root_dir = 'C:\\Program Files (x86)\\Microsoft SDKs\\Azure\\CLI2\\Lib\\site-packages\\azure\\cli\\command_modules'

mod_list = [mod for mod in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']

for mod_name in mod_list:
    exit_code = subprocess.call(['python', '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN', 
        '--junit-xml', '{}\\azure_cli_test_result\\{}.xml'.format(os.path.expanduser('~'), mod_name), '-n', 'auto', '--pyargs', 'azure.cli.command_modules.{}'.format(mod_name)])
    if exit_code != 0 and exit_code != 5:  # exit code is 5 when there is no tests collected in the module
        sys.exit(exit_code)

exit_code = subprocess.call(['python', '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN', 
    '--junit-xml', '{}\\azure_cli_test_result\\azure-cli-core.xml'.format(os.path.expanduser('~')), '-n', 'auto', '--pyargs', 'azure.cli.core', '--import-mode=append'])
sys.exit(exit_code)
