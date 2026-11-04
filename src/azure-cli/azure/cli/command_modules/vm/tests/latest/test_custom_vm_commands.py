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

    @mock.patch('azure.cli.command_modules.vm.custom.BootLogStreamWriter', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom._get_storage_management_client', autospec=True)
    @mock.patch('azure.cli.command_modules.vm.custom.get_instance_view', autospec=True)
    @mock.patch('azure.cli.core.profiles.get_sdk', autospec=True)
    def test_vm_boot_log_uses_keys_property(self, get_sdk_mock, get_instance_view_mock,
                                            get_storage_client_mock, stream_writer_mock):
        # azure-mgmt-storage>=25.0.0 renamed the account keys list from `keys` to
        # `keys_property` (`.keys` now resolves to `MutableMapping.keys`).
        blob_url = 'https://mystorage.blob.core.windows.net/bootdiagnostics/vm1.serialconsole.log'
        get_instance_view_mock.return_value = {
            'instanceView': {
                'bootDiagnostics': {'serialConsoleLogBlobUri': blob_url}
            }
        }

        storage_account = mock.MagicMock()
        storage_account.primary_endpoints.blob = 'https://mystorage.blob.core.windows.net/'
        storage_account.id = '/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.Storage/storageAccounts/mystorage'
        storage_account.name = 'mystorage'

        storage_key = mock.MagicMock()
        storage_key.value = 'the-account-key'
        list_keys_result = mock.MagicMock(spec=['keys_property'])
        list_keys_result.keys_property = [storage_key]

        storage_client_mock = get_storage_client_mock.return_value
        storage_client_mock.storage_accounts.list.return_value = [storage_account]
        storage_client_mock.storage_accounts.list_keys.return_value = list_keys_result

        blob_client_mock = mock.MagicMock()
        blob_client_class_mock = mock.MagicMock()
        blob_client_class_mock.from_blob_url.return_value = blob_client_mock
        get_sdk_mock.return_value = blob_client_class_mock

        cmd_mock = mock.MagicMock()
        get_boot_log(cmd_mock, 'rg1', 'vm1')

        blob_client_class_mock.from_blob_url.assert_called_once_with(
            blob_url=blob_url, credential='the-account-key')
        blob_client_mock.download_blob.assert_called_once_with(max_concurrency=1)
        blob_client_mock.download_blob.return_value.readinto.assert_called_once()


class TestVmssGenericUpdateOptionalCollections(unittest.TestCase):
    """Regression tests for https://github.com/Azure/azure-cli/issues/34133"""

    _OPTIONAL_COLLECTIONS = ['applicationGatewayBackendAddressPools', 'applicationSecurityGroups',
                             'loadBalancerBackendAddressPools', 'loadBalancerInboundNatPools']
    _POOL_ID = ('/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-lb/providers/'
                'Microsoft.Network/loadBalancers/lb1/backendAddressPools/vmss1-pool')

    @staticmethod
    def _ip_config(name, **collections):
        ip_config = {'name': name, 'primary': True, 'subnet': {'id': 'subnet-id-' + name}}
        ip_config.update(collections)
        return ip_config

    @classmethod
    def _vmss(cls, nic_configs):
        return {
            'name': 'vmss1',
            'tags': {'env': 'test'},
            'virtualMachineProfile': {
                'storageProfile': {'imageReference': {'id': 'image-id'}},
                'networkProfile': {'networkInterfaceConfigurations': nic_configs}
            }
        }

    def _get_vmss(self, show_result, instance_id=None):
        from azure.cli.command_modules.vm.custom import get_vmss_modified_by_aaz
        cmd = mock.MagicMock()
        if instance_id is not None:
            with mock.patch('azure.cli.command_modules.vm.operations.vmss_vms.VMSSVMSShow') as show_mock:
                show_mock.return_value.return_value = show_result
                return get_vmss_modified_by_aaz(cmd, 'rg1', 'vmss1', instance_id=instance_id)

        from azure.cli.command_modules.vm.operations.vmss import VMSSShow, VMSSShowForUpdate
        with mock.patch.object(VMSSShow, '_output', return_value=show_result):
            show = object.__new__(VMSSShowForUpdate)
            return show._output()

    @staticmethod
    def _path(nic_index, ip_index, collection):
        return ('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[{}].ipConfigurations[{}].{}'
                .format(nic_index, ip_index, collection))

    def test_vmss_generic_update_add_to_collection_states(self):
        from azure.cli.core.commands.arm import add_properties
        existing = {'id': 'existing-pool-id'}
        cases = [
            ('omitted', {}, [{'id': self._POOL_ID}]),
            ('null', {'loadBalancerBackendAddressPools': None}, [{'id': self._POOL_ID}]),
            ('empty', {'loadBalancerBackendAddressPools': []}, [{'id': self._POOL_ID}]),
            ('populated', {'loadBalancerBackendAddressPools': [existing]}, [existing, {'id': self._POOL_ID}]),
        ]
        for case, collections, expected in cases:
            with self.subTest(case=case):
                vmss = self._get_vmss(self._vmss([{'name': 'nic1', 'ipConfigurations': [
                    self._ip_config('ipconfig1', **collections)]}]))
                add_properties(vmss, [self._path(0, 0, 'loadBalancerBackendAddressPools'),
                                      'id={}'.format(self._POOL_ID)], False)

                ip_config = vmss['virtualMachineProfile']['networkProfile'][
                    'networkInterfaceConfigurations'][0]['ipConfigurations'][0]
                self.assertEqual(ip_config['loadBalancerBackendAddressPools'], expected)
                self.assertEqual(ip_config['name'], 'ipconfig1')
                self.assertEqual(ip_config['subnet'], {'id': 'subnet-id-ipconfig1'})
                self.assertTrue(ip_config['primary'])
                self.assertEqual(vmss['tags'], {'env': 'test'})

    def test_vmss_generic_update_existing_collections_unchanged(self):
        empty_list = []
        populated = [{'id': 'pool-a'}, {'id': 'pool-b'}]
        vmss = self._get_vmss(self._vmss([{'name': 'nic1', 'ipConfigurations': [self._ip_config(
            'ipconfig1', loadBalancerBackendAddressPools=populated,
            applicationSecurityGroups=empty_list, loadBalancerInboundNatPools=None)]}]))

        ip_config = vmss['virtualMachineProfile']['networkProfile'][
            'networkInterfaceConfigurations'][0]['ipConfigurations'][0]
        self.assertIs(ip_config['loadBalancerBackendAddressPools'], populated)
        self.assertEqual(ip_config['loadBalancerBackendAddressPools'], [{'id': 'pool-a'}, {'id': 'pool-b'}])
        self.assertIs(ip_config['applicationSecurityGroups'], empty_list)
        self.assertIsNone(ip_config['loadBalancerInboundNatPools'])

    def test_vmss_generic_update_add_all_collections_on_all_ip_configs(self):
        from azure.cli.core.commands.arm import add_properties
        vmss = self._get_vmss(self._vmss([
            {'name': 'nic1', 'ipConfigurations': [self._ip_config('nic1-ip1'), self._ip_config('nic1-ip2')]},
            {'name': 'nic2', 'ipConfigurations': [self._ip_config('nic2-ip1')]},
        ]))

        for nic_index, ip_index in [(0, 0), (0, 1), (1, 0)]:
            for collection in self._OPTIONAL_COLLECTIONS:
                with self.subTest(nic=nic_index, ip_config=ip_index, collection=collection):
                    item_id = '{}-{}-{}'.format(nic_index, ip_index, collection)
                    add_properties(vmss, [self._path(nic_index, ip_index, collection), 'id=' + item_id], False)
                    ip_config = vmss['virtualMachineProfile']['networkProfile'][
                        'networkInterfaceConfigurations'][nic_index]['ipConfigurations'][ip_index]
                    self.assertEqual(ip_config[collection], [{'id': item_id}])

    def test_vmss_generic_update_missing_network_levels_not_synthesized(self):
        cases = [
            ('no network profile', {'name': 'vmss1', 'virtualMachineProfile': {}}),
            ('no virtual machine profile', {'name': 'vmss1'}),
            ('no nic configurations', {'name': 'vmss1', 'virtualMachineProfile': {'networkProfile': {}}}),
            ('no ip configurations', self._vmss([{'name': 'nic1'}])),
        ]
        for case, show_result in cases:
            with self.subTest(case=case):
                import copy
                expected = copy.deepcopy(show_result).get('virtualMachineProfile')
                vmss = self._get_vmss(show_result)
                if expected is None:
                    self.assertNotIn('virtualMachineProfile', vmss)
                else:
                    self.assertEqual(vmss['virtualMachineProfile'].get('networkProfile'), expected.get('networkProfile'))

    def test_vmss_generic_update_invalid_terminal_property_still_fails(self):
        from azure.cli.core.commands.arm import add_properties
        vmss = self._get_vmss(self._vmss([{'name': 'nic1', 'ipConfigurations': [self._ip_config('ipconfig1')]}]))
        with self.assertRaises(CLIError):
            add_properties(vmss, [self._path(0, 0, 'misspelledBackendAddressPools'), 'id=x'], False)

    def test_vmss_vm_instance_generic_update_not_normalized(self):
        instance = {
            'name': 'vmss1_0',
            'storageProfile': {'imageReference': {'id': 'image-id'}},
            'networkProfileConfiguration': {'networkInterfaceConfigurations': [
                {'name': 'nic1', 'ipConfigurations': [{'name': 'ipconfig1'}]}]}
        }
        result = self._get_vmss(instance, instance_id='0')
        ip_config = result['networkProfileConfiguration']['networkInterfaceConfigurations'][0]['ipConfigurations'][0]
        self.assertEqual(ip_config, {'name': 'ipconfig1'})


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
