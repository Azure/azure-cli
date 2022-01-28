# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import subprocess

if len(sys.argv) < 2:
    print('AZ_BASE or PYTHON_VERSION are not specified')
    sys.exit(-1)

az_base = sys.argv[1]
python_version = sys.argv[2]

root_dir = '{}/lib/{}/site-packages/azure/cli/command_modules'.format(az_base, python_version)
mod_list = [mod for mod in sorted(os.listdir(root_dir)) if os.path.isdir(os.path.join(root_dir, mod)) and mod != '__pycache__']

pytest_base_cmd = 'PYTHONPATH={}/lib/{}/site-packages python -m pytest -x -v --boxed -p no:warnings --log-level=WARN'.format(az_base, python_version)
pytest_parallel_cmd = '{} -n auto'.format(pytest_base_cmd)

for mod_name in mod_list:
    if mod_name in ['botservice', 'network', 'configure', 'monitor', 'cloud']:
        exit_code = subprocess.call(['{} --junit-xml ./azure_cli_test_result/{}.xml --pyargs azure.cli.command_modules.{}'.format(pytest_base_cmd, mod_name, mod_name)], shell=True)
    else:
        exit_code = subprocess.call(['{} --junit-xml ./azure_cli_test_result/{}.xml --pyargs azure.cli.command_modules.{}'.format(pytest_parallel_cmd, mod_name, mod_name)], shell=True)
    if exit_code == 5:
        print('No tests found for {}'.format(mod_name))
    elif exit_code != 0:
        sys.exit(exit_code)

exit_code = subprocess.call(['{} --junit-xml ./azure_cli_test_result/azure-cli-core.xml --pyargs azure.cli.core'.format(pytest_base_cmd)], shell=True)
sys.exit(exit_code)
