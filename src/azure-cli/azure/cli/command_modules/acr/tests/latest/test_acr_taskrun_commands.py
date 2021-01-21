# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, StorageAccountPreparer, ResourceGroupPreparer, record_only
import os


class AcrTaskRunCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_taskrun(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'taskrun_name': "testTaskRun",
            'rg_loc': 'westus',
            'sku': 'Standard',
            'no_context': '/dev/null',
            'sourceLocation': 'https://github.com/Azure-Samples/acr-build-helloworld-node.git',
            'dockerFilePath': 'Dockerfile',
            'image': 'testtaskrun:v1',
            'tf': os.path.join(curr_dir, 'taskrunquickbuildsample.json').replace('\\', '\\\\'),
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('adminUserEnabled', False),
                         self.check('sku.name', 'Standard'),
                         self.check('sku.tier', 'Standard'),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('group deployment create --resource-group {rg} --template-file "{tf}" --parameters registryName={registry_name} --parameters taskRunName={taskrun_name} --parameters sourceLocation={sourceLocation} --parameters dockerFilePath={dockerFilePath} --parameters image={image} ')

        self.cmd('acr taskrun list -r {registry_name} -g {rg}',
                 checks=[self.check('[0].name', '{taskrun_name}'),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].runRequest.type', 'DockerBuildRequest')])

        self.cmd('acr taskrun show -r {registry_name} -n {taskrun_name} -g {rg}',
                 checks=[self.check('name', '{taskrun_name}'),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('runRequest.type', 'DockerBuildRequest')]).get_output_in_json()

        # This step passes in real run but fails using recorded file
        # self.cmd('acr taskrun logs -r {registry_name} -n {taskrun_name} -g {rg}')
        self.cmd('acr taskrun delete -r {registry_name} -n {taskrun_name} -g {rg} -y')
