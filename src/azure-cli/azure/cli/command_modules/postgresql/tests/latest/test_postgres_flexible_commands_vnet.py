# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import time
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class PostgreSQLFlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid(self, resource_group):
        self._test_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_vnetname_subnetname_and_privatednszoneid(self, resource_group):
        self._test_flexible_server_vnet_mgmt_vnetname_subnetname_and_privatednszoneid(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_vnet')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_private_dns_zone')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_server')
    def test_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid_in_different_resource_groups(self, resource_group_vnet, resource_group_private_dns_zone, resource_group_server):
        self._test_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid_in_different_resource_groups(resource_group_vnet, resource_group_private_dns_zone, resource_group_server)

    def _test_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid(self, resource_group):
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, 32)
        server_vnet_name = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        server_subnet_name = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        server_vnet_prefixes = '10.0.0.0/16'
        server_subnet_prefixes = '10.0.0.0/24'
        server_private_dns_zone_name = '{}.private.postgres.database.azure.com'.format(server_name)

        # Create a virtual network and subnet for server.
        result_vnet = self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group, location, server_vnet_name, server_vnet_prefixes, server_subnet_name, server_subnet_prefixes)).get_output_in_json()
        
        # Delegate the subnet to Microsoft.DBforPostgreSQL/flexibleServers.
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --delegations Microsoft.DBforPostgreSQL/flexibleServers'.format(
                 resource_group, server_vnet_name, server_subnet_name))
        
        # Create a private DNS zone for server.
        result_dns = self.cmd('network private-dns zone create -g {} -n {}'.format(resource_group, server_private_dns_zone_name)).get_output_in_json()

        # Scenario: Provision a server with supplied subnet identifier and private DNS zone identifier.
        self.cmd('postgres flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(resource_group, server_name, result_vnet['newVNet']['subnets'][0]['id'], location, result_dns['id']))
        
        # Validate that the server is provisioned with the correct network configuration.
        self.cmd('postgres flexible-server show -g {} -n {}'
                 .format(resource_group, server_name),
                 checks=[
                     JMESPathCheck('network.privateDnsZoneArmResourceId', result_dns['id']),
                     JMESPathCheck('network.delegatedSubnetResourceId', result_vnet['newVNet']['subnets'][0]['id'])])

        # Scenario: Migrate network of the server from integrated in customer-managed network to integrated in Microsoft-managed network.
        self.cmd('postgres flexible-server migrate-network -g {} -n {}'.format(resource_group, server_name))
        
        self.cmd('postgres flexible-server show -g {} -n {}'
                    .format(resource_group, server_name),
                    checks=[
                        JMESPathCheck('network.privateDnsZoneArmResourceId', None),
                        JMESPathCheck('network.delegatedSubnetResourceId', None)])

        # Clean up.
        # Delete server.
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, server_name), checks=NoneCheck())
        # Delete private DNS zone.
        self.cmd('network private-dns zone delete -g {} -n {} --yes'.format(resource_group, server_private_dns_zone_name), checks=NoneCheck())
        # Remove delegation from subnet.
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --remove delegations'.format(resource_group, server_vnet_name, server_subnet_name))
        # Delete virtual network.
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, server_vnet_name), checks=NoneCheck())


    def _test_flexible_server_vnet_mgmt_vnetname_subnetname_and_privatednszoneid(self, resource_group):
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, 32)
        server_vnet_name = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        server_subnet_name = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        server_vnet_prefixes = '10.0.0.0/16'
        server_subnet_prefixes = '10.0.0.0/24'
        server_private_dns_zone_name = '{}.private.postgres.database.azure.com'.format(server_name)

        # Create a virtual network and subnet for server.
        result_vnet = self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group, location, server_vnet_name, server_vnet_prefixes, server_subnet_name, server_subnet_prefixes)).get_output_in_json()
        
        # Delegate the subnet to Microsoft.DBforPostgreSQL/flexibleServers.
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --delegations Microsoft.DBforPostgreSQL/flexibleServers'.format(
                 resource_group, server_vnet_name, server_subnet_name))
        
        # Create a private DNS zone for server.
        result_dns = self.cmd('network private-dns zone create -g {} -n {}'.format(resource_group, server_private_dns_zone_name)).get_output_in_json()

        # Scenario: Provision a server with supplied virtual network name, subnet name, and private DNS zone name.
        self.cmd('postgres flexible-server create -g {} -n {} --vnet {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(resource_group, server_name, server_vnet_name, server_subnet_name, location, server_private_dns_zone_name))
        
        # Validate that the server is provisioned with the correct network configuration.
        self.cmd('postgres flexible-server show -g {} -n {}'
                 .format(resource_group, server_name),
                 checks=[
                     JMESPathCheck('network.privateDnsZoneArmResourceId', result_dns['id']),
                     JMESPathCheck('network.delegatedSubnetResourceId', result_vnet['newVNet']['subnets'][0]['id'])])

        # Scenario: Migrate network of the server from integrated in customer-managed network to integrated in Microsoft-managed network.
        self.cmd('postgres flexible-server migrate-network -g {} -n {}'.format(resource_group, server_name))
        
        self.cmd('postgres flexible-server show -g {} -n {}'
                    .format(resource_group, server_name),
                    checks=[
                        JMESPathCheck('network.privateDnsZoneArmResourceId', None),
                        JMESPathCheck('network.delegatedSubnetResourceId', None)])

        # Clean up.
        # Delete server.
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, server_name), checks=NoneCheck())
        # Delete private DNS zone.
        self.cmd('network private-dns zone delete -g {} -n {} --yes'.format(resource_group, server_private_dns_zone_name), checks=NoneCheck())
        # Remove delegation from subnet.
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group, server_subnet_name, server_vnet_name))
        # Delete virtual network.
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, server_vnet_name), checks=NoneCheck())

    def _test_flexible_server_vnet_mgmt_subnetid_and_privatednszoneid_in_different_resource_groups(self, resource_group_vnet, resource_group_private_dns_zone, resource_group_server):
        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        location = self.postgres_location
        server_name = self.create_random_name(SERVER_NAME_PREFIX, 32)
        server_vnet_name = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        server_subnet_name = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        server_vnet_prefixes = '10.0.0.0/16'
        server_subnet_prefixes = '10.0.0.0/24'
        server_private_dns_zone_name = '{}.private.postgres.database.azure.com'.format(server_name)

        # Create a virtual network and subnet for server in its own resource group.
        result_vnet = self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group_vnet, location, server_vnet_name, server_vnet_prefixes, server_subnet_name, server_subnet_prefixes)).get_output_in_json()
        
        # Delegate the subnet to Microsoft.DBforPostgreSQL/flexibleServers.
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --delegations Microsoft.DBforPostgreSQL/flexibleServers'.format(
                 resource_group_vnet, server_vnet_name, server_subnet_name))
        
        # Create a private DNS zone for server.
        result_dns = self.cmd('network private-dns zone create -g {} -n {}'.format(resource_group_private_dns_zone, server_private_dns_zone_name)).get_output_in_json()

        # Scenario: Provision a server with supplied virtual network name, subnet name, and private DNS zone name.
        self.cmd('postgres flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {} --yes'
                 .format(resource_group_server, server_name, result_vnet['newVNet']['subnets'][0]['id'], location, result_dns['id']))

        # Validate that the server is provisioned with the correct network configuration.
        self.cmd('postgres flexible-server show -g {} -n {}'
                 .format(resource_group_server, server_name),
                 checks=[
                     JMESPathCheck('network.privateDnsZoneArmResourceId', result_dns['id']),
                     JMESPathCheck('network.delegatedSubnetResourceId', result_vnet['newVNet']['subnets'][0]['id'])])

        # Scenario: Migrate network of the server from integrated in customer-managed network to integrated in Microsoft-managed network.
        self.cmd('postgres flexible-server migrate-network -g {} -n {}'.format(resource_group_server, server_name))
        
        self.cmd('postgres flexible-server show -g {} -n {}'
                    .format(resource_group_server, server_name),
                    checks=[
                        JMESPathCheck('network.privateDnsZoneArmResourceId', None),
                        JMESPathCheck('network.delegatedSubnetResourceId', None)])

        # Clean up.
        # Delete server.
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group_server, server_name), checks=NoneCheck())
        # Delete private DNS zone.
        self.cmd('network private-dns zone delete -g {} -n {} --yes'.format(resource_group_private_dns_zone, server_private_dns_zone_name), checks=NoneCheck())
        # Remove delegation from subnet.
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_vnet, server_subnet_name, server_vnet_name))
        # Delete virtual network.
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_vnet, server_vnet_name), checks=NoneCheck())
