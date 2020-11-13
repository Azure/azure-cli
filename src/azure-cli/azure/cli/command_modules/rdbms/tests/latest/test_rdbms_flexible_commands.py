# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from datetime import datetime, timedelta, tzinfo
from time import sleep
from dateutil.tz import tzutc
from azure_devtools.scenario_tests import AllowLargeResponse
from msrestazure.azure_exceptions import CloudError
from azure.cli.core.local_context import AzCLILocalContext, ALL, LOCAL_CONTEXT_FILE
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
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

# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20


class ServerPreparer(AbstractPreparer, SingleValueReplacer):

    def __init__(self, engine_type, location, engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server',
                 resource_group_parameter_name='resource_group'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.engine_type = engine_type
        self.engine_parameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.resource_group_parameter_name = resource_group_parameter_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} flexible-server create -l {} -g {} -n {}'
        execute(self.cli_ctx, template.format(self.engine_type,
                                              self.location,
                                              group, name))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    def remove_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        execute(self.cli_ctx, 'az {} flexible-server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)


class FlexibleServerMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt(self, resource_group):
        self._test_flexible_server_mgmt('mysql', resource_group)

    def _test_flexible_server_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D2s_v3'
            version = '12'
            storage_size = 128
            location = self.postgres_location
            location_result = 'East US'
        elif database_engine == 'mysql':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
            storage_size = 10
            version = '5.7'
            location = self.mysql_location
            location_result = 'West US 2'

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        storage_size_mb = storage_size * 1024
        backup_retention = 7

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('location', location_result),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {}'
                 .format(database_engine, resource_group, server_name))
        current_time = datetime.utcnow()

        if database_engine == 'postgres':
            self.cmd('postgres flexible-server create -g {} -l {} --tier Burstable --sku-name Standard_B1ms'
                     .format(resource_group, location))
            self.cmd('postgres flexible-server create -g {} -l {} --tier MemoryOptimized --sku-name Standard_E2s_v3'
                     .format(resource_group, location))
        elif database_engine == 'mysql':
            self.cmd('mysql flexible-server create -g {} -l {} --tier GeneralPurpose --sku-name Standard_D2ds_v4'
                     .format(resource_group, location))
            self.cmd('mysql flexible-server create -g {} -l {} --tier MemoryOptimized --sku-name Standard_E2ds_v4'
                     .format(resource_group, location))

        show_output = self.cmd('{} flexible-server show -g {} -n {}'
                               .format(database_engine, resource_group, server_name), checks=list_checks).get_output_in_json()
        self.assertIn('subnetArmResourceId', show_output["delegatedSubnetArguments"])

        if database_engine == 'mysql':
            self.cmd('{} flexible-server db show -g {} -s {} -d flexibleserverdb'
                     .format(database_engine, resource_group, server_name), checks=[JMESPathCheck('name', 'flexibleserverdb')])

        self.cmd('{} flexible-server update -g {} -n {} --storage-size 256'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storageProfile.storageMb', 256 * 1024)])

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'
                 .format(database_engine, resource_group, server_name, backup_retention + 10),
                 checks=[JMESPathCheck('storageProfile.backupRetentionDays', backup_retention + 10)])

        if database_engine == 'postgres':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D2ds_v4'

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server_name, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

        if database_engine == 'postgres':
            self.cmd('{} flexible-server update -g {} -n {} --maintenance-window Mon:1:30'
                     .format(database_engine, resource_group, server_name),
                     checks=[JMESPathCheck('maintenanceWindow.dayOfWeek', 1),
                             JMESPathCheck('maintenanceWindow.startHour', 1),
                             JMESPathCheck('maintenanceWindow.startMinute', 30)])

        self.cmd('{} flexible-server update -g {} -n {} --tags key=3'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('tags.key', '3')])

        restore_server_name = 'restore-' + server_name
        restore_time = (current_time + timedelta(minutes=10)).replace(tzinfo=tzutc()).isoformat()
        self.cmd('{} flexible-server restore -g {} --name {} --source-server {} --restore-time {}'
                 .format(database_engine, resource_group, restore_server_name, server_name, restore_time),
                 checks=[JMESPathCheck('name', restore_server_name),
                         JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('{} flexible-server restart -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server stop -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server start -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server list -g {}'.format(database_engine, resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])

        connection_string = self.cmd('{} flexible-server show-connection-string -s {}'
                                     .format(database_engine, server_name)).get_output_in_json()

        self.assertIn('jdbc', connection_string['connectionStrings'])
        self.assertIn('node.js', connection_string['connectionStrings'])
        self.assertIn('php', connection_string['connectionStrings'])
        self.assertIn('python', connection_string['connectionStrings'])
        self.assertIn('ado.net', connection_string['connectionStrings'])

        self.cmd('{} flexible-server list-skus -l {}'.format(database_engine, location),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())


class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('postgres', resource_group, server)
        self._test_parameter_mgmt('postgres', resource_group, server)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @ServerPreparer(engine_type='mysql', location=mysql_location)
    def test_mysql_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('mysql', resource_group, server)
        self._test_parameter_mgmt('mysql', resource_group, server)
        self._test_database_mgmt('mysql', resource_group, server)

    def _test_firewall_rule_mgmt(self, database_engine, resource_group, server):

        firewall_rule_name = 'firewall_test_rule'
        start_ip_address = '10.10.10.10'
        end_ip_address = '12.12.12.12'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]

        self.cmd('{} flexible-server firewall-rule create -g {} --name {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule show -g {} --name {} --rule-name {} '
                 .format(database_engine, resource_group, server, firewall_rule_name),
                 checks=firewall_rule_checks)

        new_start_ip_address = '9.9.9.9'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --start-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_start_ip_address),
                 checks=[JMESPathCheck('startIpAddress', new_start_ip_address)])

        new_end_ip_address = '13.13.13.13'
        self.cmd('{} flexible-server firewall-rule update -g {} --name {} --rule-name {} --end-ip-address {}'
                 .format(database_engine, resource_group, server, firewall_rule_name, new_end_ip_address))

        new_firewall_rule_name = 'firewall_test_rule2'
        firewall_rule_checks = [JMESPathCheck('name', new_firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]
        self.cmd('{} flexible-server firewall-rule create -g {} -n {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server, new_firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} flexible-server firewall-rule delete --rule-name {} -g {} --name {} --yes'
                 .format(database_engine, firewall_rule_name, resource_group, server), checks=NoneCheck())

        self.cmd('{} flexible-server firewall-rule list -g {} --name {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 1)])

        self.cmd('{} flexible-server firewall-rule delete -g {} -n {} --rule-name {} --yes'
                 .format(database_engine, resource_group, server, new_firewall_rule_name))

        self.cmd('{} flexible-server firewall-rule list -g {} -n {}'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

    def _test_parameter_mgmt(self, database_engine, resource_group, server):

        self.cmd('{} flexible-server parameter list -g {} -s {}'.format(database_engine, resource_group, server), checks=[JMESPathCheck('type(@)', 'array')])

        if database_engine == 'mysql':
            parameter_name = 'wait_timeout'
            default_value = '28800'
            value = '30000'
        elif database_engine == 'postgres':
            parameter_name = 'lock_timeout'
            default_value = '0'
            value = '2000'

        source = 'system-default'
        self.cmd('{} flexible-server parameter show --name {} -g {} -s {}'.format(database_engine, parameter_name, resource_group, server),
                 checks=[JMESPathCheck('defaultValue', default_value),
                         JMESPathCheck('source', source)])

        source = 'user-override'
        self.cmd('{} flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(database_engine, parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])

    def _test_database_mgmt(self, database_engine, resource_group, server):

        database_name = self.create_random_name('database', 20)

        self.cmd('{} flexible-server db create -g {} -s {} -d {} --collation utf8'.format(database_engine, resource_group, server, database_name),
                 checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('{} flexible-server db list -g {} -s {} '.format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('{} flexible-server db delete -g {} -s {} -d {} --yes'.format(database_engine, resource_group, server, database_name),
                 checks=NoneCheck())


class FlexibleServerValidatorScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_mgmt_validator(self, resource_group):
        self._test_mgmt_validator('mysql', resource_group)

    def _test_mgmt_validator(self, database_engine, resource_group):

        RANDOM_VARIABLE_MAX_LENGTH = 30
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 1

        # Create
        self.cmd('{} flexible-server create -g {} -l {} --tier {}'.format(database_engine, resource_group, location, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --version {}'.format(database_engine, resource_group, location, invalid_version), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --tier {} --sku-name {}'.format(database_engine, resource_group, location, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -l {} --backup-retention {}'.format(database_engine, resource_group, location, invalid_backup_retention), expect_failure=True)

        if database_engine == 'postgres':
            invalid_storage_size = 60
        elif database_engine == 'mysql':
            invalid_storage_size = 999999
        self.cmd('{} flexible-server create -g {} -l {} --storage-size {}'.format(database_engine, resource_group, location, invalid_storage_size), expect_failure=True)

        server_name = self.create_random_name(SERVER_NAME_PREFIX, RANDOM_VARIABLE_MAX_LENGTH)
        if database_engine == 'postgres':
            tier = 'MemoryOptimized'
            version = 12
            sku_name = 'Standard_E2s_v3'
            storage_size = 64
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            version = 5.7
            sku_name = 'Standard_D2ds_v4'
            storage_size = 20
        storage_size_mb = storage_size * 1024
        backup_retention = 10

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --version {} --sku-name {} --storage-size {} --backup-retention {}'
                 .format(database_engine, resource_group, server_name, location, tier, version, sku_name, storage_size, backup_retention))
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name), checks=list_checks)

        # Update
        invalid_storage_size_small = storage_size - 1
        self.cmd('{} flexible-server update -g {} -n {} --tier {}'.format(database_engine, resource_group, server_name, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'.format(database_engine, resource_group, server_name, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --storage-size {}'.format(database_engine, resource_group, server_name, invalid_storage_size_small), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'.format(database_engine, resource_group, server_name, invalid_backup_retention), expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())


class FlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    mysql_location = 'westus2'

    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('mysql', resource_group)

    def _test_flexible_server_replica_mgmt(self, database_engine, resource_group):
        location = self.mysql_location
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {}'
                 .format(database_engine, resource_group, master_server, location, 256))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'None')]).get_output_in_json()

        # test replica create
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.tier', result['sku']['tier']),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        # test replica list
        self.cmd('{} flexible-server replica list -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test replica stop
        self.cmd('{} flexible-server replica stop-replication -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, master_server),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test delete master server
        self.cmd('{} flexible-server replica create -g {} --replica-name {} --source-server {}'
                 .format(database_engine, resource_group, replicas[1], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[1]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('sourceServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, master_server), checks=NoneCheck())

        # test show server with replication info, replica was auto stopped after master server deleted
        self.cmd('{} flexible-server show -g {} --name {}'
                 .format(database_engine, resource_group, replicas[1]),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('sourceServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # clean up servers
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} flexible-server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())


class FlexibleServerVnetMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @VirtualNetworkPreparer()
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('mysql', resource_group)
        # Provision a server with supplied Subnet ID whose vnet exists, but subnet does not exist and the vnet does not contain any other subnet
        self._test_flexible_server_vnet_mgmt_non_existing_supplied_subnetid('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @VirtualNetworkPreparer()
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
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_vnet_mgmt_supplied_vnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vnet('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @VirtualNetworkPreparer(parameter_name='virtual_network')
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group, virtual_network):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('postgres', resource_group, virtual_network)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @VirtualNetworkPreparer(parameter_name='virtual_network')
    def test_mysql_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group, virtual_network):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('mysql', resource_group, virtual_network)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('postgres', resource_group_1, resource_group_2)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_2')
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('mysql', resource_group_1, resource_group_2)

    def _test_flexible_server_vnet_mgmt_existing_supplied_subnetid(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        server = 'testvnetserver1' + database_engine

        # Scenario : Provision a server with supplied Subnet ID that exists, where the subnet is not delegated

        subnet_id = self.cmd('network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()['id']

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {}'
                 .format(database_engine, resource_group, server, subnet_id))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'], subnet_id)
        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server),
                 checks=NoneCheck())

    def _test_flexible_server_vnet_mgmt_non_existing_supplied_subnetid(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        vnet_name_2 = 'clitestvnet1'
        subnet_name_2 = 'clitestsubnet1'
        server = 'testvnetserver2' + database_engine

        # Scenario : Provision a server with supplied Subnet ID whose vnet exists, but subnet does not exist and the vnet does not contain any other subnet
        # The subnet name is the default created one, not the one in subnet ID
        self.cmd('{} flexible-server create -g {} -n {} --subnet {}'
                 .format(database_engine, resource_group, server, '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(self.get_subscription_id(), resource_group, vnet_name_2, subnet_name_2)))

        # flexible-server show to validate delegation is added to both the created server
        show_result = self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server)).get_output_in_json()

        self.assertEqual(show_result['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + server[6:]))

        # Cleanup
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server), checks=NoneCheck())
        # This is required because the delegations cannot be removed until the server is completely deleted. In the current implementation, there is a delay. Hence, the wait
        time.sleep(15 * 60)
        # remove delegations from vnet
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group,
                                                                                                         'Subnet' + server[6:],
                                                                                                         vnet_name_2))
        # remove  vnet
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, vnet_name_2))

    def _test_flexible_server_vnet_mgmt_supplied_vnet(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        vnet_name = 'clitestvnet2'
        address_prefix = '10.0.0.0/16'
        subnet_prefix_1 = '10.0.0.0/24'
        vnet_name_2 = 'clitestvnet3'

        # flexible-servers
        servers = ['testvnetserver3' + database_engine, 'testvnetserver4' + database_engine]

        # Case 1 : Provision a server with supplied Vname that exists.

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        vnet_result = self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
                               .format(vnet_name, resource_group, location, address_prefix, 'Subnet' + servers[0][6:], subnet_prefix_1)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {}'
                 .format(database_engine, resource_group, servers[0], vnet_result['newVNet']['name']))

        # Case 2 : Provision a server with a supplied Vname that does not exist.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {}'
                 .format(database_engine, resource_group, servers[1], vnet_name_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name, 'Subnet' + servers[0][6:]))

        self.assertEqual(show_result_2['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1][6:]))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group,
                                                                                                         'Subnet' + servers[0][6:],
                                                                                                         vnet_name))

        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group,
                                                                                                         'Subnet' + servers[1][6:],
                                                                                                         vnet_name_2))

        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, vnet_name))
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, vnet_name_2))

    def _test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, database_engine, resource_group, virtual_network):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        vnet_name_2 = 'clitestvnet6'

        # flexible-servers
        servers = ['testvnetserver5' + database_engine, 'testvnetserver6' + database_engine]

        # Case 1 : Provision a server with supplied Vname and subnet name that exists.

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        subnet_id = self.cmd('network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()[
            'id']
        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {} --subnet default'
                 .format(database_engine, resource_group, servers[0], virtual_network))

        # Case 2 : Provision a server with a supplied Vname and subnet name that does not exist.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {}'
                 .format(database_engine, resource_group, servers[1], vnet_name_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'], subnet_id)

        self.assertEqual(show_result_2['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1][6:]))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group,
                                                                                                         'Subnet' + servers[1][6:],
                                                                                                         vnet_name_2))

        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group, vnet_name_2))

    def _test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, database_engine, resource_group_1, resource_group_2):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        vnet_name = 'clitestvnet7'
        subnet_name = 'clitestsubnet7'
        address_prefix = '10.0.0.0/16'
        subnet_prefix_1 = '10.0.0.0/24'
        vnet_name_2 = 'clitestvnet8'
        subnet_name_2 = 'clitestsubnet8'

        # flexible-servers
        servers = ['testvnetserver7' + database_engine, 'testvnetserver8' + database_engine]

        # Case 1 : Provision a server with supplied subnetid that exists in a different RG

        # create vnet and subnet.
        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group_1, location, address_prefix, subnet_name,
                    subnet_prefix_1)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {}'
                 .format(database_engine, resource_group_2, servers[0], vnet_result['newVNet']['subnets'][0]['id']))

        # Case 2 : Provision a server with supplied subnetid that has a different RG in the ID but does not exist. The vnet and subnet is then created in the RG of the server
        self.cmd('{} flexible-server create -g {} -n {} --subnet {}'
                 .format(database_engine, resource_group_2, servers[1], '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group_1, vnet_name_2, subnet_name_2)))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group_2, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group_2, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_1, vnet_name, subnet_name))

        self.assertEqual(show_result_2['delegatedSubnetArguments']['subnetArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_2, vnet_name_2, 'Subnet' + servers[1][6:]))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1,
                                                                                                         subnet_name,
                                                                                                         vnet_name))

        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_2,
                                                                                                         'Subnet' +
                                                                                                         servers[1][6:],
                                                                                                         vnet_name_2))

        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_1, vnet_name))
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_2, vnet_name_2))


class FlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @live_only()
    def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)

    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            sku_name = 'Standard_D2s_v3'
        elif database_engine == 'mysql':
            sku_name = 'Standard_B1ms'

        # flexible-servers
        servers = [self.create_random_name('azuredbpaccess', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbpaccess', SERVER_NAME_MAX_LENGTH)]

        # Case 1 : Provision a server with public access all
        # create server
        self.cmd('{} flexible-server create -g {} -n {} --public-access {}'
                 .format(database_engine, resource_group, servers[0], 'all'),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAll_'),
                         JMESPathCheck('host', '{}.{}.database.azure.com'.format(servers[0], database_engine))])

        # Case 2 : Provision a server with public access allowing all azure services
        self.cmd('{} flexible-server create -g {} -n {} --public-access {}'
                 .format(database_engine, resource_group, servers[1], '0.0.0.0'),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAllAzureServicesAndResourcesWithinAzureIps_'),
                         JMESPathCheck('host', '{}.{}.database.azure.com'.format(servers[1], database_engine))])

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_local_context(self, resource_group):
        self._test_flexible_server_local_context('mysql', resource_group)

    def _test_flexible_server_local_context(self, database_engine, resource_group):
        from knack.util import CLIError
        if database_engine == 'mysql':
            location = self.mysql_location
        else:
            location = self.postgre_location

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', location)

        self.cmd('{} flexible-server create -n {}'.format(database_engine, server_name))

        self.cmd('{} flexible-server show'.format(database_engine))

        self.cmd('{} flexible-server update --backup-retention {}'
                 .format(database_engine, 10))

        self.cmd('{} flexible-server stop'.format(database_engine))

        self.cmd('{} flexible-server start'.format(database_engine))

        self.cmd('{} flexible-server restart'.format(database_engine))

        self.cmd('{} flexible-server list'.format(database_engine))

        self.cmd('{} flexible-server show-connection-string'.format(database_engine))

        self.cmd('{} flexible-server list-skus'.format(database_engine))

        self.cmd('{} flexible-server delete --yes'.format(database_engine))
