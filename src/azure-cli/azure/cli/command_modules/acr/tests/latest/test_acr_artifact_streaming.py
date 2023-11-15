# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer


class AcrArtifactStreamingCommandsTests(ScenarioTest):

    @ResourceGroupPreparer()
    def test_acr_artifact_streaming(self, resource_group):
        repo = 'microsoft'
        tag = 'azure-cli'
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'rg_loc': 'southcentralus',
            'sku': 'Premium',
            'repo': repo,
            'tag': tag,
            'image': '{}:{}'.format(repo, tag),
            'conversionFormat': 'overlaybd',
            'conversionVersion': 'v1',
            'source_reg_id': '/subscriptions/dfb63c8c-7c89-4ef8-af13-75c1d873c895/resourcegroups/resourcegroupdiffsub/providers/Microsoft.ContainerRegistry/registries/sourceregistrydiffsub'
        })
        # Create ACR
        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('sku.name', '{sku}'),
                         self.check('sku.tier', '{sku}'),
                         self.check('provisioningState', 'Succeeded')])

        # Import image to registry.
        self.cmd('acr import -n {registry_name} -r {source_reg_id} --source {image}')

        # Artifact streaming repo level commands
        self.cmd('acr artifact-streaming show -n {registry_name} --repository {repo}',
                 checks=[self.check('convertPushedImages', False)])
        self.cmd('acr artifact-streaming update -n {registry_name} --repository {repo} --enable-streaming True',
                 checks=[self.check('conversionFormat', '{conversionFormat}'),
                         self.check('conversionVersion', '{conversionVersion}'),
                         self.check('convertPushedImages', True),
                         self.check('status', 'Succeeded')])

        # Artifact streaming image level commands
        self.cmd('acr artifact-streaming create -n {registry_name} -t {image} --no-wait')

        # Operation commands
        self.cmd('acr artifact-streaming operation cancel -n {registry_name} -t {image}')
        self.cmd('acr artifact-streaming operation show -n {registry_name} -t {image}')

        # Delete registry
        self.cmd('acr delete -n {registry_name} -g {rg} -y')
