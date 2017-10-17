#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function

import sys
import os
from subprocess import check_call, CalledProcessError

root_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))


def exec_command(command):
    try:
        print('Executing: ' + command)
        check_call(command.split(), cwd=root_dir)
        print()
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

print('Running dev setup...')
print('Root directory \'{}\'\n'.format(root_dir))

# install private whls if there are any
privates_dir = os.path.join(root_dir, 'privates')
if os.path.isdir(privates_dir) and os.listdir(privates_dir):
    whl_list = ' '.join([os.path.join(privates_dir, f) for f in os.listdir(privates_dir)])
    exec_command('pip install {}'.format(whl_list))

# install general requirements
exec_command('pip install -r requirements.txt')

# install automation package
exec_command('pip install -e ./tools')

# command modules have dependency on azure-cli-core so install this first
exec_command('pip install -e src/azure-cli-nspkg')
exec_command('pip install -e src/azure-cli-core')
exec_command('python -m automation.setup.install_modules')

# azure cli has dependencies on the above packages so install this one last
exec_command('pip install -e src/azure-cli')
exec_command('pip install -e src/azure-cli-testsdk')

# Ensure that the site package's azure/__init__.py has the old style namespace
# package declaration by installing the old namespace package
exec_command('pip install --force-reinstall azure-nspkg==1.0.0')
exec_command('pip install --force-reinstall azure-mgmt-nspkg==1.0.0')
print('Finished dev setup.')
