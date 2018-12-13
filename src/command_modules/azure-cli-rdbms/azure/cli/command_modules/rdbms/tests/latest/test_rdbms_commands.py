# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from dateutil.tz import tzutc   # pylint: disable=import-error

from azure.cli.core.util import CLIError
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError   # pylint: disable=unused-import
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)


# Constants
SERVER_NAME_PREFIX = 'azuredbclitest'
SERVER_NAME_MAX_LENGTH = 63


class ServerPreparer(AbstractPreparer, SingleValueReplacer):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, engine_type='mysql', engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server', location='koreasouth',
                 admin_user='cloudsa', admin_password='SecretPassword123',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 sku_name='GP_Gen5_2'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.engine_type = engine_type
        self.engine_parameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete
        self.sku_name = sku_name

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} server create -l {} -g {} -n {} -u {} -p {} --sku-name {}'
        execute(self.cli_ctx, template.format(self.engine_type,
                                              self.location,
                                              group, name,
                                              self.admin_user,
                                              self.admin_password,
                                              self.sku_name))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(self.cli_ctx, 'az {} server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)


class ServerMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_mariadb_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mariadb', resource_group_1, resource_group_2)

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_mysql_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mysql', resource_group_1, resource_group_2)

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_postgres_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('postgres', resource_group_1, resource_group_2)

    def _test_server_mgmt(self, database_engine, resource_group_1, resource_group_2):
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbclirestore', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbcligeorestore', SERVER_NAME_MAX_LENGTH)]
        admin_login = 'cloudsa'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        edition = 'GeneralPurpose'
        backupRetention = 10
        geoRedundantBackup = 'Enabled'
        old_cu = 2
        new_cu = 4
        family = 'Gen5'
        skuname = 'GP_{}_{}'.format(family, old_cu)
        newskuname = 'GP_{}_{}'.format(family, new_cu)
        loc = 'koreasouth'

        geoGeoRedundantBackup = 'Disabled'
        geoBackupRetention = 20
        geoloc = 'koreasouth'

        # test create server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--sku-name {} --tags key=1 --geo-redundant-backup {} '
                 '--backup-retention {}'
                 .format(database_engine, resource_group_1, servers[0], loc,
                         admin_login, admin_passwords[0], skuname,
                         geoRedundantBackup, backupRetention),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('tags.key', '1'),
                     JMESPathCheck('sku.capacity', old_cu),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('storageProfile.backupRetentionDays', backupRetention),
                     JMESPathCheck('storageProfile.geoRedundantBackup', geoRedundantBackup)])

        # test show server
        result = self.cmd('{} server show -g {} --name {}'
                          .format(database_engine, resource_group_1, servers[0]),
                          checks=[
                              JMESPathCheck('name', servers[0]),
                              JMESPathCheck('resourceGroup', resource_group_1),
                              JMESPathCheck('administratorLogin', admin_login),
                              JMESPathCheck('sslEnforcement', 'Enabled'),
                              JMESPathCheck('tags.key', '1'),
                              JMESPathCheck('sku.capacity', old_cu),
                              JMESPathCheck('sku.tier', edition),
                              JMESPathCheck('storageProfile.backupRetentionDays', backupRetention),
                              JMESPathCheck('storageProfile.geoRedundantBackup', geoRedundantBackup)]).get_output_in_json()  # pylint: disable=line-too-long

        # test update server
        self.cmd('{} server update -g {} --name {} --admin-password {} '
                 '--ssl-enforcement Disabled --tags key=2'
                 .format(database_engine, resource_group_1, servers[0], admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --sku-name {}'
                 .format(database_engine, resource_group_1, servers[0], newskuname),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test show server
        self.cmd('{} server show -g {} --name {}'
                 .format(database_engine, resource_group_1, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test update server per property
        self.cmd('{} server update -g {} --name {} --sku-name {}'
                 .format(database_engine, resource_group_1, servers[0], skuname),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', old_cu),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --ssl-enforcement Enabled'
                 .format(database_engine, resource_group_1, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --tags key=3'
                 .format(database_engine, resource_group_1, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('tags.key', '3'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test restore to a new server, make sure wait at least 5 min after server created.
        from time import sleep
        sleep(300)

        self.cmd('{} server restore -g {} --name {} '
                 '--source-server {} '
                 '--restore-point-in-time {}'
                 .format(database_engine, resource_group_2, servers[1], result['id'],
                         datetime.utcnow().replace(tzinfo=tzutc()).isoformat()),
                 checks=[
                     JMESPathCheck('name', servers[1]),
                     JMESPathCheck('resourceGroup', resource_group_2),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test georestore server
        with self.assertRaises(CLIError) as exception:
            self.cmd('{} server georestore -g {} --name {} --source-server {} -l {} '
                     '--geo-redundant-backup {} --backup-retention {}'
                     .format(database_engine, resource_group_2, servers[2], result['id'],
                             geoloc, geoGeoRedundantBackup, geoBackupRetention),
                     checks=[
                         JMESPathCheck('name', servers[2]),
                         JMESPathCheck('resourceGroup', resource_group_2),
                         JMESPathCheck('sku.tier', edition),
                         JMESPathCheck('administratorLogin', admin_login),
                         JMESPathCheck('location', geoloc),
                         JMESPathCheck('storageProfile.backupRetentionDays', geoBackupRetention),
                         JMESPathCheck('storageProfile.geoRedundantBackup', geoGeoRedundantBackup)])
        self.assertTrue(' does not have the server ' in '{}'.format(exception.exception))

        # test list servers
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_2),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # test list servers without resource group
        self.cmd('{} server list'.format(database_engine),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # test delete server
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group_1, servers[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} -n {} --yes'
                 .format(database_engine, resource_group_2, servers[1]), checks=NoneCheck())

        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_1), checks=[NoneCheck()])
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_2), checks=[NoneCheck()])


class ProxyResourcesMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mariadb')
    def test_mariadb_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mysql')
    def test_mysql_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='postgres')
    def test_postgres_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)

    def _test_firewall_mgmt(self, resource_group, server, database_engine):
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'

        # test firewall-rule create
        self.cmd('{} server firewall-rule create -n {} -g {} -s {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(database_engine, firewall_rule_1, resource_group, server,
                         start_ip_address_1, end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule show
        self.cmd('{} server firewall-rule show --name {} -g {} --server {}'
                 .format(database_engine, firewall_rule_1, resource_group, server),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule update
        self.cmd('{} server firewall-rule update -n {} -g {} -s {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(database_engine, firewall_rule_1, resource_group, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('{} server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {}'
                 .format(database_engine, firewall_rule_1, resource_group, server,
                         start_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('{} server firewall-rule update -n {} -g {} -s {} '
                 '--end-ip-address {}'
                 .format(database_engine, firewall_rule_1, resource_group, server,
                         end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule create another rule
        self.cmd('{} server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(database_engine, firewall_rule_2, resource_group, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test firewall-rule list
        self.cmd('{} server firewall-rule list -g {} -s {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} server firewall-rule delete --name {} -g {} --server {} --yes'
                 .format(database_engine, firewall_rule_1, resource_group, server), checks=NoneCheck())
        self.cmd('{} server firewall-rule list -g {} --server {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('{} server firewall-rule delete -n {} -g {} -s {} --yes'
                 .format(database_engine, firewall_rule_2, resource_group, server), checks=NoneCheck())
        self.cmd('{} server firewall-rule list -g {} --server {}'
                 .format(database_engine, resource_group, server), checks=[NoneCheck()])

    def _test_vnet_firewall_mgmt(self, resource_group, server, database_engine):
        vnet_firewall_rule_1 = 'vnet_rule1'
        vnet_firewall_rule_2 = 'vnet_rule2'
        location = 'koreasouth'
        vnet_name = 'clitestvnet'
        ignore_missing_endpoint = 'true'
        address_prefix = '10.0.0.0/16'

        subnet_name_1 = 'clitestsubnet1'
        subnet_prefix_1 = '10.0.0.0/24'

        subnet_name_2 = 'clitestsubnet2'
        subnet_prefix_2 = '10.0.1.0/24'

        subnet_name_3 = 'clitestsubnet3'
        subnet_prefix_3 = '10.0.3.0/24'

        # pre create the dependent resources here
        # create vnet and subnet
        self.cmd('network vnet create -n {} -g {} -l {} '
                 '--address-prefix {} --subnet-name {} --subnet-prefix {}'.format(vnet_name, resource_group, location, address_prefix, subnet_name_1, subnet_prefix_1))
        # add one more subnet
        self.cmd('network vnet subnet create --vnet-name {} -g {} '
                 '--address-prefix {} -n {}'.format(vnet_name, resource_group, subnet_prefix_2, subnet_name_2))

        # test vnet-rule create
        self.cmd('{} server vnet-rule create -n {} -g {} -s {} '
                 '--vnet-name {} --subnet {} --ignore-missing-endpoint {}'
                 .format(database_engine, vnet_firewall_rule_1, resource_group, server,
                         vnet_name, subnet_name_1, ignore_missing_endpoint),
                 checks=[
                     JMESPathCheck('name', vnet_firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', 'Ready')])

        # test vnet-rule show
        self.cmd('{} server vnet-rule show -n {} -g {} -s {}'
                 .format(database_engine, vnet_firewall_rule_1, resource_group, server),
                 checks=[
                     JMESPathCheck('name', vnet_firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', 'Ready')])

        # test create one more vnet rule .
        self.cmd('{} server vnet-rule create -n {} -g {} -s {} '
                 '--vnet-name {} --subnet {} --ignore-missing-endpoint {}'
                 .format(database_engine, vnet_firewall_rule_2, resource_group, server,
                         vnet_name, subnet_name_2, ignore_missing_endpoint),
                 checks=[
                     JMESPathCheck('name', vnet_firewall_rule_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', 'Ready')])

        # add one more subnet
        self.cmd('network vnet subnet create --vnet-name {} -g {} '
                 '--address-prefix {} -n {}'.format(vnet_name, resource_group, subnet_prefix_3, subnet_name_3))

        self.cmd('{} server vnet-rule update -n {} -g {} -s {} '
                 '--vnet-name {} --subnet {} --ignore-missing-endpoint {}'
                 .format(database_engine, vnet_firewall_rule_2, resource_group, server,
                         vnet_name, subnet_name_3, ignore_missing_endpoint),
                 checks=[
                     JMESPathCheck('name', vnet_firewall_rule_2),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', 'Ready')])

        # test vnet-rule list
        self.cmd('{} server vnet-rule list -g {} -s {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} server vnet-rule delete --name {} -g {} --server {}'
                 .format(database_engine, vnet_firewall_rule_1, resource_group, server), checks=NoneCheck())
        self.cmd('{} server vnet-rule list -g {} --server {}'
                 .format(database_engine, resource_group, server), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('{} server vnet-rule delete -n {} -g {} -s {}'
                 .format(database_engine, vnet_firewall_rule_2, resource_group, server), checks=NoneCheck())
        self.cmd('{} server vnet-rule list -g {} --server {}'
                 .format(database_engine, resource_group, server), checks=[NoneCheck()])
        self.cmd('network vnet delete -n {} -g {}'.format(vnet_name, resource_group))

    def _test_db_mgmt(self, resource_group, server, database_engine):
        self.cmd('{} db list -g {} -s {}'.format(database_engine, resource_group, server),
                 checks=JMESPathCheck('type(@)', 'array'))

    def _test_configuration_mgmt(self, resource_group, server, database_engine):
        if database_engine == 'mysql' or database_engine == 'mariadb':
            config_name = 'log_slow_admin_statements'
            default_value = 'OFF'
            new_value = 'ON'
        else:
            config_name = 'array_nulls'
            default_value = 'on'
            new_value = 'off'

        # test show configuration
        self.cmd('{} server configuration show --name {} -g {} --server {}'
                 .format(database_engine, config_name, resource_group, server),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', default_value),
                     JMESPathCheck('source', 'system-default')])

        # test update configuration
        self.cmd('{} server configuration set -n {} -g {} -s {} --value {}'
                 .format(database_engine, config_name, resource_group, server, new_value),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', new_value),
                     JMESPathCheck('source', 'user-override')])

        self.cmd('{} server configuration set -n {} -g {} -s {}'
                 .format(database_engine, config_name, resource_group, server),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', default_value)])

        # test list configurations
        self.cmd('{} server configuration list -g {} -s {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

    def _test_log_file_mgmt(self, resource_group, server, database_engine):
        if database_engine == 'mysql' or database_engine == 'mariadb':
            config_name = 'slow_query_log'
            new_value = 'ON'

            # test update configuration
            self.cmd('{} server configuration set -n {} -g {} -s {} --value {}'
                     .format(database_engine, config_name, resource_group, server, new_value),
                     checks=[
                         JMESPathCheck('name', config_name),
                         JMESPathCheck('value', new_value)])

        # test list log files
        # ensure recording good for at least 5 years!
        result = self.cmd('{} server-logs list -g {} -s {} --file-last-written 43800'
                          .format(database_engine, resource_group, server),
                          checks=[
                              JMESPathCheck('length(@)', 1),
                              JMESPathCheck('type(@)', 'array')]).get_output_in_json()

        self.assertIsNotNone(result[0]['name'])


class ReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    @ResourceGroupPreparer(parameter_name='resource_group')
    def test_mysql_replica_mgmt(self, resource_group):
        self._test_replica_mgmt(resource_group, 'mysql')

    def _test_replica_mgmt(self, resource_group, database_engine):
        server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        result = self.cmd('{} server create -g {} --name {} -l brazilsouth '
                          '--admin-user cloudsa --admin-password SecretPassword123 '
                          '--sku-name GP_Gen4_2'
                          .format(database_engine, resource_group, server),
                          checks=[
                              JMESPathCheck('name', server),
                              JMESPathCheck('resourceGroup', resource_group),
                              JMESPathCheck('sslEnforcement', 'Enabled'),
                              JMESPathCheck('sku.name', 'GP_Gen4_2'),
                              JMESPathCheck('replicationRole', 'None'),
                              JMESPathCheck('masterServerId', '')]).get_output_in_json()

        from time import sleep
        sleep(300)
        # test replica create
        self.cmd('{} server replica create -g {} -n {} '
                 '--source-server {}'
                 .format(database_engine, resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('masterServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        # test show server with replication info
        self.cmd('{} server show -g {} --name {}'
                 .format(database_engine, resource_group, server),
                 checks=[
                     JMESPathCheck('replicationRole', 'Master'),
                     JMESPathCheck('masterServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test replica list
        self.cmd('{} server replica list -g {} -s {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # test replica stop
        self.cmd('{} server replica stop -g {} -n {} --yes'
                 .format(database_engine, resource_group, replicas[0]),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('masterServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test show server with replication info, master becomes normal server
        self.cmd('{} server show -g {} --name {}'
                 .format(database_engine, resource_group, server),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('masterServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # test delete master server
        self.cmd('{} server replica create -g {} -n {} '
                 '--source-server {}'
                 .format(database_engine, resource_group, replicas[1], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[1]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', result['sku']['name']),
                     JMESPathCheck('replicationRole', 'Replica'),
                     JMESPathCheck('masterServerId', result['id']),
                     JMESPathCheck('replicaCapacity', '0')])

        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, server), checks=NoneCheck())

        sleep(300)
        # test show server with replication info, replica was auto stopped after master server deleted
        self.cmd('{} server show -g {} --name {}'
                 .format(database_engine, resource_group, replicas[1]),
                 checks=[
                     JMESPathCheck('replicationRole', 'None'),
                     JMESPathCheck('masterServerId', ''),
                     JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # clean up servers
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())
