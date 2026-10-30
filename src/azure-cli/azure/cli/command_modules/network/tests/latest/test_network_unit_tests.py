# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest

from unittest import mock

from knack.util import CLIError


class TestNetworkUnitTests(unittest.TestCase):
    def test_application_gateway_subresource_preserves_hsm_schema(self):
        from azure.cli.command_modules.network.aaz.latest.network.application_gateway.address_pool import Create

        self.assertEqual(Create._aaz_info['version'], '2026-01-01')
        schemas = [
            Create.ApplicationGatewaysGet._build_schema_on_200(),
            Create.ApplicationGatewaysCreateOrUpdate._build_schema_on_200_201(),
        ]
        for schema in schemas:
            hsm = schema.properties.ssl_certificates.Element.properties.hsm
            self.assertIsNotNone(hsm.key_id)
            self.assertIsNotNone(hsm.public_cert_data)

    def test_network_get_nic_ip_config(self):
        from azure.cli.command_modules.network.custom import _get_nic_ip_config

        # 1 -  Test that if ip_configurations property is null, error is thrown
        nic = mock.MagicMock()
        nic.ip_configurations = None
        with self.assertRaises(CLIError):
            _get_nic_ip_config(nic, 'test')

        def mock_ip_config(name, value):
            fake = mock.MagicMock()
            fake.name = name
            fake.value = value
            return fake

        nic = mock.MagicMock()
        nic.ip_configurations = [mock_ip_config('test1', '1'), mock_ip_config('test2', '2'),
                                 mock_ip_config('test3', '3')]
        # 2 - Test that if ip_configurations is not null but no match, error is thrown
        with self.assertRaises(CLIError):
            _get_nic_ip_config(nic, 'test4')

        # 3 - Test that match is returned
        self.assertEqual(_get_nic_ip_config(nic, 'test2').value, '2')

    def test_network_upsert(self):
        from azure.cli.core.commands import upsert_to_collection

        obj1 = mock.MagicMock()
        obj1.key = 'object1'
        obj1.value = 'cat'

        obj2 = mock.MagicMock()
        obj2.key = 'object2'
        obj2.value = 'dog'

        # 1 - verify upsert to a null collection
        parent_with_null_collection = mock.MagicMock()
        parent_with_null_collection.collection = None
        upsert_to_collection(parent_with_null_collection, 'collection', obj1, 'key')
        result = parent_with_null_collection.collection
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, 'cat')

        # 2 - verify upsert to an empty collection
        parent_with_empty_collection = mock.MagicMock()
        parent_with_empty_collection.collection = []
        upsert_to_collection(parent_with_empty_collection, 'collection', obj1, 'key')
        result = parent_with_empty_collection.collection
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, 'cat')

        # 3 - verify can add more than one
        upsert_to_collection(parent_with_empty_collection, 'collection', obj2, 'key')
        result = parent_with_empty_collection.collection
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].value, 'dog')

        # 4 - verify update to existing collection
        obj2.value = 'noodle'
        upsert_to_collection(parent_with_empty_collection, 'collection', obj2, 'key')
        result = parent_with_empty_collection.collection
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].value, 'noodle')


class TestDataReplicationPrivateEndpoint(unittest.TestCase):
    def setUp(self):
        from azure.cli.command_modules.network.private_link_resource_and_endpoint_connections import custom

        self.custom = custom
        mapping_patch = mock.patch.dict(custom.TYPE_CLIENT_MAPPING, clear=True)
        mapping_patch.start()
        self.addCleanup(mapping_patch.stop)
        custom.register_providers()
        self.cmd = mock.Mock()
        self.resource_provider = 'Microsoft.DataReplication/replicationVaults'
        self.resource_url = (
            '/subscriptions/{subscriptionId}/resourceGroups/test-rg/'
            'providers/Microsoft.DataReplication/replicationVaults/test-vault'
        )
        self.connections_url = self.resource_url + '/privateEndpointConnections?api-version=2026-05-01'
        self.connection_url = self.resource_url + '/privateEndpointConnections/test-connection?api-version=2026-05-01'
        self.connection = {
            'name': 'test-connection',
            'properties': {
                'provisioningState': 'Succeeded',
                'privateEndpoint': {'id': '/subscriptions/test/privateEndpoints/test-endpoint'},
                'privateLinkServiceConnectionState': {'status': 'Pending', 'description': ''},
            },
        }
        request_patch = mock.patch(
            'azure.cli.command_modules.network.private_link_resource_and_endpoint_connections.'
            'resource_providers.send_raw_request'
        )
        self.send_request = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.send_request.return_value.json.return_value = self.connection

    def test_network_datareplication_provider(self):
        from azure.cli.command_modules.network.private_link_resource_and_endpoint_connections.resource_providers import (
            GeneralPrivateEndpointClient,
        )

        for resource_provider in (self.resource_provider, self.resource_provider.lower()):
            with self.subTest(resource_provider=resource_provider):
                client = self.custom._get_client(self.custom.TYPE_CLIENT_MAPPING, resource_provider)
                self.assertIsInstance(client, GeneralPrivateEndpointClient)
                self.assertEqual(client.rp, self.resource_provider)
                self.assertEqual(client.api_version, '2026-05-01')
                self.assertEqual(client.resource_get_api_version, '2026-05-01')
                self.assertTrue(client.support_list)

    def test_network_datareplication_private_link_resource_list(self):
        resources = [{'name': 'test-link', 'properties': {'groupId': 'test-group'}}]
        self.send_request.return_value.json.return_value = {'value': resources}

        result = self.custom.list_private_link_resource(
            self.cmd, 'test-rg', 'test-vault', self.resource_provider
        )

        self.assertEqual(result, resources)
        self.send_request.assert_called_once_with(
            self.cmd.cli_ctx, 'get', self.resource_url + '/privateLinkResources?api-version=2026-05-01'
        )

    def test_network_datareplication_private_endpoint_connection_list(self):
        self.send_request.return_value.json.return_value = {'value': [self.connection]}

        result = self.custom.list_private_endpoint_connection(
            self.cmd, 'test-rg', 'test-vault', self.resource_provider
        )

        self.assertEqual(result, [self.connection])
        self.send_request.assert_called_once_with(self.cmd.cli_ctx, 'get', self.connections_url)

    def test_network_datareplication_private_endpoint_connection_show(self):
        result = self.custom.show_private_endpoint_connection(
            self.cmd, 'test-rg', 'test-vault', self.resource_provider, 'test-connection'
        )

        self.assertEqual(result, self.connection)
        self.send_request.assert_called_once_with(self.cmd.cli_ctx, 'get', self.connection_url)

    def test_network_datareplication_private_endpoint_connection_approve_and_reject(self):
        for handler, status in (
            (self.custom.approve_private_endpoint_connection, 'Approved'),
            (self.custom.reject_private_endpoint_connection, 'Rejected'),
        ):
            with self.subTest(status=status):
                self.send_request.reset_mock()
                with mock.patch(
                    'azure.cli.command_modules.network.private_link_resource_and_endpoint_connections.'
                    'resource_providers.time.sleep'
                ):
                    result = handler(
                        self.cmd, 'test-rg', 'test-vault', self.resource_provider,
                        'test-connection', 'Test description'
                    )

                self.assertEqual(result, self.connection)
                self.assertEqual(result['properties']['privateLinkServiceConnectionState'], {
                    'status': status, 'description': 'Test description'
                })
                self.assertEqual(self.send_request.call_args_list, [
                    mock.call(self.cmd.cli_ctx, 'get', self.connection_url),
                    mock.call(self.cmd.cli_ctx, 'put', self.connection_url, body=json.dumps(self.connection)),
                    mock.call(self.cmd.cli_ctx, 'get', self.connection_url),
                ])

    def test_network_datareplication_private_endpoint_connection_delete(self):
        self.send_request.return_value.status_code = 200

        result = self.custom.remove_private_endpoint_connection(
            self.cmd, 'test-rg', 'test-vault', self.resource_provider, 'test-connection'
        )

        self.assertIsNone(result)
        self.send_request.assert_called_once_with(self.cmd.cli_ctx, 'delete', self.connection_url)


class TestVpnConnectionCertAuthNoSharedKey(unittest.TestCase):
    """Unit test to verify that --shared-key is not required when --auth-type Certificate is used."""

    def _build_namespace(self, auth_type=None, shared_key=None):
        namespace = mock.MagicMock()
        namespace.resource_group_name = 'test-rg'
        namespace.vnet_gateway1 = ('/subscriptions/00000000-0000-0000-0000-000000000000/'
                                   'resourceGroups/test-rg/providers/Microsoft.Network/'
                                   'virtualNetworkGateways/gw1')
        namespace.local_gateway2 = ('/subscriptions/00000000-0000-0000-0000-000000000000/'
                                    'resourceGroups/test-rg/providers/Microsoft.Network/'
                                    'localNetworkGateways/lgw2')
        namespace.vnet_gateway2 = None
        namespace.express_route_circuit2 = None
        namespace.shared_key = shared_key
        namespace.shared_key_keyvault_id = None
        namespace.auth_type = auth_type
        namespace.tags = None
        namespace.location = 'eastus'
        return namespace

    def test_cert_auth_without_shared_key_should_not_raise(self):
        """--auth-type Certificate should not require --shared-key."""
        from azure.cli.command_modules.network._validators import process_vpn_connection_create_namespace

        cmd = mock.MagicMock()
        namespace = self._build_namespace(auth_type='Certificate', shared_key=None)

        try:
            process_vpn_connection_create_namespace(cmd, namespace)
        except CLIError as e:
            if '--shared-key is required' in str(e):
                self.fail(
                    'Raised CLIError for missing --shared-key even though '
                    '--auth-type Certificate was specified.')

    def test_no_shared_key_without_cert_auth_should_raise(self):
        """without --auth-type Certificate, missing --shared-key must raise CLIError."""
        from azure.cli.command_modules.network._validators import process_vpn_connection_create_namespace

        cmd = mock.MagicMock()
        namespace = self._build_namespace(auth_type=None, shared_key=None)

        with self.assertRaises(CLIError) as ctx:
            process_vpn_connection_create_namespace(cmd, namespace)
        self.assertIn('--shared-key is required', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
