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
        self.cmd("monitor log-profiles create --categories 'Write' --enabled false --days 1095 --location southcentralus --locations westus southcentralus --name {name} --storage-account-id {storage}", checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('serviceBusRuleId', None),
            self.check('retentionPolicy.enabled', 'False')
        ])
        self.cmd("monitor log-profiles delete -n {name}")
