#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path
from pkgutil import iter_modules
from unittest import TestLoader
from importlib import import_module
from json import dumps as json_dumps

import azure.cli  # pylint: disable=import-error
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest  # pylint: disable=import-error

RECORDS = []


def get_test_type(test_case):
    if isinstance(test_case, ScenarioTest):
        return 'Recording'
    elif isinstance(test_case, LiveScenarioTest):
        return 'Live'
    return 'Unit'


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
                for test in suite._tests:  # pylint: disable=protected-access
                    RECORDS.append({
                        'module': full_name,
                        'class': test.__class__.__name__,
                        'method': test._testMethodName,  # pylint: disable=protected-access
                        'type': get_test_type(test),
                        'path': '{}.{}.{}'.format(full_name, test.__class__.__name__, test._testMethodName)})  # pylint: disable=protected-access


search(azure.cli.__path__, 'azure.cli')

print(json_dumps(RECORDS))
