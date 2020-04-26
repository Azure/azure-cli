# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time


from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)

from azure.cli.command_modules.keyvault.tests.latest.test_keyvault_commands import _create_keyvault


class NetworkPrivateLinkKeyVaultScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_plr')
    def test_private_link_resource_keyvault(self, resource_group):
        self.kwargs.update({
            'kv': self.create_random_name('cli-test-kv-plr-', 24),
            'loc': 'centraluseuap',
            'rg': resource_group
        })

        _create_keyvault(self, self.kwargs, additional_args='--enable-soft-delete')
        self.cmd('network private-link-resource list '
                 '--name {kv} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('value[0].properties.groupId', 'vault'))


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
        keyvault = _create_keyvault(self, self.kwargs, additional_args='--enable-soft-delete').get_output_in_json()
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
                 '--id {kv_pe_id}',
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
                 '--id {kv_pe_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('properties.provisioningState', 'Succeeded')
                 ])


        self.cmd('network private-endpoint-connection show --id {kv_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection approve '
                 '--service-name {kv} '
                 '--name {kv_pe_name} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults '
                 '--description "{approval_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}'),
                     self.check('properties.provisioningState', 'Succeeded')
                 ])

        self.cmd('network private-endpoint-connection show --id {kv_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection list --id {kv_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {sa_pec_id} -y')


class NetworkPrivateLinkStorageAccountScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sa_plr')
    @StorageAccountPreparer(name_prefix='saplr', kind='StorageV2', sku='Standard_LRS')
    def test_private_link_resource_storage_account(self, storage_account):
        self.kwargs.update({
            'sa': storage_account
        })
        self.cmd('network private-link-resource list --name {sa} -g {rg} --type Microsoft.Storage/storageAccounts', checks=[
            self.check('length(@)', 6)])


    @ResourceGroupPreparer(name_prefix='cli_test_sa_pe')
    @StorageAccountPreparer(name_prefix='saplr', kind='StorageV2')
    def test_private_endpoint_connection_storage_account(self, storage_account):
        from msrestazure.azure_exceptions import CloudError
        self.kwargs.update({
            'sa': storage_account,
            'loc': 'eastus',
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

        # Create a private endpoint connection
        pr = self.cmd('storage account private-link-resource list --account-name {sa} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.kwargs['sa_id'] = storage['id']
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {sa_id} '
            '--group-ids blob').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at storage account
        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', storage)
        self.assertEqual(len(storage['privateEndpointConnections']), 1)
        self.assertEqual(storage['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
                         'Approved')

        self.kwargs['sa_pec_id'] = storage['privateEndpointConnections'][0]['id']
        self.kwargs['sa_pec_name'] = storage['privateEndpointConnections'][0]['name']

        self.cmd('network private-endpoint-connection show --name {sa_pec_name} -g {rg} --service-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=self.check('id', '{sa_pec_id}'))

        self.cmd('network private-endpoint-connection approve --name {sa_pec_name} -g {rg} --service-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        self.cmd('network private-endpoint-connection reject --name {sa_pec_name} -g {rg} --service-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('network private-endpoint-connection list --id {sa_pec_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {sa_pec_id} -y')


if __name__ == '__main__':
    unittest.main()
