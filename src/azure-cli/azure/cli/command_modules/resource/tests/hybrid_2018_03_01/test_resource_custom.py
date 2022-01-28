# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from urllib.request import pathname2url
from urllib.parse import urljoin

from unittest import mock

from azure.cli.core.util import CLIError, get_file_json, shell_safe_json_parse
from azure.cli.command_modules.resource.custom import \
    (_get_missing_parameters, _extract_lock_params, _process_parameters, _find_missing_parameters,
     _prompt_for_parameters, _load_file_string_or_uri)


def _simulate_no_tty():
    from knack.prompting import NoTTYException
    raise NoTTYException


@mock.patch('knack.prompting.verify_is_a_tty', _simulate_no_tty)
class TestCustom(unittest.TestCase):
    def test_file_string_or_uri(self):
        data = '{ "some": "data here"}'
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data.encode('utf-8'))
            tmp.close()

            output = _load_file_string_or_uri(tmp.name, 'test')
            self.assertEqual(get_file_json(tmp.name), output)

            uri = urljoin('file:', pathname2url(tmp.name))
            output = _load_file_string_or_uri(uri, 'test')
            self.assertEqual(get_file_json(tmp.name), output)

            os.unlink(tmp.name)

        output = _load_file_string_or_uri(data, 'test')
        self.assertEqual(shell_safe_json_parse(data), output)

        self.assertEqual(None, _load_file_string_or_uri(None, 'test', required=False))
        self.assertRaises(CLIError, _load_file_string_or_uri, None, 'test')

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

    def test_deployment_parameters(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)
        template_param_defs = template.get('parameters', {})

        # test different ways of passing in parameters
        tests = [
            {  # empty parameters works
                "parameter_list": [],
                "expected": {},
            },
            {  # loading from file
                "parameter_list": [[parameters_path]],
                "expected": {"stringParam": {"value": "foo"}, "intParam": {"value": 10}, "madeupParam": {"value": "bar"}},
            },
            {  # KEY=VALUE syntax with extra equal sign
                "parameter_list": [['stringParam=foo=bar']],
                "expected": {"stringParam": {"value": "foo=bar"}},
            },
            {  # raw JSON (same as @file)
                "parameter_list": [['{\"stringParam\": {\"value\": \"foo\"}}']],
                "expected": {"stringParam": {"value": "foo"}},
            },
            {  # multiple KEY=VALUE
                "parameter_list": [['stringParam=foo', 'intParam=3']],
                "expected": {"stringParam": {"value": "foo"}, "intParam": {"value": 3}},
            },
            {  # KEY=VALUE where last in wins
                "parameter_list": [['stringParam=foo', 'stringParam=bar']],
                "expected": {"stringParam": {"value": "bar"}},
            },
            {  # file loading overriden by KEY=VALUE
                "parameter_list": [[parameters_path], ['stringParam=bar']],
                "expected": {"stringParam": {"value": "bar"}, "intParam": {"value": 10}, "madeupParam": {"value": "bar"}},
            }
        ]

        for test in tests:
            parameter_list = test['parameter_list']
            result_parameters = _process_parameters(template_param_defs, parameter_list)
            self.assertEqual(result_parameters, test['expected'])

    def test_deployment_missing_values(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')
        parameters_with_reference_path = os.path.join(curr_dir, 'param-validation-ref-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)
        template_param_defs = template.get('parameters', {})

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template_param_defs, parameter_list)
        missing_parameters = _find_missing_parameters(result_parameters, template)

        # ensure that parameters with default values are not considered missing
        params_with_defaults = [x for x in template_param_defs if 'defaultValue' in template_param_defs[x]]
        for item in params_with_defaults:
            self.assertTrue(item not in missing_parameters)

        # ensure that a parameter that specifies a reference does not prompt
        self.assertTrue('secretReference' not in missing_parameters)
        self.assertTrue('secretReference' in result_parameters)

    def test_deployment_prompt_file_order(self):
        # check that params are prompted for in file order when the file is loaded with preserve_order=True
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')
        parameters_with_reference_path = os.path.join(curr_dir, 'param-validation-ref-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)
        template_param_defs = template.get('parameters', {})

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template_param_defs, parameter_list)
        missing_parameters = _find_missing_parameters(result_parameters, template)

        param_file_order = ["[u'secureParam', u'boolParam', u'enumParam', u'arrayParam', u'objectParam']",
                            "['secureParam', 'boolParam', 'enumParam', 'arrayParam', 'objectParam']"]
        results = _prompt_for_parameters(missing_parameters, fail_on_no_tty=False)
        self.assertTrue(str(list(results.keys())) in param_file_order)

    def test_deployment_prompt_alphabetical_order(self):
        # check that params are prompted for in alphabetical order when the file is loaded with preserve_order=False
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')
        parameters_with_reference_path = os.path.join(curr_dir, 'param-validation-ref-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=False)
        template_param_defs = template.get('parameters', {})

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template_param_defs, parameter_list)
        missing_parameters = _find_missing_parameters(result_parameters, template)

        param_alpha_order = ["[u'arrayParam', u'boolParam', u'enumParam', u'objectParam', u'secureParam']",
                             "['arrayParam', 'boolParam', 'enumParam', 'objectParam', 'secureParam']"]
        results = _prompt_for_parameters(dict(missing_parameters), fail_on_no_tty=False)
        self.assertTrue(str(list(results.keys())) in param_alpha_order)


if __name__ == '__main__':
    unittest.main()
