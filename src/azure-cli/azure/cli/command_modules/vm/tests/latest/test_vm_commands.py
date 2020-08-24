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
import mock
import uuid

from knack.util import CLIError
from azure_devtools.scenario_tests import AllowLargeResponse, record_only, live_only
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer, JMESPathCheck, StringContainCheck)
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"
TEST_SSH_KEY_PUB_2 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCof7rG2sYVyHSDPp4lbrq5zu8N8D7inS4Qb+ZZ5Kh410znTcoVJSNsLOhrM2COxg5LXca3DQMBi4S/V8UmMnwxwDVf38GvU+0QVDR6vSO6lPlj2OpPLk4OEdTv3qcj/gpEBvv1RCacpFuu5bL546r4BqG4f0dJXqBd5tT4kjpO9ytOZ1Wkg8tA35UvbucVAsDBfOZ5GtsnflPtKCY9h20LeXEjyDZ8eFzAGH/vNrfWPiWWznwN9EoPghIQHCiC0mnJgdsABraUzeTTMjxahi0DXBxb5dsKd6YbJxQw/V+AohVMPfPvs9y95Aj7IxM2zrtgBswC8bT0z678svTJSFX9 test@example.com"


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


class VMImageListByAliasesScenarioTest(ScenarioTest):

    def test_vm_image_list_by_alias(self):
        result = self.cmd('vm image list --offer ubuntu').get_output_in_json()
        self.assertTrue(len(result) >= 1)
        self.assertEqual(result[0]['publisher'], 'Canonical')
        self.assertTrue(result[0]['sku'].endswith('LTS'))


class VMUsageScenarioTest(ScenarioTest):

    def test_vm_usage(self):
        self.cmd('vm list-usage --location westus',
                 checks=self.check('type(@)', 'array'))


class VMImageListThruServiceScenarioTest(ScenarioTest):

    # Replay mode has problem
    @live_only()
    @AllowLargeResponse()
    def test_vm_images_list_thru_services(self):
        result = self.cmd('vm image list -l westus --publisher Canonical --offer UbuntuServer -o tsv --all').output
        assert result.index('16.04') >= 0

        result = self.cmd('vm image list -p Canonical -f UbuntuServer -o tsv --all').output
        assert result.index('16.04') >= 0


class VMOpenPortTest(ScenarioTest):

    @unittest.skip('We don\'t have an environment that allows opening ports. Funny.')
    @ResourceGroupPreparer(name_prefix='cli_test_open_port')
    def test_vm_open_port(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -l westus -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password @PasswordPassword1! --public-ip-address-allocation dynamic --authentication-type password --nsg-rule NONE')

        # min params - apply to existing NIC (updates existing NSG)
        self.kwargs['nsg_id'] = self.cmd('vm open-port -g {rg} -n {vm} --port "*" --priority 900').get_output_in_json()['id']
        self.kwargs['nsg'] = os.path.split(self.kwargs['nsg_id'])[1]
        self.cmd('network nsg show -g {rg} -n {nsg}',
                 checks=self.check("length(securityRules[?name == 'open-port-all'])", 1))

        # apply to subnet (creates new NSG)
        self.kwargs['nsg'] = 'newNsg'
        self.cmd('vm open-port -g {rg} -n {vm} --apply-to-subnet --nsg-name {nsg} --port "*" --priority 900')
        self.cmd('network nsg show -g {rg} -n {nsg}',
                 checks=self.check("length(securityRules[?name == 'open-port-all'])", 1))


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
        self.cmd('vm create --resource-group {rg} --location {loc} -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest'
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
        self.cmd('vm list-ip-addresses --resource-group {rg_caps}', checks=[
            self.check('length(@)', 1),
            self.check('[0].virtualMachine.name', '{vm}'),
            self.check('[0].virtualMachine.resourceGroup', '{rg}'),
            self.check('length([0].virtualMachine.network.publicIpAddresses)', 1),
            self.check('[0].virtualMachine.network.publicIpAddresses[0].ipAllocationMethod', self.kwargs['allocation'].title()),
            self.check('type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)', 'string'),
            self.check('[0].virtualMachine.network.publicIpAddresses[0].zone', '{zone}'),
            self.check('type([0].virtualMachine.network.publicIpAddresses[0].name)', 'string'),
            self.check('[0].virtualMachine.network.publicIpAddresses[0].resourceGroup', '{rg}')
        ])


class VMSizeListScenarioTest(ScenarioTest):

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
            'sku': '14.04.2-LTS',
            'ver': '14.04.201503090'
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

        self.cmd('vm create -g {rg} -n {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk --nsg-rule NONE')
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

    @ResourceGroupPreparer(name_prefix='cli_test_generalize_vm')
    def test_vm_capture_zone_resilient_image(self, resource_group):

        self.kwargs.update({
            'loc': 'francecentral',
            'vm': 'vm-generalize'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username ubuntu --image centos --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
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


class VMWindowsLicenseTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_windows_license_type')
    def test_vm_windows_license_type(self, resource_group):
        self.kwargs.update({
            'vm': 'winvm'
        })
        self.cmd('vm create -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('licenseType', 'Windows_Server')
        ])
        self.cmd('vm update -g {rg} -n {vm} --license-type None', checks=[
            self.check('licenseType', 'None')
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

        self.cmd('vm create -g {rg} -n {vm1} --image ubuntults --use-unmanaged-disk --admin-username sdk-test-admin --admin-password testPassword0 --nsg-rule NONE')
        # deprovision the VM, but we have to do it async to avoid hanging the run-command itself
        self.cmd('vm run-command invoke -g {rg} -n {vm1} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm1}')
        self.cmd('vm generalize -g {rg} -n {vm1}')
        self.cmd('image create -g {rg} -n {image1} --source {vm1}')

        self.cmd('vm create -g {rg} -n {vm2} --image ubuntults --storage-sku standard_lrs --data-disk-sizes-gb 1 1 1 1 --admin-username sdk-test-admin --admin-password testPassword0 --nsg-rule NONE')
        data_disks = self.cmd('vm show -g {rg} -n {vm2}').get_output_in_json()['storageProfile']['dataDisks']
        self.kwargs['disk_0_name'] = data_disks[0]['name']
        self.kwargs['disk_2_name'] = data_disks[2]['name']

        # detach the 0th and 2nd disks leaving disks at lun 1 and 3
        self.cmd('vm disk detach -n {disk_0_name} --vm-name {vm2} -g {rg}')
        self.cmd('vm disk detach -n {disk_2_name} --vm-name {vm2} -g {rg}')

        self.cmd('vm show -g {rg} -n {vm2}', checks=self.check("length(storageProfile.dataDisks)", 2))

        self.cmd('vm run-command invoke -g {rg} -n {vm2} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm2}')
        self.cmd('vm generalize -g {rg} -n {vm2}')
        self.cmd('image create -g {rg} -n {image2} --source {vm2}')

        self.cmd('vm create -g {rg} -n {newvm1} --image {image1} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {newvm1}', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage')
        ])
        self.cmd('vmss create -g {rg} -n vmss1 --image {image1} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage')
        ])

        self.cmd('vm create -g {rg} -n {newvm2} --image {image2} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {newvm2}', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(storageProfile.dataDisks)", 2),
            self.check("storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS')
        ])

        self.cmd('vm create -g {rg} -n vm3 --image {image2} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --storage-sku os=Premium_LRS 0=StandardSSD_LRS --data-disk-sizes-gb 1 --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n vm3', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage'),
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),

            self.check("length(storageProfile.dataDisks)", 3),
            self.check("storageProfile.dataDisks[?lun == `0`] | [0].createOption", 'Empty'),
            self.check("storageProfile.dataDisks[?lun == `1`] | [0].createOption", 'FromImage'),
            self.check("storageProfile.dataDisks[?lun == `3`] | [0].createOption", 'FromImage'),

            self.check('storageProfile.dataDisks[?lun == `0`] | [0].managedDisk.storageAccountType', 'StandardSSD_LRS'),
            self.check('storageProfile.dataDisks[?lun == `1`] | [0].managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('storageProfile.dataDisks[?lun == `3`] | [0].managedDisk.storageAccountType', 'Standard_LRS')
        ])

        self.cmd('vmss create -g {rg} -n vmss2 --image {image2} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(vmss.virtualMachineProfile.storageProfile.dataDisks)", 2),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[?lun == `1`] | [0].createOption", 'FromImage'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[?lun == `1`] | [0].managedDisk.storageAccountType", 'Standard_LRS'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[?lun == `3`] | [0].createOption", 'FromImage'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[?lun == `3`] | [0].managedDisk.storageAccountType", 'Standard_LRS')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image_conflict')
    def test_vm_custom_image_name_conflict(self, resource_group):
        self.kwargs.update({
            'vm': 'test-vm',
            'image1': 'img-from-vm',
            'image2': 'img-from-vm-id',
            'image3': 'img-from-disk-id',
        })

        self.cmd('vm create -g {rg} -n {vm} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
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
            self.check("storageProfile.osDisk.managedDisk", None),
            self.check('hyperVgeneration', 'V1')
        ])
        # Create image from vm id
        self.cmd('image create -g {rg} -n {image2} --source {vm_id}', checks=[
            self.check("sourceVirtualMachine.id", '{vm_id}'),
            self.check("storageProfile.osDisk.managedDisk", None),
            self.check('hyperVgeneration', 'V1')
        ])
        # Create image from disk id
        self.cmd('image create -g {rg} -n {image3} --source {os_disk_id} --os-type linux --hyper-v-generation "V1"', checks=[
            self.check("sourceVirtualMachine", None),
            self.check("storageProfile.osDisk.managedDisk.id", '{os_disk_id}'),
            self.check('hyperVgeneration', 'V1')
        ])


class VMImageWithPlanTest(ScenarioTest):

    # Disable temporarily. You cannot purchase reservation because required AAD tenant information is missing.
    # Please ask your tenant admin to fill this form: https://aka.ms/orgprofile
    """
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
    """


class VMCreateFromUnmanagedDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_from_unmanaged_disk')
    def test_vm_create_from_unmanaged_disk(self, resource_group):
        # create a vm with unmanaged os disk
        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
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
        self.cmd('vm create -g {rg} -n {vm} --attach-os-disk {os_disk} --os-type linux --nsg-rule NONE',
                 checks=self.check('powerState', 'VM running'))


class VMCreateWithSpecializedUnmanagedDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_with_specialized_unmanaged_disk')
    def test_vm_create_with_specialized_unmanaged_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus'
        })

        # create a vm with unmanaged os disk
        self.cmd('vm create -g {rg} -n vm1 --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        vm1_info = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()
        self.kwargs['disk_uri'] = vm1_info['storageProfile']['osDisk']['vhd']['uri']

        self.cmd('vm delete -g {rg} -n vm1 -y')

        # create a vm by attaching the OS disk from the deleted VM
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {disk_uri} --os-type linux --use-unmanaged-disk --nsg-rule NONE',
                 checks=self.check('powerState', 'VM running'))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_with_specialized_unmanaged_disk')
    def test_vm_create_with_unmanaged_data_disks(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1',
            'vm2': 'vm2'
        })

        # create a unmanaged bm with 2 unmanaged disks
        vm_create_cmd = 'vm create -g {rg} -n vm1 --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE'
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
                         '--attach-data-disks {data_disk} {data_disk2} --data-disk-caching 0=ReadWrite 1=ReadOnly --nsg-rule NONE')
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
        self.cmd('vm create -g {rg} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --data-disk-sizes-gb 2 --nsg-rule NONE')
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
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk} --attach-data-disks {data_disk} --data-disk-sizes-gb 3 --os-disk-size-gb 100 --os-type linux --nsg-rule NONE',
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
        self.cmd('vm create -g {rg} -n vm1 --use-unmanaged-disk --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name vm1 --new --size-gb 2')
        result = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()
        self.kwargs['os_disk_vhd'] = result['storageProfile']['osDisk']['vhd']['uri']
        self.kwargs['data_disk_vhd'] = result['storageProfile']['dataDisks'][0]['vhd']['uri']

        # delete the vm to end vhd's leases so they can be used to create a new vm through attaching
        self.cmd('vm deallocate -g {rg} -n vm1')
        self.cmd('vm delete -g {rg} -n vm1 -y')

        # rebuild a new vm
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk_vhd} --attach-data-disks {data_disk_vhd} --os-type linux --use-unmanaged-disk --nsg-rule NONE',
                 checks=self.check('powerState', 'VM running'))


class VMOSDiskSize(ScenarioTest):

    @AllowLargeResponse(99999)
    @ResourceGroupPreparer(name_prefix='cli_test_os_disk_size')
    def test_vm_set_os_disk_size(self, resource_group):
        # test unmanaged disk
        self.kwargs.update({'sa': self.create_random_name(prefix='cli', length=12)})
        self.cmd('vm create -g {rg} -n vm --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75 --use-unmanaged-disk --storage-account {sa} --nsg-rule NONE')
        result = self.cmd('storage blob list --account-name {sa} --container-name vhds').get_output_in_json()
        self.assertTrue(result[0]['properties']['contentLength'] > 75000000000)

        # test managed disk
        self.cmd('vm create -g {rg} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75 --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n vm1',
                 checks=self.check('storageProfile.osDisk.diskSizeGb', 75))


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
            self.check('diskSizeGb', 1),
            self.check('tags.tag1', 'd1')
        ]).get_output_in_json()
        self.cmd('disk update -g {rg} -n {disk1} --size-gb 10 --sku Standard_LRS', checks=[
            self.check('sku.name', 'Standard_LRS'),
            self.check('diskSizeGb', 10)
        ])

        # get SAS token
        result = self.cmd('disk grant-access -g {rg} -n {disk1} --duration-in-seconds 10').get_output_in_json()
        self.assertTrue('sv=' in result['accessSas'])

        # create another disk by importing from the disk1
        self.kwargs['disk1_id'] = data_disk['id']
        data_disk2 = self.cmd('disk create -g {rg} -n {disk2} --source {disk1_id}').get_output_in_json()

        # create a snpashot
        os_snapshot = self.cmd('snapshot create -g {rg} -n {snapshot1} --size-gb 1 --sku Premium_LRS --tags tag1=s1', checks=[
            self.check('sku.name', 'Premium_LRS'),
            self.check('diskSizeGb', 1),
            self.check('tags.tag1', 's1')
        ]).get_output_in_json()
        # update the sku
        self.cmd('snapshot update -g {rg} -n {snapshot1} --sku Standard_LRS', checks=[
            self.check('sku.name', 'Standard_LRS'),
            self.check('diskSizeGb', 1)
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
                 ' --os-type Linux --tags tag1=i1 --storage-sku Standard_LRS --os-disk-caching ReadWrite --data-disk-caching ReadOnly',
                 checks=[
                     self.check('storageProfile.osDisk.storageAccountType', 'Standard_LRS'),
                     self.check('storageProfile.osDisk.caching', 'ReadWrite'),
                     self.check('storageProfile.dataDisks[0].caching', 'ReadOnly')
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_disk_upload_')
    def test_vm_disk_upload(self, resource_group):
        self.kwargs.update({
            'disk': 'disk1',
        })

        # test --upload-size-bytes parameter
        self.cmd('disk create -g {rg} -n {disk} --for-upload --upload-size-bytes 21474836992', checks=[
            self.check('creationData.uploadSizeBytes', 21474836992)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_snapshot_incremental_')
    def test_vm_snapshot_incremental(self, resource_group):
        self.kwargs.update({
            'disk': 'd1',
            'snapshot': 's1'
        })

        # create a disk first
        self.cmd('disk create -g {rg} -n {disk} --size-gb 10 -l centraluseuap')

        # test snapshot --incremental
        self.cmd('snapshot create -g {rg} -n {snapshot} --incremental -l centraluseuap --source {disk}',
                 checks=[self.check('incremental', True)])

    """ Disable temporarily
    @ResourceGroupPreparer(name_prefix='cli_test_large_disk')
    def test_vm_large_disk(self, resource_group):
        self.kwargs.update({
            'disk': 'd1',
            'snapshot': 's1'
        })
        self.cmd('disk create -g {rg} -n {disk} --hyper-v-generation V2 --for-upload --upload-size-bytes 1073742336', checks=[
            self.check('hyperVgeneration', "V2")
        ])
        self.cmd('disk grant-access -g {rg} -n {disk} --access-level Write --duration-in-seconds 3600')
        self.cmd('disk revoke-access -g {rg} -n {disk}')
        self.cmd('snapshot create -g {rg} -n {snapshot} --source {disk} --hyper-v-generation V2', checks=[
            self.check('hyperVgeneration', "V2")
        ])
    """

    @ResourceGroupPreparer(name_prefix='cli_test_vm_disk_max_shares_etc_', location='westus')
    def test_vm_disk_max_shares_etc(self, resource_group):
        # Test disk create: add --disk-iops-read-only, --disk-mbps-read-only, --max-shares, --image-reference, --gallery-image-reference
        subs_id = self.get_subscription_id()
        self.kwargs.update({
            'disk1': 'd1',
            'disk2': 'd2',
            'disk3': 'd3',
            'disk4': 'd4',
            'disk5': 'd5',
            'disk6': 'd6',
            'image': '/Subscriptions/' + subs_id + '/Providers/Microsoft.Compute/Locations/westus/Publishers/Canonical/ArtifactTypes/VMImage/Offers/UbuntuServer/Skus/18.04-LTS/Versions/18.04.202002180',
            'image2': 'image2',
            'g1': self.create_random_name('g1', 20),
            'vm': 'vm1'
        })

        self.cmd('disk create -g {rg} -n {disk1} --size-gb 10 --sku UltraSSD_LRS --disk-iops-read-only 200 --disk-mbps-read-only 30', checks=[
            self.check('diskIopsReadOnly', 200),
            self.check('diskMbpsReadOnly', 30)
        ])

        self.cmd('disk create -g {rg} -n {disk2} --image-reference {image}', checks=[
            self.check('creationData.imageReference.id', '{image}')
        ])

        self.cmd('disk create -g {rg} -n {disk3} --image-reference Canonical:UbuntuServer:18.04-LTS:18.04.202002180', checks=[
            self.check('creationData.imageReference.id', '{image}')
        ])

        self.cmd('sig create -g {rg} --gallery-name {g1}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {g1} --gallery-image-definition image --os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('disk create -g {rg} -n disk --size-gb 10')
        self.cmd('snapshot create -g {rg} -n s1 --source disk')
        gallery_image = self.cmd('sig image-version create -g {rg} --gallery-name {g1} --gallery-image-definition image --gallery-image-version 1.0.0 --os-snapshot s1').get_output_in_json()['id']
        self.kwargs.update({
            'gallery_image': gallery_image
        })
        self.cmd('disk create -g {rg} -n {disk4} --gallery-image-reference {gallery_image}', checks=[
            self.check('creationData.galleryImageReference.id', '{gallery_image}')
        ])

        self.cmd('disk create -g {rg} -n {disk6} --size-gb 256 --max-shares 2 -l centraluseuap', checks=[
            self.check('maxShares', 2)
        ])


class VMCreateAndStateModificationsScenarioTest(ScenarioTest):

    def _check_vm_power_state(self, expected_power_state):

        self.cmd('vm get-instance-view --resource-group {rg} --name {vm}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{vm}'),
            self.check('resourceGroup', '{rg}'),
            self.check('length(instanceView.statuses)', 2),
            self.check('instanceView.statuses[0].code', 'ProvisioningState/succeeded'),
            self.check('instanceView.statuses[1].code', expected_power_state),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_state_mod')
    def test_vm_create_state_modifications(self, resource_group):

        self.kwargs.update({
            'loc': 'eastus',
            'vm': 'vm-state-mod',
            'nsg': 'mynsg',
            'ip': 'mypubip',
            'sa': self.create_random_name('clistorage', 15),
            'vnet': 'myvnet'
        })

        # Expecting no results
        self.cmd('vm list --resource-group {rg}',
                 checks=self.is_empty())
        self.cmd('vm create --resource-group {rg} --location {loc} --name {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --tags firsttag=1 secondtag=2 thirdtag --nsg {nsg} --public-ip-address {ip} --vnet-name {vnet} --storage-account {sa} --use-unmanaged-disk')

        # Expecting one result, the one we created
        self.cmd('vm list --resource-group {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].name', '{vm}'),
            self.check('[0].location', '{loc}'),
            self.check('[0].provisioningState', 'Succeeded')
        ])

        # Verify tags were set
        self.cmd('vm show --resource-group {rg} --name {vm}', checks=[
            self.check('tags.firsttag', '1'),
            self.check('tags.secondtag', '2'),
            self.check('tags.thirdtag', ''),
        ])
        self._check_vm_power_state('PowerState/running')

        self.cmd('vm user update -g {rg} -n {vm} -u foouser1 -p Foo12345')
        self.cmd('vm user delete -g {rg} -n {vm} -u foouser1')

        self.cmd('network nsg show --resource-group {rg} --name {nsg}', checks=[
            self.check('tags.firsttag', '1'),
            self.check('tags.secondtag', '2'),
            self.check('tags.thirdtag', ''),
        ])
        self.cmd('network public-ip show --resource-group {rg} --name {ip}', checks=[
            self.check('tags.firsttag', '1'),
            self.check('tags.secondtag', '2'),
            self.check('tags.thirdtag', ''),
        ])
        self.cmd('network vnet show --resource-group {rg} --name {vnet}', checks=[
            self.check('tags.firsttag', '1'),
            self.check('tags.secondtag', '2'),
            self.check('tags.thirdtag', ''),
        ])
        self.cmd('storage account show --resource-group {rg} --name {sa}', checks=[
            self.check('tags.firsttag', '1'),
            self.check('tags.secondtag', '2'),
            self.check('tags.thirdtag', ''),
        ])

        self.cmd('vm stop --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/stopped')
        self.cmd('vm start --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/running')
        self.cmd('vm restart --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/running')
        self.cmd('vm restart --resource-group {rg} --name {vm} --force')
        self._check_vm_power_state('PowerState/running')
        self.cmd('vm deallocate --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/deallocated')
        self.cmd('vm resize -g {rg} -n {vm} --size Standard_DS2_v2',
                 checks=self.check('hardwareProfile.vmSize', 'Standard_DS2_v2'))
        self.cmd('vm delete --resource-group {rg} --name {vm} --yes')
        # Expecting no results
        self.cmd('vm list --resource-group {rg}', checks=self.is_empty())


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
        self.cmd('vm create --resource-group {rg} --name {vm1} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Regular')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm1}', expect_failure=True)

        # simulate-eviction on a Spot VM with Deallocate policy, expect VM to be deallocated
        self.cmd('vm create --resource-group {rg} --name {vm2} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Spot --eviction-policy Deallocate')
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
        self.cmd('vm create --resource-group {rg} --name {vm3} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Spot --eviction-policy Delete')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm3}')
        time.sleep(180)
        self.cmd('vm list --resource-group {rg}', checks=[self.check('length(@)', 2)])
        self.cmd('vm show --resource-group {rg} --name {vm3}', expect_failure=True)


class VMNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_no_wait')
    def test_vm_create_no_wait(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vmnowait2'
        })
        self.cmd('vm create -g {rg} -n {vm} --admin-username user12 --admin-password testPassword0 --authentication-type password --image UbuntuLTS --nsg-rule NONE --no-wait',
                 checks=self.is_empty())
        self.cmd('vm wait -g {rg} -n {vm} --custom "instanceView.statuses[?code==\'PowerState/running\']"',
                 checks=self.is_empty())
        self.cmd('vm get-instance-view -g {rg} -n {vm}',
                 checks=self.check("length(instanceView.statuses[?code=='PowerState/running'])", 1))
        self.cmd('vm update -g {rg} -n {vm} --set tags.mytag=tagvalue1 --no-wait',
                 checks=self.is_empty())
        self.cmd('vm wait -g {rg} -n {vm} --updated',
                 checks=self.is_empty())
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check("tags.mytag", 'tagvalue1'))


class VMAvailSetScenarioTest(ScenarioTest):

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


class VMAvailSetLiveScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_availset_live')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_availset_convert(self, resource_group):

        self.kwargs.update({
            'availset': 'availset-test-conv'
        })

        self.cmd('vm availability-set create -g {rg} -n {availset} --unmanaged --platform-fault-domain-count 3 -l westus2', checks=[
            self.check('name', '{availset}'),
            self.check('platformFaultDomainCount', 3),
            self.check('sku.name', 'Classic')
        ])

        self.cmd('vm availability-set convert -g {rg} -n {availset}', checks=[
            self.check('name', '{availset}'),
            self.check('sku.name', 'Aligned')
        ])


class ComputeListSkusScenarioTest(ScenarioTest):

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

    @AllowLargeResponse(size_kb=99999)
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

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --nsg-rule NONE')

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

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm extension set -n {ext_type} --publisher {pub} --version 1.2 --vm-name {vm} --resource-group {rg} '
                 '--protected-settings "{config}" --extension-instance-name {ext_name}')

        self.cmd('vm extension show --resource-group {rg} --vm-name {vm} --name {ext_name}', checks=[
            self.check('name', '{ext_name}'),
            self.check('virtualMachineExtensionType', '{ext_type}')
        ])
        self.cmd('vm extension delete --resource-group {rg} --vm-name {vm} --name {ext_name}')

    @AllowLargeResponse(size_kb=99999)
    @ResourceGroupPreparer(name_prefix='cli_test_vm_extension_with_id_')
    def test_vm_extension_with_id(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })
        vm_id = self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --generate-ssh-keys --admin-username azureuser --nsg-rule NONE').get_output_in_json()['id']
        self.kwargs.update({
            'vm_id': vm_id
        })
        vm_ext_id = self.cmd('vm extension set -n customScript --publisher Microsoft.Azure.Extensions --ids {vm_id}')\
            .get_output_in_json()['id']
        self.kwargs.update({
            'vm_ext_id': vm_ext_id
        })
        self.cmd('vm extension delete --ids {vm_ext_id}')


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
            'comp_name': 'my-computer',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'ssh_key': TEST_SSH_KEY_PUB,
            'loc': resource_group_location
        })
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --computer-name {comp_name} '
                 ' --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1 --data-disk-caching ReadOnly --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.adminUsername', '{username}'),
            self.check('osProfile.computerName', '{comp_name}'),
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', '{ssh_key}'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[0].lun', 0),
            self.check('storageProfile.dataDisks[0].caching', 'ReadOnly'),
        ])

        # test for idempotency--no need to reverify, just ensure the command doesn't fail
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --computer-name {comp_name} '
                 ' --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1 --data-disk-caching ReadOnly --nsg-rule NONE')


class VMCreateEphemeralOsDisk(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_ephemeral_os_disk')
    def test_vm_create_ephemeral_os_disk(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vm': 'cli-test-vm-local-1',
            'vm_2': 'cli-test-vm-local-2',
            'image': 'UbuntuLTS',
            'ssh_key': TEST_SSH_KEY_PUB,
            'loc': resource_group_location,
            'user': 'user_1'
        })

        # check that we can create a vm with local / ephemeral os disk.
        self.cmd('vm create --resource-group {rg} --name {vm} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --ephemeral-os-disk --admin-username {user} --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.caching', 'ReadOnly'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
        ])

        # explicitly specify os-disk-caching
        self.cmd('vm create --resource-group {rg} --name {vm_2} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --ephemeral-os-disk --os-disk-caching ReadOnly --admin-username {user} --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm_2}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.caching', 'ReadOnly'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('osProfile.computerName', '{vm_2}'),  # check that --computer-name defaults to --name here.
        ])


class VMMultiNicScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_multi_nic_vm')
    def test_vm_create_multi_nics(self, resource_group):

        self.kwargs.update({
            'vnet': 'myvnet',
            'subnet': 'mysubnet',
            'vm': 'multinicvm1',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        for i in range(1, 5):  # create four NICs
            self.kwargs['nic'] = 'nic{}'.format(i)
            self.cmd('network nic create -g {rg} -n {nic} --subnet {subnet} --vnet-name {vnet}')

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --nics nic1 nic2 nic3 nic4 --admin-username user11 --size Standard_DS3 --ssh-key-value \'{ssh_key}\'')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check("networkProfile.networkInterfaces[0].id.ends_with(@, 'nic1')", True),
            self.check("networkProfile.networkInterfaces[1].id.ends_with(@, 'nic2')", True),
            self.check("networkProfile.networkInterfaces[2].id.ends_with(@, 'nic3')", True),
            self.check("networkProfile.networkInterfaces[3].id.ends_with(@, 'nic4')", True),
            self.check('length(networkProfile.networkInterfaces)', 4)
        ])
        # cannot alter NICs on a running (or even stopped) VM
        self.cmd('vm deallocate -g {rg} -n {vm}')

        self.cmd('vm nic list -g {rg} --vm-name {vm}', checks=[
            self.check('length(@)', 4),
            self.check('[0].primary', True)
        ])
        self.cmd('vm nic show -g {rg} --vm-name {vm} --nic nic1')
        self.cmd('vm nic remove -g {rg} --vm-name {vm} --nics nic4 --primary-nic nic1', checks=[
            self.check('length(@)', 3),
            self.check('[0].primary', True),
            self.check("[0].id.contains(@, 'nic1')", True)
        ])
        self.cmd('vm nic add -g {rg} --vm-name {vm} --nics nic4', checks=[
            self.check('length(@)', 4),
            self.check('[0].primary', True),
            self.check("[0].id.contains(@, 'nic1')", True)
        ])
        self.cmd('vm nic set -g {rg} --vm-name {vm} --nics nic1 nic2 --primary-nic nic2', checks=[
            self.check('length(@)', 2),
            self.check('[1].primary', True),
            self.check("[1].id.contains(@, 'nic2')", True)
        ])


class VMCreateNoneOptionsTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_none_options', location='westus')
    def test_vm_create_none_options(self, resource_group):

        self.kwargs.update({
            'vm': 'nooptvm',
            'loc': 'eastus',  # create in different location from RG
            'quotes': '""' if platform.system() == 'Windows' else "''",
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vm create -n {vm} -g {rg} --computer-name {quotes} --image Debian --availability-set {quotes} --nsg {quotes} --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --location {loc} --admin-username user11')

        self.cmd('vm show -n {vm} -g {rg}', checks=[
            self.check('availabilitySet', None),
            self.check('length(tags)', 0),
            self.check('location', '{loc}'),
            self.check('osProfile.computerName', '{vm}')
        ])
        self.cmd('network public-ip show -n {vm}PublicIP -g {rg}', expect_failure=True)


class VMMonitorTestDefault(ScenarioTest):
    def __init__(self, method_name, config_file=None, recording_dir=None, recording_name=None, recording_processors=None,
                 replay_processors=None, recording_patches=None, replay_patches=None):
        from ._test_util import TimeSpanProcessor
        TIMESPANTEMPLATE = '0000-00-00'
        super(VMMonitorTestDefault, self).__init__(
            method_name,
            recording_processors=[TimeSpanProcessor(TIMESPANTEMPLATE)],
            replay_processors=[TimeSpanProcessor(TIMESPANTEMPLATE)]
        )

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_with_monitor', location='eastus')
    def test_vm_create_with_monitor(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'workspace': self.create_random_name('cliworkspace', 20),
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --workspace {workspace} --nsg {nsg} --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm monitor log show -n {vm} -g {rg} -q "Perf | limit 10"')

    @ResourceGroupPreparer(name_prefix='cli_test_vm_metric_tail', location='eastus')
    def test_vm_metric_tail(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --nsg {nsg} --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm start -n {vm} -g {rg}')

        time.sleep(60)

        self.cmd('vm monitor metrics tail -n {vm} -g {rg} --metrics "Percentage CPU"', checks=[
            self.check('value[0].type', 'Microsoft.Insights/metrics'),
            self.check('value[0].name.value', 'Percentage CPU')
        ])
        self.cmd('vm monitor metrics list-definitions -n {vm} -g {rg}', checks=[
            self.check("length(@) != '0'", True)
        ])


class VMMonitorTestCreateLinux(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_with_workspace_linux', location='eastus')
    def test_vm_create_with_workspace_linux(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'workspace': self.create_random_name('cliworkspace', 20),
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --workspace {workspace} --nsg {nsg} --generate-ssh-keys --admin-username azureuser')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace} -g {rg}').get_output_in_json()['id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'LinuxPerformanceCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslog')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslogCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxPerformanceObject')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 4)
        ])


class VMMonitorTestCreateWindows(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_with_workspace_windows', location='eastus')
    def test_vm_create_with_workspace_windows(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'workspace': self.create_random_name('cliworkspace', 20),
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm create -n {vm} -g {rg} --image Win2016Datacenter --workspace {workspace} --admin-username azureuser --admin-password AzureCLI@1224 --nsg {nsg}')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace} -g {rg}').get_output_in_json()[
            'id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'WindowsEvent')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'WindowsPerformanceCounter')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 15)
        ])


class VMMonitorTestUpdateLinux(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_update_with_workspace_linux', location='eastus')
    def test_vm_update_with_workspace_linux(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'workspace1': self.create_random_name('cliworkspace', 20),
            'workspace2': self.create_random_name('cliworkspace', 20),
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --nsg {nsg} --generate-ssh-keys --admin-username azureuser')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm update -n {vm} -g {rg} --workspace {workspace1}')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace1} -g {rg}').get_output_in_json()['id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'LinuxPerformanceCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslog')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslogCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxPerformanceObject')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 4)
        ])

        self.cmd('vm monitor log show -n {vm} -g {rg} -q "Perf"')

        self.cmd('monitor log-analytics workspace create -n {workspace2} -g {rg}')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm update -n {vm} -g {rg} --workspace {workspace2}')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace2} -g {rg}').get_output_in_json()['id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'LinuxPerformanceCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslog')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxSyslogCollection')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'LinuxPerformanceObject')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 4)
        ])

        self.cmd('vm monitor log show -n {vm} -g {rg} -q "Perf"')


class VMMonitorTestUpdateWindows(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_vm_update_with_workspace_windows', location='eastus')
    def test_vm_update_with_workspace_windows(self, resource_group):

        self.kwargs.update({
            'vm': 'monitorvm',
            'workspace1': self.create_random_name('cliworkspace', 20),
            'workspace2': self.create_random_name('cliworkspace', 20),
            'rg': resource_group,
            'nsg': self.create_random_name('clinsg', 20)
        })
        self.cmd('network nsg create -g {rg} -n {nsg}')
        self.cmd('vm create -n {vm} -g {rg} --image Win2016Datacenter --admin-password AzureCLI@1224 --nsg {nsg} --admin-username azureuser')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm update -n {vm} -g {rg} --workspace {workspace1}')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace1} -g {rg}').get_output_in_json()['id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'WindowsEvent')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'WindowsPerformanceCounter')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 15)
        ])

        self.cmd('vm monitor log show -n {vm} -g {rg} -q "Perf"')

        self.cmd('monitor log-analytics workspace create -n {workspace2} -g {rg}')
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('vm update -n {vm} -g {rg} --workspace {workspace2}')

        workspace_id = self.cmd('monitor log-analytics workspace show -n {workspace2} -g {rg}').get_output_in_json()['id']
        uri_template = "https://management.azure.com{0}/dataSources?$filter=kind eq '{1}'&api-version=2020-03-01-preview"
        uri = uri_template.format(workspace_id, 'WindowsEvent')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 1)
        ])

        uri = uri_template.format(workspace_id, 'WindowsPerformanceCounter')
        self.cmd("az rest --method get --uri \"{}\"".format(uri), checks=[
            self.check('length(value)', 15)
        ])

        self.cmd('vm monitor log show -n {vm} -g {rg} -q "Perf"')


class VMBootDiagnostics(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_diagnostics')
    @StorageAccountPreparer(name_prefix='clitestbootdiag')
    @AllowLargeResponse()
    def test_vm_boot_diagnostics(self, resource_group, storage_account):

        self.kwargs.update({
            'vm': 'myvm',
            'vm2': 'myvm2'
        })
        self.kwargs['storage_uri'] = 'https://{}.blob.core.windows.net/'.format(self.kwargs['sa'])

        self.cmd('storage account create -g {rg} -n {sa} --sku Standard_LRS -l westus')
        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --use-unmanaged-disk')

        self.cmd('vm boot-diagnostics enable -g {rg} -n {vm} --storage {sa}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('diagnosticsProfile.bootDiagnostics.enabled', True),
            self.check('diagnosticsProfile.bootDiagnostics.storageUri', '{storage_uri}')
        ])

        # will uncomment after #302 gets addressed
        # self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')
        self.cmd('vm boot-diagnostics disable -g {rg} -n {vm}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('diagnosticsProfile.bootDiagnostics.enabled', False))

        # try enable it at the create
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username user11 --admin-password testPassword0 --boot-diagnostics-storage {sa}')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check('diagnosticsProfile.bootDiagnostics.enabled', True),
            self.check('diagnosticsProfile.bootDiagnostics.storageUri', '{storage_uri}')
        ])


class VMSSExtensionInstallTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_extension')
    def test_vmss_extension(self):

        username = 'myadmin'
        config_file = _write_config_file(username)

        self.kwargs.update({
            'vmss': 'vmss1',
            'net-pub': 'Microsoft.Azure.NetworkWatcher', 'script-pub': 'Microsoft.Azure.Extensions', 'access-pub': 'Microsoft.OSTCExtensions',
            'net-ext': 'NetworkWatcherAgentLinux', 'script-ext': 'customScript', 'access-ext': 'VMAccessForLinux',
            'username': username,
            'config_file': config_file
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0 --instance-count 1')

        self.cmd('vmss extension set -n {net-ext} --publisher {net-pub} --version 1.4  --vmss-name {vmss} --resource-group {rg} --protected-settings "{config_file}" --force-update')
        result = self.cmd('vmss extension show --resource-group {rg} --vmss-name {vmss} --name {net-ext}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{net-ext}'),
            self.check('publisher', '{net-pub}'),
            self.check('provisionAfterExtensions', None)
        ]).get_output_in_json()

        uuid.UUID(result['forceUpdateTag'])  # verify that command does generate a valid guid to trigger force update.

        # set the customscript extension that depends on the network watcher extension
        self.cmd('vmss extension set -g {rg} --vmss-name {vmss} -n {script-ext} --publisher {script-pub} --version 2.0 '
                 '--provision-after-extensions {net-ext} --settings "{{\\"commandToExecute\\": \\"echo testing\\"}}"')
        # verify
        self.cmd('vmss extension show -g {rg} --vmss-name {vmss} --name {script-ext}', checks=[
            self.check('length(provisionAfterExtensions)', 1),
            self.check('provisionAfterExtensions[0]', '{net-ext}'),
        ])

        # set the VMAccess extension that depends on both the network watcher and script extensions.
        self.cmd('vmss extension set -g {rg} --vmss-name {vmss} -n {access-ext} --publisher {access-pub} --version 1.5 '
                 '--provision-after-extensions {net-ext} {script-ext} --protected-settings "{config_file}"')
        # verify
        self.cmd('vmss extension show -g {rg} --vmss-name {vmss} --name {access-ext}', checks=[
            self.check('length(provisionAfterExtensions)', 2),
            self.check('provisionAfterExtensions[0]', '{net-ext}'),
            self.check('provisionAfterExtensions[1]', '{script-ext}'),
        ])

        # delete all the extensions
        self.cmd('vmss extension delete --resource-group {rg} --vmss-name {vmss} --name {access-ext}')
        self.cmd('vmss extension delete --resource-group {rg} --vmss-name {vmss} --name {script-ext}')
        self.cmd('vmss extension delete --resource-group {rg} --vmss-name {vmss} --name {net-ext}')

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_extension_2')
    def test_vmss_extension_instance_name(self):
        username = 'myadmin'
        config_file = _write_config_file(username)

        self.kwargs.update({
            'vmss': 'vmss1',
            'pub': 'Microsoft.Azure.NetworkWatcher',
            'ext_type': 'NetworkWatcherAgentLinux',
            'username': username,
            'config_file': config_file,
            'ext_name': 'MyNetworkWatcher'
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0 --instance-count 1')
        self.cmd('vmss extension set -n {ext_type} --publisher {pub} --version 1.4  --vmss-name {vmss} --resource-group {rg} '
                 '--protected-settings "{config_file}" --extension-instance-name {ext_name}')
        self.cmd('vmss extension show --resource-group {rg} --vmss-name {vmss} --name {ext_name}', checks=[
            self.check('name', '{ext_name}'),
            self.check('type1', '{ext_type}')
        ])
        self.cmd('vmss extension delete --resource-group {rg} --vmss-name {vmss} --name {ext_name}')


class DiagnosticsExtensionInstallTest(ScenarioTest):
    """
    Note that this is currently only for a Linux VM. There's currently no test of this feature for a Windows VM.
    """
    @ResourceGroupPreparer(name_prefix='cli_test_vm_vmss_diagnostics_extension')
    @StorageAccountPreparer()
    def test_diagnostics_extension_install(self, resource_group, storage_account):

        self.kwargs.update({
            'vm': 'testdiagvm',
            'vmss': 'testdiagvmss'
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$')
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$ --use-unmanaged-disk --nsg-rule NONE')
        storage_sastoken = '123'  # use junk keys, do not retrieve real keys which will get into the recording
        _, protected_settings = tempfile.mkstemp()
        with open(protected_settings, 'w') as outfile:
            json.dump({
                "storageAccountName": storage_account,
                "storageAccountSasToken": storage_sastoken
            }, outfile)
        self.kwargs['protected_settings'] = protected_settings.replace('\\', '\\\\')

        _, public_settings = tempfile.mkstemp()
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'sample-public.json').replace('\\', '\\\\')
        with open(template_file) as data_file:
            data = json.load(data_file)
        data["StorageAccount"] = storage_account
        with open(public_settings, 'w') as outfile:
            json.dump(data, outfile)
        self.kwargs['public_settings'] = public_settings.replace('\\', '\\\\')

        checks = [
            self.check('virtualMachineProfile.extensionProfile.extensions[0].name', "LinuxDiagnostic"),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].publisher', "Microsoft.Azure.Diagnostics"),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.StorageAccount', '{sa}'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].typeHandlerVersion', '3.0')
        ]

        self.cmd("vmss diagnostics set -g {rg} --vmss-name {vmss} --settings {public_settings} --protected-settings {protected_settings}", checks=checks)
        self.cmd("vmss show -g {rg} -n {vmss}", checks=checks)

        # test standalone VM, we will start with an old version
        self.cmd('vm extension set -g {rg} --vm-name {vm} -n LinuxDiagnostic --version 2.3.9025 --publisher Microsoft.OSTCExtensions --settings {public_settings} --protected-settings {protected_settings}',
                 checks=self.check('typeHandlerVersion', '2.3'))
        # see the 'diagnostics set' command upgrades to newer version
        self.cmd("vm diagnostics set -g {rg} --vm-name {vm} --settings {public_settings} --protected-settings {protected_settings}", checks=[
            self.check('name', 'LinuxDiagnostic'),
            self.check('publisher', 'Microsoft.Azure.Diagnostics'),
            self.check('settings.StorageAccount', '{sa}'),
            self.check('typeHandlerVersion', '3.0')
        ])

        self.cmd("vm show -g {rg} -n {vm}", checks=[
            self.check('resources[0].name', 'LinuxDiagnostic'),
            self.check('resources[0].publisher', 'Microsoft.Azure.Diagnostics'),
            self.check('resources[0].settings.StorageAccount', '{sa}')
        ])


class VMCreateExistingOptions(ScenarioTest):

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

        self.cmd('vm create --image UbuntuLTS --os-disk-name {disk} --vnet-name {vnet} --subnet {subnet} --availability-set {availset} --public-ip-address {pubip} -l "West US" --nsg {nsg} --use-unmanaged-disk --size Standard_DS2 --admin-username user11 --storage-account {sa} --storage-container-name {container} -g {rg} --name {vm} --ssh-key-value \'{ssh_key}\'')

        self.cmd('vm availability-set show -n {availset} -g {rg}',
                 checks=self.check('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.kwargs['vm'].upper()), True))
        self.cmd('network nsg show -n {nsg} -g {rg}',
                 checks=self.check('networkInterfaces[0].id.ends_with(@, \'{vm}VMNic\')', True))
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{pubip}\')', True))
        self.cmd('vm show -n {vm} -g {rg}',
                 checks=self.check('storageProfile.osDisk.vhd.uri', 'https://{sa}.blob.core.windows.net/{container}/{disk}.vhd'))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_provision_vm_agent_')
    def test_vm_create_provision_vm_agent(self, resource_group):
        self.kwargs.update({
            'vm1': 'vm1',
            'vm2': 'vm2',
            'pswd': 'qpwWfn1qwernv#xnklwezxcvslkdfj'
        })

        self.cmd('vm create -g {rg} -n {vm1} --image UbuntuLTS --enable-agent --admin-username azureuser --admin-password {pswd} --authentication-type password')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('osProfile.linuxConfiguration.provisionVmAgent', True)
        ])

        self.cmd('vm create -g {rg} -n {vm2} --image Win2019Datacenter --admin-username azureuser --admin-password {pswd} --authentication-type password --enable-agent false')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check('osProfile.windowsConfiguration.provisionVmAgent', False)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_existing')
    def test_vm_create_auth(self, resource_group):
        self.kwargs.update({
            'vm_1': 'vm1',
            'vm_2': 'vm2',
            'ssh_key': TEST_SSH_KEY_PUB,
            'ssh_key_2': self.create_temp_file(0),
            'ssh_dest': '/home/myadmin/.ssh/authorized_keys'
        })

        with open(self.kwargs['ssh_key_2'], 'w') as f:
            f.write(TEST_SSH_KEY_PUB_2)

        self.cmd('vm create --image Debian -l westus -g {rg} -n {vm_1} --authentication-type all '
                 ' --admin-username myadmin --admin-password testPassword0 --ssh-key-value "{ssh_key}" --nsg-rule NONE')

        self.cmd('vm show -n {vm_1} -g {rg}', checks=[
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', False),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB)
        ])

        self.cmd('vm create --image Debian -l westus -g {rg} -n {vm_2} --authentication-type ssh '
                 ' --admin-username myadmin --ssh-key-value "{ssh_key}" "{ssh_key_2}" --ssh-dest-key-path "{ssh_dest}" --nsg-rule NONE')

        self.cmd('vm show -n {vm_2} -g {rg}', checks=[
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[1].keyData', TEST_SSH_KEY_PUB_2),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].path', '{ssh_dest}'),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[1].path', '{ssh_dest}')
        ])


class VMCreateExistingIdsOptions(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_existing_ids')
    @StorageAccountPreparer()
    def test_vm_create_existing_ids_options(self, resource_group, storage_account):
        from azure.cli.core.commands.client_factory import get_subscription_id
        from msrestazure.tools import resource_id, is_valid_resource_id

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

        self.cmd('vm create --image UbuntuLTS --os-disk-name {disk} --subnet {subnet_id} --availability-set {availset_id} --public-ip-address {pubip_id} -l "West US" --nsg {nsg_id} --use-unmanaged-disk --size Standard_DS2 --admin-username user11 --storage-account {sa} --storage-container-name {container} -g {rg} --name {vm} --ssh-key-value \'{ssh_key}\'')

        self.cmd('vm availability-set show -n {availset} -g {rg}',
                 checks=self.check('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.kwargs['vm'].upper()), True))
        self.cmd('network nsg show -n {nsg} -g {rg}',
                 checks=self.check('networkInterfaces[0].id.ends_with(@, \'{vm}VMNic\')', True))
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{pubip}\')', True))
        self.cmd('vm show -n {vm} -g {rg}',
                 checks=self.check('storageProfile.osDisk.vhd.uri', 'https://{sa}.blob.core.windows.net/{container}/{disk}.vhd'))


class VMCreateCustomIP(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_ip')
    def test_vm_create_custom_ip(self, resource_group):

        self.kwargs.update({
            'vm': 'vrfvmz',
            'vm2': 'vrfvmz2',
            'dns': 'vrfmyvm00110011z',
            'public_ip_sku': 'Standard'
        })

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --admin-username user11 --private-ip-address 10.0.0.5 --public-ip-sku {public_ip_sku} --public-ip-address-dns-name {dns} --generate-ssh-keys --nsg-rule NONE')

        self.cmd('network public-ip show -n {vm}PublicIP -g {rg}', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
            self.check('dnsSettings.domainNameLabel', '{dns}'),
            self.check('sku.name', '{public_ip_sku}')
        ])
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].privateIpAllocationMethod', 'Static'))

        # verify the default should be "Basic" sku with "Dynamic" allocation method
        self.cmd('vm create -n {vm2} -g {rg} --image UbuntuLTS --admin-username user11 --generate-ssh-keys --nsg-rule NONE')
        self.cmd('network public-ip show -n {vm2}PublicIP -g {rg}', checks=[
            self.check('publicIpAllocationMethod', 'Dynamic'),
            self.check('sku.name', 'Basic')
        ])


class VMDiskAttachDetachTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli-test-disk')
    def test_vm_disk_attach_detach(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-diskattach-test',
            'disk1': 'd1',
            'disk2': 'd2'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username admin123 --image centos --admin-password testPassword0 --authentication-type password --nsg-rule NONE')

        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1} --new --size-gb 1 --caching ReadOnly')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk2} --new --size-gb 2 --lun 2 --sku standard_lrs')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 2),
            self.check('storageProfile.dataDisks[0].name', '{disk1}'),
            self.check('storageProfile.dataDisks[0].caching', 'ReadOnly'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[1].name', '{disk2}'),
            self.check('storageProfile.dataDisks[1].lun', 2),
            self.check('storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('storageProfile.dataDisks[1].caching', 'None')
        ])
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk1}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 1),
            self.check('storageProfile.dataDisks[0].name', '{disk2}'),
            self.check('storageProfile.dataDisks[0].lun', 2),
        ])

        # ensure data disk luns are managed correctly
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 2),
            self.check('storageProfile.dataDisks[0].lun', 2),
            self.check('storageProfile.dataDisks[1].lun', 0),
        ])

        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk2}')
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk1}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('length(storageProfile.dataDisks)', 0))
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1} --caching ReadWrite --sku standard_lrs')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('storageProfile.dataDisks[0].lun', 0)
        ])

    @ResourceGroupPreparer(name_prefix='cli-test-stdssdk', location='eastus2')
    def test_vm_disk_storage_sku(self, resource_group):

        self.kwargs.update({
            'vm': 'vm-storage-sku-test',
            'disk1': 'd1',
            'disk2': 'd2',
            'disk3': 'd3',
        })

        self.cmd('vm create -g {rg}  -n {vm} --admin-username admin123 --admin-password testPassword0 --image debian --storage-sku StandardSSD_LRS --data-disk-sizes-gb 1 --nsg-rule NONE')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1} --new --size-gb 1 --sku premium_lrs')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk2}  --new --size-gb 2 --sku StandardSSD_LRS')
        self.cmd('disk create -g {rg} -n {disk3} --size-gb 4 --sku StandardSSD_LRS')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk3}')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'StandardSSD_LRS'),
            self.check('storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[2].managedDisk.storageAccountType', 'StandardSSD_LRS'),
            self.check('storageProfile.dataDisks[3].managedDisk.storageAccountType', 'StandardSSD_LRS'),
        ])

    @ResourceGroupPreparer(name_prefix='cli-test-stdssdk', location='eastus')
    def test_vm_ultra_ssd_storage_sku(self, resource_group):

        self.kwargs.update({
            'vm': 'vm-ultrassd',
            'vm2': 'vm-ultrassd2',
            'disk1': 'd1',
            'disk2': 'd2',
            'disk3': 'd3',
            'disk4': 'd4'
        })
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 4 --sku UltraSSD_LRS --disk-iops-read-write 500 --disk-mbps-read-write 8 --zone 2')
        self.cmd('disk show -g {rg} -n {disk1}')
        self.cmd('disk create -g {rg} -n {disk2} --size-gb 4 --sku UltraSSD_LRS')
        self.cmd('vm create -g {rg} -n {vm} --admin-username admin123 --size Standard_D2s_v3 --admin-password testPassword0 --image debian --storage-sku UltraSSD_LRS --data-disk-sizes-gb 4 --zone 2 --location eastus --nsg-rule NONE')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk3} --new --size-gb 5 --sku UltraSSD_LRS')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1}')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
            self.check('storageProfile.dataDisks[1].managedDisk.storageAccountType', 'UltraSSD_LRS'),
            self.check('storageProfile.dataDisks[2].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])
        self.cmd('vm create -g {rg} -n {vm2} --admin-username admin123 --admin-password testPassword0 --image debian --size Standard_D2s_v3 --ultra-ssd-enabled --zone 2 --location eastus --nsg-rule NONE')
        self.cmd('vm disk attach -g {rg} --vm-name {vm2} --name {disk4} --new --size-gb 5 --sku UltraSSD_LRS')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])

    @ResourceGroupPreparer(name_prefix='cli-test-ultrassd', location='eastus2')
    def test_vm_ultra_ssd_disk_update(self, resource_group):
        self.kwargs.update({
            'disk1': 'd1'
        })
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 4 --sku UltraSSD_LRS --disk-iops-read-write 500 --disk-mbps-read-write 8 --zone 2')
        self.cmd('disk update -g {rg} -n {disk1} --disk-iops-read-write 510 --disk-mbps-read-write 10', checks=[
            self.check('diskIopsReadWrite', 510),
            self.check('diskMbpsReadWrite', 10)
        ])

    @ResourceGroupPreparer(name_prefix='cli-test-std_zrs', location='eastus2')
    def test_vm_disk_create_with_standard_zrs_sku(self, resource_group):
        self.kwargs.update({
            'disk1': 'd1',
            'snapshot1': 's1'
        })
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 4')
        self.cmd('snapshot create -g {rg} -n {snapshot1} --source {disk1} --sku Standard_ZRS',
                 checks=self.check('sku.name', 'Standard_ZRS'))

    @ResourceGroupPreparer(name_prefix='cli-test-ultrassd', location='eastus')
    def test_vmss_ultra_ssd_storage_sku(self, resource_group):

        self.kwargs.update({
            'vmss': 'vm-ultrassd',
            'vmss2': 'vm-ultrassd2'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username admin123 --admin-password testPassword0 --image debian --storage-sku UltraSSD_LRS '
                 ' --data-disk-sizes-gb 4 --zone 2 --location eastus --vm-sku Standard_D2s_v3 --instance-count 1')

        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])
        self.cmd('vmss create -g {rg} -n {vmss2} --admin-username admin123 --admin-password testPassword0 --image debian --ultra-ssd-enabled --zone 2 --location eastus --vm-sku Standard_D2s_v3')
        self.cmd('vmss disk attach -g {rg} --vmss-name {vmss2} --size-gb 5 --sku UltraSSD_LRS')
        self.cmd('vmss show -g {rg} -n {vmss2}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_vmss_update_ultra_ssd_enabled_', location='eastus2')
    @AllowLargeResponse(size_kb=18192)
    def test_vm_vmss_update_ultra_ssd_enabled(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vmss': 'vmss1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image centos --size Standard_D2s_v3 --zone 2 --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm update -g {rg} -n {vm} --ultra-ssd-enabled', checks=[
            self.check('additionalCapabilities.ultraSsdEnabled', True)
        ])

        self.cmd('vmss create -g {rg} -n {vmss} --image centos --vm-sku Standard_D2s_v3 --zone 2 --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vmss deallocate -g {rg} -n {vmss}')
        self.cmd('vmss update -g {rg} -n {vmss} --ultra-ssd-enabled', checks=[
            self.check('additionalCapabilities.ultraSsdEnabled', True)
        ])


class VMUnmanagedDataDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli-test-disk')
    def test_vm_data_unmanaged_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-datadisk-test',
            'disk': 'd7'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk')

        # check we have no data disk
        result = self.cmd('vm show -g {rg} -n {vm}',
                          checks=self.check('length(storageProfile.dataDisks)', 0)).get_output_in_json()

        # get the vhd uri from VM's storage_profile
        blob_uri = result['storageProfile']['osDisk']['vhd']['uri']

        self.kwargs['vhd_uri'] = blob_uri[0:blob_uri.rindex('/') + 1] + 'd7.vhd'

        # now attach
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} -n {disk} --vhd {vhd_uri} --new --caching ReadWrite --size-gb 8 --lun 1')
        # check we have a data disk
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 1),
            self.check('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            self.check('storageProfile.dataDisks[0].lun', 1),
            self.check('storageProfile.dataDisks[0].diskSizeGb', 8),
            self.check('storageProfile.dataDisks[0].createOption', 'Empty'),
            self.check('storageProfile.dataDisks[0].vhd.uri', '{vhd_uri}'),
            self.check('storageProfile.dataDisks[0].name', '{disk}')
        ])

        # now detach
        self.cmd('vm unmanaged-disk detach -g {rg} --vm-name {vm} -n {disk}')

        # check we have no data disk
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('length(storageProfile.dataDisks)', 0))

        # now attach to existing
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} -n {disk} --vhd {vhd_uri} --caching ReadOnly', checks=[
            self.check('storageProfile.dataDisks[0].name', '{disk}'),
            self.check('storageProfile.dataDisks[0].createOption', 'Attach')
        ])


class VMCreateCustomDataScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_create_vm_custom_data')
    def test_vm_create_custom_data(self, resource_group):

        self.kwargs.update({
            'deployment': 'azurecli-test-dep-vm-create-custom-data',
            'username': 'ubuntu',
            'loc': 'westus',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'vm': 'vm-name',
            'custom_data': '#cloud-config\nhostname: myVMhostname',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vm create -g {rg} -n {vm} --admin-username {username} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --custom-data \'{custom_data}\'')

        # custom data is write only, hence we have no automatic way to cross check. Here we just verify VM was provisioned
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('provisioningState', 'Succeeded'))


# region VMSS Tests

class VMSSCreateAndModify(ScenarioTest):

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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_scale_in_policy_')
    def test_vmss_scale_in_policy(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image centos --scale-in-policy NewestVM --admin-username azureuser', checks=[
            self.check('vmss.scaleInPolicy.rules[0]', 'NewestVM')
        ])
        self.cmd('vmss update -g {rg} -n {vmss} --scale-in-policy OldestVM', checks=[
            self.check('scaleInPolicy.rules[0]', 'OldestVM')
        ])


class VMSSCreateOptions(ScenarioTest):

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

        self.cmd('vmss create --image Debian --admin-password testPassword0 -l westus -g {rg} -n {vmss} --disable-overprovision --instance-count {count} --os-disk-caching {caching} --upgrade-policy-mode {update} --authentication-type password --admin-username myadmin --public-ip-address {ip} --os-disk-size-gb 40 --data-disk-sizes-gb 1 --vm-sku Standard_D2_v2 --computer-name-prefix vmss1')
        self.cmd('network lb show -g {rg} -n {vmss}lb ',
                 checks=self.check('frontendIpConfigurations[0].publicIpAddress.id.ends_with(@, \'{ip}\')', True))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('sku.capacity', '{count}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('upgradePolicy.mode', self.kwargs['update'].title()),
            self.check('singlePlacementGroup', True),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'vmss1'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diskSizeGb', 40)
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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_ephemeral_os_disk')
    def test_vmss_create_ephemeral_os_disk(self, resource_group):

        self.kwargs.update({
            'vmss': 'cli-test-vmss-local-1',
            'vmss_2': 'cli-test-vmss-local-2',
            'image': 'UbuntuLTS',
            'count': 2,
            'caching': 'ReadOnly',
            'user': 'user_1',
            'password': 'testPassword09'
        })

        # check that we can create a vmss with local / ephemeral os disk.
        self.cmd('vmss create --resource-group {rg} --name {vmss} --image {image} --ephemeral-os-disk --disable-overprovision '
                 '--instance-count {count} --data-disk-sizes-gb 1 --storage-sku os=standard_lrs 0=premium_lrs --admin-username {user} --admin-password {password}')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS')
        ])

        # explicitly specify os-disk-caching
        self.cmd('vmss create --resource-group {rg} --name {vmss_2} --image {image} --ephemeral-os-disk '
                 '--os-disk-caching {caching} --disable-overprovision --instance-count {count} --admin-username {user} --admin-password {password}')
        self.cmd('vmss show -g {rg} -n {vmss_2}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local')
        ])

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

        self.cmd('vmss create --image Debian --admin-username clitest1 --admin-password testPassword0 -l westus -g {rg} -n {vmss}  --storage-sku {sku}')
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
            'ssh_key_2': self.create_temp_file(0),
            'ssh_dest': '/home/myadmin/.ssh/authorized_keys'
        })

        with open(self.kwargs['ssh_key_2'], 'w') as f:
            f.write(TEST_SSH_KEY_PUB_2)

        self.cmd('vmss create --image Debian -l westus -g {rg} -n {vmss_1} --authentication-type all '
                 ' --admin-username myadmin --admin-password testPassword0 --ssh-key-value \'{ssh_key}\'',
                 checks=[
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication', False),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB)
                 ])

        self.cmd('vmss create --image Debian -l westus -g {rg} -n {vmss_2} --authentication-type ssh '
                 ' --admin-username myadmin --ssh-key-value "{ssh_key}" "{ssh_key_2}" --ssh-dest-key-path "{ssh_dest}"',
                 checks=[
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.disablePasswordAuthentication', True),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[1].keyData', TEST_SSH_KEY_PUB_2),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[0].path', '{ssh_dest}'),
                     self.check('vmss.virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys[1].path', '{ssh_dest}'),
                 ])


class VMSSCreateBalancerOptionsTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_none')
    def test_vmss_create_none_options(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'ssh_key': TEST_SSH_KEY_PUB,
            'quotes': '""' if platform.system() == 'Windows' else "''"
        })
        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --load-balancer {quotes} --admin-username ubuntu --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --vm-sku Basic_A1')
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
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian --admin-username clittester --ssh-key-value '{ssh_key}' --app-gateway apt1 --instance-count 5",
                 checks=self.check('vmss.provisioningState', 'Succeeded'))
        # spot check it is using gateway
        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('sku.capacity', 5),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].ipConfigurations[0].applicationGatewayBackendAddressPools[0].resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(location='eastus2')
    def test_vmss_create_default_app_gateway(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        res = self.cmd("vmss create -g {rg} --name {vmss} --validate --image UbuntuLTS --disable-overprovision --instance-count 101 --single-placement-group false "
                       "--admin-username ubuntuadmin --generate-ssh-keys").get_output_in_json()
        # Ensure generated template is valid. "Quota Exceeding" is expected on most subscriptions, so we allow that.
        self.assertTrue(not res['error'] or (res['error']['details'][0]['code'] == 'QuotaExceeded'))

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_lb')
    def test_vmss_existing_lb(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'lb': 'lb1'
        })
        self.cmd('network lb create -g {rg} -n {lb} --backend-pool-name test')
        self.cmd('vmss create -g {rg} -n {vmss} --load-balancer {lb} --image UbuntuLTS --admin-username clitester --admin-password TestTest12#$')

    @ResourceGroupPreparer()
    def test_vmss_single_placement_group_default_to_std_lb(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --single-placement-group false')
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
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian --admin-username clittester --ssh-key-value '{ssh_key}' --vm-domain-name {dns_label} --public-ip-per-vm --dns-servers 10.0.0.6 10.0.0.5 --nsg {nsg}",
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


class VMSSUpdateTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_')
    def test_vmss_update(self, resource_group):
        self.kwargs.update({
            'vmss': 'winvmss'
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.licenseType', 'Windows_Server'),
        ])

        # test --license-type
        self.cmd('vmss update -g {rg} -n {vmss} --license-type None', checks=[
            self.check('virtualMachineProfile.licenseType', 'None')
        ])

        # test generic update on the vmss
        self.cmd('vmss update -g {rg} -n {vmss} --set virtualMachineProfile.licenseType=Windows_Server', checks=[
            self.check('virtualMachineProfile.licenseType', 'Windows_Server')
        ])

        # get the instance id of the VM instance
        self.kwargs['instance_id'] = self.cmd('vmss list-instances -n {vmss} -g {rg}').get_output_in_json()[0]['instanceId']

        # test updating a VM instance's protection policy
        self.cmd('vmss update -g {rg} -n {vmss} --protect-from-scale-in True --protect-from-scale-set-actions True --instance-id {instance_id}', checks=[
            self.check('protectionPolicy.protectFromScaleIn', True),
            self.check('protectionPolicy.protectFromScaleSetActions', True)
        ])

        # test generic update on a VM instance
        self.cmd('vmss update -g {rg} -n {vmss} --set protectionPolicy.protectFromScaleIn=False protectionPolicy.protectFromScaleSetActions=False --instance-id {instance_id}', checks=[
            self.check('protectionPolicy.protectFromScaleIn', False),
            self.check('protectionPolicy.protectFromScaleSetActions', False)
        ])

        # test that cannot try to update protection policy on VMSS itself
        self.cmd('vmss update -g {rg} -n {vmss} --protect-from-scale-in True --protect-from-scale-set-actions True', expect_failure=True)

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_', location='westus2')
    def test_vmss_update_cross_tenant(self, resource_group):
        self.kwargs.update({
            'location': 'westus2',
            'another_rg': self.create_random_name('cli_test_vmss_update_', 40),
            'vm': self.create_random_name('cli_test_vmss_update_', 40),
            'image_name': self.create_random_name('cli_test_vmss_update_', 40),
            'aux_sub': '1c638cf4-608f-4ee6-b680-c329e824c3a8',
            'aux_tenant': '72f988bf-86f1-41af-91ab-2d7cd011db47',
            'sig_name': self.create_random_name('cli_test_vmss_update_', 40),
            'image_definition_name_1': self.create_random_name('cli_test_vmss_update_', 40),
            'image_definition_name_2': self.create_random_name('cli_test_vmss_update_', 40),
            'version': '0.1.0',
            'vmss': 'cross_tenant_vmss',
        })

        # Prepare sig in another tenant
        self.cmd('group create -g {another_rg} --location {location} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['another_rg']))
        self.cmd(
            'vm create -g {another_rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {another_rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)
        self.cmd('vm deallocate -g {another_rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {another_rg} -n {vm} --subscription {aux_sub}')
        res = self.cmd(
            'image create -g {another_rg} -n {image_name} --source {vm} --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'image_id': res['id']
        })

        self.cmd('sig create -g {another_rg} --gallery-name {sig_name} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['sig_name']))
        res1 = self.cmd(
            'sig image-definition create -g {another_rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name_1} --os-type linux -p publisher1 -f offer1 -s sku1 --subscription {aux_sub}',
            checks=self.check('name', self.kwargs['image_definition_name_1'])).get_output_in_json()
        self.cmd(
            'sig image-version create -g {another_rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name_1} --gallery-image-version {version} --managed-image {image_name} --replica-count 1 --subscription {aux_sub}',
            checks=self.check('name', self.kwargs['version']))

        res2 = self.cmd(
            'sig image-definition create -g {another_rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name_2} --os-type linux -p publisher2 -f offer2 -s sku2 --subscription {aux_sub}',
            checks=self.check('name', self.kwargs['image_definition_name_2'])).get_output_in_json()
        self.cmd(
            'sig image-version create -g {another_rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name_2} --gallery-image-version {version} --managed-image {image_name} --replica-count 1 --subscription {aux_sub}',
            checks=self.check('name', self.kwargs['version']))

        self.kwargs.update({
            'image_1_id': res1['id'],
            'image_2_id': res2['id']
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image {image_1_id}')
        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('name', self.kwargs['vmss']),
            self.check('virtualMachineProfile.storageProfile.imageReference.id', self.kwargs['image_1_id'])
        ])

        self.cmd('vmss update -g {rg} -n {vmss} --set virtualMachineProfile.storageProfile.imageReference.id={image_2_id}', checks=[
            self.check('name', self.kwargs['vmss']),
            self.check('virtualMachineProfile.storageProfile.imageReference.id', self.kwargs['image_2_id'])
        ])

        self.cmd('group delete -n {another_rg} -y --subscription {aux_sub}')


class AcceleratedNetworkingTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_accelerated_networking')
    def test_vmss_accelerated_networking(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd("vmss create -n {vmss} -g {rg} --vm-sku Standard_DS4_v2 --image Win2016Datacenter --admin-username clittester --admin-password Test12345678!!! --accelerated-networking --instance-count 1")
        self.cmd('vmss show -n {vmss} -g {rg}',
                 checks=self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].enableAcceleratedNetworking', True))

    @ResourceGroupPreparer()
    def test_vm_accelerated_networking(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })
        # Note: CLI turns sets accelerated_networking to true based on vm size and os image.
        # See _validate_vm_vmss_accelerated_networking for more info.
        self.cmd("vm create -n {vm} -g {rg} --size Standard_DS4_v2 --image ubuntults --admin-username clittester --generate-ssh-keys")
        self.cmd('network nic show -n {vm}vmnic -g {rg}', checks=self.check('enableAcceleratedNetworking', True))


class ApplicationSecurityGroup(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_asg')
    def test_vmss_asg(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'vm': 'vm1',
            'asg': 'asg1'
        })
        asg_id = self.cmd('network asg create -g {rg} -n {asg}').get_output_in_json()['id']
        self.cmd('vmss create -g {rg} -n {vmss} --image debian --instance-count 1 --asgs {asg} --admin-username clittester --generate-ssh-keys').get_output_in_json()
        self.cmd('vm create -g {rg} -n {vm} --image debian --asgs {asg} --admin-username clittester --generate-ssh-keys').get_output_in_json()
        self.cmd('vmss show -g {rg} -n {vmss}', checks=self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].ipConfigurations[0].applicationSecurityGroups[0].id', asg_id))
        self.cmd('network nic show -g {rg} -n {vm}VMNIC', checks=self.check('ipConfigurations[0].applicationSecurityGroups[0].id', asg_id))


class SecretsScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vm_secrets')
    def test_vm_create_linux_secrets(self, resource_group, resource_group_location):

        self.kwargs.update({
            'admin': 'ubuntu',
            'loc': 'westus',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'ssh_key': TEST_SSH_KEY_PUB,
            'vm': 'vm-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
            'vault': self.create_random_name('vmlinuxkv', 20)
        })

        message = 'Secret is missing vaultCertificates array or it is empty at index 0'
        with self.assertRaisesRegexp(CLIError, message):
            self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\'')

        vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')
        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
        self.kwargs['secrets'] = json.dumps(vm_format)

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\'')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', '{secret_out}')
        ])

    @ResourceGroupPreparer()
    def test_vm_create_windows_secrets(self, resource_group, resource_group_location):

        self.kwargs.update({
            'admin': 'windowsUser',
            'loc': 'westus',
            'image': 'Win2012R2Datacenter',
            'vm': 'vm-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': [{'certificateUrl': 'certurl'}]}]),
            'vault': self.create_random_name('vmkeyvault', 20)
        })

        message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
                  'vaultCertificate index 0'
        with self.assertRaisesRegexp(CLIError, message):
            self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets \'{secrets}\'')

        vault_out = self.cmd(
            'keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        self.kwargs['secrets'] = self.cmd('vm secret format -s {secret_out} --certificate-store "My"').get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets "{secrets}"')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', self.kwargs['secret_out']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
        ])


class VMSSCreateLinuxSecretsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_linux_secrets')
    @AllowLargeResponse()
    def test_vmss_create_linux_secrets(self, resource_group):
        self.kwargs.update({
            'loc': 'westus',
            'vmss': 'vmss1-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
            'vault': self.create_random_name('vmsslinuxkv', 20),
            'secret': 'mysecret',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
        self.kwargs['secrets'] = json.dumps(vm_format)

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --admin-username deploy --ssh-key-value \'{ssh_key}\' --secrets \'{secrets}\'')

        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('virtualMachineProfile.osProfile.secrets[0].vaultCertificates[0].certificateUrl', '{secret_out}')
        ])


class VMSSCreateExistingOptions(ScenarioTest):

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

        self.cmd('vmss create --image CentOS --os-disk-name {os_disk} --admin-username ubuntu --vnet-name {vnet} --subnet {subnet} -l "West US" --vm-sku {sku} --storage-container-name {container} -g {rg} --name {vmss} --load-balancer {lb} --ssh-key-value \'{ssh_key}\' --backend-pool-name {bepool} --use-unmanaged-disk')
        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('sku.name', '{sku}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.name', '{os_disk}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{container}\')', True)
        ])
        self.cmd('network lb show --name {lb} -g {rg}',
                 checks=self.check('backendAddressPools[0].backendIpConfigurations[0].id.contains(@, \'{vmss}\')', True))
        self.cmd('network vnet show --name {vnet} -g {rg}',
                 checks=self.check('subnets[0].ipConfigurations[0].id.contains(@, \'{vmss}\')', True))


class VMSSCreateExistingIdsOptions(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_ids')
    def test_vmss_create_existing_ids_options(self, resource_group):

        from msrestazure.tools import resource_id, is_valid_resource_id
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

        self.cmd('vmss create --image CentOS --os-disk-name {os_disk} --admin-username ubuntu --subnet {subnet_id} -l "West US" --vm-sku {sku} --storage-container-name {container} -g {rg} --name {vmss} --load-balancer {lb_id} --ssh-key-value \'{ssh_key}\' --backend-pool-name {bepool} --use-unmanaged-disk')
        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('sku.name', '{sku}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.name', '{os_disk}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{container}\')', True)
        ])
        self.cmd('network lb show --name {lb} -g {rg}',
                 checks=self.check('backendAddressPools[0].backendIpConfigurations[0].id.contains(@, \'{vmss}\')', True))
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

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password TestTest12#$ --instance-count {count}')

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
        self.assertTrue(result['instance 0'].split('.')[1], '5000')
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
        self.cmd('vmss create --resource-group {rg} --name {vmss1} --location {loc} --instance-count 2 --image Centos --priority Regular')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss1}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss1} --instance-id {id}', expect_failure=True)

        # simulate-eviction on a Spot VMSS with Deallocate policy, expect VMSS instance to be deallocated
        self.cmd('vmss create --resource-group {rg} --name {vmss2} --location {loc} --instance-count 2 --image Centos --priority Spot --eviction-policy Deallocate --lb-sku Standard')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss2}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss2} --instance-id {id}')
        time.sleep(180)
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss2} --instance-id {id}', checks=[
            self.check('length(statuses)', 2),
            self.check('statuses[0].code', 'ProvisioningState/succeeded'),
            self.check('statuses[1].code', 'PowerState/deallocated'),
        ])

        # simulate-eviction on a Spot VMSS with Delete policy, expect VMSS instance to be deleted
        self.cmd('vmss create --resource-group {rg} --name {vmss3} --location {loc} --instance-count 2 --image Centos --priority Spot --eviction-policy Delete --lb-sku Standard')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss3} --instance-id {id}')
        time.sleep(180)
        self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}', checks=[self.check('length(@)', len(self.kwargs['instance_ids']) - 1)])
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss3} --instance-id {id}', expect_failure=True)


class VMSSCustomDataScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_custom_data')
    def test_vmss_create_custom_data(self):

        self.kwargs.update({
            'vmss': 'vmss-custom-data',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --admin-username deploy --ssh-key-value "{ssh_key}" --custom-data "#cloud-config\nhostname: myVMhostname"')

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
        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image UbuntuLTS --use-unmanaged-disk')
        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image UbuntuLTS --use-unmanaged-disk')

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

        self.cmd('vmss create -g {rg} -n {vmss} --admin-username admin123 --admin-password PasswordPassword1! --image centos --instance-count 1 --public-ip-address ""')
        # TODO: restore error validation when #5155 is addressed
        # with self.assertRaises(AssertionError) as err:
        self.cmd('vmss list-instance-connection-info -g {rg} -n {vmss}', expect_failure=True)
        # self.assertTrue('internal load balancer' in str(err.exception))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-08-01')
class VMSSLoadBalancerWithSku(ScenarioTest):

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
        self.cmd('vmss create -g {rg} -l {loc} -n {vmss0} --image UbuntuLTS --admin-username admin123 --admin-password PasswordPassword1!')
        self.cmd('network lb list -g {rg}', checks=self.check('[0].sku.name', 'Basic'))
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Basic'),
            self.check('[0].publicIpAllocationMethod', 'Dynamic')
        ])

        # but you can overrides the defaults
        self.cmd('vmss create -g {rg} -l {loc} -n {vmss} --lb {lb} --lb-sku {sku} --public-ip-address {ip} --image UbuntuLTS --admin-username admin123 --admin-password PasswordPassword1!')
        self.cmd('network lb show -g {rg} -n {lb}',
                 checks=self.check('sku.name', 'Standard'))
        self.cmd('network public-ip show -g {rg} -n {ip}', checks=[
            self.check('sku.name', 'Standard'),
            self.check('publicIpAllocationMethod', 'Static')
        ])


class MSIScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_msi')
    def test_vm_msi(self, resource_group):
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group),
            'vm1': 'vm1',
            'vm1_id': '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachines/vm1'.format(subscription_id, resource_group),
            'vm2': 'vm2',
            'vm3': 'vm3',
            'sub': subscription_id
        })

        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            # create a linux vm with default configuration
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope}', checks=[
                self.check('identity.role', 'Contributor'),
                self.check('identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vm create -g {rg} -n {vm2} --image Win2016Datacenter --assign-identity --scope {vm1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1!', checks=[
                self.check('identity.role', 'reader'),
                self.check('identity.scope', '{vm1_id}'),
            ])
            uuid.UUID(result.get_output_in_json()['identity']['systemAssignedIdentity'])

            # create a linux vm w/o identity and later enable it
            vm3_result = self.cmd('vm create -g {rg} -n {vm3} --image debian --admin-username admin123 --admin-password PasswordPassword1!').get_output_in_json()
            self.assertIsNone(vm3_result.get('identity'))
            result = self.cmd('vm identity assign -g {rg} -n {vm3} --scope {vm1_id} --role reader', checks=[
                self.check('role', 'reader'),
                self.check('scope', '{vm1_id}'),
            ])
            uuid.UUID(result.get_output_in_json()['systemAssignedIdentity'])

            self.cmd('vm identity remove -g {rg} -n {vm3}')
            self.cmd('vm identity show -g {rg} -n {vm3}', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_msi')
    def test_vmss_msi(self, resource_group):
        subscription_id = self.get_subscription_id()

        self.kwargs.update({
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group),
            'vmss1': 'vmss1',
            'vmss1_id': '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachineScaleSets/vmss1'.format(subscription_id, resource_group),
            'vmss2': 'vmss2',
            'vmss3': 'vmss3',
            'sub': subscription_id
        })
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            # create linux vm with default configuration
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope}', checks=[
                self.check('vmss.identity.role', 'Contributor'),
                self.check('vmss.identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vmss create -g {rg} -n {vmss2} --image Win2016Datacenter --instance-count 1 --assign-identity --scope {vmss1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1!', checks=[
                self.check('vmss.identity.role', 'reader'),
                self.check('vmss.identity.scope', '{vmss1_id}'),
            ]).get_output_in_json()
            uuid.UUID(result['vmss']['identity']['systemAssignedIdentity'])

            # create a linux vm w/o identity and later enable it
            result = self.cmd('vmss create -g {rg} -n {vmss3} --image debian --instance-count 1 --admin-username admin123 --admin-password PasswordPassword1!').get_output_in_json()['vmss']
            self.assertIsNone(result.get('identity'))

            result = self.cmd('vmss identity assign -g {rg} -n {vmss3} --scope "{vmss1_id}" --role reader', checks=[
                self.check('role', 'reader'),
                self.check('scope', '{vmss1_id}'),
            ]).get_output_in_json()
            uuid.UUID(result['systemAssignedIdentity'])

            self.cmd('vmss identity remove -g {rg} -n {vmss3}')
            self.cmd('vmss identity show -g {rg} -n {vmss3}', checks=self.is_empty())

            # test that vmss identity remove does not fail when the vmss has no assigned identities.
            self.cmd('vmss identity remove -g {rg} -n {vmss3}', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_msi_no_scope')
    def test_vm_msi_no_scope(self, resource_group):

        self.kwargs.update({
            'vm1': 'vm1',
            'vmss1': 'vmss1',
            'vm2': 'vm2',
            'vmss2': 'vmss2',
        })

        # create a linux vm with identity but w/o a role assignment (--scope "")
        self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!', checks=[
            self.check('identity.scope', None),
            self.check('identity.role', None),
        ])

        # create a vmss with identity but w/o a role assignment (--scope "")
        self.cmd('vmss create -g {rg} -n {vmss1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!', checks=[
            self.check('vmss.identity.scope', None),
        ])

        # create a vm w/o identity
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username admin123 --admin-password PasswordPassword1!')
        # assign identity but w/o a role assignment
        self.cmd('vm identity assign -g {rg} -n {vm2}', checks=[
            self.check('scope', None),
        ])

        self.cmd('vmss create -g {rg} -n {vmss2} --image debian --admin-username admin123 --admin-password PasswordPassword1!')
        self.cmd('vmss identity assign -g {rg} -n {vmss2}', checks=[
            self.check('scope', None),
        ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_vm_explicit_msi(self, resource_group):

        self.kwargs.update({
            'emsi': 'id1',
            'emsi2': 'id2',
            'vm': 'vm1',
            'sub': self.get_subscription_id(),
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(self.get_subscription_id(), resource_group),
            'user': 'ubuntuadmin'
        })

        # create a managed identity
        emsi_result = self.cmd('identity create -g {rg} -n {emsi} --tags tag1=d1', checks=[
            self.check('name', '{emsi}'),
            self.check('tags.tag1', 'd1')]).get_output_in_json()
        emsi2_result = self.cmd('identity create -g {rg} -n {emsi2}').get_output_in_json()

        # create a vm with only user assigned identity
        result = self.cmd('vm create -g {rg} -n vm2 --image ubuntults --assign-identity {emsi} --generate-ssh-keys --admin-username {user}', checks=[
            self.check('identity.role', None),
            self.check('identity.scope', None),
        ]).get_output_in_json()
        emsis = [x.lower() for x in result['identity']['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])
        self.assertFalse(result['identity']['systemAssignedIdentity'])

        # create a vm with system + user assigned identities
        result = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --assign-identity {emsi} [system] --role reader --scope {scope} --generate-ssh-keys --admin-username {user}').get_output_in_json()
        emsis = [x.lower() for x in result['identity']['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])
        result = self.cmd('vm identity show -g {rg} -n {vm}', checks=[
            self.check('type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        emsis = [x.lower() for x in result['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])
        # assign a new managed identity
        self.cmd('vm identity assign -g {rg} -n {vm} --identities {emsi2}')
        result = self.cmd('vm identity show -g {rg} -n {vm}').get_output_in_json()
        emsis = [x.lower() for x in result['userAssignedIdentities'].keys()]
        self.assertEqual(set(emsis), set([emsi_result['id'].lower(), emsi2_result['id'].lower()]))

        # remove the 1st user assigned identity
        self.cmd('vm identity remove -g {rg} -n {vm} --identities {emsi}')
        result = self.cmd('vm identity show -g {rg} -n {vm}', checks=[
            self.check('type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        emsis = [x.lower() for x in result['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi2_result['id'].lower()])

        # remove the 2nd
        self.cmd('vm identity remove -g {rg} -n {vm} --identities {emsi2}')
        # verify the VM still has the system assigned identity
        self.cmd('vm identity show -g {rg} -n {vm}', checks=[
            self.check('type', 'SystemAssigned'),
            self.check('userAssignedIdentities', None),
        ])

        # remove the last assigned identity and check that remove does not fail if there are no assigned identities.
        self.cmd('vm identity remove -g {rg} -n {vm}', checks=self.is_empty())
        self.cmd('vm identity remove -g {rg} -n {vm}', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_explicit_msi', location='westcentralus')
    def test_vmss_explicit_msi(self, resource_group):

        self.kwargs.update({
            'emsi': 'id1',
            'emsi2': 'id2',
            'vmss': 'vmss1',
            'sub': self.get_subscription_id(),
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(self.get_subscription_id(), resource_group)
        })

        # create a managed identity
        emsi_result = self.cmd('identity create -g {rg} -n {emsi}').get_output_in_json()
        emsi2_result = self.cmd('identity create -g {rg} -n {emsi2}').get_output_in_json()

        # create a vmss with system + user assigned identities
        result = self.cmd('vmss create -g {rg} -n {vmss} --image ubuntults --assign-identity {emsi} [system] --role reader --scope {scope} --instance-count 1 --generate-ssh-keys --admin-username ubuntuadmin').get_output_in_json()
        emsis = [x.lower() for x in result['vmss']['identity']['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])

        result = self.cmd('vmss identity show -g {rg} -n {vmss}', checks=[
            self.check('type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        emsis = [x.lower() for x in result['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])

        # assign a new managed identity
        self.cmd('vmss identity assign -g {rg} -n {vmss} --identities {emsi2}')
        result = self.cmd('vmss identity show -g {rg} -n {vmss}').get_output_in_json()
        emsis = [x.lower() for x in result['userAssignedIdentities'].keys()]
        self.assertEqual(set(emsis), set([emsi_result['id'].lower(), emsi2_result['id'].lower()]))

        # update instances
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids *')

        # remove the 1st user assigned identity
        self.cmd('vmss identity remove -g {rg} -n {vmss} --identities {emsi}')
        result = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()
        emsis = [x.lower() for x in result['identity']['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi2_result['id'].lower()])

        # remove the 2nd
        self.cmd('vmss identity remove -g {rg} -n {vmss} --identities {emsi2}')
        # verify the vmss still has the system assigned identity
        self.cmd('vmss identity show -g {rg} -n {vmss}', checks=[
            self.check('userAssignedIdentities', None),
            self.check('type', 'SystemAssigned'),
        ])


class VMLiveScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_progress')
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging

        self.kwargs.update({'vm': 'vm123'})

        with force_progress_logging() as test_io:
            self.cmd('vm create -g {rg} -n {vm} --admin-username {vm} --admin-password PasswordPassword1! --authentication-type password --image debian')

        content = test_io.getvalue()
        print(content)
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

    @ResourceGroupPreparer(name_prefix='cli_test_vm_zone', location='eastus2')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_create_zones(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '2',
            'vm': 'vm123',
            'ip': 'vm123ip'
        })
        self.cmd('vm create -g {rg} -n {vm} --admin-username clitester --admin-password PasswordPassword1! --image debian --zone {zones} --public-ip-address {ip}',
                 checks=self.check('zones', '{zones}'))
        self.cmd('network public-ip show -g {rg} -n {ip}',
                 checks=self.check('zones[0]', '{zones}'))
        # Test VM's specific table output
        result = self.cmd('vm show -g {rg} -n {vm} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, self.kwargs['zones']]).issubset(table_output))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_zone', location='westus')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_error_on_zone_unavailable(self, resource_group, resource_group_location):
        try:
            self.cmd('vm create -g {rg} -n vm1 --admin-username clitester --admin-password PasswordPassword1! --image debian --zone 1')
        except Exception as ex:
            self.assertTrue('availability zone is not yet supported' in str(ex))

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_zones', location='eastus2')
    @AllowLargeResponse(size_kb=99999)
    def test_vmss_create_single_zone(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '2',
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --zones {zones}')
        self.cmd('vmss show -g {rg} -n {vmss}',
                 checks=self.check('zones[0]', '{zones}'))
        result = self.cmd('vmss show -g {rg} -n {vmss} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, self.kwargs['vmss'], self.kwargs['zones']]).issubset(table_output))
        result = self.cmd('vmss list -g {rg} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, self.kwargs['vmss'], self.kwargs['zones']]).issubset(table_output))

        self.cmd('network lb list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard')
        ])
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard'),
            self.check('[0].zones', ['2'])
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_zones', location='eastus2')
    @AllowLargeResponse(size_kb=99999)
    def test_vmss_create_x_zones(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '1 2 3',
            'vmss': 'vmss123',
            'lb': 'vmss123LB',  # default name chosen by the create
            'rule': 'LBRule',  # default name chosen by the create,
            'nsg': 'vmss123NSG',  # default name chosen by the create
            'probe': 'LBProbe'
        })
        self.cmd('vmss create -g {rg} -n {vmss}  --admin-username clitester --admin-password PasswordPassword1! --image debian --zones {zones} --vm-sku Standard_D1_V2')
        self.cmd('vmss show -g {rg} -n {vmss}',
                 checks=self.check('zones', ['1', '2', '3']))
        result = self.cmd('vmss show -g {rg} -n {vmss} -otable')
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, self.kwargs['vmss']] + self.kwargs['zones'].split()).issubset(table_output))

        self.cmd('network lb list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard')
        ])
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard'),
            self.check('[0].zones', None)
        ])

        # Now provision a web server
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n {probe} --protocol http --port 80 --path /')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n {rule} --protocol tcp --frontend-port 80 --backend-port 80 --probe-name {probe}')
        self.cmd('network nsg rule create -g {rg} --nsg-name {nsg} -n allowhttp --priority 4096 --destination-port-ranges 80 --protocol Tcp')

        self.cmd('vmss extension set -g {rg} --vmss-name {vmss} -n customScript --publisher Microsoft.Azure.Extensions --settings "{{\\"commandToExecute\\": \\"apt-get update && sudo apt-get install -y nginx\\"}}" --version 2.0')
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids "*"')

        # verify the server works
        result = self.cmd('vmss list-instance-connection-info -g {rg} -n {vmss} -o tsv')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + result.output.split(':')[0])
        self.assertTrue('Welcome to nginx' in str(r.content))

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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_zones', location='eastus2')
    @AllowLargeResponse(size_kb=99999)
    def test_vmss_create_zonal_with_fd(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '2',
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --zones {zones} --platform-fault-domain-count 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('singlePlacementGroup', False)
        ])

        self.cmd('network lb list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard')
        ])
        self.cmd('network public-ip list -g {rg}', checks=[
            self.check('[0].sku.name', 'Standard'),
            self.check('[0].zones', ['2'])
        ])


class VMRunCommandScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command')
    def test_vm_run_command_e2e(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vm': 'test-run-command-vm',
            'loc': resource_group_location
        })

        self.cmd('vm run-command list -l {loc}')
        self.cmd('vm run-command show --command-id RunShellScript -l {loc}')
        public_ip = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --admin-password Test12345678!! --generate-ssh-keys').get_output_in_json()['publicIpAddress']

        self.cmd('vm open-port -g {rg} -n {vm} --port 80')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx' in str(r.content))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command_w_params')
    def test_vm_run_command_with_parameters(self, resource_group):
        self.kwargs.update({'vm': 'test-run-command-vm2'})
        self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username clitest1 --admin-password Test12345678!! --generate-ssh-keys')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world')


class VMSSRunCommandScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_run_command')
    def test_vmss_run_command_e2e(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vmss': 'test-run-command-vmss',
            'loc': resource_group_location
        })

        # Test basic run-command commands
        self.cmd('vmss run-command list -l {loc}')
        self.cmd('vmss run-command show --command-id RunShellScript -l {loc}')

        self.cmd('vmss create -g {rg} -n {vmss} --image ubuntults --admin-username clitest1 --instance-count 1 --generate-ssh-keys --disable-overprovision').get_output_in_json()

        # get load balancer and allow trafic to scale set.
        lb = self.cmd('network lb list -g {rg}').get_output_in_json()[0]
        self.kwargs.update({
            'lb_name': lb['name'],
            'lb_backend': lb['backendAddressPools'][0]['name'],
            'lb_frontend': lb['frontendIpConfigurations'][0]['name'],
            'lb_ip_id': lb['frontendIpConfigurations'][0]['publicIpAddress']['id']
        })
        self.cmd('az network lb rule create -g {rg} --name allowTrafficRule --lb-name {lb_name} --backend-pool-name {lb_backend} --frontend-ip-name {lb_frontend} --backend-port 80 --frontend-port 80 --protocol tcp')
        public_ip = self.cmd('az network public-ip show --ids {lb_ip_id}').get_output_in_json()['ipAddress']

        self.kwargs['instance_ids'] = " ".join(self.cmd('az vmss list-instances -n {vmss} -g {rg} --query "[].id"').get_output_in_json())

        self.cmd('vmss run-command invoke --ids {instance_ids} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"')

        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)

        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx' in str(r.content))

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_run_command_w_params')
    def test_vmss_run_command_with_parameters(self, resource_group):
        self.kwargs.update({'vmss': 'test-run-command-vmss2'})
        self.cmd('vmss create -g {rg} -n {vmss} --image debian --admin-username clitest1 --generate-ssh-keys')
        self.kwargs['instance_ids'] = self.cmd('vmss list-instances --resource-group {rg} --name {vmss} --query "[].instanceId"').get_output_in_json()

        for id in self.kwargs['instance_ids']:
            self.kwargs['id'] = id
            self.cmd('vmss run-command invoke -g {rg} -n {vmss} --instance-id {id} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world')


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMDiskEncryptionTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_encryption', location='westus')
    def test_vmss_disk_encryption_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vault': self.create_random_name('vault', 10),
            'vmss': 'vmss1'
        })
        self.cmd('keyvault create -g {rg} -n {vault} --enabled-for-disk-encryption "true"')
        time.sleep(60)  # to avoid 504(too many requests) on a newly created vault
        self.cmd('vmss create -g {rg} -n {vmss} --image win2016datacenter --instance-count 1 --admin-username clitester1 --admin-password Test123456789!')
        self.cmd('vmss encryption enable -g {rg} -n {vmss} --disk-encryption-keyvault {vault}')
        self.cmd('vmss update-instances -g {rg} -n {vmss}  --instance-ids "*"')
        self.cmd('vmss encryption show -g {rg} -n {vmss}', checks=self.check('[0].disks[0].statuses[0].code', 'EncryptionState/encrypted'))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'EnableEncryption'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
        ])
        self.cmd('vmss encryption disable -g {rg} -n {vmss}')
        self.cmd('vmss update-instances -g {rg} -n {vmss}  --instance-ids "*"')
        self.cmd('vmss encryption show -g {rg} -n {vmss}', checks=self.check('[0].disks[0].statuses[0].code', 'EncryptionState/notEncrypted'))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'DisableEncryption'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_encryption', location='westus')
    def test_vm_disk_encryption_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vault': self.create_random_name('vault', 10),
            'vm': 'vm1'
        })
        self.cmd('keyvault create -g {rg} -n {vault} --enabled-for-disk-encryption "true"')
        time.sleep(60)  # to avoid 504(too many requests) on a newly created vault
        self.cmd('vm create -g {rg} -n {vm} --image win2012datacenter --admin-username clitester1 --admin-password Test123456789!')
        self.cmd('vm encryption enable -g {rg} -n {vm} --disk-encryption-keyvault {vault}')
        self.cmd('vm encryption show -g {rg} -n {vm}', checks=[self.check('disks[0].statuses[0].code', 'EncryptionState/encrypted')])
        self.cmd('vm encryption disable -g {rg} -n {vm}')

    @ResourceGroupPreparer(name_prefix='cli_test_vm_encryption_at_host_', location='westus')
    def test_vm_encryption_at_host(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vmss': 'vmss1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image centos --generate-ssh-keys --nsg-rule NONE --encryption-at-host --admin-username exampleusername')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('securityProfile.encryptionAtHost', True)
        ])
        self.cmd('vmss create -g {rg} -n {vmss} --image centos --generate-ssh-keys --encryption-at-host --admin-username exampleusername')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.securityProfile.encryptionAtHost', True)
        ])


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
        self.cmd('vmss create -g {rg} -n {vmss} --image ubuntults --admin-username clitester1 --admin-password Testqwer1234! --lb {lb} --health-probe {probe}')

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


class VMSSPriorityTesting(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='vmss_low_pri')
    def test_vmss_create_with_low_priority(self, resource_group):
        self.kwargs.update({
            'priority': 'Low',
            'vmss': 'vmss1',
            'vmss2': 'vmss2'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --priority {priority} --lb-sku Standard')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.priority', '{priority}'),
            self.check('virtualMachineProfile.evictionPolicy', 'Deallocate')
        ])

        self.cmd('vmss create -g {rg} -n {vmss2} --admin-username clitester --admin-password PasswordPassword1! --image centos --priority {priority} --eviction-policy delete --lb-sku Standard')
        self.cmd('vmss show -g {rg} -n {vmss2}', checks=[
            self.check('virtualMachineProfile.priority', '{priority}'),
            self.check('virtualMachineProfile.evictionPolicy', 'Delete')
        ])


# convert to ScenarioTest and re-record when issue #6006 is fixed
class VMLBIntegrationTesting(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_lb_integration')
    def test_vm_lb_integration(self, resource_group):

        self.kwargs.update({
            'lb': 'lb1',
            'vm1': 'vm1',
            'vm2': 'vm2',
            'avset': 'av1'
        })
        # provision 2 web servers
        self.cmd('vm availability-set create -g {rg} -n {avset}')
        self.cmd('vm create -g {rg} -n {vm1} --image ubuntults --public-ip-address "" --availability-set {avset} --generate-ssh-keys --admin-username ubuntuadmin')
        self.cmd('vm open-port -g {rg} -n {vm1} --port 80')
        self.cmd('vm create -g {rg} -n {vm2} --image ubuntults --public-ip-address "" --availability-set {avset} --generate-ssh-keys --admin-username ubuntuadmin')
        self.cmd('vm open-port -g {rg} -n {vm2} --port 80')

        # provision 1 LB
        self.cmd('network lb create -g {rg} -n {lb}')

        # create LB probe and rule
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n probe1 --protocol Http --port 80 --path /')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n rule1 --protocol Tcp --frontend-port 80 --backend-port 80')

        # add 2 vm into BE Pool
        self.cmd('network nic ip-config address-pool add -g {rg} --lb-name {lb} --address-pool {lb}bepool --nic-name {vm1}VMNic --ip-config-name ipconfig{vm1}')
        self.cmd('network nic ip-config address-pool add -g {rg} --lb-name {lb} --address-pool {lb}bepool --nic-name {vm2}VMNic --ip-config-name ipconfig{vm2}')

        # Create Inbound Nat Rules so each VM can be accessed through SSH
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n inbound-nat-rule1 --frontend-port 50000 --backend-port 22  --protocol Tcp')
        self.cmd('network nic ip-config inbound-nat-rule add -g {rg} --lb-name {lb} --nic-name {vm1}VMNic --ip-config-name ipconfig{vm1} --inbound-nat-rule inbound-nat-rule1')
        self.cmd('network lb inbound-nat-rule create -g {rg} --lb-name {lb} -n inbound-nat-rule2 --frontend-port 50001 --backend-port 22  --protocol Tcp')
        self.cmd('network nic ip-config inbound-nat-rule add -g {rg} --lb-name {lb} --nic-name {vm2}VMNic --ip-config-name ipconfig{vm2} --inbound-nat-rule inbound-nat-rule2')

        # install nginx web servers
        self.cmd('vm run-command invoke -g {rg} -n {vm1} --command-id RunShellScript --scripts "sudo apt-get update && sudo apt-get install -y nginx"')
        self.cmd('vm run-command invoke -g {rg} -n {vm2} --command-id RunShellScript --scripts "sudo apt-get update && sudo apt-get install -y nginx"')

        # ensure all pieces are working together
        result = self.cmd('network public-ip show -g {rg} -n PublicIP{lb}').get_output_in_json()
        pip = result['ipAddress']
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + pip)
        self.assertTrue('Welcome to nginx' in str(r.content))


class VMCreateWithExistingNic(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_create_vm_existing_nic')
    def test_vm_create_existing_nic(self, resource_group):
        import re
        self.cmd('network public-ip create -g {rg} -n my-pip')
        self.cmd('network vnet create -g {rg} -n my-vnet --subnet-name my-subnet1')
        self.cmd('network nic create -g {rg} -n my-nic --subnet my-subnet1 --vnet-name my-vnet --public-ip-address my-pip')
        self.cmd('network nic ip-config create -n my-ipconfig2 -g {rg} --nic-name my-nic --private-ip-address-version IPv6')
        self.cmd('vm create -g {rg} -n vm1 --image centos --nics my-nic --generate-ssh-keys --admin-username ubuntuadmin')
        result = self.cmd('vm show -g {rg} -n vm1 -d').get_output_in_json()
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['publicIps']))
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['privateIps']))


class VMSecretTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_secrets')
    def test_vm_secret_e2e_test(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': 'vm1',
            'vault': self.create_random_name('vmsecretkv', 20),
            'cert': 'vm-secrt-cert',
            'loc': resource_group_location
        })

        vault_result = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-disk-encryption true --enabled-for-deployment true').get_output_in_json()
        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')

        self.cmd('vm create -g {rg} -n {vm} --image rhel --generate-ssh-keys --admin-username rheladmin')
        time.sleep(60)  # ensure we don't hit the DNS exception (ignored under playback)

        self.cmd('keyvault certificate create --vault-name {vault} -n {cert} -p @"{policy_path}"')
        secret_result = self.cmd('vm secret add -g {rg} -n {vm} --keyvault {vault} --certificate {cert}', checks=[
            self.check('length([])', 1),
            self.check('[0].sourceVault.id', vault_result['id']),
            self.check('length([0].vaultCertificates)', 1),
        ]).get_output_in_json()
        self.assertTrue('https://{vault}.vault.azure.net/secrets/{cert}/'.format(**self.kwargs) in secret_result[0]['vaultCertificates'][0]['certificateUrl'])
        self.cmd('vm secret list -g {rg} -n {vm}')
        self.cmd('vm secret remove -g {rg} -n {vm} --keyvault {vault} --certificate {cert}')

        self.cmd('vm secret list -g {rg} -n {vm}',
                 checks=self.check('length([])', 0))


class VMOsDiskSwap(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_os_disk_swap(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'backupDisk': 'disk1',
        })
        self.cmd('vm create -g {rg} -n {vm} --image centos --admin-username clitest123 --generate-ssh-keys --nsg-rule NONE')
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

        self.cmd('vm create -g {rg} -n {vm} --image debian --data-disk-sizes-gb 1 2 --admin-username cligenerics --generate-ssh-keys')

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


class VMGalleryImage(ScenarioTest):
    @ResourceGroupPreparer(location='eastus2')
    def test_gallery_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': 'vm1',
            'vm2': 'vmFromImage',
            'gallery': self.create_random_name(prefix='gallery_', length=20),
            'image': 'image1',
            'version': '1.1.2',
            'version2': '1.1.3',
            'captured': 'managedImage1',
            'image_id': 'TBD',
            'location': resource_group_location,
            'location2': 'westus2',
            'vault': self.create_random_name(prefix='vault-', length=20),
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('sig show -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1',
                 checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition list -g {rg} --gallery-name {gallery}', checks=self.check('length(@)', 1))
        res = self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image}',
                       checks=self.check('name', self.kwargs['image'])).get_output_in_json()
        self.kwargs['image_id'] = res['id']
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --data-disk-sizes-gb 10 --admin-username clitest1 --generate-ssh-key --nsg-rule NONE')
        self.cmd('vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')
        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1',
                 checks=[self.check('name', self.kwargs['version']), self.check('publishingProfile.replicaCount', 1)])

        self.cmd('sig image-version list -g {rg} --gallery-name {gallery} --gallery-image-definition {image}',
                 checks=self.check('length(@)', 1))
        self.cmd('sig image-version show -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version}',
                 checks=self.check('name', self.kwargs['version']))

        self.cmd('sig image-version update -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --target-regions {location2}=1 {location} --replica-count 2',
                 checks=[
                     self.check('publishingProfile.replicaCount', 2),
                     self.check('length(publishingProfile.targetRegions)', 2),
                     self.check('publishingProfile.targetRegions[0].name', 'West US 2'),
                     self.check('publishingProfile.targetRegions[0].regionalReplicaCount', 1),
                     self.check('publishingProfile.targetRegions[0].storageAccountType', 'Standard_LRS'),
                     self.check('publishingProfile.targetRegions[1].name', 'East US 2'),
                     self.check('publishingProfile.targetRegions[1].regionalReplicaCount', 2),
                     self.check('publishingProfile.targetRegions[1].storageAccountType', 'Standard_LRS')
                 ])

        # Create disk encryption set
        vault_id = self.cmd('keyvault create -g {rg} -n {vault} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')

        time.sleep(15)

        # Test --target-region-encryption
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version2} --target-regions {location}=1 --target-region-encryption {des1},0,{des1} --managed-image {captured} --replica-count 1', checks=[
            self.check('publishingProfile.targetRegions[0].name', 'East US 2'),
            self.check('publishingProfile.targetRegions[0].regionalReplicaCount', 1),
            self.check('publishingProfile.targetRegions[0].encryption.osDiskImage.diskEncryptionSetId', '{des1_id}'),
            self.check('publishingProfile.targetRegions[0].encryption.dataDiskImages[0].lun', 0),
            self.check('publishingProfile.targetRegions[0].encryption.dataDiskImages[0].diskEncryptionSetId', '{des1_id}'),
        ])

        self.cmd('vm create -g {rg} -n {vm2} --image {image_id} --admin-username clitest1 --generate-ssh-keys --nsg-rule NONE', checks=self.check('powerState', 'VM running'))

        self.cmd('sig image-version delete -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version}')
        self.cmd('sig image-version delete -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version2}')
        time.sleep(60)  # service end latency
        self.cmd('sig image-definition delete -g {rg} --gallery-name {gallery} --gallery-image-definition {image}')
        self.cmd('sig delete -g {rg} --gallery-name {gallery}')

    @ResourceGroupPreparer(name_prefix='cli_test_gallery_specialized_', location='eastus2')
    def test_gallery_specialized(self, resource_group):
        self.kwargs.update({
            'gallery': self.create_random_name(prefix='gallery_', length=20),
            'image': 'image1'
        })
        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', '{gallery}'))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux --os-state specialized --hyper-v-generation V2 -p publisher1 -f offer1 -s sku1',
                 checks=[self.check('name', '{image}'), self.check('osState', 'Specialized'),
                         self.check('hyperVgeneration', 'V2')])
        self.cmd('disk create -g {rg} -n d1 --size-gb 10')
        self.cmd('disk create -g {rg} -n d2 --size-gb 10')
        self.cmd('disk create -g {rg} -n d3 --size-gb 10')
        s1_id = self.cmd('snapshot create -g {rg} -n s1 --source d1').get_output_in_json()['id']
        s2_id = self.cmd('snapshot create -g {rg} -n s2 --source d2').get_output_in_json()['id']
        s3_id = self.cmd('snapshot create -g {rg} -n s3 --source d3').get_output_in_json()['id']
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version 1.0.0 --os-snapshot s1 --data-snapshots s2 s3 --data-snapshot-luns 2 3',
                 checks=[
                     self.check('storageProfile.osDiskImage.source.id', s1_id),
                     self.check('storageProfile.dataDiskImages[0].source.id', s2_id),
                     self.check('storageProfile.dataDiskImages[1].source.id', s3_id),
                     self.check('storageProfile.dataDiskImages[0].lun', 2),
                     self.check('storageProfile.dataDiskImages[1].lun', 3)
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_test_specialized_image_')
    def test_specialized_image(self, resource_group):
        self.kwargs.update({
            'gallery': self.create_random_name(prefix='gallery_', length=20),
            'image': 'image1',
            'snapshot': 's1',
            'vm1': 'vm1',
            'vm2': 'vm2',
            'vm3': 'vm3',
            'vmss1': 'vmss1',
            'vmss2': 'vmss2'
        })
        self.cmd('sig create -g {rg} --gallery-name {gallery}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux --os-state specialized -p publisher1 -f offer1 -s sku1', checks=[
            self.check('osState', 'Specialized')
        ])
        self.cmd('vm create -g {rg} -n {vm1} --image ubuntults --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        disk = self.cmd('vm show -g {rg} -n {vm1}').get_output_in_json()['storageProfile']['osDisk']['name']
        self.kwargs.update({
            'disk': disk
        })
        self.cmd('snapshot create -g {rg} -n {snapshot} --source {disk}')
        image_version = self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version 1.0.0 --os-snapshot {snapshot}').get_output_in_json()['id']
        self.kwargs.update({
            'image_version': image_version
        })
        self.cmd('vm create -g {rg} -n {vm2} --image {image_version} --specialized --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vmss create -g {rg} -n {vmss1} --image {image_version} --specialized --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        with self.assertRaises(CLIError):
            self.cmd('vm create -g {rg} -n {vm3} --specialized')
        with self.assertRaises(CLIError):
            self.cmd('vmss create -g {rg} -n {vmss2} --specialized')

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_image_version_', location='westus2')
    def test_sig_image_version_cross_tenant(self):
        self.kwargs.update({
            'location': 'westus2',
            'another_rg': self.create_random_name('cli_test_image_version_', 40),
            'vm': self.create_random_name('cli_test_image_version_', 40),
            'image_name': self.create_random_name('cli_test_image_version_', 40),
            'aux_sub': '1c638cf4-608f-4ee6-b680-c329e824c3a8',
            'aux_tenant': '72f988bf-86f1-41af-91ab-2d7cd011db47',
            'sig_name': self.create_random_name('cli_test_image_version_', 40),
            'image_definition_name': self.create_random_name('cli_test_image_version_', 40),
            'version': '0.1.0'
        })

        # Prepare image in another tenant
        self.cmd('group create -g {another_rg} --location {location} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['another_rg']))
        self.cmd(
            'vm create -g {another_rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {another_rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)
        self.cmd('vm deallocate -g {another_rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {another_rg} -n {vm} --subscription {aux_sub}')
        res = self.cmd('image create -g {another_rg} -n {image_name} --source {vm} --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'image_id': res['id']
        })

        self.cmd('sig create -g {rg} --gallery-name {sig_name}',
                 checks=self.check('name', self.kwargs['sig_name']))
        self.cmd(
            'sig image-definition create -g {rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name} --os-type linux -p publisher1 -f offer1 -s sku1',
            checks=self.check('name', self.kwargs['image_definition_name']))
        self.cmd(
            'sig image-version create -g {rg} --gallery-name {sig_name} --gallery-image-definition {image_definition_name} --gallery-image-version {version} --managed-image {image_id} --replica-count 1',
            checks=self.check('name', self.kwargs['version']))

        self.cmd('group delete -n {another_rg} -y --subscription {aux_sub}')


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

        # fails because not a valid type
        self.cmd('ppg create -n fail_ppg -g {rg} -t notAvalidType', expect_failure=True)

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

        self.cmd('ppg create -n {ppg2} -t ultra -g {rg}', checks=[
            self.check('name', '{ppg2}'),
            self.check('location', '{loc}'),
            self.check('proximityPlacementGroupType', 'Ultra')
        ])

        self.cmd('ppg create -n {ppg3} -g {rg}', checks=[
            self.check('name', '{ppg3}'),
            self.check('location', '{loc}'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_ppg_vm_vmss_')
    def test_ppg_with_related_resources(self, resource_group):

        self.kwargs.update({
            'ppg': 'myppg',
            'vm': 'vm1',
            'vmss': 'vmss1',
            'avset': 'avset1',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -n {ppg} -t standard -g {rg}').get_output_in_json()['id']

        self.kwargs['vm_id'] = self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\' --ppg {ppg}').get_output_in_json()['id']

        self.cmd('vmss create -g {rg} -n {vmss} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\' --ppg {ppg_id}')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']

        self.kwargs['avset_id'] = self.cmd('vm availability-set create -g {rg} -n {avset} --ppg {ppg}').get_output_in_json()['id']

        ppg_resource = self.cmd('ppg show -n {ppg} -g {rg}').get_output_in_json()

        # check that the compute resources are created with PPG

        self._assert_ids_equal(ppg_resource['availabilitySets'][0]['id'], self.kwargs['avset_id'], rg_prefix='cli_test_ppg_vm_vmss_')
        self._assert_ids_equal(ppg_resource['virtualMachines'][0]['id'], self.kwargs['vm_id'], rg_prefix='cli_test_ppg_vm_vmss_')
        self._assert_ids_equal(ppg_resource['virtualMachineScaleSets'][0]['id'], self.kwargs['vmss_id'], 'cli_test_ppg_vm_vmss_')

    @ResourceGroupPreparer(name_prefix='cli_test_ppg_update_')
    def test_ppg_update(self, resource_group):
        self.kwargs.update({
            'ppg': 'ppg1',
            'vm': 'vm1',
            'vmss': 'vmss1',
            'avset': 'avset1',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -g {rg} -n {ppg} -t standard').get_output_in_json()['id']

        self.cmd('vmss create -g {rg} -n {vmss} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\'')
        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss}').get_output_in_json()['id']
        self.cmd('vmss deallocate -g {rg} -n {vmss}')
        time.sleep(30)
        self.cmd('vmss update -g {rg} -n {vmss} --ppg {ppg_id}')

        self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\'')
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
        from msrestazure.tools import parse_resource_id

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


# region dedicated host tests
class DedicatedHostScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_dedicated_host_', location='westeurope')
    @ResourceGroupPreparer(name_prefix='cli_test_dedicated_host2_', location='centraluseuap', key='rg2')
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

        self.cmd('vm host create -n {host-name} --host-group {host-group} -d 2 -g {rg} '
                 '--sku DSv3-Type1 --auto-replace false --tags "bar=baz" ', checks=[
                     self.check('name', '{host-name}'),
                     self.check('platformFaultDomain', 2),
                     self.check('sku.name', 'DSv3-Type1'),
                     self.check('autoReplaceOnFailure', False),
                     self.check('tags.bar', 'baz')
                 ])

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

        self.cmd('vm create -n {vm-name} --image debian -g {rg} --size Standard_D4s_v3 '
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
        self.cmd('vm create -g {rg2} -n vm1 --image centos --host {host_id} --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm create -g {rg2} -n vm2 --image centos --host-group {host-group} --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm show -g {rg2} -n vm1', checks=[
            self.check_pattern('host.id', '.*/{host-name}$')
        ])
        self.cmd('vm show -g {rg2} -n vm2', checks=[
            self.check_pattern('hostGroup.id', '.*/{host-group}$')
        ])
        self.cmd('vm delete --name vm1 -g {rg2} --yes')
        self.cmd('vm delete --name vm2 -g {rg2} --yes')
        self.cmd('vm host delete --name {host-name} --host-group {host-group} -g {rg2} --yes')
# endregion


class VMSSTerminateNotificationScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_terminate_notification_')
    def test_vmss_terminate_notification(self, resource_group):
        update_enable_key = 'virtualMachineProfile.scheduledEventsProfile.terminateNotificationProfile.enable'
        update_not_before_timeout_key = 'virtualMachineProfile.scheduledEventsProfile.terminateNotificationProfile.notBeforeTimeout'
        create_enable_key = 'vmss.' + update_enable_key
        create_not_before_timeout_key = 'vmss.' + update_not_before_timeout_key

        self.kwargs.update({
            'vmss1': 'vmss1',
            'vmss2': 'vmss2'
        })

        # Create, enable terminate notification
        self.cmd('vmss create -g {rg} -n {vmss1} --image UbuntuLTS --terminate-notification-time 5 --admin-username azureuser',
                 checks=[
                     self.check(create_enable_key, True),
                     self.check(create_not_before_timeout_key, 'PT5M')
                 ])

        # Update, enable terminate notification and set time
        self.cmd('vmss update -g {rg} -n {vmss1} --enable-terminate-notification --terminate-notification-time 8',
                 checks=[
                     self.check(update_enable_key, True),
                     self.check(update_not_before_timeout_key, 'PT8M')
                 ])

        # Update, set time
        self.cmd('vmss update -g {rg} -n {vmss1} --terminate-notification-time 9',
                 checks=[
                     self.check(update_not_before_timeout_key, 'PT9M')
                 ])

        # Update, disable terminate notification
        self.cmd('vmss update -g {rg} -n {vmss1} --enable-terminate-notification false',
                 checks=[
                     self.check('virtualMachineProfile.scheduledEventsProfile.terminateNotificationProfile', None)
                 ])

        # Parameter validation, the following commands should fail
        with self.assertRaises(CLIError):
            self.cmd('vmss update -g {rg} -n {vmss1} --enable-terminate-notification false --terminate-notification-time 5')
        with self.assertRaises(CLIError):
            self.cmd('vmss update -g {rg} -n {vmss1} --enable-terminate-notification')

        # Create vmss without terminate notification and enable it with vmss update
        self.cmd('vmss create -g {rg} -n {vmss2} --image UbuntuLTS --admin-username azureuser')
        self.cmd('vmss update -g {rg} -n {vmss2} --enable-terminate-notification true --terminate-notification-time 5',
                 checks=[
                     self.check(update_enable_key, True),
                     self.check(update_not_before_timeout_key, 'PT5M')
                 ])


class VMPriorityEvictionBillingTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_priority_eviction_billing_')
    def test_vm_priority_eviction_billing(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vmss': 'vmss1'
        })

        # vm create
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --priority Low --eviction-policy Deallocate --max-price 50 --admin-username azureuser --admin-password testPassword0 --authentication-type password')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('priority', 'Low'),
            self.check('evictionPolicy', 'Deallocate'),
            self.check('billingProfile.maxPrice', 50)
        ])

        # vmss create
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --lb-sku Standard --priority Low --eviction-policy Deallocate --max-price 50 --admin-username azureuser --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.priority', 'Low'),
            self.check('vmss.virtualMachineProfile.evictionPolicy', 'Deallocate'),
            self.check('vmss.virtualMachineProfile.billingProfile.maxPrice', 50)
        ])

        # vm update
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm update -g {rg} -n {vm} --priority Spot --max-price 100', checks=[
            self.check('priority', 'Spot'),
            self.check('billingProfile.maxPrice', 100)
        ])

        # vmss update
        self.cmd('vmss deallocate -g {rg} -n {vmss}')
        self.cmd('vmss update -g {rg} -n {vmss} --priority Spot --max-price 100', checks=[
            self.check('virtualMachineProfile.priority', 'Spot'),
            self.check('virtualMachineProfile.billingProfile.maxPrice', 100)
        ])


class VMCreateSpecialName(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_special_name_')
    def test_vm_create_special_name(self, resource_group):
        """
        Compose a valid computer name from VM name if computer name is not provided.
        Remove special characters: '`~!@#$%^&*()=+_[]{}\\|;:\'\",<>/?'
        """
        self.kwargs.update({
            'vm': 'vm_1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('name', '{vm}'),
            self.check('osProfile.computerName', 'vm1')
        ])


class VMImageTermsTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_image_terms_')
    def test_vm_image_terms(self, resource_group):
        """
        Test `accept`, `cancel`, `show` in `az vm image terms`
        """
        self.kwargs.update({
            'publisher': 'fortinet',
            'offer': 'fortinet_fortigate-vm_v5',
            'plan': 'fortinet_fg-vm_payg',
            'urn': 'fortinet:fortinet_fortigate-vm_v5:fortinet_fg-vm_payg:5.6.5'
        })
        self.cmd('vm image terms accept --urn {urn}', checks=[
            self.check('accepted', True)
        ])
        self.cmd('vm image terms show --urn {urn}', checks=[
            self.check('accepted', True)
        ])
        self.cmd('vm image terms cancel --urn {urn}', checks=[
            self.check('accepted', False)
        ])
        self.cmd('vm image terms show --urn {urn}', checks=[
            self.check('accepted', False)
        ])
        self.cmd('vm image terms accept --publisher {publisher} --offer {offer} --plan {plan}', checks=[
            self.check('accepted', True)
        ])
        self.cmd('vm image terms show --publisher {publisher} --offer {offer} --plan {plan}', checks=[
            self.check('accepted', True)
        ])
        self.cmd('vm image terms cancel --publisher {publisher} --offer {offer} --plan {plan}', checks=[
            self.check('accepted', False)
        ])
        self.cmd('vm image terms show --publisher {publisher} --offer {offer} --plan {plan}', checks=[
            self.check('accepted', False)
        ])


class DiskEncryptionSetTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_', location='westcentralus')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set(self, resource_group):
        self.kwargs.update({
            'vault': self.create_random_name(prefix='vault-', length=20),
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'des2': self.create_random_name(prefix='des2-', length=20),
            'des3': self.create_random_name(prefix='des3-', length=20),
            'disk': self.create_random_name(prefix='disk-', length=20),
            'vm1': self.create_random_name(prefix='vm1-', length=20),
            'vm2': self.create_random_name(prefix='vm2-', length=20),
            'vmss': self.create_random_name(prefix='vmss-', length=20),
        })

        vault_id = self.cmd('keyvault create -g {rg} -n {vault} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('keyvault set-policy -n {vault} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('keyvault set-policy -n {vault} --object-id {des3_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')
            self.cmd('role assignment create --assignee {des2_sp_id} --role Reader --scope {vault_id}')
            self.cmd('role assignment create --assignee {des3_sp_id} --role Reader --scope {vault_id}')

        time.sleep(15)

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

        self.cmd('vm create -g {rg} -n {vm2} --image centos --os-disk-encryption-set {des1} --data-disk-sizes-gb 10 10 --data-disk-encryption-sets {des2} {des3} --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check_pattern('storageProfile.osDisk.managedDisk.diskEncryptionSet.id', self.kwargs['des1_pattern']),
            self.check_pattern('storageProfile.dataDisks[0].managedDisk.diskEncryptionSet.id', self.kwargs['des2_pattern']),
            self.check_pattern('storageProfile.dataDisks[1].managedDisk.diskEncryptionSet.id', self.kwargs['des3_pattern'])
        ])

        self.cmd('vmss create -g {rg} -n {vmss} --image centos --os-disk-encryption-set {des1} --data-disk-sizes-gb 10 10 --data-disk-encryption-sets {des2} {des3} --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check_pattern('virtualMachineProfile.storageProfile.osDisk.managedDisk.diskEncryptionSet.id', self.kwargs['des1_pattern']),
            self.check_pattern('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.diskEncryptionSet.id', self.kwargs['des2_pattern']),
            self.check_pattern('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.diskEncryptionSet.id', self.kwargs['des3_pattern'])
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_update_', location='westcentralus')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_update(self, resource_group):

        self.kwargs.update({
            'vault1': self.create_random_name(prefix='vault1-', length=20),
            'key1': self.create_random_name(prefix='key1-', length=20),
            'vault2': self.create_random_name(prefix='vault2-', length=20),
            'key2': self.create_random_name(prefix='key2-', length=20),
            'des': self.create_random_name(prefix='des-', length=20)
        })

        vault1_id = self.cmd('keyvault create -g {rg} -n {vault1} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
        kid1 = self.cmd('keyvault key create -n {key1} --vault {vault1} --protection software').get_output_in_json()['key']['kid']
        vault2_id = self.cmd('keyvault create -g {rg} -n {vault2} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
        kid2 = self.cmd('keyvault key create -n {key2} --vault {vault2} --protection software').get_output_in_json()['key']['kid']

        self.kwargs.update({
            'vault1_id': vault1_id,
            'kid1': kid1,
            'vault2_id': vault2_id,
            'kid2': kid2
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des} --key-url {kid1} --source-vault {vault1}')
        des_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des}').get_output_in_json()
        des_sp_id = des_show_output['identity']['principalId']
        des_id = des_show_output['id']
        self.kwargs.update({
            'des_sp_id': des_sp_id,
            'des_id': des_id
        })

        self.cmd('keyvault set-policy -n {vault2} --object-id {des_sp_id} --key-permissions wrapKey unwrapKey get')
        time.sleep(15)
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des_sp_id} --role Reader --scope {vault2_id}')
        time.sleep(15)

        self.cmd('disk-encryption-set update -g {rg} -n {des} --key-url {kid2} --source-vault {vault2}', checks=[
            self.check('activeKey.keyUrl', '{kid2}'),
            self.check('activeKey.sourceVault.id', '{vault2_id}'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_disk_update_', location='westcentralus')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_disk_update(self, resource_group):
        self.kwargs.update({
            'vault': self.create_random_name(prefix='vault3-', length=20),
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'disk': self.create_random_name(prefix='disk-', length=20),
        })

        vault_id = self.cmd('keyvault create -g {rg} -n {vault} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')

        time.sleep(15)

        self.kwargs.update({
            'des1_pattern': '.*/{}$'.format(self.kwargs['des1'])
        })

        self.cmd('disk create -g {rg} -n {disk} --size-gb 10')
        self.cmd('disk update -g {rg} -n {disk} --disk-encryption-set {des1} --encryption-type EncryptionAtRestWithCustomerKey', checks=[
            self.check_pattern('encryption.diskEncryptionSetId', self.kwargs['des1_pattern']),
            self.check('encryption.type', 'EncryptionAtRestWithCustomerKey')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_snapshot_', location='westcentralus')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_snapshot(self, resource_group):
        self.kwargs.update({
            'vault': self.create_random_name(prefix='vault4-', length=20),
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'des2': self.create_random_name(prefix='des2-', length=20),
            'snapshot1': self.create_random_name(prefix='snapshot1-', length=20),
            'snapshot2': self.create_random_name(prefix='snapshot2-', length=20),
        })

        vault_id = self.cmd('keyvault create -g {rg} -n {vault} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('keyvault set-policy -n {vault} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')
            self.cmd('role assignment create --assignee {des2_sp_id} --role Reader --scope {vault_id}')

        time.sleep(15)

        self.kwargs.update({
            'des1_pattern': '.*/{}$'.format(self.kwargs['des1']),
            'des2_pattern': '.*/{}$'.format(self.kwargs['des2'])
        })

        self.cmd('snapshot create -g {rg} -n {snapshot1} --encryption-type EncryptionAtRestWithCustomerKey --disk-encryption-set {des1} --size-gb 10', checks=[
            self.check_pattern('encryption.diskEncryptionSetId', self.kwargs['des1_pattern']),
            self.check('encryption.type', 'EncryptionAtRestWithCustomerKey')
        ])

        self.cmd('snapshot create -g {rg} -n {snapshot2} --size-gb 10')

        self.cmd('snapshot update -g {rg} -n {snapshot2} --encryption-type EncryptionAtRestWithCustomerKey --disk-encryption-set {des2}', checks=[
            self.check_pattern('encryption.diskEncryptionSetId', self.kwargs['des2_pattern'])
        ])

    @unittest.skip('disable temporarily, will fix in another PR')
    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_double_encryption_', location='centraluseuap')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_double_encryption(self, resource_group):
        self.kwargs.update({
            'vault': self.create_random_name(prefix='vault-', length=20),
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'disk1': self.create_random_name(prefix='disk-', length=20),
            'vm1': self.create_random_name(prefix='vm1-', length=20),
            'vmss1': self.create_random_name(prefix='vmss-', length=20)
        })

        vault_id = self.cmd('keyvault create -g {rg} -n {vault} --enable-purge-protection true --enable-soft-delete true').get_output_in_json()['id']
        kid = self.cmd('keyvault key create -n {key} --vault {vault} --protection software').get_output_in_json()['key']['kid']
        self.kwargs.update({
            'vault_id': vault_id,
            'kid': kid
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des1} --key-url {kid} --source-vault {vault} --encryption-type EncryptionAtRestWithPlatformAndCustomerKeys')
        des1_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des1}').get_output_in_json()
        des1_sp_id = des1_show_output['identity']['principalId']
        des1_id = des1_show_output['id']
        self.kwargs.update({
            'des1_sp_id': des1_sp_id,
            'des1_id': des1_id
        })

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')

        self.cmd('disk create -g {rg} -n {disk1} --disk-encryption-set {des1} --size-gb 10', checks=[
            self.check('encryption.type', 'EncryptionAtRestWithPlatformAndCustomerKeys')
        ])

        self.cmd('vm create -g {rg} -n {vm1} --image centos --os-disk-encryption-set {des1} --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')

        self.cmd('vmss create -g {rg} -n {vmss1} --image centos --os-disk-encryption-set {des1} --admin-username azureuser --admin-password testPassword0 --authentication-type password')


class DiskAccessTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_access_', location='centraluseuap')
    def test_disk_access(self, resource_group):
        self.kwargs.update({
            'loc': 'centraluseuap',
            'diskaccess': 'mydiskaccess',
            'disk': 'mydisk',
            'snapshot': 'mysnapshot'
        })

        self.cmd('disk-access create -g {rg} -l {loc} -n {diskaccess}')
        self.cmd('disk-access list -g {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].name', '{diskaccess}'),
            self.check('[0].location', '{loc}')
        ])

        self.cmd('disk-access update -g {rg} -n {diskaccess} --tags tag1=val1')
        disk_access_output = self.cmd('disk-access show -g {rg} -n {diskaccess}', checks=[
            self.check('name', '{diskaccess}'),
            self.check('location', '{loc}'),
            self.check('tags.tag1', 'val1')
        ]).get_output_in_json()
        disk_access_id = disk_access_output['id']

        self.cmd('disk create -g {rg} -n {disk} --size-gb 10 --network-access-policy AllowPrivate --disk-access {diskaccess}')
        self.cmd('disk show -g {rg} -n {disk}', checks=[
            self.check('name', '{disk}'),
            self.check('diskAccessId', disk_access_id),
            self.check('networkAccessPolicy', 'AllowPrivate')
        ])

        self.cmd('snapshot create -g {rg} -n {snapshot} --size-gb 10 --network-access-policy AllowPrivate --disk-access {diskaccess}')
        self.cmd('snapshot show -g {rg} -n {snapshot}', checks=[
            self.check('name', '{snapshot}'),
            self.check('diskAccessId', disk_access_id),
            self.check('networkAccessPolicy', 'AllowPrivate')
        ])

        self.cmd('disk delete -g {rg} -n {disk} --yes')
        self.cmd('snapshot delete -g {rg} -n {snapshot}')
        self.cmd('disk-access delete -g {rg} -n {diskaccess}')
        self.cmd('disk-access list -g {rg}', checks=[
            self.check('length(@)', 0)
        ])


class VMSSCreateDiskOptionTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_disk_iops_mbps_', location='eastus')
    @AllowLargeResponse(size_kb=99999)
    def test_vmss_create_disk_iops_mbps(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image debian --data-disk-sizes-gb 10 10 --data-disk-iops 555 666 '
                 '--data-disk-mbps 77 88 --ultra-ssd-enabled --zone 1 --vm-sku Standard_D2s_v3 '
                 '--storage-sku UltraSSD_LRS --location eastus --admin-username azureuser',
                 checks=[
                     self.check('vmss.virtualMachineProfile.storageProfile.dataDisks[0].diskIOPSReadWrite', '555'),
                     self.check('vmss.virtualMachineProfile.storageProfile.dataDisks[1].diskIOPSReadWrite', '666'),
                     self.check('vmss.virtualMachineProfile.storageProfile.dataDisks[0].diskMBpsReadWrite', '77'),
                     self.check('vmss.virtualMachineProfile.storageProfile.dataDisks[1].diskMBpsReadWrite', '88')
                 ])

        self.cmd('vmss update -g {rg} -n {vmss} --set '
                 'virtualMachineProfile.storageProfile.dataDisks[0].diskIOPSReadWrite=444 '
                 'virtualMachineProfile.storageProfile.dataDisks[1].diskIOPSReadWrite=555 '
                 'virtualMachineProfile.storageProfile.dataDisks[0].diskMBpsReadWrite=66 '
                 'virtualMachineProfile.storageProfile.dataDisks[1].diskMBpsReadWrite=77 ',
                 checks=[
                     self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskIopsReadWrite', '444'),
                     self.check('virtualMachineProfile.storageProfile.dataDisks[1].diskIopsReadWrite', '555'),
                     self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskMbpsReadWrite', '66'),
                     self.check('virtualMachineProfile.storageProfile.dataDisks[1].diskMbpsReadWrite', '77'),
                 ])


class VMCreateAutoCreateSubnetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_subnet')
    def test_vm_create_auto_create_subnet(self, resource_group):

        self.kwargs.update({
            'loc': 'eastus',
            'vm': 'vm-subnet',
            'vnet': 'myvnet'
        })

        # Expecting no results
        self.cmd('vm list --resource-group {rg}',
                 checks=self.is_empty())
        self.cmd('network vnet list --resource-group {rg}',
                 checks=self.is_empty())

        self.cmd('network vnet create --resource-group {rg} --name {vnet} --location {loc}')
        self.cmd('vm create --resource-group {rg} --location {loc} --name {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --vnet-name {vnet}')

        # Expecting one result, the one we created
        self.cmd('vm list --resource-group {rg}', checks=[
            self.check('length(@)', 1),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].name', '{vm}'),
            self.check('[0].location', '{loc}')
        ])

        self.cmd('network vnet show --resource-group {rg} --name {vnet}', checks=[
            self.check('subnets[0].name', '{vm}Subnet')
        ])


class VMSSAutomaticRepairsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_automatic_repairs_with_health_probe_')
    def test_vmss_create_automatic_repairs_with_health_probe(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'lb': 'lb1',
            'probe': 'probe',
            'lbrule': 'lbrule'
        })

        # Test raise error if not provide health probe or load balance
        with self.assertRaises(CLIError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --automatic-repairs-grace-period 30 --admin-username azureuser')
        with self.assertRaises(CLIError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --load-balancer {lb} --automatic-repairs-grace-period 30 --admin-username azureuser')
        with self.assertRaises(CLIError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --health-probe {probe} --automatic-repairs-grace-period 30 --admin-username azureuser')

        # Prepare health probe
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n {probe} --protocol Tcp --port 80')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n {lbrule} --probe-name {probe} --protocol Tcp --frontend-port 80 --backend-port 80')
        # Test enable automatic repairs with a health probe when create vmss
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --load-balancer {lb} --health-probe {probe} --automatic-repairs-grace-period 30 --admin-username azureuser',
                 checks=[
                     self.check('vmss.automaticRepairsPolicy.enabled', True),
                     self.check('vmss.automaticRepairsPolicy.gracePeriod', 'PT30M')
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_automatic_repairs_with_health_probe_')
    def test_vmss_update_automatic_repairs_with_health_probe(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'probe': 'probe',
            'lbrule': 'lbrule'
        })

        # Prepare vmss
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username azureuser')

        # Validate automatic repairs parameters
        with self.assertRaises(CLIError):
            self.cmd(
                'vmss update -g {rg} -n {vmss} --enable-automatic-repairs false --automatic-repairs-grace-period 30')
        with self.assertRaises(CLIError):
            self.cmd('vmss update -g {rg} -n {vmss} --enable-automatic-repairs true')

        # Prepare health probe
        self.kwargs['probe_id'] = self.cmd(
            'network lb probe create -g {rg} --lb-name {vmss}LB -n {probe} --protocol Tcp --port 80'
        ).get_output_in_json()['id']
        self.cmd(
            'network lb rule create -g {rg} --lb-name {vmss}LB -n {lbrule} --probe-name {probe} --protocol Tcp '
            '--frontend-port 80 --backend-port 80'
        )
        # Test enable automatic repairs with a health probe when update vmss
        self.cmd('vmss update -g {rg} -n {vmss} --set virtualMachineProfile.networkProfile.healthProbe.id={probe_id}',
                 checks=[
                     self.check('virtualMachineProfile.networkProfile.healthProbe.id', self.kwargs['probe_id'])
                 ])
        self.kwargs['instance_ids'] = ' '.join(
            self.cmd('vmss list-instances -g {rg} -n {vmss} --query "[].instanceId"').get_output_in_json()
        )
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids {instance_ids}')
        self.cmd('vmss update -g {rg} -n {vmss} --enable-automatic-repairs true --automatic-repairs-grace-period 30',
                 checks=[
                     self.check('automaticRepairsPolicy.enabled', True),
                     self.check('automaticRepairsPolicy.gracePeriod', 'PT30M')
                 ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_automatic_repairs_with_health_extension_')
    def test_vmss_update_automatic_repairs_with_health_extension(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        # Prepare vmss
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --admin-username azureuser')

        # Prepare health extension
        _, settings_file = tempfile.mkstemp()
        with open(settings_file, 'w') as outfile:
            json.dump({
                "port": 80,
                "protocol": "http",
                "requestPath": "/"
            }, outfile)
        settings_file = settings_file.replace('\\', '\\\\')
        self.kwargs['settings'] = settings_file
        self.cmd(
            'vmss extension set -g {rg} --vmss-name {vmss} '
            '--name ApplicationHealthLinux --version 1.0 '
            '--publisher Microsoft.ManagedServices '
            '--settings {settings}'
        )

        # Test enable automatic repairs with a health extension when update vmss
        self.kwargs['instance_ids'] = ' '.join(
            self.cmd('vmss list-instances -g {rg} -n {vmss} --query "[].instanceId"').get_output_in_json()
        )
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids {instance_ids}')
        self.cmd('vmss update -g {rg} -n {vmss} --enable-automatic-repairs true --automatic-repairs-grace-period 30',
                 checks=[
                     self.check('automaticRepairsPolicy.enabled', True),
                     self.check('automaticRepairsPolicy.gracePeriod', 'PT30M')
                 ])


class VMCreateNSGRule(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_nsg_rule_')
    def test_vm_create_nsg_rule(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image centos --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('network nsg show -g {rg} -n {vm}NSG', checks=[
            self.check('securityRules', '[]')
        ])


class VMSSSetOrchestrationServiceStateScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_set_orchestration_service_state_')
    def test_vmss_set_orchestration_service_state(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'lb': 'lb1',
            'probe': 'probe',
            'lbrule': 'lbrule',
            'service_name': 'AutomaticRepairs'
        })

        # Prepare health probe
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n {probe} --protocol Tcp --port 80')
        self.cmd(
            'network lb rule create -g {rg} --lb-name {lb} -n {lbrule} --probe-name {probe} --protocol Tcp --frontend-port 80 --backend-port 80')
        self.cmd(
            'vmss create -g {rg} -n {vmss} --image UbuntuLTS --load-balancer {lb} --health-probe {probe} --automatic-repairs-grace-period 30 --admin-username azureuser',
            checks=[
                self.check('vmss.automaticRepairsPolicy.enabled', True),
                self.check('vmss.automaticRepairsPolicy.gracePeriod', 'PT30M')
            ])
        self.cmd('vmss set-orchestration-service-state -g {rg} -n {vmss} --service-name {service_name} --action Resume')
        self.cmd('vmss set-orchestration-service-state -g {rg} -n {vmss} --service-name {service_name} --action Suspend')
        self.cmd('vmss get-instance-view -g {rg} -n {vmss}', checks=[
            self.check('orchestrationServices[0].serviceName', self.kwargs['service_name']),
            self.check('orchestrationServices[0].serviceState', 'Suspended')
        ])


class VMAutoShutdownScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_auto_shutdown')
    def test_vm_auto_shutdown(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image centos --nsg-rule NONE --admin-username azureuser --admin-password testPassword0 --authentication-type password')
        self.cmd('vm auto-shutdown -g {rg} -n {vm} --time 1730 --email "foo@bar.com" --webhook "https://example.com/"', checks=[
            self.check('name', 'shutdown-computevm-{vm}'),
            self.check('taskType', 'ComputeVmShutdownTask'),
            self.check('status', 'Enabled'),
            self.check('dailyRecurrence.time', '1730'),
            self.check('notificationSettings.status', 'Enabled'),
            self.check('notificationSettings.webhookUrl', 'https://example.com/'),
            self.check('notificationSettings.emailRecipient', 'foo@bar.com')
        ])
        self.cmd('vm auto-shutdown -g {rg} -n {vm} --off')


class VMSSOrchestrationModeScenarioTest(ScenarioTest):

    @unittest.skip('not whitelist yet')
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_orchestration_mode_', location='centraluseuap')
    def test_vmss_orchestration_mode(self, resource_group):
        self.kwargs.update({
            'ppg': 'ppg1',
            'vmss': 'vmss1'
        })

        self.cmd('ppg create -g {rg} -n {ppg}')
        self.cmd('vmss create -g {rg} -n {vmss} --orchestration-mode VM --single-placement-group false --ppg {ppg} '
                 '--platform-fault-domain-count 3 --generate-ssh-keys')


class VMCrossTenantUpdateScenarioTest(ScenarioTest):

    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_vm_cross_tenant_', location='westus2')
    def test_vm_cross_tenant_update(self, resource_group):
        self.kwargs.update({
            'location': 'westus2',
            'another_rg': self.create_random_name('cli_test_vm_cross_tenant_', 40),
            'another_vm': self.create_random_name('cli_test_vm_cross_tenant_', 40),
            'image_name': self.create_random_name('cli_test_vm_cross_tenant_', 40),
            'aux_sub': '1c638cf4-608f-4ee6-b680-c329e824c3a8',
            'aux_tenant': '72f988bf-86f1-41af-91ab-2d7cd011db47',
            'vm': self.create_random_name('cli_test_vm_cross_tenant_', 40)
        })

        # Prepare sig in another tenant
        self.cmd('group create -g {another_rg} --location {location} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['another_rg']))
        self.cmd(
            'vm create -g {another_rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {another_rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)
        self.cmd('vm deallocate -g {another_rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {another_rg} -n {vm} --subscription {aux_sub}')
        res = self.cmd(
            'image create -g {another_rg} -n {image_name} --source {vm} --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'image_id': res['id']
        })

        self.cmd(
            'vm create -g {rg} -n {vm} --image {image_id} --admin-username clitest1 --generate-ssh-key --nsg-rule NONE')
        self.cmd('vm update -g {rg} -n {vm} --set tags.tagName=tagValue', checks=[
            self.check('tags.tagName', 'tagValue')
        ])

        self.cmd('group delete -n {another_rg} -y --subscription {aux_sub}')


class VMAutoUpdateScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_auto_update_')
    def test_vm_auto_update(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image Win2019Datacenter --enable-agent --enable-auto-update --patch-mode AutomaticByOS --admin-username azureuser --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('osProfile.windowsConfiguration.enableAutomaticUpdates', True),
            self.check('osProfile.windowsConfiguration.patchSettings.patchMode', 'AutomaticByOS')
        ])
        self.cmd('vm assess-patches -g {rg} -n {vm}', checks=[
            self.check('status', 'Succeeded')
        ])


if __name__ == '__main__':
    unittest.main()
