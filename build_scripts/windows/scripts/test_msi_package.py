# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Invoke this script in Powershell with:
# & 'C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\python.exe' test_msi_package.py <start_mod_name>

import os 
import sys
import subprocess 

base_dir = 'C:\\Program Files (x86)\\Microsoft SDKs\\Azure\\CLI2\\Lib\\site-packages\\azure\\cli'
root_dir = '{}\\command_modules'.format(base_dir)
mod_list = [mod for mod in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']

pytest_base_cmd = ['python', '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN']
pytest_parallel_cmd = pytest_base_cmd + ['-n', 'auto']

for mod_name in mod_list:
    try:
        start_mod = sys.argv[1]
        if mod_name < start_mod:
            continue
    except:
        pass
    mod_cmd = ['--junit-xml', '{}\\azure_cli_test_result\\{}.xml'.format(os.path.expanduser('~'), mod_name),
               '--pyargs', 'azure.cli.command_modules.{}'.format(mod_name)]
    if mod_name in ['botservice', 'network']:
        exit_code = subprocess.call(pytest_base_cmd + mod_cmd)
    else:
        exit_code = subprocess.call(pytest_parallel_cmd + mod_cmd)
    if exit_code == 5:
        print('No tests found for {}'.format(mod_name))
    elif exit_code != 0:
        sys.exit(exit_code)

core_dir = '{}\\core'.format(base_dir)
exit_code = subprocess.call(['python', '-m', 'pytest', '-x', '-v', '-p', 'no:warnings', '--log-level', 'WARN', 
    '--junit-xml', '{}\\azure_cli_test_result\\azure-cli-core.xml'.format(os.path.expanduser('~')), '-n', 'auto', '--import-mode=append', core_dir])
sys.exit(exit_code)
