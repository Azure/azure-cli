# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.testsdk import record_only
from azure.cli.testsdk import ScenarioTest

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE = os.path.join(TEST_DIR, 'lab_template.json').replace('\\', '\\\\')
ENV_PARAMETERS = os.path.join(TEST_DIR, 'docdbenv_parameters.json').replace('\\', '\\\\')
LAB_NAME = 'cliautomationlab'


class LabScenarioTest(ScenarioTest):
    @record_only()
    def test_lab_vm(self):
        self.kwargs.update({
            'linux_vm_name': self.create_random_name('linuxvm', 15),
            'linux_image': '\"Ubuntu Server 22.04 LTS\"',
            'windows_vm_name': self.create_random_name('winvm', 15),
            'windows_image': '\"Windows Server 2022 Datacenter\"',
            'image_type': 'gallery',
            'size': 'Standard_DS1_v2',
            'password': 'SecretPassword123',
            'lab_name': LAB_NAME,
            'rg': 'labtest'
        })

        # Create claimable linux vm in the lab
        self.cmd('lab vm create -g {rg} --lab-name {lab_name} --name {linux_vm_name} --image {linux_image}'
                 ' --image-type {image_type} --size {size} --admin-password {password} --allow-claim', checks=[
                     self.is_empty()])

        self.cmd('lab vm show -g {rg} --lab-name {lab_name} --name {linux_vm_name}', checks=[
            self.check('name', '{linux_vm_name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('osType', 'Linux'),
            self.check('virtualMachineCreationSource', 'FromGalleryImage'),
            self.check('size', '{size}'),
            self.check('disallowPublicIpAddress', True),
            self.check('artifactDeploymentStatus.totalArtifacts', 0),
            self.check('galleryImageReference.publisher', 'canonical')
        ])

        # Create windows vm in the lab
        self.cmd('lab vm create -g {rg} --lab-name {lab_name} --name {windows_vm_name} '
                 '--image {windows_image} --image-type {image_type} --size {size} --admin-password {password} '
                 '--allow-claim', checks=[
                     self.is_empty()])

        self.cmd('lab vm show -g {rg} --lab-name {lab_name} --name {windows_vm_name} ', checks=[
            self.check('name', '{windows_vm_name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check('osType', 'Windows'),
            self.check('virtualMachineCreationSource', 'FromGalleryImage'),
            self.check('size', '{size}'),
            self.check('disallowPublicIpAddress', True),
            self.check('artifactDeploymentStatus.totalArtifacts', 0),
            self.check('galleryImageReference.publisher', 'MicrosoftWindowsServer')
        ])

        # List claimable vms
        self.cmd('lab vm list -g {rg} --lab-name {lab_name} --claimable', checks=[
            self.check('length(@)', 2)
        ])

        # claim a specific vm
        self.cmd('lab vm claim -g {rg} --lab-name {lab_name} --name {linux_vm_name}', checks=[
            self.is_empty()
        ])

        # List my vms - we have already claimed one VM
        self.cmd('lab vm list -g {rg} --lab-name {lab_name}', checks=[
            self.check('length(@)', 3)
        ])

        # claim any vm
        self.cmd('lab vm claim -g {rg} --lab-name {lab_name}', checks=[
            self.is_empty()
        ])

        # List my vms - we have claimed both VMs
        self.cmd('lab vm list -g {rg} --lab-name {lab_name}', checks=[
            self.check('length(@)', 4)
        ])

        # Delete all the vms
        self.cmd('lab vm delete -g {rg} --lab-name {lab_name} --name {linux_vm_name} -y', checks=[
            self.is_empty()
        ])
        self.cmd('lab vm delete -g {rg} --lab-name {lab_name} --name {windows_vm_name} -y', checks=[
            self.is_empty()
        ])

    @record_only()
    def test_lab_custom_image(self):
        self.kwargs.update({
            'image_name': self.create_random_name('image_', 15),
            'lab_name': LAB_NAME,
            'rg': 'labtest'
        })
        vm = self.cmd('lab vm show -g {rg} --lab-name {lab_name} --name linuxvm1').get_output_in_json()
        self.kwargs.update({
            'vm_id': vm['id']
        })
        self.cmd('lab custom-image create --lab-name {lab_name} -n {image_name} -g {rg} --os-state NonDeprovisioned --os-type linux --source-vm-id {vm_id}', checks=[
            self.check('name', '{image_name}'),
            self.check('vm.sourceVmId', '{vm_id}'),
            self.check('vm.linuxOsInfo.linuxOsState', 'NonDeprovisioned')
        ])
        self.cmd('lab custom-image show --lab-name {lab_name} --name {image_name} -g {rg}', checks=[
            self.check('name', '{image_name}'),
            self.check('vm.sourceVmId', '{vm_id}'),
            self.check('vm.linuxOsInfo.linuxOsState', 'NonDeprovisioned')
        ])
        self.cmd('lab custom-image list --lab-name {lab_name} -g {rg}', checks=[
            self.check('[2].name', '{image_name}'),
            self.check('[2].vm.sourceVmId', '{vm_id}'),
            self.check('[2].vm.linuxOsInfo.linuxOsState', 'NonDeprovisioned')
        ])
        self.cmd('lab custom-image delete --lab-name {lab_name} --name {image_name} -g {rg} -y')

    @record_only()
    def test_lab_retrieve_commands(self):
        self.kwargs.update({
            'lab_name': LAB_NAME,
            'rg': 'labtest'
        })
        self.cmd('lab artifact-source show -g {rg} --lab-name {lab_name} --name "Public Repo"', checks=[
            self.check('name', 'Public Repo')
        ])
        self.cmd('lab artifact-source list -g {rg} --lab-name {lab_name}', checks=[
            self.check('[0].name', 'Public Repo')
        ])
        self.cmd('lab vnet list -g {rg} --lab-name {lab_name}', checks=[
            self.check('[0].type', 'Microsoft.DevTestLab/labs/virtualNetworks')
        ])
        self.cmd('lab vnet list -g {rg} --lab-name {lab_name}', checks=[
            self.check('[0].type', 'Microsoft.DevTestLab/labs/virtualNetworks')
        ])
        self.cmd('lab vnet get -g {rg} --lab-name {lab_name} --name Dtlcliautomationlab', checks=[
            self.check('type', 'Microsoft.DevTestLab/labs/virtualNetworks')
        ])
        self.cmd('lab formula list --lab-name {lab_name} -g {rg}')
        self.cmd('lab arm-template list --lab-name {lab_name} -g {rg} --artifact-source-name "Public Environment Repo" --top 3', checks=[
            self.check('length(@)', 3),
            self.check('[0].type', 'Microsoft.DevTestLab/labs/artifactSources/armTemplates')
        ])
        self.cmd('lab arm-template show --name ServiceFabric-LabCluster --lab-name {lab_name} -g {rg} --artifact-source-name "Public Environment Repo"', checks=[
            self.check('type', 'Microsoft.DevTestLab/labs/artifactSources/armTemplates')
        ])

    @record_only()
    def test_lab_secret(self):
        self.kwargs.update({
            'lab_name': LAB_NAME,
            'secret_name': self.create_random_name('secret', 15),
            'rg': 'labtest'
        })
        self.cmd('lab secret set -g {rg} --lab-name {lab_name} -n {secret_name} --value none', checks=[
            self.check('name', '{secret_name}'),
            self.check('type', 'Microsoft.DevTestLab/labs/users/secrets')
        ])
        self.cmd('lab secret show -g {rg} --lab-name {lab_name} -n {secret_name}', checks=[
            self.check('name', '{secret_name}'),
            self.check('type', 'Microsoft.DevTestLab/labs/users/secrets')
        ])
        self.cmd('lab secret list -g {rg} --lab-name {lab_name} ', checks=[
            self.check('[0].name', '{secret_name}'),
            self.check('[0].type', 'Microsoft.DevTestLab/labs/users/secrets')
        ])
        self.cmd('lab secret delete -g {rg} --lab-name {lab_name} -n {secret_name} -y')

    @unittest.skip('No resource for test')
    def test_lab_environment(self):
        self.kwargs.update({
            'env_name': self.create_random_name('env_', 15),
            'arm_template': 'WebApp',
            'password': 'SecretPassword123',
            'template': TEMPLATE,
            'lab_name': LAB_NAME,
            'env_params': ENV_PARAMETERS,
            'rg': 'labtest'
        })

        artifact_sources = self.cmd('lab artifact-source list -g {rg} --lab-name {lab_name}').get_output_in_json()

        self.kwargs.update({
            'artifact_source_name': artifact_sources[1]['name']
        })

        # Create environment in the lab
        self.cmd('lab environment create -g {rg} --lab-name {lab_name} --name {env_name} --arm-template '
                 '{arm_template} --artifact-source-name "{artifact_source_name}" --parameters {env_params}', checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('type', 'Microsoft.DevTestLab/labs/users/environments')])

        self.cmd('lab environment show -g {rg} --lab-name {lab_name} --name {env_name}', checks=[

        ])
        self.cmd('lab environment list -g {rg} --lab-name {lab_name}', checks=[

        ])
        # Delete environment from the lab
        self.cmd('lab environment delete -g {rg} --lab-name {lab_name} --name {env_name} -y')
