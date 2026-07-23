# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class PostgreSQLFlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_replica(self, resource_group):
        self._test_postgres_flexible_server_vnet_replica(resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_auto_grow_replica(self, resource_group):
        self._test_postgres_flexible_server_auto_grow_replica(resource_group)

    def _test_flexible_server_replica_mgmt(self, resource_group):
        location = self.postgres_location
        primary_role = 'Primary'
        replica_role = 'AsyncReplica'
        virtual_endpoint_name = self.create_random_name(F'virtual-endpoint', 32)
        read_write_endpoint_type = 'ReadWrite'
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]

        # Create a server
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} --tier GeneralPurpose --sku-name Standard_D2ds_v4 --public-access none --yes'
                 .format(resource_group, master_server, location, 256))
        result = self.cmd('postgres flexible-server show -g {} --name {} '
                          .format(resource_group, master_server),
                          checks=[JMESPathCheck('replica.role', primary_role)]).get_output_in_json()
        
        # Test replica create
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                 .format(resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id'])])

        # Test replica list
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # Test replica promote
        self.cmd('postgres flexible-server replica promote -g {} --name {} --yes'
                 .format(resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', None)])

        # Test show server with replication info, master becomes normal server
        self.cmd('postgres flexible-server show -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', None)])

        # Create second replica
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                .format(resource_group, replicas[1], result['id']),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('sku.name', result['sku']['name']),
                    JMESPathCheck('replica.role', replica_role),
                    JMESPathCheck('sourceServerResourceId', result['id'])])

        # In Postgres we can't delete master server if it has replicas
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server),
                    expect_failure=True)

        # Test virtual-endpoint create
        self.cmd('postgres flexible-server virtual-endpoint create -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                .format(resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, master_server),
                checks=[
                    JMESPathCheck('endpointType', read_write_endpoint_type),
                    JMESPathCheck('name', virtual_endpoint_name),
                    JMESPathCheck('length(virtualEndpoints)', 2)])

        # Test virtual-endpoint update
        update_result = self.cmd('postgres flexible-server virtual-endpoint update -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                .format(resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, replicas[1]),
                checks=[JMESPathCheck('length(members)', 2)]).get_output_in_json()

        # Test virtual-endpoint show
        self.cmd('postgres flexible-server virtual-endpoint show -g {} --server-name {} --name {}'
                .format(resource_group, master_server, virtual_endpoint_name),
                checks=[JMESPathCheck('members', update_result['members'])])

        # Test replica switchover planned
        switchover_result = self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option planned --yes'
                .format(resource_group, replicas[1]),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', None)]).get_output_in_json()

        # Test show server with replication info, master became replica server
        self.cmd('postgres flexible-server show -g {} --name {}'
                .format(resource_group, master_server),
                checks=[
                    JMESPathCheck('replica.role',replica_role),
                    JMESPathCheck('sourceServerResourceId', switchover_result['id'])])

        # Test replica switchover forced
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option forced --yes'
                .format(resource_group, master_server),
                checks=[
                    JMESPathCheck('name', master_server),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', None)])

        # Test promote replica standalone forced
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode standalone --promote-option forced --yes'
                .format(resource_group, replicas[1]),
                checks=[
                    JMESPathCheck('name',replicas[1]),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', None)])

        # Test replica list
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 0)])

        # Test virtual-endpoint delete
        self.cmd('postgres flexible-server virtual-endpoint delete -g {} --server-name {} --name {} --yes'
                .format(resource_group, master_server, virtual_endpoint_name))

        # Test virtual-endpoint list
        self.cmd('postgres flexible-server virtual-endpoint list -g {} --server-name {}'
                .format(resource_group, master_server),
                expect_failure=True)
        
        # test replica create ssdv2
        replica_ssdv2 = self.create_random_name(F'azuredbclirepssdv2', SERVER_NAME_MAX_LENGTH)
        storage_type = 'PremiumV2_LRS'
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {} --storage-type {}'
                 .format(resource_group, replica_ssdv2, result['id'], storage_type),
                 checks=[
                     JMESPathCheck('name', replica_ssdv2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('storage.type', storage_type),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id'])])

        # Clean up servers
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replicas[1]), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replica_ssdv2), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server), checks=NoneCheck())
        
    def _test_postgres_flexible_server_vnet_replica(self, resource_group):
        location = self.postgres_location
        primary_role = 'Primary'
        replica_role = 'AsyncReplica'
        public_access_arg = ''
        public_access_check = []
        tier = 'GeneralPurpose'
        sku_name = 'Standard_D2ds_v4'
        server_one = self.create_random_name(SERVER_NAME_PREFIX, 32)
        both_servers_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        server_one_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        both_servers_vnet_prefixes = '10.0.0.0/16'
        server_one_subnet_prefixes = '10.0.0.0/24'
        server_one_private_dns_zone = '{}.private.postgres.database.azure.com'.format(server_one)
        server_one_vnet_args = '--vnet {} --subnet {} --private-dns-zone {}'.format(both_servers_vnet, server_one_subnet, server_one_private_dns_zone)
        server_one_vnet_check = [JMESPathCheck('network.delegatedSubnetResourceId', '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(self.get_subscription_id(), resource_group, both_servers_vnet, server_one_subnet))]
        server_two = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_two_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        server_two_subnet_prefixes = '10.0.1.0/24'
        server_two_private_dns_zone = '{}.private.postgres.database.azure.com'.format(server_two)
        server_two_vnet_args = '--vnet {} --subnet {} --private-dns-zone {}'.format(both_servers_vnet, server_two_subnet, server_two_private_dns_zone)
        server_two_vnet_check = [JMESPathCheck('network.delegatedSubnetResourceId', '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(self.get_subscription_id(), resource_group, both_servers_vnet, server_two_subnet))]
        virtual_endpoint_name = self.create_random_name(F'virtual-endpoint', 32)
        read_write_endpoint_type = 'ReadWrite'


        # Create a virtual network and subnet for server one
        self.cmd('network vnet create -g {} -l {} -n {} --address-prefixes {} --subnet-name {} --subnet-prefixes {}'.format(
                 resource_group, location, both_servers_vnet, both_servers_vnet_prefixes, server_one_subnet, server_one_subnet_prefixes))
        
        # Delegate the subnet to Microsoft.DBforPostgreSQL/flexibleServers
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --delegations Microsoft.DBforPostgreSQL/flexibleServers'.format(
                 resource_group, both_servers_vnet, server_one_subnet))
        
        # Create a subnet for server two
        self.cmd('network vnet subnet create -g {} --vnet-name {} -n {} --address-prefixes {}'.format(
                 resource_group, both_servers_vnet, server_two_subnet, server_two_subnet_prefixes))
        
        # Delegate the subnet to Microsoft.DBforPostgreSQL/flexibleServers
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --delegations Microsoft.DBforPostgreSQL/flexibleServers'.format(
                 resource_group, both_servers_vnet, server_two_subnet))
        
        # Create a private DNS zone for server one
        self.cmd('network private-dns zone create -g {} -n {}'.format(resource_group, server_one_private_dns_zone))

        # Create a private DNS zone for server two
        self.cmd('network private-dns zone create -g {} -n {}'.format(resource_group, server_two_private_dns_zone))

        # Create server one
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} {} --tier {} --sku-name {} --private-dns-zone {} --yes'
                 .format(resource_group, server_one, location, 256, server_one_vnet_args, tier, sku_name, server_one_private_dns_zone))
        result_server_one = self.cmd('postgres flexible-server show -g {} --name {}'
                 .format(resource_group, server_one),
                    checks=[
                        JMESPathCheck('replica.role', primary_role)]
                        + server_one_vnet_check).get_output_in_json()
                                       
        # Create server two, as a replica of server one, with vnet and subnet, and validate that replica is created with the same vnet and subnet as master server.
        result_server_two = self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {} --zone 2 {} {}'
                 .format(resource_group, server_two, result_server_one['id'], server_two_vnet_args, public_access_arg),
                 checks=[
                     JMESPathCheck('name', server_two),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result_server_one['sku']['tier']),
                     JMESPathCheck('sku.name', result_server_one['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result_server_one['id'])] + server_two_vnet_check + public_access_check).get_output_in_json()

        # Validate that server two is listed under server one's replicas.
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, server_one),
                 checks=[
                     JMESPathCheck('length(@)', 1)])
        
        # Create virtual endpoints on server one (primary) with server two (replica) behind reader endpoint.
        self.cmd('postgres flexible-server virtual-endpoint create -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                .format(resource_group, server_one, virtual_endpoint_name, read_write_endpoint_type, server_two),
                checks=[
                    JMESPathCheck('endpointType', read_write_endpoint_type),
                    JMESPathCheck('name', virtual_endpoint_name),
                    JMESPathCheck('length(virtualEndpoints)', 2),
                    JMESPathCheck('length(members)', 2),
                    JMESPathCheck('members[1]', server_two)])

        # Validate that server two can be switched over successfully with vnet and subnet.
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option forced --yes'
                 .format(resource_group, server_two),
                    checks=[
                        JMESPathCheck('name', server_two),
                        JMESPathCheck('replica.role', primary_role),
                        JMESPathCheck('sourceServerResourceId', None)])

        # Validate that server one shows correct replication info after switchover, server one is playing the replica role, and source server is server two.
        self.cmd('postgres flexible-server show -g {} --name {} '
                 .format(resource_group, server_one),
                 checks=[
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result_server_two['id'])]).get_output_in_json()
        
        # Validate that server one is listed under server two's replicas.
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, server_two),
                 checks=[
                     JMESPathCheck('length(@)', 1)])

        # Validate that server one can be promoted to stand alone successfully with vnet and subnet.
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode standalone --promote-option forced --yes'
                 .format(resource_group, server_one),
                 checks=[
                     JMESPathCheck('name', server_one),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', None)])

        # Validate that server two shows correct replication info after promotion, server two is playing the primary role, and has no source server.
        self.cmd('postgres flexible-server show -g {} --name {}'
                 .format(resource_group, server_two),
                 checks=[
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', None)])

        # Clean up
        # Delete servers
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, server_one), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, server_two), checks=NoneCheck())
        # Delete private DNS zones
        self.cmd('network private-dns zone delete -g {} -n {} --yes'.format(resource_group, server_one_private_dns_zone), checks=NoneCheck())
        self.cmd('network private-dns zone delete -g {} -n {} --yes'.format(resource_group, server_two_private_dns_zone), checks=NoneCheck())
        # Remove delegation from subnets
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --remove delegations'.format(resource_group, both_servers_vnet, server_one_subnet))
        self.cmd('network vnet subnet update -g {} --vnet-name {} -n {} --remove delegations'.format(resource_group, both_servers_vnet, server_two_subnet))
        # Delete virtual network
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, both_servers_vnet), checks=NoneCheck())

    def _test_postgres_flexible_server_auto_grow_replica(self, resource_group):
        location = self.postgres_location
        primary_role = 'Primary'
        public_access_arg = ''
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replica_role = 'AsyncReplica'
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]
        storage_auto_grow = "Enabled"

        # Create a server
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none --tier GeneralPurpose --sku-name Standard_D4ds_v5 --yes --storage-auto-grow Enabled'
                 .format(resource_group, master_server, location, 256))
        result = self.cmd('postgres flexible-server show -g {} --name {} '
                          .format(resource_group, master_server),
                          checks=[
                              JMESPathCheck('replica.role', primary_role),
                              JMESPathCheck('storage.autoGrow', storage_auto_grow)]).get_output_in_json()
        
        # Test replica create
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {} --zone 2 {}'
                 .format(resource_group, replicas[0], result['id'], public_access_arg),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id']),
                     JMESPathCheck('storage.autoGrow', storage_auto_grow)])

        # Delete replica server first
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, replicas[0]))

        # Now we can delete master server
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server))