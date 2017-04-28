# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from azure.cli.core.test_utils.vcr_test_base import (
    ResourceGroupVCRTestBase, JMESPathCheck, NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
TEMPLATE = '{}/lab_template.json'.format(TEST_DIR)
ENV_PARAMTERS = '@{}/docdbenv_paramters.json'.format(TEST_DIR)
LAB_NAME = 'cliautomationlab'


class LabGalleryVMMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(LabGalleryVMMgmtScenarioTest, self).__init__(__file__, test_method,
                                                           resource_group='cliautomation')

    def test_lab_gallery_vm_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        linux_vm_name = 'ubuntuvm5367'
        linux_image = 'Ubuntu\ Server\ 16.04\ LTS'
        windows_vm_name = 'winvm5367'
        windows_image = 'Windows\ Server\ 2008\ R2\ SP1'
        image_type = 'gallery'
        size = 'Standard_DS1_v2'
        password = 'SecretPassword123'

        self.cmd('group deployment create -g {} --template-file {}'
                 .format(rg, TEMPLATE),
                 checks=[JMESPathCheck('properties.provisioningState', 'Succeeded')])

        # Create linux vm in the lab
        self.cmd('lab vm create -g {} --lab-name {} --name {} '
                 '--image {} --image-type {} --size {} --admin-password {}'
                 .format(rg, LAB_NAME, linux_vm_name, linux_image, image_type, size, password),
                 checks=[NoneCheck()])

        self.cmd('lab vm show -g {} --lab-name {} --name {} '
                 .format(rg, LAB_NAME, linux_vm_name),
                 checks=[
                     JMESPathCheck('name', linux_vm_name),
                     JMESPathCheck('provisioningState', 'Succeeded'),
                     JMESPathCheck('osType', 'Linux'),
                     JMESPathCheck('virtualMachineCreationSource', 'FromGalleryImage'),
                     JMESPathCheck('size', size),
                     JMESPathCheck('disallowPublicIpAddress', True),
                     JMESPathCheck('artifactDeploymentStatus.totalArtifacts', 0),
                     JMESPathCheck('galleryImageReference.publisher', 'Canonical')
                 ])

        # Create windows vm in the lab
        self.cmd('lab vm create -g {} --lab-name {} --name {} '
                 '--image {} --image-type {} --size {} --admin-password {}'
                 .format(rg, LAB_NAME, windows_vm_name, windows_image, image_type, size, password),
                 checks=[NoneCheck()])

        self.cmd('lab vm show -g {} --lab-name {} --name {} '
                 .format(rg, LAB_NAME, windows_vm_name),
                 checks=[
                     JMESPathCheck('name', windows_vm_name),
                     JMESPathCheck('provisioningState', 'Succeeded'),
                     JMESPathCheck('osType', 'Windows'),
                     JMESPathCheck('virtualMachineCreationSource', 'FromGalleryImage'),
                     JMESPathCheck('size', size),
                     JMESPathCheck('disallowPublicIpAddress', True),
                     JMESPathCheck('artifactDeploymentStatus.totalArtifacts', 0),
                     JMESPathCheck('galleryImageReference.publisher', 'MicrosoftWindowsServer')
                 ])

        # Delete all the vms
        self.cmd('lab vm delete -g {} --lab-name {} --name {}'
                 .format(rg, LAB_NAME, linux_vm_name), checks=[NoneCheck()])
        self.cmd('lab vm delete -g {} --lab-name {} --name {}'
                 .format(rg, LAB_NAME, windows_vm_name), checks=[NoneCheck()])

        # Delete the lab
        self.cmd('lab delete -g {} --name {}'.format(rg, LAB_NAME), checks=[NoneCheck()])


class LabEnvironmentMgmtScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(LabEnvironmentMgmtScenarioTest, self).__init__(__file__, test_method,
                                                             resource_group='cliautomation01')

    def test_lab_environment_mgmt(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        env_name = 'docdbenv'
        arm_template = 'documentdb-webapp'

        self.cmd('group deployment create -g {} --template-file {}'.format(rg, TEMPLATE),
                 checks=[JMESPathCheck('properties.provisioningState', 'Succeeded')])

        artifact_sources = self.cmd('lab artifact-source list -g {} --lab-name {}'
                                    .format(rg, LAB_NAME))

        # Create environment in the lab
        self.cmd('lab environment create -g {} --lab-name {} --name {} '
                 '--arm-template {} --artifact-source-name {} --parameters {}'
                 .format(rg, LAB_NAME, env_name, arm_template, artifact_sources[0]['name'], ENV_PARAMTERS),
                 checks=[JMESPathCheck('provisioningState', 'Succeeded'),
                         JMESPathCheck('type', 'Microsoft.DevTestLab/labs/users/environments')])

        # Delete environment from the lab
        self.cmd('lab environment delete -g {} --lab-name {} --name {}'
                 .format(rg, LAB_NAME, env_name), checks=[NoneCheck()])

        # Delete the lab
        self.cmd('lab delete -g {} --name {}'.format(rg, LAB_NAME), checks=[NoneCheck()])
