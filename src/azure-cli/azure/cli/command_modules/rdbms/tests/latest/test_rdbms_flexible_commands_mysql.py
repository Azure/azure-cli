# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import pytest
import os
from datetime import datetime, timedelta, tzinfo
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StringContainCheck,
    VirtualNetworkPreparer,
    LocalContextScenarioTest,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from .test_rdbms_flexible_commands import (
    ServerPreparer,
    FlexibleServerMgmtScenarioTest,
    FlexibleServerProxyResourceMgmtScenarioTest,
    FlexibleServerValidatorScenarioTest,
    FlexibleServerReplicationMgmtScenarioTest,
    FlexibleServerVnetMgmtScenarioTest,
    FlexibleServerPublicAccessMgmtScenarioTest
)
from .conftest import mysql_location


class MySqlFlexibleServerMgmtScenarioTest(FlexibleServerMgmtScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @ServerPreparer(engine_type='mysql', location=mysql_location)
    def test_mysql_flexible_server_mgmt(self, resource_group, server):
        self._test_flexible_server_mgmt('mysql', resource_group, server)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_iops_mgmt(self, resource_group):
        self._test_flexible_server_iops_mgmt('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_high_availability_mgmt(self, resource_group):
        self._test_flexible_server_high_availability_mgmt('mysql', resource_group)


class MySqlFlexibleServerProxyResourceMgmtScenarioTest(FlexibleServerProxyResourceMgmtScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @ServerPreparer(engine_type='mysql', location=mysql_location)
    def test_mysql_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('mysql', resource_group, server)
        self._test_parameter_mgmt('mysql', resource_group, server)
        self._test_database_mgmt('mysql', resource_group, server)


class MySqlFlexibleServerValidatorScenarioTest(FlexibleServerValidatorScenarioTest):

    mysql_location = mysql_location

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('mysql', resource_group)


class MySqlFlexibleServerReplicationMgmtScenarioTest(FlexibleServerReplicationMgmtScenarioTest):  # pylint: disable=too-few-public-methods

    mysql_location = mysql_location

    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('mysql', resource_group)


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
