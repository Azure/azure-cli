# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
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
from azure.cli.command_modules.appservice.actions import EgressConnectionAddAction
from azure.cli.command_modules.appservice import custom


SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'
IDENTITY = (
    '/subscriptions/' + SUBSCRIPTION +
    '/resourceGroups/MyRG/providers/Microsoft.ManagedIdentity/userAssignedIdentities/MyIdentity'
)


class EgressActionTests(unittest.TestCase):

    def setUp(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('--connection', dest='connections', action=EgressConnectionAddAction, nargs='+')

    def test_webapp_egress_repeated_connections(self):
        args = self.parser.parse_args([
            '--connection', 'name=cache', 'protocol=Redis', 'auth=Credential',
            'host-setting=REDIS_HOST', 'credential-setting=REDIS_PASSWORD',
            '--connection', 'name=orders-db', 'protocol=Tds', 'auth=ManagedIdentity',
            'source=ConnectionStrings', 'value-setting=OrdersDb',
        ])
        self.assertEqual(args.connections, [
            {'connection_name': 'cache', 'protocol': 'Redis', 'auth': 'Credential',
             'host_setting': 'REDIS_HOST', 'credential_setting': 'REDIS_PASSWORD'},
            {'connection_name': 'orders-db', 'protocol': 'Tds', 'auth': 'ManagedIdentity',
             'source': 'ConnectionStrings', 'value_setting': 'OrdersDb'},
        ])
        self.assertIsNone(self.parser.parse_args([]).connections)

    def test_webapp_egress_rejects_malformed_entries(self):
        for entries in [
                ['name'], ['unknown=hidden-value'], ['name='], ['=hidden-value'],
                ['name=cache', 'name=orders'], ['protocol=Redis', 'protocol=Tds']]:
            with self.subTest(entries=entries):
                with self.assertRaises(InvalidArgumentValueError) as caught:
                    self.parser.parse_args(['--connection'] + entries)
                self.assertNotIn('hidden-value', str(caught.exception))

    def test_webapp_egress_format_preserves_equals(self):
        args = self.parser.parse_args(['--connection', 'name=api', 'credential-format=token={value}'])
        self.assertEqual(args.connections[0]['credential_format'], 'token={value}')


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

    def test_webapp_egress_set_cli_examples(self):
        result = self._invoke([
            'webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp', '--enabled', 'Enabled',
            '--connection', 'name=cache', 'protocol=Redis', 'auth=Credential',
            'host-setting=REDIS_HOST', 'credential-setting=REDIS_PASSWORD',
            '--connection', 'name=orders-db', 'protocol=Tds', 'auth=ManagedIdentity',
            'source=ConnectionStrings', 'value-setting=OrdersDb',
        ])
        expected = {
            'enabled': 'Enabled',
            'connections': {
                'cache': {'protocol': 'Redis', 'auth': 'Credential', 'source': 'AppSettings',
                          'settings': {'REDIS_HOST': {'role': 'Host'}, 'REDIS_PASSWORD': {'role': 'Credential'}}},
                'orders-db': {'protocol': 'Tds', 'auth': 'ManagedIdentity', 'source': 'ConnectionStrings',
                              'settings': {'OrdersDb': {'role': 'Value'}}},
            },
        }
        self.assertEqual(self.config, expected)
        self.assertEqual(result['properties'], expected)
        self.assertEqual(len(self.requests), 1)
        self._assert_request(0, 'PUT')

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

    def test_webapp_egress_set_replaces_and_clears(self):
        self.config['connections'] = {'obsolete': {}}
        custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', connections=[
            {'connection_name': 'cache', 'protocol': 'Redis', 'auth': 'Credential', 'value_setting': 'Redis'},
        ])
        self.assertEqual(list(self.config['connections']), ['cache'])
        custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled='Disabled', slot='staging')
        self.assertEqual(self.requests[-1]['body'], {'properties': {'connections': {}, 'enabled': 'Disabled'}})
        self._assert_request(-1, 'PUT', 'staging')

    def test_webapp_egress_build_all_setting_roles_and_injection(self):
        result = custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled='enabled', connections=[
            {'connection_name': 'api', 'protocol': 'http', 'auth': 'credential', 'source': 'appsettings',
             'host_setting': 'HOST', 'username_setting': 'USER', 'credential_setting': 'TOKEN',
             'credential_header': 'Authorization', 'credential_format': 'Bearer {value}'},
        ])
        connection = result['properties']['connections']['api']
        self.assertEqual(connection['protocol'], 'Http')
        self.assertEqual(connection['source'], 'AppSettings')
        self.assertEqual(connection['credentialInjection'], {'header': 'Authorization', 'format': 'Bearer {value}'})
        self.assertEqual(connection['settings'], {
            'HOST': {'role': 'Host'}, 'USER': {'role': 'Username'}, 'TOKEN': {'role': 'Credential'}})
        self.assertEqual(result['properties']['enabled'], 'Enabled')

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
                    custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', connections=[{**valid, **overrides}])
        for field in ['connection_name', 'protocol', 'auth', 'value_setting']:
            with self.subTest(missing=field):
                definition = {key: value for key, value in valid.items() if key != field}
                with self.assertRaises(RequiredArgumentMissingError):
                    custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', connections=[definition])
        with self.assertRaises(InvalidArgumentValueError):
            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', connections=[
                valid, {**valid, 'connection_name': 'CACHE'}])
        with self.assertRaises(InvalidArgumentValueError):
            custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', enabled='true')
        self.assertEqual(self.requests, [])

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
        custom.set_egress_config(self.cmd, 'MyRG', 'MyApp', connections=[
            {'connection_name': connection_name, 'protocol': 'Redis', 'auth': 'Credential',
             'value_setting': 'Redis'},
        ])
        self.assertIn(connection_name, self.config['connections'])

    def test_webapp_egress_cli_rejects_missing_and_invalid_arguments(self):
        base = ['webapp', 'config', 'egress', 'connection', 'add', '-g', 'MyRG', '-n', 'MyApp']
        self._invoke(base + ['--connection-name', 'cache', '--protocol', 'Redis'], expected_code=2)
        self._invoke(base + ['--connection-name', 'cache', '--auth', 'Credential',
                             '--protocol', 'unknown'], expected_code=2)
        self._invoke([
            'webapp', 'config', 'egress', 'set', '-g', 'MyRG', '-n', 'MyApp',
            '--connection', 'name=cache', 'protocol=Redis', 'auth=Credential',
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
