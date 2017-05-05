# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.command_modules.resource.custom import (
    _merge_parameters,
    _get_missing_parameters
)


class TestCustom(unittest.TestCase):
    def test_resource_missing_parameters(self):
        template = {
            "parameters": {
                "def": {
                    "type": "string",
                    "defaultValue": "default"
                },
                "present": {
                    "type": "string",
                },
                "missing": {
                    "type": "string",
                }
            }
        }
        parameters = {
            "present": {
                "value": "foo"
            }
        }
        out_params = _get_missing_parameters(parameters, template, lambda x: {"missing": "baz"})

        expected = {
            "present": {
                "value": "foo"
            },
            "missing": {
                "value": "baz"
            }
        }

        self.assertDictEqual(out_params, expected)


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

if __name__ == '__main__':
    unittest.main()
