# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time


from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer)

from azure.cli.command_modules.keyvault.tests.latest.test_keyvault_commands import _create_keyvault


class NetworkPrivateLinkResourceKeyVaultScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_plr')
    def test_private_link_resource_keyvault(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-plr-', 24),
            'loc': 'centraluseuap',
            'rg': resource_group
        })

        _create_keyvault(self, self.kwargs)
        self.cmd('network private-link-resource list '
                 '--name {kv} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('value[0].groupId', 'vault'))


    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pe')
    def test_private_endpoint_connection_keyvault(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-pe-', 24),
            'loc': 'centraluseuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group
        })

        # Prepare vault and network
        keyvault = _create_keyvault(self, self.kwargs).get_output_in_json()
        self.kwargs['kv_id'] = keyvault['id']
        self.cmd('network vnet create '
                 '-n {vnet} '
                 '-g {rg} '
                 '-l {loc} '
                 '--subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update '
                 '-n {subnet} '
                 '--vnet-name {vnet} '
                 '-g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('network private-endpoint create '
                      '-g {rg} '
                      '-n {pe} '
                      '--vnet-name {vnet} '
                      '--subnet {subnet} '
                      '-l {loc} '
                      '--connection-name {pe_connection} '
                      '--private-connection-resource-id {kv_id} '
                      '--group-ids vault').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']

        # Show the connection at vault side
        keyvault = self.cmd('keyvault show -n {kv}',
                            checks=self.check('length(properties.privateEndpointConnections)', 1)).get_output_in_json()
        self.kwargs['kv_pe_id'] = keyvault['properties']['privateEndpointConnections'][0]['id']
        print(self.kwargs['kv_pe_id'])
        self.cmd('network private-endpoint-connection show '
                 '--connection-id {kv_pe_id}',
                 checks=self.check('id', '{kv_pe_id}'))
        self.kwargs['kv_pe_name'] = self.kwargs['kv_pe_id'].split('/')[-1]
        self.cmd('network private-endpoint-connection show  '
                 '--service-name {kv} '
                 '-g {rg} '
                 '--name {kv_pe_name} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('name', '{kv_pe_name}'))
        self.cmd('network private-endpoint-connection show  '
                 '--service-name {kv} '
                 '-g {rg} '
                 '-n {kv_pe_name} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('name', '{kv_pe_name}'))

        # Try running `set-policy` on the linked vault
        self.kwargs['policy_id'] = keyvault['properties']['accessPolicies'][0]['objectId']
        self.cmd('keyvault set-policy '
                 '-g {rg} '
                 '-n {kv} '
                 '--object-id {policy_id} '
                 '--certificate-permissions get list',
                 checks=self.check('length(properties.accessPolicies[0].permissions.certificates)', 2))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd('network private-endpoint-connection reject '
                 '--connection-id {kv_pe_id} '
                 '--rejection-description "{rejection_desc}"',
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('provisioningState', 'Updating')
                 ])

        max_retries = 20
        retries = 0
        while self.cmd('network private-endpoint-connection show --connection-id {kv_pe_id}'). \
                get_output_in_json()['provisioningState'] != 'Succeeded' or retries > max_retries:
            if self.is_live:
                time.sleep(5)
            retries += 1

        self.cmd('network private-endpoint-connection show --connection-id {kv_pe_id}',
                 checks=self.check('provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection approve '
                 '--service-name {kv} '
                 '--name {kv_pe_name} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults '
                 '--approval-description "{approval_desc}"',
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', '{approval_desc}'),
                     self.check('provisioningState', 'Updating')
                 ])

        retries = 0
        while self.cmd('network private-endpoint-connection show --connection-id {kv_pe_id}'). \
                get_output_in_json()['provisioningState'] != 'Succeeded' or retries > max_retries:
            if self.is_live:
                time.sleep(5)
            retries += 1

        self.cmd('network private-endpoint-connection show --connection-id {kv_pe_id}',
                 checks=self.check('provisioningState', 'Succeeded'))


if __name__ == '__main__':
    unittest.main()
