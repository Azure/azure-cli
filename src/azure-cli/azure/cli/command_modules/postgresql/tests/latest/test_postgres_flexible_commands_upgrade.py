# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION


class PostgreSQLFlexibleServerUpgradeMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgres_flexible_server_upgrade_mgmt(self, resource_group):
        self._test_flexible_server_upgrade_mgmt(resource_group)

    def _test_flexible_server_upgrade_mgmt(self, resource_group):
        server_name = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        current_version = '15'
        new_version = '17'
        location = DEFAULT_LOCATION

        # create server
        self.cmd('postgres flexible-server create -g {} -n {} --tier GeneralPurpose --location {} --version {} --public-access none --yes'.format(
            resource_group, server_name, location, current_version))

        self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name),
                 checks=[JMESPathCheck('version', current_version)])

        # upgrade server
        result = self.cmd('postgres flexible-server upgrade -g {} -n {} --version {} --yes'.format(resource_group, server_name, new_version)).get_output_in_json()
        self.assertTrue(result['version'].startswith(new_version))