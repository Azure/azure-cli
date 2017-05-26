# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk import (
    JMESPathCheck,
    JMESPathCheckExists,
    JMESPathCheckGreaterThan,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    StorageAccountPreparer)
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)


# Constants
server_name_prefix = 'clitestserver'
server_name_max_length = 63


class SqlServerPreparer(AbstractPreparer, SingleValueReplacer):
    def __init__(self, name_prefix=server_name_prefix, parameter_name='server', location='westus',
                 admin_user='admin123', admin_password='SecretPassword123',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(SqlServerPreparer, self).__init__(name_prefix, server_name_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        template = 'az sql server create -l {} -g {} -n {} -u {} -p {}'
        execute(template.format(self.location, group, name, self.admin_user, self.admin_password))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute('az sql server delete -g {} -n {} --yes --no-wait'.format(group, name))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a sql server account a resource group is required. Please add ' \
                       'decorator @{} in front of this storage account preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))


class SqlServerMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_sql_server_mgmt(self, resource_group, resource_group_location):
        server1 = self.create_random_name(server_name_prefix, server_name_max_length)
        server2 = self.create_random_name(server_name_prefix, server_name_max_length)
        admin_login = 'admin123'
        admin_passwords = ['SecretPassword123', 'SecretPassword456']

        rg = resource_group
        loc = resource_group_location
        user = admin_login

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, server1, loc, user, admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', admin_passwords[0])])

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 1)])

        # test update sql server
        self.cmd('sql server update -g {} --name {} --admin-password {}'
                 .format(rg, server1, admin_passwords[1]),
                 checks=[
                     JMESPathCheck('name', server1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', admin_passwords[1])])

        # test create another sql server
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, server2, loc, user, admin_passwords[0]),
                 checks=[
                     JMESPathCheck('name', server2),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', admin_passwords[0])])

        # test list sql server should be 2
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 2)])

        # test show sql server
        self.cmd('sql server show -g {} --name {}'
                 .format(rg, server1),
                 checks=[
                     JMESPathCheck('name', server1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        self.cmd('sql server list-usages -g {} -n {}'
                 .format(rg, server1),
                 checks=[JMESPathCheck('[0].resourceName', server1)])

        # test delete sql server
        self.cmd('sql server delete -g {} --name {} --yes'
                 .format(rg, server1), checks=NoneCheck())
        self.cmd('sql server delete -g {} --name {} --yes'
                 .format(rg, server2), checks=NoneCheck())

        # test list sql server should be 0
        self.cmd('sql server list -g {}'.format(rg), checks=[NoneCheck()])


class SqlServerFirewallMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    @SqlServerPreparer()
    def test_sql_firewall_mgmt(self, resource_group, resource_group_location, server):
        rg = resource_group
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'
        # allow_all_azure_ips_rule = 'AllowAllAzureIPs'
        # allow_all_azure_ips_address = '0.0.0.0'

        # test sql server firewall-rule create
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, server,
                         start_ip_address_1, end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule show
        self.cmd('sql server firewall-rule show --name {} -g {} --server {}'
                 .format(firewall_rule_1, rg, server),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule update
        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {}'
                 .format(firewall_rule_1, rg, server,
                         start_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--end-ip-address {}'
                 .format(firewall_rule_1, rg, server,
                         end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule create another rule
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_2, rg, server,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_2),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall-rule list
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, server), checks=[JMESPathCheck('length(@)', 2)])

        # # test sql server firewall-rule create azure ip rule
        # self.cmd('sql server firewall-rule allow-all-azure-ips -g {} --server {} '
        #          .format(rg, server), checks=[
        #                      JMESPathCheck('name', allow_all_azure_ips_rule),
        #                      JMESPathCheck('resourceGroup', rg),
        #                      JMESPathCheck('startIpAddress', allow_all_azure_ips_address),
        #                      JMESPathCheck('endIpAddress', allow_all_azure_ips_address)])

        # # test sql server firewall-rule list
        # self.cmd('sql server firewall-rule list -g {} --server {}'
        #          .format(rg, server), checks=[JMESPathCheck('length(@)', 3)])

        # # test sql server firewall-rule delete
        # self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
        #          .format(allow_all_azure_ips_rule, rg, server), checks=NoneCheck())
        # self.cmd('sql server firewall-rule list -g {} --server {}'
        #          .format(rg, server), checks=[JMESPathCheck('length(@)', 2)])
        self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
                 .format(firewall_rule_1, rg, server), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, server), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
                 .format(firewall_rule_2, rg, server), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, server), checks=[NoneCheck()])


class SqlServerDbMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer()
    def test_sql_db_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"
        update_service_objective = 'S1'
        update_storage = '10GB'
        update_storage_bytes = str(10 * 1024 * 1024 * 1024)

        rg = resource_group
        loc_display = 'West US'

        # test sql db commands
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('location', loc_display),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db list -g {} --server {}'
                 .format(rg, server),
                 checks=[
                     JMESPathCheck('length(@)', 2),
                     JMESPathCheck('sort([].name)', sorted([database_name, 'master'])),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[1].resourceGroup', rg)])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', rg)])

        self.cmd('sql db list-usages -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[JMESPathCheck('[0].resourceName', database_name)])

        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --max-size {}'
                 ' --set tags.key1=value1'
                 .format(rg, server, database_name,
                         update_service_objective, update_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('requestedServiceObjectiveName', update_service_objective),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql db delete -g {} --server {} --name {} --yes'
                 .format(rg, server, database_name),
                 checks=[NoneCheck()])


class SqlServerDbCopyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name='resource_group_1')
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    @SqlServerPreparer(parameter_name='server1', resource_group_parameter_name='resource_group_1')
    @SqlServerPreparer(parameter_name='server2', resource_group_parameter_name='resource_group_2')
    def test_sql_db_copy(self, resource_group_1, resource_group_2,
                         resource_group_location,
                         server1, server2):

        database_name = "cliautomationdb01"
        database_copy_name = "cliautomationdb02"
        service_objective = 'S1'

        rg = resource_group_1
        loc_display = 'West US'

        # create database
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(rg, server1, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('location', loc_display),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        # copy database to same server (min parameters)
        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {}'
                 .format(rg, server1, database_name, database_copy_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_copy_name)
                 ])

        # copy database to other server (max parameters)
        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {} --dest-resource-group {} --dest-server {} '
                 '--service-objective {}'
                 .format(rg, server1, database_name, database_copy_name,
                         resource_group_2, server2, service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group_2),
                     JMESPathCheck('name', database_copy_name),
                     JMESPathCheck('requestedServiceObjectiveName', service_objective)
                 ])


class SqlServerDbRestoreScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer()
    def test_sql_db_restore(self, resource_group, resource_group_location, server):
        from datetime import datetime
        from time import sleep

        rg = resource_group
        database_name = 'cliautomationdb01'

        # Standalone db
        restore_service_objective = 'S1'
        restore_edition = 'Standard'
        restore_standalone_database_name = 'cliautomationdb01restore1'

        restore_pool_database_name = 'cliautomationdb01restore2'
        elastic_pool = 'cliautomationpool1'

        # create db
        db = self.cmd('sql db create -g {} --server {} --name {}'
                      .format(rg, server, database_name),
                      checks=[
                          JMESPathCheck('resourceGroup', rg),
                          JMESPathCheck('name', database_name),
                          JMESPathCheck('status', 'Online')])

        # create elastic pool
        self.cmd('sql elastic-pool create -g {} -s {} -n {}'
                 .format(rg, server, elastic_pool))

        # Wait until earliestRestoreDate is in the past. When run live, this will take at least
        # 10 minutes. Unforunately there's no way to speed this up.
        earliest_restore_date = datetime.strptime(db.get_output_in_json()['earliestRestoreDate'],
                                                  "%Y-%m-%dT%H:%M:%S.%f+00:00")
        while datetime.utcnow() <= earliest_restore_date:
            sleep(10)  # seconds

        # Restore to standalone db
        db = self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {}'
                      ' --service-objective {} --edition {}'
                      .format(rg, server, database_name, datetime.utcnow().isoformat(),
                              restore_standalone_database_name, restore_service_objective,
                              restore_edition),
                      checks=[
                          JMESPathCheck('resourceGroup', rg),
                          JMESPathCheck('name', restore_standalone_database_name),
                          JMESPathCheck('requestedServiceObjectiveName',
                                        restore_service_objective),
                          JMESPathCheck('status', 'Online')])

        # Restore to db into pool
        db = self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {}'
                      ' --elastic-pool {}'
                      .format(rg, server, database_name, datetime.utcnow().isoformat(),
                              restore_pool_database_name, elastic_pool),
                      checks=[
                          JMESPathCheck('resourceGroup', rg),
                          JMESPathCheck('name', restore_pool_database_name),
                          JMESPathCheck('elasticPoolName', elastic_pool),
                          JMESPathCheck('status', 'Online')])


class SqlServerDbSecurityScenarioTest(ScenarioTest):
    def _get_storage_endpoint(self, storage_account, resource_group):
        return self.cmd('storage account show -g {} -n {}'
                        ' --query primaryEndpoints.blob'
                        .format(resource_group, storage_account)).get_output_in_json()

    def _get_storage_key(self, storage_account, resource_group):
        return self.cmd('storage account keys list -g {} -n {} --query [0].value'
                        .format(resource_group, storage_account)).get_output_in_json()

    @ResourceGroupPreparer()
    @ResourceGroupPreparer(parameter_name='resource_group_2')
    @SqlServerPreparer()
    @StorageAccountPreparer()
    @StorageAccountPreparer(parameter_name='storage_account_2',
                            resource_group_parameter_name='resource_group_2')
    def test_sql_db_security_mgmt(self, resource_group, resource_group_2,
                                  resource_group_location, server,
                                  storage_account, storage_account_2):
        database_name = "cliautomationdb01"

        # get storage account endpoint and key
        storage_endpoint = self._get_storage_endpoint(storage_account, resource_group)
        key = self._get_storage_key(storage_account, resource_group)

        # create db
        self.cmd('sql db create -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('status', 'Online')])

        # get audit policy
        self.cmd('sql db audit-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('resourceGroup', resource_group)])

        # update audit policy - enable
        state_enabled = 'Enabled'
        key
        retention_days = 30
        audit_actions_input = 'DATABASE_LOGOUT_GROUP DATABASE_ROLE_MEMBER_CHANGE_GROUP'
        audit_actions_expected = ['DATABASE_LOGOUT_GROUP',
                                  'DATABASE_ROLE_MEMBER_CHANGE_GROUP']

        self.cmd('sql db audit-policy update -g {} -s {} -n {}'
                 ' --state {} --storage-key {} --storage-endpoint={}'
                 ' --retention-days={} --actions {}'
                 .format(resource_group, server, database_name, state_enabled, key,
                         storage_endpoint, retention_days, audit_actions_input),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', ''),  # service doesn't return it
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # update audit policy - specify storage account and resource group. use secondary key
        storage_endpoint_2 = self._get_storage_endpoint(storage_account_2, resource_group_2)
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --storage-account {}'
                 .format(resource_group, server, database_name, storage_account_2,
                         resource_group_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', ''),  # service doesn't return it
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # update audit policy - disable
        state_disabled = 'Disabled'
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {}'
                 .format(resource_group, server, database_name, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_disabled),
                     JMESPathCheck('storageAccountAccessKey', ''),  # service doesn't return it
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])

        # get threat detection policy
        self.cmd('sql db threat-policy show -g {} -s {} -n {}'
                 .format(resource_group, server, database_name),
                 checks=[JMESPathCheck('resourceGroup', resource_group)])

        # update threat detection policy - enable
        disabled_alerts_input = 'Sql_Injection_Vulnerability Access_Anomaly'
        disabled_alerts_expected = 'Sql_Injection_Vulnerability;Access_Anomaly'
        email_addresses_input = 'test1@example.com test2@example.com'
        email_addresses_expected = 'test1@example.com;test2@example.com'
        email_account_admins = 'Enabled'

        self.cmd('sql db threat-policy update -g {} -s {} -n {}'
                 ' --state {} --storage-key {} --storage-endpoint {}'
                 ' --retention-days {} --email-addresses {} --disabled-alerts {}'
                 ' --email-account-admins {}'
                 .format(resource_group, server, database_name, state_enabled, key,
                         storage_endpoint, retention_days, email_addresses_input,
                         disabled_alerts_input, email_account_admins),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', key),
                     JMESPathCheck('storageEndpoint', storage_endpoint),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('emailAddresses', email_addresses_expected),
                     JMESPathCheck('disabledAlerts', disabled_alerts_expected),
                     JMESPathCheck('emailAccountAdmins', email_account_admins)])

        # update threat policy - specify storage account and resource group. use secondary key
        key_2 = self._get_storage_key(storage_account_2, resource_group_2)
        self.cmd('sql db threat-policy update -g {} -s {} -n {} --storage-account {}'
                 .format(resource_group, server, database_name, storage_account_2,
                         resource_group_2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_enabled),
                     JMESPathCheck('storageAccountAccessKey', key_2),
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('emailAddresses', email_addresses_expected),
                     JMESPathCheck('disabledAlerts', disabled_alerts_expected),
                     JMESPathCheck('emailAccountAdmins', email_account_admins)])

        # update threat policy - disable
        self.cmd('sql db audit-policy update -g {} -s {} -n {} --state {}'
                 .format(resource_group, server, database_name, state_disabled),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('state', state_disabled),
                     JMESPathCheck('storageAccountAccessKey', ''),  # service doesn't return it
                     JMESPathCheck('storageEndpoint', storage_endpoint_2),
                     JMESPathCheck('retentionDays', retention_days),
                     JMESPathCheck('auditActionsAndGroups', audit_actions_expected)])


class SqlServerDwMgmtScenarioTest(ScenarioTest):
    # pylint: disable=too-many-instance-attributes
    @ResourceGroupPreparer()
    @SqlServerPreparer()
    def test_sql_dw_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb01"
        update_service_objective = 'DW200'
        storage_bytes = str(10 * 1024 * 1024 * 1024 * 1024)
        update_storage = '20TB'
        update_storage_bytes = str(20 * 1024 * 1024 * 1024 * 1024)

        rg = resource_group
        loc_display = 'West US'

        # test sql db commands
        self.cmd('sql dw create -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('location', loc_display),
                     JMESPathCheck('edition', 'DataWarehouse'),
                     JMESPathCheck('maxSizeBytes', storage_bytes),
                     JMESPathCheck('status', 'Online')])

        # DataWarehouse is a little quirky and is considered to be both a database and its
        # separate own type of thing. (Why? Because it has the same REST endpoint as regular
        # database, so it must be a database. However it has only a subset of supported operations,
        # so to clarify which operations are supported by dw we group them under `sql dw`.) So the
        # dw shows up under both `db list` and `dw list`.
        self.cmd('sql db list -g {} --server {}'
                 .format(rg, server),
                 checks=[
                     JMESPathCheck('length(@)', 2),  # includes dw and master
                     JMESPathCheck('sort([].name)', sorted([database_name, 'master'])),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[1].resourceGroup', rg)])

        self.cmd('sql dw list -g {} --server {}'
                 .format(rg, server),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].resourceGroup', rg)])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', rg)])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', rg)])

        # pause/resume
        self.cmd('sql dw pause -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('status', 'Paused')])

        self.cmd('sql dw resume -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('status', 'Online')])

        # Update DW storage
        self.cmd('sql dw update -g {} -s {} -n {} --max-size {}'
                 ' --set tags.key1=value1'
                 .format(rg, server, database_name, update_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Update DW service objective
        self.cmd('sql dw update -g {} -s {} -n {} --service-objective {}'
                 .format(rg, server, database_name,
                         update_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('requestedServiceObjectiveName', update_service_objective),
                     JMESPathCheck('maxSizeBytes', update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Delete DW
        self.cmd('sql dw delete -g {} --server {} --name {} --yes'
                 .format(rg, server, database_name),
                 checks=[NoneCheck()])


class SqlServerDbReplicaMgmtScenarioTest(ScenarioTest):

    # create 2 servers in the same resource group, and 1 server in a different resource group
    @ResourceGroupPreparer(parameter_name="resource_group_1",
                           parameter_name_for_location="resource_group_location_1")
    @ResourceGroupPreparer(parameter_name="resource_group_2",
                           parameter_name_for_location="resource_group_location_2")
    @SqlServerPreparer(parameter_name="server_name_1",
                       resource_group_parameter_name="resource_group_1")
    @SqlServerPreparer(parameter_name="server_name_2",
                       resource_group_parameter_name="resource_group_1")
    @SqlServerPreparer(parameter_name="server_name_3",
                       resource_group_parameter_name="resource_group_2")
    def test_sql_db_replica_mgmt(self,
                                 resource_group_1, resource_group_location_1,
                                 resource_group_2, resource_group_location_2,
                                 server_name_1, server_name_2, server_name_3):

        database_name = "cliautomationdb01"
        service_objective = 'S1'

        # helper class so that it's clear which servers are in which groups
        class ServerInfo(object):  # pylint: disable=too-few-public-methods
            def __init__(self, name, group, location):
                self.name = name
                self.group = group
                self.location = location

        s1 = ServerInfo(server_name_1, resource_group_1, resource_group_location_1)
        s2 = ServerInfo(server_name_2, resource_group_1, resource_group_location_1)
        s3 = ServerInfo(server_name_3, resource_group_2, resource_group_location_2)

        # verify setup
        for s in (s1, s2, s3):
            self.cmd('sql server show -g {} -n {}'
                     .format(s.group, s.name),
                     checks=[
                         JMESPathCheck('name', s.name),
                         JMESPathCheck('resourceGroup', s.group)])

        # create db in first server
        self.cmd('sql db create -g {} -s {} -n {}'
                 .format(s1.group, s1.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s1.group)])

        # create replica in second server with min params
        # partner resouce group unspecified because s1.group == s2.group
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {}'
                 .format(s1.group, s1.name, database_name,
                         s2.name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s2.group)])

        # check that the replica was created in the correct server
        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(s2.group, s2.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s2.group)])

        # create replica in third server with max params
        # --elastic-pool is untested
        self.cmd('sql db replica create -g {} -s {} -n {} --partner-server {}'
                 ' --partner-resource-group {} --service-objective {}'
                 .format(s1.group, s1.name, database_name,
                         s3.name, s3.group, service_objective),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s3.group),
                     JMESPathCheck('requestedServiceObjectiveName', service_objective)])

        # check that the replica was created in the correct server
        self.cmd('sql db show -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', s3.group)])

        # list replica links on s1 - it should link to s2 and s3
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s1.group, s1.name, database_name),
                 checks=[JMESPathCheck('length(@)', 2)])

        # list replica links on s3 - it should link only to s1
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].role', 'Secondary'),
                     JMESPathCheck('[0].partnerRole', 'Primary')])

        # Failover to s3.
        self.cmd('sql db replica set-primary -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[NoneCheck()])

        # list replica links on s3 - it should link to s1 and s2
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Stop replication from s3 to s2 twice. Second time should be no-op.
        for _ in range(2):
            # Delete link
            self.cmd('sql db replica delete-link -g {} -s {} -n {} --partner-resource-group {}'
                     ' --partner-server {} --yes'
                     .format(s3.group, s3.name, database_name, s2.group, s2.name),
                     checks=[NoneCheck()])

            # Verify link was deleted. s3 should still be the primary.
            self.cmd('sql db replica list-links -g {} -s {} -n {}'
                     .format(s3.group, s3.name, database_name),
                     checks=[
                         JMESPathCheck('length(@)', 1),
                         JMESPathCheck('[0].role', 'Primary'),
                         JMESPathCheck('[0].partnerRole', 'Secondary')])

        # Failover to s3 again (should be no-op, it's already primary)
        self.cmd('sql db replica set-primary -g {} -s {} -n {} --allow-data-loss'
                 .format(s3.group, s3.name, database_name),
                 checks=[NoneCheck()])

        # s3 should still be the primary.
        self.cmd('sql db replica list-links -g {} -s {} -n {}'
                 .format(s3.group, s3.name, database_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].role', 'Primary'),
                     JMESPathCheck('[0].partnerRole', 'Secondary')])

        # Force failover back to s1
        self.cmd('sql db replica set-primary -g {} -s {} -n {} --allow-data-loss'
                 .format(s1.group, s1.name, database_name),
                 checks=[NoneCheck()])


class SqlElasticPoolsMgmtScenarioTest(ScenarioTest):
    def __init__(self, method_name):
        super(SqlElasticPoolsMgmtScenarioTest, self).__init__(method_name)
        self.pool_name = "cliautomationpool01"

    def verify_activities(self, activities, resource_group, server):
        if isinstance(activities, list.__class__):
            raise AssertionError("Actual value '{}' expected to be list class."
                                 .format(activities))

        for activity in activities:
            if isinstance(activity, dict.__class__):
                raise AssertionError("Actual value '{}' expected to be dict class"
                                     .format(activities))
            if activity['resourceGroup'] != resource_group:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['resourceGroup'], resource_group))
            elif activity['serverName'] != server:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['serverName'], server))
            elif activity['currentElasticPoolName'] != self.pool_name:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['currentElasticPoolName'], self.pool_name))
        return True

    @ResourceGroupPreparer()
    @SqlServerPreparer()
    def test_sql_elastic_pools_mgmt(self, resource_group, resource_group_location, server):
        database_name = "cliautomationdb02"
        pool_name2 = "cliautomationpool02"
        edition = 'Standard'

        dtu = 1200
        db_dtu_min = 10
        db_dtu_max = 50
        storage = '1200GB'
        storage_mb = 1228800

        updated_dtu = 50
        updated_db_dtu_min = 10
        updated_db_dtu_max = 50
        updated_storage = '50GB'
        updated_storage_mb = 51200

        db_service_objective = 'S1'

        rg = resource_group
        loc_display = 'West US'

        # test sql elastic-pool commands
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 '--dtu {} --edition {} --db-dtu-min {} --db-dtu-max {} '
                 '--storage {}'
                 .format(rg, server, self.pool_name, dtu,
                         edition, db_dtu_min, db_dtu_max, storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('location', loc_display),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', dtu),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('storageMb', storage_mb)])

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(rg, server, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('storageMb', storage_mb)])

        self.cmd('sql elastic-pool list -g {} --server {}'
                 .format(rg, server),
                 checks=[
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.pool_name),
                     JMESPathCheck('[0].state', 'Ready'),
                     JMESPathCheck('[0].databaseDtuMin', db_dtu_min),
                     JMESPathCheck('[0].databaseDtuMax', db_dtu_max),
                     JMESPathCheck('[0].edition', edition),
                     JMESPathCheck('[0].storageMb', storage_mb)])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --storage {} --set tags.key1=value1'
                 .format(rg, server, self.pool_name,
                         updated_dtu, updated_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', updated_dtu),
                     JMESPathCheck('edition', edition),
                     JMESPathCheck('databaseDtuMin', db_dtu_min),
                     JMESPathCheck('databaseDtuMax', db_dtu_max),
                     JMESPathCheck('storageMb', updated_storage_mb),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --db-dtu-min {} --db-dtu-max {} --storage {}'
                 .format(rg, server, self.pool_name, dtu,
                         updated_db_dtu_min, updated_db_dtu_max,
                         storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', dtu),
                     JMESPathCheck('databaseDtuMin', updated_db_dtu_min),
                     JMESPathCheck('databaseDtuMax', updated_db_dtu_max),
                     JMESPathCheck('storageMb', storage_mb),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--remove tags.key1'
                 .format(rg, server, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('tags', {})])

        # create a second pool with minimal params
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 .format(rg, server, pool_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', pool_name2),
                     JMESPathCheck('location', loc_display),
                     JMESPathCheck('state', 'Ready')])

        self.cmd('sql elastic-pool list -g {} -s {}'.format(rg, server),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Create a database directly in an Azure sql elastic pool
        self.cmd('sql db create -g {} --server {} --name {} '
                 '--elastic-pool {}'
                 .format(rg, server, database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # Move database to second pool. Specify service objective just for fun
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(rg, server, database_name, pool_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolName', pool_name2),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # Remove database from pool
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {}'
                 .format(rg, server, database_name, db_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('requestedServiceObjectiveName', db_service_objective),
                     JMESPathCheck('status', 'Online')])

        # Move database back into pool
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(rg, server, database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # List databases in a pool
        self.cmd('sql elastic-pool list-dbs -g {} -s {} -n {}'
                 .format(rg, server, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # List databases in a pool - alternative command
        self.cmd('sql db list -g {} -s {} --elastic-pool {}'
                 .format(rg, server, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # self.cmd('sql elastic-pool db show-activity -g {} --server {} --elastic-pool {}'
        #          .format(rg, server, pool_name),
        #          checks=[
        #              JMESPathCheck('length(@)', 1),
        #              JMESPathCheck('[0].resourceGroup', rg),
        #              JMESPathCheck('[0].serverName', server),
        #              JMESPathCheck('[0].currentElasticPoolName', pool_name)])

        # activities = self.cmd('sql elastic-pools db show-activity -g {} '
        #                       '--server-name {} --elastic-pool-name {}'
        #                       .format(rg, server, pool_name),
        #                       checks=[JMESPathCheck('type(@)', 'array')])
        # self.verify_activities(activities, resource_group)

        # delete sql server database
        self.cmd('sql db delete -g {} --server {} --name {} --yes'
                 .format(rg, server, database_name),
                 checks=[NoneCheck()])

        # delete sql elastic pool
        self.cmd('sql elastic-pool delete -g {} --server {} --name {}'
                 .format(rg, server, self.pool_name),
                 checks=[NoneCheck()])


class SqlServerCapabilityScenarioTest(ScenarioTest):
    def test_sql_capabilities(self):
        location = 'westus'

        # New capabilities are added quite frequently and the state of each capability depends
        # on your subscription. So it's not a good idea to make strict checks against exactly
        # which capabilities are returned. The idea is to just check the overall structure.

        db_max_size_length_jmespath = 'length([].supportedServiceLevelObjectives[].supportedMaxSizes[])'

        # Get all db capabilities
        self.cmd('sql db list-editions -l {}'.format(location),
                 checks=[
                     # At least standard and premium edition exist
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheckExists("[?name == 'Premium']"),
                     # At least s0 and p1 service objectives exist
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'S0']"),
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'P1']"),
                     # Max size data is omitted
                     JMESPathCheck(db_max_size_length_jmespath, 0)])

        # Get all db capabilities with size data
        self.cmd('sql db list-editions -l {} --show-details max-size'.format(location),
                 checks=[
                     # Max size data is included
                     JMESPathCheckGreaterThan(db_max_size_length_jmespath, 0)])

        # Search for db edition - note that it's case insensitive
        self.cmd('sql db list-editions -l {} --edition standard'.format(location),
                 checks=[
                     # Standard edition exists, other editions don't
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheck("length([?name != 'Standard'])", 0),
                 ])

        # Search for db service objective - note that it's case insensitive
        self.cmd('sql db list-editions -l {} --edition standard --service-objective s0'
                 .format(location), checks=[
                     # Standard edition exists, other editions don't
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheck("length([?name != 'Standard'])", 0),
                     # S0 service objective exists, others don't exist
                     JMESPathCheckExists("[].supportedServiceLevelObjectives[] | [?name == 'S0']"),
                     JMESPathCheck(
                         "length([].supportedServiceLevelObjectives[] | [?name != 'S0'])",
                         0),
                 ])

        pool_max_size_length_jmespath = 'length([].supportedElasticPoolDtus[].supportedMaxSizes[])'
        pool_db_max_dtu_length_jmespath = 'length([].supportedElasticPoolDtus[].supportedPerDatabaseMaxDtus[])'
        pool_db_min_dtu_length_jmespath = ('length([].supportedElasticPoolDtus[].supportedPerDatabaseMaxDtus[]'
                                           '.supportedPerDatabaseMinDtus[])')
        pool_db_max_size_length_jmespath = 'length([].supportedElasticPoolDtus[].supportedPerDatabaseMaxSizes[])'

        # Get all elastic pool capabilities
        self.cmd('sql elastic-pool list-editions -l {}'.format(location),
                 checks=[
                     # At least standard and premium edition exist
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheckExists("[?name == 'Premium']"),
                     # Optional details are omitted
                     JMESPathCheck(pool_max_size_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_size_length_jmespath, 0)
                 ])

        # Search for elastic pool edition - note that it's case insensitive
        self.cmd('sql elastic-pool list-editions -l {} --edition standard'.format(location),
                 checks=[
                     # Standard edition exists, other editions don't
                     JMESPathCheckExists("[?name == 'Standard']"),
                     JMESPathCheck("length([?name != 'Standard'])", 0)
                 ])

        # Search for dtu limit
        self.cmd('sql elastic-pool list-editions -l {} --dtu 100'.format(location),
                 checks=[
                     # All results have 100 dtu
                     JMESPathCheckGreaterThan('length([].supportedElasticPoolDtus[?limit == `100`][])', 0),
                     JMESPathCheck('length([].supportedElasticPoolDtus[?limit != `100`][])', 0)
                 ])

        # Get all db capabilities with pool max size
        self.cmd('sql elastic-pool list-editions -l {} --show-details max-size'.format(location),
                 checks=[
                     JMESPathCheckGreaterThan(pool_max_size_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_size_length_jmespath, 0)
                 ])

        # Get all db capabilities with per db max size
        self.cmd('sql elastic-pool list-editions -l {} --show-details db-max-size'.format(location),
                 checks=[
                     JMESPathCheck(pool_max_size_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_max_size_length_jmespath, 0)
                 ])

        # Get all db capabilities with per db max dtu
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-max-dtu'.format(location),
                 checks=[
                     JMESPathCheck(pool_max_size_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_size_length_jmespath, 0)
                 ])

        # Get all db capabilities with per db min dtu (which is nested under per db max dtu)
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-min-dtu'.format(location),
                 checks=[
                     JMESPathCheck(pool_max_size_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheck(pool_db_max_size_length_jmespath, 0)
                 ])

        # Get all db capabilities with everything
        self.cmd('sql elastic-pool list-editions -l {} --edition standard --show-details db-min-dtu db-max-dtu db-max-size max-size'.format(location),
                 checks=[
                     JMESPathCheckGreaterThan(pool_max_size_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_max_dtu_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_min_dtu_length_jmespath, 0),
                     JMESPathCheckGreaterThan(pool_db_max_size_length_jmespath, 0)
                 ])


class SqlServerImportExportMgmtScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    @SqlServerPreparer()
    @StorageAccountPreparer()
    def test_sql_db_import_export_mgmt(self, resource_group, resource_group_location, server, storage_account):
        location_long_name = 'West US'
        admin_login = 'admin123'
        admin_password = 'SecretPassword123'
        db_name = 'cliautomationdb01'
        db_name2 = 'cliautomationdb02'
        db_name3 = 'cliautomationdb03'
        blob = 'testbacpac.bacpac'
        blob2 = 'testbacpac2.bacpac'

        container = 'bacpacs'

        firewall_rule_1 = 'allowAllIps'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '0.0.0.0'

        # create server firewall rule
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, resource_group, server,
                         start_ip_address_1, end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # create dbs
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', db_name),
                     JMESPathCheck('location', location_long_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', db_name2),
                     JMESPathCheck('location', location_long_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(resource_group, server, db_name3),
                 checks=[
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('name', db_name3),
                     JMESPathCheck('location', location_long_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        # get storage account endpoint
        storage_endpoint = self.cmd('storage account show -g {} -n {}'
                                    ' --query primaryEndpoints.blob'
                                    .format(resource_group, storage_account)).get_output_in_json()
        bacpacUri = '{}{}/{}'.format(storage_endpoint, container, blob)
        bacpacUri2 = '{}{}/{}'.format(storage_endpoint, container, blob2)

        # get storage account key
        storageKey = self.cmd('storage account keys list -g {} -n {} --query [0].value'
                              .format(resource_group, storage_account)).get_output_in_json()

        # Set Expiry
        expiryString = '9999-12-25T00:00:00Z'

        # Get sas key
        sasKey = self.cmd('storage blob generate-sas --account-name {} -c {} -n {} --permissions rw --expiry {}'.format(
            storage_account, container, blob2, expiryString)).get_output_in_json()

        # create storage account blob container
        self.cmd('storage container create -n {} --account-name {} --account-key {} '
                 .format(container, storage_account, storageKey),
                 checks=[
                     JMESPathCheck('created', True)])

        # export database to blob container using both keys
        self.cmd('sql db export -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type StorageAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name, resource_group, admin_password, admin_login, storageKey,
                         bacpacUri),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri),
                     JMESPathCheck('databaseName', db_name),
                     JMESPathCheck('requestType', 'Export'),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        self.cmd('sql db export -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type SharedAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name, resource_group, admin_password, admin_login, sasKey,
                         bacpacUri2),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri2),
                     JMESPathCheck('databaseName', db_name),
                     JMESPathCheck('requestType', 'Export'),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        # import bacpac to second database using Storage Key
        self.cmd('sql db import -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type StorageAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name2, resource_group, admin_password, admin_login, storageKey,
                         bacpacUri),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri),
                     JMESPathCheck('databaseName', db_name2),
                     JMESPathCheck('name', 'import'),
                     JMESPathCheck('requestType', 'Import'),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])

        # import bacpac to third database using SAS key
        self.cmd('sql db import -s {} -n {} -g {} -p {} -u {}'
                 ' --storage-key {} --storage-key-type SharedAccessKey'
                 ' --storage-uri {}'
                 .format(server, db_name3, resource_group, admin_password, admin_login, sasKey,
                         bacpacUri2),
                 checks=[
                     JMESPathCheck('blobUri', bacpacUri2),
                     JMESPathCheck('databaseName', db_name3),
                     JMESPathCheck('name', 'import'),
                     JMESPathCheck('requestType', 'Import'),
                     JMESPathCheck('resourceGroup', resource_group),
                     JMESPathCheck('serverName', server),
                     JMESPathCheck('status', 'Completed')])
