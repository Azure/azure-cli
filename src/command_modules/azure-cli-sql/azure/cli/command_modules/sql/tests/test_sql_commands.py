# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.test_utils.vcr_test_base import (
    ResourceGroupVCRTestBase, JMESPathCheck, NoneCheck)


class SqlServerMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlServerMgmtScenarioTest, self).__init__(__file__, test_method,
                                                        resource_group='cli-test-sql-mgmt')
        self.sql_server_names = ['cliautomation01', 'cliautomation02']
        self.location = "westus"
        self.admin_login = 'admin123'
        self.admin_passwords = ['SecretPassword123', 'SecretPassword456']

    def test_sql_server_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.admin_login
        password = self.admin_passwords[0]
        password_updated = self.admin_passwords[1]

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_names[0], loc, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', password)])

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 1)])

        # test update sql server
        self.cmd('sql server update -g {} --name {} --admin-password {}'
                 .format(rg, self.sql_server_names[0], password_updated),
                 checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', password_updated)])

        # test create another sql server
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_names[1], loc, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_names[1]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user),
                     JMESPathCheck('administratorLoginPassword', password)])

        # test list sql server should be 2
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 2)])

        # test show sql server
        self.cmd('sql server show -g {} --name {}'
                 .format(rg, self.sql_server_names[0]),
                 checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_names[0]), checks=NoneCheck())
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_names[1]), checks=NoneCheck())

        # test list sql server should be 0
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 0)])


class SqlServerFirewallMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlServerFirewallMgmtScenarioTest, self).__init__(__file__, test_method,
                                                                resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation10'
        self.location = "westus"
        self.admin_login = 'admin123'
        self.admin_password = 'SecretPassword123'

    def test_sql_firewall_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.admin_login
        password = self.admin_password
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'
        # allow_all_azure_ips_rule = 'AllowAllAzureIPs'
        # allow_all_azure_ips_address = '0.0.0.0'

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_name, loc, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test sql server firewall-rule create
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         start_ip_address_1, end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule show
        self.cmd('sql server firewall-rule show --name {} -g {} --server {}'
                 .format(firewall_rule_1, rg, self.sql_server_name),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule update
        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--start-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         start_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        self.cmd('sql server firewall-rule update --name {} -g {} --server {} '
                 '--end-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         end_ip_address_1),
                 checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall-rule create another rule
        self.cmd('sql server firewall-rule create --name {} -g {} --server {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_2, rg, self.sql_server_name,
                         start_ip_address_2, end_ip_address_2),
                 checks=[
                     JMESPathCheck('name', firewall_rule_2),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_2),
                     JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall-rule list
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 2)])

        # # test sql server firewall-rule create azure ip rule
        # self.cmd('sql server firewall-rule allow-all-azure-ips -g {} --server {} '
        #          .format(rg, self.sql_server_name), checks=[
        #                      JMESPathCheck('name', allow_all_azure_ips_rule),
        #                      JMESPathCheck('resourceGroup', rg),
        #                      JMESPathCheck('startIpAddress', allow_all_azure_ips_address),
        #                      JMESPathCheck('endIpAddress', allow_all_azure_ips_address)])

        # # test sql server firewall-rule list
        # self.cmd('sql server firewall-rule list -g {} --server {}'
        #          .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 3)])

        # # test sql server firewall-rule delete
        # self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
        #          .format(allow_all_azure_ips_rule, rg, self.sql_server_name), checks=NoneCheck())
        # self.cmd('sql server firewall-rule list -g {} --server {}'
        #          .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 2)])
        self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
                 .format(firewall_rule_1, rg, self.sql_server_name), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('sql server firewall-rule delete --name {} -g {} --server {}'
                 .format(firewall_rule_2, rg, self.sql_server_name), checks=NoneCheck())
        self.cmd('sql server firewall-rule list -g {} --server {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 0)])

        # test delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlServerDbMgmtScenarioTest(ResourceGroupVCRTestBase):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, test_method):
        super(SqlServerDbMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation14'
        self.location_short_name = 'westus'
        self.location_long_name = 'West US'
        self.admin_login = 'admin123'
        self.admin_password = 'SecretPassword123'
        self.database_name = "cliautomationdb01"
        self.database_copy_name = "cliautomationdb02"
        self.update_service_objective = 'S1'
        self.update_storage = '10GB'
        self.update_storage_bytes = str(10 * 1024 * 1024 * 1024)

    def test_sql_db_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc_short = self.location_short_name
        loc_long = self.location_long_name
        user = self.admin_login
        password = self.admin_password

        # create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l "{}" '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_name, loc_short, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('administratorLogin', user)])

        # test sql db commands
        self.cmd('sql db create -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db list -g {} --server {}'
                 .format(rg, self.sql_server_name),
                 checks=[
                     JMESPathCheck('length(@)', 2),
                     JMESPathCheck('[1].name', 'master'),
                     JMESPathCheck('[1].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].resourceGroup', rg)])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg)])

        # # Usages will not be included in the first batch of GA commands
        # self.cmd('sql db show-usage -g {} --server {} --name {}'
        #          .format(rg, self.sql_server_name, self.database_name), checks=[
        #              JMESPathCheck('[0].resourceName', self.database_name)])

        self.cmd('sql db update -g {} -s {} -n {} --service-objective {} --max-size {}'
                 ' --set tags.key1=value1'
                 .format(rg, self.sql_server_name, self.database_name,
                         self.update_service_objective, self.update_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('requestedServiceObjectiveName', self.update_service_objective),
                     JMESPathCheck('maxSizeBytes', self.update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql db copy -g {} --server {} --name {} '
                 '--dest-name {}'
                 .format(rg, self.sql_server_name, self.database_name, self.database_copy_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_copy_name)
                 ])

        self.cmd('sql db delete -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[NoneCheck()])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlServerDbRestoreScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(SqlServerDbRestoreScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')

    def test_sql_db_restore(self):
        self.execute()

    def body(self):
        from datetime import datetime
        from time import sleep

        rg = self.resource_group
        server_name = 'cliautomation44'
        location = 'westus'
        admin_login = 'admin123'
        admin_password = 'SecretPassword123'
        database_name = 'cliautomationdb01'

        # Standalone db
        restore_service_objective = 'S1'
        restore_edition = 'Standard'
        restore_standalone_database_name = 'cliautomationdb01restore1'

        restore_pool_database_name = 'cliautomationdb01restore2'
        elastic_pool = 'cliautomationpool1'

        # create server
        self.cmd('sql server create -g {} --name {} -l "{}" '
                 '--admin-user {} --admin-password {}'
                 .format(rg, server_name, location, admin_login, admin_password),
                 checks=[
                     JMESPathCheck('name', server_name),
                     JMESPathCheck('resourceGroup', rg)])

        # create db
        db = self.cmd('sql db create -g {} --server {} --name {}'
                      .format(rg, server_name, database_name),
                      checks=[
                          JMESPathCheck('resourceGroup', rg),
                          JMESPathCheck('name', database_name),
                          JMESPathCheck('status', 'Online')])

        # create elastic pool
        self.cmd('sql elastic-pool create -g {} -s {} -n {}'
                 .format(rg, server_name, elastic_pool))

        # Wait until earliestRestoreDate is in the past. When run live, this will take at least
        # 10 minutes. Unforunately there's no way to speed this up.
        earliest_restore_date = datetime.strptime(db['earliestRestoreDate'],
                                                  "%Y-%m-%dT%H:%M:%S.%f+00:00")
        while datetime.utcnow() <= earliest_restore_date:
            sleep(10)  # seconds

        # Restore to standalone db
        db = self.cmd('sql db restore -g {} -s {} -n {} -t {} --dest-name {}'
                      ' --service-objective {} --edition {}'
                      .format(rg, server_name, database_name, datetime.utcnow().isoformat(),
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
                      .format(rg, server_name, database_name, datetime.utcnow().isoformat(),
                              restore_pool_database_name, elastic_pool),
                      checks=[
                          JMESPathCheck('resourceGroup', rg),
                          JMESPathCheck('name', restore_pool_database_name),
                          JMESPathCheck('elasticPoolName', elastic_pool),
                          JMESPathCheck('status', 'Online')])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, server_name), checks=NoneCheck())


class SqlServerDwMgmtScenarioTest(ResourceGroupVCRTestBase):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, test_method):
        super(SqlServerDwMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation24'
        self.location_short_name = 'westus'
        self.location_long_name = 'West US'
        self.admin_login = 'admin123'
        self.admin_password = 'SecretPassword123'
        self.database_name = "cliautomationdb01"
        self.database_copy_name = "cliautomationdb02"
        self.update_service_objective = 'DW200'
        self.storage_bytes = str(10 * 1024 * 1024 * 1024 * 1024)
        self.update_storage = '20TB'
        self.update_storage_bytes = str(20 * 1024 * 1024 * 1024 * 1024)

    def test_sql_dw_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc_short = self.location_short_name
        loc_long = self.location_long_name
        user = self.admin_login
        password = self.admin_password

        # create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l "{}" '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_name, loc_short, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('administratorLogin', user)])

        # test sql db commands
        self.cmd('sql dw create -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('edition', 'DataWarehouse'),
                     JMESPathCheck('maxSizeBytes', self.storage_bytes),
                     JMESPathCheck('status', 'Online')])

        # DataWarehouse is a little quirky and is considered to be both a database and its
        # separate own type of thing. (Why? Because it has the same REST endpoint as regular
        # database, so it must be a database. However it has only a subset of supported operations,
        # so to clarify which operations are supported by dw we group them under `sql dw`.) So the
        # dw shows up under both `db list` and `dw list`.
        self.cmd('sql db list -g {} --server {}'
                 .format(rg, self.sql_server_name),
                 checks=[
                     JMESPathCheck('length(@)', 2),  # includes dw and master
                     JMESPathCheck('[1].name', 'master'),
                     JMESPathCheck('[1].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].resourceGroup', rg)])

        self.cmd('sql dw list -g {} --server {}'
                 .format(rg, self.sql_server_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].resourceGroup', rg)])

        self.cmd('sql db show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg)])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg)])

        # pause/resume
        self.cmd('sql dw pause -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('status', 'Paused')])

        self.cmd('sql dw resume -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[NoneCheck()])

        self.cmd('sql dw show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('status', 'Online')])

        # Update DW storage
        self.cmd('sql dw update -g {} -s {} -n {} --max-size {}'
                 ' --set tags.key1=value1'
                 .format(rg, self.sql_server_name, self.database_name, self.update_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('maxSizeBytes', self.update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Update DW service objective
        self.cmd('sql dw update -g {} -s {} -n {} --service-objective {}'
                 .format(rg, self.sql_server_name, self.database_name,
                         self.update_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('requestedServiceObjectiveName', self.update_service_objective),
                     JMESPathCheck('maxSizeBytes', self.update_storage_bytes),
                     JMESPathCheck('tags.key1', 'value1')])

        # Delete DW
        self.cmd('sql dw delete -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[NoneCheck()])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlElasticPoolsMgmtScenarioTest(ResourceGroupVCRTestBase):
    # pylint: disable=too-many-instance-attributes
    def __init__(self, test_method):
        super(SqlElasticPoolsMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation22'
        self.location_short_name = 'westus'
        self.location_long_name = 'West US'
        self.admin_login = 'admin123'
        self.admin_password = 'SecretPassword123'
        self.database_name = "cliautomationdb02"
        self.pool_name = "cliautomationpool01"
        self.pool_name2 = "cliautomationpool02"
        self.edition = 'Standard'

        self.dtu = 1200
        self.db_dtu_min = 10
        self.db_dtu_max = 50
        self.storage = '1200GB'
        self.storage_mb = 1228800

        self.updated_dtu = 50
        self.updated_db_dtu_min = 10
        self.updated_db_dtu_max = 50
        self.updated_storage = '50GB'
        self.updated_storage_mb = 51200

        self.db_service_objective = 'S1'

    def test_sql_elastic_pools_mgmt(self):
        self.execute()

    def verify_activities(self, activities):
        if isinstance(activities, list.__class__):
            raise AssertionError("Actual value '{}' expected to be list class."
                                 .format(activities))

        for activity in activities:
            if isinstance(activity, dict.__class__):
                raise AssertionError("Actual value '{}' expected to be dict class"
                                     .format(activities))
            if activity['resourceGroup'] != self.resource_group:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['resourceGroup'], self.resource_group))
            elif activity['serverName'] != self.sql_server_name:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['serverName'], self.sql_server_name))
            elif activity['currentElasticPoolName'] != self.pool_name:
                raise AssertionError("Actual value '{}' != Expected value {}"
                                     .format(activity['currentElasticPoolName'], self.pool_name))
        return True

    def body(self):
        rg = self.resource_group
        loc_short = self.location_short_name
        loc_long = self.location_long_name
        user = self.admin_login
        password = self.admin_password

        # create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--admin-user {} --admin-password {}'
                 .format(rg, self.sql_server_name, loc_short, user, password),
                 checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('administratorLogin', user)])

        # test sql elastic-pool commands
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 '--dtu {} --edition {} --db-dtu-min {} --db-dtu-max {} '
                 '--storage {}'
                 .format(rg, self.sql_server_name, self.pool_name, self.dtu,
                         self.edition, self.db_dtu_min, self.db_dtu_max, self.storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', self.dtu),
                     JMESPathCheck('databaseDtuMin', self.db_dtu_min),
                     JMESPathCheck('databaseDtuMax', self.db_dtu_max),
                     JMESPathCheck('edition', self.edition),
                     JMESPathCheck('storageMb', self.storage_mb)])

        self.cmd('sql elastic-pool show -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('databaseDtuMin', self.db_dtu_min),
                     JMESPathCheck('databaseDtuMax', self.db_dtu_max),
                     JMESPathCheck('edition', self.edition),
                     JMESPathCheck('storageMb', self.storage_mb)])

        self.cmd('sql elastic-pool list -g {} --server {}'
                 .format(rg, self.sql_server_name),
                 checks=[
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.pool_name),
                     JMESPathCheck('[0].state', 'Ready'),
                     JMESPathCheck('[0].databaseDtuMin', self.db_dtu_min),
                     JMESPathCheck('[0].databaseDtuMax', self.db_dtu_max),
                     JMESPathCheck('[0].edition', self.edition),
                     JMESPathCheck('[0].storageMb', self.storage_mb)])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --storage {} --set tags.key1=value1'
                 .format(rg, self.sql_server_name, self.pool_name,
                         self.updated_dtu, self.updated_storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', self.updated_dtu),
                     JMESPathCheck('edition', self.edition),
                     JMESPathCheck('databaseDtuMin', self.db_dtu_min),
                     JMESPathCheck('databaseDtuMax', self.db_dtu_max),
                     JMESPathCheck('storageMb', self.updated_storage_mb),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--dtu {} --db-dtu-min {} --db-dtu-max {} --storage {}'
                 .format(rg, self.sql_server_name, self.pool_name, self.dtu,
                         self.updated_db_dtu_min, self.updated_db_dtu_max,
                         self.storage),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('dtu', self.dtu),
                     JMESPathCheck('databaseDtuMin', self.updated_db_dtu_min),
                     JMESPathCheck('databaseDtuMax', self.updated_db_dtu_max),
                     JMESPathCheck('storageMb', self.storage_mb),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pool update -g {} --server {} --name {} '
                 '--remove tags.key1'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('tags', {})])

        # create a second pool with minimal params
        self.cmd('sql elastic-pool create -g {} --server {} --name {} '
                 .format(rg, self.sql_server_name, self.pool_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name2),
                     JMESPathCheck('location', loc_long),
                     JMESPathCheck('state', 'Ready')])

        self.cmd('sql elastic-pool list -g {} -s {}'.format(rg, self.sql_server_name),
                 checks=[JMESPathCheck('length(@)', 2)])

        # Create a database directly in an Azure sql elastic pool
        self.cmd('sql db create -g {} --server {} --name {} '
                 '--elastic-pool {}'
                 .format(rg, self.sql_server_name, self.database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # Move database to second pool. Specify service objective just for fun
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(rg, self.sql_server_name, self.database_name, self.pool_name2),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name2),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # Remove database from pool
        self.cmd('sql db update -g {} -s {} -n {} --service-objective {}'
                 .format(rg, self.sql_server_name, self.database_name, self.db_service_objective),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('requestedServiceObjectiveName', self.db_service_objective),
                     JMESPathCheck('status', 'Online')])

        # Move database back into pool
        self.cmd('sql db update -g {} -s {} -n {} --elastic-pool {}'
                 ' --service-objective ElasticPool'
                 .format(rg, self.sql_server_name, self.database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('requestedServiceObjectiveName', 'ElasticPool'),
                     JMESPathCheck('status', 'Online')])

        # List databases in a pool
        self.cmd('sql elastic-pool list-dbs -g {} -s {} -n {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # List databases in a pool - alternative command
        self.cmd('sql db list -g {} -s {} --elastic-pool {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name)])

        # self.cmd('sql elastic-pool db show-activity -g {} --server {} --elastic-pool {}'
        #          .format(rg, self.sql_server_name, self.pool_name),
        #          checks=[
        #              JMESPathCheck('length(@)', 1),
        #              JMESPathCheck('[0].resourceGroup', rg),
        #              JMESPathCheck('[0].serverName', self.sql_server_name),
        #              JMESPathCheck('[0].currentElasticPoolName', self.pool_name)])

        # activities = self.cmd('sql elastic-pools db show-activity -g {} '
        #                       '--server-name {} --elastic-pool-name {}'
        #                       .format(rg, self.sql_server_name, self.pool_name),
        #                       checks=[JMESPathCheck('type(@)', 'array')])
        # self.verify_activities(activities)

        # delete sql server database
        self.cmd('sql db delete -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name),
                 checks=[NoneCheck()])

        # delete sql elastic pool
        self.cmd('sql elastic-pool delete -g {} --server {} --name {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[NoneCheck()])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())
