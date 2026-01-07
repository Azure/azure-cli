# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    NoneCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .constants import BACKUP_LOCATION, DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH
from .server_preparer import ServerPreparer


class FlexibleServerGeoRestoreMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_geo_restore_mgmt(self, resource_group, server_name):
        self._test_flexible_server_geo_restore_mgmt(resource_group, server_name)

    def _test_flexible_server_geo_restore_mgmt(self, resource_group, server_name):

        self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # restore server
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restore_result = self.cmd('postgres flexible-server geo-restore -g {} -l {} --name {} --source-server {} --yes'
                                  .format(resource_group, BACKUP_LOCATION, target_server_default, server_name)).get_output_in_json()
        self.assertEqual(restore_result['name'], target_server_default)
        self.assertEqual(str(restore_result['location']).replace(' ', '').lower(), BACKUP_LOCATION)

        # clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_default), checks=NoneCheck())