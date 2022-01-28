# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
import unittest

_running_state = "Running"
_stopped_state = "Stopped"


class AzureKustoClusterTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_kusto_cluster_life_cycle(self, resource_group):
        self.kwargs.update({
            'sku': 'Standard_D13_v2',
            'name': self.create_random_name(prefix='test', length=20),
            'location': "Central US",
            'capacity': 4
        })

        # Create cluster
        self.cmd('az kusto cluster create -n {name} -g {rg} --sku {sku} --capacity {capacity}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _running_state),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.capacity', '{capacity}')])

        # Get cluster
        self.cmd('az kusto cluster show -n {name} -g {rg}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _running_state),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.capacity', '{capacity}')])

        # Update cluster
        self.kwargs.update({
            'sku': 'Standard_D14_v2',
            'capacity': 6
        })
        self.cmd('az kusto cluster update -n {name} -g {rg} --sku {sku} --capacity {capacity} ',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _running_state),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.capacity', '{capacity}')])

        # Delete cluster
        self.cmd('az kusto cluster delete -n {name} -g {rg} -y')

    @ResourceGroupPreparer()
    def test_kusto_cluster_stop_start(self, resource_group):
        self.kwargs.update({
            'sku': 'Standard_D13_v2',
            'name': self.create_random_name(prefix='test', length=20),
        })

        self.cmd('az kusto cluster create -n {name} -g {rg} --sku {sku}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _running_state),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('az kusto cluster stop -n {name} -g {rg}')

        # Verify that the state is stopped
        self.cmd('az kusto cluster show -n {name} -g {rg}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _stopped_state),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('az kusto cluster start -n {name} -g {rg}')

        # Verify that the state is running
        self.cmd('az kusto cluster show -n {name} -g {rg}',
                 checks=[self.check('name', '{name}'),
                         self.check('sku.name', '{sku}'),
                         self.check('state', _running_state),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('az kusto cluster delete -n {name} -g {rg} -y')


class AzureKustoDatabaseTests (ScenarioTest):
    @ResourceGroupPreparer()
    def test_kusto_database_life_cycle(self, resource_group):
        self.kwargs.update({
            'sku': 'Standard_D13_v2',
            'cluster_name': self.create_random_name(prefix='test', length=20),
            'database_name': self.create_random_name(prefix='testdb', length=20),
            'location': "Central US",
            'soft_delete_period': 'P10D',
            'hot_cache_period': 'P5D',
            'soft_delete_period_display': '10 days, 0:00:00',
            'hot_cache_period_display': '5 days, 0:00:00'
        })

        # Create cluster
        self.cmd('az kusto cluster create -n {cluster_name} -g {rg} --sku {sku}',
                 checks=[self.check('name', '{cluster_name}'),
                         self.check('sku.name', '{sku}')])

        # Create database
        self.cmd('az kusto database create --cluster-name {cluster_name} -g {rg} -n {database_name}  --soft-delete-period {soft_delete_period} --hot-cache-period {hot_cache_period}',
                 checks=[self.check('name', '{cluster_name}/{database_name}'),
                         self.check('softDeletePeriod', '{soft_delete_period_display}'),
                         self.check('hotCachePeriod', '{hot_cache_period_display}')])

        # Update database
        self.kwargs.update({
            'soft_delete_period': 'P20D',
            'hot_cache_period': 'P10D',
            'soft_delete_period_display': '20 days, 0:00:00',
            'hot_cache_period_display': '10 days, 0:00:00'
        })

        self.cmd('az kusto database update --cluster-name {cluster_name} -g {rg} -n {database_name}  --soft-delete-period {soft_delete_period} --hot-cache-period {hot_cache_period}',
                 checks=[self.check('name', '{cluster_name}/{database_name}'),
                         self.check('softDeletePeriod', '{soft_delete_period_display}'),
                         self.check('hotCachePeriod', '{hot_cache_period_display}')])

        # Delete database
        self.cmd('az kusto database delete --cluster-name {cluster_name} -g {rg} -n {database_name} -y')

        # Delete cluster
        self.cmd('az kusto cluster delete -n {cluster_name} -g {rg} -y')


if __name__ == '__main__':
    unittest.main()
