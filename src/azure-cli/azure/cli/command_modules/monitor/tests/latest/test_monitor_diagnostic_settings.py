# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer


class TestMonitorDiagnosticSettings(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_diagnostic_settings_scenario(self, resource_group, storage_account):

        self.kwargs.update({
            'nsg': self.create_random_name(prefix='nsg', length=16),
            'ws': self.create_random_name(prefix='ws', length=16)
        })
        self.cmd('network nsg create -n {nsg} -g {rg}')
        self.cmd('monitor log-analytics workspace create -g {rg} -n {ws}')

        self.cmd('monitor diagnostic-settings categories list -g {rg} --resource-type Microsoft.Network/networkSecurityGroups --resource {nsg}', checks=[
            self.check('length(value)', 2)
        ])

        # test diagnostic-settings categories show
        self.cmd(
            'monitor diagnostic-settings categories show -n NetworkSecurityGroupEvent -g {rg} --resource-type Microsoft.Network/networkSecurityGroups --resource {nsg}',
            checks=[
                self.check('categoryType', 'Logs')
            ])

        self.kwargs['log_config'] = json.dumps([
            {
                "category": "NetworkSecurityGroupEvent",
                "enabled": True,
                "retentionPolicy": {"days": 0, "enabled": False}
            },
            {
                "category": "NetworkSecurityGroupRuleCounter",
                "enabled": True,
                "retentionPolicy": {"days": 0, "enabled": False}
            }
        ])

        self.cmd('monitor diagnostic-settings create -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} --storage-account {sa} --logs \'{log_config}\' -o json',
                 checks=self.check('name', 'test01'))

        self.cmd('monitor diagnostic-settings list --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json', checks=[
            self.check('length(value)', 1),
            self.check('value[0].name', 'test01')
        ])

        self.cmd('monitor diagnostic-settings show -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json',
                 checks=self.check('name', 'test01'))

        self.cmd('monitor diagnostic-settings delete -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json')

        self.cmd('monitor diagnostic-settings list --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json',
                 checks=self.check('length(value)', 0))

        self.cmd('monitor diagnostic-settings create -n test02 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} --workspace {ws} --export-to-resource-specific --logs \'{log_config}\' -o json',
                 checks=[
                     self.check('name', 'test02'),
                     self.check('logAnalyticsDestinationType', 'Dedicated')
                 ])


if __name__ == '__main__':
    import unittest

    unittest.main()
