# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class CosmosdbThroughputBucketsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cosmosdb_throughput_buckets')
    def test_cosmosdb_throughput_buckets_stable_api(self, resource_group):
        subscription_id = self.get_subscription_id()
        throughput_body = {
            'properties': {
                'resource': {
                    'throughput': 400,
                    'throughputBuckets': [
                        {'id': 1, 'maxThroughputPercentage': 10, 'isDefaultBucket': True},
                        {'id': 2, 'maxThroughputPercentage': 20, 'isDefaultBucket': False},
                        {'id': 3, 'maxThroughputPercentage': 15}
                    ]
                }
            }
        }
        self.kwargs.update({
            'acc': self.create_random_name(prefix='buckets-', length=20),
            'db_name': self.create_random_name(prefix='database-', length=20),
            'ctn_name': self.create_random_name(prefix='container-', length=20),
            'subscription_id': subscription_id,
            'throughput_body': json.dumps(throughput_body, separators=(',', ':'))
        })

        self.cmd('az cosmosdb create -n {acc} -g {rg}')
        self.cmd('az cosmosdb sql database create -g {rg} -a {acc} -n {db_name}')
        self.cmd(
            'az cosmosdb sql container create -g {rg} -a {acc} -d {db_name} '
            '-n {ctn_name} -p /partitionKey --throughput 400')

        throughput_url = (
            '/subscriptions/{subscription_id}/resourceGroups/{rg}/providers/Microsoft.DocumentDB/'
            'databaseAccounts/{acc}/sqlDatabases/{db_name}/containers/{ctn_name}/'
            'throughputSettings/default?api-version=2026-07-15')
        self.cmd(
            "az rest --method put --url '" + throughput_url + "' "
            "--body '{throughput_body}'")

        bucket_checks = [
            self.check('resource.throughputBuckets[0].id', 1),
            self.check('resource.throughputBuckets[0].maxThroughputPercentage', 10),
            self.check('resource.throughputBuckets[0].isDefaultBucket', True),
            self.check('resource.throughputBuckets[1].id', 2),
            self.check('resource.throughputBuckets[1].maxThroughputPercentage', 20),
            self.check('resource.throughputBuckets[1].isDefaultBucket', False),
            self.check('resource.throughputBuckets[2].id', 3),
            self.check('resource.throughputBuckets[2].maxThroughputPercentage', 15)
        ]
        self.cmd(
            'az cosmosdb sql container throughput show -g {rg} -a {acc} '
            '-d {db_name} -n {ctn_name}',
            checks=bucket_checks)
        self.cmd(
            'az cosmosdb sql container throughput update -g {rg} -a {acc} '
            '-d {db_name} -n {ctn_name} --throughput 400',
            checks=bucket_checks)

        self.cmd('az cosmosdb delete -n {acc} -g {rg} --yes')