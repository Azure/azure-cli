# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, JMESPathCheck


class TestMonitorMetrics(ScenarioTest):

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_monitor_metrics_scenario(self, resource_group, storage_account):
        from azure.mgmt.core.tools import resource_id
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

    @ResourceGroupPreparer(location='westus')
    def test_monitor_metrics_list_by_sub(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'vm': "vm1",
            "location": "westus",
        })
        vm_json = self.cmd('vm create -g {rg} -n {vm} --image Ubuntu2204 --admin-password TestPassword11!! --admin-username testadmin --authentication-type password').get_output_in_json()
        self.kwargs['vm_id'] = vm_json['id']
        self.kwargs['namespace'] = self.cmd('az monitor metrics list-namespaces --resource {vm_id}').get_output_in_json()[0]['properties']['metricNamespaceName']
        self.cmd('az monitor metrics list-sub-definitions --region {location} --metricnamespace {namespace}')
        self.cmd('az monitor metrics list-sub --region {location} --metricnamespace {namespace} --metricnames "Data Disk Max Burst IOPS" ',
                 checks=[
                     JMESPathCheck('resourceregion', self.kwargs["location"]),
                     JMESPathCheck('namespace', self.kwargs["namespace"]),
                 ])
