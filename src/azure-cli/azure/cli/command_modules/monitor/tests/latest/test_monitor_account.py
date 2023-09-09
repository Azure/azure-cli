# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class TestAccountScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_account')
    def test_monitor_account(self, resource_group):
        self.kwargs.update({
            'account': self.create_random_name('ac', 10)
        })
        self.cmd('monitor account create -n {account} -g {rg}', checks=[
            self.check('name', '{account}'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('monitor account update -n {account} -g {rg} --tags {{tag:test,tag2:test2}}', checks=[
            self.check('name', '{account}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags.tag', 'test'),
            self.check('tags.tag2', 'test2')
        ])
        self.cmd('monitor account show -n {account} -g {rg}', checks=[
            self.check('name', '{account}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags.tag', 'test'),
            self.check('tags.tag2', 'test2')
        ])
        self.cmd('monitor account list -g {rg}', checks=[
            self.check('[0].name', '{account}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].tags.tag', 'test'),
            self.check('[0].tags.tag2', 'test2')
        ])
