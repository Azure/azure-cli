# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrAgentPoolCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_agentpool(self, resource_group):
        # Agentpool prerequisites for agentpool testing
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'agents1_name': 'agents1',
            'agents2_name': 'agents2',
            'rg_loc': 'eastus',
            'sku': 'Premium',
            'vnet_name': 'agentvnets',
            'subnet_name': 'agentsubnets'
        })
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])
        response = self.cmd('network vnet create -n {vnet_name} --subnet-name {subnet_name} -g {rg} -l {rg_loc}',
                            checks=[self.check('newVNet.name', '{vnet_name}'),
                                    self.check('newVNet.location', '{rg_loc}'),
                                    self.check('newVNet.provisioningState', 'Succeeded'),
                                    self.check('newVNet.subnets[0].name', '{subnet_name}'),
                                    self.check('newVNet.subnets[0].provisioningState', 'Succeeded')]).get_output_in_json()
        self.kwargs.update({
            'subnet_id': response['newVNet']['subnets'][0]['id']
        })

        # Create a default S1 count 1 agentpool.
        self.cmd('acr agentpool create -n {agents1_name} -r {registry_name}',
                 checks=[self.check('name', '{agents1_name}'),
                         self.check('count', 1),
                         self.check('tier', 'S1'),
                         self.check('virtualNetworkSubnetResourceId', 'None'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'Linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg}')])

        # Create a S2 tier agentpool in a VNET.
        self.cmd('acr agentpool create -n {agents2_name} -r {registry_name} --tier s2 --subnet-id {subnet_id}',
                 checks=[self.check('name', '{agents2_name}'),
                         self.check('count', 1),
                         self.check('tier', 'S2'),
                         self.check('virtualNetworkSubnetResourceId', '{subnet_id}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'Linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg}')])
        # List agentpools
        self.cmd('acr agentpool list -r {registry_name}',
                 checks=[self.check('[0].name', '{agents2_name}'),
                         self.check('[1].name', '{agents1_name}')])

        # Delete Agent 2
        self.cmd('acr agentpool delete -n {agents2_name} -r {registry_name} -y')

        # Update the first agentpool using non-default parameter values
        self.cmd('acr agentpool update -n {agents1_name} -r {registry_name} -c 2',
                 checks=[self.check('name', '{agents1_name}'),
                         self.check('count', 2),
                         self.check('tier', 'S1'),
                         self.check('virtualNetworkSubnetResourceId', 'None'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'Linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg}')])

        # show agentpool properties
        self.cmd('acr agentpool show -n {agents1_name} -r {registry_name}',
                 checks=[self.check('name', '{agents1_name}')])

        # Delete registry
        self.cmd('acr delete -n {registry_name} -g {rg} -y')

        # Delete VNET
        self.cmd('network vnet delete -n {vnet_name} -g {rg}')
