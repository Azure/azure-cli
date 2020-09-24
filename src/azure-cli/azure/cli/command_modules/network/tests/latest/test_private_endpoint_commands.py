# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest

from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, live_only)
from azure.cli.core.util import parse_proxy_resource_id, CLIError

from .preparers import _create_keyvault, ServerPreparer


TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


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
                 checks=self.check('@[0].properties.groupId', 'vault'))

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
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}'),
                     self.check('properties.provisioningState', 'Succeeded')
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
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}'),
                     self.check('properties.provisioningState', 'Succeeded')
                 ])

        self.cmd('network private-endpoint-connection show --id {kv_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))

        self.cmd('network private-endpoint-connection list --id {kv_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {kv_pe_id} -y')


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
        with self.assertRaisesRegexp(SystemExit, '3'):
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

        with self.assertRaisesRegexp(CLIError, expectedError):
            self.cmd('network private-endpoint-connection approve --resource-name {} -g {} --name {} --description "{}" --type {}'
                     .format(server, resource_group, server_pec_name, approval_description, rp_type))

        with self.assertRaisesRegexp(CLIError, expectedError):
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

        with self.assertRaisesRegexp(CLIError, expectedError):
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

        with self.assertRaisesRegexp(CLIError, expectedError):
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

    # Currently private-link-resource and private-endpoint-connection are whitelist only features so scenario tests are limited
    @ResourceGroupPreparer(location='westcentralus')
    def test_private_link_resource_batch_account(self, resource_group, batch_account_name='testplinksbatch'):
        self.kwargs.update({
            'vnet_name': self.create_random_name('testvnet', 20),
            'subnet_name': self.create_random_name('testsubnet', 20),
            'second_endpoint_name': self.create_random_name('priv_endpoint', 25),
            'second_endpoint_conn_name': self.create_random_name('priv_endpointconn', 25),
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!',
            'rg': resource_group,
            'acc_n': batch_account_name,
            'loc': 'westcentralus'
        })
        account = self.cmd('batch account create -g {rg} -n {acc_n} -l {loc} --public-network-access disabled').assert_with_checks([
            self.check('name', '{acc_n}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')]).get_output_in_json()
        self.kwargs['acc_id'] = account['id']
        # create subnet with disabled endpoint network policies
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        # add an endpoint and then reject it
        self.cmd(
            'network private-endpoint create '
            '-n {second_endpoint_name} '
            '-g {rg} '
            '--subnet {subnet_name} '
            '--vnet-name {vnet_name} '
            '--private-connection-resource-id {acc_id} '
            '--group-ids batchAccount '
            '--connection-name {second_endpoint_conn_name} '
            '--manual-request').get_output_in_json()
        private_endpoints = self.cmd('network private-endpoint-connection list --name {acc_n} --resource-group {rg} --type Microsoft.Batch/batchAccounts', checks=[
            self.check('length(@)', 1)
        ]).get_output_in_json()
        self.cmd('batch account show --name {acc_n} --resource-group {rg}', checks=[
            self.check('length(privateEndpointConnections[*])', 1),
            self.check('privateEndpointConnections[0].id', private_endpoints[0]['id'])
        ])
        self.kwargs['pe_id'] = private_endpoints[0]["id"]
        self.kwargs['pe_name'] = private_endpoints[0]['name']

        self.cmd(
            'network private-endpoint-connection approve --resource-name {acc_n} --name {pe_name} --resource-group {rg} --type Microsoft.Batch/batchAccounts '
            '--description "{approval_desc}"')
        self.cmd(
            'network private-endpoint-connection show --resource-name {acc_n} --name {pe_name} --resource-group {rg} --type Microsoft.Batch/batchAccounts',
            checks=[
                self.check('name', '{pe_name}'),
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}')])

        self.cmd('network private-endpoint-connection reject --resource-name {acc_n} --name {pe_name} --resource-group {rg} --type Microsoft.Batch/batchAccounts '
                 '--description "{rejection_desc}"')
        self.cmd('network private-endpoint-connection show --id {pe_id}',
                 checks=[
                     self.check('id', '{pe_id}'),
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}')])

        # Test delete
        self.cmd('network private-endpoint-connection delete --id {pe_id} -y')
        self.cmd('network private-endpoint delete -n {second_endpoint_name} -g {rg}')


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
        account = self.cmd('az cosmosdb create -n {acc} -g {rg}').get_output_in_json()
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


class NetworkPrivateLinkWebappScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westus2')
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

    @ResourceGroupPreparer(location='westus2')
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


class NetworkPrivateLinkEventGridScenarioTest(ScenarioTest):
    def setUp(self):
        super(NetworkPrivateLinkEventGridScenarioTest, self).setUp()
        self.cmd('extension add -n eventgrid')

    def tearDown(self):
        self.cmd('extension remove -n eventgrid')
        super(NetworkPrivateLinkEventGridScenarioTest, self).tearDown()

    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_plr')
    def test_private_link_resource_event_grid(self, resource_group):
        self.kwargs.update({
            'topic_name': self.create_random_name(prefix='cli', length=40),
            'domain_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'rg': resource_group
        })

        scope_id = self.cmd(
            'az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location} --public-network-access disabled',
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

        self.cmd('az network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('az network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('az network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        scope = self.cmd('az eventgrid topic create --name {topic_name} --resource-group {rg} --location {location} --public-network-access disabled', checks=[
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
        self.cmd('az network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids topic --connection-name {connection_name}')

        server_pec_id = self.cmd('az eventgrid topic show --name {topic_name} --resource-group {rg}').get_output_in_json()['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('az network private-endpoint-connection list --resource-group {rg} --name {topic_name} --type Microsoft.EventGrid/topics',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('az network private-endpoint-connection show --resource-group {rg} --resource-name {topic_name} --name {server_pec_name} --type Microsoft.EventGrid/topics')

        self.cmd('az network private-endpoint-connection approve --resource-group {rg} --resource-name {topic_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/topics --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])
        self.cmd('az network private-endpoint-connection reject --resource-group {rg} --resource-name {topic_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/topics --description "{rejection_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_description}')
                 ])

        self.cmd('az network private-endpoint-connection delete --resource-group {rg} --resource-name {topic_name} --name {server_pec_name} --type Microsoft.EventGrid/topics -y')

        self.cmd('az network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('az network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('az network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('az eventgrid topic delete --name {topic_name} --resource-group {rg}')

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

        self.cmd('az network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('az network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('az network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        scope = self.cmd('az eventgrid domain create --name {domain_name} --resource-group {rg} --location {location} --public-network-access disabled', checks=[
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
        self.cmd('az network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids domain --connection-name {connection_name}')

        server_pec_id = self.cmd('az eventgrid domain show --name {domain_name} --resource-group {rg}').get_output_in_json()['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('az network private-endpoint-connection list --resource-group {rg} --name {domain_name} --type Microsoft.EventGrid/domains',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('az network private-endpoint-connection show --resource-group {rg} --resource-name {domain_name} --name {server_pec_name} --type Microsoft.EventGrid/domains')

        self.cmd('az network private-endpoint-connection approve --resource-group {rg} --resource-name {domain_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/domains --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])
        self.cmd('az network private-endpoint-connection reject --resource-group {rg} --resource-name {domain_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/domains --description "{rejection_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_description}')
                 ])

        self.cmd('az network private-endpoint-connection delete --resource-group {rg} --resource-name {domain_name} --name {server_pec_name} --type Microsoft.EventGrid/domains -y')

        self.cmd('az network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('az network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('az network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('az eventgrid domain delete --name {domain_name} --resource-group {rg}')


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


if __name__ == '__main__':
    unittest.main()
