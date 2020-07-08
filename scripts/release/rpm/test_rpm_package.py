# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import subprocess

d = '/usr/lib64/az/lib/python3.6/site-packages/azure/cli/command_modules'
mod_list = [os.path.join(d, o) for o in sorted(os.listdir(d)) if os.path.isdir(os.path.join(d, o)) and o != '__pycache__']

for mod in mod_list:
    mod_name = os.path.basename(os.path.normpath(mod))
    if mod_name == 'botservice':
        exit_code = subprocess.call(['PYTHONPATH=/usr/lib64/az/lib/python3.6/site-packages python3 -m pytest -x -v --boxed -p no:warnings --log-level=WARN --junit-xml /result/{}.xml --pyargs azure.cli.command_modules.{}'.format(mod_name, mod_name)], shell=True)
    else:
        exit_code = subprocess.call(['PYTHONPATH=/usr/lib64/az/lib/python3.6/site-packages python3 -m pytest -x -v --boxed -p no:warnings --log-level=WARN --junit-xml /result/{}.xml -n auto --pyargs azure.cli.command_modules.{}'.format(mod_name, mod_name)], shell=True)
    if exit_code != 0 and exit_code != 5:  # exit code is 5 when there is no tests collected
        sys.exit(exit_code)
exit_code = subprocess.call(['PYTHONPATH=/usr/lib64/az/lib/python3.6/site-packages python3 -m pytest -x -v --boxed -p no:warnings --log-level=WARN --junit-xml /result/azure-cli-core.xml -n auto --pyargs azure.cli.core'], shell=True)
sys.exit(exit_code)
