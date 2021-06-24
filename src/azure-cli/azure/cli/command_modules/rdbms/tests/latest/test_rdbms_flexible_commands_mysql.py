# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pytest
import os
import time
import unittest
from datetime import datetime, timedelta, tzinfo
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ScenarioTest,
    StringContainCheck,
    ResourceGroupPreparer,
    VirtualNetworkPreparer,
    LocalContextScenarioTest,
    live_only)
from .test_rdbms_flexible_commands import (
    RdbmsScenarioTest,
    ServerPreparer,
    FlexibleServerMgmtScenarioTest,
    FlexibleServerIopsMgmtScenarioTest,
    FlexibleServerHighAvailabilityMgmt,
    FlexibleServerVnetServerMgmtScenarioTest,
    FlexibleServerProxyResourceMgmtScenarioTest,
    FlexibleServerValidatorScenarioTest,
    FlexibleServerReplicationMgmtScenarioTest,
    FlexibleServerVnetMgmtScenarioTest,
    FlexibleServerPublicAccessMgmtScenarioTest
)
from .conftest import mysql_location

SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20
RG_NAME_PREFIX = 'clitest.rg'
RG_NAME_MAX_LENGTH = 75

if mysql_location is None:
    mysql_location = 'eastus2euap'


class MySqlFlexibleServerMgmtScenarioTest(FlexibleServerMgmtScenarioTest):

    def __init__(self, method_name):
        super(MySqlFlexibleServerMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        self.random_name_1 = self.create_random_name(SERVER_NAME_PREFIX + '1', SERVER_NAME_MAX_LENGTH)
        self.random_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        self.random_name_3 = self.create_random_name(SERVER_NAME_PREFIX + '3', SERVER_NAME_MAX_LENGTH)
        self.current_time = datetime.utcnow()
        self.location = mysql_location

    @pytest.mark.order(1)
    def test_mysql_flexible_server_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(mysql_location, self.resource_group))
        self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('mysql', mysql_location, self.resource_group, self.server))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    def test_mysql_flexible_server_create(self):
        self._test_flexible_server_create('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    def test_mysql_flexible_server_update_password(self):
        self._test_flexible_server_update_password('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    def test_mysql_flexible_server_update_storage(self):
        self._test_flexible_server_update_storage('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    def test_mysql_flexible_server_update_backup_retention(self):
        self._test_flexible_server_update_backup_retention('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    def test_mysql_flexible_server_update_scale_up(self):
        self._test_flexible_server_update_scale_up('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    def test_mysql_flexible_server_update_scale_down(self):
        self._test_flexible_server_update_scale_down('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    def test_mysql_flexible_server_update_mmw(self):
        self._test_flexible_server_update_mmw('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    def test_mysql_flexible_server_update_tag(self):
        self._test_flexible_server_update_tag('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    def test_mysql_flexible_server_restart(self):
        self._test_flexible_server_restart('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    def test_mysql_flexible_server_stop(self):
        self._test_flexible_server_stop('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(11)
    def test_mysql_flexible_server_start(self):
        self._test_flexible_server_start('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(12)
    def test_mysql_flexible_server_list(self):
        self._test_flexible_server_list('mysql', self.resource_group)
        self._test_flexible_server_connection_string('mysql', self.server)

    @AllowLargeResponse()
    @pytest.mark.order(13)
    def test_mysql_flexible_server_list_skus(self):
        self._test_flexible_server_list_skus('mysql', self.location)

    @AllowLargeResponse()
    @pytest.mark.order(14)
    def test_mysql_flexible_server_restore(self):
        self._test_flexible_server_restore('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(15)
    def test_mysql_flexible_server_create_non_default_tiers(self):
        self._test_flexible_server_create_non_default_tiers('mysql', self.resource_group)

    @AllowLargeResponse()
    @pytest.mark.order(16)
    def test_mysql_flexible_server_delete(self):
        self.cmd('az group delete --name {} --yes --no-wait'.format(self.resource_group))


class MySqlFlexibleServerIopsMgmtScenarioTest(FlexibleServerIopsMgmtScenarioTest):

    def __init__(self, method_name):
        super(MySqlFlexibleServerIopsMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server_1 = self.create_random_name(SERVER_NAME_PREFIX + '1', SERVER_NAME_MAX_LENGTH)
        self.server_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        self.server_3 = self.create_random_name(SERVER_NAME_PREFIX + '3', SERVER_NAME_MAX_LENGTH)
        self.location = mysql_location

    @AllowLargeResponse()
    @pytest.mark.order(1)
    def test_mysql_flexible_server_iops_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(mysql_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    def test_mysql_flexible_server_iops_create(self):
        self._test_flexible_server_iops_create('mysql', self.resource_group, self.server_1, self.server_2, self.server_3)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    def test_mysql_flexible_server_iops_scale_up(self):
        self._test_flexible_server_iops_scale_up('mysql', self.resource_group, self.server_1, self.server_2, self.server_3)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    def test_mysql_flexible_server_iops_scale_down(self):
        self._test_flexible_server_iops_scale_down('mysql', self.resource_group, self.server_1, self.server_2, self.server_3)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    def test_mysql_flexible_server_iops_delete(self):
        self.cmd('az group delete --name {} --yes --no-wait'.format(self.resource_group))


class MySqlFlexibleServerProxyResourceMgmtScenarioTest(FlexibleServerProxyResourceMgmtScenarioTest):

    mysql_location = mysql_location

    def __init__(self, method_name):
        super(MySqlFlexibleServerProxyResourceMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

    @AllowLargeResponse()
    @pytest.mark.order(1)
    def test_mysql_flexible_server_proxy_resource_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(mysql_location, self.resource_group))
        self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('mysql', mysql_location, self.resource_group, self.server))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    def test_mysql_flexible_server_firewall_rule_mgmt(self):
        self._test_firewall_rule_mgmt('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    def test_mysql_flexible_server_parameter_mgmt(self):
        self._test_parameter_mgmt('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    def test_mysql_flexible_server_database_mgmt(self):
        self._test_database_mgmt('mysql', self.resource_group, self.server)

    @pytest.mark.order(5)
    def test_mysql_flexible_server_proxy_resource_mgmt_delete(self):
        self._test_flexible_server_proxy_resource_mgmt_delete(self.resource_group)


class MySqlFlexibleServerValidatorScenarioTest(FlexibleServerValidatorScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('mysql', resource_group)


class MySqlFlexibleServerReplicationMgmtScenarioTest(FlexibleServerReplicationMgmtScenarioTest):  # pylint: disable=too-few-public-methods

    mysql_location = mysql_location

    def __init__(self, method_name):
        super(MySqlFlexibleServerReplicationMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.master_server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        self.replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                         self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]
        self.location = mysql_location
        self.result = None

    @AllowLargeResponse()
    @pytest.mark.order(1)
    def test_mysql_flexible_server_replica_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(mysql_location, self.resource_group))
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none'
                 .format('mysql', self.resource_group, self.master_server, mysql_location, 256))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    def test_mysql_flexible_server_replica_create(self):
        self._test_flexible_server_replica_create('mysql', self.resource_group, self.master_server, self.replicas)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    def test_mysql_flexible_server_replica_list(self):
        self._test_flexible_server_replica_list('mysql', self.resource_group, self.master_server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    def test_mysql_flexible_server_replica_stop(self):
        self._test_flexible_server_replica_stop('mysql', self.resource_group, self.master_server, self.replicas)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    def test_mysql_flexible_server_replica_delete_source(self):
        self._test_flexible_server_replica_delete_source('mysql', self.resource_group, self.master_server, self.replicas)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    def test_mysql_flexible_server_replica_delete(self):
        self._test_flexible_server_replica_delete('mysql', self.resource_group, self.replicas)


class MySqlFlexibleServerHighAvailabilityMgmt(FlexibleServerHighAvailabilityMgmt):

    def __init__(self, method_name):
        super(MySqlFlexibleServerHighAvailabilityMgmt, self).__init__(method_name)
        self.current_time = datetime.utcnow()
        self.location = mysql_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

    @pytest.mark.order(1)
    def test_mysql_flexible_server_high_availability_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(mysql_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    def test_mysql_flexible_server_high_availability_create(self):
        self._test_flexible_server_high_availability_create('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    def test_mysql_flexible_server_high_availability_update_scale_up(self):
        self._test_flexible_server_high_availability_update_scale_up('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    def test_mysql_flexible_server_high_availability_update_parameter(self):
        self._test_flexible_server_high_availability_update_parameter('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    def test_mysql_flexible_server_high_availability_restart(self):
        self._test_flexible_server_high_availability_restart('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    def test_mysql_flexible_server_high_availability_stop(self):
        self._test_flexible_server_high_availability_stop('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    def test_mysql_flexible_server_high_availability_start(self):
        self._test_flexible_server_high_availability_start('mysql', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    def test_mysql_flexible_server_high_availability_delete(self):
        self._test_flexible_server_high_availability_delete(self.resource_group)


class MySqlFlexibleServerVnetMgmtScenarioTest(FlexibleServerVnetMgmtScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @VirtualNetworkPreparer(location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('mysql', resource_group)
        # Provision a server with supplied Subnet ID whose vnet exists, but subnet does not exist and the vnet does not contain any other subnet
        self._test_flexible_server_vnet_mgmt_non_existing_supplied_subnetid('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_vnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vnet('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @VirtualNetworkPreparer(parameter_name='virtual_network', location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group, virtual_network):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('mysql', resource_group, virtual_network)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_2')
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('mysql', resource_group_1, resource_group_2)


class MySqlFlexibleServerPublicAccessMgmtScenarioTest(FlexibleServerPublicAccessMgmtScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @live_only()
    def test_mysql_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)
