# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from knack.util import CLIError

from test_framework import MigrateTestCase, TestConfig
from azure.cli.command_modules.migrate.custom import (
    check_migration_prerequisites,
    get_discovered_server,
    get_discovered_servers_table,
    create_server_replication,
    get_discovered_servers_by_display_name,
    get_replication_job_status,
    set_replication_target_properties,
    create_local_disk_mapping,
    create_local_server_replication,
    get_local_replication_job,
    list_resource_groups,
    check_powershell_module,
    initialize_replication_infrastructure,
    check_replication_infrastructure,
    connect_azure_account,
    disconnect_azure_account,
    set_azure_context,
    _get_powershell_install_instructions
)


class TestMigratePowerShellUtils(MigrateTestCase):
    """Test PowerShell utility functions."""

    def test_check_migration_prerequisites_success(self):
        """Test successful prerequisite check."""
        result = check_migration_prerequisites(self.cmd)
        
        self.assertEqual(result['platform'], 'Windows')
        self.assertEqual(result['python_version'], '3.9.7')
        self.assertTrue(result['powershell_available'])

    def test_check_migration_prerequisites_powershell_not_available(self):
        """Test prerequisite check when PowerShell is not available."""
        self.mock_ps_executor.check_powershell_availability.return_value = (False, None)
        
        result = check_migration_prerequisites(self.cmd)
        
        self.assertEqual(result['platform'], 'Windows')
        self.assertFalse(result['powershell_available'])

    def test_get_powershell_install_instructions(self):
        """Test PowerShell installation instructions for different platforms."""
        windows_instructions = _get_powershell_install_instructions('windows')
        linux_instructions = _get_powershell_install_instructions('linux')
        darwin_instructions = _get_powershell_install_instructions('darwin')
        
        self.assertIn('winget install', windows_instructions)
        self.assertIn('sudo apt install', linux_instructions)
        self.assertIn('brew install', darwin_instructions)


class TestMigrateDiscoveryCommands(MigrateTestCase):
    """Test server discovery and listing commands."""

    def test_get_discovered_server(self):
        """Test getting a specific discovered server."""
        get_discovered_server(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            server_id=TestConfig.SAMPLE_SERVER_NAME
        )
        
    def test_get_discovered_servers_table(self):
        """Test getting discovered servers in table format."""
        get_discovered_servers_table(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME
        )
        

    def test_get_discovered_servers_by_display_name(self):
        """Test getting servers by display name."""
        get_discovered_servers_by_display_name(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            display_name=TestConfig.SAMPLE_SERVER_NAME
        )

class TestMigrateReplicationCommands(MigrateTestCase):
    """Test server replication and migration commands."""

    def test_create_server_replication(self):
        """Test creating server replication."""
        create_server_replication(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network',
            server_index=0
        )
        
    def test_get_replication_job_status(self):
        """Test getting replication job status."""
        get_replication_job_status(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            vm_name='test-vm'
        )
        
    def test_set_replication_target_properties(self):
        """Test setting replication target properties."""
        set_replication_target_properties(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            vm_name='test-vm',
            target_vm_size='Standard_D2s_v3',
            target_disk_type='Premium_LRS'
        )
class TestMigrateLocalCommands(MigrateTestCase):
    """Test local migration commands."""

    def test_create_local_disk_mapping(self):
        """Test creating local disk mapping."""
        create_local_disk_mapping(
            self.cmd,
            disk_id='disk-001',
            is_os_disk=True,
            is_dynamic=False,
            size_gb=64,
            format_type='VHDX',
            physical_sector_size=512
        )
        
    def test_create_local_server_replication(self):
        """Test creating local server replication."""
        create_local_server_replication(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            server_index=0,
            target_vm_name='target-vm',
            target_storage_path_id='/subscriptions/xxx/storageContainers/container001',
            target_virtual_switch_id='/subscriptions/xxx/logicalnetworks/network001',
            target_resource_group_id='/subscriptions/xxx/resourceGroups/target-rg'
        )
        
    def test_get_local_replication_job(self):
        """Test getting local replication job status."""
        get_local_replication_job(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            job_id='job-12345'
        )
        
class TestMigrateInfrastructureCommands(MigrateTestCase):
    """Test infrastructure management commands."""

    def test_initialize_replication_infrastructure(self):
        """Test initializing replication infrastructure."""
        initialize_replication_infrastructure(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME,
            target_region='East US'
        )
        

    def test_check_replication_infrastructure(self):
        """Test checking replication infrastructure status."""
        check_replication_infrastructure(
            self.cmd,
            resource_group_name=TestConfig.SAMPLE_RESOURCE_GROUP,
            project_name=TestConfig.SAMPLE_PROJECT_NAME
        )
class TestMigrateAuthenticationCommands(MigrateTestCase):
    """Test authentication management commands."""

    def test_connect_azure_account(self):
        """Test Azure account connection."""
        connect_azure_account(self.cmd)

    def test_disconnect_azure_account(self):
        """Test Azure account disconnection."""
        disconnect_azure_account(self.cmd)

    def test_set_azure_context(self):
        """Test setting Azure context."""
        set_azure_context(
            self.cmd,
            subscription_id=TestConfig.SAMPLE_SUBSCRIPTION_ID
        )
class TestMigrateUtilityCommands(MigrateTestCase):
    """Test utility and helper commands."""

    def test_list_resource_groups(self):
        """Test listing resource groups."""
        list_resource_groups(self.cmd)

    def test_check_powershell_module(self):
        """Test checking PowerShell module availability."""
        check_powershell_module(
            self.cmd,
            module_name="Az.Migrate"
        )
class TestMigrateErrorHandling(MigrateTestCase):
    """Test error handling and edge cases."""

    def test_invalid_parameters(self):
        """Test handling of invalid parameters."""
        try:
            result = get_discovered_server(
                self.cmd,
                resource_group_name="",
                project_name="test-project",
                server_id="test-server"
            )
            self.assertIsNotNone(result)
        except (ValueError, CLIError):
            pass


if __name__ == '__main__':
    unittest.main()
