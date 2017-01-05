# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
import multiprocessing
from subprocess import check_call
from itertools import chain
from ..utilities.path import get_command_modules_paths, get_core_modules_paths, get_repo_root


def run_pylint():
    modules_list = ' '.join(os.path.join(path, 'azure') for _, path in
                            chain(get_command_modules_paths(), get_core_modules_paths()))
    arguments = '{} --rcfile={} -j {} -r n -d I0013'.format(
        modules_list,
        os.path.join(get_repo_root(), 'pylintrc'),
        multiprocessing.cpu_count())

    print('pylint arguments: ' + arguments)

    check_call(('python -m pylint ' + arguments).split())

    print('Pylint done')

if __name__ == '__main__':
    run_pylint()
