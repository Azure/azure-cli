# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestMonitorMetrics(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_monitor_metrics_scenario(self, resource_group, storage_account):
        self.kwargs.update({})
        self.kwargs['sa_id'] = self.cmd('az storage account show -n {sa} -g {rg}').get_output_in_json()['id']
        self.cmd('az monitor metrics list-definitions --resource {sa_id} --namespace Microsoft.Storage/storageAccounts')
        self.cmd('az monitor metrics list --resource {sa_id} --namespace Microsoft.Storage/storageAccounts --metrics "Ingress" "Egress" --start-time 2018-01-01T00:00:00Z --end-time 2999-01-01T00:00:00Z',
                 checks=self.check('length(@.value)', 2))
