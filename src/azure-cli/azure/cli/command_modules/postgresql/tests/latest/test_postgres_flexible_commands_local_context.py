# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.testsdk import (
    JMESPathCheck,
    StringContainCheck,
    LocalContextScenarioTest)

# Constants
SERVER_NAME_PREFIX = 'azuredbclitest-'
SERVER_NAME_MAX_LENGTH = 20


class FlexibleServerLocalContextScenarioTest(LocalContextScenarioTest):

    def _test_flexible_server_local_context(self, resource_group):
        self.cmd('config param-persist on')
        location = self.postgres_location

        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)

        self.cli_ctx.local_context.set(['all'], 'resource_group_name', resource_group)
        self.cli_ctx.local_context.set(['all'], 'location', location)

        self.cmd('postgres flexible-server create -n {} --public-access none'.format(server_name))

        local_context_info = self.cmd('config param-persist show').get_output_in_json()

        show_result = self.cmd('postgres flexible-server show',
                               checks=[JMESPathCheck('resourceGroup', local_context_info['all']['resource_group_name']),
                                       JMESPathCheck('name', local_context_info['postgres flexible-server']['server_name']),
                                       JMESPathCheck('administratorLogin', local_context_info['postgres flexible-server']['administrator_login'])]).get_output_in_json()
        self.assertEqual(''.join(show_result['location'].lower().split()), location)

        self.cmd('postgres flexible-server show-connection-string',
                 checks=[StringContainCheck(local_context_info['postgres flexible-server']['administrator_login'])]).get_output_in_json()

        self.cmd('postgres flexible-server list-skus')

        self.cmd('postgres flexible-server delete --yes')

        delete_local_context_info = self.cmd('config param-persist show').get_output_in_json()

        self.assertNotIn('postgres flexible-server', delete_local_context_info)
        self.assertNotIn(local_context_info['postgres flexible-server']['server_name'], delete_local_context_info)
        self.assertNotIn(local_context_info['postgres flexible-server']['administrator_login'], delete_local_context_info)
