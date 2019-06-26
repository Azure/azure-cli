# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import mock
from azure.cli.command_modules.vm.custom import get_vm
from azure.cli.core.mock import DummyCli

class TestModuleDependencies(unittest.TestCase):

    @mock.patch('azure.cli.command_modules.vm.custom._compute_client_factory')
    def test_vm_module_get_vm(self, mock_compute_client_factory):
        """Sanity check to confirm get_vm() exists and returns the result of compute_client_factory.virtual_machines.get()"""
        vmname = 'testvm'
        rg = 'testrg'
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()
        return_val = 'returned val'

        mock_client = mock.MagicMock()
        mock_compute_client_factory.return_value = mock_client
        mock_client.virtual_machines.get.return_value = return_val

        val = get_vm(cmd, rg, vmname)

        mock_client.virtual_machines.get.assert_called_with(rg, vmname, expand=None)
        assert val == return_val


    def test_msrestazure_tools_parse_resource_id(self):
        from msrestazure.tools import parse_resource_id
        resource_id = '/subscriptions/88fd8cb2-8248-499e-9a2d-4929a4b0133c/resourceGroups/testrg/providers/Microsoft.Compute/disks/testdisk'
        resource = parse_resource_id(resource_id)
        
        assert 'testrg' == resource['resource_group']


    def test_msrestazure_tools_valid_resource_id(self):
        from msrestazure.tools import is_valid_resource_id
        resource_id = '/subscriptions/88fd8cb2-8248-499e-9a2d-4929a4b0133c/resourceGroups/testrg/providers/Microsoft.Compute/disks/testdisk'
        valid = is_valid_resource_id(resource_id)

        assert True == valid


    def test_msrestazure_tools_invalid_resource_id(self):
        from msrestazure.tools import is_valid_resource_id
        resource_id = '/subscriptiofd8cb2-8248-499e-9a2d-4929a4b0133c/rerg/providers/Microsoft.Compute/disks/testdisk/'
        invalid = is_valid_resource_id(resource_id)

        assert False == invalid

    
    def test_storage_module_storage_resource_identifier(self):
        from azure.cli.command_modules.storage.storage_url_helpers import StorageResourceIdentifier
        disk_uri = 'https://vhdstorage64a4b896267ec5.blob.core.windows.net/vhds/osdisk_50faed183e.vhd'
        cmd = mock.MagicMock()
        cmd.cli_ctx = DummyCli()

        storage_account = StorageResourceIdentifier(cmd.cli_ctx.cloud, disk_uri)

        assert 'vhdstorage64a4b896267ec5' == storage_account.account_name
        assert 'osdisk_50faed183e.vhd' == storage_account.blob
        assert 'vhds' == storage_account.container

if __name__ == '__main__':
    unittest.main()
