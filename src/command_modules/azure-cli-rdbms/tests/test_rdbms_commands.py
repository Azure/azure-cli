# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from datetime import datetime
from dateutil.tz import tzutc

from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)

from azure.cli.testsdk.utilities import create_random_name


# Constants
server_name_prefix = 'clitestserver'
server_name_max_length = 63


class ServerPreparer(AbstractPreparer, SingleValueReplacer):
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes
    def __init__(self, engine_type='mysql', engine_parameter_name='engine',
                 name_prefix=server_name_prefix, parameter_name='server', location='northeurope',
                 admin_user='cloudsa', admin_password='SecretPassword123',
                 resource_group_parameter_name='resource_group', skip_delete=False):
        super(ServerPreparer, self).__init__(name_prefix, server_name_max_length)
        self.engine_type = engine_type
        self.engine_parameter_name = engine_parameter_name
        self.location = location
        self.parameter_name = parameter_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az {} server create -l {} -g {} -n {} -u {} -p {}'
        execute(template.format(self.engine_type,
                                self.location,
                                group, name,
                                self.admin_user,
                                self.admin_password))
        return {self.parameter_name: name,
                self.engine_parameter_name: self.engine_type}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute('az {} server delete -g {} -n {} --yes'.format(self.engine_type, group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a rdbms server, resource group is required. Please add ' \
                       'decorator @{} in front of this server preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class ServerMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_mysql_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mysql', resource_group_1, resource_group_2)

    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_postgres_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('postgres', resource_group_1, resource_group_2)

    def _test_server_mgmt(self, engine, resource_group_1, resource_group_2):
        servers = [create_random_name(server_name_prefix),
                   create_random_name('clitestrestore')]
        admin_login = 'cloudsa'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']
        edition = 'Basic'
        new_cu = 50

        rg = resource_group_1
        loc = 'northeurope'

        # test create server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--performance-tier {} --compute-units 100 --tags key=1'
                 .format(engine, rg, servers[0], loc, admin_login, admin_passwords[0], edition),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', admin_login),
                     JMESPathCheck('sslEnforcement', 'Enabled'),
                     JMESPathCheck('tags.key', '1'),
                     JMESPathCheck('sku.capacity', 100),
                     JMESPathCheck('sku.tier', edition)])

        # test show server
        result = self.cmd('{} server show -g {} --name {}'
                          .format(engine, rg, servers[0]),
                          checks=[
                              JMESPathCheck('name', servers[0]),
                              JMESPathCheck('administratorLogin', admin_login),
                              JMESPathCheck('sku.capacity', 100),
                              JMESPathCheck('resourceGroup', rg)]).get_output_in_json()

        # test update server
        self.cmd('{} server update -g {} --name {} --admin-password {} '
                 '--ssl-enforcement Disabled --tags key=2'
                 .format(engine, rg, servers[0], admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        self.cmd('{} server update -g {} --name {} --compute-units {}'
                 .format(engine, rg, servers[0], new_cu),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test show server
        self.cmd('{} server show -g {} --name {}'
                 .format(engine, rg, servers[0]),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sslEnforcement', 'Disabled'),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('sku.capacity', new_cu),
                     JMESPathCheck('tags.key', '2'),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test restore to a new server
        self.cmd('{} server restore -g {} --name {} '
                 '--source-server {} '
                 '--restore-point-in-time {}'
                 .format(engine, resource_group_2, servers[1], result['id'],
                         datetime.utcnow().replace(tzinfo=tzutc()).isoformat()),
                 checks=[
                     JMESPathCheck('name', servers[1]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test list servers should be 2
        self.cmd('{} server list -g {}'.format(engine, rg),
                 checks=[JMESPathCheck('type(@)', 'array'),
                         JMESPathCheck('length(@)', 2)])

        # test delete server
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(engine, rg, servers[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} -n {} --yes'
                 .format(engine, rg, servers[1]), checks=NoneCheck())

        # test list server should be 0
        self.cmd('{} server list -g {}'.format(engine, rg), checks=[NoneCheck()])


class ProxyResourcesMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mysql')
    def test_mysql_proxy_resources_mgmt(self, resource_group, server, engine):
        self._test_firewall_mgmt(resource_group, server, engine)
        self._test_db_mgmt(resource_group, server, engine)
        self._test_configuration_mgmt(resource_group, server, engine)
        self._test_log_file_mgmt(resource_group, server, engine)

    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='postgres')
    def test_postgres_proxy_resources_mgmt(self, resource_group, server, engine):
        self._test_firewall_mgmt(resource_group, server, engine)
        self._test_db_mgmt(resource_group, server, engine)
        self._test_configuration_mgmt(resource_group, server, engine)
        self._test_log_file_mgmt(resource_group, server, engine)

    def _test_firewall_mgmt(self, resource_group, server, engine):
        rg = resource_group
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'

        # test firewall-rule create
        self.cmd('{} server firewall-rule create -n {} -g {} -s {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(engine, firewall_rule_1, rg, server,
                         start_ip_address_1, end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule show
        self.cmd('{} server firewall-rule show --name {} -g {} --server {}'
                 .format(engine, firewall_rule_1, rg, server),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule update
        self.cmd('{} server firewall-rule update -n {} -g {} -s {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(engine, firewall_rule_1, rg, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('{} server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {}'
                 .format(engine, firewall_rule_1, rg, server,
                         start_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('{} server firewall-rule update -n {} -g {} -s {} '
                 '--end-ip-address {}'
                 .format(engine, firewall_rule_1, rg, server,
                         end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test firewall-rule create another rule
        self.cmd('{} server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(engine, firewall_rule_2, rg, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_2),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test firewall-rule list
        self.cmd('{} server firewall-rule list -g {} -s {}'
                 .format(engine, rg, server), checks=[JMESPathCheck('length(@)', 2)])

        self.cmd('{} server firewall-rule delete --name {} -g {} --server {} --yes'
                 .format(engine, firewall_rule_1, rg, server), checks=NoneCheck())
        self.cmd('{} server firewall-rule list -g {} --server {}'
                 .format(engine, rg, server), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('{} server firewall-rule delete -n {} -g {} -s {} --yes'
                 .format(engine, firewall_rule_2, rg, server), checks=NoneCheck())
        self.cmd('{} server firewall-rule list -g {} --server {}'
                 .format(engine, rg, server), checks=[NoneCheck()])

    def _test_db_mgmt(self, resource_group, server, engine):

        rg = resource_group

        check = NoneCheck() if engine == 'mysql' else JMESPathCheck('type(@)', 'array')

        self.cmd('{} db list -g {} -s {}'
                 .format(engine, rg, server),
                 checks=[check])

    def _test_configuration_mgmt(self, resource_group, server, engine):
        rg = resource_group
        if engine == 'mysql':
            config_name = 'event_scheduler'
            default_value = 'OFF'
            new_value = 'ON'
        else:
            config_name = 'array_nulls'
            default_value = 'on'
            new_value = 'off'

        # test show configuration
        self.cmd('{} server configuration show --name {} -g {} --server {}'
                 .format(engine, config_name, rg, server),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', default_value),
                     JMESPathCheck('source', 'system-default')])

        # test update configuration
        self.cmd('{} server configuration set -n {} -g {} -s {} --value {}'
                 .format(engine, config_name, rg, server, new_value),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', new_value),
                     JMESPathCheck('source', 'user-override')])

        self.cmd('{} server configuration set -n {} -g {} -s {}'
                 .format(engine, config_name, rg, server),
                 checks=[
                     JMESPathCheck('name', config_name),
                     JMESPathCheck('value', default_value)])

        # test list configurations
        self.cmd('{} server configuration list -g {} -s {}'
                 .format(engine, rg, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

    def _test_log_file_mgmt(self, resource_group, server, engine):
        rg = resource_group

        if engine == 'mysql':
            config_name = 'slow_query_log'
            new_value = 'ON'

            # test update configuration
            self.cmd('{} server configuration set -n {} -g {} -s {} --value {}'
                     .format(engine, config_name, rg, server, new_value),
                     checks=[
                         JMESPathCheck('name', config_name),
                         JMESPathCheck('value', new_value)])

        # test list log files
        result = self.cmd('{} server-logs list -g {} -s {}'
                          .format(engine, rg, server),
                          checks=[
                              JMESPathCheck('length(@)', 1),
                              JMESPathCheck('type(@)', 'array')]).get_output_in_json()

        # test download file
        file_name = result[0]['name']
        self.cmd('{} server-logs download -g {} -s {} --name {}'
                 .format(engine, rg, server, file_name),
                 checks=[NoneCheck()])

        import os
        os.remove(file_name)
