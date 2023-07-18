# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchServicesTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_list_private_link_resources(self, resource_group):
        import json

        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'public_network_access': 'Disabled'
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name} --public-access {public_network_access}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

        _private_link_resources = self.cmd('az search private-link-resource list --service-name {name} -g {rg}').get_output_in_json()

        self.assertTrue(_private_link_resources[0]['name'] == 'searchService')
        self.assertTrue(len(_private_link_resources[0]['properties']['shareablePrivateLinkResourceTypes']), 5)
        _private_link_resource_types = [item.get('name') for item in _private_link_resources[0]['properties']['shareablePrivateLinkResourceTypes']]
        self.assertTrue('vault' in _private_link_resource_types)
        self.assertTrue('blob' in _private_link_resource_types)
        self.assertTrue('plr' in _private_link_resource_types)
        self.assertTrue('Sql' in _private_link_resource_types)
        self.assertTrue('table' in _private_link_resource_types)


if __name__ == '__main__':
    unittest.main()
