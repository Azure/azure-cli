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
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH
from .server_preparer import ServerPreparer


class FlexibleServerRestoreMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    def test_postgres_flexible_server_restore_mgmt(self, resource_group, server):
        self._test_flexible_server_restore_mgmt(resource_group, server)

    def _test_flexible_server_restore_mgmt(self, resource_group, server):

        server_name = server

        self.cmd('postgres flexible-server show -g {} -n {}'.format(resource_group, server_name)).get_output_in_json()

        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)

        # restore server
        target_server_default = self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH)
        restore_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} '
                                  .format(resource_group, target_server_default, server_name)).get_output_in_json()
        self.assertEqual(restore_result['name'], target_server_default)

        # Restore to ssdv2
        target_server_ssdv2 = self.create_random_name(SERVER_NAME_PREFIX + 'ssdv2-', SERVER_NAME_MAX_LENGTH)
        storage_type = 'PremiumV2_LRS'
        restore_migration_result = self.cmd('postgres flexible-server restore -g {} --name {} --source-server {} --storage-type {}'
                                  .format(resource_group, target_server_ssdv2, server_name, storage_type)).get_output_in_json()
        self.assertEqual(restore_migration_result['storage']['type'], storage_type)

        # clean up
        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_default), checks=NoneCheck())

        self.cmd('postgres flexible-server delete -g {} -n {} --yes'.format(
                 resource_group, target_server_ssdv2), checks=NoneCheck())