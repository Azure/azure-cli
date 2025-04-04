# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI VM TEST DEFINITIONS
import json
import os
import platform
import tempfile
import time
import unittest
from unittest import mock
import uuid

from knack.util import CLIError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer, KeyVaultPreparer)
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"


def _write_config_file(user_name):

    public_key = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8InHIPLAu6lMc0d+5voyXqigZfT5r6fAM1+FQAi+mkPDdk2hNq1BG0Bwfc88G'
                  'm7BImw8TS+x2bnZmhCbVnHd6BPCDY7a+cHCSqrQMW89Cv6Vl4ueGOeAWHpJTV9CTLVz4IY1x4HBdkLI2lKIHri9+z7NIdvFk7iOk'
                  'MVGyez5H1xDbF2szURxgc4I2/o5wycSwX+G8DrtsBvWLmFv9YAPx+VkEHQDjR0WWezOjuo1rDn6MQfiKfqAjPuInwNOg5AIxXAOR'
                  'esrin2PUlArNtdDH1zlvI4RZi36+tJO7mtm3dJiKs4Sj7G6b1CjIU6aaj27MmKy3arIFChYav9yYM3IT')
    config = {
        'username': user_name,
        'ssh_key': public_key
    }
    _, config_file = tempfile.mkstemp()
    with open(config_file, 'w') as outfile:
        json.dump(config, outfile)
    return config_file


# class VMImageListByAliasesScenarioTest(ScenarioTest):

#     def test_vm_image_list_by_alias(self):
#         result = self.cmd('vm image list --offer ubuntu').get_output_in_json()
#         self.assertTrue(len(result) >= 1)
#         self.assertEqual(result[0]['publisher'], 'Canonical')
#         self.assertTrue(result[0]['sku'].endswith('LTS'))


# class VMUsageScenarioTest(ScenarioTest):

#     def test_vm_usage(self):
#         self.cmd('vm list-usage --location westus',
#                  checks=self.check('type(@)', 'array'))


# class VMImageListThruServiceScenarioTest(ScenarioTest):

#     @AllowLargeResponse()
#     def test_vm_images_list_thru_services(self):
#         result = self.cmd('vm image list -l westus --publisher Canonical --offer UbuntuServer -o tsv --all').output
#         assert result.index('16.04') >= 0

#         result = self.cmd('vm image list -p Canonical -f UbuntuServer -o tsv --all').output
#         assert result.index('16.04') >= 0


# class VMOpenPortTest(ScenarioTest):

#     @ResourceGroupPreparer(name_prefix='cli_test_open_port')
#     def test_vm_open_port(self, resource_group):

#         self.kwargs.update({
#             'vm': 'vm1'
#         })

#         self.cmd('vm create -g {rg} -l westus -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password @PasswordPassword1! --public-ip-address-allocation dynamic --authentication-type password')

#         # min params - apply to existing NIC (updates existing NSG)
#         self.kwargs['nsg_id'] = self.cmd('vm open-port -g {rg} -n {vm} --port "*" --priority 900').get_output_in_json()['id']
#         self.kwargs['nsg'] = os.path.split(self.kwargs['nsg_id'])[1]
#         self.cmd('network nsg show -g {rg} -n {nsg}',
#                  checks=self.check("length(securityRules[?name == 'open-port-all'])", 1))

#         # apply to subnet (creates new NSG)
#         self.kwargs['nsg'] = 'newNsg'
#         self.cmd('vm open-port -g {rg} -n {vm} --apply-to-subnet --nsg-name {nsg} --port "*" --priority 900')
#         self.cmd('network nsg show -g {rg} -n {nsg}',
#                  checks=self.check("length(securityRules[?name == 'open-port-all'])", 1))


class VMShowListSizesListIPAddressesScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_list_ip')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_show_list_sizes_list_ip_addresses(self, resource_group):
        self.kwargs.update({
            'loc': 'centralus',
            'vm': 'vm-with-public-ip',
            'allocation': 'static',
            'zone': 2
        })
        # Expecting no results at the beginning
        self.cmd('vm list-ip-addresses --resource-group {rg}', checks=self.is_empty())
        self.cmd('vm create --resource-group {rg} --location {loc} -n {vm} --admin-username ubuntu --image Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest'
                 ' --admin-password testPassword0 --public-ip-address-allocation {allocation} --authentication-type password --zone {zone} --nsg-rule NONE')
        result = self.cmd('vm show --resource-group {rg} --name {vm} -d', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{vm}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()
        self.assertEqual(4, len(result['publicIps'].split('.')))

        result = self.cmd('vm list --resource-group {rg} -d', checks=[
            self.check('[0].name', '{vm}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].powerState', 'VM running')
        ]).get_output_in_json()
        self.assertEqual(4, len(result[0]['publicIps'].split('.')))

        self.cmd('vm list-vm-resize-options --resource-group {rg} --name {vm}',
                 checks=self.check('type(@)', 'array'))

        # Expecting the one we just added
        self.kwargs['rg_caps'] = resource_group.upper()  # test the command handles name with casing diff.
        self.cmd('vm list-ip-addresses --resource-group {rg_caps}', self.check('type(@)', 'array'))


class VMSizeListScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    def test_vm_size_list(self):
        self.cmd('vm list-sizes --location westus',
                 checks=self.check('type(@)', 'array'))


class VMImageListOffersScenarioTest(ScenarioTest):

    def test_vm_image_list_offers(self):
        self.kwargs.update({
            'loc': 'westus',
            'pub': 'Canonical'
        })

        result = self.cmd('vm image list-offers --location {loc} --publisher {pub}').get_output_in_json()
        self.assertTrue(len(result) > 0)
        self.assertFalse([i for i in result if i['location'].lower() != self.kwargs['loc']])


class VMImageListPublishersScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    def test_vm_image_list_publishers(self):
        self.kwargs.update({
            'loc': 'westus'
        })
        self.cmd('vm image list-publishers --location {loc}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?location == '{loc}']) == length(@)", True),
        ])


class VMImageListSkusScenarioTest(ScenarioTest):

    def test_vm_image_list_skus(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'Canonical',
            'offer': 'UbuntuServer'
        })

        result = self.cmd("vm image list-skus --location {loc} -p {pub} --offer {offer} --query \"length([].id.contains(@, '/Publishers/{pub}/ArtifactTypes/VMImage/Offers/{offer}/Skus/'))\"").get_output_in_json()
        self.assertTrue(result > 0)


class VMImageShowScenarioTest(ScenarioTest):

    def test_vm_image_show(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'Canonical',
            'offer': 'UbuntuServer',
            'sku': '18.04-LTS',
            'ver': '18.04.202002180'
        })

        self.cmd('vm image show --location {loc} --publisher {pub} --offer {offer} --sku {sku} --version {ver}', checks=[
            self.check('type(@)', 'object'),
            self.check('location', '{loc}'),
            self.check('name', '{ver}'),
            self.check("contains(id, '/Publishers/{pub}/ArtifactTypes/VMImage/Offers/{offer}/Skus/{sku}/Versions/{ver}')", True)
        ])


class VMGeneralizeScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_generalize_vm')
    def test_vm_generalize(self, resource_group):

        self.kwargs.update({
            'vm': 'vm-generalize'
        })

        self.cmd('vm create -g {rg} -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:18.04-LTS:latest --admin-password testPassword0 --authentication-type password --use-unmanaged-disk')
        self.cmd('vm stop -g {rg} -n {vm}')
        # Should be able to generalize the VM after it has been stopped
        self.cmd('vm generalize -g {rg} -n {vm}', checks=self.is_empty())
        vm = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        self.cmd('vm capture -g {rg} -n {vm} --vhd-name-prefix vmtest')

        # capture to a custom image
        self.kwargs['image'] = 'myImage'
        self.cmd('image create -g {rg} -n {image} --source {vm}', checks=[
            self.check('name', '{image}'),
            self.check('sourceVirtualMachine.id', vm['id']),
            self.check('storageProfile.zoneResilient', None)
        ])
        self.cmd('image show -g {rg} -n {image}', checks=[
            self.check('name', '{image}'),
            self.check('sourceVirtualMachine.id', vm['id']),
            self.check('storageProfile.zoneResilient', None)
        ])
        self.cmd('image list -g {rg}', checks=[
            self.check('length(@)', '1')
        ])
        self.cmd('image delete -g {rg} -n {image}')

    @ResourceGroupPreparer(name_prefix='cli_test_generalize_vm')
    def test_vm_capture_zone_resilient_image(self, resource_group):

        self.kwargs.update({
            'loc': 'francecentral',
            'vm': 'vm-generalize'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username ubuntu --image OpenLogic:CentOS:7.5:latest --admin-password testPassword0 --authentication-type password')
        self.cmd('vm deallocate -g {rg} -n {vm}')
        # Should be able to generalize the VM after it has been stopped
        self.cmd('vm generalize -g {rg} -n {vm}', checks=self.is_empty())
        vm = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()

        # capture to a custom image
        self.kwargs['image'] = 'myImage2'
        self.cmd('image create -g {rg} -n {image} --source {vm} --zone-resilient -l {loc}', checks=[
            self.check('name', '{image}'),
            self.check('sourceVirtualMachine.id', vm['id']),
            self.check('storageProfile.zoneResilient', True)
        ])


class VMVMSSWindowsLicenseTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_windows_license_type')
    def test_vm_vmss_windows_license_type(self, resource_group):

        self.kwargs.update({
            'vm': 'winvm',
            'vmss': 'winvmss'
        })
        self.cmd('vm create -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('licenseType', 'Windows_Server')
        ])
        self.cmd('vm update -g {rg} -n {vm} --license-type None', checks=[
            self.check('licenseType', 'None')
        ])
        self.cmd('vmss create -g {rg} -n {vmss} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1', checks=[
            self.check('vmss.orchestrationMode', 'Uniform')
        ])
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.licenseType', 'Windows_Server')
        ])
        self.cmd('vmss update -g {rg} -n {vmss} --license-type None', checks=[
            self.check('virtualMachineProfile.licenseType', 'None')
        ])


class VMCustomImageTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image')
    def test_vm_custom_image(self, resource_group):
        self.kwargs.update({
            'vm1': 'vm-unmanaged-disk',
            'vm2': 'vm-managed-disk',
            'newvm1': 'fromimage1',
            'newvm2': 'fromimage2',
            'image1': 'img-from-unmanaged',
            'image2': 'img-from-managed',
        })

        self.cmd('vm create -g {rg} -n {vm1} --image Canonical:UbuntuServer:18.04-LTS:latest --use-unmanaged-disk --admin-username sdk-test-admin --admin-password testPassword0')
        # deprovision the VM, but we have to do it async to avoid hanging the run-command itself
        self.cmd('vm run-command invoke -g {rg} -n {vm1} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm1}')
        self.cmd('vm generalize -g {rg} -n {vm1}')
        self.cmd('image create -g {rg} -n {image1} --source {vm1}')

        self.cmd('vm create -g {rg} -n {vm2} --image Canonical:UbuntuServer:18.04-LTS:latest --storage-sku standard_lrs --data-disk-sizes-gb 1 1 --admin-username sdk-test-admin --admin-password testPassword0')
        self.cmd('vm run-command invoke -g {rg} -n {vm2} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm2}')
        self.cmd('vm generalize -g {rg} -n {vm2}')
        self.cmd('image create -g {rg} -n {image2} --source {vm2}')

        self.cmd('vm create -g {rg} -n {newvm1} --image {image1} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password')
        self.cmd('vm show -g {rg} -n {newvm1}', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage')
        ])
        self.cmd('vmss create -g {rg} -n vmss1 --image {image1} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage')
        ])

        self.cmd('vm create -g {rg} -n {newvm2} --image {image2} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password')
        self.cmd('vm show -g {rg} -n {newvm2}', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(storageProfile.dataDisks)", 2),
            self.check("storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS')
        ])

        self.cmd('vmss create -g {rg} -n vmss2 --image {image2} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(vmss.virtualMachineProfile.storageProfile.dataDisks)", 2),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType", 'Standard_LRS'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[1].createOption", 'FromImage'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.storageAccountType", 'Standard_LRS')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image_conflict')
    def test_vm_custom_image_name_conflict(self, resource_group):
        self.kwargs.update({
            'vm': 'test-vm',
            'image1': 'img-from-vm',
            'image2': 'img-from-vm-id',
            'image3': 'img-from-disk-id',
        })

        self.cmd('vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password')
        vm1_info = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        self.cmd('vm stop -g {rg} -n {vm}')

        # set variables up to test against name conflict between disk and vm.
        self.kwargs.update({
            'os_disk_vhd_uri': vm1_info['storageProfile']['osDisk']['vhd']['uri'],
            'vm_id': vm1_info['id'],
            'os_disk': vm1_info['name']
        })

        # create disk with same name as vm
        disk_info = self.cmd('disk create -g {rg} -n {os_disk} --source {os_disk_vhd_uri} --os-type linux').get_output_in_json()
        self.kwargs.update({'os_disk_id': disk_info['id']})

        # Deallocate and generalize vm. Do not need to deprovision vm as this test will not recreate a vm from the image.
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')

        # Create image from vm
        self.cmd('image create -g {rg} -n {image1} --source {vm}', checks=[
            self.check("sourceVirtualMachine.id", '{vm_id}'),
            self.check("storageProfile.osDisk.managedDisk", None)
        ])
        # Create image from vm id
        self.cmd('image create -g {rg} -n {image2} --source {vm_id}', checks=[
            self.check("sourceVirtualMachine.id", '{vm_id}'),
            self.check("storageProfile.osDisk.managedDisk", None)
        ])
        # Create image from disk id
        self.cmd('image create -g {rg} -n {image3} --source {os_disk_id} --os-type linux', checks=[
            self.check("sourceVirtualMachine", None),
            self.check("storageProfile.osDisk.managedDisk.id", '{os_disk_id}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image_mgmt_')
    def test_vm_custom_image_management(self, resource_group):
        self.kwargs.update({
            'vm1':'vm1',
            'vm2':'vm2',
            'image1':'myImage1',
            'image2':'myImage2'
        })

        vm1 = self.cmd('vm create -g {rg} -n {vm1} --admin-username theuser --image OpenLogic:CentOS:7.5:latest --admin-password testPassword0 --authentication-type password --nsg-rule NONE').get_output_in_json()
        self.cmd('vm deallocate -g {rg} -n {vm1}')
        self.cmd('vm generalize -g {rg} -n {vm1}')

        self.cmd('image create -g {rg} -n {image1} --source {vm1}')

        self.cmd('image list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('image show -g {rg} -n {image1}',
                 checks=[
                     self.check('name', '{image1}'),
                 ])
        self.cmd('image update -n {image1} -g {rg} --tags foo=bar', checks=self.check('tags.foo', 'bar'))
        self.cmd('image delete -n {image1} -g {rg}')
        self.cmd('image list -g {rg}', checks=self.check('length(@)', 0))


class VMImageWithPlanTest(ScenarioTest):

    @unittest.skip('You cannot purchase reservation because required AAD tenant information is missing')
    @ResourceGroupPreparer()
    def test_vm_create_with_market_place_image(self, resource_group, resource_group_location):
        # test 2 scenarios, 1. create vm from market place image, 2. create from a custom image captured from such vms
        self.kwargs.update({
            'location': resource_group_location,
            'publisher': 'microsoft-ads',
            'offer': 'linux-data-science-vm-ubuntu',
            'sku': 'linuxdsvmubuntu',
            'vm1': 'vm1',
            'vm2': 'vm2',
            'image': 'image1'
        })
        self.kwargs['urn'] = '{publisher}:{offer}:{sku}:latest'.format(**self.kwargs)

        # extract out the plan info to be used when create the vm from the captured image
        plan = self.cmd('vm image show --urn {urn}').get_output_in_json()['plan']
        self.kwargs['plan_name'] = plan['name']
        self.kwargs['plan_product'] = plan['product']
        self.kwargs['plan_publisher'] = plan['publisher']

        # let us accept the term
        self.cmd('vm image accept-terms --urn {urn}', checks=self.check('accepted', True))

        # create a vm and capture an image from it
        self.cmd('vm create -g {rg} -n {vm1} --image {urn} --admin-username sdk-test-admin --admin-password testPassword0')
        # deprovision the VM, but we have to do it async to avoid hanging the run-command itself
        self.cmd('vm run-command invoke -g {rg} -n {vm1} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm1}')
        self.cmd('vm generalize -g {rg} -n {vm1}')
        self.cmd('image create -g {rg} -n {image} --source {vm1}')

        self.cmd('vm create -g {rg} -n {vm2} --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --plan-publisher {plan_publisher} --plan-name {plan_name} --plan-product {plan_product}')
        self.cmd('vm show -g {rg} -n {vm2}', checks=self.check('provisioningState', 'Succeeded'))


class VMCreateFromUnmanagedDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_from_unmanaged_disk')
    def test_vm_create_from_unmanaged_disk(self, resource_group):
        # create a vm with unmanaged os disk
        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password')
        vm1_info = self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('name', '{vm}'),
            self.check('licenseType', None)
        ]).get_output_in_json()
        self.cmd('vm stop -g {rg} -n {vm}')

        # import the unmanaged os disk into a specialized managed disk
        self.kwargs.update({
            'os_disk_vhd_uri': vm1_info['storageProfile']['osDisk']['vhd']['uri'],
            'vm': 'vm2',
            'os_disk': 'os1'
        })
        self.cmd('disk create -g {rg} -n {os_disk} --source {os_disk_vhd_uri} --os-type linux',
                 checks=[self.check('name', '{os_disk}'), self.check('osType', 'Linux')])
        # create a vm by attaching to it
        self.cmd('vm create -g {rg} -n {vm} --attach-os-disk {os_disk} --os-type linux',
                 checks=self.check('powerState', 'VM running'))


class VMCreateWithSpecializedUnmanagedDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_with_specialized_unmanaged_disk')
    def test_vm_create_with_specialized_unmanaged_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus'
        })

        # create a vm with unmanaged os disk
        self.cmd('vm create -g {rg} -n vm1 --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password')
        vm1_info = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()
        self.kwargs['disk_uri'] = vm1_info['storageProfile']['osDisk']['vhd']['uri']

        self.cmd('vm delete -g {rg} -n vm1 -y')

        # create a vm by attaching the OS disk from the deleted VM
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {disk_uri} --os-type linux --use-unmanaged-disk',
                 checks=self.check('powerState', 'VM running'))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_with_specialized_unmanaged_disk')
    def test_vm_create_with_unmanaged_data_disks(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1',
            'vm2': 'vm2'
        })

        # create a unmanaged bm with 2 unmanaged disks
        vm_create_cmd = 'vm create -g {rg} -n vm1 --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password'
        self.cmd(vm_create_cmd)
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} --new --size-gb 1')
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} --new --size-gb 2')
        vm1_info = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        self.kwargs['disk_uri'] = vm1_info['storageProfile']['osDisk']['vhd']['uri']
        self.kwargs['data_disk'] = vm1_info['storageProfile']['dataDisks'][0]['vhd']['uri']
        self.kwargs['data_disk2'] = vm1_info['storageProfile']['dataDisks'][1]['vhd']['uri']

        self.cmd('vm delete -g {rg} -n vm1 -y')

        # create a vm by attaching the OS disk from the deleted VM
        vm_create_cmd = ('vm create -g {rg} -n {vm2} --attach-os-disk {disk_uri} --os-type linux --use-unmanaged-disk '
                         '--attach-data-disks {data_disk} {data_disk2} --data-disk-caching 0=ReadWrite 1=ReadOnly')
        self.cmd(vm_create_cmd)
        self.cmd('vm show -g {rg} -n {vm2} -d', checks=[
            self.check('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            self.check('storageProfile.dataDisks[0].lun', 0),
            self.check('storageProfile.dataDisks[1].caching', 'ReadOnly'),
            self.check('storageProfile.dataDisks[1].lun', 1)
        ])


class VMAttachDisksOnCreate(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_create_by_attach_os_and_data_disks(self, resource_group):
        # the testing below follow a real custom's workflow requiring the support of attaching data disks on create

        # creating a vm
        self.cmd('vm create -g {rg} -n vm1 --image CentOS85Gen2 --admin-username centosadmin --admin-password testPassword0 --authentication-type password --data-disk-sizes-gb 2')
        result = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()

        self.kwargs.update({
            'origin_os_disk': result['storageProfile']['osDisk']['name'],
            'origin_data_disk': result['storageProfile']['dataDisks'][0]['name'],
            # snapshot the os & data disks
            'os_snapshot': 'oSnapshot',
            'os_disk': 'sDisk',
            'data_snapshot': 'dSnapshot',
            'data_disk': 'dDisk'
        })
        self.cmd('snapshot create -g {rg} -n {os_snapshot} --source {origin_os_disk}')
        self.cmd('disk create -g {rg} -n {os_disk} --source {os_snapshot}')
        self.cmd('snapshot create -g {rg} -n {data_snapshot} --source {origin_data_disk}')
        self.cmd('disk create -g {rg} -n {data_disk} --source {data_snapshot}')

        # rebuild a new vm
        # (os disk can be resized)
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk} --attach-data-disks {data_disk} --data-disk-sizes-gb 3 --os-disk-size-gb 100 --os-type linux',
                 checks=self.check('powerState', 'VM running'))
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check('length(storageProfile.dataDisks)', 2),
            self.check('storageProfile.dataDisks[0].diskSizeGb', 3),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.osDisk.diskSizeGb', 100)
        ])

    @ResourceGroupPreparer()
    def test_vm_create_by_attach_unmanaged_os_and_data_disks(self, resource_group):
        # creating a vm
        self.cmd('vm create -g {rg} -n vm1 --use-unmanaged-disk --image OpenLogic:CentOS:7.5:latest --admin-username centosadmin --admin-password testPassword0 --authentication-type password')
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name vm1 --new --size-gb 2')
        result = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()
        self.kwargs['os_disk_vhd'] = result['storageProfile']['osDisk']['vhd']['uri']
        self.kwargs['data_disk_vhd'] = result['storageProfile']['dataDisks'][0]['vhd']['uri']

        # delete the vm to end vhd's leases so they can be used to create a new vm through attaching
        self.cmd('vm deallocate -g {rg} -n vm1')
        self.cmd('vm delete -g {rg} -n vm1 -y')

        # rebuild a new vm
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk_vhd} --attach-data-disks {data_disk_vhd} --os-type linux --use-unmanaged-disk',
                 checks=self.check('powerState', 'VM running'))


class VMManagedDiskScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_managed_disk')
    def test_vm_managed_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'disk1': 'd1',
            'disk2': 'd2',
            'snapshot1': 's1',
            'snapshot2': 's2',
            'image': 'i1',
            'image_2': 'i2',
            'image_3': 'i3'
        })

        # create a disk and update
        data_disk = self.cmd('disk create -g {rg} -n {disk1} --size-gb 1 --tags tag1=d1', checks=[
            self.check('sku.name', 'Premium_LRS'),
            self.check('diskSizeGB', 1),
            self.check('tags.tag1', 'd1')
        ]).get_output_in_json()
        self.cmd('disk update -g {rg} -n {disk1} --size-gb 10 --sku Standard_LRS', checks=[
            self.check('sku.name', 'Standard_LRS'),
            self.check('diskSizeGB', 10)
        ])

        # get SAS token
        result = self.cmd('disk grant-access -g {rg} -n {disk1} --duration-in-seconds 10').get_output_in_json()
        self.assertTrue('sv=' in result['accessSAS'])

        # create another disk by importing from the disk1
        self.kwargs['disk1_id'] = data_disk['id']
        data_disk2 = self.cmd('disk create -g {rg} -n {disk2} --source {disk1_id}').get_output_in_json()

        # create a snpashot
        os_snapshot = self.cmd('snapshot create -g {rg} -n {snapshot1} --size-gb 1 --sku Premium_LRS --tags tag1=s1', checks=[
            self.check('sku.name', 'Premium_LRS'),
            self.check('diskSizeGB', 1),
            self.check('tags.tag1', 's1')
        ]).get_output_in_json()
        # update the sku
        self.cmd('snapshot update -g {rg} -n {snapshot1} --sku Standard_LRS', checks=[
            self.check('sku.name', 'Standard_LRS'),
            self.check('diskSizeGB', 1)
        ])

        # create another snapshot by importing from the disk1
        data_snapshot = self.cmd('snapshot create -g {rg} -n {snapshot2} --source {disk1} --sku Premium_LRS').get_output_in_json()
        self.kwargs.update({
            'snapshot1_id': os_snapshot['id'],
            'snapshot2_id': data_snapshot['id'],
            'disk2_id': data_disk2['id']
        })

        # till now, image creation doesn't inspect the disk for os, so the command below should succeed with junk disk
        self.cmd('image create -g {rg} -n {image} --source {snapshot1} --data-disk-sources {disk1} {snapshot2_id} {disk2_id} --os-type Linux --tags tag1=i1', checks=[
            self.check('storageProfile.osDisk.osType', 'Linux'),
            self.check('storageProfile.osDisk.snapshot.id', '{snapshot1_id}'),
            self.check('length(storageProfile.dataDisks)', 3),
            self.check('storageProfile.dataDisks[0].lun', 0),
            self.check('storageProfile.dataDisks[1].lun', 1),
            self.check('tags.tag1', 'i1')
        ])

        # test that images can be created with different storage skus and os disk caching settings.
        self.cmd('image create -g {rg} -n {image_2} --source {snapshot1} --data-disk-sources {disk1} {snapshot2_id} {disk2_id}'
                 ' --os-type Linux --tags tag1=i1 --storage-sku Premium_LRS --os-disk-caching None',
                 checks=[
                     self.check('storageProfile.osDisk.storageAccountType', 'Premium_LRS'),
                     self.check('storageProfile.osDisk.osType', 'Linux'),
                     self.check('storageProfile.osDisk.snapshot.id', '{snapshot1_id}'),
                     self.check('length(storageProfile.dataDisks)', 3),
                     self.check('storageProfile.dataDisks[0].lun', 0),
                     self.check('storageProfile.dataDisks[1].lun', 1),
                     self.check('storageProfile.osDisk.caching', 'None'),
                     self.check('tags.tag1', 'i1')
                 ])

        self.cmd('image create -g {rg} -n {image_3} --source {snapshot1} --data-disk-sources {disk1} {snapshot2_id} {disk2_id}'
                 ' --os-type Linux --tags tag1=i1 --storage-sku Standard_LRS --os-disk-caching ReadWrite',
                 checks=[
                     self.check('storageProfile.osDisk.storageAccountType', 'Standard_LRS'),
                     self.check('storageProfile.osDisk.caching', 'ReadWrite')
                 ])


class ComputeListSkusScenarioTest(ScenarioTest):

    @unittest.skip("Need to check this")
    @AllowLargeResponse(size_kb=99999)
    def test_list_compute_skus_table_output(self):
        result = self.cmd('vm list-skus -l eastus2 -otable')
        lines = result.output.split('\n')
        # 1st line is header
        self.assertEqual(lines[0].split(), ['ResourceType', 'Locations', 'Name', 'Zones', 'Restrictions'])
        # spot check the first 4 entries
        fd_found, ud_found, size_found, zone_found = False, False, False, False
        for line in lines[2:]:
            parts = line.split()
            if not fd_found and (parts[:4] == ['availabilitySets', 'eastus2', 'Classic', 'None']):
                fd_found = True
            elif not ud_found and (parts[:4] == ['availabilitySets', 'eastus2', 'Aligned', 'None']):
                ud_found = True
            elif not size_found and parts[:3] == ['disks', 'eastus2', 'Standard_LRS']:
                size_found = True
            elif not zone_found and parts[3] == '1,2,3':
                zone_found = True

        self.assertTrue(fd_found)
        self.assertTrue(ud_found)
        self.assertTrue(size_found)
        self.assertTrue(zone_found)

    @unittest.skip("Need to check this")
    @AllowLargeResponse(size_kb=16144)
    def test_list_compute_skus_filter(self):
        result = self.cmd('vm list-skus -l eastus2 --size Standard_DS1_V2 --zone').get_output_in_json()
        self.assertTrue(result and len(result) == len([x for x in result if x['name'] == 'Standard_DS1_v2' and x['locationInfo'][0]['zones']]))
        result = self.cmd('vm list-skus -l westus --resource-type disks').get_output_in_json()
        self.assertTrue(result and len(result) == len([x for x in result if x['resourceType'] == 'disks']))


class VMExtensionScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_extension')
    def test_vm_extension(self, resource_group):

        user_name = 'foouser1'
        config_file = _write_config_file(user_name)

        self.kwargs.update({
            'vm': 'myvm',
            'pub': 'Microsoft.OSTCExtensions',
            'ext': 'VMAccessForLinux',
            'config': config_file,
            'user': user_name
        })

        self.cmd('vm create -n {vm} -g {rg} --image ubuntu2204 --authentication-type password --admin-username user11 --admin-password testPassword0')

        self.cmd('vm extension list --vm-name {vm} --resource-group {rg}',
                 checks=self.check('length([])', 0))
        self.cmd('vm extension set -n {ext} --publisher {pub} --version 1.2 --vm-name {vm} --resource-group {rg} --protected-settings "{config}" --force-update')
        result = self.cmd('vm get-instance-view -n {vm} -g {rg}', checks=[
            self.check('*.extensions[0].name', ['VMAccessForLinux']),
        ]).get_output_in_json()
        # ensure the minor version is 2+
        minor_version = int(result['instanceView']['extensions'][0]['typeHandlerVersion'].split('.')[1])
        self.assertGreater(minor_version, 2)

        result = self.cmd('vm extension show --resource-group {rg} --vm-name {vm} --name {ext}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{ext}'),
            self.check('resourceGroup', '{rg}'),
        ]).get_output_in_json()
        uuid.UUID(result['forceUpdateTag'])
        self.cmd('vm extension delete --resource-group {rg} --vm-name {vm} --name {ext}')

    @ResourceGroupPreparer(name_prefix='cli_test_vm_extension_2')
    def test_vm_extension_instance_name(self, resource_group):

        user_name = 'foouser1'
        config_file = _write_config_file(user_name)

        self.kwargs.update({
            'vm': 'myvm',
            'pub': 'Microsoft.OSTCExtensions',
            'ext_type': 'VMAccessForLinux',
            'config': config_file,
            'user': user_name,
            'ext_name': 'MyAccessExt'
        })

        self.cmd('vm create -n {vm} -g {rg} --image Canonical:UbuntuServer:18.04-LTS:latest --authentication-type password --admin-username user11 --admin-password testPassword0')
        self.cmd('vm extension set -n {ext_type} --publisher {pub} --version 1.2 --vm-name {vm} --resource-group {rg} '
                 '--protected-settings "{config}" --extension-instance-name {ext_name}')

        self.cmd('vm extension show --resource-group {rg} --vm-name {vm} --name {ext_name}', checks=[
            self.check('name', '{ext_name}'),
            self.check('typePropertiesType', '{ext_type}')
        ])
        self.cmd('vm extension delete --resource-group {rg} --vm-name {vm} --name {ext_name}')


class VMMachineExtensionImageScenarioTest(ScenarioTest):

    def test_vm_machine_extension_image(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'Microsoft.Azure.Diagnostics',
            'ext': 'IaaSDiagnostics',
            'ver': '1.6.4.0'
        })

        self.cmd('vm extension image list-names --location {loc} --publisher {pub}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?location == '{loc}']) == length(@)", True),
        ])
        self.cmd('vm extension image list-versions --location {loc} -p {pub} --name {ext}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?location == '{loc}']) == length(@)", True),
        ])
        self.cmd('vm extension image show --location {loc} -p {pub} --name {ext} --version {ver}', checks=[
            self.check('type(@)', 'object'),
            self.check('location', '{loc}'),
            self.check("contains(id, '/Providers/Microsoft.Compute/Locations/{loc}/Publishers/{pub}/ArtifactTypes/VMExtension/Types/{ext}/Versions/{ver}')", True)
        ])


class VMExtensionImageSearchScenarioTest(LiveScenarioTest):

    def test_vm_extension_image_search(self):
        # pick this specific name, so the search will be under one publisher. This avoids
        # the parallel searching behavior that causes incomplete VCR recordings.
        self.kwargs.update({
            'pub': 'Test.Microsoft.VisualStudio.Services',
            'image': 'TeamServicesAgentLinux1'
        })
        self.cmd('vm extension image list -l westus --publisher {pub} --name {image}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?name == '{image}']) == length(@)", True)
        ])


class VMCreateUbuntuScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_ubuntu')
    def test_vm_create_ubuntu(self, resource_group, resource_group_location):

        self.kwargs.update({
            'username': 'ubuntu',
            'vm': 'cli-test-vm2',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'ssh_key': TEST_SSH_KEY_PUB,
            'loc': resource_group_location
        })
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1 --data-disk-caching ReadOnly')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.adminUsername', '{username}'),
            self.check('osProfile.computerName', '{vm}'),
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', '{ssh_key}'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[0].lun', 0),
            self.check('storageProfile.dataDisks[0].caching', 'ReadOnly'),
        ])

        # test for idempotency--no need to reverify, just ensure the command doesn't fail
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1 --data-disk-caching ReadOnly  ')


class VMCreateExistingOptions(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_existing')
    @StorageAccountPreparer()
    def test_vm_create_existing_options(self, resource_group, storage_account):

        self.kwargs.update({
            'availset': 'vrfavailset',
            'pubip': 'vrfpubip',
            'vnet': 'vrfvnet',
            'subnet': 'vrfsubnet',
            'nsg': 'vrfnsg',
            'vm': 'vrfvm',
            'disk': 'vrfosdisk',
            'container': 'vrfcontainer',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vm availability-set create --name {availset} -g {rg} --unmanaged --platform-fault-domain-count 3 --platform-update-domain-count 3')
        self.cmd('network public-ip create --name {pubip} -g {rg}')
        self.cmd('network vnet create --name {vnet} -g {rg} --subnet-name {subnet}')
        self.cmd('network nsg create --name {nsg} -g {rg}')

        self.cmd('vm create --image Canonical:UbuntuServer:18.04-LTS:latest --os-disk-name {disk} --vnet-name {vnet} --subnet {subnet} --availability-set {availset} --public-ip-address {pubip} -l "West US" --nsg {nsg} --use-unmanaged-disk --size Standard_DS2 --admin-username user11 --storage-account {sa} --storage-container-name {container} -g {rg} --name {vm} --ssh-key-value \'{ssh_key}\'')

        self.cmd('vm availability-set show -n {availset} -g {rg}',
                 checks=self.check('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.kwargs['vm'].upper()), True))
        self.cmd('network nsg show -n {nsg} -g {rg}',
                 checks=self.check('networkInterfaces[0].id.ends_with(@, \'{vm}VMNic\')', True))
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].publicIPAddress.id.ends_with(@, \'{pubip}\')', True))
        self.cmd('vm show -n {vm} -g {rg}',
                 checks=self.check('storageProfile.osDisk.vhd.uri', 'https://{sa}.blob.core.windows.net/{container}/{disk}.vhd'))


class VMCreateExistingIdsOptions(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_existing_ids')
    @StorageAccountPreparer()
    def test_vm_create_existing_ids_options(self, resource_group, storage_account):
        from azure.cli.core.commands.client_factory import get_subscription_id
        from azure.mgmt.core.tools import resource_id, is_valid_resource_id

        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'availset': 'vrfavailset',
            'pubip': 'vrfpubip',
            'vnet': 'vrfvnet',
            'subnet': 'vrfsubnet',
            'nsg': 'vrfnsg',
            'vm': 'vrfvm',
            'disk': 'vrfosdisk',
            'container': 'vrfcontainer',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vm availability-set create --name {availset} -g {rg} --unmanaged --platform-fault-domain-count 3 --platform-update-domain-count 3')
        self.cmd('network public-ip create --name {pubip} -g {rg}')
        self.cmd('network vnet create --name {vnet} -g {rg} --subnet-name {subnet}')
        self.cmd('network nsg create --name {nsg} -g {rg}')

        rg = self.kwargs['rg']
        self.kwargs.update({
            'availset_id': resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Compute', type='availabilitySets', name=self.kwargs['availset']),
            'pubip_id': resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='publicIpAddresses', name=self.kwargs['pubip']),
            'subnet_id': resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name=self.kwargs['vnet'], child_name_1=self.kwargs['subnet']),
            'nsg_id': resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='networkSecurityGroups', name=self.kwargs['nsg'])
        })

        assert is_valid_resource_id(self.kwargs['availset_id'])
        assert is_valid_resource_id(self.kwargs['pubip_id'])
        assert is_valid_resource_id(self.kwargs['subnet_id'])
        assert is_valid_resource_id(self.kwargs['nsg_id'])

        self.cmd('vm create --image Canonical:UbuntuServer:18.04-LTS:latest --os-disk-name {disk} --subnet {subnet_id} --availability-set {availset_id} --public-ip-address {pubip_id} -l "West US" --nsg {nsg_id} --use-unmanaged-disk --size Standard_DS2 --admin-username user11 --storage-account {sa} --storage-container-name {container} -g {rg} --name {vm} --ssh-key-value \'{ssh_key}\'')

        self.cmd('vm availability-set show -n {availset} -g {rg}',
                 checks=self.check('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.kwargs['vm'].upper()), True))
        self.cmd('network nsg show -n {nsg} -g {rg}',
                 checks=self.check('networkInterfaces[0].id.ends_with(@, \'{vm}VMNic\')', True))
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].publicIPAddress.id.ends_with(@, \'{pubip}\')', True))
        self.cmd('vm show -n {vm} -g {rg}',
                 checks=self.check('storageProfile.osDisk.vhd.uri', 'https://{sa}.blob.core.windows.net/{container}/{disk}.vhd'))


# region VMSS Tests

class VMSSCreateAndModify(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_and_modify')
    def test_vmss_create_and_modify(self):

        self.kwargs.update({
            'vmss': 'vmss1',
            'count': 5,
            'new_count': 4
        })

        self.cmd('vmss create --admin-password testPassword0 --name {vmss} -g {rg} --admin-username myadmin --image Win2012R2Datacenter --instance-count {count}')

        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('virtualMachineProfile.priority', None),
            self.check('sku.name', 'Standard_DS1_v2'),
        ])

        self.cmd('vmss list',
                 checks=self.check('type(@)', 'array'))

        self.cmd('vmss list --resource-group {rg}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', 1),
            self.check('[0].name', '{vmss}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        self.cmd('vmss list-skus --resource-group {rg} --name {vmss}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('vmss show --resource-group {rg} --name {vmss}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{vmss}'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('vmss get-os-upgrade-history --resource-group {rg} --name {vmss}', checks=self.is_empty())
        result = self.cmd('vmss list-instances --resource-group {rg} --name {vmss} --query "[].instanceId"').get_output_in_json()
        self.kwargs['instance_ids'] = result[3] + ' ' + result[4]
        self.cmd('vmss update-instances --resource-group {rg} --name {vmss} --instance-ids {instance_ids}')
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss}', checks=[
            self.check('type(@)', 'object'),
            self.check('type(virtualMachine)', 'object'),
            self.check('type(statuses)', 'array')
        ])

        self.cmd('vmss stop --resource-group {rg} --name {vmss}')
        self.cmd('vmss start --resource-group {rg} --name {vmss}')
        self.cmd('vmss restart --resource-group {rg} --name {vmss}')

        self.cmd('vmss scale --resource-group {rg} --name {vmss} --new-capacity {new_count}')
        self.cmd('vmss show --resource-group {rg} --name {vmss}', checks=[
            self.check('sku.capacity', '{new_count}'),
            self.check('virtualMachineProfile.osProfile.windowsConfiguration.enableAutomaticUpdates', True)
        ])

        result = self.cmd('vmss list-instances --resource-group {rg} --name {vmss} --query "[].instanceId"').get_output_in_json()
        self.kwargs['instance_ids'] = result[2] + ' ' + result[3]
        self.cmd('vmss delete-instances --resource-group {rg} --name {vmss} --instance-ids {instance_ids}')
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss}', checks=[
            self.check('type(@)', 'object'),
            self.check('type(virtualMachine)', 'object'),
            self.check('virtualMachine.statusesSummary[0].count', self.kwargs['new_count'] - 2)
        ])
        self.cmd('vmss deallocate --resource-group {rg} --name {vmss}')
        self.cmd('vmss delete --resource-group {rg} --name {vmss}')
        self.cmd('vmss list --resource-group {rg}', checks=self.is_empty())


class VMSSCreateOptions(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_options')
    def test_vmss_create_options(self, resource_group):

        self.kwargs.update({
            'vmss': 'vrfvmss',
            'count': 2,
            'caching': 'ReadWrite',
            'update': 'automatic',
            'ip': 'vrfpubip'
        })

        self.cmd('network public-ip create --name {ip} -g {rg}')

        self.cmd('vmss create --image Debian:debian-10:10:latest --admin-password testPassword0 -l westus -g {rg} -n {vmss} --disable-overprovision --instance-count {count} --os-disk-caching {caching} --upgrade-policy-mode {update} --authentication-type password --admin-username myadmin --public-ip-address {ip} --data-disk-sizes-gb 1 --vm-sku Standard_D2_v2')
        self.cmd('network lb show -g {rg} -n {vmss}lb ',
                 checks=self.check('frontendIPConfigurations[0].publicIPAddress.id.ends_with(@, \'{ip}\')', True))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('sku.capacity', '{count}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('upgradePolicy.mode', self.kwargs['update'].title()),
            self.check('singlePlacementGroup', True),
        ])
        self.kwargs['id'] = self.cmd('vmss list-instances -g {rg} -n {vmss} --query "[].instanceId"').get_output_in_json()[0]
        self.cmd('vmss show -g {rg} -n {vmss} --instance-id {id}',
                 checks=self.check('instanceId', '{id}'))

        self.cmd('vmss disk attach -g {rg} --vmss-name {vmss} --size-gb 3')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 2),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[1].diskSizeGb', 3),
            self.check('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Standard_LRS'),
        ])
        self.cmd('vmss disk detach -g {rg} --vmss-name {vmss} --lun 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].lun', 0),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1)
        ])
        result = self.cmd('vmss list -g {rg} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue({self.kwargs['vmss']}.issubset(table_output))

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_options')
    def test_vmss_update_instance_disks(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1',
            'caching': 'ReadWrite',
            'update': 'automatic',
            'ip': 'vrfpubip',
            'disk': 'd1',
            'instance_id': '1',
            'sku': 'Standard_LRS'
        })

        self.cmd('vmss create --image Debian11 --admin-username clitest1 --admin-password testPassword0 -l westus -g {rg} -n {vmss}  --storage-sku {sku}')
        self.cmd('disk create -g {rg} -n {disk} --size-gb 1 --sku {sku}')
        instances = self.cmd('vmss list-instances -g {rg} -n {vmss}').get_output_in_json()
        self.kwargs['instance_id'] = instances[0]['instanceId']

        self.cmd('vmss disk attach -g {rg} --vmss-name {vmss} --instance-id {instance_id} --disk {disk} --caching {caching}')
        self.cmd("vmss list-instances -g {rg} -n {vmss} --query \"[?instanceId=='{instance_id}']\"", checks=[
            self.check('length([0].storageProfile.dataDisks)', 1),
            self.check('[0].storageProfile.dataDisks[0].caching', self.kwargs['caching'])
        ])
        self.cmd('vmss disk detach -g {rg} --vmss-name {vmss} --instance-id {instance_id} --lun 0')
        self.cmd("vmss list-instances -g {rg} -n {vmss} --query \"[?instanceId=='{instance_id}']\"", checks=[
            self.check('length([0].storageProfile.dataDisks)', 0)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_options')
    def test_vmss_create_auth(self, resource_group):
        self.kwargs.update({
            'vmss_1': 'vmss1',
            'vmss_2': 'vmss2',
            'ssh_key': TEST_SSH_KEY_PUB,
        })

        self.cmd('vmss create --image Debian11 -l westus -g {rg} -n {vmss_1} --authentication-type all '
                 ' --admin-username myadmin --admin-password testPassword0 --ssh-key-value \'{ssh_key}\'',
                 checks=[
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication', False),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB)
                 ])

        self.cmd('vmss create --image Debian11 -l westus -g {rg} -n {vmss_2} --authentication-type ssh '
                 ' --admin-username myadmin --ssh-key-value \'{ssh_key}\'',
                 checks=[
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication', True)
                 ])


class VMSSCreateBalancerOptionsTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_none')
    def test_vmss_create_none_options(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'ssh_key': TEST_SSH_KEY_PUB,
            'quotes': '""' if platform.system() == 'Windows' else "''"
        })
        self.cmd('vmss create -n {vmss} -g {rg} --image Debian:debian-10:10:latest --load-balancer {quotes} --admin-username ubuntu --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --vm-sku Basic_A1')
        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('tags', {}),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations.ipConfigurations.loadBalancerBackendAddressPools', None),
            self.check('sku.name', 'Basic_A1'),
            self.check('sku.tier', 'Basic')
        ])
        self.cmd('vmss update -g {rg} -n {vmss} --set tags.test=success',
                 checks=self.check('tags.test', 'success'))
        self.cmd('network public-ip show -n {vmss}PublicIP -g {rg}', expect_failure=True)

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_w_ag')
    def test_vmss_create_with_app_gateway(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'ssh_key': TEST_SSH_KEY_PUB
        })
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian:debian-10:10:latest --admin-username clittester --ssh-key-value '{ssh_key}' --app-gateway apt1 --instance-count 5",
                 checks=self.check('vmss.provisioningState', 'Succeeded'))
        # spot check it is using gateway
        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('sku.capacity', 5),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].ipConfigurations[0].applicationGatewayBackendAddressPools[0].resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_lb')
    def test_vmss_existing_lb(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'lb': 'lb1'
        })
        self.cmd('network lb create -g {rg} -n {lb} --backend-pool-name test')
        self.cmd('vmss create -g {rg} -n {vmss} --load-balancer {lb} --image ubuntu2204 --admin-username clitester --admin-password TestTest12#$')

    @ResourceGroupPreparer()
    def test_vmss_single_placement_group_default_to_std_lb(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image Debian:debian-10:10:latest --single-placement-group false')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('singlePlacementGroup', False)
        ])

        self.cmd('network lb list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard')
        ])
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard')
        ])


class VMSSCreatePublicIpPerVm(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_w_ips')
    def test_vmss_public_ip_per_vm_custom_domain_name(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1',
            'nsg': 'testnsg',
            'ssh_key': TEST_SSH_KEY_PUB,
            'dns_label': self.create_random_name('clivmss', 20)
        })
        nsg_result = self.cmd('network nsg create -g {rg} -n {nsg}').get_output_in_json()
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian:debian-10:10:latest --admin-username clittester --ssh-key-value '{ssh_key}' --vm-domain-name {dns_label} --public-ip-per-vm --dns-servers 10.0.0.6 10.0.0.5 --nsg {nsg}",
                 checks=self.check('vmss.provisioningState', 'Succeeded'))
        result = self.cmd("vmss show -n {vmss} -g {rg}", checks=[
            self.check('length(virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers)', 2),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers[0]', '10.0.0.6'),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers[1]', '10.0.0.5'),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].networkSecurityGroup.id', nsg_result['NewNSG']['id'])
        ])
        # spot check we have the domain name and have a public ip
        result = self.cmd('vmss list-instance-public-ips -n {vmss} -g {rg}').get_output_in_json()
        self.assertEqual(len(result[0]['ipAddress'].split('.')), 4)
        self.assertTrue(result[0]['dnsSettings']['domainNameLabel'].endswith(self.kwargs['dns_label']))


# class SecretsScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    # @ResourceGroupPreparer(name_prefix='cli_test_vm_secrets')
    # def test_vm_create_linux_secrets(self, resource_group, resource_group_location):

    #     self.kwargs.update({
    #         'admin': 'ubuntu',
    #         'loc': 'westus',
    #         'image': 'UbuntuLTS',
    #         'auth': 'ssh',
    #         'ssh_key': TEST_SSH_KEY_PUB,
    #         'vm': 'vm-name',
    #         'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
    #         'vault': self.create_random_name('vmlinuxkv', 20)
    #     })

    #     message = 'Secret is missing vaultCertificates array or it is empty at index 0'
    #     with self.assertRaisesRegex(CLIError, message):
    #         self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

    #     vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

    #     time.sleep(60)

    #     self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
    #     self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')
    #     self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
    #     vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
    #     self.kwargs['secrets'] = json.dumps(vm_format)

    #     self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

    #     self.cmd('vm show -g {rg} -n {vm}', checks=[
    #         self.check('provisioningState', 'Succeeded'),
    #         self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
    #         self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', '{secret_out}')
    #     ])

    # @ResourceGroupPreparer()
    # def test_vm_create_windows_secrets(self, resource_group, resource_group_location):

    #     self.kwargs.update({
    #         'admin': 'windowsUser',
    #         'loc': 'westus',
    #         'image': 'Win2012R2Datacenter',
    #         'vm': 'vm-name',
    #         'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': [{'certificateUrl': 'certurl'}]}]),
    #         'vault': self.create_random_name('vmkeyvault', 20)
    #     })

    #     message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
    #               'vaultCertificate index 0'
    #     with self.assertRaisesRegex(CLIError, message):
    #         self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

    #     vault_out = self.cmd(
    #         'keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

    #     time.sleep(60)

    #     self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
    #     self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

    #     self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
    #     self.kwargs['secrets'] = self.cmd('vm secret format -s {secret_out} --certificate-store "My"').get_output_in_json()

    #     self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets "{secrets}" --nsg-rule NONE')

    #     self.cmd('vm show -g {rg} -n {vm}', checks=[
    #         self.check('provisioningState', 'Succeeded'),
    #         self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
    #         self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', self.kwargs['secret_out']),
    #         self.check('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
    #     ])


# class VMSSCreateLinuxSecretsScenarioTest(ScenarioTest):

#     @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_linux_secrets')
#     @AllowLargeResponse()
#     def test_vmss_create_linux_secrets(self, resource_group):
#         self.kwargs.update({
#             'loc': 'westus',
#             'vmss': 'vmss1-name',
#             'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
#             'vault': self.create_random_name('vmsslinuxkv', 20),
#             'secret': 'mysecret',
#             'ssh_key': TEST_SSH_KEY_PUB
#         })

#         vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

#         time.sleep(60)

#         self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
#         self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

#         self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
#         vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
#         self.kwargs['secrets'] = json.dumps(vm_format)

#         self.cmd('vmss create -n {vmss} -g {rg} --image Debian:debian-10:10:latest --admin-username deploy --ssh-key-value \'{ssh_key}\' --secrets \'{secrets}\'')

#         self.cmd('vmss show -n {vmss} -g {rg}', checks=[
#             self.check('provisioningState', 'Succeeded'),
#             self.check('virtualMachineProfile.osProfile.secrets[0].sourceVault.id', vault_out['id']),
#             self.check('virtualMachineProfile.osProfile.secrets[0].vaultCertificates[0].certificateUrl', '{secret_out}')
#         ])


class VMSSCreateExistingOptions(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_options')
    def test_vmss_create_existing_options(self):

        self.kwargs.update({
            'vmss': 'vrfvmss',
            'os_disk': 'vrfosdisk',
            'container': 'vrfcontainer',
            'sku': 'Standard_A3',
            'vnet': 'vrfvnet',
            'subnet': 'vrfsubnet',
            'lb': 'vrflb',
            'bepool': 'mybepool',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('network vnet create -n {vnet} -g {rg} --subnet-name {subnet}')
        self.cmd('network lb create --name {lb} -g {rg} --backend-pool-name {bepool}')

        self.cmd('vmss create --image OpenLogic:CentOS:7.5:latest --os-disk-name {os_disk} --admin-username ubuntu --vnet-name {vnet} --subnet {subnet} -l "West US" --vm-sku {sku} --storage-container-name {container} -g {rg} --name {vmss} --load-balancer {lb} --ssh-key-value \'{ssh_key}\' --backend-pool-name {bepool} --use-unmanaged-disk')
        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('sku.name', '{sku}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.name', '{os_disk}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{container}\')', True)
        ])
        self.cmd('network lb show --name {lb} -g {rg}',
                 checks=self.check('backendAddressPools[0].backendIPConfigurations[0].id.contains(@, \'{vmss}\')', True))
        self.cmd('network vnet show --name {vnet} -g {rg}',
                 checks=self.check('subnets[0].ipConfigurations[0].id.contains(@, \'{vmss}\')', True))


class VMSSCreateExistingIdsOptions(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_ids')
    def test_vmss_create_existing_ids_options(self, resource_group):

        from azure.mgmt.core.tools import resource_id, is_valid_resource_id
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'vmss': 'vrfvmss',
            'os_disk': 'vrfosdisk',
            'container': 'vrfcontainer',
            'sku': 'Standard_A3',
            'vnet': 'vrfvnet',
            'subnet': 'vrfsubnet',
            'lb': 'vrflb',
            'bepool': 'mybepool',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('network vnet create -n {vnet} -g {rg} --subnet-name {subnet}')
        self.cmd('network lb create --name {lb} -g {rg} --backend-pool-name {bepool}')

        self.kwargs.update({
            'subnet_id': resource_id(subscription=subscription_id, resource_group=resource_group, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name=self.kwargs['vnet'], child_name_1=self.kwargs['subnet']),
            'lb_id': resource_id(subscription=subscription_id, resource_group=resource_group, namespace='Microsoft.Network', type='loadBalancers', name=self.kwargs['lb'])
        })

        assert is_valid_resource_id(self.kwargs['subnet_id'])
        assert is_valid_resource_id(self.kwargs['lb_id'])

        self.cmd('vmss create --image OpenLogic:CentOS:7.5:latest --os-disk-name {os_disk} --admin-username ubuntu --subnet {subnet_id} -l "West US" --vm-sku {sku} --storage-container-name {container} -g {rg} --name {vmss} --load-balancer {lb_id} --ssh-key-value \'{ssh_key}\' --backend-pool-name {bepool} --use-unmanaged-disk')
        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('sku.name', '{sku}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.name', '{os_disk}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{container}\')', True)
        ])
        self.cmd('network lb show --name {lb} -g {rg}',
                 checks=self.check('backendAddressPools[0].backendIPConfigurations[0].id.contains(@, \'{vmss}\')', True))
        self.cmd('network vnet show --name {vnet} -g {rg}',
                 checks=self.check('subnets[0].ipConfigurations[0].id.contains(@, \'{vmss}\')', True))


class VMSSVMsScenarioTest(ScenarioTest):

    def _check_vms_power_state(self, *args):
        for iid in self.kwargs['instance_ids']:
            result = self.cmd('vmss get-instance-view --resource-group {{rg}} --name {{vmss}} --instance-id {}'.format(iid)).get_output_in_json()
            self.assertTrue(result['statuses'][1]['code'] in args)

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_vms')
    def test_vmss_vms(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1',
            'count': 2,
            'instance_ids': []
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image Canonical:UbuntuServer:18.04-LTS:latest --authentication-type password --admin-username admin123 --admin-password TestTest12#$ --instance-count {count}')

        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss}', checks=[
            self.check('type(@)', 'array'),
            self.check('length(@)', '{count}'),
            self.check("length([].name.starts_with(@, '{vmss}'))", self.kwargs['count'])
        ]).get_output_in_json()

        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]

        self.cmd('vmss show --resource-group {rg} --name {vmss} --instance-id {id}', checks=[
            self.check('type(@)', 'object'),
            self.check('instanceId', '{id}')
        ])
        result = self.cmd('vmss list-instance-connection-info --resource-group {rg} --name {vmss}').get_output_in_json()
        self.assertEqual(result['instance 0'].split(':')[1], '50000')
        self.cmd('vmss restart --resource-group {rg} --name {vmss} --instance-ids *')
        self._check_vms_power_state('PowerState/running', 'PowerState/starting')
        self.cmd('vmss stop --resource-group {rg} --name {vmss} --instance-ids *')
        self._check_vms_power_state('PowerState/stopped')
        self.cmd('vmss start --resource-group {rg} --name {vmss} --instance-ids *')
        self._check_vms_power_state('PowerState/running', 'PowerState/starting')
        self.cmd('vmss deallocate --resource-group {rg} --name {vmss} --instance-ids *')
        self._check_vms_power_state('PowerState/deallocated')
        self.cmd('vmss delete-instances --resource-group {rg} --name {vmss} --instance-ids *')
        self.cmd('vmss list-instances --resource-group {rg} --name {vmss}')


class VMSSCustomDataScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_custom_data')
    def test_vmss_create_custom_data(self):

        self.kwargs.update({
            'vmss': 'vmss-custom-data',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian:debian-10:10:latest --admin-username deploy --ssh-key-value "{ssh_key}" --custom-data "#cloud-config\nhostname: myVMhostname"')

        # custom data is write only, hence we have no automatic way to cross check. Here we just verify VM was provisioned
        self.cmd('vmss show -n {vmss} -g {rg}',
                 checks=self.check('provisioningState', 'Succeeded'))


class VMSSNicScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_nics')
    def test_vmss_nics(self):

        self.kwargs.update({
            'vmss': 'vmss1',
        })

        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        self.cmd('vmss nic list -g {rg} --vmss-name {vmss}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])

        result = self.cmd('vmss list-instances -g {rg} -n {vmss}').get_output_in_json()
        self.kwargs['iid'] = result[0]['instanceId']

        nic_list = self.cmd('vmss nic list-vm-nics -g {rg} --vmss-name {vmss} --instance-id {iid}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ]).get_output_in_json()

        self.kwargs['nic'] = nic_list[0].get('name')
        self.cmd('vmss nic show --resource-group {rg} --vmss-name {vmss} --instance-id {iid} -n {nic}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{nic}'),
            self.check('resourceGroup', '{rg}')
        ])


class VMSSCreateIdempotentTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_idempotent')
    def test_vmss_create_idempotent(self, resource_group):

        self.kwargs.update({'vmss': 'vmss1'})

        # run the command twice with the same parameters and verify it does not fail
        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Canonical:UbuntuServer:18.04-LTS:latest --use-unmanaged-disk')
        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Canonical:UbuntuServer:18.04-LTS:latest --use-unmanaged-disk')

        # still 1 vnet and 1 subnet inside
        self.cmd('network vnet list -g {rg}', checks=[
            self.check('length([])', 1),
            self.check('[0].name', self.kwargs['vmss'] + 'VNET'),
            self.check('[0].subnets[0].addressPrefix', '10.0.0.0/24'),
            self.check('length([0].subnets)', 1),
        ])


class VMSSILBTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_ilb')
    def test_vmss_with_ilb(self, resource_group):

        self.kwargs.update({'vmss': 'vmss1'})

        self.cmd('vmss create -g {rg} -n {vmss} --admin-username admin123 --admin-password PasswordPassword1! --image OpenLogic:CentOS:7.5:latest --instance-count 1 --public-ip-address ""')
        # TODO: restore error validation when #5155 is addressed
        # with self.assertRaises(AssertionError) as err:
        self.cmd('vmss list-instance-connection-info -g {rg} -n {vmss}', expect_failure=True)
        # self.assertTrue('internal load balancer' in str(err.exception))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-08-01')
class VMSSLoadBalancerWithSku(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_lb_sku')
    def test_vmss_lb_sku(self, resource_group):

        self.kwargs.update({
            'vmss0': 'vmss0',
            'vmss': 'vmss1',
            'lb': 'lb1',
            'ip': 'pubip1',
            'sku': 'standard',
            'loc': 'eastus2'
        })

        # default to Basic
        self.cmd('vmss create -g {rg} -l {loc} -n {vmss0} --image Canonical:UbuntuServer:18.04-LTS:latest --admin-username admin123 --admin-password PasswordPassword1!')
        self.cmd('network lb list -g {rg}', checks=self.check('[0].sku.name', 'Basic'))
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Basic'),
            self.check('[0].publicIPAllocationMethod', 'Dynamic')
        ])

        # but you can overrides the defaults
        self.cmd('vmss create -g {rg} -l {loc} -n {vmss} --lb {lb} --lb-sku {sku} --public-ip-address {ip} --image Canonical:UbuntuServer:18.04-LTS:latest --admin-username admin123 --admin-password PasswordPassword1!')
        self.cmd('network lb show -g {rg} -n {lb}',
                 checks=self.check('sku.name', 'Standard'))
        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('sku.name', 'Standard'),
            self.check('publicIPAllocationMethod', 'Static')
        ])


class VMLiveScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_progress')
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging

        self.kwargs.update({'vm': 'vm123'})

        with force_progress_logging() as test_io:
            self.cmd('vm create -g {rg} -n {vm} --admin-username {vm} --admin-password PasswordPassword1! --image Debian:debian-10:10:latest')

        content = test_io.getvalue()
        # check log has okay format
        lines = content.splitlines()
        for line in lines:
            self.assertTrue(line.split(':')[0] in ['Accepted', 'Succeeded'])
        # spot check we do have some relevant progress messages coming out
        # (Note, CLI's progress controller does routine "sleep" before sample the LRO response.
        # This has the consequence that it can't promise each resource's result wil be displayed)
        self.assertTrue(any(line.startswith('Succeeded:') or line.startswith('Accepted:') for line in lines))


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMZoneScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_zones', location='eastus2')
    def test_vm_disk_create_zones(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '2',
            'disk': 'disk123',
            'size': 1
        })
        self.cmd('disk create -g {rg} -n {disk} --size-gb {size} --zone {zones}', checks=[
            self.check('zones[0]', '{zones}')
        ])
        self.cmd('disk show -g {rg} -n {disk}',
                 checks=self.check('zones[0]', '{zones}'))
        result = self.cmd('disk show -g {rg} -n {disk} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group, resource_group_location, self.kwargs['disk'], self.kwargs['zones'], str(self.kwargs['size']), 'Premium_LRS']).issubset(table_output))
        result = self.cmd('disk list -g {rg} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group, resource_group_location, self.kwargs['disk'], self.kwargs['zones']]).issubset(table_output))


class VMRunCommandScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command')
    def test_vm_run_command_e2e(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vm': 'test-run-command-vm',
            'loc': resource_group_location
        })

        self.cmd('vm run-command list -l {loc}')
        self.cmd('vm run-command show --command-id RunShellScript -l {loc}')
        public_ip = self.cmd('vm create -g {rg} -n {vm} --image Canonical:UbuntuServer:18.04-LTS:latest --admin-username clitest1 --admin-password Test12345678!!').get_output_in_json()['publicIpAddress']

        self.cmd('vm open-port -g {rg} -n {vm} --port 80')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx' in str(r.content))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command_w_params')
    def test_vm_run_command_with_parameters(self, resource_group):
        self.kwargs.update({'vm': 'test-run-command-vm2'})
        self.cmd('vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --admin-username clitest1 --admin-password Test12345678!!')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world')

    # @ResourceGroupPreparer(name_prefix='cli_test_vm_encryption', location='westus')
    # def test_vm_disk_encryption_e2e(self, resource_group, resource_group_location):
    #     self.kwargs.update({
    #         'vault': self.create_random_name('vault', 10),
    #         'vm': 'vm1'
    #     })
    #     self.cmd('keyvault create -g {rg} -n {vault} --enabled-for-disk-encryption "true"')
    #     time.sleep(60)  # to avoid 504(too many requests) on a newly created vault
    #     self.cmd('vm create -g {rg} -n {vm} --image win2012datacenter --admin-username clitester1 --admin-password Test123456789!')
    #     self.cmd('vm encryption enable -g {rg} -n {vm} --disk-encryption-keyvault {vault}')
    #     self.cmd('vm encryption show -g {rg} -n {vm}', checks=[self.check('disks[0].statuses[0].code', 'EncryptionState/encrypted')])
    #     self.cmd('vm encryption disable -g {rg} -n {vm}')


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMSSRollingUpgrade(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_rolling_update')
    def test_vmss_rolling_upgrade(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'probe': 'probe1',
            'vmss': 'vmss1'
        })

        # set up a LB with the probe for rolling upgrade
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n {probe} --protocol http --port 80 --path /')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule1 --protocol tcp --frontend-port 80 --backend-port 80 --probe-name {probe}')
        self.cmd('network lb inbound-nat-pool create -g {rg} --lb-name {lb} -n nat-pool1 --backend-port 22 --frontend-port-range-start 50000 --frontend-port-range-end 50119 --protocol Tcp --frontend-ip-name LoadBalancerFrontEnd')

        # create a scaleset to use the LB, note, we start with the manual mode as we are not done with the setup yet
        self.cmd('vmss create -g {rg} -n {vmss} --image Canonical:UbuntuServer:18.04-LTS:latest --admin-username clitester1 --admin-password Testqwer1234! --lb {lb} --health-probe {probe}')

        # install the web server
        _, settings_file = tempfile.mkstemp()
        with open(settings_file, 'w') as outfile:
            json.dump({
                "commandToExecute": "sudo apt-get update && sudo apt-get install -y nginx",
            }, outfile)
        settings_file = settings_file.replace('\\', '\\\\')
        self.kwargs['settings'] = settings_file
        self.cmd('vmss extension set -g {rg} --vmss-name {vmss} -n customScript --publisher Microsoft.Azure.Extensions --settings {settings} --version 2.0')
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids "*"')

        # now we are ready for the rolling upgrade mode
        self.cmd('vmss update -g {rg} -n {vmss} --set upgradePolicy.mode=rolling')

        # make sure the web server works
        result = self.cmd('vmss list-instance-connection-info -g {rg} -n {vmss} -o tsv')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + result.output.split(':')[0])
        self.assertTrue('Welcome to nginx' in str(r.content))

        # do some rolling upgrade, maybe nonsense, but we need to test the command anyway
        self.cmd('vmss rolling-upgrade start -g {rg} -n {vmss}')
        result = self.cmd('vmss rolling-upgrade get-latest -g {rg} -n {vmss}').get_output_in_json()
        self.assertTrue(('policy' in result) and ('progress' in result))  # spot check that it is about rolling upgrade

        # 'cancel' should fail as we have no active upgrade to cancel
        self.cmd('vmss rolling-upgrade cancel -g {rg} -n {vmss}', expect_failure=True)


class VMCreateWithExistingNic(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_create_vm_existing_nic')
    def test_vm_create_existing_nic(self, resource_group):
        import re
        self.cmd('network public-ip create -g {rg} -n my-pip')
        self.cmd('network vnet create -g {rg} -n my-vnet --subnet-name my-subnet1')
        self.cmd('network nic create -g {rg} -n my-nic --subnet my-subnet1 --vnet-name my-vnet --public-ip-address my-pip')
        self.cmd('network nic ip-config create -n my-ipconfig2 -g {rg} --nic-name my-nic --private-ip-address-version IPv6')
        self.cmd('vm create -g {rg} -n vm1 --image Canonical:UbuntuServer:18.04-LTS:latest --nics my-nic --generate-ssh-keys --admin-username ubuntuadmin')
        result = self.cmd('vm show -g {rg} -n vm1 -d').get_output_in_json()
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['publicIps']))
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['privateIps']))


class VMOsDiskSwap(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_os_disk_swap(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'backupDisk': 'disk1',
        })
        self.cmd('vm create -g {rg} -n {vm} --image OpenLogic:CentOS:7.5:latest --admin-username clitest123 --generate-ssh-keys')
        res = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        original_disk_id = res['storageProfile']['osDisk']['managedDisk']['id']
        backup_disk_id = self.cmd('disk create -g {{rg}} -n {{backupDisk}} --source {}'.format(original_disk_id)).get_output_in_json()['id']

        self.cmd('vm stop -g {rg} -n {vm}')
        self.cmd('vm update -g {{rg}} -n {{vm}} --os-disk {}'.format(backup_disk_id))
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.osDisk.managedDisk.id', backup_disk_id),
            self.check('storageProfile.osDisk.name', self.kwargs['backupDisk'])
        ])


class VMGenericUpdate(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_generic_update(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
        })

        self.cmd('vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --data-disk-sizes-gb 1 2 --admin-username cligenerics --generate-ssh-keys')

        # we will try all kinds of generic updates we can
        self.cmd('vm update -g {rg} -n {vm} --set identity.type="SystemAssigned"', checks=[
            self.check('identity.type', 'SystemAssigned')
        ])
        self.cmd('vm update -g {rg} -n {vm} --set storageProfile.dataDisks[0].caching="ReadWrite"', checks=[
            self.check('storageProfile.dataDisks[0].caching', 'ReadWrite')
        ])
        self.cmd('vm update -g {rg} -n {vm} --remove storageProfile.dataDisks', checks=[
            self.check('storageProfile.dataDisks', [])
        ])


class DedicatedHostScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_host_management_')
    def test_vm_host_management(self, resource_group):
        self.kwargs.update({
            'host-group': 'my-host-group',
            'host': 'my-host',
        })

        self.cmd('vm host group create -n {host-group} -c 3 -g {rg}')
        self.cmd('vm host group list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{host-group}')
        ])
        self.cmd('vm host create -n {host} --host-group {host-group} -d 2 -g {rg} --sku DSv3-Type1')
        self.cmd('vm host list --host-group {host-group} -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{host}')
        ])

        self.cmd('vm host group update -n {host-group} -g {rg} --set tags.foo="bar"', checks=[
            self.check('tags.foo','bar')
        ])
        self.cmd('vm host update -n {host} --host-group {host-group} -g {rg} --set tags.foo="bar"', checks=[
            self.check('tags.foo', 'bar')
        ])

        self.cmd('vm host delete -n {host} --host-group {host-group} -g {rg} --yes')
        self.cmd('vm host group delete -n {host-group} -g {rg} --yes')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_dedicated_host_', location='westeurope')
    @ResourceGroupPreparer(name_prefix='cli_test_dedicated_host2_', location='eastus', key='rg2')
    def test_dedicated_host_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'host-group': 'my-host-group',
            'host-name': 'my-host',
            'vm-name': 'ded-host-vm'
        })

        # create resources
        self.cmd('vm host group create -n {host-group} -c 3 -g {rg} --tags "foo=bar"', checks=[
            self.check('name', '{host-group}'),
            self.check('platformFaultDomainCount', 3),
            self.check('tags.foo', 'bar')
        ])

        try:
            self.cmd('vm host create -n {host-name} --host-group {host-group} -d 2 -g {rg} '
                     '--sku DSv3-Type1 --auto-replace false --tags "bar=baz" ', checks=[
                         self.check('name', '{host-name}'),
                         self.check('platformFaultDomain', 2),
                         self.check('sku.name', 'DSv3-Type1'),
                         self.check('autoReplaceOnFailure', False),
                         self.check('tags.bar', 'baz')
                     ])

        except CLIError as e:
            if 'capacity' in str(e):
                return

        result = self.cmd('vm host get-instance-view --host-group {host-group} --name {host-name} -g {rg}', checks=[
            self.check('name', '{host-name}'),
        ]).get_output_in_json()
        instance_view = result["instanceView"]
        self.assertTrue(instance_view["assetId"])
        self.assertTrue(instance_view["availableCapacity"])

        self.cmd('vm host group get-instance-view -g {rg} -n {host-group}', checks=[
            self.exists('instanceView')
        ])

        host_id = self.cmd('vm host show -g {rg} -n {host-name} --host-group {host-group}').get_output_in_json()['id']
        self.kwargs.update({
            'host_id': host_id
        })

        self.cmd('vm create -n {vm-name} --image Debian:debian-10:10:latest -g {rg} --size Standard_D4s_v3 '
                 '--host {host_id} --generate-ssh-keys --admin-username azureuser --nsg-rule NONE')

        # validate resources created successfully
        vm_json = self.cmd('vm show -n {vm-name} -g {rg}', checks=[
            self.check('name', '{vm-name}'),
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()

        host_json = self.cmd('vm host show --name {host-name} --host-group {host-group} -g {rg}', checks=[
            self.check('name', '{host-name}'),
        ]).get_output_in_json()

        host_group_json = self.cmd('vm host group show --name {host-group} -g {rg}', checks=[
            self.check('name', '{host-group}'),
        ]).get_output_in_json()

        self.assertTrue(vm_json['host']['id'].lower(), host_json['id'].lower())
        self.assertTrue(host_json['virtualMachines'][0]['id'].lower(), vm_json['id'].lower())
        self.assertTrue(host_group_json['hosts'][0]['id'].lower(), host_json['id'].lower())

        # delete resources (test vm host delete commands)
        self.cmd('vm delete --name {vm-name} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host delete --name {host-name} --host-group {host-group} -g {rg} --yes')
        # Service has problem. It is not deleted yet but it returns.
        time.sleep(30)
        self.cmd('vm host group delete --name {host-group} -g {rg} --yes')

        # Test --automatic-placement
        self.cmd('vm host group create -n {host-group} -c 1 -g {rg2} --automatic-placement', checks=[
            self.check('supportAutomaticPlacement', True),
        ])
        host_id = self.cmd('vm host create -n {host-name} --host-group {host-group} -d 0 -g {rg2} --sku DSv3-Type1').get_output_in_json()['id']
        self.kwargs.update({
            'host_id': host_id
        })
        self.cmd('vm create -g {rg2} -n vm1 --image OpenLogic:CentOS:7.5:latest --host {host_id} --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm create -g {rg2} -n vm2 --image OpenLogic:CentOS:7.5:latest --host-group {host-group} --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm show -g {rg2} -n vm1', checks=[
            self.check_pattern('host.id', '.*/{host-name}$')
        ])
        self.cmd('vm show -g {rg2} -n vm2', checks=[
            self.check_pattern('hostGroup.id', '.*/{host-group}$')
        ])
        self.cmd('vm delete --name vm1 -g {rg2} --yes')
        self.cmd('vm delete --name vm2 -g {rg2} --yes')
        self.cmd('vm host delete --name {host-name} --host-group {host-group} -g {rg2} --yes')

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_dedicated_host_', location='westus2')
    def test_update_dedicated_host_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'host-group': 'my-host-group',
            'host-name': 'my-host',
            'host2-group': 'my-host2-group',
            'host2-name': 'my-host2',
            'vm-name': 'ded-host-vm',
        })

        # create resources
        self.cmd('vm host group create -n {host-group} -c 3 -g {rg} --tags "foo=bar"', checks=[
            self.check('name', '{host-group}'),
            self.check('platformFaultDomainCount', 3),
            self.check('tags.foo', 'bar')
        ])

        self.cmd('vm host group create -n {host2-group} -c 3 -g {rg} --tags "foo=bar"', checks=[
            self.check('name', '{host2-group}'),
            self.check('platformFaultDomainCount', 3),
            self.check('tags.foo', 'bar')
        ])

        try:
            self.cmd('vm host create -n {host-name} --host-group {host-group} -d 2 -g {rg} '
                     '--sku DSv3-Type1 --auto-replace false --tags "bar=baz" ', checks=[
                self.check('name', '{host-name}'),
                self.check('platformFaultDomain', 2),
                self.check('sku.name', 'DSv3-Type1'),
                self.check('autoReplaceOnFailure', False),
                self.check('tags.bar', 'baz')
            ])

        except CLIError as e:
            if 'capacity' in str(e):
                return

        try:
            self.cmd('vm host create -n {host2-name} --host-group {host2-group} -d 2 -g {rg} '
                     '--sku DSv3-Type1 --auto-replace false --tags "bar=baz" ', checks=[
                self.check('name', '{host2-name}'),
                self.check('platformFaultDomain', 2),
                self.check('sku.name', 'DSv3-Type1'),
                self.check('autoReplaceOnFailure', False),
                self.check('tags.bar', 'baz')
            ])

        except CLIError as e:
            if 'capacity' in str(e):
                return

        result = self.cmd('vm host get-instance-view --host-group {host-group} --name {host-name} -g {rg}', checks=[
            self.check('name', '{host-name}'),
        ]).get_output_in_json()
        instance_view = result["instanceView"]
        self.assertTrue(instance_view["assetId"])
        self.assertTrue(instance_view["availableCapacity"])

        result = self.cmd('vm host get-instance-view --host-group {host2-group} --name {host2-name} -g {rg}', checks=[
            self.check('name', '{host2-name}'),
        ]).get_output_in_json()
        instance_view = result["instanceView"]
        self.assertTrue(instance_view["assetId"])
        self.assertTrue(instance_view["availableCapacity"])

        self.cmd('vm host group get-instance-view -g {rg} -n {host-group}', checks=[
            self.exists('instanceView')
        ])

        self.cmd('vm host group get-instance-view -g {rg} -n {host2-group}', checks=[
            self.exists('instanceView')
        ])

        host_id = self.cmd('vm host show -g {rg} -n {host-name} --host-group {host-group}').get_output_in_json()['id']
        host2_id = self.cmd('vm host show -g {rg} -n {host2-name} --host-group {host2-group}').get_output_in_json()['id']
        self.kwargs.update({
            'host_id': host_id,
            'host2_id': host2_id
        })

        self.cmd('vm create -n {vm-name} --image Debian:debian-10:10:latest -g {rg} --size Standard_D4s_v3 '
                 '--generate-ssh-keys --admin-username azureuser --nsg-rule NONE')

        # validate resources created successfully
        vm_json = self.cmd('vm show -n {vm-name} -g {rg}', checks=[
            self.check('name', '{vm-name}'),
            self.check('provisioningState', 'Succeeded')
        ]).get_output_in_json()
        self.assertEqual(vm_json['host'], None)

        # validate none host to host
        self.cmd('vm deallocate -n {vm-name} -g {rg}')
        self.cmd('vm update -n {vm-name} -g {rg} --host {host_id} --set tags.tagName=tagValue')
        self.cmd('vm start -n {vm-name} -g {rg}')

        self.cmd('vm show -n {vm-name} -g {rg}', checks=[
            self.check('name', '{vm-name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check_pattern('host.id', '.*/{host-name}$'),
            # Test --update multiple arguments
            self.check('tags.tagName', 'tagValue'),
        ])

        # validate host to host2
        self.cmd('vm deallocate -n {vm-name} -g {rg}')
        self.cmd('vm update -n {vm-name} -g {rg} --host {host2_id} --set tags.tagName=tagValue')
        self.cmd('vm start -n {vm-name} -g {rg}')

        self.cmd('vm show -n {vm-name} -g {rg}', checks=[
            self.check('name', '{vm-name}'),
            self.check('provisioningState', 'Succeeded'),
            self.check_pattern('host.id', '.*/{host2-name}$'),
            # Test --update multiple arguments
            self.check('tags.tagName', 'tagValue'),
        ])

        # delete resources (test vm host delete commands)
        # Service has problem. It is not deleted yet but it returns.
        self.cmd('vm delete --name {vm-name} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host delete --name {host-name} --host-group {host-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host delete --name {host2-name} --host-group {host2-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host group delete --name {host-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host group delete --name {host2-group} -g {rg} --yes')
        time.sleep(30)

        # Test --automatic-placement
        self.cmd('vm host group create -n {host-group} -c 1 -g {rg} --automatic-placement', checks=[
            self.check('supportAutomaticPlacement', True),
        ])
        self.cmd('vm host group create -n {host2-group} -c 1 -g {rg} --automatic-placement', checks=[
            self.check('supportAutomaticPlacement', True),
        ])
        host_id = self.cmd('vm host create -n {host-name} --host-group {host-group} -d 0 -g {rg} --sku DSv3-Type1').get_output_in_json()['id']
        host2_id = self.cmd('vm host create -n {host2-name} --host-group {host2-group} -d 0 -g {rg} --sku DSv3-Type1').get_output_in_json()['id']
        self.kwargs.update({
            'host_id': host_id,
            'host2_id': host2_id
        })
        self.cmd('vm create -g {rg} -n vm1 --image OpenLogic:CentOS:7.5:latest --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm create -g {rg} -n vm2 --image OpenLogic:CentOS:7.5:latest --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm show -g {rg} -n vm1', checks=[
            self.check('host', None)
        ])
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check('hostGroup', None)
        ])

        # validate none host to host
        self.cmd('vm deallocate -n vm1 -g {rg}')
        self.cmd('vm update -n vm1 -g {rg} --host {host_id}')
        self.cmd('vm start -n vm1 -g {rg}')
        self.cmd('vm show -g {rg} -n vm1', checks=[
            self.check_pattern('host.id', '.*/{host-name}$')
        ])

        # validate host to host2
        self.cmd('vm deallocate -n vm1 -g {rg}')
        self.cmd('vm update -n vm1 -g {rg} --host {host2_id}')
        self.cmd('vm start -n vm1 -g {rg}')
        self.cmd('vm show -g {rg} -n vm1', checks=[
            self.check_pattern('host.id', '.*/{host2-name}$')
        ])

        # validate none group to group
        self.cmd('vm deallocate -n vm2 -g {rg}')
        self.cmd('vm update -n vm2 -g {rg} --host-group {host-group}')
        self.cmd('vm start -n vm2 -g {rg}')
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check_pattern('hostGroup.id', '.*/{host-group}$')
        ])

        # validate group to group2
        self.cmd('vm deallocate -n vm2 -g {rg}')
        self.cmd('vm update -n vm2 -g {rg} --host-group {host2-group}')
        self.cmd('vm start -n vm2 -g {rg}')
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check_pattern('hostGroup.id', '.*/{host2-group}$')
        ])

        # validate group2 to host
        self.cmd('vm deallocate -n vm2 -g {rg}')
        self.cmd('vm update -n vm2 -g {rg} --host {host_id}')
        self.cmd('vm start -n vm2 -g {rg}')
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check_pattern('host.id', '.*/{host-name}$')
        ])

        # validate host to group2
        self.cmd('vm deallocate -n vm2 -g {rg}')
        self.cmd('vm update -n vm2 -g {rg} --host-group {host2-group}')
        self.cmd('vm start -n vm2 -g {rg}')
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check_pattern('hostGroup.id', '.*/{host2-group}$')
        ])

        # delete resources (test vm host delete commands)
        # Service has problem. It is not deleted yet but it returns.
        self.cmd('vm delete --name vm1 -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm delete --name vm2 -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host delete --name {host-name} --host-group {host-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host delete --name {host2-name} --host-group {host2-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host group delete --name {host-group} -g {rg} --yes')
        time.sleep(30)
        self.cmd('vm host group delete --name {host2-group} -g {rg} --yes')
        time.sleep(30)
# endregion


# region ppg tests
class ProximityPlacementGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix="cli_test_ppg_cmds_")
    def test_proximity_placement_group(self, resource_group, resource_group_location):
        self.kwargs.update({
            'ppg1': 'my_ppg_1',
            'ppg2': 'my_ppg_2',
            'ppg3': 'my_ppg_3',
            'loc': resource_group_location
        })

        self.cmd('ppg create -n {ppg1} -t StandarD -g {rg}', checks=[
            self.check('name', '{ppg1}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Standard')
        ])

        self.cmd('ppg show -g {rg} -n {ppg1} --include-colocation-status', checks=[
            self.check('name', '{ppg1}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Standard'),
            self.exists('colocationStatus')
        ])

        self.cmd('ppg create -n {ppg2} -t Standard -g {rg}', checks=[
            self.check('name', '{ppg2}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Standard')
        ])

        self.cmd('ppg create -n {ppg3} -g {rg}', checks=[
            self.check('name', '{ppg3}'),
            self.check('location', '{loc}'),
        ])

        self.cmd('ppg list -g {rg}', checks=[
            self.check('length(@)', 3)
        ])
        self.cmd('ppg delete -n {ppg1} -g {rg}')
        self.cmd('ppg list -g {rg}', checks=[
            self.check('length(@)', 2),
        ])

        self.cmd('ppg update -n {ppg3} -g {rg} --set tags.foo="bar"', checks=[
            self.check('tags.foo', 'bar')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_ppg_vm_vmss_')
    def test_ppg_with_related_resources(self, resource_group):

        self.kwargs.update({
            'ppg': 'myppg',
            'vm': 'vm1',
            'vmss': 'vmss1',
            'avset': 'avset1',
            'ssh_key': TEST_SSH_KEY_PUB,
            'nsg': 'nsg1',
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -n {ppg} -t standard -g {rg}').get_output_in_json()['id']

        self.kwargs['vm_id'] = self.cmd(
            'vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --admin-username debian --ssh-key-value \'{ssh_key}\' --ppg {ppg} --nsg-rule NONE').get_output_in_json()[
            'id']

        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd(
            'vmss create -g {rg} -n {vmss} --image Debian:debian-10:10:latest --admin-username debian --ssh-key-value \'{ssh_key}\' --ppg {ppg_id} --nsg {nsg}')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.kwargs['avset_id'] = \
        self.cmd('vm availability-set create -g {rg} -n {avset} --ppg {ppg}').get_output_in_json()['id']

        ppg_resource = self.cmd('ppg show -n {ppg} -g {rg}').get_output_in_json()

        # check that the compute resources are created with PPG

        self._assert_ids_equal(ppg_resource['availabilitySets'][0]['id'], self.kwargs['avset_id'],
                               rg_prefix='cli_test_ppg_vm_vmss_')
        self._assert_ids_equal(ppg_resource['virtualMachines'][0]['id'], self.kwargs['vm_id'],
                               rg_prefix='cli_test_ppg_vm_vmss_')
        self._assert_ids_equal(ppg_resource['virtualMachineScaleSets'][0]['id'], self.kwargs['vmss_id'],
                               'cli_test_ppg_vm_vmss_')

    @ResourceGroupPreparer(name_prefix='cli_test_ppg_update_')
    def test_ppg_update(self, resource_group):
        self.kwargs.update({
            'ppg': 'ppg1',
            'vm': 'vm1',
            'vmss': 'vmss1',
            'avset': 'avset1',
            'ssh_key': TEST_SSH_KEY_PUB,
            'nsg': 'nsg1',
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -g {rg} -n {ppg} -t standard').get_output_in_json()['id']

        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('vmss create -g {rg} -n {vmss} --image Debian:debian-10:10:latest --admin-username debian --ssh-key-value \'{ssh_key}\' --nsg {nsg}')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']
        self.cmd('vmss deallocate -g {rg} -n {vmss}')
        time.sleep(30)
        self.cmd('vmss update -g {rg} -n {vmss} --ppg {ppg_id}')

        self.cmd(
            'vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --admin-username debian --ssh-key-value \'{ssh_key}\' --nsg-rule NONE')
        self.kwargs['vm_id'] = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()['id']
        self.cmd('vm deallocate -g {rg} -n {vm}')
        time.sleep(30)
        self.cmd('vm update -g {rg} -n {vm} --ppg {ppg_id}')

        self.kwargs['avset_id'] = self.cmd('vm availability-set create -g {rg} -n {avset}').get_output_in_json()['id']
        self.cmd('vm availability-set update -g {rg} -n {avset} --ppg {ppg_id}')

        ppg_resource = self.cmd('ppg show -n {ppg} -g {rg}').get_output_in_json()

        self._assert_ids_equal(ppg_resource['availabilitySets'][0]['id'], self.kwargs['avset_id'],
                               rg_prefix='cli_test_ppg_update_')
        self._assert_ids_equal(ppg_resource['virtualMachines'][0]['id'], self.kwargs['vm_id'],
                               rg_prefix='cli_test_ppg_update_')
        self._assert_ids_equal(ppg_resource['virtualMachineScaleSets'][0]['id'], self.kwargs['vmss_id'],
                               'cli_test_ppg_update_')

    # it would be simpler to do the following:
    # self.assertEqual(ppg_resource['availabilitySets'][0]['id'].lower(), self.kwargs['avset_id'].lower())
    # self.assertEqual(ppg_resource['virtualMachines'][0]['id'].lower(), self.kwargs['vm_id'].lower())
    # self.assertEqual(ppg_resource['virtualMachineScaleSets'][0]['id'].lower(), self.kwargs['vmss_id'].lower())
    #
    # however, the CLI does not replace resource group values in payloads in the recordings.
    def _assert_ids_equal(self, id_1, id_2, rg_prefix=None):
        from azure.mgmt.core.tools import parse_resource_id

        id_1, id_2, rg_prefix = id_1.lower(), id_2.lower(), rg_prefix.lower() if rg_prefix else rg_prefix

        parsed_1, parsed_2 = parse_resource_id(id_1), parse_resource_id(id_2)

        self.assertEqual(len(parsed_1.keys()), len(parsed_2.keys()))

        for k1, k2 in zip(sorted(parsed_1.keys()), sorted(parsed_2.keys())):
            if rg_prefix is not None and k1 == 'resource_group':
                self.assertTrue(parsed_1[k1].startswith(rg_prefix))
                self.assertTrue(parsed_2[k2].startswith(rg_prefix))
            else:
                self.assertEqual(parsed_1[k1], parsed_2[k2])
# endregion


class VMGalleryImage(ScenarioTest):

    @ResourceGroupPreparer(location='westus')
    def test_gallery_image(self, resource_group):
        self.kwargs.update({
            'gallery': self.create_random_name('sig_', 10),
            'image': 'image1',
            'disk': 'disk',
            'snapshot': 'snapshot',
            'version': '1.0.0',
        })

        self.cmd('sig create -g {rg} -r {gallery}', checks=[
            self.check('location', 'westus'),
            self.check('name', '{gallery}'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('sig list -g {rg}', checks=self.check('length(@)', 1))

        self.cmd(
            'sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1',
            checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition list -g {rg} --gallery-name {gallery}', checks=self.check('length(@)', 1))
        res = self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image}',
                       checks=self.check('name', self.kwargs['image'])).get_output_in_json()

        self.cmd('snapshot create -g {rg} -n {snapshot} --size-gb 1 --sku Premium_LRS --tags tag1=s1')
        self.cmd('sig image-version create --resource-group {rg} --gallery-name {gallery} '
                 '--gallery-image-definition {image} --gallery-image-version {version} --os-snapshot {snapshot}',
                 checks=[
                     self.check('provisioningState', 'Succeeded')
                 ])

        self.cmd('sig image-version show -g {rg} -r {gallery} -i {image} -e {version}', checks=[
            self.check('name', '{version}')
        ])

        self.cmd('sig image-version list -g {rg} -r {gallery} -i {image}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{version}')
        ])
        self.cmd('sig image-version delete -g {rg} -r {gallery} -i {image} -e {version}')
        time.sleep(60)

        self.cmd('sig image-definition delete -g {rg} --gallery-name {gallery} --gallery-image-definition {image}')
        time.sleep(60)  # service end latency
        self.cmd('sig delete -g {rg} --gallery-name {gallery}')
# endregion


class DiskAccessTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_access_', location='centraluseuap')
    def test_disk_access(self, resource_group):
        self.kwargs.update({
            'loc': 'centraluseuap',
            'diskaccess': 'mydiskaccess',
            'disk': 'mydisk',
            'snapshot': 'mysnapshot'
        })

        self.cmd('disk-access create -g {rg} -l {loc} -n {diskaccess} --no-wait')
        self.cmd('disk-access wait --created -g {rg} -n {diskaccess}')
        self.cmd('disk-access list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{diskaccess}'),
            self.check('[0].location', '{loc}')
        ])

        self.cmd('disk-access update -g {rg} -n {diskaccess} --tags tag1=val1')
        self.kwargs['disk_access_id'] = self.cmd('disk-access show -g {rg} -n {diskaccess}', checks=[
            self.check('name', '{diskaccess}'),
            self.check('location', '{loc}'),
            self.check('tags.tag1', 'val1')
        ]).get_output_in_json()['id']

        self.cmd('disk create -g {rg} -n {disk} --size-gb 10 --network-access-policy AllowPrivate --disk-access {diskaccess}')

        self.cmd('disk update -g {rg} -n {disk} --network-access-policy AllowPrivate --disk-access {disk_access_id}')

        self.cmd('disk show -g {rg} -n {disk}', checks=[
            self.check('name', '{disk}')
        ])

        self.cmd('disk delete -g {rg} -n {disk} --yes')
        self.cmd('disk-access delete -g {rg} -n {diskaccess}')
        self.cmd('disk-access list -g {rg}', checks=[
            self.check('length(@)', 0)
        ])


class DiskEncryptionSetTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_', location='westcentralus')
    @KeyVaultPreparer(name_prefix='vault-', name_len=20, key='vault', location='westcentralus', additional_params='--enable-purge-protection --enable-rbac-authorization false')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set(self, resource_group, key_vault):
        self.kwargs.update({
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'des2': self.create_random_name(prefix='des2-', length=20),
            'des3': self.create_random_name(prefix='des3-', length=20),
            'disk': self.create_random_name(prefix='disk-', length=20),
            'vm1': self.create_random_name(prefix='vm1-', length=20),
            'vm2': self.create_random_name(prefix='vm2-', length=20),
            'vmss': self.create_random_name(prefix='vmss-', length=20),
        })

        self.cmd('keyvault update -g {rg} -n {vault} --set properties.enableSoftDelete=true')
        vault_id = self.cmd('keyvault show -g {rg} -n {vault}').get_output_in_json()['id']
        kid = self.cmd('keyvault key create -n {key} --vault {vault} --protection software').get_output_in_json()['key']['kid']
        self.kwargs.update({
            'vault_id': vault_id,
            'kid': kid
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des1} --key-url {kid} --source-vault {vault}')
        des1_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des1}').get_output_in_json()
        des1_sp_id = des1_show_output['identity']['principalId']
        des1_id = des1_show_output['id']
        self.kwargs.update({
            'des1_sp_id': des1_sp_id,
            'des1_id': des1_id
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des2} --key-url {kid} --source-vault {vault}')
        des2_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des2}').get_output_in_json()
        des2_sp_id = des2_show_output['identity']['principalId']
        des2_id = des2_show_output['id']
        self.kwargs.update({
            'des2_sp_id': des2_sp_id,
            'des2_id': des2_id
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des3} --key-url {kid} --source-vault {vault}')
        des3_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des3}').get_output_in_json()
        des3_sp_id = des3_show_output['identity']['principalId']
        des3_id = des3_show_output['id']
        self.kwargs.update({
            'des3_sp_id': des3_sp_id,
            'des3_id': des3_id
        })

        self.cmd('keyvault set-policy -n {vault} -g {rg} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('keyvault set-policy -n {vault} -g {rg} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('keyvault set-policy -n {vault} -g {rg} --object-id {des3_sp_id} --key-permissions wrapKey unwrapKey get')

        self.kwargs.update({
            'des1_pattern': '.*/{}$'.format(self.kwargs['des1']),
            'des2_pattern': '.*/{}$'.format(self.kwargs['des2']),
            'des3_pattern': '.*/{}$'.format(self.kwargs['des3'])
        })

        self.cmd('disk create -g {rg} -n {disk} --encryption-type EncryptionAtRestWithCustomerKey --disk-encryption-set {des1} --size-gb 10', checks=[
            self.check_pattern('encryption.diskEncryptionSetId', self.kwargs['des1_pattern']),
            self.check('encryption.type', 'EncryptionAtRestWithCustomerKey')
        ])
        self.cmd('vm create -g {rg} -n {vm1} --attach-os-disk {disk} --os-type linux --nsg-rule NONE')

        self.cmd('vm create -g {rg} -n {vm2} --image OpenLogic:CentOS:7.5:latest --os-disk-encryption-set {des1} --data-disk-sizes-gb 10 10 --data-disk-encryption-sets {des2} {des3} --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check_pattern('storageProfile.osDisk.managedDisk.diskEncryptionSet.id', self.kwargs['des1_pattern']),
            self.check_pattern('storageProfile.dataDisks[0].managedDisk.diskEncryptionSet.id', self.kwargs['des2_pattern']),
            self.check_pattern('storageProfile.dataDisks[1].managedDisk.diskEncryptionSet.id', self.kwargs['des3_pattern'])
        ])

        self.cmd('vmss create -g {rg} -n {vmss} --image OpenLogic:CentOS:7.5:latest --os-disk-encryption-set {des1} --data-disk-sizes-gb 10 10 --data-disk-encryption-sets {des2} {des3} --admin-username azureuser --admin-password testPassword0 --authentication-type password --nsg ""')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check_pattern('virtualMachineProfile.storageProfile.osDisk.managedDisk.diskEncryptionSet.id', self.kwargs['des1_pattern']),
            self.check_pattern('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.diskEncryptionSet.id', self.kwargs['des2_pattern']),
            self.check_pattern('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.diskEncryptionSet.id', self.kwargs['des3_pattern'])
        ])


class VMRedeployTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_vm_redeploy_')
    def test_vm_redeploy(self, resource_group):
        self.kwargs.update({
            'vm':'myvm'
        })

        self.cmd('vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm reapply -n {vm} -g {rg}')
        self.cmd('vm redeploy -n {vm} -g {rg}')


class VMConvertTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_vm_convert_')
    def test_vm_convert(self, resource_group):
        self.kwargs.update({
            'vm': 'myvm'
        })

        self.cmd(
            'vm create -g {rg} -n {vm} --image Debian:debian-10:10:latest --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} --new --size-gb 1')

        output = self.cmd('vm unmanaged-disk list --vm-name {vm} -g {rg}').get_output_in_json()
        self.assertFalse(output[0]['managedDisk'])
        self.assertTrue(output[0]['vhd'])

        self.cmd('vm deallocate -n {vm} -g {rg}')
        self.cmd('vm convert -n {vm} -g {rg}')

        converted = self.cmd('vm unmanaged-disk list --vm-name {vm} -g {rg}').get_output_in_json()
        self.assertTrue(converted[0]['managedDisk'])
        self.assertFalse(converted[0]['vhd'])


class VMSimulateEvictionScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_simulate_eviction')
    def test_vm_simulate_eviction(self, resource_group):

        self.kwargs.update({
            'loc': 'eastus',
            'vm1': 'vm-simualte-eviction1',
            'vm2': 'vm-simulate-eviction2',
            'vm3': 'vm-simulate-eviction3'
        })

        # simulate-eviction on a Regular VM, expect failure
        self.cmd('vm create --resource-group {rg} --name {vm1} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image OpenLogic:CentOS:7.5:latest --priority Regular --nsg-rule NONE')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm1}', expect_failure=True)

        # simulate-eviction on a Spot VM with Deallocate policy, expect VM to be deallocated
        self.cmd('vm create --resource-group {rg} --name {vm2} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image OpenLogic:CentOS:7.5:latest --priority Spot --eviction-policy Deallocate --nsg-rule NONE')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm2}')
        time.sleep(180)
        self.cmd('vm get-instance-view --resource-group {rg} --name {vm2}', checks=[
            self.check('name', '{vm2}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(instanceView.statuses)', 2),
            self.check('instanceView.statuses[0].code', 'ProvisioningState/succeeded'),
            self.check('instanceView.statuses[1].code', 'PowerState/deallocated'),
        ])

        # simulate-eviction on a Spot VM with Delete policy, expect VM to be deleted
        self.cmd('vm create --resource-group {rg} --name {vm3} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image OpenLogic:CentOS:7.5:latest --priority Spot --eviction-policy Delete --nsg-rule NONE')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm3}')
        time.sleep(180)
        self.cmd('vm list --resource-group {rg}', checks=[self.check('length(@)', 2)])
        self.cmd('vm show --resource-group {rg} --name {vm3}', expect_failure=True)


class VMRestartTest(ScenarioTest):
    def _check_vm_power_state(self, expected_power_state):

        self.cmd('vm get-instance-view --resource-group {rg} --name {vm}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{vm}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(instanceView.statuses)', 2),
            self.check('instanceView.statuses[0].code', 'ProvisioningState/succeeded'),
            self.check('instanceView.statuses[1].code', expected_power_state),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_stop_start')
    def test_vm_stop_start(self, resource_group):
        self.kwargs.update({
            'vm': 'vm'
        })
        self.cmd(
            'vm create --resource-group {rg} --name {vm} --admin-username azureuser --admin-password testPassword0 --authentication-type password --image OpenLogic:CentOS:7.5:latest --priority Regular --nsg-rule NONE')

        self.cmd('vm stop --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/stopped')
        self.cmd('vm start --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/running')


class VMAutoUpdateScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_linux_vm_patch_mode_')
    def test_linux_vm_patch_mode(self, resource_group):
        self.cmd('vm create -g {rg} -n vm1 --image Canonical:UbuntuServer:18.04-LTS:latest --enable-agent --generate-ssh-keys --nsg-rule NONE --admin-username vmtest')

        self.cmd('vm assess-patches -g {rg} -n vm1', checks=[
            self.check('status', 'Succeeded')
        ])


class VMSSSimulateEvictionScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_simulate_eviction')
    def test_vmss_simulate_eviction(self, resource_group):

        self.kwargs.update({
            'loc': 'eastus',
            'vmss1': 'vmss-simualte-eviction1',
            'vmss2': 'vmss-simulate-eviction2',
            'vmss3': 'vmss-simulate-eviction3',
            'instance_ids': []
        })

        # simulate-eviction on a Regular VMSS, expect failure
        self.cmd('vmss create --resource-group {rg} --name {vmss1} --location {loc} --instance-count 2 --image OpenLogic:CentOS:7.5:latest --priority Regular --admin-username vmtest')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss1}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss1} --instance-id {id}', expect_failure=True)

        # simulate-eviction on a Spot VMSS with Deallocate policy, expect VMSS instance to be deallocated
        self.cmd('vmss create --resource-group {rg} --name {vmss2} --location {loc} --instance-count 2 --image OpenLogic:CentOS:7.5:latest --priority Spot --eviction-policy Deallocate --single-placement-group True --admin-username vmtest')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss2}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss2} --instance-id {id}')

        # simulate-eviction on a Spot VMSS with Delete policy, expect VMSS instance to be deleted
        self.cmd('vmss create --resource-group {rg} --name {vmss3} --location {loc} --instance-count 2 --image OpenLogic:CentOS:7.5:latest --priority Spot --eviction-policy Delete --single-placement-group True --admin-username vmtest')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss3} --instance-id {id}')
        time.sleep(180)
        self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}', checks=[self.check('length(@)', len(self.kwargs['instance_ids']) - 1)])
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss3} --instance-id {id}', expect_failure=True)
# endregion


class VMAvailSetScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_vm_availset(self, resource_group):

        self.kwargs.update({
            'availset': 'availset-test'
        })
        self.cmd('vm availability-set create -g {rg} -n {availset}', checks=[
            self.check('name', '{availset}'),
            self.check('platformFaultDomainCount', 2),
            self.check('platformUpdateDomainCount', 5),  # server defaults to 5
            self.check('sku.name', 'Aligned')
        ])

        # create with explict UD count
        self.cmd('vm availability-set create -g {rg} -n avset2 --platform-fault-domain-count 2 --platform-update-domain-count 2', checks=[
            self.check('platformFaultDomainCount', 2),
            self.check('platformUpdateDomainCount', 2),
            self.check('sku.name', 'Aligned')
        ])
        self.cmd('vm availability-set delete -g {rg} -n avset2')

        self.cmd('vm availability-set update -g {rg} -n {availset} --set tags.test=success',
                 checks=self.check('tags.test', 'success'))
        self.cmd('vm availability-set list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{availset}')
        ])
        result = self.cmd('vm availability-set list --query "[?name==\'availset-test\']"').get_output_in_json()
        self.assertEqual(1, len(result))
        self.cmd('vm availability-set list-sizes -g {rg} -n {availset}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('vm availability-set show -g {rg} -n {availset}',
                 checks=[self.check('name', '{availset}')])
        self.cmd('vm availability-set delete -g {rg} -n {availset}')
        self.cmd('vm availability-set list -g {rg}',
                 checks=self.check('length(@)', 0))
# endregion


class TestSnapShotAccess(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_snapshot_access_')
    def test_snapshot_access(self, resource_group):
        self.kwargs.update({
            'snapshot': 'snapshot'
        })

        self.cmd('snapshot create -n {snapshot} -g {rg} --size-gb 1')
        self.cmd('snapshot grant-access --duration-in-seconds 600 -n {snapshot} -g {rg}')
        self.cmd('snapshot show -n {snapshot} -g {rg}')
        self.cmd('snapshot list -g {rg}',
                 checks=[
                     self.check('length(@)', '1'),
                 ])
        self.cmd('snapshot revoke-access -n {snapshot} -g {rg}')
        self.cmd('snapshot delete -n {snapshot} -g {rg}')
# endregion

# endregion


if __name__ == '__main__':
    unittest.main()
