﻿# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
import time

from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)
from azure.cli.core.util import parse_proxy_resource_id, CLIError

from azure.cli.command_modules.keyvault.tests.latest.test_keyvault_commands import _create_keyvault
from azure.cli.command_modules.rdbms.tests.latest.test_rdbms_commands import ServerPreparer


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

        self.cmd('network private-endpoint-connection approve --name {sa_pec_name} -g {rg} --resource-name {sa} --type Microsoft.Storage/storageAccounts',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

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
    @ResourceGroupPreparer(location='eastus2euap')
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


class NetworkPrivateLinkCosmosDBScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_plr')
    def test_private_link_resource_cosmosdb(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-plr-', 28),
            'loc': 'centraluseuap'
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')

        self.cmd('network private-link-resource list --name {acc} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'Sql')])

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_pe')
    def test_private_endpoint_connection_cosmosdb(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name('cli-test-cosmosdb-pe-', 28),
            'loc': 'centraluseuap',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        # Prepare cosmos db account and network
        account = self.cmd('az cosmosdb create -n {acc} -g {rg}').get_output_in_json()
        self.kwargs['acc_id'] = account['id']
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pe = self.cmd('network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
                      '--connection-name {pe_connection} --private-connection-resource-id {acc_id} '
                      '--group-id Sql').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        results = self.kwargs['pe_id'].split('/')
        self.kwargs[
            'pec_id'] = '/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.DocumentDB/databaseAccounts/{2}/privateEndpointConnections/{3}'.format(
            results[2], results[4], self.kwargs['acc'], results[-1])
        self.cmd('network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd(
            'network private-endpoint-connection show --resource-name {acc} --name {pe_name} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts',
            checks=self.check('name', '{pe_name}'))
        self.cmd('network private-endpoint-connection show --resource-name {acc} -n {pe_name} -g {rg} --type Microsoft.DocumentDB/databaseAccounts',
                 checks=self.check('name', '{pe_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })
        self.cmd(
            'network private-endpoint-connection approve --resource-name {acc} --resource-group {rg} --name {pe_name} --type Microsoft.DocumentDB/databaseAccounts '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}')
            ])
        self.cmd('network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}')
                 ])
        self.cmd('network private-endpoint-connection list --name {acc} --resource-group {rg} --type Microsoft.DocumentDB/databaseAccounts', checks=[
            self.check('length(@)', 1)
        ])

        # Test delete
        self.cmd('network private-endpoint-connection delete --id {pec_id} -y')


if __name__ == '__main__':
    unittest.main()
