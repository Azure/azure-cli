# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI Relay - NAMESPACE PRIVATE ENDPOINT CONNECTION TEST DEFINITIONS

import time

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)


# pylint: disable=line-too-long
# pylint: disable=too-many-lines


class RelayPrivateEndpointScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_relay_pe')
    def test_relay_privateendpoint(self, resource_group):
        self.kwargs.update({
            'namespacename': self.create_random_name(prefix='relay-nscli', length=20),
            'loc': 'eastus',
            'tags': 'tag1=value1',
            'sku': 'Standard',
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
            'relay namespace create --resource-group {rg} --name {namespacename} --location {loc} --tags {tags}',
            checks=[self.check('name', self.kwargs['namespacename'])])

        # Get Created Namespace
        namespace = self.cmd(
            'relay namespace show --resource-group {rg} --name {namespacename}').get_output_in_json()
        self.kwargs['relay_id'] = namespace['id']

        # Get the private link resource group id
        pr = self.cmd(
            'relay namespace private-link-resource list --namespace-name {namespacename} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        # Create a private endpoint
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {relay_id} '
            '--group-ids {group_id}').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])

        # Show the connection at relay namespace
        namespace = self.cmd(
            'relay namespace show -n {namespacename} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', namespace)
        self.assertEqual(len(namespace['privateEndpointConnections']), 1)
        self.assertEqual(
            namespace['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs['pec_id'] = namespace['privateEndpointConnections'][0]['id']
        self.kwargs['pec_name'] = namespace['privateEndpointConnections'][0]['name']

        # List private endpoint connections
        self.cmd('relay namespace private-endpoint-connection list --namespace-name {namespacename} -g {rg}')

        # Show the private endpoint connection
        self.cmd(
            'relay namespace private-endpoint-connection show --namespace-name {namespacename} -g {rg} --name {pec_name}',
            checks=self.check('id', '{pec_id}'))

        # Reject the private endpoint connection (auto-approved on creation).
        # The service only allows Approved -> Rejected; Rejected -> Approved is not permitted.
        getstatus = self.cmd(
            'relay namespace private-endpoint-connection update --namespace-name {namespacename} -g {rg} --name {pec_name} '
            '--private-link-service-connection-state status=Rejected description=Rejected').get_output_in_json()
        self.assertEqual(getstatus['privateLinkServiceConnectionState']['status'], 'Rejected')

        # Show reflecting rejected status
        getstatus = self.cmd(
            'relay namespace private-endpoint-connection show --namespace-name {namespacename} -g {rg} --name {pec_name}').get_output_in_json()
        self.assertEqual(getstatus['privateLinkServiceConnectionState']['status'], 'Rejected')

        while getstatus['provisioningState'] != 'Succeeded':
            time.sleep(30)
            getstatus = self.cmd(
                'relay namespace private-endpoint-connection show --namespace-name {namespacename} -g {rg} --name {pec_name}').get_output_in_json()

        # Delete the private endpoint connection
        self.cmd(
            'relay namespace private-endpoint-connection delete --namespace-name {namespacename} -g {rg} --name {pec_name} --yes')

        # Delete Namespace
        self.cmd('relay namespace delete --resource-group {rg} --name {namespacename}')
