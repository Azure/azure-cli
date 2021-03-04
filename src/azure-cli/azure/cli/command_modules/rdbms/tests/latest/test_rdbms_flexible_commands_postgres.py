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
from .conftest import postgres_location

SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20
RG_NAME_PREFIX = 'clitest.rg'
RG_NAME_MAX_LENGTH = 75

if postgres_location is None:
    postgres_location = 'eastus2euap'


class PostgresFlexibleServerMgmtScenarioTest(FlexibleServerMgmtScenarioTest):

    def __init__(self, method_name):
        super(PostgresFlexibleServerMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        self.random_name_1 = self.create_random_name(SERVER_NAME_PREFIX + '4', SERVER_NAME_MAX_LENGTH)
        self.random_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '5', SERVER_NAME_MAX_LENGTH)
        self.random_name_3 = self.create_random_name(SERVER_NAME_PREFIX + '6', SERVER_NAME_MAX_LENGTH)
        self.current_time = datetime.utcnow()
        self.location = postgres_location

    @pytest.mark.order(1)
    def test_postgres_flexible_server_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(postgres_location, self.resource_group))
        self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('postgres', postgres_location, self.resource_group, self.server))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_mgmt_prepare'])
    def test_postgres_flexible_server_create(self):
        self._test_flexible_server_create('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_create'])
    def test_postgres_flexible_server_update_password(self):
        self._test_flexible_server_update_password('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_password'])
    def test_postgres_flexible_server_update_storage(self):
        self._test_flexible_server_update_storage('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_storage'])
    def test_postgres_flexible_server_update_backup_retention(self):
        self._test_flexible_server_update_backup_retention('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_backup_retention'])
    def test_postgres_flexible_server_update_scale_up(self):
        self._test_flexible_server_update_scale_up('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_scale_up'])
    def test_postgres_flexible_server_update_scale_down(self):
        self._test_flexible_server_update_scale_down('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_scale_down'])
    def test_postgres_flexible_server_upadte_mmw(self):
        self._test_flexible_server_upadte_mmw('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_upadte_mmw'])
    def test_postgres_flexible_server_update_tag(self):
        self._test_flexible_server_update_tag('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_update_tag'])
    def test_postgres_flexible_server_restart(self):
        self._test_flexible_server_restart('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(11)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_restart'])
    def test_postgres_flexible_server_stop(self):
        self._test_flexible_server_stop('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(12)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_stop'])
    def test_postgres_flexible_server_start(self):
        self._test_flexible_server_start('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(13)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_start'])
    def test_postgres_flexible_server_list(self):
        self._test_flexible_server_list('postgres', self.resource_group)
        self._test_flexible_server_connection_string('postgres', self.server)

    @AllowLargeResponse()
    @pytest.mark.order(14)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_list'])
    def test_postgres_flexible_server_list_skus(self):
        self._test_flexible_server_list_skus('postgres', self.location)

    @AllowLargeResponse()
    @pytest.mark.order(15)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_list_skus'])
    def test_postgres_flexible_server_create_non_default_tiers_select_zone(self):
        self._test_flexible_server_create_non_default_tiers('postgres', self.resource_group)

    @AllowLargeResponse()
    @pytest.mark.order(16)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_create_non_default_tiers_select_zone'])
    def test_postgres_flexible_server_create_different_version(self):
        self._test_flexible_server_create_different_version('postgres', self.resource_group)

    @AllowLargeResponse()
    @pytest.mark.order(17)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_create_different_version'])
    def test_postgres_flexible_server_restore(self):
        self._test_flexible_server_restore('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(18)
    @pytest.mark.depends(on=['PostgresFlexibleServerMgmtScenarioTest::test_postgres_flexible_server_restore'])
    def test_postgres_flexible_server_delete(self):
        self.cmd('az group delete --name {} --yes --no-wait'.format(self.resource_group))


class PostgresFlexibleServerHighAvailabilityMgmt(FlexibleServerHighAvailabilityMgmt):

    def __init__(self, method_name):
        super(PostgresFlexibleServerHighAvailabilityMgmt, self).__init__(method_name)
        self.current_time = datetime.utcnow()
        self.location = postgres_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

    @pytest.mark.order(1)
    def test_postgres_flexible_server_high_availability_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(postgres_location, self.resource_group))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_prepare'])
    def test_postgres_flexible_server_high_availability_create(self):
        self._test_flexible_server_high_availability_create('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_create'])
    def test_postgres_flexible_server_high_availability_disable(self):
        self._test_flexible_server_high_availability_disable('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_disable'])
    def test_postgres_flexible_server_high_availability_enable(self):
        self._test_flexible_server_high_availability_enable('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_enable'])
    def test_postgres_flexible_server_high_availability_update_scale_up(self):
        self._test_flexible_server_high_availability_update_scale_up('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_update_scale_up'])
    def test_postgres_flexible_server_high_availability_update_parameter(self):
        self._test_flexible_server_high_availability_update_parameter('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_update_parameter'])
    def test_postgres_flexible_server_high_availability_restart(self):
        self._test_flexible_server_high_availability_restart('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_restart'])
    def test_postgres_flexible_server_high_availability_stop(self):
        self._test_flexible_server_high_availability_stop('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_stop'])
    def test_postgres_flexible_server_high_availability_start(self):
        self._test_flexible_server_high_availability_start('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(10)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_start'])
    def test_postgres_flexible_server_high_availability_restore(self):
        self._test_flexible_server_high_availability_restore('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(11)
    @pytest.mark.depends(on=['PostgresFlexibleServerHighAvailabilityMgmt::test_postgres_flexible_server_high_availability_restore'])
    def test_postgres_flexible_server_high_availability_delete(self):
        self._test_flexible_server_high_availability_delete(self.resource_group)


class PostgresFlexibleServerVnetServerMgmtScenarioTest(FlexibleServerVnetServerMgmtScenarioTest):

    def __init__(self, method_name):
        super(PostgresFlexibleServerVnetServerMgmtScenarioTest, self).__init__(method_name)
        self.location = postgres_location
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        self.server_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        self.restore_server = 'restore-' + self.server[:55]
        self.restore_server_2 = 'restore-' + self.server_2[:55]

    @pytest.mark.order(1)
    def test_postgres_flexible_server_vnet_server_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(postgres_location, self.resource_group))

    @unittest.skip("Takes too long. Need to re-record.")
    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_prepare'])
    def test_postgres_flexible_server_vnet_server_create(self):
        self._test_flexible_server_vnet_server_create('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_create'])
    def test_postgres_flexible_server_vnet_server_update_scale_up(self):
        self._test_flexible_server_vnet_server_update_scale_up('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(4)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_update_scale_up'])
    def test_postgres_flexible_server_vnet_server_restore(self):
        self._test_flexible_server_vnet_server_restore('postgres', self.resource_group, self.server, self.restore_server)

    @AllowLargeResponse()
    @pytest.mark.order(5)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_restore'])
    def test_postgres_flexible_server_vnet_server_delete(self):
        self._test_flexible_server_vnet_server_delete('postgres', self.resource_group, self.server, self.restore_server)

    @unittest.skip("Takes too long. Need to re-record.")
    @AllowLargeResponse()
    @pytest.mark.order(6)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_prepare'])
    def test_postgres_flexible_server_vnet_ha_server_create(self):
        self._test_flexible_server_vnet_ha_server_create('postgres', self.resource_group, self.server_2)

    @AllowLargeResponse()
    @pytest.mark.order(7)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_ha_server_create'])
    def test_postgres_flexible_server_vnet_ha_server_update_scale_up(self):
        self._test_flexible_server_vnet_server_update_scale_up('postgres', self.resource_group, self.server_2)

    @AllowLargeResponse()
    @pytest.mark.order(8)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_ha_server_update_scale_up'])
    def test_postgres_flexible_server_vnet_ha_server_restore(self):
        self._test_flexible_server_vnet_server_restore('postgres', self.resource_group, self.server_2, self.restore_server_2)

    @AllowLargeResponse()
    @pytest.mark.order(9)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_ha_server_restore'])
    def test_postgres_flexible_server_vnet_ha_server_delete(self):
        self._test_flexible_server_vnet_server_delete('postgres', self.resource_group, self.server_2, self.restore_server_2)

    @pytest.mark.order(10)
    @pytest.mark.depends(on=['PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_ha_server_delete', 'PostgresFlexibleServerVnetServerMgmtScenarioTest::test_postgres_flexible_server_vnet_server_delete'])
    def test_postgres_flexible_server_vnet_server_mgmt_delete(self):
        self._test_flexible_server_vnet_server_mgmt_delete(self.resource_group)


class PostgresFlexibleServerProxyResourceMgmtScenarioTest(FlexibleServerProxyResourceMgmtScenarioTest):

    postgres_location = postgres_location

    def __init__(self, method_name):
        super(PostgresFlexibleServerProxyResourceMgmtScenarioTest, self).__init__(method_name)
        self.resource_group = self.create_random_name(RG_NAME_PREFIX, RG_NAME_MAX_LENGTH)
        self.server = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

    @AllowLargeResponse()
    @pytest.mark.order(1)
    def test_postgres_flexible_server_proxy_resource_mgmt_prepare(self):
        self.cmd('az group create --location {} --name {}'.format(postgres_location, self.resource_group))
        self.cmd('az {} flexible-server create -l {} -g {} -n {} --public-access none'.format('postgres', postgres_location, self.resource_group, self.server))

    @AllowLargeResponse()
    @pytest.mark.order(2)
    @pytest.mark.depends(on=['PostgresFlexibleServerProxyResourceMgmtScenarioTest::test_postgres_flexible_server_proxy_resource_mgmt_prepare'])
    def test_postgres_flexible_server_firewall_rule_mgmt(self):
        self._test_firewall_rule_mgmt('postgres', self.resource_group, self.server)

    @AllowLargeResponse()
    @pytest.mark.order(3)
    @pytest.mark.depends(on=['PostgresFlexibleServerProxyResourceMgmtScenarioTest::test_postgres_flexible_server_firewall_rule_mgmt'])
    def test_postgres_flexible_server_parameter_mgmt(self):
        self._test_parameter_mgmt('postgres', self.resource_group, self.server)

    @pytest.mark.order(4)
    @pytest.mark.depends(on=['PostgresFlexibleServerProxyResourceMgmtScenarioTest::test_postgres_flexible_server_parameter_mgmt'])
    def test_postgres_flexible_server_proxy_resource_mgmt_delete(self):
        self._test_flexible_server_proxy_resource_mgmt_delete(self.resource_group)


class PostgresFlexibleServerValidatorScenarioTest(FlexibleServerValidatorScenarioTest):

    postgres_location = postgres_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('postgres', resource_group)


class PostgresFlexibleServerVnetMgmtScenarioTest(FlexibleServerVnetMgmtScenarioTest):

    postgres_location = postgres_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @VirtualNetworkPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('postgres', resource_group)
        # Provision a server with supplied Subnet ID whose vnet exists, but subnet does not exist and the vnet does not contain any other subnet
        self._test_flexible_server_vnet_mgmt_non_existing_supplied_subnetid('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vnet('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @VirtualNetworkPreparer(parameter_name='virtual_network', location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group, virtual_network):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('postgres', resource_group, virtual_network)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('postgres', resource_group_1, resource_group_2)


class PostgresFlexibleServerPublicAccessMgmtScenarioTest(FlexibleServerPublicAccessMgmtScenarioTest):

    postgres_location = postgres_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)
