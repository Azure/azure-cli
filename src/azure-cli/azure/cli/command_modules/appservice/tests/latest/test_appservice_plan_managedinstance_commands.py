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
            JMESPathCheck('sku.name', 'P1V4'),
            JMESPathCheckExists('id')
        ])
        
        # Verify plan shows correctly and has managed instance properties
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('sku.name', 'P1V4'),
            # Validate managed instance mode is enabled via additional properties
            JMESPathCheck('isCustomMode', True)
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
            JMESPathCheck('isCustomMode', True),
            JMESPathCheck('identity.type', 'SystemAssigned,UserAssigned'),
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
            JMESPathCheck('sku.name', 'P1V4')
        ])
        
        # Verify plan shows correctly with RDP enabled
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('isCustomMode', True),
            JMESPathCheck('rdpEnabled', True)
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
            JMESPathCheck('isCustomMode', True)
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
            JMESPathCheck('type', 'SystemAssigned,UserAssigned'),
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
            JMESPathCheck('isCustomMode', True)
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
        source_path = '//example.com/share'
        destination_path = 'C:\\mounts\\share'
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('isCustomMode', True)
        ])
        
        # List storage mounts (should be empty initially)
        self.cmd('appservice plan managed-instance storage-mount list -g {} -n {}'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('length(@)', 0)
        ])
        
        # Add storage mount
        self.cmd('appservice plan managed-instance storage-mount add -g {} -n {} --mount-name {} --source {} --destination-path {} --type FileShare'.format(
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
        secret_uri = 'https://example.vault.azure.net/secrets/test-secret'
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('isCustomMode', True)
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
            JMESPathCheck('isCustomMode', True),
            JMESPathCheck('rdpEnabled', True),
            JMESPathCheck('identity.type', 'SystemAssigned,UserAssigned'),
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
            JMESPathCheck('type', 'SystemAssigned,UserAssigned'),
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
    def test_appservice_plan_identity_multiple_user_assigned(self, resource_group):
        """Test identity operations with multiple user-assigned identities."""
        plan_name = self.create_random_name('mi-plan-multi-id', 24)
        identity1_name = self.create_random_name('mi-id1', 24)
        identity2_name = self.create_random_name('mi-id2', 24)
        
        # Create managed instance plan
        self.cmd('appservice plan create -g {} -n {} --sku P1V4 --is-managed-instance'.format(
            resource_group, plan_name))
        
        # Verify basic managed instance creation
        self.cmd('appservice plan show -g {} -n {}'.format(resource_group, plan_name), checks=[
            JMESPathCheck('name', plan_name),
            JMESPathCheck('isCustomMode', True)
        ])
        
        # Create two user-assigned identities
        identity1_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity1_name)).get_output_in_json()
        identity2_result = self.cmd('identity create -g {} -n {}'.format(
            resource_group, identity2_name)).get_output_in_json()
        
        identity1_id = identity1_result['id']
        identity2_id = identity2_result['id']
        
        # Assign both identities at once with system
        self.cmd('appservice plan identity assign -g {} -n {} --identities [system] {} {}'.format(
            resource_group, plan_name, identity1_id, identity2_id), checks=[
            JMESPathCheck('type', 'SystemAssigned,UserAssigned'),
            JMESPathCheckExists('principalId'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity1_id)),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity2_id))
        ])
        
        # Remove one user identity
        self.cmd('appservice plan identity remove -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity1_id), checks=[
            JMESPathCheck('type', 'SystemAssigned,UserAssigned'),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity2_id)),
            JMESPathCheckNotExists('userAssignedIdentities."{}"'.format(identity1_id))
        ])
        
        # Remove system identity (should still have user identity)
        self.cmd('appservice plan identity remove -g {} -n {} --identities [system]'.format(
            resource_group, plan_name), checks=[
            JMESPathCheck('type', 'UserAssigned'),
            JMESPathCheck('principalId', None),
            JMESPathCheckExists('userAssignedIdentities."{}"'.format(identity2_id))
        ])
        
        # Remove remaining user identity
        self.cmd('appservice plan identity remove -g {} -n {} --identities {}'.format(
            resource_group, plan_name, identity2_id), checks=[
            JMESPathCheck('type', None)
        ])