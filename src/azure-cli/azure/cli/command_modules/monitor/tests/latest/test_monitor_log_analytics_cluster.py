# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only, ResourceGroupPreparer


class TestClusterScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_log_analytics_cluster_c', parameter_name='rg1', key='rg1', location='centralus')
    def test_monitor_log_analytics_cluster_default(self, rg1):
        new_cluster_name = self.create_random_name('clitest-cluster-', 20)
        sku_capacity = 1000
        self.kwargs.update({
            'new_cluster_name': new_cluster_name,
            'sku_capacity': sku_capacity
        })

        self.cmd("monitor log-analytics cluster create -g {rg1} -n {new_cluster_name} --sku-capacity {sku_capacity}",
                 checks=[])

        self.cmd("monitor log-analytics cluster show -g {rg1} -n {new_cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('name', new_cluster_name),
            self.check('sku.capacity', sku_capacity)
        ])

        new_sku_capacity = 2000
        self.kwargs.update({
            'sku_capacity': new_sku_capacity
        })

        self.cmd("monitor log-analytics cluster update -g {rg1} -n {new_cluster_name} "
                 "--sku-capacity {sku_capacity}",
                 checks=[
                     self.check('sku.capacity', new_sku_capacity)
                 ])

        self.cmd("monitor log-analytics cluster show -g {rg1} -n {new_cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.capacity', new_sku_capacity)
        ])

        self.cmd("monitor log-analytics cluster list -g {rg1}", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("monitor log-analytics cluster delete -g {rg1} -n {new_cluster_name} -y", checks=[])

        self.cmd("monitor log-analytics cluster list -g {rg1}", checks=[
            self.check('length(@)', 0)
        ])

    # @record_only()
    def test_monitor_log_analytics_cluster_update_key(self):
        new_key_name = 'log-analytics-cluster'
        new_key_version = '903ca0dc34b44f0789e35488eaffc9f5'
        self.kwargs.update({
            'rg': 'azure-cli-test-scus',
            'key_name': new_key_name,
            'key_version': new_key_version,
            'key_vault_uri': 'https://azure-cli-test-scus.vault.azure.net/',
            'cluster_name': 'test-cluster'
        })

        self.cmd("monitor log-analytics cluster update -g {rg} -n {cluster_name} --key-name {key_name} "
                 "--key-vault-uri {key_vault_uri} --key-version {key_version}",
                 checks=[])

        self.cmd("monitor log-analytics cluster show -g {rg} -n {cluster_name}", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('keyVaultProperties.keyName', new_key_name),
            self.check('keyVaultProperties.keyVersion', new_key_version)
        ])

        self.cmd("monitor log-analytics cluster update -g {rg} -n {cluster_name} --key-name {key_name} "
                 "--key-vault-uri {key_vault_uri} --key-version ''",
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('keyVaultProperties.keyName', new_key_name),
                     self.check('keyVaultProperties.keyVersion', '')
                 ])
