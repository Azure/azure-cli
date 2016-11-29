# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock
from azure.cli.command_modules.vm.custom import enable_boot_diagnostics, disable_boot_diagnostics
from azure.cli.command_modules.vm.custom import (_get_access_extension_upgrade_info,
                                                 _LINUX_ACCESS_EXT,
                                                 _WINDOWS_ACCESS_EXT)
from azure.cli.command_modules.vm.custom import \
    (attach_new_disk, attach_existing_disk, detach_disk)
from azure.mgmt.compute.models import NetworkProfile, StorageProfile, DataDisk, VirtualHardDisk
from azure.mgmt.compute.models.compute_management_client_enums import (DiskCreateOptionTypes,
                                                                       CachingTypes)

class Test_Vm_Custom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

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
        mock_vm_set.assert_called_once_with(vm_fake, mock.ANY)

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
        mock_vm_set.assert_called_once_with(vm_fake, mock.ANY)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_attach_new_datadisk_default_on_vm(self, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        #stub to get the vm which has no datadisks
        vm = FakedVM(None, None)
        mock_vm_get.return_value = vm

        #execute
        attach_new_disk('rg1', 'vm1', VirtualHardDisk(faked_vhd_uri))

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 1)
        data_disk = vm.storage_profile.data_disks[0]
        self.assertIsNone(data_disk.caching)
        self.assertEqual(data_disk.create_option, DiskCreateOptionTypes.empty)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)
        self.assertEqual(data_disk.name, 'd1')
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_attach_new_datadisk_custom_on_vm(self, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        faked_vhd_uri2 = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d2.vhd'

        #stub to get the vm which has no datadisks
        vhd = VirtualHardDisk(faked_vhd_uri)
        existing_disk = DataDisk(lun=1, vhd=vhd, name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        mock_vm_get.return_value = vm

        #execute
        attach_new_disk('rg1', 'vm1', VirtualHardDisk(faked_vhd_uri2), None, 'd2', 512, CachingTypes.read_write)

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 2)
        data_disk = vm.storage_profile.data_disks[1]
        self.assertEqual(CachingTypes.read_write, data_disk.caching)
        self.assertEqual(DiskCreateOptionTypes.empty, data_disk.create_option)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0) #the existing disk has '1', so it verifes the second one be picked as '0'
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri2)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_attach_existing_datadisk_on_vm(self, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        #stub to get the vm which has no datadisks
        vm = FakedVM()
        mock_vm_get.return_value = vm

        #execute
        vhd = VirtualHardDisk(faked_vhd_uri)
        attach_existing_disk('rg1', 'vm1', vhd, caching=CachingTypes.read_only)

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 1)
        data_disk = vm.storage_profile.data_disks[0]
        self.assertEqual(CachingTypes.read_only, data_disk.caching)
        self.assertEqual(DiskCreateOptionTypes.attach, data_disk.create_option)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)
        self.assertEqual(data_disk.name, 'd1')
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri)

    @mock.patch('azure.cli.command_modules.vm.custom._vm_get', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._vm_set', autospec=True)
    def test_deattach_disk_on_vm(self, mock_vm_set, mock_vm_get):
        #pylint: disable=line-too-long
        #stub to get the vm which has no datadisks
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        existing_disk = DataDisk(lun=1, vhd=VirtualHardDisk(faked_vhd_uri), name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        mock_vm_get.return_value = vm

        #execute
        detach_disk('rg1', 'vm1', 'd1')

        #assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 0)

class FakedVM:#pylint: disable=too-few-public-methods,old-style-class
    def __init__(self, nics=None, disks=None):
        self.network_profile = NetworkProfile(nics)
        self.storage_profile = StorageProfile(data_disks=disks)

class FakedAccessExtensionEntity:#pylint: disable=too-few-public-methods,old-style-class
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version

if __name__ == '__main__':
    unittest.main()
