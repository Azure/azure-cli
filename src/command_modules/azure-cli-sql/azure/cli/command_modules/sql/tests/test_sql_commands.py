# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
from __future__ import print_function

import os
import time

from azure.cli.core._util import CLIError
from azure.cli.core.test_utils.vcr_test_base import (ResourceGroupVCRTestBase, JMESPathCheck,
                                                     NoneCheck, VCRTestBase)

class SqlServerMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(SqlServerMgmtScenarioTest, self).__init__(__file__, test_method, resource_group='cli-test-sql-mgmt')
        self.sql_server_name = 'cli-sql-12345-a'
        self.location = "westus"
        self.administrator_login = 'admin123'
        self.administrator_login_password = 'SecretPassword123'

    def test_sql_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        sql_server_name = self.sql_server_name
        loc = self.location
        user = self.administrator_login
        password = self.administrator_login_password

        # test create sql server with minimal required parameters
        self.cmd('sql server create -g {} --server-name {} -l {} --administrator-login {} --administrator-login-password {}'
                .format(rg, sql_server_name, loc, user, password), checks=[
            JMESPathCheck('name', sql_server_name),
            JMESPathCheck('resourceGroup', rg)])

        # test list sql server should be 1
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 1)])

        # test delete sql server
        self.cmd('sql server delete -g {} --server-name {}'.format(rg, sql_server_name), checks=NoneCheck())

        # test list sql server should be 0
        self.cmd('sql server list -g {}'.format(rg), checks=[JMESPathCheck('length(@)', 0)])
