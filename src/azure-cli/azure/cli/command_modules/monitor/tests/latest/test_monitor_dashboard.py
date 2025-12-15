# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class TestDashboardScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_dashboard')
    def test_monitor_dashboard(self, resource_group):
        self.kwargs.update({
            'dashboard': self.create_random_name('dwg', 10)
        })
        self.cmd('monitor dashboard create -n {dashboard} -g {rg}', checks=[
            self.check('name', '{dashboard}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type', 'microsoft.dashboard/dashboards')
        ])
        self.cmd('monitor dashboard show -n {dashboard} -g {rg}', checks=[
            self.check('name', '{dashboard}'),
            self.check('resourceGroup', '{rg}'),
            self.check('type', 'microsoft.dashboard/dashboards')
        ])
        self.cmd('monitor dashboard list -g {rg}', checks=[
            self.check('[0].name', '{dashboard}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].type', 'microsoft.dashboard/dashboards')
        ])
