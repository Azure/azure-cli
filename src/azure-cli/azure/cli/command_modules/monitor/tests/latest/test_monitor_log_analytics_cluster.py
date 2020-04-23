# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest

from azure.cli.testsdk import ScenarioTest, record_only


class TestClusterScenarios(ScenarioTest):

    @record_only()
    @unittest.skip('Need run this test after review')
    def test_monitor_log_analytics_cluster_default(self):
        cluster_name = self.create_random_name('clitest-cluster-', 20)
        sku_capacity = 1000
        self.kwargs.update({
            'rg1': 'cli_test_monitor_cluster-rg-ukwest',
            'rg2': 'yu-test-eastus2-rg',
            'new_cluster_name': cluster_name,
            'existing_cluster_name': 'yutestcluster4',
            'sku_capacity': sku_capacity
        })

        self.cmd("monitor log-analytics cluster create -g {rg1} -n {new_cluster_name} --sku-capacity {sku_capacity}",
                 checks=[
                     self.check('provisioningState', 'ProvisioningAccount'),
                     self.check('name', cluster_name),
                     self.check('sku.name', 'capacityreservation'),
                     self.check('sku.capacity', sku_capacity)
                 ])

        new_sku_capacity = 1700
        self.kwargs.update({
            'cluster_name': cluster_name,
            'sku_capacity': new_sku_capacity
        })

        self.cmd("monitor log-analytics cluster update -g {rg2} -n {existing_cluster_name} --key-name my-key "
                 "--key-vault-uri https://vaultforcluster.vault.azure.net/ --key-version "
                 "f4932c4b94a943c598650522d10ef301 --sku-capacity {sku_capacity}",
                 checks=[
                     self.check('provisioningState', 'Updating'),
                     self.check('sku.capacity', new_sku_capacity)
                 ])

        self.cmd("monitor log-analytics cluster wait -g {rg2} -n {existing_cluster_name} --updated", checks=[])

        self.cmd("monitor log-analytics cluster show -g {rg2} -n {existing_cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('keyVaultProperties.keyName', 'my-key'),
            self.check('keyVaultProperties.keyVaultUri', 'https://vaultforcluster.vault.azure.net:443'),
            self.check('keyVaultProperties.keyVersion', 'f4932c4b94a943c598650522d10ef301'),
            self.check('sku.capacity', new_sku_capacity)
        ])

        self.cmd("monitor log-analytics cluster list -g {rg1}", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("monitor log-analytics cluster delete -g {rg2} -n {existing_cluster_name} -y", checks=[])

        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('monitor log-analytics cluster show -g {rg2} -n {existing_cluster_name}')
