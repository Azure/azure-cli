# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import sys

from automation.utilities.path import filter_user_selected_modules
from automation.tests.nose_helper import get_nose_runner
from automation.utilities.display import print_records
from automation.utilities.path import get_test_results_dir


def run_tests(modules, parallel):
    print('\n\nRun automation')
    print('Modules: {}'.format(', '.join(name for name, _, _ in modules)))

    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='tests')

    # get test runner
    run_nose = get_nose_runner(test_results_folder, xunit_report=True, exclude_integration=True,
                               parallel=parallel)

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
                            'azure-cli, azure-cli-core and azure-cli-nspkg')
    parse.add_argument('--non-parallel', action='store_true',
                       help='Not to run the tests in parallel.')
    args = parse.parse_args()

    selected_modules = filter_user_selected_modules(args.modules)
    if not selected_modules:
        parse.print_help()
        sys.exit(1)

    retval = run_tests(selected_modules, not args.non_parallel)

    sys.exit(0 if retval else 1)
