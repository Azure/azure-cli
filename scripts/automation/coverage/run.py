# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import os.path
import sys
import itertools

from coverage import Coverage

import azure.cli.core.application as cli_application
from ..tests.nose_helper import get_nose_runner
from ..utilities.path import get_core_modules_paths_with_tests, \
    get_command_modules_paths_with_tests, get_repo_root, get_test_results_dir, make_dirs


# TODO: Fix track command logic in vcr_test_base.py.
def run_command_coverage(output_file='command_coverage.txt', output_dir=None):
    class CoverageContext(object):
        def __enter__(self):
            os.environ['AZURE_CLI_TEST_TRACK_COMMANDS'] = '1'
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            del os.environ['AZURE_CLI_TEST_TRACK_COMMANDS']

    if output_dir is None:
        from ..utilities.path import get_test_results_dir
        output_dir = get_test_results_dir(with_timestamp=True, prefix='cmd_cov')

    coverage_file = os.path.join(output_dir, output_file)
    if os.path.isfile(coverage_file):
        os.remove(coverage_file)

    config = cli_application.Configuration([])
    cli_application.APPLICATION = cli_application.Application(config)

    cmd_table = config.get_command_table()
    cmd_list = cmd_table.keys()
    cmd_set = set(cmd_list)

    print('Running tests...')
    with CoverageContext():
        test_result = run_all_tests()
        if not test_result:
            print("Tests failed")
            sys.exit(1)
        else:
            print('Tests passed.')

    commands_tested_with_params = [line.rstrip('\n') for line in open(coverage_file)]

    commands_tested = []
    for tested_command in commands_tested_with_params:
        for c in cmd_list:
            if tested_command.startswith(c):
                commands_tested.append(c)

    commands_tested_set = set(commands_tested)
    untested = list(cmd_set - commands_tested_set)
    print()
    print("Untested commands")
    print("=================")
    print('\n'.join(sorted(untested)))
    percentage_tested = (len(commands_tested_set) * 100.0 / len(cmd_set))
    print()
    print('Total commands {}, Tested commands {}, Untested commands {}'.format(
        len(cmd_set),
        len(commands_tested_set),
        len(cmd_set) - len(commands_tested_set)))
    print('COMMAND COVERAGE {0:.2f}%'.format(percentage_tested))


class CoverageContext(object):
    def __init__(self):
        self._cov = Coverage(cover_pylib=False)
        self._cov.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cov.stop()


def run_code_coverage():
    # create test results folder
    test_results_folder = get_test_results_dir(with_timestamp=True, prefix='cover')

    # get test runner
    run_nose = get_nose_runner(test_results_folder, xunit_report=False, exclude_integration=True,
                               code_coverage=True, parallel=False)

    # list test modules
    test_modules = itertools.chain(get_core_modules_paths_with_tests(),
                                   get_command_modules_paths_with_tests())

    # run code coverage on each project
    for index, (name, _, test_path) in enumerate(test_modules):
        with CoverageContext():
            run_nose(name, test_path)

        import shutil
        shutil.move('.coverage', os.path.join(test_results_folder, '.coverage.{}'.format(name)))


if __name__ == '__main__':
    run_code_coverage()
