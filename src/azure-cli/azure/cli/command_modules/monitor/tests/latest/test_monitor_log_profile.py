# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestLogProfileScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_lp_create', location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_create_log_profile(self, resource_group, storage_account):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20)
        })
        self.kwargs['storage'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'\
            .format(self.get_subscription_id(), resource_group, storage_account)
        self.cmd("monitor log-profiles create --categories 'Write' --enabled false --days 1095 --location southcentralus --locations westus southcentralus --name {name} --storage-account-id {storage}", checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('serviceBusRuleId', None),
            self.check('retentionPolicy.enabled', 'False')
        ])
        self.cmd("monitor log-profiles delete -n {name}")
