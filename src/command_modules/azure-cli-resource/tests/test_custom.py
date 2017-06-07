# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from azure.cli.command_modules.resource.custom import (
    _merge_parameters,
    _get_missing_parameters,
    _extract_lock_params
)


class TestCustom(unittest.TestCase):
    def test_extract_parameters(self):
        tests = [
            {
                'input': {},
                'expected': {},
                'name': 'empty'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                },
                'expected': {
                    'resource_group_name': 'foo',
                },
                'name': 'resource_group'
            },
            {
                'input': {
                    'resource_type': 'foo',
                },
                'expected': {},
                'name': 'missing resource_group'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                    'resource_type': 'bar',
                },
                'expected': {
                    'resource_group_name': 'foo',
                },
                'name': 'missing resource_name'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'bar',
                },
                'expected': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'bar',
                },
                'name': 'missing resource_name'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'bar/blah',
                },
                'expected': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'blah',
                    'resource_provider_namespace': 'bar'
                },
                'name': 'slashes'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'blah',
                    'resource_provider_namespace': 'bar'
                },
                'expected': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'blah',
                    'resource_provider_namespace': 'bar'
                },
                'name': 'separate'
            },
            {
                'input': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'blah/bug',
                    'resource_provider_namespace': 'bar'
                },
                'expected': {
                    'resource_group_name': 'foo',
                    'resource_name': 'baz',
                    'resource_type': 'blah/bug',
                    'resource_provider_namespace': 'bar'
                },
                'name': 'separate'
            }

        ]

        for test in tests:
            resource_group_name = test['input'].get('resource_group_name', None)
            resource_type = test['input'].get('resource_type', None)
            resource_name = test['input'].get('resource_name', None)
            resource_provider_namespace = test['input'].get('resource_provider_namespace', None)

            output = _extract_lock_params(resource_group_name, resource_provider_namespace,
                                          resource_type, resource_name)

            resource_group_name = test['expected'].get('resource_group_name', None)
            resource_type = test['expected'].get('resource_type', None)
            resource_name = test['expected'].get('resource_name', None)
            resource_provider_namespace = test['expected'].get('resource_provider_namespace', None)

            self.assertEqual(resource_group_name, output[0], test['name'])
            self.assertEqual(resource_name, output[1], test['name'])
            self.assertEqual(resource_provider_namespace, output[2], test['name'])
            self.assertEqual(resource_type, output[3], test['name'])

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
