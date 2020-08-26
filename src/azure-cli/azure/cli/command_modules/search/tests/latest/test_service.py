# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest


class AzureSearchServicesTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_create_skus(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'sku_name': 'basic',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_create_multi_partition(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 2,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_create_multi_replica(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 2,
            'partition_count': 1,
        })

        self.cmd(
            'az search service create -n {name} -g {rg} --sku {sku_name}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_update(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'replica_count': 2,
            'partition_count': 1,
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.kwargs.update({
            'replica_count': 1,
            'partition_count': 2,
        })

        self.cmd(
            'az search service update -n {name} -g {rg}'
            ' --replica-count {replica_count} --partition-count {partition_count}',
            checks=[self.check('name', '{name}'),
                    self.check('sku.name', '{sku_name}'),
                    self.check('replicaCount', '{replica_count}'),
                    self.check('partitionCount', '{partition_count}')])

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_create_delete_show(self, resource_group):
        self.kwargs.update({
            'sku_name': 'standard',
            'name': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        self.cmd('az search service show -n {name} -g {rg}')

        self.cmd('az search service delete -n {name} -g {rg} -y')

        self.cmd('az search service show -n {name} -g {rg}', expect_failure=True)

    @ResourceGroupPreparer(name_prefix='azure_search_cli_test')
    def test_service_create_delete_list(self, resource_group):
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 0)

        self.kwargs.update({
            'sku_name': 'standard',
            'name1': self.create_random_name(prefix='test', length=24),
            'name2': self.create_random_name(prefix='test', length=24),
            'replica_count': 1,
            'partition_count': 1,
        })

        self.cmd('az search service create -n {name1} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name1}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 1)
        self.assertTrue(self.kwargs['name1'] in [x['name'] for x in _services])

        self.cmd('az search service create -n {name2} -g {rg} --sku {sku_name}',
                 checks=[self.check('name', '{name2}'),
                         self.check('sku.name', '{sku_name}'),
                         self.check('replicaCount', '{replica_count}'),
                         self.check('partitionCount', '{partition_count}')])

        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 2)
        self.assertTrue(self.kwargs['name1'] in [x['name'] for x in _services])
        self.assertTrue(self.kwargs['name2'] in [x['name'] for x in _services])

        self.cmd('az search service delete -n {name1} -g {rg} -y')
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 1)
        self.assertTrue(self.kwargs['name2'] in [x['name'] for x in _services])
        self.assertFalse(self.kwargs['name1'] in [x['name'] for x in _services])

        self.cmd('az search service delete -n {name2} -g {rg} -y')
        _services = self.cmd('az search service list -g {rg}').get_output_in_json()
        self.assertTrue(len(_services) == 0)


if __name__ == '__main__':
    unittest.main()
