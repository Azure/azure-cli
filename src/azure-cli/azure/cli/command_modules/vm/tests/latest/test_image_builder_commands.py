# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import time
import unittest
from unittest import mock
from knack.testsdk import record_only
from knack.util import CLIError

from azure.cli.testsdk import (ScenarioTest, ResourceGroupPreparer, live_only)
from azure.core.exceptions import HttpResponseError

from msrestazure.tools import parse_resource_id

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

# todo: store a local copy of this.
TEST_SHELL_SCRIPT_URL = "https://raw.githubusercontent.com/danielsollondon/azvmimagebuilder/master/quickquickstarts/customizeScript.sh"
TEST_PWSH_SCRIPT_URL = "https://raw.githubusercontent.com/danielsollondon/azvmimagebuilder/master/testPsScript.ps1"
TEST_PWSH_SCRIPT_INLINE = [
    '"mkdir c:\\buildActions"',
    '"echo Azure-Image-Builder-Was-Here  > c:\\buildActions\\buildActionsOutput.txt"'
]

LINUX_IMAGE_SOURCE = "Canonical:UbuntuServer:18.04-LTS:18.04.201808140"
WIN_IMAGE_SOURCE = "MicrosoftWindowsServer:WindowsServer:2019-Datacenter:2019.0.20190214"
INDEX_FILE = "https://raw.githubusercontent.com/danielsollondon/azvmimagebuilder/master/quickquickstarts/exampleArtifacts/buildArtifacts/index.html"


class ImageTemplateTest(ScenarioTest):
    def _assign_ib_permissions(self, rg):   # need to manually give IB service permission to add image to grou
        subscription_id = self.get_subscription_id()
        assignee = "cf32a0cc-373c-47c9-9156-0db11f6a6dfc"

        self.kwargs.update({
            'sub': subscription_id,
            'assignee': assignee,
            'role': 'Contributor',
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, rg)
        })

        try:
            self.cmd("role assignment create --assignee {assignee} --role {role} --scope {scope}")
        except AssertionError as ex:
            if self.is_live:
                raise ex
            pass

    def _identity_role(self, rg):
        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'ide': 'ide1'
        })
        identity_id = self.cmd('identity create -g {rg} -n {ide}').get_output_in_json()['clientId']
        self.kwargs.update({
            'identity_id': identity_id
        })
        role_definition = """\
{{
    "Name": "{0}",
    "IsCustom": true,
    "Description": "Image Builder access to create resources for the image build, you should delete or split out as appropriate",
    "Actions": [
        "Microsoft.Compute/galleries/read",
        "Microsoft.Compute/galleries/images/read",
        "Microsoft.Compute/galleries/images/versions/read",
        "Microsoft.Compute/galleries/images/versions/write",

        "Microsoft.Compute/images/write",
        "Microsoft.Compute/images/read",
        "Microsoft.Compute/images/delete"
    ],
    "NotActions": [],
    "AssignableScopes": [
      "/subscriptions/{1}/resourceGroups/{2}"
    ]
}}\
        """
        role_name = 'Azure Image Builder Service Image Creation Role ' + self.create_random_name(prefix='', length=10)
        role_definition = role_definition.format(role_name, subscription_id, rg)
        self.kwargs.update({
            'role_name': role_name,
            'role_definition': role_definition
        })
        # self.cmd('role definition create --role-definition \'{role_definition}\'').get_output_in_json()
        scope = '/subscriptions/{0}/resourceGroups/{1}'.format(subscription_id, rg)
        self.kwargs.update({
            'scope': scope
        })
        time.sleep(45)
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            # self.cmd('role assignment create --assignee {identity_id} --role "{role_name}" --scope {scope}')
            self.cmd('role assignment create --assignee {identity_id} --role Contributor --scope {scope}')

    @unittest.skip('The identity is genereated dynamically. Template file should contain it')
    @ResourceGroupPreparer(name_prefix='cli_test_image_builder_template_file_')
    def test_image_builder_template_file(self, resource_group):
        self._identity_role(resource_group)

        # URL
        self.cmd('image builder create -g {rg} -n tmp1 --image-template "https://raw.githubusercontent.com/qwordy/azvmimagebuilder/master/quickquickstarts/0_Creating_a_Custom_Linux_Managed_Image/example.json"',
                 checks=[
                     self.check('source.offer', 'UbuntuServer'),
                     self.check('source.publisher', 'Canonical'),
                     self.check('source.sku', '18.04-LTS'),
                     self.check('source.version', '18.04.201903060'),
                     self.check('source.type', 'PlatformImage'),
                     self.check('length(customize)', 5),
                     self.check('distribute[0].type', 'ManagedImage')
                 ])

        # Local file
        self.cmd('image builder create -g {rg} -n tmp2 --image-template image_template.json',
                 checks=[
                     self.check('source.offer', 'UbuntuServer'),
                     self.check('source.publisher', 'Canonical'),
                     self.check('source.sku', '18.04-LTS'),
                     self.check('source.version', '18.04.201903060'),
                     self.check('source.type', 'PlatformImage'),
                     self.check('length(customize)', 5),
                     self.check('distribute[0].type', 'ManagedImage')
                 ])

    @ResourceGroupPreparer(name_prefix='img_tmpl_basic')
    def test_image_builder_basic(self, resource_group):
        self._identity_role(resource_group)

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'vnet': 'vnet1',
            'subnet': 'subnet1',
            'tmpl_01': 'template01',
            'tmpl_02': 'template02',
            'img_src': LINUX_IMAGE_SOURCE,
            'script': TEST_SHELL_SCRIPT_URL,
            'sub': subscription_id,
            'vhd_out': "my_vhd_output",
        })

        subnet_id = self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}').get_output_in_json()['newVNet']['subnets'][0]['id']
        self.cmd('network vnet subnet update -g {rg} -n {subnet} --vnet-name {vnet} --disable-private-link-service-network-policies true')

        # test template creation works. use cache
        self.cmd('image builder create -n {tmpl_01} -g {rg} --scripts {script} {script} --image-source {img_src} --identity {ide} --vnet {vnet} --subnet {subnet} --vm-size Standard_D1_v2 --os-disk-size 20 --defer',
                 checks=[
                     self.check('properties.source.offer', 'UbuntuServer'), self.check('properties.source.publisher', 'Canonical'),
                     self.check('properties.source.sku', '18.04-LTS'), self.check('properties.source.version', '18.04.201808140'),
                     self.check('properties.source.type', 'PlatformImage'),
                     self.check('length(properties.customize)', 2),

                     self.check('properties.customize[0].name', 'customizeScript.sh'), self.check('properties.customize[0].scriptUri', TEST_SHELL_SCRIPT_URL),
                     self.check('properties.customize[0].type', 'Shell'),
                     self.check('properties.customize[1].name', 'customizeScript.sh'), self.check('properties.customize[1].scriptUri', TEST_SHELL_SCRIPT_URL),
                     self.check('properties.customize[1].type', 'Shell'),

                     self.check('properties.vmProfile.vmSize', 'Standard_D1_v2'),
                     self.check('properties.vmProfile.osDiskSizeGB', 20),
                     self.check('properties.vmProfile.vnetConfig.subnetId', subnet_id, False)
                 ])

        self.kwargs.update({
            'new_img': 'new_img',
            'new_loc': 'southcentralus'
        })

        # test managed image output
        out_2 = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/images/{}".format(subscription_id, resource_group, 'new_img')
        self.cmd('image builder output add -n {tmpl_01} -g {rg} --managed-image {new_img} --managed-image-location {new_loc} --defer',
                 checks=[
                     self.check('properties.distribute[0].imageId', out_2),
                     self.check('properties.distribute[0].location', '{new_loc}'),
                     self.check('properties.distribute[0].runOutputName', '{new_img}'),
                     self.check('properties.distribute[0].type', 'ManagedImage')
                 ])

        # test vhd output
        self.cmd('image builder output add -n {tmpl_01} -g {rg} --output-name {vhd_out} --is-vhd --defer',
                 checks=[
                     self.check('properties.distribute[1].runOutputName', '{vhd_out}'),
                     self.check('properties.distribute[1].type', 'VHD')
                 ])

        # finally send request to ARM using cached object
        self.cmd('image builder update -n {tmpl_01} -g {rg}',
                 checks=[
                     self.check('name', '{tmpl_01}'), self.check('provisioningState', 'Succeeded'),
                     self.check('source.offer', 'UbuntuServer'), self.check('source.publisher', 'Canonical'),
                     self.check('source.sku', '18.04-LTS'), self.check('source.version', '18.04.201808140'),
                     self.check('source.type', 'PlatformImage'),
                     self.check('length(customize)', 2),
                     self.check('length(distribute)', 2),

                     self.check('customize[0].name', 'customizeScript.sh'),
                     self.check('customize[0].scriptUri', TEST_SHELL_SCRIPT_URL), self.check('customize[0].type', 'Shell'),
                     self.check('customize[1].name', 'customizeScript.sh'),
                     self.check('customize[1].scriptUri', TEST_SHELL_SCRIPT_URL), self.check('customize[1].type', 'Shell'),

                     self.check('distribute[0].imageId', out_2),
                     self.check('distribute[0].location', '{new_loc}'),
                     self.check('distribute[0].runOutputName', '{new_img}'),
                     self.check('distribute[0].type', 'ManagedImage'),
                     self.check('distribute[1].runOutputName', '{vhd_out}'),
                     self.check('distribute[1].type', 'VHD')
                 ])

        # test that outputs can be set through create command.
        out_3 = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2=centralus"
        self.cmd('image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22'
                 ' --managed-image-destinations img_1=westus ' + out_3,
                 checks=[
                     self.check('name', '{tmpl_02}'), self.check('provisioningState', 'Succeeded'),
                     self.check('length(distribute)', 2),
                     self.check('distribute[0].imageId', '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_1'),
                     self.check('distribute[0].location', 'westus'),
                     self.check('distribute[0].runOutputName', 'img_1'),
                     self.check('distribute[0].type', 'ManagedImage'),
                     self.check('distribute[1].imageId', '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2'),
                     self.check('distribute[1].location', 'centralus'),
                     self.check('distribute[1].runOutputName', 'img_2'),
                     self.check('distribute[1].type', 'ManagedImage'),
                     self.check('buildTimeoutInMinutes', 22)
                 ])

        self.cmd('image builder list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('image builder delete -n {templ_02} -g {rg}')

    @ResourceGroupPreparer(name_prefix='img_tmpl_basic_2', location="westus2")
    def test_image_builder_basic_sig(self, resource_group):
        self._identity_role(resource_group)

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'tmpl_01': 'template01',
            'img_src': LINUX_IMAGE_SOURCE,
            'script': TEST_SHELL_SCRIPT_URL,
            'sub': subscription_id,
            'gallery': self.create_random_name("sig1", 10),
            'sig1': 'image1'
        })

        # create a sig
        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))

        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1} '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')

        # Test that sig output can be set through output.

        self.kwargs['sig_out'] = "{}/{}=westus,eastus".format(self.kwargs['gallery'], self.kwargs['sig1'])
        output = self.cmd('image builder create -n {tmpl_01} -g {rg} --scripts {script} --image-source {img_src} '
                          '--shared-image-destinations {sig_out} --identity {ide}',
                          checks=[
                              self.check('distribute[0].replicationRegions[0]', 'westus'),
                              self.check('distribute[0].replicationRegions[1]', 'eastus'),
                              self.check('distribute[0].runOutputName', '{sig1}')
                          ]).get_output_in_json()

        parsed = parse_resource_id(output['distribute'][0]['galleryImageId'])

        self.assertTrue(parsed['name'], self.kwargs['gallery'])
        self.assertTrue(parsed['child_name_1'], self.kwargs['sig1'])

    # @record_only()
    @ResourceGroupPreparer(name_prefix='img_tmpl_managed')
    def test_image_build_managed_image(self, resource_group, resource_group_location):
        self._identity_role(resource_group)

        self.kwargs.update({
            'tmpl_1': 'template01',
            'tmpl_2': 'template02',
            'img_src': LINUX_IMAGE_SOURCE,
            'script': TEST_SHELL_SCRIPT_URL,
            'loc': resource_group_location,
            'vm': 'testvm',
            'img_1': 'img_1',
            'img_2': 'img_2'
        })

        # create and build image template
        self.cmd('image builder create -n {tmpl_1} -g {rg} --image-source {img_src} --managed-image-destinations '
                 '{img_1}={loc} --scripts {script} --identity {ide}')
        self.cmd('image builder run -n {tmpl_1} -g {rg}')

        # get the run output
        output = self.cmd('image builder show-runs -n {tmpl_1} -g {rg} --output-name {img_1}',
                          checks=self.check('provisioningState', 'Succeeded')
                          ).get_output_in_json()

        self.kwargs['image_id'] = output['artifactId']

        # check that vm successfully created from template.
        self.cmd('vm create --name {vm} -g {rg} --image {image_id} --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm show -n {vm} -g {rg}', checks=self.check('provisioningState', 'Succeeded'))

        # test template creation from managed image
        img_tmpl = self.cmd('image builder create -n {tmpl_2} -g {rg} --image-source {image_id} '
                            '--managed-image-destinations {img_2}={loc} --scripts {script} --identity {ide}').get_output_in_json()

        self.assertEqual(img_tmpl['source']['imageId'].lower(), self.kwargs['image_id'].lower())
        self.assertEqual(img_tmpl['source']['type'].lower(), 'managedimage')

    # @record_only()
    @ResourceGroupPreparer(name_prefix='img_tmpl_sig')
    def test_image_build_shared_image(self, resource_group, resource_group_location):
        self._identity_role(resource_group)

        self.kwargs.update({
            'loc': resource_group_location,
            'img_src': LINUX_IMAGE_SOURCE,
            'gallery': self.create_random_name("ib_sig", 10),
            'sig1': 'image1',
            'tmpl': 'template01',
            'tmpl_2': 'template02',
            'script': TEST_SHELL_SCRIPT_URL,
            'vm': 'custom-vm'
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1} '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')

        self.cmd('image builder create -n {tmpl} -g {rg} --scripts {script} --image-source {img_src} --identity {ide} --defer')
        self.cmd('image builder output add -n {tmpl} -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1}'
                 ' --gallery-replication-regions westus --defer',
                 checks=[
                     self.check('properties.distribute[0].replicationRegions[0]', 'westus'),
                     self.check('properties.distribute[0].runOutputName', '{sig1}')
                 ])

        # send put request using cached template object
        self.cmd('image builder update -n {tmpl} -g {rg}', checks=[
            self.check('distribute[0].replicationRegions[0]', 'westus'),
            self.check('distribute[0].runOutputName', '{sig1}')
        ])

        # Takes a long time to build a SIG based image template.
        self.cmd('image builder run -n {tmpl} -g {rg}')

        output = self.cmd('image builder show-runs -n {tmpl} -g {rg} --output-name {sig1}',
                          checks=self.check('provisioningState', 'Succeeded')
                          ).get_output_in_json()

        self.kwargs['image_id'] = output['artifactId']

        # check that vm successfully created from template.
        self.cmd('vm create --name {vm} -g {rg} --image {image_id} --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm show -n {vm} -g {rg}', checks=self.check('provisioningState', 'Succeeded'))

        # test template creation from sig image
        img_tmpl = self.cmd('image builder create -n {tmpl_2} -g {rg} --image-source {image_id} --identity {ide} '
                            '--shared-image-destinations "{gallery}/{sig1}={loc}" --scripts {script}').get_output_in_json()

        self.assertEqual(img_tmpl['source']['imageVersionId'].lower(), self.kwargs['image_id'].lower())
        self.assertEqual(img_tmpl['source']['type'].lower(), 'sharedimageversion')

    @ResourceGroupPreparer(name_prefix='img_tmpl_customizers')
    def test_image_builder_customizers(self, resource_group, resource_group_location):
        self._identity_role(resource_group)

        self.kwargs.update({
            'tmpl': 'template01',
            'loc': resource_group_location,
            'vm': 'testvm',
            'img': 'img_1',
            'img_src': WIN_IMAGE_SOURCE,

            'pwsh_name': 'powershell_script',
            'pwsh_name_2': 'powershell_script_inline',
            'shell_name': 'shell_script',
            'win_restart_name': 'windows_restart_name',
            'file_name': 'file_customizer_name',
            'win_update_name': 'win_update_name',

            'script_url': TEST_PWSH_SCRIPT_URL,
            'inline_script': " ".join(TEST_PWSH_SCRIPT_INLINE),
            'inline_shell_script': 'sudo apt install unattended-upgrades',
            'file_url': 'https://raw.githubusercontent.com/danielsollondon/azvmimagebuilder/master/quickquickstarts/exampleArtifacts/buildArtifacts/index.html',
            'file_dest_path': 'c:\\buildArtifacts\\index.html',
            'win_restart_check_cmd': 'echo Azure-Image-Builder-Restarted-the-VM  > c:\\buildArtifacts\\azureImageBuilderRestart.txt',
        })

        # create and build image template
        self.cmd('image builder create -n {tmpl} -g {rg} --scripts {script_url} --image-source {img_src} --managed-image-destinations {img}={loc} --identity {ide} --defer',
                 checks=[
                     self.check('properties.customize[0].name', self.kwargs['script_url'].rsplit("/", 1)[1]),
                     self.check('properties.customize[0].scriptUri', '{script_url}'),
                     self.check('properties.customize[0].type', 'PowerShell')
                 ])

        # Test customizer add, remove and clear..

        self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {pwsh_name} --type powershell -e 0 1 2 --script-url {script_url} --defer',
                 checks=[
                     self.check('properties.customize[1].name', '{pwsh_name}'),
                     self.check('properties.customize[1].scriptUri', '{script_url}'),
                     self.check('properties.customize[1].validExitCodes', '[0, 1, 2]'),
                     self.check('properties.customize[1].type', 'PowerShell')
                 ])

        img_tmpl = self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {pwsh_name_2} --type powershell -e 12 14 16 --inline-script {inline_script} --defer',
                            checks=[
                                self.check('properties.customize[2].name', '{pwsh_name_2}'),
                                self.check('properties.customize[2].validExitCodes', '[12, 14, 16]'),
                                self.check('properties.customize[2].type', 'PowerShell')
                            ]).get_output_in_json()

        self.assertEqual(img_tmpl['properties']['customize'][2]['inline'][0], TEST_PWSH_SCRIPT_INLINE[0][1:-1])  # strip extra quotation
        self.assertEqual(img_tmpl['properties']['customize'][2]['inline'][1], TEST_PWSH_SCRIPT_INLINE[1][1:-1])  # strip extra quotation

        self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {win_restart_name} -t windows-restart --restart-check-command "{win_restart_check_cmd}" --defer',
                 checks=[
                     self.check('properties.customize[3].name', '{win_restart_name}'),
                     self.check('properties.customize[3].restartCheckCommand', '{win_restart_check_cmd}'),
                     self.check('properties.customize[3].restartTimeout', '5m'),
                     self.check('properties.customize[3].type', 'WindowsRestart')
                 ])

        # add file customizer
        self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {file_name} -t file --file-source "{file_url}" --dest-path "{file_dest_path}" --defer',
                 checks=[
                     self.check('properties.customize[4].name', '{file_name}'),
                     self.check('properties.customize[4].sourceUri', '{file_url}'),
                     self.check('properties.customize[4].destination', '{file_dest_path}'),
                     self.check('properties.customize[4].type', 'File')
                 ])

        # add shell script argument even though this is a windows image template
        self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {shell_name} --type shell --inline-script "{inline_shell_script}" --defer',
                 checks=[
                     self.check('properties.customize[5].name', '{shell_name}'),
                     self.check('properties.customize[5].inline[0]', '{inline_shell_script}'),
                     self.check('properties.customize[5].type', 'Shell')
                 ])

        self.cmd('image builder customizer add -n {tmpl} -g {rg} --customizer-name {win_update_name} '
                 '--type windows-update --search-criteria IsInstalled=0 '
                 '--filters "exclude:$_.Title -like \'*Preview*\'" "include:$true" --update-limit 20 --defer',
                 checks=[
                     self.check('properties.customize[6].name', '{win_update_name}'),
                     self.check('properties.customize[6].searchCriteria', 'IsInstalled=0'),
                     # $_ is a dangerous string. You may need to escape it.
                     # self.check('properties.customize[6].filters[0]', 'exclude:$_.Title -like \'*Preview*\''),
                     self.check('properties.customize[6].filters[1]', 'include:$true'),
                     self.check('properties.customize[6].updateLimit', '20')
                 ])

        self.cmd('image builder customizer remove -n {tmpl} -g {rg} --customizer-name {shell_name} --defer', checks=[
            self.check('length(properties.customize)', 6)
        ])

        # create image template from cache
        self.cmd('image builder update -n {tmpl} -g {rg}', checks=[
            self.check('length(customize)', 6)
        ])

        # test clear using object cache
        self.cmd('image builder customizer clear -n {tmpl} -g {rg} --defer', checks=[
            self.check('length(properties.customize)', 0)
        ])

    @ResourceGroupPreparer(name_prefix='img_tmpl_customizers', location='westus2')
    def test_image_template_outputs(self, resource_group, resource_group_location):
        self._identity_role(resource_group)

        self.kwargs.update({
            'tmpl_01': 'template01',
            'img_src': LINUX_IMAGE_SOURCE,
            'script': TEST_SHELL_SCRIPT_URL,
            'loc': resource_group_location,
            'img_1': 'managed_img_1',
            'img_2': 'managed_img_2',
            'vhd_out': 'vhd_1',
        })

        self.cmd('image builder create -n {tmpl_01} -g {rg} --scripts {script} --image-source {img_src} --identity {ide} --defer')

        self.cmd('image builder output add -n {tmpl_01} -g {rg} --managed-image {img_1} --managed-image-location {loc} --defer',
                 checks=[
                     self.check('properties.distribute[0].location', '{loc}'),
                     self.check('properties.distribute[0].runOutputName', '{img_1}'),
                     self.check('properties.distribute[0].type', 'ManagedImage')
                 ])

        self.cmd('image builder output add -n {tmpl_01} -g {rg} --managed-image {img_2} --managed-image-location {loc} --defer',
                 checks=[
                     self.check('properties.distribute[1].location', '{loc}'),
                     self.check('properties.distribute[1].runOutputName', '{img_2}'),
                     self.check('properties.distribute[1].type', 'ManagedImage')
                 ])

        self.cmd('image builder output add -n {tmpl_01} -g {rg} --output-name {vhd_out} --artifact-tags "is_vhd=True" --is-vhd --defer',
                 checks=[
                     self.check('properties.distribute[2].artifactTags.is_vhd', 'True'),
                     self.check('properties.distribute[2].runOutputName', '{vhd_out}'),
                     self.check('properties.distribute[2].type', 'VHD')
                 ])

        self.cmd('image builder output remove -n {tmpl_01} -g {rg} --output-name {img_2} --defer',
                 checks=[
                     self.check('length(properties.distribute)', 2)
                 ])

        # create image template from cache
        self.cmd('image builder update -n {tmpl_01} -g {rg}', checks=[
            self.check('length(distribute)', 2)
        ])

        # test clear using object cache
        self.cmd('image builder output clear -n {tmpl_01} -g {rg} --defer',
                 checks=[
                     self.check('length(properties.distribute)', 0)
                 ])

    @ResourceGroupPreparer(name_prefix='img_tmpl_customizers', location='westus2')
    def test_defer_only_commands(self, resource_group, resource_group_location):
        def _ensure_cmd_raises_defer_error(self, cmds):
            for cmd in cmds:
                with self.assertRaisesRegex(CLIError, "This command requires --defer"):
                    self.cmd(cmd)

        self._identity_role(resource_group)

        self.kwargs.update({
            'tmpl': 'template01',
            'img_src': WIN_IMAGE_SOURCE,
            'script_url': TEST_PWSH_SCRIPT_URL,
            'pwsh_name': 'powershell_script',
            'vhd_name': 'example.vhd',
        })

        self.cmd('image builder create -n {tmpl} -g {rg} --scripts {script_url} --image-source {img_src} --identity {ide} --defer')

        # test that customizer commands require defer
        customizer_commands = [
            'image builder customizer add -n {tmpl} -g {rg} --customizer-name {pwsh_name} --type powershell -e 0 1 2 --script-url {script_url}',
            'image builder customizer remove -n {tmpl} -g {rg} --customizer-name {pwsh_name}',
            'image builder customizer clear -n {tmpl} -g {rg}'
        ]
        _ensure_cmd_raises_defer_error(self, customizer_commands)

        # test that output commands require defer
        output_commands = [
            'image builder output add -n {tmpl} -g {rg} --is-vhd --output-name {vhd_name}',
            'image builder output remove -n {tmpl} -g {rg} --output-name {vhd_name}',
            'image builder output clear -n {tmpl} -g {rg}'
        ]
        _ensure_cmd_raises_defer_error(self, output_commands)

    @ResourceGroupPreparer(name_prefix='img_tmpl_cancel_')
    def test_image_builder_cancel(self, resource_group, resource_group_location):
        self._identity_role(resource_group)

        self.kwargs.update({
            'tmpl': 'template1',
            'img_src': LINUX_IMAGE_SOURCE,
            'loc': resource_group_location,
            'img': 'img1',
        })

        self.cmd('image builder create -g {rg} -n {tmpl} --image-source {img_src} --managed-image-destinations '
                 '{img}={loc} --identity {ide}')
        self.cmd('image builder run -g {rg} -n {tmpl} --no-wait')
        self.cmd('image builder show -g {rg} -n {tmpl}')
        time.sleep(15)
        # Service is not stable
        self.cmd('image builder cancel -g {rg} -n {tmpl}')
        self.cmd('image builder show -g {rg} -n {tmpl}', checks=[
            self.check_pattern('lastRunStatus.runState', 'Canceling|Canceled')
        ])

    @ResourceGroupPreparer(name_prefix='img_tmpl_vmprofile')
    def test_image_builder_vm_profile(self, resource_group):

        self.kwargs.update({
            'vnet': self.create_random_name('vnet_', 15),
            'identity': self.create_random_name('id_', 10),
            'img_src': LINUX_IMAGE_SOURCE,
            'loc': 'westus',
            'subnet': self.create_random_name('subnet_', 15),
            'ib_name': self.create_random_name('ib_', 10),
            'proxy_vm_size': 'Standard_A1_v1'
        })
        my_vnet = self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}').get_output_in_json()
        my_identity=self.cmd('identity create -n {identity} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'subnet_id': my_vnet['newVNet']['subnets'][0]['id'],
            'identity_vm': my_identity['id']
        })
        with self.assertRaises(HttpResponseError):
            self.cmd('image builder create -g {rg} -n {ib_name} --image-source {img_src} --managed-image-destinations image_1=westus --identity {identity} '
                 '--subnet {subnet_id} --proxy-vm-size {proxy_vm_size} --build-vm-identities {identity_vm}')

        self.cmd('image builder show -g {rg} -n {ib_name}', checks=[
            self.check('vmProfile.vnetConfig.proxyVmSize', '{proxy_vm_size}'),
            self.check('vmProfile.userAssignedIdentities[0]', '{identity_vm}')
        ])


if __name__ == '__main__':
    unittest.main()
