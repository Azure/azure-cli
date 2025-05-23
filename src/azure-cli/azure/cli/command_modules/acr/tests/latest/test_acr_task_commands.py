# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only, live_only
import os


class AcrTaskCommandsTests(ScenarioTest):

    # @unittest.skip("task.py line 250, BUG: Discriminator type is absent or null, use base class TaskStepProperties.")
    @ResourceGroupPreparer()
    @live_only()
    def test_acr_task(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'task_name': 'testTask',
            'task_no_context_cmd': 'contextlessTaskCmd',
            'task_no_context_file': 'contextlessTaskfile',
            'rg_loc': 'westus',
            'sku': 'Standard',
            'no_context': '/dev/null',
            'context': 'https://github.com/Azure-Samples/acr-build-helloworld-node',
            'file': 'Dockerfile',
            'image': 'testtask:v1',
            'existing_image': 'bash',
            'trigger_enabled': 'False',
            'identity': '[system]',
            'loginServer': 'test.acr.com',
            'file_path': os.path.join(curr_dir, 'taskfilesample.yaml').replace('\\', '\\\\')
        })
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        # Create a docker build task.
        self.cmd('acr task create -n {task_name} -r {registry_name} --context {context} --image {image} -f {file} --commit-trigger-enabled {trigger_enabled} --pull-request-trigger-enabled {trigger_enabled} --assign-identity {identity}',
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
                         self.check('identity.type', 'SystemAssigned')]),

        # Create a contextless task using cmd.
        self.cmd('acr task create -n {task_no_context_cmd} -r {registry_name} --cmd {existing_image} -c {no_context}',
                 checks=[self.check('name', '{task_no_context_cmd}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('step.type', 'EncodedTask')])

        # Show version is correctly added to cmd created encoded task.
        # cannot decode the encodedTaskContent in check, compare the base64 encoded value directly.
        self.cmd('acr task show -n {task_no_context_cmd} -r {registry_name}',
                checks=[self.check('step.encodedTaskContent', 'dmVyc2lvbjogdjEuMS4wCnN0ZXBzOiAKICAtIGNtZDogYmFzaAogICAgZGlzYWJsZVdvcmtpbmdEaXJlY3RvcnlPdmVycmlkZTogdHJ1ZQogICAgdGltZW91dDogMzYwMAo=')])
        
        # Create a contextless task using file.
        self.cmd('acr task create -n {task_no_context_file} -r {registry_name} -f {file_path} -c {no_context}',
                 checks=[self.check('name', '{task_no_context_file}'),
                         self.check('location', '{rg_loc}'),
                         self.check('platform.os', 'linux'),
                         self.check('agentConfiguration.cpu', 2),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('status', 'Enabled'),
                         self.check('timeout', 3600),
                         self.check('step.type', 'EncodedTask')])

        # Show version is not added to file created encoded task.
        # cannot decode the encodedTaskContent in check, compare the base64 encoded value directly.
        self.cmd('acr task show -n {task_no_context_file} -r {registry_name}',
                checks=[self.check('step.encodedTaskContent', 'c3RlcHM6CiAgLSBidWlsZDo=')])

        # list tasks
        self.cmd('acr task list -r {registry_name}',
                 checks=[self.check('[0].name', '{task_name}')])

        # trigger a run for the contextless task
        response = self.cmd('acr task run -n {task_no_context_cmd} -r {registry_name} --no-logs',
                            checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                                    self.check('status', 'Succeeded')]).get_output_in_json()

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
        self.cmd('acr task update -n {task_name} -r {registry_name} --platform linux/arm',
                 checks=[self.check('name', '{task_name}'),
                         self.check('platform.os', 'linux'),
                         self.check('platform.architecture', 'arm')])

        # update a run of the first task
        self.cmd('acr task update-run -r {registry_name} --run-id {run_id} --no-archive false',
                 checks=[self.check('type', 'Microsoft.ContainerRegistry/registries/runs'),
                         self.check('runId', '{run_id}'),
                         self.check('isArchiveEnabled', True),
                         self.check('provisioningState', 'Succeeded')])

        # Add credential for the task
        self.cmd('acr task credential add -n {task_name} -r {registry_name} --login-server {loginServer} -u testuser -p random --use-identity {identity}',
                 checks=[self.check('{loginServer}', None)])

        # Update credential for the task
        self.cmd('acr task credential update -n {task_name} -r {registry_name} --login-server {loginServer} -u testuser -p random',
                 checks=[self.check('{loginServer}', None)])

        # Remove credential for the task
        self.cmd('acr task credential remove -n {task_name} -r {registry_name} --login-server {loginServer}')

        # test task delete
        self.cmd('acr task delete -n {task_name} -r {registry_name} -y')

        # test acr delete
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
