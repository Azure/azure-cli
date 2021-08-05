#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
import os
from subprocess import check_call, CalledProcessError
from logging import getLogger

root_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))
logger = getLogger(__name__)

def print_support_message():
    logger.warning('''

*******************************************************************************

dev_setup.py is no longer supported for developer use.
Instead, please do the following:

create and activate new venv
pip install azdev
azdev setup -c

For full details, please read
 https://github.com/Azure/azure-cli/blob/dev/doc/configuring_your_machine.md

*******************************************************************************

''')


def py_command(command):
    try:
        print('Executing: python ' + command)
        check_call([sys.executable] + command.split(), cwd=root_dir)
        print()
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        print_support_message()
        sys.exit(1)

def pip_command(command):
    py_command('-m pip ' + command)

print_support_message()

print('Running dev setup...')
print('Root directory \'{}\'\n'.format(root_dir))

# install private whls if there are any
privates_dir = os.path.join(root_dir, 'privates')
if os.path.isdir(privates_dir) and os.listdir(privates_dir):
    whl_list = ' '.join([os.path.join(privates_dir, f) for f in os.listdir(privates_dir)])
    pip_command('install {}'.format(whl_list))

# install general requirements
pip_command('install -r requirements.txt')

# install automation package
pip_command('install -e ./tools')

# command modules have dependency on azure-cli-core so install this first
pip_command('install -e src/azure-cli-telemetry')
pip_command('install -e src/azure-cli-core')
py_command('-m automation.setup.install_modules')

# azure cli has dependencies on the above packages so install this one last
pip_command('install -e src/azure-cli')
pip_command('install -e src/azure-cli-testsdk')

print_support_message()
print('Finished dev setup.')

