# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestMonitorMetrics(ScenarioTest):

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_monitor_metrics_scenario(self, resource_group, storage_account):
        from msrestazure.tools import resource_id
        self.kwargs.update({
            'sa_id': resource_id(
                resource_group=resource_group,
                subscription=self.get_subscription_id(),
                name=storage_account,
                namespace='Microsoft.Storage',
                type='storageAccounts')
        })
        self.kwargs['namespace'] = self.cmd('az monitor metrics list-namespaces --resource {sa_id}').get_output_in_json()[0]['properties']['metricNamespaceName']
        self.cmd('az monitor metrics list-definitions --resource {sa_id} --namespace {namespace}')
        self.cmd('az monitor metrics list --resource {sa_id} --namespace {namespace} --metrics Ingress Egress --start-time 2018-01-01T00:00:00Z --end-time 2999-01-01T00:00:00Z',
                 checks=self.check('length(@.value)', 2))
        self.cmd('az monitor metrics list --resource {sa_id} --metrics Ingress Egress --start-time 2018-01-01 00:00:00 +00:00 --offset 5000d',
                 checks=self.check('length(@.value)', 2))
        self.cmd('az monitor metrics list --resource {sa_id} --metrics Ingress Egress --end-time 2025-01-01 00:00:00 +00:00 --offset 5000d',
                 checks=self.check('length(@.value)', 2))
