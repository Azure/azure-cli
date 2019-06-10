# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer)

from msrestazure.tools import parse_resource_id

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SCRIPT="https://raw.githubusercontent.com/danielsollondon/azvmimagebuilder/master/quickquickstarts/customizeScript.sh"
IMAGE_SOURCE="Canonical:UbuntuServer:18.04-LTS:18.04.201808140"

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

    @ResourceGroupPreparer(name_prefix='img_tmpl_basic')
    def test_image_template_basic(self, resource_group):
        self._assign_ib_permissions(resource_group)

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'tmpl_01': 'template01',
            'tmpl_02': 'template02',
            'img_src': IMAGE_SOURCE,
            'script': TEST_SCRIPT,
            'sub': subscription_id,
        })

        # test template creation works.
        self.cmd('image-builder template create -n {tmpl_01} -g {rg} --scripts {script} {script} --image-source {img_src}',
                 checks=[
                     self.check('name', '{tmpl_01}'), self.check('provisioningState', 'Succeeded'),
                     self.check('source.offer', 'UbuntuServer'), self.check('source.publisher', 'Canonical'),
                     self.check('source.sku', '18.04-LTS'), self.check('source.version', '18.04.201808140'),
                     self.check('source.type', 'PlatformImage'),
                     self.check('length(customize)', 2),
                     self.check('customize[0].name', 'customizeScript.sh'), self.check('customize[0].script', TEST_SCRIPT), self.check('customize[0].type', 'shell'),
                     self.check('customize[1].name', 'customizeScript.sh'), self.check('customize[1].script', TEST_SCRIPT), self.check('customize[1].type', 'shell'),
                     self.check('distribute', None)
                 ])

        # test that outputs can be set through create command.
        out_2 = "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2=centralus"
        self.cmd('image-builder template create -n {tmpl_02} -g {rg} --scripts {script} --image-source {img_src} '
                 '--managed-image-destinations img_1=westus ' + out_2,
                 checks=[
                     self.check('name', '{tmpl_02}'), self.check('provisioningState', 'Succeeded'),
                     self.check('length(distribute)', 2),
                     self.check('distribute[0].imageId', '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_1'),
                     self.check('distribute[0].location', 'westus'),
                     self.check('distribute[0].runOutputName', 'img_1'),
                     self.check('distribute[0].type', 'managedImage'),
                     self.check('distribute[1].imageId', '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2'),
                     self.check('distribute[1].location', 'centralus'),
                     self.check('distribute[1].runOutputName', 'img_2'),
                     self.check('distribute[1].type', 'managedImage'),

                 ])

        self.kwargs.update({
            'new_img': 'new_img',
            'new_loc': 'southcentralus'
        })
        out_3 = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/images/{}".format(subscription_id, resource_group, 'new_img')
        self.cmd('image-builder output add -n {tmpl_01} -g {rg} --managed-image {new_img} --managed-image-location {new_loc}',
                 checks=[
                     self.check('name', '{tmpl_01}'),
                     self.check('distribute[0].imageId', out_3),
                     self.check('distribute[0].location', '{new_loc}'),
                     self.check('distribute[0].runOutputName', '{new_img}'),
                     self.check('distribute[0].type', 'managedImage')
                 ])

    @ResourceGroupPreparer(name_prefix='img_tmpl_basic_2', location="westus2")
    def test_image_template_basic_sig(self, resource_group):
        self._assign_ib_permissions(resource_group)

        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'tmpl_01': 'template01',
            'img_src': IMAGE_SOURCE,
            'script': TEST_SCRIPT,
            'sub': subscription_id,
            'gallery': 'gallery1',
            'sig1': 'image1'
        })

        # create a sig
        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1} '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')

        # Test that sig output can be set through output.

        self.kwargs['sig_out'] = "{}/{}=westus,eastus".format(self.kwargs['gallery'], self.kwargs['sig1'])
        output = self.cmd('image-builder template create -n {tmpl_01} -g {rg} --scripts {script} --image-source {img_src} '
                 '--shared-image-destinations {sig_out}',
                 checks=[
                     self.check('distribute[0].replicationRegions[0]', 'westus'),
                     self.check('distribute[0].replicationRegions[1]', 'eastus'),
                     self.check('distribute[0].runOutputName', '{sig1}')
                 ]).get_output_in_json()

        parsed = parse_resource_id(output['distribute'][0]['galleryImageId'])

        self.assertTrue(parsed['name'], self.kwargs['gallery'])
        self.assertTrue(parsed['child_name_1'], self.kwargs['sig1'])


    @ResourceGroupPreparer(name_prefix='img_tmpl_managed')
    def test_image_build_managed_image(self, resource_group, resource_group_location):
        self._assign_ib_permissions(resource_group)

        self.kwargs.update({
            'tmpl': 'template01',
            'img_src': IMAGE_SOURCE,
            'script': TEST_SCRIPT,
            'loc': resource_group_location,
            'vm': 'testvm',
            'img': 'img_1'
        })

        # create and build image template
        self.cmd('image-builder template create -n {tmpl} -g {rg} --scripts {script} --image-source {img_src} --managed-image-destinations {img}={loc}')
        self.cmd('image-builder run -n {tmpl} -g {rg}')

        # get the run output
        output = self.cmd('image-builder show -n {tmpl} -g {rg} --output-name {img}',
                          checks=self.check('provisioningState', 'Succeeded')
                          ).get_output_in_json()

        self.kwargs['image_id'] = output['artifactId']

        # check that vm successfully created from template.
        self.cmd('vm create --name {vm} -g {rg} --image {image_id}')
        self.cmd('vm show -n {vm} -g {rg}', checks=self.check('provisioningState', 'Succeeded'))


    @ResourceGroupPreparer(name_prefix='img_tmpl_sig')
    def test_image_build_shared_image(self, resource_group):
        self._assign_ib_permissions(resource_group)

        self.kwargs.update({
            'img_src': IMAGE_SOURCE,
            'gallery': 'gallery1',
            'sig1': 'image1',
            'tmpl': 'template01',
            'script': TEST_SCRIPT,
            'vm': 'custom-vm'
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1} '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')

        self.cmd('image-builder template create -n {tmpl} -g {rg} --scripts {script} --image-source {img_src}')
        self.cmd('image-builder output add -n {tmpl} -g {rg} --gallery-name {gallery} --gallery-image-definition {sig1} --gallery-replication-regions westus',
                 checks=[
                     self.check('distribute[0].replicationRegions[0]', 'westus'),
                     self.check('distribute[0].runOutputName', '{sig1}')
                 ])

        # Takes a long time to build a SIG based image template.
        self.cmd('image-builder run -n {tmpl} -g {rg}')

        output = self.cmd('image-builder show -n {tmpl} -g {rg} --output-name {sig1}',
                          checks=self.check('provisioningState', 'Succeeded')
                          ).get_output_in_json()
        self.kwargs['image_id'] = output['artifactId']

        # check that vm successfully created from template.
        self.cmd('vm create --name {vm} -g {rg} --image {image_id}')
        self.cmd('vm show -n {vm} -g {rg}', checks=self.check('provisioningState', 'Succeeded'))


