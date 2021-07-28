# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock

from knack.util import CLIError

from azure.cli.command_modules.vm.custom import (enable_boot_diagnostics, disable_boot_diagnostics,
                                                 _merge_secrets, BootLogStreamWriter,
                                                 _get_access_extension_upgrade_info,
                                                 _LINUX_ACCESS_EXT,
                                                 _WINDOWS_ACCESS_EXT,
                                                 _get_extension_instance_name,
                                                 get_boot_log)
from azure.cli.command_modules.vm.custom import \
    (attach_unmanaged_data_disk, detach_data_disk, get_vmss_instance_view)

from azure.cli.core import AzCommandsLoader
from azure.cli.core.commands import AzCliCommand


from azure.cli.command_modules.vm.disk_encryption import (encrypt_vm, decrypt_vm, encrypt_vmss, decrypt_vmss)
from azure.cli.core.profiles import get_sdk, ResourceType

from azure.cli.core.mock import DummyCli


NetworkProfile, StorageProfile, DataDisk, OSDisk, OperatingSystemTypes, InstanceViewStatus, \
    VirtualMachineExtensionInstanceView, VirtualMachineExtension, ImageReference, DiskCreateOptionTypes, \
    CachingTypes = get_sdk(DummyCli(), ResourceType.MGMT_COMPUTE, 'NetworkProfile', 'StorageProfile', 'DataDisk', 'OSDisk',
                           'OperatingSystemTypes', 'InstanceViewStatus', 'VirtualMachineExtensionInstanceView',
                           'VirtualMachineExtension', 'ImageReference', 'DiskCreateOptionTypes',
                           'CachingTypes',
                           mod='models', operation_group='virtual_machines')  # FIXME split into loading by RT


def _get_test_cmd():
    cli_ctx = DummyCli()
    loader = AzCommandsLoader(cli_ctx, resource_type=ResourceType.MGMT_COMPUTE)
    cmd = AzCliCommand(loader, 'test', None)
    cmd.command_kwargs = {'resource_type': ResourceType.MGMT_COMPUTE, 'operation_group': 'virtual_machines'}
    cmd.cli_ctx = cli_ctx
    return cmd


class TestVmCustom(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_get_access_extension_upgrade_info(self):

        # when there is no extension installed on linux vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _LINUX_ACCESS_EXT)
        self.assertEqual('Microsoft.OSTCExtensions', publisher)
        self.assertEqual('1.5', version)
        self.assertEqual(None, auto_upgrade)

        # when there is no extension installed on windows vm, use the version we like
        publisher, version, auto_upgrade = _get_access_extension_upgrade_info(
            None, _WINDOWS_ACCESS_EXT)
        self.assertEqual('Microsoft.Compute', publisher)
        self.assertEqual('2.4', version)
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
        self.assertEqual('1.5', version)
        self.assertEqual(True, auto_upgrade)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_enable_boot_diagnostics_on_vm_never_enabled(self, mock_vm_set, mock_vm_get_to_update):
        vm_fake = mock.MagicMock()
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm_fake
        enable_boot_diagnostics(cmd, 'g1', 'vm1', 'https://storage_uri1')
        self.assertTrue(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertEqual('https://storage_uri1',
                         vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm_fake, mock.ANY)

    # @mock.patch('azure.cli.command_modules.vm.custom.get_vm', autospec=True)
    # @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    # def test_enable_boot_diagnostics_skip_when_enabled_already(self, mock_vm_set, mock_vm_get):
    #     vm_fake = mock.MagicMock()
    #     cmd = _get_test_cmd()
    #     mock_vm_get.return_value = vm_fake
    #     vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
    #     vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'https://storage_uri1'
    #     enable_boot_diagnostics(cmd, 'g1', 'vm1', 'https://storage_uri1')
    #     self.assertTrue(mock_vm_get.called)
    #     self.assertFalse(mock_vm_set.called)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_disable_boot_diagnostics_on_vm(self, mock_vm_set, mock_vm_get_to_update):
        vm_fake = mock.MagicMock()
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm_fake
        vm_fake.diagnostics_profile.boot_diagnostics.enabled = True
        vm_fake.diagnostics_profile.boot_diagnostics.storage_uri = 'storage_uri1'
        disable_boot_diagnostics(cmd, 'g1', 'vm1')
        self.assertFalse(vm_fake.diagnostics_profile.boot_diagnostics.enabled)
        self.assertIsNone(vm_fake.diagnostics_profile.boot_diagnostics.storage_uri)
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm_fake, mock.ANY)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_new_datadisk_default_on_vm(self, mock_vm_set, mock_vm_get_to_update):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        # stub to get the vm which has no datadisks
        vm = FakedVM(None, None)
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm

        # execute
        attach_unmanaged_data_disk(cmd, 'rg1', 'vm1', True, faked_vhd_uri)

        # assert
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 1)
        data_disk = vm.storage_profile.data_disks[0]
        self.assertIsNone(data_disk.caching)
        self.assertEqual(data_disk.create_option, DiskCreateOptionTypes.empty)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)
        self.assertTrue(data_disk.name.startswith('vm1-'))
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_new_datadisk_custom_on_vm(self, mock_vm_set, mock_vm_get_to_update):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        faked_vhd_uri2 = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d2.vhd'

        # stub to get the vm which has no datadisks
        existing_disk = DataDisk(lun=1, vhd=faked_vhd_uri, name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm

        # execute
        attach_unmanaged_data_disk(cmd, 'rg1', 'vm1', True, faked_vhd_uri2, None, 'd2', 512, CachingTypes.read_write)

        # assert
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 2)
        data_disk = vm.storage_profile.data_disks[1]
        self.assertEqual(CachingTypes.read_write, data_disk.caching)
        self.assertEqual(DiskCreateOptionTypes.empty, data_disk.create_option)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)  # the existing disk has '1', so it verifes the second one be picked as '0'
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri2)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_attach_existing_datadisk_on_vm(self, mock_vm_set, mock_vm_get_to_update):
        # pylint: disable=line-too-long
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'

        # stub to get the vm which has no datadisks
        vm = FakedVM()
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm

        # execute
        attach_unmanaged_data_disk(cmd, 'rg1', 'vm1', False, faked_vhd_uri, disk_name='d1', caching=CachingTypes.read_only)

        # assert
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 1)
        data_disk = vm.storage_profile.data_disks[0]
        self.assertEqual(CachingTypes.read_only, data_disk.caching)
        self.assertEqual(DiskCreateOptionTypes.attach, data_disk.create_option)
        self.assertIsNone(data_disk.image)
        self.assertEqual(data_disk.lun, 0)
        self.assertEqual(data_disk.name, 'd1')
        self.assertEqual(data_disk.vhd.uri, faked_vhd_uri)

    @mock.patch('azure.cli.command_modules.vm.custom.get_vm_to_update', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.set_vm', autospec=True)
    def test_deattach_disk_on_vm(self, mock_vm_set, mock_vm_get_to_update):
        # pylint: disable=line-too-long
        # stub to get the vm which has no datadisks
        faked_vhd_uri = 'https://your_stoage_account_name.blob.core.windows.net/vhds/d1.vhd'
        existing_disk = DataDisk(lun=1, vhd=faked_vhd_uri, name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk])
        cmd = _get_test_cmd()
        mock_vm_get_to_update.return_value = vm

        # execute
        detach_data_disk(cmd, 'rg1', 'vm1', 'd1')

        # assert
        self.assertTrue(mock_vm_get_to_update.called)
        mock_vm_set.assert_called_once_with(cmd, vm)
        self.assertEqual(len(vm.storage_profile.data_disks), 0)

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    def test_show_vmss_instance_view(self, factory_mock):
        vm_client = mock.MagicMock()
        cmd = _get_test_cmd()
        factory_mock.return_value = vm_client

        # execute
        get_vmss_instance_view(cmd, 'rg1', 'vmss1', '*')
        # assert
        vm_client.virtual_machine_scale_set_vms.list.assert_called_once_with('rg1', 'vmss1', expand='instanceView',
                                                                             select='instanceView')

    # pylint: disable=line-too-long
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._compute_client_factory', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._get_keyvault_key_url', autospec=True)
    def test_enable_encryption_error_cases_handling(self, mock_get_keyvault_key_url, mock_compute_client_factory):
        faked_keyvault = '/subscriptions/01234567-1bf0-4dda-aec3-cb9272f09590/resourceGroups/rg1/providers/Microsoft.KeyVault/vaults/v1'
        os_disk = OSDisk(create_option=None, os_type=OperatingSystemTypes.linux)
        existing_disk = DataDisk(lun=1, vhd='https://someuri', name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk], os_disk=os_disk)
        cmd = _get_test_cmd()

        compute_client_mock = mock.MagicMock()
        compute_client_mock.virtual_machines.get.return_value = vm
        mock_compute_client_factory.return_value = compute_client_mock

        mock_get_keyvault_key_url.return_value = 'https://somevaults.vault.azure.net/'

        # throw when VM has disks, but no --volume-type is specified
        with self.assertRaises(CLIError) as context:
            encrypt_vm(cmd, 'rg1', 'vm1', 'client_id', faked_keyvault, 'client_secret')

        self.assertTrue("supply --volume-type" in str(context.exception))

        # throw when no AAD client secrets
        with self.assertRaises(CLIError) as context:
            encrypt_vm(cmd, 'rg1', 'vm1', 'client_id', faked_keyvault)

        self.assertTrue("--aad-client-cert-thumbprint or --aad-client-secret" in str(context.exception))

    @mock.patch('azure.cli.command_modules.vm.disk_encryption.set_vm', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.disk_encryption._compute_client_factory', autospec=True)
    def test_disable_encryption_error_cases_handling(self, mock_compute_client_factory, mock_vm_set):  # pylint: disable=unused-argument
        os_disk = OSDisk(create_option=None, os_type=OperatingSystemTypes.linux)
        existing_disk = DataDisk(lun=1, vhd='https://someuri', name='d1', create_option=DiskCreateOptionTypes.empty)
        vm = FakedVM(None, [existing_disk], os_disk=os_disk)
        cmd = _get_test_cmd()
        vm_extension = VirtualMachineExtension(location='westus',
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
        with self.assertRaises(CLIError):
            decrypt_vm(cmd, 'rg1', 'vm1', 'OS')

        # self.assertTrue("Only Data disks can have encryption disabled in a Linux VM." in str(context.exception))

        # works fine to disable encryption on daat disk when OS disk is never encrypted
        vm_extension.instance_view.substatuses[0].message = '{}'
        decrypt_vm(cmd, 'rg1', 'vm1', 'DATA')

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

    def test_get_extension_instance_name_when_type_none(self):
        instance_view = mock.MagicMock()
        extension = mock.MagicMock()
        extension.type = None
        instance_view.extensions = [extension]

        # action
        result = _get_extension_instance_name(instance_view, 'na', 'extension-name')

        # assert
        self.assertEqual(result, 'extension-name')


class TestVMBootLog(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.vm.custom.logger.warning')
    def test_vm_boot_log_handle_unicode(self, logger_warning__mock):
        import sys
        writer = BootLogStreamWriter(sys.stdout)
        writer.write('hello')
        writer.write(u'\u54c8')  # a random unicode trying to fail default output

        # we are good once we are here

    @mock.patch('azure.cli.core.profiles.get_sdk', autospec=True)
    def test_vm_boot_log_init_storage_sdk(self, get_sdk_mock):

        class ErrorToExitCommandEarly(Exception):
            pass

        cmd_mock = mock.MagicMock()
        cli_ctx_mock = mock.MagicMock()
        cmd_mock.cli_ctx = cli_ctx_mock
        get_sdk_mock.side_effect = ErrorToExitCommandEarly()

        try:
            get_boot_log(cmd_mock, 'rg1', 'vm1')
            self.fail("'get_boot_log' didn't exit early")
        except ErrorToExitCommandEarly:
            get_sdk_mock.assert_called_with(cli_ctx_mock, ResourceType.DATA_STORAGE, 'blob.blockblobservice#BlockBlobService')


class FakedVM(object):  # pylint: disable=too-few-public-methods
    def __init__(self, nics=None, disks=None, os_disk=None):
        self.network_profile = NetworkProfile(network_interfaces=nics)
        self.storage_profile = StorageProfile(data_disks=disks, os_disk=os_disk)
        self.location = 'westus'
        ext = mock.MagicMock()
        ext.publisher, ext.type_properties_type = 'Microsoft.Azure.Security', 'AzureDiskEncryptionForLinux'
        self.resources = [ext]
        self.instance_view = mock.MagicMock()
        self.instance_view.extensions = [ext]


class FakedAccessExtensionEntity(object):  # pylint: disable=too-few-public-methods
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version


if __name__ == '__main__':
    unittest.main()
