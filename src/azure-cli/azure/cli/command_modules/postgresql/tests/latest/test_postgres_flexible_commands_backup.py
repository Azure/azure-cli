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
    ScenarioTest,
    live_only)
from .server_preparer import ServerPreparer
from .constants import DEFAULT_LOCATION, SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH


class PostgreSQLFlexibleServerBackupsMgmtScenarioTest(ScenarioTest):

    # Keep this live-only until a service recording is available.
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(location=DEFAULT_LOCATION)
    def test_postgres_flexible_server_immutable_backup_mgmt(self, resource_group):
        for immutable_backup in ('Enabled', 'Disabled'):
            self.kwargs.update(
                server_name=self.create_random_name(SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH),
                location=DEFAULT_LOCATION,
                immutable_backup=immutable_backup)
            self.cmd('postgres flexible-server create --resource-group {rg} --name {server_name} '
                     '--location {location} --sku-name Standard_D2s_v3 --tier GeneralPurpose '
                     '--storage-size 64 --version 16 --backup-retention 25 '
                     '--immutable-backup {immutable_backup} --public-access None --yes')
            self.cmd('postgres flexible-server show --resource-group {rg} --name {server_name}',
                     checks=[JMESPathCheck('backup.immutableBackup', immutable_backup),
                             JMESPathCheck('backup.backupRetentionDays', 25)])

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
            backups = self.cmd('postgres flexible-server backup list -g {} -s {}'
                            .format(resource_group, server)).get_output_in_json()
            attempts += 1
            if len(backups) > 0:
                break
            os.environ.get(ENV_LIVE_TEST, False) and sleep(60)

        backups_length = len(backups)
        self.assertTrue(backups_length > 0)

        automatic_backup = self.cmd('postgres flexible-server backup show -g {} -s {} -n {}'
                                    .format(resource_group, server, backups[0]['name'])).get_output_in_json()

        self.assertDictEqual(automatic_backup, backups[0])

        # Create on-demand backup
        backup_name = self.create_random_name(F'backup', 16)

        self.cmd('postgres flexible-server backup create -g {} -s {} -n {}'
                .format(resource_group, server, backup_name),
                checks=[JMESPathCheck('name', backup_name)])

        # Confirm that on-demand backup is created
        backups_update = self.cmd('postgres flexible-server backup list -g {} -s {}'
                        .format(resource_group, server)).get_output_in_json()

        self.assertTrue(backups_length < len(backups_update))

        # Delete on-demand backup
        self.cmd('postgres flexible-server backup delete -g {} -s {} -n {} --yes'
                .format(resource_group, server, backup_name))

        # Confirm that on-demand backup is deleted
        backups_update = self.cmd('postgres flexible-server backup list -g {} -s {}'
                        .format(resource_group, server)).get_output_in_json()

        self.assertTrue(backups_length == len(backups_update))