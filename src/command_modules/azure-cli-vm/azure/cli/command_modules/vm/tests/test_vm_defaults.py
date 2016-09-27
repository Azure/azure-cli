#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import argparse
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient

import azure.cli.core.commands.client_factory
from azure.cli.command_modules.vm._validators import \
    (validate_default_vnet, validate_default_storage_account)

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
#pylint: disable=too-many-lines

def _mock_resource_client(client_class):
    client = mock.MagicMock()
    if client_class is NetworkManagementClient:
        def _mock_list(rg):

            def _get_mock_vnet(name, rg, location):
                vnet = mock.MagicMock()
                vnet.name = name
                vnet.rg = rg
                vnet.location = location
                subnet = mock.MagicMock()
                subnet.name = '{}subnet'.format(name)
                vnet.subnets = [subnet]
                return vnet
            all_mocks = [
                _get_mock_vnet('vnet1', 'rg1', 'eastus'),
                _get_mock_vnet('vnet2', 'rg1', 'westus'),
                _get_mock_vnet('vnet3', 'rg2', 'westus'),
                _get_mock_vnet('vnet4', 'rg2', 'eastus')
            ]
            return [x for x in all_mocks if x.rg == rg]
        client.virtual_networks.list = _mock_list
    elif client_class is ResourceManagementClient:
        def _mock_get(rg):
            def _get_mock_rg(name, location):
                mock_rg = mock.MagicMock()
                mock_rg.location = location
                mock_rg.name = name
                return mock_rg
            all_mocks = [
                _get_mock_rg('rg1', 'westus'),
                _get_mock_rg('rg2', 'eastus')
            ]
            return next((x for x in all_mocks if x.name == rg), _get_mock_rg(rg, 'unknown'))
        client.resource_groups.get = _mock_get
    elif client_class is StorageManagementClient:
        def _mock_list_by_resource_group(rg):
            def _get_mock_sa(name, rg, location, tier):
                mock_sa = mock.MagicMock()
                mock_sa.name = name
                mock_sa.resource_group = rg
                mock_sa.location = location
                mock_sa.sku.tier.value = tier
                return mock_sa
            all_mocks = [
                _get_mock_sa('sa1', 'rg1', 'eastus', 'Standard'),
                _get_mock_sa('sa2', 'rg1', 'eastus', 'Premium'),
                _get_mock_sa('sa3', 'rg1', 'westus', 'Standard'),
                _get_mock_sa('sa4', 'rg1', 'westus', 'Premium')
            ]
            return list(x for x in all_mocks if x.resource_group == rg)
        client.storage_accounts.list_by_resource_group = _mock_list_by_resource_group
    return client

class TestVMCreateDefaultVnet(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        azure.cli.core.commands.client_factory.get_mgmt_service_client = _mock_resource_client

    @classmethod
    def tearDownClass(cls):
        pass

    def _set_ns(self, rg, location=None):
        self.ns.resource_group_name = rg
        self.ns.location = location

    def setUp(self):
        ns = argparse.Namespace()
        ns.resource_group_name = None
        ns.subnet_name = None
        ns.virtual_network = None
        ns.virtual_network_type = None
        ns.location = None
        self.ns = ns

    def tearDown(self):
        pass

    def test_no_matching_vnet(self):
        self._set_ns('emptyrg', 'eastus')
        validate_default_vnet(self.ns)
        self.assertIsNone(self.ns.virtual_network)
        self.assertIsNone(self.ns.subnet_name)
        self.assertIsNone(self.ns.virtual_network_type)

    def test_matching_vnet_default_location(self):
        self._set_ns('rg1')
        validate_default_vnet(self.ns)
        self.assertEqual(self.ns.virtual_network, 'vnet2')
        self.assertEqual(self.ns.subnet_name, 'vnet2subnet')
        self.assertEqual(self.ns.virtual_network_type, 'existingName')

    def test_matching_vnet_specified_location(self):
        self._set_ns('rg1', 'eastus')
        validate_default_vnet(self.ns)
        self.assertEqual(self.ns.virtual_network, 'vnet1')
        self.assertEqual(self.ns.subnet_name, 'vnet1subnet')
        self.assertEqual(self.ns.virtual_network_type, 'existingName')

if __name__ == '__main__':
    unittest.main()

class TestVMCreateDefaultStorageAccount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        azure.cli.core.commands.client_factory.get_mgmt_service_client = _mock_resource_client

    @classmethod
    def tearDownClass(cls):
        pass

    def _set_ns(self, rg, location=None, tier='Standard'):
        ns = argparse.Namespace()
        ns.resource_group_name = rg
        ns.location = location
        ns.storage_type = tier
        ns.storage_account = None
        ns.storage_account_type = None
        self.ns = ns # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        self.ns = None

    def tearDown(self):
        pass

    def test_no_matching_storage_account(self):
        self._set_ns('emptyrg', 'eastus')
        validate_default_storage_account(self.ns)
        try:
            self.assertRegex(self.ns.storage_account, '^vhd.*')
        except AttributeError:
            self.assertRegexpMatches(self.ns.storage_account, '^vhd.*') # pylint: disable=deprecated-method
        self.assertIsNone(self.ns.storage_account_type)

    def test_matching_storage_account_default_location(self):
        self._set_ns('rg1')
        validate_default_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa3')
        self.assertEqual(self.ns.storage_account_type, 'existingName')

        self._set_ns('rg1', tier='Premium')
        validate_default_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa4')
        self.assertEqual(self.ns.storage_account_type, 'existingName')


    def test_matching_storage_account_specified_location(self):
        self._set_ns('rg1', 'eastus')
        validate_default_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa1')
        self.assertEqual(self.ns.storage_account_type, 'existingName')

        self._set_ns('rg1', 'eastus', 'Premium')
        validate_default_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa2')
        self.assertEqual(self.ns.storage_account_type, 'existingName')

if __name__ == '__main__':
    unittest.main()
