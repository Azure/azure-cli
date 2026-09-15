# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.cli.command_modules.vm.custom import _parse_vm_file_path, vm_cp

class TestVmCp(unittest.TestCase):

    def test_parse_vm_file_path(self):
        # Local paths (non-VM)
        self.assertIsNone(_parse_vm_file_path("/path/to/file"))
        self.assertIsNone(_parse_vm_file_path("C:\\path\\to\\file"))
        self.assertIsNone(_parse_vm_file_path("D:/path/to/file"))
        self.assertIsNone(_parse_vm_file_path("justfile"))
        
        # VM path: vm:path
        self.assertEqual(_parse_vm_file_path("myvm:/tmp/file"), (None, "myvm", "/tmp/file"))
        
        # VM path: rg:vm:path
        self.assertEqual(_parse_vm_file_path("myrg:myvm:/tmp/file"), ("myrg", "myvm", "/tmp/file"))
        
        # VM path with colons in the path component
        self.assertEqual(_parse_vm_file_path("vm:C:\\remote\\path"), (None, "vm", "C:\\remote\\path"))
        self.assertEqual(_parse_vm_file_path("rg:vm:C:\\remote\\path"), ("rg", "vm", "C:\\remote\\path"))

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_sa')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_sa_for_keys')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_blob_service')
    @mock.patch('azure.cli.command_modules.storage.util.create_short_lived_blob_sas_v2')
    @mock.patch('azure.cli.command_modules.storage.operations.blob.upload_blob')
    def test_vm_cp_upload_basic(self, mock_upload, mock_sas, mock_blob_factory, mock_keys_factory, mock_sa_factory, mock_compute_factory):
        cmd = mock.MagicMock()
        cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.windows.net'
        
        # Mock compute client
        mock_compute = mock.MagicMock()
        mock_compute_factory.return_value = mock_compute
        
        vm_obj = mock.MagicMock()
        vm_obj.name = "myvm"
        vm_obj.storage_profile.os_disk.os_type.lower.return_value = 'linux'
        vm_obj.id = "/subscriptions/sub/resourceGroups/myrg/providers/Microsoft.Compute/virtualMachines/myvm"
        mock_compute.virtual_machines.get.return_value = vm_obj
        mock_compute.virtual_machines.list_all.return_value = [vm_obj]
        
        # Mock storage clients
        mock_sa = mock.MagicMock()
        mock_sa_factory.return_value = mock_sa
        
        sa = mock.MagicMock()
        sa.name = 'mystorage'
        sa.id = "/subscriptions/sub/resourceGroups/myrg/providers/Microsoft.Storage/storageAccounts/mystorage"
        mock_sa.list.return_value = [sa]
        
        mock_keys = mock.MagicMock()
        mock_keys_factory.return_value = mock_keys
        key = mock.MagicMock()
        key.value = 'key1'
        mock_keys.list_keys.return_value.keys = [key]
        
        # Mock blob service
        mock_blob_service = mock.MagicMock()
        mock_blob_factory.return_value = mock_blob_service
        mock_container = mock.MagicMock()
        mock_blob_service.get_container_client.return_value = mock_container
        mock_blob = mock.MagicMock()
        mock_container.get_blob_client.return_value = mock_blob
        
        # Execute
        with mock.patch('azure.cli.command_modules.vm.aaz.latest.vm.run_command.Invoke') as mock_invoke:
            mock_invoke.return_value.return_value = {'value': [{'message': 'success'}]}
            vm_cp(cmd, source="local.txt", destination="myrg:myvm:/tmp/remote.txt")
            
            # Verify
            mock_upload.assert_called_once()
            mock_compute.virtual_machines.get.assert_called()
            mock_blob.delete_blob.assert_called_once()

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_sa')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_sa_for_keys')
    @mock.patch('azure.cli.command_modules.storage._client_factory.cf_blob_service')
    @mock.patch('azure.cli.command_modules.storage.operations.blob.download_blob')
    def test_vm_cp_download_basic(self, mock_download, mock_blob_factory, mock_keys_factory, mock_sa_factory, mock_compute_factory):
        cmd = mock.MagicMock()
        cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.windows.net'
        
        # Mock compute client
        mock_compute = mock.MagicMock()
        mock_compute_factory.return_value = mock_compute
        
        vm_obj = mock.MagicMock()
        vm_obj.name = "myvm"
        vm_obj.storage_profile.os_disk.os_type.lower.return_value = 'linux'
        vm_obj.id = "/subscriptions/sub/resourceGroups/myrg/providers/Microsoft.Compute/virtualMachines/myvm"
        mock_compute.virtual_machines.get.return_value = vm_obj
        
        # Mock storage clients
        mock_sa = mock.MagicMock()
        mock_sa_factory.return_value = mock_sa
        
        sa = mock.MagicMock()
        sa.name = 'mystorage'
        sa.id = "/subscriptions/sub/resourceGroups/myrg/providers/Microsoft.Storage/storageAccounts/mystorage"
        mock_sa.list.return_value = [sa]
        
        mock_keys = mock.MagicMock()
        mock_keys_factory.return_value = mock_keys
        key = mock.MagicMock()
        key.value = 'key1'
        mock_keys.list_keys.return_value.keys = [key]
        
        # Mock blob service
        mock_blob_service = mock.MagicMock()
        mock_blob_factory.return_value = mock_blob_service
        mock_container = mock.MagicMock()
        mock_blob_service.get_container_client.return_value = mock_container
        mock_blob = mock.MagicMock()
        mock_container.get_blob_client.return_value = mock_blob
        
        # Execute
        with mock.patch('azure.cli.command_modules.vm.aaz.latest.vm.run_command.Invoke') as mock_invoke:
            mock_invoke.return_value.return_value = {'value': [{'message': 'success'}]}
            vm_cp(cmd, source="myrg:myvm:/tmp/remote.txt", destination="local.txt")
            
            # Verify
            mock_invoke.assert_called_once()
            mock_download.assert_called_once()
            mock_blob.delete_blob.assert_called_once()

if __name__ == '__main__':
    unittest.main()

