# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

from unittest import mock

from knack.util import CLIError


class TestNetworkUnitTests(unittest.TestCase):
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
