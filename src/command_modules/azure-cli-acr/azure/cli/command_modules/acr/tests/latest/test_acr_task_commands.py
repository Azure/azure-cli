# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only


class AcrTaskCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_task(self, resource_group):
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'task_name': 'testTask',
            'rg_loc': 'westcentralus',
            'sku': 'Standard',
            # This token requires 'admin:repo_hook' access. Recycle the token after recording tests.
            'git_access_token': 'c79e207682b7aeea3d94313f66f0dc328c1c4a62',
            'context': 'https://github.com/ankurkhemani/acr-helloworld.git',
            'file': './AcrHelloworld/Dockerfile',
            'image': 'testtask:v1',
            'commit_trigger_status': 'Enabled',
            'git_source_control_type': 'Github'
        })
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Create a docker build task.
        self.cmd('acr task create -n {task_name} -r {registry_name} --git-access-token {git_access_token} --context {context} --image {image} -f {file}',
                 checks=[self.check('name', '{task_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'Linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('trigger.sourceTriggers[0].sourceRepository.repositoryUrl', '{context}'),
                         self.check('trigger.sourceTriggers[0].sourceRepository.sourceControlType', '{git_source_control_type}'),
                         self.check('trigger.sourceTriggers[0].status', '{commit_trigger_status}'),
                         self.check('step.dockerFilePath', '{file}'),
                         self.check('step.imageNames', ['testtask:v1']),
                         self.check('step.arguments', []),
                         self.check('step.isPushEnabled', True),
                         self.check('step.noCache', False)])

        self.cmd('acr task list -r {registry_name}',
                 checks=[self.check('[0].name', '{task_name}')])

        # trigger a run from the task
        response = self.cmd('acr task run -n {task_name} -r {registry_name} --no-logs',
                            checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                                    self.check('status', 'Succeeded')]).get_output_in_json()

        self.kwargs.update({
            'run_id': response['runId']
        })

        # list all runs for the task
        self.cmd('acr task list-runs -n {task_name} -r {registry_name}',
                 checks=[self.check('[0].type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('[0].runId', '{run_id}'),
                         self.check('[0].isArchiveEnabled', False)])

        # show task properties
        self.cmd('acr task show -n {task_name} -r {registry_name}',
                 checks=[self.check('name', '{task_name}')])

        # update the first task using non-default parameter values
        self.cmd('acr task update -n {task_name} -r {registry_name} --cpu 1',
                 checks=[self.check('name', '{task_name}'),
                         self.check('agentConfiguration.cpu', 1)])

        # update a run of the first task
        self.cmd('acr task update-run -r {registry_name} --run-id {run_id} --no-archive false',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('runId', '{run_id}'),
                         self.check('isArchiveEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

        # test task delete
        self.cmd('acr task delete -n {task_name} -r {registry_name}')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg}')
