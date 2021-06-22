# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AcrNetworkRuleCommandsTests(ScenarioTest):

    @ResourceGroupPreparer(location='westcentralus')
    def test_acr_network_rule(self, resource_group, resource_group_location):
        self.kwargs.update({
            'acr_provider': 'Microsoft.ContainerRegistry',
            'registry_name': self.create_random_name('clireg', 20),
            'rg_loc': resource_group_location,
            'sku': 'Premium',
            'allow_action': 'Allow',
            'deny_action': 'Deny',
            'vnet_name': 'cliregvnet',
            'subnet': 'cliregsubnet',
            'ip_address': '16.17.18.0/24'
        })

        # Create vnet and subnet
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet}',
                 checks=[self.check('newVNet.name', '{vnet_name}'),
                         self.check('newVNet.subnets[0].name', '{subnet}')])

        # Enable service endpoints
        response = self.cmd('az network vnet subnet update -g {rg} --vnet-name {vnet_name} -n {subnet} --service-endpoints {acr_provider}',
                            checks=[self.check('name', '{subnet}'),
                                    self.check('serviceEndpoints[0].service', '{acr_provider}')]).get_output_in_json()

        subnet_id = response['id']

        # Create a registry
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --default-action {deny_action}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{deny_action}'),
                         self.check('networkRuleSet.virtualNetworkRules', []),
                         self.check('networkRuleSet.ipRules', [])])

        # Add a VNet rule
        self.cmd('acr network-rule add -g {rg} -n {registry_name} --vnet-name {vnet_name} --subnet {subnet}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{deny_action}'),
                         self.check('networkRuleSet.virtualNetworkRules[0].virtualNetworkResourceId', subnet_id),
                         self.check('networkRuleSet.virtualNetworkRules[0].action', '{allow_action}'),
                         self.check('networkRuleSet.ipRules', [])])

        # Add an IP rule
        self.cmd('acr network-rule add -g {rg} -n {registry_name} --ip-address {ip_address}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{deny_action}'),
                         self.check('networkRuleSet.virtualNetworkRules[0].virtualNetworkResourceId', subnet_id),
                         self.check('networkRuleSet.virtualNetworkRules[0].action', '{allow_action}'),
                         self.check('networkRuleSet.ipRules[0].ipAddressOrRange', '{ip_address}'),
                         self.check('networkRuleSet.ipRules[0].action', '{allow_action}')])

        self.cmd('acr network-rule list -g {rg} -n {registry_name}',
                 checks=[self.check('virtualNetworkRules[0].virtualNetworkResourceId', subnet_id),
                         self.check('virtualNetworkRules[0].action', '{allow_action}'),
                         self.check('ipRules[0].ipAddressOrRange', '{ip_address}'),
                         self.check('ipRules[0].action', '{allow_action}')])

        # Switch network rule default action
        self.cmd('acr update -n {registry_name} -g {rg} --default-action {allow_action}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{allow_action}'),
                         self.check('networkRuleSet.virtualNetworkRules[0].virtualNetworkResourceId', subnet_id),
                         self.check('networkRuleSet.virtualNetworkRules[0].action', '{allow_action}'),
                         self.check('networkRuleSet.ipRules[0].ipAddressOrRange', '{ip_address}'),
                         self.check('networkRuleSet.ipRules[0].action', '{allow_action}')])

        # Remove a VNet rule
        self.cmd('acr network-rule remove -g {rg} -n {registry_name} --vnet-name {vnet_name} --subnet {subnet}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{allow_action}'),
                         self.check('networkRuleSet.virtualNetworkRules', []),
                         self.check('networkRuleSet.ipRules[0].ipAddressOrRange', '{ip_address}'),
                         self.check('networkRuleSet.ipRules[0].action', '{allow_action}')])

        # Remove an IP rule
        self.cmd('acr network-rule remove -g {rg} -n {registry_name} --ip-address {ip_address}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('networkRuleSet.defaultAction', '{allow_action}'),
                         self.check('networkRuleSet.virtualNetworkRules', []),
                         self.check('networkRuleSet.ipRules', [])])

        self.cmd('acr network-rule list -g {rg} -n {registry_name}',
                 checks=[self.check('virtualNetworkRules', []),
                         self.check('ipRules', [])])

        self.cmd('acr delete -g {rg} -n {registry_name} -y')
        self.cmd('network vnet delete -g {rg} -n {vnet_name}')
