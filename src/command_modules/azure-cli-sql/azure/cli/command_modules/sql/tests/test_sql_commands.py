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
        self.cmd('sql server create -g {} --server-name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_names[0], loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 1)])

        # test create another sql server
        self.cmd('sql server create -g {} --server-name {} -l {} '
                 '--administrator-login {} --administrator-login-password {}'
                 .format(rg, self.sql_server_names[1], loc, user, password), checks=[
                     JMESPathCheck('name', self.sql_server_names[1]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test list sql server should be 2
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 2)])

        # test show sql server
        self.cmd('sql server show -g {} --server-name {}'
                 .format(rg, self.sql_server_names[0]), checks=[
                     JMESPathCheck('name', self.sql_server_names[0]),
                     JMESPathCheck('resourceGroup', rg),
                     JMESPathCheck('administratorLogin', user)])

        # test delete sql server
        self.cmd('sql server delete -g {} --server-name {}'
                 .format(rg, self.sql_server_names[0]), checks=NoneCheck())
        self.cmd('sql server delete -g {} --server-name {}'
                 .format(rg, self.sql_server_names[1]), checks=NoneCheck())

        # test list sql server should be 0
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 0)])
