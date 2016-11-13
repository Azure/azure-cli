#!/usr/bin/env python

from __future__ import print_function

import os.path
import os
import fnmatch
import multiprocessing

from datetime import datetime
from pylint import epylint as lint

root = os.path.realpath(__file__)
root = os.path.abspath(root + '/../../')

pylintrc = os.path.join(root, 'pylintrc')

def get_all_command_modules():
    # The prefix for the command module folders
    modules_root = os.path.join(root, 'src', 'command_modules')
    return [os.path.join(modules_root, f, 'azure')
            for f in fnmatch.filter(os.listdir(modules_root), 'azure-cli-*')]

all_modules = get_all_command_modules() + \
    [os.path.join(root, 'src', 'azure-cli-core', 'azure'),
     os.path.join(root, 'src', 'azure-cli', 'azure')]

options = '{} --rcfile={} -j {} -d I0013'.format(
    ' '.join(all_modules),
    pylintrc,
    multiprocessing.cpu_count())

print('pylint options: ' + options)
lint.py_run(options)
