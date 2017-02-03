# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import os
import sys

from automation.utilities.path import filter_user_selected_modules_with_tests
from automation.tests.nose_helper import get_nose_runner
from automation.utilities.display import print_records
from automation.utilities.path import get_test_results_dir


def run_tests(modules, parallel, run_live):
    print('\n\nRun automation')
    print('Modules: {}'.format(', '.join(name for name, _, _ in modules)))

    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='tests')

    # get test runner
    run_nose = get_nose_runner(test_results_folder, xunit_report=True, exclude_integration=True,
                               parallel=parallel)

    # set environment variable
    if run_live:
        os.environ['AZURE_CLI_TEST_RUN_LIVE'] = 'True'

    # run tests
    passed = True
    module_results = []
    for name, _, test_path in modules:
        result, start, end, _ = run_nose(name, test_path)
        passed &= result
        record = (name, start.strftime('%H:%M:%D'), str((end - start).total_seconds()),
                  'Pass' if result else 'Fail')

        module_results.append(record)

    print_records(module_results, title='test results')

    return passed


if __name__ == '__main__':
    parse = argparse.ArgumentParser('Test tools')
    parse.add_argument('--module', dest='modules', action='append',
                       help='The modules of which the test to be run. Accept short names, except '
                            'azure-cli, azure-cli-core and azure-cli-nspkg. The modules list can '
                            'also be set through environment variable AZURE_CLI_TEST_MODULES. The '
                            'value should be a string of comma separated module names. The '
                            'environment variable will be overwritten by command line parameters.')
    parse.add_argument('--non-parallel', action='store_true',
                       help='Not to run the tests in parallel.')
    parse.add_argument('--live', action='store_true', help='Run all the tests live.')
    args = parse.parse_args()

    if not args.modules and os.environ.get('AZURE_CLI_TEST_MODULES', None):
        print('Test modules list is parsed from environment variable AZURE_CLI_TEST_MODULES.')
        args.modules = [m.strip() for m in os.environ.get('AZURE_CLI_TEST_MODULES').split(',')]

    selected_modules = filter_user_selected_modules_with_tests(args.modules)
    if not selected_modules:
        parse.print_help()
        sys.exit(1)

    retval = run_tests(selected_modules, not args.non_parallel, args.live)

    sys.exit(0 if retval else 1)
