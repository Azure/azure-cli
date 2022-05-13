# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only


class TestMonitorPrivateLinkScope(ScenarioTest):
    def __init__(self, method_name, config_file=None, recording_dir=None, recording_name=None, recording_processors=None,
                 replay_processors=None, recording_patches=None, replay_patches=None):
        super(TestMonitorPrivateLinkScope, self).__init__(method_name)
        self.cmd('extension add -n application-insights')

    # @record_only()  # record_only as the private-link-scope scoped-resource cannot find the components of application insights
    @unittest.skip('If it cannot run, how to record_only, how yaml file is created')
    @ResourceGroupPreparer(location='westus2')
    def test_monitor_private_link_scope_scenario(self, resource_group, resource_group_location):
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

        app_id = self.cmd('monitor app-insights component create -a {app} -g {rg} -l eastus').get_output_in_json()['id']
        workspace_id = self.cmd('monitor log-analytics workspace create -n {workspace} -g {rg} -l {loc}').get_output_in_json()['id']
        self.kwargs.update({
            'app_id': app_id,
            'workspace_id': workspace_id
        })

        # this command failed as service cannot find component of application insights
        self.cmd('monitor private-link-scope scoped-resource create -g {rg} -n {assigned_app} --linked-resource {app_id} --scope-name {scope}', checks=[
            self.check('name', '{assigned_app}')
        ])
        self.cmd('monitor private-link-scope scoped-resource show -g {rg} -n {assigned_app} --scope-name {scope}', checks=[
            self.check('name', '{assigned_app}')
        ])
        self.cmd('monitor private-link-scope scoped-resource list -g {rg} --scope-name {scope}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd('monitor private-link-scope scoped-resource create -g {rg} -n {assigned_ws} --linked-resource {workspace_id} --scope-name {scope}', checks=[
            self.check('name', '{assigned_ws}')
        ])

        self.cmd('monitor private-link-scope scoped-resource list -g {rg} --scope-name {scope}', checks=[
            self.check('length(@)', 2)
        ])

        self.cmd('monitor private-link-scope private-link-resource list --scope-name {scope} -g {rg}', checks=[
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
            '--group-ids {group_id}').get_output_in_json()
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

        self.cmd('monitor private-link-scope private-endpoint-connection show --scope-name {scope} -g {rg} --name {scope_pec_name}',
                 checks=self.check('id', '{scope_pec_id}'))

        self.cmd('monitor private-link-scope private-endpoint-connection approve --scope-name {scope} -g {rg} --name {scope_pec_name}')

        self.cmd('monitor private-link-scope private-endpoint-connection reject --scope-name {scope} -g {rg} --name {scope_pec_name}',
                 checks=[self.check('privateLinkServiceConnectionState.status', 'Rejected')])

        self.cmd('monitor private-link-scope private-endpoint-connection delete --id {scope_pec_id} -y')
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
