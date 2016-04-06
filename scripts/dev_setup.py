#!/usr/bin/python
from __future__ import print_function
import sys
from subprocess import check_call, CalledProcessError

def exec_command(command):
    try:
        print('Executing: ' + command)
        check_call(command, shell=True)
    except CalledProcessError as err:
        print(err, file=sys.stderr)
        sys.exit(1)

print('Running dev setup...')
exec_command('pip install -r requirements.txt')
exec_command('pip install -e .')
exec_command('python scripts/command_modules/install.py')
print('Finished dev setup.')
