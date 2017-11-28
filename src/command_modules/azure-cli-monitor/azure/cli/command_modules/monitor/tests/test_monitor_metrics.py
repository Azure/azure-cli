# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestMonitorMetrics(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer()
    def test_monitor_metrics(self, resource_group, storage_account):
        resource_id = self.cmd(
            'az storage account show -n {} -g {} --query id -otsv'.format(storage_account, resource_group)).output

        self.cmd('az monitor metrics list-definitions --resource {}'.format(resource_id))
