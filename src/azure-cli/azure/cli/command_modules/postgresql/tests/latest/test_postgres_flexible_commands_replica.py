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

        # create a server
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} --tier GeneralPurpose --sku-name Standard_D2ds_v4 --public-access none --yes'
                 .format(resource_group, master_server, location, 256))
        result = self.cmd('postgres flexible-server show -g {} --name {} '
                          .format(resource_group, master_server),
                          checks=[JMESPathCheck('replica.role', primary_role)]).get_output_in_json()
        
        # test replica create
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                 .format(resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id'])])

        # test replica list
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test replica promote
        self.cmd('postgres flexible-server replica promote -g {} --name {} --yes'
                 .format(resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None')])

        # test show server with replication info, master becomes normal server
        self.cmd('postgres flexible-server show -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None')])

        # Create second replica
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {}'
                .format(resource_group, replicas[1], result['id']),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('resourceGroup', resource_group),
                    JMESPathCheck('sku.name', result['sku']['name']),
                    JMESPathCheck('replica.role', replica_role),
                    JMESPathCheck('sourceServerResourceId', result['id'])])

        # in postgres we can't delete master server if it has replicas
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server),
                    expect_failure=True)

        # test virtual-endpoint create
        self.cmd('postgres flexible-server virtual-endpoint create -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                .format(resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, master_server),
                checks=[
                    JMESPathCheck('endpointType', read_write_endpoint_type),
                    JMESPathCheck('name', virtual_endpoint_name),
                    JMESPathCheck('length(virtualEndpoints)', 2)])

        # test virtual-endpoint update
        update_result = self.cmd('postgres flexible-server virtual-endpoint update -g {} --server-name {} --name {} --endpoint-type {} --members {}'
                .format(resource_group, master_server, virtual_endpoint_name, read_write_endpoint_type, replicas[1]),
                checks=[JMESPathCheck('length(members)', 2)]).get_output_in_json()

        # test virtual-endpoint show
        self.cmd('postgres flexible-server virtual-endpoint show -g {} --server-name {} --name {}'
                .format(resource_group, master_server, virtual_endpoint_name),
                checks=[JMESPathCheck('members', update_result['members'])])

        # test replica switchover planned
        switchover_result = self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option planned --yes'
                .format(resource_group, replicas[1]),
                checks=[
                    JMESPathCheck('name', replicas[1]),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', 'None')]).get_output_in_json()

        # test show server with replication info, master became replica server
        self.cmd('postgres flexible-server show -g {} --name {}'
                .format(resource_group, master_server),
                checks=[
                    JMESPathCheck('replica.role',replica_role),
                    JMESPathCheck('sourceServerResourceId', switchover_result['id'])])

        # test replica switchover forced
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode switchover --promote-option forced --yes'
                .format(resource_group, master_server),
                checks=[
                    JMESPathCheck('name', master_server),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', 'None')])

        # test promote replica standalone forced
        self.cmd('postgres flexible-server replica promote -g {} --name {} --promote-mode standalone --promote-option forced --yes'
                .format(resource_group, replicas[1]),
                checks=[
                    JMESPathCheck('name',replicas[1]),
                    JMESPathCheck('replica.role', primary_role),
                    JMESPathCheck('sourceServerResourceId', 'None')])

        # test virtual-endpoint delete
        self.cmd('postgres flexible-server virtual-endpoint delete -g {} --server-name {} --name {} --yes'
                .format(resource_group, master_server, virtual_endpoint_name))

        # test virtual-endpoint list
        self.cmd('postgres flexible-server virtual-endpoint list -g {} --server-name {}'
                .format(resource_group, master_server),
                expect_failure=True)

        # clean up servers
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replicas[1]), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server))
        
    def _test_postgres_flexible_server_vnet_replica(self, resource_group):
        location = self.postgres_location
        primary_role = 'Primary'
        replica_role = 'AsyncReplica'
        public_access_arg = ''
        public_access_check = []
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        master_vnet = self.create_random_name('VNET', SERVER_NAME_MAX_LENGTH)
        master_subnet = self.create_random_name('SUBNET', SERVER_NAME_MAX_LENGTH)
        master_vnet_args = F'--vnet {master_vnet} --subnet {master_subnet} --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.0.0/24'
        master_vnet_check = [JMESPathCheck('network.delegatedSubnetResourceId', F'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{master_vnet}/subnets/{master_subnet}')]

        # create a server
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} {} --tier GeneralPurpose --sku-name Standard_D2ds_v4 --yes'
                 .format(resource_group, master_server, location, 256, master_vnet_args))
        result = self.cmd('postgres flexible-server show -g {} --name {} '
                          .format(resource_group, master_server),
                          checks=[JMESPathCheck('replica.role', primary_role)] + master_vnet_check).get_output_in_json()
        
        # test replica create
        replica = self.create_random_name(F'azuredbclirep', SERVER_NAME_MAX_LENGTH)
        replica_subnet = self.create_random_name(F'SUBNET1', SERVER_NAME_MAX_LENGTH)
        replica_vnet_args = F'--vnet {master_vnet} --subnet {replica_subnet} --address-prefixes 10.0.0.0/16 --subnet-prefixes 10.0.1.0/24 --yes'
        replica_vnet_check = [JMESPathCheck('network.delegatedSubnetResourceId', F'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Network/virtualNetworks/{master_vnet}/subnets/{replica_subnet}')]
        self.cmd('postgres flexible-server replica create -g {} --name {} --source-server {} --zone 2 {} {}'
                 .format(resource_group, replica, result['id'], replica_vnet_args, public_access_arg),
                 checks=[
                     JMESPathCheck('name', replica),
                     JMESPathCheck('availabilityZone', 2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replica.role', replica_role),
                     JMESPathCheck('sourceServerResourceId', result['id'])] + replica_vnet_check + public_access_check)

        # test replica list
        self.cmd('postgres flexible-server replica list -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test replica promote
        self.cmd('postgres flexible-server replica promote -g {} --name {} --yes'
                 .format(resource_group, replica),
                 checks=[
                     JMESPathCheck('name', replica),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None')])

        # test show server with replication info, master becomes normal server
        self.cmd('postgres flexible-server show -g {} --name {}'
                 .format(resource_group, master_server),
                 checks=[
                     JMESPathCheck('replica.role', primary_role),
                     JMESPathCheck('sourceServerResourceId', 'None')])

        # clean up servers
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, replica), checks=NoneCheck())
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                 .format(resource_group, master_server), checks=NoneCheck())

    def _test_postgres_flexible_server_auto_grow_replica(self, resource_group):
        location = self.postgres_location
        primary_role = 'Primary'
        public_access_arg = ''
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replica_role = 'AsyncReplica'
        replicas = [self.create_random_name(F'azuredbclirep{i+1}', SERVER_NAME_MAX_LENGTH) for i in range(2)]
        storage_auto_grow = "Enabled"

        # create a server
        self.cmd('postgres flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none --tier GeneralPurpose --sku-name Standard_D4ds_v5 --yes --storage-auto-grow Enabled'
                 .format(resource_group, master_server, location, 256))
        result = self.cmd('postgres flexible-server show -g {} --name {} '
                          .format(resource_group, master_server),
                          checks=[
                              JMESPathCheck('replica.role', primary_role),
                              JMESPathCheck('storage.autoGrow', storage_auto_grow)]).get_output_in_json()
        
        # test replica create
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

        # delete replica server first
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, replicas[0]))

        # now we can delete master server
        self.cmd('postgres flexible-server delete -g {} --name {} --yes'
                    .format(resource_group, master_server))