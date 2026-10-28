# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import requests
from azure.core.credentials import AccessToken
from azure.core.exceptions import HttpResponseError, ServiceRequestError, ServiceResponseError
from azure.core.pipeline.transport import RequestsTransport
from azure.mgmt.mysqlflexibleservers import MySQLManagementClient
from azure.cli.core.azclierror import InvalidArgumentValueError, ValidationError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.mysql import _client_factory, custom


class MysqlFlexibleServerRenameTest(unittest.TestCase):
    subscription = '00000000-0000-0000-0000-000000000000'
    endpoint = 'https://management.example.test'
    source_id = ('/subscriptions/' + subscription +
                 '/resourceGroups/testGroup/providers/Microsoft.DBforMySQL/flexibleServers/oldserver')
    destination_id = source_id.rsplit('/', 1)[0] + '/newserver'
    availability_path = ('/subscriptions/' + subscription +
                         '/providers/Microsoft.DBforMySQL/locations/eastus/checkNameAvailability')
    operation_path = ('/subscriptions/' + subscription +
                      '/providers/Microsoft.DBforMySQL/locations/eastus/azureAsyncOperation/rename-operation')
    api_version = '2025-12-30'
    availability_api_version = '2025-06-01-preview'

    def setUp(self):
        self.responses = []
        self.requests = []
        credential = MagicMock(spec=['get_token'])
        credential.get_token.return_value = AccessToken('test-token', 4102444800)
        self.session = MagicMock()
        self.session.request.side_effect = self._request
        self.clients = {}
        for api_version in (self.api_version, self.availability_api_version):
            client = MySQLManagementClient(
                credential, self.subscription, base_url=self.endpoint, api_version=api_version,
                transport=RequestsTransport(session=self.session), polling_interval=0, retry_total=0)
            self.clients[api_version] = client
            self.addCleanup(client.close)
        self.client = self.clients[self.api_version]
        factory = patch.object(
            _client_factory, 'get_mgmt_service_client',
            side_effect=lambda cli_ctx, client_type, **kwargs: self.clients[kwargs['api_version']])
        self.factory = factory.start()
        self.addCleanup(factory.stop)
        environment = patch.dict('os.environ', {_client_factory.RM_URI_OVERRIDE: ''})
        environment.start()
        self.addCleanup(environment.stop)
        self.cmd = SimpleNamespace(cli_ctx=MagicMock())

    def _request(self, method, url, **kwargs):
        self.assertTrue(self.responses, 'Unexpected HTTP request: {} {}'.format(method, url))
        expected_method, path, status, body, headers = self.responses.pop(0)
        parsed = urlsplit(url)
        self.assertEqual(expected_method, method)
        self.assertEqual(self.endpoint, '{}://{}'.format(parsed.scheme, parsed.netloc))
        self.assertEqual(path, parsed.path)
        api_version = self.availability_api_version if path == self.availability_path else self.api_version
        self.assertEqual([api_version], parse_qs(parsed.query)['api-version'])
        data = kwargs.get('data')
        self.requests.append((method, path, json.loads(data) if data else None))
        response = requests.Response()
        response.status_code = status
        response.url = url
        response.headers.update({'Content-Type': 'application/json', **headers})
        response._content = b'' if body is None else json.dumps(body).encode('utf-8')
        response.raw = io.BytesIO(response._content)
        response.request = requests.Request(method, url).prepare()
        return response

    def _queue(self, method, path, status=200, body=None, headers=None):
        self.responses.append((method, path, status, body, headers or {}))

    def _source(self):
        self._queue('GET', self.source_id, body={
            'id': self.source_id, 'name': 'oldserver', 'location': 'eastus',
            'properties': {'state': 'Ready'},
            'sku': {'name': 'Standard_D2ds_v4', 'tier': 'GeneralPurpose'},
            'tags': {'preserve': 'do-not-send-in-rename'}})

    def _available(self):
        self._queue('POST', self.availability_path, body={'nameAvailable': True})

    def _accepted(self):
        self._source()
        self._available()
        self._queue('PUT', self.destination_id, 202, headers={
            'Azure-AsyncOperation': self.endpoint + self.operation_path + '?api-version=' + self.api_version,
            'Retry-After': '0'})

    def _destination(self):
        return {
            'id': self.destination_id, 'name': 'newserver', 'location': 'eastus',
            'properties': {'state': 'Ready', 'fullyQualifiedDomainName': 'newserver.mysql.example.test'}}

    def _rename(self, new_name='newserver', no_wait=False):
        return custom.flexible_server_rename(
            self.cmd, self.client.servers, 'testGroup', 'oldserver', new_name, no_wait=no_wait)

    def _invoke(self, arguments):
        cli = DummyCli()
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stderr(stderr):
            try:
                exit_code = cli.invoke(
                    ['mysql', 'flexible-server', 'rename'] + arguments, out_file=stdout)
            except SystemExit as ex:
                exit_code = ex.code
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _assert_payload(self):
        puts = [entry for entry in self.requests if entry[0] == 'PUT']
        self.assertEqual([('PUT', self.destination_id, {
            'location': 'eastus',
            'properties': {'createMode': 'Rename', 'sourceServerResourceId': self.source_id}
        })], puts)

    def test_mysql_rename_returns_initial_response_without_polling(self):
        self._accepted()
        result = self._rename(new_name='NewServer')
        self.assertEqual({
            'statusCode': 202,
            'content': '',
            'azureAsyncOperation': self.endpoint + self.operation_path + '?api-version=' + self.api_version
        }, result)
        self._assert_payload()
        self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
        self.assertFalse(self.responses)

    def test_mysql_rename_no_wait_submits_once_without_polling(self):
        self._accepted()
        result = self._rename(no_wait=True)
        self.assertEqual(202, result['statusCode'])
        self.assertEqual('', result['content'])
        self.assertEqual(self.endpoint + self.operation_path + '?api-version=' + self.api_version,
                         result['azureAsyncOperation'])
        self._assert_payload()
        self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
        self.assertFalse(self.responses)

    def test_mysql_rename_preserves_initial_body_and_case_insensitive_header(self):
        body = {**self._destination(), 'operationDetails': {'status': 'InProgress'}}
        operation_url = self.endpoint + self.operation_path + '?api-version=' + self.api_version
        for status in (200, 201, 202):
            with self.subTest(status=status):
                self.requests.clear()
                self._source()
                self._available()
                self._queue('PUT', self.destination_id, status, body,
                            {'azure-asyncoperation': operation_url})
                result = self._rename()
                self.assertEqual({
                    'statusCode': status, 'content': json.dumps(body), 'azureAsyncOperation': operation_url
                }, result)
                self._assert_payload()
                self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
                self.assertFalse(self.responses)

    def test_mysql_rename_missing_operation_header_is_not_fabricated(self):
        for status in (200, 201, 202):
            with self.subTest(status=status):
                self.requests.clear()
                self._source()
                self._available()
                self._queue('PUT', self.destination_id, status)
                self.assertEqual({'statusCode': status, 'content': '', 'azureAsyncOperation': None},
                                 self._rename())
                self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
                self.assertFalse(self.responses)

    def test_mysql_rename_same_name_and_empty_name_are_rejected(self):
        for name in ('oldserver', 'OldServer', ''):
            with self.subTest(name=name), self.assertRaises(InvalidArgumentValueError):
                self._rename(new_name=name)
        self.assertFalse(self.requests)

    def test_mysql_rename_invalid_name_length_is_rejected(self):
        for name in ('ab', 'x' * 64):
            with self.subTest(name=name):
                self._source()
                with self.assertRaises(ValidationError):
                    self._rename(new_name=name)
        self.assertTrue(all(entry[0] == 'GET' for entry in self.requests))

    def test_mysql_rename_name_validation_uses_source_location(self):
        self._source()
        self._queue('POST', self.availability_path, body={
            'nameAvailable': False, 'reason': 'Invalid', 'message': 'Invalid server name.'})
        with self.assertRaisesRegex(ValidationError, 'Invalid server name'):
            self._rename(new_name='invalid_name')
        self.assertEqual({'name': 'invalid_name', 'type': 'Microsoft.DBforMySQL/flexibleServers'},
                         self.requests[-1][2])
        self.assertFalse(self.responses)

    def test_mysql_rename_unavailable_name_is_rejected(self):
        self._source()
        self._queue('POST', self.availability_path, body={
            'nameAvailable': False, 'reason': 'AlreadyExists', 'message': 'Target name is unavailable.'})
        with self.assertRaisesRegex(ValidationError, 'Target name is unavailable'):
            self._rename()
        self.assertFalse(any(entry[0] == 'PUT' for entry in self.requests))

    def test_mysql_rename_source_read_errors_never_submit(self):
        for status in (401, 403, 404):
            with self.subTest(status=status):
                self._queue('GET', self.source_id, status, {'error': {
                    'code': 'SourceReadFailed', 'message': 'Cannot read source.'}})
                with self.assertRaisesRegex(HttpResponseError, 'Cannot read source'):
                    self._rename()
        self.assertTrue(all(entry[0] == 'GET' for entry in self.requests))

    def test_mysql_rename_service_rejection_is_preserved(self):
        for status, code in ((409, 'Conflict'), (400, 'FeatureNotEnabled'),
                             (400, 'InvalidApiVersionParameter'), (403, 'AuthorizationFailed')):
            with self.subTest(code=code):
                self._source()
                self._available()
                self._queue('PUT', self.destination_id, status, {'error': {'code': code, 'message': code}})
                with self.assertRaisesRegex(HttpResponseError, code):
                    self._rename()
        self.assertEqual(4, len([entry for entry in self.requests if entry[0] == 'PUT']))

    def test_mysql_rename_submission_transport_failure_is_not_success(self):
        self._accepted()
        original_request = self.session.request.side_effect

        def request(method, url, **kwargs):
            response = original_request(method, url, **kwargs)
            if method == 'PUT':
                raise requests.exceptions.ConnectionError('Rename submission connection failed')
            return response

        self.session.request.side_effect = request
        with self.assertRaises(ServiceRequestError):
            self._rename()
        self._assert_payload()
        self.assertFalse(self.responses)

    def test_mysql_rename_submission_timeout_is_not_success(self):
        self._accepted()
        original_request = self.session.request.side_effect

        def request(method, url, **kwargs):
            response = original_request(method, url, **kwargs)
            if method == 'PUT':
                raise requests.exceptions.ReadTimeout('Rename submission timed out')
            return response

        self.session.request.side_effect = request
        with self.assertRaises(ServiceResponseError):
            self._rename()
        self._assert_payload()
        self.assertFalse(self.responses)

    def test_mysql_rename_uses_canonical_source_id(self):
        canonical_id = self.source_id.replace('testGroup', 'TESTGROUP')
        self._queue('GET', self.source_id, body={
            'id': canonical_id, 'name': 'oldserver', 'location': 'eastus'})
        self._available()
        self._queue('PUT', self.destination_id, body=self._destination())
        self._rename()
        self.assertEqual(canonical_id, self.requests[-1][2]['properties']['sourceServerResourceId'])

    def test_mysql_rename_cli_default_and_no_wait_return_initial_response(self):
        for no_wait in (False, True):
            with self.subTest(no_wait=no_wait):
                self.requests.clear()
                self._accepted()
                args = ['-g', 'testGroup', '-n', 'oldserver', '--new-name', 'newserver', '--yes']
                if no_wait:
                    args.append('--no-wait')
                code, stdout, stderr = self._invoke(args)
                self.assertEqual(0, code, stderr)
                self.assertEqual({
                    'statusCode': 202,
                    'content': '',
                    'azureAsyncOperation': self.endpoint + self.operation_path + '?api-version=' + self.api_version
                }, json.loads(stdout))
                self._assert_payload()
                self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
                self.assertFalse(self.responses)

    def test_mysql_rename_cli_ids(self):
        self._accepted()
        code, stdout, stderr = self._invoke(
            ['--ids', self.source_id, '--new-name', 'newserver', '--yes'])
        self.assertEqual(0, code, stderr)
        self.assertEqual(202, json.loads(stdout)['statusCode'])
        self.assertEqual(self.endpoint + self.operation_path + '?api-version=' + self.api_version,
                         json.loads(stdout)['azureAsyncOperation'])
        self._assert_payload()
        self.assertFalse(self.responses)
        self.assertEqual(self.subscription, self.factory.call_args.args[0].data['subscription_id'])

    def test_mysql_rename_cli_operation_url_can_be_queried(self):
        self._accepted()
        code, stdout, stderr = self._invoke([
            '-g', 'testGroup', '-n', 'oldserver', '--new-name', 'newserver', '--no-wait', '--yes',
            '--query', 'azureAsyncOperation', '--output', 'tsv'])
        self.assertEqual(0, code, stderr)
        self.assertEqual(self.endpoint + self.operation_path + '?api-version=' + self.api_version, stdout.strip())
        self.assertEqual(['GET', 'POST', 'PUT'], [entry[0] for entry in self.requests])
        self.assertFalse(self.responses)

    def test_mysql_rename_cli_rejects_wrong_resource_ids(self):
        for source_id in (
                '/invalid',
                self.source_id.replace('Microsoft.DBforMySQL', 'Microsoft.DBforPostgreSQL'),
                self.source_id.replace('flexibleServers', 'servers'),
                self.source_id + '/databases/mydb'):
            with self.subTest(source_id=source_id):
                code, _, _ = self._invoke(['--ids', source_id, '--new-name', 'newserver', '--yes'])
                self.assertNotEqual(0, code)
        self.assertFalse(self.requests)
        self.factory.assert_not_called()

    def test_mysql_rename_cli_requires_source_and_destination(self):
        for args in (['--new-name', 'newserver'], ['-g', 'testGroup', '-n', 'oldserver'],
                     ['-g', 'testGroup', '--new-name', 'newserver']):
            with self.subTest(args=args):
                code, _, _ = self._invoke(args + ['--yes'])
                self.assertNotEqual(0, code)
        self.assertFalse(self.requests)

    def test_mysql_rename_cli_rejects_multiple_sources_and_destination_id(self):
        code, _, _ = self._invoke(
            ['--ids', self.source_id, self.source_id.replace('oldserver', 'anotherserver'),
             '--new-name', 'newserver', '--yes'])
        self.assertNotEqual(0, code)
        self.factory.assert_not_called()

        self._source()
        code, _, _ = self._invoke(
            ['--ids', self.source_id, '--new-name',
             self.destination_id.replace('testGroup', 'anotherGroup'), '--yes'])
        self.assertNotEqual(0, code)
        self.assertFalse(any(entry[0] == 'PUT' for entry in self.requests))

    def test_mysql_rename_cli_confirmation_can_be_declined(self):
        with patch('azure.cli.core.commands.AzCliCommand._user_confirmed', return_value=False):
            code, _, _ = self._invoke(
                ['-g', 'testGroup', '-n', 'oldserver', '--new-name', 'newserver'])
        self.assertNotEqual(0, code)
        self.assertFalse(self.requests)

    def test_mysql_rename_cli_submission_failure_has_nonzero_exit(self):
        self._source()
        self._available()
        self._queue('PUT', self.destination_id, 409, body={
            'error': {'code': 'RenameFailed', 'message': 'Rename failed.'}})
        with self.assertLogs(level='ERROR') as logs:
            code, stdout, _ = self._invoke(
                ['-g', 'testGroup', '-n', 'oldserver', '--new-name', 'newserver', '--yes'])
        self.assertNotEqual(0, code)
        self.assertEqual('', stdout.strip())
        self.assertIn('RenameFailed', '\n'.join(logs.output))
        self.assertFalse(self.responses)

    def test_mysql_rename_factory_preserves_cloud_and_api_version(self):
        servers = _client_factory.cf_mysql_flexible_servers_rename(self.cmd.cli_ctx, None)
        self.assertIs(self.client.servers, servers)
        self.factory.assert_called_once_with(
            self.cmd.cli_ctx, MySQLManagementClient, api_version=self.api_version)

    def test_mysql_rename_factory_preserves_endpoint_and_subscription_overrides(self):
        subscription = '11111111-1111-1111-1111-111111111111'
        with patch.dict('os.environ', {
                _client_factory.RM_URI_OVERRIDE: self.endpoint,
                _client_factory.SUB_ID_OVERRIDE: subscription,
                _client_factory.AZURE_CLIENT_ID: ''}), \
                patch('azure.mgmt.mysqlflexibleservers.MySQLManagementClient',
                      return_value=self.client) as client_type:
            servers = _client_factory.cf_mysql_flexible_servers_rename(self.cmd.cli_ctx, None)
        self.assertIs(self.client.servers, servers)
        client_type.assert_called_once()
        self.assertEqual(subscription, client_type.call_args.kwargs['subscription_id'])
        self.assertEqual(self.endpoint, client_type.call_args.kwargs['base_url'])
        self.assertEqual(self.api_version, client_type.call_args.kwargs['api_version'])
        self.factory.assert_not_called()

    def test_mysql_rename_does_not_change_default_server_api_version(self):
        servers = _client_factory.cf_mysql_flexible_servers(self.cmd.cli_ctx, None)
        self.assertIs(self.clients[self.availability_api_version].servers, servers)
        self.factory.assert_called_once_with(
            self.cmd.cli_ctx, MySQLManagementClient, api_version=self.availability_api_version)


if __name__ == '__main__':
    unittest.main()
