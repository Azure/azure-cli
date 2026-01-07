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
    ScenarioTest,
    StringContainCheck)
from ..._client_factory import cf_postgres_flexible_private_dns_zone_suffix_operations
from ...flexible_server_virtual_network import prepare_private_dns_zone
from ...flexible_server_custom_postgres import DbContext as PostgresDbContext
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class PostgreSQLFlexibleServerPrivateDnsZoneScenarioTest(ScenarioTest):
    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    def test_postgres_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        self._test_flexible_server_existing_private_dns_zone(server_resource_group, vnet_resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='server_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='vnet_resource_group')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='dns_resource_group')
    def test_postgres_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        self._test_flexible_server_new_private_dns_zone(server_resource_group, vnet_resource_group, dns_resource_group)


    def _test_flexible_server_existing_private_dns_zone(self, server_resource_group, vnet_resource_group):
        server_names = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        location = self.postgres_location
        delegation_service_name = "Microsoft.DBforPostgreSQL/flexibleServers"
        private_dns_zone_key = "privateDnsZoneArmResourceId"
        server_group_vnet_name = 'servergrouptestvnet'
        server_group_subnet_name = 'servergrouptestsubnet'
        vnet_group_vnet_name = 'vnetgrouptestvnet'
        vnet_group_subnet_name = 'vnetgrouptestsubnet'
        vnet_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 server_resource_group, location, server_group_vnet_name, vnet_prefix, server_group_subnet_name, subnet_prefix))
        server_group_vnet = self.cmd('network vnet show -g {} -n {}'.format(
                                     server_resource_group, server_group_vnet_name)).get_output_in_json()
        server_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       server_resource_group, server_group_subnet_name, server_group_vnet_name)).get_output_in_json()
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 vnet_resource_group, location, vnet_group_vnet_name, vnet_prefix, vnet_group_subnet_name, subnet_prefix))
        vnet_group_vnet = self.cmd('network vnet show -g {} -n {}'.format(
                                   vnet_resource_group, vnet_group_vnet_name)).get_output_in_json()
        vnet_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       vnet_resource_group, vnet_group_subnet_name, vnet_group_vnet_name)).get_output_in_json()

        # FQDN validator
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --vnet {} --subnet {} --yes'.format(
                 server_resource_group, server_resource_group, server_names[0], location, server_names[0] + '.postgres.database.azure.com', server_group_vnet_name, server_group_subnet_name),
                 expect_failure=True)

        # validate wrong suffix
        dns_zone_incorrect_suffix = 'clitestincorrectsuffix.database.postgres.azure.com'
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
            server_resource_group, server_names[0], location, dns_zone_incorrect_suffix, server_group_subnet["id"]),
            expect_failure=True)

        # existing private dns zone in server group, no link
        unlinked_dns_zone = 'clitestunlinked.postgres.database.azure.com'
        self.cmd('network private-dns zone create -g {} --name {}'.format(
                 server_resource_group, unlinked_dns_zone))

        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
            server_resource_group, server_names[0], location, unlinked_dns_zone, server_group_subnet["id"]))
        result = self.cmd('postgres flexible-server show -g {} -n {}'.format(server_resource_group, server_names[0])).get_output_in_json()

        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_group_vnet_name, server_group_subnet_name))
        self.assertEqual(result["network"][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                        self.get_subscription_id(), server_resource_group, unlinked_dns_zone))
        self.cmd('network vnet show --id {}'.format(server_group_vnet['id']),
                 checks=[StringContainCheck(vnet_prefix)])
        self.cmd('network vnet subnet show --id {}'.format(server_group_subnet['id']),
                 checks=[JMESPathCheck('addressPrefix', subnet_prefix),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # exisitng private dns zone in vnet group
        vnet_group_dns_zone = 'clitestvnetgroup.postgres.database.azure.com'
        self.cmd('network private-dns zone create -g {} --name {}'.format(
                 vnet_resource_group, vnet_group_dns_zone))
        self.cmd('network private-dns link vnet create -g {} -n MyLinkName -z {} -v {} -e False'.format(
                 vnet_resource_group, vnet_group_dns_zone, vnet_group_vnet['id']
        ))
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 server_resource_group, server_names[1], location, vnet_group_dns_zone, vnet_group_subnet["id"]))
        result = self.cmd('postgres flexible-server show -g {} -n {}'.format(server_resource_group, server_names[1])).get_output_in_json()

        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, vnet_group_vnet_name, vnet_group_subnet_name))
        self.assertEqual(result["network"][private_dns_zone_key],
                        '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                        self.get_subscription_id(), vnet_resource_group, vnet_group_dns_zone))
        self.cmd('network vnet show --id {}'.format(vnet_group_vnet['id']),
                 checks=[StringContainCheck(vnet_prefix)])
        self.cmd('network vnet subnet show --id {}'.format(vnet_group_subnet['id']),
                 checks=[JMESPathCheck('addressPrefix', subnet_prefix),
                         JMESPathCheck('delegations[0].serviceName', delegation_service_name)])

        # delete all servers
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(server_resource_group, server_names[0]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(server_resource_group, server_names[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_new_private_dns_zone(self, server_resource_group, vnet_resource_group, dns_resource_group):
        server_names = ['clitest-private-dns-zone-test-3', 'clitest-private-dns-zone-test-4',
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                        self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)]
        private_dns_zone_names = ["clitestdnszone1.private.postgres.database.azure.com",
                                  "clitestdnszone2.private.postgres.database.azure.com",
                                  "clitestdnszone3.private.postgres.database.azure.com"]
        location = self.postgres_location
        private_dns_zone_key = "privateDnsZoneArmResourceId"
        db_context = PostgresDbContext(cmd=self,
                                           cf_private_dns_zone_suffix=cf_postgres_flexible_private_dns_zone_suffix_operations,
                                           command_group='postgres')

        server_group_vnet_name = 'servergrouptestvnet'
        server_group_subnet_name = 'servergrouptestsubnet'
        vnet_group_vnet_name = 'vnetgrouptestvnet'
        vnet_group_subnet_name = 'vnetgrouptestsubnet'
        vnet_prefix = '172.1.0.0/16'
        subnet_prefix = '172.1.0.0/24'
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 server_resource_group, location, server_group_vnet_name, vnet_prefix, server_group_subnet_name, subnet_prefix))
        server_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       server_resource_group, server_group_subnet_name, server_group_vnet_name)).get_output_in_json()
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 vnet_resource_group, location, vnet_group_vnet_name, vnet_prefix, vnet_group_subnet_name, subnet_prefix))
        vnet_group_subnet = self.cmd('network vnet subnet show -g {} -n {} --vnet-name {}'.format(
                                       vnet_resource_group, vnet_group_subnet_name, vnet_group_vnet_name)).get_output_in_json()
        # no input, vnet in server rg
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[0], None, server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_names[0] + ".private.postgres.database.azure.com"))

        # no input, vnet in vnet rg
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[1], None, vnet_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, server_names[1] + ".private.postgres.database.azure.com"))

        # new private dns zone, zone name (vnet in same rg)
        dns_zone = prepare_private_dns_zone(db_context, server_resource_group, server_names[2], private_dns_zone_names[0],
                                            server_group_subnet["id"], location, True)
        self.assertEqual(dns_zone,
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                         self.get_subscription_id(), server_resource_group, private_dns_zone_names[0]))

        # new private dns zone in dns rg, zone id (vnet in diff rg)
        dns_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                 self.get_subscription_id(), dns_resource_group, private_dns_zone_names[1])
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 server_resource_group, server_names[3], location, dns_id, vnet_group_subnet["id"]))
        result = self.cmd('postgres flexible-server show -g {} -n {}'.format(server_resource_group, server_names[3])).get_output_in_json()
        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), vnet_resource_group, vnet_group_vnet_name, vnet_group_subnet_name))
        self.assertEqual(result["network"][private_dns_zone_key], dns_id)

        # new private dns zone, zone id vnet server same rg, zone diff rg
        dns_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                 self.get_subscription_id(), dns_resource_group, private_dns_zone_names[2])
        self.cmd('postgres flexible-server create -g {} -n {} -l {} --private-dns-zone {} --subnet {} --yes'.format(
                 server_resource_group, server_names[4], location, dns_id, server_group_subnet["id"]))
        result = self.cmd('postgres flexible-server show -g {} -n {}'.format(server_resource_group, server_names[4])).get_output_in_json()
        self.assertEqual(result["network"]["delegatedSubnetResourceId"],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), server_resource_group, server_group_vnet_name, server_group_subnet_name))
        self.assertEqual(result["network"][private_dns_zone_key], dns_id)

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(server_resource_group, server_names[3]),
                 checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(server_resource_group, server_names[4]),
                 checks=NoneCheck())

        time.sleep(15 * 60)