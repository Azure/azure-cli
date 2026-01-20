# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .server_preparer import ServerPreparer
from .constants import DEFAULT_LOCATION


class FlexibleServerParameterMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_parameter_mgmt(self, resource_group, server):
        self._test_parameter_mgmt(resource_group, server)

    def _test_parameter_mgmt(self, resource_group, server):

        self.cmd('postgres flexible-server parameter list -g {} -s {}'.format(resource_group, server), checks=[JMESPathCheck('type(@)', 'array')])

        parameter_name = 'lock_timeout'
        default_value = '0'
        value = '2000'

        source = 'system-default'
        self.cmd('postgres flexible-server parameter show --name {} -g {} -s {}'.format(parameter_name, resource_group, server),
                 checks=[JMESPathCheck('defaultValue', default_value),
                         JMESPathCheck('source', source)])

        source = 'user-override'
        self.cmd('postgres flexible-server parameter set --name {} -v {} --source {} -s {} -g {}'.format(parameter_name, value, source, server, resource_group),
                 checks=[JMESPathCheck('value', value),
                         JMESPathCheck('source', source)])