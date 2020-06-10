# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
import unittest
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AzureSignalRServicePrivateEndpointScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(random_name_length=20)
    def test_signalr_private_endpoint(self, resource_group):
        signalr_name = self.create_random_name('signalr', 16)
        sku = 'Standard_S1'
        unit_count = 1
        location = 'eastus'

        self.kwargs.update({
            'location': location,
            'signalr_name': signalr_name,
            'sku': sku,
            'unit_count': unit_count,
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'private_endpoint': 'private_endpoint1',
            'private_endpoint_connection': 'private_endpoint_connection1'
        })

        signalr = self.cmd('az signalr create -n {signalr_name} -g {rg} --sku {sku}  -l {location}', checks=[
            self.check('name', '{signalr_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}')
        ]).get_output_in_json()

        # Prepare network
        self.cmd('network vnet create -g {rg} -n {vnet} -l {location} --subnet-name {subnet}')
        self.cmd('network vnet subnet update --name {subnet} --resource-group {rg} --vnet-name {vnet} --disable-private-endpoint-network-policies true')

        self.kwargs.update({
            'signalr_id': signalr['id']
        })

        # Create a private endpoint connection
        self.cmd('network private-endpoint create --resource-group {rg} --vnet-name {vnet} --subnet {subnet} --name {private_endpoint}  --private-connection-resource-id {signalr_id} --group-ids signalr --connection-name {private_endpoint_connection} --location {location} --manual-request')

        # Test private link resource list
        p_e_c = self.cmd('signalr private-link-resource list -n {signalr_name} -g {rg}', checks=[
            self.check('length(@)', 1)
        ]).get_output_in_json()

        self.kwargs.update({
            'private_endpoint_connection_id': p_e_c[0]['id']
        })

        # Test update public network rules
        self.cmd('signalr network-rule update --public-network -n {signalr_name} -g {rg} --allow RESTAPI', checks=[
            self.check('networkAcLs.publicNetwork.allow[0]', 'RESTAPI'),
            self.check('length(networkAcLs.publicNetwork.deny)', 0),
        ])

        # Test list network rules
        n_r = self.cmd('signalr network-rule list -n {signalr_name} -g {rg}', checks=[
            self.check('length(privateEndpoints)', 1)
        ]).get_output_in_json()

        self.kwargs.update({
            'connection_name': n_r['privateEndpoints'][0]['name']
        })

        # Test update private network rules
        self.cmd('signalr network-rule update --connection-name {connection_name} -n {signalr_name} -g {rg} --allow RESTAPI', checks=[
            self.check('networkAcLs.privateEndpoints[0].allow[0]', 'RESTAPI'),
            self.check('length(networkAcLs.privateEndpoints[0].deny)', 0),
        ])
