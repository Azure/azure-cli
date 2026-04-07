# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class DeploymentStacksWhatIfTest(ScenarioTest):
    LOCATION = "westcentralus"
    MGMT_GROUP_NAME = "AzBlueprintAssignTest"

    @ResourceGroupPreparer(name_prefix='cli_test_stacks_what_if', location=LOCATION)
    def test_deployment_stack_what_if_at_resource_group(self, resource_group):
        stack_what_if_name = self.create_random_name('cli-test-create-rg-stack-what-if', 60)
        stack_name = self.create_random_name('cli-test-create-rg-stack-for-what-if', 60)

        self.kwargs.update({
            'name': stack_what_if_name,
            'location': DeploymentStacksWhatIfTest.LOCATION,
            'resource-group': resource_group,
            'template-file': self._get_test_file('simple_template.json'),
            'parameter-file': self._get_test_file('simple_template_params.json'),
            'stack-id': f'/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Resources/deploymentStacks/{stack_name}',
        })

        self.cmd(
            'stack-whatif group create --name {name} --resource-group {resource-group} --template-file "{template-file}" --deny-settings-mode denYdeletE --parameters "{parameter-file}" --description "stack deployment" --aou deleteAll --deny-settings-excluded-principals "01010000-0000-0000-0000-000000001111" --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes --vl ProviderNoRbac --ri P1D --stack-id "{stack-id}" --no-pretty-print',
            checks=self.check('properties.provisioningState', 'succeeded'))

        self.cmd(
            'stack-whatif group show --name {name} --resource-group {resource-group}')

        self.cmd(
            'stack-whatif group list --resource-group {resource-group}',
            checks=self.check(f"length([?name=='{stack_what_if_name}']) > `0`", True))

        self.cmd('stack-whatif group delete --name {name} --resource-group {resource-group} --yes')

    def test_deployment_stack_what_if_at_subscription(self):
        stack_what_if_name = self.create_random_name('cli-test-create-sub-stack-what-if', 60)
        stack_name = self.create_random_name('cli-test-create-sub-stack-for-what-if', 60)

        self.kwargs.update({
            'name': stack_what_if_name,
            'location': DeploymentStacksWhatIfTest.LOCATION,
            'template-file': self._get_test_file('template_sub_validate.json'),
            'parameter-file': self._get_test_file('template_sub_validate_parameters_valid.json'),
            'stack-id': f'/subscriptions/{self.get_subscription_id()}/providers/Microsoft.Resources/deploymentStacks/{stack_name}',
        })

        self.cmd(
            'stack-whatif sub create --name {name} --location {location} --template-file "{template-file}" --dm denyDelete --parameters "{parameter-file}" --description "stack deployment" --aou deleteAll --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes --vl ProviderNoRbac --ri P1D --stack-id "{stack-id}" --no-pretty-print',
            checks=self.check('properties.provisioningState', 'succeeded'))

        self.cmd('stack-whatif sub show --name {name}')

        self.cmd(
            'stack-whatif sub list',
            checks=self.check(f"length([?name=='{stack_what_if_name}']) > `0`", True))

        self.cmd('stack-whatif sub delete --name {name} --yes')

    def test_deployment_stack_what_if_at_management_group(self):
        stack_what_if_name = self.create_random_name('cli-test-create-mg-stack-what-if', 60)
        stack_name = self.create_random_name('cli-test-create-mg-stack-for-what-if', 60)

        self.kwargs.update({
            'name': stack_what_if_name,
            'location': DeploymentStacksWhatIfTest.LOCATION,
            'management-group': DeploymentStacksWhatIfTest.MGMT_GROUP_NAME,
            'template-file': self._get_test_file('template_mg_validate.json'),
            'parameter-file': self._get_test_file('template_mg_validate_parameters_valid.json'),
            'stack-id': f'/providers/Microsoft.Management/managementGroups/{DeploymentStacksWhatIfTest.MGMT_GROUP_NAME}/providers/Microsoft.Resources/deploymentStacks/{stack_name}',
        })

        self.cmd('stack-whatif mg create --name {name} --location {location} --management-group-id {management-group} --template-file "{template-file}" --dm denyDelete --parameters "{parameter-file}" --description "stack deployment" --aou deleteAll --deny-settings-excluded-actions "action1 action2" --deny-settings-apply-to-child-scopes --vl ProviderNoRbac --ri P1D --stack-id "{stack-id}" --no-color')

        self.cmd(
            'stack-whatif mg show --name {name} --management-group-id {management-group} --no-pretty-print',
            checks=self.check('properties.provisioningState', 'succeeded'))

        self.cmd(
            'stack-whatif mg list --management-group-id {management-group}',
            checks=self.check(f"length([?name=='{stack_what_if_name}']) > `0`", True))

        self.cmd('stack-whatif mg delete --name {name} --management-group-id {management-group} --yes')

    @staticmethod
    def _get_test_file(file_path: str):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), file_path).replace('\\', '\\\\')