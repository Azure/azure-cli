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

import six

from knack.util import CLIError

from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint, StorageAccountPreparer)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"


def _write_config_file(user_name):
    from datetime import datetime

    public_key = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8InHIPLAu6lMc0d+5voyXqigZfT5r6fAM1+FQAi+mkPDdk2hNq1BG0Bwfc88G'
                  'm7BImw8TS+x2bnZmhCbVnHd6BPCDY7a+cHCSqrQMW89Cv6Vl4ueGOeAWHpJTV9CTLVz4IY1x4HBdkLI2lKIHri9+z7NIdvFk7iOk'
                  'MVGyez5H1xDbF2szURxgc4I2/o5wycSwX+G8DrtsBvWLmFv9YAPx+VkEHQDjR0WWezOjuo1rDn6MQfiKfqAjPuInwNOg5AIxXAOR'
                  'esrin2PUlArNtdDH1zlvI4RZi36+tJO7mtm3dJiKs4Sj7G6b1CjIU6aaj27MmKy3arIFChYav9yYM3IT')
    config_file_name = 'private_config_{}.json'.format(datetime.utcnow().strftime('%H%M%S%f'))
    config = {
        'username': user_name,
        'ssh_key': public_key
    }
    config_file = os.path.join(TEST_DIR, config_file_name)
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

    def test_vm_images_list_thru_services(self):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 4096

        result = self.cmd('vm image list -l westus --publisher Canonical --offer Ubuntu_Snappy_Core -o tsv --all').output
        assert result.index('15.04') >= 0

        result = self.cmd('vm image list -p Canonical -f Ubuntu_Snappy_Core -o tsv --all').output
        assert result.index('15.04') >= 0


class VMOpenPortTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_open_port')
    def test_vm_open_port(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -l westus -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password PasswordPassword1! --public-ip-address-allocation dynamic --authentication-type password')

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
    def test_vm_show_list_sizes_list_ip_addresses(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-with-public-ip',
            'allocation': 'dynamic'
        })
        # Expecting no results at the beginning
        self.cmd('vm list-ip-addresses --resource-group {rg}', checks=self.is_empty())
        self.cmd('vm create --resource-group {rg} --location {loc} -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 --public-ip-address-allocation {allocation} --authentication-type password')
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
            self.check('type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)', 'string')
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

    def test_vm_image_list_publishers(self):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 4096

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

    def test_list_skus_contains_zone_info(self):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 2048
        # we pick eastus2 as it is one of 3 regions so far with zone support
        self.kwargs['loc'] = 'eastus2'
        result = self.cmd('vm list-skus -otable -l {loc} -otable')
        self.assertTrue(next(l for l in result.output.splitlines() if '1,2,3' in l).split()[-1] == '1,2,3')


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
            'loc': 'westus',
            'vm': 'vm-generalize'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk')
        self.cmd('vm stop -g {rg} -n {vm}')
        # Should be able to generalize the VM after it has been stopped
        self.cmd('vm generalize -g {rg} -n {vm}', checks=self.is_empty())
        vm = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        self.cmd('vm capture -g {rg} -n {vm} --vhd-name-prefix vmtest',
                 checks=self.is_empty())

        # capture to a custom image
        self.kwargs['image'] = 'myImage'
        self.cmd('image create -g {rg} -n {image} --source {vm}', checks=[
            self.check('name', '{image}'),
            self.check('sourceVirtualMachine.id', vm['id'])
        ])


class VMVMSSWindowsLicenseTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_windows_license_type')
    def test_windows_vm_vmss_license_type(self, resource_group):

        self.kwargs.update({
            'vm': 'winvm',
            'vmss': 'winvmss'
        })
        self.cmd('vm create -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('licenseType', 'Windows_Server')
        ])
        self.cmd('vmss create -g {rg} -n {vmss} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.licenseType', 'Windows_Server')
        ])


class VMCustomImageTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image')
    def test_custom_image(self, resource_group):
        # this test should be recorded using accounts "@azuresdkteam.onmicrosoft.com", as it uses pre-made generalized vms
        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'prepared_vm_unmanaged': '/subscriptions/{}/resourceGroups/sdk-test/providers/Microsoft.Compute/virtualMachines/sdk-test-um'.format(subscription_id),
            'prepared_vm': '/subscriptions/{}/resourceGroups/sdk-test/providers/Microsoft.Compute/virtualMachines/sdk-test-m'.format(subscription_id),
            'image': 'image1'  # for image captured from vm with unmanaged disk
        })

        self.cmd('image create -g {rg} -n {image} --source {prepared_vm_unmanaged}',
                 checks=self.check('name', '{image}'))
        self.cmd('vm create -g {rg} -n vm1 --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password',
                 checks=self.check('resourceGroup', resource_group))  # spot check ensuring the VM was created
        self.cmd('vm show -g {rg} -n vm1', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage')
        ])
        self.cmd('vmss create -g {rg} -n vmss1 --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage')
        ])

        self.kwargs['image'] = 'image2'  # for image captured from vm with managed os disk and data disk
        self.cmd('image create -g {rg} -n {image} --source {prepared_vm}',
                 checks=self.check('name', '{image}'))

        self.cmd('vm create -g {rg} -n vm2 --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password',
                 checks=self.check('resourceGroup', '{rg}'))  # spot check enusing the VM was created
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(storageProfile.dataDisks)", 1),
            self.check("storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS')
        ])

        self.cmd('vm create -g {rg} -n vm3 --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --storage-sku Premium_LRS')
        self.cmd('vm show -g {rg} -n vm3', checks=[
            self.check('storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(storageProfile.dataDisks)", 1),
            self.check("storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS')
        ])

        self.cmd('vmss create -g {rg} -n vmss2 --image {image} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password', checks=[
            self.check('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', '{rg}'),
            self.check('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check("length(vmss.virtualMachineProfile.storageProfile.dataDisks)", 1),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[0].createOption", 'FromImage'),
            self.check("vmss.virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType", 'Standard_LRS')
        ])


class VMImageWithPlanTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_custom_image_with_plan(self, resource_group):
        # this test should be recorded using accounts "@azuresdkteam.onmicrosoft.com", as it uses pre-made custom image
        subscription_id = self.get_subscription_id()
        self.kwargs.update({
            'prepared_image_with_plan_info': '/subscriptions/{}/resourceGroups/sdk-test/providers/Microsoft.Compute/images/custom-image-with-plan'.format(subscription_id),
            'plan': 'linuxdsvmubuntu'
        })

        self.cmd('vm create -g {rg} -n vm1 --admin-username cliuser --image {prepared_image_with_plan_info} --generate-ssh-keys --plan-publisher microsoft-ads --plan-name {plan} --plan-product linux-data-science-vm-ubuntu')
        self.cmd('vm show -g {rg} -n vm1',
                 checks=self.check('plan.name', '{plan}'))

    @ResourceGroupPreparer()
    def test_vm_create_with_market_place_image(self, resource_group, resource_group_location):
        self.kwargs.update({
            'location': resource_group_location,
            'publisher': 'kemptech',
            'offer': 'vlm-azure',
            'sku': 'basic-byol',
            'plan': 'basic-byol'
        })
        self.kwargs['urn'] = '{publisher}:{offer}:{sku}:7.2.362142710'.format(**self.kwargs)
        self.cmd('vm image show --urn {urn}', checks=self.check('plan.name', '{plan}'))
        self.cmd('vm image accept-terms -p {publisher} --offer {offer} --plan {plan}', checks=self.check('accepted', True))
        # repeat the same command using --urn
        self.cmd('vm image accept-terms --urn {urn}', checks=self.check('accepted', True))
        self.cmd('vm create -g {rg} -n vm1 --no-wait --image {urn}')


class VMCreateFromUnmanagedDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_from_unmanaged_disk')
    def test_vm_create_from_unmanaged_disk(self, resource_group):
        # create a vm with unmanaged os disk
        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password')
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
        self.cmd('disk create -g {rg} -n {os_disk} --source {os_disk_vhd_uri}',
                 checks=self.check('name', '{os_disk}'))
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
        self.cmd('vm create -g {rg} -n vm1 --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password')
        vm1_info = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()
        self.kwargs['disk_uri'] = vm1_info['storageProfile']['osDisk']['vhd']['uri']

        self.cmd('vm delete -g {rg} -n vm1 -y')

        # create a vm by attaching the OS disk from the deleted VM
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {disk_uri} --os-type linux --use-unmanaged-disk',
                 checks=self.check('powerState', 'VM running'))


class VMAttachDisksOnCreate(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_create_by_attach_os_and_data_disks(self, resource_group):
        # the testing below follow a real custom's workflow requiring the support of attaching data disks on create

        # creating a vm
        self.cmd('vm create -g {rg} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --data-disk-sizes-gb 2')
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
        self.cmd('vm create -g {rg} -n vm1 --use-unmanaged-disk --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password')
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


class VMOSDiskSize(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_os_disk_size')
    def test_set_os_disk_size(self, resource_group):
        # test unmanaged disk
        self.kwargs.update({'sa': self.create_random_name(prefix='cli', length=12)})
        self.cmd('vm create -g {rg} -n vm --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75 --use-unmanaged-disk --storage-account {sa}')
        result = self.cmd('storage blob list --account-name {sa} --container-name vhds').get_output_in_json()
        self.assertTrue(result[0]['properties']['contentLength'] > 75000000000)

        # test managed disk
        self.cmd('vm create -g {rg} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75')
        self.cmd('vm show -g {rg} -n vm1',
                 checks=self.check('storageProfile.osDisk.diskSizeGb', 75))


class VMManagedDiskScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_managed_disk')
    def test_managed_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'disk1': 'd1',
            'disk2': 'd2',
            'snapshot1': 's1',
            'snapshot2': 's2',
            'image': 'i1'
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
        self.cmd('vm deallocate --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/deallocated')
        self.cmd('vm resize -g {rg} -n {vm} --size Standard_DS2_v2',
                 checks=self.check('hardwareProfile.vmSize', 'Standard_DS2_v2'))
        self.cmd('vm delete --resource-group {rg} --name {vm} --yes')
        # Expecting no results
        self.cmd('vm list --resource-group {rg}', checks=self.is_empty())


class VMNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_no_wait')
    def test_vm_create_no_wait(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vmnowait2'
        })
        self.cmd('vm create -g {rg} -n {vm} --admin-username user12 --admin-password testPassword0 --authentication-type password --image UbuntuLTS --no-wait',
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
        self.cmd('vm availability-set list-sizes -g {rg} -n {availset}',
                 checks=self.check('type(@)', 'array'))
        self.cmd('vm availability-set show -g {rg} -n {availset}',
                 checks=[self.check('name', '{availset}')])
        self.cmd('vm availability-set delete -g {rg} -n {availset}')
        self.cmd('vm availability-set list -g {rg}',
                 checks=self.check('length(@)', 0))


# once https://github.com/Azure/azure-cli/issues/4127 is fixed, switch back to a regular ScenarioTest
class VMAvailSetLiveScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_availset_live')
    def test_vm_availset_convert(self, resource_group):

        self.kwargs.update({
            'availset': 'availset-test'
        })

        self.cmd('vm availability-set create -g {rg} -n {availset} --unmanaged --platform-fault-domain-count 3 -l westus2', checks=[
            self.check('name', '{availset}'),
            self.check('platformFaultDomainCount', 3),
            self.check('platformUpdateDomainCount', 5),  # server defaults to 5
            self.check('sku.name', 'Classic')
        ])

        # the conversion should auto adjust the FD from 3 to 2 as 'westus2' only offers 2
        self.cmd('vm availability-set convert -g {rg} -n {availset}', checks=[
            self.check('name', '{availset}'),
            self.check('platformFaultDomainCount', 2),
            self.check('sku.name', 'Aligned')
        ])


class ComputeListSkusScenarioTest(LiveScenarioTest):

    def test_list_compute_skus_table_output(self):
        result = self.cmd('vm list-skus -l westus -otable')
        lines = result.output.split('\n')
        # 1st line is header
        self.assertEqual(lines[0].split(), ['ResourceType', 'Locations', 'Name', 'Tier', 'Size', 'Capabilities'])
        # spot check the first 3 entries
        self.assertEqual(lines[3].split(), ['availabilitySets', 'westus', 'Classic', 'MaximumPlatformFaultDomainCount=3'])
        self.assertEqual(lines[4].split(), ['availabilitySets', 'westus', 'Aligned', 'MaximumPlatformFaultDomainCount=3'])
        self.assertEqual(lines[5].split(), ['virtualMachines', 'westus', 'Standard_DS1_v2', 'DS1_v2', 'Standard'])


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

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0')

        try:
            self.cmd('vm extension list --vm-name {vm} --resource-group {rg}',
                     checks=self.check('length([])', 0))
            self.cmd('vm extension set -n {ext} --publisher {pub} --version 1.2  --vm-name {vm} --resource-group {rg} --protected-settings "{config}"')
            self.cmd('vm get-instance-view -n {vm} -g {rg}', checks=[
                self.check('*.extensions[0].name', ['VMAccessForLinux']),
                self.check('*.extensions[0].typeHandlerVersion', ['1.4.7.1']),
            ])
            self.cmd('vm extension show --resource-group {rg} --vm-name {vm} --name {ext}', checks=[
                self.check('type(@)', 'object'),
                self.check('name', '{ext}'),
                self.check('resourceGroup', '{rg}')
            ])
            self.cmd('vm extension delete --resource-group {rg} --vm-name {vm} --name {ext}',
                     checks=[self.check('status', 'Succeeded')])
        finally:
            os.remove(config_file)


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


class VMExtensionImageSearchScenarioTest(ScenarioTest):

    def test_vm_extension_image_search(self):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 4096

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
        self.cmd('vm extension image list -l westus -p {pub} --name {image} --latest',
                 checks=self.check('length(@)', 1))


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
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.adminUsername', '{username}'),
            self.check('osProfile.computerName', '{vm}'),
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', '{ssh_key}'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
        ])

        # test for idempotency--no need to reverify, just ensure the command doesn't fail
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-sizes-gb 1')


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

        self.cmd('vm create -n {vm} -g {rg} --image Debian --availability-set {quotes} --nsg {quotes} --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --location {loc} --admin-username user11')

        self.cmd('vm show -n {vm} -g {rg}', checks=[
            self.check('availabilitySet', None),
            self.check('length(tags)', 0),
            self.check('location', '{loc}')
        ])
        self.cmd('network public-ip show -n {vm}PublicIP -g {rg}',
                 checks=self.is_empty())


class VMBootDiagnostics(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_diagnostics')
    @StorageAccountPreparer(name_prefix='clitestbootdiag')
    def test_vm_boot_diagnostics(self, resource_group, storage_account):

        self.kwargs.update({
            'vm': 'myvm'
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


class VMSSExtensionInstallTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_extension')
    def test_vmss_extension(self):

        username = 'myadmin'
        config_file = _write_config_file(username)

        self.kwargs.update({
            'vmss': 'vmss1',
            'pub': 'Microsoft.OSTCExtensions',
            'ext': 'VMAccessForLinux',
            'username': username,
            'config_file': config_file
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0')

        try:
            self.cmd('vmss extension set -n {ext} --publisher {pub} --version 1.4  --vmss-name {vmss} --resource-group {rg} --protected-settings "{config_file}"')
            self.cmd('vmss extension show --resource-group {rg} --vmss-name {vmss} --name {ext}', checks=[
                self.check('type(@)', 'object'),
                self.check('name', '{ext}')
            ])
        finally:
            os.remove(config_file)


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
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$ --use-unmanaged-disk')
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
            'dns': 'vrfmyvm00110011z',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.cmd('vm create -n {vm} -g {rg} --image openSUSE-Leap --admin-username user11 --private-ip-address 10.0.0.5 --public-ip-address-allocation static --public-ip-address-dns-name {dns} --ssh-key-value \'{ssh_key}\'')

        self.cmd('network public-ip show -n {vm}PublicIP -g {rg}', checks=[
            self.check('publicIpAllocationMethod', 'Static'),
            self.check('dnsSettings.domainNameLabel', '{dns}')
        ])
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].privateIpAllocationMethod', 'Static'))


class VMDiskAttachDetachTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli-test-disk')
    def test_vm_disk_attach_detach(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-diskattach-test',
            'disk1': 'd1',
            'disk2': 'd2'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username admin123 --image centos --admin-password testPassword0 --authentication-type password')

        self.cmd('vm disk attach -g {rg} --vm-name {vm} --disk {disk1} --new --size-gb 1 --caching ReadOnly')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --disk {disk2} --new --size-gb 2 --lun 2 --sku standard_lrs')
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
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk2}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 1),
            self.check('storageProfile.dataDisks[0].name', '{disk1}'),
        ])
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk1}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('length(storageProfile.dataDisks)', 0))
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --disk {disk1} --caching ReadWrite --sku standard_lrs')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
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

        self.cmd('vmss show --name {vmss} -g {rg}')

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

        self.cmd('vmss create --image Debian --admin-password testPassword0 -l westus -g {rg} -n {vmss} --disable-overprovision --instance-count {count} --os-disk-caching {caching} --upgrade-policy-mode {update} --authentication-type password --admin-username myadmin --public-ip-address {ip} --data-disk-sizes-gb 1 --vm-sku Standard_D2_v2')
        self.cmd('network lb show -g {rg} -n {vmss}lb ',
                 checks=self.check('frontendIpConfigurations[0].publicIpAddress.id.ends_with(@, \'{ip}\')', True))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('sku.capacity', '{count}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('upgradePolicy.mode', self.kwargs['update'].title()),
            self.check('singlePlacementGroup', True),
        ])
        self.kwargs['id'] = self.cmd('vmss list-instances -g {rg} -n {vmss} --query "[].instanceId"').get_output_in_json()[0]
        self.cmd('vmss show -g {rg} -n {vmss} --instance-id {id}',
                 checks=self.check('instanceId', '{id}'))

        self.cmd('vmss disk attach -g {rg} -n {vmss} --size-gb 3')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 2),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[1].diskSizeGb', 3),
            self.check('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Standard_LRS'),
        ])
        self.cmd('vmss disk detach -g {rg} -n {vmss} --lun 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].lun', 0),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1)
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
        self.cmd('network public-ip show -n {vmss}PublicIP -g {rg}',
                 checks=self.is_empty())

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

    @ResourceGroupPreparer()
    def test_vmss_create_default_app_gateway(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        res = self.cmd("vmss create -g {rg} --name {vmss} --validate --image UbuntuLTS --disable-overprovision --instance-count 101 --single-placement-group false --admin-username ubuntuadmin").get_output_in_json()
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


class VMSSCreateAcceleratedNetworkingTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_accelerated_networking')
    def test_vmss_accelerated_networking(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd("vmss create -n {vmss} -g {rg} --vm-sku Standard_DS4_v2 --image Win2016Datacenter --admin-username clittester --admin-password Test12345678!!! --accelerated-networking --instance-count 1")
        self.cmd('vmss show -n {vmss} -g {rg}',
                 checks=self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].enableAcceleratedNetworking', True))


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

        # TODO: Re-enable when issue #5155 is resolved.
        # message = 'Secret is missing vaultCertificates array or it is empty at index 0'
        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\'', expect_failure=True)

        vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')
        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm format-secret -s {secret_out}').get_output_in_json()
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

        # TODO: Re-enable when issue #5155 is resolved.
        # message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
        #           'vaultCertificate index 0'
        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets \'{secrets}\'', expect_failure=True)

        vault_out = self.cmd(
            'keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        self.kwargs['secrets'] = self.cmd('vm format-secret -s {secret_out} --certificate-store "My"').get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets "{secrets}"')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', self.kwargs['secret_out']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
        ])


class VMSSCreateLinuxSecretsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_linux_secrets')
    def test_vmss_create_linux_secrets(self, resource_group):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 2048

        self.kwargs.update({
            'loc': 'westus',
            'vmss': 'vmss1-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
            'vault': 'vmcreatelinuxsecret3334',
            'secret': 'mysecret',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm format-secret -s {secret_out}').get_output_in_json()
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
            'iid': 0
        })

        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        self.cmd('vmss nic list -g {rg} --vmss-name {vmss}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?resourceGroup == '{rg}']) == length(@)", True)
        ])
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

        # Fixing the role assignment guids so test can run under playback. The assignments will
        # be auto-deleted when the RG gets recycled, so the same ids can be reused.
        guids = [uuid.UUID('88DAAF5A-EA86-4A68-9D45-477538D41732'),
                 uuid.UUID('13ECC8E1-A3AA-40CE-95E9-1313957D6CF3')]
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=guids, autospec=True):
            # create a linux vm with default configuration
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope}', checks=[
                self.check('identity.role', 'Contributor'),
                self.check('identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
                self.check('identity.port', 50342)
            ])

            self.cmd('vm extension list -g {rg} --vm-name {vm1}', checks=[
                self.check('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
                self.check('[0].settings.port', 50342)
            ])

            # create a windows vm with reader role on the linux vm
            self.cmd('vm create -g {rg} -n {vm2} --image Win2016Datacenter --assign-identity --scope {vm1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1!', checks=[
                self.check('identity.role', 'reader'),
                self.check('identity.scope', '{vm1_id}'),
                self.check('identity.port', 50342)
            ])

            self.cmd('vm extension list -g {rg} --vm-name {vm2}', checks=[
                self.check('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForWindows'),
                self.check('[0].publisher', 'Microsoft.ManagedIdentity'),
                self.check('[0].settings.port', 50342)
            ])

            # create a linux vm w/o identity and later enable it
            vm3_result = self.cmd('vm create -g {rg} -n {vm3} --image debian --admin-username admin123 --admin-password PasswordPassword1!').get_output_in_json()
            self.assertIsNone(vm3_result.get('identity'))
            self.cmd('vm assign-identity -g {rg} -n {vm3} --scope {vm1_id} --role reader --port 50343', checks=[
                self.check('role', 'reader'),
                self.check('scope', '{vm1_id}'),
                self.check('port', 50343)
            ])

            self.cmd('vm extension list -g {rg} --vm-name {vm3}', checks=[
                self.check('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
                self.check('[0].publisher', 'Microsoft.ManagedIdentity'),
                self.check('[0].settings.port', 50343)
            ])

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
        # Fixing the role assignment guids so test can run under playback. The assignments will
        # be auto-deleted when the RG gets recycled, so the same ids can be reused.
        guids = [uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C138'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C137'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C136'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C135')]
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=guids, autospec=True):
            # create linux vm with default configuration
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope}', checks=[
                self.check('vmss.identity.role', 'Contributor'),
                self.check('vmss.identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
                self.check('vmss.identity.port', 50342)
            ])

            self.cmd('vmss extension list -g {rg} --vmss-name {vmss1}', checks=[
                self.check('[0].type', 'ManagedIdentityExtensionForLinux'),
                self.check('[0].publisher', 'Microsoft.ManagedIdentity'),
                self.check('[0].settings.port', 50342)
            ])

            # create a windows vm with reader role on the linux vm
            self.cmd('vmss create -g {rg} -n {vmss2} --image Win2016Datacenter --instance-count 1 --assign-identity --scope {vmss1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1!', checks=[
                self.check('vmss.identity.role', 'reader'),
                self.check('vmss.identity.scope', '{vmss1_id}'),
                self.check('vmss.identity.port', 50342)
            ])
            self.cmd('vmss extension list -g {rg} --vmss-name {vmss2}', checks=[
                self.check('[0].type', 'ManagedIdentityExtensionForWindows'),
                self.check('[0].publisher', 'Microsoft.ManagedIdentity'),
                self.check('[0].settings.port', 50342)
            ])

            # create a linux vm w/o identity and later enable it
            vmss3_result = self.cmd('vmss create -g {rg} -n {vmss3} --image debian --instance-count 1 --admin-username admin123 --admin-password PasswordPassword1!').get_output_in_json()['vmss']
            self.assertIsNone(vmss3_result.get('identity'))

            # skip playing back till the test issue gets addressed https://github.com/Azure/azure-cli/issues/4016
            if self.is_live:
                self.cmd('vmss assign-identity -g {rg} -n {vmss3} --scope "{vmss1_id}" --role reader --port 50343', checks=[
                    self.check('role', 'reader'),
                    self.check('scope', '{vmss1_id}'),
                    self.check('port', 50343)
                ])

                self.cmd('vmss extension list -g {rg} --vmss-name {vmss3}', checks=[
                    self.check('[0].type', 'ManagedIdentityExtensionForLinux'),
                    self.check('[0].settings.port', 50343)
                ])

    @ResourceGroupPreparer(name_prefix='cli_test_msi_no_scope')
    def test_msi_no_scope(self, resource_group):

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
            self.check('identity.port', 50342)
        ])
        # the extension should still get provisioned
        self.cmd('vm extension list -g {rg} --vm-name {vm1}', checks=[
            self.check('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
            self.check('[0].settings.port', 50342)
        ])

        # create a vmss with identity but w/o a role assignment (--scope "")
        self.cmd('vmss create -g {rg} -n {vmss1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!', checks=[
            self.check('vmss.identity.scope', None),
            self.check('vmss.identity.port', 50342)
        ])

        # the extension should still get provisioned
        self.cmd('vmss extension list -g {rg} --vmss-name {vmss1}', checks=[
            self.check('[0].type', 'ManagedIdentityExtensionForLinux'),
            self.check('[0].settings.port', 50342)
        ])

        # create a vm w/o identity
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username admin123 --admin-password PasswordPassword1!')
        # assign identity but w/o a role assignment
        self.cmd('vm assign-identity -g {rg} -n {vm2}', checks=[
            self.check('scope', None),
            self.check('port', 50342)
        ])
        # the extension should still get provisioned
        self.cmd('vm extension list -g {rg} --vm-name {vm2}', checks=[
            self.check('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
            self.check('[0].settings.port', 50342)
        ])

        self.cmd('vmss create -g {rg} -n {vmss2} --image debian --admin-username admin123 --admin-password PasswordPassword1!')
        # skip playing back till the test issue gets addressed https://github.com/Azure/azure-cli/issues/4016
        if self.is_live:
            self.cmd('vmss assign-identity -g {rg} -n {vmss2}', checks=[
                self.check('scope', None),
                self.check('port', 50342)
            ])

            self.cmd('vmss extension list -g {rg} --vmss-name {vmss2}', checks=[
                self.check('[0].type', 'ManagedIdentityExtensionForLinux'),
                self.check('[0].settings.port', 50342)
            ])

    @ResourceGroupPreparer(random_name_length=20, location='westcentralus')
    def test_vm_explicit_msi(self, resource_group):

        self.kwargs.update({
            'emsi': 'id1',
            'emsi2': 'id2',
            'vm': 'vm1',
            'sub': self.get_subscription_id(),
            'scope': '/subscriptions/{}/resourceGroups/{}'.format(self.get_subscription_id(), resource_group)
        })

        # create a managed identity
        emsi_result = self.cmd('identity create -g {rg} -n {emsi}',
                               checks=self.check('name', '{emsi}')).get_output_in_json()
        emsi2_result = self.cmd('identity create -g {rg} -n {emsi2}').get_output_in_json()

        # create a vm with only user assigned identity
        result = self.cmd('vm create -g {rg} -n vm2 --image ubuntults --assign-identity {emsi} --generate-ssh-keys', checks=[
            self.check('identity.role', None),
            self.check('identity.scope', None),
            self.check('length(identity.userAssignedIdentities)', 1)
        ]).get_output_in_json()
        self.assertEqual(result['identity']['userAssignedIdentities'][0].lower(), emsi_result['id'].lower())

        # create a vm with system + user assigned identities
        result = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --assign-identity {emsi} [system] --role reader --scope {scope} --generate-ssh-keys --admin-username ubuntuadmin').get_output_in_json()
        self.assertEqual(result['identity']['userAssignedIdentities'][0].lower(), emsi_result['id'].lower())
        result = self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(identity.identityIds)', 1),
            self.check('identity.type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi_result['id'].lower())
        # assign a new managed identity
        self.cmd('vm assign-identity -g {rg} -n {vm} --identities {emsi2}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('length(identity.identityIds)', 2))
        # remove the 1st user assigned identity
        self.cmd('vm remove-identity -g {rg} -n {vm} --identities {emsi}')
        result = self.cmd('vm show -g {rg} -n {vm}',
                          checks=self.check('length(identity.identityIds)', 1)).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi2_result['id'].lower())

        # remove the 2nd
        self.cmd('vm remove-identity -g {rg} -n {vm} --identities {emsi2}')
        # verify the VM still has the system assigned identity
        result = self.cmd('vm show -g {rg} -n {vm}', checks=[
            # blocked by https://github.com/Azure/azure-cli/issues/5103
            # self.check('length(identity.identityIds)', 0)
            self.check('identity.type', 'SystemAssigned'),
        ])

    @ResourceGroupPreparer(random_name_length=20, location='westcentralus')
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
        self.assertEqual(result['vmss']['identity']['userAssignedIdentities'][0].lower(), emsi_result['id'].lower())

        result = self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('length(identity.identityIds)', 1),
            self.check('identity.type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi_result['id'].lower())

        # assign a new managed identity
        self.cmd('vmss assign-identity -g {rg} -n {vmss} --identities {emsi2}')
        self.cmd('vmss show -g {rg} -n {vmss}',
                 checks=self.check('length(identity.identityIds)', 2))

        # update instances
        self.cmd('vmss update-instances -g {rg} -n {vmss} --instance-ids *')

        # remove the 1st user assigned identity
        self.cmd('vmss remove-identity -g {rg} -n {vmss} --identities {emsi}')
        result = self.cmd('vmss show -g {rg} -n {vmss}',
                          checks=self.check('length(identity.identityIds)', 1)).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi2_result['id'].lower())

        # remove the 2nd
        self.cmd('vmss remove-identity -g {rg} -n {vmss} --identities {emsi2}')
        # verify the vmss still has the system assigned identity
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            # blocked by https://github.com/Azure/azure-cli/issues/5103
            # self.check('length(identity.identityIds)', 0)
            self.check('identity.type', 'SystemAssigned'),
        ])


class VMLiveScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_progress')
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging

        self.kwargs.update({'vm': 'vm123'})

        with force_progress_logging() as test_io:
            self.cmd('vm create -g {rg} -n {vm} --admin-username {vm} --admin-password PasswordPassword1! --image debian')

        content = test_io.getvalue()
        # check log has okay format
        lines = content.splitlines()
        for l in lines:
            self.assertTrue(l.split(':')[0] in ['Accepted', 'Succeeded'])
        # spot check we do have relevant messages coming out
        self.assertTrue('Succeeded: {vm}VMNic (Microsoft.Network/networkInterfaces)'.format(**self.kwargs) in lines)
        self.assertTrue('Succeeded: {vm} (Microsoft.Compute/virtualMachines)'.format(**self.kwargs) in lines)


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMZoneScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_zone', location='eastus2')
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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_zones', location='eastus2')
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
    def test_vmss_create_x_zones(self, resource_group, resource_group_location):

        self.kwargs.update({
            'zones': '1 2 3',
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --zones {zones}')
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

    @ResourceGroupPreparer(name_prefix='cli_test_disk_zones', location='eastus2')
    def test_disk_create_zones(self, resource_group, resource_group_location):

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
    def test_run_command_e2e(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vm': 'test-run-command-vm',
            'loc': resource_group_location
        })

        self.cmd('vm run-command list -l {loc}')
        self.cmd('vm run-command show --command-id RunShellScript -l {loc}')
        public_ip = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --admin-password Test12345678!!').get_output_in_json()['publicIpAddress']

        self.cmd('vm open-port -g {rg} -n {vm} --port 80')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx!' in str(r.content))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command_w_params')
    def test_run_command_with_parameters(self, resource_group):
        self.kwargs.update({'vm': 'test-run-command-vm2'})
        self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username clitest1 --admin-password Test12345678!!')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world')


# TOOD: FAIL no KeyVault commands!
@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMSSDiskEncryptionTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_encryption', location='eastus2euap')  # the feature is only available in canary, should rollout to public soon
    def test_vmss_disk_encryption_e2e(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vault': self.create_random_name('vault', 10),
            'vmss': 'vmss1'
        })
        self.cmd('keyvault create -g {rg} -n {vault} --enabled-for-disk-encryption "true"')
        self.cmd('vmss create -g {rg} -n {vmss} --image win2016datacenter --instance-count 1 --admin-username clitester1 --admin-password Test123456789!')
        self.cmd('vmss encryption enable -g {rg} -n {vmss} --disk-encryption-keyvault {vault}')
        self.cmd('vmss update-instances -g {rg} -n {vmss}  --instance-ids "*"')
        self.cmd('vmss encryption show -g {rg} -n {vmss}',
                 checks=self.check('[0].disks[0].statuses[0].code', 'EncryptionState/encrypted'))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'EnableEncryption'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
        ])
        self.cmd('vmss encryption disable -g {rg} -n {vmss}')
        self.cmd('vmss update-instances -g {rg} -n {vmss}  --instance-ids "*"')
        self.cmd('vmss encryption show -g {rg} -n {vmss}',
                 checks=self.check('[0].disks[0].statuses[0].code', 'EncryptionState/notEncrypted'))
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'DisableEncryption'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
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
                "commandToExecute": "sudo apt-get install -y nginx",
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
        self.assertTrue('Welcome to nginx!' in str(r.content))

        # do some rolling upgrade, maybe nonsense, but we need to test the command anyway
        self.cmd('vmss rolling-upgrade start -g {rg} -n {vmss}')
        result = self.cmd('vmss rolling-upgrade get-latest -g {rg} -n {vmss}').get_output_in_json()
        self.assertTrue(('policy' in result) and ('progress' in result))  # spot check that it is about rolling upgrade

        # 'cancel' should fail as we have no active upgrade to cancel
        self.cmd('vmss rolling-upgrade cancel -g {rg} -n {vmss}', expect_failure=True)


class VMSSPriorityTesting(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='vmss_low_pri', location='CentralUSEUAP')
    def test_vmss_create_with_low_priority(self, resource_group, resource_group_location):
        self.kwargs.update({
            'priority': 'Low',
            'vmss': 'vmss123'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username clitester --admin-password PasswordPassword1! --image debian --priority {priority}')
        self.cmd('vmss show -g {rg} -n {vmss}',
                 checks=self.check('virtualMachineProfile.priority', '{priority}'))


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
        self.cmd('vm run-command invoke -g {rg} -n {vm1} --command-id RunShellScript --scripts "sudo apt-get install -y nginx"')
        self.cmd('vm run-command invoke -g {rg} -n {vm2} --command-id RunShellScript --scripts "sudo apt-get install -y nginx"')

        # ensure all pieces are working together
        result = self.cmd('network public-ip show -g {rg} -n PublicIP{lb}').get_output_in_json()
        pip = result['ipAddress']
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + pip)
        self.assertTrue('Welcome to nginx!' in str(r.content))


class VMCreateWithExistingNic(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_create_vm_existing_nic')
    def test_vm_create_existing_nic(self, resource_group):
        import re
        self.cmd('network public-ip create -g {rg} -n my-pip')
        self.cmd('network vnet create -g {rg} -n my-vnet --subnet-name my-subnet1')
        self.cmd('network nic create -g {rg} -n my-nic --subnet my-subnet1 --vnet-name my-vnet --public-ip-address my-pip')
        self.cmd('network nic ip-config create -n my-ipconfig2 -g {rg} --nic-name my-nic --private-ip-address-version IPv6')
        self.cmd('vm create -g {rg} -n vm1 --image ubuntults --nics my-nic --generate-ssh-keys --admin-username ubuntuadmin')
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
        self.cmd('vm create -g {rg} -n {vm} --image centos')
        res = self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        original_disk_id = res['storageProfile']['osDisk']['managedDisk']['id']
        backup_disk_id = self.cmd('disk create -g {{rg}} -n {{backupDisk}} --source {}'.format(original_disk_id)).get_output_in_json()['id']

        self.cmd('vm stop -g {rg} -n {vm}')
        self.cmd('vm update -g {{rg}} -n {{vm}} --os-disk {}'.format(backup_disk_id))
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.osDisk.managedDisk.id', backup_disk_id),
            self.check('storageProfile.osDisk.name', self.kwargs['backupDisk'])
        ])
        pass
# endregion


if __name__ == '__main__':
    unittest.main()
