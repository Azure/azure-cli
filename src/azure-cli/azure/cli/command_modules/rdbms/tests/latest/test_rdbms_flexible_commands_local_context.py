# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.local_context import AzCLILocalContext, ALL, LOCAL_CONTEXT_FILE
from azure.cli.core.util import CLIError
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    StringContainCheck,
    ScenarioTest,
    LocalContextScenarioTest)

# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    def _test_flexible_server_local_context(self, database_engine, resource_group):
        self.cmd('config param-persist on')
        if database_engine == 'mysql':
            location = self.mysql_location
        else:
            location = self.postgres_location

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', location)

        self.cmd('{} flexible-server create -n {} --public-access none'.format(database_engine, server_name))

        local_context_info = self.cmd('config param-persist show').get_output_in_json()

        show_result = self.cmd('{} flexible-server show'.format(database_engine),
                               checks=[JMESPathCheck('resourceGroup', local_context_info['all']['resource_group_name']),
                                       JMESPathCheck('name', local_context_info[database_engine + ' flexible-server']['server_name']),
                                       JMESPathCheck('administratorLogin', local_context_info[database_engine + ' flexible-server']['administrator_login'])]).get_output_in_json()
        self.assertEqual(''.join(show_result['location'].lower().split()), location)

        self.cmd('{} flexible-server show-connection-string'.format(database_engine),
                 checks=[StringContainCheck(local_context_info[database_engine + ' flexible-server']['administrator_login'])]).get_output_in_json()

        self.cmd('{} flexible-server list-skus'.format(database_engine))

        self.cmd('{} flexible-server delete --yes'.format(database_engine))

        delete_local_context_info = self.cmd('config param-persist show').get_output_in_json()

        self.assertNotIn(database_engine + ' flexible-server', delete_local_context_info)
        self.assertNotIn(local_context_info[database_engine + ' flexible-server']['server_name'], delete_local_context_info)
        self.assertNotIn(local_context_info[database_engine + ' flexible-server']['administrator_login'], delete_local_context_info)
