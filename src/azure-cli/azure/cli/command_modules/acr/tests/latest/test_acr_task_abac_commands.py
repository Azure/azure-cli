# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, live_only
import time

class AcrTaskAbacCommandsTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    @live_only()
    def test_acr_abac_task(self):
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'task_name': 'testTask',
            'task_name2': 'testTask2',
            'task_name3': 'testTask3',
            'rg_loc': 'westus',
            'sku': 'Standard',
            'context': 'https://github.com/Azure-Samples/acr-build-helloworld-node',
            'file': 'Dockerfile',
            'image': 'testtask:v1',
            'trigger_enabled': 'False',
            'identity': '[system]',
            'role_assignment_mode': 'rbac-abac',
            'uami_name': self.create_random_name('acr', 10),
            'auth_mode': 'None'
        })

        # Create a user-assigned managed identity
        response = self.cmd('identity create --name {uami_name} --resource-group {rg}', 
                 checks=[self.check('name', '{uami_name}')]).get_output_in_json()
        uami_resource_id = response['id']
        uami_client_id = response['clientId']
        self.kwargs.update({
            'uami_resource_id': uami_resource_id,
            'uami_client_id': uami_client_id
        })

        # Create an ABAC-enabled registry
        response = self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --role-assignment-mode {role_assignment_mode}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('roleAssignmentMode', 'AbacRepositoryPermissions')]).get_output_in_json()
        self.kwargs.update({
            'registry_resource_id': response['id']
        })

        # Assign "Container Registry Repository Contributor" role to the user-assigned managed identity for the registry.
        self.cmd('role assignment create --role "Container Registry Repository Contributor" --assignee {uami_client_id} --scope {registry_resource_id}',
                 checks=[self.check('scope', '{registry_resource_id}')])

        # Create a Docker build task with a system-assigned identity for source registry authentication.
        response = self.cmd('acr task create -n {task_name} -r {registry_name} --source-acr-auth-id {identity} --context {context} --image {image} -f {file} --commit-trigger-enabled {trigger_enabled}',
                 checks=[self.check('name', '{task_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('step.dockerFilePath', '{file}'),
                         self.check('step.imageNames', ['testtask:v1']),
                         self.check('step.arguments', []),
                         self.check('step.isPushEnabled', True),
                         self.check('step.noCache', False),
                         self.check('step.type', 'Docker'),
                         self.check('identity.type', 'SystemAssigned')]).get_output_in_json()
        identity = response['identity']['principalId']
        self.kwargs.update({
            'principal_id': identity
        })

        # Trigger a run from the task without the necessary permissions, expect failure
        self.cmd('acr task run -n {task_name} -r {registry_name} --no-logs', expect_failure=True)

        # Assign "Container Registry Repository Contributor" role to the system-assigned identity for the registry.
        self.cmd('role assignment create --role "Container Registry Repository Contributor" --assignee {principal_id} --scope {registry_resource_id}',
                 checks=[self.check('principalId', '{principal_id}')])

        # Wait for the role assignment to propagate
        time.sleep(60)

        # Trigger a run from the task with necessary permissions
        self.cmd('acr task run -n {task_name} -r {registry_name} --no-logs',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('status', 'Succeeded')])

        # Update the task with user-assigned managed identity
        response = self.cmd('acr task update -n {task_name} -r {registry_name} --source-acr-auth-id {uami_resource_id}',
                 checks=[self.check('name', '{task_name}'),
                         self.check('identity.type', 'SystemAssigned, UserAssigned')]).get_output_in_json()
        assert response['identity']['userAssignedIdentities'][uami_resource_id]['clientId'] == uami_client_id

        # Trigger a run from the task with necessary permissions
        self.cmd('acr task run -n {task_name} -r {registry_name} --no-logs',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('status', 'Succeeded')])
        
        # Create a Docker build task with a user-assigned identity for source registry authentication.
        self.cmd('acr task create -n {task_name2} -r {registry_name} --source-acr-auth-id {uami_resource_id} --context {context} --image {image} -f {file} --commit-trigger-enabled {trigger_enabled}',
                 checks=[self.check('name', '{task_name2}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('step.dockerFilePath', '{file}'),
                         self.check('step.imageNames', ['testtask:v1']),
                         self.check('step.arguments', []),
                         self.check('step.isPushEnabled', True),
                         self.check('step.noCache', False),
                         self.check('step.type', 'Docker'),
                         self.check('identity.type', 'UserAssigned')])
        
        # Trigger a run from the task with necessary permissions
        self.cmd('acr task run -n {task_name2} -r {registry_name} --no-logs',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('status', 'Succeeded')])
        
        # Create a Docker build task without a managed identity for source registry authentication for an ABAC-enabled registry
        self.cmd('acr task create -n {task_name3} -r {registry_name} --context {context} --image {image} -f {file} --commit-trigger-enabled {trigger_enabled}',
                 checks=[self.check('name', '{task_name3}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('step.dockerFilePath', '{file}'),
                         self.check('step.imageNames', ['testtask:v1']),
                         self.check('step.arguments', []),
                         self.check('step.isPushEnabled', True),
                         self.check('step.noCache', False),
                         self.check('step.type', 'Docker')])

        # Trigger a run from the task without the necessary permissions, expect failure
        self.cmd('acr task run -n {task_name3} -r {registry_name} --no-logs', expect_failure=True)

        # update the registry to use RBAC
        self.kwargs.update({
            'role_assignment_mode': 'rbac'
        })
        self.cmd('acr update -n {registry_name} -g {rg} --role-assignment-mode {role_assignment_mode}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        # Expect failure due to conflicting authentication parameters.
        self.cmd('acr task create -n failedTask -r {registry_name} --source-acr-auth-id {identity} --auth-mode {auth_mode} --context {context} --image {image} -f {file} --commit-trigger-enabled {trigger_enabled}', expect_failure=True)

        # test task delete
        self.cmd('acr task delete -n {task_name} -r {registry_name} -y')
        self.cmd('acr task delete -n {task_name2} -r {registry_name} -y')
        self.cmd('acr task delete -n {task_name3} -r {registry_name} -y')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')


    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    @live_only()
    def test_acr_abac_run(self):
        user_id = self.cmd("az ad signed-in-user show").get_output_in_json()["id"]
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'rg_loc': 'westus',
            'sku': 'Standard',
            'role_assignment_mode': 'rbac-abac',
            'user_id': user_id,
            'file': 'build-push-hello-world.yaml',
            'source_location': 'https://github.com/Azure-Samples/acr-tasks.git',
            'identity': '[caller]',
            'auth_mode': 'None'
        })

        # Create an ABAC-enabled registry
        response = self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --role-assignment-mode {role_assignment_mode}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('roleAssignmentMode', 'AbacRepositoryPermissions')]).get_output_in_json()
        self.kwargs.update({
            'registry_resource_id': response['id']
        })

        # Expect failure due to missing permissions
        self.cmd('acr run -r {registry_name} --source-acr-auth-id {identity} -f {file} {source_location} --no-logs', expect_failure=True)

        # Assign "Container Registry Repository Contributor" role to the user identity
        self.cmd('role assignment create --role "Container Registry Repository Contributor" --assignee {user_id} --scope {registry_resource_id}',
                 checks=[self.check('scope', '{registry_resource_id}')])

        # Wait for the role assignment to propagate
        time.sleep(60)
        
        # Queues a quick run with necessary permissions
        self.cmd('acr run -r {registry_name} --source-acr-auth-id {identity} -f {file} {source_location} --no-logs', 
                 checks=[self.check('status', 'Succeeded'),
                         self.check('type', 'Microsoft.ContainerRegistry/registries/runs')])

        # update the registry to use RBAC
        self.kwargs.update({
            'role_assignment_mode': 'rbac'
        })
        self.cmd('acr update -n {registry_name} -g {rg} --role-assignment-mode {role_assignment_mode}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])

        # Expect failure due to conflicting authentication parameters.
        self.cmd('acr run -r {registry_name} --source-acr-auth-id {identity} --auth-mode {auth_mode} -f {file} {source_location} --no-logs', expect_failure=True)

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')


    @ResourceGroupPreparer(name_prefix='cli_test_acrabac_')
    @live_only()
    def test_acr_abac_build(self):
        user_id = self.cmd("az ad signed-in-user show").get_output_in_json()["id"]
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'rg_loc': 'westus',
            'sku': 'Standard',
            'image': 'myimage:tag',
            'identity': '[caller]',
            'role_assignment_mode': 'rbac-abac',
            'source_location': 'https://github.com/Azure-Samples/acr-build-helloworld-node.git',
            'user_id': user_id,
            'auth_mode': 'None'
        })
        
        # Create an ABAC-enabled registry
        response = self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku} --role-assignment-mode {role_assignment_mode}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('roleAssignmentMode', 'AbacRepositoryPermissions')]).get_output_in_json()
        self.kwargs.update({
            'registry_resource_id': response['id']
        })

        # Expect failure due to missing permissions
        self.cmd('acr build -r {registry_name} --source-acr-auth-id {identity} --image {image} {source_location} --no-logs', expect_failure=True)

        # Assign "Container Registry Repository Contributor" role to the user identity
        self.cmd('role assignment create --role "Container Registry Repository Contributor" --assignee {user_id} --scope {registry_resource_id}',
                 checks=[self.check('scope', '{registry_resource_id}')])

        # Wait for the role assignment to propagate
        time.sleep(60)

        # Queues a quick build with necessary permissions
        self.cmd('acr build -r {registry_name} --source-acr-auth-id {identity} --image {image} {source_location} --no-logs', 
                 checks=[self.check('status', 'Succeeded'),
                         self.check('type', 'Microsoft.ContainerRegistry/registries/runs')])

        # update the registry to use RBAC
        self.kwargs.update({
            'role_assignment_mode': 'rbac'
        })
        self.cmd('acr update -n {registry_name} -g {rg} --role-assignment-mode {role_assignment_mode}', checks=[
            self.check('roleAssignmentMode', 'LegacyRegistryPermissions')
        ])
        
        # Expect failure due to conflicting authentication parameters.
        self.cmd('acr build -r {registry_name} --source-acr-auth-id {identity} --auth-mode {auth_mode} --image {image} {source_location} --no-logs', expect_failure=True)

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
