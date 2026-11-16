# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy
import io
import logging
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
from knack.prompting import NoTTYException
from knack.util import CLIError


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
                        expected = {'connections': connections, 'enabled': enabled}
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
            for configuration in [None, {}, {'connections': None}, {'connections': {}}, {'enabled': None},
                                  {'enabled': 'Enabled'}, {'connections': {}, 'enabled': 'Disabled'}]:
                for enabled in [True, False]:
                    with self.subTest(slot=slot, configuration=configuration, enabled=enabled):
                        self.requests.clear()
                        self.config = copy.deepcopy(configuration)
                        with self.assertRaisesRegex(
                                InvalidArgumentValueError,
                                'Cannot update the egress enabled state without a connection.*'
                                'az webapp config egress connection add.*then retry'):
                            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=enabled, slot=slot)
                        self.assertEqual(len(self.requests), 1)
                        self._assert_request(0, 'GET', slot)
                        self.assertEqual(self.config, configuration)

    def test_webapp_egress_set_requires_enabled_cli(self):
        for slot in [None, 'staging']:
            for configuration in [None, {}, {'connections': {}}, {
                    'enabled': 'Enabled', 'connections': {
                        'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                  'settings': {'Redis': {'role': 'Value'}}},
                    }}]:
                with self.subTest(slot=slot, configuration=configuration):
                    self.requests.clear()
                    self.client.send_request.reset_mock()
                    self.config = copy.deepcopy(configuration)
                    with self.assertLogs(level='ERROR') as errors:
                        self._invoke(
                            ['webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp'] +
                            (['--slot', slot] if slot else []), expected_code=2)
                    self.assertTrue(any('--enabled' in entry for entry in errors.output))
                    self.client.send_request.assert_not_called()
                    self.assertEqual(self.requests, [])
                    self.assertEqual(self.config, configuration)

    def test_webapp_egress_set_requires_enabled_handler(self):
        for slot in [None, 'staging']:
            for enabled_arguments in [{}, {'enabled': None}]:
                for configuration in [None, {}, {'connections': {}}, {
                        'enabled': 'Disabled', 'connections': {
                            'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                      'settings': {'Redis': {'role': 'Value'}}},
                        }}]:
                    with self.subTest(slot=slot, enabled_arguments=enabled_arguments, configuration=configuration):
                        self.requests.clear()
                        self.client.send_request.reset_mock()
                        self.config = copy.deepcopy(configuration)
                        with self.assertRaisesRegex(
                                RequiredArgumentMissingError, 'Specify --enabled true or --enabled false'):
                            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', slot=slot, **enabled_arguments)
                        self.client.send_request.assert_not_called()
                        self.assertEqual(self.requests, [])
                        self.assertEqual(self.config, configuration)

    def test_webapp_egress_set_cannot_update_state_without_connections_cli(self):
        error = (
            'Cannot update the egress enabled state without a connection. Add a connection using '
            '`az webapp config egress connection add`, then retry.')
        for slot in [None, 'staging']:
            for configuration in [None, {}, {'connections': None}, {'connections': {}}, {'enabled': None},
                                  {'enabled': 'Enabled'}, {'connections': {}, 'enabled': 'Disabled'}]:
                for arguments in [['--enabled', 'true'], ['--enabled', 'TrUe'],
                                  ['--enabled', 'false'], ['--enabled', 'FaLsE'], ['--enabled']]:
                    with self.subTest(slot=slot, configuration=configuration, arguments=arguments):
                        self.requests.clear()
                        self.config = copy.deepcopy(configuration)
                        with self.assertLogs(level='ERROR') as logs:
                            self._invoke(
                                ['webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp'] +
                                arguments + (['--slot', slot] if slot else []), expected_code=1)
                        self.assertTrue(any(error in entry for entry in logs.output))
                        self.assertEqual(len(self.requests), 1)
                        self._assert_request(0, 'GET', slot)
                        self.assertEqual(self.config, configuration)

    def test_webapp_egress_set_missing_properties(self):
        def respond_without_properties(request, **kwargs):
            response = self._send_request(request, **kwargs)
            if request['method'] == 'GET':
                del response.context[ContentDecodePolicy.CONTEXT_NAME]['properties']
            return response

        self.client.send_request.side_effect = respond_without_properties
        for slot in [None, 'staging']:
            for enabled in [True, False, None]:
                with self.subTest(slot=slot, enabled=enabled):
                    self.requests.clear()
                    self.config = {}
                    if enabled is not None:
                        with self.assertRaisesRegex(
                                InvalidArgumentValueError,
                                'Cannot update the egress enabled state without a connection'):
                            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=enabled, slot=slot)
                        self.assertEqual(len(self.requests), 1)
                        self.assertEqual(self.config, {})
                    else:
                        with self.assertRaisesRegex(
                                RequiredArgumentMissingError, 'Specify --enabled true or --enabled false'):
                            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled=None, slot=slot)
                        self.assertEqual(self.requests, [])
                    if enabled is not None:
                        self._assert_request(0, 'GET', slot)

        for slot in [None, 'staging']:
            for arguments in [['--enabled', 'true'], ['--enabled', 'false'], ['--enabled']]:
                with self.subTest(slot=slot, arguments=arguments):
                    self.requests.clear()
                    self.config = {}
                    with self.assertLogs(level='ERROR') as logs:
                        self._invoke(
                            ['webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp'] +
                            arguments + (['--slot', slot] if slot else []), expected_code=1)
                    self.assertTrue(any(
                        'Cannot update the egress enabled state without a connection' in entry
                        for entry in logs.output))
                    self.assertEqual(len(self.requests), 1)
                    self._assert_request(0, 'GET', slot)
                    self.assertEqual(self.config, {})

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
                    expected_enabled = 'Disabled' if enabled is None else enabled
                    original['enabled'] = expected_enabled
                    self.assertEqual(self.requests[1]['body']['properties']['enabled'], expected_enabled)
                    self.assertEqual(self.config['connections']['keep'], original['connections']['keep'])
                    custom.remove_egress_connection(self.cmd, 'MyRG', 'MyApp', 'CACHE', slot=slot)
                    self.assertEqual(self.requests[3]['body']['properties']['enabled'], expected_enabled)
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
        for slot in [None, 'staging']:
            for state in [{}, {'enabled': None}, {'enabled': 'Enabled'}, {'enabled': 'Disabled'}]:
                for use_cli in [False, True]:
                    with self.subTest(slot=slot, state=state, use_cli=use_cli):
                        self.requests.clear()
                        self.config = {
                            **state, 'connections': {
                                'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                          'settings': {'Redis': {'role': 'Value'}}},
                            },
                        }
                        if use_cli:
                            result = self._invoke(
                                ['webapp', 'config', 'egress', 'connection', 'remove', '-g', 'MyRG', '-n', 'MyApp',
                                 '--connection-name', 'CACHE', '--yes'] + (['--slot', slot] if slot else []))
                        else:
                            result = custom.remove_egress_connection(
                                self.cmd, 'MyRG', 'MyApp', 'CACHE', slot=slot, yes=True)
                        self.assertIsNone(result)
                        self.assertEqual(len(self.requests), 2)
                        self._assert_request(0, 'GET', slot)
                        self._assert_request(1, 'PUT', slot)
                        self.assertEqual(self.requests[1]['body'], {'properties': {}})
                        self.assertEqual(self.config, {})
                        shown = custom.show_egress_config(self.cmd, 'MyRG', 'MyApp', slot=slot)
                        self.assertEqual(shown['properties'], {})
                        self._assert_request(2, 'GET', slot)

    def test_webapp_egress_remove_last_connection_confirmed(self):
        for slot in [None, 'staging']:
            for use_cli in [False, True]:
                with self.subTest(slot=slot, use_cli=use_cli):
                    self.requests.clear()
                    self.config = {'enabled': 'Enabled', 'connections': {
                        'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                  'settings': {'Redis': {'role': 'Value'}}},
                    }}
                    with mock.patch('knack.prompting.prompt_y_n', return_value=True) as prompt, \
                            self.assertLogs(custom.logger, level='WARNING') as warnings:
                        if use_cli:
                            result = self._invoke(
                                ['webapp', 'config', 'egress', 'connection', 'remove', '-g', 'MyRG', '-n', 'MyApp',
                                 '--connection-name', 'CACHE'] + (['--slot', slot] if slot else []))
                        else:
                            result = custom.remove_egress_connection(self.cmd, 'MyRG', 'MyApp', 'CACHE', slot=slot)
                    prompt.assert_called_once_with("Are you sure you want to remove the last egress connection?")
                    self.assertTrue(any(
                        'Removing the last connection clears the entire egress configuration, '
                        'including its enabled state.'
                        in entry for entry in warnings.output))
                    self.assertIsNone(result)
                    self.assertEqual(len(self.requests), 2)
                    self._assert_request(0, 'GET', slot)
                    self._assert_request(1, 'PUT', slot)
                    self.assertEqual(self.requests[1]['body'], {'properties': {}})

    def test_webapp_egress_remove_last_connection_cancelled_or_no_tty(self):
        for slot in [None, 'staging']:
            for use_cli in [False, True]:
                for no_tty in [False, True]:
                    with self.subTest(slot=slot, use_cli=use_cli, no_tty=no_tty):
                        self.requests.clear()
                        self.config = {'enabled': 'Disabled', 'connections': {
                            'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                      'settings': {'Redis': {'role': 'Value'}}},
                        }}
                        before = copy.deepcopy(self.config)
                        message = 'Unable to prompt for confirmation as no tty available. Use --yes.' if no_tty else \
                            'Operation cancelled.'
                        with mock.patch('knack.prompting.prompt_y_n', return_value=False,
                                        side_effect=NoTTYException() if no_tty else None) as prompt, \
                                self.assertLogs(custom.logger, level='WARNING') as warnings:
                            if use_cli:
                                with self.assertLogs(level='ERROR') as errors:
                                    self._invoke(
                                        ['webapp', 'config', 'egress', 'connection', 'remove',
                                         '-g', 'MyRG', '-n', 'MyApp', '--connection-name', 'cache'] +
                                        (['--slot', slot] if slot else []), expected_code=1)
                                self.assertTrue(any(message in entry for entry in errors.output))
                            else:
                                with self.assertRaises(CLIError) as caught:
                                    custom.remove_egress_connection(self.cmd, 'MyRG', 'MyApp', 'cache', slot=slot)
                                self.assertEqual(str(caught.exception), message)
                        prompt.assert_called_once()
                        self.assertTrue(any('including its enabled state' in entry for entry in warnings.output))
                        self.assertEqual(len(self.requests), 1)
                        self._assert_request(0, 'GET', slot)
                        self.assertEqual(self.config, before)

    def test_webapp_egress_remove_last_connection_yes_warning_on_stderr(self):
        warning = 'Removing the last connection clears the entire egress configuration, including its enabled state.'
        for slot in [None, 'staging']:
            for option in ['--yes', '-y']:
                with self.subTest(slot=slot, option=option):
                    self.requests.clear()
                    self.config = {'enabled': 'Enabled', 'connections': {
                        'cache': {'protocol': 'Redis', 'auth': 'Credential',
                                  'settings': {'Redis': {'role': 'Value'}}},
                    }}
                    stdout, stderr = io.StringIO(), io.StringIO()
                    handler = logging.StreamHandler(stderr)
                    with mock.patch('knack.prompting.prompt_y_n') as prompt, \
                            mock.patch.object(custom.logger, 'handlers', [handler]), \
                            mock.patch.object(custom.logger, 'propagate', False), \
                            mock.patch.object(custom.logger, 'level', logging.WARNING):
                        with redirect_stdout(stdout):
                            result = self._invoke(
                                ['webapp', 'config', 'egress', 'connection', 'remove',
                                 '-g', 'MyRG', '-n', 'MyApp', '--connection-name', 'cache', option] +
                                (['--slot', slot] if slot else []))
                    prompt.assert_not_called()
                    self.assertIsNone(result)
                    self.assertIn(warning, stderr.getvalue())
                    self.assertNotIn(warning, stdout.getvalue())
                    self.assertEqual(len(self.requests), 2)
                    self._assert_request(0, 'GET', slot)
                    self._assert_request(1, 'PUT', slot)
                    self.assertEqual(self.requests[1]['body'], {'properties': {}})

    def test_webapp_egress_remove_non_last_does_not_warn_or_prompt(self):
        for slot in [None, 'staging']:
            for option in [[], ['--yes'], ['-y']]:
                with self.subTest(slot=slot, option=option):
                    self.requests.clear()
                    connection = {'protocol': 'Redis', 'auth': 'Credential',
                                  'settings': {'Redis': {'role': 'Value'}}}
                    self.config = {'enabled': 'Enabled', 'connections': {'cache': connection, 'keep': connection}}
                    with mock.patch('knack.prompting.prompt_y_n') as prompt, \
                            mock.patch.object(custom.logger, 'warning') as warning:
                        result = self._invoke(
                            ['webapp', 'config', 'egress', 'connection', 'remove',
                             '-g', 'MyRG', '-n', 'MyApp', '--connection-name', 'CACHE'] +
                            option + (['--slot', slot] if slot else []))
                    prompt.assert_not_called()
                    warning.assert_not_called()
                    self.assertIsNone(result)
                    self.assertEqual(self.config, {'enabled': 'Enabled', 'connections': {'keep': connection}})
                    self.assertEqual(len(self.requests), 2)
                    self._assert_request(0, 'GET', slot)
                    self._assert_request(1, 'PUT', slot)

    def test_webapp_egress_remove_missing_does_not_warn_or_prompt(self):
        for slot in [None, 'staging']:
            for yes in [False, True]:
                with self.subTest(slot=slot, yes=yes):
                    self.requests.clear()
                    self.config = {'enabled': 'Disabled', 'connections': {
                        'keep': {'protocol': 'Redis', 'auth': 'Credential',
                                 'settings': {'Redis': {'role': 'Value'}}},
                    }}
                    before = copy.deepcopy(self.config)
                    with mock.patch('knack.prompting.prompt_y_n') as prompt, \
                            mock.patch.object(custom.logger, 'warning') as warning:
                        with self.assertRaises(ResourceNotFoundError):
                            custom.remove_egress_connection(
                                self.cmd, 'MyRG', 'MyApp', 'missing', slot=slot, yes=yes)
                    prompt.assert_not_called()
                    warning.assert_not_called()
                    self.assertEqual(self.config, before)
                    self.assertEqual(len(self.requests), 1)
                    self._assert_request(0, 'GET', slot)

    def test_webapp_egress_missing_connection_does_not_write(self):
        for connections in [None, {}]:
            self.config = {'connections': connections}
            for handler in [custom.show_egress_connection, custom.remove_egress_connection]:
                with self.subTest(connections=connections, handler=handler.__name__):
                    with self.assertRaises(ResourceNotFoundError):
                        handler(self.cmd, 'MyRG', 'MyApp', 'missing')
        self.assertTrue(all(request['method'] == 'GET' for request in self.requests))

    def test_webapp_egress_add_to_empty_configuration(self):
        for slot in [None, 'staging']:
            for configuration in [None, {}, {'connections': None}, {'connections': {}}, {'enabled': None},
                                  {'connections': {}, 'enabled': None}]:
                with self.subTest(slot=slot, configuration=configuration):
                    self.requests.clear()
                    self.config = copy.deepcopy(configuration)
                    result = custom.add_egress_connection(
                        self.cmd, 'MyRG', 'MyApp', 'cache', 'Redis', 'Credential', value_setting='Redis', slot=slot)
                    self.assertEqual(result['source'], 'AppSettings')
                    self.assertEqual(len(self.requests), 2)
                    self._assert_request(0, 'GET', slot)
                    self._assert_request(1, 'PUT', slot)
                    self.assertEqual(
                        self.requests[1]['body']['properties'],
                        {'connections': {'cache': result}, 'enabled': 'Disabled'})
                    shown = custom.show_egress_config(self.cmd, 'MyRG', 'MyApp', slot=slot)
                    self.assertEqual(shown['properties'], {'connections': {'cache': result}, 'enabled': 'Disabled'})
                    self._assert_request(2, 'GET', slot)

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
        self.config['connections']['cache'] = {
            'protocol': 'Redis', 'auth': 'Credential', 'source': 'AppSettings',
            'settings': {'Redis': {'role': 'Value'}},
        }
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
