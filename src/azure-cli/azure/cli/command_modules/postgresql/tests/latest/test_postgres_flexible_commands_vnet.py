# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from ...flexible_server_virtual_network import prepare_private_network, DEFAULT_VNET_ADDRESS_PREFIX, DEFAULT_SUBNET_ADDRESS_PREFIX
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class PostgreSQLFlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(resource_group_1, resource_group_2)

    def _test_flexible_server_vnet_mgmt_existing_supplied_subnetid(self, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone0.private.postgres.database.azure.com"

        # Scenario : Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        vnet_name = 'testvnet'
        subnet_name = 'testsubnet'
        address_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group, location, vnet_name, address_prefix, subnet_name, subnet_prefix))
        subnet_id = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(resource_group, subnet_name, vnet_name)).get_output_in_json()['id']

        # create server - Delegation should be added.
        self.cmd('postgres flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(resource_group, server_name, subnet_id, location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('postgres flexible-server show -g {} -n {}'
                                 .format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'], subnet_id)
        self.assertEqual(show_result_1['network'][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group, private_dns_zone))
        # delete server
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, server_name))

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        vnet_name = 'clitestvnet3'
        subnet_name = 'clitestsubnet3'
        vnet_name_2 = 'clitestvnet4'
        address_prefix = '13.0.0.0/16'
        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"

        # flexible-servers
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) + "postgres", self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH) + "postgres"]
        private_dns_zone_1 = "testdnszone3.private.postgres.database.azure.com"
        private_dns_zone_2 = "testdnszone4.private.postgres.database.azure.com"
        # Case 1 : Provision a server with supplied Vname and subnet name that exists.

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format(vnet_name, resource_group, location, address_prefix))

        # create server - Delegation should be added.
        self.cmd('postgres flexible-server create -g {} -n {} --vnet {} -l {} --subnet {} --private-dns-zone {} --yes'
                 .format(resource_group, servers[0], vnet_name, location, subnet_name, private_dns_zone_1))

        # Case 2 : Provision a server with a supplied Vname and subnet name that does not exist.
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --vnet {} --private-dns-zone {} --yes'
                 .format(resource_group, servers[1], location, vnet_name_2, private_dns_zone_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('postgres flexible-server show -g {} -n {}'
                                 .format(resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('postgres flexible-server show -g {} -n {}'
                                 .format(resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name, subnet_name))

        self.assertEqual(show_result_2['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1]))

        self.assertEqual(show_result_1['network'][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group, private_dns_zone_1))

        self.assertEqual(show_result_2['network'][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group, private_dns_zone_2))

        # delete all servers
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"
        vnet_name = 'clitestvnet5'
        subnet_name = 'clitestsubnet5'
        address_prefix = '10.10.0.0/16'
        subnet_prefix = '10.10.0.0/24'

        # flexible-servers
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone5.private.postgres.database.azure.com"

        # Case 1 : Provision a server with supplied subnetid that exists in a different RG

        # create vnet and subnet.
        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group_1, location, address_prefix, subnet_name,
                    subnet_prefix)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('postgres flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(resource_group_2, server_name, vnet_result['newVNet']['subnets'][0]['id'], location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('postgres flexible-server show -g {} -n {}'
                                 .format(resource_group_2, server_name)).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_1, vnet_name, subnet_name))

        self.assertEqual(show_result_1['network'][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                            self.get_subscription_id(), resource_group_1, private_dns_zone))

        # delete all servers
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(resource_group_2, server_name),
                 checks=NoneCheck())

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1, subnet_name, vnet_name))
        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_1, vnet_name))