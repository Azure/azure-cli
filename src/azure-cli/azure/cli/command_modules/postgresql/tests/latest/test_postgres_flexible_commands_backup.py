# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from time import sleep
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk.scenario_tests.const import ENV_LIVE_TEST
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest)
from .server_preparer import ServerPreparer
from .constants import DEFAULT_LOCATION


class PostgreSQLFlexibleServerBackupsMgmtScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    @ServerPreparer(location=DEFAULT_LOCATION)
    def test_postgres_flexible_server_backups_mgmt(self, resource_group, server):
        self._test_backups_mgmt(resource_group, server)

    def _test_backups_mgmt(self, resource_group, server):
        # Wait until snapshot is created
        os.environ.get(ENV_LIVE_TEST, False) and sleep(1800)
        attempts = 0
        while attempts < 10:
            backups = self.cmd('postgres flexible-server backup list -g {} -n {}'
                            .format(resource_group, server)).get_output_in_json()
            attempts += 1
            if len(backups) > 0:
                break
            os.environ.get(ENV_LIVE_TEST, False) and sleep(60)

        backups_length = len(backups)
        self.assertTrue(backups_length > 0)

        automatic_backup = self.cmd('postgres flexible-server backup show -g {} -n {} --backup-name {}'
                                    .format(resource_group, server, backups[0]['name'])).get_output_in_json()

        self.assertDictEqual(automatic_backup, backups[0])

        # test on-demand backup create
        backup_name = self.create_random_name(F'backup', 16)

        self.cmd('postgres flexible-server backup create -g {} -n {} --backup-name {}'
                .format(resource_group, server, backup_name),
                checks=[JMESPathCheck('name', backup_name)])

        backups_update = self.cmd('postgres flexible-server backup list -g {} -n {}'
                        .format(resource_group, server)).get_output_in_json()

        self.assertTrue(backups_length < len(backups_update))

        # test on-demand backup delete
        self.cmd('postgres flexible-server backup delete -g {} -n {} --backup-name {} --yes'
                .format(resource_group, server, backup_name))

        backups_update = self.cmd('postgres flexible-server backup list -g {} -n {}'
                        .format(resource_group, server)).get_output_in_json()

        self.assertTrue(backups_length == len(backups_update))