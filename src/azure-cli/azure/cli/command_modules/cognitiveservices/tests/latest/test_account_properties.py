# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from azure.cli.core.mock import DummyCli
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.core.credentials import AccessToken
from azure.core.pipeline.transport import HttpTransport
from azure.core.rest import HttpResponse
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient


class CognitiveServicesAccountCostControlUnitTests(unittest.TestCase):
    CONNECTION_ID = (
        '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/'
        'providers/Microsoft.CognitiveServices/accounts/my-account/connections/telemetry'
    )

    def _invoke_update(self, connection_value=None, include_sku=True):
        credential = mock.Mock(spec=['get_token'])
        credential.get_token.return_value = AccessToken('test-token', 4102444800)
        transport = mock.MagicMock(spec=HttpTransport)
        response = mock.Mock(spec=HttpResponse)
        response.status_code = 200
        response.headers = {'Content-Type': 'application/json'}
        response.content_type = 'application/json'
        response.content = b'{"sku": {"name": "S0"}}'
        response.text.return_value = response.content.decode()
        response.json.return_value = {'sku': {'name': 'S0'}}
        response.iter_bytes.return_value = iter([response.content])
        transport.send.return_value = response
        output = io.StringIO()
        errors = io.StringIO()
        args = [
            'cognitiveservices', 'account', 'update', '--resource-group', 'my-rg',
            '--name', 'my-account', '--tags', 'environment=test',
        ]
        if include_sku:
            args.extend(['--sku', 'S0'])
        if connection_value is not None:
            args.extend(['--cost-control-connections', connection_value])

        with CognitiveServicesManagementClient(
                credential, '00000000-0000-0000-0000-000000000000', transport=transport) as client, \
                mock.patch(
                    'azure.cli.command_modules.cognitiveservices._client_factory.'
                    'get_cognitiveservices_management_client', return_value=client), \
                mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                redirect_stdout(output), redirect_stderr(errors):
            exit_code = DummyCli().invoke(args)
        return exit_code, errors.getvalue(), transport

    def test_cognitiveservices_account_update_cost_control_connections_on_wire(self):
        for value, expected in (
                (f'app-insights-connection-id={self.CONNECTION_ID}', self.CONNECTION_ID),
                (f'appInsightsConnectionId={self.CONNECTION_ID}', self.CONNECTION_ID),
                (f'app_insights_connection_id={self.CONNECTION_ID}', self.CONNECTION_ID),
                (json.dumps({'appInsightsConnectionId': self.CONNECTION_ID}), self.CONNECTION_ID),
                ('null', None),
                ('app-insights-connection-id=null', None),
                ('{"appInsightsConnectionId": null}', None)):
            with self.subTest(value=value):
                exit_code, errors, transport = self._invoke_update(value)
                self.assertEqual(exit_code, 0, errors)
                transport.send.assert_called_once()
                request = transport.send.call_args.args[0]
                payload = json.loads(request.body)
                self.assertEqual(request.method, 'PATCH')
                self.assertIn('api-version=2026-11-15-preview', request.url)
                self.assertEqual(payload['properties']['costControlConnections'], {
                    'appInsightsConnectionId': expected,
                })
                self.assertEqual(payload['sku']['name'], 'S0')
                self.assertEqual(payload['tags'], {'environment': 'test'})

    def test_cognitiveservices_account_update_omits_unspecified_cost_control_connections(self):
        exit_code, errors, transport = self._invoke_update()
        self.assertEqual(exit_code, 0, errors)
        transport.send.assert_called_once()
        payload = json.loads(transport.send.call_args.args[0].body)
        self.assertNotIn('costControlConnections', payload['properties'])

    def test_cognitiveservices_account_update_cost_control_connections_without_sku(self):
        exit_code, errors, transport = self._invoke_update(
            f'app-insights-connection-id={self.CONNECTION_ID}', include_sku=False)
        self.assertEqual(exit_code, 0, errors)
        self.assertEqual(transport.send.call_count, 2)
        get_request = transport.send.call_args_list[0].args[0]
        update_request = transport.send.call_args_list[1].args[0]
        self.assertEqual(get_request.method, 'GET')
        self.assertEqual(update_request.method, 'PATCH')
        payload = json.loads(update_request.body)
        self.assertEqual(payload['sku']['name'], 'S0')
        self.assertEqual(payload['properties']['costControlConnections'], {
            'appInsightsConnectionId': self.CONNECTION_ID,
        })

    def test_cognitiveservices_account_update_rejects_invalid_cost_control_connections(self):
        for value in ('app-insights-connection-id=', 'wrong-key=value', '{}',
                      '{"eventGridConnectionId": "value"}', '{"appInsightsConnectionId": 123}',
                      '{"appInsightsConnectionId":'):
            with self.subTest(value=value):
                exit_code, errors, transport = self._invoke_update(value, include_sku=False)
                self.assertNotEqual(exit_code, 0, errors)
                self.assertTrue(errors)
                transport.send.assert_not_called()

    def test_cognitiveservices_account_update_cost_control_connections_help(self):
        output = io.StringIO()
        with mock.patch('azure.cli.core.extension.get_extensions', return_value=[]), \
                redirect_stdout(output), redirect_stderr(output), self.assertRaises(SystemExit) as exit_context:
            DummyCli().invoke(['cognitiveservices', 'account', 'update', '--help'])
        self.assertEqual(exit_context.exception.code, 0, output.getvalue())
        self.assertIn('--cost-control-connections', output.getvalue())
        self.assertIn('app-insights-connection-id', output.getvalue())


class CognitiveServicesPropertiesTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_cognitiveservices_account_capabilities(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'FormRecognizer',
            'sku': 'S0',
            'location': 'southcentralus'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.assertTrue(account['properties']['capabilities'] is not None)
        self.assertTrue(len(account['properties']['capabilities']) > 0)
        self.assertTrue(account['properties']['capabilities'][0]['name'] is not None)
        self.assertTrue(account['properties']['capabilities'][0]['name'] != '')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_cognitiveservices_account_public_network_access(self, resource_group):
        sname = self.create_random_name(prefix='cs_cli_test_', length=16)

        self.kwargs.update({
            'sname': sname,
            'kind': 'Face',
            'sku': 'S0',
            'location': 'southcentralus'
        })

        # test to create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        print(account)
        self.assertEqual(account['properties']['publicNetworkAccess'], 'Enabled')


        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_cognitiveservices_aiservices(self, resource_group):
        sname = self.create_random_name(prefix='csclitest_', length=16)
        sname2 = self.create_random_name(prefix='csclitest2_', length=16)
        self.kwargs.update({
            'sname': sname,
            'sname2': sname2,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })

        # test to create cognitive services account with allow_project_management set to True by default for AIServices kind
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.allowProjectManagement', True)])
        account = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        self.assertTrue(account['identity']['type'] == 'SystemAssigned')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

        self.cmd('az cognitiveservices account create -n {sname2} -g {rg} --kind {kind} --sku {sku} -l {location} --allow-project-management true --yes',
                 checks=[self.check('name', '{sname2}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}'),
                         self.check('properties.allowProjectManagement', True)])
        account = self.cmd('az cognitiveservices account show -n {sname2} -g {rg}').get_output_in_json()
        self.assertTrue(account['identity']['type'] == 'SystemAssigned')

        # delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname2} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
