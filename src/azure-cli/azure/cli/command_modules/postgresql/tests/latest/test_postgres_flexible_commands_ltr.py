# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from datetime import datetime, timedelta, timezone
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (
    JMESPathCheck,
    ResourceGroupPreparer,
    ScenarioTest,
    live_only)
from .constants import DEFAULT_LOCATION
from .server_preparer import ServerPreparer


class FlexibleServerLtrMgmtScenarioTest(ScenarioTest):

    postgres_location = DEFAULT_LOCATION

    @AllowLargeResponse()
    @ResourceGroupPreparer(location=postgres_location)
    @ServerPreparer(location=postgres_location)
    @live_only()
    def test_postgres_flexible_server_ltr(self, resource_group, server):
        self._test_flexible_server_ltr(resource_group, server)

    def _test_flexible_server_ltr(self, resource_group, server):

        if self.cli_ctx.local_context.is_on:
            self.cmd('config param-persist off')

        server_name = server
        storage_account_name = self.create_random_name('teststorage', 24)
        container_account_name = self.create_random_name('testcontainer', 24)
        start_time = (datetime.now(timezone.utc) - timedelta(minutes=60)).strftime(f"%Y-%m-%dT%H:%MZ")
        expiry_time = (datetime.now(timezone.utc) + timedelta(minutes=200)).strftime(f"%Y-%m-%dT%H:%MZ")

        # create storage account
        storage_account = self.cmd('az storage account create -n {} -g {} --encryption-services blob'.format(
                                    storage_account_name, resource_group)).get_output_in_json()

        # create storage container inside storage account
        self.cmd('az storage container create -n {} --account-name {}'.format(container_account_name, storage_account_name))

        # generate SAS URL for storage account
        container_sas_token = self.cmd('az storage container generate-sas -n {} --account-name {} \
                                       --permissions dlrw --expiry {} \
                                       --start {}'.format(container_account_name, storage_account_name,
                                                          expiry_time, start_time)).output
        sas_url = storage_account['primaryEndpoints']['blob'] + container_account_name + "?" + container_sas_token[1:-2]

        # precheck LTR
        backup_name = "testbackup"
        precheck_result = self.cmd('postgres flexible-server long-term-retention pre-check -g {} \
                 -n {} -b {}'.format(resource_group, server_name, backup_name)).get_output_in_json()
        self.assertGreaterEqual(precheck_result['numberOfContainers'], 0)

        # start LTR
        self.cmd('postgres flexible-server long-term-retention start -g {} -n {} -u {} -b {}'
                 .format(resource_group, server_name, sas_url, backup_name),
                 checks=[JMESPathCheck('backupName', backup_name)])

        # show LTR
        self.cmd('postgres flexible-server long-term-retention show -g {} -n {} -b {}'
                 .format(resource_group, server_name, backup_name),
                 checks=[JMESPathCheck('backupName', backup_name)])

        # list LTR
        list_result = self.cmd('postgres flexible-server long-term-retention list -g {} \
                 -n {}'.format(resource_group, server_name)).get_output_in_json()
        self.assertEqual(len(list_result), 1)
        self.assertEqual(list_result[0]['backupName'], backup_name)