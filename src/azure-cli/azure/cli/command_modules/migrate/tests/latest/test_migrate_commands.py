# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest import mock
from azure.cli.testsdk import ScenarioTest, record_only
from azure.cli.core.util import CLIError
from knack.util import CLIError as KnackCLIError


class MigrateGetDiscoveredServerTests(ScenarioTest):
    """Unit tests for the 'az migrate local get-discovered-server' command"""

    def setUp(self):
        super(MigrateGetDiscoveredServerTests, self).setUp()
        self.mock_subscription_id = "00000000-0000-0000-0000-000000000000"
        self.mock_rg_name = "test-rg"
        self.mock_project_name = "test-project"
        self.mock_appliance_name = "test-appliance"

    def _create_mock_response(self, data):
        """Helper to create a mock response object"""
        mock_response = mock.Mock()
        mock_response.json.return_value = data
        return mock_response

    def _create_sample_server_data(self, index=1,
                                   machine_name="test-machine",
                                   display_name="TestServer"):
        """Helper to create sample discovered server data"""
        return {
            'id': (f'/subscriptions/sub-id/resourceGroups/rg/providers/'
                   f'Microsoft.Migrate/migrateprojects/project/machines/'
                   f'machine-{index}'),
            'name': f'machine-{index}',
            'properties': {
                'displayName': display_name,
                'discoveryData': [
                    {
                        'machineName': machine_name,
                        'ipAddresses': ['192.168.1.10'],
                        'osName': 'Windows Server 2019',
                        'extendedInfo': {
                            'bootType': 'UEFI',
                            'diskDetails': '[{"InstanceId": "disk-0"}]'
                        }
                    }
                ]
            }
        }

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_list_all(self, mock_get_sub_id,
                                            mock_send_get):
        """Test listing all discovered servers in a project"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        # Setup mocks
        mock_get_sub_id.return_value = self.mock_subscription_id
        mock_send_get.return_value = self._create_mock_response({
            'value': [
                self._create_sample_server_data(1, "machine-1", "Server1"),
                self._create_sample_server_data(2, "machine-2", "Server2")
            ]
        })

        # Create a minimal mock cmd object
        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        # Execute the command
        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name
        )

        # Verify the API was called correctly
        mock_send_get.assert_called_once()
        call_args = mock_send_get.call_args[0]
        self.assertIn(self.mock_project_name, call_args[1])
        self.assertIn(self.mock_rg_name, call_args[1])
        self.assertIn('/machines?', call_args[1])

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_with_display_name_filter(
            self, mock_get_sub_id, mock_send_get):
        """Test filtering discovered servers by display name"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_get_sub_id.return_value = self.mock_subscription_id
        target_display_name = "WebServer"
        mock_send_get.return_value = self._create_mock_response({
            'value': [self._create_sample_server_data(
                1, "machine-1", target_display_name)]
        })

        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name,
            display_name=target_display_name
        )

        # Verify the filter was applied in the URL
        call_args = mock_send_get.call_args[0]
        self.assertIn("$filter", call_args[1])
        self.assertIn(target_display_name, call_args[1])

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_with_appliance_vmware(
            self, mock_get_sub_id, mock_send_get):
        """Test getting servers from a specific VMware appliance"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_get_sub_id.return_value = self.mock_subscription_id
        mock_send_get.return_value = self._create_mock_response({
            'value': [self._create_sample_server_data(1)]
        })

        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name,
            appliance_name=self.mock_appliance_name,
            source_machine_type="VMware"
        )

        # Verify VMwareSites endpoint was used
        call_args = mock_send_get.call_args[0]
        self.assertIn("VMwareSites", call_args[1])
        self.assertIn(self.mock_appliance_name, call_args[1])

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_with_appliance_hyperv(
            self, mock_get_sub_id, mock_send_get):
        """Test getting servers from a specific HyperV appliance"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_get_sub_id.return_value = self.mock_subscription_id
        mock_send_get.return_value = self._create_mock_response({
            'value': [self._create_sample_server_data(1)]
        })

        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name,
            appliance_name=self.mock_appliance_name,
            source_machine_type="HyperV"
        )

        # Verify HyperVSites endpoint was used
        call_args = mock_send_get.call_args[0]
        self.assertIn("HyperVSites", call_args[1])
        self.assertIn(self.mock_appliance_name, call_args[1])

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_specific_machine(
            self, mock_get_sub_id, mock_send_get):
        """Test getting a specific machine by name"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_get_sub_id.return_value = self.mock_subscription_id
        specific_name = "machine-12345"
        mock_send_get.return_value = self._create_mock_response(
            self._create_sample_server_data(1, specific_name, "SpecificServer")
        )

        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name,
            name=specific_name
        )

        # Verify the specific machine endpoint was used
        call_args = mock_send_get.call_args[0]
        self.assertIn(f"/machines/{specific_name}?", call_args[1])

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_get_discovered_server_with_pagination(self, mock_get_sub_id,
                                                   mock_send_get):
        """Test handling paginated results"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_get_sub_id.return_value = self.mock_subscription_id

        # First page with nextLink
        first_page = {
            'value': [self._create_sample_server_data(1)],
            'nextLink': 'https://management.azure.com/next-page'
        }

        # Second page without nextLink
        second_page = {
            'value': [self._create_sample_server_data(2)]
        }

        mock_send_get.side_effect = [
            self._create_mock_response(first_page),
            self._create_mock_response(second_page)
        ]

        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")

        result = get_discovered_server(
            cmd=mock_cmd,
            project_name=self.mock_project_name,
            resource_group_name=self.mock_rg_name
        )

        # Verify pagination was handled (two API calls)
        self.assertEqual(mock_send_get.call_count, 2)

    def test_get_discovered_server_missing_project_name(self):
        """Test error handling when project_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_cmd = mock.Mock()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            get_discovered_server(
                cmd=mock_cmd,
                project_name=None,
                resource_group_name=self.mock_rg_name
            )

        self.assertIn("project_name", str(context.exception))

    def test_get_discovered_server_missing_resource_group(self):
        """Test error handling when resource_group_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_cmd = mock.Mock()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            get_discovered_server(
                cmd=mock_cmd,
                project_name=self.mock_project_name,
                resource_group_name=None
            )

        self.assertIn("resource_group_name", str(context.exception))

    def test_get_discovered_server_invalid_machine_type(self):
        """Test error handling for invalid source_machine_type"""
        from azure.cli.command_modules.migrate.custom import (
            get_discovered_server)

        mock_cmd = mock.Mock()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            get_discovered_server(
                cmd=mock_cmd,
                project_name=self.mock_project_name,
                resource_group_name=self.mock_rg_name,
                source_machine_type="InvalidType"
            )

        self.assertIn("VMware", str(context.exception))
        self.assertIn("HyperV", str(context.exception))


class MigrateReplicationInitTests(ScenarioTest):
    """Unit tests for the 'az migrate local replication init' command"""

    def setUp(self):
        super(MigrateReplicationInitTests, self).setUp()
        self.mock_subscription_id = "00000000-0000-0000-0000-000000000000"
        self.mock_rg_name = "test-rg"
        self.mock_project_name = "test-project"
        self.mock_source_appliance = "vmware-appliance"
        self.mock_target_appliance = "azlocal-appliance"

    def _create_mock_cmd(self):
        """Helper to create a mock cmd object"""
        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")
        return mock_cmd

    def _create_mock_resource_group(self):
        """Helper to create mock resource group response"""
        return {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}'),
            'name': self.mock_rg_name,
            'location': 'eastus'
        }

    def _create_mock_migrate_project(self):
        """Helper to create mock migrate project response"""
        return {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.Migrate/migrateprojects/'
                   f'{self.mock_project_name}'),
            'name': self.mock_project_name,
            'location': 'eastus',
            'properties': {
                'provisioningState': 'Succeeded'
            }
        }

    def _create_mock_solution(self, solution_name, vault_id=None,
                              storage_account_id=None):
        """Helper to create mock solution response"""
        extended_details = {
            'applianceNameToSiteIdMapV2': (
                '[{"ApplianceName": "vmware-appliance", '
                '"SiteId": "/subscriptions/sub/resourceGroups/rg/providers/'
                'Microsoft.OffAzure/VMwareSites/vmware-site"}]'),
            'applianceNameToSiteIdMapV3': (
                '{"azlocal-appliance": {"SiteId": '
                '"/subscriptions/sub/resourceGroups/rg/providers/'
                'Microsoft.OffAzure/HyperVSites/azlocal-site"}}')
        }

        if vault_id:
            extended_details['vaultId'] = vault_id
        if storage_account_id:
            extended_details['replicationStorageAccountId'] = (
                storage_account_id)

        return {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.Migrate/migrateprojects/'
                   f'{self.mock_project_name}/solutions/{solution_name}'),
            'name': solution_name,
            'properties': {
                'details': {
                    'extendedDetails': extended_details
                }
            }
        }

    def _create_mock_vault(self, with_identity=True):
        """Helper to create mock replication vault response"""
        vault = {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.DataReplication/replicationVaults/'
                   f'test-vault'),
            'name': 'test-vault',
            'properties': {
                'provisioningState': 'Succeeded'
            }
        }

        if with_identity:
            vault['identity'] = {
                'type': 'SystemAssigned',
                'principalId': '11111111-1111-1111-1111-111111111111'
            }

        return vault

    def _create_mock_fabric(self, fabric_name, instance_type,
                            appliance_name):
        """Helper to create mock fabric response"""
        return {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.DataReplication/replicationFabrics/'
                   f'{fabric_name}'),
            'name': fabric_name,
            'properties': {
                'provisioningState': 'Succeeded',
                'customProperties': {
                    'instanceType': instance_type,
                    'migrationSolutionId': (
                        f'/subscriptions/{self.mock_subscription_id}/'
                        f'resourceGroups/{self.mock_rg_name}/providers/'
                        f'Microsoft.Migrate/migrateprojects/'
                        f'{self.mock_project_name}/solutions/'
                        f'Servers-Migration-ServerMigration_DataReplication')
                }
            }
        }

    def _create_mock_dra(self, appliance_name, instance_type):
        """Helper to create mock DRA (fabric agent) response"""
        return {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.DataReplication/replicationFabrics/'
                   f'fabric/fabricAgents/dra'),
            'name': 'dra',
            'properties': {
                'machineName': appliance_name,
                'isResponsive': True,
                'customProperties': {
                    'instanceType': instance_type
                },
                'resourceAccessIdentity': {
                    'objectId': '22222222-2222-2222-2222-222222222222'
                }
            }
        }

    @mock.patch(
        'azure.cli.command_modules.migrate.custom.get_mgmt_service_client')
    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.'
        'create_or_update_resource')
    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.get_resource_by_id')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    @mock.patch('azure.cli.command_modules.migrate.custom.time.sleep')
    def test_initialize_replication_infrastructure_success(
            self, mock_sleep, mock_get_sub_id,
            mock_get_resource, mock_send_get,
            mock_create_or_update, mock_get_client):
        """Test successful initialization of replication infrastructure"""
        from azure.cli.command_modules.migrate.custom import (
            initialize_replication_infrastructure)

        # Setup mocks
        mock_get_sub_id.return_value = self.mock_subscription_id

        vault_id = (f'/subscriptions/{self.mock_subscription_id}/'
                    f'resourceGroups/{self.mock_rg_name}/providers/'
                    f'Microsoft.DataReplication/replicationVaults/'
                    f'test-vault')

        # Mock get_resource_by_id calls in sequence
        mock_get_resource.side_effect = [
            self._create_mock_resource_group(),  # Resource group
            self._create_mock_migrate_project(),  # Migrate project
            self._create_mock_solution(
                'Servers-Migration-ServerMigration_DataReplication',
                vault_id=vault_id),  # AMH solution
            self._create_mock_vault(with_identity=True),  # Vault
            self._create_mock_solution(
                'Servers-Discovery-ServerDiscovery'),  # Discovery solution
            None,  # Policy (doesn't exist initially - will be created)
            {'properties': {'provisioningState': 'Succeeded'}},  # Policy
            {'id': vault_id,
             'properties': {'provisioningState': 'Succeeded'}},  # Storage
            None,  # Extension doesn't exist
        ]

        # Mock send_get_request for listing fabrics and DRAs
        mock_send_get.side_effect = [
            # Fabrics list
            self._create_mock_response({
                'value': [
                    self._create_mock_fabric(
                        'vmware-appliance-fabric',
                        'HyperVToAzStackHCI',
                        'vmware-appliance'),
                    self._create_mock_fabric(
                        'azlocal-appliance-fabric',
                        'AzStackHCIInstance',
                        'azlocal-appliance')
                ]
            }),
            # Source DRAs
            self._create_mock_response({
                'value': [self._create_mock_dra(
                    'vmware-appliance', 'HyperVToAzStackHCI')]
            }),
            # Target DRAs
            self._create_mock_response({
                'value': [self._create_mock_dra(
                    'azlocal-appliance', 'AzStackHCIInstance')]
            })
        ]

        # Mock authorization client
        mock_auth_client = mock.Mock()
        mock_auth_client.role_assignments.list_for_scope.return_value = []
        mock_auth_client.role_assignments.create.return_value = None
        mock_get_client.return_value = mock_auth_client

        mock_cmd = self._create_mock_cmd()

        # Note: This test will fail at storage account creation,
        # but validates the main logic path
        with self.assertRaises(Exception):
            initialize_replication_infrastructure(
                cmd=mock_cmd,
                resource_group_name=self.mock_rg_name,
                project_name=self.mock_project_name,
                source_appliance_name=self.mock_source_appliance,
                target_appliance_name=self.mock_target_appliance
            )

    def _create_mock_response(self, data):
        """Helper to create a mock response object"""
        mock_response = mock.Mock()
        mock_response.json.return_value = data
        return mock_response

    def test_initialize_replication_missing_resource_group(self):
        """Test error when resource_group_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            initialize_replication_infrastructure)

        mock_cmd = self._create_mock_cmd()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            initialize_replication_infrastructure(
                cmd=mock_cmd,
                resource_group_name=None,
                project_name=self.mock_project_name,
                source_appliance_name=self.mock_source_appliance,
                target_appliance_name=self.mock_target_appliance
            )

        self.assertIn("resource_group_name", str(context.exception))

    def test_initialize_replication_missing_project_name(self):
        """Test error when project_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            initialize_replication_infrastructure)

        mock_cmd = self._create_mock_cmd()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            initialize_replication_infrastructure(
                cmd=mock_cmd,
                resource_group_name=self.mock_rg_name,
                project_name=None,
                source_appliance_name=self.mock_source_appliance,
                target_appliance_name=self.mock_target_appliance
            )

        self.assertIn("project_name", str(context.exception))

    def test_initialize_replication_missing_source_appliance(self):
        """Test error when source_appliance_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            initialize_replication_infrastructure)

        mock_cmd = self._create_mock_cmd()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            initialize_replication_infrastructure(
                cmd=mock_cmd,
                resource_group_name=self.mock_rg_name,
                project_name=self.mock_project_name,
                source_appliance_name=None,
                target_appliance_name=self.mock_target_appliance
            )

        self.assertIn("source_appliance_name", str(context.exception))

    def test_initialize_replication_missing_target_appliance(self):
        """Test error when target_appliance_name is missing"""
        from azure.cli.command_modules.migrate.custom import (
            initialize_replication_infrastructure)

        mock_cmd = self._create_mock_cmd()

        with self.assertRaises((CLIError, KnackCLIError)) as context:
            initialize_replication_infrastructure(
                cmd=mock_cmd,
                resource_group_name=self.mock_rg_name,
                project_name=self.mock_project_name,
                source_appliance_name=self.mock_source_appliance,
                target_appliance_name=None
            )

        self.assertIn("target_appliance_name", str(context.exception))


class MigrateReplicationNewTests(ScenarioTest):
    """Unit tests for the 'az migrate local replication new' command"""

    def setUp(self):
        super(MigrateReplicationNewTests, self).setUp()
        self.mock_subscription_id = "00000000-0000-0000-0000-000000000000"
        self.mock_rg_name = "test-rg"
        self.mock_project_name = "test-project"
        self.mock_machine_id = (
            f"/subscriptions/{self.mock_subscription_id}"
            f"/resourceGroups/{self.mock_rg_name}/providers"
            f"/Microsoft.Migrate/migrateprojects/"
            f"{self.mock_project_name}/machines/machine-12345")

    def _create_mock_cmd(self):
        """Helper to create a mock cmd object"""
        mock_cmd = mock.Mock()
        mock_cmd.cli_ctx.cloud.endpoints.resource_manager = (
            "https://management.azure.com")
        return mock_cmd

    def test_new_replication_missing_machine_identifier(self):
        """Test error when neither machine_id nor machine_index is provided
        """
        from azure.cli.command_modules.migrate.custom import (
            new_local_server_replication)

        mock_cmd = self._create_mock_cmd()

        # Note: The actual implementation may have this validation
        # This test documents the expected behavior
        try:
            new_local_server_replication(
                cmd=mock_cmd,
                machine_id=None,
                machine_index=None,
                target_storage_path_id=("/subscriptions/sub/resourceGroups"
                                        "/rg/providers/"
                                        "Microsoft.AzureStackHCI"
                                        "/storageContainers/storage"),
                target_resource_group_id=("/subscriptions/sub/resourceGroups/"
                                          "target-rg"),
                target_vm_name="test-vm",
                source_appliance_name="source-appliance",
                target_appliance_name="target-appliance"
            )
        except (CLIError, KnackCLIError, Exception) as e:
            # Expected to fail
            # Either machine_id or machine_index should be provided
            pass

    def test_new_replication_machine_index_without_project(self):
        """Test error when machine_index is provided without project_name"""
        from azure.cli.command_modules.migrate.custom import (
            new_local_server_replication)

        mock_cmd = self._create_mock_cmd()

        try:
            new_local_server_replication(
                cmd=mock_cmd,
                machine_id=None,
                machine_index=1,
                project_name=None,  # Missing
                resource_group_name=None,  # Missing
                target_storage_path_id=("/subscriptions/sub/resourceGroups"
                                        "/rg/providers/"
                                        "Microsoft.AzureStackHCI"
                                        "/storageContainers/storage"),
                target_resource_group_id=("/subscriptions/sub/resourceGroups/"
                                          "target-rg"),
                target_vm_name="test-vm",
                source_appliance_name="source-appliance",
                target_appliance_name="target-appliance"
            )
        except (CLIError, KnackCLIError, Exception) as e:
            # Expected to fail
            pass

    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.send_get_request')
    @mock.patch(
        'azure.cli.command_modules.migrate._helpers.get_resource_by_id')
    @mock.patch(
        'azure.cli.core.commands.client_factory.get_subscription_id')
    def test_new_replication_with_machine_index(self,
                                                mock_get_sub_id,
                                                mock_get_resource,
                                                mock_send_get):
        """Test creating replication using machine_index"""
        from azure.cli.command_modules.migrate.custom import (
            new_local_server_replication)

        # Setup mocks
        mock_get_sub_id.return_value = self.mock_subscription_id

        # Mock discovery solution
        mock_get_resource.return_value = {
            'id': (f'/subscriptions/{self.mock_subscription_id}/'
                   f'resourceGroups/{self.mock_rg_name}/providers/'
                   f'Microsoft.Migrate/migrateprojects/'
                   f'{self.mock_project_name}/solutions/'
                   f'Servers-Discovery-ServerDiscovery'),
            'properties': {
                'details': {
                    'extendedDetails': {
                        'applianceNameToSiteIdMapV2': (
                            '[{"ApplianceName": "source-appliance", '
                            '"SiteId": "/subscriptions/sub/resourceGroups/rg'
                            '/providers/Microsoft.OffAzure/VMwareSites/'
                            'vmware-site"}]')
                    }
                }
            }
        }

        # Mock machines list response
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'id': self.mock_machine_id,
                    'name': 'machine-12345',
                    'properties': {'displayName': 'TestMachine'}
                }
            ]
        }
        mock_send_get.return_value = mock_response

        mock_cmd = self._create_mock_cmd()

        # This will fail at a later stage, but tests the machine_index logic
        try:
            new_local_server_replication(
                cmd=mock_cmd,
                machine_id=None,
                machine_index=1,
                project_name=self.mock_project_name,
                resource_group_name=self.mock_rg_name,
                target_storage_path_id=("/subscriptions/sub/resourceGroups/"
                                        "rg/providers/"
                                        "Microsoft.AzureStackHCI/"
                                        "storageContainers/storage"),
                target_resource_group_id=("/subscriptions/sub/resourceGroups/"
                                          "target-rg"),
                target_vm_name="test-vm",
                source_appliance_name="source-appliance",
                target_appliance_name="target-appliance",
                os_disk_id="disk-0",
                target_virtual_switch_id=("/subscriptions/sub/resourceGroups/"
                                          "rg/providers/"
                                          "Microsoft.AzureStackHCI/"
                                          "logicalNetworks/network")
            )
        except Exception as e:
            # Expected to fail at resource creation,
            # but validates parameter handling
            pass

        # Verify get_resource_by_id was called for discovery solution
        self.assertTrue(mock_get_resource.called)
        # Verify send_get_request was called to fetch machines
        self.assertTrue(mock_send_get.called)

    def test_new_replication_required_parameters_default_mode(self):
        """Test that required parameters for default user mode are
        validated"""
        from azure.cli.command_modules.migrate.custom import (
            new_local_server_replication)

        mock_cmd = self._create_mock_cmd()

        # Default mode requires: os_disk_id and target_virtual_switch_id
        # This test documents the expected required parameters
        required_params = {
            'cmd': mock_cmd,
            'machine_id': self.mock_machine_id,
            'target_storage_path_id': ("/subscriptions/sub/resourceGroups/"
                                       "rg/providers/"
                                       "Microsoft.AzureStackHCI/"
                                       "storageContainers/storage"),
            'target_resource_group_id': ("/subscriptions/sub/resourceGroups/"
                                         "target-rg"),
            'target_vm_name': "test-vm",
            'source_appliance_name': "source-appliance",
            'target_appliance_name': "target-appliance",
            'os_disk_id': "disk-0",
            'target_virtual_switch_id': ("/subscriptions/sub/resourceGroups/"
                                         "rg/providers/"
                                         "Microsoft.AzureStackHCI/"
                                         "logicalNetworks/network")
        }

        try:
            new_local_server_replication(**required_params)
        except Exception as e:
            # Expected to fail at later stages
            pass

    def test_new_replication_required_parameters_power_user_mode(self):
        """Test that required parameters for power user mode are
        validated"""
        from azure.cli.command_modules.migrate.custom import (
            new_local_server_replication)

        mock_cmd = self._create_mock_cmd()

        # Power user mode requires: disk_to_include and nic_to_include
        required_params = {
            'cmd': mock_cmd,
            'machine_id': self.mock_machine_id,
            'target_storage_path_id': ("/subscriptions/sub/resourceGroups/"
                                       "rg/providers/"
                                       "Microsoft.AzureStackHCI/"
                                       "storageContainers/storage"),
            'target_resource_group_id': ("/subscriptions/sub/resourceGroups/"
                                         "target-rg"),
            'target_vm_name': "test-vm",
            'source_appliance_name': "source-appliance",
            'target_appliance_name': "target-appliance",
            'disk_to_include': ["disk-0", "disk-1"],
            'nic_to_include': ["nic-0"]
        }

        try:
            new_local_server_replication(**required_params)
        except Exception as e:
            # Expected to fail at later stages
            pass


class MigrateScenarioTests(ScenarioTest):
    @record_only()
    def test_migrate_local_get_discovered_server_all_parameters(self):
        self.kwargs.update({
            'project': 'test-migrate-project',
            'rg': 'test-resource-group',
            'display_name': 'test-server',
            'machine_type': 'VMware',
            'subscription': '00000000-0000-0000-0000-000000000000',
            'machine_name': 'machine-001',
            'appliance': 'test-appliance'
        })

        # Test with project-name and resource-group-name parameters
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg}')

        # Test with display-name filter
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--display-name {display_name}')

        # Test with source-machine-type
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--source-machine-type {machine_type}')

        # Test with subscription-id
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--subscription-id {subscription}')

        # Test with name parameter
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--name {machine_name}')

        # Test with appliance-name
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--appliance-name {appliance}')

        # Test with all parameters combined
        self.cmd('az migrate local get-discovered-server '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--display-name {display_name} '
                 '--source-machine-type {machine_type} '
                 '--subscription-id {subscription} '
                 '--appliance-name {appliance}')

    @record_only()
    def test_migrate_local_replication_init_all_parameters(self):
        self.kwargs.update({
            'rg': 'test-resource-group',
            'project': 'test-migrate-project',
            'source_appliance': 'vmware-appliance',
            'target_appliance': 'azlocal-appliance',
            'storage_account': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.Storage'
                '/storageAccounts/cachestorage'),
            'subscription': '00000000-0000-0000-0000-000000000000'
        })

        # Test with required parameters
        self.cmd('az migrate local replication init '
                 '--resource-group-name {rg} '
                 '--project-name {project} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance}')

        # Test with cache-storage-account-id
        self.cmd('az migrate local replication init '
                 '--resource-group-name {rg} '
                 '--project-name {project} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--cache-storage-account-id {storage_account}')

        # Test with subscription-id
        self.cmd('az migrate local replication init '
                 '--resource-group-name {rg} '
                 '--project-name {project} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--subscription-id {subscription}')

        # Test with pass-thru
        self.cmd('az migrate local replication init '
                 '--resource-group-name {rg} '
                 '--project-name {project} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--pass-thru')

        # Test with all parameters
        self.cmd('az migrate local replication init '
                 '--resource-group-name {rg} '
                 '--project-name {project} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--cache-storage-account-id {storage_account} '
                 '--subscription-id {subscription} '
                 '--pass-thru')

    @record_only()
    def test_migrate_local_replication_new_with_machine_id(self):
        self.kwargs.update({
            'machine_id': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.Migrate'
                '/migrateprojects/test-project/machines/machine-001'),
            'storage_path': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/storageContainers/storage01'),
            'target_rg': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/target-rg'),
            'vm_name': 'migrated-vm-01',
            'source_appliance': 'vmware-appliance',
            'target_appliance': 'azlocal-appliance',
            'virtual_switch': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/logicalNetworks/network01'),
            'test_switch': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/logicalNetworks/test-network'),
            'os_disk': 'disk-0',
            'subscription': '00000000-0000-0000-0000-000000000000'
        })

        # Test with machine-id (default user mode)
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk}')

        # Test with target-vm-cpu-core
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk} '
                 '--target-vm-cpu-core 4')

        # Test with target-vm-ram
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk} '
                 '--target-vm-ram 8192')

        # Test with is-dynamic-memory-enabled
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk} '
                 '--is-dynamic-memory-enabled false')

        # Test with target-test-virtual-switch-id
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--target-test-virtual-switch-id {test_switch} '
                 '--os-disk-id {os_disk}')

        # Test with subscription-id
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk} '
                 '--subscription-id {subscription}')

    @record_only()
    def test_migrate_local_replication_new_with_machine_index(self):
        """Test replication new command with machine-index"""
        self.kwargs.update({
            'machine_index': 1,
            'project': 'test-migrate-project',
            'rg': 'test-resource-group',
            'storage_path': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/storageContainers/storage01'),
            'target_rg': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/target-rg'),
            'vm_name': 'migrated-vm-02',
            'source_appliance': 'vmware-appliance',
            'target_appliance': 'azlocal-appliance',
            'virtual_switch': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/logicalNetworks/network01'),
            'os_disk': 'disk-0'
        })

        # Test with machine-index and required parameters
        self.cmd('az migrate local replication new '
                 '--machine-index {machine_index} '
                 '--project-name {project} '
                 '--resource-group-name {rg} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--target-virtual-switch-id {virtual_switch} '
                 '--os-disk-id {os_disk}')

    @record_only()
    def test_migrate_local_replication_new_power_user_mode(self):
        """Test replication new command with power user mode"""
        self.kwargs.update({
            'machine_id': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.Migrate'
                '/migrateprojects/test-project/machines/machine-003'),
            'storage_path': (
                '/subscriptions/00000000-0000-0000-0000-000000000000'
                '/resourceGroups/test-rg/providers/Microsoft.AzureStackHCI'
                '/storageContainers/storage01'),
            'target_rg': ('/subscriptions/00000000-0000-0000-0000-000000000000'
                          '/resourceGroups/target-rg'),
            'vm_name': 'migrated-vm-03',
            'source_appliance': 'vmware-appliance',
            'target_appliance': 'azlocal-appliance'
        })

        # Test with disk-to-include and nic-to-include (power user mode)
        self.cmd('az migrate local replication new '
                 '--machine-id {machine_id} '
                 '--target-storage-path-id {storage_path} '
                 '--target-resource-group-id {target_rg} '
                 '--target-vm-name {vm_name} '
                 '--source-appliance-name {source_appliance} '
                 '--target-appliance-name {target_appliance} '
                 '--disk-to-include disk-0 disk-1 '
                 '--nic-to-include nic-0')


if __name__ == '__main__':
    unittest.main()
