# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class CosmosdbPriorityBasedExecutionScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_priority_based_execution', location='westus')
    def test_cosmosdb_priority_based_execution(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name(prefix='pbe-', length=8),
            'loc': 'westus'
        })

        # create priority based execution enabled account
        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-pbe')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enablePriorityBasedExecution', True),
        ])
        print('Created account with Priority Based Execution Enabled')

        # set default priority level to low priority
        self.cmd('az cosmosdb update -n {acc} -g {rg} --default-priority-level Low')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('defaultPriorityLevel', 'Low'),
        ])
        print('Set Default Priority Level to Low')

        # disable Priority Based Execution
        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-pbe false')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enablePriorityBasedExecution', False),
        ])
        print('Disabled Priority Based Execution')

        # enable Priority Based Execution
        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-pbe')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enablePriorityBasedExecution', True),
        ])
        print('Enabled Priority Based Execution')

        # set default priority level to high priority
        self.cmd('az cosmosdb update -n {acc} -g {rg} --default-priority-level High')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('defaultPriorityLevel', 'High'),
        ])
        print('Set Default Priority Level to High')

        # delete account
        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')
