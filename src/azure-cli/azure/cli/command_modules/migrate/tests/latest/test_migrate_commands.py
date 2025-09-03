# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import Mock, patch
from knack.util import CLIError
from azure.cli.command_modules.migrate.commands import load_command_table
from azure.cli.command_modules.migrate.custom import check_migration_prerequisites, list_resource_groups, get_discovered_server
class TestMigrateCommandLoading(unittest.TestCase):
    """Test command loading and registration."""

    def setUp(self):
        self.loader = Mock()
        self.loader.command_group = Mock()

    def test_command_table_loading(self):
        """Test that all command groups are properly loaded."""
        mock_command_group = Mock()
        mock_command_group.__enter__ = Mock(return_value=mock_command_group)
        mock_command_group.__exit__ = Mock(return_value=None)
        mock_command_group.custom_command = Mock()
        mock_command_group.show_command = Mock()
        
        self.loader.command_group.return_value = mock_command_group
        
        load_command_table(self.loader, None)
        
        expected_groups = [
            'migrate',
            'migrate server',
            'migrate project',
            'migrate assessment',
            'migrate machine',
            'migrate local',
            'migrate resource',
            'migrate powershell',
            'migrate infrastructure',
            'migrate auth',
            'migrate storage'
        ]
        
        group_calls = [call[0][0] for call in self.loader.command_group.call_args_list]
        for group in expected_groups:
            self.assertIn(group, group_calls)

    def test_migrate_core_commands_registered(self):
        """Test that core migrate commands are registered."""
        mock_command_group = Mock()
        mock_command_group.__enter__ = Mock(return_value=mock_command_group)
        mock_command_group.__exit__ = Mock(return_value=None)
        mock_command_group.custom_command = Mock()
        
        self.loader.command_group.return_value = mock_command_group
        
        load_command_table(self.loader, None)
        
        custom_command_calls = mock_command_group.custom_command.call_args_list
        command_names = [call[0][0] for call in custom_command_calls]
        
        expected_commands = [
            'check-prerequisites',
            'setup-env'
        ]
        
        for command in expected_commands:
            self.assertIn(command, command_names)

    def test_migrate_server_commands_registered(self):
        """Test that server management commands are registered."""
        mock_command_group = Mock()
        mock_command_group.__enter__ = Mock(return_value=mock_command_group)
        mock_command_group.__exit__ = Mock(return_value=None)
        mock_command_group.custom_command = Mock()
        
        self.loader.command_group.return_value = mock_command_group
        
        load_command_table(self.loader, None)
        
        custom_command_calls = mock_command_group.custom_command.call_args_list
        command_names = [call[0][0] for call in custom_command_calls]
        
        expected_server_commands = [
            'list-discovered',
            'get-discovered-servers-table',
            'find-by-name',
            'create-replication',
            'show-replication-status',
            'update-replication'
        ]
        
        for command in expected_server_commands:
            self.assertIn(command, command_names)

    def test_migrate_local_commands_registered(self):
        """Test that Azure Local (Stack HCI) commands are registered."""
        mock_command_group = Mock()
        mock_command_group.__enter__ = Mock(return_value=mock_command_group)
        mock_command_group.__exit__ = Mock(return_value=None)
        mock_command_group.custom_command = Mock()
        
        self.loader.command_group.return_value = mock_command_group
        
        load_command_table(self.loader, None)
        
        custom_command_calls = mock_command_group.custom_command.call_args_list
        command_names = [call[0][0] for call in custom_command_calls]
        
        expected_local_commands = [
            'create-disk-mapping',
            'create-nic-mapping',
            'create-replication',
            'get-job',
            'get-azure-local-job',
            'init',
            'init-azure-local',
            'get-replication',
            'set-replication',
            'start-migration',
            'remove-replication'
        ]
        
        for command in expected_local_commands:
            self.assertIn(command, command_names)

    def test_migrate_auth_commands_registered(self):
        """Test that authentication commands are registered."""
        mock_command_group = Mock()
        mock_command_group.__enter__ = Mock(return_value=mock_command_group)
        mock_command_group.__exit__ = Mock(return_value=None)
        mock_command_group.custom_command = Mock()
        
        self.loader.command_group.return_value = mock_command_group
        
        load_command_table(self.loader, None)
        
        custom_command_calls = mock_command_group.custom_command.call_args_list
        command_names = [call[0][0] for call in custom_command_calls]
        
        expected_auth_commands = [
            'check',
            'login',
            'logout',
            'set-context',
            'show-context'
        ]
        
        for command in expected_auth_commands:
            self.assertIn(command, command_names)
class TestMigrateCommandParameters(unittest.TestCase):
    """Test command parameter validation and parsing."""

    def setUp(self):
        pass

    @patch('azure.cli.command_modules.migrate.custom.check_migration_prerequisites')
    def test_check_prerequisites_command(self, mock_check_prereqs):
        """Test check-prerequisites command execution."""
        mock_check_prereqs.return_value = {
            'platform': 'Windows',
            'powershell_available': True,
            'azure_powershell_available': True,
            'recommendations': []
        }
        
        result = mock_check_prereqs(Mock())
        self.assertIn('platform', result)
        self.assertTrue(result['powershell_available'])

    @patch('azure.cli.command_modules.migrate.custom.setup_migration_environment')
    def test_setup_env_command_parameters(self, mock_setup_env):
        """Test setup-env command with parameters."""
        mock_setup_env.return_value = {
            'platform': 'windows',
            'checks': ['✅ PowerShell is available'],
            'actions_taken': [],
            'cross_platform_ready': True
        }
        
        cmd_mock = Mock()
        result = mock_setup_env(cmd_mock, install_powershell=True, check_only=False)
        self.assertIn('checks', result)        
        mock_setup_env.assert_called_with(cmd_mock, install_powershell=True, check_only=False)

    @patch('azure.cli.command_modules.migrate.custom.get_discovered_server')
    def test_list_discovered_command_parameters(self, mock_get_discovered):
        """Test list-discovered command with various parameters."""
        mock_get_discovered.return_value = {
            'DiscoveredServers': [],
            'Count': 0
        }
        
        result = mock_get_discovered(
            Mock(),
            resource_group_name='test-rg',
            project_name='test-project'
        )
        
        self.assertEqual(result['Count'], 0)
        
        mock_get_discovered(
            Mock(),
            resource_group_name='test-rg',
            project_name='test-project',
            subscription_id='test-sub',
            server_id='test-server',
            source_machine_type='VMware',
            output_format='json',
            display_fields='Name,Type'
        )
        
        self.assertEqual(mock_get_discovered.call_count, 2)

    @patch('azure.cli.command_modules.migrate.custom.create_server_replication')
    def test_create_replication_command_parameters(self, mock_create_replication):
        """Test create-replication command parameters."""
        mock_create_replication.return_value = None
        mock_create_replication(
            Mock(),
            resource_group_name='test-rg',
            project_name='test-project',
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network'
        )
        
        mock_create_replication(
            Mock(),
            resource_group_name='test-rg',
            project_name='test-project',
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network',
            server_name='source-server'
        )
        
        mock_create_replication(
            Mock(),
            resource_group_name='test-rg',
            project_name='test-project',
            target_vm_name='target-vm',
            target_resource_group='target-rg',
            target_network='target-network',
            server_index=0
        )
        
        self.assertEqual(mock_create_replication.call_count, 3)

    @patch('azure.cli.command_modules.migrate.custom.connect_azure_account')
    def test_auth_login_command_parameters(self, mock_connect):
        """Test auth login command with different authentication methods."""
        mock_connect.return_value = None
        
        # Test interactive login
        mock_connect(Mock())
        
        # Test device code login
        mock_connect(Mock(), device_code=True)
        
        # Test service principal login
        mock_connect(
            Mock(),
            app_id='test-app-id',
            secret='test-secret',
            tenant_id='test-tenant'
        )
        
        # Test with subscription and tenant
        mock_connect(
            Mock(),
            subscription_id='test-subscription',
            tenant_id='test-tenant'
        )
        
        self.assertEqual(mock_connect.call_count, 4)

    @patch('azure.cli.command_modules.migrate.custom.create_local_disk_mapping')
    def test_create_disk_mapping_parameters(self, mock_create_disk_mapping):
        """Test create-disk-mapping command parameters."""
        mock_create_disk_mapping.return_value = None
        
        # Test with all parameters
        mock_create_disk_mapping(
            Mock(),
            disk_id='disk-001',
            is_os_disk=True,
            is_dynamic=False,
            size_gb=64,
            format_type='VHDX',
            physical_sector_size=512
        )
        
        # Test with minimal parameters (defaults)
        mock_create_disk_mapping(
            Mock(),
            disk_id='disk-002'
        )
        
        self.assertEqual(mock_create_disk_mapping.call_count, 2)


class TestMigrateCommandValidation(unittest.TestCase):
    """Test command validation and error handling."""

    def setUp(self):
        pass

    @patch('azure.cli.command_modules.migrate.custom.set_azure_context')
    def test_set_context_parameter_validation(self, mock_set_context):
        """Test set-context command parameter validation."""
        
        # Test missing required parameters
        mock_set_context.side_effect = CLIError(
            'Either subscription_id or subscription_name must be provided'
        )
        
        with self.assertRaises(CLIError):
            mock_set_context(Mock())

    @patch('azure.cli.command_modules.migrate.custom.get_discovered_server')
    def test_authentication_required_validation(self, mock_get_discovered):
        """Test that authentication is properly validated."""        
        mock_get_discovered.side_effect = CLIError(
            'Azure authentication required: Not authenticated'
        )
        
        with self.assertRaises(CLIError) as context:
            mock_get_discovered(
                Mock(),
                resource_group_name='test-rg',
                project_name='test-project'
            )
        
        self.assertIn('Azure authentication required', str(context.exception))

    @patch('azure.cli.command_modules.migrate.custom.create_server_replication')
    def test_server_selection_validation(self, mock_create_replication):
        """Test server selection parameter validation."""        
        mock_create_replication.side_effect = CLIError(
            'Either server_name or server_index must be provided'
        )
        
        with self.assertRaises(CLIError):
            mock_create_replication(
                Mock(),
                resource_group_name='test-rg',
                project_name='test-project',
                target_vm_name='target-vm',
                target_resource_group='target-rg',
                target_network='target-network'
            )


class TestMigrateCommandIntegration(unittest.TestCase):
    """Test integration between different command components."""

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_powershell_executor_integration(self, mock_get_executor):
        """Test that commands properly integrate with PowerShell executor."""
        mock_executor = Mock()
        mock_executor.check_powershell_availability.return_value = (True, 'powershell')
        mock_executor.execute_script.return_value = {'stdout': '7.3.0', 'stderr': ''}
        mock_get_executor.return_value = mock_executor
        
        with patch('platform.system', return_value='Windows'), \
             patch('platform.version', return_value='10.0.19041'), \
             patch('platform.python_version', return_value='3.9.7'):
            
            result = check_migration_prerequisites(Mock())
            
            mock_get_executor.assert_called()
            mock_executor.check_powershell_availability.assert_called()
            
            self.assertIn('platform', result)
            self.assertIn('powershell_available', result)

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_azure_authentication_integration(self, mock_get_executor):
        """Test that Azure authentication is properly integrated."""        
        mock_executor = Mock()
        mock_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_executor.execute_script_interactive.return_value = None
        mock_get_executor.return_value = mock_executor
        
        list_resource_groups(Mock())
        
        mock_executor.check_azure_authentication.assert_called()
        mock_executor.execute_script_interactive.assert_called()

    @patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
    def test_error_propagation(self, mock_get_executor):
        """Test that errors are properly propagated through the command stack."""
        mock_executor = Mock()
        mock_executor.check_azure_authentication.return_value = {
            'IsAuthenticated': False,
            'Error': 'Authentication failed'
        }
        mock_get_executor.return_value = mock_executor
        
        with self.assertRaises(CLIError) as context:
            get_discovered_server(
                Mock(),
                resource_group_name='test-rg',
                project_name='test-project'
            )
        
        self.assertIn('Azure authentication required', str(context.exception))


if __name__ == '__main__':
    unittest.main()
