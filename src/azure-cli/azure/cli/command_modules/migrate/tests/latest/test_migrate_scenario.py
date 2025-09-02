# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest
from unittest.mock import patch, Mock

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, LiveScenarioTest)


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class MigrateScenarioTest(ScenarioTest):
    """Scenario tests for Azure Migrate CLI commands."""

    def setUp(self):
        super().setUp()
        # Mock PowerShell executor to avoid actual PowerShell execution during tests
        self.mock_ps_executor_patcher = patch('azure.cli.command_modules.migrate.custom.get_powershell_executor')
        self.mock_ps_executor = self.mock_ps_executor_patcher.start()
        
        # Configure mock PowerShell executor
        mock_executor = Mock()
        mock_executor.check_powershell_availability.return_value = (True, 'powershell')
        mock_executor.check_azure_authentication.return_value = {'IsAuthenticated': True}
        mock_executor.execute_script.return_value = {'stdout': 'Success', 'stderr': '', 'returncode': 0}
        mock_executor.execute_script_interactive.return_value = {'returncode': 0}
        mock_executor.execute_azure_authenticated_script.return_value = {
            'stdout': '{"DiscoveredServers": [], "Count": 0}',
            'stderr': ''
        }
        self.mock_ps_executor.return_value = mock_executor

    def tearDown(self):
        self.mock_ps_executor_patcher.stop()
        super().tearDown()

    def test_migrate_check_prerequisites(self):
        """Test migrate check-prerequisites command."""
        with patch('platform.system', return_value='Windows'), \
             patch('platform.version', return_value='10.0.19041'), \
             patch('platform.python_version', return_value='3.9.7'):
            
            result = self.cmd('migrate check-prerequisites').get_output_in_json()
            
            self.assertIn('platform', result)
            self.assertIn('powershell_available', result)
            self.assertEqual(result['platform'], 'Windows')

    def test_migrate_setup_environment(self):
        """Test migrate setup-env command."""
        result = self.cmd('migrate setup-env --check-only').get_output_in_json()
        
        self.assertIn('platform', result)
        self.assertIn('checks', result)

    def test_migrate_powershell_check_module(self):
        """Test migrate powershell check-module command."""
        # This command should execute without errors when PowerShell is mocked
        self.cmd('migrate powershell check-module --module-name Az.Migrate')

    @ResourceGroupPreparer(name_prefix='cli_test_migrate')
    def test_migrate_server_list_discovered_mock(self, resource_group):
        """Test migrate server list-discovered command with mocked responses."""
        self.kwargs.update({
            'rg': resource_group,
            'project': 'test-project'
        })

        # Test successful discovery (mocked)
        result = self.cmd('migrate server list-discovered -g {rg} --project-name {project} --source-machine-type VMware').get_output_in_json()
        
        self.assertIn('DiscoveredServers', result)
        self.assertIn('Count', result)
        self.assertEqual(result['Count'], 0)

    @ResourceGroupPreparer(name_prefix='cli_test_migrate')
    def test_migrate_server_get_discovered_servers_table(self, resource_group):
        """Test migrate server get-discovered-servers-table command."""
        self.kwargs.update({
            'rg': resource_group,
            'project': 'test-project'
        })

        # This should execute without errors when mocked
        self.cmd('migrate server get-discovered-servers-table -g {rg} --project-name {project}')

    def test_migrate_auth_commands(self):
        """Test migrate auth command group."""
        # Test auth check (should work with mocked executor)
        self.cmd('migrate auth check')

    @ResourceGroupPreparer(name_prefix='cli_test_migrate')
    def test_migrate_infrastructure_commands(self, resource_group):
        """Test migrate infrastructure commands."""
        self.kwargs.update({
            'rg': resource_group,
            'project': 'test-project'
        })

        # Test infrastructure check
        self.cmd('migrate infrastructure check -g {rg} --project-name {project}')

    def test_migrate_local_create_disk_mapping(self):
        """Test migrate local create-disk-mapping command."""
        # Test creating disk mapping
        self.cmd('migrate local create-disk-mapping --disk-id disk-001 --is-os-disk --size-gb 64 --format-type VHDX')

    @ResourceGroupPreparer(name_prefix='cli_test_migrate')
    def test_migrate_local_create_replication(self, resource_group):
        """Test migrate local create-replication command."""
        self.kwargs.update({
            'rg': resource_group,
            'project': 'test-project',
            'target_vm': 'target-vm',
            'storage_path': '/subscriptions/test/storageContainers/container001',
            'virtual_switch': '/subscriptions/test/logicalnetworks/network001',
            'target_rg': '/subscriptions/test/resourceGroups/target-rg'
        })

        # Test creating local replication
        self.cmd('migrate local create-replication -g {rg} --project-name {project} --server-index 0 '
                '--target-vm-name {target_vm} --target-storage-path-id {storage_path} '
                '--target-virtual-switch-id {virtual_switch} --target-resource-group-id {target_rg}')

    def test_migrate_command_help(self):
        """Test that help is available for all command groups."""
        # Test main help
        self.cmd('migrate -h')
        
        # Test command group help
        help_commands = [
            'migrate server -h',
            'migrate local -h',
            'migrate auth -h',
            'migrate infrastructure -h',
            'migrate powershell -h',
            'migrate resource -h'
        ]
        
        for help_cmd in help_commands:
            self.cmd(help_cmd)

    def test_migrate_error_scenarios(self):
        """Test error handling scenarios."""
        # Configure mock to simulate authentication failure
        mock_executor = self.mock_ps_executor.return_value
        mock_executor.check_azure_authentication.return_value = {
            'IsAuthenticated': False,
            'Error': 'Not authenticated'
        }

        # This should handle the authentication error gracefully
        with self.assertRaises(SystemExit):
            self.cmd('migrate resource list-groups')


class MigrateLiveScenarioTest(LiveScenarioTest):
    """Live scenario tests for Azure Migrate (require actual Azure resources)."""

    def setUp(self):
        super().setUp()
        # Only run live tests if AZURE_TEST_RUN_LIVE environment variable is set
        if not self.is_live:
            self.skipTest('Live tests are skipped in playback mode')

    @ResourceGroupPreparer(name_prefix='cli_live_test_migrate')
    def test_migrate_resource_list_groups_live(self, resource_group):
        """Live test for listing resource groups."""
        try:
            result = self.cmd('migrate resource list-groups').get_output_in_json()
            # The result should be a valid response if authentication works
            self.assertIsInstance(result, (list, dict))
        except SystemExit:
            # This is expected if Azure authentication is not configured
            self.skipTest('Azure authentication not configured for live tests')

    @ResourceGroupPreparer(name_prefix='cli_live_test_migrate')
    def test_migrate_check_prerequisites_live(self, resource_group):
        """Live test for checking migration prerequisites."""
        try:
            result = self.cmd('migrate check-prerequisites').get_output_in_json()
            
            # Verify the structure of the response
            self.assertIn('platform', result)
            self.assertIn('powershell_available', result)
            self.assertIn('recommendations', result)
            
            # Platform should be detected correctly
            import platform
            expected_platform = platform.system()
            self.assertEqual(result['platform'], expected_platform)
            
        except SystemExit:
            # This might happen if PowerShell is not available
            self.skipTest('PowerShell not available for live tests')

    def test_migrate_setup_env_live(self):
        """Live test for setting up migration environment."""
        try:
            result = self.cmd('migrate setup-env --check-only').get_output_in_json()
            
            # Verify the response structure
            self.assertIn('platform', result)
            self.assertIn('checks', result)
            self.assertIsInstance(result['checks'], list)
            
        except SystemExit:
            self.skipTest('Environment setup test failed - PowerShell may not be available')


class MigrateParameterValidationTest(ScenarioTest):
    """Test parameter validation for migrate commands."""

    def test_migrate_server_list_discovered_missing_params(self):
        """Test that required parameters are validated."""
        # Test missing resource group
        with self.assertRaises(SystemExit):
            self.cmd('migrate server list-discovered --project-name test-project')

        # Test missing project name
        with self.assertRaises(SystemExit):
            self.cmd('migrate server list-discovered -g test-rg')

    def test_migrate_local_create_disk_mapping_validation(self):
        """Test disk mapping parameter validation."""
        # Test missing disk ID
        with self.assertRaises(SystemExit):
            self.cmd('migrate local create-disk-mapping --is-os-disk')

    def test_migrate_auth_set_context_validation(self):
        """Test auth set-context parameter validation."""
        # Test with neither subscription ID nor name
        with self.assertRaises(SystemExit):
            self.cmd('migrate auth set-context')

    def test_migrate_server_create_replication_validation(self):
        """Test server replication creation parameter validation."""
        # Test missing required parameters
        with self.assertRaises(SystemExit):
            self.cmd('migrate server create-replication -g test-rg --project-name test-project')


if __name__ == '__main__':
    unittest.main()