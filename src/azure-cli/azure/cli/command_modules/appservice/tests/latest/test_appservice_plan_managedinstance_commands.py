# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import unittest
import os

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, JMESPathCheck, 
                               JMESPathCheckExists, JMESPathCheckNotExists)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# Test location for managed instance plans
MANAGED_INSTANCE_LOCATION = 'eastus2euap'


class AppServicePlanManagedInstanceTest(ScenarioTest):
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_basic_create(self, resource_group):
        """Test creating a basic managed instance app service plan."""
        plan_name = self.create_random_name('mi-plan', 24)
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            JMESPathCheckExists('id')
        ])
        
        # Verify plan shows correctly and has managed instance properties
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            # Validate managed instance mode is enabled via additional properties
            JMESPathCheck('properties.isCustomMode', True)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_with_identities(self, resource_group):
        """Test creating managed instance plan with identity assignments."""
        plan_name = self.create_random_name('mi-plan-id', 24)
        identity_name = self.create_random_name('mi-identity', 24)
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # Create plan with system and user assigned identities
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --assign-identity [system] {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheckExists('id')
        ])
        
        # Verify plan shows correctly with identity properties
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.tenantId'),
            JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity_id))
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_with_rdp(self, resource_group):
        """Test creating managed instance plan with RDP enabled."""
        plan_name = self.create_random_name('mi-plan-rdp', 24)
        
        # Create plan with RDP enabled
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --rdp-enabled'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4')
        ])
        
        # Verify plan shows correctly with RDP enabled
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', True)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_identity_operations(self, resource_group):
        """Test identity assign, show, and remove operations."""
        plan_name = self.create_random_name('mi-plan-identity', 24)
        identity_name = self.create_random_name('mi-identity', 24)
        
        # Create plan without identity
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True)
        ])
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # Test identity show (empty initially)
        self.cmd('appservice plan identity show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', None)
        ])
        
        # Assign system-assigned identity
        self.cmd('appservice plan identity assign -g {} -n {} --identities [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('tenantId')
        ])
        
        # Show identity (should have system)
        self.cmd('appservice plan identity show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId')
        ])
        
        # Assign user-assigned identity (should now have both)
        self.cmd('appservice plan identity assign -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Remove user-assigned identity
        self.cmd('appservice plan identity remove -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheck('userAssignedIdentities', None)
        ])
        
        # Remove system-assigned identity
        self.cmd('appservice plan identity remove -g {} -n {} --identities [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', None)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_install_script_operations(self, resource_group):
        """Test install script add, list, and remove operations."""
        plan_name = self.create_random_name('mi-plan-script', 24)
        script_name = 'test-script'
        script_uri = 'https://example.com/script.ps1'
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True)
        ])
        
        # List install scripts (should be empty initially)
        self.cmd('appservice plan managed-instance install-script list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        
        # Add install script
        self.cmd('appservice plan managed-instance install-script add -g {} -n {} --install-script-name {} --source-uri {} --type RemoteAzureBlob'.format(
            resource_group, plan_name, script_name, script_uri), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', script_name),
            JMESPathCheck('[0].source.sourceUri', script_uri),
            JMESPathCheck('[0].source.type', 'RemoteAzureBlob')
        ])
        
        # List install scripts (should show one)
        self.cmd('appservice plan managed-instance install-script list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', script_name)
        ])
        
        # Remove install script
        self.cmd('appservice plan managed-instance install-script remove -g {} -n {} --install-script-name {}'.format(
            resource_group, plan_name, script_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_storage_mount_operations(self, resource_group):
        """Test storage mount add, list, and remove operations."""
        plan_name = self.create_random_name('mi-plan-storage', 24)
        mount_name = 'test-mount'
        source_path = '\\\\example.file.core.windows.net\\share1'
        destination_path = 'D:\\mount\\share1'
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True)
        ])
        
        # List storage mounts (should be empty initially)
        self.cmd('appservice plan managed-instance storage-mount list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        
        # Add storage mount
        self.cmd('appservice plan managed-instance storage-mount add -g {} -n {} --mount-name {} --source {} --destination-path {} --type AzureFiles'.format(
            resource_group, plan_name, mount_name, source_path, destination_path), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', mount_name),
            JMESPathCheck('[0].source', source_path),
            JMESPathCheck('[0].destinationPath', destination_path),
            JMESPathCheck('[0].type', 'FileShare')
        ])
        
        # List storage mounts (should show one)
        self.cmd('appservice plan managed-instance storage-mount list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', mount_name)
        ])
        
        # Remove storage mount
        self.cmd('appservice plan managed-instance storage-mount remove -g {} -n {} --mount-name {}'.format(
            resource_group, plan_name, mount_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_registry_adapter_operations(self, resource_group):
        """Test registry adapter add, list, and remove operations."""
        plan_name = self.create_random_name('mi-plan-registry', 24)
        registry_key = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\TestKey'
        secret_uri = 'https://example.vault.azure.net/secrets/test-secret/version'
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True)
        ])
        
        # List registry adapters (should be empty initially)
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        
        # Add registry adapter
        self.cmd('appservice plan managed-instance registry-adapter add -g {} -n {} --registry-key "{}" --type String --secret-uri {}'.format(
            resource_group, plan_name, registry_key, secret_uri), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].registryKey', registry_key),
            JMESPathCheck('[0].type', 'String'),
            JMESPathCheck('[0].keyVaultSecretReference.secretUri', secret_uri)
        ])
        
        # List registry adapters (should show one)
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].registryKey', registry_key)
        ])
        
        # Remove registry adapter
        self.cmd('appservice plan managed-instance registry-adapter remove -g {} -n {} --registry-key "{}"'.format(
            resource_group, plan_name, registry_key), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_complex_scenario(self, resource_group):
        """Test complex scenario with multiple features."""
        plan_name = self.create_random_name('mi-plan-complex', 24)
        identity_name = self.create_random_name('mi-identity', 24)
        script_name = 'complex-script'
        mount_name = 'complex-mount'
        registry_key = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\ComplexKey'
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # Create complex managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --assign-identity [system] {} --rdp-enabled'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheckExists('id')
        ])
        
        # Verify plan shows correctly with all complex properties
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', True),
            JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Add install script
        self.cmd('appservice plan managed-instance install-script add -g {} -n {} --install-script-name {} --source-uri https://example.com/complex.ps1 --type RemoteAzureBlob'.format(
            resource_group, plan_name, script_name))
        
        # Add storage mount
        self.cmd('appservice plan managed-instance storage-mount add -g {} -n {} --mount-name {} --source //complex.share/path --destination-path C:\\complex --type FileShare'.format(
            resource_group, plan_name, mount_name))
        
        # Add registry adapter
        self.cmd('appservice plan managed-instance registry-adapter add -g {} -n {} --registry-key "{}" --type String --secret-uri https://vault.azure.net/secrets/complex'.format(
            resource_group, plan_name, registry_key))
        
        # Verify all components are present
        self.cmd('appservice plan managed-instance install-script list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1)
        ])
        
        self.cmd('appservice plan managed-instance storage-mount list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1)
        ])
        
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1)
        ])
        
        # Test identity operations on complex plan
        self.cmd('appservice plan identity show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Remove user identity
        self.cmd('appservice plan identity remove -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheck('userAssignedIdentities', None)
        ])
        
        # Clean up components
        self.cmd('appservice plan managed-instance install-script remove -g {} -n {} --install-script-name {}'.format(
            resource_group, plan_name, script_name))
        
        self.cmd('appservice plan managed-instance storage-mount remove -g {} -n {} --mount-name {}'.format(
            resource_group, plan_name, mount_name))
        
        self.cmd('appservice plan managed-instance registry-adapter remove -g {} -n {} --registry-key "{}"'.format(
            resource_group, plan_name, registry_key))
        
        # Verify cleanup
        self.cmd('appservice plan managed-instance install-script list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_identity_set_default(self, resource_group):
        """Test setting default identity for managed instance plans."""
        plan_name = self.create_random_name('mi-plan-default-id', 24)
        identity_name = self.create_random_name('mi-identity-default', 24)
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # First assign system-assigned identity
        self.cmd('appservice plan identity assign -g {} -n {} --identities [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId')
        ])
        
        # Test setting system-assigned identity as default
        self.cmd('appservice plan identity set-default -g {} -n {} --identity [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckNotExists('userAssignedIdentityResourceId')
        ])
        
        # Verify the plan shows the default identity configuration
        plan_result = self.cmd('appservice plan show -g {} -n {}'.format(
            resource_group, plan_name)).get_output_in_json()
        self.assertIsNotNone(plan_result.get('planDefaultIdentity'))
        self.assertEqual(plan_result['planDefaultIdentity']['type'], 'SystemAssigned')
        
        # Now assign user-assigned identity to the plan
        self.cmd('appservice plan identity assign -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Test setting user-assigned identity as default
        self.cmd('appservice plan identity set-default -g {} -n {} --identity {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'UserAssigned'),
            JMESPathCheck('userAssignedIdentityResourceId', identity_id)
        ])
        
        # Verify the plan shows the updated default identity configuration
        plan_result = self.cmd('appservice plan show -g {} -n {}'.format(
            resource_group, plan_name)).get_output_in_json()
        self.assertIsNotNone(plan_result.get('planDefaultIdentity'))
        self.assertEqual(plan_result['planDefaultIdentity']['type'], 'UserAssigned')
        self.assertEqual(plan_result['planDefaultIdentity']['userAssignedIdentityResourceId'], identity_id)
        
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_network_basic(self, resource_group):
        """Test basic network operations for managed instance plans."""
        plan_name = self.create_random_name('mi-plan-net', 24)
        webapp_name = self.create_random_name('mi-app-net', 24)
        vnet_name = self.create_random_name('mi-vnet', 24)
        subnet_name = self.create_random_name('mi-subnet', 24)
        
        # Create VNet and subnet
        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16'.format(
            resource_group, vnet_name))
        
        subnet_result = self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix 10.0.1.0/24 --delegations Microsoft.Web/serverFarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        subnet_id = subnet_result['id']
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Create app service
        self.cmd('webapp create -g {} -n {} --plan {}'
                 .format(resource_group, webapp_name, plan_name))

        # Test network show (should be empty initially)
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', None)
        ])
        
        # Add VNet integration using VNet and subnet names
        self.cmd('appservice plan managed-instance network add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, plan_name, vnet_name, subnet_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])
        
        # Verify network configuration shows the subnet ID
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])
        
        # Remove VNet integration
        self.cmd('appservice plan managed-instance network remove -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', None)
        ])
        
        # Verify network configuration is cleared
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', None)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_network_resource_id(self, resource_group):
        """Test network operations using resource IDs."""
        plan_name = self.create_random_name('mi-plan-net-id', 24)
        vnet_name = self.create_random_name('mi-vnet-id', 24)
        subnet_name = self.create_random_name('mi-subnet-id', 24)
        
        # Create VNet and subnet
        vnet_result = self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16'.format(
            resource_group, vnet_name)).get_output_in_json()
        vnet_id = vnet_result['newVNet']['id']
        
        subnet_result = self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix 10.0.1.0/24 --delegations Microsoft.Web/serverFarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        subnet_id = subnet_result['id']
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Add VNet integration using VNet resource ID and subnet name
        self.cmd('appservice plan managed-instance network add -g {} -n {} --vnet {} --subnet {}'.format(
            resource_group, plan_name, vnet_id, subnet_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])
        
        # Remove and re-add using subnet resource ID only
        self.cmd('appservice plan managed-instance network remove -g {} -n {}'.format(
            resource_group, plan_name))
        
        self.cmd('appservice plan managed-instance network add -g {} -n {} --subnet {}'.format(
            resource_group, plan_name, subnet_id), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_network_with_plan_creation(self, resource_group):
        """Test creating managed instance plan with network integration from the start."""
        plan_name = self.create_random_name('mi-plan-net-create', 24)
        vnet_name = self.create_random_name('mi-vnet-create', 24)
        subnet_name = self.create_random_name('mi-subnet-create', 24)
        
        # Create VNet and subnet first
        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16'.format(
            resource_group, vnet_name))
        
        subnet_result = self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix 10.0.1.0/24 --delegations Microsoft.Web/serverFarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        subnet_id = subnet_result['id']
        
        # Create managed instance plan with network integration
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --vnet {} --subnet {}'.format(
            resource_group, plan_name, vnet_name, subnet_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('network.virtualNetworkSubnetId', subnet_id)
        ])
        
        # Verify network configuration is set correctly
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_comprehensive_create(self, resource_group):
        """Test creating a managed instance plan with all features in a single command."""
        plan_name = self.create_random_name('mi-plan-comprehensive', 24)
        identity_name = self.create_random_name('mi-identity-comprehensive', 24)
        vnet_name = self.create_random_name('mi-vnet-comprehensive', 24)
        subnet_name = self.create_random_name('mi-subnet-comprehensive', 24)
        
        # Test data
        script_name = 'ComprehensiveScript'
        script_uri = 'https://example.com/comprehensive-script.ps1'
        mount_name = 'ComprehensiveMount'
        source_path = '//example.com/comprehensive-share'
        destination_path = 'D:/comprehensive-mount'
        registry_key = 'HKEY_LOCAL_MACHINE/Software/ComprehensiveApp/Key1'
        secret_uri = 'https://comprehensive.vault.azure.net/secrets/comprehensive-secret/version'
        storage_secret_uri = 'https://comprehensive.vault.azure.net/secrets/storage-secret/version'
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # Create VNet and subnet
        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16'.format(
            resource_group, vnet_name))
        subnet_result = self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix 10.0.0.0/24'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        subnet_id = subnet_result['id']
        
        # Create comprehensive managed instance plan with all features
        self.cmd('appservice plan create -g {} -n {} --number-of-workers 2 --sku P1V4 --location {} --is-managed-instance --assign-identity [system] {} --default-identity {} --rdp-enabled --subnet {} --registry-adapter registry-key="{}" type="String" secret-uri="{}" --install-script name="{}" source-uri="{}" --storage-mount mount-name="{}" source="{}" destination-path="{}" secret-uri="{}"'.format(
            resource_group, plan_name, MANAGED_INSTANCE_LOCATION, identity_id, identity_id, subnet_id, 
            registry_key, secret_uri, script_name, script_uri, mount_name, source_path, destination_path, storage_secret_uri), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', True),
            JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.tenantId'),
            JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity_id)),
            JMESPathCheck('network.virtualNetworkSubnetId', subnet_id)
        ])
        
        # Verify all features were set correctly via show command
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', True),
            JMESPathCheck('identity.type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.tenantId'),
            JMESPathCheckExists('identity.userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Verify default identity was set
        default_identity_result = self.cmd('appservice plan managed-instance identity show-default -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'UserAssigned'),
            JMESPathCheck('userAssignedIdentityResourceId', identity_id)
        ])
        
        # Verify network configuration
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', subnet_id)
        ])
        
        # Verify install script was added
        self.cmd('appservice plan managed-instance install-script list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', script_name),
            JMESPathCheck('[0].source.sourceUri', script_uri),
            JMESPathCheck('[0].source.type', 'RemoteAzureBlob')
        ])
        
        # Verify storage mount was added
        self.cmd('appservice plan managed-instance storage-mount list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', mount_name),
            JMESPathCheck('[0].source', source_path),
            JMESPathCheck('[0].destinationPath', destination_path),
            JMESPathCheck('[0].type', 'FileShare')
        ])
        
        # Verify registry adapter was added
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].registryKey', registry_key),
            JMESPathCheck('[0].type', 'String'),
            JMESPathCheck('[0].keyVaultSecretReference.secretUri', secret_uri)
        ])
