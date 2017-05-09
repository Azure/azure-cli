# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import multiprocessing
import os.path
import sys
from subprocess import call

import automation.utilities.path as automation_path


def run_pylint(modules):
    print('\n\nRun pylint')
    print(
    'Modules: {}'.format(', '.join([name for name, _ in modules if not name.endswith('-nspkg')])))

    modules_list = ' '.join(
        [os.path.join(path, 'azure') for name, path in modules if not name.endswith('-nspkg')])
    arguments = '{} --rcfile={} -j {} -r n -d I0013'.format(
        modules_list,
        os.path.join(automation_path.get_repo_root(), 'pylintrc'),
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

    command = 'flake8 --statistics --exclude=azure_bdist_wheel.py --append-config={} {}'.format(
        os.path.join(automation_path.get_repo_root(), '.flake8'),
        ' '.join(path for _, path in modules))

    return_code = call(command.split())
    if return_code:
        print('Flake8 failed')
    else:
        print('Flake8 passed')

    return return_code


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Code style tools')
    parser.add_argument('--ci', action='store_true', help='Run in CI mode')
    parser.add_argument('--pep8', dest='suites', action='append_const', const='pep8',
                        help='Run flake8 to check PEP8')
    parser.add_argument('--pylint', dest='suites', action='append_const', const='pylint',
                        help='Run pylint')
    parser.add_argument('--module', dest='modules', action='append',
                        help='The modules on which the style check should run. Accept short names, '
                             'except azure-cli, azure-cli-core and azure-cli-nspkg')
    args = parser.parse_args()

    if args.ci:
        # When the command is run in CI mode all the other parameters are ignored
        selected_modules = automation_path.filter_user_selected_modules(None)

        # Run pylint on all modules
        return_code_sum = run_pylint(selected_modules)

        # Run flake8 on modules
        pep8_ready_modules = automation_path.filter_blacklisted_modules('network')

        return_code_sum += run_pep8(pep8_ready_modules)

        sys.exit(return_code_sum)

    selected_modules = automation_path.filter_user_selected_modules(args.modules)
    if not selected_modules:
        parser.print_help()
        sys.exit(1)

    if not args.suites or not any(args.suites):
        return_code_sum = run_pylint(selected_modules)
    else:
        return_code_sum = 0
        if 'pep8' in args.suites:
            return_code_sum += run_pep8(selected_modules)

        if 'pylint' in args.suites:
            return_code_sum += run_pylint(selected_modules)

    sys.exit(return_code_sum)
