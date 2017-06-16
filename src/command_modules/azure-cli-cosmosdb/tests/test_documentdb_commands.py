# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer


class DocumentDBTests(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_database_account(self, resource_group):
        name = self.create_random_name(prefix='cli', length=40)
        self.cmd(
            'az cosmosdb create -n {} -g {} '
            '--enable-automatic-failover {} --default-consistency-level {}'
            .format(name, resource_group, 'true', 'ConsistentPrefix'))
        self.cmd('az cosmosdb show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('enableAutomaticFailover', True),
            JMESPathCheck('consistencyPolicy.defaultConsistencyLevel',
                          'ConsistentPrefix'),
        ])
        self.cmd(
            'az cosmosdb update -n {} -g {} '
            '--enable-automatic-failover {} --default-consistency-level {}'
            .format(name, resource_group, 'false', 'Session'))
        self.cmd('az cosmosdb show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('enableAutomaticFailover', False),
            JMESPathCheck('consistencyPolicy.defaultConsistencyLevel',
                          'Session'),
        ])
