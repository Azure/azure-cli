# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CognitiveServicesManagedNetworkTests(ScenarioTest):

    INPUT_DATA_PATH: str = os.path.join(TEST_DIR, 'data')

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

        # List managed networks
        ret = self.cmd('az cognitiveservices account managed-network list -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

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
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'FQDN'),
                     self.check('properties.destination', '*.openai.azure.com'),
                     self.check('properties.category', 'UserDefined')
                 ])

        # Show outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule show -n {sname} -g {rg} --rule {rule_name}',
                 checks=[
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'FQDN')
                 ])

        # List outbound rules
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@)', 1)
                       ])
        self.assertEqual(ret.exit_code, 0)

        # Delete outbound rule
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule remove -n {sname} -g {rg} --rule {rule_name} --yes')
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
    def test_outbound_rule_private_endpoint(self, resource_group):
        """Test Private Endpoint outbound rule operations."""
        
        sname = self.create_random_name(prefix='cog', length=12)
        rule_name = 'test-pe-rule'
        
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

        # Create Private Endpoint outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule set -n {sname} -g {rg} --rule {rule_name} --type privateendpoint --destination "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/teststorage" --category Required',
                 checks=[
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'PrivateEndpoint'),
                     self.check('properties.category', 'Required')
                 ])

        # Show outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule show -n {sname} -g {rg} --rule {rule_name}',
                 checks=[
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'PrivateEndpoint')
                 ])

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

    @ResourceGroupPreparer()
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

        # Create Service Tag outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule set -n {sname} -g {rg} --rule {rule_name} --type servicetag --destination "Storage" --category Recommended',
                 checks=[
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'ServiceTag'),
                     self.check('properties.destination', 'Storage'),
                     self.check('properties.category', 'Recommended')
                 ])

        # Show outbound rule
        self.cmd('az cognitiveservices account managed-network outbound-rule show -n {sname} -g {rg} --rule {rule_name}',
                 checks=[
                     self.check('name', '{rule_name}'),
                     self.check('properties.type', 'ServiceTag')
                 ])

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)

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
            'rules_file': rules_file
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Bulk set outbound rules from YAML
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule bulk-set -n {sname} -g {rg} --file {rules_file}')
        self.assertEqual(ret.exit_code, 0)

        # Verify rules were created
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@)', 3)
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
            'rules_file': rules_file
        })

        # Create cognitive services account
        self.cmd('az cognitiveservices account create -n {sname} -g {rg} --kind {kind} --sku {sku} -l {location} --yes',
                 checks=[self.check('name', '{sname}')])

        # Create managed network
        self.cmd('az cognitiveservices account managed-network create -n {sname} -g {rg} --managed-network allow_only_approved_outbound')

        # Bulk set outbound rules from JSON
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule bulk-set -n {sname} -g {rg} --file {rules_file}')
        self.assertEqual(ret.exit_code, 0)

        # Verify rules were created
        ret = self.cmd('az cognitiveservices account managed-network outbound-rule list -n {sname} -g {rg}',
                       checks=[
                           self.check('length(@)', 2)
                       ])
        self.assertEqual(ret.exit_code, 0)

        # Delete the cognitive services account
        ret = self.cmd('az cognitiveservices account delete -n {sname} -g {rg}')
        self.assertEqual(ret.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
