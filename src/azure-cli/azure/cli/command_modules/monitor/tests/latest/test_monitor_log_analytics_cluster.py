# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only


class TestClusterScenarios(ScenarioTest):

    @record_only()
    def test_monitor_log_analytics_cluster_default(self):
        new_cluster_name = self.create_random_name('clitest-cluster-', 20)
        sku_capacity = 1000
        self.kwargs.update({
            'rg1': 'cli_test_monitor_cluster_rg_centralus',
            'rg2': 'yu-test-eastus2-rg',
            'new_cluster_name': new_cluster_name,
            'sku_capacity': sku_capacity,
            'existing_cluster_name': 'yutestcluster4'
        })

        self.cmd("monitor log-analytics cluster create -g {rg1} -n {new_cluster_name} --sku-capacity {sku_capacity} --no-wait",
                 checks=[])

        self.cmd("monitor log-analytics cluster show -g {rg1} -n {new_cluster_name}", checks=[
            self.check('provisioningState', 'ProvisioningAccount'),
            self.check('name', new_cluster_name),
            self.check('sku.capacity', sku_capacity)
        ])

        new_sku_capacity = 2000
        self.kwargs.update({
            'sku_capacity': new_sku_capacity
        })

        self.cmd("monitor log-analytics cluster update -g {rg2} -n {existing_cluster_name} "
                 "--sku-capacity {sku_capacity}",
                 checks=[
                     self.check('sku.capacity', new_sku_capacity)
                 ])

        self.cmd("monitor log-analytics cluster show -g {rg2} -n {existing_cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.capacity', new_sku_capacity)
        ])

        self.cmd("monitor log-analytics cluster list -g {rg1}", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("monitor log-analytics cluster delete -g {rg2} -n {existing_cluster_name} -y", checks=[])

        with self.assertRaisesRegexp(SystemExit, '3'):
            self.cmd('monitor log-analytics cluster show -g {rg2} -n {existing_cluster_name}')

    @record_only()
    def test_monitor_log_analytics_cluster_update_key(self):
        new_key_name = 'key2'
        new_key_version = 'dc814576e6b34de69a10b186a4723035'
        self.kwargs.update({
            'rg': 'azure-cli-test-scus',
            'key_name': new_key_name,
            'key_version': new_key_version,
            'key_vault_uri': 'https://yu-vault-1.vault.azure.net/',
            'cluster_name': 'yu-test-cluster2'
        })

        self.cmd("monitor log-analytics cluster update -g {rg} -n {cluster_name} --key-name {key_name} "
                 "--key-vault-uri {key_vault_uri} --key-version {key_version}",
                 checks=[])

        self.cmd("monitor log-analytics cluster wait -g {rg} -n {cluster_name} --updated", checks=[])

        self.cmd("monitor log-analytics cluster show -g {rg} -n {cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('keyVaultProperties.keyName', new_key_name),
            self.check('keyVaultProperties.keyVersion', new_key_version)
        ])
