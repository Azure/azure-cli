# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer

class AcrCheckHealthCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_check_health(self):
        repository = 'microsoft'
        tag = 'azure-cli'

        self.kwargs.update({
            'registry': self.create_random_name('clireg', 20),
            'sku': 'Premium',
            'resource-group': 'rg',
            'ignore_errors': False,
            'yes': False,
            'vnet': None,
            'repository': repository,
            'tag': tag,
            'image': '{}:{}'.format(repository, tag),
            'reason': 'OK',
            'source_reg_id': '/subscriptions/dfb63c8c-7c89-4ef8-af13-75c1d873c895/resourcegroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub',
        })

        # Create the registry
        result = self.cmd('acr create --name {registry} --sku {sku} --resource-group {rg}').get_output_in_json()
        self.kwargs['registry'] = result['name']

        # Import image to registry.
        self.cmd('acr import -n {registry} -r {source_reg_id} --source {image}')
        
        # Check the health of the registry
        self.cmd('acr check-health --name {registry} --yes --ignore-errors')
        
        # Test if imported image can be pulled from the registry
        result = self.cmd('acr check-health --name {registry} --repository {repository} --image {tag} --yes --ignore-errors')
        self.assertTrue(result)