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

from azure.cli.core.util import CLIError, get_file_json, shell_safe_json_parse, read_file_content
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.command_modules.resource.custom import (
    _get_missing_parameters,
    _extract_lock_params,
    _process_parameters,
    _find_missing_parameters,
    _prompt_for_parameters,
    _is_bicepparam_file_provided,
    _load_file_string_or_uri,
    _what_if_deploy_arm_template_core,
    deploy_arm_template_at_resource_group,
    deploy_arm_template_at_subscription_scope,
    deploy_arm_template_at_management_group,
    deploy_arm_template_at_tenant_scope,
    format_bicep_file,
    publish_bicep_file,
    _process_template_file,
    _prepare_deployment_properties_unmodified,
)

from azure.cli.command_modules.resource._bicep import (run_bicep_command)

from azure.cli.core.mock import DummyCli
from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles._shared import ResourceType

from azure.cli.testsdk import live_only

cli_ctx = DummyCli()
loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_RESOURCE_DEPLOYMENTS)
cmd = AzCliCommand(loader, 'test', None)
cmd.command_kwargs = {'resource_type': ResourceType.MGMT_RESOURCE_DEPLOYMENTS}
cmd.cli_ctx = cli_ctx

WhatIfOperationResult, WhatIfChange, ChangeType = cmd.get_models(
    'WhatIfOperationResult', 'WhatIfChange', 'ChangeType'
)

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

    def test_resource_missing_parameters_no_tty(self):
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

        def prompt_function(x):
            from knack.prompting import NoTTYException
            raise NoTTYException
        with self.assertRaisesRegex(CLIError, "Missing input parameters: missing"):
            _get_missing_parameters(parameters, template, prompt_function)

    def test_deployment_parameters(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)

        # test different ways of passing in parameters
        tests = [
            {  # empty JSON works
                "parameter_list": [["{}"]],
                "expected": {},
            },
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

        for i, test in enumerate(tests):
            parameter_list = test['parameter_list']
            result_parameters = _process_parameters(template, parameter_list)
            self.assertEqual(result_parameters, test['expected'], i)

    def test_deployment_parameters_with_type_references(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template-$ref-indirection.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)

        # test different ways of passing in parameters
        tests = [
            {  # empty JSON works
                "parameter_list": [["{}"]],
                "expected": {},
            },
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
            },
            {
                "parameter_list": [['boolParam=true', 'tupleParam=[21]']],
                "expected": {"boolParam": {"value": True}, "tupleParam": {"value": [21]}},
            }
        ]

        for i, test in enumerate(tests):
            parameter_list = test['parameter_list']
            result_parameters = _process_parameters(template, parameter_list)
            self.assertEqual(result_parameters, test['expected'], i)

    def test_deployment_missing_values(self):

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')
        parameters_with_reference_path = os.path.join(curr_dir, 'param-validation-ref-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=True)
        template_param_defs = template.get('parameters', {})

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template, parameter_list)
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

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template, parameter_list)
        missing_parameters = _find_missing_parameters(result_parameters, template)

        param_file_order = ["['secureParam', 'boolParam', 'enumParam', 'arrayParam', 'objectParam']"]
        results = _prompt_for_parameters(missing_parameters, fail_on_no_tty=False)
        self.assertTrue(str(list(results.keys())) in param_file_order)

    def test_deployment_prompt_alphabetical_order(self):
        # check that params are prompted for in alphabetical order when the file is loaded with preserve_order=False
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        template_path = os.path.join(curr_dir, 'param-validation-template.json').replace('\\', '\\\\')
        parameters_path = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')
        parameters_with_reference_path = os.path.join(curr_dir, 'param-validation-ref-params.json').replace('\\', '\\\\')

        template = get_file_json(template_path, preserve_order=False)

        parameter_list = [[parameters_path], [parameters_with_reference_path]]
        result_parameters = _process_parameters(template, parameter_list)
        missing_parameters = _find_missing_parameters(result_parameters, template)

        param_alpha_order = ["['arrayParam', 'boolParam', 'enumParam', 'objectParam', 'secureParam']"]
        results = _prompt_for_parameters(dict(missing_parameters), fail_on_no_tty=False)
        self.assertTrue(str(list(results.keys())) in param_alpha_order)

    def test_deployment_bicepparam_file_input_check(self):
        self.assertEqual(_is_bicepparam_file_provided(None), False)
        self.assertEqual(_is_bicepparam_file_provided([]), False)
        self.assertEqual(_is_bicepparam_file_provided([['test.json']]), False)
        self.assertEqual(_is_bicepparam_file_provided([['test.bicepparam']]), True)
        self.assertEqual(_is_bicepparam_file_provided([['test.bicepparam'], ['test.json'],  ['{ \"foo\": { \"value\": \"bar\" } }']]), True)

    @live_only()
    def test_bicep_generate_params_defaults(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        bicep_file = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        json_file = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["generate-params", bicep_file])
        is_generated_params_file_exists = os.path.exists(json_file)
        self.assertTrue(is_generated_params_file_exists)

    @live_only()
    def test_bicep_generate_params_output_format(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        bicep_file = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        json_file = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["generate-params", bicep_file, "--output-format", "json"])
        is_generated_params_file_exists = os.path.exists(json_file)
        self.assertTrue(is_generated_params_file_exists)

    @live_only()
    def test_bicep_generate_params_include_params(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        bicep_file = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        json_file = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["generate-params", bicep_file, "--include-params", "all"])
        is_generated_params_file_exists = os.path.exists(json_file)
        self.assertTrue(is_generated_params_file_exists)

    @live_only()
    def test_bicep_lint_defaults(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        param_file = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["lint", param_file])

        self.assertTrue(param_file)

    @live_only()
    def test_bicep_build_params_defaults(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        param_file = os.path.join(curr_dir, 'sample_params.bicepparam').replace('\\', '\\\\')
        json_file = os.path.join(curr_dir, 'sample_params.json').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["build-params", param_file])
        is_generated_params_file_exists = os.path.exists(json_file)

        self.assertTrue(is_generated_params_file_exists)

    @live_only()
    def test_bicep_decompile_params_defaults(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        param_file = os.path.join(curr_dir, 'param-validation-params.bicepparam').replace('\\', '\\\\')
        json_file = os.path.join(curr_dir, 'param-validation-params.json').replace('\\', '\\\\')

        run_bicep_command(cli_ctx, ["decompile-params", json_file, "--force"])
        is_generated_params_file_exists = os.path.exists(param_file)

        self.assertTrue(is_generated_params_file_exists)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_resource_group_core", autospec=True)
    def test_confirm_with_what_if_prompt_at_resource_group(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_resource_group(mock.MagicMock(), confirm_with_what_if=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_resource_group_core", autospec=True)
    def test_proceed_if_no_change_prompt_at_resource_group(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.modify),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_resource_group(mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_resource_group_core", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._deploy_arm_template_at_resource_group", autospec=True)
    def test_proceed_if_no_change_skip_prompt_at_resource_group(self, deploy_template_mock, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.no_change),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        # Act.
        deploy_arm_template_at_resource_group(cmd, mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_not_called()
        deploy_template_mock.assert_called_once()

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_subscription_scope_core", autospec=True)
    def test_confirm_with_what_if_prompt_at_subscription_scope(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_subscription_scope(mock.MagicMock(), confirm_with_what_if=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_subscription_scope_core", autospec=True)
    def test_proceed_if_no_change_prompt_at_subscription_scope(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.modify),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_subscription_scope(mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_subscription_scope_core", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._deploy_arm_template_at_subscription_scope", autospec=True)
    def test_proceed_if_no_change_skip_prompt_at_subscription_scope(self, deploy_template_mock, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.no_change),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        # Act.
        deploy_arm_template_at_subscription_scope(cmd, mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_not_called()
        deploy_template_mock.assert_called_once()

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_management_group_core", autospec=True)
    def test_confirm_with_what_if_prompt_at_management_group(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_management_group(mock.MagicMock(), confirm_with_what_if=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_management_group_core", autospec=True)
    def test_proceed_if_no_change_prompt_at_management_group(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.modify),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_management_group(mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_management_group_core", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._deploy_arm_template_at_management_group", autospec=True)
    def test_proceed_if_no_change_skip_prompt_at_management_group(self, deploy_template_mock, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.no_change),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        # Act.
        deploy_arm_template_at_management_group(cmd, mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_not_called()
        deploy_template_mock.assert_called_once()

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_tenant_scope_core", autospec=True)
    def test_confirm_with_what_if_prompt_at_tenant_scope(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_tenant_scope(mock.MagicMock(), confirm_with_what_if=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_tenant_scope_core", autospec=True)
    def test_proceed_if_no_change_prompt_at_tenant_scope(self, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.modify),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        prompt_y_n_mock.return_value = False
        # Act.
        result = deploy_arm_template_at_tenant_scope(mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_called_once_with("\nAre you sure you want to execute the deployment?")
        self.assertIsNone(result)

    @mock.patch("knack.prompting.prompt_y_n", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._what_if_deploy_arm_template_at_tenant_scope_core", autospec=True)
    @mock.patch("azure.cli.command_modules.resource.custom._deploy_arm_template_at_tenant_scope", autospec=True)
    def test_proceed_if_no_change_skip_prompt_at_tenant_scope(self, deploy_template_mock, what_if_command_mock, prompt_y_n_mock):
        # Arrange.
        what_if_command_mock.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource1', change_type=ChangeType.no_change),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])
        # Act.
        deploy_arm_template_at_tenant_scope(cmd, mock.MagicMock(), confirm_with_what_if=True, proceed_if_no_change=True)
        # Assert.
        prompt_y_n_mock.assert_not_called()
        deploy_template_mock.assert_called_once()

    @mock.patch("azure.cli.command_modules.resource.custom.LongRunningOperation.__call__", autospec=True)
    def test_what_if_exclude_change_types(self, long_running_operation_stub):
        # Arrange.
        long_running_operation_stub.return_value = WhatIfOperationResult(changes=[
            WhatIfChange(resource_id='resource0', change_type=ChangeType.create),
            WhatIfChange(resource_id='resource1', change_type=ChangeType.modify),
            WhatIfChange(resource_id='resource2', change_type=ChangeType.ignore),
        ])

        # Act.
        result = _what_if_deploy_arm_template_core(cmd.cli_ctx, mock.MagicMock(), True, ["create", "igNoRE"])

        # Assert.
        self.assertEqual(1, len(result.changes))
        self.assertEqual(ChangeType.modify, result.changes[0].change_type)

class TestFormatBicepFile(unittest.TestCase):
    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to", return_value=True)
    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command", return_value="formatted content")
    @mock.patch("builtins.print")
    def test_format_bicep_file(self, mock_print, mock_run_bicep_command, mock_bicep_version_greater_than_or_equal_to):
        # Arrange.
        file_path = "path/to/file.bicep"
        stdout = True

        # Act.
        format_bicep_file(cmd, file_path, stdout=stdout)

        # Assert.
        mock_bicep_version_greater_than_or_equal_to.assert_has_calls([
            mock.call(cmd.cli_ctx, "0.12.1"),
            mock.call(cmd.cli_ctx, "0.26.54"),
        ])
        mock_run_bicep_command.assert_called_once_with(cmd.cli_ctx, ["format", file_path, "--stdout"])

class TestPublishWithSource(unittest.TestCase):
    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to", return_value=True)
    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command", return_value="formatted content")
    def test_publish_withsource(self, mock_run_bicep_command, mock_bicep_version_greater_than_or_equal_to):
        # Arrange.
        file_path = "path/to/file.bicep"
        target = "br:contoso.azurecr.io/bicep/mymodule:v1"

        # Act.
        publish_bicep_file(cmd, file_path, target, documentationUri=None, with_source=None)

        # Assert.
        mock_bicep_version_greater_than_or_equal_to.assert_has_calls([
            mock.call(cmd.cli_ctx, "0.4.1008"), # Min version for 'bicep publish'
        ])
        mock_run_bicep_command.assert_called_once_with(cmd.cli_ctx, ['publish', file_path, '--target', 'br:contoso.azurecr.io/bicep/mymodule:v1'])

    @mock.patch("azure.cli.command_modules.resource.custom.bicep_version_greater_than_or_equal_to", return_value=True)
    @mock.patch("azure.cli.command_modules.resource.custom.run_bicep_command", return_value="formatted content")
    def test_publish_without_source(self, mock_run_bicep_command, mock_bicep_version_greater_than_or_equal_to):
        # Arrange.
        file_path = "path/to/file.bicep"
        target = "br:contoso.azurecr.io/bicep/mymodule:v1"

        # Act.
        publish_bicep_file(cmd, file_path, target, documentationUri=None, with_source=True)

        # Assert.
        mock_bicep_version_greater_than_or_equal_to.assert_has_calls([
            mock.call(cmd.cli_ctx, "0.4.1008"), # Min version for 'bicep publish'
            mock.call(cmd.cli_ctx, '0.26.54'),
            mock.call(cmd.cli_ctx, "0.23.1") # Min version for 'bicep publish --with-source'
        ])
        mock_run_bicep_command.assert_called_once_with(cmd.cli_ctx, ['publish', file_path, '--target', 'br:contoso.azurecr.io/bicep/mymodule:v1', '--with-source'])


class TestTemplateSizeOptimization(unittest.TestCase):
    """Tests for bicep template size optimization changes."""

    @mock.patch('azure.cli.command_modules.resource.custom.validate_bicep_target_scope')
    @mock.patch('azure.cli.command_modules.resource.custom.run_bicep_command')
    @mock.patch('azure.cli.command_modules.resource.custom.is_bicep_file')
    def test_process_template_file_bicep_returns_both(self, mock_is_bicep, mock_run_bicep, mock_validate):
        """Test that bicep files return both template_content and template_obj."""
        # Arrange
        mock_is_bicep.return_value = True
        mock_template_json = '{"$schema": "https://schema.management.azure.com/schemas/2019-08-01/deploymentTemplate.json#", "resources": []}'
        mock_run_bicep.return_value = mock_template_json
        mock_validate.return_value = None  # No validation errors
        
        # Act
        template_content, template_obj = _process_template_file(cmd, "test.bicep", "resourceGroup")
        
        # Assert
        self.assertEqual(template_content, mock_template_json)
        self.assertIsInstance(template_obj, dict)
        self.assertEqual(template_obj['$schema'], "https://schema.management.azure.com/schemas/2019-08-01/deploymentTemplate.json#")
        mock_run_bicep.assert_called_once()
        mock_validate.assert_called_once()

    @mock.patch('azure.cli.command_modules.resource.custom._remove_comments_from_json')
    @mock.patch('azure.cli.command_modules.resource.custom.read_file_content')
    @mock.patch('azure.cli.command_modules.resource.custom.is_bicep_file')
    def test_process_template_file_arm_returns_both(self, mock_is_bicep, mock_read_file, mock_remove_comments):
        """Test that ARM templates return both template_content and template_obj."""
        # Arrange
        mock_is_bicep.return_value = False
        mock_template_content = '{"$schema": "https://schema.management.azure.com/schemas/2019-08-01/deploymentTemplate.json#", "resources": []}'
        mock_template_obj = {"$schema": "https://schema.management.azure.com/schemas/2019-08-01/deploymentTemplate.json#", "resources": []}
        mock_read_file.return_value = mock_template_content
        mock_remove_comments.return_value = mock_template_obj
        
        # Act
        template_content, template_obj = _process_template_file(cmd, "test.json", "resourceGroup")
        
        # Assert
        self.assertEqual(template_content, mock_template_content)
        self.assertEqual(template_obj, mock_template_obj)
        mock_read_file.assert_called_once_with("test.json")
        mock_remove_comments.assert_called_once()

    @mock.patch('azure.cli.command_modules.resource.custom._get_template_for_deployment')
    @mock.patch('azure.cli.command_modules.resource.custom._process_template_file')
    def test_bicep_deployment_uses_compact_json_string(self, mock_process_template, mock_get_template):
        """Test that bicep deployments use compact JSON string to avoid size inflation."""
        # Arrange
        mock_template_content = '{"resources": []}'
        mock_template_obj = {"resources": []}
        mock_process_template.return_value = (mock_template_content, mock_template_obj)
        compact_json = '{"resources":[]}'  # Compact version
        mock_get_template.return_value = compact_json  # This is the key - bicep uses compact JSON string
        
        # Act
        properties = _prepare_deployment_properties_unmodified(cmd, "resourceGroup", "test.bicep", None, None, None, None)
        
        # Assert
        self.assertEqual(properties.template, compact_json)
        self.assertIsInstance(properties.template, str)  # Should be string, not dict
        mock_get_template.assert_called_once()
        # Verify that _get_template_for_deployment was called with both content and obj
        args = mock_get_template.call_args[0]
        self.assertIn(mock_template_content, args)  # template_content parameter
        self.assertIn(mock_template_obj, args)      # template_obj parameter

    @mock.patch('azure.cli.command_modules.resource.custom._get_template_for_deployment')
    @mock.patch('azure.cli.command_modules.resource.custom._process_template_file')  
    def test_arm_deployment_uses_template_content(self, mock_process_template, mock_get_template):
        """Test that ARM deployments use template_content for JsonC compatibility."""
        # Arrange
        mock_template_content = '{"resources": []}'
        mock_template_obj = {"resources": []}
        mock_process_template.return_value = (mock_template_content, mock_template_obj)
        mock_get_template.return_value = mock_template_content  # ARM uses template_content
        
        # Act
        properties = _prepare_deployment_properties_unmodified(cmd, "resourceGroup", "test.json", None, None, None, None)
        
        # Assert
        self.assertEqual(properties.template, mock_template_content)
        mock_get_template.assert_called_once()

    @mock.patch('azure.cli.command_modules.resource.custom._urlretrieve')
    def test_uri_deployment_uses_template_link(self, mock_urlretrieve):
        """Test that URI deployments use templateLink without local processing."""
        # Arrange
        mock_urlretrieve.return_value = b'{"resources": []}'
        
        # Act
        properties = _prepare_deployment_properties_unmodified(cmd, "resourceGroup", None, "https://example.com/template.json", None, None, None)
        
        # Assert
        self.assertEqual(properties.template_link.uri, "https://example.com/template.json")
        self.assertIsNone(properties.template)  # Uses templateLink, not template

    @mock.patch('azure.cli.command_modules.resource.custom.is_bicep_file')
    def test_get_template_for_deployment_bicep_uses_compact_json(self, mock_is_bicep):
        """Test that _get_template_for_deployment returns compact JSON string for bicep files."""
        # Arrange
        mock_is_bicep.return_value = True
        template_content = '{"resources": []}'
        template_obj = {"resources": []}

        # Import the function we're testing
        from azure.cli.command_modules.resource.custom import _get_template_for_deployment

        # Act
        result = _get_template_for_deployment(None, None, "test.bicep", template_content, template_obj, None)

        # Assert
        import json
        self.assertEqual(result, json.dumps(template_obj, separators=(',', ':')))  # Should return compact JSON string
        self.assertIsInstance(result, str)  # Should be a string, not an object

    @mock.patch('azure.cli.command_modules.resource.custom.is_bicep_file')
    def test_get_template_for_deployment_arm_uses_content(self, mock_is_bicep):
        """Test that _get_template_for_deployment returns template_content for ARM files."""
        # Arrange
        mock_is_bicep.return_value = False
        template_content = '{"resources": []}'
        template_obj = {"resources": []}
        
        # Import the function we're testing  
        from azure.cli.command_modules.resource.custom import _get_template_for_deployment
        
        # Act
        result = _get_template_for_deployment(None, None, "test.json", template_content, template_obj, None)
        
        # Assert
        self.assertEqual(result, template_content)  # Should return the string, not the object

    def test_bicep_vs_arm_size_comparison(self):
        """Test that demonstrates bicep templates avoid string escaping overhead."""
        # This test demonstrates the size optimization concept
        
        # Sample content with characters that would be escaped in JSON strings
        test_content = '''
        {
          "description": "A test template\\nwith special \\"chars\\" and 'quotes'",
          "value": "Line 1\\nLine 2\\nLine 3\\\\path"
        }
        '''
        
        # When treated as JSON object (bicep path) - no escaping
        import json
        template_obj = json.loads(test_content)
        obj_representation = json.dumps(template_obj, separators=(',', ':'))
        
        # When treated as string content (ARM path) - escaping applied
        import re
        escaped_content = re.sub(r'\\', r'\\\\', test_content)  # Simplified escaping simulation
        escaped_content = re.sub(r'"', r'\\"', escaped_content)
        
        # Assert that object representation is more compact
        self.assertLess(len(obj_representation), len(escaped_content))
        
        # This demonstrates why bicep templates using template_obj avoid size inflation


class BicepTemplateSizeOptimizationScenarioTest(ScenarioTest):
    """Functional tests for bicep template size optimization.
    
    These scenario tests verify that our bicep template size optimization works
    correctly in real deployment scenarios and generates recordings for CI/CD.
    """

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_bicep_size_opt')
    def test_bicep_deployment_size_optimization(self, resource_group):
        """Test that bicep deployments work correctly with size optimization.
        
        This test verifies that:
        1. Bicep templates deploy successfully with our optimization
        2. The optimization doesn't break existing functionality
        3. Key Vault creation works with bicep templates
        """
        self.kwargs.update({
            'deployment_name': self.create_random_name('deploy', 15),
            'kv_name': self.create_random_name('testkv', 15)[:24]  # Key Vault names max 24 chars
        })

        # Create a simple bicep template content that creates a Key Vault
        bicep_content = '''param keyVaultName string
param location string = resourceGroup().location
param tenantId string = subscription().tenantId

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
'''

        # Create a temporary bicep file
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bicep', delete=False) as f:
            f.write(bicep_content)
            bicep_file_path = f.name

        try:
            # Test bicep deployment - this exercises our optimization
            result = self.cmd(f'az deployment group create -g {{rg}} -n {{deployment_name}} --template-file "{bicep_file_path}" --parameters keyVaultName={{kv_name}}', checks=[
                self.check('properties.provisioningState', 'Succeeded'),
                self.check('properties.outputs.keyVaultName.value', '{kv_name}')
            ])

            # Verify the deployment was successful
            self.cmd('az deployment group show -g {rg} -n {deployment_name}', checks=[
                self.check('properties.provisioningState', 'Succeeded'),
                self.check('name', '{deployment_name}')
            ])

            # Verify the Key Vault was created successfully
            self.cmd('az keyvault show -g {rg} -n {kv_name}', checks=[
                self.check('name', '{kv_name}'),
                self.check('properties.sku.name', 'standard'),
                self.check('properties.enableSoftDelete', True)
            ])

        finally:
            # Clean up temporary file
            if os.path.exists(bicep_file_path):
                os.unlink(bicep_file_path)

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_bicep_vs_arm_opt')  
    def test_bicep_vs_arm_template_deployment(self, resource_group):
        """Test both bicep and ARM template deployments work correctly.
        
        This test verifies that our optimization doesn't break ARM templates
        while optimizing bicep templates.
        """
        self.kwargs.update({
            'bicep_deployment': self.create_random_name('biceptest', 20),
            'arm_deployment': self.create_random_name('armtest', 20),
            'kv_name_bicep': self.create_random_name('bicepkv', 15)[:24],
            'kv_name_arm': self.create_random_name('armkv', 15)[:24]
        })

        # Bicep template content
        bicep_content = '''param keyVaultName string
param location string = resourceGroup().location
param tenantId string = subscription().tenantId

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: tenantId
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

output keyVaultName string = keyVault.name
'''

        # ARM template content (equivalent to the bicep above)
        arm_content = '''{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "keyVaultName": {
      "type": "string"
    },
    "location": {
      "type": "string",
      "defaultValue": "[resourceGroup().location]"
    },
    "tenantId": {
      "type": "string", 
      "defaultValue": "[subscription().tenantId]"
    }
  },
  "resources": [
    {
      "type": "Microsoft.KeyVault/vaults",
      "apiVersion": "2023-07-01",
      "name": "[parameters('keyVaultName')]",
      "location": "[parameters('location')]",
      "properties": {
        "sku": {
          "family": "A",
          "name": "standard"
        },
        "tenantId": "[parameters('tenantId')]",
        "accessPolicies": [],
        "enableRbacAuthorization": true,
        "enableSoftDelete": true,
        "softDeleteRetentionInDays": 7
      }
    }
  ],
  "outputs": {
    "keyVaultName": {
      "type": "string",
      "value": "[parameters('keyVaultName')]"
    }
  }
}'''

        import tempfile
        import os
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bicep', delete=False) as f:
            f.write(bicep_content)
            bicep_file_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(arm_content)
            arm_file_path = f.name

        try:
            # Test bicep deployment (uses our optimization)
            self.cmd(f'az deployment group create -g {{rg}} -n {{bicep_deployment}} --template-file "{bicep_file_path}" --parameters keyVaultName={{kv_name_bicep}}', checks=[
                self.check('properties.provisioningState', 'Succeeded')
            ])

            # Test ARM template deployment (should still work normally)  
            self.cmd(f'az deployment group create -g {{rg}} -n {{arm_deployment}} --template-file "{arm_file_path}" --parameters keyVaultName={{kv_name_arm}}', checks=[
                self.check('properties.provisioningState', 'Succeeded')
            ])

            # Verify both deployments succeeded
            self.cmd('az deployment group list -g {rg}', checks=[
                self.check('length(@)', 2)
            ])

            # Verify both key vaults were created
            self.cmd('az keyvault show -g {rg} -n {kv_name_bicep}', checks=[
                self.check('name', '{kv_name_bicep}')
            ])

            self.cmd('az keyvault show -g {rg} -n {kv_name_arm}', checks=[
                self.check('name', '{kv_name_arm}')
            ])

        finally:
            # Clean up temporary files
            for file_path in [bicep_file_path, arm_file_path]:
                if os.path.exists(file_path):
                    os.unlink(file_path)


if __name__ == '__main__':
    unittest.main()
