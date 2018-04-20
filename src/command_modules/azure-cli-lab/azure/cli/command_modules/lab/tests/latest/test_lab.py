# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import unittest

from azure.cli.testsdk import record_only
from azure.cli.testsdk import LiveScenarioTest, ResourceGroupPreparer

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATE = os.path.join(TEST_DIR, 'lab_template.json').replace('\\', '\\\\')
ENV_PARAMETERS = os.path.join('@' + TEST_DIR, 'lab_template.json').replace('\\', '\\\\')
LAB_NAME = 'cliautomationlab'


class LabGalleryVMMgmtScenarioTest(LiveScenarioTest):

    @unittest.skip("The test is not working. Pending update.")
    @ResourceGroupPreparer(name_prefix='cliautomation')
    def test_lab_gallery_vm_mgmt(self, resource_group):
        self.kwargs.update({
            'linux_vm_name': 'ubuntuvm5367',
            'linux_image': '\"Ubuntu Server 16.04 LTS\"',
            'windows_vm_name': 'winvm5367',
            'windows_image': '\"Windows Server 2008 R2 SP1\"',
            'image_type': 'gallery',
            'size': 'Standard_DS1_v2',
            'password': 'SecretPassword123',
            'template': TEMPLATE,
            'lab_name': LAB_NAME
        })

        self.cmd('group deployment create -g {rg} --template-file {template}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

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
            self.check('galleryImageReference.publisher', 'Canonical')
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
            self.check('length(@)', 1)
        ])

        # claim any vm
        self.cmd('lab vm claim -g {rg} --lab-name {lab_name}', checks=[
            self.is_empty()
        ])

        # List my vms - we have claimed both VMs
        self.cmd('lab vm list -g {rg} --lab-name {lab_name}', checks=[
            self.check('length(@)', 2)
        ])

        # Delete all the vms
        self.cmd('lab vm delete -g {rg} --lab-name {lab_name} --name {linux_vm_name}', checks=[
            self.is_empty()
        ])
        self.cmd('lab vm delete -g {rg} --lab-name {lab_name} --name {windows_vm_name}', checks=[
            self.is_empty()
        ])

        # Delete the lab
        self.cmd('lab delete -g {rg} --name {lab_name}', checks=[
            self.is_empty()
        ])


class LabEnvironmentMgmtScenarioTest(LiveScenarioTest):

    @unittest.skip("The test is not working. Pending update.")
    @ResourceGroupPreparer(name_prefix='cliautomation01')
    def test_lab_environment_mgmt(self, resource_group):
        self.kwargs.update({
            'env_name': 'docdbenv',
            'arm_template': 'documentdb-webapp',
            'password': 'SecretPassword123',
            'template': TEMPLATE,
            'lab_name': LAB_NAME,
            'env_params': ENV_PARAMETERS
        })

        self.cmd('group deployment create -g {rg} --template-file {template}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        artifact_sources = self.cmd('lab artifact-source list -g {rg} --lab-name {lab_name}') \
            .get_output_in_json()

        self.kwargs.update({
            'artifact_source_name': artifact_sources[0]['name']
        })

        # Create environment in the lab
        self.cmd('lab environment create -g {rg} --lab-name {lab_name} --name {env_name} --arm-template '
                 '{arm_template} --artifact-source-name {artifact_source_name} --parameters {env_params}', checks=[
                     self.check('provisioningState', 'Succeeded'),
                     self.check('type', 'Microsoft.DevTestLab/labs/users/environments')])

        # Delete environment from the lab
        self.cmd('lab environment delete -g {rg} --lab-name {lab_name} --name {env_name}', checks=[
            self.is_empty()
        ])

        # Delete the lab
        self.cmd('lab delete -g {rg} --name {lab_name}', checks=[
            self.is_empty()
        ])
