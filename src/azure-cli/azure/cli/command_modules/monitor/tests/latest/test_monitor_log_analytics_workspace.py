# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from azure_devtools.scenario_tests import AllowLargeResponse


class TestLogProfileScenarios(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_monitor_workspace', location='centralus')
    @AllowLargeResponse()
    def test_monitor_log_analytics_workspace_default(self, resource_group):
        self.kwargs.update({
            'name': self.create_random_name('clitest', 20)
        })

        self.cmd("monitor log-analytics workspace create -g {rg} -n {name} --tags clitest=myron", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 30),
            self.check('sku.name', 'pergb2018')
        ])

        self.cmd("monitor log-analytics workspace update -g {rg} -n {name} --retention-time 100", checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('retentionInDays', 100)
        ])

        self.cmd("monitor log-analytics workspace show -g {rg} -n {name}", checks=[
            self.check('retentionInDays', 100)
        ])

        self.cmd("monitor log-analytics workspace list-usages -g {rg} -n {name}")
        self.cmd("monitor log-analytics workspace list -g {rg}", checks=[
            self.check('length(@)', 1),
        ])
        self.cmd("monitor log-analytics workspace get-shared-keys -g {rg} -n {name}", checks=[
            self.check("contains(keys(@), 'primarySharedKey')", True),
            self.check("contains(keys(@), 'secondarySharedKey')", True)
        ])

        self.cmd("monitor log-analytics workspace get-schema -g {rg} -n {name}", checks=[
            self.check('__metadata.resultType', 'schema')
        ])

        self.cmd("monitor log-analytics workspace pack enable -g {rg} --workspace-name {name} -n AzureSecurityOfThings")
        self.cmd("monitor log-analytics workspace pack list -g {rg} --workspace-name {name}", checks=[
            self.check("@[?name=='AzureSecurityOfThings'].enabled", '[True]')
        ])

        self.cmd("monitor log-analytics workspace pack disable -g {rg} --workspace-name {name} -n AzureSecurityOfThings")
        self.cmd("monitor log-analytics workspace pack list -g {rg} --workspace-name {name}", checks=[
            self.check("@[?name=='AzureSecurityOfThings'].enabled", '[False]')
        ])

        self.cmd("monitor log-analytics workspace delete -g {rg} -n {name}")
