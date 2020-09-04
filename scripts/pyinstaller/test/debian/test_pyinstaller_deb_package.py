# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import subprocess

root_dir = '/home/xiaojxu/code/pyinstaller/ptest37/lib/python3.7/site-packages/azure/cli/command_modules'
# mod_list = [mod for mod in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']
mod_list = ['vm']

pytest_base_cmd = 'python -m pytest -x -v --boxed -p no:warnings --log-level=WARN'
pytest_parallel_cmd = '{} -n auto'.format(pytest_base_cmd)

for mod_name in mod_list:
    if mod_name in ['botservice', 'network']:
        exit_code = subprocess.call(['{} --junit-xml ./azure_cli_test_result/{}.xml --pyargs azure.cli.command_modules.{}'.format(pytest_base_cmd, mod_name, mod_name)], shell=True)
    else:
        exit_code = subprocess.call(['{} --junit-xml ./azure_cli_test_result/{}.xml --pyargs azure.cli.command_modules.{}'.format(pytest_parallel_cmd, mod_name, mod_name)], shell=True)
    if exit_code == 5:
        print('No tests found for {}'.format(mod_name))
    elif exit_code != 0:
        sys.exit(exit_code)
