#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from __future__ import print_function

import os.path
import os
import fnmatch
import multiprocessing

from subprocess import check_call

root = os.path.realpath(__file__)
root = os.path.abspath(root + '/../../')
modules_root = os.path.join(root, 'src', 'command_modules')

pylintrc = os.path.join(root, 'pylintrc')

all_modules = [os.path.join(modules_root, f, 'azure')
               for f in fnmatch.filter(os.listdir(modules_root), 'azure-cli-*')]

all_modules += [os.path.join(root, 'src', 'azure-cli-core', 'azure'),
                os.path.join(root, 'src', 'azure-cli', 'azure')]

arguments = '{} --rcfile={} -j {} -r n -d I0013'.format(
    ' '.join(all_modules),
    pylintrc,
    multiprocessing.cpu_count())

print('pylint arguments: ' + arguments)

command = ('python -m pylint ' + arguments).split()
check_call(command)

print('Pylint done')
