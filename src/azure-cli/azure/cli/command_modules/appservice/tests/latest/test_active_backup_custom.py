# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from http import HTTPStatus
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from azure.core.credentials import AccessToken
from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.core.pipeline.transport import HttpResponse
from requests.structures import CaseInsensitiveDict
from azure.cli.core._profile import Profile
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.appservice import AppserviceCommandsLoader, _active_backup


SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'
ROOT = '/subscriptions/' + SUBSCRIPTION + '/resourceGroups/MyRG/providers/Microsoft.Web'
SUBNET = ROOT.replace('Microsoft.Web', 'Microsoft.Network') + '/virtualNetworks/MyNet/subnets/integration'
GROUPS = {
    'appservice plan silo': ('create', 'update', 'show', 'list', 'delete', 'wait'),
    'appservice plan silo vnet-integration': ('list',),
    'webapp silo': ('create', 'update', 'show', 'list', 'delete', 'wait', 'refresh'),
    'webapp silo vnet-integration': ('show', 'add', 'update', 'remove'),
    'webapp managed-traffic': ('list', 'show', 'update'),
    'webapp last-known-good': ('list', 'show', 'mark'),
}


class ActiveBackupRecordingTests(unittest.TestCase):
    def test_scenario_sanitizes_publishing_credentials(self):
        from .test_active_backup_scenarios import ActiveBackupScenarioTests
        from .test_webapp_egress_scenario import EgressRecordingSanitizer

        scenario = ActiveBackupScenarioTests('test_active_backup_windows_lifecycle')
        sanitizer = next(p for p in scenario.recording_processors if isinstance(p, EgressRecordingSanitizer))
        response = {
            'headers': {'content-type': ['text/xml']},
            'body': {'string': '<publishProfile userPWD="synthetic-password" />'},
        }
        sanitized = sanitizer.process_response(response)['body']['string']
        self.assertNotIn('synthetic-password', sanitized)
        self.assertIn('userPWD="sanitized"', sanitized)


class ActiveBackupCustomTests(unittest.TestCase):
    def setUp(self):
        self.cli = DummyCli()
        self.requests = []
        self.resource = {
            'location': 'westus2',
            'tags': {'existing': 'keep'},
            'properties': {
                'primaryLocation': 'eastus',
                'instanceNumberOverride': 1,
                'zoneRedundantOverride': True,
                'followLastKnownGood': True,
                'trafficMode': 'Active',
                'provisioningState': 'Succeeded',
            },
        }
        self.client = mock.Mock()
        self.client.format_url.side_effect = lambda path, **kwargs: (
            'https://management.azure.com' + path.format(**kwargs))
        self.client._request.side_effect = self._make_request  # pylint: disable=protected-access
        self.client.send_request.side_effect = self._send_request
        self.client.build_lro_polling.side_effect = self._polling
        for patch in (
                mock.patch('azure.cli.core.aaz._command_ctx.AAZCommandCtx.get_http_client', return_value=self.client),
                mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', return_value=SUBSCRIPTION),
                mock.patch('socket.socket.connect', side_effect=AssertionError('Unexpected network request')),
                mock.patch('socket.create_connection', side_effect=AssertionError('Unexpected network request'))):
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def _make_request(method, url, query, headers, content, *_):
        return {'method': method, 'url': url, 'query': query, 'headers': headers, 'body': content}

    @staticmethod
    def _polling(_no_wait, session, on_success, _on_error, **_kwargs):
        return SimpleNamespace(run=lambda: on_success(session), resource=lambda: None)

    def _send_request(self, request, **_kwargs):
        self.requests.append(copy.deepcopy(request))
        data = copy.deepcopy(self.resource)
        if request['method'] in ('PUT', 'PATCH'):
            data = copy.deepcopy(request['body'])
        return SimpleNamespace(
            http_response=SimpleNamespace(status_code=200),
            context={ContentDecodePolicy.CONTEXT_NAME: data},
        )

    def _invoke(self, command, expected_code=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = self.cli.invoke(command.split(), out_file=stdout)
            except SystemExit as error:
                code = error.code
        self.assertEqual(code, expected_code, stderr.getvalue())
        return stdout.getvalue(), stderr.getvalue()

    def _assert_request(self, index, method, suffix):
        request = self.requests[index]
        self.assertEqual(request['method'], method)
        self.assertEqual(request['url'], 'https://management.azure.com' + ROOT + suffix)
        self.assertEqual(request['query'], {'api-version': '2026-08-01'})
        return request

    def test_command_catalog_and_preview(self):
        loader = AppserviceCommandsLoader(self.cli)
        commands = loader.load_command_table(None)
        expected = {group + ' ' + verb for group, verbs in GROUPS.items() for verb in verbs}
        actual = {
            name for name in commands
            if any(name.startswith(group + ' ') for group in GROUPS)
        }
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 24)
        self.assertNotIn('webapp silo vnet-integration list', commands)
        self.assertNotIn('web site silo virtual-network-connection list', commands)
        for name in expected:
            with self.subTest(command=name):
                command = commands[name]
                self.assertIsNotNone(command.preview_info)
                schema = command.get_arguments_schema()
                self.assertEqual(schema.name._options, ['-n', '--name'])  # pylint: disable=protected-access
                if hasattr(schema, 'silo_name'):
                    self.assertEqual(schema.silo_name._options, ['--silo'])  # pylint: disable=protected-access
        self.assertFalse(any(name.startswith((
            'web serverfarm silo ', 'web site silo ', 'web site last-known-good ', 'web site managed-traffic-config ',
        )) or name == 'web site refresh-silo' for name in commands))
        self.assertIn('webapp show', commands)
        for group in GROUPS:
            self.assertIn('preview_info', loader.command_group_table[group].group_kwargs)

    def test_group_and_command_help(self):
        for group in GROUPS:
            with self.subTest(group=group):
                self._invoke(group + ' --help')
            for verb in GROUPS[group]:
                with self.subTest(command=group + ' ' + verb):
                    self._invoke(group + ' ' + verb + ' --help')
        stdout, _ = self._invoke('appservice plan silo create --help')
        self.assertIn('--number-of-workers', stdout)
        self.assertIn('--zone-redundant', stdout)
        self.assertNotIn('--instance-number-override', stdout)
        self.assertNotIn('--silo-name', stdout)
        stdout, _ = self._invoke('webapp silo vnet-integration update --help')
        self.assertIn('--subnet', stdout)
        self.assertNotIn('--subnet-resource-id', stdout)
        self.assertNotIn('--set ', stdout)
        self.assertFalse(self.requests)

    def test_parent_and_silo_names_route_to_expected_resource(self):
        for group, parent in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            with self.subTest(group=group):
                self.requests.clear()
                self._invoke(group + ' show -g MyRG -n Primary --silo Backup')
                self._assert_request(0, 'GET', '/' + parent + '/Primary/silos/Backup')
                self.assertEqual(len(self.requests), 1)

    def test_primary_location_required_before_network(self):
        for group in ('appservice plan silo', 'webapp silo'):
            with self.subTest(group=group):
                self._invoke(group + ' create -g MyRG -n Primary --silo Backup --location westus2', expected_code=2)
        self.assertFalse(self.requests)

    def test_create_preserves_stage_location_on_wire(self):
        for group, parent in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            with self.subTest(group=group):
                self.requests.clear()
                self._invoke(group + ' create -g MyRG -n Primary --silo Backup '
                             '--location eastasia(stage) --primary-location eastus2euap')
                request = self._assert_request(0, 'PUT', '/' + parent + '/Primary/silos/Backup')
                self.assertEqual(request['body']['location'], 'eastasia(stage)')
                self.assertEqual(request['body']['properties']['primaryLocation'], 'eastus2euap')
                self.assertEqual(len(self.requests), 1)

    def test_plan_create_aliases_preserve_wire_names(self):
        self._invoke(
            'appservice plan silo create -g MyRG -n Primary --silo Backup --location westus2 '
            '--primary-location eastus --primary-plan-name Primary '
            '--number-of-workers 2 --zone-redundant false --tags environment=preview')
        request = self._assert_request(0, 'PUT', '/serverfarms/Primary/silos/Backup')
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(request['body'], {
            'location': 'westus2',
            'tags': {'environment': 'preview'},
            'properties': {
                'primaryLocation': 'eastus',
                'primaryServerFarmName': 'Primary',
                'instanceNumberOverride': 2,
                'zoneRedundantOverride': False,
            },
        })

    def test_site_create_location_and_traffic_mode(self):
        self._invoke(
            'webapp silo create -g MyRG -n Primary --silo Backup --location westus2 '
            '--primary-location eastus --traffic-mode Active --follow-last-known-good false')
        request = self._assert_request(0, 'PUT', '/sites/Primary/silos/Backup')
        self.assertEqual(request['body'], {
            'location': 'westus2',
            'properties': {'primaryLocation': 'eastus', 'trafficMode': 'Active', 'followLastKnownGood': False},
        })

    def test_silo_updates_keep_get_put_and_existing_fields(self):
        for group, parent, options in (
                ('appservice plan silo', 'serverfarms', '--number-of-workers 2 --zone-redundant false'),
                ('webapp silo', 'sites', '--follow-last-known-good false')):
            with self.subTest(group=group):
                self.requests.clear()
                self._invoke(group + ' update -g MyRG -n Primary --silo Backup ' + options)
                suffix = '/' + parent + '/Primary/silos/Backup'
                self._assert_request(0, 'GET', suffix)
                request = self._assert_request(1, 'PUT', suffix)
                self.assertEqual(len(self.requests), 2)
                self.assertEqual(request['body']['location'], 'westus2')
                self.assertEqual(request['body']['tags'], {'existing': 'keep'})
                self.assertEqual(request['body']['properties']['primaryLocation'], 'eastus')
                self.assertNotIn('provisioningState', request['body']['properties'])
                if parent == 'serverfarms':
                    self.assertEqual(request['body']['properties']['instanceNumberOverride'], 2)
                    self.assertIs(request['body']['properties']['zoneRedundantOverride'], False)
                else:
                    self.assertIs(request['body']['properties']['followLastKnownGood'], False)

    def test_silo_updates_without_tags_handle_null_service_tags(self):
        self.resource['tags'] = None
        for group, parent, options in (
                ('appservice plan silo', 'serverfarms', '--number-of-workers 2'),
                ('webapp silo', 'sites', '--follow-last-known-good false')):
            with self.subTest(group=group):
                self.requests.clear()
                self._invoke(group + ' update -g MyRG -n Primary --silo Backup ' + options)
                suffix = '/' + parent + '/Primary/silos/Backup'
                self._assert_request(0, 'GET', suffix)
                request = self._assert_request(1, 'PUT', suffix)
                self.assertEqual(len(self.requests), 2)
                self.assertIsNone(request['body'].get('tags'))
                if parent == 'serverfarms':
                    self.assertEqual(request['body']['properties']['instanceNumberOverride'], 2)
                else:
                    self.assertIs(request['body']['properties']['followLastKnownGood'], False)

    def test_vnet_show_flattens_response_properties(self):
        self.resource['properties'] = {'subnetResourceId': SUBNET, 'swiftSupported': True}
        stdout, _ = self._invoke('webapp silo vnet-integration show -g MyRG -n Primary --silo Backup')
        result = json.loads(stdout)
        self.assertEqual(result['subnetResourceId'], SUBNET)
        self.assertIs(result['swiftSupported'], True)
        self.assertNotIn('properties', result)
        self._assert_request(0, 'GET', '/sites/Primary/silos/Backup/virtualNetworkConnections/virtualNetwork')
        self.assertEqual(len(self.requests), 1)

    def test_vnet_patch_only_sends_supplied_fields(self):
        for options, expected in (
                ('--swift-supported false', {'swiftSupported': False}),
                ('--subnet ' + SUBNET, {'subnetResourceId': SUBNET}),
                ('--kind app --swift-supported false', {'swiftSupported': False})):
            with self.subTest(options=options):
                self.requests.clear()
                self._invoke('webapp silo vnet-integration update -g MyRG -n Primary --silo Backup ' + options)
                request = self._assert_request(
                    0, 'PATCH', '/sites/Primary/silos/Backup/virtualNetworkConnections/virtualNetwork')
                self.assertEqual(len(self.requests), 1)
                body = {'properties': expected}
                if '--kind' in options:
                    body['kind'] = 'app'
                self.assertEqual(request['body'], body)

    def test_vnet_add_uses_put_and_subnet_alias(self):
        self._invoke('webapp silo vnet-integration add -g MyRG -n Primary --silo Backup --subnet ' + SUBNET)
        request = self._assert_request(
            0, 'PUT', '/sites/Primary/silos/Backup/virtualNetworkConnections/virtualNetwork')
        self.assertEqual(request['body'], {'properties': {'subnetResourceId': SUBNET}})

    def test_plan_vnet_list_preserves_resource_envelope(self):
        self.resource = {
            'location': 'westus2',
            'properties': [{'subnetResourceId': SUBNET}],
        }
        self._invoke('appservice plan silo vnet-integration list -g MyRG -n Primary --silo Backup')
        self._assert_request(0, 'GET', '/serverfarms/Primary/silos/Backup/virtualNetworkIntegrations')
        result = self.cli.result.result
        self.assertEqual(result['properties'], [{'subnetResourceId': SUBNET}])

    def test_plan_vnet_list_requires_explicit_scope(self):
        command = 'appservice plan silo vnet-integration list'
        stdout, _ = self._invoke(command + ' --help')
        self.assertNotIn('--ids', stdout)
        for options in (
                '-n Primary --silo Backup',
                '-g MyRG --silo Backup',
                '-g MyRG -n Primary',
                '--ids ' + ROOT + '/serverfarms/Primary/silos/Backup'):
            with self.subTest(options=options):
                self._invoke(command + ' ' + options, expected_code=2)
        self.assertFalse(self.requests)

    def test_managed_traffic_update_preserves_get_put(self):
        self.resource = {'properties': {'trafficMode': 'Active', 'endpoints': [{'region': 'eastus', 'weight': 700}]}}
        self._invoke('webapp managed-traffic update -g MyRG -n Primary --traffic-mode Passive')
        self._assert_request(0, 'GET', '/sites/Primary/managedTrafficConfig/default')
        request = self._assert_request(1, 'PUT', '/sites/Primary/managedTrafficConfig/default')
        self.assertEqual(request['body'], {
            'properties': {'trafficMode': 'Passive', 'endpoints': [{'region': 'eastus', 'weight': 700}]},
        })

    def test_generated_schemas_are_not_modified(self):
        for custom, generated in (
                (_active_backup.PlanSiloCreate, _active_backup.plan_silo.Create),
                (_active_backup.PlanSiloUpdate, _active_backup.plan_silo.Update),
                (_active_backup.PlanSiloVnetList, _active_backup.PlanVnetShow),
                (_active_backup.WebappSiloCreate, _active_backup.site_silo.Create),
                (_active_backup.WebappSiloVnetUpdate, _active_backup.site_vnet.Update)):
            with self.subTest(command=custom.AZ_NAME):
                custom_schema = custom.get_arguments_schema()
                generated_schema = generated.get_arguments_schema()
                self.assertIsNot(custom_schema, generated_schema)
                self.assertEqual(  # pylint: disable=protected-access
                    generated_schema.silo_name._options, ['--silo-name'])
                if custom.AZ_NAME.endswith('create'):
                    self.assertFalse(generated_schema.primary_location._required)  # pylint: disable=protected-access
                    self.assertTrue(custom_schema.primary_location._required)  # pylint: disable=protected-access
                if custom is _active_backup.PlanSiloVnetList:
                    self.assertIsNone(custom_schema.name._id_part)  # pylint: disable=protected-access
                    self.assertEqual(generated_schema.name._id_part, 'name')  # pylint: disable=protected-access
        self.assertTrue(_active_backup.site_vnet.Update.AZ_SUPPORT_GENERIC_UPDATE)
        self.assertFalse(_active_backup.WebappSiloVnetUpdate.AZ_SUPPORT_GENERIC_UPDATE)
        patch_schema = _active_backup.WebappSiloVnetUpdate.get_arguments_schema()
        for field in ('subnet_resource_id', 'swift_supported', 'kind'):
            self.assertFalse(patch_schema[field]._nullable)  # pylint: disable=protected-access

    def test_silo_waits_still_poll_the_resource(self):
        for group, parent in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            with self.subTest(group=group):
                self.requests.clear()
                self._invoke(group + ' wait -g MyRG -n Primary --silo Backup --created --interval 1 --timeout 1')
                self._assert_request(0, 'GET', '/' + parent + '/Primary/silos/Backup')
                self.assertEqual(len(self.requests), 1)

    def test_delete_confirmation_is_preserved(self):
        for custom, generated in (
                (_active_backup.PlanSiloDelete, _active_backup.plan_silo.Delete),
                (_active_backup.WebappSiloDelete, _active_backup.site_silo.Delete),
                (_active_backup.WebappSiloVnetRemove, _active_backup.site_vnet.Delete)):
            self.assertTrue(custom.AZ_CONFIRMATION)
            self.assertEqual(custom.AZ_CONFIRMATION, generated.AZ_CONFIRMATION)

    def test_service_errors_propagate(self):
        self.client.send_request.side_effect = HttpResponseError(message='Service rejected the update.')
        with self.assertLogs(level='ERROR') as errors:
            self._invoke(
                'webapp silo vnet-integration update -g MyRG -n Primary --silo Backup --swift-supported false',
                expected_code=1)
        self.assertTrue(any('Service rejected the update' in entry for entry in errors.output))

    def test_hybrid_profile_does_not_load_latest_customizations(self):
        with mock.patch.object(self.cli.cloud, 'profile', '2020-09-01-hybrid'):
            commands = AppserviceCommandsLoader(self.cli).load_command_table(None)
        self.assertNotIn('webapp silo create', commands)
        self.assertNotIn('appservice plan silo create', commands)


class _OfflineCredential:
    def get_token(self, *_args, **_kwargs):
        return AccessToken('offline-active-backup-test', 9999999999)


class _OfflineResponse(HttpResponse):
    def __init__(self, request, status, payload, headers):
        super().__init__(request, None)
        self.status_code = status
        self.reason = HTTPStatus(status).phrase
        self.headers = CaseInsensitiveDict({'content-type': 'application/json', **headers})
        self.content_type = 'application/json'
        self._body = b'' if payload is None else json.dumps(payload).encode('utf-8')

    def body(self):
        return self._body


class ActiveBackupHttpTests(unittest.TestCase):
    """Exercise the real AAZ HTTP pipeline and poller, mocking only transport and credentials."""

    def setUp(self):
        self.cli = DummyCli()
        self.responses = []
        self.calls = []
        self.resource = {
            'id': ROOT + '/sites/Primary/silos/Backup',
            'name': 'Backup',
            'location': 'westus2',
            'properties': {'primaryLocation': 'eastus', 'provisioningState': 'Succeeded'},
        }
        for patch in (
                mock.patch.object(Profile, 'get_subscription',
                                  return_value={'id': SUBSCRIPTION, 'tenantId': SUBSCRIPTION, 'name': 'Offline'}),
                mock.patch.object(Profile, 'get_login_credentials',
                                  return_value=(_OfflineCredential(), SUBSCRIPTION, SUBSCRIPTION)),
                mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', return_value=SUBSCRIPTION),
                mock.patch('azure.core.pipeline.transport.RequestsTransport.send',
                           autospec=True, side_effect=self._send),
                mock.patch('socket.socket.connect', side_effect=AssertionError('Unexpected network request')),
                mock.patch('socket.create_connection', side_effect=AssertionError('Unexpected network request')),
                mock.patch('time.sleep')):
            patch.start()
            self.addCleanup(patch.stop)

    def _queue(self, method, suffix, status=200, payload=None, headers=None):
        self.responses.append((method, ROOT + suffix, status, payload, headers or {}))

    def _send(self, _transport, request, **_kwargs):
        self.assertTrue(self.responses, 'Unexpected HTTP request: ' + request.method + ' ' + request.url)
        method, path, status, payload, headers = self.responses.pop(0)
        parsed = urlsplit(request.url)
        self.assertEqual(request.method, method)
        self.assertEqual(parsed.path, path)
        self.assertEqual(parse_qs(parsed.query).get('api-version'), ['2026-08-01'])
        self.calls.append({
            'method': method,
            'url': request.url,
            'body': json.loads(request.body) if request.body else None,
        })
        return _OfflineResponse(request, status, payload, headers)

    def _invoke(self, command, expected_code=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = self.cli.invoke(command.split(), out_file=stdout)
            except SystemExit as error:
                code = error.code
        self.assertEqual(code, expected_code, stderr.getvalue())
        self.assertFalse(self.responses, 'Expected HTTP requests were not sent.')
        return self.cli.result.result if self.cli.result else None

    def test_collection_pagination_follows_next_link(self):
        for command, path, silo_option in (
                ('appservice plan silo list', '/serverfarms/Primary/silos', ''),
                ('webapp silo list', '/sites/Primary/silos', ''),
                ('webapp managed-traffic list', '/sites/Primary/managedTrafficConfig', ''),
                ('webapp last-known-good list', '/sites/Primary/lastKnownGood', '')):
            with self.subTest(command=command):
                self.calls.clear()
                first = {**self.resource, 'name': 'First'}
                second = {**self.resource, 'name': 'Second'}
                next_link = 'https://management.azure.com' + ROOT + path + '?api-version=2026-08-01&page=2'
                self._queue('GET', path, payload={'value': [first], 'nextLink': next_link})
                self._queue('GET', path, payload={'value': [second]})
                result = self._invoke(command + ' -g MyRG -n Primary ' + silo_option)
                self.assertEqual([item['name'] for item in result], ['First', 'Second'])
                self.assertEqual(len(self.calls), 2)
                self.assertEqual(self.calls[1]['url'], next_link)

    def test_http_errors_are_not_success_or_fallback(self):
        for status in (400, 403, 404, 409):
            for command, method, path, options in (
                    ('webapp silo show', 'GET', '/sites/Primary/silos/Backup', '--silo Backup'),
                    ('webapp silo vnet-integration update', 'PATCH',
                     '/sites/Primary/silos/Backup/virtualNetworkConnections/virtualNetwork',
                     '--silo Backup --swift-supported false')):
                with self.subTest(command=command, status=status):
                    self.calls.clear()
                    self._queue(method, path, status, {
                        'error': {'code': 'FixtureError', 'message': 'The service rejected this operation.'},
                    })
                    with self.assertLogs(level='ERROR') as errors:
                        self._invoke(command + ' -g MyRG -n Primary ' + options,
                                     expected_code=3 if status == 404 else 1)
                    self.assertTrue(any('FixtureError' in entry for entry in errors.output))
                    self.assertEqual(len(self.calls), 1)

    def test_update_get_failure_prevents_put(self):
        for command, path, options in (
                ('appservice plan silo update', '/serverfarms/Primary/silos/Backup', '--number-of-workers 2'),
                ('webapp silo update', '/sites/Primary/silos/Backup', '--follow-last-known-good false')):
            with self.subTest(command=command):
                self.calls.clear()
                self._queue('GET', path, 403, {'error': {'code': 'Forbidden', 'message': 'Read denied.'}})
                with self.assertLogs(level='ERROR'):
                    self._invoke(command + ' -g MyRG -n Primary --silo Backup ' + options, expected_code=1)
                self.assertEqual(len(self.calls), 1)

    def _silo_command(self, group, parent, verb):
        path = '/' + parent + '/Primary/silos/Backup'
        command = group + ' ' + verb + ' -g MyRG -n Primary --silo Backup'
        if verb == 'create':
            command += ' --location westus2 --primary-location eastus'
        elif verb == 'update':
            self._queue('GET', path, payload=self.resource)
            command += ' --number-of-workers 2' if parent == 'serverfarms' else ' --follow-last-known-good false'
        else:
            command += ' --yes'
        return command, path

    def test_async_create_update_delete_complete(self):
        for group, parent in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            for verb in ('create', 'update', 'delete'):
                with self.subTest(group=group, verb=verb):
                    self.calls.clear()
                    command, path = self._silo_command(group, parent, verb)
                    headers = {
                        'Azure-AsyncOperation': 'https://management.azure.com' + ROOT +
                        '/operations/test?api-version=2026-08-01',
                        'Retry-After': '0',
                    }
                    method = 'DELETE' if verb == 'delete' else 'PUT'
                    self._queue(method, path, 202, self.resource, headers)
                    self._queue('GET', '/operations/test', payload={'status': 'InProgress'})
                    self._queue('GET', '/operations/test', payload={'status': 'Succeeded'})
                    if verb != 'delete':
                        self._queue('GET', path, payload=self.resource)
                    result = self._invoke(command)
                    if verb != 'delete':
                        self.assertEqual(result['properties']['provisioningState'], 'Succeeded')
                    else:
                        self.assertIsNone(result)

    def test_no_wait_submits_without_polling(self):
        for group, parent in (('appservice plan silo', 'serverfarms'), ('webapp silo', 'sites')):
            for verb in ('create', 'update', 'delete'):
                with self.subTest(group=group, verb=verb):
                    self.calls.clear()
                    command, path = self._silo_command(group, parent, verb)
                    self._queue('DELETE' if verb == 'delete' else 'PUT', path, 202, self.resource, {
                        'Azure-AsyncOperation': 'https://management.azure.com' + ROOT +
                        '/operations/test?api-version=2026-08-01',
                    })
                    self.assertIsNone(self._invoke(command + ' --no-wait'))
                    self.assertEqual(len(self.calls), 2 if verb == 'update' else 1)

    def test_async_failure_cancellation_and_malformed_status_propagate(self):
        for status_body in (
                {'status': 'Failed', 'error': {'code': 'PlacementFailed', 'message': 'No capacity.'}},
                {'status': 'Canceled'},
                {}):
            with self.subTest(status=status_body):
                self.calls.clear()
                command, path = self._silo_command('webapp silo', 'sites', 'create')
                self._queue('PUT', path, 202, self.resource, {
                    'Azure-AsyncOperation': 'https://management.azure.com' + ROOT +
                    '/operations/test?api-version=2026-08-01',
                    'Retry-After': '0',
                })
                self._queue('GET', '/operations/test', payload=status_body)
                with self.assertLogs(level='ERROR'):
                    self._invoke(command, expected_code=1)
                self.assertEqual(len(self.calls), 2)

    def test_delete_204_and_refresh_204_have_no_output(self):
        for command, method, path in (
                ('webapp silo delete --silo Backup --yes', 'DELETE', '/sites/Primary/silos/Backup'),
                ('appservice plan silo delete --silo Backup --yes', 'DELETE', '/serverfarms/Primary/silos/Backup'),
                ('webapp silo refresh', 'POST', '/sites/Primary/refreshSilos')):
            with self.subTest(command=command):
                self.calls.clear()
                self._queue(method, path, 204)
                self.assertIsNone(self._invoke(command + ' -g MyRG -n Primary'))
                self.assertEqual(len(self.calls), 1)
