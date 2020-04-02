# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrAgentPoolCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_agentpool(self, resource_group):
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'agents1_name': 'agents1',
            'agents2_name': 'agents2',
            'rg_loc': 'westus',
            'sku': 'Premium',
            'vnet_name': 'vnets2',
            'subnet_name': 'subnets2',
        })
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])

        # Create a default S1 count 1 agentpool.
        self.cmd('acr agentpool create -n {agents1_name} -r {registry_name}',
                 checks=[self.check('name', '{agents1_name}'),
                         self.check('count', 1),
                         self.check('tier', 'S1'),
                         self.check('virtualNetworkSubnetResourceId', 'null'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg_loc}')])

        # Create a S2 tier agentpool in a VNET.
        response = self.cmd('network vnet create -n {vnet_name} --subnet-name {subnet_name} -g {rg} -l {rg_loc}',
                            checks=[self.check('name', '{vnet_name}'),
                                    self.check('location', '{rg_loc}'),
                                    self.check('provisioningState', 'Succeeded'),
                                    self.check('subnets[0].name', '{subnet_name}'),
                                    self.check('subnets[0].provisioningState', 'Succeeded')]).get_output_in_json()

        self.kwargs.update({
            'subnet_id': response['subnets[0].id']
        })

        self.cmd('acr agentpool create -n {agents2_name} -r {registry_name} --tier s2 --subnet-id {subnet_id}',
                 checks=[self.check('name', '{agents2_name}'),
                         self.check('count', 1),
                         self.check('tier', 'S2'),
                         self.check('virtualNetworkSubnetResourceId', '{subnet_id}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg_loc}')])

        # list agentpools
        self.cmd('acr agentpool list -r {registry_name}',
                 checks=[self.check('[0].name', '{agents1_name}'),
                         self.check('[1].name', '{agents2_name}')])

        # show agentpool properties
        self.cmd('acr agentpool show -n {agents1_name} -r {registry_name}',
                 checks=[self.check('name', '{agents1_name}')])

        # update the first agentpool using non-default parameter values
        self.cmd('acr agentpool update -n {agents1_name} -r {registry_name} -c 2',
                 checks=[self.check('name', '{agents1_name}'),
                         self.check('count', 2),
                         self.check('tier', 'S1'),
                         self.check('virtualNetworkSubnetResourceId', 'null'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('os', 'linux'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', '{rg_loc}')])

        # test agentpool delete
        self.cmd('acr agentpool delete -n {agents2_name} -r {registry_name} -y')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
