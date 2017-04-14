# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from azure.cli.core.profiles import ResourceType

from azure.cli.command_modules.vm._validators import (_validate_vm_create_vnet,
                                                      _validate_vmss_create_subnet,
                                                      _validate_vm_create_storage_account,
                                                      _validate_vm_create_auth)

# pylint: disable=method-hidden
# pylint: disable=line-too-long
# pylint: disable=bad-continuation
# pylint: disable=too-many-lines


def _mock_resource_client(client_type):
    client = mock.MagicMock()
    if client_type is ResourceType.MGMT_NETWORK:
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
    elif client_type is ResourceType.MGMT_RESOURCE_RESOURCES:
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
    elif client_type is ResourceType.MGMT_STORAGE:
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


def _mock_network_client_with_existing_subnet(_):
    client = mock.MagicMock()

    def _mock_list(rg):
        def _get_mock_vnet(name, rg, location):
            vnet = mock.MagicMock()
            vnet.name = name
            vnet.rg = rg
            vnet.location = location
            subnet = mock.MagicMock()
            subnet.name = '{}subnet'.format(name)
            subnet.address_prefix = '10.0.0.0/24'
            vnet.subnets = [subnet]
            return vnet
        all_mocks = [
            _get_mock_vnet('vnet1', 'rg1', 'eastus'),
            _get_mock_vnet('vnet2', 'rg1', 'westus'),
        ]
        return [x for x in all_mocks if x.rg == rg]
    client.virtual_networks.list = _mock_list
    return client


class TestVMCreateDefaultVnet(unittest.TestCase):

    def _set_ns(self, rg, location=None):
        self.ns.resource_group_name = rg
        self.ns.location = location

    def setUp(self):
        ns = argparse.Namespace()
        ns.resource_group_name = None
        ns.subnet = None
        ns.vnet_name = None
        ns.vnet_type = None
        ns.location = None
        self.ns = ns

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_resource_client)
    def test_no_matching_vnet(self):
        self._set_ns('emptyrg', 'eastus')
        _validate_vm_create_vnet(self.ns)
        self.assertIsNone(self.ns.vnet_name)
        self.assertIsNone(self.ns.subnet)
        self.assertEqual(self.ns.vnet_type, 'new')

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_resource_client)
    def test_matching_vnet_specified_location(self):
        self._set_ns('rg1', 'eastus')
        _validate_vm_create_vnet(self.ns)
        self.assertEqual(self.ns.vnet_name, 'vnet1')
        self.assertEqual(self.ns.subnet, 'vnet1subnet')
        self.assertEqual(self.ns.vnet_type, 'existing')


class TestVMSSCreateDefaultVnet(unittest.TestCase):

    @staticmethod
    def _set_ns(rg, location=None):
        ns = argparse.Namespace()
        ns.resource_group_name = rg
        ns.location = location
        ns.subnet = None
        ns.vnet_name = None
        ns.vnet_type = None
        return ns

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_network_client_with_existing_subnet)
    def test_matching_vnet_subnet_size_matching(self):
        ns = TestVMSSCreateDefaultVnet._set_ns('rg1', 'eastus')
        ns.instance_count = 5
        _validate_vm_create_vnet(ns, for_scale_set=True)
        self.assertEqual(ns.vnet_name, 'vnet1')
        self.assertEqual(ns.subnet, 'vnet1subnet')
        self.assertEqual(ns.vnet_type, 'existing')

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_network_client_with_existing_subnet)
    def test_matching_vnet_no_subnet_size_matching(self):
        ns = TestVMSSCreateDefaultVnet._set_ns('rg1', 'eastus')
        ns.instance_count = 1000
        _validate_vm_create_vnet(ns, for_scale_set=True)
        self.assertIsNone(ns.vnet_name)
        self.assertIsNone(ns.subnet)
        self.assertEqual(ns.vnet_type, 'new')

        ns = TestVMSSCreateDefaultVnet._set_ns('rg1', 'eastus')
        ns.instance_count = 255
        _validate_vm_create_vnet(ns, for_scale_set=True)
        self.assertEqual(ns.vnet_type, 'new')

    def test_new_subnet_size_for_big_vmss(self):
        ns = argparse.Namespace()
        ns.vnet_type = 'new'
        ns.vnet_address_prefix = '10.0.0.0/16'
        ns.subnet_address_prefix = None
        ns.app_gateway_type = 'new'
        ns.app_gateway_subnet_address_prefix = '10.0.1.0/22'
        ns.instance_count = 1000
        _validate_vmss_create_subnet(ns)
        self.assertEqual('10.0.0.0/22', ns.subnet_address_prefix)

    def test_new_subnet_size_for_small_vmss(self):
        ns = argparse.Namespace()
        ns.vnet_type = 'new'
        ns.vnet_address_prefix = '10.0.0.0/16'
        ns.subnet_address_prefix = None
        ns.app_gateway_type = None
        ns.app_gateway_subnet_address_prefix = None
        ns.instance_count = 2
        _validate_vmss_create_subnet(ns)
        self.assertEqual('10.0.0.0/24', ns.subnet_address_prefix)


class TestVMCreateDefaultStorageAccount(unittest.TestCase):

    def _set_ns(self, rg, location=None, tier='Standard'):
        ns = argparse.Namespace()
        ns.resource_group_name = rg
        ns.location = location
        ns.storage_sku = tier
        ns.storage_account = None
        ns.storage_account_type = None
        self.ns = ns  # pylint: disable=attribute-defined-outside-init

    def setUp(self):
        self.ns = None

    def tearDown(self):
        pass

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_resource_client)
    def test_no_matching_storage_account(self):
        self._set_ns('emptyrg', 'eastus')
        _validate_vm_create_storage_account(self.ns)
        self.assertIsNone(self.ns.storage_account)
        self.assertEqual(self.ns.storage_account_type, 'new')

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client', _mock_resource_client)
    def test_matching_storage_account_specified_location(self):
        self._set_ns('rg1', 'eastus')
        _validate_vm_create_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa1')
        self.assertEqual(self.ns.storage_account_type, 'existing')

        self._set_ns('rg1', 'eastus', 'Premium')
        _validate_vm_create_storage_account(self.ns)
        self.assertEqual(self.ns.storage_account, 'sa2')
        self.assertEqual(self.ns.storage_account_type, 'existing')


class TestVMDefaultAuthType(unittest.TestCase):

    @staticmethod
    def _set_ns():
        ns = argparse.Namespace()
        ns.storage_profile = None
        ns.ssh_key_value = None
        ns.ssh_dest_key_path = None
        ns.admin_password = None
        return ns

    def test_default_windows(self):
        ns = TestVMDefaultAuthType._set_ns()
        ns.os_type = "WindowS"
        ns.authentication_type = None
        ns.admin_username = 'user12345'
        ns.admin_password = 'verySecret123'
        _validate_vm_create_auth(ns)
        self.assertEqual(ns.authentication_type, 'password')

    def test_default_linux(self):
        ns = TestVMDefaultAuthType._set_ns()
        ns.os_type = "LINux"
        ns.authentication_type = None
        test_user = 'user12345'
        ns.admin_username = test_user
        ns.admin_password = None
        ns.ssh_key_value = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n'
        _validate_vm_create_auth(ns)
        self.assertEqual(ns.authentication_type, 'ssh')
        self.assertEqual(ns.ssh_dest_key_path, '/home/{}/.ssh/authorized_keys'.format(test_user))

    def test_linux_with_password(self):
        ns = TestVMDefaultAuthType._set_ns()
        ns.os_type = "LINux"
        ns.authentication_type = 'password'
        ns.admin_username = 'user12345'
        ns.admin_password = 'verySecret!!!'
        _validate_vm_create_auth(ns)
        # still has 'password'
        self.assertEqual(ns.authentication_type, 'password')

        # throw when conflict with ssh key value
        ns.ssh_key_value = 'junk but does not matter'
        with self.assertRaises(ValueError) as context:
            _validate_vm_create_auth(ns)
        self.assertTrue("incorrect usage for authentication-type 'password':" in str(context.exception))


if __name__ == '__main__':
    unittest.main()
