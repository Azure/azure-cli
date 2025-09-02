# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch
from knack.util import CLIError

# Import unified testing framework
from test_framework import MigrateTestCase, TestConfig

# Import functions with comprehensive mocking via the framework
with patch('azure.cli.command_modules.migrate.custom.get_powershell_executor') as mock_get_ps:
    from test_framework import create_mock_powershell_executor
    mock_get_ps.return_value = create_mock_powershell_executor()
    
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
        _get_powershell_install_instructions,
        _attempt_powershell_installation,
        _perform_platform_specific_checks
    )


class TestMigratePowerShellUtils(MigrateTestCase):
    """Test PowerShell utility functions."""

    @patch('azure.cli.command_modules.migrate.custom.platform.system', return_value='Windows')
    @patch('azure.cli.command_modules.migrate.custom.platform.version', return_value='10.0.19041')
    @patch('azure.cli.command_modules.migrate.custom.platform.python_version', return_value='3.9.7')
    def test_check_migration_prerequisites_success(self, mock_python_version, mock_version, mock_system):
        """Test successful prerequisite check."""
        result = check_migration_prerequisites(self.cmd)
        
        self.assertEqual(result['platform'], 'Windows')
        self.assertEqual(result['python_version'], '3.9.7')
        self.assertTrue(result['powershell_available'])

    @patch('azure.cli.command_modules.migrate.custom.platform.system', return_value='Windows')
    @patch('azure.cli.command_modules.migrate.custom.platform.version', return_value='10.0.19041')
    @patch('azure.cli.command_modules.migrate.custom.platform.python_version', return_value='3.9.7')
    def test_check_migration_prerequisites_powershell_not_available(self, mock_python_version, mock_version, mock_system):
        """Test prerequisite check when PowerShell is not available."""
        # Override the mock for this specific test
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

    @patch('subprocess.run')
    def test_attempt_powershell_installation_windows_success(self, mock_subprocess):
        """Test successful PowerShell installation on Windows."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = _attempt_powershell_installation('windows')
        
        self.assertIn('PowerShell Core installed via winget', result)
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    def test_attempt_powershell_installation_failure(self, mock_subprocess):
        """Test failed PowerShell installation."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = 'Installation failed'
        mock_subprocess.return_value = mock_result
        
        result = _attempt_powershell_installation('windows')
        
        self.assertIn('winget installation failed', result)

    def test_perform_platform_specific_checks_windows(self):
        """Test platform-specific checks for Windows."""
        with patch('platform.system', return_value='Windows'):
            checks = _perform_platform_specific_checks('windows')
            
            self.assertIn('Windows detected', checks[0])

    def test_perform_platform_specific_checks_linux(self):
        """Test platform-specific checks for Linux."""
        with patch('shutil.which', return_value='/usr/bin/apt'):
            checks = _perform_platform_specific_checks('linux')
            
            self.assertIn('Linux detected', checks[0])
            self.assertIn('APT package manager available', checks[1])


class TestMigrateDiscoveryCommands(unittest.TestCase):
    """Test server discovery and migration commands."""

    def setUp(self):
        self.cmd = Mock()
        self.resource_group = 'test-rg'
        self.project_name = 'test-project'

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_discovered_server_success(self, mock_get_ps_executor):
        """Test successful server discovery."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_azure_authenticated_script.return_value = {
            'stdout': '{"DiscoveredServers": [{"Name": "server1", "DisplayName": "Test Server"}], "Count": 1}',
            'stderr': ''
        }
        mock_get_ps_executor.return_value = mock_ps_executor

        result = get_discovered_server(
            self.cmd, self.resource_group, self.project_name,
            source_machine_type='VMware'
        )

        self.assertEqual(result['Count'], 1)
        self.assertEqual(len(result['DiscoveredServers']), 1)
        self.assertEqual(result['DiscoveredServers'][0]['Name'], 'server1')

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_discovered_server_authentication_failure(self, mock_get_ps_executor):
        """Test server discovery with authentication failure."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {
            'IsAuthenticated': False,
            'Error': 'Not authenticated'
        }
        mock_get_ps_executor.return_value = mock_ps_executor

        with self.assertRaises(CLIError) as context:
            get_discovered_server(
                self.cmd, self.resource_group, self.project_name
            )

        self.assertIn('Azure authentication required', str(context.exception))

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_discovered_servers_table(self, mock_get_ps_executor):
        """Test table format server discovery."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        # Should not raise an exception
        get_discovered_servers_table(
            self.cmd, self.resource_group, self.project_name
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_discovered_servers_by_display_name(self, mock_get_ps_executor):
        """Test server discovery by display name."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        get_discovered_servers_by_display_name(
            self.cmd, self.resource_group, self.project_name, 'test-server'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        # Verify the script contains the display name filter
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('test-server', script_call)


class TestMigrateReplicationCommands(unittest.TestCase):
    """Test replication and migration commands."""

    def setUp(self):
        self.cmd = Mock()
        self.resource_group = 'test-rg'
        self.project_name = 'test-project'

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_create_server_replication_by_index(self, mock_get_ps_executor):
        """Test server replication creation by server index."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        create_server_replication(
            self.cmd,
            resource_group_name=self.resource_group,
            project_name=self.project_name,
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network',
            server_index=0
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('$ServerIndex = [int]"0"', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_create_server_replication_by_name(self, mock_get_ps_executor):
        """Test server replication creation by server name."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        create_server_replication(
            self.cmd,
            resource_group_name=self.resource_group,
            project_name=self.project_name,
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network',
            server_name='test-server'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('test-server', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_replication_job_status_by_vm_name(self, mock_get_ps_executor):
        """Test getting replication job status by VM name."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        get_replication_job_status(
            self.cmd, self.resource_group, self.project_name, vm_name='test-vm'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('test-vm', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_set_replication_target_properties(self, mock_get_ps_executor):
        """Test updating replication target properties."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        set_replication_target_properties(
            self.cmd,
            resource_group_name=self.resource_group,
            project_name=self.project_name,
            vm_name='test-vm',
            target_vm_size='Standard_D2s_v3',
            target_disk_type='Premium_LRS'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('Standard_D2s_v3', script_call)
        self.assertIn('Premium_LRS', script_call)


class TestMigrateLocalCommands(unittest.TestCase):
    """Test Azure Local (Stack HCI) migration commands."""

    def setUp(self):
        self.cmd = Mock()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_create_local_disk_mapping(self, mock_get_ps_executor):
        """Test creating local disk mapping object."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        create_local_disk_mapping(
            self.cmd,
            disk_id='disk-001',
            is_os_disk=True,
            is_dynamic=False,
            size_gb=64,
            format_type='VHDX',
            physical_sector_size=512
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('disk-001', script_call)
        self.assertIn('VHDX', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_create_local_server_replication(self, mock_get_ps_executor):
        """Test creating local server replication."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        create_local_server_replication(
            self.cmd,
            resource_group_name='test-rg',
            project_name='test-project',
            server_index=0,
            target_vm_name='target-vm',
            target_storage_path_id='/subscriptions/xxx/storageContainers/container001',
            target_virtual_switch_id='/subscriptions/xxx/logicalnetworks/network001',
            target_resource_group_id='/subscriptions/xxx/resourceGroups/target-rg'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('target-vm', script_call)
        self.assertIn('storageContainers/container001', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_get_local_replication_job_by_id(self, mock_get_ps_executor):
        """Test getting local replication job by ID."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        get_local_replication_job(
            self.cmd,
            resource_group_name='test-rg',
            project_name='test-project',
            job_id='job-12345'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('job-12345', script_call)


class TestMigrateInfrastructureCommands(unittest.TestCase):
    """Test infrastructure management commands."""

    def setUp(self):
        self.cmd = Mock()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_initialize_replication_infrastructure(self, mock_get_ps_executor):
        """Test initializing replication infrastructure."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        initialize_replication_infrastructure(
            self.cmd,
            resource_group_name='test-rg',
            project_name='test-project',
            target_region='East US'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('East US', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_check_replication_infrastructure(self, mock_get_ps_executor):
        """Test checking replication infrastructure status."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        check_replication_infrastructure(
            self.cmd,
            resource_group_name='test-rg',
            project_name='test-project'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()


class TestMigrateAuthenticationCommands(unittest.TestCase):
    """Test authentication management commands."""

    def setUp(self):
        self.cmd = Mock()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_connect_azure_account_interactive(self, mock_get_ps_executor):
        """Test interactive Azure account connection."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        connect_azure_account(self.cmd)

        mock_ps_executor.execute_script_interactive.assert_called_once()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_connect_azure_account_device_code(self, mock_get_ps_executor):
        """Test device code Azure account connection."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        connect_azure_account(self.cmd, device_code=True)

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('UseDeviceAuthentication', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_connect_azure_account_service_principal(self, mock_get_ps_executor):
        """Test service principal Azure account connection."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        connect_azure_account(
            self.cmd,
            app_id='app-id',
            secret='secret',
            tenant_id='tenant-id'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('ServicePrincipal', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_disconnect_azure_account(self, mock_get_ps_executor):
        """Test Azure account disconnection."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        disconnect_azure_account(self.cmd)

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('Disconnect-AzAccount', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_set_azure_context_by_subscription_id(self, mock_get_ps_executor):
        """Test setting Azure context by subscription ID."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = {'returncode': 0}
        mock_get_ps_executor.return_value = mock_ps_executor

        set_azure_context(
            self.cmd,
            subscription_id='00000000-0000-0000-0000-000000000000'
        )

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('00000000-0000-0000-0000-000000000000', script_call)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_set_azure_context_missing_parameters(self, mock_get_ps_executor):
        """Test setting Azure context with missing parameters."""
        with self.assertRaises(CLIError) as context:
            set_azure_context(self.cmd)

        self.assertIn('subscription_id or subscription_name must be provided', str(context.exception))


class TestMigrateUtilityCommands(unittest.TestCase):
    """Test utility and resource management commands."""

    def setUp(self):
        self.cmd = Mock()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_list_resource_groups(self, mock_get_ps_executor):
        """Test listing resource groups."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        list_resource_groups(self.cmd)

        mock_ps_executor.execute_script_interactive.assert_called_once()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_check_powershell_module(self, mock_get_ps_executor):
        """Test checking PowerShell module availability."""
        mock_ps_executor = Mock()
        mock_ps_executor.execute_script_interactive.return_value = None
        mock_get_ps_executor.return_value = mock_ps_executor

        check_powershell_module(self.cmd, module_name='Az.Migrate')

        mock_ps_executor.execute_script_interactive.assert_called_once()
        script_call = mock_ps_executor.execute_script_interactive.call_args[0][0]
        self.assertIn('Az.Migrate', script_call)


class TestMigrateErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def setUp(self):
        self.cmd = Mock()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_powershell_execution_error(self, mock_get_ps_executor):
        """Test handling of PowerShell execution errors."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_azure_authenticated_script.side_effect = Exception('PowerShell error')
        mock_get_ps_executor.return_value = mock_ps_executor

        with self.assertRaises(CLIError) as context:
            get_discovered_server(
                self.cmd, 'test-rg', 'test-project'
            )

        self.assertIn('Failed to get discovered servers', str(context.exception))

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_invalid_json_response(self, mock_get_ps_executor):
        """Test handling of invalid JSON responses."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_ps_executor.execute_azure_authenticated_script.return_value = {
            'stdout': 'Invalid JSON response',
            'stderr': ''
        }
        mock_get_ps_executor.return_value = mock_ps_executor

        result = get_discovered_server(
            self.cmd, 'test-rg', 'test-project'
        )

        self.assertIn('raw_output', result)
        self.assertEqual(result['raw_output'], 'Invalid JSON response')

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_authentication_required_error(self, mock_get_ps_executor):
        """Test authentication required error."""
        mock_ps_executor = Mock()
        mock_ps_executor.check_azure_authentication.return_value = {
            'IsAuthenticated': False,
            'Error': 'Authentication token expired'
        }
        mock_get_ps_executor.return_value = mock_ps_executor

        with self.assertRaises(CLIError) as context:
            list_resource_groups(self.cmd)

        self.assertIn('Azure authentication required', str(context.exception))


if __name__ == '__main__':
    unittest.main()
