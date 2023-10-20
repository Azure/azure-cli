# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
import unittest


class AzureSearchServicesTests(ScenarioTest):

    # https://vcrpy.readthedocs.io/en/latest/configuration.html#request-matching
    def setUp(self):
        self.vcr.match_on = ['scheme', 'method', 'path', 'query'] # not 'host', 'port'
        super(AzureSearchServicesTests, self).setUp()

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test', location='westcentralus')
    @StorageAccountPreparer(name_prefix='satest', kind='StorageV2')
    def test_shared_private_link_resource_crud(self, resource_group, storage_account):
        self.kwargs.update({
            'sku_name': 'basic',
            'search_service_name': self.create_random_name(prefix='azstest', length=24),
            'public_network_access': 'Disabled',
            'shared_private_link_resource_name': self.create_random_name(prefix='spltest', length=24),
            'storage_account_name': storage_account,
            'shared_private_link_resource_group_id': 'blob',
            'shared_private_link_resource_request_provisioning_state_default': 'Succeeded',
            'shared_private_link_resource_request_status_default': 'Pending',
            'shared_private_link_resource_request_message_default': 'Please approve',
            'shared_private_link_resource_request_message': 'Please approve again'
        })

        self.cmd(
            'az search service create -n {search_service_name} -g {rg} --sku {sku_name} --public-network-access {public_network_access}',
            checks=[self.check('name', '{search_service_name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')])

        _account_resource_id = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}".format(self.get_subscription_id(), resource_group, storage_account)

        self.kwargs.update({'_account_resource_id': _account_resource_id})

        # create shared private link resource
        _tpe_resource = self.cmd('az search shared-private-link-resource create --service-name {search_service_name} -g {rg} --resource-id {_account_resource_id} --name {shared_private_link_resource_name} --group-id {shared_private_link_resource_group_id}',
                                 checks=[self.check('name', '{shared_private_link_resource_name}'),
                                         self.check('properties.provisioningState', '{shared_private_link_resource_request_provisioning_state_default}'),
                                         self.check('properties.requestMessage', '{shared_private_link_resource_request_message_default}'),
                                         self.check('properties.status', '{shared_private_link_resource_request_status_default}')]).get_output_in_json()

        # update shared private link resource
        self.cmd('az search shared-private-link-resource update --service-name {search_service_name} -g {rg} --resource-id {_account_resource_id} --name {shared_private_link_resource_name} --group-id {shared_private_link_resource_group_id} --request-message "{shared_private_link_resource_request_message}"',
                 checks=[self.check('properties.requestMessage', '{shared_private_link_resource_request_message}')])

        # list shared private link resources
        _tpe_resources = self.cmd('az search shared-private-link-resource list --service-name {search_service_name} -g {rg}').get_output_in_json()
        self.assertTrue(len(_tpe_resources) == 1)

        # get shared private link resource
        _tpe_resource = self.cmd('az search shared-private-link-resource show --service-name {search_service_name} -g {rg} --name {shared_private_link_resource_name}').get_output_in_json()
        self.assertTrue(_tpe_resource['properties']['privateLinkResourceId'] == _account_resource_id)

        # delete shared private link resource
        self.cmd('az search shared-private-link-resource delete --service-name {search_service_name} -g {rg} --name {shared_private_link_resource_name} -y')

        # list shared private link resources
        _tpe_resources = self.cmd('az search shared-private-link-resource list --service-name {search_service_name} -g {rg}').get_output_in_json()
        self.assertTrue(len(_tpe_resources) == 0)

        # get shared private link resource
        with self.assertRaises(SystemExit) as ex:
            self.cmd('az search shared-private-link-resource show --service-name {search_service_name} -g {rg} --name {shared_private_link_resource_name}')
        self.assertEqual(ex.exception.code, 3)

if __name__ == '__main__':
    unittest.main()
