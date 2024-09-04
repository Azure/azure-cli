# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchAdminKeysTests(ScenarioTest):

    # https://vcrpy.readthedocs.io/en/latest/configuration.html#request-matching
    def setUp(self):
        self.vcr.match_on = ['scheme', 'method', 'path', 'query'] # not 'host', 'port'
        super(AzureSearchAdminKeysTests, self).setUp()

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='eastus2euap')
    def test_admin_key_show_renew(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _adminkey = self.cmd('az search admin-key show --service-name {name} -g {rg}').get_output_in_json()
        self.assertTrue(len(_adminkey['primaryKey']) > 0)
        self.assertTrue(len(_adminkey['secondaryKey']) > 0)

        self.cmd('az search admin-key renew --service-name {name} -g {rg} --key-kind primary')
        _adminkey_1 = self.cmd('az search admin-key show --service-name {name} -g {rg}').get_output_in_json()
        self.assertNotEqual(_adminkey['primaryKey'], _adminkey_1['primaryKey'])
        self.assertEqual(_adminkey['secondaryKey'], _adminkey_1['secondaryKey'])

        self.cmd('az search admin-key renew --service-name {name} -g {rg} --key-kind secondary')
        _adminkey_2 = self.cmd('az search admin-key show --service-name {name} -g {rg}').get_output_in_json()
        self.assertNotEqual(_adminkey_2['secondaryKey'], _adminkey_1['secondaryKey'])
        self.assertEqual(_adminkey_2['primaryKey'], _adminkey_1['primaryKey'])


if __name__ == '__main__':
    unittest.main()
