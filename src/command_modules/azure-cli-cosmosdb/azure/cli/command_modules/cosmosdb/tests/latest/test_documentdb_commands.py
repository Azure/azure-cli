# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class DocumentDBTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_account')
    def test_create_database_account(self, resource_group):

        self.kwargs.update({
            'acc': self.create_random_name(prefix='cli', length=40)
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-automatic-failover --default-consistency-level ConsistentPrefix')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', True),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'ConsistentPrefix'),
        ])
        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-automatic-failover false --default-consistency-level Session')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableAutomaticFailover', False),
            self.check('consistencyPolicy.defaultConsistencyLevel', 'Session')
        ])
