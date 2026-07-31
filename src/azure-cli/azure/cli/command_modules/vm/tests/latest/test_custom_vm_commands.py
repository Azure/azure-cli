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
    (attach_unmanaged_data_disk, detach_unmanaged_data_disk, get_vmss_instance_view)

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
            get_sdk_mock.assert_called_with(cli_ctx_mock, ResourceType.DATA_STORAGE_BLOB, '_blob_client#BlobClient')


class FakedVM:  # pylint: disable=too-few-public-methods
    def __init__(self, nics=None, disks=None, os_disk=None):
        self.network_profile = NetworkProfile(network_interfaces=nics)
        self.storage_profile = StorageProfile(data_disks=disks, os_disk=os_disk)
        self.location = 'westus'
        ext = mock.MagicMock()
        ext.publisher, ext.type_properties_type = 'Microsoft.Azure.Security', 'AzureDiskEncryptionForLinux'
        self.resources = [ext]
        self.instance_view = mock.MagicMock()
        self.instance_view.extensions = [ext]


class FakedAccessExtensionEntity:  # pylint: disable=too-few-public-methods
    def __init__(self, is_linux, version):
        self.name = 'VMAccessForLinux' if is_linux else 'VMAccessAgent'
        self.type_handler_version = version


if __name__ == '__main__':
    unittest.main()
