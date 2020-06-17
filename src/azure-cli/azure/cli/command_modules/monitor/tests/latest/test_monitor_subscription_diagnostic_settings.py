# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestLogProfileScenarios(ScenarioTest):
    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_create_log_profile(self, resource_group, storage_account):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20)
        })
        self.kwargs['storage'] = self.cmd('storage account show -n {sa} -g {rg} --query id -otsv').output.strip()
        self.cmd("monitor diagnostic-settings subscription create --location southcentralus --name {name} --storage-account-id {storage} "
                 "--logs '[{'category': 'Security','enabled': true},{'category': 'Administrative','enabled': true},{'category': 'ServiceHealth','enabled': true},"
                 "{'category': 'Alert','enabled': true},{'category': 'Recommendation','enabled': true},{'category': 'Policy','enabled': true},"
                 "{'category': 'Autoscale','enabled': true},{'category': 'ResourceHealth','enabled': true}]'", checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('serviceBusRuleId', None),
        ])
        self.cmd("monitor diagnostic-settings subscription show --name {name}")
        self.cmd("monitor diagnostic-settings subscription list")
        self.cmd("monitor diagnostic-settings subscription delete --name {name}")
