# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


@unittest.skip("Skipped: pending service fix")
class CognitiveServicesManagedNetworkTests(ScenarioTest):

    INPUT_DATA_PATH: str = os.path.join(TEST_DIR, 'data', 'managed_network')

    @ResourceGroupPreparer()
    def test_managed_network_crud(self, resource_group):
        """Test managed network create, update, show, list operations."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}'),
                         self.check('location', '{location}'),
                         self.check('sku.name', '{sku}')])

        # Create managed network with internet outbound
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_internet_outbound',
                 checks=[
                     self.check('properties.managedNetwork.isolationMode', 'AllowInternetOutbound')
                 ])

        # Show managed network
        self.cmd('az cognitiveservices account managed-network show -n {sname} -g {rg}',
                 checks=[
                     self.check('properties.managedNetwork.isolationMode', 'AllowInternetOutbound')
                 ])

        # Update managed network to approved outbound only with standard firewall
        self.cmd('az cognitiveservices account managed-network update -n {sname} -g {rg} --managed-network allow_only_approved_outbound --firewall-sku Standard',
                 checks=[
                     self.check('properties.managedNetwork.isolationMode', 'AllowOnlyApprovedOutbound'),
                     self.check('properties.managedNetwork.firewallSku', 'Standard')
                 ])

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_managed_network_provision(self, resource_group):
        """Test managed network provisioning."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus'
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Provision managed network
        ret = self.cmd('az cognitiveservices account managed-network provision-network -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_outbound_rule_fqdn(self, resource_group):
        """Test FQDN outbound rule operations."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rule_name = 'test-fqdn-rule'
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'rule_name': rule_name
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Create FQDN outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule set -n {sname} -g {rg} --rule {rule_name} --type fqdn --destination "*.openai.azure.com" --category UserDefined',
                 checks=[
                     self.check('properties.type', 'FQDN'),
                     self.check('properties.destination', '*.openai.azure.com'),
                     self.check('properties.category', 'UserDefined')
                 ])

        # Show outbound rule (SDK deserializer returns null for name/id fields)
        self.cmd('az cognitiveservices account managed-network outbound-rule show -n {sname} -g {rg} --rule {rule_name}',
                 checks=[
                     self.check('properties.type', 'FQDN'),
                     self.check('properties.destination', '*.openai.azure.com')
                 ])

        # List outbound rules (may include system-default rules like AzureActiveDirectory)
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@) >= `1`', True)
                       ])
        self.assertEqual(ret.exit_code, 0)

        # Delete outbound rule
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule remove -n {sname} -g {rg} --rule {rule_name} --yes')
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='storage_account', allow_shared_key_access=False, kind='StorageV2')
    def test_outbound_rule_private_endpoint(self, resource_group, storage_account):
        """Test Private Endpoint outbound rule operations."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rule_name = 'test-pe-rule'
        
        # Get the real storage account resource ID
        stgacct = self.cmd('az storage account show -n {} -g {}'.format(storage_account, resource_group)).get_output_in_json()
        storage_id = stgacct['id']
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'rule_name': rule_name,
            'storage_id': storage_id
        })

        # Create cognitive services account with system-assigned identity
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --assign-identity --yes',
                 checks=[self.check('name', '{sname}')])

        # Get the managed identity principal ID
        identity = self.cmd('az cognitiveservices account show -n {sname} -g {rg}').get_output_in_json()
        principal_id = identity['identity']['principalId']
        self.kwargs['principal_id'] = principal_id

        # Grant the CS account's identity "Contributor" on the storage account
        # (needs privateEndpointConnectionsApproval/action which Network Contributor lacks)
        self.cmd('az role assignment create --assignee-object-id {principal_id} --assignee-principal-type ServicePrincipal --role "Contributor" --scope {storage_id}')

        # Wait for RBAC propagation
        time.sleep(60)

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Create Private Endpoint outbound rule
        # Note: properties.type deserializes as null because the SDK's OutboundRule._subtype_map
        # only maps FQDN (PrivateEndpoint/ServiceTag subtypes are missing from the Swagger spec)
        self.cmd('az cognitiveservices account managed-network outbound-rule set -n {sname} -g {rg} --rule {rule_name} --type privateendpoint --destination {storage_id} --subresource-target blob --category UserDefined',
                 checks=[
                     self.check('properties.category', 'UserDefined'),
                     self.check('properties.destination.subresourceTarget', 'blob')
                 ])

        # Show outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule show -n {sname} -g {rg} --rule {rule_name}',
                 checks=[
                     self.check('properties.category', 'UserDefined'),
                     self.check('properties.destination.subresourceTarget', 'blob')
                 ])

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer(random_name_length=20, parameter_name_for_location='location')
    def test_outbound_rule_service_tag(self, resource_group):
        """Test Service Tag outbound rule operations."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rule_name = 'test-st-rule'

        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'rule_name': rule_name
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Create Service Tag outbound rule - this will fail with LRO 404
        self.cmd('az cognitiveservices account managed-network outbound-rule set -n {sname} -g {rg} --rule {rule_name} --type servicetag --destination "Storage" --category Recommended',
                 checks=[
                     self.check('properties.type', 'ServiceTag'),
                     self.check('properties.category', 'Recommended')
                 ])

    @ResourceGroupPreparer()
    def test_outbound_rule_bulk_set_yaml(self, resource_group):
        """Test bulk outbound rule operations from YAML file."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rules_file = os.path.join(self.INPUT_DATA_PATH, 'managed_network_outbound_rules.yaml')
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'rules_file': rules_file.replace(os.sep, '/')
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Bulk set outbound rules from YAML
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule bulk-set -n {sname} -g {rg} --file {rules_file}')
        self.assertEqual(ret.exit_code, 0)

        # Verify rules were created (may include system-default rules)
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@) >= `2`', True)
                       ])
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_outbound_rule_bulk_set_json(self, resource_group):
        """Test bulk outbound rule operations from JSON file."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rules_file = os.path.join(self.INPUT_DATA_PATH, 'managed_network_outbound_rules.json')
        
        self.kwargs.update({
            'sname': sname,
            'kind': 'AIServices',
            'sku': 'S0',
            'location': 'eastus',
            'rules_file': rules_file.replace(os.sep, '/')
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Bulk set outbound rules from JSON
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule bulk-set -n {sname} -g {rg} --file {rules_file}')
        self.assertEqual(ret.exit_code, 0)

        # Verify rules were created (may include system-default rules)
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@) >= `2`', True)
                       ])
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
