# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only
from azure_devtools.scenario_tests import AllowLargeResponse


class TestLogProfileScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace', location='centralus')
    @AllowLargeResponse()
    def test_monitor_log_analytics_workspace_default(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20)
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name} --tags clitest=myron", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 30),
            self.check('sku.name', 'pergb2018')
        ])

        self.cmd("monitor log-analytics workspace update -g {rg} -n {name} --retention-time 100", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 100)
        ])

        self.cmd("monitor log-analytics workspace show -g {rg} -n {name}", checks=[
            self.check('retentionInDays', 100)
        ])

        self.cmd("monitor log-analytics workspace list-usages -g {rg} -n {name}")
        self.cmd("monitor log-analytics workspace list -g {rg}", checks=[
            self.check('length(@)', 1),
        ])
        self.cmd("monitor log-analytics workspace get-shared-keys -g {rg} -n {name}", checks=[
            self.check("contains(keys(@), 'primarySharedKey')", True),
            self.check("contains(keys(@), 'secondarySharedKey')", True)
        ])

        self.cmd("monitor log-analytics workspace get-schema -g {rg} -n {name}", checks=[
            self.check('__metadata.resultType', 'schema')
        ])

        self.cmd("monitor log-analytics workspace pack enable -g {rg} --workspace-name {name} -n AzureSecurityOfThings")
        self.cmd("monitor log-analytics workspace pack list -g {rg} --workspace-name {name}", checks=[
            self.check("@[?name=='AzureSecurityOfThings'].enabled", '[True]')
        ])

        self.cmd(
            "monitor log-analytics workspace pack disable -g {rg} --workspace-name {name} -n AzureSecurityOfThings")
        self.cmd("monitor log-analytics workspace pack list -g {rg} --workspace-name {name}", checks=[
            self.check("@[?name=='AzureSecurityOfThings'].enabled", '[False]')
        ])

        self.cmd("monitor log-analytics workspace delete -g {rg} -n {name}")

    @record_only()
    def test_monitor_log_analytics_workspace_linked_service_common_scenario(self):
        cluster_resource_id_1 = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/azure-cli-test' \
                                '-scus/providers/Microsoft.OperationalInsights/clusters/yu-test-cluster1'
        recorded_cluster_resource_id_1 = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/azure' \
                                         '-cli-test-scus/providers/Microsoft.OperationalInsights/clusters/yu-test' \
                                         '-cluster1'
        cluster_resource_id_2 = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/azure-cli-test' \
                                '-scus/providers/Microsoft.OperationalInsights/clusters/yu-test-cluster2'
        recorded_cluster_resource_id_2 = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/azure' \
                                         '-cli-test-scus/providers/Microsoft.OperationalInsights/clusters/yu-test' \
                                         '-cluster2'
        linked_service_name = 'cluster'

        self.kwargs.update({
            'rg': 'azure-cli-test-scus',
            'workspace_name': 'yu-test-ws1',
            'linked_service_name': linked_service_name,
            'cluster_resource_id_1': cluster_resource_id_1,
            'cluster_resource_id_2': cluster_resource_id_2
        })

        self.cmd("monitor log-analytics workspace linked-service create -g {rg} --workspace-name {workspace_name} "
                 "-n {linked_service_name} --write-access-resource-id {cluster_resource_id_1}",
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('writeAccessResourceId', recorded_cluster_resource_id_1)
                 ])

        self.cmd("monitor log-analytics workspace linked-service update -g {rg} --workspace-name {workspace_name} "
                 "-n {linked_service_name} --write-access-resource-id {cluster_resource_id_2}",
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('writeAccessResourceId', recorded_cluster_resource_id_2)
                 ])

        self.cmd("monitor log-analytics workspace linked-service show -g {rg} --workspace-name {workspace_name} "
                 "-n {linked_service_name}",
                 checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('writeAccessResourceId', recorded_cluster_resource_id_2)
                 ])

        self.cmd("monitor log-analytics workspace linked-service list -g {rg} --workspace-name {workspace_name}",
                 checks=[self.check('length(@)', 1)])

        self.cmd("monitor log-analytics workspace linked-service delete -g {rg} --workspace-name {workspace_name} "
                 "-n {linked_service_name} -y", checks=[])

        self.cmd("monitor log-analytics workspace linked-service list -g {rg} --workspace-name {workspace_name}",
                 checks=[self.check('length(@)', 0)])
