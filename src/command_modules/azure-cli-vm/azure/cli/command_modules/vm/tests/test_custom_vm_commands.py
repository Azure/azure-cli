import unittest
import mock
import azure.cli.application as application
from azure.cli.command_modules.vm.custom import enable_boot_diagnostics, disable_boot_diagnostics
from azure.cli.command_modules.vm.custom import (_get_access_extension_upgrade_info,
                                                 _LINUX_ACCESS_EXT,
                                                 _WINDOWS_ACCESS_EXT)
from azure.cli.command_modules.vm.custom import (vm_add_nics, vm_delete_nics, vm_update_nics)
from azure.mgmt.compute.models import NetworkProfile, NetworkInterfaceReference

class Test_Vm_Custom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_custom_minmax(self):
        config = application.Configuration([])
        application.APPLICATION = application.Application(config)
        from azure.cli.command_modules.vm._validators import MinMaxValue

        validator = MinMaxValue(1, 3)
        self.assertEqual(1, validator(1))
        self.assertEqual(2, validator(2))
        self.assertEqual(3, validator(3))
        self.assertEqual(1, validator('1'))
        self.assertEqual(2, validator('2'))
        self.assertEqual(3, validator('3'))
        with self.assertRaises(ValueError):
            validator(0)
        with self.assertRaises(ValueError):
            validator('0')
        with self.assertRaises(ValueError):
            validator(4)
        with self.assertRaises(ValueError):
            validator('4')

    def test_get_access_extension_upgrade_info(self):

        #when there is no extension installed on linux vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _LINUX_ACCESS_EXT)
        self.assertEqual('Microsoft.OSTCExtensions', publisher)
        self.assertEqual('1.4', version)
        self.assertEqual(None, auto_upgrade)

        #when there is no extension installed on windows vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _WINDOWS_ACCESS_EXT)
        self.assertEqual('Microsoft.Compute', publisher)
        self.assertEqual('2.0', version)
        self.assertEqual(None, auto_upgrade)

        #when there is existing extension with higher version, stick to that
        extentions = [FakedAccessExtensionEntity(True, '3.0')]
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, _LINUX_ACCESS_EXT)
        self.assertEqual('3.0', version)
        self.assertEqual(None, auto_upgrade)

        extentions = [FakedAccessExtensionEntity(False, '10.0')]
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, _WINDOWS_ACCESS_EXT)
        self.assertEqual('10.0', version)
        self.assertEqual(None, auto_upgrade)

        #when there is existing extension with lower version, upgrade to ours
        extentions = [FakedAccessExtensionEntity(True, '1.0')]
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, _LINUX_ACCESS_EXT)
        self.assertEqual('1.4', version)
        self.assertEqual(True, auto_upgrade)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_enable_boot_diagnostics_on_vm_never_enabled(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        enable_boot_diagnostics('g1', 'vm1', 'https://storage_uri1')
        self.assertTrue(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertEqual('https://storage_uri1',
                         vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm_fake)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_enable_boot_diagnostics_skip_when_enabled_already(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'https://storage_uri1'
        enable_boot_diagnostics('g1', 'vm1', 'https://storage_uri1')
        self.assertTrue(mock_vm_get.called)
        self.assertFalse(mock_vm_set.called)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_disable_boot_diagnostics_on_vm(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'storage_uri1'
        disable_boot_diagnostics('g1', 'vm1')
        self.assertFalse(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertIsNone(vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm_fake)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.get_mgmt_service_client', autospec=True)
    def test_add_single_nic_on_vm(self, client_mock, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        new_nic_name = 'new_nic'
        new_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + new_nic_name
        new_nic = NetworkInterfaceReference(new_nic_id, False)

        #stub to get the vm which has no nic
        vm = FakedVM(None)
        vm.network_profile = None
        mock_vm_get.return_value = vm

        #stub to return nic on 'get'
        network_client_fake = mock.MagicMock()
        network_client_fake.network_interfaces.get.return_value = new_nic
        client_mock.return_value = network_client_fake

        #execute
        vm_add_nics('rg1', 'vm1', [new_nic_id], [])

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        network_client_fake.network_interfaces.get.assert_called_once_with('rg1', new_nic_name)
        self.assertEqual(len(vm.network_profile.network_interfaces), 1)
        self.assertEqual(vm.network_profile.network_interfaces[0].id, new_nic_id)
        self.assertTrue(vm.network_profile.network_interfaces[0].primary)


    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.get_mgmt_service_client', autospec=True)
    def test_add_nics_on_vm(self, client_mock, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        new_nic_name = 'new_nic'
        new_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + new_nic_name
        new_nic = NetworkInterfaceReference(new_nic_id, False)
        existing_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/existing_nic'
        existing_nic = NetworkInterfaceReference(existing_nic_id, True)
        existing_nic_name2 = 'existing_nic2'
        existing_nic_id2 = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name2
        existing_nic2 = NetworkInterfaceReference(existing_nic_id2, False)

        #stub to get the vm
        vm = FakedVM([existing_nic, existing_nic2])
        mock_vm_get.return_value = vm

        #stub to return nic on 'get'
        network_client_fake = mock.MagicMock()
        network_client_fake.network_interfaces.get.return_value = new_nic
        client_mock.return_value = network_client_fake

        #execute
        vm_add_nics('rg1', 'vm1', [new_nic_id], [], existing_nic_name2)

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        network_client_fake.network_interfaces.get.assert_called_once_with('rg1', new_nic_name)
        self.assertEqual(len(vm.network_profile.network_interfaces), 3)
        self.assertEqual(vm.network_profile.network_interfaces[0].id, existing_nic_id)
        self.assertEqual(vm.network_profile.network_interfaces[1].id, existing_nic_id2)
        self.assertEqual(vm.network_profile.network_interfaces[2].id, new_nic_id)
        self.assertFalse(vm.network_profile.network_interfaces[0].primary)
        self.assertTrue(vm.network_profile.network_interfaces[1].primary)
        self.assertFalse(vm.network_profile.network_interfaces[2].primary)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.get_mgmt_service_client', autospec=True)
    def test_remove_nics_on_vm(self, client_mock, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        existing_nic_name = 'existing_nic'
        existing_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name
        existing_nic = NetworkInterfaceReference(existing_nic_id, True)
        existing_nic_name2 = 'existing_nic2'
        existing_nic_id2 = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name2
        existing_nic2 = NetworkInterfaceReference(existing_nic_id2, False)
        existing_nic_name3 = 'existing_nic3'
        existing_nic_id3 = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name3
        existing_nic3 = NetworkInterfaceReference(existing_nic_id3, False)

        #stub to get the vm
        vm = FakedVM([existing_nic, existing_nic2, existing_nic3])
        mock_vm_get.return_value = vm

        #stub to return nic on 'get'
        network_client_fake = mock.MagicMock()
        network_client_fake.network_interfaces.get.return_value = existing_nic
        client_mock.return_value = network_client_fake

        #execute
        vm_delete_nics('rg1', 'vm1', [], [existing_nic_name], existing_nic_name2)

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        network_client_fake.network_interfaces.get.assert_called_once_with('rg1', existing_nic_name)
        self.assertEqual(len(vm.network_profile.network_interfaces), 2)
        self.assertEqual(vm.network_profile.network_interfaces[0].id, existing_nic_id2)
        self.assertEqual(vm.network_profile.network_interfaces[1].id, existing_nic_id3)
        self.assertTrue(vm.network_profile.network_interfaces[0].primary)
        self.assertFalse(vm.network_profile.network_interfaces[1].primary)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.get_mgmt_service_client', autospec=True)
    def test_update_nics_on_vm(self, client_mock, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        existing_nic_name = 'existing_nic'
        existing_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name
        existing_nic = NetworkInterfaceReference(existing_nic_id, True)
        existing_nic_name2 = 'existing_nic2'
        existing_nic_id2 = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + existing_nic_name2
        existing_nic2 = NetworkInterfaceReference(existing_nic_id2, False)
        new_nic_name = 'existing_nic3'
        new_nic_id = '/subscriptions/123/resourceGroups/rg1/providers/Microsoft.Network/networkInterfaces/' + new_nic_name
        new_nic = NetworkInterfaceReference(new_nic_id, False)

        #stub to get the vm
        vm = FakedVM([existing_nic, existing_nic2])
        mock_vm_get.return_value = vm

        #stub to return nic on 'get'
        network_client_fake = mock.MagicMock()
        network_client_fake.network_interfaces.get.side_effect = [existing_nic2, new_nic]
        client_mock.return_value = network_client_fake

        #execute
        vm_update_nics('rg1', 'vm1', [], [existing_nic_name2, new_nic_name], new_nic_id)

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(network_client_fake.network_interfaces.get.call_count, 2)
        self.assertEqual(len(vm.network_profile.network_interfaces), 2)
        self.assertEqual(vm.network_profile.network_interfaces[0].id, existing_nic_id2)
        self.assertEqual(vm.network_profile.network_interfaces[1].id, new_nic_id)
        self.assertFalse(vm.network_profile.network_interfaces[0].primary)
        self.assertTrue(vm.network_profile.network_interfaces[1].primary)

class FakedVM:#pylint: disable=too-few-public-methods,old-style-class
    def __init__(self, nics):
        self.network_profile = NetworkProfile(nics)

class FakedAccessExtensionEntity:#pylint: disable=too-few-public-methods,old-style-class
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version

if __name__ == '__main__':
    unittest.main()
