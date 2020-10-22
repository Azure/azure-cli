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
    LocalContextScenarioTest,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)

# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20
SERVER_LOGIN_PWD_PREFIX = 'cliPwd'
SERVER_LOGIN_PWD_MAX_LENGTH = 15


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
        elif database_engine == 'mysql':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
            storage_size = 10
            version = '5.7'
            location = self.mysql_location

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        storage_size_mb = storage_size * 1024
        backup_retention = 7

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storageProfile.storageMb', storage_size_mb),
                       JMESPathCheck('storageProfile.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {} -l {}'
                 .format(database_engine, resource_group, server_name, location))
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

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=list_checks).get_output_in_json()

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


class FlexibleServerConnectMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus'
    mysql_location = 'westus2'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_connect(self, resource_group):
        self._test_successful_connect('postgres', resource_group)
        self._test_vnet_connect('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @live_only()
    def test_mysql_flexible_server_connect(self, resource_group):
        self._test_successful_connect('mysql', resource_group)
        self._test_vnet_connect('mysql', resource_group)

    def _test_successful_connect(self, database_engine, resource_group):
        # setup variables for commands
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        username = 'cliuser'
        storage_size = 32
        public_access = 'none'
        simple_query = '"select 1;"'
        if database_engine == 'postgres':
            version = '12'
            location = self.postgres_location
            default_database = 'postgres'
        elif database_engine == 'mysql':
            version = '5.7'
            location = self.mysql_location
            default_database = 'flexibleserverdb'

        # create server with public access enabled for all IPs
        self.cmd('{} flexible-server create -g {} -n {} -l {} --admin-user {} --storage-size {} --version {} --public-access {}'.
                 format(database_engine, resource_group, server_name, location, username, storage_size, version, public_access))

        # update password for generated username and server with a generated password
        generated_password = self.create_random_name(SERVER_LOGIN_PWD_PREFIX, SERVER_LOGIN_PWD_MAX_LENGTH)
        self.cmd('{} flexible-server update -g {} -n {} -p {}'.format(database_engine, resource_group, server_name, generated_password))

        # test connect without firewall
        self.cmd('{} flexible-server connect -n {} -u {} -p {}'.
                 format(database_engine, server_name, username, generated_password),
                 expect_failure=True)

        # add firewall
        firewall_rule_name = 'allIps'
        start_ip_address = '0.0.0.0'
        end_ip_address = '255.255.255.255'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]

        # firewall-rule create
        self.cmd('{} flexible-server firewall-rule create -g {} -n {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        # test connection to the server without command/database specified
        self.cmd('{} flexible-server connect -n {} -u {} -p {}'.
                 format(database_engine, server_name, username, generated_password),
                 checks=NoneCheck())

        # test connection to the server with a simple query
        self.cmd('{} flexible-server connect -n {} -u {} -p {} -d {} -c {}'
                 .format(database_engine, server_name, username, generated_password, default_database, simple_query),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test with invalid username
        username_wrong = 'fakeusername'
        self.cmd('{} flexible-server connect -n {} -u {} -p {} -d {} -c {}'
                 .format(database_engine, server_name, username_wrong, generated_password, default_database, simple_query),
                 expect_failure=True)

    def _test_vnet_connect(self, database_engine, resource_group):
        # setup variables for commands
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        username = 'cliuser'
        storage_size = 32
        if database_engine == 'postgres':
            version = '12'
            location = self.postgres_location
        elif database_engine == 'mysql':
            version = '5.7'
            location = self.mysql_location

        # create server with vnet access
        self.cmd('{} flexible-server create -g {} -n {} -l {} --admin-user {} --storage-size {} --version {}'.
                 format(database_engine, resource_group, server_name, location, username, storage_size, version))

        # update password for generated username and server with a generated password
        generated_password = self.create_random_name(SERVER_LOGIN_PWD_PREFIX, SERVER_LOGIN_PWD_MAX_LENGTH)
        self.cmd('{} flexible-server update -g {} -n {} -p {}'.format(database_engine, resource_group, server_name, generated_password))

        # test connect with vnet and no firewall
        self.cmd('{} flexible-server connect -n {} -u {} -p {}'
                 .format(database_engine, server_name, username, generated_password), expect_failure=True)

        # add firewall
        firewall_rule_name = 'all_ips'
        start_ip_address = '0.0.0.0'
        end_ip_address = '255.255.255.255'
        firewall_rule_checks = [JMESPathCheck('name', firewall_rule_name),
                                JMESPathCheck('endIpAddress', end_ip_address),
                                JMESPathCheck('startIpAddress', start_ip_address)]

        # firewall-rule create
        self.cmd('{} flexible-server firewall-rule create -g {} -n {} --rule-name {} '
                 '--start-ip-address {} --end-ip-address {} '
                 .format(database_engine, resource_group, server_name, firewall_rule_name, start_ip_address, end_ip_address),
                 checks=firewall_rule_checks)

        # test connection to the server without command/database specified and with firewall, but vnet
        self.cmd('{} flexible-server connect -n {} -u {} -p {}'.
                 format(database_engine, server_name, username, generated_password),
                 expect_failure=True)
