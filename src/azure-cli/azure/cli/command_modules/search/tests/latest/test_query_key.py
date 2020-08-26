# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchQueryKeysTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_query_key_create_delete_list(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'key_name_1': self.create_random_name(prefix='test', length=24),
            'key_name_2': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _querykeys = self.cmd('az search query-key list --service-name {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(_querykeys) == 1)
        self.assertTrue(_querykeys[0]['name'] is None)
        self.assertTrue(len(_querykeys[0]['key']) > 1)

        _querykey_1 = self.cmd('az search query-key create --service-name {name} -g {rg} -n {key_name_1}',
                               checks=[self.check('name', '{key_name_1}')]).get_output_in_json()

        self.kwargs.update({
            'key_value_1': _querykey_1['key']
        })

        _querykeys = self.cmd('az search query-key list --service-name {name} -g {rg}').get_output_in_json()
        self.assertTrue(_querykey_1['name'] in [x['name'] for x in _querykeys])

        _querykey_2 = self.cmd('az search query-key create --service-name {name} -g {rg} -n {key_name_2}',
                               checks=[self.check('name', '{key_name_2}')]).get_output_in_json()

        self.kwargs.update({
            'key_value_2': _querykey_2['key']
        })

        _querykeys = self.cmd('az search query-key list --service-name {name} -g {rg}').get_output_in_json()
        self.assertTrue(_querykey_2['name'] in [x['name'] for x in _querykeys])

        self.cmd('az search query-key delete --service-name {name} -g {rg} --key-value {key_value_1}')

        _querykeys = self.cmd('az search query-key list --service-name {name} -g {rg}').get_output_in_json()
        self.assertFalse(_querykey_1['name'] in [x['key'] for x in _querykeys])

        self.cmd('az search query-key delete --service-name {name} -g {rg} --key-value {key_value_2}')

        _querykeys = self.cmd('az search query-key list --service-name {name} -g {rg}').get_output_in_json()
        self.assertFalse(_querykey_2['name'] in [x['key'] for x in _querykeys])


if __name__ == '__main__':
    unittest.main()
