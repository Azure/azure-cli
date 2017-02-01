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
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'

    def test_sql_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_names[0], loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 1)])

        # test create another sql server
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_names[1], loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_names[1]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test list sql server should be 2
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 2)])

        # test show sql server
        self.cmd('sql server show -g {} --name {}'
                 .format(rg, self.sql_server_names[0]), checks=[
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
        self.sql_server_name = 'cliautomation03'
        self.location = "westus"
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'

    def test_sql_firewall_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password
        firewall_rule_1 = 'rule1'
        start_ip_address_1 = '0.0.0.0'
        end_ip_address_1 = '255.255.255.255'
        firewall_rule_2 = 'rule2'
        start_ip_address_2 = '123.123.123.123'
        end_ip_address_2 = '123.123.123.124'

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_name, loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test sql server firewall create
        self.cmd('sql server firewall create --name {} -g {} --server-name {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         start_ip_address_1, end_ip_address_1), checks=[
                             JMESPathCheck('name', firewall_rule_1),
                             JMESPathCheck('resourceGroup', rg),
                             JMESPathCheck('startIpAddress', start_ip_address_1),
                             JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall show
        self.cmd('sql server firewall show --name {} -g {} --server-name {}'
                 .format(firewall_rule_1, rg, self.sql_server_name), checks=[
                     JMESPathCheck('name', firewall_rule_1),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('startIpAddress', start_ip_address_1),
                     JMESPathCheck('endIpAddress', end_ip_address_1)])

        # test sql server firewall update
        self.cmd('sql server firewall update --name {} -g {} --server-name {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_1, rg, self.sql_server_name,
                         start_ip_address_2, end_ip_address_2), checks=[
                             JMESPathCheck('name', firewall_rule_1),
                             JMESPathCheck('resourceGroup', rg),
                             JMESPathCheck('startIpAddress', start_ip_address_2),
                             JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall create another rule
        self.cmd('sql server firewall create --name {} -g {} --server-name {} '
                 '--start-ip-address {} --end-ip-address {}'
                 .format(firewall_rule_2, rg, self.sql_server_name,
                         start_ip_address_2, end_ip_address_2), checks=[
                             JMESPathCheck('name', firewall_rule_2),
                             JMESPathCheck('resourceGroup', rg),
                             JMESPathCheck('startIpAddress', start_ip_address_2),
                             JMESPathCheck('endIpAddress', end_ip_address_2)])

        # test sql server firewall list
        self.cmd('sql server firewall list -g {} --server-name {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 2)])

        # test sql server firewall delete
        self.cmd('sql server firewall delete --name {} -g {} --server-name {}'
                 .format(firewall_rule_1, rg, self.sql_server_name), checks=NoneCheck())
        self.cmd('sql server firewall list -g {} --server-name {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 1)])
        self.cmd('sql server firewall delete --name {} -g {} --server-name {}'
                 .format(firewall_rule_2, rg, self.sql_server_name), checks=NoneCheck())
        self.cmd('sql server firewall list -g {} --server-name {}'
                 .format(rg, self.sql_server_name), checks=[JMESPathCheck('length(@)', 0)])

        # test delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlServerServiceObjectiveMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlServerServiceObjectiveMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation04'
        self.location = "westus"
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'

    def test_sql_service_objective_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_name, loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test sql server service-objective list
        service_objectives = self.cmd('sql server service-objective list -g {} --server-name {}'
                                      .format(rg, self.sql_server_name), checks=[
                                          JMESPathCheck('length(@)', 42)])

        # test sql server service-objective show
        self.cmd('sql server service-objective show -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, service_objectives[0]['name']), checks=[
                     JMESPathCheck('name', service_objectives[0]['name']),
                     JMESPathCheck('resourceGroup', rg)])

        # test delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlServerDbMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlServerDbMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation05'
        self.location = "westus"
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'
        self.database_name = "cliautomationdb01"

    def test_sql_db_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password

        # create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_name, loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test sql db commands
        self.cmd('sql db create -g {} --server-name {} -l {} --name {}'
                 .format(rg, self.sql_server_name, loc, self.database_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', None),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql db list -g {} --server-name {}'
                 .format(rg, self.sql_server_name), checks=[
                     JMESPathCheck('length(@)', 2),
                     JMESPathCheck('[1].name', 'master'),
                     JMESPathCheck('[1].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].resourceGroup', rg)])

        self.cmd('sql db show -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name), checks=[
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('resourceGroup', rg)])

        self.cmd('sql db show-usage -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name), checks=[
                     JMESPathCheck('[0].resourceName', self.database_name)])

        self.cmd('sql db update -g {} --server-name {} --name {} '
                 '--set tags.key1=value1'
                 .format(rg, self.sql_server_name, self.database_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql db delete -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name), checks=[NoneCheck()])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())


class SqlElasticPoolsMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlElasticPoolsMgmtScenarioTest, self).__init__(
            __file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cliautomation06'
        self.location = "westus"
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'
        self.database_name = "cliautomationdb02"
        self.pool_name = "cliautomationpool01"

    def test_sql_elastic_pools_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password

        # create sql server with minimal required parameters
        self.cmd('sql server create -g {} --name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_name, loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_name),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test sql elastic-pools commands
        self.cmd('sql elastic-pools create -g {} --server-name {} -l {} --name {}'
                 .format(rg, self.sql_server_name, loc, self.pool_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready')])

        self.cmd('sql elastic-pools show -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.pool_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready')])

        self.cmd('sql elastic-pools list -g {} --server-name {}'
                 .format(rg, self.sql_server_name), checks=[
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.pool_name),
                     JMESPathCheck('[0].state', 'Ready')])

        self.cmd('sql elastic-pools update -g {} --server-name {} --name {} '
                 '--set tags.key1=value1'
                 .format(rg, self.sql_server_name, self.pool_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('tags.key1', 'value1')])

        self.cmd('sql elastic-pools update -g {} --server-name {} --name {} '
                 '--remove tags.key1'
                 .format(rg, self.sql_server_name, self.pool_name), checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.pool_name),
                     JMESPathCheck('state', 'Ready'),
                     JMESPathCheck('tags', {})])

        # Create a database in an Azure sql elastic pool
        self.cmd('sql db create -g {} --server-name {} -l {} --name {} '
                 '--elastic-pool-name {}'
                 .format(rg, self.sql_server_name, loc, self.database_name, self.pool_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('status', 'Online')])

        # test sql elastic-pools db sub-group commands
        self.cmd('sql elastic-pools db list -g {} --server-name {} --elastic-pool-name {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].name', self.database_name),
                     JMESPathCheck('[0].elasticPoolName', self.pool_name),
                     JMESPathCheck('[0].status', 'Online')])

        self.cmd('sql elastic-pools db show -g {} --server-name {} --elastic-pool-name {} '
                 '--name {}'
                 .format(rg, self.sql_server_name, self.pool_name, self.database_name),
                 checks=[
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('name', self.database_name),
                     JMESPathCheck('elasticPoolName', self.pool_name),
                     JMESPathCheck('status', 'Online')])

        self.cmd('sql elastic-pools db show-activity -g {} --server-name {} --elastic-pool-name {}'
                 .format(rg, self.sql_server_name, self.pool_name),
                 checks=[
                     JMESPathCheck('length(@)', 1),
                     JMESPathCheck('[0].resourceGroup', rg),
                     JMESPathCheck('[0].serverName', self.sql_server_name),
                     JMESPathCheck('[0].currentElasticPoolName', self.pool_name)])

        # delete sql server database
        self.cmd('sql db delete -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.database_name), checks=[NoneCheck()])

        # delete sql elastic pool
        self.cmd('sql elastic-pools delete -g {} --server-name {} --name {}'
                 .format(rg, self.sql_server_name, self.pool_name), checks=[NoneCheck()])

        # delete sql server
        self.cmd('sql server delete -g {} --name {}'
                 .format(rg, self.sql_server_name), checks=NoneCheck())
