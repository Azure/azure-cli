# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from copy import deepcopy
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


class TestExpressRouteMultiCloud(unittest.TestCase):
    def setUp(self):
        self.resource = {
            'name': 'circuit',
            'location': 'eastus2',
            'sku': {'name': 'MultiCloud_MeteredData', 'tier': 'MultiCloud', 'family': 'MeteredData'},
            'properties': {
                'partnerAccountId': 'original-account',
                'activationKey': 'original-key',
                'resiliencyLevel': 'Maximum',
                'serviceProviderProvisioningState': 'DeProvisioned',
                'serviceProviderProperties': {
                    'serviceProviderName': 'AWS', 'peeringLocation': 'uswest2', 'bandwidthInMbps': 200,
                },
            },
        }

    def _command(self, command_type, **arguments):
        from azure.cli.core import AzCli
        from azure.cli.core.aaz._command_ctx import AAZCommandCtx

        cli = mock.MagicMock(spec=AzCli)
        cli.data = {}
        cli.cloud = mock.MagicMock()
        command = command_type(cli_ctx=cli)
        command.ctx = AAZCommandCtx(cli, command.get_arguments_schema(), {
            'name': 'circuit', 'resource_group': 'rg',
            'subscription': '00000000-0000-0000-0000-000000000000',
            **arguments,
        })
        command.ctx.get_http_client = mock.Mock()
        command.ctx.format_args()
        return command

    def test_create_multicloud_provisioning(self):
        from azure.cli.command_modules.network.custom import ExpressRouteCreate

        for argument, field in [('partner_account_id', 'partnerAccountId'), ('activation_key', 'activationKey')]:
            with self.subTest(argument=argument):
                command = self._command(
                    ExpressRouteCreate, location='eastus2', bandwidth=['200'], provider='AWS',
                    peering_location='uswest2', sku_tier='MultiCloud', sku_family='MeteredData',
                    **{argument: 'test-value+/='})
                command.pre_operations()
                operation = command.ExpressRouteCircuitsCreateOrUpdate(command.ctx)
                self.assertEqual(operation.query_parameters['api-version'], '2025-09-01')
                self.assertEqual(operation.content, {
                    'location': 'eastus2',
                    'sku': self.resource['sku'],
                    'properties': {
                        field: 'test-value+/=',
                        'serviceProviderProperties': self.resource['properties']['serviceProviderProperties'],
                    },
                })

    def test_update_multicloud_provisioning(self):
        from azure.cli.command_modules.network.custom import ExpressRouteUpdate

        cases = [
            {'partner_account_id': 'updated-account'},
            {'activation_key': 'updated-key'},
            {'partner_account_id': ''},
            {'activation_key': ''},
            {'partner_account_id': None},
            {'activation_key': None},
            {'tags': {'purpose': 'test'}},
            {'sku_tier': 'MultiCloud', 'sku_family': 'MeteredData'},
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                command = self._command(ExpressRouteUpdate, **arguments)
                command.pre_operations()
                command.ctx.set_var(
                    'instance', deepcopy(self.resource), command.ExpressRouteCircuitsGet._build_schema_on_200)
                command.InstanceUpdateByJson(command.ctx)()
                command.post_instance_update(command.ctx.vars.instance)
                operation = command.ExpressRouteCircuitsCreateOrUpdate(command.ctx)
                body = operation.content
                self.assertEqual(operation.query_parameters['api-version'], '2025-09-01')
                self.assertEqual(body['sku'], self.resource['sku'])
                for argument, field in [('partner_account_id', 'partnerAccountId'), ('activation_key', 'activationKey')]:
                    if argument in arguments and arguments[argument] is None:
                        self.assertNotIn(field, body['properties'])
                    else:
                        self.assertEqual(
                            body['properties'][field], arguments.get(argument, self.resource['properties'][field]))
                self.assertEqual(
                    body['properties']['serviceProviderProperties'],
                    self.resource['properties']['serviceProviderProperties'])
                self.assertNotIn('resiliencyLevel', body['properties'])
                if 'tags' in arguments:
                    self.assertEqual(body['tags'], arguments['tags'])

    def test_multicloud_output_and_read_only_resiliency(self):
        from azure.cli.core.aaz import AAZCommand
        from azure.cli.command_modules.network.custom import ExpressRouteCreate, ExpressRouteUpdate
        from azure.cli.command_modules.network.aaz.latest.network.express_route import List, Show, Wait

        operations = [
            (ExpressRouteCreate.ExpressRouteCircuitsCreateOrUpdate._build_schema_on_200_201, False),
            (ExpressRouteUpdate.ExpressRouteCircuitsGet._build_schema_on_200, False),
            (ExpressRouteUpdate.ExpressRouteCircuitsCreateOrUpdate._build_schema_on_200_201, False),
            (Show.ExpressRouteCircuitsGet._build_schema_on_200, False),
            (List.ExpressRouteCircuitsList._build_schema_on_200, True),
            (List.ExpressRouteCircuitsListAll._build_schema_on_200, True),
            (Wait.ExpressRouteCircuitsGet._build_schema_on_200, False),
        ]
        for schema_builder, is_list in operations:
            for level in ['Standard', 'High', 'Maximum']:
                with self.subTest(operation=schema_builder.__qualname__, resiliency=level):
                    resource = deepcopy(self.resource)
                    resource['properties']['resiliencyLevel'] = level
                    schema = schema_builder()
                    data = {'value': [resource]} if is_list else resource
                    value = schema._ValueCls(schema=schema, data=schema.process_data(data))
                    output = AAZCommand.deserialize_output(value)
                    if is_list:
                        output = output['value'][0]
                    for field in ['partnerAccountId', 'activationKey', 'resiliencyLevel',
                                  'serviceProviderProvisioningState']:
                        self.assertEqual(output[field], resource['properties'][field])

        for command_type in [ExpressRouteCreate, ExpressRouteUpdate]:
            command = self._command(command_type, location='eastus2')
            self.assertNotIn('resiliency_level', dict(command._cli_arguments_loader()))


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
