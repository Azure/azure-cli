# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, record_only, StorageAccountPreparer
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


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

        # test list-management-groups
        self.cmd("monitor log-analytics workspace list-management-groups -g {rg} -n {name}", checks=[
            self.check('length(@)', 0)
        ])

        self.cmd("monitor log-analytics workspace delete -g {rg} -n {name} -y")

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

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_linked_storage', location='eastus')
    @AllowLargeResponse()
    @StorageAccountPreparer(name_prefix='saws1', kind='StorageV2', sku='Standard_LRS', parameter_name='account_1',
                            location='eastus')
    @StorageAccountPreparer(name_prefix='saws2', kind='StorageV2', sku='Standard_LRS', parameter_name='account_2',
                            location='eastus')
    @StorageAccountPreparer(name_prefix='saws3', kind='StorageV2', sku='Standard_LRS', parameter_name='account_3',
                            location='eastus')
    @StorageAccountPreparer(name_prefix='saws4', kind='StorageV2', sku='Standard_LRS', parameter_name='account_4',
                            location='eastus')
    def test_monitor_log_analytics_workspace_linked_storage(self, resource_group, account_1,
                                                            account_2, account_3, account_4):
        from msrestazure.tools import resource_id
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20),
            'name_2': self.create_random_name('clitest', 20),
            'rg': resource_group,
            'sa_1': account_1,
            'sa_2': account_2,
            'sa_3': account_3,
            'sa_4': account_4,
            'sa_id_1': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=account_1,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'sa_id_2': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=account_2,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'sa_id_3': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=account_3,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'sa_id_4': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=account_4,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name} --tags clitest=myron", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 30),
            self.check('sku.name', 'pergb2018')
        ])

        self.cmd('monitor log-analytics workspace linked-storage create '
                 '--type CustomLogs -g {rg} -n {name} --storage-accounts {sa_1}',
                 checks=[
                     self.check('storageAccountIds[0]', '{sa_id_1}'),
                     self.check('name', 'customlogs')
                 ])

        self.cmd('monitor log-analytics workspace linked-storage add '
                 '--type CustomLogs -g {rg} -n {name} --storage-accounts {sa_2} {sa_id_3}',
                 checks=[
                     self.check('storageAccountIds[0]', '{sa_id_1}'),
                     self.check('storageAccountIds[1]', '{sa_id_2}'),
                     self.check('storageAccountIds[2]', '{sa_id_3}')
                 ])

        self.cmd('monitor log-analytics workspace linked-storage remove '
                 '--type CustomLogs -g {rg} -n {name} --storage-accounts {sa_1}',
                 checks=[
                     self.check('storageAccountIds[0]', '{sa_id_2}'),
                     self.check('storageAccountIds[1]', '{sa_id_3}')
                 ])

        self.cmd('monitor log-analytics workspace linked-storage show '
                 '--type CustomLogs -g {rg} -n {name}',
                 checks=[
                     self.check('storageAccountIds[0]', '{sa_id_2}'),
                     self.check('storageAccountIds[1]', '{sa_id_3}')
                 ])

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name_2} --tags clitest=myron", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 30),
            self.check('sku.name', 'pergb2018')
        ])

        self.cmd('monitor log-analytics workspace linked-storage create '
                 '--type AzureWatson -g {rg} -n {name} --storage-accounts {sa_1}',
                 checks=[
                     self.check('storageAccountIds[0]', '{sa_id_1}'),
                     self.check('name', 'azurewatson')
                 ])

        self.cmd('monitor log-analytics workspace linked-storage list '
                 '-g {rg} -n {name}',
                 checks=[
                     self.check('length(@)', 2)
                 ])

        self.cmd('monitor log-analytics workspace linked-storage delete '
                 '--type AzureWatson -g {rg} -n {name} -y')

        self.cmd('monitor log-analytics workspace linked-storage list '
                 '-g {rg} -n {name}',
                 checks=[
                     self.check('length(@)', 1)
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_public_access', location='eastus')
    def test_monitor_log_analytics_workspace_public_access(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20),
            'name_2': self.create_random_name('clitest', 20)
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name} --tags clitest=myron "
                 "--query-access Disabled --ingestion-access Disabled",
                 checks=[
                     self.check('publicNetworkAccessForIngestion', 'Disabled'),
                     self.check('publicNetworkAccessForQuery', 'Disabled')
                 ])

        self.cmd("monitor log-analytics workspace update -g {rg} -n {name} "
                 "--query-access Disabled --ingestion-access Enabled",
                 checks=[
                     self.check('publicNetworkAccessForIngestion', 'Enabled'),
                     self.check('publicNetworkAccessForQuery', 'Disabled')
                 ])

        self.cmd("monitor log-analytics workspace show -g {rg} -n {name}", checks=[
            self.check('publicNetworkAccessForIngestion', 'Enabled'),
            self.check('publicNetworkAccessForQuery', 'Disabled')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_recover', location='WestEurope')
    @AllowLargeResponse()
    def test_monitor_log_analytics_workspace_recover(self, resource_group):
        workspace_name = self.create_random_name('clitest', 20)
        self.kwargs.update({
            'name': workspace_name
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name} --quota 1 --level 100 --sku CapacityReservation", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 30),
            self.check('sku.name', 'capacityreservation'),
            self.check('sku.capacityReservationLevel', 100),
            self.check('workspaceCapping.dailyQuotaGb', 1.0)
        ])

        self.cmd("monitor log-analytics workspace update -g {rg} -n {name} --quota 2 --level 200", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.capacityReservationLevel', 200),
            self.check('workspaceCapping.dailyQuotaGb', 2.0)
        ])

        self.kwargs.update({
            'table_name': 'Syslog'
        })

        self.cmd("monitor log-analytics workspace table update -g {rg} --workspace-name {name} -n {table_name} --retention-time 30 --debug", checks=[
            self.check('retentionInDays', 30)
        ])

        # not supported in api_version = 2021-12-01-preview
        # self.cmd("monitor log-analytics workspace list-deleted-workspaces -g {rg}", checks=[
        #     self.check('length(@)', 0)
        # ])

        self.cmd("monitor log-analytics workspace delete -g {rg} -n {name} -y")

        # not supported in api_version = 2021-12-01-preview
        # self.cmd("monitor log-analytics workspace list-deleted-workspaces -g {rg}", checks=[
        #     self.check('length(@)', 1)
        # ])

        # self.cmd("monitor log-analytics workspace recover -g {rg} -n {name}", checks=[
        #     self.check('provisioningState', 'Succeeded'),
        #     self.check('retentionInDays', 30),
        #     self.check('sku.name', 'capacityreservation'),
        #     self.check('sku.capacityReservationLevel', 200),
        #     self.check('workspaceCapping.dailyQuotaGb', 2.0)
        # ])

        # self.cmd("monitor log-analytics workspace show -g {rg} -n {name}", checks=[
        #     self.check('provisioningState', 'Succeeded'),
        #     self.check('retentionInDays', 30),
        #     self.check('sku.name', 'capacityreservation'),
        #     self.check('sku.capacityReservationLevel', 200),
        #     self.check('workspaceCapping.dailyQuotaGb', 2.0)
        # ])

        # self.cmd("monitor log-analytics workspace list-deleted-workspaces -g {rg}", checks=[
        #     self.check('length(@)', 0)
        # ])

        self.cmd("monitor log-analytics workspace delete -g {rg} -n {name} --force -y")

        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('monitor log-analytics workspace show -g {rg} -n {name}')

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_saved_search', location='eastus')
    def test_monitor_log_analytics_workspace_saved_search(self, resource_group):
        self.kwargs.update({
            'workspace_name': self.create_random_name('clitest', 20),
            'saved_search_name': 'clitest',
            'category': 'cli',
            'category_2': 'cli2',
            'query': "Heartbeat | getschema",
            'query_2': "AzureActivity | summarize count() by bin(TimeGenerated, 1h)",
            'display_name': 'myclitest',
            'display_name_2': 'myclitest2',
            'function_alias': 'myfun',
            'function_param': "a:string = value",
            'function_alias_2': 'myfun2',
            'function_param_2': "a2:string = value",
            'rg': resource_group
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {workspace_name} --tags clitest=myron")

        # Disable checks due to service issue: https://github.com/Azure/azure-rest-api-specs/issues/12363, will enable checks after service issue is fixed.
        self.cmd('monitor log-analytics workspace saved-search create -g {rg} --workspace-name {workspace_name} -n {saved_search_name} '
                 '--category {category} --display-name {display_name} -q "{query}" --fa {function_alias} '
                 '--fp "{function_param}" --tags a=b c=d',
                 checks=[
                     # self.check('category', '{category}'),
                     # self.check('displayName', '{display_name}'),
                     # self.check('query', "{query}"),
                     # self.check('functionAlias', '{function_alias}'),
                     # self.check('functionParameters', '{function_param}'),
                     # self.check('length(tags)', 2)
                 ])


        self.cmd('monitor log-analytics workspace saved-search show -g {rg} --workspace-name {workspace_name} -n {saved_search_name}', checks=[
            # self.check('category', '{category}'),
            # self.check('displayName', '{display_name}'),
            # self.check('query', "Heartbeat | getschema"),
            # self.check('functionAlias', '{function_alias}'),
            # self.check('functionParameters', '{function_param}'),
            # self.check('length(tags)', 2)
        ])
        self.cmd('monitor log-analytics workspace saved-search list -g {rg} --workspace-name {workspace_name}', checks=[
            self.check('length(@)', 1)
        ])

        self.cmd(
            'monitor log-analytics workspace saved-search update -g {rg} --workspace-name {workspace_name} -n {saved_search_name} '
            '--category {category_2} --display-name {display_name_2} -q "{query_2}" --fa {function_alias_2} '
            '--fp "{function_param_2}" --tags a=c f=e',
            checks=[
                # self.check('category', '{category_2}'),
                # self.check('displayName', '{display_name_2}'),
                # self.check('query', "{query_2}"),
                # self.check('functionAlias', '{function_alias_2}'),
                # self.check('functionParameters', '{function_param_2}'),
                # self.check('length(tags)', 2),
                # self.check('tags[0].value', 'c'),
                # self.check('tags[1].value', 'e')
            ])

        self.cmd('monitor log-analytics workspace saved-search delete -g {rg} --workspace-name {workspace_name} -n {saved_search_name} -y')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('monitor log-analytics workspace saved-search show -g {rg} --workspace-name {workspace_name} -n {saved_search_name}')

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_data_export', location='eastus')
    @StorageAccountPreparer(name_prefix='saws1', kind='StorageV2', sku='Standard_LRS', parameter_name='account_1',
                            location='eastus')
    def test_monitor_log_analytics_workspace_data_export(self, resource_group, account_1):
        from msrestazure.tools import resource_id
        self.kwargs.update({
            'workspace_name': self.create_random_name('clitest', 20),
            'data_export_name': 'clitest',
            'data_export_name_2': 'clitest2',
            'sa_1': account_1,
            'sa_id_1': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=account_1,
                namespace='Microsoft.Storage',
                type='storageAccounts'),
            'namespacename': self.create_random_name(prefix='eventhubs-nscli', length=20),
            'eventhubname': "hub_name",
            'rg': resource_group
        })

        self.cmd(
            "monitor log-analytics workspace create -g {rg} -n {workspace_name} --quota 1 --level 100 --sku CapacityReservation",
            checks=[
                self.check('provisioningState', 'Succeeded'),
                self.check('retentionInDays', 30),
                self.check('sku.name', 'capacityreservation'),
                self.check('sku.capacityReservationLevel', 100),
                self.check('workspaceCapping.dailyQuotaGb', 1.0)
            ])
        self.kwargs.update({
            'table_name': 'Syslog'
        })

        self.cmd('monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name} '
                 '--destination {sa_id_1} --enable -t {table_name}',
                 checks=[
                 ])

        from azure.core.exceptions import HttpResponseError
        with self.assertRaisesRegex(HttpResponseError, 'Table SecurityEvent Heartbeat does not exist in the workspace'):
            self.cmd('monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name_2} '
                     '--destination {sa_id_1} --enable -t "SecurityEvent Heartbeat"',
                     checks=[
                     ])
        with self.assertRaisesRegex(HttpResponseError, 'You are adding a destination that is already defined in rule: clitest. Destination must be unique across export rules in your workspace . See http://aka.ms/LADataExport#limitations'):
            self.cmd('monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name_2} '
                     '--destination {sa_id_1} --enable -t {table_name}',
                     checks=[
                     ])
        with self.assertRaisesRegex(HttpResponseError, 'Table ABC does not exist in the workspace'):
            self.cmd('monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name_2} '
                     '--destination {sa_id_1} --enable -t ABC',
                     checks=[
                     ])
        with self.assertRaisesRegex(HttpResponseError,'You are adding a destination that is already defined in rule: clitest. Destination must be unique across export rules in your workspace . See http://aka.ms/LADataExport#limitations'):
            self.cmd('monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name_2} '
                     '--destination {sa_id_1} --enable -t AppPerformanceCounters',
                     checks=[
                     ])
        self.cmd('monitor log-analytics workspace data-export show -g {rg} --workspace-name {workspace_name} -n {data_export_name}', checks=[
        ])

        self.cmd('monitor log-analytics workspace data-export list -g {rg} --workspace-name {workspace_name}', checks=[
            self.check('length(@)', 1)
        ])

        result = self.cmd('eventhubs namespace create --resource-group {rg} --name {namespacename}').get_output_in_json()
        self.kwargs.update({
            'namespace_id': result['id']
        })
        result = self.cmd('eventhubs eventhub create --resource-group {rg} --namespace-name {namespacename} --name {eventhubname}').get_output_in_json()
        self.kwargs.update({
            'eventhub_id': result['id']
        })
        self.cmd(
            'monitor log-analytics workspace data-export update -g {rg} --workspace-name {workspace_name} -n {data_export_name} '
            '--destination {namespace_id} --enable true -t Usage Alert',
            checks=[
            ])

        self.cmd('eventhubs eventhub list -g {rg} --namespace-name {namespacename}')

        self.cmd('monitor log-analytics workspace data-export delete -g {rg} --workspace-name {workspace_name} -n {data_export_name} -y')

        self.cmd(
            'monitor log-analytics workspace data-export create -g {rg} --workspace-name {workspace_name} -n {data_export_name} '
            '--destination {eventhub_id} --enable false -t {table_name}',
            checks=[
            ])

        self.cmd('monitor log-analytics workspace data-export delete -g {rg} --workspace-name {workspace_name} -n {data_export_name} -y')
        with self.assertRaisesRegex(SystemExit, '3'):
            self.cmd('monitor log-analytics workspace data-export show -g {rg} --workspace-name {workspace_name} -n {data_export_name}')

    @record_only()
    def test_monitor_log_analytics_workspace_data_collection_rules(self):
        self.kwargs.update({
            'ws_name': 'wsn1',
            'rule_name': 'rule11',
            'rule_id': '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/tbtest/providers/Microsoft.Insights/dataCollectionRules/rule11'
        })
        # extension command
        # rule = self.cmd('monitor data-collection rule show -g tbtest -n rule11').get_output_in_json()
        # self.kwargs.update({
        #     'rule_id': rule['id']
        # })
        self.cmd('monitor log-analytics workspace update -g tbtest -n {ws_name} --data-collection-rule {rule_id}', checks=[
            # self.check('defaultDataCollectionRuleResourceId', '{rule_id}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace_table', location='WestEurope')
    @AllowLargeResponse()
    def test_monitor_log_analytics_workspace_table(self, resource_group):

        self.kwargs.update({
            'ws_name':self.create_random_name('ws-', 10),
            'table_name': self.create_random_name('TB', 10) + '_CL',
            'table2_name': self.create_random_name('TB', 10) + '_SRCH',
            'table3_name': self.create_random_name('TB', 10) +'RST'

        })

        self.cmd('monitor log-analytics workspace create -g {rg} -n {ws_name}')
        self.cmd('monitor log-analytics workspace table create -g {rg} -n {table_name} --workspace-name {ws_name} --retention-time 45 --total-retention-time 70 --plan Analytics --columns col1=guid TimeGenerated=datetime', checks=[
            self.check('name', '{table_name}'),
            self.check('retentionInDays', 45),
            self.check('totalRetentionInDays', 70),
            self.check('schema.columns[0].name', 'col1'),
            self.check('schema.columns[0].type', 'guid'),
            self.check('schema.columns[1].name', 'TimeGenerated'),
            self.check('schema.columns[1].type', 'datetime'),
        ])
        self.cmd('monitor log-analytics workspace table update -g {rg} -n {table_name} --workspace-name {ws_name} --retention-time 50 --total-retention-time 80 --columns col2=guid', checks=[
            self.check('name', '{table_name}'),
            self.check('retentionInDays', 50),
            self.check('totalRetentionInDays', 80),
            self.check('schema.columns[0].name', 'col2'),
            self.check('schema.columns[0].type', 'guid'),
        ])
        self.cmd('monitor log-analytics workspace table show -g {rg} -n {table_name} --workspace-name {ws_name}', checks=[
            self.check('name', '{table_name}'),
            self.check('retentionInDays', 50),
            self.check('totalRetentionInDays', 80),
        ])

        self.cmd('monitor log-analytics workspace table delete -g {rg} -n {table_name} --workspace-name {ws_name} -y')

        # self.cmd('monitor log-analytics workspace table create -g {rg} -n {table2_name} --workspace-name {ws_name} --search "Heartbeat | where SourceSystem != '' | project SourceSystem" --limit 1000 --start-search-time "2021-08-01 05:29:18" --end-search-time "2021-08-02 05:29:18" --description "a test table"', checks=[
        #     self.check('name', '{table_name}'),
        #     self.check('searchResults.query', 'Heartbeat | where SourceSystem != '' | project SourceSystem'),
        #     self.check('searchResults.limit', 1000),
        #     self.check('searchResults.sourceTable', "Heartbeat"),
        #     self.check('searchResults.type', 'datetime'),
        # ])

        # self.cmd('monitor log-analytics workspace table create -g {rg} -n {table3_name} --workspace-name {ws_name} --start-restore-time "2021-08-01 05:29:18" --end-restore-time "2021-08-02 05:29:18"', checks=[
        #     self.check('name', '{table_name}'),
        #     self.check('restoredLogs.startRestoreTime', ''),
        #     self.check('restoredLogs.endRestoreTime', ''),
        # ])
