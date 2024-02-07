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
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, KeyVaultPreparer, ManagedHSMPreparer, live_only, record_only)
from azure.cli.core.util import parse_proxy_resource_id, CLIError

from azure.cli.command_modules.rdbms.tests.latest.test_rdbms_commands import ServerPreparer
from azure.cli.command_modules.batch.tests.latest.batch_preparers import BatchAccountPreparer, BatchScenarioMixin
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_text_payload

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
KV_CERTS_DIR = os.path.join(TEST_DIR, 'certs')


class RedisCacheCredentialReplacer(RecordingProcessor):
    def process_response(self, response):
        import json
        KEY_REPLACEMENT = "replaced-access-key"

        if is_text_payload(response) and response["body"]["string"]:
            try:
                props = json.loads(response["body"]["string"])
                if "accessKeys" in props["properties"]:
                    props["properties"]["accessKeys"]["primaryKey"] = KEY_REPLACEMENT
                    props["properties"]["accessKeys"]["secondaryKey"] = KEY_REPLACEMENT
                response["body"]["string"] = json.dumps(props)
            except (TypeError, KeyError):
                pass
        return response


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
    @ManagedHSMPreparer(name_prefix='cli-test-hsm-plr-', certs_path=KV_CERTS_DIR)
    def test_mhsm_private_link_resource(self, resource_group, managed_hsm):
        self.kwargs.update({
            'hsm': managed_hsm,
        })
        self.cmd('network private-link-resource list '
                 '--name {hsm} '
                 '-g {rg} '
                 '--type microsoft.keyvault/managedHSMs',
                 checks=self.check('@[0].properties.groupId', 'managedhsm'))

    @ResourceGroupPreparer(name_prefix='cli_test_keyvault_pe')
    @KeyVaultPreparer(name_prefix='cli-test-kv-pe-', location='uksouth')
    def test_private_endpoint_connection_keyvault(self, resource_group):
        self.kwargs.update({
            'loc': 'uksouth',
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
    @ManagedHSMPreparer(name_prefix='cli-test-hsm-pe-', certs_path=KV_CERTS_DIR, location='uksouth')
    def test_hsm_private_endpoint_connection2(self, resource_group, managed_hsm):
        self.kwargs.update({
            'hsm': managed_hsm,
            'loc': 'uksouth',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group,
            'subscription_id': self.get_subscription_id(),
        })

        # Prepare hsm and network
        self.kwargs['hsm_id'] = f"/subscriptions/{self.kwargs['subscription_id']}/resourceGroups/{resource_group}/providers/Microsoft.KeyVault/managedHSMs/{managed_hsm}"
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
        keyvault = self.cmd('keyvault show --hsm-name {hsm} -g {rg}',
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

    @ResourceGroupPreparer(location='centralus')
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

class NetworkPrivateLinkAgFoodPlatformsScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_farmbeats_pe', random_name_length=40, location="centraluseuap")
    def test_farmbeats_private_endpoint(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'resource_name': self.create_random_name('cli', 15),
            'resource_type': 'farmBeats',
            'sub': self.get_subscription_id(),
            'namespace': 'Microsoft.AgFoodPlatform',
            'vnet': self.create_random_name('cli-farmbeats-vnet-', 40),
            'subnet': self.create_random_name('cli-farmbeats-subnet-', 40),
            'private_endpoint': self.create_random_name('cli-farmbeats-pe-', 40),
            'private_endpoint_connection': self.create_random_name('cli-farmbeats-pec-', 40),
            'location': 'centraluseuap',
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!',
            'body': '{\\"location\\":\\"centraluseuap\\",\\"tags\\":{\\"awesomeness\\":\\"100\\",\\"farm\\":\\"beats\\"},\\"sku\\":{\\"name\\":\\"S0\\"}}',
            'api_version': '2021-09-01-preview',
            'type': 'Microsoft.AgFoodPlatform/farmBeats'
        })

        # Create farmbeats resource S0 sku in centraluseuap
        # This API only accepts the creation request, provisioning state of the resource has to be polled
        self.cmd('az rest --method "PUT" \
                --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/{namespace}/{resource_type}/{resource_name}?api-version={api_version}" \
                --body "{body}"')

        # check for resource provisioning state
        self.check_provisioning_state_for_farmbeats_resource()

        # Get resource id for the instance
        self.kwargs['resource_id']= self.cmd(
            'az resource show --name {resource_name} -g {rg} --resource-type {resource_type} --namespace {namespace} --query id').output

        # Create virtual net and sub net
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')

        # Update sub net
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} --name {subnet} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources. Get group id
        private_link_resources = self.cmd(
            'network private-link-resource list --id {resource_id} ').get_output_in_json()
        self.kwargs['group_id'] = private_link_resources[0]['properties']['groupId']


        # Create private endpoint
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {resource_id} --connection-name {private_endpoint_connection} '
            '--group-id {group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint'].lower() in private_endpoint['name'].lower())


        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {resource_id}').get_output_in_json()

        self.kwargs['private_endpoint_connection_id'] = private_endpoint_connections[0]['id']

        # Test reject private endpoint connection
        self.cmd(
            'network private-endpoint-connection reject --id {private_endpoint_connection_id}'
            ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {private_endpoint_connection_id} -y')
        time.sleep(30)
        self.cmd('az network private-endpoint-connection list --id {private_endpoint_connection_id}', checks=[
            self.check('length(@)', '0'),
        ])

    def get_provisioning_state_for_farmbeats_resource(self):
        # get provisioning state
        response = self.cmd('az rest --method "GET" \
                --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/{namespace}/{resource_type}/{resource_name}?api-version={api_version}"').get_output_in_json()

        return response['properties']['provisioningState']

    def check_provisioning_state_for_farmbeats_resource(self):
        count = 0
        print("checking status of creation...........")
        state = self.get_provisioning_state_for_farmbeats_resource()
        print(state)
        while state!="Succeeded":
            if state == "Failed":
                print("creation failed!")
                self.assertTrue(False)
            elif (count == 12):
                print("TimeOut after waiting for 120 mins!")
                self.assertTrue(False)
            print("instance not yet created. waiting for 10 more mins...")
            count+=1
            time.sleep(600) # Wait for 10 minutes
            state = self.get_provisioning_state_for_farmbeats_resource()
        print("creation succeeded!")


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
        account = self.cmd('az cosmosdb create -n {acc} -g {rg} --public-network-access "DISABLED"').get_output_in_json()
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
            'apim create -g {resource_group} -n {service_name} --l {location} --publisher-email email@mydomain.com --publisher-name Microsoft --sku-name "Premium"').get_output_in_json()
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
            'network private-endpoint-connection reject -g {resource_group} --resource-name {service_name} -n {endpoint_request} --type Microsoft.ApiManagement/service ',
            checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd("az apim wait --updated --name {service_name} --resource-group {resource_group}")

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

        self.cmd("az apim wait --updated --name {service_name} --resource-group {resource_group}")

        self.cmd(
            'network private-endpoint-connection reject -g {resource_group} --resource-name {service_name} -n {endpoint_request2} --type Microsoft.ApiManagement/service',
            checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('network private-endpoint-connection show -g {resource_group} --resource-name {service_name} -n {endpoint_request2} --type Microsoft.ApiManagement/service', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('name', '{endpoint_request2}')
        ])

        self.cmd("az apim wait --updated --name {service_name} --resource-group {resource_group}")
        self.cmd("az apim wait --updated --name {service_name} --resource-group {resource_group}")

        # Remove endpoint
        self.cmd(
            'network private-endpoint-connection delete -g {resource_group} --resource-name {service_name} -n {endpoint_request} --type Microsoft.ApiManagement/service -y')


class NetworkPrivateLinkEventGridScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_plr')
    def test_private_link_resource_event_grid(self, resource_group):
        self.kwargs.update({
            'topic_name': self.create_random_name(prefix='cli', length=40),
            'domain_name': self.create_random_name(prefix='cli', length=40),
            'namespace_name': self.create_random_name(prefix='cli', length=40),
            'partner_registration_name': self.create_random_name(prefix='cli', length=40),
            'partner_namespace_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'rg': resource_group,
            'namespace_properties': '{ \\"location\\": \\"centraluseuap\\"}'
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

        namespace_id = self.cmd('az resource create -g {rg} -n {namespace_name} --resource-type Microsoft.EventGrid/namespaces --location {location} --properties "{namespace_properties}"',).get_output_in_json()['id']
        self.kwargs.update({
            'namespace_id': namespace_id
        })

        self.cmd(
            'network private-link-resource list --id {namespace_id}',
            checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'topic')])

        partner_registration_id = self.cmd('az eventgrid partner registration create --name {partner_registration_name} --resource-group {rg}',).get_output_in_json()['id']
        self.kwargs.update({
            'partner_registration_id': partner_registration_id
        })
        partner_namespace_id = self.cmd('az eventgrid partner namespace create --name {partner_namespace_name} --resource-group {rg} --partner-registration-id {partner_registration_id} --location {location}',).get_output_in_json()['id']
        self.kwargs.update({
            'partner_namespace_id': partner_namespace_id
        })

        self.cmd(
            'network private-link-resource list --id {partner_namespace_id}',
            checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'partnerNamespace')])


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

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', location='centraluseuap')
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', parameter_name='resource_group_2', location='centraluseuap')
    def test_private_endpoint_connection_event_grid_namespaces(self, resource_group, resource_group_2):
        self.kwargs.update({
            'resource_group_net': resource_group_2,
            'vnet_name': self.create_random_name(prefix='cli', length=20),
            'subnet_name': self.create_random_name(prefix='cli', length=20),
            'private_endpoint_name': self.create_random_name(prefix='cli', length=20),
            'connection_name': self.create_random_name(prefix='cli', length=20),
            'namespace_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'approval_description': 'You are approved!',
            'rejection_description': 'You are rejected!',
            'rg': resource_group,
            'namespace_properties': '{ \\"location\\": \\"centraluseuap\\"}'
        })

        self.cmd('network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        scope = self.cmd('resource create -g {rg} -n {namespace_name} --resource-type Microsoft.EventGrid/namespaces --properties "{namespace_properties}"', checks=[
            self.check('type', 'Microsoft.EventGrid/namespaces'),
            self.check('name', self.kwargs['namespace_name']),
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('sku.name', 'Standard'),
            self.check('properties.publicNetworkAccess', 'Enabled'),
        ]).get_output_in_json()['id']

        self.kwargs.update({
            'scope': scope,
        })

        # Create private endpoint
        self.cmd('network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids topic --connection-name {connection_name}').get_output_in_json()

        server_pec_id = self.cmd('resource show --name {namespace_name} --resource-group {rg} --resource-type Microsoft.EventGrid/namespaces').get_output_in_json()['properties']['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('network private-endpoint-connection list --resource-group {rg} --name {namespace_name} --type Microsoft.EventGrid/namespaces',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('network private-endpoint-connection show --resource-group {rg} --resource-name {namespace_name} --name {server_pec_name} --type Microsoft.EventGrid/namespaces')

        self.cmd('network private-endpoint-connection approve --resource-group {rg} --resource-name {namespace_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/namespaces --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])

        self.cmd('network private-endpoint-connection delete --resource-group {rg} --resource-name {namespace_name} --name {server_pec_name} --type Microsoft.EventGrid/namespaces -y')

        self.cmd('network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('resource delete --name {namespace_name} --resource-group {rg} --resource-type Microsoft.EventGrid/namespaces')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', location='centraluseuap')
    @ResourceGroupPreparer(name_prefix='cli_test_event_grid_pec', parameter_name='resource_group_2', location='centraluseuap')
    def test_private_endpoint_connection_event_grid_partner_namespaces(self, resource_group, resource_group_2):
        self.kwargs.update({
            'resource_group_net': resource_group_2,
            'vnet_name': self.create_random_name(prefix='cli', length=20),
            'subnet_name': self.create_random_name(prefix='cli', length=20),
            'private_endpoint_name': self.create_random_name(prefix='cli', length=20),
            'connection_name': self.create_random_name(prefix='cli', length=20),
            'partner_registration_name': self.create_random_name(prefix='cli', length=40),
            'partner_namespace_name': self.create_random_name(prefix='cli', length=40),
            'location': 'centraluseuap',
            'approval_description': 'You are approved!',
            'rejection_description': 'You are rejected!',
            'rg': resource_group
        })

        self.cmd('network vnet create --resource-group {resource_group_net} --location {location} --name {vnet_name} --address-prefix 10.0.0.0/16')
        self.cmd('network vnet subnet create --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --address-prefixes 10.0.0.0/24')
        self.cmd('network vnet subnet update --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name} --disable-private-endpoint-network-policies true')

        partner_registration_id = self.cmd('eventgrid partner registration create --name {partner_registration_name} --resource-group {rg}',).get_output_in_json()['id']
        self.kwargs.update({
            'partner_registration_id': partner_registration_id
        })

        scope = self.cmd('eventgrid partner namespace create --name {partner_namespace_name} --resource-group {rg} --partner-registration-id {partner_registration_id} --location {location}', checks=[
            self.check('type', 'Microsoft.EventGrid/partnerNamespaces'),
            self.check('name', self.kwargs['partner_namespace_name']),
            self.check('provisioningState', 'Succeeded'),
            self.check('publicNetworkAccess', 'Enabled'),
        ]).get_output_in_json()['id']

        self.kwargs.update({
            'scope': scope,
        })

        # Create private endpoint
        self.cmd('network private-endpoint create --resource-group {resource_group_net} --name {private_endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} --private-connection-resource-id {scope} --location {location} --group-ids partnerNamespace --connection-name {connection_name}')

        server_pec_id = self.cmd('eventgrid partner namespace show --name {partner_namespace_name} --resource-group {rg}').get_output_in_json()['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']
        self.kwargs.update({
            'server_pec_name': server_pec_name,
        })
        self.cmd('network private-endpoint-connection list --resource-group {rg} --name {partner_namespace_name} --type Microsoft.EventGrid/partnerNamespaces',
                 checks=[
                     self.check('length(@)', 1)
                 ])
        self.cmd('network private-endpoint-connection show --resource-group {rg} --resource-name {partner_namespace_name} --name {server_pec_name} --type Microsoft.EventGrid/partnerNamespaces')

        self.cmd('network private-endpoint-connection approve --resource-group {rg} --resource-name {partner_namespace_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/partnerNamespaces --description "{approval_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_description}')
                 ])
        self.cmd('network private-endpoint-connection reject --resource-group {rg} --resource-name {partner_namespace_name} '
                 '--name {server_pec_name} --type Microsoft.EventGrid/partnerNamespaces --description "{rejection_description}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_description}')
                 ])

        self.cmd('network private-endpoint-connection delete --resource-group {rg} --resource-name {partner_namespace_name} --name {server_pec_name} --type Microsoft.EventGrid/partnerNamespaces -y')

        self.cmd('network private-endpoint delete --resource-group {resource_group_net} --name {private_endpoint_name}')
        self.cmd('network vnet subnet delete --resource-group {resource_group_net} --vnet-name {vnet_name} --name {subnet_name}')
        self.cmd('network vnet delete --resource-group {resource_group_net} --name {vnet_name}')
        self.cmd('eventgrid partner namespace delete --name {partner_namespace_name} --resource-group {rg} -y')


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
                 '--enable-private-link '
                 '--priority 1001')

        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()

        self.assertEqual(show_appgw_data['name'], self.kwargs['appgw'])
        self.assertEqual(show_appgw_data['sku']['tier'], 'Standard_v2')
        # One default private link would be here
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations']), 1)
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations']), 1)
        # The frontendIpConfigurations must be associated with the same ID of private link configuration ID
        self.assertEqual(show_appgw_data['frontendIPConfigurations'][0]['privateLinkConfiguration']['id'],
                         show_appgw_data['privateLinkConfigurations'][0]['id'])
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['name'], 'PrivateLinkDefaultConfiguration')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['privateIPAllocationMethod'],
                         'Dynamic')
        self.assertNotIn("primary", show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0])

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
                 '--private-link-subnet-prefix 10.0.2.0/24 '
                 '--priority 1001')

        show_appgw_data = self.cmd('network application-gateway show -g {rg} -n {appgw}').get_output_in_json()

        self.assertEqual(show_appgw_data['name'], self.kwargs['appgw'])
        self.assertEqual(show_appgw_data['sku']['tier'], 'Standard_v2')
        # One default private link would be here
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations']), 1)
        self.assertEqual(len(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations']), 1)
        # The frontendIpConfigurations must be associated with the same ID of private link configuration ID
        self.assertEqual(show_appgw_data['frontendIPConfigurations'][0]['privateLinkConfiguration']['id'],
                         show_appgw_data['privateLinkConfigurations'][0]['id'])
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['name'], 'PrivateLinkDefaultConfiguration')
        self.assertEqual(show_appgw_data['privateLinkConfigurations'][0]['ipConfigurations'][0]['privateIPAllocationMethod'],
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
                 '--public-ip-address {appgw_public_ip} '
                 '--priority 1001')

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
                 '--http-listener privateHTTPListener '
                 '--priority 1002')

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

    @ResourceGroupPreparer(name_prefix="cli_test_private_link_ip_config_", location="westus")
    def test_private_link_ip_config(self):
        self.kwargs.update({
            "pip": self.create_random_name("public-ip-", 16),
            "ag": self.create_random_name("application-gateway-", 24),
            "pl": self.create_random_name("private-link-", 20),
            "subnet": self.create_random_name("subnet-", 12),
            "ip_config": self.create_random_name("ip-configuration-", 24),
        })
        self.cmd("network public-ip create -n {pip} -g {rg} --sku standard")
        self.cmd("network application-gateway create -n {ag} -g {rg} --public-ip-address {pip} --sku standard_v2 --priority 1001")
        self.cmd("network application-gateway private-link add -n {pl} -g {rg} --gateway-name {ag} --frontend-ip appGatewayFrontendIP --subnet {subnet} --subnet-prefix 10.0.4.0/24")

        self.cmd(
            "network application-gateway private-link ip-config add -n {ip_config} -g {rg} "
            "--gateway-name {ag} --private-link {pl} --primary true",
            checks=[
                self.check("name", "{ip_config}"),
                self.check("primary", True),
            ]
        )
        self.cmd(
            "network application-gateway private-link ip-config show -n {ip_config} -g {rg} "
            "--gateway-name {ag} --private-link {pl}",
            checks=[
                self.check("name", "{ip_config}"),
                self.check("privateIPAllocationMethod", "Dynamic"),
            ]
        )
        self.cmd(
            "network application-gateway private-link ip-config list -g {rg} --gateway-name {ag} --private-link {pl}",
            checks=[
                self.check("length(@)", 2),
                self.check("@[1].name", "{ip_config}"),
                self.check("@[1].primary", True),
            ]
        )
        self.cmd("network application-gateway private-link ip-config remove -n {ip_config} -g {rg} --gateway-name {ag} --private-link {pl} --yes")
        self.cmd(
            "network application-gateway private-link ip-config list -g {rg} --gateway-name {ag} --private-link {pl}",
            checks=[
                self.check("length(@)", 1),
                self.check("@[0].name", "PrivateLinkDefaultIPConfiguration"),
                self.check("@[0].privateIPAllocationMethod", "Dynamic"),
            ]
        )

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
        self.cmd('network public-ip create -g {rg} -n {appgw_public_ip} --sku basic')

        # Create a application gateway without enable --enable-private-link
        self.cmd('network application-gateway create -g {rg} -n {appgw} '
                 '--public-ip-address {appgw_public_ip} --priority 1001')

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
                      checks=self.check('type(@)', 'array')).get_output_in_json()
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

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_synapse_workspace", location="eastus")
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

    @ResourceGroupPreparer(name_prefix="test_private_endpoint_connection_sql_server", location="eastus")
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

        result = self.cmd('bot create -g {rg} -n {bot_name} --app-type MultiTenant --appid {app_id}').get_output_in_json()
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
    def __init__(self, method_name):
        super().__init__(
            method_name,
            recording_processors=[RedisCacheCredentialReplacer()]
        )

    @ResourceGroupPreparer(name_prefix='cli_test_acfr_plr')
    def test_private_link_resource_acfr(self, resource_group):
        self.kwargs.update({
            'cache_name': self.create_random_name('cli-test-acfr-plr', 28),
            'loc': 'eastus'
        })
        self.cmd('az redis create --location {loc} --name {cache_name} --resource-group {rg} --sku Basic --vm-size c0')

        self.cmd('network private-link-resource list --name {cache_name} -g {rg} --type Microsoft.Cache/Redis' , checks=[
            self.check('length(@)', 1)])

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


class NetworkPrivateLinkEnergyServicesScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_energyservices_pe', random_name_length=40, location="centraluseuap")
    def test_energyservices_private_endpoint(self, resource_group):

        # Currently create energy services resource not supported in OAK
        self.kwargs.update({
            'rg': resource_group,
            'resource_name': self.create_random_name('cli', 15),
            'resource_type': 'energyServices',
            'sub': self.get_subscription_id(),
            'namespace': 'Microsoft.OpenEnergyPlatform',
            'vnet': self.create_random_name('cli-energyservices-vnet-', 40),
            'subnet': self.create_random_name('cli-energyservices-subnet-', 40),
            'private_endpoint': self.create_random_name('cli-energyservices-pe-', 40),
            'private_endpoint_connection': self.create_random_name('cli-energyservices-pec-', 40),
            'location': 'centraluseuap',
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!',
            'body': '{\\"location\\":\\"centraluseuap\\",\\"properties\\":{\\"authAppId\\":\\"2f59abbc-7b40-4d0e-91b2-22ca3084bc84\\",\\"dataPartitionNames\\":[{\\"name\\":\\"dp1\\"}]},\\"tags\\":{\\"environment\\":\\"test\\",\\"program\\":\\"exploration\\"}}',
            'api_version': '2022-07-21-preview'
        })

        # Create energy services resource
        # This API only accepts the creation request, provisioning state of the resource has to be polled
        self.cmd('az rest --method "PUT" \
                --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/{namespace}/{resource_type}/{resource_name}?api-version={api_version}" \
                --body "{body}"')

        # check for resource provisioning state
        self.check_provisioning_state_for_energyservices_resource()

        # Get resource id for the instance
        self.kwargs['resource_id']= self.cmd(
            'az resource show --name {resource_name} -g {rg} --resource-type {resource_type} --namespace {namespace} --query id').output

        # Create virtual net and sub net
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')

        # Update sub net
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} --name {subnet} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources
        private_link_resources = self.cmd(
            'network private-link-resource list --id {resource_name} ').get_output_in_json()
        self.kwargs['group_id'] = private_link_resources[0]['properties']['groupId']

        # Create private endpoint
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {resource_id} --connection-name {private_endpoint_connection} '
            '--group-id {group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {resource_id}',
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

    def get_provisioning_state_for_energyservices_resource(self):
        # get provisioning state
        response = self.cmd('az rest --method "GET" \
                --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/{namespace}/{resource_type}/{resource_name}?api-version={api_version}"').get_output_in_json()

        return response['properties']['provisioningState']

    def check_provisioning_state_for_energyservices_resource(self):
        count = 0
        print("checking status of creation...........")
        state = self.get_provisioning_state_for_energyservices_resource()
        print(state)
        while state!="Succeeded":
            if state == "Failed":
                print("creation failed!")
                self.assertTrue(False)
            elif (count == 12):
                print("TimeOut after waiting for 120 mins!")
                self.assertTrue(False)
            print("instance not yet created. waiting for 10 more mins...")
            count+=1
            time.sleep(600) # Wait for 10 minutes
            state = self.get_provisioning_state_for_energyservices_resource()
        print("creation succeeded!")


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

class NetworkKubernetesConfigurationPrivateLinkScopesTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_kubernetesconfiguration_pe', random_name_length=40)
    def test_kubernetesconfiguration_private_endpoint(self, resource_group):
        self.kwargs.update({
            'vnet': self.create_random_name('cli-vnet-', 24),
            'scopename': self.create_random_name('clitestscopename', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'private_endpoint': self.create_random_name('cli-pe-', 24),
            'private_endpoint2': self.create_random_name('cli-pe-', 24),
            'private_endpoint_connection': self.create_random_name('cli-pec-', 24),
            'private_endpoint_connection2': self.create_random_name('cli-pec-', 24),
            'location': 'eastus2euap',
            'approve_desc': 'ApprovedByTest',
            'reject_desc': 'RejectedByTest',
            'rg': resource_group,
            'sub': self.get_subscription_id(),
            'body': '{\\"location\\":\\"eastus2euap\\",\\"properties\\":{\\"clusterResourceId\\":\\"non-existing-resource\\"\\}\\}'
        })


        # Test create Private Link Scope create
        self.cmd('az rest --method "PUT" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.KubernetesConfiguration/privateLinkScopes/{scopename}?api-version=2022-04-02-preview" \
                        --body "{body}"')

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {location} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test private link resource list
        pr = self.cmd('network private-link-resource list --name {scope} -g {rg} --type microsoft.KubernetesConfiguration/privateLinkScopes', checks=[
            self.check('length(@)', 1)
        ]).get_output_in_json()

        # Add an endpoint that gets auto approved
        self.kwargs['group_id'] = pr[0]['groupId']
        self.kwargs['scope_id'] = '/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.KubernetesConfiguration/privateLinkScopes/{scopename}'

        result = self.cmd('network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} --private-connection-resource-id {scope_id} '
        '--connection-name {private_endpoint_connection} --group-id {group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint_connection'].lower() in result['name'].lower())

        # Add an endpoint and approve it
        result = self.cmd('network private-endpoint create -g {rg} -n {private_endpoint2} --vnet-name {vnet} --subnet {subnet} --private-connection-resource-id {scope_id} '
        '--connection-name {private_endpoint_connection2} --group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint_connection2'].lower() in result['name'].lower())

        self.cmd('network private-endpoint-connection approve -g {rg} -n {private_endpoint_connection2} --resource-name {scope} --type Microsoft.KubernetesConfiguration/privateLinkScopes --description {approve_desc}',
        checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{approve_desc}')
        ])

        # Reject previous approved endpoint
        self.cmd('network private-endpoint-connection reject -g {rg} -n {private_endpoint_connection2} --resource-name {scope} --type Microsoft.KubernetesConfiguration/privateLinkScopes --description {reject_desc}',
        checks= [
            self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
            self.check('properties.privateLinkServiceConnectionState.description', '{reject_desc}')
        ])

        # List endpoints
        self.cmd('network private-endpoint-connection list -g {rg} --name {scope} --type Microsoft.KubernetesConfiguration/privateLinkScopes', checks=[
            self.check('length(@)', '2')
        ])
        # Remove endpoints
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {scope} -n {private_endpoint_connection2} --type Microsoft.KubernetesConfiguration/privateLinkScopes -y')
        time.sleep(30)
        self.cmd('network private-endpoint-connection list -g {rg} --name {scope} --type Microsoft.KubernetesConfiguration/privateLinkScopes', checks=[
            self.check('length(@)', '1')
        ])
        # Show endpoint
        self.cmd('az network private-endpoint-connection show -g {rg} --type Microsoft.KubernetesConfiguration/privateLinkScopes --resource-name {scope} -n {private_endpoint_connection}', checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', 'Auto-Approved')
        ])
        self.cmd('network private-endpoint-connection delete -g {rg} --resource-name {scope} -n {private_endpoint_connection} --type Microsoft.KubernetesConfiguration/privateLinkScopes -y')



class NetworkPrivateLinkManagedGrafanaScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='test_grafana_private_endpoint_', random_name_length=40)
    def test_private_endpoint_connection_grafana(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'service_name': self.create_random_name('cli-test-srv-', 22),
            'vnet_name': self.create_random_name('cli-test-vnet-', 22),
            'subnet_name': self.create_random_name('cli-test-subnet-', 22),
            'endpoint_name': self.create_random_name('cli-test-pe-', 22),
            'endpoint_conn_name': self.create_random_name('cli-test-pec-', 22),
            'location': "eastus2euap",
        })

        # Install extension for Azure Managed Grafana Service
        self.cmd('extension add -n amg')

        # Create Azure Managed Grafana Service
        service_created = self.cmd(
            'grafana create -g {resource_group} -n {service_name} --l {location}').get_output_in_json()
        self.kwargs['service_id'] = service_created['id']

        # Check private link resource is available
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

        # Create private endpoint
        result = self.cmd(
            'network private-endpoint create -g {resource_group} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--connection-name {endpoint_conn_name} --private-connection-resource-id {service_id} '
            '--group-id Gateway').get_output_in_json()
        self.assertTrue(
            self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd(
            'network private-endpoint-connection list -g {resource_group} -n {service_name} --type Microsoft.Dashboard/grafana',
            checks=[self.check('length(@)', 1), ]).get_output_in_json()
        self.kwargs.update({
            "endpoint_request": result[0]['name'],
            "pec_id": result[0]['id'],
            "pec_name": result[0]['id'].split('/')[-1]
        })

        # Show the private endpoint connection
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))

        self.cmd('az network private-endpoint-connection show --resource-name {service_name} -n {pec_name} -g {resource_group} --type Microsoft.Dashboard/grafana',
                 checks=self.check('id', '{pec_id}'))

        # Remove private endpoint
        self.cmd(
            'network private-endpoint-connection delete -g {resource_group} --resource-name {service_name} -n {endpoint_request} --type Microsoft.Dashboard/grafana -y')

class NetworkPrivateLinkDeviceUpdateScenarioTest(ScenarioTest):
    @live_only()
    @AllowLargeResponse(4096)
    @ResourceGroupPreparer(name_prefix='test_deviceupdate_private_endpoint', random_name_length=40, location="westus2")
    def test_private_link_endpoint_deviceupdate(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'deviceupdate_name': self.create_random_name('cli-test-adu-', 24),
            'vnet_name': self.create_random_name('cli-test-adu-pe-vnet', 40),
            'subnet_name': self.create_random_name('cli-test-adu-pe-subnet', 40),
            'endpoint_name': self.create_random_name('cli-test-adu-pe-', 40),
            'endpoint_connection_name': self.create_random_name('cli-test-adu-pec-', 40),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })

        # Device Update is an IoT extension
        self.cmd('extension add --name azure-iot')

        # Create device update account
        deviceupdate = self.cmd(
            'iot du account create --account {deviceupdate_name} --resource-group {rg}').get_output_in_json()
        self.kwargs['deviceupdate_id'] = deviceupdate['id']

        # Create a vnet and subnet for private endpoint connection
        self.cmd('network vnet create -g {rg} -n {vnet_name} --subnet-name {subnet_name}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet_name} --name {subnet_name} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources
        deviceupdate_private_link_resources = self.cmd(
            'network private-link-resource list --id {deviceupdate_id}').get_output_in_json()
        self.kwargs['group_id'] = deviceupdate_private_link_resources[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--private-connection-resource-id {deviceupdate_id} --connection-name {endpoint_connection_name} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {deviceupdate_id}',
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
        time.sleep(90)
        self.cmd('network private-endpoint-connection show --id {private-endpoint-connection-id}',
                 expect_failure=True)

class NetworkPrivateLinkDesktopVirtualizationScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_desktopvirtual_pe', random_name_length=40, location ="westus2")
    def test_desktopvirtualization_private_endpoint(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'location': "westus2",
            'vnet': self.create_random_name('cli-vnet-dv', 20),
            'subnet': self.create_random_name('cli-subnet-dv', 20),
            'hostpoolName': self.create_random_name('cli-test-dv-hp', 20),
            'workspaceName': self.create_random_name('cli-test-dv-ws', 20),
            'hostpoolType': "Pooled",
            'loadBalancerType': "BreadthFirst",
            'preferredAppGroupType': "Desktop",
            'hp_pe1_name': self.create_random_name('cli-test-dv-hp-pe1', 20),
            'hp_pec1_name': self.create_random_name('cli-test-dv-hp-pec1', 20),
            'hp_pe2_name': self.create_random_name('cli-test-dv-hp-pe2', 20),
            'hp_pec2_name': self.create_random_name('cli-test-dv-hp-pec2', 20),
            'ws_pe1_name': self.create_random_name('cli-test-dv-ws-pe1', 20),
            'ws_pec1_name': self.create_random_name('cli-test-dv-ws-pec1', 20),
            'ws_pe2_name': self.create_random_name('cli-test-dv-ws-pe2', 20),
            'ws_pec2_name': self.create_random_name('cli-test-dv-ws-pec2', 20),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!'
        })

        # DesktopVirtualzation is an extension
        self.cmd('extension add --name desktopvirtualization')

        #Create hostpool and workspace
        hostpool = self.cmd('desktopvirtualization hostpool create --name {hostpoolName} --resource-group {rg} --location {location} '
        '--host-pool-type {hostpoolType} --load-balancer-type {loadBalancerType} --preferred-app-group-type {preferredAppGroupType}').get_output_in_json()
        self.kwargs['hostpool_id'] = hostpool['id']

        workspace = self.cmd('desktopvirtualization workspace create --name {workspaceName} --resource-group {rg} --location {location}').get_output_in_json()
        self.kwargs['workspace_id'] = workspace['id']

        # Create vnet and subnet for private endpoint connection
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.cmd('network vnet subnet update -g {rg} --vnet-name {vnet} --name {subnet} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # List hostpool private link resources
        dv_hostpool_private_link_resources = self.cmd(
            'network private-link-resource list --id {hostpool_id}').get_output_in_json()
        self.kwargs['hp_group_id'] = dv_hostpool_private_link_resources[0]['properties']['groupId']

        # List workspace private link resources
        dv_workspace_private_link_resources = self.cmd(
            'network private-link-resource list --id {workspace_id}').get_output_in_json()
        self.kwargs['ws_group_id'] = dv_workspace_private_link_resources[0]['properties']['groupId']

        # Create auto-approved private endpoint for hostpool
        peHostpoolCreation = self.cmd(
            'network private-endpoint create -g {rg} -n {hp_pe1_name} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {hostpool_id} --connection-name {hp_pec1_name} '
            '--group-id {hp_group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['hp_pe1_name'].lower() in peHostpoolCreation['name'].lower())

        # Create auto-approved private endpoint for workspace
        peWorkspaceCreation = self.cmd(
            'network private-endpoint create -g {rg} -n {ws_pe1_name} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {workspace_id} --connection-name {ws_pec1_name} '
            '--group-id {ws_group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['ws_pe1_name'].lower() in peWorkspaceCreation['name'].lower())

        # Get private endpoint connection for hostpool
        pecsHostpool = self.cmd('network private-endpoint-connection list --id {hostpool_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Approved'),
                                                ]).get_output_in_json()
        self.kwargs['pecsHostpool-id'] = pecsHostpool[0]['id']

        # Get private endpoint connection for workpace
        pecsWorkspace = self.cmd('network private-endpoint-connection list --id {workspace_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Approved'),
                                                ]).get_output_in_json()

        self.kwargs['pecsWorkspace-id'] = pecsWorkspace[0]['id']

        # Reject private endpoint connection on hostpool using resource id
        self.cmd(
            'network private-endpoint-connection reject --id {pecsHostpool-id}'
            ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        # Reject private endpoint connection on workspace using resource id
        self.cmd(
            'network private-endpoint-connection reject --id {pecsWorkspace-id}'
            ' --description {reject_description_msg}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
            ])

        # Manually create an endpoint for hostpool and approve it using resourceGroup/name/type
        pe2HostpoolCreation = self.cmd(
            'network private-endpoint create -g {rg} -n {hp_pe2_name} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {hostpool_id} --connection-name {hp_pec2_name} '
            '--group-id {hp_group_id}').get_output_in_json()
        self.assertTrue(self.kwargs['hp_pe2_name'].lower() in pe2HostpoolCreation['name'].lower())

        self.cmd('network private-endpoint-connection approve -g {rg} -n {hp_pec2_name} --type Microsoft.DesktopVirtualization/hostpools --description {approve_description_msg}',
        checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{approve_description_msg}')
        ])

        # Manually create an endpoint for workspace and approve it using resourceGroup/name/type
        pe2WorkspaceCreation = self.cmd(
            'network private-endpoint create -g {rg} -n {ws_pe2_name} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {workspace_id} --connection-name {ws_pec2_name} '
            '--group-id {ws_group_id} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['ws_pe2_name'].lower() in pe2WorkspaceCreation['name'].lower())

        self.cmd('network private-endpoint-connection approve -g {rg} -n {ws_pec2_name} --type Microsoft.DesktopVirtualization/workspaces --description {approve_description_msg}',
        checks=[
            self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
            self.check('properties.privateLinkServiceConnectionState.description', '{approve_description_msg}')
        ])

        # Delete the autoapproved private endpoint connections for hostpool and workspace using resource id
        self.cmd('az network private-endpoint-connection delete --id {pecHostpool-id} -y')
        self.cmd('az network private-endpoint-connection delete --id {pecsWorkspace-id} -y')
        import time
        time.sleep(90)
        self.cmd('az network private-endpoint-connection list --id {pecHostpool-id}', checks=[
            self.check('length(@)', '1'),
        ])
        self.cmd('az network private-endpoint-connection list --id {pecsWorkspace-id}', checks=[
            self.check('length(@)', '1'),
        ])

class NetworkPrivateLinkMLRegistryScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='test_ml_registries_pe_', random_name_length=40, location="eastus2euap")
    def test_private_link_endpoint_ml_registry(self, resource_group):
        self.kwargs.update({
            'resource_group_name': resource_group,
            'subscription_id': self.get_subscription_id(),
            'registry_name': self.create_random_name('registry-', 20),
            'vnet_name': self.create_random_name('vnet-', 20),
            'subnet_name': self.create_random_name('subnet-', 20),
            'endpoint_name': self.create_random_name('pe-', 20),
            'endpoint_connection_name': self.create_random_name('pec-', 20),
            'approve_description_msg': 'Approved!',
            'reject_description_msg': 'Rejected!',
            'location': 'eastus2euap',
        })

        self.cmd('extension add --name ml')

        # Create registry
        with open('registry.yml', 'w') as the_file:
            the_file.write(f'name: {self.kwargs["registry_name"]}\nlocation: {self.kwargs["location"]}\nreplication_locations:\n  - location: {self.kwargs["location"]}')

        self.cmd('ml registry create --subscription {subscription_id} --resource-group {resource_group_name} --file registry.yml')
        registryJson = self.cmd('ml registry show --subscription {subscription_id} --resource-group {resource_group_name} --name {registry_name}').get_output_in_json()
        os.remove('registry.yml')
        self.kwargs['registry_resource_id'] = registryJson['id']

        # Create a vnet and subnet for private endpoint connection
        self.cmd('network vnet create -g {resource_group_name} -n {vnet_name} --subnet-name {subnet_name} --location {location}')
        self.cmd('network vnet subnet update -g {resource_group_name} --vnet-name {vnet_name} --name {subnet_name} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test list private link resources
        registry_private_link_resources = self.cmd(
            'network private-link-resource list --id {registry_resource_id}').get_output_in_json()
        self.kwargs['group_id'] = registry_private_link_resources[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {resource_group_name} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
            '--private-connection-resource-id {registry_resource_id} --connection-name {endpoint_connection_name} '
            '--group-id {group_id} --location {location} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in private_endpoint['name'].lower())

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {registry_resource_id}',
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
        time.sleep(90)
        self.cmd('network private-endpoint-connection show --id {private-endpoint-connection-id}',
                 expect_failure=True)

class NetworkPrivateLinkMicrosoftMonitorAccountsRegistryScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='test_monitor_accounts_registries_pe_', random_name_length=40, location="eastus2euap")
    def test_private_link_endpoint_monitor_accounts_registry(self, resource_group):
        self.kwargs.update({
            'vnet': self.create_random_name('cli-vnet-', 24),
            'account_name': self.create_random_name('test-amw-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'private_endpoint': self.create_random_name('cli-pe-', 24),
            'private_endpoint2': self.create_random_name('cli-pe-', 24),
            'private_endpoint_connection': self.create_random_name('cli-pec-', 24),
            'private_endpoint_connection2': self.create_random_name('cli-pec-', 24),
            'location': 'eastus2euap',
            'approve_desc': 'ApprovedByTest',
            'reject_desc': 'RejectedByTest',
            'rg': resource_group,
            'sub': self.get_subscription_id(),
            'body': '{\\"location\\":\\"eastus2euap\\"}'
        })

        # Test create Azure monitor workspace create
        macAccount = self.cmd('az rest --method "PUT" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.Monitor/accounts/{account_name}?api-version=2021-06-03-preview" \
                        --body "{body}"').get_output_in_json()
        self.kwargs['account_id'] = macAccount['id']
        print(macAccount['id'])

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {location} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Test private link resource list
        pr = self.cmd('network private-link-resource list --name {account_name} -g {rg} --type microsoft.monitor/accounts', checks=[
            self.check('length(@)', 1)
        ]).get_output_in_json()
        self.kwargs['group_id'] = pr[0]['properties']['groupId']

        # Create private endpoint with manual request approval
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {private_endpoint2} --vnet-name {vnet} --subnet {subnet} '
            '--private-connection-resource-id {account_id} --connection-name {private_endpoint_connection2} '
            '--group-id {group_id} --location {location} --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['private_endpoint2'].lower() in private_endpoint['name'].lower())
        print("PrivateEndpt created for manual approval", private_endpoint)

        # Test get private endpoint connection
        private_endpoint_connections = self.cmd('network private-endpoint-connection list --id {account_id}',
                                                checks=[
                                                    self.check(
                                                        '@[0].properties.privateLinkServiceConnectionState.status',
                                                        'Pending'),
                                                ]).get_output_in_json()
        self.kwargs['private_endpoint_connection2_id'] = private_endpoint_connections[0]['id']

        # Test approve private endpoint connection
        self.cmd(
            'network private-endpoint-connection approve --id {private_endpoint_connection2_id} '
            '--description {approve_desc}', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])

        # Test reject previous approved private endpoint connnection
        self.cmd('network private-endpoint-connection reject --id {private_endpoint_connection2_id}'
                 ' --description {reject_desc}', checks=[
                  self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
        ])

        # Test delete private endpoint connection
        self.cmd('network private-endpoint-connection delete --id {private_endpoint_connection2_id} --yes')
        import time
        time.sleep(90)
        self.cmd('network private-endpoint-connection show --id {private_endpoint_connection2_id}',
                 expect_failure=True)

        # Add an endpoint that gets auto approved
        result = self.cmd('network private-endpoint create -g {rg} -n {private_endpoint} --vnet-name {vnet} --subnet {subnet} --private-connection-resource-id {account_id} '
        '--connection-name {private_endpoint_connection} --group-id {group_id}').get_output_in_json()
        print("AutoApprove Private endpoint", result)
        print("----break-----")
        self.assertTrue(self.kwargs['private_endpoint'].lower() in result['name'].lower())
        self.assertTrue("Approved" in result['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'])

if __name__ == '__main__':
    unittest.main()

class NetworkPrivateLinkMysqlFlexibleServerScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westus2')
    def test_private_link_resource_mysql_flexible_server(self, resource_group):
        #At very first, we define some params
        self.kwargs.update({
            'server_name': self.create_random_name(prefix='cli', length=40),
            'rg': resource_group
        })

        #First of all, we need to create a flexible server
        result = self.cmd('mysql flexible-server create -g {rg} --name {server_name}  --public-access none').get_output_in_json()
        self.kwargs['flexible_sever_id'] = result['id']

        #Secondly, we should check private-link-resource list
        self.cmd('network private-link-resource list --id {flexible_sever_id}', checks=[
            self.check('length(@)', 1),
        ])

    @ResourceGroupPreparer(location='centraluseuap')
    def test_private_endpoint_connection_mysql_flexible_server(self, resource_group):
        self.kwargs.update({
            'resource_group': resource_group,
            'server_name': self.create_random_name('mysql-privatelink-server', 40),
            'plan_name': self.create_random_name('mysql-privatelink-asp', 40),
            'vnet_name': self.create_random_name('mysql-privatelink-vnet', 40),
            'subnet_name': self.create_random_name('mysql-privatelink-subnet', 40),
            'endpoint_name': self.create_random_name('mysql-privatelink-endpoint', 40),
            'endpoint_conn_name': self.create_random_name('mysql-privatelink-endpointconn', 40),
            'second_endpoint_name': self.create_random_name('mysql-privatelink-endpoint2', 40),
            'second_endpoint_conn_name': self.create_random_name('mysql-privatelink-endpointconn2', 40),
            'description_msg': 'somedescription'
        })

        #Prepare Network
        self.cmd('network vnet create -n {vnet_name} -g {resource_group} --subnet-name {subnet_name}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet_name} --vnet-name {vnet_name} -g {resource_group} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        #Create MySQL Server
        result = self.cmd('mysql flexible-server create -g {rg} --name {server_name}  --public-access none').get_output_in_json()
        self.kwargs['flexible_sever_id'] = result['id']

        #Create Endpoint
        result = self.cmd('network private-endpoint create -g {resource_group} -n {endpoint_name} --vnet-name {vnet_name} --subnet {subnet_name} '
                          '--connection-name {endpoint_conn_name} --private-connection-resource-id {flexible_sever_id} '
                          '--group-id mysqlServer --manual-request').get_output_in_json()
        self.assertTrue(self.kwargs['endpoint_name'].lower() in result['name'].lower())

        result = self.cmd('network private-endpoint-connection list -g {resource_group} -n {server_name} --type Microsoft.DBforMySQL/flexibleServers', checks=[
            self.check('length(@)', 1),
        ]).get_output_in_json()
        self.kwargs['private_endpoint_connection_id'] = result[0]['id']

        self.cmd('network private-endpoint-connection approve --id {private_endpoint_connection_id} --description Approved',
                 checks=[self.check('properties.privateLinkServiceConnectionState.status', 'Approved')])

        #Remove Endpoint
        self.cmd('network private-endpoint-connection delete --id {private_endpoint_connection_id} -y')

class NetworkPrivateLinkCloudHsmClustersScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_chsm_plr_rg')
    def test_chsm_private_link_resource(self, resource_group):
        # Define Params
        self.kwargs.update({
            'chsm_name': self.create_random_name('cli-test-chsm-plr-', 24),
            'loc': 'ukwest',
            'rg': resource_group,
            'type': 'Microsoft.HardwareSecurityModules/cloudHsmClusters',
            'properties': '{ \\"sku\\": { \\"family\\": \\"B\\", \\"name\\": \\"Standard_B1\\" }, \\"location\\": \\"ukwest\\", \\"properties\\": { }, \\"tags\\": { \\"UseMockHfc\\": \\"true\\" } }'
        })

        # Create CHSM Resource
        self.cmd('resource create -g {rg} -n {chsm_name} --resource-type {type} --location {loc} --is-full-object --properties "{properties}"')

        # Show resource was created
        self.cmd('network private-link-resource list '
                 '--name {chsm_name} '
                 '-g {rg} '
                 '--type {type}',
                 checks=self.check('@[0].properties.groupId', 'cloudhsm'))
        self.cmd('resource delete --name {chsm_name} -g {rg} --resource-type {type}')

    @ResourceGroupPreparer(name_prefix='cli_test_chsm_pe')
    def test_chsm_private_endpoint_connection(self, resource_group):
        # Define Params
        self.kwargs.update({
            'chsm_name': self.create_random_name('cli-test-chsm-pe-', 24),
            'loc': 'ukwest',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'rg': resource_group,
            'type': 'Microsoft.HardwareSecurityModules/cloudHsmClusters',
            'properties': '{\\"sku\\": { \\"family\\": \\"B\\", \\"name\\": \\"Standard_B1\\" }, \\"location\\": \\"ukwest\\", \\"properties\\": { }, \\"tags\\": { \\"UseMockHfc\\": \\"true\\" } }'
        })

        # Prepare chsm and network
        hsm = self.cmd('resource create -g {rg} -n {chsm_name} --resource-type {type} --location {loc} --is-full-object --properties "{properties}"').get_output_in_json()
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
                      '--group-id cloudHsm').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']

        # Show the private endpoint connection
        result = self.cmd('network private-endpoint-connection list --name {chsm_name} -g {rg} --type {type}',
                          checks=self.check('length(@)', 1)).get_output_in_json()
        print(result)
        self.kwargs['hsm_pe_id'] = result[0]['id']

        self.cmd('network private-endpoint-connection show '
                 '--id {hsm_pe_id}',
                 checks=self.check('id', '{hsm_pe_id}'))
        self.kwargs['hsm_pe_name'] = self.kwargs['hsm_pe_id'].split('/')[-1]
        self.cmd('network private-endpoint-connection show  '
                 '--resource-name {chsm_name} '
                 '-g {rg} '
                 '--name {hsm_pe_name} '
                 '--type Microsoft.HardwareSecurityModules/cloudHsmClusters',
                 checks=self.check('name', '{hsm_pe_name}'))

        # Test approval/rejection
        self.kwargs.update({
            'approval_desc': 'You are approved!',
            'rejection_desc': 'You are rejected!'
        })

        self.cmd('network private-endpoint-connection approve '
                 '--resource-name {chsm_name} '
                 '--name {hsm_pe_name} '
                 '-g {rg} '
                 '--type Microsoft.HardwareSecurityModules/cloudHsmClusters '
                 '--description "{approval_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{approval_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {hsm_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded', False))

        self.cmd('network private-endpoint-connection reject '
                 '--id {hsm_pe_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('properties.privateLinkServiceConnectionState.description', '{rejection_desc}')
                 ])

        self.cmd('network private-endpoint-connection show --id {hsm_pe_id}',
                 checks=self.check('properties.provisioningState', 'Succeeded', False))

        self.cmd('network private-endpoint-connection list --id {hsm_id}',
                 checks=self.check('length(@)', 1))

        self.cmd('network private-endpoint-connection delete --id {hsm_pe_id} -y')

        # clear resources
        self.cmd('network private-endpoint delete -g {rg} -n {pe}')
        self.cmd('az resource delete --name {chsm_name} -g {rg} --resource-type {type}')

class NetworkPrivateLinkCosmosDBPostgresScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_pg')
    def test_private_link_resource_cosmosdb_postgres(self, resource_group):
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'westus',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
        })

        self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count 0 '
                '--coordinator-storage {storage} '
                '--administrator-login-password {pass} '
                )

        self.cmd('az cosmosdb postgres cluster wait --created -n {cluster_name} -g {rg}')

        self.cmd('az network private-link-resource list --name {cluster_name} --resource-group {rg} --type Microsoft.DBforPostgreSQL/serverGroupsv2',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'coordinator')])


    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_pg', random_name_length=30)
    def test_private_endpoint_connection_cosmosdb_postgres(self, resource_group):
        from azure.mgmt.core.tools import resource_id
        namespace = 'Microsoft.DBforPostgreSQL'
        instance_type = 'serverGroupsv2'
        resource_name = self.create_random_name(prefix='cli', length=10)
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=instance_type,
            name=resource_name,
        )
        self.kwargs.update({
            'cluster_name': resource_name,
            'target_resource_id': target_resource_id,
            'loc': 'westus',
            'storage': 131072,
            'pass': 'aBcD1234!@#$',
            'resource_type': 'Microsoft.DBforPostgreSQL/serverGroupsv2',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })

        cluster = self.cmd('az cosmosdb postgres cluster create '
                '--name {cluster_name} -g {rg} -l {loc} --coordinator-v-cores 4 '
                '--coordinator-server-edition "GeneralPurpose" --node-count 0 '
                '--coordinator-storage {storage} '
                '--administrator-login-password {pass} '
                ).get_output_in_json()
        self.kwargs['cluster_id'] = cluster['id']

        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        target_private_link_resource = self.cmd('az network private-link-resource list --name {cluster_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            'group_id': target_private_link_resource[0]['properties']['groupId']
        })
        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} '
            '--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        list_private_endpoint_conn = self.cmd('az network private-endpoint-connection list --name {cluster_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })

        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('az network private-endpoint-connection show --resource-name {cluster_name} -n {pec_name} -g {rg} --type {resource_type}')

        self.cmd(
            "az network private-endpoint-connection show --resource-name {cluster_name} -n {pec_name} -g {rg} --type {resource_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Approve / reject private endpoint
        self.kwargs.update({
            'approval_desc': 'Approved.',
            'rejection_desc': 'Rejected.'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {cluster_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd('az network private-endpoint-connection list --name {cluster_name} --resource-group {rg} --type {resource_type}', checks=[
            self.check('length(@)', 1)
        ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')


class NetworkPrivateLinkElasticSANScenarioTest(ScenarioTest):
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_elastic_san', location='eastus2euap')
    def test_private_link_resource_elasticsan(self):
        self.kwargs.update({
            "san_name": self.create_random_name('elastic-san', 24),
            "vg_name": self.create_random_name('volume-group', 24),
            "volume_name": self.create_random_name('volume', 24),
            "loc": "eastus2euap"
        })
        # self.cmd('extension add -n elastic-san')
        self.cmd('az elastic-san create -n {san_name} -g {rg} --tags {{key1810:aaaa}} -l {loc} '
                 '--base-size-tib 23 --extended-capacity-size-tib 14 '
                 '--sku {{name:Premium_LRS,tier:Premium}}')
        self.cmd('az elastic-san volume-group create -e {san_name} -n {vg_name} -g {rg} '
                 '--encryption EncryptionAtRestWithPlatformKey --protocol-type Iscsi')
        self.cmd('az elastic-san volume create -g {rg} -e {san_name} -v {vg_name} -n {volume_name} --size-gib 2')

        self.cmd('az network private-link-resource list --name {san_name} --resource-group {rg} '
                 '--type Microsoft.ElasticSan/elasticSans',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', self.kwargs.get('vg_name'))])
        self.cmd('az elastic-san delete -g {rg} -n {san_name} -y')

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_elastic_san', random_name_length=30, location='eastus2euap')
    def test_private_endpoint_connection_elasticsan(self, resource_group):
        from azure.mgmt.core.tools import resource_id
        namespace = 'Microsoft.ElasticSan'
        instance_type = 'elasticSans'
        resource_name = self.create_random_name(prefix='cli', length=10)
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=instance_type,
            name=resource_name,
        )
        self.kwargs.update({
            'san_name': resource_name,
            "vg_name": self.create_random_name('volume-group', 24),
            "volume_name": self.create_random_name('volume', 24),
            'target_resource_id': target_resource_id,
            'loc': 'eastus2euap',
            'resource_type': 'Microsoft.ElasticSan/elasticSans',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24)
        })
        # self.cmd('extension add -n elastic-san')

        san = self.cmd('az elastic-san create -n {san_name} -g {rg} --tags {{key1810:aaaa}} -l {loc} '
                       '--base-size-tib 23 --extended-capacity-size-tib 14 '
                       '--sku {{name:Premium_LRS,tier:Premium}}').get_output_in_json()
        self.kwargs['san_id'] = san['id']

        subnet_id = self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                             checks=self.check('length(newVNet.subnets)', 1)).get_output_in_json()["newVNet"]["subnets"][0]["id"]
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        self.kwargs.update({"subnet_id": subnet_id})
        self.cmd('az elastic-san volume-group create -e {san_name} -n {vg_name} -g {rg} '
                 '--encryption EncryptionAtRestWithPlatformKey --protocol-type Iscsi')

        self.cmd('az elastic-san volume create -g {rg} -e {san_name} -v {vg_name} -n {volume_name} --size-gib 2')

        target_private_link_resource = self.cmd(
            'az network private-link-resource list --name {san_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            'group_id': target_private_link_resource[0]['properties']['groupId']
        })
        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} '
            '--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        list_private_endpoint_conn = self.cmd(
            'az network private-endpoint-connection list --name {san_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })

        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd(
            'az network private-endpoint-connection show --resource-name {san_name} -n {pec_name} -g {rg} --type {resource_type}')

        self.cmd(
            "az network private-endpoint-connection show --resource-name {san_name} -n {pec_name} -g {rg} --type {resource_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Approve / reject private endpoint
        self.kwargs.update({
            'approval_desc': 'Approved.',
            'rejection_desc': 'Rejected.'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {san_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd(
            'az network private-endpoint-connection list --name {san_name} --resource-group {rg} --type {resource_type}',
            checks=[
                self.check('length(@)', 1)
            ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')
    
class NetworkPrivateLinkMongoClustersTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongo_cl', location='eastus2euap')
    def test_private_link_resource_cosmosdb_mongo_clusters(self, resource_group):
        secret1 = "mongo"
        secret2 = "Administrator1"
        self.kwargs.update({
            'cluster_name': self.create_random_name(prefix='cli', length=10),
            'loc': 'eastus2euap',
            'sub': self.get_subscription_id(),
            'namespace': 'Microsoft.DocumentDB',
            'resource_type': 'mongoClusters',
            'api_version': '2023-03-01-preview',
            'body': f"""{{\\"location\\":\\"eastus2euap\\",\\"properties\\":{{\\"nodeGroupSpecs\\":[{{\\"kind\\":\\"Shard\\",\\"sku\\":\\"M30\\",\\"diskSizeGB\\":128,\\"nodeCount\\":1,\\"enableHa\\":false}}],\\"administratorLogin\\":\\"{secret1}\\",\\"administratorLoginPassword\\":\\"{secret2}\\"}}}}"""
        })

        self.cmd('az rest --method "PUT" \
                 --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/{namespace}/{resource_type}/{cluster_name}?api-version={api_version}" \
                 --body "{body}"')

        # check for resource provisioning state
        self.check_provisioning_state_for_mongocluster_resource()
        self.cmd('az network private-link-resource list --name {cluster_name} --resource-group {rg} --type Microsoft.DocumentDB/mongoClusters',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'MongoCluster')])

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_mongo_cl', random_name_length=30, location='eastus2euap')
    def test_private_endpoint_connection_cosmosdb_mongo_clusters(self, resource_group):
        from azure.mgmt.core.tools import resource_id
        namespace = 'Microsoft.DocumentDB'
        resource_type = 'mongoClusters'
        secret1 = "mongo"
        secret2 = "Administrator1"
        resource_name = self.create_random_name(prefix='cli', length=10)
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=resource_type,
            name=resource_name,
        )
        self.kwargs.update({
            'cluster_name': resource_name,
            'target_resource_id': target_resource_id,
            'loc': 'eastus2euap',
            'sub': self.get_subscription_id(),
            'namespace': namespace,
            'resource_type': resource_type,
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'api_version': '2023-03-01-preview',
            'body': f"""{{\\"location\\":\\"eastus2euap\\",\\"properties\\":{{\\"nodeGroupSpecs\\":[{{\\"kind\\":\\"Shard\\",\\"sku\\":\\"M30\\",\\"diskSizeGB\\":128,\\"nodeCount\\":1,\\"enableHa\\":false}}],\\"administratorLogin\\":\\"{secret1}\\",\\"administratorLoginPassword\\":\\"{secret2}\\"}}}}"""
        })

        cluster = self.cmd('az rest --method "PUT" \
                 --url "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}/providers/{namespace}/{resource_type}/{cluster_name}?api-version={api_version}" \
                 --body "{body}"').get_output_in_json()

        # check for resource provisioning state
        self.check_provisioning_state_for_mongocluster_resource()
        self.kwargs['cluster_id'] = cluster['id']
        
        self.cmd('az network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))
        
        target_private_link_resource = self.cmd('az network private-link-resource list --name {cluster_name} --resource-group {rg} --type {namespace}/{resource_type}').get_output_in_json()
        self.kwargs.update({
            'group_id': target_private_link_resource[0]['properties']['groupId']
        })
        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at cosmos db side
        list_private_endpoint_conn = self.cmd('az network private-endpoint-connection list --name {cluster_name} --resource-group {rg} --type {namespace}/{resource_type}').get_output_in_json()
        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })

        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('az network private-endpoint-connection show --resource-name {cluster_name} -n {pec_name} -g {rg} --type {namespace}/{resource_type}')

        self.cmd(
            "az network private-endpoint-connection show --resource-name {cluster_name} -n {pec_name} -g {rg} --type {namespace}/{resource_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Approve / reject private endpoint
        self.kwargs.update({
            'approval_desc': 'Approved.',
            'rejection_desc': 'Rejected.'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {cluster_name} --resource-group {rg} --name {pec_name} --type {namespace}/{resource_type} '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd('az network private-endpoint-connection list --name {cluster_name} --resource-group {rg} --type {namespace}/{resource_type}', checks=[
            self.check('length(@)', 1)
        ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')

    def get_provisioning_state_for_mongocluster_resource(self):
        # get provisioning state
        response = self.cmd('az rest --method "GET" \
                --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/{namespace}/{resource_type}/{cluster_name}?api-version={api_version}"').get_output_in_json()

        return response['properties']['provisioningState']

    def check_provisioning_state_for_mongocluster_resource(self):
        count = 0
        print("checking status of creation...........")
        state = self.get_provisioning_state_for_mongocluster_resource()
        print(state)
        while state!="Succeeded":
            if state == "Failed":
                print("creation failed!")
                self.assertTrue(False)
            elif (count == 12):
                print("TimeOut after waiting for 120 mins!")
                self.assertTrue(False)
            print("instance not yet created. waiting for 10 more mins...")
            count+=1
            time.sleep(600) # Wait for 10 minutes
            state = self.get_provisioning_state_for_mongocluster_resource()
        print("creation succeeded!")


class NetworkPrivateLinkPostgreSQLFlexibleServerScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_fspg', random_name_length=18, location='eastus2euap')
    def test_private_link_resource_postgres_flexible_server(self, resource_group):
        password = "aBcD1234!@#$"
        username = "admin123"
        self.kwargs.update({
            'server_name': self.create_random_name(prefix='clitest', length=15),
            'sub': self.get_subscription_id(),
            'body': f"""{{\\"location\\": \\"eastus2euap\\", \\"sku\\": {{\\"name\\": \\"Standard_D2ds_v4\\", \\"tier\\": \\"GeneralPurpose\\"}}, \\"properties\\": {{\\"administratorLogin\\": \\"{username}\\", \\"administratorLoginPassword\\": \\"{password}\\", \\"version\\": \\"15\\", \\"storage\\": {{\\"storageSizeGB\\": 64, \\"autoGrow\\": \\"Disabled\\"}}, \\"authConfig\\": {{\\"activeDirectoryAuth\\": \\"Disabled\\", \\"passwordAuth\\": \\"Enabled\\",  \\"tenantId\\": \\"\\"}}, \\"backup\\": {{\\"backupRetentionDays\\": 7, \\"geoRedundantBackup\\": \\"Disabled\\"}}, \\"highAvailability\\": {{\\"mode\\": \\"Disabled\\"}}, \\"createMode\\": \\"Create\\"}}}}""",
            'headers': '{\\"Content-Type\\":\\"application/json\\"}'
        })

        response = self.cmd('az rest --method "PUT" --headers "{headers}" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version=2023-06-01-preview" \
                        --body "{body}"')

        self.check_provisioning_state_for_postgresql_flexible_server()

        self.cmd('az network private-link-resource list --name {server_name} --resource-group {rg} --type Microsoft.DBforPostgreSQL/flexibleServers',
                 checks=[self.check('length(@)', 1), self.check('[0].properties.groupId', 'postgresqlServer')])

    @ResourceGroupPreparer(name_prefix='cli_test_fspg', random_name_length=18, location='eastus2euap')
    def test_private_endpoint_connection_postgres_flexible_server(self, resource_group):
        from azure.mgmt.core.tools import resource_id
        namespace = 'Microsoft.DBforPostgreSQL'
        instance_type = 'flexibleServers'
        resource_name = self.create_random_name(prefix='clitest', length=15)
        target_resource_id = resource_id(
            subscription=self.get_subscription_id(),
            resource_group=resource_group,
            namespace=namespace,
            type=instance_type,
            name=resource_name,
        )
        password = "aBcD1234!@#$"
        username = "admin123"
        self.kwargs.update({
            'server_name': resource_name,
            'target_resource_id': target_resource_id,
            'location': 'eastus2euap',
            'storage': 64,
            'resource_type': 'Microsoft.DBforPostgreSQL/flexibleServers',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
            'sub': self.get_subscription_id(),
            'body': f"""{{\\"location\\": \\"eastus2euap\\", \\"sku\\": {{\\"name\\": \\"Standard_D2ds_v4\\", \\"tier\\": \\"GeneralPurpose\\"}}, \\"properties\\": {{\\"administratorLogin\\": \\"{username}\\", \\"administratorLoginPassword\\": \\"{password}\\", \\"version\\": \\"15\\", \\"storage\\": {{\\"storageSizeGB\\": 64, \\"autoGrow\\": \\"Disabled\\"}}, \\"authConfig\\": {{\\"activeDirectoryAuth\\": \\"Disabled\\", \\"passwordAuth\\": \\"Enabled\\",  \\"tenantId\\": \\"\\"}}, \\"backup\\": {{\\"backupRetentionDays\\": 7, \\"geoRedundantBackup\\": \\"Disabled\\"}}, \\"highAvailability\\": {{\\"mode\\": \\"Disabled\\"}}, \\"createMode\\": \\"Create\\"}}}}""",
            'headers': '{\\"Content-Type\\":\\"application/json\\"}'
        })

        self.cmd('az network vnet create -n {vnet} -g {rg} -l {location} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('az network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        response = self.cmd('az rest --method "PUT" --headers "{headers}" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version=2023-06-01-preview" \
                        --body "{body}"')
        self.check_provisioning_state_for_postgresql_flexible_server()

        target_private_link_resource = self.cmd('az network private-link-resource list --name {server_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            'group_id': target_private_link_resource[0]['properties']['groupId']
        })

        # Create a private endpoint connection
        pe = self.cmd(
            'az network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} '
            '--connection-name {pe_connection} --private-connection-resource-id {target_resource_id} '
            '--group-id {group_id} --manual-request').get_output_in_json()
        self.kwargs['pe_id'] = pe['id']
        self.kwargs['pe_name'] = self.kwargs['pe_id'].split('/')[-1]

        # Show the connection at PostgreSQL side
        list_private_endpoint_conn = self.cmd('az network private-endpoint-connection list --name {server_name} --resource-group {rg} --type {resource_type}').get_output_in_json()
        self.kwargs.update({
            "pec_id": list_private_endpoint_conn[0]['id']
        })

        self.kwargs.update({
            "pec_name": self.kwargs['pec_id'].split('/')[-1]
        })
        self.cmd('az network private-endpoint-connection show --id {pec_id}',
                 checks=self.check('id', '{pec_id}'))
        self.cmd('az network private-endpoint-connection show --resource-name {server_name} -n {pec_name} -g {rg} --type {resource_type}')

        self.cmd(
            "az network private-endpoint-connection show --resource-name {server_name} -n {pec_name} -g {rg} --type {resource_type}",
            checks=self.check('properties.privateLinkServiceConnectionState.status', 'Pending')
        )

        # Approve / reject private endpoint
        self.kwargs.update({
            'approval_desc': 'Approved.',
            'rejection_desc': 'Rejected.'
        })
        self.cmd(
            'az network private-endpoint-connection approve --resource-name {server_name} --resource-group {rg} --name {pec_name} --type {resource_type} '
            '--description "{approval_desc}"', checks=[
                self.check('properties.privateLinkServiceConnectionState.status', 'Approved')
            ])
        self.cmd('az network private-endpoint-connection reject --id {pec_id} '
                 '--description "{rejection_desc}"',
                 checks=[
                     self.check('properties.privateLinkServiceConnectionState.status', 'Rejected')
                 ])
        self.cmd('az network private-endpoint-connection list --name {server_name} --resource-group {rg} --type {resource_type}', checks=[
            self.check('length(@)', 1)
        ])

        # Test delete
        self.cmd('az network private-endpoint-connection delete --id {pec_id} -y')


    def get_provisioning_state_for_postgresql_flexible_server(self):
        # get provisioning state
        response = self.cmd('az rest --method "GET" \
                        --url "https://management.azure.com/subscriptions/{sub}/resourcegroups/{rg}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{server_name}?api-version=2023-06-01-preview" \
                        ').get_output_in_json()

        return response['properties']['state']


    def check_provisioning_state_for_postgresql_flexible_server(self):

        # Wait for a moment before the server provisioning has begun to avoid inaccurate 404 errors.
        time.sleep(10) 
        count = 0
        print("checking status of creation...........")
        state = self.get_provisioning_state_for_postgresql_flexible_server()
        print(state)
        while state!="Ready":
            if state == "Provisioning":
                print("instance not yet created. waiting for 1 more min...")
                time.sleep(60) # Wait for 1 minute
            elif (count == 15):
                print("TimeOut after waiting for 15 mins!")
                self.assertTrue(False)
            count+=1
            state = self.get_provisioning_state_for_postgresql_flexible_server()
        print("Server creation succeeded!")
