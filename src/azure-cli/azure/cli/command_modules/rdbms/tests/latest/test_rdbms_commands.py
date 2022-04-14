# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from datetime import datetime
from dateutil.tz import tzutc  # pylint: disable=import-error
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from msrestazure.azure_exceptions import CloudError
from azure.core.exceptions import HttpResponseError
from azure.cli.core.util import CLIError
from azure.cli.core.util import parse_proxy_resource_id
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError  # pylint: disable=unused-import
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StringContainCheck,
    live_only)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)

# Constants
SERVER_NAME_PREFIX = 'azuredbclitest'
SERVER_NAME_MAX_LENGTH = 63


class ServerPreparer(AbstractPreparer, SingleValueReplacer):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, engine_type='mysql', engine_parameter_name='database_engine',
                 name_prefix=SERVER_NAME_PREFIX, parameter_name='server', location='westus',
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_mariadb_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mariadb', resource_group_1, resource_group_2)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_mysql_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('mysql', resource_group_1, resource_group_2)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    def test_postgres_server_mgmt(self, resource_group_1, resource_group_2):
        self._test_server_mgmt('postgres', resource_group_1, resource_group_2)

    def _test_server_mgmt(self, database_engine, resource_group_1, resource_group_2):
        servers = [self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbclirestore', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbcligeorestore', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbcliinfraencrypt', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbcliupgrade', SERVER_NAME_MAX_LENGTH)]

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
        loc = 'westus2'
        default_public_network_access = 'Enabled'
        public_network_access = 'Disabled'
        minimal_tls_version = 'TLS1_2'
        default_minimal_tls_version = 'TLSEnforcementDisabled'

        geoGeoRedundantBackup = 'Disabled'
        geoBackupRetention = 20
        infrastructureEncryption = 'Enabled'
        geoloc = 'eastus'

        if self.cli_ctx.local_context.is_on:
            self.cmd('local-context off')

        list_checks = [JMESPathCheck('name', servers[0]),
                       JMESPathCheck('resourceGroup', resource_group_1),
                       JMESPathCheck('administratorLogin', admin_login),
                       JMESPathCheck('sslEnforcement', 'Enabled'),
                       JMESPathCheck('tags.key', '1'),
                       JMESPathCheck('sku.capacity', old_cu),
                       JMESPathCheck('sku.tier', edition),
                       JMESPathCheck('storageProfile.backupRetentionDays', backupRetention),
                       JMESPathCheck('publicNetworkAccess', default_public_network_access),
                       JMESPathCheck('storageProfile.geoRedundantBackup', geoRedundantBackup)]

        if database_engine != 'mariadb':
            list_checks.append(JMESPathCheck('minimalTlsVersion', default_minimal_tls_version))

        # test create server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--sku-name {} --tags key=1 --geo-redundant-backup {} '
                 '--backup-retention {}'
                 .format(database_engine, resource_group_1, servers[0], loc,
                         admin_login, admin_passwords[0], skuname,
                         geoRedundantBackup, backupRetention),
                 checks=list_checks)

        # test show server
        result = self.cmd('{} server show -g {} --name {}'
                          .format(database_engine, resource_group_1, servers[0]),
                          checks=list_checks).get_output_in_json()

        # test update server
        if database_engine != 'mariadb':
            self.cmd('{} server update -g {} --name {} --minimal-tls-version {}'
                     .format(database_engine, resource_group_1, servers[0], minimal_tls_version),
                     checks=[
                         JMESPathCheck('name', servers[0]),
                         JMESPathCheck('resourceGroup', resource_group_1),
                         JMESPathCheck('minimalTlsVersion', minimal_tls_version)])

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

        self.cmd('{} server update -g {} --name {} --public-network-access {}'
                 .format(database_engine, resource_group_1, servers[0], public_network_access),
                 checks=[
                     JMESPathCheck('name', servers[0]),
                     JMESPathCheck('resourceGroup', resource_group_1),
                     JMESPathCheck('publicNetworkAccess', public_network_access)])

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

        # Before we do restore we will have to check whether the current time is less than earliest restore time
        current_time = datetime.utcnow().replace(tzinfo=tzutc()).isoformat()
        earliest_restore_time = result['earliestRestoreDate']
        date_format = '%Y-%m-%dT%H:%M:%S.%f+00:00'

        if current_time < earliest_restore_time:
            time.sleep((datetime.strptime(earliest_restore_time, date_format) - datetime.strptime(current_time,
                                                                                             date_format)).total_seconds())

        self.cmd('{} server restore -g {} --name {} '
                 '--source-server {} '
                 '--restore-point-in-time {}'
                 .format(database_engine, resource_group_2, servers[1], result['id'],
                         earliest_restore_time),
                 checks=[
                     JMESPathCheck('name', servers[1]),
                     JMESPathCheck('resourceGroup', resource_group_2),
                     JMESPathCheck('sku.tier', edition),
                     JMESPathCheck('administratorLogin', admin_login)])

        # test georestore server
        with self.assertRaises(HttpResponseError) as exception:
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

        # test infrastructre encryption on server
        if database_engine != 'mariadb':
            self.cmd('{} server create -g {} --name {} -l {} '
                     '--admin-user {} --admin-password {} '
                     '--sku-name {} --tags key=1 --geo-redundant-backup {} '
                     '--backup-retention {} --infrastructure-encryption {}'
                     .format(database_engine, resource_group_1, servers[3], loc,
                             admin_login, admin_passwords[0], skuname,
                             geoRedundantBackup, backupRetention, infrastructureEncryption),
                     checks=[
                         JMESPathCheck('name', servers[3]),
                         JMESPathCheck('resourceGroup', resource_group_1),
                         JMESPathCheck('administratorLogin', admin_login),
                         JMESPathCheck('sslEnforcement', 'Enabled'),
                         JMESPathCheck('infrastructureEncryption', 'Enabled'),
                         JMESPathCheck('tags.key', '1'),
                         JMESPathCheck('sku.capacity', old_cu),
                         JMESPathCheck('sku.tier', edition),
                         JMESPathCheck('storageProfile.backupRetentionDays', backupRetention),
                         JMESPathCheck('publicNetworkAccess', default_public_network_access),
                         JMESPathCheck('storageProfile.geoRedundantBackup', geoRedundantBackup)])

        # test list servers
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_2),
                 checks=[JMESPathCheck('type(@)', 'array')])

        # test list servers without resource group
        self.cmd('{} server list'.format(database_engine),
                 checks=[JMESPathCheck('type(@)', 'array')])

        connection_string = self.cmd('{} server show-connection-string -s {}'
                                     .format(database_engine, servers[0])).get_output_in_json()

        self.assertIn('jdbc', connection_string['connectionStrings'])
        self.assertIn('node.js', connection_string['connectionStrings'])
        self.assertIn('php', connection_string['connectionStrings'])
        self.assertIn('python', connection_string['connectionStrings'])
        self.assertIn('ruby', connection_string['connectionStrings'])
        # test mysql version upgrade
        if database_engine == 'mysql':
            self.cmd('{} server create -g {} --name {} -l {} '
                     '--admin-user {} --admin-password {} '
                     '--sku-name {} --tags key=1 --geo-redundant-backup {} '
                     '--backup-retention {} --version 5.6'
                     .format(database_engine, resource_group_1, servers[4], loc,
                             admin_login, admin_passwords[0], skuname,
                             geoRedundantBackup, backupRetention),
                     checks=[
                         JMESPathCheck('version', '5.6')])
            self.cmd('{} server upgrade -g {} --name {} --target-server-version 5.7'
                     .format(database_engine, resource_group_1, servers[4]), checks=NoneCheck())
            result = self.cmd('{} server show -g {} -n {}'
                              .format(database_engine, resource_group_1, servers[4])).get_output_in_json()
            server_version = result['version']
            self.assertEqual(server_version, '5.7')

        # test delete server
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group_1, servers[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} -n {} --yes'
                 .format(database_engine, resource_group_2, servers[1]), checks=NoneCheck())
        if database_engine != 'mariadb':
            self.cmd('{} server delete -g {} -n {} --yes'
                     .format(database_engine, resource_group_1, servers[3]), checks=NoneCheck())
        if database_engine == 'mysql':
            self.cmd('{} server delete -g {} -n {} --yes'
                     .format(database_engine, resource_group_1, servers[4]), checks=NoneCheck())

        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_1), checks=[NoneCheck()])
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_2), checks=[NoneCheck()])

        self.cmd('{} server list-skus -l {}'.format(database_engine, loc),
                 checks=[JMESPathCheck('type(@)', 'array')])


class ProxyResourcesMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mariadb')
    def test_mariadb_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)
        self._test_private_link_resource(resource_group, server, database_engine, 'mariadbServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine)

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='mysql')
    def test_mysql_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)
        self._test_private_link_resource(resource_group, server, database_engine, 'mysqlServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine)
        # self._test_data_encryption(resource_group, server, database_engine, self.create_random_name('mysql', 24))
        self._test_aad_admin(resource_group, server, database_engine)

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @ServerPreparer(engine_type='postgres')
    def test_postgres_proxy_resources_mgmt(self, resource_group, server, database_engine):
        self._test_firewall_mgmt(resource_group, server, database_engine)
        self._test_vnet_firewall_mgmt(resource_group, server, database_engine)
        self._test_db_mgmt(resource_group, server, database_engine)
        self._test_configuration_mgmt(resource_group, server, database_engine)
        self._test_log_file_mgmt(resource_group, server, database_engine)
        self._test_private_link_resource(resource_group, server, database_engine, 'postgresqlServer')
        self._test_private_endpoint_connection(resource_group, server, database_engine)
        # self._test_data_encryption(resource_group, server, database_engine, self.create_random_name('postgres', 24))
        self._test_aad_admin(resource_group, server, database_engine)

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
        location = 'westus'
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
                 '--address-prefix {} --subnet-name {} --subnet-prefix {}'.format(vnet_name, resource_group, location,
                                                                                  address_prefix, subnet_name_1,
                                                                                  subnet_prefix_1))
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

    def _test_private_link_resource(self, resource_group, server, database_engine, group_id):
        result = self.cmd('{} server private-link-resource list -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(result[0]['properties']['groupId'], group_id)

    def _test_private_endpoint_connection(self, resource_group, server, database_engine):
        loc = 'westus'
        vnet = self.create_random_name('cli-vnet-', 24)
        subnet = self.create_random_name('cli-subnet-', 24)
        pe_name_auto = self.create_random_name('cli-pe-', 24)
        pe_name_manual_approve = self.create_random_name('cli-pe-', 24)
        pe_name_manual_reject = self.create_random_name('cli-pe-', 24)
        pe_connection_name_auto = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_approve = self.create_random_name('cli-pec-', 24)
        pe_connection_name_manual_reject = self.create_random_name('cli-pec-', 24)

        # Prepare network and disable network policies
        self.cmd('network vnet create -n {} -g {} -l {} --subnet-name {}'
                 .format(vnet, resource_group, loc, subnet),
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {} --vnet-name {} -g {} '
                 '--disable-private-endpoint-network-policies true'
                 .format(subnet, vnet, resource_group),
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Get Server Id and Group Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        server_id = result['id']
        result = self.cmd('{} server private-link-resource list -g {} -s {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        group_id = result[0]['properties']['groupId']

        approval_description = 'You are approved!'
        rejection_description = 'You are rejected!'
        expectedError = 'Private Endpoint Connection Status is not Pending'

        # Testing Auto-Approval workflow
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {}'
                                    .format(resource_group, pe_name_auto, vnet, subnet, loc, pe_connection_name_auto,
                                            server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_auto)
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], pe_connection_name_auto)
        self.assertEqual(
            private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
            'Approved')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(HttpResponseError, expectedError):
            self.cmd('{} server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server, resource_group, server_pec_name, approval_description))

        with self.assertRaisesRegex(HttpResponseError, expectedError):
            self.cmd('{} server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server, resource_group, server_pec_name, rejection_description))

        self.cmd('{} server private-endpoint-connection delete --id {}'
                 .format(database_engine, server_pec_id))

        # Testing Manual-Approval workflow [Approval]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request'
                                    .format(resource_group, pe_name_manual_approve, vnet, subnet, loc,
                                            pe_connection_name_manual_approve, server_id,
                                            group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_approve)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_approve)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Ready')
                 ])

        self.cmd('{} server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                 .format(database_engine, server, resource_group, server_pec_name, approval_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Approved'),
                     self.check('privateLinkServiceConnectionState.description', approval_description),
                     self.check('provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(HttpResponseError, expectedError):
            self.cmd('{} server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server, resource_group, server_pec_name, rejection_description))

        self.cmd('{} server private-endpoint-connection delete --id {}'
                 .format(database_engine, server_pec_id))

        # Testing Manual-Approval workflow [Rejection]
        # Create a private endpoint connection
        private_endpoint = self.cmd('network private-endpoint create -g {} -n {} --vnet-name {} --subnet {} -l {} '
                                    '--connection-name {} --private-connection-resource-id {} '
                                    '--group-id {} --manual-request true'
                                    .format(resource_group, pe_name_manual_reject, vnet, subnet, loc,
                                            pe_connection_name_manual_reject, server_id, group_id)).get_output_in_json()
        self.assertEqual(private_endpoint['name'], pe_name_manual_reject)
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['name'],
                         pe_connection_name_manual_reject)
        self.assertEqual(
            private_endpoint['manualPrivateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'],
            'Pending')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['manualPrivateLinkServiceConnections'][0]['groupIds'][0], group_id)

        # Get Private Endpoint Connection Name and Id
        result = self.cmd('{} server show -g {} -n {}'
                          .format(database_engine, resource_group, server)).get_output_in_json()
        self.assertEqual(len(result['privateEndpointConnections']), 1)
        self.assertEqual(
            result['privateEndpointConnections'][0]['properties']['privateLinkServiceConnectionState']['status'],
            'Pending')
        server_pec_id = result['privateEndpointConnections'][0]['id']
        result = parse_proxy_resource_id(server_pec_id)
        server_pec_name = result['child_name_1']

        self.cmd('{} server private-endpoint-connection show --server-name {} -g {} --name {}'
                 .format(database_engine, server, resource_group, server_pec_name),
                 checks=[
                     self.check('id', server_pec_id),
                     self.check('privateLinkServiceConnectionState.status', 'Pending'),
                     self.check('provisioningState', 'Ready')
                 ])

        self.cmd('{} server private-endpoint-connection reject --server-name {} -g {} --name {} --description "{}"'
                 .format(database_engine, server, resource_group, server_pec_name, rejection_description),
                 checks=[
                     self.check('privateLinkServiceConnectionState.status', 'Rejected'),
                     self.check('privateLinkServiceConnectionState.description', rejection_description),
                     self.check('provisioningState', 'Ready')
                 ])

        with self.assertRaisesRegex(HttpResponseError, expectedError):
            self.cmd('{} server private-endpoint-connection approve --server-name {} -g {} --name {} --description "{}"'
                     .format(database_engine, server, resource_group, server_pec_name, approval_description))

        self.cmd('{} server private-endpoint-connection delete --id {}'
                 .format(database_engine, server_pec_id))

    def _test_data_encryption(self, resource_group, server, database_engine, vault_name):
        resource_prefix = 'ossrdbmsbyok'
        key_name = self.create_random_name(resource_prefix, 32)

        # add identity to server
        server_resp = self.cmd('{} server update -g {} --name {} --assign-identity'
                               .format(database_engine, resource_group, server)).get_output_in_json()

        server_identity = server_resp['identity']['principalId']

        # create vault and acl server identity
        self.cmd(
            'keyvault create -g {} -n {} --location westus --enable-soft-delete true --enable-purge-protection true'
            .format(resource_group, vault_name))

        # create key
        key_resp = self.cmd('keyvault key create --name {} -p software --vault-name {}'
                            .format(key_name, vault_name)).get_output_in_json()

        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions wrapKey unwrapKey get list'
                 .format(resource_group, vault_name, server_identity))

        # add server key
        kid = key_resp['key']['kid']
        server_key_resp = self.cmd('{} server key create -g {} --name {} --kid {}'
                                   .format(database_engine, resource_group, server, kid),
                                   checks=[JMESPathCheck('uri', kid)])

        server_key_name = server_key_resp.get_output_in_json()['name']

        # validate show key
        self.cmd('{} server key show -g {} --name {} --kid {}'
                 .format(database_engine, resource_group, server, kid),
                 checks=[
                     JMESPathCheck('uri', kid),
                     JMESPathCheck('name', server_key_name)])

        # validate list key (should return 1 items)
        self.cmd('{} server key list -g {} --name {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('length(@)', 1)])

        # delete server key
        self.cmd('{} server key delete -g {} --name {} --kid {} --yes'
                 .format(database_engine, resource_group, server, kid))

        # wait for key to be deleted
        time.sleep(10)

        # validate deleted server key via list (should return no item)
        self.cmd('{} server key list -g {} -s {}'
                 .format(database_engine, resource_group, server),
                 checks=[JMESPathCheck('length(@)', 0)])

    def _test_aad_admin(self, resource_group, server, database_engine):
        oid = '5e90ef3b-9b42-4777-819b-25c36961ea4d'
        oid2 = 'e4d43337-d52c-4a0c-b581-09055e0359a0'
        user = 'DSEngAll'
        user2 = 'TestUser'

        self.cmd('{} server ad-admin create --server-name {} -g {} -i {} -u {}'
                 .format(database_engine, server, resource_group, oid, user),
                 checks=[
                     self.check('login', user),
                     self.check('sid', oid)])

        self.cmd('{} server ad-admin show --server-name {} -g {}'
                 .format(database_engine, server, resource_group),
                 checks=[
                     self.check('login', user),
                     self.check('sid', oid)])

        self.cmd('{} server ad-admin list --server-name {} -g {}'
                 .format(database_engine, server, resource_group),
                 checks=[
                     self.check('[0].login', user),
                     self.check('[0].sid', oid)])

        self.cmd('{} server ad-admin create --server-name {} -g {} -i {} -u {} --no-wait'
                 .format(database_engine, server, resource_group, oid2, user2))

        self.cmd('{} server ad-admin wait --server-name {} -g {} --created'
                 .format(database_engine, server, resource_group))

        self.cmd('{} server ad-admin delete --server-name {} -g {} --yes'
                 .format(database_engine, server, resource_group))

        self.cmd('{} server ad-admin list --server-name {} -g {}'
                 .format(database_engine, server, resource_group),
                 checks=[
                     self.check('[0].login', None),
                     self.check('[0].sid', None)])


class ReplicationMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    @ResourceGroupPreparer(parameter_name='resource_group')
    def test_mysql_replica_mgmt(self, resource_group):
        self._test_replica_mgmt(resource_group, 'mysql')

    def _test_replica_mgmt(self, resource_group, database_engine):
        server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        result = self.cmd('{} server create -g {} --name {} -l westus '
                          '--admin-user cloudsa --admin-password SecretPassword123 '
                          '--sku-name GP_Gen5_2'
                          .format(database_engine, resource_group, server),
                          checks=[
                              JMESPathCheck('name', server),
                              JMESPathCheck('resourceGroup', resource_group),
                              JMESPathCheck('sslEnforcement', 'Enabled'),
                              JMESPathCheck('sku.name', 'GP_Gen5_2'),
                              JMESPathCheck('replicationRole', 'None'),
                              JMESPathCheck('masterServerId', '')]).get_output_in_json()

        # test replica create
        self.cmd('{} server replica create -g {} -n {} -l westus --sku-name GP_Gen5_4 '
                 '--source-server {}'
                 .format(database_engine, resource_group, replicas[0], result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', 'GP_Gen5_4'),
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
                     JMESPathCheck('sku.name', 'GP_Gen5_4'),
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


class ReplicationPostgreSqlMgmtScenarioTest(ScenarioTest):  # pylint: disable=too-few-public-methods

    @ResourceGroupPreparer(parameter_name='resource_group')
    def test_postgrsql_basic_replica_mgmt(self, resource_group):
        self._test_replica_mgmt(resource_group, 'B_Gen5_2', 'B_Gen5_2', True)

    @ResourceGroupPreparer(parameter_name='resource_group')
    def test_postgrsql_general_purpose_replica_mgmt(self, resource_group):
        self._test_replica_mgmt(resource_group, 'GP_Gen5_2', 'GP_Gen5_4', False)

    def _test_replica_mgmt(self, resource_group, skuName, testSkuName, isBasicTier):
        database_engine = 'postgres'
        server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        server = self.create_random_name(SERVER_NAME_PREFIX, 32)
        replicas = [self.create_random_name('azuredbclirep1', SERVER_NAME_MAX_LENGTH),
                    self.create_random_name('azuredbclirep2', SERVER_NAME_MAX_LENGTH)]

        # create a server
        result = self.cmd('{} server create -g {} --name {} -l westus '
                          '--admin-user cloudsa --admin-password SecretPassword123 '
                          '--sku-name {}'
                          .format(database_engine, resource_group, server, skuName),
                          checks=[
                              JMESPathCheck('name', server),
                              JMESPathCheck('resourceGroup', resource_group),
                              JMESPathCheck('sslEnforcement', 'Enabled'),
                              JMESPathCheck('sku.name', skuName),
                              JMESPathCheck('replicationRole', 'None'),
                              JMESPathCheck('masterServerId', '')]).get_output_in_json()

        if isBasicTier is False:
            # enable replication support for  GP/MO servers
            self.cmd('{} server configuration set -g {} -s {} -n azure.replication_support --value REPLICA'
                     .format(database_engine, resource_group, server),
                     checks=[
                         JMESPathCheck('name', 'azure.replication_support'),
                         JMESPathCheck('value', 'REPLICA')])
            # restart server
            self.cmd('{} server restart -g {} --name {}'
                     .format(database_engine, resource_group, server), checks=NoneCheck())
            time.sleep(120)

        # test replica create
        self.cmd('{} server replica create -g {} -n {} -l westus --sku-name {} '
                 '--source-server {}'
                 .format(database_engine, resource_group, replicas[0], testSkuName, result['id']),
                 checks=[
                     JMESPathCheck('name', replicas[0]),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('sku.name', testSkuName),
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

        # test replica delete
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())

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

        # test show server with replication info, replica was auto stopped after master server deleted
        # self.cmd('{} server show -g {} --name {}'
        #          .format(database_engine, resource_group, replicas[1]),
        #          checks=[
        #              JMESPathCheck('replicationRole', 'None'),
        #              JMESPathCheck('masterServerId', ''),
        #              JMESPathCheck('replicaCapacity', result['replicaCapacity'])])

        # clean up servers
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group, replicas[1]), checks=NoneCheck())


class ServerMgmtScenarioPublicParameterTest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @live_only()
    def test_mariadb_server_mgmt_public_parameter(self, resource_group_1):
        self._test_server_mgmt_public_parameter('mariadb', resource_group_1)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @live_only()
    def test_mysql_server_mgmt_public_parameter(self, resource_group_1):
        self._test_server_mgmt_public_parameter('mysql', resource_group_1)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @live_only()
    def test_postgres_server_mgmt_public_parameter(self, resource_group_1):
        self._test_server_mgmt_public_parameter('postgres', resource_group_1)

    def _test_server_mgmt_public_parameter(self, database_engine, resource_group_1):
        servers = [self.create_random_name('azuredbclipublicall', SERVER_NAME_MAX_LENGTH),
                   self.create_random_name('azuredbclipublicazureservices', SERVER_NAME_MAX_LENGTH)]
        admin_login = 'cloudsa'
        admin_password = 'SecretPassword123'
        old_cu = 2
        family = 'Gen5'
        skuname = 'GP_{}_{}'.format(family, old_cu)
        loc = 'westus2'

        # test public access for all IPs on server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--sku-name {} --tags key=1 --public {}'
                 .format(database_engine, resource_group_1, servers[0], loc,
                         admin_login, admin_password, skuname, 'all'),
                 checks=[JMESPathCheck('name', servers[0]),
                         JMESPathCheck('resourceGroup', resource_group_1),
                         JMESPathCheck('sku.capacity', old_cu),
                         StringContainCheck('AllowAll_')])

        # test public access for all azure services on server
        self.cmd('{} server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {} '
                 '--sku-name {} --tags key=1 --public {}'
                 .format(database_engine, resource_group_1, servers[1], loc,
                         admin_login, admin_password, skuname, '0.0.0.0'),
                 checks=[JMESPathCheck('name', servers[1]),
                         JMESPathCheck('resourceGroup', resource_group_1),
                         JMESPathCheck('sku.capacity', old_cu),
                         StringContainCheck('AllowAllAzureServicesAndResourcesWithinAzureIps_')])
        # test delete server
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group_1, servers[0]), checks=NoneCheck())
        self.cmd('{} server delete -g {} --name {} --yes'
                 .format(database_engine, resource_group_1, servers[1]), checks=NoneCheck())
        # test list server should be 0
        self.cmd('{} server list -g {}'.format(database_engine, resource_group_1), checks=[NoneCheck()])
