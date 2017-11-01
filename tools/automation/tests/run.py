# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import os
import sys

from automation.utilities.path import filter_user_selected_modules_with_tests, get_repo_root
from automation.tests.nose_helper import get_nose_runner
from automation.utilities.path import get_test_results_dir


def get_unittest_runner(tests):
    test_cases = list(tests)

    def _runner(module_paths):
        from subprocess import check_call, CalledProcessError
        if len(module_paths) > 1:
            print('When --test is given, no more than 1 module can be selected.')
            return False

        module_path = module_paths[0][len(os.path.join(get_repo_root(), 'src' + os.sep)):]
        if module_path.startswith('command_modules'):
            module_path = module_path.split(os.sep, 2)[-1].replace(os.sep, '.')
        else:
            module_path = module_path.split(os.sep, 1)[-1].replace(os.sep, '.')

        try:
            import unittest
            suite = unittest.TestLoader().loadTestsFromNames(['{}.{}'.format(module_path, t) for t in test_cases])
            runner = unittest.TextTestRunner()
            result = runner.run(suite)

            return not result.failures
        except CalledProcessError:
            return False

    return _runner


def run_tests(modules, parallel, run_live, tests):
    print('Run automation')
    print('Modules: {}'.format(', '.join(name for name, _, _ in modules)))

    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='tests')

    # set environment variable
    if run_live:
        os.environ['AZURE_TEST_RUN_LIVE'] = 'True'

    if not tests:
        # the --test is not given, use nosetests to run entire module
        print('Drive test by nosetests')
        runner = get_nose_runner(test_results_folder, parallel=parallel, process_timeout=3600 if run_live else 600)
    else:
        # the --test is given, use unittest to run single test
        print('Drive test by unittest')
        runner = get_unittest_runner(tests)

    # run tests
    result = runner([p for _, _, p in modules])

    return result


def main():
    parse = argparse.ArgumentParser('Test tools')
    parse.add_argument('--module', dest='modules', nargs='+',
                       help='The modules of which the test to be run. Accept short names, except azure-cli, '
                            'azure-cli-core and azure-cli-nspkg. The modules list can also be set through environment '
                            'variable AZURE_CLI_TEST_MODULES. The value should be a string of space separated module '
                            'names. The environment variable will be overwritten by command line parameters.')
    parse.add_argument('--parallel', action='store_true',
                       help='Run the tests in parallel. This will affect the test output file.')
    parse.add_argument('--live', action='store_true', help='Run all the tests live.')
    parse.add_argument('--test', dest='tests', action='append',
                       help='The specific test to run in the given module. The string can represent a test class or a '
                            'test class and a test method name. Multiple tests can be given, but they should all '
                            'belong to one command modules.')
    parse.add_argument('--ci', dest='ci', action='store_true', help='Run the tests in CI mode.')
    args = parse.parse_args()

    if args.ci:
        print('Run tests in CI mode')
        selected_modules = [('CI mode', 'azure.cli', 'azure.cli')]
    else:
        if not args.modules and os.environ.get('AZURE_CLI_TEST_MODULES', None):
            print('Test modules list is parsed from environment variable AZURE_CLI_TEST_MODULES.')
            args.modules = [m.strip() for m in os.environ.get('AZURE_CLI_TEST_MODULES').split(',')]

        selected_modules = filter_user_selected_modules_with_tests(args.modules)
        if not selected_modules:
            parse.print_help()
            sys.exit(1)

    success = run_tests(selected_modules, parallel=args.parallel, run_live=args.live, tests=args.tests)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
