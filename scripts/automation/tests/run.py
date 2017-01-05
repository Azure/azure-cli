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


def run_all():
    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='tests')

    # get test runner
    run_nose = get_nose_runner(test_results_folder, xunit_report=True, exclude_integration=True)

    # get test list
    modules_to_test = itertools.chain(
        get_core_modules_paths_with_tests(),
        get_command_modules_paths_with_tests())

    # run tests
    passed = True
    module_results = []
    for name, _, test_path in modules_to_test:
        result, start, end, log_file = run_nose(name, test_path)
        passed &= result
        record = (name, start.strftime('%H:%M:%D'), str((end - start).total_seconds()),
                  'Pass' if result else 'Fail')

        module_results.append(record)

    print_records(module_results, title='test results')

    return passed

if __name__ == '__main__':
    sys.exit(0 if run_all() else 1)
