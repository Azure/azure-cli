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
        template = 'az {} flexible-server create -l {} -g {} -n {} --public-access none'
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

    postgres_location = 'eastus2euap'
    mysql_location = 'eastus2euap'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_iops_mgmt(self, resource_group):
        self._test_flexible_server_iops_mgmt('mysql', resource_group)

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
            storage_size = 32
            version = '5.7'
            location = self.mysql_location
        location_result = 'East US 2 EUAP'
        backup_retention = 7
        database_name = 'testdb'
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --backup-retention {} --sku-name {} --tier {} \
                  --storage-size {} -u {} --version {} --tags keys=3 --database-name {} --high-availability Disabled \
                  --zone 1 --maintenance-window Mon:1:10 --geo-redundant-backup Enabled'.format(database_engine,
                  resource_group, server_name, location, backup_retention, sku_name, tier, storage_size, 'dbadmin', version, database_name))

        list_checks = [JMESPathCheck('name', server_name),
                        JMESPathCheck('location', location_result),
                        JMESPathCheck('resourceGroup', resource_group),
                        JMESPathCheck('sku.name', sku_name),
                        JMESPathCheck('sku.tier', tier),
                        JMESPathCheck('version', version),
                        JMESPathCheck('storage.storageSizeGb', storage_size),
                        JMESPathCheck('backup.backupRetentionDays', backup_retention),
                        JMESPathCheck('maintenanceWindow.customWindow', 'Enabled')]

        self.cmd('{} flexible-server show -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=list_checks)

        self.cmd('{} flexible-server db show -g {} -s {} -d {}'
                    .format(database_engine, resource_group, server_name, database_name), checks=[JMESPathCheck('name', database_name)])

        self.cmd('{} flexible-server update -g {} -n {} -p randompw321##@!'
                 .format(database_engine, resource_group, server_name))

        self.cmd('{} flexible-server update -g {} -n {} --storage-size 256'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storage.storageSizeGb', 256 )])

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'
                 .format(database_engine, resource_group, server_name, backup_retention + 10),
                 checks=[JMESPathCheck('backup.backupRetentionDays', backup_retention + 10)])

        if database_engine == 'postgres':
            tier = 'Burstable'
            sku_name = 'Standard_B1ms'
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            sku_name = 'Standard_D2s_v3'

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'
                 .format(database_engine, resource_group, server_name, tier, sku_name),
                 checks=[JMESPathCheck('sku.tier', tier),
                         JMESPathCheck('sku.name', sku_name)])

        self.cmd('{} flexible-server update -g {} -n {} --maintenance-window Mon:1:30'
                    .format(database_engine, resource_group, server_name),
                    checks=[JMESPathCheck('maintenanceWindow.dayOfWeek', 1),
                            JMESPathCheck('maintenanceWindow.startHour', 1),
                            JMESPathCheck('maintenanceWindow.startMinute', 30)])

        self.cmd('{} flexible-server update -g {} -n {} --tags key=3'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('tags.key', '3')])

        self.cmd('{} flexible-server restart -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server stop -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server start -g {} -n {}'
                 .format(database_engine, resource_group, server_name), checks=NoneCheck())

        self.cmd('{} flexible-server list -g {}'.format(database_engine, resource_group),
                 checks=[JMESPathCheck('type(@)', 'array')])
        
        restore_server_name = 'restore-' + server_name
        self.cmd('{} flexible-server restore -g {} --name {} --source-server {}'
                 .format(database_engine, resource_group, restore_server_name, server_name),
                 checks=[JMESPathCheck('name', restore_server_name)])

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

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, restore_server_name), checks=NoneCheck())

    def _test_flexible_server_iops_mgmt(self, database_engine, resource_group):

        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        location = self.mysql_location

        # flexible-server create with user input
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        server_name_2 = self.create_random_name(SERVER_NAME_PREFIX + '2', SERVER_NAME_MAX_LENGTH)
        server_name_3 = self.create_random_name(SERVER_NAME_PREFIX + '3', SERVER_NAME_MAX_LENGTH)

        # IOPS passed is within limit of max allowed by SKU but smaller than storage*3
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 200 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name, location))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storageProfile.storageIops', 320)])

        # SKU upgraded and IOPS value set smaller than free iops, max iops for the sku
        self.cmd('{} flexible-server update -g {} -n {} --tier Burstable --sku-name Standard_B1ms --iops 400'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storageProfile.storageIops', 600)])

        # SKU downgraded and IOPS not specified
        self.cmd('{} flexible-server update -g {} -n {} --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name),
                 checks=[JMESPathCheck('storageProfile.storageIops', 320)])

        # IOPS passed is within limit of max allowed by SKU but smaller than default
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 30 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name_2, location))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name_2),
                 checks=[JMESPathCheck('storageProfile.storageIops', 100)])

        # SKU upgraded and IOPS value set bigger than max iops for the sku
        self.cmd('{} flexible-server update -g {} -n {} --tier Burstable --sku-name Standard_B1ms --iops 700'
                 .format(database_engine, resource_group, server_name_2),
                 checks=[JMESPathCheck('storageProfile.storageIops', 640)])

        # IOPS passed is within limit of max allowed by SKU and bigger than default
        self.cmd('{} flexible-server create --public-access none -g {} -n {} -l {} --iops 50 --storage-size 40 --tier Burstable --sku-name Standard_B1s'
                 .format(database_engine, resource_group, server_name_3, location))

        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name_3),
                 checks=[JMESPathCheck('storageProfile.storageIops', 120)])

        # SKU upgraded and IOPS value set lower than max iops for the sku but bigger than free iops
        self.cmd('{} flexible-server update -g {} -n {} --tier Burstable --sku-name Standard_B1ms --storage-size 300 --iops 500'
                 .format(database_engine, resource_group, server_name_3),
                 checks=[JMESPathCheck('storageProfile.storageIops', 640)])


class FlexibleServerProxyResourceMgmtScenarioTest(ScenarioTest):

    postgres_location = 'eastus2euap'
    mysql_location = 'eastus2euap'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(engine_type='postgres', location=postgres_location)
    def test_postgres_flexible_server_proxy_resource(self, resource_group, server):
        self._test_firewall_rule_mgmt('postgres', resource_group, server)
        self._test_parameter_mgmt('postgres', resource_group, server)
        self._test_database_mgmt('postgres', resource_group, server)

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

        self.cmd('{} flexible-server db create -g {} -s {} -d {}'.format(database_engine, resource_group, server, database_name),
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

    postgres_location = 'eastus2euap'
    mysql_location = 'eastus2euap'

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
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        invalid_version = self.create_random_name('version', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_sku_name = self.create_random_name('sku_name', RANDOM_VARIABLE_MAX_LENGTH)
        invalid_tier = self.create_random_name('tier', RANDOM_VARIABLE_MAX_LENGTH)
        valid_tier = 'GeneralPurpose'
        invalid_backup_retention = 1

        # Create
        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {}'.format(database_engine, resource_group, server_name, location, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --version {}'.format(database_engine, resource_group, server_name, location, invalid_version), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --sku-name {}'.format(database_engine, resource_group, server_name, location, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --backup-retention {}'.format(database_engine, resource_group, server_name, location, invalid_backup_retention), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l centraluseuap --high-availability Enabled '.format(database_engine, resource_group, server_name), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier Burstable --sku-name Standard_B1ms --high-availability Enabled'.format(database_engine, resource_group, server_name, location), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n Wrongserver.Name -l {}'.format(database_engine, resource_group, location, invalid_backup_retention), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --vnet testvnet --subnet testsubnet --public-access All'.format(database_engine, resource_group, server_name, location), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --maintenance-window Day:2:300'.format(database_engine, resource_group, server_name, location), expect_failure=True)

        self.cmd('{} flexible-server create -g {} -n {} -l {} --public-access 12.0.0.0-10.0.0.0.0'.format(database_engine, resource_group, server_name, location), expect_failure=True)

        if database_engine == 'postgres':
            invalid_storage_size = 60
        elif database_engine == 'mysql':
            invalid_storage_size = 999999
        self.cmd('{} flexible-server create -g {} -l {} --storage-size {} --public-access none'.format(database_engine, resource_group, location, invalid_storage_size), expect_failure=True)

        server_name = self.create_random_name(SERVER_NAME_PREFIX, RANDOM_VARIABLE_MAX_LENGTH)
        if database_engine == 'postgres':
            tier = 'MemoryOptimized'
            version = 12
            sku_name = 'Standard_E2s_v3'
            storage_size = 64
        elif database_engine == 'mysql':
            tier = 'GeneralPurpose'
            version = 5.7
            sku_name = 'Standard_D2s_v3'
            storage_size = 20
        backup_retention = 10

        list_checks = [JMESPathCheck('name', server_name),
                       JMESPathCheck('resourceGroup', resource_group),
                       JMESPathCheck('sku.name', sku_name),
                       JMESPathCheck('sku.tier', tier),
                       JMESPathCheck('version', version),
                       JMESPathCheck('storage.storageSizeGb', storage_size),
                       JMESPathCheck('backup.backupRetentionDays', backup_retention)]

        self.cmd('{} flexible-server create -g {} -n {} -l {} --tier {} --version {} --sku-name {} --storage-size {} --backup-retention {} --public-access none'
                 .format(database_engine, resource_group, server_name, location, tier, version, sku_name, storage_size, backup_retention))
        self.cmd('{} flexible-server show -g {} -n {}'.format(database_engine, resource_group, server_name), checks=list_checks)

        invalid_storage_size_small = storage_size - 1
        self.cmd('{} flexible-server update -g {} -n {} --tier {}'.format(database_engine, resource_group, server_name, invalid_tier), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --tier {} --sku-name {}'.format(database_engine, resource_group, server_name, valid_tier, invalid_sku_name), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --storage-size {}'.format(database_engine, resource_group, server_name, invalid_storage_size_small), expect_failure=True)

        self.cmd('{} flexible-server update -g {} -n {} --backup-retention {}'.format(database_engine, resource_group, server_name, invalid_backup_retention), expect_failure=True)

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name), checks=NoneCheck())


class FlexibleServerReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    mysql_location = 'eastus2euap'

    @ResourceGroupPreparer(location=mysql_location)
    def test_mysql_flexible_server_replica_mgmt(self, resource_group):
        self._test_flexible_server_replica_mgmt('mysql', resource_group)

    def _test_flexible_server_replica_mgmt(self, database_engine, resource_group):
        location = self.mysql_location
        master_server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        self.cmd('{} flexible-server create -g {} --name {} -l {} --storage-size {} --public-access none'
                 .format(database_engine, resource_group, master_server, location, 256))
        result = self.cmd('{} flexible-server show -g {} --name {} '
                          .format(database_engine, resource_group, master_server),
                          checks=[JMESPathCheck('replicationRole', 'None')]).get_output_in_json()
        time.sleep(5 * 60)

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

    postgres_location = 'eastus2euap'
    mysql_location = 'eastus2euap'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @VirtualNetworkPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
        # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
        self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('postgres', resource_group)

    # @AllowLargeResponse()
    # @ResourceGroupPreparer(location=mysql_location)
    # @VirtualNetworkPreparer(location=mysql_location)
    # def test_mysql_flexible_server_vnet_mgmt_supplied_subnetid(self, resource_group):
    #     # Provision a server with supplied Subnet ID that exists, where the subnet is not delegated
    #     self._test_flexible_server_vnet_mgmt_existing_supplied_subnetid('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vnet(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vnet('postgres', resource_group)

    # @AllowLargeResponse()
    # @ResourceGroupPreparer(location=mysql_location)
    # def test_mysql_flexible_server_vnet_mgmt_supplied_vnet(self, resource_group):
    #     self._test_flexible_server_vnet_mgmt_supplied_vnet('mysql', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    def test_postgres_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group):
        self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('postgres', resource_group)

    # @AllowLargeResponse()
    # @ResourceGroupPreparer(location=mysql_location)
    # @VirtualNetworkPreparer(parameter_name='virtual_network', location=mysql_location)
    # def test_mysql_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, resource_group, virtual_network):
    #     self._test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname('mysql', resource_group, virtual_network)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_1')
    @ResourceGroupPreparer(location=postgres_location, parameter_name='resource_group_2')
    def test_postgres_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
        self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('postgres', resource_group_1, resource_group_2)

    # @AllowLargeResponse()
    # @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_1')
    # @ResourceGroupPreparer(location=mysql_location, parameter_name='resource_group_2')
    # def test_mysql_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, resource_group_1, resource_group_2):
    #     self._test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg('mysql', resource_group_1, resource_group_2)

    def _test_flexible_server_vnet_mgmt_existing_supplied_subnetid(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone0.private.{}.database.azure.com".format(database_engine)

        # Scenario : Provision a server with supplied Subnet ID that exists, where the subnet is not delegated

        subnet_id = self.cmd('network vnet subnet show -g {rg} -n default --vnet-name {vnet}').get_output_in_json()['id']

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {}'
                 .format(database_engine, resource_group, server_name, subnet_id, location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, server_name)).get_output_in_json()
        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'], subnet_id)
        
        self.assertEqual(show_result_1['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone))
        # delete server
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, server_name),
                 checks=NoneCheck())
        
        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_vnet(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        vnet_name = 'clitestvnet1'
        vnet_name_2 = 'clitestvnet2'
        address_prefix = '13.0.0.0/16'
        subnet_prefix = '13.0.0.0/24'
        private_dns_zone_1 = "testdnszone1.private.{}.database.azure.com".format(database_engine)
        private_dns_zone_2 = "testdnszone2.private.{}.database.azure.com".format(database_engine)

        # flexible-servers
        servers = ['testvnetserver1' + database_engine, 'testvnetserver2' + database_engine]

        # Case 1 : Provision a server with supplied Vname that exists.
        vnet_name = 'clitestvnet3'
        vnet_name_2 = 'clitestvnet2'
        address_prefix = '13.0.0.0/16'
        subnet_prefix = '13.0.0.0/24'

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format(vnet_name, resource_group, location, address_prefix)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {} -l {} --private-dns-zone {}'
                 .format(database_engine, resource_group, servers[0], vnet_name, location, private_dns_zone_1))

        # Case 2 : Provision a server with a supplied Vname that does not exist.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {} -l {} --private-dns-zone {}'
                 .format(database_engine, resource_group, servers[1], vnet_name_2, location, private_dns_zone_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name, 'Subnet' + servers[0]))

        self.assertEqual(show_result_2['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1]))
        
        self.assertEqual(show_result_1['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone_1))
        
        self.assertEqual(show_result_2['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone_2))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)

    def _test_flexible_server_vnet_mgmt_supplied_vname_and_subnetname(self, database_engine, resource_group):

        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        vnet_name = 'clitestvnet3'
        subnet_name = 'clitestsubnet3'
        vnet_name_2 = 'clitestvnet4'
        address_prefix = '13.0.0.0/16'
        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        # flexible-servers
        servers = ['testvnetserver3' + database_engine, 'testvnetserver4' + database_engine]
        private_dns_zone_1 = "testdnszone3.private.{}.database.azure.com".format(database_engine)
        private_dns_zone_2 = "testdnszone4.private.{}.database.azure.com".format(database_engine)
        # Case 1 : Provision a server with supplied Vname and subnet name that exists.

        # create vnet and subnet. When vnet name is supplied, the subnet created will be given the default name.
        self.cmd('network vnet create -n {} -g {} -l {} --address-prefix {}'
                  .format(vnet_name, resource_group, location, address_prefix))

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --vnet {} -l {} --subnet {} --private-dns-zone {}'
                 .format(database_engine, resource_group, servers[0], vnet_name, location, subnet_name, private_dns_zone_1))

        # Case 2 : Provision a server with a supplied Vname and subnet name that does not exist.
        self.cmd('{} flexible-server create -g {} -n {} -l {} --vnet {} --private-dns-zone {}'
                 .format(database_engine, resource_group, servers[1], location, vnet_name_2, private_dns_zone_2))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[0])).get_output_in_json()

        show_result_2 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group, servers[1])).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'], 
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name, subnet_name))

        self.assertEqual(show_result_2['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                         self.get_subscription_id(), resource_group, vnet_name_2, 'Subnet' + servers[1]))
        
        self.assertEqual(show_result_1['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone_1))
        
        self.assertEqual(show_result_2['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group, private_dns_zone_2))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())

        time.sleep(15 * 60)


    def _test_flexible_server_vnet_mgmt_supplied_subnet_id_in_different_rg(self, database_engine, resource_group_1, resource_group_2):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            location = self.postgres_location
        elif database_engine == 'mysql':
            location = self.mysql_location

        vnet_name = 'clitestvnet5'
        subnet_name = 'clitestsubnet5'
        address_prefix = '10.10.0.0/16'
        subnet_prefix = '10.10.0.0/24'

        # flexible-servers
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        private_dns_zone = "testdnszone5.private.{}.database.azure.com".format(database_engine)

        # Case 1 : Provision a server with supplied subnetid that exists in a different RG

        # create vnet and subnet.
        vnet_result = self.cmd(
            'network vnet create -n {} -g {} -l {} --address-prefix {} --subnet-name {} --subnet-prefix {}'
            .format(vnet_name, resource_group_1, location, address_prefix, subnet_name,
                    subnet_prefix)).get_output_in_json()

        # create server - Delegation should be added.
        self.cmd('{} flexible-server create -g {} -n {} --subnet {} -l {} --private-dns-zone {}'
                 .format(database_engine, resource_group_2, server_name, vnet_result['newVNet']['subnets'][0]['id'], location, private_dns_zone))

        # flexible-server show to validate delegation is added to both the created server
        show_result_1 = self.cmd('{} flexible-server show -g {} -n {}'
                                 .format(database_engine, resource_group_2, server_name)).get_output_in_json()

        self.assertEqual(show_result_1['network']['delegatedSubnetResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
                             self.get_subscription_id(), resource_group_1, vnet_name, subnet_name))
        
        self.assertEqual(show_result_1['network']['privateDnsZoneArmResourceId'],
                         '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/privateDnsZones/{}'.format(
                             self.get_subscription_id(), resource_group_1, private_dns_zone))

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group_2, server_name),
                 checks=NoneCheck())


        time.sleep(15 * 60)

        # remove delegations from all vnets
        self.cmd('network vnet subnet update -g {} --name {} --vnet-name {} --remove delegations'.format(resource_group_1,
                                                                                                         subnet_name,
                                                                                                         vnet_name))
        # remove all vnets
        self.cmd('network vnet delete -g {} -n {}'.format(resource_group_1, vnet_name))


class FlexibleServerPublicAccessMgmtScenarioTest(ScenarioTest):
    postgres_location = 'eastus2euap'
    mysql_location = 'eastus2euap'

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('postgres', resource_group)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=mysql_location)
    @live_only()
    def test_mysql_flexible_server_public_access_mgmt(self, resource_group):
        self._test_flexible_server_public_access_mgmt('mysql', resource_group)

    def _test_flexible_server_public_access_mgmt(self, database_engine, resource_group):
        # flexible-server create
        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        if database_engine == 'postgres':
            sku_name = 'Standard_D2s_v3'
            location = self.postgres_location
        elif database_engine == 'mysql':
            sku_name = 'Standard_B1ms'
            location = self.mysql_location

        # flexible-servers
        servers = [self.create_random_name('azuredbpaccess', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbpaccess', SERVER_NAME_MAX_LENGTH)]

        # Case 1 : Provision a server with public access all
        # create server
        self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                 .format(database_engine, resource_group, servers[0], 'all', location),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAll_'),
                         StringContainCheck(servers[0])])

        # Case 2 : Provision a server with public access allowing all azure services
        self.cmd('{} flexible-server create -g {} -n {} --public-access {} -l {}'
                 .format(database_engine, resource_group, servers[1], '0.0.0.0', location),
                 checks=[JMESPathCheck('resourceGroup', resource_group), JMESPathCheck('skuname', sku_name),
                         StringContainCheck('AllowAllAzureServicesAndResourcesWithinAzureIps_'),
                         StringContainCheck(servers[1])])

        # delete all servers
        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[0]),
                 checks=NoneCheck())

        self.cmd('{} flexible-server delete -g {} -n {} --yes'.format(database_engine, resource_group, servers[1]),
                 checks=NoneCheck())
