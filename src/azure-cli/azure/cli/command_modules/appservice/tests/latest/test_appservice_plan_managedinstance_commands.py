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
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --mi-system-assigned --mi-user-assigned {}'.format(
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
        self.cmd('appservice plan identity assign -g {} -n {} --system-assigned'.format(
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
        self.cmd('appservice plan identity assign -g {} -n {} --user-assigned {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Remove user-assigned identity
        self.cmd('appservice plan identity remove -g {} -n {} --user-assigned {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheck('userAssignedIdentities', None)
        ])
        
        # Remove system-assigned identity
        self.cmd('appservice plan identity remove -g {} -n {} --system-assigned'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', None)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_install_script_operations(self, resource_group):
        """Test install script add, list, and remove operations."""
        plan_name = self.create_random_name('mi-plan-script', 24)
        storage_account_name = self.create_random_name('miscriptstg', 24)
        script_name = 'test-script'
        script_uri = f'https://{storage_account_name}.blob.core.windows.net/scripts/script1.ps1'
        
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
        storage_account_name = self.create_random_name('mistoragestg', 24)
        key_vault_name = self.create_random_name('mi-storage-kv', 20)
        mount_name = 'test-mount'
        # For UNC paths, we need 4 backslashes to get 2 in the final JSON
        source_path = f'\\\\\\\\{storage_account_name}.file.core.windows.net\\share1'
        destination_path = r'D:\mount1'
        
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
        
        # Add storage mount - use quotes around paths to handle backslashes properly
        # Include credentials for the storage mount as required by the API
        credentials_uri = f'https://{key_vault_name}.vault.azure.net/secrets/storage-credentials/version'
        
        # Expected response values (after JSON parsing)
        # The JSON response has escaped backslashes, but when parsed they become unescaped
        expected_source = f'\\\\{storage_account_name}.file.core.windows.net\\share1'  # 2 backslashes at start, 1 in middle
        expected_destination = r'D:\mount1'  # 1 backslash
        
        self.cmd('appservice plan managed-instance storage-mount add -g {} -n {} --mount-name {} --source "{}" --destination-path "{}" --type AzureFiles --credentials-secret-uri {}'.format(
            resource_group, plan_name, mount_name, source_path, destination_path, credentials_uri), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', mount_name),
            JMESPathCheck('[0].source', expected_source),
            JMESPathCheck('[0].destinationPath', expected_destination),
            JMESPathCheck('[0].type', 'AzureFiles')
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
        key_vault_name = self.create_random_name('mi-registry-kv', 20)
        registry_key = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\TestKey'
        secret_uri = f'https://{key_vault_name}.vault.azure.net/secrets/test-secret/version'
        
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
        storage_account_name = self.create_random_name('micomplexstg', 24)
        key_vault_name = self.create_random_name('mi-complex-kv', 20)
        script_name = 'complex-script'
        mount_name = 'complex-mount'
        registry_key = 'HKEY_LOCAL_MACHINE\\SOFTWARE\\ComplexKey'
        
        # Create user-assigned identity
        identity_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity_name)).get_output_in_json()
        identity_id = identity_result['id']
        
        # Create complex managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --mi-system-assigned --mi-user-assigned {} --rdp-enabled'.format(
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
        self.cmd('appservice plan managed-instance install-script add -g {} -n {} --install-script-name {} --source-uri https://{}.blob.core.windows.net/scripts/complex.ps1 --type RemoteAzureBlob'.format(
            resource_group, plan_name, script_name, storage_account_name))
        
        # Add storage mount - use proper UNC path formatting
        # For UNC paths, we need 4 backslashes to get 2 in the final JSON
        complex_source_path = f'\\\\\\\\{storage_account_name}.file.core.windows.net\\complex-share'
        complex_destination_path = r'C:\complex'
        complex_credentials_uri = f'https://{key_vault_name}.vault.azure.net/secrets/complex-storage/version'
        
        self.cmd('appservice plan managed-instance storage-mount add -g {} -n {} --mount-name {} --source "{}" --destination-path "{}" --type AzureFiles --credentials-secret-uri {}'.format(
            resource_group, plan_name, mount_name, complex_source_path, complex_destination_path, complex_credentials_uri))
        
        # Add registry adapter
        self.cmd('appservice plan managed-instance registry-adapter add -g {} -n {} --registry-key "{}" --type String --secret-uri https://{}.vault.azure.net/secrets/complex/version'.format(
            resource_group, plan_name, registry_key, key_vault_name))
        
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
        self.cmd('appservice plan identity remove -g {} -n {} --user-assigned {}'.format(
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
        self.cmd('appservice plan identity assign -g {} -n {} --system-assigned'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'SystemAssigned'),
            JMESPathCheckExists('principalId')
        ])
        
        # Test setting system-assigned identity as default
        self.cmd('appservice plan identity set-default -g {} -n {} --identity [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('identityType', 'SystemAssigned'),
            JMESPathCheckNotExists('userAssignedIdentityResourceId')
        ])
        
        # Verify the plan shows the default identity configuration
        self.cmd('appservice plan show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheckExists('properties.planDefaultIdentity'),
            JMESPathCheck('properties.planDefaultIdentity.identityType', 'SystemAssigned')
        ])
        
        # Now assign user-assigned identity to the plan
        self.cmd('appservice plan identity assign -g {} -n {} --user-assigned {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('type', 'SystemAssigned, UserAssigned'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity_id))
        ])
        
        # Test setting user-assigned identity as default
        self.cmd('appservice plan identity set-default -g {} -n {} --identity {}'.format(
            resource_group, plan_name, identity_id), checks=[
            JMESPathCheck('identityType', 'UserAssigned'),
            JMESPathCheck('userAssignedIdentityResourceId', identity_id)
        ])
        
        # Verify the plan shows the updated default identity configuration
        self.cmd('appservice plan show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheckExists('properties.planDefaultIdentity'),
            JMESPathCheck('properties.planDefaultIdentity.identityType', 'UserAssigned'),
            JMESPathCheck('properties.planDefaultIdentity.userAssignedIdentityResourceId', identity_id)
        ])
        
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
            JMESPathCheck('virtualNetworkSubnetId', "")
        ])
        
        # Verify network configuration is cleared
        self.cmd('appservice plan managed-instance network show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('virtualNetworkSubnetId', "")
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
        
        # Add VNet integration using subnet resource ID only
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
            JMESPathCheck('isCustomMode', True),
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
        plan_name = self.create_random_name('mi-plan-comp', 24)
        identity_name = self.create_random_name('mi-identity-comp', 24)
        vnet_name = self.create_random_name('mi-vnet-comp', 24)
        subnet_name = self.create_random_name('mi-subnet-comp', 24)
        
        # Generate random names for storage account and key vault
        storage_account_name = self.create_random_name('micompstg', 24)
        key_vault_name = self.create_random_name('mi-comp-kv', 20)
        
        # Test data using generated names
        script_name = 'Script1'
        script_uri = f'https://{storage_account_name}.blob.core.windows.net/scripts/comprehensive-script.ps1'
        mount_name = 'Mount1'
        # Use proper Windows UNC path format with proper escaping
        source_path = f'\\\\\\\\{storage_account_name}.file.core.windows.net\\comprehensive-share'  # 4 backslashes for UNC path
        destination_path = r'D:\comprehensive-mount'  # 1 backslash for drive path
        registry_key = 'HKEY_LOCAL_MACHINE\\Software\\ComprehensiveApp\\Key1'  # Use backslashes for registry keys
        secret_uri = f'https://{key_vault_name}.vault.azure.net/secrets/comprehensive-secret/version'
        storage_secret_uri = f'https://{key_vault_name}.vault.azure.net/secrets/storage-secret/version'
        
        # Expected response values (after JSON parsing)
        expected_source = f'\\\\{storage_account_name}.file.core.windows.net\\comprehensive-share'  # 2 backslashes after JSON parsing
        expected_destination = r'D:\comprehensive-mount'  # 1 backslash after JSON parsing
        
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
        self.cmd('appservice plan create -g {} -n {} --number-of-workers 2 --sku P1V4 --location {} --is-managed-instance --mi-system-assigned --mi-user-assigned {} --default-identity {} --rdp-enabled --subnet {} --registry-adapter registry-key="{}" type="String" secret-uri="{}" --install-script name="{}" source-uri="{}" type="RemoteAzureBlob" --storage-mount name="{}" source="{}" destination-path="{}" type="AzureFiles" credentials-secret-uri="{}"'.format(
            resource_group, plan_name, MANAGED_INSTANCE_LOCATION, identity_id, identity_id, subnet_id, 
            registry_key, secret_uri, script_name, script_uri, mount_name, source_path, destination_path, storage_secret_uri), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            JMESPathCheck('isCustomMode', True),
            JMESPathCheck('rdpEnabled', True),
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
        
        # Verify default identity was set (this should be visible in the plan show command)
        self.cmd('appservice plan show -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheckExists('properties.planDefaultIdentity'),
            JMESPathCheck('properties.planDefaultIdentity.identityType', 'UserAssigned'),
            JMESPathCheck('properties.planDefaultIdentity.userAssignedIdentityResourceId', identity_id)
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
            JMESPathCheck('[0].source', expected_source),
            JMESPathCheck('[0].destinationPath', expected_destination),
            JMESPathCheck('[0].type', 'AzureFiles')  # Changed from 'FileShare' to 'AzureFiles'
        ])
        
        # Verify registry adapter was added
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].registryKey', registry_key),
            JMESPathCheck('[0].type', 'String'),
            JMESPathCheck('[0].keyVaultSecretReference.secretUri', secret_uri)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_instance_operations(self, resource_group):
        """Test managed instance plan instance list and recycle operations."""
        plan_name = self.create_random_name('mi-plan-inst', 24)
        webapp_name = self.create_random_name('mi-webapp-inst', 24)

        # Create managed instance plan with 3 instances
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --number-of-workers 3'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            JMESPathCheck('sku.capacity', 3),
            JMESPathCheck('isCustomMode', True)
        ])

        self.cmd(
            'webapp create -g {} -n {} --plan {}'.format(resource_group, webapp_name, plan_name))

        # List instances - should have 3 instances
        instances_result = self.cmd('appservice plan managed-instance instance list -g {} --name {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('instanceCount', 3)
        ]).get_output_in_json()

        # Verify instances have required properties
        for i, instance in enumerate(instances_result['instances']):
            self.assertIsNotNone(instance.get('instanceName'), f"Instance {i} should have instanceName")

        # Get the last worker name for recycle test
        last_worker_name = instances_result['instances'][2]['instanceName']

        # Test recycle operation on the last worker
        # Recycle command doesn't return output, so we just verify it runs successfully
        self.cmd('appservice plan managed-instance instance recycle -g {} --name {} --instance-name {}'.format(
            resource_group, plan_name, last_worker_name))

        # Verify instances list still works after recycle
        self.cmd('appservice plan managed-instance instance list -g {} --name {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 3)
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=MANAGED_INSTANCE_LOCATION)
    def test_appservice_plan_managed_instance_comprehensive_update(self, resource_group):
        """Test updating a managed instance plan with all features in a single command."""
        plan_name = self.create_random_name('mi-plan-update', 24)
        vnet_name = self.create_random_name('mi-vnet-update', 24)
        subnet_name = self.create_random_name('mi-subnet-update', 24)
        
        # Generate random names for storage account and key vault
        storage_account_name = self.create_random_name('miupdatestg', 24)
        key_vault_name = self.create_random_name('mi-update-kv', 20)
        
        # Test data using generated names
        script_name = 'UpdateScript1'
        script_uri = f'https://{storage_account_name}.blob.core.windows.net/scripts/update-script.ps1'
        mount_name = 'UpdateMount1'
        # Use proper Windows UNC path format with proper escaping
        source_path = f'\\\\\\\\{storage_account_name}.file.core.windows.net\\update-share'  # 4 backslashes for UNC path
        destination_path = r'D:\update-mount'  # 1 backslash for drive path
        registry_key = 'HKEY_LOCAL_MACHINE\\Software\\UpdateApp\\Key1'  # Use backslashes for registry keys
        secret_uri = f'https://{key_vault_name}.vault.azure.net/secrets/update-secret/version'
        storage_secret_uri = f'https://{key_vault_name}.vault.azure.net/secrets/update-storage-secret/version'
        
        # Expected response values (after JSON parsing)
        expected_source = f'\\\\{storage_account_name}.file.core.windows.net\\update-share'  # 2 backslashes after JSON parsing
        expected_destination = r'D:\update-mount'  # 1 backslash after JSON parsing
        
        # Create VNet and subnet
        self.cmd('network vnet create -g {} -n {} --address-prefix 10.0.0.0/16'.format(
            resource_group, vnet_name))
        subnet_result = self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefix 10.0.1.0/24 --delegations Microsoft.Web/serverFarms'.format(
            resource_group, vnet_name, subnet_name)).get_output_in_json()
        subnet_id = subnet_result['id']
        
        # Create basic managed instance plan with system-assigned identity only
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance --mi-system-assigned'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4'),
            JMESPathCheck('isCustomMode', True),
            JMESPathCheck('identity.type', 'SystemAssigned')
        ])
        
        # Verify initial state
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', None),  # Should not be set initially
            JMESPathCheck('properties.planDefaultIdentity', None),  # Should not be set initially
            JMESPathCheck('identity.type', 'SystemAssigned')
        ])
        
        # Now perform comprehensive update with all managed instance features
        self.cmd('appservice plan update -g {} -n {} --default-identity [system] --rdp-enabled --vnet {} --subnet {} --registry-adapter registry-key="{}" type="String" secret-uri="{}" --install-script name="{}" source-uri="{}" type="RemoteAzureBlob" --storage-mount name="{}" source="{}" destination-path="{}" type="AzureFiles" credentials-secret-uri="{}"'.format(
            resource_group, plan_name, vnet_name, subnet_name,
            registry_key, secret_uri, script_name, script_uri, mount_name, source_path, destination_path, storage_secret_uri), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4')
        ])
        
        # Verify all features were set correctly via comprehensive show command
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('properties.isCustomMode', True),
            JMESPathCheck('properties.rdpEnabled', True),
            JMESPathCheck('identity.type', 'SystemAssigned'),
            JMESPathCheckExists('identity.principalId'),
            JMESPathCheckExists('identity.tenantId'),
            JMESPathCheckExists('properties.planDefaultIdentity'),
            JMESPathCheck('properties.planDefaultIdentity.identityType', 'SystemAssigned'),
            JMESPathCheckNotExists('properties.planDefaultIdentity.userAssignedIdentityResourceId')
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
            JMESPathCheck('[0].source', expected_source),
            JMESPathCheck('[0].destinationPath', expected_destination),
            JMESPathCheck('[0].type', 'AzureFiles')
        ])
        
        # Verify registry adapter was added
        self.cmd('appservice plan managed-instance registry-adapter list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].registryKey', registry_key),
            JMESPathCheck('[0].type', 'String'),
            JMESPathCheck('[0].keyVaultSecretReference.secretUri', secret_uri)
        ])
        
        # Test that we can update individual components later
        # Update RDP to disabled
        self.cmd('appservice plan update -g {} -n {} --rdp-enabled false'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1v4')
        ])
        
        # Verify RDP was disabled
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('properties.rdpEnabled', False)
        ])
