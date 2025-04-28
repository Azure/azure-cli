# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer)
from azure.cli.testsdk.scenario_tests.decorators import live_only

class AcrabacScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    def test_acr_create_abac(self):
        self.kwargs.update({
            'name': self.create_random_name('clitestabac', length=16),
        })

        # Create an abac-enabled registry
        self.cmd('acr create -g {rg} -n {name} --sku Basic --location southeastasia --role-assignment-mode rbac-abac', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        # An error will occur when performing check-health on an ABAC-enabled registry for a specific repository if no 
        # data plane permissions are assigned.
        self.cmd('acr check-health -n {name} --repository hello-world -y', expect_failure=True)

        self.cmd('acr update -g {rg} -n {name} --role-assignment-mode rbac', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr update -g {rg} -n {name} --role-assignment-mode rbac-abac', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr delete -g {rg} -n {name} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    def test_acr_create_normal(self):
        self.kwargs.update({
            'name': self.create_random_name('clitestabac', length=16),
        })

        self.cmd('acr create -g {rg} -n {name} --sku Basic --location southeastasia', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr update -g {rg} -n {name} --role-assignment-mode RBAC-ABAC', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr update -g {rg} -n {name} --sku Premium', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'AbacRepositoryPermissions')
        ])

        self.cmd('acr delete -g {rg} -n {name} --yes')

    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    @live_only()
    def test_acr_create_normal_check_health(self):
        self.kwargs.update({
            'name': self.create_random_name('clitestabac', length=16),
        })

        self.cmd('acr create -g {rg} -n {name} --sku Basic --location southeastasia', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr show -g {rg} -n {name}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        self.cmd('acr check-health -n {name} --repository hello-world -y', checks=[self.is_empty()])
