# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest

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

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_account_np')
    def test_monitor_account_new_params(self, resource_group):
        self.kwargs.update({
            'account': self.create_random_name('ac', 10)
        })
        self.cmd('monitor account create -n {account} -g {rg} '
                 '--enable-access-using-resource-permissions true --public-network-access Disabled', checks=[
            self.check('name', '{account}'),
            self.check('publicNetworkAccess', 'Disabled'),
            self.check('metrics.enableAccessUsingResourcePermissions', True)
        ])
        self.cmd('monitor account update -n {account} -g {rg} '
                 '--enable-access-using-resource-permissions false', checks=[
            self.check('metrics.enableAccessUsingResourcePermissions', False)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_account_id')
    def test_monitor_account_identity(self, resource_group):
        self.kwargs.update({
            'account': self.create_random_name('ac', 10),
            'id_name': self.create_random_name('amid', 10)
        })
        self.cmd('monitor account create -n {account} -g {rg}')

        # Assign system-assigned identity
        self.cmd('monitor account identity assign -n {account} -g {rg} --system-assigned', checks=[
            self.check('type', 'systemAssigned')
        ])
        self.cmd('monitor account identity show -n {account} -g {rg}', checks=[
            self.check('type', 'systemAssigned')
        ])

        # Remove system-assigned identity
        self.cmd('monitor account identity remove -n {account} -g {rg} --system-assigned')

        # Assign user-assigned identity (AMW only supports one type at a time)
        identity = self.cmd('identity create -n {id_name} -g {rg}').get_output_in_json()
        self.kwargs['identity'] = identity['id']
        self.cmd('monitor account identity assign -n {account} -g {rg} --user-assigned {identity}', checks=[
            self.check('type', 'userAssigned'),
            self.check('length(userAssignedIdentities)', 1)
        ])

        # Remove user-assigned identity
        self.cmd('monitor account identity remove -n {account} -g {rg} --user-assigned {identity}')

    @ResourceGroupPreparer(name_prefix='cli_test_monitor_account_mc')
    def test_monitor_account_metrics_container(self, resource_group):
        self.kwargs.update({
            'account': self.create_random_name('ac', 10)
        })
        self.cmd('monitor account create -n {account} -g {rg}')

        # Create metrics container (name must be "default")
        self.cmd('monitor account metrics-container create '
                 '--azure-monitor-workspace-name {account} -g {rg} -n default', checks=[
            self.check('name', 'default')
        ])
        self.cmd('monitor account metrics-container show '
                 '--azure-monitor-workspace-name {account} -g {rg} -n default', checks=[
            self.check('name', 'default')
        ])
        self.cmd('monitor account metrics-container update '
                 '--azure-monitor-workspace-name {account} -g {rg} -n default', checks=[
            self.check('name', 'default')
        ])

    @unittest.skip('accounts/issues resource type requires preview API version (2025-10-03-preview), not supported in GA 2025-10-03')
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_account_issue')
    def test_monitor_account_issue(self, resource_group):
        self.kwargs.update({
            'account': self.create_random_name('ac', 10),
            'issue': self.create_random_name('issue', 10)
        })
        self.cmd('monitor account create -n {account} -g {rg}')

        # Create issue
        self.cmd('monitor account issue create --azure-monitor-workspace-name {account} -g {rg} '
                 '-n {issue} --title "Test Issue" --severity Low --status New', checks=[
            self.check('name', '{issue}'),
            self.check('properties.title', 'Test Issue'),
            self.check('properties.severity', 'Low'),
            self.check('properties.status', 'New')
        ])
        self.cmd('monitor account issue show --azure-monitor-workspace-name {account} -g {rg} '
                 '-n {issue}', checks=[
            self.check('name', '{issue}')
        ])
        self.cmd('monitor account issue list --azure-monitor-workspace-name {account} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{issue}')
        ])
        self.cmd('monitor account issue update --azure-monitor-workspace-name {account} -g {rg} '
                 '-n {issue} --status InProgress', checks=[
            self.check('properties.status', 'InProgress')
        ])
        self.cmd('monitor account issue delete --azure-monitor-workspace-name {account} -g {rg} '
                 '-n {issue} -y')
