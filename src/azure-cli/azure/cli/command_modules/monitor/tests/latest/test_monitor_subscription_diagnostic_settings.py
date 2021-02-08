# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer
import json


class TestDiagnosticSettingsSubscriptionScenarios(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_diagnostic_settings_subscription(self, resource_group, storage_account):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20),
            'ws': self.create_random_name('cliws', 20)
        })
        self.kwargs['storage'] = self.cmd('storage account show -n {sa} -g {rg} --query id -otsv').output.strip()
        self.kwargs['log_config'] = json.dumps([
            {
                "category": "Security",
                "enabled": True,
            },
            {
                "category": "Administrative",
                "enabled": True,
            },
            {
                "category": "ServiceHealth",
                "enabled": True,
            },
            {
                "category": "Alert",
                "enabled": True,
            },
            {
                "category": "Recommendation",
                "enabled": True,
            },
            {
                "category": "Policy",
                "enabled": True,
            },
            {
                "category": "Autoscale",
                "enabled": True,
            },
            {
                "category": "ResourceHealth",
                "enabled": True,
            }
        ])
        diagns = self.cmd("monitor diagnostic-settings subscription list").get_output_in_json()['value']
        for diagn in diagns:
            name = diagn['name']
            self.cmd("monitor diagnostic-settings subscription delete --name {} -y".format(name))
        self.cmd("monitor diagnostic-settings subscription create -l southcentralus --name {name} --storage-account {storage} "
                 "--logs \'{log_config}\'",
                 checks=[
                     self.check('storageAccountId', '{storage}'),
                     self.check('serviceBusRuleId', None),
                 ])
        self.cmd("monitor diagnostic-settings subscription show --name {name}", checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('serviceBusRuleId', None),
        ])
        self.cmd("monitor diagnostic-settings subscription list", checks=[
            self.check('length(@)', 1)
        ])
        self.kwargs['ws_id'] = self.cmd('monitor log-analytics workspace create -n {ws} -g {rg} --query id -otsv').output.strip()
        self.cmd('monitor diagnostic-settings subscription update --name {name} --workspace {ws_id}', checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('workspaceId', '{ws_id}')
        ])
        self.cmd("monitor diagnostic-settings subscription delete --name {name} -y")
