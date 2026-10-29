# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import contextlib
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch, sentinel
from urllib.parse import parse_qs, urlparse

from azure.core.exceptions import ResourceNotFoundError
from azure.core.pipeline.policies import ContentDecodePolicy
from azure.cli.core import get_default_cli
from azure.cli.core.aaz import AAZCommand, AAZUndefined
from azure.cli.core.aaz._command_ctx import AAZCommandCtx
from azure.cli.core.azclierror import InvalidArgumentValueError
from azure.cli.command_modules.storage import StorageCommandsLoader
from azure.cli.command_modules.storage.aaz.latest.storage.account import blob_access_point_configuration as bap
from azure.cli.command_modules.storage.aaz.latest.storage.account import connector, data_share
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
            'connector_name': 'myconnector', 'data_share_name': 'myshare',
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
            'storage account connector': (
                'create', 'update', 'delete', 'show', 'list', 'test-existing-connection', 'wait'),
            'storage account data-share': ('create', 'update', 'delete', 'show', 'list', 'wait'),
            'storage account blob-access-point-configuration': (
                'create', 'update', 'delete', 'show', 'list',
                'test-existing-connection', 'test-proposed-connection', 'wait'),
            'storage context-cache': ('create', 'update', 'delete', 'show', 'list', 'check-name', 'wait'),
            'storage context-cache container': ('create', 'update', 'delete', 'show', 'list', 'wait'),
            'storage context-cache identity': ('assign', 'remove', 'show')
        }
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

    def test_data_share_create_requires_explicit_non_null_collections(self):
        operation = self._operation(data_share.Create, data_share.Create.DataSharesCreate,
                                    access_policies=[], assets=[])
        method, body = self._request_body(operation)
        self.assertEqual('PUT', method)
        self.assertEqual({'accessPolicies': [], 'assets': []}, body['properties'])
        self.assertEqual('eastus', body['location'])
        for field in ('assets', 'access_policies'):
            arg = data_share.Create.get_arguments_schema()._fields[field]
            self.assertTrue(arg._required)
            self.assertFalse(arg._nullable)
        for assets in (None, 'null'):
            with self.subTest(assets=assets):
                args = ['-g', 'myrg', '--account-name', 'mystorage', '-n', 'myshare', '-l', 'eastus',
                        '--access-policies', '[]']
                if assets is not None:
                    args += ['--assets', assets]
                result, requests, _ = self._cli_request(
                    data_share.Create, data_share.Create.DataSharesCreate, args)
                self.assertNotEqual(0, result)
                self.assertEqual([], requests)

    def test_data_share_patch_preserves_omitted_and_null_collections(self):
        for args in ({}, {'assets': None, 'access_policies': None}):
            with self.subTest(arguments=args):
                operation = self._operation(
                    data_share.Update, data_share.Update.DataSharesUpdate, description='updated', **args)
                method, body = self._request_body(operation)
                self.assertEqual('PATCH', method)
                self.assertEqual({'properties': {'description': 'updated'}}, body)
        result, requests, output = self._cli_request(
            data_share.Update, data_share.Update.DataSharesUpdate,
            ['-g', 'myrg', '--account-name', 'mystorage', '-n', 'myshare',
             '--description', 'updated', '--assets', 'null', '--access-policies', 'null'])
        self.assertEqual(0, result, output)
        self.assertEqual({'properties': {'description': 'updated'}}, json.loads(requests[0].body))

    def test_data_share_patch_replaces_collections_and_preserves_empty_arrays(self):
        for assets, policies in (
                ([], []),
                ([{'asset_path': 'blobServices/default/containers/shared', 'display_name': 'shared'}],
                 [{'principal_id': SUBSCRIPTION, 'tenant_id': SUBSCRIPTION, 'permission': 'Read'}])):
            with self.subTest(assets=assets):
                operation = self._operation(data_share.Update, data_share.Update.DataSharesUpdate,
                                            assets=assets, access_policies=policies)
                method, body = self._request_body(operation)
                self.assertEqual('PATCH', method)
                self.assertEqual(len(assets), len(body['properties']['assets']))
                self.assertEqual(len(policies), len(body['properties']['accessPolicies']))
                if assets:
                    self.assertEqual('shared', body['properties']['assets'][0]['displayName'])
                    self.assertEqual(SUBSCRIPTION, body['properties']['accessPolicies'][0]['principalId'])

    def test_data_share_public_collection_arguments_serialize(self):
        result, requests, output = self._cli_request(
            data_share.Create, data_share.Create.DataSharesCreate,
            ['-g', 'myrg', '--account-name', 'mystorage', '-n', 'myshare', '-l', 'eastus',
             '--assets', json.dumps([{'asset-path': '/shared', 'display-name': 'shared'}]),
             '--access-policies', json.dumps([{
                 'principal-id': SUBSCRIPTION, 'tenant-id': SUBSCRIPTION, 'permission': 'Read'
             }])])
        self.assertEqual(0, result, output)
        properties = json.loads(requests[0].body)['properties']
        self.assertEqual([{'assetPath': '/shared', 'displayName': 'shared'}], properties['assets'])
        self.assertEqual([{
            'principalId': SUBSCRIPTION, 'tenantId': SUBSCRIPTION, 'permission': 'Read'
        }], properties['accessPolicies'])

    def test_connector_create_and_patch_use_discriminated_source(self):
        source = {
            'data_share': {
                'connection': {'data_share': {'data_share_uri': 'azds://eastus:myshare:' + SUBSCRIPTION}},
                'auth_properties': {'managed_identity': {'identity_resource_id': IDENTITY}}
            }
        }
        operation = self._operation(connector.Create, connector.Create.ConnectorsCreate,
                                    data_source_type='Azure_DataShare', source=source, test_connection=False)
        method, body = self._request_body(operation)
        self.assertEqual('PUT', method)
        properties = body['properties']
        self.assertFalse(properties['testConnection'])
        self.assertEqual('Azure_DataShare', properties['dataSourceType'])
        self.assertEqual('DataShare', properties['source']['type'])
        self.assertEqual('DataShare', properties['source']['connection']['type'])
        self.assertEqual('ManagedIdentity', properties['source']['authProperties']['type'])
        self.assertEqual(IDENTITY, properties['source']['authProperties']['identityResourceId'])
        operation = self._operation(
            connector.Update, connector.Update.ConnectorsUpdate,
            source={'data_share': {'auth_properties': {'managed_identity': {'identity_resource_id': IDENTITY}}}},
            test_connection=False)
        method, body = self._request_body(operation)
        self.assertEqual('PATCH', method)
        self.assertNotIn('connection', body['properties']['source'])
        self.assertNotIn('dataSourceType', body['properties'])
        self.assertNotIn('location', body)
        self.assertFalse(body['properties']['testConnection'])

    def test_connector_description_patch_does_not_reset_state(self):
        operation = self._operation(connector.Update, connector.Update.ConnectorsUpdate, description='updated')
        method, body = self._request_body(operation)
        self.assertEqual('PATCH', method)
        self.assertEqual({'properties': {'description': 'updated'}}, body)
        result, requests, output = self._cli_request(
            connector.Update, connector.Update.ConnectorsUpdate,
            ['-g', 'myrg', '--account-name', 'mystorage', '-n', 'myconnector', '--description', 'updated'])
        self.assertEqual(0, result, output)
        self.assertEqual({'properties': {'description': 'updated'}}, json.loads(requests[0].body))
        operation = self._operation(connector.Update, connector.Update.ConnectorsUpdate, state='Inactive')
        self.assertEqual({'properties': {'state': 'Inactive'}}, self._request_body(operation)[1])
        result, requests, output = self._cli_request(
            connector.Update, connector.Update.ConnectorsUpdate,
            ['-g', 'myrg', '--account-name', 'mystorage', '-n', 'myconnector', '--state', 'Inactive'])
        self.assertEqual(0, result, output)
        self.assertEqual({'properties': {'state': 'Inactive'}}, json.loads(requests[0].body))

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
            (connector.TestExistingConnection,
             connector.TestExistingConnection.ConnectorsTestExistingConnection, {'unique_id': SUBSCRIPTION}),
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
                (connector.Show, connector.Show.ConnectorsGet),
                (data_share.Show, data_share.Show.DataSharesGet),
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
                (connector.Create, connector.Create.ConnectorsCreate),
                (bap.Create, bap.Create.BlobAccessPointConfigurationsCreate),
                (bap.TestProposedConnection, bap.TestProposedConnection.BlobAccessPointConnectionTestsTestProposedConnection)):
            with self.subTest(command=command_type.AZ_NAME):
                example = command_type.AZ_HELP['examples'][0]['text']
                source = json.loads(example.split(" --source '", 1)[1].rsplit("'", 1)[0])
                args = ['-g', 'myrg', '--account-name', 'mystorage', '--source', json.dumps(source)]
                if command_type is not bap.TestProposedConnection:
                    args += ['-n', 'myresource', '-l', 'eastus']
                if command_type is connector.Create:
                    args += ['--data-source-type', 'Azure_DataShare']
                result, requests, output = self._cli_request(command_type, operation_type, args)
                self.assertEqual(0, result, output)
                body = json.loads(requests[0].body)
                self.assertIn('source', body if command_type is bap.TestProposedConnection else body['properties'])
