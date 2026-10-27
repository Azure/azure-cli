# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest import mock

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core.azclierror import (
    InvalidArgumentValueError, RequiredArgumentMissingError, ResourceNotFoundError,
)
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.appservice import AppserviceCommandsLoader
from azure.cli.command_modules.appservice import custom


SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'
IDENTITY = (
    '/subscriptions/' + SUBSCRIPTION +
    '/resourceGroups/MyRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/MyIdentity'
)


class EgressCommandTests(unittest.TestCase):

    def setUp(self):
        self.cli = DummyCli()
        self.cmd = SimpleNamespace(cli_ctx=self.cli)
        self.config = {'enabled': 'Disabled', 'connections': {}}
        self.requests = []
        client = mock.Mock()
        client.format_url.side_effect = lambda path, **kwargs: 'https://management.azure.com' + path.format(**kwargs)
        client._request.side_effect = self._make_request  # pylint: disable=protected-access
        client.send_request.side_effect = self._send_request
        self.client = client
        patches = [
            mock.patch('azure.cli.core.aaz._command_ctx.AAZCommandCtx.get_http_client', return_value=client),
            mock.patch('azure.cli.core.commands.client_factory.get_subscription_id', return_value=SUBSCRIPTION),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    @staticmethod
    def _make_request(method, url, query, headers, content, *_):
        return {'method': method, 'url': url, 'query': query, 'headers': headers, 'body': content}

    def _send_request(self, request, **_):
        self.requests.append(copy.deepcopy(request))
        if request['method'] == 'PUT':
            self.config = copy.deepcopy(request['body']['properties'])
        return SimpleNamespace(
            http_response=SimpleNamespace(status_code=200),
            context={ContentDecodePolicy.CONTEXT_NAME: {
                'id': '/subscriptions/' + SUBSCRIPTION + '/resourceGroups/MyRG/providers/Microsoft.Web/sites/MyApp/config/egress',
                'name': 'egress', 'type': 'Microsoft.Web/sites/config',
                'properties': copy.deepcopy(self.config),
            }},
        )

    def _invoke(self, command, expected_code=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = self.cli.invoke(command, out_file=stdout)
            except SystemExit as ex:
                code = ex.code
        self.assertEqual(code, expected_code, stderr.getvalue())
        if '--help' in command or expected_code:
            return None
        return self.cli.result.result if self.cli.result else None

    def _assert_request(self, index, method, slot=None):
        request = self.requests[index]
        self.assertEqual(request['method'], method)
        slot_path = '/slots/' + slot if slot else ''
        self.assertEqual(
            request['url'],
            'https://management.azure.com/subscriptions/' + SUBSCRIPTION +
            '/resourceGroups/MyRG/providers/Microsoft.Web/sites/MyApp' + slot_path + '/config/egress')
        self.assertEqual(request['query'], {'api-version': '2026-09-01'})

    def test_webapp_egress_set_enabled_boolean_cli(self):
        connections = {
            'api': {'protocol': 'Http', 'auth': 'Credential', 'source': 'AppSettings',
                    'settings': {'HOST': {'role': 'Host'}, 'USER': {'role': 'Username'},
                                 'TOKEN': {'role': 'Credential'}},
                    'credentialInjection': {'header': 'Authorization', 'format': 'token={value}'}},
            'Orders-Db': {'protocol': 'Tds', 'auth': 'ManagedIdentity', 'source': 'ConnectionStrings',
                          'settings': {'OrdersDb': {'role': 'Value'}}, 'identityResourceId': IDENTITY,
                          'identityScope': 'https://database.windows.net/.default'},
        }
        cases = [
            (['--enabled', 'true'], 'Enabled'),
            (['--enabled', 'false'], 'Disabled'),
            (['--enabled', 'TrUe'], 'Enabled'),
            (['--enabled', 'FaLsE'], 'Disabled'),
            (['--enabled'], 'Enabled'),
            ([], None),
        ]
        for slot in [None, 'staging']:
            for existing_enabled in ['Enabled', 'Disabled', None]:
                for arguments, enabled in cases:
                    with self.subTest(slot=slot, existing_enabled=existing_enabled, arguments=arguments):
                        self.requests.clear()
                        self.config = {'connections': copy.deepcopy(connections)}
                        if existing_enabled is not None:
                            self.config['enabled'] = existing_enabled
                        command = [
                            'webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp',
                        ] + arguments + (['--slot', slot] if slot else [])
                        result = self._invoke(command)
                        expected = {'connections': connections}
                        expected_enabled = existing_enabled if enabled is None else enabled
                        if expected_enabled is not None:
                            expected['enabled'] = expected_enabled
                        self.assertEqual(len(self.requests), 2)
                        self._assert_request(0, 'GET', slot)
                        self._assert_request(1, 'PUT', slot)
                        self.assertEqual(self.requests[1]['body'], {'properties': expected})
                        self.assertEqual(result['properties'], expected)
                        self.assertEqual(self.config, expected)
                        shown = self._invoke(
                            ['webapp', 'config', 'egress', 'show', '-g', 'MyRG', '-n', 'MyApp'] +
                            (['--slot', slot] if slot else []))
                        self.assertEqual(shown['properties'], expected)
                        self._assert_request(2, 'GET', slot)

    def test_webapp_egress_set_enabled_boolean_handler(self):
        for slot in [None, 'staging']:
            for configuration in [None, {}, {'connections': None}, {'connections': {}}, {'enabled': 'Enabled'},
                                  {'connections': {}, 'enabled': 'Disabled'}]:
                for enabled, backend_enabled in [(True, 'Enabled'), (False, 'Disabled'), (None, None)]:
                    with self.subTest(slot=slot, configuration=configuration, enabled=enabled):
                        self.requests.clear()
                        self.config = copy.deepcopy(configuration)
                        result = custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=enabled, slot=slot)
                        expected = {'connections': {}}
                        expected_enabled = (configuration or {}).get('enabled') if enabled is None else backend_enabled
                        if expected_enabled is not None:
                            expected['enabled'] = expected_enabled
                        self.assertEqual(len(self.requests), 2)
                        self._assert_request(0, 'GET', slot)
                        self._assert_request(1, 'PUT', slot)
                        self.assertEqual(self.requests[1]['body'], {'properties': expected})
                        self.assertEqual(result['properties'], expected)

    def test_webapp_egress_set_rejects_connection_arguments(self):
        for slot in [None, 'staging']:
            for option in [
                    '--connection', '--connections', '--connection-name', '--protocol', '--auth', '--source',
                    '--host-setting', '--credential-setting', '--username-setting', '--value-setting',
                    '--identity-resource-id', '--identity-scope', '--credential-header', '--credential-format']:
                with self.subTest(slot=slot, option=option):
                    self._invoke(
                        ['webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp',
                         '--enabled', 'false', option, 'unused'] +
                        (['--slot', slot] if slot else []), expected_code=2)
        self.assertEqual(self.requests, [])

    def test_webapp_egress_set_rejects_non_boolean_cli_values(self):
        for slot in [None, 'staging']:
            for enabled in ['Enabled', 'Disabled', 'enabled', 'disabled', 'unknown', '0', '1']:
                with self.subTest(slot=slot, enabled=enabled):
                    self._invoke(
                        ['webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp',
                         '--enabled', enabled] + (['--slot', slot] if slot else []), expected_code=2)
        self.assertEqual(self.requests, [])

    def test_webapp_egress_set_rejects_non_boolean_handler_values(self):
        for enabled in ['true', 'false', 'Enabled', 'Disabled', 'unknown', '', 0, 1, [], {}]:
            with self.subTest(enabled=enabled):
                with self.assertRaisesRegex(InvalidArgumentValueError, 'Specify true or false for --enabled'):
                    custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=enabled)
        self.assertEqual(self.requests, [])

    def test_webapp_egress_connection_mutations_preserve_enabled_strings(self):
        for slot in [None, 'staging']:
            for enabled in ['Enabled', 'Disabled', None]:
                with self.subTest(slot=slot, enabled=enabled):
                    self.requests.clear()
                    self.config = {
                        'connections': {
                            'keep': {'protocol': 'Tds', 'auth': 'ManagedIdentity', 'source': 'ConnectionStrings',
                                     'settings': {'OrdersDb': {'role': 'Value'}}},
                        },
                    }
                    if enabled is not None:
                        self.config['enabled'] = enabled
                    original = copy.deepcopy(self.config)
                    custom.add_egress_connection(
                        self.cmd, 'MyRG', 'MyApp', 'cache', 'Redis', 'Credential',
                        value_setting='Redis', slot=slot)
                    self.assertEqual(self.requests[1]['body']['properties'].get('enabled'), enabled)
                    self.assertEqual(self.config['connections']['keep'], original['connections']['keep'])
                    custom.remove_egress_connection(self.cmd, 'MyRG', 'MyApp', 'CACHE', slot=slot)
                    self.assertEqual(self.requests[3]['body']['properties'].get('enabled'), enabled)
                    self.assertEqual(self.config, original)
                    self.assertEqual(len(self.requests), 4)
                    for index, method in enumerate(['GET', 'PUT', 'GET', 'PUT']):
                        self._assert_request(index, method, slot)

    def test_webapp_egress_connection_add_cli_example(self):
        self.config['connections']['cache'] = {
            'protocol': 'Redis', 'auth': 'Credential', 'source': 'AppSettings',
            'settings': {'REDIS_HOST': {'role': 'Host'}, 'REDIS_PASSWORD': {'role': 'Credential'}},
        }
        original = copy.deepcopy(self.config['connections']['cache'])
        result = self._invoke([
            'webapp', 'config', 'egress', 'connection', 'add', '-g', 'MyRG', '-n', 'MyApp',
            '--connection-name', 'orders-db', '--source', 'ConnectionStrings',
            '--protocol', 'Tds', '--auth', 'ManagedIdentity', '--value-setting', 'OrdersDb',
        ])
        self.assertEqual(self.config['enabled'], 'Disabled')
        self.assertEqual(self.config['connections']['cache'], original)
        self.assertEqual(result, self.config['connections']['orders-db'])
        self.assertEqual(result['settings'], {'OrdersDb': {'role': 'Value'}})
        self.assertEqual(len(self.requests), 2)
        self._assert_request(0, 'GET')
        self._assert_request(1, 'PUT')

    def test_webapp_egress_round_trip_extended_properties_and_upsert(self):
        existing = {
            'auth': 'Credential', 'protocol': 'Http', 'source': 'AppSettings',
            'settings': {'API_HOST': {'role': 'Host'}, 'API_TOKEN': {'role': 'Credential'}},
            'credentialInjection': {'header': 'Authorization', 'format': 'Bearer {value}'},
        }
        self.config = {'enabled': 'Enabled', 'connections': {
            'api': copy.deepcopy(existing),
            'Orders-Db': {'auth': 'ManagedIdentity', 'protocol': 'Tds', 'source': 'ConnectionStrings',
                          'settings': {'OldDb': {'role': 'Value'}}, 'identityResourceId': IDENTITY,
                          'identityScope': 'https://database.windows.net/.default'},
        }}
        result = custom.add_egress_connection(
            self.cmd, 'MyRG', 'MyApp', 'orders-db', 'Tds', 'ManagedIdentity',
            source='ConnectionStrings', value_setting='OrdersDb', identity_resource_id=IDENTITY,
            identity_scope='https://database.windows.net/.default', slot='staging')
        self.assertEqual(list(self.config['connections']), ['api', 'Orders-Db'])
        self.assertEqual(self.config['connections']['api'], existing)
        self.assertEqual(result['identityResourceId'], IDENTITY)
        self.assertEqual(result['identityScope'], 'https://database.windows.net/.default')
        self.assertNotIn('OldDb', result['settings'])
        self._assert_request(0, 'GET', 'staging')
        self._assert_request(1, 'PUT', 'staging')

    def test_webapp_egress_build_all_setting_roles_and_injection(self):
        connection = custom.add_egress_connection(
            self.cmd, 'MyRG', 'MyApp', 'api', 'http', 'credential', source='appsettings',
            host_setting='HOST', username_setting='USER', credential_setting='TOKEN',
            credential_header='Authorization', credential_format='Bearer {value}')
        self.assertEqual(connection['protocol'], 'Http')
        self.assertEqual(connection['source'], 'AppSettings')
        self.assertEqual(connection['credentialInjection'], {'header': 'Authorization', 'format': 'Bearer {value}'})
        self.assertEqual(connection['settings'], {
            'HOST': {'role': 'Host'}, 'USER': {'role': 'Username'}, 'TOKEN': {'role': 'Credential'}})
        self.assertEqual(self.config['enabled'], 'Disabled')

    def test_webapp_egress_show_and_remove_cli(self):
        connection = {'auth': 'ManagedIdentity', 'protocol': 'Tds', 'source': 'ConnectionStrings',
                      'settings': {'OrdersDb': {'role': 'Value'}}}
        self.config = {'enabled': 'Enabled', 'connections': {'Orders-Db': connection, 'keep': connection}}
        result = self._invoke(['webapp', 'config', 'egress', 'show', '-g', 'MyRG', '-n', 'MyApp'])
        self.assertEqual(result['properties']['connections'], self.config['connections'])
        result = self._invoke([
            'webapp', 'config', 'egress', 'connection', 'show', '-g', 'MyRG', '-n', 'MyApp',
            '--connection-name', 'orders-db', '--slot', 'staging'])
        self.assertEqual(result, connection)
        result = self._invoke([
            'webapp', 'config', 'egress', 'connection', 'remove', '-g', 'MyRG', '-n', 'MyApp',
            '--connection-name', 'orders-db', '--slot', 'staging'])
        self.assertIsNone(result)
        self.assertEqual(self.config, {'enabled': 'Enabled', 'connections': {'keep': connection}})
        self._assert_request(-2, 'GET', 'staging')
        self._assert_request(-1, 'PUT', 'staging')

    def test_webapp_egress_remove_last_connection(self):
        self.config['connections'] = {
            'cache': {'protocol': 'Redis', 'auth': 'Credential', 'settings': {'Redis': {'role': 'Value'}}},
        }
        self.assertIsNone(custom.remove_egress_connection(self.cmd, 'MyRG', 'MyApp', 'CACHE'))
        self.assertEqual(self.requests[-1]['body']['properties'], {'enabled': 'Disabled', 'connections': {}})

    def test_webapp_egress_missing_connection_does_not_write(self):
        for connections in [None, {}]:
            self.config = {'connections': connections}
            for handler in [custom.show_egress_connection, custom.remove_egress_connection]:
                with self.subTest(connections=connections, handler=handler.__name__):
                    with self.assertRaises(ResourceNotFoundError):
                        handler(self.cmd, 'MyRG', 'MyApp', 'missing')
        self.assertTrue(all(request['method'] == 'GET' for request in self.requests))

    def test_webapp_egress_add_to_empty_configuration(self):
        self.config = {}
        result = custom.add_egress_connection(
            self.cmd, 'MyRG', 'MyApp', 'cache', 'Redis', 'Credential', value_setting='Redis')
        self.assertEqual(result['source'], 'AppSettings')
        self.assertNotIn('enabled', self.requests[-1]['body']['properties'])

    def test_webapp_egress_invalid_definitions_do_not_call_service(self):
        valid = {'connection_name': 'cache', 'protocol': 'Redis', 'auth': 'Credential', 'value_setting': 'Redis'}
        invalid = [
            {'connection_name': ''}, {'connection_name': 'cache '}, {'connection_name': 'a' * 257},
            {'protocol': 'unknown'}, {'auth': 'unknown'}, {'source': 'unknown'}, {'value_setting': ''},
            {'host_setting': 'redis'}, {'value_setting': 'Redis '},
            {'credential_format': 'Bearer {value}'},
        ]
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises((InvalidArgumentValueError, RequiredArgumentMissingError)):
                    custom.add_egress_connection(self.cmd, 'MyRG', 'MyApp', **{**valid, **overrides})
        for field in ['connection_name', 'protocol', 'auth', 'value_setting']:
            with self.subTest(missing=field):
                definition = {**valid, field: None}
                with self.assertRaises(RequiredArgumentMissingError):
                    custom.add_egress_connection(self.cmd, 'MyRG', 'MyApp', **definition)
        self.assertEqual(self.requests, [])

    def test_webapp_egress_set_get_error_prevents_put(self):
        self.client.send_request.side_effect = HttpResponseError('Cannot read the existing configuration')
        for slot in [None, 'staging']:
            with self.subTest(slot=slot):
                self.client.send_request.reset_mock()
                with self.assertRaisesRegex(HttpResponseError, 'Cannot read the existing configuration'):
                    custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=False, slot=slot)
                self.assertEqual(self.client.send_request.call_count, 1)
                self.assertEqual(self.client.send_request.call_args.kwargs['request']['method'], 'GET')

    def test_webapp_egress_set_put_error_is_propagated(self):
        def fail_on_put(request, **_):
            if request['method'] == 'PUT':
                raise HttpResponseError('Cannot write the existing configuration')
            return self._send_request(request)

        self.client.send_request.side_effect = fail_on_put
        original = copy.deepcopy(self.config)
        for slot in [None, 'staging']:
            with self.subTest(slot=slot):
                self.client.send_request.reset_mock()
                with self.assertRaisesRegex(HttpResponseError, 'Cannot write the existing configuration'):
                    custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=True, slot=slot)
                self.assertEqual(
                    [call.kwargs['request']['method'] for call in self.client.send_request.call_args_list],
                    ['GET', 'PUT'])
                self.assertEqual(self.config, original)

    def test_webapp_egress_api_errors_are_not_swallowed(self):
        self.client.send_request.side_effect = HttpResponseError('Service rejected the configuration')
        with self.assertRaises(HttpResponseError):
            custom.add_egress_connection(
                self.cmd, 'MyRG', 'MyApp', 'cache', 'Redis', 'Credential', value_setting='Redis')
        self.assertEqual(self.client.send_request.call_count, 1)

    def test_webapp_egress_put_error_is_propagated(self):
        self.client.send_request.side_effect = [
            self._send_request(self._make_request('GET', '', {}, {}, None)),
            HttpResponseError('Service rejected the configuration'),
        ]
        with self.assertRaises(HttpResponseError):
            custom.add_egress_connection(
                self.cmd, 'MyRG', 'MyApp', 'cache', 'Redis', 'Credential', value_setting='Redis')
        self.assertEqual(self.client.send_request.call_count, 2)
        self.assertEqual(self.config['connections'], {})

    def test_webapp_egress_maximum_connection_name_length(self):
        connection_name = 'a' * 256
        custom.add_egress_connection(
            self.cmd, 'MyRG', 'MyApp', connection_name, 'Redis', 'Credential', value_setting='Redis')
        self.assertIn(connection_name, self.config['connections'])

    def test_webapp_egress_cli_rejects_missing_and_invalid_arguments(self):
        base = ['webapp', 'config', 'egress', 'connection', 'add', '-g', 'MyRG', '-n', 'MyApp']
        self._invoke(base + ['--connection-name', 'cache', '--protocol', 'Redis'], expected_code=2)
        self._invoke(base + ['--connection-name', 'cache', '--auth', 'Credential',
                             '--protocol', 'unknown'], expected_code=2)
        self._invoke([
            *base, '--connection-name', 'cache', '--protocol', 'Redis', '--auth', 'Credential',
        ], expected_code=1)
        self.assertEqual(self.requests, [])

    def test_webapp_egress_missing_connection_cli_exit_code(self):
        self._invoke([
            'webapp', 'config', 'egress', 'connection', 'show', '-g', 'MyRG', '-n', 'MyApp',
            '--connection-name', 'missing',
        ], expected_code=3)
        self.assertEqual(len(self.requests), 1)
        self._assert_request(0, 'GET')

    def test_webapp_egress_help_and_private_aaz_helpers(self):
        for suffix in [[], ['set'], ['show'], ['connection'], ['connection', 'add'],
                       ['connection', 'remove'], ['connection', 'show']]:
            with self.subTest(command=suffix):
                self._invoke(['webapp', 'config', 'egress'] + suffix + ['--help'])
        loader = AppserviceCommandsLoader(self.cli)
        commands = loader.load_command_table([])
        self.assertEqual(
            {command.split()[-1] for command in commands if command.startswith('webapp config egress connection ')},
            {'add', 'remove', 'show'})
        self.assertFalse(any(command.startswith('web site') for command in commands))
        self.assertEqual(self.requests, [])
