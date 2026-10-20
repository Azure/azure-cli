# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, unquote, urlsplit

import requests

from azure.cli.core.azclierror import (AzureConnectionError, AzureResponseError, FileOperationError,
                                       InvalidArgumentValueError, ResourceNotFoundError)
from azure.cli.command_modules.appservice._active_backup_client import (
    ActiveBackupClient, API_VERSION, load_json, segment)


MODULE = 'azure.cli.command_modules.appservice._active_backup_client'


def response(status=200, payload=None, headers=None, content=None):
    result = requests.Response()
    result.status_code = status
    result.headers.update({'Content-Type': 'application/json'})
    result.headers.update(headers or {})
    result._content = (json.dumps(payload).encode('utf-8') if payload is not None else b'') if content is None else content
    result._content_consumed = True
    result.encoding = 'utf-8'
    return result


def cli_context():
    cli_ctx = MagicMock()
    cli_ctx.cloud.endpoints.resource_manager = 'https://management.example.test/'
    cli_ctx.cloud.endpoints.active_directory_resource_id = 'https://audience.example.test/'
    cli_ctx.data = {'command': 'webapp silo show'}
    return cli_ctx


class ActiveBackupClientTests(unittest.TestCase):

    def setUp(self):
        self.ctx = cli_context()
        self.client = ActiveBackupClient(self.ctx, 'group', 'primary', subscription='subscription')
        self.resource = self.client.resource('backup')

    def test_resource_identity_and_encoding(self):
        self.assertEqual(self.resource,
                         '/subscriptions/subscription/resourceGroups/group/providers/Microsoft.Web/sites/primary/silos/backup')
        client = ActiveBackupClient(self.ctx, 'a group', 'plan', 'serverfarms', subscription='sub')
        self.assertIn('/resourceGroups/a%20group/providers/Microsoft.Web/serverfarms/plan', client.resource())
        self.assertEqual(segment('x?#%'), 'x%3F%23%25')
        for value in ('', '..', '.', 'a/b', 'a\\b', 'a\nb', None):
            with self.subTest(value=value), self.assertRaises(InvalidArgumentValueError):
                segment(value)

    def test_api_version_query_and_origin(self):
        url = self.client.url(self.resource, {'enabled': False, 'count': 0, 'missing': None})
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query, {'api-version': [API_VERSION], 'enabled': ['false'], 'count': ['0']})
        supplied = self.client.url(self.resource + '?api-version=2026-01-01&x=1')
        self.assertEqual(parse_qs(urlsplit(supplied).query)['api-version'], ['2026-01-01'])
        for bad in ('https://evil.test/path', '//evil.test/path',
                    'http://management.example.test/path', 'https://user@management.example.test/path',
                    'https://management.example.test/path#fragment', 'https://management.example.test:0/path'):
            with self.subTest(address=bad), self.assertRaises(AzureResponseError):
                self.client.url(bad)

    def test_crud_operation_url_uses_async_status_mode_in_the_selected_cloud(self):
        self.ctx.cloud.endpoints.resource_manager = 'https://management.sovereign.example.test/'
        for resource_type in ('sites', 'serverfarms'):
            with self.subTest(resource_type=resource_type):
                client = ActiveBackupClient(
                    self.ctx, 'group', 'primary', resource_type, subscription='subscription')
                parsed = urlsplit(client.operation_url('back up', 'op?#%'))
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.netloc, 'management.sovereign.example.test')
                self.assertEqual(parsed.path, client.resource('back up') + '/operationresults/op%3F%23%25')
                self.assertEqual(parse_qs(parsed.query),
                                 {'api-version': [API_VERSION], 'azureAsyncOperation': ['1']})
                self.assertEqual(parsed.fragment, '')
        for operation_id in ('', '..', 'a/b', 'a\\b', None):
            with self.subTest(operation_id=operation_id), self.assertRaises(InvalidArgumentValueError):
                self.client.operation_url('backup', operation_id)

    def test_request_uses_cli_auth_cloud_and_no_redirects(self):
        result = response(payload={'properties': {'secret': 'not-logged'}})
        with patch(MODULE + '.Profile') as profile, patch(MODULE + '.requests.Session') as factory, \
                patch(MODULE + '.get_az_user_agent', return_value='test-cli'), \
                patch(MODULE + '.should_disable_connection_verify', return_value=False):
            profile.return_value.get_raw_token.return_value = (('Bearer', 'private-token', {}), 'sub', 'tenant')
            session = factory.return_value.__enter__.return_value
            session.request.return_value = result
            actual = self.client.request('PUT', self.resource, {'properties': {'enabled': False}})
            self.assertEqual(self.client.decode(actual), {'properties': {'secret': 'not-logged'}})
            call = session.request.call_args
            self.assertEqual(call.args[0], 'PUT')
            self.assertTrue(call.args[1].startswith(self.ctx.cloud.endpoints.resource_manager))
            self.assertFalse(call.kwargs['allow_redirects'])
            self.assertTrue(call.kwargs['verify'])
            self.assertEqual(call.kwargs['headers']['Authorization'], 'Bearer private-token')
            self.assertEqual(json.loads(call.kwargs['data']), {'properties': {'enabled': False}})
            profile.return_value.get_raw_token.assert_called_once_with(
                resource='https://audience.example.test/', subscription='subscription')

    def test_service_errors_preserve_code_and_request_id(self):
        for status, error_type in ((404, ResourceNotFoundError), (409, AzureResponseError), (500, AzureResponseError)):
            failed = response(status, {'error': {'code': 'SiloBusy', 'message': 'Try again.'}},
                              {'x-ms-request-id': 'request-one'})
            with self.subTest(status=status), patch(MODULE + '.Profile') as profile, \
                    patch(MODULE + '.requests.Session') as factory:
                profile.return_value.get_raw_token.return_value = (('Bearer', 'token', {}), None, None)
                factory.return_value.__enter__.return_value.request.return_value = failed
                with self.assertRaises(error_type) as caught:
                    self.client.request('GET', self.resource)
                self.assertIn('SiloBusy', str(caught.exception))
                self.assertIn('request-one', str(caught.exception))
                self.assertEqual(caught.exception.response.status_code, status)
        legacy = response(400, {'Code': 'LegacyFailure', 'Message': 'Legacy detail.'})
        with patch(MODULE + '.Profile') as profile, patch(MODULE + '.requests.Session') as factory:
            profile.return_value.get_raw_token.return_value = (('Bearer', 'token', {}), None, None)
            factory.return_value.__enter__.return_value.request.return_value = legacy
            with self.assertRaises(AzureResponseError) as caught:
                self.client.request('GET', self.resource)
            self.assertIn('LegacyFailure', str(caught.exception))
            self.assertIn('Legacy detail.', str(caught.exception))

    def test_cli_global_policy_headers_are_forwarded(self):
        policy = MagicMock()
        policy.on_request.side_effect = lambda request: request.http_request.headers.update(
            {'x-ms-policy-external-evaluations': 'policy-token'})
        with patch(MODULE + '.Profile') as profile, patch(MODULE + '.requests.Session') as factory, \
                patch(MODULE + '.get_custom_hook_policy', return_value=policy):
            profile.return_value.get_raw_token.return_value = (('Bearer', 'token', {}), None, None)
            session = factory.return_value.__enter__.return_value
            session.request.return_value = response(payload={'id': 'silo'})
            self.client.request('PUT', self.resource, {'properties': {}})
            self.assertEqual(session.request.call_args.kwargs['headers']['x-ms-policy-external-evaluations'],
                             'policy-token')
            policy.on_request.assert_called_once()

    def test_transport_error_does_not_echo_credentials(self):
        with patch(MODULE + '.Profile') as profile, patch(MODULE + '.requests.Session') as factory:
            profile.return_value.get_raw_token.return_value = (('Bearer', 'token', {}), None, None)
            factory.return_value.__enter__.return_value.request.side_effect = requests.ConnectionError('secret URL')
            with self.assertRaises(AzureConnectionError) as caught:
                self.client.request('GET', self.resource)
            self.assertNotIn('secret URL', str(caught.exception))

    def test_response_decoding(self):
        self.assertIsNone(self.client.decode(response(204)))
        self.assertEqual(self.client.decode(response(payload={'value': []})), {'value': []})
        self.assertEqual(self.client.decode(response(headers={'Content-Type': 'application/xml'},
                                                     content=b'<profile/>')), {'content': '<profile/>'})
        with self.assertRaises(AzureResponseError):
            self.client.decode(response(content=b'bad json'))
        with self.assertRaises(InvalidArgumentValueError):
            self.client.decode(response(headers={'Content-Type': 'application/zip'}, content=b'zip'))

    def test_collection_pagination_and_repeated_link(self):
        second = self.resource + '?page=2'
        with patch.object(self.client, 'request', side_effect=[
                response(payload={'value': [{'name': 'one'}], 'nextLink': second}),
                response(payload={'value': [{'name': 'two'}]})]) as request:
            self.assertEqual(self.client.list(self.resource), [{'name': 'one'}, {'name': 'two'}])
            self.assertEqual(request.call_count, 2)
        with patch.object(self.client, 'request', return_value=response(
                payload={'value': [], 'nextLink': self.resource})), self.assertRaises(AzureResponseError):
            self.client.list(self.resource)
        with patch.object(self.client, 'request', return_value=response(payload={'unexpected': []})), \
                self.assertRaises(AzureResponseError):
            self.client.list(self.resource)
        with patch.object(self.client, 'request', return_value=response(
                payload={'value': [], 'nextLink': 'https://evil.test/page'})) as request, \
                self.assertRaises(AzureResponseError):
            self.client.list(self.resource)
        request.assert_called_once()

    def test_synchronous_mutation_and_empty_delete(self):
        with patch.object(self.client, 'request', return_value=response(payload={'id': self.resource})):
            self.assertEqual(self.client.mutate('PUT', self.resource), {'id': self.resource})
            self.assertIsNone(self.client.mutate('DELETE', self.resource))
        with patch.object(self.client, 'request', return_value=response(204)):
            self.assertIsNone(self.client.mutate('DELETE', self.resource))

    def test_origin_resource_read_prefers_a_working_point_endpoint(self):
        origin = self.client.resource('origin')
        payload = {'id': origin, 'properties': {'outboundIpAddresses': 'fixture-ip', 'unknown': 1}}
        with patch.object(self.client, 'request', return_value=response(payload=payload)) as request, \
                patch.object(self.client, 'list') as listing, patch(MODULE + '.logger.warning') as warning:
            self.assertEqual(self.client.get_resource(origin), payload)
        request.assert_called_once_with('GET', origin)
        listing.assert_not_called()
        warning.assert_not_called()

    def test_origin_404_uses_the_exact_paginated_resource_and_warns_once(self):
        client = ActiveBackupClient(self.ctx, 'grüp', 'primary', subscription='subscription')
        origin = client.resource('origin')
        payload = {'id': unquote(origin).upper(), 'name': 'origin', 'type': 'Microsoft.Web/sites/silos',
                   'properties': {'endpointStatus': 'Enabled', 'unknown': {'preserved': True}}}
        foreign = dict(payload, id=origin.replace('/primary/', '/different/'))
        missing = ResourceNotFoundError('Original origin error; request-id.')
        with patch.object(client, 'request', side_effect=[
                missing, response(payload={'value': [foreign], 'nextLink': client.resource() + '?page=2'}),
                response(payload={'value': [payload]}), missing, response(payload={'value': [payload]})]) as request, \
                patch(MODULE + '.logger.warning') as warning:
            self.assertEqual(client.get_resource(origin), payload)
            self.assertEqual(client.get_resource(origin), payload)
        warning.assert_called_once()
        self.assertIn('Origin point GET returned HTTP 404', warning.call_args.args[0])
        self.assertEqual(request.call_count, 5)

    def test_origin_fallback_never_applies_to_other_reads_or_errors(self):
        plan = ActiveBackupClient(self.ctx, 'group', 'primary', 'serverfarms', subscription='subscription')
        cases = (
            (self.client, self.resource, ResourceNotFoundError('Missing replica')),
            (self.client, self.client.resource('origin') + '/config/web', ResourceNotFoundError('Missing config')),
            (plan, plan.resource('origin'), ResourceNotFoundError('Missing plan origin')),
            (self.client, self.client.resource('origin'), AzureResponseError('Forbidden')),
            (self.client, self.client.resource('origin'), AzureResponseError('Service failed')),
        )
        for client, path, error in cases:
            with self.subTest(path=path, error=str(error)), \
                    patch.object(client, 'request', side_effect=error), patch.object(client, 'list') as listing:
                with self.assertRaises(type(error)) as caught:
                    client.get_resource(path)
                self.assertIs(caught.exception, error)
                listing.assert_not_called()

    def test_origin_collection_missing_duplicate_or_invalid_results_remain_errors(self):
        origin = self.client.resource('origin')
        payload = {'id': origin, 'type': 'Microsoft.Web/sites/silos', 'properties': {'endpointStatus': 'Enabled'}}
        for entries, error_type in (
                ([], ResourceNotFoundError),
                ([dict(payload, id=self.resource)], ResourceNotFoundError),
                ([payload, dict(payload)], AzureResponseError),
                ([dict(payload, type='Microsoft.Web/sites')], AzureResponseError),
                ([dict(payload, properties=None)], AzureResponseError)):
            with self.subTest(entries=entries), \
                    patch.object(self.client, 'request', side_effect=ResourceNotFoundError('Original error')), \
                    patch.object(self.client, 'list', return_value=entries), \
                    patch(MODULE + '.logger.warning') as warning, self.assertRaises(error_type):
                self.client.get_resource(origin)
            warning.assert_not_called()

    def test_origin_collection_failures_are_not_hidden(self):
        origin = self.client.resource('origin')
        for error in (AzureResponseError('List forbidden'), ResourceNotFoundError('List missing')):
            with self.subTest(error=str(error)), \
                    patch.object(self.client, 'request', side_effect=ResourceNotFoundError('Point missing')), \
                    patch.object(self.client, 'list', side_effect=error):
                with self.assertRaises(type(error)) as caught:
                    self.client.get_resource(origin)
                self.assertIs(caught.exception, error)

    def test_no_wait_returns_receipt_without_polling(self):
        poll = self.resource + '/operationresults/operation'
        for header in ('Location', 'Azure-AsyncOperation'):
            with self.subTest(header=header), patch.object(self.client, 'request', return_value=response(
                    202, {'id': self.resource}, {header: poll})) as request:
                result = self.client.mutate('PUT', self.resource, no_wait=True)
                self.assertEqual(result['status'], 'Accepted')
                self.assertEqual(result['operationId'], 'operation')
                self.assertEqual(result['resourceId'], self.resource)
                request.assert_called_once()

    def test_async_status_header_takes_precedence_and_preserves_its_query(self):
        location = self.resource + '/operationresults/operation'
        poll = self.client.url(location, {'azureAsyncOperation': 1})
        initial = response(202, headers={
            'Location': location, 'Azure-AsyncOperation': poll, 'Retry-After': '0'})
        with patch.object(self.client, 'request', return_value=initial) as request:
            receipt = self.client.mutate('DELETE', self.resource, no_wait=True)
        self.assertEqual(receipt['operationUrl'], poll)
        request.assert_called_once()
        with patch.object(self.client, 'request', side_effect=[
                initial, response(payload={'status': 'Succeeded'})]) as request, patch(MODULE + '.time.sleep'):
            self.assertIsNone(self.client.mutate('DELETE', self.resource))
        self.assertEqual(request.call_args.args[:2], ('GET', poll))
        self.assertEqual(request.call_count, 2)

    def test_poll_status_body_and_final_resource(self):
        poll = self.resource + '/operationresults/operation'
        with patch.object(self.client, 'request', side_effect=[
                response(202, headers={'Location': poll, 'Retry-After': '0'}),
                response(payload={'status': 'InProgress'}, headers={'Retry-After': '0'}),
                response(payload={'status': 'Succeeded'}),
                response(payload={'id': self.resource, 'properties': {'revisionNumber': 7}})]) as request, \
                patch(MODULE + '.time.sleep'):
            result = self.client.mutate('PUT', self.resource)
            self.assertEqual(result['properties']['revisionNumber'], 7)
            self.assertEqual(request.call_args.args, ('GET', self.resource))
            self.assertEqual(request.call_count, 4)

    def test_operation_status_envelopes_are_not_resources(self):
        for identifier in (None, '', '/operations/op', 123):
            with self.subTest(identifier=identifier):
                result = self.client.operation(self.resource, response(payload={
                    'id': identifier, 'status': 'Succeeded', 'properties': None}))
                self.assertEqual(result['status'], 'Succeeded')
                self.assertNotIn('resource', result)
        resource = {'id': self.resource, 'properties': {'provisioningState': 'Succeeded'}}
        self.assertEqual(self.client.operation(self.resource, response(payload=resource))['resource'], resource)

    def test_async_writes_return_the_canonical_target_resource(self):
        poll = self.resource + '/operationresults/op?azureAsyncOperation=1'
        resource = {'id': self.resource, 'properties': {'revisionNumber': 8}}
        for method in ('PUT', 'PATCH'):
            for terminal in (
                    {'status': 'Succeeded'},
                    {'id': None, 'status': 'Succeeded', 'properties': None},
                    {'id': '/operations/op', 'status': 'Succeeded'},
                    {'id': self.resource, 'properties': {'revisionNumber': 7}}):
                with self.subTest(method=method, terminal=terminal), \
                        patch.object(self.client, 'request', side_effect=[
                            response(202, headers={'Azure-AsyncOperation': poll, 'Retry-After': '0'}),
                            response(payload=terminal), response(payload=resource)]) as request, \
                        patch(MODULE + '.time.sleep'):
                    self.assertEqual(self.client.mutate(method, self.resource), resource)
                    self.assertEqual(request.call_args.args, ('GET', self.resource))
                    self.assertEqual(request.call_count, 3)

    def test_final_resource_read_errors_remain_errors(self):
        poll = self.resource + '/operationresults/op'
        with patch.object(self.client, 'request', side_effect=[
                response(202, headers={'Location': poll, 'Retry-After': '0'}),
                response(payload={'id': None, 'status': 'Succeeded'}),
                ResourceNotFoundError('The target was not found.')]) as request, \
                patch(MODULE + '.time.sleep'), self.assertRaises(ResourceNotFoundError):
            self.client.mutate('PUT', self.resource)
        self.assertEqual(request.call_args.args, ('GET', self.resource))

    def test_delete_and_post_do_not_get_deleted_resource_or_action(self):
        poll = self.resource + '/operationresults/operation'
        for method in ('DELETE', 'POST'):
            with self.subTest(method=method), patch.object(self.client, 'request', side_effect=[
                    response(202, headers={'Location': poll, 'Retry-After': '0'}),
                    response(payload={'id': None, 'status': 'Succeeded'})]) as request, patch(MODULE + '.time.sleep'):
                self.assertIsNone(self.client.mutate(method, self.resource))
                self.assertEqual(request.call_count, 2)

    def test_http_200_terminal_failure_is_not_success(self):
        for status in ('Failed', 'Cancelled', 'TimedOut'):
            with self.subTest(status=status), self.assertRaises(AzureResponseError) as caught:
                self.client.operation(self.resource, response(payload={
                    'status': status, 'error': {'code': 'SiloFailed', 'message': 'Provisioning failed.'}}))
            self.assertIn('SiloFailed', str(caught.exception))

    def test_missing_or_cross_origin_poll_address_fails(self):
        for headers in ({}, {'Location': 'https://evil.test/poll'}):
            with self.subTest(headers=headers), \
                    patch.object(self.client, 'request', return_value=response(202, headers=headers)), \
                    self.assertRaises(AzureResponseError):
                self.client.mutate('PUT', self.resource)

    def test_timeout_does_not_cancel_service(self):
        with patch(MODULE + '.time.monotonic', side_effect=[0, 2]), \
                patch.object(self.client, 'request') as request, self.assertRaises(AzureResponseError):
            self.client.wait(self.resource, timeout=1)
        request.assert_not_called()
        for value in (0, -1):
            with self.subTest(timeout=value), self.assertRaises(InvalidArgumentValueError):
                self.client.wait(self.resource, timeout=value)
            with patch.object(self.client, 'request') as request, self.assertRaises(InvalidArgumentValueError):
                self.client.mutate('PUT', self.resource, timeout=value)
            request.assert_not_called()

    def test_poll_io_timeout_is_bounded_by_remaining_deadline(self):
        with patch(MODULE + '.time.monotonic', side_effect=[0, 0.25]), \
                patch.object(self.client, 'request', return_value=response(payload={'status': 'Succeeded'})) as request:
            self.client.wait(self.resource, timeout=1)
        self.assertEqual(request.call_args.kwargs['timeout'], 0.75)

    def test_http_date_retry_after(self):
        with patch(MODULE + '.datetime') as clock, patch(MODULE + '.time.sleep') as sleep, \
                patch.object(self.client, 'request', return_value=response(payload={'status': 'Succeeded'})):
            clock.now.return_value = datetime(2026, 10, 18, 23, 0, 0, tzinfo=timezone.utc)
            self.client.wait(self.resource, initial=response(
                202, headers={'Retry-After': 'Sun, 18 Oct 2026 23:00:05 GMT'}))
            sleep.assert_called_once_with(5)

    def test_only_transient_polling_reads_are_retried(self):
        for status in (429, 500, 502, 503, 504):
            error = AzureResponseError('Transient failure')
            error.response = response(status, headers={'Retry-After': '0'})
            with self.subTest(status=status), patch.object(self.client, 'request', side_effect=[
                    error, response(payload={'status': 'Succeeded'})]) as request, patch(MODULE + '.time.sleep'):
                self.assertEqual(self.client.wait(self.resource)['status'], 'Succeeded')
                self.assertEqual(request.call_count, 2)
        error = AzureResponseError('Bad input')
        error.response = response(400)
        with patch.object(self.client, 'request', side_effect=error) as request, self.assertRaises(AzureResponseError):
            self.client.wait(self.resource)
        request.assert_called_once()

    def test_operation_inspection_preserves_pending_and_success(self):
        running = self.client.operation(self.resource, response(202))
        succeeded = self.client.operation(self.resource, response())
        self.assertEqual(running['status'], 'InProgress')
        self.assertEqual(succeeded['status'], 'Succeeded')
        with self.assertRaises(AzureResponseError):
            self.client.operation(self.resource, response(payload={'status': 'Unexpected'}))

    def test_poll_retry_after_and_transient_missing_operation(self):
        initial = response(202, headers={'Retry-After': '0'})
        with patch.object(self.client, 'request', side_effect=[
                ResourceNotFoundError('Not yet visible'), response(payload={'status': 'Succeeded'})]) as request, \
                patch(MODULE + '.time.sleep'):
            self.assertEqual(self.client.wait(self.resource, initial=initial)['status'], 'Succeeded')
            self.assertEqual(request.call_count, 2)
        with patch.object(self.client, 'request', side_effect=ResourceNotFoundError('Missing')), \
                self.assertRaises(ResourceNotFoundError):
            self.client.wait(self.resource)
        for retry in ('malformed', 'nan', '-1', '0'):
            with self.subTest(header=retry), \
                    patch.object(self.client, 'request', return_value=response(payload={'status': 'Succeeded'})), \
                    patch(MODULE + '.time.sleep') as sleep:
                self.client.wait(self.resource, initial=response(202, headers={'Retry-After': retry}))
                self.assertGreaterEqual(sleep.call_args.args[0], 0.1)
                self.assertLessEqual(sleep.call_args.args[0], 5)

    def test_json_inputs(self):
        self.assertEqual(load_json('{"enabled":false}'), {'enabled': False})
        self.assertEqual(load_json('[1,2]', list), [1, 2])
        self.assertEqual(load_json('[1,2]', expected_type=None), [1, 2])
        for value in ('not json', '[1]', 'null'):
            with self.subTest(value=value), self.assertRaises(InvalidArgumentValueError):
                load_json(value)
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'body.json'
            filename.write_text('{"value":1}', encoding='utf-8')
            self.assertEqual(load_json('@' + str(filename)), {'value': 1})

    def test_byte_exact_download_and_overwrite_policy(self):
        payload = b'\x00\xffbinary\x00'
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'output.bin'
            with patch.object(self.client, '_response') as context:
                context.return_value.__enter__.return_value = response(content=payload)
                self.assertEqual(self.client.consume('GET', self.resource, str(destination)),
                                 {'file': str(destination)})
            self.assertEqual(destination.read_bytes(), payload)
            with self.assertRaises(FileOperationError):
                self.client.consume('GET', self.resource, str(destination))
            with patch.object(self.client, '_response') as context:
                context.return_value.__enter__.return_value = response(content=b'new')
                self.client.consume('GET', self.resource, str(destination), overwrite=True)
            self.assertEqual(destination.read_bytes(), b'new')
            self.assertEqual(list(Path(directory).iterdir()), [destination])

    def test_live_log_decoding_without_buffering(self):
        streamed = MagicMock()
        streamed.iter_content.return_value = iter([b'\xe2', b'\x82\xac', b'\xff'])
        with patch.object(self.client, '_response') as context, patch(MODULE + '.sys.stdout', new_callable=io.StringIO) as stdout:
            context.return_value.__enter__.return_value = streamed
            self.assertIsNone(self.client.consume('GET', self.resource, tail=True))
            self.assertEqual(stdout.getvalue(), '\u20ac\ufffd')
        streamed.json.assert_not_called()

    def test_interrupted_download_removes_only_its_own_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'output.bin'
            keep = Path(directory) / 'unrelated'
            keep.write_bytes(b'keep')
            streamed = MagicMock()
            streamed.iter_content.side_effect = KeyboardInterrupt
            with patch.object(self.client, '_response') as context, self.assertRaises(KeyboardInterrupt):
                context.return_value.__enter__.return_value = streamed
                self.client.consume('GET', self.resource, str(destination))
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(directory).iterdir()), [keep])
            self.assertEqual(keep.read_bytes(), b'keep')
            context.return_value.__exit__.assert_called_once()

    def test_download_permission_failure_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'output.bin'
            with patch.object(self.client, '_response') as context, \
                    patch(MODULE + '.tempfile.mkstemp', side_effect=PermissionError(13, 'Permission denied')), \
                    self.assertRaises(FileOperationError) as caught:
                context.return_value.__enter__.return_value = response(content=b'bytes')
                self.client.consume('GET', self.resource, str(destination))
            self.assertIn('Permission denied', str(caught.exception))
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
