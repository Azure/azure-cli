# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import multiprocessing
import os.path
import sys
from itertools import chain
from subprocess import check_call, call

from ..utilities.path import get_command_modules_paths, get_core_modules_paths, get_repo_root


def run_pylint(modules):
    print('\n\nRun pylint')
    print('Modules: {}'.format(', '.join(name for name, _ in modules)))

    modules_list = ' '.join(os.path.join(path, 'azure') for _, path in modules)
    arguments = '{} --rcfile={} -j {} -r n -d I0013'.format(
        modules_list,
        os.path.join(get_repo_root(), 'pylintrc'),
        multiprocessing.cpu_count())

    return_code = call(('python -m pylint ' + arguments).split())

    if return_code:
        print('Pylint failed')
    else:
        print('Pylint passed')

    return return_code


def run_pep8(modules):
    print('\n\nRun flake8 for PEP8 compliance')
    print('Modules: {}'.format(', '.join(name for name, _ in modules)))

    command = 'flake8 --statistics --append-config={} {}'.format(
        os.path.join(get_repo_root(), '.flake8'),
        ' '.join(path for _, path in modules))

    return_code = call(command)
    if return_code:
        print('Flake8 failed')
    else:
        print('Flake8 passed')

    return return_code


if __name__ == '__main__':
    import argparse

    parse = argparse.ArgumentParser('Code styple tools')
    parse.add_argument('--pep8', dest='suites', action='append_const', const='pep8',
                       help='Run flake8 to check PEP8')
    parse.add_argument('--pylint', dest='suites', action='append_const', const='pylint',
                       help='Run pylint')
    parse.add_argument('--module', dest='modules', action='append',
                       help='The modules on which the style check should run. Accept short names. '
                            'Use "main" for the azure-cli package and "core" for the '
                            'azure-cli-core')
    args = parse.parse_args()

    print(args.suites)

    existing_modules = list(chain(get_command_modules_paths(), get_core_modules_paths()))

    if args.modules:
        selected_modules = set(args.modules)
        extra = selected_modules - set([name for name, _ in existing_modules])
        if any(extra):
            print('ERROR: These modules do not exist: {}.'.format(', '.join(extra)))
            sys.exit(1)

        selected_modules = list((name, path) for name, path in existing_modules
                                if name in selected_modules)
    else:
        selected_modules = existing_modules

    if not args.suites or not any(args.suites):
        run_pylint(selected_modules)
    else:
        return_code_sum = 0
        if 'pep8' in args.suites:
            return_code_sum += run_pep8(selected_modules)

        if 'pylint' in args.suites:
            return_code_sum += run_pylint(selected_modules)

    sys.exit(return_code_sum)
