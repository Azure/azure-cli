# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import itertools
import sys

from .nose_helper import get_nose_runner
from ..utilities.display import print_records
from ..utilities.path import get_command_modules_paths_with_tests, \
                             get_core_modules_paths_with_tests,\
                             get_test_results_dir


def run_tests(modules, parallel):
    print('\n\nRun automation')
    print('Modules: {}'.format(', '.join(name for name, _ in modules)))

    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='tests')

    # get test runner
    run_nose = get_nose_runner(test_results_folder, xunit_report=True, exclude_integration=True,
                               parallel=parallel)

    # run tests
    passed = True
    module_results = []
    for name, test_path in modules:
        result, start, end, log_file = run_nose(name, test_path)
        passed &= result
        record = (name, start.strftime('%H:%M:%D'), str((end - start).total_seconds()),
                  'Pass' if result else 'Fail')

        module_results.append(record)

    print_records(module_results, title='test results')

    return passed

if __name__ == '__main__':
    import argparse
    from itertools import chain
    from automation.utilities.path import (get_command_modules_paths_with_tests,
                                           get_core_modules_paths_with_tests)

    parse = argparse.ArgumentParser('Test tools')
    parse.add_argument('--module', dest='modules', action='append',
                       help='The modules of which the test to be run. Accept short names, except '
                            'azure-cli, azure-cli-core and azure-cli-nspkg')
    parse.add_argument('--non-parallel', action='store_true',
                       help='Not to run the tests in parallel.')
    args = parse.parse_args()

    existing_modules = list(chain(get_core_modules_paths_with_tests(),
                                  get_command_modules_paths_with_tests()))

    if args.modules:
        selected_modules = set(args.modules)
        extra = selected_modules - set([name for name, _, _ in existing_modules])
        if any(extra):
            print('ERROR: These modules do not exist: {}.'.format(', '.join(extra)))
            sys.exit(1)

        selected_modules = list((name, path) for name, _, path in existing_modules
                                if name in selected_modules)
    else:
        selected_modules = list((name, path) for name, _, path in existing_modules)

    retval = run_tests(selected_modules, not args.non_parallel)

    sys.exit(0 if retval else 1)
