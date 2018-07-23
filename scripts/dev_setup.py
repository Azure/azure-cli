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


def py_command(command):
    try:
        print('Executing: python ' + command)
        check_call([sys.executable] + command.split(), cwd=root_dir)
        print()
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

def pip_command(command):
    py_command('-m pip ' + command)

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
pip_command('install -e src/azure-cli-nspkg')
pip_command('install -e src/azure-cli-telemetry')
pip_command('install -e src/azure-cli-core')
py_command('-m automation.setup.install_modules')

# azure cli has dependencies on the above packages so install this one last
pip_command('install -e src/azure-cli')
pip_command('install -e src/azure-cli-testsdk')

# Ensure that the site package's azure/__init__.py has the old style namespace
# package declaration by installing the old namespace package
pip_command('install --force-reinstall azure-nspkg==1.0.0')
pip_command('install --force-reinstall azure-mgmt-nspkg==1.0.0')
print('Finished dev setup.')
