# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from azure.cli.testsdk import ScenarioTest, JMESPathCheck, ResourceGroupPreparer, StorageAccountPreparer
from azure.core.exceptions import HttpResponseError

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
            self.check('length(@)', 1),
            self.check('[0].name', 'test01')
        ])

        self.cmd('monitor diagnostic-settings show -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json',
                 checks=self.check('name', 'test01'))

        self.cmd('monitor diagnostic-settings delete -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json')

        self.cmd('monitor diagnostic-settings list --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} -o json',
                 checks=self.check('length(@)', 0))

        self.cmd('monitor diagnostic-settings create -n test02 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} --workspace {ws} --export-to-resource-specific --logs \'{log_config}\' -o json',
                 checks=[
                     self.check('name', 'test02'),
                     self.check('logAnalyticsDestinationType', 'Dedicated')
                 ])

    @ResourceGroupPreparer(location='southcentralus')
    def test_monitor_diagnostic_settings_marketplace_id(self, resource_group):
        self.kwargs.update({
            'nsg': self.create_random_name(prefix='nsg', length=16),
            'ws': self.create_random_name(prefix='ws', length=16),
            'sa': self.create_random_name(prefix='sa', length=16),
            'vm1': 'vm1',
            'vmss': 'vmss1'
        })
        self.cmd('network nsg create -n {nsg} -g {rg}')

        #self.kwargs['mp_id'] = self.cmd('network nsg show -n {nsg} -g {rg}').get_output_in_json()['id']
        #self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username testadmin --admin-password TestTest12#$')
        #self.kwargs['mp_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']
        # self.kwargs['mp_id'] = self.cmd('vm create -g {rg} -n {vm1} --image UbuntuLTS --admin-password TestPassword11!! '
        #                     '--admin-username testadmin --authentication-type password').get_output_in_json()['id']

        self.cmd('monitor log-analytics workspace create -g {rg} -n {ws}')
        #self.kwargs['mp_id'] = self.cmd('monitor log-analytics workspace show -g {rg} -n {ws}').get_output_in_json()['id']
        #self.kwargs['mp_id'] = self.cmd('az storage account create -n {sa} -g {rg} -l westus --sku Standard_LRS --kind Storage --https-only').get_output_in_json()['id']
        self.cmd('az storage account create -n {sa} -g {rg} -l westus --sku Standard_LRS --kind Storage --https-only')
        self.kwargs['mp_id'] = "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/test-rg/providers/Microsoft.Datadog/monitors/dd1"

        self.kwargs['log_config'] = json.dumps([
            {
                "category": "NetworkSecurityGroupEvent",
                "enabled": True,
                "retention-policy": {"days": 0, "enabled": False}
            },
            {
                "category": "NetworkSecurityGroupRuleCounter",
                "enabled": True,
                "retention-policy": {"days": 0, "enabled": False}
            }
        ])
        with self.assertRaisesRegex(HttpResponseError, '/resourcegroups/test-rg/providers/microsoft.datadog/monitors/dd1 was not '
                                                       'found or does not support the required functionality.'):
            self.cmd('monitor diagnostic-settings create -n test01 --resource {nsg} --resource-type Microsoft.Network/networkSecurityGroups --resource-group {rg} --storage-account {sa} --marketplace-partner-id {mp_id} --logs \'{log_config}\' -o json')



if __name__ == '__main__':
    import unittest

    unittest.main()
