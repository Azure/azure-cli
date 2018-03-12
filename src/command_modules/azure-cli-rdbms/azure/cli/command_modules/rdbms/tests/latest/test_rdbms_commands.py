# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from dateutil.tz import tzutc   # pylint: disable=import-error

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
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server', location='brazilsouth',
                 admin_user='cloudsa', admin_password='SecretPassword123',
                 resource_group_parameter_name='resource_group', skip_delete=True,
                 sku_name='GP_Gen4_2'):
        super(ServerPreparer, self).__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.testsdk import TestCli
        self.cli_ctx = TestCli()
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
    def test_mysql_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mysql', resource_group_1, resource_group_2)

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_postgres_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('postgres', resource_group_1, resource_group_2)

    def _test_server_mgmt(self, database_engine, resource_group_1, resource_group_2):
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbclirestore', SERVER_NAME_MAX_LENGTH)]
        admin_login = 'cloudsa'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        edition = 'GeneralPurpose'
        old_cu = 2
        new_cu = 4
        family = 'Gen4'
        skuname = '{}_{}_{}'.format("GP", family, old_cu)

        rg = resource_group_1
        loc = 'brazilsouth'

        # test create server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--sku-name {} --tags key=1'
                 .format(database_engine, rg, servers[0], loc,
                         admin_login, admin_passwords[0], skuname),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('tags.key', '1'),
                     JMESPathCheck('sku.capacity', old_cu),
                     JMESPathCheck('sku.tier', edition)])

        # test show server
        result = self.cmd('{} server show -g {} --name {}'
                          .format(database_engine, rg, servers[0]),
                          checks=[
                              JMESPathCheck('name', servers[0]),
                              JMESPathCheck('administratorLogin', admin_login),
                              JMESPathCheck('sku.capacity', old_cu),
                              JMESPathCheck('resourceGroup', rg)]).get_output_in_json()

        # test update server
        self.cmd('{} server update -g {} --name {} --admin-password {} '
                 '--ssl-enforcement Disabled --tags key=2'
                 .format(database_engine, rg, servers[0], admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --vcore {}'
                 .format(database_engine, rg, servers[0], new_cu),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test show server
        self.cmd('{} server show -g {} --name {}'
                 .format(database_engine, rg, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test update server per property
        self.cmd('{} server update -g {} --name {} --vcore {}'
                 .format(database_engine, rg, servers[0], old_cu),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', old_cu),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --ssl-enforcement Enabled'
                 .format(database_engine, rg, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --tags key=3'
                 .format(database_engine, rg, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
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

        # test list servers
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_2),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # test list servers without resource group
        self.cmd('{} server list'.format(database_engine),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # test delete server
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, rg, servers[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} -n {} --yes'
                 .format(database_engine, resource_group_2, servers[1]), checks=NoneCheck())

        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, rg), checks=[NoneCheck()])


class ProxyResourcesMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mysql')
    def test_mysql_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='postgres')
    def test_postgres_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
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

    def _test_db_mgmt(self, resource_group, server, database_engine):
        self.cmd('{} db list -g {} -s {}'.format(database_engine, resource_group, server),
                 checks=JMESPathCheck('type(@)', 'array'))

    def _test_configuration_mgmt(self, resource_group, server, database_engine):
        if database_engine == 'mysql':
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
        if database_engine == 'mysql':
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
