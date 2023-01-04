# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, record_only, ResourceGroupPreparer


class TestLogAnalyticsQueryPackScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_log_analytics_query_pack_crud', location="eastus2")
    def test_log_analytics_query_pack_crud(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'name': self.create_random_name('clitest', 20),
        })

        response = self.cmd('monitor log-analytics query-pack create -g {rg} -n {name} -l eastus2', checks=[
            self.check('name', "{name}"),
        ]).get_output_in_json()
        self.kwargs['id'] = response['id']

        self.cmd('monitor log-analytics query-pack show -g {rg} -n {name}', checks=[
            self.check('name', "{name}")
        ])

        self.cmd('monitor log-analytics query-pack show --ids {id}', checks=[
            self.check('name', "{name}")
        ])

        self.cmd("monitor log-analytics query-pack update -g {rg} -n {name} --tags flag1=v1", checks=[
            self.check('tags.flag1', 'v1')
        ])

        self.cmd("monitor log-analytics query-pack list", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("monitor log-analytics query-pack list -g {rg}", checks=[
            self.check('length(@)', 1)
        ])

        self.cmd("monitor log-analytics query-pack delete -g {rg} -n {name} --yes")

        self.cmd("monitor log-analytics query-pack list -g {rg}", checks=[
            self.check('length(@)', 0)
        ])

    @ResourceGroupPreparer(name_prefix='test_log_analytics_query_pack_query_crud', location="eastus2")
    def test_log_analytics_query_pack_query_crud(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'pack_name': self.create_random_name('clitest', 20),
            'query_id': '5865fd70-3d2c-4c83-9423-7d204c3b3f90'
        })

        response = self.cmd('monitor log-analytics query-pack create -g {rg} -n {pack_name} -l eastus2', checks=[
            self.check('name', "{pack_name}"),
        ]).get_output_in_json()
        self.kwargs['pack_id'] = response['id']

        response = self.cmd('monitor log-analytics query-pack query create --query-id {query_id} -g {rg} '
                            '--query-pack-name {pack_name} --display-name query-test '
                            '--body "let newExceptionsTimeRange = 1d;let timeRangeToCheckBefore = 7d;exceptions | where timestamp < ago(timeRangeToCheckBefore) | summarize count() by problemId | join kind= rightanti (exceptions | where timestamp >= ago(newExceptionsTimeRange) | extend stack = tostring(details[0].rawStack) | summarize count(), dcount(user_AuthenticatedId), min(timestamp), max(timestamp), any(stack) by problemId) on problemId | order by  count_ desc" '
                            '--description "this is for test" '
                            '--categories "[network,monitor]" '
                            '--resource-types "[microsoft.network/loadbalancers,microsoft.insights/autoscalesettings]" '
                            '--solutions "[networkmonitoring]" '
                            '--tags "{{version:[v2022-01-01,v2021-12-01]}}"', checks=[
            self.check('properties.id', '{query_id}'),
            self.check('properties.related.categories', ['network', 'monitor']),
            self.check('properties.related.resourceTypes', ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('properties.related.solutions', ['networkmonitoring']),
            self.check('properties.tags', {"version": ["v2022-01-01", "v2021-12-01"]}),
        ]).get_output_in_json()
        self.kwargs['id'] = response['id']

        self.cmd('monitor log-analytics query-pack query show --ids {id}', checks=[self.check('properties.id', '{query_id}'),
            self.check('properties.related.categories', ['network', 'monitor']),
            self.check('properties.related.resourceTypes', ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('properties.related.solutions', ['networkmonitoring']),
            self.check('properties.tags', {"version": ["v2022-01-01", "v2021-12-01"]}),
        ])

        self.cmd('monitor log-analytics query-pack query show --query-id {query_id} -g {rg} --query-pack-name {pack_name}', checks=[self.check('properties.id', '{query_id}'),
            self.check('properties.related.categories', ['network', 'monitor']),
            self.check('properties.related.resourceTypes', ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('properties.related.solutions', ['networkmonitoring']),
            self.check('properties.tags', {"version": ["v2022-01-01", "v2021-12-01"]}),
        ])

        self.cmd(
            'monitor log-analytics query-pack query update --query-id {query_id} -g {rg} --body "heartbeat | take 10" --query-pack-name {pack_name} --categories [2]=databases --tags version[0]=null',
            checks=[self.check('properties.id', '{query_id}'),
                    self.check('properties.related.categories', ['network', 'monitor', 'databases']),
                    self.check('properties.related.resourceTypes',
                               ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
                    self.check('properties.related.solutions', ['networkmonitoring']),
                    self.check('properties.tags', {"version": ["v2021-12-01"]}),
                    self.check('properties.body', "heartbeat | take 10")
                    ])

        self.cmd('monitor log-analytics query-pack query list -g {rg} --query-pack-name {pack_name}', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.body', "heartbeat | take 10")
        ])

        self.cmd('monitor log-analytics query-pack query list -g {rg} --query-pack-name {pack_name} --include-body false', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.body', None)
        ])

        self.cmd('monitor log-analytics query-pack query search -g {rg} --query-pack-name {pack_name} '
                 '--categories network', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.id', '{query_id}'),
            self.check('[0].properties.related.categories', ['network', 'monitor', 'databases']),
            self.check('[0].properties.related.resourceTypes',
                       ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('[0].properties.related.solutions', ['networkmonitoring']),
            self.check('[0].properties.tags', {"version": ["v2021-12-01"]}),
            self.check('[0].properties.body', "heartbeat | take 10")
        ])

        self.cmd('monitor log-analytics query-pack query search -g {rg} --query-pack-name {pack_name} '
                 '--resource-types microsoft.insights/autoscalesettings microsoft.network/loadbalancers ', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.id', '{query_id}'),
            self.check('[0].properties.related.categories', ['network', 'monitor', 'databases']),
            self.check('[0].properties.related.resourceTypes',
                       ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('[0].properties.related.solutions', ['networkmonitoring']),
            self.check('[0].properties.tags', {"version": ["v2021-12-01"]}),
            self.check('[0].properties.body', "heartbeat | take 10")
        ])

        self.cmd('monitor log-analytics query-pack query search -g {rg} --query-pack-name {pack_name} '
                 '--solutions "[networkmonitoring]"', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.id', '{query_id}'),
            self.check('[0].properties.related.categories', ['network', 'monitor', 'databases']),
            self.check('[0].properties.related.resourceTypes',
                       ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('[0].properties.related.solutions', ['networkmonitoring']),
            self.check('[0].properties.tags', {"version": ["v2021-12-01"]}),
            self.check('[0].properties.body', "heartbeat | take 10")
        ])

        self.cmd('monitor log-analytics query-pack query search -g {rg} --query-pack-name {pack_name} '
                 '--tags version="[v2021-12-01]"', checks=[
            self.check('length(@)', 1),
            self.check('[0].properties.id', '{query_id}'),
            self.check('[0].properties.related.categories', ['network', 'monitor', 'databases']),
            self.check('[0].properties.related.resourceTypes',
                       ['microsoft.network/loadbalancers', 'microsoft.insights/autoscalesettings']),
            self.check('[0].properties.related.solutions', ['networkmonitoring']),
            self.check('[0].properties.tags', {"version": ["v2021-12-01"]}),
            self.check('[0].properties.body', "heartbeat | take 10")
        ])

        self.cmd('monitor log-analytics query-pack query delete --ids {id} --yes')
        self.cmd('monitor log-analytics query-pack query list -g {rg} --query-pack-name {pack_name}', checks=[
            self.check('length(@)', 0),
        ])
