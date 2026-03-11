# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .server_preparer import ServerPreparer
from .constants import DEFAULT_LOCATION


class FlexibleServerDatabaseMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_database_mgmt(self, resource_group, server):
        self._test_database_mgmt(resource_group, server)

    def _test_database_mgmt(self, resource_group, server):

        database_name = self.create_random_name('database', 20)

        self.cmd('postgres flexible-server db create -g {} -s {} -d {}'.format(resource_group, server, database_name),
                 checks=[JMESPathCheck('name', database_name)])

        self.cmd('postgres flexible-server db show -g {} -s {} -d {}'.format(resource_group, server, database_name),
                 checks=[
                     JMESPathCheck('name', database_name),
                     JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('postgres flexible-server db list -g {} -s {} '.format(resource_group, server),
                 checks=[JMESPathCheck('type(@)', 'array')])

        self.cmd('postgres flexible-server db delete -g {} -s {} -d {} --yes'.format(resource_group, server, database_name),
                 checks=NoneCheck())