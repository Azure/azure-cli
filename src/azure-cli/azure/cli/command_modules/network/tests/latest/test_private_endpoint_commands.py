# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import uuid
import unittest

from azure.core.exceptions import HttpResponseError

from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, KeyVaultPreparer, live_only, record_only)
from azure.cli.core.util import parse_proxy_resource_id, CLIError

from azure.cli.command_modules.rdbms.tests.latest.test_rdbms_commands import ServerPreparer
from azure.cli.command_modules.batch.tests.latest.batch_preparers import BatchAccountPreparer, BatchScenarioMixin
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class NetworkPrivateLinkKeyVaultScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_plr')
    @KeyVaultPreparer(name_prefix='cli-test-kv-plr-', location='centraluseuap')
    def test_private_link_resource_keyvault(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'centraluseuap',
            'rg': resource_group
        })

        self.cmd('network private-link-resource list '
                 '--name {kv} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('@[0].properties.groupId', 'vault'))

    @ResourceGroupPreparer(name_prefix='cli_test_hsm_plr_rg')
    def test_mhsm_private_link_resource(self, resource_group):
        self.kwargs.update({
            'hsm': self.create_random_name('cli-test-hsm-plr-', 24),
            'loc': 'centraluseuap'
        })
        self.cmd('keyvault create --hsm-name {hsm} -g {rg} -l {loc} '
                 '--administrators "3707fb2f-ac10-4591-a04f-8b0d786ea37d"')
        self.cmd('network private-link-resource list '
                 '--name {hsm} '
                 '-g {rg} '
                 '--type microsoft.keyvault/managedHSMs',
                 checks=self.check('@[0].properties.groupId', 'managedhsm'))
        self.cmd('keyvault delete --hsm-name {hsm} -g {rg}')
        self.cmd('keyvault purge --hsm-name {hsm} -l {loc}')

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pe')
    @KeyVaultPreparer(name_prefix='cli-test-kv-pe-', location='centraluseuap')
    def test_private_endpoint_connection_keyvault(self, resource_group):
        self.kwargs.update({
            'loc': 'centraluseuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group
        })

        # Prepare vault and network
        self.kwargs['kv_id'] = self.cmd('keyvault show -n {kv} -g {rg} --query "id" -otsv').output
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
                      '--group-id vault').get_output_in_json()
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
                 '--resource-name {kv} '
                 '-g {rg} '
                 '--name {kv_pe_name} '
                 '--type microsoft.keyvault/vaults',
                 checks=self.check('name', '{kv_pe_name}'))
        self.cmd('network private-endpoint-connection show  '
                 '--resource-name {kv} '
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
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {kv_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection approve '
                 '--resource-name {kv} '
                 '--name {kv_pe_name} '
                 '-g {rg} '
                 '--type microsoft.keyvault/vaults '
                 '--description "{approval_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {kv_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection list --id {kv_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {kv_pe_id} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_hsm_pe')
    def test_hsm_private_endpoint_connection(self, resource_group):
        self.kwargs.update({
            'hsm': self.create_random_name('cli-test-hsm-pe-', 24),
            'loc': 'centraluseuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group
        })

        # Prepare hsm and network
        hsm = self.cmd('keyvault create --hsm-name {hsm} -g {rg} -l {loc} '
                       '--administrators "3707fb2f-ac10-4591-a04f-8b0d786ea37d"').get_output_in_json()
        self.kwargs['hsm_id'] = hsm['id']
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
                      '--private-connection-resource-id {hsm_id} '
                      '--group-id managedhsm').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']

        # Show the connection at vault side
        keyvault = self.cmd('keyvault show --hsm-name {hsm}',
                            checks=self.check('length(properties.privateEndpointConnections)', 1)).get_output_in_json()
        self.kwargs['hsm_pe_id'] = keyvault['properties']['privateEndpointConnections'][0]['id']

        self.cmd('network private-endpoint-connection show '
                 '--id {hsm_pe_id}',
                 checks=self.check('id', '{hsm_pe_id}'))
        self.kwargs['hsm_pe_name'] = self.kwargs['hsm_pe_id'].split('/')[-1]
        self.cmd('network private-endpoint-connection show  '
                 '--resource-name {hsm} '
                 '-g {rg} '
                 '--name {hsm_pe_name} '
                 '--type Microsoft.KeyVault/managedHSMs',
                 checks=self.check('name', '{hsm_pe_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })

        self.cmd('network private-endpoint-connection approve '
                 '--resource-name {hsm} '
                 '--name {hsm_pe_name} '
                 '-g {rg} '
                 '--type Microsoft.KeyVault/managedHSMs '
                 '--description "{approval_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {hsm_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection reject '
                 '--id {hsm_pe_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {hsm_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection list --id {hsm_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {hsm_pe_id} -y')

        # clear resources
        self.cmd('network private-endpoint delete -g {rg} -n {pe}')
        self.cmd('keyvault delete --hsm-name {hsm} -g {rg}')
        self.cmd('keyvault purge --hsm-name {hsm} -l {loc}')


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
            '--group-id blob').get_output_in_json()
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

        self.cmd('network private-endpoint-connection show --name {sa_pec_name} -g {rg} --resource-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=self.check('id', '{sa_pec_id}'))

        # cannot approve it from auto-approved state
        # self.cmd('network private-endpoint-connection approve --name {sa_pec_name} -g {rg} --resource-name {sa} --type Microsoft.Storage/storageAccounts',
        #          checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        self.cmd('network private-endpoint-connection reject --name {sa_pec_name} -g {rg} --resource-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('network private-endpoint-connection list --id {sa_pec_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {sa_pec_id} -y')

class NetworkPrivateLinkAMLScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_aml_plr')
    def test_private_link_resource_aml(self):
        self.kwargs.update({
            'workspace_name': self.create_random_name('testaml', 20)
        })
        self.cmd('extension add -n azure-cli-ml')
        result = self.cmd('ml workspace create --workspace-name {workspace_name} --resource-group {rg}').get_output_in_json()
        self.kwargs['workspace_id'] = result['id']
        self.cmd('network private-link-resource list --id {workspace_id}', checks=[
            self.check('length(@)', 1)])

    @live_only()
    @ResourceGroupPreparer(location='centraluseuap')
    def test_private_endpoint_connection_aml(self):
        self.kwargs.update({
            'workspace_name': self.create_random_name('testaml', 20),
            'vnet_name': self.create_random_name('testvnet', 20),
            'subnet_name': self.create_random_name('testsubnet', 20),
            'endpoint_name': self.create_random_name('priv_endpoint', 25),
            'endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'second_endpoint_name': self.create_random_name('priv_endpoint', 25),
            'second_endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'description_msg': 'somedescription'
        })

        # create subnet with disabled endpoint network policies
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        self.cmd('extension add -n azure-cli-ml')
        result = self.cmd('ml workspace create --workspace-name {workspace_name} --resource-group {rg}').get_output_in_json()
        self.kwargs['workspace_id'] = result['id']

        # add an endpoint and approve it
        result = self.cmd(
            'network private-endpoint create -n {endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name}  '
            '--private-connection-resource-id {workspace_id} --group-id amlworkspace --connection-name {endpoint_conn_name} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd(
            'network private-endpoint-connection list -g {rg} --name {workspace_name} --type Microsoft.MachineLearningServices/workspaces').get_output_in_json()
        self.kwargs['endpoint_request'] = result[0]['name']

        self.cmd(
            'network private-endpoint-connection approve -g {rg} --resource-name {workspace_name} -n {endpoint_request} --description {description_msg} --type Microsoft.MachineLearningServices/workspaces',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}')
            ])

        # add an endpoint and then reject it
        self.cmd(
            'network private-endpoint create -n {second_endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name} --private-connection-resource-id {workspace_id} --group-id amlworkspace --connection-name {second_endpoint_conn_name} --manual-request')
        result = self.cmd('network private-endpoint-connection list -g {rg} --name {workspace_name} --type Microsoft.MachineLearningServices/workspaces').get_output_in_json()

        # the connection request name starts with the workspaces name
        self.kwargs['second_endpoint_request'] = [conn['name'] for conn in result if
                                                  self.kwargs['second_endpoint_name'].lower() in
                                                  conn['properties']['privateEndpoint']['id'].lower()][0]

        self.cmd(
            'network private-endpoint-connection reject -g {rg} --resource-name {workspace_name} -n {second_endpoint_request} --description {description_msg} --type Microsoft.MachineLearningServices/workspaces',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}')
            ])

        # list endpoints
        self.cmd('network private-endpoint-connection list -g {rg} -n {workspace_name} --type Microsoft.MachineLearningServices/workspaces', checks=[
            self.check('length(@)', '2'),
        ])

        # remove endpoints
        self.cmd(
            'network private-endpoint-connection delete -g {rg} --resource-name {workspace_name} -n {second_endpoint_request} --type Microsoft.MachineLearningServices/workspaces -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list -g {rg} -n {workspace_name} --type Microsoft.MachineLearningServices/workspaces', checks=[
            self.check('length(@)', '1'),
        ])
        self.cmd('network private-endpoint-connection show -g {rg} --resource-name {workspace_name} -n {endpoint_request} --type Microsoft.MachineLearningServices/workspaces', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}'),
            self.check('name', '{endpoint_request}')
        ])

        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {workspace_name} -n {endpoint_request} --type Microsoft.MachineLearningServices/workspaces -y')


class NetworkPrivateLinkACRScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sa_plr')
    def test_private_link_resource_acr(self):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20)
        })
        result = self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium').get_output_in_json()
        self.kwargs['registry_id'] = result['id']
        self.cmd('network private-link-resource list --id {registry_id}', checks=[
            self.check('length(@)', 1)])

    @ResourceGroupPreparer(location='centraluseuap')
    def test_private_endpoint_connection_acr(self, resource_group):
        self.kwargs.update({
            'registry_name': self.create_random_name('testreg', 20),
            'vnet_name': self.create_random_name('testvnet', 20),
            'subnet_name': self.create_random_name('testsubnet', 20),
            'endpoint_name': self.create_random_name('priv_endpoint', 25),
            'endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'second_endpoint_name': self.create_random_name('priv_endpoint', 25),
            'second_endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'description_msg': 'somedescription'
        })

        # create subnet with disabled endpoint network policies
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        result = self.cmd('acr create --name {registry_name} --resource-group {rg} --sku premium').get_output_in_json()
        self.kwargs['registry_id'] = result['id']

        # add an endpoint and approve it
        result = self.cmd(
            'network private-endpoint create -n {endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name}  '
            '--private-connection-resource-id {registry_id} --group-id registry --connection-name {endpoint_conn_name} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd(
            'network private-endpoint-connection list -g {rg} --name {registry_name} --type Microsoft.ContainerRegistry/registries').get_output_in_json()
        self.kwargs['endpoint_request'] = result[0]['name']

        self.cmd(
            'network private-endpoint-connection approve -g {rg} --resource-name {registry_name} -n {endpoint_request} --description {description_msg} --type Microsoft.ContainerRegistry/registries',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}')
            ])

        # add an endpoint and then reject it
        self.cmd(
            'network private-endpoint create -n {second_endpoint_name} -g {rg} --subnet {subnet_name} --vnet-name {vnet_name} --private-connection-resource-id {registry_id} --group-id registry --connection-name {second_endpoint_conn_name} --manual-request')
        result = self.cmd('network private-endpoint-connection list -g {rg} --name {registry_name} --type Microsoft.ContainerRegistry/registries').get_output_in_json()

        # the connection request name starts with the registry / resource name
        self.kwargs['second_endpoint_request'] = [conn['name'] for conn in result if
                                                  self.kwargs['second_endpoint_name'].lower() in
                                                  conn['properties']['privateEndpoint']['id'].lower()][0]

        self.cmd(
            'network private-endpoint-connection reject -g {rg} --resource-name {registry_name} -n {second_endpoint_request} --description {description_msg} --type Microsoft.ContainerRegistry/registries',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}')
            ])

        # list endpoints
        self.cmd('network private-endpoint-connection list -g {rg} -n {registry_name} --type Microsoft.ContainerRegistry/registries', checks=[
            self.check('length(@)', '2'),
        ])

        # remove endpoints
        self.cmd(
            'network private-endpoint-connection delete -g {rg} --resource-name {registry_name} -n {second_endpoint_request} --type Microsoft.ContainerRegistry/registries -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list -g {rg} -n {registry_name} --type Microsoft.ContainerRegistry/registries', checks=[
            self.check('length(@)', '1'),
        ])
        self.cmd('network private-endpoint-connection show -g {rg} --resource-name {registry_name} -n {endpoint_request} --type Microsoft.ContainerRegistry/registries', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{description_msg}'),
            self.check('name', '{endpoint_request}')
        ])

        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {registry_name} -n {endpoint_request} --type Microsoft.ContainerRegistry/registries -y')


class NetworkPrivateLinkPrivateLinkScopeScenarioTest(ScenarioTest):
    @unittest.skip('clitesthafdg4ouudnih not found in AIMON environment')
    # @record_only()  # record_only as the private-link-scope scoped-resource cannot find the components of application insights
    @ResourceGroupPreparer(location='eastus')
    def test_private_endpoint_connection_private_link_scope(self, resource_group, resource_group_location):
        self.kwargs.update({
            'rg': resource_group,
            'scope': 'clitestscopename',
            'assigned_app': 'assigned_app',
            'assigned_ws': 'assigned_ws',
            'workspace': self.create_random_name('clitest', 20),
            'app': self.create_random_name('clitest', 20),
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'loc': resource_group_location
        })

        self.cmd('monitor private-link-scope create -n {scope} -g {rg}', checks=[
            self.check('name', '{scope}')
        ])

        self.cmd('monitor private-link-scope update -n {scope} -g {rg} --tags tag1=d1', checks=[
            self.check('tags.tag1', 'd1')
        ])

        self.cmd('monitor private-link-scope show -n {scope} -g {rg}', checks=[
            self.check('tags.tag1', 'd1')
        ])
        self.cmd('monitor private-link-scope list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('monitor private-link-scope list')

        workspace_id = self.cmd('monitor log-analytics workspace create -n {workspace} -g {rg} -l {loc}').get_output_in_json()['id']
        self.kwargs.update({
            'workspace_id': workspace_id
        })

        # this command failed as service cannot find component of application insights
        self.cmd('monitor private-link-scope scoped-resource create -g {rg} -n {assigned_ws} --linked-resource {workspace_id} --scope-name {scope}', checks=[
            self.check('name', '{assigned_ws}')
        ])

        self.cmd('monitor private-link-scope scoped-resource list -g {rg} --scope-name {scope}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('network private-link-resource list --name {scope} -g {rg} --type microsoft.insights/privateLinkScopes', checks=[
            self.check('length(@)', 1)
        ])

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pr = self.cmd('monitor private-link-scope private-link-resource list --scope-name {scope} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        private_link_scope = self.cmd('monitor private-link-scope show -n {scope} -g {rg}').get_output_in_json()
        self.kwargs['scope_id'] = private_link_scope['id']
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {scope_id} '
            '--group-id {group_id}').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at monitor private-link-scope

        private_endpoint_connections = self.cmd('monitor private-link-scope show --name {scope} -g {rg}').get_output_in_json()['privateEndpointConnections']
        self.assertEqual(len(private_endpoint_connections), 1)
        self.assertEqual(private_endpoint_connections[0]['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs['scope_pec_id'] = private_endpoint_connections[0]['id']
        self.kwargs['scope_pec_name'] = private_endpoint_connections[0]['name']

        self.cmd('network private-endpoint-connection show --resource-name {scope} -g {rg} --name {scope_pec_name} --type microsoft.insights/privateLinkScopes',
                 checks=self.check('id', '{scope_pec_id}'))

        self.cmd('network private-endpoint-connection reject --resource-name {scope} -g {rg} --name {scope_pec_name} --type microsoft.insights/privateLinkScopes',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('network private-endpoint-connection list --name {scope} -g {rg} --type microsoft.insights/privateLinkScopes',
                 checks=[self.check('length(@)', 1)])

        self.cmd('network private-endpoint-connection delete --id {scope_pec_id} -y')
        self.cmd('monitor private-link-scope show --name {scope} -g {rg}', checks=[
            self.check('privateEndpointConnections', None)
        ])
        self.cmd('monitor private-link-scope scoped-resource delete -g {rg} -n {assigned_app} --scope-name {scope} -y')
        self.cmd('monitor private-link-scope scoped-resource list -g {rg} --scope-name {scope}', checks=[
            self.check('length(@)', 1)
        ])
        self.cmd('monitor private-link-scope delete -n {scope} -g {rg} -y')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('monitor private-link-scope show -n {scope} -g {rg}')


class NetworkPrivateLinkRDBMSScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mariadb')
    def test_mariadb_private_link_scenario(self, resource_group, server, database_engine):
        print(server)
        self._test_private_link_resource(resource_group, server, 'Microsoft.DBforMariaDB/servers', 'mariadbServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine, 'Microsoft.DBforMariaDB/servers')

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mysql')
    def test_mysql_private_link_scenario(self, resource_group, server, database_engine):
        self._test_private_link_resource(resource_group, server, 'Microsoft.DBforMySQL/servers', 'mysqlServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine, 'Microsoft.DBforMySQL/servers')

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='postgres')
    def test_postgres_private_link_scenario(self, resource_group, server, database_engine):
        self._test_private_link_resource(resource_group, server, 'Microsoft.DBforPostgreSQL/servers', 'postgresqlServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine, 'Microsoft.DBforPostgreSQL/servers')

    def _test_private_link_resource(self, resource_group, server, database_engine, group_id):
        result = self.cmd('network private-link-resource list -g {} --name {} --type {}'
                          .format(resource_group, server, database_engine)).get_output_in_json()
        self.assertEqual(result[0]['properties']['groupId'], group_id)

    def _test_private_endpoint_connection(self, resource_group, server, database_engine, rp_type):
        loc = 'westus'
        vnet = self.create_random_name('cli-vnet-', 24)
        subnet = self.create_random_name('cli-subnet-', 24)
        pe_name_auto = self.create_random_name('cli-pe-', 24)
        pe_name_manual_approve = self.create_random_name('cli-pe-', 24)
        pe_name_manual_reject = self.create_random_name('cli-pe-', 24)
        pe_connection_name_auto = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_approve = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_reject = self.create_random_name('cli-pec-', 24)

        # Prepare network and disable network policies
        self.cmd('network vnet create -n {} -g {} -l {} --subnet-name {}'
                 .format(vnet, resource_group, loc, subnet),
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {} --vnet-name {} -g {} '
                 '--disable-private-endpoint-network-policies true'
                 .format(subnet, vnet, resource_group),
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Get Server Id and Group Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        server_id = result['id']
        result = self.cmd('network private-link-resource list -g {} -n {} --type {}'
                          .format(resource_group, server, rp_type)).get_output_in_json()
        group_id = result[0]['properties']['groupId']

        approval_description = 'You are approved!'
        rejection_description = 'You are rejected!'
        expectedError = 'Private Endpoint Connection Status is not Pending'

        # Testing Auto-Approval workflow
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {}'
                                    .format(resource_group, pe_name_auto, vnet, subnet, loc, pe_connection_name_auto, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_auto)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], pe_connection_name_auto)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
                         'Approved')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('network private-endpoint-connection show --resource-name {} -g {} --name {} --type {}'
                 .format(server, resource_group, server_pec_name, rp_type),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(CLIError, expectedError):
            self.cmd('network private-endpoint-connection approve --resource-name {} -g {} --name {} --description "{}" --type {}'
                     .format(server, resource_group, server_pec_name, approval_description, rp_type))

        with self.assertRaisesRegex(CLIError, expectedError):
            self.cmd('network private-endpoint-connection reject --resource-name {} -g {} --name {} --description "{}" --type {}'
                     .format(server, resource_group, server_pec_name, rejection_description, rp_type))

        self.cmd('network private-endpoint-connection delete --id {} -y'
                 .format(server_pec_id))

        # Testing Manual-Approval workflow [Approval]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request'
                                    .format(resource_group, pe_name_manual_approve, vnet, subnet, loc, pe_connection_name_manual_approve, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_approve)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'], pe_connection_name_manual_approve)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
                         'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('network private-endpoint-connection show --resource-name {} -g {} --name {} --type {}'
                 .format(server, resource_group, server_pec_name, rp_type),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('properties.privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('properties.provisioningState', 'Ready')
                 ])

        self.cmd('network private-endpoint-connection approve --resource-name {} -g {} --name {} --description "{}" --type {}'
                 .format(server, resource_group, server_pec_name, approval_description, rp_type),
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', approval_description),
                     self.check('properties.provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(CLIError, expectedError):
            self.cmd('network private-endpoint-connection reject --resource-name {} -g {} --name {} --description "{}" --type {}'
                     .format(server, resource_group, server_pec_name, rejection_description, rp_type))

        self.cmd('network private-endpoint-connection delete --id {} -y'
                 .format(server_pec_id))

        # Testing Manual-Approval workflow [Rejection]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request true'
                                    .format(resource_group, pe_name_manual_reject, vnet, subnet, loc, pe_connection_name_manual_reject, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_reject)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'], pe_connection_name_manual_reject)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
                         'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('network private-endpoint-connection show --resource-name {} -g {} --name {} --type {}'
                 .format(server, resource_group, server_pec_name, rp_type),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('properties.privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('properties.provisioningState', 'Ready')
                 ])

        self.cmd('network private-endpoint-connection reject --resource-name {} -g {} --name {} --description "{}" --type {}'
                 .format(server, resource_group, server_pec_name, rejection_description, rp_type),
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', rejection_description),
                     self.check('properties.provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(CLIError, expectedError):
            self.cmd('network private-endpoint-connection approve --resource-name {} -g {} --name {} --description "{}" --type {}'
                     .format(server, resource_group, server_pec_name, approval_description, rp_type))

        self.cmd('network private-endpoint-connection list --name {} -g {} --type {}'
                 .format(server, resource_group, rp_type))

        self.cmd('network private-endpoint-connection delete --id {} -y'
                 .format(server_pec_id))


class NetworkPrivateLinkBatchAccountScenarioTest(ScenarioTest):
    def _get_test_data_file(self, filename):
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
        self.assertTrue(os.path.isfile(filepath), 'File {} does not exist.'.format(filepath))
        return filepath

class NetworkResourceManagementPrivateLinksTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_rmpl_plr')
    def test_private_link_resource_resourcemanagementprivatelink(self, resource_group):
        self.kwargs.update({
            'rmplname': self.create_random_name('cli_test_rmpl_plr-', 28),
            'loc': 'eastus',
            'rg': resource_group,
            'sub': self.get_subscription_id(),
            'body': '{\\"location\\":\\"eastus\\"}'
        })

        self.cmd('az rest --method PUT \
                 --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{rmplname}?api-version=2020-05-01" \
                 --body {body}')

        self.cmd('az network private-link-resource list --name {rmplname} --resource-group {rg} --type Microsoft.Authorization/resourceManagementPrivateLinks',
                 checks=[self.check('length(@)', 1)])

    @ResourceGroupPreparer(name_prefix='cli_test_rmpl_pe')
    def test_private_endpoint_connection_resourcemanagementprivatelink(self, resource_group):
        self.kwargs.update({
            'rmplname': self.create_random_name('cli-test-rmpl-pe-', 28),
            'loc': 'eastus',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pename': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group,
            'sub': self.get_subscription_id(),
            'body': '{\\"location\\":\\"eastus\\"}'
        })

        # prepare network
        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # create resource management private link
        rmpl = self.cmd('az rest --method "PUT" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{rmplname}?api-version=2020-05-01" \
                        --body "{body}"').get_output_in_json()
        self.kwargs['rmpl_id'] = rmpl['id']

        # Create a private endpoint connection
        result = self.cmd('az network private-endpoint create -g {rg} -n {pename} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {rmpl_id} '
                      '--group-id ResourceManagement').get_output_in_json()
        self.kwargs['pe_id'] = result['id']

        result = self.cmd('az rest --method "GET" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{rmplname}?api-version=2020-05-01"').get_output_in_json()
        self.kwargs['pe'] = result['properties']['privateEndpointConnections'][0]['name']

        # Show
        self.cmd('az network private-endpoint-connection show --resource-name {rmplname} --name {pe} --resource-group {rg} --type Microsoft.Authorization/resourceManagementPrivateLinks',
                 checks=self.check('name', '{pe}'))

        # Approve
        self.cmd('az network private-endpoint-connection approve -g {rg} --resource-name {rmplname} --name {pe} --type Microsoft.Authorization/resourceManagementPrivateLinks',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        # Reject
        self.cmd('az network private-endpoint-connection reject -g {rg} --resource-name {rmplname} --name {pe} --type Microsoft.Authorization/resourceManagementPrivateLinks',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        # Delete
        self.cmd('az network private-endpoint-connection delete -g {rg} --resource-name {rmplname} -n {pe} --type Microsoft.Authorization/resourceManagementPrivateLinks -y')

class NetworkPrivateLinkCosmosDBScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_plr')
    def test_private_link_resource_cosmosdb(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-plr-', 28),
            'loc': 'eastus'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('az network private-link-resource list --name {acc} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'Sql')])

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_pe')
    def test_private_endpoint_connection_cosmosdb(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-pe-', 28),
            'loc': 'eastus',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare cosmos db account and network
        account = self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-public-network false').get_output_in_json()
        self.kwargs['acc_id'] = account['id']
        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {acc_id} '
                      '--group-id Sql').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        results = self.kwargs['pe_id'].split('/')
        self.kwargs[
            'pec_id'] = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/privateEndpointConnections/{3}'.format(
            results[2], results[4], self.kwargs['acc'], results[-1])
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd(
            'az network private-endpoint-connection show --resource-name {acc} --name {pe_name} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts',
            checks=self.check('name', '{pe_name}'))
        self.cmd('az network private-endpoint-connection show --resource-name {acc} -n {pe_name} -g {rg} --type Microsoft.DocumentDB/databaseAccounts',
                 checks=self.check('name', '{pe_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {acc} --resource-group {rg} --name {pe_name} --type Microsoft.DocumentDB/databaseAccounts '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd('az network private-endpoint-connection list --name {acc} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts', checks=[
            self.check('length(@)', 1)
        ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')


class NetworkPrivateLinkKustoClusterScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westus')
    def test_private_link_resource_kusto_cluster(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('clikusto', 12),
            'loc': 'eastus',
            'rg': resource_group,
            'sku': 'Standard_D12_v2'
        })

        self.cmd('az kusto cluster create -l {loc} -n {acc} -g {rg} --sku {sku}')

        self.cmd('az network private-link-resource list --name {acc} --resource-group {rg} --type Microsoft.Kusto/clusters',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'cluster')])

    @ResourceGroupPreparer(name_prefix='cli_test_kusto_pe')
    def test_private_endpoint_connection_kusto_cluster(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('clikusto', 12),
            'loc': 'eastus',
            'rg': resource_group,
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'sku': 'Standard_D11_v2'
        })

        # Prepare kusto cluster and network
        account = self.cmd('az kusto cluster create -l {loc} -n {acc} -g {rg} --sku {sku}').get_output_in_json()
        self.kwargs['acc_id'] = account['id']
        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {acc_id} '
            '--group-id cluster').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        list_private_endpoint_conn = self.cmd(
            "az network private-endpoint-connection list --name {acc} --resource-group {rg} --type Microsoft.Kusto/clusters",
            checks=[self.check('length(@)', 1)]
        ).get_output_in_json()
        self.kwargs.update({"pec_id": list_private_endpoint_conn[0]["id"]})

        self.kwargs.update({"pec_name": self.kwargs["pec_id"].split("/")[-1]})
        self.cmd(
            "az network private-endpoint-connection show --id {pec_id}",
            checks=self.check("id", "{pec_id}"),
        )

        self.cmd(
            'az network private-endpoint-connection show --resource-name {acc} --name {pec_name} --resource-group {rg} --type Microsoft.Kusto/clusters',
            checks=self.check('name', '{pec_name}'))
        self.cmd(
            'az network private-endpoint-connection show --resource-name {acc} -n {pec_name} -g {rg} --type Microsoft.Kusto/clusters',
            checks=self.check('name', '{pec_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {acc} --resource-group {rg} --name {pec_name} --type Microsoft.Kusto/clusters '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd(
            'az network private-endpoint-connection list --name {acc} --resource-group {rg} --type Microsoft.Kusto/clusters',
            checks=[
                self.check('length(@)', 1)
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')


class NetworkPrivateLinkWebappScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westus')
    def test_private_link_resource_webapp(self, resource_group):
        self.kwargs.update({
            'plan_name': self.create_random_name('webapp-privatelink-asp', 40),
            'webapp_name': self.create_random_name('webapp-privatelink-webapp', 40),
            'resource_group': resource_group
        })
        self.cmd('appservice plan create -g {resource_group} -n {plan_name} --sku P1V2')
        result = self.cmd('webapp create -g {resource_group} -n {webapp_name} --plan {plan_name}').get_output_in_json()
        self.kwargs['webapp_id'] = result['id']

        self.cmd('network private-link-resource list --id {webapp_id}', checks=[
            self.check('length(@)', 1),
        ])


    @ResourceGroupPreparer(location='westus')
    def test_private_endpoint_connection_webapp(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'webapp_name': self.create_random_name('webapp-privatelink-webapp', 40),
            'plan_name': self.create_random_name('webapp-privatelink-asp', 40),
            'vnet_name': self.create_random_name('webapp-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('webapp-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('webapp-privatelink-endpoint', 40),
            'endpoint_conn_name': self.create_random_name('webapp-privatelink-endpointconn', 40),
            'second_endpoint_name': self.create_random_name('webapp-privatelink-endpoint2', 40),
            'second_endpoint_conn_name': self.create_random_name('webapp-privatelink-endpointconn2', 40),
            'description_msg': 'somedescription'
        })

        # Prepare network
        self.cmd('network vnet create -n {vnet_name} -g {resource_group} --subnet-name {subnet_name}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet_name} --vnet-name {vnet_name} -g {resource_group} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create appService
        self.cmd('appservice plan create -g {resource_group} -n {plan_name} --sku P1V2')
        webapp = self.cmd('webapp create -g {resource_group} -n {webapp_name} --plan {plan_name}').get_output_in_json()
        self.kwargs['webapp_id'] = webapp['id']

        # Create endpoint
        result = self.cmd('network private-endpoint create -g {resource_group} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
                          '--connection-name {endpoint_conn_name} --private-connection-resource-id {webapp_id} '
                          '--group-id sites --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd('network private-endpoint-connection list -g {resource_group} -n {webapp_name} --type Microsoft.Web/sites', checks=[
            self.check('length(@)', 1),
        ]).get_output_in_json()
        self.kwargs['endpoint_request'] = result[0]['name']

        self.cmd('network private-endpoint-connection approve -g {resource_group} --resource-name {webapp_name} -n {endpoint_request} --type Microsoft.Web/sites',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        # Create second endpoint
        result = self.cmd('network private-endpoint create -g {resource_group} -n {second_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
                          '--connection-name {second_endpoint_conn_name} --private-connection-resource-id {webapp_id} '
                          '--group-id sites --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['second_endpoint_name'].lower() in result['name'].lower())

        result = self.cmd('network private-endpoint-connection list -g {resource_group} -n {webapp_name} --type Microsoft.Web/sites', checks=[
            self.check('length(@)', 2),
        ]).get_output_in_json()
        self.kwargs['second_endpoint_request'] = [conn['name'] for conn in result if
                                                  self.kwargs['second_endpoint_name'].lower() in
                                                  conn['properties']['privateEndpoint']['id'].lower()][0]

        self.cmd('network private-endpoint-connection reject -g {resource_group} --resource-name {webapp_name} -n {second_endpoint_request} --type Microsoft.Web/sites',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejecting')])

        # Remove endpoints
        self.cmd('network private-endpoint-connection delete -g {resource_group} --resource-name {webapp_name} -n {second_endpoint_request} --type Microsoft.Web/sites -y')
        self.cmd('network private-endpoint-connection show -g {resource_group} --resource-name {webapp_name} -n {second_endpoint_request} --type Microsoft.Web/sites', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Disconnecting'),
            self.check('name', '{second_endpoint_request}')
        ])
        self.cmd('network private-endpoint-connection show -g {resource_group} --resource-name {webapp_name} -n {endpoint_request} --type Microsoft.Web/sites', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('name', '{endpoint_request}')
        ])

        self.cmd('network private-endpoint-connection delete -g {resource_group} --resource-name {webapp_name} -n {endpoint_request} --type Microsoft.Web/sites -y')


class NetworkPrivateLinkApiManagementScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_api_management_private_endpoint_', location="westus2")
    def test_private_endpoint_connection_apim(self, resource_group, resource_group_location):
        self.kwargs.update({
            'resource_group': resource_group,
            'service_name': self.create_random_name('apim-privatelink-service', 40),
            'vnet_name': self.create_random_name('apim-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('apim-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('apim-privatelink-endpoint', 40),
            'endpoint_conn_name': self.create_random_name('apim-privatelink-endpointconn', 40),
            'endpoint_name2': self.create_random_name('apim-privatelink-endpoint2', 40),
            'endpoint_conn_name2': self.create_random_name('apim-privatelink-endpointconn2', 40),
            'description_msg': 'somedescription',
            'location': resource_group_location,
        })

        # Create ApiManagement Service
        service_created = self.cmd(
            'apim create -g {resource_group} -n {service_name} --l {location} --publisher-email email@mydomain.com --publisher-name Microsoft').get_output_in_json()
        self.kwargs['service_id'] = service_created['id']

        # check private link resource is available
        self.cmd('network private-link-resource list --id {service_id}', checks=[
            self.check('length(@)', 1),
        ])

        # Prepare network
        self.cmd('network vnet create -n {vnet_name} -g {resource_group} --subnet-name {subnet_name}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet_name} --vnet-name {vnet_name} -g {resource_group} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        result = self.cmd(
            'network vnet subnet show -n {subnet_name} --vnet-name {vnet_name} -g {resource_group} ').get_output_in_json()

        # Create endpoint with auto approval
        result = self.cmd(
            'network private-endpoint create -g {resource_group} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--connection-name {endpoint_conn_name} --private-connection-resource-id {service_id} '
            '--group-id Gateway').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd(
            'network private-endpoint-connection list -g {resource_group} -n {service_name} --type Microsoft.ApiManagement/service',
            checks=[self.check('length(@)', 1), ]).get_output_in_json()
        self.kwargs['endpoint_request'] = result[0]['name']

        result = self.cmd(
            'network private-endpoint-connection reject -g {resource_group} --resource-name {service_name} -n {endpoint_request} --type Microsoft.ApiManagement/service',
            checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        # Create second endpoint with manual approval
        result = self.cmd(
            'network private-endpoint create -g {resource_group} -n {endpoint_name2} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--connection-name {endpoint_conn_name2} --private-connection-resource-id {service_id} '
            '--group-id Gateway --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name2'].lower() in result['name'].lower())

        result = self.cmd(
            'network private-endpoint-connection list -g {resource_group} -n {service_name} --type Microsoft.ApiManagement/service',
            checks=[self.check('length(@)', 2), ]).get_output_in_json()
        self.kwargs['endpoint_request2'] = [conn['name'] for conn in result if
                                            self.kwargs['endpoint_name2'].lower() in
                                            conn['properties']['privateEndpoint']['id'].lower()][0]

        self.cmd(
            'network private-endpoint-connection approve -g {resource_group} --resource-name {service_name} -n {endpoint_request2} --type Microsoft.ApiManagement/service',
            checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        self.cmd(
            'network private-endpoint-connection reject -g {resource_group} --resource-name {service_name} -n {endpoint_request2} --type Microsoft.ApiManagement/service',
            checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('network private-endpoint-connection show -g {resource_group} --resource-name {service_name} -n {endpoint_request2} --type Microsoft.ApiManagement/service', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('name', '{endpoint_request2}')
        ])

        # Remove endpoint
        self.cmd(
            'network private-endpoint-connection delete -g {resource_group} --resource-name {service_name} -n {endpoint_request} --type Microsoft.ApiManagement/service -y')


class NetworkPrivateLinkEventGridScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_plr')
    def test_private_link_resource_event_grid(self, resource_group):
        self.kwargs.update({
            'topic_name': self.create_random_name(prefix='cli', length=40),
            'domain_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'rg': resource_group
        })

        scope_id = self.cmd(
            'eventgrid topic create --name {topic_name} --resource-group {rg} --location {location} --public-network-access disabled',
            checks=[
                self.check('type', 'Microsoft.EventGrid/topics'),
                self.check('name', self.kwargs['topic_name']),
                self.check('provisioningState', 'Succeeded'),
                self.check('sku', {'name': 'Basic'}),
                self.check('publicNetworkAccess', 'Disabled'),
                self.check('identity.principalId', None),
                self.check('identity.tenantId', None),
                self.check('identity.type', None),
                self.check('identity.userAssignedIdentities', None)
            ]).get_output_in_json()['id']
        self.kwargs.update({
            'scope_id': scope_id
        })

        self.cmd(
            'network private-link-resource list --id {scope_id}',
            checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'topic')])

        domain_id = self.cmd('az eventgrid domain create --name {domain_name} --resource-group {rg} --location {location} --public-network-access disabled',).get_output_in_json()['id']
        self.kwargs.update({
            'domain_id': domain_id
        })

        self.cmd(
            'network private-link-resource list --id {domain_id}',
            checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'domain')])

    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', location='centraluseuap')
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', parameter_name='resource_group_2', location='centraluseuap')
    def test_private_endpoint_connection_event_grid_topic(self, resource_group, resource_group_2):
        self.kwargs.update({
            'resource_group_net': resource_group_2,
            'vnet_name': self.create_random_name(prefix='cli', length=20),
            'subnet_name': self.create_random_name(prefix='cli', length=20),
            'private_endpoint_name': self.create_random_name(prefix='cli', length=20),
            'connection_name': self.create_random_name(prefix='cli', length=20),
            'topic_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'approval_description': 'You are approved!',
            'rejection_description': 'You are rejected!',
            'rg': resource_group
        })

        self.cmd('network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        scope = self.cmd('eventgrid topic create --name {topic_name} --resource-group {rg} --location {location} --public-network-access disabled', checks=[
            self.check('type', 'Microsoft.EventGrid/topics'),
            self.check('name', self.kwargs['topic_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'}),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
            self.check('identity.type', None),
            self.check('identity.userAssignedIdentities', None)
        ]).get_output_in_json()['id']

        self.kwargs.update({
            'scope': scope,
        })

        # Create private endpoint
        self.cmd('network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids topic --connection-name {connection_name}')

        server_pec_id = self.cmd('eventgrid topic show --name {topic_name} --resource-group {rg}').get_output_in_json()['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('network private-endpoint-connection list --resource-group {rg} --name {topic_name} --type Microsoft.EventGrid/topics',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('network private-endpoint-connection show --resource-group {rg} --resource-name {topic_name} --name {server_pec_name} --type Microsoft.EventGrid/topics')

        self.cmd('network private-endpoint-connection approve --resource-group {rg} --resource-name {topic_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/topics --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])
        self.cmd('network private-endpoint-connection reject --resource-group {rg} --resource-name {topic_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/topics --description "{rejection_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_description}')
                 ])

        self.cmd('network private-endpoint-connection delete --resource-group {rg} --resource-name {topic_name} --name {server_pec_name} --type Microsoft.EventGrid/topics -y')

        self.cmd('network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('eventgrid topic delete --name {topic_name} --resource-group {rg}')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', location='centraluseuap')
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', parameter_name='resource_group_2', location='centraluseuap')
    def test_private_endpoint_connection_event_grid_domain(self, resource_group, resource_group_2):
        self.kwargs.update({
            'resource_group_net': resource_group_2,
            'vnet_name': self.create_random_name(prefix='cli', length=20),
            'subnet_name': self.create_random_name(prefix='cli', length=20),
            'private_endpoint_name': self.create_random_name(prefix='cli', length=20),
            'connection_name': self.create_random_name(prefix='cli', length=20),
            'domain_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'approval_description': 'You are approved!',
            'rejection_description': 'You are rejected!',
            'rg': resource_group
        })

        self.cmd('network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        scope = self.cmd('eventgrid domain create --name {domain_name} --resource-group {rg} --location {location} --public-network-access disabled', checks=[
            self.check('type', 'Microsoft.EventGrid/domains'),
            self.check('name', self.kwargs['domain_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku', {'name': 'Basic'}),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('identity.principalId', None),
            self.check('identity.tenantId', None),
            self.check('identity.type', None),
            self.check('identity.userAssignedIdentities', None)
        ]).get_output_in_json()['id']

        self.kwargs.update({
            'scope': scope,
        })

        # Create private endpoint
        self.cmd('network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids domain --connection-name {connection_name}')

        server_pec_id = self.cmd('eventgrid domain show --name {domain_name} --resource-group {rg}').get_output_in_json()['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('network private-endpoint-connection list --resource-group {rg} --name {domain_name} --type Microsoft.EventGrid/domains',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('network private-endpoint-connection show --resource-group {rg} --resource-name {domain_name} --name {server_pec_name} --type Microsoft.EventGrid/domains')

        self.cmd('network private-endpoint-connection approve --resource-group {rg} --resource-name {domain_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/domains --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])
        self.cmd('network private-endpoint-connection reject --resource-group {rg} --resource-name {domain_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/domains --description "{rejection_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_description}')
                 ])

        self.cmd('network private-endpoint-connection delete --resource-group {rg} --resource-name {domain_name} --name {server_pec_name} --type Microsoft.EventGrid/domains -y')

        self.cmd('network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('eventgrid domain delete --name {domain_name} --resource-group {rg}')


class NetworkPrivateLinkAppGwScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_appgw_private_endpoint_with_default')
    def test_appgw_private_endpoint_with_default(self, resource_group):
        self.kwargs.update({
            'appgw': 'appgw',
            'appgw_pe_vnet': 'appgw_private_endpoint_vnet',
            'appgw_pe_subnet': 'appgw_private_endpoint_subnet',
            'appgw_ip': 'appgw_ip',
            'appgw_pe': 'appgw_private_endpoint',
            'appgw_pec': 'appgw_private_endpoint_connection'
        })

        # Enable private link feature on Application Gateway would require a public IP with Standard tier
        self.cmd('network public-ip create -g {rg} -n {appgw_ip} --sku Standard')

        # Prepare the vnet to be connected to
        self.cmd('network vnet create -g {rg} -n {appgw_pe_vnet} --subnet-name {appgw_pe_subnet}')
        # Enable private endpoint on a vnet would require --disable-private-endpoint-network-policies=true
        self.cmd('network vnet subnet update -g {rg} -n {appgw_pe_subnet} '
                 '--vnet-name {appgw_pe_vnet} '
                 '--disable-private-endpoint-network-policies true')

        # Enable private link feature on Application Gateway would require Standard_v2,WAF_v2 SKU tiers
        # --enable-private-link would enable private link feature with default settings
        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--sku Standard_v2 '
                 '--public-ip-address {appgw_ip} '
                 '--enable-private-link')

        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()

        self.assertEqual(show_appgw_data['name'], self.kwargs['appgw'])
        self.assertEqual(show_appgw_data['sku']['tier'], 'Standard_v2')
        # One default private link would be here
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations']), 1)
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations']), 1)
        # The frontendIpConfigurations must be assocciated with the same ID of private link configuration ID
        self.assertEqual(show_appgw_data['frontendIpConfigurations'][0]['privateLinkConfiguration']['id'],
                         show_appgw_data['privateLinkConfigurations'][0]['id'])
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['name'], 'PrivateLinkDefaultConfiguration')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['privateIpAllocationMethod'],
                         'Dynamic')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['primary'], None)

        appgw_vnet = self.cmd('network vnet show -g {rg} -n "{appgw}Vnet"').get_output_in_json()
        self.assertEqual(len(appgw_vnet['subnets']), 2)
        self.assertEqual(appgw_vnet['subnets'][0]['name'], 'default')
        self.assertEqual(appgw_vnet['subnets'][0]['addressPrefix'], '10.0.0.0/24')
        # The subnet name and CIDR is default one
        self.assertEqual(appgw_vnet['subnets'][1]['name'], 'PrivateLinkDefaultSubnet')
        self.assertEqual(appgw_vnet['subnets'][1]['addressPrefix'], '10.0.1.0/24')

        self.kwargs.update({
            'appgw_id': show_appgw_data['id']
        })

        private_link_resource = self.cmd('network private-link-resource list --id {appgw_id}').get_output_in_json()
        self.assertEqual(len(private_link_resource), 1)
        self.assertEqual(private_link_resource[0]['name'], 'appGatewayFrontendIP')

        self.kwargs.update({
            'private_link_group_id': private_link_resource[0]['properties']['groupId']
        })

        # Create a private endpoint against this application gateway
        self.cmd('network private-endpoint create -g {rg} -n {appgw_pe} '
                 '--connection-name {appgw_pec} '
                 '--vnet-name {appgw_pe_vnet} '
                 '--subnet {appgw_pe_subnet} '
                 '--private-connection-resource-id {appgw_id} '
                 '--group-id {private_link_group_id}')

        list_private_endpoint_conn = self.cmd('network private-endpoint-connection list --id {appgw_id} ').get_output_in_json()
        self.assertEqual(len(list_private_endpoint_conn), 1)
        self.assertEqual(list_private_endpoint_conn[0]['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs.update({
            'private_endpoint_conn_id': list_private_endpoint_conn[0]['id']
        })

        self.cmd('network private-endpoint-connection reject --id {private_endpoint_conn_id}').get_output_in_json()

        show_private_endpoint_conn = self.cmd('network private-endpoint-connection show --id {private_endpoint_conn_id}').get_output_in_json()
        self.assertEqual(show_private_endpoint_conn['properties']['privateLinkServiceConnectionState']['status'], 'Rejected')

        self.cmd('network private-endpoint delete -g {rg} -n {appgw_pe}')

    @ResourceGroupPreparer(name_prefix='test_appgw_private_endpoint_with_overwrite_default')
    def test_appgw_private_endpoint_with_overwrite_default(self, resource_group):
        self.kwargs.update({
            'appgw': 'appgw',
            'appgw_pe_vnet': 'appgw_private_endpoint_vnet',
            'appgw_pe_subnet': 'appgw_private_endpoint_subnet',
            'appgw_ip': 'appgw_ip',
            'appgw_pe': 'appgw_private_endpoint',
            'appgw_pec': 'appgw_private_endpoint_connection'
        })

        # Enable private link feature on Application Gateway would require a public IP with Standard tier
        self.cmd('network public-ip create -g {rg} -n {appgw_ip} --sku Standard')

        # Prepare the vnet to be connected to
        self.cmd('network vnet create -g {rg} -n {appgw_pe_vnet} --subnet-name {appgw_pe_subnet}')
        # Enable private endpoint on a vnet would require --disable-private-endpoint-network-policies=true
        self.cmd('network vnet subnet update -g {rg} -n {appgw_pe_subnet} '
                 '--vnet-name {appgw_pe_vnet} '
                 '--disable-private-endpoint-network-policies true')

        # Enable private link feature on Application Gateway would require Standard_v2,WAF_v2 SKU tiers
        # --enable-private-link would enable private link feature with default settings
        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--sku Standard_v2 '
                 '--public-ip-address {appgw_ip} '
                 '--enable-private-link '
                 '--private-link-subnet YetAnotherSubnetName '
                 '--private-link-primary true '
                 '--private-link-subnet-prefix 10.0.2.0/24')

        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()

        self.assertEqual(show_appgw_data['name'], self.kwargs['appgw'])
        self.assertEqual(show_appgw_data['sku']['tier'], 'Standard_v2')
        # One default private link would be here
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations']), 1)
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations']), 1)
        # The frontendIpConfigurations must be assocciated with the same ID of private link configuration ID
        self.assertEqual(show_appgw_data['frontendIpConfigurations'][0]['privateLinkConfiguration']['id'],
                         show_appgw_data['privateLinkConfigurations'][0]['id'])
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['name'], 'PrivateLinkDefaultConfiguration')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['privateIpAllocationMethod'],
                         'Dynamic')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['primary'], True)

        # The vnet created along with this application gateway
        appgw_vnet = self.cmd('network vnet show -g {rg} -n "{appgw}Vnet"').get_output_in_json()
        self.assertEqual(len(appgw_vnet['subnets']), 2)
        self.assertEqual(appgw_vnet['subnets'][0]['name'], 'default')
        self.assertEqual(appgw_vnet['subnets'][0]['addressPrefix'], '10.0.0.0/24')
        # The subnet name and CIDR is different from default one
        self.assertEqual(appgw_vnet['subnets'][1]['name'], 'YetAnotherSubnetName')
        self.assertEqual(appgw_vnet['subnets'][1]['addressPrefix'], '10.0.2.0/24')

        self.kwargs.update({
            'appgw_id': show_appgw_data['id']
        })

        private_link_resource = self.cmd('network private-link-resource list --id {appgw_id}').get_output_in_json()
        self.assertEqual(len(private_link_resource), 1)
        self.assertEqual(private_link_resource[0]['name'], 'appGatewayFrontendIP')

        self.kwargs.update({
            'private_link_group_id': private_link_resource[0]['properties']['groupId']
        })

        # Create a private endpoint against this application gateway
        self.cmd('network private-endpoint create -g {rg} -n {appgw_pe} '
                 '--connection-name {appgw_pec} '
                 '--vnet-name {appgw_pe_vnet} '
                 '--subnet {appgw_pe_subnet} '
                 '--private-connection-resource-id {appgw_id} '
                 '--group-id {private_link_group_id}')

        list_private_endpoint_conn = self.cmd('network private-endpoint-connection list --id {appgw_id} ').get_output_in_json()
        self.assertEqual(len(list_private_endpoint_conn), 1)
        self.assertEqual(list_private_endpoint_conn[0]['properties']['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs.update({
            'private_endpoint_conn_id': list_private_endpoint_conn[0]['id']
        })

        self.cmd('network private-endpoint-connection reject --id {private_endpoint_conn_id}').get_output_in_json()

        show_private_endpoint_conn = self.cmd('network private-endpoint-connection show --id {private_endpoint_conn_id}').get_output_in_json()
        self.assertEqual(show_private_endpoint_conn['properties']['privateLinkServiceConnectionState']['status'], 'Rejected')

        self.cmd('network private-endpoint delete -g {rg} -n {appgw_pe}')

    @live_only()
    @ResourceGroupPreparer(name_prefix='test_manage_appgw_private_endpoint')
    def test_manage_appgw_private_endpoint(self, resource_group):
        """
        Add/Remove/Show/List Private Link
        """
        self.kwargs.update({
            'appgw': 'appgw',
            'appgw_private_link_for_public': 'appgw_private_link_for_public',
            'appgw_private_link_for_private': 'appgw_private_link_for_private',
            'appgw_private_link_subnet_for_public': 'appgw_private_link_subnet_for_public',
            'appgw_private_link_subnet_for_private': 'appgw_private_link_subnet_for_private',
            'appgw_public_ip': 'public_ip',
            'appgw_private_ip': 'private_ip',
            'appgw_private_endpoint_for_public': 'appgw_private_endpoint_for_public',
            'appgw_private_endpoint_for_private': 'appgw_private_endpoint_for_private',
            'appgw_private_endpoint_vnet': 'appgw_private_endpoint_vnet',
            'appgw_private_endpoint_subnet_for_public': 'appgw_private_endpoint_subnet_for_public',
            'appgw_private_endpoint_subnet_for_private': 'appgw_private_endpoint_subnet_for_private',
            'appgw_private_endpoint_connection_for_public': 'appgw_private_endpoint_connection_for_public',
            'appgw_private_endpoint_connection_for_private': 'appgw_private_endpoint_connection_for_private'
        })

        # Enable private link feature on Application Gateway would require a public IP with Standard tier
        self.cmd('network public-ip create -g {rg} -n {appgw_public_ip} --sku Standard')

        # Create a application gateway without enable --enable-private-link
        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--sku Standard_v2 '
                 '--public-ip-address {appgw_public_ip}')

        # Add one private link
        self.cmd('network application-gateway private-link add -g {rg} '
                 '--gateway-name {appgw} '
                 '--name {appgw_private_link_for_public} '
                 '--frontend-ip appGatewayFrontendIP '
                 '--subnet {appgw_private_link_subnet_for_public} '
                 '--subnet-prefix 10.0.4.0/24')
        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()
        self.kwargs.update({
            'appgw_id': show_appgw_data['id']
        })

        self.cmd('network application-gateway private-link show -g {rg} --gateway-name {appgw} '
                 '--name {appgw_private_link_for_public}')

        self.cmd('network application-gateway private-link list -g {rg} --gateway-name {appgw} ')

        private_link_resource = self.cmd('network private-link-resource list --id {appgw_id}').get_output_in_json()
        self.assertEqual(len(private_link_resource), 1)
        self.assertEqual(private_link_resource[0]['name'], 'appGatewayFrontendIP')

        self.kwargs.update({
            'private_link_group_id_for_public': private_link_resource[0]['properties']['groupId']
        })

        # Prepare the first vnet to be connected to
        self.cmd('network vnet create -g {rg} '
                 '--name {appgw_private_endpoint_vnet} '
                 '--subnet-name {appgw_private_endpoint_subnet_for_public}')
        # Enable private endpoint on a vnet would require --disable-private-endpoint-network-policies=true
        self.cmd('network vnet subnet update -g {rg} '
                 '--vnet-name {appgw_private_endpoint_vnet} '
                 '--name {appgw_private_endpoint_subnet_for_public} '
                 '--disable-private-endpoint-network-policies true')
        # Create the first private endpoint against this application gateway's public IP
        self.cmd('network private-endpoint create -g {rg} '
                 '--name {appgw_private_endpoint_for_public} '
                 '--connection-name {appgw_private_endpoint_connection_for_public} '
                 '--vnet-name {appgw_private_endpoint_vnet} '
                 '--subnet {appgw_private_endpoint_subnet_for_public} '
                 '--private-connection-resource-id {appgw_id} '
                 '--group-id {private_link_group_id_for_public}')

        # ------------------------------------------------------------------------------------------

        # Add another frontend IP
        self.cmd('network application-gateway frontend-ip create -g {rg} '
                 '--gateway-name {appgw} '
                 '--name {appgw_private_ip} '
                 '--vnet-name "{appgw}Vnet" '
                 '--subnet default '
                 '--private-ip-address 10.0.0.11')

        # Add another private link
        self.cmd('network application-gateway private-link add -g {rg} '
                 '--gateway-name {appgw} '
                 '--name {appgw_private_link_for_private} '
                 '--frontend-ip {appgw_private_ip} '
                 '--subnet {appgw_private_link_subnet_for_private} '
                 '--subnet-prefix 10.0.5.0/24')
        self.cmd('network application-gateway private-link show -g {rg} --gateway-name {appgw} '
                 '--name {appgw_private_link_for_private}')
        self.cmd('network application-gateway private-link list -g {rg} --gateway-name {appgw} ')

        self.cmd('network application-gateway frontend-port create -g {rg} '
                 '--gateway {appgw} '
                 '--name privatePort '
                 '--port 8080 ')
        # The another http listener for private IP is necessary to setup an private link properly
        self.cmd('network application-gateway http-listener create -g {rg} '
                 '--gateway-name {appgw} '
                 '--name privateHTTPListener '
                 '--frontend-port privatePort '
                 '--frontend-ip {appgw_private_ip} ')
        # Associate a rule for private http listener
        self.cmd('network application-gateway rule create -g {rg} '
                 '--gateway {appgw} '
                 '--name privateRule '
                 '--http-listener privateHTTPListener')

        private_link_resource = self.cmd('network private-link-resource list --id {appgw_id}').get_output_in_json()
        self.assertEqual(len(private_link_resource), 2)
        self.assertEqual(private_link_resource[1]['name'], self.kwargs['appgw_private_ip'])

        self.kwargs.update({
            'private_link_group_id_for_private': private_link_resource[1]['properties']['groupId']
        })

        # Prepare the second vnet to be connected to
        self.cmd('network vnet subnet create -g {rg} '
                 '--vnet-name {appgw_private_endpoint_vnet} '
                 '--name {appgw_private_endpoint_subnet_for_private} '
                 '--address-prefixes 10.0.6.0/24')
        # Enable private endpoint on a vnet would require --disable-private-endpoint-network-policies=true
        self.cmd('network vnet subnet update -g {rg} '
                 '--vnet-name {appgw_private_endpoint_vnet} '
                 '--name {appgw_private_endpoint_subnet_for_private} '
                 '--disable-private-endpoint-network-policies true')
        # Create the second private endpoint against this application gateway's private IP
        self.cmd('network private-endpoint create -g {rg} '
                 '--name {appgw_private_endpoint_for_private} '
                 '--connection-name {appgw_private_endpoint_connection_for_private} '
                 '--vnet-name {appgw_private_endpoint_vnet} '
                 '--subnet {appgw_private_endpoint_subnet_for_private} '
                 '--private-connection-resource-id {appgw_id} '
                 '--group-id {private_link_group_id_for_private}')

        # Could not remove unless remove all private endpoint connections
        # self.cmd('network application-gateway private-link remove -g {rg} '
        #          '--gateway-name {appgw} '
        #          '--name {appgw_private_link_for_public} '
        #          '--yes')

        # self.cmd('network application-gateway private-link remove -g {rg} '
        #          '--gateway-name {appgw} '
        #          '--name {appgw_private_link_for_private} '
        #          '--yes')

        self.cmd('network application-gateway private-link list -g {rg} --gateway-name {appgw} ')

    @ResourceGroupPreparer(name_prefix='test_manage_appgw_private_endpoint_without_standard')
    def test_manage_appgw_private_endpoint_without_standard(self, resource_group):
        """
        Add Private Link without standard
        """
        self.kwargs.update({
            'appgw': 'appgw',
            'appgw_private_link_for_public': 'appgw_private_link_for_public',
            'appgw_private_link_subnet_for_public': 'appgw_private_link_subnet_for_public',
            'appgw_public_ip': 'public_ip',
        })

        # Enable private link feature on Application Gateway would require a public IP without Standard tier
        self.cmd('network public-ip create -g {rg} -n {appgw_public_ip}')

        # Create a application gateway without enable --enable-private-link
        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--public-ip-address {appgw_public_ip}')

        # Add one private link
        # These will fail because application-gateway feature cannot be enabled for selected sku
        with self.assertRaises(HttpResponseError):
            self.cmd('network application-gateway private-link add -g {rg} '
                     '--gateway-name {appgw} '
                     '--name {appgw_private_link_for_public} '
                     '--frontend-ip appGatewayFrontendIP '
                     '--subnet {appgw_private_link_subnet_for_public} '
                     '--subnet-prefix 10.0.4.0/24'
                     '--no-wait')


class NetworkPrivateLinkDiskAccessScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_disk_access_private_endpoint_')
    def test_disk_access_private_endpoint(self, resource_group):
        self.kwargs.update({
            'loc': 'centraluseuap',
            'disk_access': 'disk_access_name',
            'pe_vnet': 'private_endpoint_vnet',
            'pe_subnet': 'private_endpoint_subnet',
            'pe_name': 'private_endpoint_name',
            'pe_connection': 'private_connection_name'
        })

        # Create disk access for private endpoint
        disk_access_output = self.cmd('disk-access create -g {rg} -l {loc} -n {disk_access}').get_output_in_json()
        self.kwargs.update({
            'disk_access_id': disk_access_output['id']
        })

        # Check private link resource
        self.cmd('network private-link-resource list -g {rg} -n {disk_access} --type Microsoft.Compute/diskAccesses',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('@[0].name', 'disks')
                 ])

        # Prepare the vnet to be connected to
        self.cmd('network vnet create -g {rg} -n {pe_vnet} --subnet-name {pe_subnet}')
        # Enable private endpoint on a vnet would require --disable-private-endpoint-network-policies=true
        self.cmd('network vnet subnet update -g {rg} -n {pe_subnet} '
                 '--vnet-name {pe_vnet} '
                 '--disable-private-endpoint-network-policies true')

        # Create a private endpoint connection for the disk access object
        pe_output = self.cmd('network private-endpoint create -g {rg} -n {pe_name} --vnet-name {pe_vnet} '
                             '--subnet {pe_subnet} --private-connection-resource-id {disk_access_id} '
                             '--group-ids disks --connection-name {pe_connection}').get_output_in_json()
        self.kwargs.update({
            'pe_id': pe_output['id']
        })

        # Check the auto-approve of the private endpoint connection
        self.cmd('network private-endpoint-connection list -g {rg} -n {disk_access} --type Microsoft.Compute/diskAccesses',
                 checks=[
                     self.check('length(@)', 1),
                     self.check('@[0].properties.privateEndpoint.id', '{pe_id}'),
                     self.check('@[0].properties.privateLinkServiceConnectionState.status', 'Approved')
                 ])


class NetworkARMTemplateBasedScenarioTest(ScenarioTest):
    def _test_private_endpoint_connection_scenario(self, resource_group, target_resource_name, resource_type):
        from azure.mgmt.core.tools import resource_id
        self.kwargs.update({
            'target_resource_name': target_resource_name,
            'target_resource_id': resource_id(subscription=self.get_subscription_id(),
                                              resource_group=resource_group,
                                              namespace=resource_type.split('/')[0],
                                              type=resource_type.split('/')[1],
                                              name=target_resource_name),
            'rg': resource_group,
            'resource_type': resource_type,
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        param_file_name = "{}_{}_parameters.json".format(resource_type.split('/')[0].split('.')[1].lower(), resource_type.split('/')[1].lower())
        template_file_name = "{}_{}_template.json".format(resource_type.split('/')[0].split('.')[1].lower(), resource_type.split('/')[1].lower())
        self.kwargs.update({
            'param_path': os.path.join(TEST_DIR, 'private_endpoint_arm_templates', param_file_name),
            'template_path': os.path.join(TEST_DIR, 'private_endpoint_arm_templates', template_file_name)
        })
        self.cmd('az deployment group create -g {rg} -p "@{param_path}" target_resource_name={target_resource_name} -f "{template_path}"')

        self.cmd('az network vnet create -n {vnet} -g {rg} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        target_private_link_resource = self.cmd('az network private-link-resource list --name {target_resource_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            'group_id': target_private_link_resource[0]['properties']['groupId']
        })
        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} '
            '--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} '
            '--group-id {group_id}').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        list_private_endpoint_conn = self.cmd('az network private-endpoint-connection list --name {target_resource_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })

        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('az network private-endpoint-connection show --resource-name {target_resource_name} --name {pec_name} --resource-group {rg} --type {resource_type}')
        self.cmd('az network private-endpoint-connection show --resource-name {target_resource_name} -n {pec_name} -g {rg} --type {resource_type}')

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {target_resource_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd(
            'az network private-endpoint-connection list --name {target_resource_name} --resource-group {rg} --type {resource_type}',
            checks=[
                self.check('length(@)', 1)
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')

    @ResourceGroupPreparer(location='westus2')
    def test_private_endpoint_connection_app_configuration(self, resource_group):
        self._test_private_endpoint_connection_scenario(resource_group, 'clitestappconfig', 'Microsoft.AppConfiguration/configurationStores')


class NetworkPrivateLinkDigitalTwinsScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(
        name_prefix="test_digital_twin_private_endpoint_", location="eastus"
    )
    def test_private_endpoint_connection_digitaltwins(
        self, resource_group, resource_group_location
    ):
        from azure.mgmt.core.tools import resource_id

        resource_name = self.create_random_name("cli-test-dt-", 24)
        templateFile = os.path.join(
            TEST_DIR,
            "private_endpoint_arm_templates",
            "digitaltwins_resource_template.json",
        )
        namespace = "Microsoft.DigitalTwins"
        instance_type = "digitalTwinsInstances"
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=instance_type,
            name=resource_name,
        )
        self.kwargs.update(
            {
                "deployment_name": self.create_random_name("cli-test-dt-plr-", 24),
                "dt_rg": resource_group,
                "dt_name": resource_name,
                "dt_loc": resource_group_location,
                "dt_template": templateFile,
                "vnet": self.create_random_name("cli-vnet-", 24),
                "subnet": self.create_random_name("cli-subnet-", 24),
                "pe": self.create_random_name("cli-pe-", 24),
                "pe_connection": self.create_random_name("cli-pec-", 24),
                "target_resource_id": target_resource_id,
                "dt_type": "{}/{}".format(namespace, instance_type),
            }
        )

        # Create DT resource
        self.cmd(
            'az deployment group create --name {deployment_name} -g {dt_rg} --template-file "{dt_template}" --parameters name={dt_name} --parameters location={dt_loc}'
        )

        # List private link resources
        target_private_link_resource = self.cmd(
            "az network private-link-resource list --name {dt_name} --resource-group {dt_rg} --type {dt_type}",
            checks=self.check("@[0].properties.groupId", "API"),
        ).get_output_in_json()
        self.kwargs.update(
            {"group_id": target_private_link_resource[0]["properties"]["groupId"]}
        )

        # Create VNET
        self.cmd(
            "az network vnet create -n {vnet} -g {dt_rg} --subnet-name {subnet}",
            checks=self.check("length(newVNet.subnets)", 1),
        )
        self.cmd(
            "az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {dt_rg} "
            "--disable-private-endpoint-network-policies true",
            checks=self.check("privateEndpointNetworkPolicies", "Disabled"),
        )

        # Create a private endpoint connection (force manual approval)
        pe = self.cmd(
            "az network private-endpoint create -g {dt_rg} -n {pe} --vnet-name {vnet} --subnet {subnet} "
            "--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} "
            "--group-id {group_id} --manual-request"
        ).get_output_in_json()
        self.kwargs["pe_id"] = pe["id"]
        self.kwargs["pe_name"] = self.kwargs["pe_id"].split("/")[-1]

        # Show the connection on DT instance
        list_private_endpoint_conn = self.cmd(
            "az network private-endpoint-connection list --name {dt_name} --resource-group {dt_rg} --type {dt_type}"
        ).get_output_in_json()
        self.kwargs.update({"pec_id": list_private_endpoint_conn[0]["id"]})

        self.kwargs.update({"pec_name": self.kwargs["pec_id"].split("/")[-1]})
        self.cmd(
            "az network private-endpoint-connection show --id {pec_id}",
            checks=self.check("id", "{pec_id}"),
        )
        self.cmd(
            "az network private-endpoint-connection show --resource-name {dt_name} --name {pec_name} --resource-group {dt_rg} --type {dt_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Test approval states
        # Approved
        self.kwargs.update(
            {"approval_desc": "Approved.", "rejection_desc": "Rejected."}
        )
        self.cmd(
            "az network private-endpoint-connection approve --resource-name {dt_name} --resource-group {dt_rg} --name {pec_name} --type {dt_type} "
            '--description "{approval_desc}"',
            checks=[
                self.check(
                    "properties.privateLinkServiceConnectionState.status", "Approved"
                )
            ],
        )

        # Rejected
        self.cmd(
            "az network private-endpoint-connection reject --id {pec_id} "
            '--description "{rejection_desc}"',
            checks=[
                self.check(
                    "properties.privateLinkServiceConnectionState.status", "Rejected"
                )
            ],
        )

        # Approval will fail after rejection
        with self.assertRaises(CLIError):
            self.cmd(
                "az network private-endpoint-connection approve --resource-name {dt_name} --resource-group {dt_rg} --name {pec_name} --type {dt_type} "
                '--description "{approval_desc}"'
            )

        self.cmd(
            "az network private-endpoint-connection list --name {dt_name} --resource-group {dt_rg} --type {dt_type}",
            checks=[self.check("length(@)", 1)],
        )

        # Test delete
        self.cmd("az network private-endpoint-connection delete --id {pec_id} -y")


class NetworkPrivateLinkSearchScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(
        name_prefix="test_search_service_private_endpoint_", location="eastus"
    )
    def test_private_endpoint_connection_search(
        self, resource_group, resource_group_location
    ):
        from azure.mgmt.core.tools import resource_id

        resource_name = self.create_random_name("cli-test-azs-", 24)
        templateFile = os.path.join(
            TEST_DIR,
            "private_endpoint_arm_templates",
            "search_resource_template.json",
        )
        namespace = "Microsoft.Search"
        instance_type = "searchServices"
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=instance_type,
            name=resource_name,
        )
        self.kwargs.update(
            {
                "deployment_name": self.create_random_name("cli-test-azs-plr-", 24),
                "azs_rg": resource_group,
                "azs_name": resource_name,
                "azs_loc": resource_group_location,
                "azs_template": templateFile,
                "vnet": self.create_random_name("cli-vnet-", 24),
                "subnet": self.create_random_name("cli-subnet-", 24),
                "pe": self.create_random_name("cli-pe-", 24),
                "pe_connection": self.create_random_name("cli-pec-", 24),
                "target_resource_id": target_resource_id,
                "azs_type": "{}/{}".format(namespace, instance_type),
            }
        )

        # Create search resource
        self.cmd(
            'az deployment group create --name {deployment_name} -g {azs_rg} --template-file "{azs_template}" --parameters name={azs_name} --parameters location={azs_loc}'
        )

        # List private link resources
        target_private_link_resource = self.cmd(
            "az network private-link-resource list --name {azs_name} --resource-group {azs_rg} --type {azs_type}",
            checks=self.check("@[0].properties.groupId", "searchService"),
        ).get_output_in_json()
        self.kwargs.update(
            {"group_id": target_private_link_resource[0]["properties"]["groupId"]}
        )

        # Create VNET
        self.cmd(
            "az network vnet create -n {vnet} -g {azs_rg} --subnet-name {subnet}",
            checks=self.check("length(newVNet.subnets)", 1),
        )
        self.cmd(
            "az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {azs_rg} "
            "--disable-private-endpoint-network-policies true",
            checks=self.check("privateEndpointNetworkPolicies", "Disabled"),
        )

        # Create a private endpoint connection (force manual approval)
        pe = self.cmd(
            "az network private-endpoint create -g {azs_rg} -n {pe} --vnet-name {vnet} --subnet {subnet} "
            "--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} "
            "--group-id {group_id} --manual-request"
        ).get_output_in_json()
        self.kwargs["pe_id"] = pe["id"]
        self.kwargs["pe_name"] = self.kwargs["pe_id"].split("/")[-1]

        # Show the connection on search instance
        list_private_endpoint_conn = self.cmd(
            "az network private-endpoint-connection list --name {azs_name} --resource-group {azs_rg} --type {azs_type}"
        ).get_output_in_json()
        self.kwargs.update({"pec_id": list_private_endpoint_conn[0]["id"]})

        self.kwargs.update({"pec_name": self.kwargs["pec_id"].split("/")[-1]})
        self.cmd(
            "az network private-endpoint-connection show --id {pec_id}",
            checks=self.check("id", "{pec_id}"),
        )
        self.cmd(
            "az network private-endpoint-connection show --resource-name {azs_name} --name {pec_name} --resource-group {azs_rg} --type {azs_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Test approval states
        # Approved
        self.kwargs.update(
            {"approval_desc": "Approved.", "rejection_desc": "Rejected."}
        )
        self.cmd(
            "az network private-endpoint-connection approve --resource-name {azs_name} --resource-group {azs_rg} --name {pec_name} --type {azs_type} "
            '--description "{approval_desc}"',
            checks=[
                self.check(
                    "properties.privateLinkServiceConnectionState.status", "Approved"
                )
            ],
        )

        # Rejected
        self.cmd(
            "az network private-endpoint-connection reject --id {pec_id} "
            '--description "{rejection_desc}"',
            checks=[
                self.check(
                    "properties.privateLinkServiceConnectionState.status", "Rejected"
                )
            ],
        )

        # Approval will fail after rejection
        with self.assertRaises(CLIError):
            self.cmd(
                "az network private-endpoint-connection approve --resource-name {azs_name} --resource-group {azs_rg} --name {pec_name} --type {azs_type} "
                '--description "{approval_desc}"'
            )

        self.cmd(
            "az network private-endpoint-connection list --name {azs_name} --resource-group {azs_rg} --type {azs_type}",
            checks=[self.check("length(@)", 1)],
        )

        # Test delete
        self.cmd("az network private-endpoint-connection delete --id {pec_id} -y")


def _test_private_endpoint(self, approve=True, rejected=True, list_name=True, group_id=True, delete=True):
    self.kwargs.update({
        'vnet': self.create_random_name('cli-vnet-', 24),
        'subnet': self.create_random_name('cli-subnet-', 24),
        'pe': self.create_random_name('cli-pe-', 24),
        'pe_connection': self.create_random_name('cli-pec-', 24),
    })

    self.kwargs['resource'] = self.kwargs.get('resource', self.create_random_name('cli-test-resource-', 24))

    # create resource
    self.kwargs['extra_create'] = self.kwargs.get('extra_create', '')
    self.kwargs['show_name'] = self.kwargs.get('show_name', '-n')
    self.kwargs['create_name'] = self.kwargs.get('create_name', '-n')
    self.cmd('{cmd} create -g {rg} {create_name} {resource} {extra_create}')
    result = self.cmd('{cmd} show -g {rg} {show_name} {resource}').get_output_in_json()
    self.kwargs['id'] = result['id']

    # test private-link-resource
    result = self.cmd('network private-link-resource list --name {resource} -g {rg} --type {type}',
                      checks=self.check('length(@)', '{list_num}')).get_output_in_json()
    self.kwargs['group_id'] = result[0]['properties']['groupId'] if group_id else result[0]['groupId']

    # create private-endpoint
    self.cmd('network vnet create -n {vnet} -g {rg} --subnet-name {subnet}')
    self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
             '--disable-private-endpoint-network-policies true')

    self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} '
             '--connection-name {pe_connection}  --private-connection-resource-id {id} --group-id {group_id}',
             checks=self.check('privateLinkServiceConnections[0].privateLinkServiceConnectionState.status', 'Approved'))

    # test private-endpoint-connection
    result = self.cmd('network private-endpoint-connection list --name {resource} -g {rg} --type {type}',
                      checks=self.check('length(@)', 1)).get_output_in_json()
    self.kwargs['name'] = result[0]['name'] if list_name else result[0]['id'].split('/')[-1]
    # For some services: A state change from Approved to Approved is not valid
    if approve:
        self.cmd('network private-endpoint-connection approve --name {name} -g {rg} '
                 '--resource-name {resource} --type {type}')

    self.cmd('network private-endpoint-connection show --name {name} -g {rg} --resource-name {resource} --type {type}',
             checks=self.check('properties.privateLinkServiceConnectionState.status', 'Approved'))

    if rejected:
        self.cmd('network private-endpoint-connection reject --name {name} -g {rg} '
                 '--resource-name {resource} --type {type}',
                 checks=self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'))

    if delete:
        self.cmd('network private-endpoint-connection delete --name {name} -g {rg} '
                 '--resource-name {resource} --type {type} -y')


# Rely on other modules. The test may be broken when other modules bump sdk. At that time, run the failed test in live.
class NetworkPrivateLinkScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_automation", location="eastus2")
    def test_private_endpoint_connection_automation(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'automation account',
            'list_num': 2,
            'type': 'Microsoft.Automation/automationAccounts',
        })
        self.cmd('extension add -n automation')

        _test_private_endpoint(self)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_eventhub", location="westus")
    def test_private_endpoint_connection_eventhub(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'eventhubs namespace',
            'list_num': 1,
            'type': 'Microsoft.EventHub/namespaces',
        })

        _test_private_endpoint(self, approve=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_disk_access", location="westus")
    def test_private_endpoint_connection_disk_access(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'disk-access',
            'list_num': 1,
            'type': 'Microsoft.Compute/diskAccesses',
        })

        _test_private_endpoint(self)

    @live_only()
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_health_care_apis", location="eastus")
    @AllowLargeResponse()
    def test_private_endpoint_connection_health_care_apis(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'healthcareapis service',
            'list_num': 1,
            'type': 'Microsoft.HealthcareApis/services',
            'extra_create': '-l eastus --kind fhir --identity-type SystemAssigned ',
            'show_name': '--resource-name',
            'create_name': '--resource-name'
        })
        self.cmd('extension add -n healthcareapis')

        _test_private_endpoint(self, list_name=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_synapse_workspace")
    @StorageAccountPreparer(name_prefix="testpesyn")
    def test_private_endpoint_connection_synapse_workspace(self, resource_group, storage_account):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'synapse workspace',
            'list_num': 3,
            'type': 'Microsoft.Synapse/workspaces',
            'extra_create': '--storage-account {} --file-system file-000 -p 123-xyz-456 -u synapse1230'.format(
                storage_account),
        })

        _test_private_endpoint(self, group_id=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_sql_server")
    def test_private_endpoint_connection_sql_server(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            # config begin
            'cmd': 'sql server',
            'list_num': 1,
            'type': 'Microsoft.Sql/servers',
            'extra_create': '--admin-user admin123 --admin-password SecretPassword123',
        })

        _test_private_endpoint(self, approve=False, rejected=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_batch_account")
    def test_private_endpoint_connection_batch_account(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'batch account',
            'resource': self.create_random_name(prefix='clibatchtestacct', length=24),
            'list_num': 1,
            'type': 'Microsoft.Batch/batchAccounts',
            'extra_create': '-l eastus --public-network-access Disabled',
        })

        _test_private_endpoint(self, approve=False, rejected=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_media_service")
    @StorageAccountPreparer(name_prefix="testams")
    @AllowLargeResponse()
    def test_private_endpoint_connection_media_service(self, resource_group, storage_account):
        storage_account_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'.format(
            self.get_subscription_id(), resource_group, storage_account)

        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'ams account',
            'list_num': 3,
            'resource': self.create_random_name('clitestams', 24),
            'type': 'Microsoft.Media/mediaservices',
            'extra_create': '--storage-account {storage_account} -l eastus'.format(
                storage_account=storage_account_id)
        })

        _test_private_endpoint(self, approve=False, rejected=False)

    @live_only()
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_storage_sync")
    def test_private_endpoint_connection_storage_sync(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'storagesync',
            'list_num': 1,
            'type': 'Microsoft.StorageSync/storageSyncServices',
            'extra_create': '-l eastus'
        })
        # self.cmd('extension add -n storagesync')

        _test_private_endpoint(self, approve=False, rejected=False)

    @unittest.skip("ASE V3 create takes 2-2.5 hrs to complete, this is a not good test, make this a mock test instead")
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_web")
    def test_private_endpoint_connection_web(self, resource_group):

        web_vnet = self.create_random_name('cli-vnet-web', 24)
        web_subnet = self.create_random_name('cli-subnet-web', 24)

        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'appservice ase',
            'list_num': 1,
            'type': 'Microsoft.Web/hostingEnvironments',
            'extra_create': '--vnet-name {vnet} --subnet {subnet} --kind asev3'.format(
                vnet=web_vnet,
                subnet=web_subnet
            ),
            'web_vnet': web_vnet,
            'web_subnet': web_subnet
        })

        self.cmd('network vnet create -g {rg} -n {web_vnet} --address-prefixes 10.1.0.0/16 '
                 '--subnet-name {web_subnet} --subnet-prefixes 10.1.0.0/24')

        _test_private_endpoint(self, approve=False, rejected=False)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_service_bus")
    def test_private_endpoint_connection_service_bus(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'servicebus namespace',
            'list_num': 1,
            'type': 'Microsoft.ServiceBus/namespaces',
            'extra_create': '-l eastus --sku Premium'
        })

        _test_private_endpoint(self, approve=False, rejected=False)

    @live_only()
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_datafactory", location="westus")
    def test_private_endpoint_connection_datafactory(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'datafactory',
            'list_num': 1,
            'type': 'Microsoft.DataFactory/factories'
        })
        self.cmd('extension add -n datafactory')

        _test_private_endpoint(self)

    @live_only()
    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_databricks_workspaces")
    def test_private_endpoint_connection_databricks_workspaces(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'cmd': 'databricks workspaces',
            'list_num': 1,
            'type': 'Microsoft.Databricks/workspaces',
            'extra_create': '--location westus --sku premium'
        })
        self.cmd('extension add -n databricks')

        _test_private_endpoint(self, approve=False, rejected=False)


class PowerBINetworkARMTemplateBasedScenarioTest(ScenarioTest):
    def _test_private_endpoint_connection_scenario_powerbi(self, resource_group, powerBIResourceName, resource_type, reject):
        from azure.mgmt.core.tools import resource_id

        tenant_id = self.cmd('account list --query "[?isDefault].tenantId" -o tsv').output.strip()

        self.kwargs.update({
            'powerbi_resource_name': powerBIResourceName,
            'powerbi_resource_id': resource_id(subscription=self.get_subscription_id(),
                                              resource_group=resource_group,
                                              namespace=resource_type.split('/')[0],
                                              type=resource_type.split('/')[1],
                                              name=powerBIResourceName),
            'rg': resource_group,
            'resource_type': resource_type,
            'tenant_id': tenant_id,
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'loc': 'eastus2',
            'group_ids': 'tenant'
        })

        # Create powerbi resource from template : private_endpoint_arm_templates/powerbi_privatelinkservicesforpowerbi_parameters.json, powerbi_privatelinkservicesforpowerbi_parameters.json
        param_file_name = "{}_{}_parameters.json".format(resource_type.split('/')[0].split('.')[1].lower(), resource_type.split('/')[1].lower())
        template_file_name = "{}_{}_template.json".format(resource_type.split('/')[0].split('.')[1].lower(), resource_type.split('/')[1].lower())
        self.kwargs.update({
            'param_path': os.path.join(TEST_DIR, 'private_endpoint_arm_templates', param_file_name),
            'template_path': os.path.join(TEST_DIR, 'private_endpoint_arm_templates', template_file_name)
        })
        self.cmd('deployment group create -g {rg} -p "@{param_path}" powerbi_resource_name={powerbi_resource_name} tenant_object_id={tenant_id} -f "{template_path}"')

        # Create vnet and subnet
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --address-prefixes 10.5.0.0/16 '
                 '--subnet-name {subnet} --subnet-prefixes 10.5.0.0/24')

        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # List all private link resources for PowerBI resource
        target_private_link_resource = self.cmd('network private-link-resource list --name {powerbi_resource_name} --resource-group {rg} --type {resource_type}').get_output_in_json()

        # Create a private endpoint connection
        pe = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} -l {loc} --vnet-name {vnet} --subnet {subnet} '
            '--connection-name {pe_connection} --private-connection-resource-id {powerbi_resource_id} '
            '--group-ids {group_ids}').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # List powerbi private link connection
        list_private_endpoint_conn = self.cmd('network private-endpoint-connection list --name {powerbi_resource_name} --resource-group {rg} --type {resource_type}').get_output_in_json()

        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })
        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })

        # Show the private endpoint connection
        self.cmd('network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('network private-endpoint-connection show --resource-name {powerbi_resource_name} --name {pec_name} --resource-group {rg} --type {resource_type}')

        # Approve the private endpoint connection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })

        self.cmd(
            'network private-endpoint-connection approve --resource-name {powerbi_resource_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{approval_desc}"',
                checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])

        # Reject the private endpoint connection
        if reject: self.cmd(
            'network private-endpoint-connection reject --resource-name {powerbi_resource_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{rejection_desc}"',
                checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        self.cmd(
            'network private-endpoint-connection list --name {powerbi_resource_name} --resource-group {rg} --type {resource_type}',
            checks=[
                self.check('length(@)', 1)
            ])

        # Delete the private endpoint connection
        self.cmd('network private-endpoint-connection delete --id {pec_id} -y')

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_powerbi", location="eastus2")
    @unittest.skip('Test account subscription not registered')
    def test_private_endpoint_connection_powerbi(self, resource_group):
        self._test_private_endpoint_connection_scenario_powerbi(resource_group, 'myPowerBIResource', 'Microsoft.PowerBI/privateLinkServicesForPowerBI', True)

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_powerbi", location="eastus2")
    def test_private_endpoint_connection_powerbi_ignoreReject(self, resource_group):
        self._test_private_endpoint_connection_scenario_powerbi(resource_group, 'myPowerBIResource', 'Microsoft.PowerBI/privateLinkServicesForPowerBI', False)

class NetworkPrivateLinkBotServiceScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_abs_private_endpoint', random_name_length=40)
    def test_abs_privatendpoint_with_default(self, resource_group):
        self.kwargs.update({
            'vnet_name': self.create_random_name('testabsvnet', 20),
            'subnet_name': self.create_random_name('testabssubnet', 20),
            'bot_name': self.create_random_name('testbot', 20),
            'app_id': str(uuid.uuid4()),
            'endpoint_name': self.create_random_name('bot_pename', 20),
            'endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'second_endpoint_name': self.create_random_name('bot_penametoo', 20),
            'second_endpoint_conn_name': self.create_random_name('bot_endpointconntoo', 25),
            'desc': 'descriptionMsg'
        })

        # Create subnet with disabled endpoint network policies
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        result = self.cmd('bot create -g {rg} -n {bot_name} -k registration --appid {app_id}').get_output_in_json()
        self.kwargs['bot_id'] = result['id']

        # Add an endpoint that gets auto approved
        result = self.cmd('network private-endpoint create -g {rg} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {bot_id} '
        '--connection-name {endpoint_conn_name} --group-id bot').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        # Add an endpoint and approve it
        result = self.cmd('network private-endpoint create -g {rg} -n {second_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {bot_id} '
        '--connection-name {second_endpoint_conn_name} --group-id bot --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['second_endpoint_name'].lower() in result['name'].lower())

        self.cmd('network private-endpoint-connection approve -g {rg} -n {second_endpoint_name} --resource-name {bot_name} --type Microsoft.BotService/botServices --description {desc}',
        checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{desc}')
        ])

        # Reject previous approved endpoint
        self.cmd('network private-endpoint-connection reject -g {rg} -n {second_endpoint_name} --resource-name {bot_name} --type Microsoft.BotService/botServices --description {desc}',
        checks= [
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('properties.privateLinkServiceConnectionState.description', '{desc}')
        ])

        # List endpoints
        self.cmd('network private-endpoint-connection list -g {rg} --name {bot_name} --type Microsoft.BotService/botServices', checks=[
            self.check('length(@)', '2')
        ])
        # Remove endpoints
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {bot_name} -n {second_endpoint_name} --type Microsoft.BotService/botServices -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list -g {rg} --name {bot_name} --type Microsoft.BotService/botServices', checks=[
            self.check('length(@)', '1')
        ])
        # Show endpoint
        self.cmd('az network private-endpoint-connection show -g {rg} --type Microsoft.BotService/botServices --resource-name {bot_name} -n {endpoint_name}', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', 'Auto-Approved')
        ])
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {bot_name} -n {endpoint_name} --type Microsoft.BotService/botServices -y')


class NetworkPrivateLinkHDInsightScenarioTest(ScenarioTest):

    @record_only()  # This test need to create hdinsight cluster in advance
    @ResourceGroupPreparer(name_prefix='test_hdi_private_link', random_name_length=40, location="southcentralus")
    def test_private_link_resource_hdinsight(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'cluster_id': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/hdicsharprg8691/providers/Microsoft.HDInsight/clusters/hdisdk-pe7318',
            'vnet_name': self.create_random_name('hdi-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('hdi-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('hdi-privatelink-endpoint', 40),
            'endpoint_connection_name': self.create_random_name('hdi-privatelink-endpoint-connection', 40),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })
        # Create hdinsight cluster in advance

        # Create a vnet and subnet for private endpoint connection
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} '
                 '--disable-private-endpoint-network-policies true')

        # Test list private link resources
        hdi_private_link_resources = self.cmd(
            'network private-link-resource list --id {cluster_id}').get_output_in_json()

        self.kwargs['group_id'] = hdi_private_link_resources[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--private-connection-resource-id {cluster_id} --connection-name {endpoint_connection_name} -'
            '-group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {cluster_id}', checks=[
            self.check('@[0].properties.privateLinkServiceConnectionState.status', 'Pending'),
        ]).get_output_in_json()

        # Test approve private endpoint connection
        self.kwargs['private-endpoint-connection-id'] = private_endpoint_connections[0]['id']
        self.cmd(
            'network private-endpoint-connection approve --id {private-endpoint-connection-id} '
            '--description {approve_description_msg}', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])

        # Test reject private endpoint connnection
        self.cmd('network private-endpoint-connection reject --id {private-endpoint-connection-id}'
                 ' --description {reject_description_msg}', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
        ])

        # Test delete private endpoint connection
        self.cmd('network private-endpoint-connection delete --id {private-endpoint-connection-id} --yes')
        import time
        time.sleep(10)
        self.cmd('network private-endpoint-connection show --id {private-endpoint-connection-id}', expect_failure=True)


class NetworkPrivateLinkAzureCacheforRedisScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_acfr_plr')
    def test_private_link_resource_acfr(self, resource_group):
        self.kwargs.update({
            'cache_name': self.create_random_name('cli-test-acfr-plr', 28),
            'loc': 'eastus'
        })
        self.cmd('az redis create --location {loc} --name {cache_name} --resource-group {rg} --sku Basic --vm-size c0')

        self.cmd('network private-link-resource list --name {cache_name} -g {rg} --type Microsoft.Cache/Redis' , checks=[
            self.check('length(@)', 1)]) #####

    @ResourceGroupPreparer(name_prefix='cli_test_acfr_pe')
    def test_private_endpoint_connection_acfr(self,resource_group):
        self.kwargs.update({
            'cache_name': self.create_random_name('cli-test-acfr-pe-', 28),
            'loc': 'westus',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare Redis Cache and network
        cache = self.cmd('az redis create --location {loc} --name {cache_name} --resource-group {rg} --sku Standard --vm-size c1').get_output_in_json()
        self.kwargs['acfr_id'] = cache['id']

        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))

        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Waiting for Cache creation
        if self.is_live:
            time.sleep(25 * 60)

        # Creating Private Endpoint
        pe = self.cmd('az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} --connection-name {pe_connection} --private-connection-resource-id {acfr_id} --group-id redisCache').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Test get details of private endpoint
        results = self.kwargs['pe_id'].split('/')
        self.kwargs['pec_id'] = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/privateEndpoints/{2}'.format(results[2], results[4], results[-1])

        self.cmd('az network private-endpoint show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))

        self.cmd(
            'az network private-endpoint show --resource-group {rg} --name {pe_name}',
            checks=self.check('name', '{pe_name}'))


        # Show the connection at azure cache for redis

        redis = self.cmd('az redis show -n {cache_name} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', redis)
        self.assertEqual(len(redis['privateEndpointConnections']), 1)
        self.assertEqual(redis['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')

        self.kwargs['red_pec_id'] = redis['privateEndpointConnections'][0]['id']

        self.cmd('az network private-endpoint-connection list --id {red_pec_id}', checks=[
            self.check('length(@)', '1'),
        ])

        self.cmd('az network private-endpoint-connection show --id {red_pec_id}', checks=self.check('id', '{red_pec_id}'))

        self.cmd('az network private-endpoint-connection reject --id {red_pec_id}', checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {red_pec_id} -y')

        self.cmd('az network private-endpoint-connection list --id {red_pec_id}', checks=[
            self.check('length(@)', '0'),
        ])


class AzureWebPubSubServicePrivateEndpointScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(random_name_length=20)
    def test_webpubsub_private_endpoint(self, resource_group):
        webpubsub_name = self.create_random_name('webpubsub', 16)
        sku = 'Standard_S1'
        unit_count = 1
        location = 'centraluseuap'

        self.kwargs.update({
            'location': location,
            'webpubsub_name': webpubsub_name,
            'sku': sku,
            'unit_count': unit_count,
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'private_endpoint': 'private_endpoint1',
            'private_endpoint_connection': 'private_endpoint_connection1'
        })

        # install az webpubsub
        self.cmd('extension add --name webpubsub')

        webpubsub = self.cmd('az webpubsub create -n {webpubsub_name} -g {rg} --sku {sku} -l {location}', checks=[
            self.check('name', '{webpubsub_name}'),
            self.check('location', '{location}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{sku}')
        ]).get_output_in_json()

        # Prepare network
        self.cmd('network vnet create -g {rg} -n {vnet} -l {location} --subnet-name {subnet}')
        self.cmd('network vnet subnet update --name {subnet} --resource-group {rg} --vnet-name {vnet} --disable-private-endpoint-network-policies true')

        self.kwargs.update({
            'webpubsub_id': webpubsub['id']
        })

        # Create a private endpoint connection
        self.cmd('network private-endpoint create --resource-group {rg} --vnet-name {vnet} --subnet {subnet} --name {private_endpoint}  --private-connection-resource-id {webpubsub_id} --group-ids webpubsub --connection-name {private_endpoint_connection} --location {location} --manual-request')

        # Test private link resource list
        self.cmd('network private-link-resource list -n {webpubsub_name} -g {rg} --type Microsoft.SignalRService/webpubsub', checks=[
            self.check('length(@)', 1)
        ])

        s_r = self.cmd('webpubsub show -n {webpubsub_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'private_endpoint_connection_id': s_r['privateEndpointConnections'][0]['id']
        })

        # Test show private endpoint connection
        self.cmd('network private-endpoint-connection show --id {private_endpoint_connection_id}', checks=[
            self.check('id', '{private_endpoint_connection_id}'),
            self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        ])

        # Test list private endpoint connection
        self.cmd('network private-endpoint-connection list --id {webpubsub_id}', checks=[
            self.check('length(@)', 1)
        ])

        # Test approve private endpoint connection
        self.cmd('network private-endpoint-connection approve --id {private_endpoint_connection_id}', checks=[
            self.check('id', '{private_endpoint_connection_id}'),
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
        ])

        # Test reject private endpoint connection
        self.cmd('network private-endpoint-connection reject --id {private_endpoint_connection_id}', checks=[
            self.check('id', '{private_endpoint_connection_id}'),
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
        ])

        # Test update public network rules
        self.cmd('webpubsub network-rule update --public-network -n {webpubsub_name} -g {rg} --allow RESTAPI', checks=[
            self.check('networkAcLs.publicNetwork.allow[0]', 'RESTAPI'),
            self.check('length(networkAcLs.publicNetwork.deny)', 0),
        ])

        # Test list network rules
        n_r = self.cmd('webpubsub network-rule show -n {webpubsub_name} -g {rg}', checks=[
            self.check('length(privateEndpoints)', 1)
        ]).get_output_in_json()

        self.kwargs.update({
            'connection_name': n_r['privateEndpoints'][0]['name']
        })

        # Test update private network rules
        self.cmd('webpubsub network-rule update --connection-name {connection_name} -n {webpubsub_name} -g {rg} --allow RESTAPI', checks=[
            self.check('networkAcLs.privateEndpoints[0].allow[0]', 'RESTAPI'),
            self.check('length(networkAcLs.privateEndpoints[0].deny)', 0),
        ])

        # Test delete private endpoint connection
        self.cmd('network private-endpoint-connection delete --id {private_endpoint_connection_id} -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list --id {webpubsub_id}', checks=[
            self.check('length(@)', 0)
        ])


class NetworkPrivateLinkDataFactoryScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='test_datafactory_private_endpoint', random_name_length=40, location="westus")
    def test_private_link_endpoint_datafactory(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'datafactory_name': self.create_random_name('cli-test-datafactory-pe-', 40),
            'vnet_name': self.create_random_name('datafactory-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('datafactory-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('datafactory-privatelink-endpoint', 40),
            'endpoint_connection_name': self.create_random_name('df-privatelink-endpoint-connection', 40),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })
        # Create datafactory
        datafactory = self.cmd(
            'az datafactory create --name {datafactory_name} --resource-group {rg}').get_output_in_json()
        self.kwargs['datafactory_id'] = datafactory['id']

        # Create a vnet and subnet for private endpoint connection
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources
        datafactory_private_link_resources = self.cmd(
            'network private-link-resource list --id {datafactory_id}').get_output_in_json()
        self.kwargs['group_id'] = datafactory_private_link_resources[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--private-connection-resource-id {datafactory_id} --connection-name {endpoint_connection_name} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {datafactory_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Pending'),
                                                ]).get_output_in_json()

        # Test approve private endpoint connection
        self.kwargs['private-endpoint-connection-id'] = private_endpoint_connections[0]['id']
        self.cmd(
            'network private-endpoint-connection approve --id {private-endpoint-connection-id} '
            '--description {approve_description_msg}', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])

        # Test reject private endpoint connnection
        self.cmd('network private-endpoint-connection reject --id {private-endpoint-connection-id}'
                 ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
        ])

        # Test delete private endpoint connection
        self.cmd('network private-endpoint-connection delete --id {private-endpoint-connection-id} --yes')
        import time
        time.sleep(10)
        self.cmd('network private-endpoint-connection show --id {private-endpoint-connection-id}',
                 expect_failure=True)


class NetworkHybridComputePrivateLinkScopesTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_hybridcompute_pe', random_name_length=40)
    def test_hybridcompute_private_endpoint(self, resource_group):
        self.kwargs.update({
            'scope': 'clitestscopename',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'private_endpoint': self.create_random_name('cli-pe-', 24),
            'private_endpoint2': self.create_random_name('cli-pe-', 24),
            'private_endpoint_connection': self.create_random_name('cli-pec-', 24),
            'private_endpoint_connection2': self.create_random_name('cli-pec-', 24),
            'location': 'eastus2euap',
            'approve_desc': 'ApprovedByTest',
            'reject_desc': 'RejectedByTest'
        })

        # install az connectedmachine
        self.cmd('extension add --name connectedmachine')

        # Test connectedmachine private-link-scope funcitons and create a private link scope
        self.cmd('connectedmachine private-link-scope create --scope-name {scope} -g {rg}', checks=[
            self.check('name', '{scope}')
        ])

        self.cmd('connectedmachine private-link-scope update --scope-name {scope} -g {rg} --tags tag1=d1', checks=[
            self.check('tags.tag1', 'd1')
        ])

        self.cmd('connectedmachine private-link-scope show --scope-name {scope} -g {rg}', checks=[
            self.check('tags.tag1', 'd1')
        ])
        self.cmd('connectedmachine private-link-scope list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {location} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test private link resource list
        pr = self.cmd('network private-link-resource list --name {scope} -g {rg} --type microsoft.HybridCompute/privateLinkScopes', checks=[
            self.check('length(@)', 1)
        ]).get_output_in_json()

        # Add an endpoint that gets auto approved
        self.kwargs['group_id'] = pr[0]['groupId']
        private_link_scope = self.cmd('connectedmachine private-link-scope show --scope-name {scope} -g {rg}').get_output_in_json()
        self.kwargs['scope_id'] = private_link_scope['id']

        result = self.cmd('network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} --private-connection-resource-id {scope_id} '
        '--connection-name {private_endpoint_connection} --group-id {group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint_connection'].lower() in result['name'].lower())

        # Add an endpoint and approve it
        result = self.cmd('network private-endpoint create -g {rg} -n {private_endpoint2} --vnet-name {vnet} --subnet {subnet} --private-connection-resource-id {scope_id} '
        '--connection-name {private_endpoint_connection2} --group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint_connection2'].lower() in result['name'].lower())

        self.cmd('network private-endpoint-connection approve -g {rg} -n {private_endpoint_connection2} --resource-name {scope} --type Microsoft.HybridCompute/privateLinkScopes --description {approve_desc}',
        checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{approve_desc}')
        ])

        # Reject previous approved endpoint
        self.cmd('network private-endpoint-connection reject -g {rg} -n {private_endpoint_connection2} --resource-name {scope} --type Microsoft.HybridCompute/privateLinkScopes --description {reject_desc}',
        checks= [
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('properties.privateLinkServiceConnectionState.description', '{reject_desc}')
        ])

        # List endpoints
        self.cmd('network private-endpoint-connection list -g {rg} --name {scope} --type Microsoft.HybridCompute/privateLinkScopes', checks=[
            self.check('length(@)', '2')
        ])
        # Remove endpoints
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {scope} -n {private_endpoint_connection2} --type Microsoft.HybridCompute/privateLinkScopes -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list -g {rg} --name {scope} --type Microsoft.HybridCompute/privateLinkScopes', checks=[
            self.check('length(@)', '1')
        ])
        # Show endpoint
        self.cmd('az network private-endpoint-connection show -g {rg} --type Microsoft.HybridCompute/privateLinkScopes --resource-name {scope} -n {private_endpoint_connection}', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', 'Auto-Approved')
        ])
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {scope} -n {private_endpoint_connection} --type Microsoft.HybridCompute/privateLinkScopes -y')


class NetworkPrivateLinkDatabricksScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='test_databricks_private_endpoint', random_name_length=40, location="westus")
    def test_private_endpoint_databricks_workspace(self, resource_group):
        location = 'westus'
        self.kwargs.update({
            'resource_group': resource_group,
            'databricks_name': 'test-workspace',
            'location': location,
            'nsg_name': self.create_random_name('nsg', 40),
            'vnet_name': self.create_random_name('databricks-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('databricks-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('databricks-privatelink-endpoint', 40),
            'endpoint_connection_name': self.create_random_name('db-privatelink-endpoint-connection', 40),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })
        # Create vnet and create nsg and attach it to both subnets.
        self.cmd('network nsg create -g {rg} --name {nsg_name} ')

        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name} '
                 '--network-security-group {nsg_name}')

        # Create private-subnet and public-subnet and attach nsg to both subnets
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet_name} --name private-subnet '
                 '--address-prefixes 10.0.1.0/24',
                 checks=self.check('provisioningState', 'Succeeded'))
        self.cmd('network vnet subnet create -g {rg} --vnet-name {vnet_name} --name public-subnet '
                 '--address-prefixes 10.0.2.0/24',
                 checks=self.check('provisioningState', 'Succeeded'))

        # Update subnet
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name private-subnet '
                 '--delegation "Microsoft.Databricks/workspaces" '
                 '--network-security-group {nsg_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name public-subnet '
                 '--delegation "Microsoft.Databricks/workspaces" '
                 '--network-security-group {nsg_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create vnet injected databricks workspace
        databricks = self.cmd(
            'az databricks workspace create --name {databricks_name} --resource-group {rg} '
            '--sku premium --private-subnet private-subnet --public-subnet public-subnet '
            '--vnet {vnet_name} --location {location}').get_output_in_json()
        self.kwargs['databricks_id'] = databricks['id']

        # Test list private link resources
        db_private_link_resources = self.cmd(
            'network private-link-resource list --id {databricks_id} ').get_output_in_json()
        self.kwargs['group_id'] = db_private_link_resources[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--private-connection-resource-id {databricks_id} --connection-name {endpoint_connection_name} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {databricks_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Pending'),
                                                ]).get_output_in_json()

        # Test approve private endpoint connection
        self.kwargs['private-endpoint-connection-id'] = private_endpoint_connections[0]['id']
        self.cmd(
            'network private-endpoint-connection approve --id {private-endpoint-connection-id} '
            '--description {approve_description_msg}', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])

        self.cmd('az network private-endpoint-connection show --id {private-endpoint-connection-id}',
                 checks=self.check('id', '{private-endpoint-connection-id}'))

        # Test reject private endpoint connection
        self.cmd(
            'network private-endpoint-connection reject --id {private-endpoint-connection-id}'
            ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {private-endpoint-connection-id} -y')
        time.sleep(300)
        self.cmd('az network private-endpoint-connection list --id {private-endpoint-connection-id}', checks=[
            self.check('length(@)', '0'),
        ])


class NetworkPrivateLinkRecoveryServicesScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_recoveryservices_pe', random_name_length=40, location="centraluseuap")
    def test_recoveryservices_private_endpoint(self, resource_group):
        self.kwargs.update({
            'vault': self.create_random_name('cli-recoveryservices-vault-', 40),
            'vnet': self.create_random_name('cli-recoveryservices-vnet-', 40),
            'subnet': self.create_random_name('cli-recoveryservices-subnet-', 40),
            'private_endpoint': self.create_random_name('cli-recoveryservices-pe-', 40),
            'private_endpoint_connection': self.create_random_name('cli-recoveryservices-pec-', 40),
            'location': 'centraluseuap',
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })

        # Create recovery services vault
        self.kwargs['vault_id']= self.cmd(
            'backup vault create --name {vault} --resource-group {rg} --location {location} --query id').output

        # Enable System assigned msi
        self.kwargs['system_msi'] = self.cmd(
            'backup vault identity assign --system-assigned -g {rg} -n {vault} --query identity.principalId').output

        # Give rg contributor access to system msi
        self.cmd('role assignment create --role Contributor --assignee-object-id {system_msi} -g {rg}')

        # Create virtual net and sub net
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')

        # Update sub net
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} --name {subnet} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources
        vault_private_link_resources = self.cmd(
            'network private-link-resource list --id {vault_id} ').get_output_in_json()
        self.kwargs['group_id'] = vault_private_link_resources[0]['properties']['groupId']

        # Create private endpoint
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {vault_id} --connection-name {private_endpoint_connection} '
            '--group-id {group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {vault_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Approved'),
                                                ]).get_output_in_json()

        self.kwargs['private-endpoint-connection-id'] = private_endpoint_connections[0]['id']

        # Test reject private endpoint connection
        self.cmd(
            'network private-endpoint-connection reject --id {private-endpoint-connection-id}'
            ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {private-endpoint-connection-id} -y')
        time.sleep(30)
        self.cmd('az network private-endpoint-connection list --id {private-endpoint-connection-id}', checks=[
            self.check('length(@)', '0'),
        ])

        self.cmd('vault delete --name {vault} --resource-group {rg}')


class NetworkPrivateLinkPrivateLinkServicesScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_private_endpoint_pls', location='centralus')
    def test_private_endpoint_pls(self):
        self.kwargs.update({
            'vnet': self.create_random_name('cli-test-vnet-', 20),
            'subnet1': self.create_random_name('cli-test-subnet-', 20),
            'subnet2': self.create_random_name('cli-test-subnet-', 20),
            'lb': self.create_random_name('cli-test-lb-', 20),
            'ip': self.create_random_name('cli-test-ip-', 20),
            'pls': self.create_random_name('cli-test-pls-', 20),
            'endpoint1': self.create_random_name('cli-test-endpoint-', 25),
            'endpoint2': self.create_random_name('cli-test-endpoint-', 25),
            'connection1': self.create_random_name('cli-test-conn-', 20),
            'connection2': self.create_random_name('cli-test-conn-', 20),
            'type': 'Microsoft.Network/privateLinkServices'
        })

        # create private link service
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet2}')
        self.cmd('network vnet subnet update -g {rg} -n {subnet2} --vnet-name {vnet} --disable-private-link-service-network-policies')
        self.cmd('network lb create -g {rg} -n {lb} --public-ip-address {ip} --sku Standard')
        self.kwargs['pls_id'] = self.cmd('network private-link-service create -g {rg} -n {pls} --vnet-name {vnet} --subnet {subnet2} --lb-name {lb} --lb-frontend-ip-configs LoadBalancerFrontEnd').get_output_in_json()['id']

        # create subnet with disabled endpoint network policies
        self.cmd('network vnet subnet create -g {rg} -n {subnet1} --vnet-name {vnet} --address-prefixes 10.0.2.0/24')
        self.cmd('network vnet subnet update -g {rg} -n {subnet1} --vnet-name {vnet} --disable-private-endpoint-network-policies')

        # add an endpoint and approve it
        self.cmd('network private-endpoint create -g {rg} -n {endpoint1} --vnet-name {vnet} --subnet {subnet1} --private-connection-resource-id {pls_id} --connection-name {connection1}')
        self.kwargs['request1'] = self.cmd('network private-endpoint-connection list -g {rg} -n {pls} --type {type}').get_output_in_json()[0]['name']
        self.cmd(
            'network private-endpoint-connection approve -n {request1} -g {rg} --resource-name {pls} --type {type} --description Approved',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', 'Approved')
            ]
        )

        # add an endpoint and then reject it
        self.cmd('network private-endpoint create -g {rg} -n {endpoint2} --vnet-name {vnet} --subnet {subnet1} --private-connection-resource-id {pls_id} --connection-name {connection2}')
        self.kwargs['request2'] = self.cmd('network private-endpoint-connection list -g {rg} -n {pls} --type {type}').get_output_in_json()[1]['name']
        self.cmd(
            'network private-endpoint-connection reject -n {request2} -g {rg} --resource-name {pls} --type {type} --description Rejected',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                self.check('properties.privateLinkServiceConnectionState.description', 'Rejected')
            ]
        )

        # remove endpoints
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {pls} -n {request2} --type {type} --yes')
        time.sleep(30)
        self.cmd(
            'network private-endpoint-connection show -g {rg} --resource-name {pls} -n {request1} --type {type}',
            checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', 'Approved'),
                self.check('name', '{request1}')
            ]
        )
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {pls} -n {request1} --type {type} --yes')


if __name__ == '__main__':
    unittest.main()
