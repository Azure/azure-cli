# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Native API09 egress configuration-management recording through BrazilUS ARM.

Resources are created in East US 2 EUAP; the transport endpoint is independent of location.
Uses synthetic setting values and real assigned identities, without outbound workloads or
SQL/Storage resources, grants, or firewall changes. Production cloud settings are unchanged.
"""

import os
import re
from unittest.mock import patch

from azure.cli.testsdk import ResourceGroupPreparer, ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload


class EgressRecordingSanitizer(RecordingProcessor):
    @staticmethod
    def _sanitize(value):
        value = re.sub(
            r'(?i)("(?:tenantId|principalId|clientId|subscriptionId|subscription|customerId)"\s*:\s*")'
            r'[0-9a-f-]{36}(")',
            r'\g<1>00000000-0000-0000-0000-000000000000\2', value)
        value = re.sub(
            r'(?i)("(?:publishingPassword|password|access_token|refresh_token|id_token|client_secret)"'
            r'\s*:\s*")[^"]*(")', r'\1sanitized\2', value)
        return re.sub(r'(?i)(userPWD=")[^"]*(")', r'\1sanitized\2', value)

    def process_request(self, request):
        if is_text_payload(request) and request.body:
            body = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
            request.body = self._sanitize(body)
        return request

    def process_response(self, response):
        response['headers'] = {
            key: values for key, values in response['headers'].items()
            if key.lower() != 'x-ms-operation-identifier'
        }
        if is_text_payload(response) and response['body']['string']:
            response['body']['string'] = self._sanitize(response['body']['string'])
        return response


class WebappEgressScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[EgressRecordingSanitizer()])
        self.vcr.match_on += ('body',)

    def setUp(self):
        if os.environ.get('AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME'):
            raise RuntimeError('Egress scenarios require their own new resource group, not an existing dev group.')
        super().setUp()
        self.assertEqual(
            self.cli_ctx.cloud.endpoints.active_directory_resource_id, 'https://management.core.windows.net/')
        self.kwargs['subscription'] = self.get_subscription_id()
        if self.in_recording:
            self.assertEqual(self.kwargs['subscription'], os.environ['AZURE_EGRESS_TEST_SUBSCRIPTION_ID'])

    def _egress(self, command='', expect_failure=False):
        # Global fixture APIs use the normal host; only egress requests target regional ARM.
        with patch.object(self.cli_ctx.cloud.endpoints, 'resource_manager', 'https://brazilus.management.azure.com/'):
            return self.cmd(
                'webapp config egress ' + command +
                ' -g {rg} -n {app} --subscription {subscription} {slot}', expect_failure=expect_failure)

    def _configuration(self):
        return self._egress('show').get_output_in_json()['properties']

    def _assert_configuration(self, connections, enabled):
        configuration = self._configuration()
        self.assertEqual(configuration['connections'], connections)
        self.assertEqual(configuration['enabled'], enabled)
        return configuration

    def _assert_enabled_is_required(self):
        from azure.cli.core.aaz._client import AAZBaseClient

        before = self._configuration()
        with patch.object(
                AAZBaseClient, 'send_request', autospec=True,
                side_effect=AAZBaseClient.send_request) as send_request:
            with self.assertRaises(SystemExit) as error:
                self._egress('set', expect_failure=True)
        self.assertEqual(error.exception.code, 2)
        send_request.assert_not_called()
        self.assertEqual(self._configuration(), before)

    def _assert_cannot_update_empty_configuration(self):
        from azure.cli.core import util as cli_util
        from azure.cli.core.aaz._client import AAZBaseClient
        from azure.cli.core.azclierror import InvalidArgumentValueError

        before = self._configuration()
        self.assertFalse(before.get('connections'))
        error = (
            'Cannot update the egress enabled state without a connection. Add a connection using '
            '`az webapp config egress connection add`, then retry.')
        for arguments in ['--enabled true', '--enabled false', '--enabled']:
            with patch.object(
                    AAZBaseClient, 'send_request', autospec=True,
                    side_effect=AAZBaseClient.send_request) as send_request, \
                    patch.object(cli_util, 'handle_exception', wraps=cli_util.handle_exception) as handle_exception:
                result = self._egress('set ' + arguments, expect_failure=True)
            self.assertEqual(result.exit_code, 1)
            handle_exception.assert_called_once()
            exception = handle_exception.call_args.args[0]
            self.assertIsInstance(exception, InvalidArgumentValueError)
            self.assertEqual(str(exception), error)
            send_request.assert_called_once()
            request = send_request.call_args.kwargs['request']
            self.assertEqual(request.method, 'GET')
            slot_path = '/slots/staging' if self.kwargs['slot'] else ''
            self.assertTrue(request.url.split('?', 1)[0].endswith(
                '/sites/' + self.kwargs['app'] + slot_path + '/config/egress'))
            self.assertEqual(self._configuration(), before)

    @AllowLargeResponse()
    @ResourceGroupPreparer(
        name_prefix='clitest-egress-', random_name_length=40, location='eastus2euap',
        subscription=os.environ.get('AZURE_EGRESS_TEST_SUBSCRIPTION_ID'))
    def test_webapp_egress_app_and_slot(self, resource_group):
        print('Egress temporary resource group: ' + resource_group)
        self.kwargs.update({
            'app': self.create_random_name('egressapp', 24),
            'plan': self.create_random_name('egressplan', 24),
            'identity': self.create_random_name('egressid', 24),
            'slot': '',
        })
        self.cmd(
            'appservice plan create -g {rg} -n {plan} --sku S1 --is-linux '
            '--location eastus2euap --subscription {subscription}')
        self.cmd(
            'webapp create -g {rg} -n {app} --plan {plan} --runtime "PYTHON:3.12" '
            '--subscription {subscription}')
        identity = self.cmd(
            'identity create -g {rg} -n {identity} --location eastus2euap '
            '--subscription {subscription}').get_output_in_json()
        self.kwargs['identity_id'] = identity['id']
        self.cmd(
            'webapp deployment slot create -g {rg} -n {app} --slot staging --subscription {subscription}')

        app_configuration = None
        for slot in ['', '--slot staging']:
            with self.subTest(slot=slot or 'production'):
                self.kwargs['slot'] = slot
                self._configure_settings_and_identity()
                self._exercise_connections()
                if not slot:
                    app_configuration = self._configuration()
        self.kwargs['slot'] = ''
        self.assertEqual(self._configuration(), app_configuration)

    def _configure_settings_and_identity(self):
        target = ' -g {rg} -n {app} --subscription {subscription} {slot}'
        assigned = self.cmd(
            'webapp identity assign --identities "[system]" {identity_id}' + target).get_output_in_json()
        self.assertIn(self.kwargs['identity_id'].lower(),
                      {key.lower() for key in assigned['userAssignedIdentities']})
        self.assertTrue(assigned['principalId'])
        self.cmd(
            'webapp config appsettings set --settings '
            'API_HOST=https://example.com API_TOKEN=non-secret-egress-fixture' + target)
        self.cmd(
            'webapp config connection-string set --connection-string-type SQLAzure --settings '
            '"OrdersDb=Server=tcp:egress-fixture.database.windows.net,1433;Database=Orders;'
            'Encrypt=True;Authentication=Active Directory Managed Identity;"' + target)

    def _exercise_connections(self):
        api = {
            'protocol': 'Http', 'auth': 'Credential', 'source': 'AppSettings',
            'settings': {'API_HOST': {'role': 'Host'}, 'API_TOKEN': {'role': 'Credential'}},
            'credentialInjection': {'header': 'Authorization', 'format': 'Bearer {value}'},
        }
        sql = {
            'protocol': 'Tds', 'auth': 'ManagedIdentity', 'source': 'ConnectionStrings',
            'settings': {'OrdersDb': {'role': 'Value'}},
            'identityScope': 'https://database.windows.net/.default',
        }
        api_arguments = (
            'connection add --connection-name api --protocol Http --auth Credential --source AppSettings '
            '--host-setting API_HOST --credential-setting API_TOKEN --credential-header Authorization '
            '--credential-format "Bearer {{value}}"')
        sql_arguments = (
            ' --protocol Tds --auth ManagedIdentity --source ConnectionStrings --value-setting OrdersDb '
            '--identity-scope https://database.windows.net/.default')
        self._assert_enabled_is_required()
        self._assert_cannot_update_empty_configuration()

        self.assertEqual(self._egress(api_arguments).get_output_in_json(), api)
        self._assert_configuration({'api': api}, 'Disabled')
        result = self._egress('set --enabled true').get_output_in_json()
        self.assertEqual(result['properties']['connections'], {'api': api})
        self._assert_configuration({'api': api}, 'Enabled')

        result = self._egress('connection add --connection-name orders-db' + sql_arguments).get_output_in_json()
        self.assertEqual(result, sql)
        self._assert_configuration({'api': api, 'orders-db': sql}, 'Enabled')

        result = self._egress(
            'connection add --connection-name ORDERS-DB' + sql_arguments +
            ' --identity-resource-id {identity_id}').get_output_in_json()
        sql = {**sql, 'identityResourceId': self.kwargs['identity_id']}
        self.assertEqual(result, sql)
        before = self._assert_configuration({'api': api, 'orders-db': sql}, 'Enabled')
        self.assertEqual(len([name for name in before['connections'] if name.lower() == 'orders-db']), 1)
        self.assertEqual(
            self._egress('connection show --connection-name OrDeRs-Db').get_output_in_json(), sql)

        self._assert_enabled_is_required()
        self._egress('set --enabled true')
        self.assertEqual(self._configuration(), before)
        self._egress('set --enabled false')
        self._assert_configuration({'api': api, 'orders-db': sql}, 'Disabled')
        self._egress('set --enabled')
        self._assert_configuration({'api': api, 'orders-db': sql}, 'Enabled')

        for action in ['show', 'remove']:
            result = self._egress('connection ' + action + ' --connection-name missing', expect_failure=True)
            self.assertNotEqual(result.exit_code, 0)
            self.assertEqual(self._configuration(), before)

        self._egress('connection remove --connection-name ORDERS-DB')
        self._assert_configuration({'api': api}, 'Enabled')

        self._egress('set --enabled false')
        disabled = self._assert_configuration({'api': api}, 'Disabled')
        self._egress('set --enabled false')
        self.assertEqual(self._configuration(), disabled)
        self._egress('connection remove --connection-name API --yes')
        self.assertEqual(self._configuration(), {})

        self.assertEqual(self._egress(
            'connection add --connection-name orders-db' + sql_arguments +
            ' --identity-resource-id {identity_id}').get_output_in_json(), sql)
        self._assert_configuration({'orders-db': sql}, 'Disabled')
        self._egress('set --enabled true')
        self._assert_configuration({'orders-db': sql}, 'Enabled')
        self._egress('connection remove --connection-name ORDERS-DB --yes')
        self.assertEqual(self._configuration(), {})
        self._assert_cannot_update_empty_configuration()
