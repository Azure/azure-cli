# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION
from .server_preparer import ServerPreparer


class FlexibleServerPrivateEndpointsMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_private_endpoint_mgmt(self, resource_group, server):
        self._test_private_endpoint_connection(resource_group, server)
        self._test_private_link_resource(resource_group, server, 'postgresqlServer')

    def _test_private_endpoint_connection(self, resource_group, server_name):
        loc = self.postgres_location
        vnet = self.create_random_name('cli-vnet-', 24)
        subnet = self.create_random_name('cli-subnet-', 24)
        pe_name_auto = self.create_random_name('cli-pe-', 24)
        pe_name_manual_approve = self.create_random_name('cli-pe-', 24)
        pe_name_manual_reject = self.create_random_name('cli-pe-', 24)
        pe_connection_name_auto = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_approve = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_reject = self.create_random_name('cli-pec-', 24)

        result = self.cmd('postgres flexible-server show -n {} -g {}'.format(server_name, resource_group),
                               checks=[JMESPathCheck('resourceGroup', resource_group),
                                       JMESPathCheck('name', server_name)]).get_output_in_json()
        self.assertEqual(''.join(result['location'].lower().split()), self.postgres_location)

        # Prepare network and disable network policies
        self.cmd('network vnet create -n {} -g {} -l {} --subnet-name {}'
                 .format(vnet, resource_group, loc, subnet),
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {} --vnet-name {} -g {} '
                 '--private-endpoint-network-policies Disabled'
                 .format(subnet, vnet, resource_group),
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Get Server Id and Group Id
        result = self.cmd('postgres flexible-server show -g {} -n {}'
                          .format(resource_group, server_name)).get_output_in_json()
        server_id = result['id']
        group_id = 'postgresqlServer'

        approval_description = 'You are approved!'
        rejection_description = 'You are rejected!'

        # Testing Auto-Approval workflow
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {}'
                                    .format(resource_group, pe_name_auto, vnet, subnet, loc, pe_connection_name_auto,
                                            server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_auto)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], pe_connection_name_auto)
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('postgres flexible-server show -g {} -n {}'
                          .format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('postgres flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Approved')
                 ])
        
        self.cmd('postgres flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(server_name, resource_group, server_pec_name, approval_description))

        self.cmd('postgres flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(server_name, resource_group, server_pec_name, rejection_description))

        self.cmd('postgres flexible-server private-endpoint-connection delete --server-name {} -g {} --id {}'
                 .format(server_name, resource_group, server_pec_id))

        # Testing Manual-Approval workflow [Approval]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request'
                                    .format(resource_group, pe_name_manual_approve, vnet, subnet, loc,
                                            pe_connection_name_manual_approve, server_id,
                                            group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_approve)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_approve)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('postgres flexible-server show -g {} -n {}'
                          .format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('postgres flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('postgres flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                 .format(server_name, resource_group, server_pec_name, approval_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', approval_description),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('postgres flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(server_name, resource_group, server_pec_name, rejection_description))

        self.cmd('postgres flexible-server private-endpoint-connection delete --server-name {} -g {}  --id {}'
                 .format(server_name, resource_group, server_pec_id))

        # Testing Manual-Approval workflow [Rejection]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request true'
                                    .format(resource_group, pe_name_manual_reject, vnet, subnet, loc,
                                            pe_connection_name_manual_reject, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_reject)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_reject)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('postgres flexible-server show -g {} -n {}'
                          .format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('postgres flexible-server private-endpoint-connection list -g {} --server-name {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 1)])

        self.cmd('postgres flexible-server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(server_name, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('postgres flexible-server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                 .format(server_name, resource_group, server_pec_name, rejection_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', rejection_description),
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('postgres flexible-server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(server_name, resource_group, server_pec_name, approval_description), expect_failure=True)

        self.cmd('postgres flexible-server private-endpoint-connection delete --server-name {} -g {}  --id {}'
                 .format(server_name, resource_group, server_pec_id))
        result = self.cmd('postgres flexible-server show -g {} -n {}'
                          .format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 0)

    def _test_private_link_resource(self, resource_group, server, group_id):
        result = self.cmd('postgres flexible-server private-link-resource list -g {} -s {}'
                          .format(resource_group, server)).get_output_in_json()
        self.assertEqual(result[0]['groupId'], group_id)

        result = self.cmd('postgres flexible-server private-link-resource show -g {} -s {}'
                          .format(resource_group, server)).get_output_in_json()
        self.assertEqual(result['groupId'], group_id)