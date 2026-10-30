# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import io
import json
import shlex
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch, sentinel
from urllib.parse import parse_qs, urlparse

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.core.pipeline import PipelineContext, PipelineResponse
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.core.utils import CaseInsensitiveDict
from azure.cli.core import get_default_cli
from azure.cli.core.aaz import AAZCommand, AAZUndefined
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.aaz._poller import AAZBasePolling, AAZNoPolling
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.storage import StorageCommandsLoader
from azure.cli.command_modules.storage.aaz.latest.storage.account import blob_access_point_configuration as bap
from azure.cli.command_modules.storage.aaz.latest.storage import context_cache as cache
from azure.cli.command_modules.storage.aaz.latest.storage.context_cache import container
from azure.cli.command_modules.storage.aaz.latest.storage.context_cache import identity


SUBSCRIPTION = '00000000-0000-0000-0000-000000000000'
IDENTITY = (
    '/subscriptions/' + SUBSCRIPTION + '/resourceGroups/myrg/providers/'
    'Microsoft.ManagedIdentity/userAssignedIdentities/myidentity')
SOURCE_TYPES = {
    'net_app_ontap': 'NetAppOntap',
    'azure_net_app_files': 'AzureNetAppFiles',
    'dell_one_fs': 'DellOneFs',
    'qumulo': 'Qumulo',
    'commvault': 'Commvault',
    'nasuni': 'Nasuni',
    's3_compatible': 'S3Compatible'
}


# pylint: disable=protected-access
class StorageResourceAazTest(unittest.TestCase):

    def setUp(self):
        self.cli_ctx = get_default_cli()

    def _operation(self, command_type, operation_type, **kwargs):
        schema = command_type.get_arguments_schema()
        defaults = {
            'resource_group': 'myrg', 'account_name': 'mystorage', 'location': 'eastus',
            'blob_access_point_configuration_name': 'myaccesspoint',
            'context_cache_name': 'mycache', 'context_cache_container_name': 'mycontainer',
            'name': 'mycache'
        }
        args = {name: value for name, value in defaults.items() if name in schema._fields}
        for name, field in schema._fields.items():
            if field._default != AAZUndefined:
                args.setdefault(name, field._default)
        for name in kwargs:
            self.assertIn(name, schema._fields)
        args.update(kwargs)
        args['subscription'] = SUBSCRIPTION
        ctx = AAZCommandCtx(self.cli_ctx, schema, args)
        ctx.format_args()
        with patch.object(ctx, 'get_login_credential', return_value=Mock()):
            operation = operation_type(ctx)
        self.addCleanup(operation.client.close)
        return operation

    def _request_body(self, operation):
        with patch.object(operation.client, 'send_request') as send_request:
            request = operation.make_request()
            send_request.assert_not_called()
        self.assertEqual({'api-version': ['2026-09-01']}, parse_qs(urlparse(request.url).query))
        return request.method, json.loads(request.body) if request.body else None

    @staticmethod
    def _source(source_type='s3_compatible', private_link=False):
        connection = {'endpoint': {'endpoint': 'https://s3.example.com'}}
        if private_link:
            connection = {
                'private_link': {
                    'endpoint': 'https://s3.example.com',
                    'private_link_id_type': 'ResourceId',
                    'private_link_id': (
                        '/subscriptions/' + SUBSCRIPTION + '/resourceGroups/myrg/providers/'
                        'Microsoft.Network/privateLinkServices/myservice'),
                    'private_link_location': 'eastus',
                    'request_message': 'Connect storage'
                }
            }
        return {
            source_type: {
                'connection': connection,
                'auth': {'access_key': {'access_key_id': 'fake-id', 'secret_access_key': 'fake-secret'}}
            }
        }

    def _cli_request(self, command_type, operation_type, arguments):
        requests = []

        def capture(command, command_args):
            AAZCommand._handler(command, command_args)
            with patch.object(command.ctx, 'get_login_credential', return_value=Mock()):
                operation = operation_type(command.ctx)
            self.addCleanup(operation.client.close)
            with patch.object(operation.client, 'send_request') as send_request:
                requests.append(operation.make_request())
                send_request.assert_not_called()

        output = io.StringIO()
        with patch.object(command_type, '_handler', capture), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                result = self.cli_ctx.invoke(
                    command_type.AZ_NAME.split() + arguments + ['--subscription', SUBSCRIPTION], out_file=output)
            except SystemExit as error:
                result = error.code
        return result, requests, output.getvalue()

    def test_all_remaining_commands_are_registered_and_schemas_build(self):
        self.cli_ctx.invocation = self.cli_ctx.invocation_cls(cli_ctx=self.cli_ctx)
        loader = StorageCommandsLoader(self.cli_ctx)
        commands = loader.load_command_table(None)
        expected = {
            'storage account blob-access-point-configuration': (
                'create', 'update', 'delete', 'show', 'list',
                'test-existing-connection', 'test-proposed-connection', 'wait'),
            'storage context-cache': ('create', 'update', 'delete', 'show', 'list', 'check-name', 'wait'),
            'storage context-cache container': ('create', 'update', 'delete', 'show', 'list', 'wait'),
            'storage context-cache identity': ('assign', 'remove', 'show')
        }
        for excluded in ('storage account connector', 'storage account data-share'):
            self.assertFalse([name for name in commands if name == excluded or name.startswith(excluded + ' ')])
        for group, operations in expected.items():
            for operation in operations:
                name = group + ' ' + operation
                with self.subTest(command=name):
                    self.assertIn(name, commands)
                    command = commands[name]
                    self.assertIsNotNone(command.get_arguments_schema())
                    self.assertNotIn('storage-account', command.AZ_NAME)
                    if operation not in ('wait',):
                        self.assertEqual('2026-09-01', command._aaz_info['version'])

    def test_context_cache_help_examples_parse(self):
        for command_type in [cache.Update, container.Create, container.Update, identity.Assign]:
            examples = [line.strip() for line in command_type.__doc__.splitlines()
                        if line.strip().startswith('az ')]
            self.assertTrue(examples, command_type.AZ_NAME)
            for example in examples:
                with self.subTest(command=example):
                    parsed = []

                    def capture(command, command_args):
                        AAZCommand._handler(command, command_args)
                        parsed.append(command.ctx.args)

                    output = io.StringIO()
                    with patch.object(command_type, '_handler', capture), \
                            contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                        try:
                            result = self.cli_ctx.invoke(
                                shlex.split(example)[1:] + ['--subscription', SUBSCRIPTION], out_file=output)
                        except SystemExit as error:
                            result = error.code
                    self.assertEqual(0, result or 0, output.getvalue())
                    self.assertEqual(1, len(parsed))

    def test_blob_access_point_all_sources_and_connection_types_serialize(self):
        for source_type, wire_type in SOURCE_TYPES.items():
            for private_link in (False, True):
                with self.subTest(source=wire_type, private_link=private_link):
                    operation = self._operation(
                        bap.Create, bap.Create.BlobAccessPointConfigurationsCreate,
                        source=self._source(source_type, private_link))
                    method, body = self._request_body(operation)
                    self.assertEqual('PUT', method)
                    source = body['properties']['source']
                    self.assertEqual(wire_type, source['sourceType'])
                    self.assertEqual('PrivateLink' if private_link else 'Endpoint',
                                     source['connection']['connectionType'])
                    self.assertEqual('AccessKey', source['auth']['authType'])
                    self.assertEqual('fake-secret', source['auth']['secretAccessKey'])
                    self.assertNotIn('uniqueId', body['properties'])

    def test_blob_access_point_patch_does_not_resend_create_only_connection_targets(self):
        operation = self._operation(
            bap.Update, bap.Update.BlobAccessPointConfigurationsUpdate,
            source={'s3_compatible': {
                'connection': {'endpoint': {'tls_verification': 'Skip'}},
                'auth': {'access_key': {'secret_access_key': 'rotated-fake-secret'}}
            }})
        method, body = self._request_body(operation)
        self.assertEqual('PATCH', method)
        source = body['properties']['source']
        self.assertEqual({'connectionType': 'Endpoint', 'tlsVerification': 'Skip'}, source['connection'])
        self.assertEqual({'authType': 'AccessKey', 'secretAccessKey': 'rotated-fake-secret'}, source['auth'])
        self.assertNotIn('location', body)
        operation = self._operation(
            bap.Update, bap.Update.BlobAccessPointConfigurationsUpdate, description='updated')
        self.assertEqual({'properties': {'description': 'updated'}}, self._request_body(operation)[1])

    def test_blob_access_point_read_and_list_never_return_secret_access_key(self):
        payload = {
            'name': 'myaccesspoint', 'properties': {
                'uniqueId': SUBSCRIPTION,
                'source': {
                    'sourceType': 'S3Compatible',
                    'connection': {'connectionType': 'Endpoint', 'endpoint': 'https://s3.example.com'},
                    'auth': {'authType': 'AccessKey', 'accessKeyId': 'fake-id', 'secretAccessKey': 'fake-secret'}
                }
            }
        }
        for command_type, operation_type, data in (
                (bap.Show, bap.Show.BlobAccessPointConfigurationsGet, payload),
                (bap.List, bap.List.BlobAccessPointConfigurationsListByStorageAccount, {
                    'value': [payload], 'nextLink': 'https://management.azure.com/next'})):
            with self.subTest(command=command_type.__name__):
                operation = self._operation(command_type, operation_type)
                operation.on_200(SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: data}))
                command = command_type(cli_ctx=self.cli_ctx)
                command.ctx = operation.ctx
                output = command._output()
                self.assertNotIn('fake-secret', json.dumps(output))
                if isinstance(output, tuple):
                    self.assertEqual('https://management.azure.com/next', output[1])
                    output = output[0]
                item = output[0] if isinstance(output, list) else output
                self.assertEqual('fake-id', item['properties']['source']['auth']['accessKeyId'])
                self.assertEqual(SUBSCRIPTION, item['properties']['uniqueId'])

    def test_connection_tests_send_required_bodies_and_are_long_running(self):
        cases = (
            (bap.TestExistingConnection,
             bap.TestExistingConnection.BlobAccessPointConfigurationsTestExistingConnection,
             {'unique_id': SUBSCRIPTION}),
            (bap.TestProposedConnection,
             bap.TestProposedConnection.BlobAccessPointConnectionTestsTestProposedConnection,
             {'source': self._source()})
        )
        for command_type, operation_type, args in cases:
            for no_wait in (False, True):
                with self.subTest(command=command_type.AZ_NAME, no_wait=no_wait):
                    operation = self._operation(command_type, operation_type, no_wait=no_wait, **args)
                    method, body = self._request_body(operation)
                    self.assertEqual('POST', method)
                    if 'unique_id' in args:
                        self.assertEqual({'uniqueId': SUBSCRIPTION}, body)
                    else:
                        self.assertEqual('S3Compatible', body['source']['sourceType'])
                    session = SimpleNamespace(http_response=SimpleNamespace(status_code=202))
                    with patch.object(operation.client, 'send_request', return_value=session), \
                            patch.object(operation.client, 'build_lro_polling', return_value=sentinel.polling) as poll:
                        self.assertIs(sentinel.polling, operation())
                        self.assertEqual(no_wait, poll.call_args.args[0])
                        self.assertIs(session, poll.call_args.args[1])
                    self.assertTrue(command_type.AZ_SUPPORT_NO_WAIT)

    def test_new_resource_operations_surface_service_errors(self):
        for command_type, operation_type in (
                (bap.Show, bap.Show.BlobAccessPointConfigurationsGet),
                (cache.Show, cache.Show.ContextCachesGet)):
            with self.subTest(command=command_type.AZ_NAME):
                operation = self._operation(command_type, operation_type)
                response = Mock(status_code=404, reason='Not Found', headers={})
                response.text.return_value = '{"error":{"code":"ResourceNotFound","message":"Not found"}}'
                with patch.object(operation.client, 'send_request',
                                  return_value=SimpleNamespace(http_response=response)):
                    with self.assertRaises(ResourceNotFoundError):
                        operation()

    def test_cache_create_and_patch_support_user_assigned_managed_identity(self):
        for command_type, operation_type, args in (
                (cache.Create, cache.Create.ContextCachesCreateOrUpdate,
                 {'account_kind': 'Regional', 'identity': {
                     'type': 'SystemAssigned,UserAssigned',
                     'mi_user_assigned': [IDENTITY], 'mi_system_assigned': 'true'}}),
                (cache.Update, cache.Update.ContextCachesUpdate,
                 {'mi_user_assigned': [IDENTITY], 'mi_system_assigned': 'true'})):
            with self.subTest(command=command_type.__name__):
                operation = self._operation(command_type, operation_type, **args)
                method, body = self._request_body(operation)
                self.assertEqual('PUT' if command_type is cache.Create else 'PATCH', method)
                self.assertEqual({
                    'type': 'SystemAssigned,UserAssigned', 'userAssignedIdentities': {IDENTITY: {}}
                }, body['identity'])

    def test_cache_patch_preserves_unmentioned_identity_and_create_only_properties(self):
        operation = self._operation(cache.Update, cache.Update.ContextCachesUpdate, description='updated')
        method, body = self._request_body(operation)
        self.assertEqual('PATCH', method)
        self.assertEqual({'properties': {'description': 'updated'}}, body)
        self.assertNotIn('account_kind', cache.Update.get_arguments_schema()._fields)
        operation = self._operation(
            container.Update, container.Update.ContextCacheContainersUpdate, time_to_live=15)
        method, body = self._request_body(operation)
        self.assertEqual('PATCH', method)
        self.assertEqual({'properties': {'timeToLive': 15}}, body)
        fields = container.Update.get_arguments_schema()._fields
        self.assertNotIn('model_name', fields)
        self.assertNotIn('provider', fields)

    def _resource_patch_polling(self, command_type, no_wait=False, failed=False):
        resource_path = (
            'https://management.azure.com/subscriptions/' + SUBSCRIPTION +
            '/resourceGroups/myrg/providers/Microsoft.Storage/contextCaches/mycache')
        if command_type is container.Update:
            resource_path += '/contextCacheContainers/mycontainer'
        resource_url = resource_path + '?api-version=2026-09-01'
        status_url = (
            'https://management.azure.com/subscriptions/' + SUBSCRIPTION +
            '/providers/Microsoft.Storage/locations/eastus/ContextCacheRPOperationStatuses/update'
            '?api-version=2026-09-01')
        resource = {
            'id': resource_url.split('?')[0], 'name': 'mycache', 'location': 'eastus',
            'properties': {'accountKind': 'Regional', 'description': 'updated'},
            'identity': {'type': 'SystemAssigned', 'principalId': SUBSCRIPTION, 'tenantId': SUBSCRIPTION}
        }
        if command_type is container.Update:
            resource = {
                'id': resource_path, 'name': 'mycontainer',
                'properties': {
                    'modelName': 'gpt-4o', 'provider': 'OpenAI', 'timeToLive': 30, 'description': 'updated'
                }
            }
            operation_type = command_type.ContextCacheContainersUpdate
        else:
            operation_type = command_type.ContextCachesUpdate
        operation = self._operation(command_type, operation_type, no_wait=no_wait)
        if command_type in (identity.Assign, identity.Remove):
            command_type.ContextCachesGet(operation.ctx).on_200(
                SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: resource}))
            command_type.SubresourceSelector(ctx=operation.ctx, name='subresource')

        requests = []

        def send(request, **kwargs):
            request.headers['x-ms-client-request-id'] = SUBSCRIPTION
            requests.append((request.method, request.url))
            if request.method == 'PATCH':
                status_code, body = 202, None
                headers = {'Azure-AsyncOperation': status_url, 'Location': status_url, 'Retry-After': '0'}
            elif request.url == status_url:
                status_code = 200
                body = {'status': 'Failed' if failed else 'Succeeded', 'properties': None}
                if failed:
                    body['error'] = {'code': 'UpdateFailed', 'message': 'Resource update failed'}
                headers = {}
            else:
                self.assertEqual(resource_url, request.url)
                status_code, body, headers = 200, resource, {}
            response = Mock(
                status_code=status_code, headers=CaseInsensitiveDict(headers), request=request, reason='OK')
            content = json.dumps(body) if body is not None else ''
            response.text.return_value = content
            response.body.return_value = content.encode()
            context = PipelineContext(None, stream=False)
            context[ContentDecodePolicy.CONTEXT_NAME] = body
            return PipelineResponse(request, response, context)

        with patch.object(operation.client._pipeline, 'run', side_effect=send), \
                patch.object(AAZBasePolling, '_sleep'):
            polling = operation()
            if failed:
                with self.assertRaisesRegex(HttpResponseError, 'UpdateFailed'):
                    polling.run()
            else:
                polling.run()
                polling.resource()

        if no_wait:
            self.assertIsInstance(polling, AAZNoPolling)
            self.assertEqual([('PATCH', resource_url)], requests)
        elif failed:
            self.assertEqual([('PATCH', resource_url), ('GET', status_url)], requests)
        else:
            self.assertEqual(
                [('PATCH', resource_url), ('GET', status_url), ('GET', resource_url)], requests)
            self.assertEqual(resource, command_type.deserialize_output(
                operation.ctx.vars.instance, client_flatten=True))

    def test_cache_patch_polls_then_gets_original_resource(self):
        for command_type in (cache.Update, container.Update, identity.Assign, identity.Remove):
            for no_wait in (False, True):
                with self.subTest(command=command_type.AZ_NAME, no_wait=no_wait):
                    self._resource_patch_polling(command_type, no_wait=no_wait)

    def test_cache_patch_polling_failure_does_not_get_resource(self):
        for command_type in (cache.Update, container.Update, identity.Assign, identity.Remove):
            with self.subTest(command=command_type.AZ_NAME):
                self._resource_patch_polling(command_type, failed=True)

    def test_cache_create_public_system_identity_argument_serializes(self):
        result, requests, output = self._cli_request(
            cache.Create, cache.Create.ContextCachesCreateOrUpdate,
            ['-g', 'myrg', '-n', 'mycache', '-l', 'eastus', '--account-kind', 'Regional',
             '--identity', 'type=SystemAssigned'])
        self.assertEqual(0, result, output)
        self.assertEqual({'type': 'SystemAssigned'}, json.loads(requests[0].body)['identity'])

    def test_cache_identity_commands_merge_and_remove_without_overwriting_other_properties(self):
        other_identity = IDENTITY + '2'
        for command_type, existing, args, expected in (
                (identity.Assign, [IDENTITY], {'mi_user_assigned': [other_identity]},
                 {'type': 'SystemAssigned,UserAssigned',
                  'userAssignedIdentities': {IDENTITY: {}, other_identity: {}}}),
                (identity.Remove, [IDENTITY, other_identity], {'mi_user_assigned': [IDENTITY]},
                 {'type': 'SystemAssigned,UserAssigned', 'userAssignedIdentities': {other_identity: {}}}),
                (identity.Remove, [IDENTITY], {'mi_system_assigned': 'true'},
                 {'type': 'UserAssigned', 'userAssignedIdentities': {IDENTITY: {}}})):
            with self.subTest(command=command_type.AZ_NAME, arguments=args):
                operation = self._operation(command_type, command_type.ContextCachesGet, **args)
                operation.on_200(SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: {
                    'location': 'eastus', 'properties': {'description': 'Keep this', 'accountKind': 'Regional'},
                    'identity': {
                        'type': 'SystemAssigned,UserAssigned', 'principalId': SUBSCRIPTION, 'tenantId': SUBSCRIPTION,
                        'userAssignedIdentities': {item: {'principalId': SUBSCRIPTION} for item in existing}
                    }
                }}))
                command_type.SubresourceSelector(ctx=operation.ctx, name='subresource')
                command_type.InstanceUpdateByJson(ctx=operation.ctx)()
                with patch.object(operation.ctx, 'get_login_credential', return_value=Mock()):
                    update = command_type.ContextCachesUpdate(operation.ctx)
                self.addCleanup(update.client.close)
                method, body = self._request_body(update)
                self.assertEqual('PATCH', method)
                self.assertEqual({'identity': expected}, body)

    def test_cache_container_ttl_inclusive_bounds_apply_to_create_and_patch(self):
        for command_type, operation_type, base in (
                (container.Create, container.Create.ContextCacheContainersCreateOrUpdate,
                 {'model_name': 'gpt-4o', 'provider': 'OpenAI'}),
                (container.Update, container.Update.ContextCacheContainersUpdate, {})):
            for ttl in (1, 30):
                with self.subTest(command=command_type.__name__, ttl=ttl):
                    operation = self._operation(command_type, operation_type, time_to_live=ttl, **base)
                    self.assertEqual(ttl, self._request_body(operation)[1]['properties']['timeToLive'])
            for ttl in (0, 31):
                with self.subTest(command=command_type.__name__, ttl=ttl):
                    with self.assertRaises(InvalidArgumentValueError):
                        self._operation(command_type, operation_type, time_to_live=ttl, **base)

    def test_cache_list_keeps_both_scopes(self):
        operation = self._operation(cache.List, cache.List.ContextCachesListBySubscription)
        self.assertEqual('/subscriptions/' + SUBSCRIPTION + '/providers/Microsoft.Storage/contextCaches',
                         urlparse(operation.url).path)
        operation = self._operation(cache.List, cache.List.ContextCachesListByResourceGroup)
        self.assertIn('/resourceGroups/myrg/', operation.url)
        self.assertFalse(cache.List.get_arguments_schema().resource_group._required)

    def test_check_name_defaults_resource_type_and_returns_unavailable_result(self):
        result, requests, output = self._cli_request(
            cache.CheckName, cache.CheckName.ContextCachesCheckNameAvailability, ['--name', 'mycache'])
        self.assertEqual(0, result, output)
        self.assertEqual({'name': 'mycache', 'type': 'Microsoft.Storage/contextCaches'}, json.loads(requests[0].body))
        self.assertFalse(cache.CheckName.AZ_SUPPORT_NO_WAIT)
        operation = self._operation(cache.CheckName, cache.CheckName.ContextCachesCheckNameAvailability)
        data = {'nameAvailable': False, 'reason': 'AlreadyExists', 'message': 'Name already in use'}
        operation.on_200(SimpleNamespace(context={ContentDecodePolicy.CONTEXT_NAME: data}))
        command = cache.CheckName(cli_ctx=self.cli_ctx)
        command.ctx = operation.ctx
        self.assertEqual(data, command._output())

    def test_documented_polymorphic_cli_examples_build_requests(self):
        for command_type, operation_type in (
                (bap.Create, bap.Create.BlobAccessPointConfigurationsCreate),
                (bap.TestProposedConnection, bap.TestProposedConnection.BlobAccessPointConnectionTestsTestProposedConnection)):
            with self.subTest(command=command_type.AZ_NAME):
                example = command_type.AZ_HELP['examples'][0]['text']
                source = json.loads(example.split(" --source '", 1)[1].rsplit("'", 1)[0])
                args = ['-g', 'myrg', '--account-name', 'mystorage', '--source', json.dumps(source)]
                if command_type is not bap.TestProposedConnection:
                    args += ['-n', 'myresource', '-l', 'eastus']
                result, requests, output = self._cli_request(command_type, operation_type, args)
                self.assertEqual(0, result, output)
                body = json.loads(requests[0].body)
                self.assertIn('source', body if command_type is bap.TestProposedConnection else body['properties'])
