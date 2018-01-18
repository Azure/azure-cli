# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from automation.utilities.path import get_repo_root
from automation.tests.nose_helper import get_nose_runner
from automation.utilities.path import get_test_results_dir


def get_unittest_runner(tests):
    test_cases = list(tests)

    def _runner(module_paths):
        from subprocess import CalledProcessError
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


def collect_test():
    from importlib import import_module

    paths = import_module('azure.cli').__path__
    result = []
    collect_tests(paths, result, 'azure.cli')
    return result


def collect_tests(path, return_collection, prefix=''):
    from unittest import TestLoader
    from importlib import import_module
    from pkgutil import iter_modules

    loader = TestLoader()
    for _, name, is_pkg in iter_modules(path):
        full_name = '{}.{}'.format(prefix, name)
        module_path = os.path.join(path[0], name)

        if is_pkg:
            collect_tests([module_path], return_collection, full_name)

        if not is_pkg and name.startswith('test'):
            test_module = import_module(full_name)
            for suite in loader.loadTestsFromModule(test_module):
                for test in suite._tests:  # pylint: disable=protected-access
                    return_collection.append(
                        '{}.{}.{}'.format(full_name, test.__class__.__name__, test._testMethodName))  # pylint: disable=protected-access