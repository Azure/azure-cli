# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.command_modules.resource.custom  import _merge_parameters

class TestCustom(unittest.TestCase):
    def test_resource_merge_parameters(self):
        tests = [
            {
                "parameter_list": [],
                "expected": None,
            },
            {
                "parameter_list": ['{"foo": "bar"}'],
                "expected": {"foo": "bar"},
            },
            {
                "parameter_list": ['{"foo": "bar"}', '{"baz": "blat"}'],
                "expected": {"foo": "bar", "baz": "blat"},
            },
            {
                "parameter_list": ['{"foo": "bar"}', '{"foo": "baz"}'],
                "expected": {"foo": "baz"},
            },
        ]

        for test in tests:
            output = _merge_parameters(test['parameter_list'])
            self.assertEqual(output, test['expected'])
