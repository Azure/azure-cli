# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


class CosmosdbPerPartitionAutomaticFailoverScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_ppaf', location='southcentralus')
    def test_cosmosdb_per_partition_automatic_failover(self, resource_group):
        self.kwargs.update({
            'acc': self.create_random_name(prefix='ppaf-test-', length=20)
        })

        self.cmd(
            'az cosmosdb create -n {acc} -g {rg} '
            '--locations regionName=southcentralus failoverPriority=0 '
            '--locations regionName=eastus failoverPriority=1 '
            '--enable-per-partition-automatic-failover true')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('perPartitionAutomaticFailoverEnabled', True),
        ])

        self.cmd(
            'az cosmosdb update -n {acc} -g {rg} '
            '--enable-per-partition-automatic-failover true')
        self.cmd('az cosmosdb show -n {acc} -g {rg}', checks=[
            self.check('perPartitionAutomaticFailoverEnabled', True),
        ])

        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')