# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI EventHub - NAMESPACE TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class SBNamespacePrivateEndpointCRUDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_sb_private')
    def test_sb_privateendpoint(self, resource_group):
        from msrestazure.azure_exceptions import CloudError
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='servicebus-nscli', length=20),
            'loc': 'eastus',
            'tags': {'tag1=value1'},
            'tags2': {'tag2=value2'},
            'sku': 'Premium',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
        })

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create Namespace
        self.cmd(
            'servicebus namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}'
            ' --sku {sku}', checks=[self.check('sku.name', '{sku}')])

        # Get Created Namespace
        getnamespace = self.cmd(
            'servicebus namespace show --resource-group {rg} --name {namespacename}').get_output_in_json()

        # Create a private endpoint connection
        pr = self.cmd('servicebus namespace private-link-resource show --namespace-name {namespacename} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        getnamesapce = self.cmd('servicebus namespace show -n {namespacename} -g {rg}').get_output_in_json()
        self.kwargs['ehn_id'] = getnamesapce['id']
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {ehn_id} '
            '--group-ids {group_id}').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at eventhubs namespace
        getnamesapce = self.cmd('servicebus namespace show -n {namespacename} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', getnamesapce)
        self.assertEqual(len(getnamesapce['privateEndpointConnections']), 1)
        self.assertEqual(getnamesapce['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
                         'Approved')

        self.kwargs['sa_pec_id'] = getnamesapce['privateEndpointConnections'][0]['id']
        self.kwargs['ehn_pec_name'] = getnamesapce['privateEndpointConnections'][0]['name']

        self.cmd('servicebus namespace private-endpoint-connection show --namespace-name {namespacename} -g {rg} --name {ehn_pec_name}',
                 checks=self.check('id', '{sa_pec_id}'))

        getstatus = self.cmd('servicebus namespace private-endpoint-connection approve --namespace-name {namespacename} -g {rg} --name {ehn_pec_name}').get_output_in_json()
        self.assertEqual(getstatus['privateLinkServiceConnectionState']['status'], 'Approved')

        getstatus = self.cmd(
            'servicebus namespace private-endpoint-connection reject --namespace-name {namespacename} -g {rg} --name {ehn_pec_name}').get_output_in_json()
        self.assertEqual(getstatus['privateLinkServiceConnectionState']['status'], 'Rejected')

        getstatus = self.cmd(
            'servicebus namespace private-endpoint-connection show --namespace-name {namespacename} -g {rg} --name {ehn_pec_name}').get_output_in_json()
        self.assertEqual(getstatus['privateLinkServiceConnectionState']['status'], 'Rejected')

        time.sleep(30)

        self.cmd('servicebus namespace private-endpoint-connection delete --id {sa_pec_id} -y')
