# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.cli.command_modules.vm.custom import _parse_vm_file_path, vm_cp

class TestVmCp(unittest.TestCase):

    def test_parse_vm_file_path(self):
        # Local path
        self.assertIsNone(_parse_vm_file_path("/path/to/file"))
        self.assertIsNone(_parse_vm_file_path("C:\\path\\to\\file"))
        
        # VM path: vm:path
        self.assertEqual(_parse_vm_file_path("myvm:/tmp/file"), (None, "myvm", "/tmp/file"))
        
        # VM path: rg:vm:path
        self.assertEqual(_parse_vm_file_path("myrg:myvm:/tmp/file"), ("myrg", "myvm", "/tmp/file"))
        
        # Edge cases
        self.assertIsNone(_parse_vm_file_path("justfile"))
        self.assertEqual(_parse_vm_file_path("vm:C:\\path"), (None, "vm", "C:\\path"))
        self.assertEqual(_parse_vm_file_path("rg:vm:C:\\path"), ("rg", "vm", "C:\\path"))

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    @mock.patch('azure.cli.command_modules.vm.custom.get_storage_client_factory')
    @mock.patch('azure.cli.command_modules.vm.custom.create_short_lived_blob_sas_v2')
    @mock.patch('azure.cli.command_modules.vm.custom.upload_blob')
    def test_vm_cp_upload_basic(self, mock_upload, mock_sas, mock_storage_factory, mock_compute_factory):
        cmd = mock.MagicMock()
        cmd.cli_ctx.cloud.suffixes.storage_endpoint = 'core.windows.net'
        
        # Mock compute client
        mock_compute = mock.MagicMock()
        mock_compute_factory.return_value = mock_compute
        
        vm_obj = mock.MagicMock()
        vm_obj.storage_profile.os_disk.os_type.lower.return_value = 'linux'
        mock_compute.virtual_machines.get.return_value = vm_obj
        
        # Mock storage client
        mock_storage = mock.MagicMock()
        mock_storage_factory.return_value = mock_storage
        
        sa = mock.MagicMock()
        sa.name = 'mystorage'
        mock_storage.storage_accounts.list_by_resource_group.return_value = [sa]
        
        key = mock.MagicMock()
        key.value = 'key1'
        mock_storage.storage_accounts.list_keys.return_value.keys = [key]
        
        # Mock blob client
        with mock.patch('azure.cli.command_modules.vm.custom.BlobServiceClient') as mock_blob_service:
            mock_container = mock.MagicMock()
            mock_blob_service.from_connection_string.return_value.get_container_client.return_value = mock_container
            
            # Execute
            vm_cp(cmd, source="local.txt", destination="myrg:myvm:/tmp/remote.txt")
            
            # Verify
            mock_upload.assert_called_once()
            mock_compute.virtual_machines.get.assert_called_with("myrg", "myvm")

if __name__ == '__main__':
    unittest.main()
