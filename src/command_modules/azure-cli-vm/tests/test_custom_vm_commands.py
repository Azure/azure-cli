# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock

from azure.cli.core.util import CLIError

from azure.cli.command_modules.vm.custom import enable_boot_diagnostics, disable_boot_diagnostics, \
    _merge_secrets
from azure.cli.command_modules.vm.custom import (_get_access_extension_upgrade_info,
                                                 _LINUX_ACCESS_EXT,
                                                 _WINDOWS_ACCESS_EXT,
                                                 _get_extension_instance_name)
from azure.cli.command_modules.vm.custom import \
    (attach_unmanaged_data_disk, detach_data_disk, get_vmss_instance_view)
from azure.cli.command_modules.vm.disk_encryption import (enable,
                                                          disable,
                                                          _check_encrypt_is_supported)
from azure.mgmt.compute.models import (NetworkProfile, StorageProfile, DataDisk, OSDisk,
                                       OperatingSystemTypes, InstanceViewStatus,
                                       VirtualMachineExtensionInstanceView,
                                       VirtualMachineExtension, ImageReference,
                                       DiskCreateOptionTypes, CachingTypes)


class Test_Vm_Custom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_get_access_extension_upgrade_info(self):

        # when there is no extension installed on linux vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _LINUX_ACCESS_EXT)
        self.assertEqual('Microsoft.OSTCExtensions', publisher)
        self.assertEqual('1.4', version)
        self.assertEqual(None, auto_upgrade)

        # when there is no extension installed on windows vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _WINDOWS_ACCESS_EXT)
        self.assertEqual('Microsoft.Compute', publisher)
        self.assertEqual('2.0', version)
        self.assertEqual(None, auto_upgrade)

        # when there is existing extension with higher version, stick to that
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

        # when there is existing extension with lower version, upgrade to ours
        extentions = [FakedAccessExtensionEntity(True, '1.0')]
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            extentions, _LINUX_ACCESS_EXT)
        self.assertEqual('1.4', version)
        self.assertEqual(True, auto_upgrade)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_enable_boot_diagnostics_on_vm_never_enabled(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        enable_boot_diagnostics('g1', 'vm1', 'https://storage_uri1')
        self.assertTrue(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertEqual('https://storage_uri1',
                         vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm_fake, mock.ANY)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_enable_boot_diagnostics_skip_when_enabled_already(self, mock_vm_set, mock_vm_get):
        vm_fake = mock.MagicMock()
        mock_vm_get.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'https://storage_uri1'
        enable_boot_diagnostics('g1', 'vm1', 'https://storage_uri1')
        self.assertTrue(mock_vm_get.called)
        self.assertFalse(mock_vm_set.called)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
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

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_new_datadisk_default_on_vm(self, mock_vm_set, mock_vm_get):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        # stub to get the vm which has no datadisks
        vm = FakedVM(None, None)
        mock_vm_get.return_value = vm

        # execute
        attach_unmanaged_data_disk('rg1', 'vm1', True, faked_vhd_uri)

        # assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 1)
        data_disk = vm.storage_profile.data_disks[0]
        self.assertIsNone(data_disk.caching)
        self.assertEqual(data_disk.create_option, DiskCreateOptionTypes.empty)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)
        self.assertTrue(data_disk.name.startswith('vm1-'))
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_new_datadisk_custom_on_vm(self, mock_vm_set, mock_vm_get):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        faked_vhd_uri2 = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d2.vhd'

        # stub to get the vm which has no datadisks
        existing_disk = DataDisk(lun=1, vhd=faked_vhd_uri, name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        mock_vm_get.return_value = vm

        # execute
        attach_unmanaged_data_disk('rg1', 'vm1', True, faked_vhd_uri2, None, 'd2', 512, CachingTypes.read_write)

        # assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 2)
        data_disk = vm.storage_profile.data_disks[1]
        self.assertEqual(CachingTypes.read_write, data_disk.caching)
        self.assertEqual(DiskCreateOptionTypes.empty, data_disk.create_option)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)  # the existing disk has '1', so it verifes the second one be picked as '0'
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri2)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_existing_datadisk_on_vm(self, mock_vm_set, mock_vm_get):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        # stub to get the vm which has no datadisks
        vm = FakedVM()
        mock_vm_get.return_value = vm

        # execute
        attach_unmanaged_data_disk('rg1', 'vm1', False, faked_vhd_uri, disk_name='d1', caching=CachingTypes.read_only)

        # assert
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

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_deattach_disk_on_vm(self, mock_vm_set, mock_vm_get):
        # pylint: disable=line-too-long
        # stub to get the vm which has no datadisks
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        existing_disk = DataDisk(lun=1, vhd=faked_vhd_uri, name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        mock_vm_get.return_value = vm

        # execute
        detach_data_disk('rg1', 'vm1', 'd1')

        # assert
        self.assertTrue(mock_vm_get.called)
        mock_vm_set.assert_called_once_with(vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 0)

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    def test_show_vmss_instance_view(self, factory_mock):
        vm_client = mock.MagicMock()
        factory_mock.return_value = vm_client

        # execute
        get_vmss_instance_view('rg1', 'vmss1', '*')
        # assert
        vm_client.virtual_machine_scale_set_vms.list.assert_called_once_with('rg1', 'vmss1', expand='instanceView',
                                                                             select='instanceView')

    # pylint: disable=line-too-long
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._compute_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._get_keyvault_key_url', autospec=True)
    def test_enable_encryption_error_cases_handling(self, mock_get_keyvault_key_url, mock_compute_client_factory):
        faked_keyvault = '/subscriptions/01234567-1bf0-4dda-aec3-cb9272f09590/resourceGroups/rg1/providers/Microsoft.KeyVault/vaults/v1'
        os_disk = OSDisk(None, OperatingSystemTypes.linux)
        existing_disk = DataDisk(lun=1, vhd='https://someuri', name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk], os_disk=os_disk)

        compute_client_mock = mock.MagicMock()
        compute_client_mock.virtual_machines.get.return_value = vm
        mock_compute_client_factory.return_value = compute_client_mock

        mock_get_keyvault_key_url.return_value = 'https://somevaults.vault.azure.net/'

        # throw when VM has disks, but no --volume-type is specified
        with self.assertRaises(CLIError) as context:
            enable('rg1', 'vm1', 'client_id', faked_keyvault, 'client_secret')

        self.assertTrue("supply --volume-type" in str(context.exception))

        # throw when no AAD client secrets
        with self.assertRaises(CLIError) as context:
            enable('rg1', 'vm1', 'client_id', faked_keyvault)

        self.assertTrue("--aad-client-id or --aad-client-cert-thumbprint" in str(context.exception))

    @mock.patch('azure.cli.command_modules.vm.disk_encryption.set_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._compute_client_factory', autospec=True)
    def test_disable_encryption_error_cases_handling(self, mock_compute_client_factory, mock_vm_set):  # pylint: disable=unused-argument
        os_disk = OSDisk(None, OperatingSystemTypes.linux)
        existing_disk = DataDisk(lun=1, vhd='https://someuri', name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk], os_disk=os_disk)
        vm_extension = VirtualMachineExtension('westus',
                                               settings={'SequenceVersion': 1},
                                               instance_view=VirtualMachineExtensionInstanceView(
                                                   statuses=[InstanceViewStatus(message='Encryption completed successfully')],
                                                   substatuses=[InstanceViewStatus(message='{"os":"Encrypted"}')]))
        vm_extension.provisioning_state = 'Succeeded'
        compute_client_mock = mock.MagicMock()
        compute_client_mock.virtual_machines.get.return_value = vm
        compute_client_mock.virtual_machine_extensions.get.return_value = vm_extension
        mock_compute_client_factory.return_value = compute_client_mock

        # throw on disabling encryption on OS disk of a linux VM
        with self.assertRaises(CLIError) as context:
            disable('rg1', 'vm1', 'OS')

        self.assertTrue("Only data disk is supported to disable on Linux VM" in str(context.exception))

        # throw on disabling encryption on data disk, but os disk is also encrypted
        with self.assertRaises(CLIError) as context:
            disable('rg1', 'vm1', 'DATA')

        self.assertTrue("Disabling encryption on data disk can render the VM unbootable" in str(context.exception))

        # works fine to disable encryption on daat disk when OS disk is never encrypted
        vm_extension.instance_view.substatuses[0].message = '{}'
        disable('rg1', 'vm1', 'DATA')

    def test_encryption_distro_check(self):
        image = ImageReference(None, 'canonical', 'ubuntuserver', '16.04.0-LTS')
        result, msg = _check_encrypt_is_supported(image, 'data')
        self.assertTrue(result)
        self.assertEqual(None, msg)

        image = ImageReference(None, 'OpenLogic', 'CentOS', '7.2n')
        result, msg = _check_encrypt_is_supported(image, 'data')
        self.assertTrue(result)
        self.assertEqual(None, msg)

        image = ImageReference(None, 'OpenLogic', 'CentOS', '7.2')
        result, msg = _check_encrypt_is_supported(image, 'all')
        self.assertFalse(result)
        self.assertEqual(msg,
                         "Encryption might fail as current VM uses a distro not in the known list, which are '['RHEL 7.2', 'RHEL 7.3', 'CentOS 7.2n', 'Ubuntu 14.04', 'Ubuntu 16.04']'")

        image = ImageReference(None, 'OpenLogic', 'CentOS', '7.2')
        result, msg = _check_encrypt_is_supported(image, 'data')
        self.assertTrue(result)

    def test_merge_secrets(self):
        secret1 = [{
            'sourceVault': {'id': '123'},
            'vaultCertificates': [
                {
                    'certificateUrl': 'abc',
                    'certificateStore': 'My'
                }
            ]}]

        secret2 = [{
            'sourceVault': {'id': '123'},
            'vaultCertificates': [
                {
                    'certificateUrl': 'def',
                    'certificateStore': 'Machine'
                },
                {
                    'certificateUrl': 'xyz',
                    'certificateStore': 'My'
                }
            ]}]

        secret3 = [{
            'sourceVault': {'id': '456'},
            'vaultCertificates': [
                {
                    'certificateUrl': 'abc',
                    'certificateStore': 'My'
                }
            ]}]
        merged = _merge_secrets([secret1, secret2, secret3])
        self.assertIn('456', [item['sourceVault']['id'] for item in merged])
        self.assertIn('123', [item['sourceVault']['id'] for item in merged])
        vault123 = [item['vaultCertificates'] for item in merged
                    if item['sourceVault']['id'] == '123'][0]
        vault123.sort(key=lambda x: x['certificateUrl'])
        vault123Expected = [
            {
                'certificateUrl': 'abc',
                'certificateStore': 'My'
            },
            {
                'certificateUrl': 'def',
                'certificateStore': 'Machine'
            },
            {
                'certificateUrl': 'xyz',
                'certificateStore': 'My'
            }
        ]
        vault123Expected.sort(key=lambda x: x['certificateUrl'])
        self.assertListEqual(vault123Expected, vault123)

    def test_get_extension_instance_name(self):
        instance_view = mock.MagicMock()
        extension = mock.MagicMock()
        extension.type = 'publisher2.extension2'
        instance_view.extensions = [extension]

        # action
        result = _get_extension_instance_name(instance_view, 'publisher1', 'extension1')

        # assert
        self.assertEqual(result, 'extension1')


class FakedVM(object):  # pylint: disable=too-few-public-methods
    def __init__(self, nics=None, disks=None, os_disk=None):
        self.network_profile = NetworkProfile(nics)
        self.storage_profile = StorageProfile(data_disks=disks, os_disk=os_disk)
        self.location = 'westus'


class FakedAccessExtensionEntity(object):  # pylint: disable=too-few-public-methods
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version


if __name__ == '__main__':
    unittest.main()
