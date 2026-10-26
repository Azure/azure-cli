# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from itertools import product
from unittest import mock

from azure.cli.core.azclierror import InvalidArgumentValueError, RequiredArgumentMissingError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.cognitiveservices.custom import deployment_begin_create_or_update
from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpTransport
from azure.core.rest import HttpResponse
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Deployment


class CognitiveServicesDeploymentUnitTests(unittest.TestCase):

    def setUp(self):
        self.client = mock.Mock()
        self.arguments = {
            'client': self.client,
            'resource_group_name': 'my-rg',
            'account_name': 'my-account',
            'deployment_name': 'my-haiku',
            'model_format': 'Anthropic',
            'model_name': 'claude-haiku-4-5',
            'model_version': '2',
            'sku_name': 'GlobalStandard',
            'sku_capacity': 1,
        }
        self.provider_arguments = {
            'organization_name': 'Contoso',
            'industry': 'Law',
            'country': 'United States',
        }

    def test_cognitiveservices_deployment_provider_data(self):
        result = deployment_begin_create_or_update(**self.arguments, **self.provider_arguments)

        args, kwargs = self.client.begin_create_or_update.call_args
        self.assertEqual(args[:3], ('my-rg', 'my-account', 'my-haiku'))
        self.assertEqual(args[3].as_dict(), {
            'sku': {'name': 'GlobalStandard', 'capacity': 1},
            'properties': {
                'model': {'format': 'Anthropic', 'name': 'claude-haiku-4-5', 'version': '2'},
                'modelProviderData': {
                    'organizationName': 'Contoso',
                    'industry': 'Law',
                    'countryCode': 'US',
                },
            },
        })
        self.assertEqual(kwargs, {'polling': False})
        self.assertIs(result, self.client.begin_create_or_update.return_value)

    def test_cognitiveservices_deployment_country_names_and_codes(self):
        for country, expected in (
                ('United States', 'US'), ('us', 'US'), (' US ', 'US'),
                ('United Kingdom', 'GB'), ('Canada', 'CA'), ('Germany', 'DE'),
                ('Japan', 'JP'), ('India', 'IN')):
            with self.subTest(country=country):
                self.provider_arguments['country'] = country
                deployment_begin_create_or_update(**self.arguments, **self.provider_arguments)
                payload = self.client.begin_create_or_update.call_args.args[3].as_dict()
                self.assertEqual(payload['properties']['modelProviderData']['countryCode'], expected)

    def test_cognitiveservices_deployment_provider_data_optional(self):
        for model_format in ('OpenAI', 'Meta'):
            with self.subTest(model_format=model_format):
                self.arguments['model_format'] = model_format
                deployment_begin_create_or_update(**self.arguments)
                payload = self.client.begin_create_or_update.call_args.args[3].as_dict()
                self.assertNotIn('modelProviderData', payload['properties'])

    def test_cognitiveservices_deployment_existing_options(self):
        self.arguments['model_format'] = 'OpenAI'
        deployment_begin_create_or_update(
            **self.arguments, model_source='my-source', scale_settings_scale_type='Manual',
            scale_settings_capacity=3, spillover_deployment_name='my-spillover')

        payload = self.client.begin_create_or_update.call_args.args[3].as_dict()
        self.assertEqual(payload['properties']['model']['source'], 'my-source')
        self.assertEqual(payload['properties']['scaleSettings'], {'scaleType': 'Manual', 'capacity': 3})
        self.assertEqual(payload['properties']['spilloverDeploymentName'], 'my-spillover')
        self.assertNotIn('modelProviderData', payload['properties'])

    def test_cognitiveservices_deployment_missing_provider_fields(self):
        for model_format in ('Anthropic', 'anthropic', 'ANTHROPIC'):
            self.arguments['model_format'] = model_format
            for included in product((False, True), repeat=3):
                if all(included):
                    continue
                arguments = {
                    field: value for (field, value), include in zip(self.provider_arguments.items(), included)
                    if include
                }
                with self.subTest(model_format=model_format, fields=tuple(arguments)):
                    with self.assertRaises(RequiredArgumentMissingError):
                        deployment_begin_create_or_update(**self.arguments, **arguments)
                    self.client.begin_create_or_update.assert_not_called()

    def test_cognitiveservices_deployment_anthropic_format_casing(self):
        for model_format in ('Anthropic', 'anthropic', 'ANTHROPIC'):
            with self.subTest(model_format=model_format):
                self.arguments['model_format'] = model_format
                deployment_begin_create_or_update(**self.arguments, **self.provider_arguments)
                payload = self.client.begin_create_or_update.call_args.args[3].as_dict()
                self.assertEqual(payload['properties']['modelProviderData']['countryCode'], 'US')

    def test_cognitiveservices_deployment_empty_provider_fields(self):
        for field in self.provider_arguments:
            for value in ('', '   '):
                with self.subTest(field=field, value=value):
                    arguments = dict(self.provider_arguments, **{field: value})
                    with self.assertRaises(InvalidArgumentValueError):
                        deployment_begin_create_or_update(**self.arguments, **arguments)
                    self.client.begin_create_or_update.assert_not_called()

    def test_cognitiveservices_deployment_invalid_country(self):
        self.provider_arguments['country'] = 'not-a-country'
        with self.assertRaisesRegex(InvalidArgumentValueError, 'ISO country name or code'):
            deployment_begin_create_or_update(**self.arguments, **self.provider_arguments)
        self.client.begin_create_or_update.assert_not_called()

    def test_cognitiveservices_deployment_sdk_serialization(self):
        credential = mock.Mock(spec=['get_token'])
        credential.get_token.return_value = AccessToken('test-token', 4102444800)
        transport = mock.MagicMock(spec=HttpTransport)
        response = mock.Mock(spec=HttpResponse)
        response.status_code = 200
        response.headers = {'Content-Type': 'application/json'}
        response.content_type = 'application/json'
        response.content = b'{}'
        response.text.return_value = '{}'
        response.json.return_value = {}
        response.iter_bytes.return_value = iter([b'{}'])
        transport.send.return_value = response

        with CognitiveServicesManagementClient(
                credential, '00000000-0000-0000-0000-000000000000', transport=transport) as client:
            self.arguments['client'] = client.deployments
            deployment_begin_create_or_update(**self.arguments, **self.provider_arguments)

        transport.send.assert_called_once()
        request = transport.send.call_args.args[0]
        payload = json.loads(request.body)
        self.assertEqual(request.method, 'PUT')
        self.assertIn('api-version=2026-05-15-preview', request.url)
        self.assertEqual(payload['properties']['modelProviderData'], {
            'organizationName': 'Contoso', 'industry': 'Law', 'countryCode': 'US',
        })


class CognitiveServicesDeploymentCliUnitTests(unittest.TestCase):

    def test_cognitiveservices_deployment_cli_requires_anthropic_provider_arguments(self):
        cli = DummyCli()
        with mock.patch(
                'azure.cli.command_modules.cognitiveservices._client_factory.'
                'get_cognitiveservices_management_client') as factory, \
                mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            exit_code = cli.invoke([
                'cognitiveservices', 'account', 'deployment', 'create',
                '-g', 'my-rg', '-n', 'my-account', '--deployment-name', 'my-haiku',
                '--model-name', 'claude-haiku-4-5', '--model-version', '2',
                '--model-format', 'Anthropic', '--sku-name', 'GlobalStandard', '--sku-capacity', '1',
            ])

        self.assertNotEqual(exit_code, 0)
        factory.return_value.deployments.begin_create_or_update.assert_not_called()

    def test_cognitiveservices_deployment_cli_provider_arguments(self):
        for country_option, country in (('--country', 'United States'), ('--country-code', 'US')):
            with self.subTest(country_option=country_option):
                cli = DummyCli()
                output = io.StringIO()
                errors = io.StringIO()
                with mock.patch(
                        'azure.cli.command_modules.cognitiveservices._client_factory.'
                        'get_cognitiveservices_management_client') as factory, \
                        mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                        redirect_stdout(output), redirect_stderr(errors):
                    client = factory.return_value.deployments
                    client.begin_create_or_update.return_value = Deployment(name='my-haiku')
                    exit_code = cli.invoke([
                        'cognitiveservices', 'account', 'deployment', 'create',
                        '-g', 'my-rg', '-n', 'my-account', '--deployment-name', 'my-haiku',
                        '--model-name', 'claude-haiku-4-5', '--model-version', '2',
                        '--model-format', 'Anthropic', '--sku-capacity', '1',
                        '--sku-name', 'GlobalStandard', '--organization-name', 'Contoso',
                        '--industry', 'Law', country_option, country,
                    ])

                self.assertEqual(exit_code, 0, errors.getvalue())
                client.begin_create_or_update.assert_called_once()
                payload = client.begin_create_or_update.call_args.args[3].as_dict()
                self.assertEqual(payload['properties']['modelProviderData'], {
                    'organizationName': 'Contoso', 'industry': 'Law', 'countryCode': 'US',
                })

    def test_cognitiveservices_deployment_cli_help(self):
        cli = DummyCli()
        output = io.StringIO()
        with mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                redirect_stdout(output), redirect_stderr(output), self.assertRaises(SystemExit) as exit_context:
            cli.invoke(['cognitiveservices', 'account', 'deployment', 'create', '--help'])

        self.assertEqual(exit_context.exception.code, 0, output.getvalue())
        for option in ('--organization-name', '--industry', '--country', '--country-code'):
            self.assertIn(option, output.getvalue())
        self.assertIn('United States', output.getvalue())


if __name__ == '__main__':
    unittest.main()
