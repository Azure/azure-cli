# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class TestMonitorPrivateLinkScope(ScenarioTest):
    @ResourceGroupPreparer(location='centralus')
    def test_monitor_private_link_scope_scenario(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'scope': 'clitestscopename',
            'workspace': self.create_random_name('clitest', 20),
            'app': self.create_random_name('clitest', 20),
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
        })

        self.cmd('monitor private-link-scope create -n {scope} -g {rg} -l global')