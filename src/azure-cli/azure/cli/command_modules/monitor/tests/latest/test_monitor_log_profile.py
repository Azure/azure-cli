# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer


class TestLogProfileScenarios(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_lp_create', location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    def test_monitor_create_log_profile(self, resource_group, storage_account):

        log_id = self.cmd("monitor log-profiles list --query [0].name -o tsv").output.strip()
        if log_id:
            self.kwargs.update({
                'log_id': log_id
            })
            self.cmd('monitor log-profiles delete -n "{log_id}"')
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20),

        })
        self.kwargs['storage'] = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Storage/storageAccounts/{}'\
            .format(self.get_subscription_id(), resource_group, storage_account)
        self.cmd("monitor log-profiles create --categories 'Write' --enabled false --days 100 --location southcentralus --locations westus southcentralus --name {name} --storage-account-id {storage}", checks=[
            self.check('storageAccountId', '{storage}'),
            self.check('serviceBusRuleId', None),
            self.check('retentionPolicy.enabled', 'False')
        ])

        time.sleep(2)
        # test monitor log-profiles show
        self.cmd("monitor log-profiles show -n {name}", checks=[
            self.check('storageAccountId', '{storage}')
        ])

        # test monitor log-profiles update
        self.cmd("monitor log-profiles update -n {name} --set location=southcentralus retentionPolicy.enabled=True",
                 checks=[
                     self.check('retentionPolicy.enabled', 'True')
                 ])

        self.cmd("monitor log-profiles delete -n {name}")
