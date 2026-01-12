# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class CosmosdbBurstCapacityScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_burst_capacity', location='australiaeast')
    def test_cosmosdb_burst_capacity(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name(prefix='burst-test-', length=20),
            'loc': 'australiaeast',
            'tar': '0=1200 1=1200',
            'src': '2'
        })

        #create burst capacity enabled account
        self.cmd('az cosmosdb create -n {acc} -g {rg} --enable-burst-capacity')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableBurstCapacity', True),
        ])
        print('Created burst capacity enabled account')

        #disable burst capacity
        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-burst-capacity false')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableBurstCapacity', False),
        ])
        print('Disabled burst capacity')

        #enable burst capacity
        self.cmd('az cosmosdb update -n {acc} -g {rg} --enable-burst-capacity')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('enableBurstCapacity', True),
        ])
        print('Enabled burst capacity')

        #clean up
        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')