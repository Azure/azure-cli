#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=import-error, protected-access
# Justification:
#   * The azure.cli packages are not visible while the script is scaned but they are guaranteed
#     existence on the droid image
#   * The test method names and other properties are protected for unit test framework.

import os.path
from pkgutil import iter_modules
from unittest import TestLoader
from importlib import import_module
from json import dumps as json_dumps

import azure.cli
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest

RECORDS = []


def get_test_type(test_case):
    if isinstance(test_case, ScenarioTest):
        return 'Recording'
    elif isinstance(test_case, LiveScenarioTest):
        return 'Live'
    return 'Unit'


def find_recording_file(test_path):
    module_path, _, test_method = test_path.rsplit('.', 2)
    test_folder = os.path.dirname(import_module(module_path).__file__)
    recording_file = os.path.join(test_folder, 'recordings', test_method + '.yaml')
    return recording_file if os.path.exists(recording_file) else None


def search(path, prefix=''):
    loader = TestLoader()
    for _, name, is_pkg in iter_modules(path):
        full_name = '{}.{}'.format(prefix, name)
        module_path = os.path.join(path[0], name)

        if is_pkg:
            search([module_path], full_name)

        if not is_pkg and name.startswith('test'):
            test_module = import_module(full_name)
            for suite in loader.loadTestsFromModule(test_module):
                for test in suite._tests:
                    path = '{}.{}.{}'.format(full_name, test.__class__.__name__, test._testMethodName)
                    rec = {
                        'ver': '1.0',
                        'execution': {
                            'command': 'python -m unittest {}'.format(path),
                            'recording': find_recording_file(path)
                        },
                        'classifier': {
                            'identifier': path,
                            'type': get_test_type(test),
                        }
                    }
                    RECORDS.append(rec)


search(azure.cli.__path__, 'azure.cli')

print(json_dumps(RECORDS))
