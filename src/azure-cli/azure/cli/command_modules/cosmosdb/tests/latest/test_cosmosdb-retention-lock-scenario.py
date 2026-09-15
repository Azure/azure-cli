# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class CosmosdbRetentionLockScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_retention_lock')
    def test_cosmosdb_retention_lock(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name(prefix='retention-lock-', length=25),
            'create_timestamp': '2030-01-01T00:00:00Z',
            'update_timestamp': '2030-06-01T00:00:00Z'
        })

        self.cmd(
            'az cosmosdb create -n {acc} -g {rg} '
            '--backup-policy-type Continuous '
            '--backup-retention-lock-expiration-timestamp {create_timestamp}',
            checks=[
                self.check('backupPolicy.type', 'Continuous'),
                self.check('backupPolicy.backupRetentionLockExpirationTimestamp', '{create_timestamp}'),
            ])
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('backupPolicy.backupRetentionLockExpirationTimestamp', '{create_timestamp}'),
        ])

        self.cmd(
            'az cosmosdb update -n {acc} -g {rg} '
            '--backup-retention-lock-expiration-timestamp {update_timestamp}',
            checks=[
                self.check('backupPolicy.backupRetentionLockExpirationTimestamp', '{update_timestamp}'),
            ])

        self.cmd('az cosmosdb update -n {acc} -g {rg} --tags retention-lock=preserved')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('backupPolicy.backupRetentionLockExpirationTimestamp', '{update_timestamp}'),
        ])

        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')