# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchServicesTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_private_endpoint_connection_crud(self, resource_group):
        self.kwargs.update({
            'sku_name': 'basic',
            'search_service_name': self.create_random_name(prefix='test', length=24),
            'vnet_name': self.create_random_name(prefix='vnet', length=24),
            'subnet_name': self.create_random_name(prefix='subnet', length=24),
            'private_endpoint_name': self.create_random_name(prefix='testpe', length=24),
            'private_endpoint_connection_name': self.create_random_name(prefix='testpec', length=24),
            'private_endpoint_connection_status_approved': 'Approved',
            'private_endpoint_connection_status_pending': 'Pending',
            'private_endpoint_connection_status_rejected': 'Rejected',
            'private_endpoint_connection_status_disconnected': 'Disconnected',
            'private_endpoint_connection_description_approved': 'Approved by test',
            'private_endpoint_connection_description_pending': 'Pending by test',
            'private_endpoint_connection_description_rejected': 'Rejected by test',
            'public_network_access': 'Disabled'
        })

        # create search service
        _search_service = self.cmd(
            'az search service create -n {search_service_name} -g {rg} --sku {sku_name} --public-access {public_network_access}',
            checks=[self.check('name', '{search_service_name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('publicNetworkAccess', '{public_network_access}')]).get_output_in_json()
        _search_service_resource_id = _search_service['id']

        self.kwargs.update({
            '_search_service_resource_id': _search_service_resource_id,
        })

        # create vnet
        self.cmd('az network vnet create --resource-group {rg} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('az network vnet subnet create --resource-group {rg} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('az network vnet subnet update --resource-group {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        # create private endpoint
        self.cmd('az network private-endpoint create --resource-group {rg} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {_search_service_resource_id} --connection-name {private_endpoint_connection_name} --group-id searchService')

        _search_service = self.cmd('az search service show -n {search_service_name} -g {rg}').get_output_in_json()
        self.assertTrue(_search_service['name'] == self.kwargs['search_service_name'])
        self.assertTrue(len(_search_service['privateEndpointConnections']) == 1)

        # list private endpoints
        _private_endpoint_connections = self.cmd('az search private-endpoint-connection list -g {rg} --service-name {search_service_name}').get_output_in_json()
        self.assertTrue(len(_private_endpoint_connections) == 1)

        # get private endpoint
        _private_endpoint_connection_name = _private_endpoint_connections[0]['name']
        self.kwargs.update({
            '_private_endpoint_connection_name': _private_endpoint_connection_name,
        })
        self.cmd('az search private-endpoint-connection show --name {_private_endpoint_connection_name} -g {rg} --service-name {search_service_name}',
                 checks=[self.check('name', '{_private_endpoint_connection_name}'),
                         self.check('properties.privateLinkServiceConnectionState.status', '{private_endpoint_connection_status_approved}')])

        # update private endpoint
        self.cmd('az search private-endpoint-connection update --service-name {search_service_name} -g {rg} --name {_private_endpoint_connection_name} --status {private_endpoint_connection_status_rejected} --description "{private_endpoint_connection_description_rejected}" --actions-required "No action required"',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', '{private_endpoint_connection_status_rejected}'),
                         self.check('properties.privateLinkServiceConnectionState.description', '{private_endpoint_connection_description_rejected}')])

        self.cmd('az search private-endpoint-connection update --service-name {search_service_name} -g {rg} --name {_private_endpoint_connection_name} --status {private_endpoint_connection_status_pending} --description "{private_endpoint_connection_description_pending}" --actions-required "No action required"',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', '{private_endpoint_connection_status_pending}'),
                         self.check('properties.privateLinkServiceConnectionState.description', '{private_endpoint_connection_description_pending}')])

        self.cmd('az search private-endpoint-connection update --service-name {search_service_name} -g {rg} --name {_private_endpoint_connection_name} --status {private_endpoint_connection_status_approved} --description "{private_endpoint_connection_description_approved}" --actions-required "No action required"',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', '{private_endpoint_connection_status_approved}'),
                         self.check('properties.privateLinkServiceConnectionState.description', '{private_endpoint_connection_description_approved}')])

        # delete private endpoint
        self.cmd('az search private-endpoint-connection delete --service-name {search_service_name} -g {rg} --name {_private_endpoint_connection_name} -y',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', '{private_endpoint_connection_status_disconnected}')])

        # get private endpoint
        with self.assertRaises(SystemExit) as ex:
            self.cmd('az search private-endpoint-connection show --name {_private_endpoint_connection_name} -g {rg} --service-name {search_service_name}')
        self.assertEqual(ex.exception.code, 3)

        # list private endpoints
        _private_endpoint_connections = self.cmd('az search private-endpoint-connection list -g {rg} --service-name {search_service_name}').get_output_in_json()
        self.assertTrue(len(_private_endpoint_connections) == 0)


if __name__ == '__main__':
    unittest.main()
