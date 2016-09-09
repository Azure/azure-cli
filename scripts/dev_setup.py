#!/usr/bin/python

#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function
import sys
import os
from subprocess import check_call, CalledProcessError

root_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))

def exec_command(command):
    try:
        print('Executing: ' + command)
        check_call(command.split(), cwd=root_dir)
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

print('Running dev setup...')
print('Root directory \'{}\''.format(root_dir))
exec_command('pip install -r requirements.txt')
# command modules have dependency on azure-cli-core so install this first
exec_command('pip install -e src/azure-cli-core')
exec_command('python scripts/command_modules/install.py')
# azure cli has dependencies on the above packages so install this one last
exec_command('pip install -e src/azure-cli')
print('Finished dev setup.')
