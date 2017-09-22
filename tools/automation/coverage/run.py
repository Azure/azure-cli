# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import collections
import os
import os.path
import sys

import automation.tests.nose_helper as automation_tests
import automation.utilities.path as automation_path
from azure.cli.testsdk.vcr_test_base import COMMAND_COVERAGE_CONTROL_ENV


# pylint: disable=too-few-public-methods
class CommandCoverageContext(object):
    FILE_NAME = 'command_coverage.txt'

    def __init__(self, data_file_path):
        self._data_file_path = os.path.join(data_file_path, self.FILE_NAME)

    def __enter__(self):
        os.environ[COMMAND_COVERAGE_CONTROL_ENV] = self._data_file_path
        automation_path.make_dirs(os.path.dirname(self.coverage_file_path))
        with open(self.coverage_file_path, 'w') as f:
            f.write('')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del os.environ[COMMAND_COVERAGE_CONTROL_ENV]

    @property
    def coverage_file_path(self):
        return self._data_file_path


def run_command_coverage(modules):
    test_result_dir = automation_path.get_test_results_dir(with_timestamp=True, prefix='cmdcov')
    data_file = os.path.join(test_result_dir, 'cmdcov.data')

    # run tests to generate executed command list
    run_nose = automation_tests.get_nose_runner(test_result_dir, parallel=False)

    with CommandCoverageContext(data_file) as context:
        for name, path in modules:
            run_nose(name, path)

        print('BEGIN: Full executed commands list')
        for line in open(context.coverage_file_path):
            sys.stdout.write(line)
        print('END: Full executed commands list')


# pylint: disable=too-few-public-methods
class CoverageContext(object):
    def __init__(self):
        from coverage import Coverage
        self._cov = Coverage(cover_pylib=False)
        self._cov.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cov.stop()


def run_code_coverage(modules):
    # create test results folder
    test_results_folder = automation_path.get_test_results_dir(with_timestamp=True, prefix='cover')

    # get test runner
    run_nose = automation_tests.get_nose_runner(
        test_results_folder, code_coverage=True, parallel=False)

    # run code coverage on each project
    for name, _, test_path in modules:
        with CoverageContext():
            run_nose(name, test_path)

        import shutil
        shutil.move('.coverage', os.path.join(test_results_folder, '.coverage.{}'.format(name)))


def coverage_command_rundown(log_file_path):
    import azure.cli.core.application

    config = azure.cli.core.application.Configuration([])
    azure.cli.core.application.APPLICATION = azure.cli.core.application.Application(config)
    existing_commands = set(config.get_command_table().keys())

    command_counter = collections.defaultdict(lambda: 0)
    for line in open(log_file_path, 'r'):
        command = line.split(' -', 1)[0].strip()
        if command:
            command_counter[command] += 1

    print('COUNT\tCOMMAND')
    for c in sorted(command_counter.keys()):
        print('{}\t{}'.format(command_counter[c], c))

    print('\nUncovered commands:')
    for c in sorted(existing_commands - set(command_counter.keys())):
        print(c)


def main():
    import argparse
    parser = argparse.ArgumentParser('Code coverage tools')
    parser.add_argument('--command-coverage', action='store_true', help='Run command coverage')
    parser.add_argument('--code-coverage', action='store_true', help='Run code coverage')
    parser.add_argument('--module', action='append', dest='modules',
                        help='The modules to run coverage. Multiple modules can be fed.')
    parser.add_argument('--command-rundown', action='store',
                        help='Analyze a command coverage test result.')
    args = parser.parse_args()

    selected_modules = automation_path.filter_user_selected_modules(args.modules)
    if not selected_modules:
        parser.print_help()
        sys.exit(1)

    if not args.code_coverage and not args.command_coverage and not args.command_rundown:
        parser.print_help()
        sys.exit(1)

    if args.command_rundown:
        coverage_command_rundown(args.command_rundown)
        sys.exit(0)

    if args.code_coverage:
        run_code_coverage(selected_modules)

    if args.command_coverage:
        run_command_coverage(selected_modules)

    sys.exit(0)


if __name__ == '__main__':
    main()
