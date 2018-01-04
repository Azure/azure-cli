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
from azure.cli.core.profiles import ResourceType
from azure.cli.core.util import CLIError
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk.vcr_test_base import (VCRTestBase,
                                             ResourceGroupVCRTestBase,
                                             JMESPathCheck,
                                             NoneCheck, MOCKED_SUBSCRIPTION_ID)
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint
from azure.cli.testsdk import JMESPathCheck as JMESPathCheckV2
from azure.cli.testsdk.checkers import NoneCheck as NoneCheckV2

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=line-too-long
# pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"


class VMImageListByAliasesScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListByAliasesScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_list_by_alias(self):
        self.execute()

    def body(self):
        result = self.cmd('vm image list --offer ubuntu')
        self.assertTrue(len(result) >= 1)
        self.assertEqual(result[0]['publisher'], 'Canonical')
        self.assertTrue(result[0]['sku'].endswith('LTS'))


class VMUsageScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMUsageScenarioTest, self).__init__(__file__, test_method)

    def test_vm_usage(self):
        self.execute()

    def body(self):
        self.cmd('vm list-usage --location westus',
                 checks=JMESPathCheck('type(@)', 'array'))


class VMImageListThruServiceScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListThruServiceScenarioTest, self).__init__(__file__, test_method)

    def test_vm_images_list_thru_services(self):
        self.execute()

    def body(self):
        result = self.cmd('vm image list -l westus --publisher Canonical --offer Ubuntu_Snappy_Core -o tsv --all')
        assert result.index('15.04') >= 0

        result = self.cmd('vm image list -p Canonical -f Ubuntu_Snappy_Core -o tsv --all')
        assert result.index('15.04') >= 0


class VMOpenPortTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMOpenPortTest, self).__init__(__file__, test_method, resource_group='cli_test_open_port')
        self.vm_name = 'vm1'

    def set_up(self):
        super(VMOpenPortTest, self).set_up()
        rg = self.resource_group
        vm = self.vm_name
        self.cmd('vm create -g {0} -l westus -n {1} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password PasswordPassword1! '
                 '--public-ip-address-allocation dynamic '
                 '--authentication-type password'.format(rg, vm))

    def test_vm_open_port(self):
        self.execute()

    def body(self):
        rg = self.resource_group
        vm = self.vm_name

        # min params - apply to existing NIC (updates existing NSG)
        nsg_id = self.cmd('vm open-port -g {} -n {} --port * --priority 900'.format(rg, vm))['id']
        nsg_name = os.path.split(nsg_id)[1]
        self.cmd('network nsg show -g {} -n {}'.format(rg, nsg_name),
                 checks=JMESPathCheck("length(securityRules[?name == 'open-port-all'])", 1))

        # apply to subnet (creates new NSG)
        new_nsg = 'newNsg'
        self.cmd('vm open-port -g {} -n {} --apply-to-subnet --nsg-name {} --port * --priority 900'.format(rg, vm, new_nsg))
        self.cmd('network nsg show -g {} -n {}'.format(rg, new_nsg),
                 checks=JMESPathCheck("length(securityRules[?name == 'open-port-all'])", 1))


class VMShowListSizesListIPAddressesScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMShowListSizesListIPAddressesScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_list_ip')
        self.location = 'westus'
        self.vm_name = 'vm-with-public-ip'
        self.ip_allocation_method = 'dynamic'

    def test_vm_show_list_sizes_list_ip_addresses(self):
        self.execute()

    def body(self):
        # Expecting no results at the beginning
        self.cmd('vm list-ip-addresses --resource-group {}'.format(self.resource_group), checks=NoneCheck())
        self.cmd('vm create --resource-group {0} --location {1} -n {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--public-ip-address-allocation {3} '
                 '--authentication-type password'.format(
                     self.resource_group, self.location, self.vm_name, self.ip_allocation_method))
        result = self.cmd('vm show --resource-group {} --name {} -d'.format(
            self.resource_group, self.vm_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.vm_name),
                JMESPathCheck('location', self.location),
                JMESPathCheck('resourceGroup', self.resource_group),
        ])
        self.assertEqual(4, len(result['publicIps'].split('.')))

        result = self.cmd('vm list --resource-group {} -d'.format(self.resource_group), checks=[
            JMESPathCheck('[0].name', self.vm_name),
            JMESPathCheck('[0].location', self.location),
            JMESPathCheck('[0].resourceGroup', self.resource_group),
            JMESPathCheck('[0].powerState', 'VM running')
        ])
        self.assertEqual(4, len(result[0]['publicIps'].split('.')))

        self.cmd('vm list-vm-resize-options --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name), checks=JMESPathCheck('type(@)', 'array'))

        # Expecting the one we just added
        rg_name_all_upper = self.resource_group.upper()  # test the command handles name with casing diff.
        self.cmd('vm list-ip-addresses --resource-group {}'.format(rg_name_all_upper), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].virtualMachine.name', self.vm_name),
            JMESPathCheck('[0].virtualMachine.resourceGroup', self.resource_group),
            JMESPathCheck('length([0].virtualMachine.network.publicIpAddresses)', 1),
            JMESPathCheck('[0].virtualMachine.network.publicIpAddresses[0].ipAllocationMethod', self.ip_allocation_method.title()),
            JMESPathCheck('type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)', 'string')
        ])


class VMSizeListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMSizeListScenarioTest, self).__init__(__file__, test_method)

    def test_vm_size_list(self):
        self.execute()

    def body(self):
        self.cmd('vm list-sizes --location westus',
                 checks=JMESPathCheck('type(@)', 'array'))


class VMImageListOffersScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListOffersScenarioTest, self).__init__(__file__, test_method)
        self.location = 'westus'
        self.publisher_name = 'Canonical'

    def test_vm_image_list_offers(self):
        self.execute()

    def body(self):
        result = self.cmd('vm image list-offers --location {} --publisher {}'.format(
            self.location, self.publisher_name))
        self.assertTrue(len(result) > 0)
        self.assertFalse([i for i in result if i['location'].lower() != self.location])


class VMImageListPublishersScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListPublishersScenarioTest, self).__init__(__file__, test_method)
        self.location = 'westus'

    def test_vm_image_list_publishers(self):
        self.execute()

    def body(self):
        self.cmd('vm image list-publishers --location {}'.format(self.location), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?location == '{}']) == length(@)".format(self.location), True),
        ])


class VMImageListSkusScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListSkusScenarioTest, self).__init__(__file__, test_method)
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'

    def test_vm_image_list_skus(self):
        self.execute()

    def body(self):
        query = "length([].id.contains(@, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/'))".format(
            self.publisher_name, self.offer)
        result = self.cmd('vm image list-skus --location {} -p {} --offer {} --query "{}"'.format(
            self.location, self.publisher_name, self.offer, query))
        self.assertTrue(result > 0)


class VMImageShowScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageShowScenarioTest, self).__init__(__file__, test_method)
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'
        self.skus = '14.04.2-LTS'
        self.version = '14.04.201503090'

    def test_vm_image_show(self):
        self.execute()

    def body(self):
        self.cmd('vm image show --location {} --publisher {} --offer {} --sku {} --version {}'.format(
            self.location, self.publisher_name, self.offer, self.skus, self.version), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('location', self.location),
                JMESPathCheck('name', self.version),
                JMESPathCheck("contains(id, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/{}/Versions/{}')".format(
                    self.publisher_name, self.offer, self.skus, self.version), True),
        ])


class VMGeneralizeScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMGeneralizeScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_generalize_vm')
        self.location = 'westus'
        self.vm_name = 'vm-generalize'

    def body(self):
        self.cmd('vm create -g {0} --location {1} -n {2} --admin-username ubuntu '
                 '--image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk'.format(
                     self.resource_group, self.location, self.vm_name))
        self.cmd('vm stop -g {} -n {}'.format(self.resource_group, self.vm_name))
        # Should be able to generalize the VM after it has been stopped
        self.cmd('vm generalize -g {} -n {}'.format(self.resource_group, self.vm_name), checks=NoneCheck())
        vm = self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name))
        self.cmd('vm capture -g {} -n {} --vhd-name-prefix vmtest'.format(self.resource_group, self.vm_name),
                 checks=NoneCheck())

        # capture to a custom image
        image_name = 'myImage'
        self.cmd('image create -g {} -n {} --source {}'.format(self.resource_group, image_name, self.vm_name), checks=[
            JMESPathCheck('name', image_name),
            JMESPathCheck('sourceVirtualMachine.id', vm['id'])
        ])

    def test_vm_generalize(self):
        self.execute()


class VMVMSSWindowsLicenseTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_windows_vm_vmss_license_type(self, resource_group):
        vm_name = 'winvm'
        vmss_name = 'winvmss'
        self.cmd('vm create -g {} -n {} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server'.format(resource_group, vm_name))
        self.cmd('vm show -g {} -n {}'.format(resource_group, vm_name), checks=[
            JMESPathCheckV2('licenseType', 'Windows_Server')
        ])
        self.cmd('vmss create -g {} -n {} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1'.format(resource_group, vmss_name))
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('virtualMachineProfile.licenseType', 'Windows_Server')
        ])


class VMCustomImageTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_custom_image(self, resource_group):
        # this test should be recorded using accounts "@azuresdkteam.onmicrosoft.com", as it uses pre-made generalized vms
        prepared_vm_unmanaged = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/sdk-test/providers/Microsoft.Compute/virtualMachines/sdk-test-um'
        prepared_vm = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/sdk-test/providers/Microsoft.Compute/virtualMachines/sdk-test-m'

        image1 = 'image1'  # for image captured from vm with unmanaged disk
        self.cmd('image create -g {} -n {} --source {}'.format(resource_group, image1, prepared_vm_unmanaged), checks=[
            JMESPathCheckV2('name', image1)
        ])
        self.cmd('vm create -g {} -n vm1 --image {} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password'.format(
            resource_group, image1), checks=[
                JMESPathCheckV2('resourceGroup', resource_group)  # spot check enusing the VM was created
        ])
        self.cmd('vm show -g {} -n vm1'.format(resource_group), checks=[
            JMESPathCheckV2('storageProfile.imageReference.resourceGroup', resource_group),
            JMESPathCheckV2('storageProfile.osDisk.createOption', 'FromImage')
        ])
        self.cmd('vmss create -g {} -n vmss1 --image {} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password'.format(
            resource_group, image1), checks=[
            JMESPathCheckV2('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', resource_group),
            JMESPathCheckV2('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage')
        ])

        image2 = 'image2'  # for image captured from vm with managed os disk and data disk
        self.cmd('image create -g {} -n {} --source {}'.format(resource_group, image2, prepared_vm), checks=[
            JMESPathCheckV2('name', image2)
        ])

        self.cmd('vm create -g {} -n vm2 --image {} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password'.format(
            resource_group, image2), checks=[
                JMESPathCheckV2('resourceGroup', resource_group)  # spot check enusing the VM was created
        ])
        self.cmd('vm show -g {} -n vm2'.format(resource_group), checks=[
            JMESPathCheckV2('storageProfile.imageReference.resourceGroup', resource_group),
            JMESPathCheckV2('storageProfile.osDisk.createOption', 'FromImage'),
            JMESPathCheckV2("length(storageProfile.dataDisks)", 1),
            JMESPathCheckV2("storageProfile.dataDisks[0].createOption", 'FromImage'),
            JMESPathCheckV2('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS')
        ])

        self.cmd('vm create -g {} -n vm3 --image {} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password --storage-sku Premium_LRS'.format(
            resource_group, image2))
        self.cmd('vm show -g {} -n vm3'.format(resource_group), checks=[
            JMESPathCheckV2('storageProfile.imageReference.resourceGroup', resource_group),
            JMESPathCheckV2('storageProfile.osDisk.createOption', 'FromImage'),
            JMESPathCheckV2("length(storageProfile.dataDisks)", 1),
            JMESPathCheckV2("storageProfile.dataDisks[0].createOption", 'FromImage'),
            JMESPathCheckV2('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS')
        ])

        self.cmd('vmss create -g {} -n vmss2 --image {} --admin-username sdk-test-admin --admin-password testPassword0 --authentication-type password'.format(
            resource_group, image2), checks=[
            JMESPathCheckV2('vmss.virtualMachineProfile.storageProfile.imageReference.resourceGroup', resource_group),
            JMESPathCheckV2('vmss.virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            JMESPathCheckV2("length(vmss.virtualMachineProfile.storageProfile.dataDisks)", 1),
            JMESPathCheckV2("vmss.virtualMachineProfile.storageProfile.dataDisks[0].createOption", 'FromImage'),
            JMESPathCheckV2("vmss.virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType", 'Standard_LRS')
        ])

    @ResourceGroupPreparer()
    def test_custom_image_with_plan(self, resource_group):
        # this test should be recorded using accounts "@azuresdkteam.onmicrosoft.com", as it uses pre-made custom image
        prepared_image_with_plan_info = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/sdk-test/providers/Microsoft.Compute/images/custom-image-with-plan'
        plan_name = 'linuxdsvmubuntu'
        self.cmd('vm create -g {} -n vm1 --image {} --generate-ssh-keys --plan-promotion-code 99percentoff --plan-publisher microsoft-ads --plan-name {} --plan-product linux-data-science-vm-ubuntu'.format(
            resource_group, prepared_image_with_plan_info, plan_name))
        self.cmd('vm show -g {} -n vm1'.format(resource_group), checks=[
            JMESPathCheckV2('plan.name', plan_name)
        ])


class VMCreateFromUnmanagedDiskTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateFromUnmanagedDiskTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_from_unmanaged_disk')
        self.location = 'westus'

    def test_vm_create_from_unmanaged_disk(self):
        self.execute()

    def body(self):
        # create a vm with unmanaged os disk
        vm1 = 'vm1'
        self.cmd('vm create -g {} -n {} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password'.format(
            self.resource_group, vm1))
        vm1_info = self.cmd('vm show -g {} -n {}'.format(self.resource_group, vm1), checks=[
            JMESPathCheck('name', vm1),
            JMESPathCheck('licenseType', None)
        ])
        self.cmd('vm stop -g {} -n {}'.format(self.resource_group, vm1))

        # import the unmanaged os disk into a specialized managed disk
        test_specialized_os_disk_vhd_uri = vm1_info['storageProfile']['osDisk']['vhd']['uri']
        vm2 = 'vm2'
        attach_os_disk = 'os1'
        self.cmd('disk create -g {} -n {} --source {}'.format(self.resource_group, attach_os_disk, test_specialized_os_disk_vhd_uri), checks=[
            JMESPathCheck('name', attach_os_disk)
        ])
        # create a vm by attaching to it
        self.cmd('vm create -g {} -n {} --attach-os-disk {} --os-type linux'.format(self.resource_group, vm2, attach_os_disk), checks=[
            JMESPathCheck('powerState', 'VM running')
        ])


class VMCreateWithSpecializedUnmanagedDiskTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateWithSpecializedUnmanagedDiskTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_with_specialized_unmanaged_disk')
        self.location = 'westus'

    def test_vm_create_with_specialized_unmanaged_disk(self):
        self.execute()

    def body(self):
        # create a vm with unmanaged os disk
        self.cmd('vm create -g {} -n vm1 --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password'.format(
            self.resource_group))
        vm1_info = self.cmd('vm show -g {} -n vm1'.format(self.resource_group))
        disk_uri = vm1_info['storageProfile']['osDisk']['vhd']['uri']

        self.cmd('vm delete -g {} -n vm1 -y'.format(self.resource_group))

        # create a vm by attaching the OS disk from the deleted VM
        self.cmd('vm create -g {} -n vm2 --attach-os-disk {} --os-type linux --use-unmanaged-disk'.format(self.resource_group, disk_uri), checks=[
            JMESPathCheck('powerState', 'VM running')
        ])


class VMAttachDisksOnCreate(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_create_by_attach_os_and_data_disks(self, resource_group):
        # the testing below follow a real custom's workflow requiring the support of attaching data disks on create

        # creating a vm
        self.cmd('vm create -g {} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --data-disk-sizes-gb 2'.format(resource_group))
        result = self.cmd('vm show -g {} -n vm1'.format(resource_group)).get_output_in_json()
        origin_os_disk_name = result['storageProfile']['osDisk']['name']
        origin_data_disk_name = result['storageProfile']['dataDisks'][0]['name']

        # snapshot the os & data disks
        os_snapshot = 'oSnapshot'
        os_disk = 'sDisk'
        data_snapshot = 'dSnapshot'
        data_disk = 'dDisk'
        self.cmd('snapshot create -g {} -n {} --source {}'.format(resource_group, os_snapshot, origin_os_disk_name))
        self.cmd('disk create -g {} -n {} --source {}'.format(resource_group, os_disk, os_snapshot))
        self.cmd('snapshot create -g {} -n {} --source {}'.format(resource_group, data_snapshot, origin_data_disk_name))
        self.cmd('disk create -g {} -n {} --source {}'.format(resource_group, data_disk, data_snapshot))

        # rebuild a new vm
        # (os disk can be resized)
        self.cmd('vm create -g {} -n vm2 --attach-os-disk {} --attach-data-disks {} --data-disk-sizes-gb 3 --os-disk-size-gb 100 --os-type linux'.format(resource_group, os_disk, data_disk), checks=[
            JMESPathCheckV2('powerState', 'VM running'),
        ])
        self.cmd('vm show -g {} -n vm2'.format(resource_group), checks=[
            JMESPathCheckV2('length(storageProfile.dataDisks)', 2),
            JMESPathCheckV2('storageProfile.dataDisks[0].diskSizeGb', 3),
            JMESPathCheckV2('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            JMESPathCheckV2('storageProfile.osDisk.diskSizeGb', 100)
        ])

    @ResourceGroupPreparer()
    def test_vm_create_by_attach_unmanaged_os_and_data_disks(self, resource_group):
        # creating a vm
        self.cmd('vm create -g {} -n vm1 --use-unmanaged-disk --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password'.format(resource_group))
        self.cmd('vm unmanaged-disk attach -g {} --vm-name vm1 --new --size-gb 2'.format(resource_group))
        result = self.cmd('vm show -g {} -n vm1'.format(resource_group)).get_output_in_json()
        os_disk_vhd = result['storageProfile']['osDisk']['vhd']['uri']
        data_disk_vhd = result['storageProfile']['dataDisks'][0]['vhd']['uri']

        # delete the vm to end vhd's leases so they can be used to create a new vm through attaching
        self.cmd('vm deallocate -g {} -n vm1'.format(resource_group))
        self.cmd('vm delete -g {} -n vm1 -y'.format(resource_group))

        # rebuild a new vm
        self.cmd('vm create -g {} -n vm2 --attach-os-disk {} --attach-data-disks {} --os-type linux --use-unmanaged-disk'.format(
            resource_group, os_disk_vhd, data_disk_vhd), checks=[JMESPathCheckV2('powerState', 'VM running')])


class VMOSDiskSize(ScenarioTest):

    @ResourceGroupPreparer()
    def test_set_os_disk_size(self, resource_group):
        # test unmanaged disk
        storage_name = self.create_random_name(prefix='cli', length=12)
        self.cmd('vm create -g {} -n vm --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75 --use-unmanaged-disk --storage-account {}'.format(resource_group, storage_name))
        result = self.cmd('storage blob list --account-name {} --container-name vhds'.format(storage_name)).get_output_in_json()
        self.assertTrue(result[0]['properties']['contentLength'] > 75000000000)

        # test managed disk
        self.cmd('vm create -g {} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --os-disk-size-gb 75'.format(resource_group))
        self.cmd('vm show -g {} -n vm1'.format(resource_group), checks=[
            JMESPathCheckV2('storageProfile.osDisk.diskSizeGb', 75)
        ])


class VMManagedDiskScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMManagedDiskScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_managed_disk')
        self.location = 'westus'

    def body(self):
        disk_name = 'd1'
        disk_name2 = 'd2'
        snapshot_name = 's1'
        snapshot_name2 = 's2'
        image_name = 'i1'

        # create a disk and update
        data_disk = self.cmd('disk create -g {} -n {} --size-gb {} --tags tag1=d1'.format(self.resource_group, disk_name, 1), checks=[
            JMESPathCheck('sku.name', 'Premium_LRS'),
            JMESPathCheck('diskSizeGb', 1),
            JMESPathCheck('tags.tag1', 'd1')
        ])
        self.cmd('disk update -g {} -n {} --size-gb {} --sku {}'.format(self.resource_group, disk_name, 10, 'Standard_LRS'), checks=[
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('diskSizeGb', 10)
        ])

        # create another disk by importing from the disk1
        data_disk2 = self.cmd('disk create -g {} -n {} --source {}'.format(self.resource_group, disk_name2, data_disk['id']))

        # create a snpashot
        os_snapshot = self.cmd('snapshot create -g {} -n {} --size-gb {} --sku {} --tags tag1=s1'.format(
            self.resource_group, snapshot_name, 1, 'Premium_LRS'), checks=[
            JMESPathCheck('sku.name', 'Premium_LRS'),
            JMESPathCheck('diskSizeGb', 1),
            JMESPathCheck('tags.tag1', 's1')
        ])
        # update the sku
        self.cmd('snapshot update -g {} -n {} --sku {}'.format(self.resource_group, snapshot_name, 'Standard_LRS'), checks=[
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('diskSizeGb', 1)
        ])

        # create another snapshot by importing from the disk1
        data_snapshot = self.cmd('snapshot create -g {} -n {} --source {} --sku {}'.format(
            self.resource_group, snapshot_name2, disk_name, 'Premium_LRS'))

        # till now, image creation doesn't inspect the disk for os, so the command below should succeed with junk disk
        self.cmd('image create -g {} -n {} --source {} --data-disk-sources {} {} {} --os-type Linux --tags tag1=i1'.format(
            self.resource_group, image_name, snapshot_name, disk_name, data_snapshot['id'], data_disk2['id']), checks=[
            JMESPathCheck('storageProfile.osDisk.osType', 'Linux'),
            JMESPathCheck('storageProfile.osDisk.snapshot.id', os_snapshot['id']),
            JMESPathCheck('length(storageProfile.dataDisks)', 3),
            JMESPathCheck('storageProfile.dataDisks[0].lun', 0),
            JMESPathCheck('storageProfile.dataDisks[1].lun', 1),
            JMESPathCheck('tags.tag1', 'i1')
        ])

    def test_managed_disk(self):
        self.execute()


class VMCreateAndStateModificationsScenarioTest(ResourceGroupVCRTestBase):  # pylint:disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateAndStateModificationsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_state_mod')
        self.location = 'eastus'
        self.vm_name = 'vm-state-mod'
        self.nsg_name = 'mynsg'
        self.ip_name = 'mypubip'
        self.storage_name = 'clitestvmcreate20170301'
        self.vnet_name = 'myvnet'

    def test_vm_create_state_modifications(self):
        self.execute()

    def _check_vm_power_state(self, expected_power_state):
        self.cmd('vm get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', self.vm_name),
                JMESPathCheck('resourceGroup', self.resource_group),
                JMESPathCheck('length(instanceView.statuses)', 2),
                JMESPathCheck('instanceView.statuses[0].code', 'ProvisioningState/succeeded'),
                JMESPathCheck('instanceView.statuses[1].code', expected_power_state),
        ])

    def body(self):
        # Expecting no results
        self.cmd('vm list --resource-group {}'.format(self.resource_group), checks=NoneCheck())
        self.cmd('vm create --resource-group {0} --location {1} --name {2} --admin-username ubuntu '
                 '--image UbuntuLTS --admin-password testPassword0 '
                 '--authentication-type password '
                 '--tags firsttag=1 secondtag=2 thirdtag --nsg {3} --public-ip-address {4} '
                 '--vnet-name {5} --storage-account {6} --use-unmanaged-disk'.format(
                     self.resource_group, self.location, self.vm_name,
                     self.nsg_name, self.ip_name, self.vnet_name, self.storage_name))

        # Expecting one result, the one we created
        self.cmd('vm list --resource-group {}'.format(self.resource_group), [
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].resourceGroup', self.resource_group),
            JMESPathCheck('[0].name', self.vm_name),
            JMESPathCheck('[0].location', self.location),
            JMESPathCheck('[0].provisioningState', 'Succeeded'),
        ])

        # Verify tags were set
        self.cmd('vm show --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name), checks=[
                JMESPathCheck('tags.firsttag', '1'),
                JMESPathCheck('tags.secondtag', '2'),
                JMESPathCheck('tags.thirdtag', ''),
        ])
        self._check_vm_power_state('PowerState/running')

        self.cmd('vm user update -g {} -n {} -u foouser1 -p Foo12345 '.format(self.resource_group, self.vm_name))
        self.cmd('vm user delete -g {} -n {} -u foouser1'.format(self.resource_group, self.vm_name))

        self.cmd('network nsg show --resource-group {} --name {}'.format(
            self.resource_group, self.nsg_name), checks=[
                JMESPathCheck('tags.firsttag', '1'),
                JMESPathCheck('tags.secondtag', '2'),
                JMESPathCheck('tags.thirdtag', ''),
        ])
        self.cmd('network public-ip show --resource-group {} --name {}'.format(
            self.resource_group, self.ip_name), checks=[
                JMESPathCheck('tags.firsttag', '1'),
                JMESPathCheck('tags.secondtag', '2'),
                JMESPathCheck('tags.thirdtag', ''),
        ])
        self.cmd('network vnet show --resource-group {} --name {}'.format(
            self.resource_group, self.vnet_name), checks=[
                JMESPathCheck('tags.firsttag', '1'),
                JMESPathCheck('tags.secondtag', '2'),
                JMESPathCheck('tags.thirdtag', ''),
        ])
        self.cmd('storage account show --resource-group {} --name {}'.format(
            self.resource_group, self.storage_name), checks=[
                JMESPathCheck('tags.firsttag', '1'),
                JMESPathCheck('tags.secondtag', '2'),
                JMESPathCheck('tags.thirdtag', ''),
        ])

        self.cmd('vm stop --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/stopped')
        self.cmd('vm start --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.cmd('vm restart --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.cmd('vm deallocate --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/deallocated')
        self.cmd('vm resize -g {} -n {} --size {}'.format(
            self.resource_group, self.vm_name, ' Standard_DS2_v2'),
            checks=JMESPathCheck('hardwareProfile.vmSize', 'Standard_DS2_v2'))
        self.cmd('vm delete --resource-group {} --name {} --yes'.format(
            self.resource_group, self.vm_name))
        # Expecting no results
        self.cmd('vm list --resource-group {}'.format(self.resource_group), checks=NoneCheck())


class VMNoWaitScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMNoWaitScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_no_wait')
        self.location = 'westus'
        self.name = 'vmnowait2'

    def test_vm_create_no_wait(self):
        self.execute()

    def body(self):
        self.cmd('vm create -g {} -n {} --admin-username user12 --admin-password testPassword0 --authentication-type password --image UbuntuLTS --no-wait'.format(self.resource_group, self.name), checks=NoneCheck())
        self.cmd('vm wait -g {} -n {} --custom "{}"'.format(self.resource_group, self.name, "instanceView.statuses[?code=='PowerState/running']"), checks=NoneCheck())
        self.cmd('vm get-instance-view -g {} -n {}'.format(self.resource_group, self.name), checks=[
            JMESPathCheck("length(instanceView.statuses[?code=='PowerState/running'])", 1)
        ])
        self.cmd('vm update -g {} -n {} --set tags.mytag=tagvalue1 --no-wait'.format(self.resource_group, self.name), checks=NoneCheck())
        self.cmd('vm wait -g {} -n {} --updated'.format(self.resource_group, self.name), checks=NoneCheck())
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.name), checks=[
            JMESPathCheck("tags.mytag", 'tagvalue1')
        ])


class VMAvailSetScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_availset(self, resource_group):
        name = 'availset-test'
        self.cmd('vm availability-set create -g {} -n {}'.format(resource_group, name),
                 checks=[JMESPathCheckV2('name', name),
                         JMESPathCheckV2('platformFaultDomainCount', 2),
                         JMESPathCheckV2('platformUpdateDomainCount', 5),  # server defaults to 5
                         JMESPathCheckV2('sku.name', 'Aligned')])

        # create with explict UD count
        self.cmd('vm availability-set create -g {} -n avset2 --platform-fault-domain-count 2 --platform-update-domain-count 2'.format(resource_group),
                 checks=[JMESPathCheckV2('platformFaultDomainCount', 2),
                         JMESPathCheckV2('platformUpdateDomainCount', 2),
                         JMESPathCheckV2('sku.name', 'Aligned')])
        self.cmd('vm availability-set delete -g {} -n avset2'.format(resource_group))

        self.cmd('vm availability-set update -g {} -n {} --set tags.test=success'.format(resource_group, name),
                 checks=JMESPathCheckV2('tags.test', 'success'))
        self.cmd('vm availability-set list -g {}'.format(resource_group), checks=[
            JMESPathCheckV2('length(@)', 1),
            JMESPathCheckV2('[0].name', name)])
        self.cmd('vm availability-set list-sizes -g {} -n {}'.format(resource_group, name),
                 checks=JMESPathCheckV2('type(@)', 'array'))
        self.cmd('vm availability-set show -g {} -n {}'.format(resource_group, name),
                 checks=[JMESPathCheckV2('name', name)])
        self.cmd('vm availability-set delete -g {} -n {}'.format(resource_group, name))
        self.cmd('vm availability-set list -g {}'.format(resource_group), checks=[JMESPathCheckV2('length(@)', 0)])


# once https://github.com/Azure/azure-cli/issues/4127 is fixed, switch back to a regular ScenarioTest
class VMAvailSetLiveScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_availset_convert(self, resource_group):
        name = 'availset-test'
        self.cmd('vm availability-set create -g {} -n {} --unmanaged --platform-fault-domain-count 3 -l westus2 '.format(resource_group, name),
                 checks=[JMESPathCheckV2('name', name),
                         JMESPathCheckV2('platformFaultDomainCount', 3),
                         JMESPathCheckV2('platformUpdateDomainCount', 5),  # server defaults to 5
                         JMESPathCheckV2('sku.name', 'Classic')])

        # the conversion should auto adjust the FD from 3 to 2 as 'westus2' only offers 2
        self.cmd('vm availability-set convert -g {} -n {}'.format(resource_group, name),
                 checks=[JMESPathCheckV2('name', name),
                         JMESPathCheckV2('platformFaultDomainCount', 2),
                         JMESPathCheckV2('sku.name', 'Aligned')])


class ComputeListSkusScenarioTest(LiveScenarioTest):

    def test_list_compute_skus_table_output(self):
        result = self.cmd('vm list-skus -l westus -otable')
        lines = result.output.split('\n')
        # 1st line is header
        self.assertEqual(lines[0].split(), ['ResourceType', 'Locations', 'Name', 'Capabilities', 'Size', 'Tier'])
        # spot check the first 3 entries
        self.assertEqual(lines[3].split(), ['availabilitySets', 'westus', 'Classic', 'MaximumPlatformFaultDomainCount=3'])
        self.assertEqual(lines[4].split(), ['availabilitySets', 'westus', 'Aligned', 'MaximumPlatformFaultDomainCount=3'])
        self.assertEqual(lines[5].split(), ['virtualMachines', 'westus', 'Standard_DS1_v2', 'DS1_v2', 'Standard'])


class VMExtensionScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMExtensionScenarioTest, self).__init__(__file__, test_method)
        self.vm_name = 'myvm'

    def set_up(self):
        super(VMExtensionScenarioTest, self).set_up()
        self.cmd('vm create -n {} -g {} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0'.format(self.vm_name, self.resource_group))

    def test_vm_extension(self):
        self.execute()

    def body(self):
        publisher = 'Microsoft.OSTCExtensions'
        extension_name = 'VMAccessForLinux'
        user_name = 'foouser1'
        config_file = _write_config_file(user_name)

        try:
            self.cmd('vm extension list --vm-name {} --resource-group {}'.format(self.vm_name, self.resource_group), checks=[
                JMESPathCheck('length([])', 0)
            ])
            self.cmd('vm extension set -n {} --publisher {} --version 1.2  --vm-name {} --resource-group {} --protected-settings "{}"'
                     .format(extension_name, publisher, self.vm_name, self.resource_group, config_file))
            self.cmd('vm get-instance-view -n {} -g {}'.format(self.vm_name, self.resource_group), checks=[
                JMESPathCheck('*.extensions[0].name', ['VMAccessForLinux']),
                # JMESPathCheck('*.extensions[0].typeHandlerVersion', ['1.4.6.0']),
            ])
            self.cmd('vm extension show --resource-group {} --vm-name {} --name {}'.format(self.resource_group, self.vm_name, extension_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', extension_name),
                JMESPathCheck('resourceGroup', self.resource_group)
            ])
            self.cmd('vm extension delete --resource-group {} --vm-name {} --name {}'.format(self.resource_group, self.vm_name, extension_name),
                     checks=[JMESPathCheck('status', 'Succeeded')])
        finally:
            os.remove(config_file)


class VMMachineExtensionImageScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMMachineExtensionImageScenarioTest, self).__init__(__file__, test_method)
        self.location = 'westus'
        self.publisher = 'Microsoft.Azure.Diagnostics'
        self.name = 'IaaSDiagnostics'
        self.version = '1.6.4.0'

    def test_vm_machine_extension_image(self):
        self.execute()

    def body(self):
        self.cmd('vm extension image list-names --location {} --publisher {}'.format(
            self.location, self.publisher), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck("length([?location == '{}']) == length(@)".format(self.location), True),
        ])
        self.cmd('vm extension image list-versions --location {} -p {} --name {}'.format(
            self.location, self.publisher, self.name), checks=[
                JMESPathCheck('type(@)', 'array'),
                JMESPathCheck("length([?location == '{}']) == length(@)".format(self.location), True),
        ])
        self.cmd('vm extension image show --location {} -p {} --name {} --version {}'.format(
            self.location, self.publisher, self.name, self.version), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('location', self.location),
                JMESPathCheck("contains(id, '/Providers/Microsoft.Compute/Locations/{}/Publishers/{}/ArtifactTypes/VMExtension/Types/{}/Versions/{}')".format(
                    self.location, self.publisher, self.name, self.version), True)
        ])


class VMExtensionImageSearchScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMExtensionImageSearchScenarioTest, self).__init__(__file__, test_method)

    def test_vm_extension_image_search(self):
        self.execute()

    def body(self):
        # pick this specific name, so the search will be under one publisher. This avoids
        # the parallel searching behavior that causes incomplete VCR recordings.
        publisher = 'Test.Microsoft.VisualStudio.Services'
        image_name = 'TeamServicesAgentLinux1'
        self.cmd('vm extension image list -l westus --publisher {} --name {}'.format(publisher, image_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?name == '{}']) == length(@)".format(image_name), True)
        ])
        result = self.cmd('vm extension image list -l westus -p {} --name {} --latest'.format(publisher, image_name))
        assert len(result) == 1


class VMCreateUbuntuScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_create_ubuntu(self, resource_group, resource_group_location):
        admin_username = 'ubuntu'
        vm_names = ['cli-test-vm2']
        vm_image = 'UbuntuLTS'
        auth_type = 'ssh'
        self.cmd('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' --location {location} --data-disk-sizes-gb 1'.format(
            rg=resource_group,
            admin=admin_username,
            vm_name=vm_names[0],
            image=vm_image,
            auth_type=auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=resource_group_location
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=resource_group, vm_name=vm_names[0]), checks=[
            JMESPathCheckV2('provisioningState', 'Succeeded'),
            JMESPathCheckV2('osProfile.adminUsername', admin_username),
            JMESPathCheckV2('osProfile.computerName', vm_names[0]),
            JMESPathCheckV2('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            JMESPathCheckV2('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB),
            JMESPathCheckV2('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            JMESPathCheckV2('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
        ])

        # test for idempotency--no need to reverify, just ensure the command doesn't fail
        self.cmd('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' --location {location} --data-disk-sizes-gb 1'.format(
            rg=resource_group,
            admin=admin_username,
            vm_name=vm_names[0],
            image=vm_image,
            auth_type=auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=resource_group_location
        ))


class VMMultiNicScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMMultiNicScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_multi_nic_vm')
        self.vm_name = 'multinicvm1'

    def test_vm_create_multi_nics(self):
        self.execute()

    def set_up(self):
        super(VMMultiNicScenarioTest, self).set_up()
        rg = self.resource_group
        vnet_name = 'myvnet'
        subnet_name = 'mysubnet'
        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(rg, vnet_name, subnet_name))
        for i in range(1, 5):  # create four NICs
            self.cmd('network nic create -g {} -n nic{} --subnet {} --vnet-name {}'.format(rg, i, subnet_name, vnet_name))

    def body(self):
        rg = self.resource_group
        vm_name = self.vm_name

        self.cmd('vm create -g {} -n {} --image UbuntuLTS --nics nic1 nic2 nic3 nic4 --admin-username user11 --size Standard_DS3 --ssh-key-value \'{}\''.format(rg, vm_name, TEST_SSH_KEY_PUB))
        self.cmd('vm show -g {} -n {}'.format(rg, vm_name), checks=[
            JMESPathCheck("networkProfile.networkInterfaces[0].id.ends_with(@, 'nic1')", True),
            JMESPathCheck("networkProfile.networkInterfaces[1].id.ends_with(@, 'nic2')", True),
            JMESPathCheck("networkProfile.networkInterfaces[2].id.ends_with(@, 'nic3')", True),
            JMESPathCheck("networkProfile.networkInterfaces[3].id.ends_with(@, 'nic4')", True),
            JMESPathCheck('length(networkProfile.networkInterfaces)', 4)
        ])
        # cannot alter NICs on a running (or even stopped) VM
        self.cmd('vm deallocate -g {} -n {}'.format(rg, vm_name))

        self.cmd('vm nic list -g {} --vm-name {}'.format(rg, vm_name), checks=[
            JMESPathCheck('length(@)', 4),
            JMESPathCheck('[0].primary', True)
        ])
        self.cmd('vm nic show -g {} --vm-name {} --nic nic1'.format(rg, vm_name))
        self.cmd('vm nic remove -g {} --vm-name {} --nics nic4 --primary-nic nic1'.format(rg, vm_name), checks=[
            JMESPathCheck('length(@)', 3),
            JMESPathCheck('[0].primary', True),
            JMESPathCheck("[0].id.contains(@, 'nic1')", True)
        ])
        self.cmd('vm nic add -g {} --vm-name {} --nics nic4'.format(rg, vm_name), checks=[
            JMESPathCheck('length(@)', 4),
            JMESPathCheck('[0].primary', True),
            JMESPathCheck("[0].id.contains(@, 'nic1')", True)
        ])
        self.cmd('vm nic set -g {} --vm-name {} --nics nic1 nic2 --primary-nic nic2'.format(rg, vm_name), checks=[
            JMESPathCheck('length(@)', 2),
            JMESPathCheck('[1].primary', True),
            JMESPathCheck("[1].id.contains(@, 'nic2')", True)
        ])


class VMCreateNoneOptionsTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateNoneOptionsTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_create_none_options')  # create resource group in westus...

    def test_vm_create_none_options(self):
        self.execute()

    def body(self):
        vm_name = 'nooptvm'
        self.location = 'eastus'  # ...but create resources in eastus

        self.cmd('vm create -n {vm_name} -g {resource_group} --image Debian --availability-set {quotes} --nsg {quotes}'
                 ' --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --location {loc} --admin-username user11'
                 .format(vm_name=vm_name, resource_group=self.resource_group,
                         ssh_key=TEST_SSH_KEY_PUB,
                         quotes='""' if platform.system() == 'Windows' else "''", loc=self.location))

        self.cmd('vm show -n {vm_name} -g {resource_group}'.format(vm_name=vm_name, resource_group=self.resource_group), [
            JMESPathCheck('availabilitySet', None),
            JMESPathCheck('length(tags)', 0),
            JMESPathCheck('location', self.location)
        ])
        self.cmd('network public-ip show -n {vm_name}PublicIP -g {resource_group}'.format(vm_name=vm_name, resource_group=self.resource_group), checks=[
            NoneCheck()
        ], allowed_exceptions='was not found')


class VMBootDiagnostics(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMBootDiagnostics, self).__init__(__file__, test_method, resource_group='cli_test_vm_diagnostics')
        self.vm_name = 'myvm'
        self.storage_name = 'clitestbootdiag20170227'

    def test_vm_boot_diagnostics(self):
        self.execute()

    def set_up(self):
        super(VMBootDiagnostics, self).set_up()
        self.cmd('storage account create -g {} -n {} --sku Standard_LRS -l westus'.format(self.resource_group, self.storage_name))
        self.cmd('vm create -n {} -g {} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --use-unmanaged-disk'.format(self.vm_name, self.resource_group))

    def body(self):
        storage_uri = 'https://{}.blob.core.windows.net/'.format(self.storage_name)
        self.cmd('vm boot-diagnostics enable -g {} -n {} --storage {}'.format(self.resource_group, self.vm_name, self.storage_name))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('diagnosticsProfile.bootDiagnostics.enabled', True),
            JMESPathCheck('diagnosticsProfile.bootDiagnostics.storageUri', storage_uri)
        ])

        # will uncomment after #302 gets addressed
        # self.run('vm boot-diagnostics get-boot-log {}'.format(common_part))
        self.cmd('vm boot-diagnostics disable -g {} -n {}'.format(self.resource_group, self.vm_name))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name),
                 checks=JMESPathCheck('diagnosticsProfile.bootDiagnostics.enabled', False))


class VMSSExtensionInstallTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSExtensionInstallTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_extension')
        self.vmss_name = 'vmss1'

    def set_up(self):
        super(VMSSExtensionInstallTest, self).set_up()
        self.cmd('vmss create -n {} -g {} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0'.format(self.vmss_name, self.resource_group))

    def test_vmss_extension(self):
        self.execute()

    def body(self):
        publisher = 'Microsoft.OSTCExtensions'
        extension_name = 'VMAccessForLinux'
        user_name = 'myadmin'
        config_file = _write_config_file(user_name)

        try:
            self.cmd('vmss extension set -n {} --publisher {} --version 1.4  --vmss-name {} --resource-group {} --protected-settings "{}"'
                     .format(extension_name, publisher, self.vmss_name, self.resource_group, config_file))
            self.cmd('vmss extension show --resource-group {} --vmss-name {} --name {}'.format(self.resource_group, self.vmss_name, extension_name), checks=[
                JMESPathCheck('type(@)', 'object'),
                JMESPathCheck('name', extension_name)
            ])
        finally:
            os.remove(config_file)


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


class DiagnosticsExtensionInstallTest(ResourceGroupVCRTestBase):
    """
    Note that this is currently only for a Linux VM. There's currently no test of this feature for a Windows VM.
    """

    def __init__(self, test_method):
        super(DiagnosticsExtensionInstallTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_vmss_diagnostics_extension')
        self.storage_account = 'clitestdiagextsa20170510'
        self.vm = 'testdiagvm'
        self.vmss = 'testdiagvmss'

    def set_up(self):
        super(DiagnosticsExtensionInstallTest, self).set_up()
        self.cmd('storage account create -g {} -n {} -l westus --sku Standard_LRS'.format(self.resource_group, self.storage_account))
        self.cmd('vmss create -g {} -n {} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$'.format(self.resource_group, self.vmss))
        self.cmd('vm create -g {} -n {} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$ --use-unmanaged-disk'.format(self.resource_group, self.vm))

    def test_diagnostics_extension_install(self):
        self.execute()

    def body(self):
        storage_sastoken = '123'  # use junk keys, do not retrieve real keys which will get into the recording
        _, protected_settings = tempfile.mkstemp()
        with open(protected_settings, 'w') as outfile:
            json.dump({
                "storageAccountName": self.storage_account,
                "storageAccountSasToken": storage_sastoken
            }, outfile)
        protected_settings = protected_settings.replace('\\', '\\\\')

        _, public_settings = tempfile.mkstemp()
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'sample-public.json').replace('\\', '\\\\')
        with open(template_file) as data_file:
            data = json.load(data_file)
        data["StorageAccount"] = self.storage_account
        with open(public_settings, 'w') as outfile:
            json.dump(data, outfile)
        public_settings = public_settings.replace('\\', '\\\\')

        checks = [
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].name', "LinuxDiagnostic"),
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].publisher', "Microsoft.Azure.Diagnostics"),
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].settings.StorageAccount', self.storage_account),
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].typeHandlerVersion', '3.0')
        ]

        self.cmd("vmss diagnostics set -g {} --vmss-name {} --settings {} --protected-settings {}".format(
            self.resource_group, self.vmss, public_settings, protected_settings), checks=checks)

        self.cmd("vmss show -g {} -n {}".format(self.resource_group, self.vmss), checks=checks)

        # test standalone VM, we will start with an old version
        self.cmd('vm extension set -g {} --vm-name {} -n LinuxDiagnostic --version 2.3.9025 --publisher Microsoft.OSTCExtensions --settings {} --protected-settings {}'.format(
            self.resource_group, self.vm, public_settings, protected_settings), checks=[
            JMESPathCheck('typeHandlerVersion', '2.3')
        ])
        # see the 'diagnostics set' command upgrades to newer version
        self.cmd("vm diagnostics set -g {} --vm-name {} --settings {} --protected-settings {}".format(
            self.resource_group, self.vm, public_settings, protected_settings), checks=[
                JMESPathCheck('name', 'LinuxDiagnostic'),
                JMESPathCheck('publisher', 'Microsoft.Azure.Diagnostics'),
                JMESPathCheck('settings.StorageAccount', self.storage_account),
                JMESPathCheck('typeHandlerVersion', '3.0')
        ])

        self.cmd("vm show -g {} -n {}".format(self.resource_group, self.vm), checks=[
            JMESPathCheck('resources[0].name', 'LinuxDiagnostic'),
            JMESPathCheck('resources[0].publisher', 'Microsoft.Azure.Diagnostics'),
            JMESPathCheck('resources[0].settings.StorageAccount', self.storage_account)
        ])


# pylint: disable=too-many-instance-attributes
class VMCreateExistingOptions(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateExistingOptions, self).__init__(__file__, test_method, resource_group='cli_test_vm_create_existing')
        self.availset_name = 'vrfavailset'
        self.pubip_name = 'vrfpubip'
        self.storage_name = 'vcrstorage0012345'
        self.vnet_name = 'vrfvnet'
        self.subnet_name = 'vrfsubnet'
        self.nsg_name = 'vrfnsg'
        self.vm_name = 'vrfvm'
        self.disk_name = 'vrfosdisk'
        self.container_name = 'vrfcontainer'

    def test_vm_create_existing_options(self):
        self.execute()

    def set_up(self):
        super(VMCreateExistingOptions, self).set_up()

        self.cmd('vm availability-set create --name {} -g {} --unmanaged --platform-fault-domain-count 3 --platform-update-domain-count 3'.format(self.availset_name, self.resource_group))
        self.cmd('network public-ip create --name {} -g {}'.format(self.pubip_name, self.resource_group))
        self.cmd('storage account create --name {} -g {} -l westus --sku Standard_LRS'.format(self.storage_name, self.resource_group))
        self.cmd('network vnet create --name {} -g {} --subnet-name {}'.format(self.vnet_name, self.resource_group, self.subnet_name))
        self.cmd('network nsg create --name {} -g {}'.format(self.nsg_name, self.resource_group))

    def body(self):

        self.cmd('vm create --image UbuntuLTS --os-disk-name {disk_name}'
                 ' --vnet-name {vnet_name} --subnet {subnet_name}'
                 ' --availability-set {availset_name}'
                 ' --public-ip-address {pubip_name} -l "West US"'
                 ' --nsg {nsg_name}'
                 ' --use-unmanaged-disk'
                 ' --size Standard_DS2'
                 ' --admin-username user11'
                 ' --storage-account {storage_name} --storage-container-name {container_name} -g {resource_group}'
                 ' --name {vm_name} --ssh-key-value \'{key_value}\''
                 .format(vnet_name=self.vnet_name, subnet_name=self.subnet_name,
                         availset_name=self.availset_name, pubip_name=self.pubip_name,
                         resource_group=self.resource_group, nsg_name=self.nsg_name,
                         vm_name=self.vm_name, disk_name=self.disk_name,
                         container_name=self.container_name, storage_name=self.storage_name,
                         key_value=TEST_SSH_KEY_PUB))

        self.cmd('vm availability-set show -n {} -g {}'.format(self.availset_name, self.resource_group),
                 checks=JMESPathCheck('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.vm_name.upper()), True))
        self.cmd('network nsg show -n {} -g {}'.format(self.nsg_name, self.resource_group),
                 checks=JMESPathCheck('networkInterfaces[0].id.ends_with(@, \'{}\')'.format(self.vm_name + 'VMNic'), True))
        self.cmd('network nic show -n {}VMNic -g {}'.format(self.vm_name, self.resource_group),
                 checks=JMESPathCheck('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{}\')'.format(self.pubip_name), True))
        self.cmd('vm show -n {} -g {}'.format(self.vm_name, self.resource_group),
                 checks=JMESPathCheck('storageProfile.osDisk.vhd.uri', 'https://{}.blob.core.windows.net/{}/{}.vhd'.format(self.storage_name, self.container_name, self.disk_name)))


# pylint: disable=too-many-instance-attributes
class VMCreateExistingIdsOptions(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateExistingIdsOptions, self).__init__(__file__, test_method, resource_group='cli_test_vm_create_existing_ids')
        self.availset_name = 'vrfavailset'
        self.pubip_name = 'vrfpubip'
        self.storage_name = 'vcrstorage01234569'
        self.vnet_name = 'vrfvnet'
        self.subnet_name = 'vrfsubnet'
        self.nsg_name = 'vrfnsg'
        self.vm_name = 'vrfvm'
        self.disk_name = 'vrfosdisk'
        self.container_name = 'vrfcontainer'

    def test_vm_create_existing_ids_options(self):
        self.execute()

    def set_up(self):
        super(VMCreateExistingIdsOptions, self).set_up()

        self.cmd('vm availability-set create --name {} -g {} --unmanaged --platform-fault-domain-count 3 --platform-update-domain-count 3'.format(self.availset_name, self.resource_group))
        self.cmd('network public-ip create --name {} -g {}'.format(self.pubip_name, self.resource_group))
        self.cmd('storage account create --name {} -g {} -l westus --sku Standard_LRS'.format(self.storage_name, self.resource_group))
        self.cmd('network vnet create --name {} -g {} --subnet-name {}'.format(self.vnet_name, self.resource_group, self.subnet_name))
        self.cmd('network nsg create --name {} -g {}'.format(self.nsg_name, self.resource_group))

    def body(self):
        from azure.cli.core.commands.client_factory import get_subscription_id
        from msrestazure.tools import resource_id, is_valid_resource_id
        subscription_id = get_subscription_id()
        rg = self.resource_group

        av_set = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Compute', type='availabilitySets', name=self.availset_name)
        pub_ip = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='publicIpAddresses', name=self.pubip_name)
        subnet = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name=self.vnet_name, child_name_1=self.subnet_name)
        nsg = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='networkSecurityGroups', name=self.nsg_name)

        assert is_valid_resource_id(av_set)
        assert is_valid_resource_id(pub_ip)
        assert is_valid_resource_id(subnet)
        assert is_valid_resource_id(nsg)

        self.cmd('vm create --image UbuntuLTS --os-disk-name {disk_name}'
                 ' --subnet {subnet}'
                 ' --availability-set {availset}'
                 ' --public-ip-address {pubip} -l "West US"'
                 ' --nsg {nsg}'
                 ' --use-unmanaged-disk'
                 ' --size Standard_DS2'
                 ' --admin-username user11'
                 ' --storage-account {storage_name} --storage-container-name {container_name} -g {resource_group}'
                 ' --name {vm_name} --ssh-key-value \'{key_value}\''
                 .format(subnet=subnet, availset=av_set, pubip=pub_ip,
                         resource_group=self.resource_group, nsg=nsg,
                         vm_name=self.vm_name, disk_name=self.disk_name,
                         container_name=self.container_name, storage_name=self.storage_name,
                         key_value=TEST_SSH_KEY_PUB))

        self.cmd('vm availability-set show -n {} -g {}'.format(self.availset_name, self.resource_group),
                 checks=JMESPathCheck('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.vm_name.upper()), True))
        self.cmd('network nsg show -n {} -g {}'.format(self.nsg_name, self.resource_group),
                 checks=JMESPathCheck('networkInterfaces[0].id.ends_with(@, \'{}\')'.format(self.vm_name + 'VMNic'), True))
        self.cmd('network nic show -n {}VMNic -g {}'.format(self.vm_name, self.resource_group),
                 checks=JMESPathCheck('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{}\')'.format(self.pubip_name), True))
        self.cmd('vm show -n {} -g {}'.format(self.vm_name, self.resource_group),
                 checks=JMESPathCheck('storageProfile.osDisk.vhd.uri', 'https://{}.blob.core.windows.net/{}/{}.vhd'.format(self.storage_name, self.container_name, self.disk_name)))


class VMCreateCustomIP(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateCustomIP, self).__init__(__file__, test_method, resource_group='cli_test_vm_custom_ip')

    def test_vm_create_custom_ip(self):
        self.execute()

    def body(self):
        vm_name = 'vrfvmz'
        dns_name = 'vrfmyvm00110011z'

        self.cmd('vm create -n {vm_name} -g {resource_group} --image openSUSE-Leap --admin-username user11'
                 ' --private-ip-address 10.0.0.5 --public-ip-address-allocation static'
                 ' --public-ip-address-dns-name {dns_name} --ssh-key-value \'{key_value}\''
                 .format(vm_name=vm_name, resource_group=self.resource_group, dns_name=dns_name, key_value=TEST_SSH_KEY_PUB))

        self.cmd('network public-ip show -n {vm_name}PublicIP -g {resource_group}'.format(vm_name=vm_name, resource_group=self.resource_group), checks=[
            JMESPathCheck('publicIpAllocationMethod', 'Static'),
            JMESPathCheck('dnsSettings.domainNameLabel', dns_name)
        ])
        self.cmd('network nic show -n {vm_name}VMNic -g {resource_group}'.format(vm_name=vm_name, resource_group=self.resource_group),
                 checks=JMESPathCheck('ipConfigurations[0].privateIpAllocationMethod', 'Static'))


class VMDiskAttachDetachTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMDiskAttachDetachTest, self).__init__(__file__, test_method, resource_group='cli-test-disk')
        self.location = 'westus'
        self.vm_name = 'vm-diskattach-test'

    def test_vm_disk_attach_detach(self):
        self.execute()

    def set_up(self):
        super(VMDiskAttachDetachTest, self).set_up()
        self.cmd('vm create -g {} --location {} -n {} --admin-username admin123 '
                 '--image centos --admin-password testPassword0 '
                 '--authentication-type password'.format(
                     self.resource_group, self.location, self.vm_name))

    def body(self):
        disk_name = 'd1'
        disk_name2 = 'd2'
        self.cmd('vm disk attach -g {} --vm-name {} --disk {} --new --size-gb 1 --caching ReadOnly'.format(
            self.resource_group, self.vm_name, disk_name))
        self.cmd('vm disk attach -g {} --vm-name {} --disk {} --new --size-gb 2 --lun 2 --sku standard_lrs'.format(
            self.resource_group, self.vm_name, disk_name2))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 2),
            JMESPathCheck('storageProfile.dataDisks[0].name', disk_name),
            JMESPathCheck('storageProfile.dataDisks[0].caching', 'ReadOnly'),
            JMESPathCheck('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            JMESPathCheck('storageProfile.dataDisks[1].name', disk_name2),
            JMESPathCheck('storageProfile.dataDisks[1].lun', 2),
            JMESPathCheck('storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Standard_LRS'),
            JMESPathCheck('storageProfile.dataDisks[1].caching', 'None')
        ])
        self.cmd('vm disk detach -g {} --vm-name {} -n {}'.format(
            self.resource_group, self.vm_name, disk_name2))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 1),
            JMESPathCheck('storageProfile.dataDisks[0].name', disk_name),
        ])
        self.cmd('vm disk detach -g {} --vm-name {} -n {}'.format(
            self.resource_group, self.vm_name, disk_name))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 0),
        ])
        self.cmd('vm disk attach -g {} --vm-name {} --disk {} --caching ReadWrite --sku standard_lrs'.format(
            self.resource_group, self.vm_name, disk_name))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            JMESPathCheck('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
        ])


class VMUnmanagedDataDiskTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMUnmanagedDataDiskTest, self).__init__(__file__, test_method, resource_group='cli-test-disk')
        self.location = 'westus'
        self.vm_name = 'vm-datadisk-test'

    def test_vm_data_unmanaged_disk(self):
        self.execute()

    def set_up(self):
        super(VMUnmanagedDataDiskTest, self).set_up()
        self.cmd('vm create -g {} --location {} -n {} --admin-username ubuntu '
                 '--image UbuntuLTS --admin-password testPassword0 '
                 '--authentication-type password --use-unmanaged-disk'.format(
                     self.resource_group, self.location, self.vm_name))

    def body(self):
        # check we have no data disk
        result = self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 0)
        ])

        # get the vhd uri from VM's storage_profile
        blob_uri = result['storageProfile']['osDisk']['vhd']['uri']
        disk_name = 'd7'
        vhd_uri = blob_uri[0:blob_uri.rindex('/') + 1] + disk_name + '.vhd'

        # now attach
        self.cmd('vm unmanaged-disk attach -g {} --vm-name {} -n {} --vhd {} --new --caching ReadWrite --size-gb 8 --lun 1'.format(
            self.resource_group, self.vm_name, disk_name, vhd_uri))
        # check we have a data disk
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 1),
            JMESPathCheck('storageProfile.dataDisks[0].caching', 'ReadWrite'),
            JMESPathCheck('storageProfile.dataDisks[0].lun', 1),
            JMESPathCheck('storageProfile.dataDisks[0].diskSizeGb', 8),
            JMESPathCheck('storageProfile.dataDisks[0].createOption', 'Empty'),
            JMESPathCheck('storageProfile.dataDisks[0].vhd.uri', vhd_uri),
            JMESPathCheck('storageProfile.dataDisks[0].name', disk_name),
        ])

        # now detach
        self.cmd('vm unmanaged-disk detach -g {} --vm-name {} -n {}'.format(
            self.resource_group, self.vm_name, disk_name))

        # check we have no data disk
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 0),
        ])

        # now attach to existing
        self.cmd('vm unmanaged-disk attach -g {} --vm-name {} -n {} --vhd {} --caching ReadOnly'.format(
            self.resource_group, self.vm_name, disk_name, vhd_uri), checks=[
                JMESPathCheck('storageProfile.dataDisks[0].name', disk_name),
                JMESPathCheck('storageProfile.dataDisks[0].createOption', 'Attach')
        ])


class VMCreateCustomDataScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateCustomDataScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_create_vm_custom_data')
        self.deployment_name = 'azurecli-test-dep-vm-create-custom-data'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'
        self.vm_name = 'vm-name'
        self.custom_data = '#cloud-config\nhostname: myVMhostname'

    def test_vm_create_custom_data(self):
        self.execute()

    def set_up(self):
        super(VMCreateCustomDataScenarioTest, self).set_up()

    def body(self):
        self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' -l {location} --custom-data \'{custom_data}\''.format(
            rg=self.resource_group,
            admin=self.admin_username,
            image=self.vm_image,
            vm_name=self.vm_name,
            auth_type=self.auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=self.location,
            custom_data=self.custom_data
        ))

        # custom data is write only, hence we have no automatic way to cross check. Here we just verify VM was provisioned
        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=self.resource_group, vm_name=self.vm_name), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
        ])


# region VMSS Tests

class VMSSCreateAndModify(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSCreateAndModify, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_and_modify')

    def test_vmss_create_and_modify(self):
        self.execute()

    def body(self):
        vmss_name = 'vmss1'
        instance_count = 5
        new_instance_count = 4

        self.cmd('vmss create --admin-password testPassword0 --name {} -g {} --admin-username myadmin --image Win2012R2Datacenter --instance-count {}'
                 .format(vmss_name, self.resource_group, instance_count))

        self.cmd('vmss show --name {} -g {}'.format(vmss_name, self.resource_group))

        self.cmd('vmss list', checks=JMESPathCheck('type(@)', 'array'))

        self.cmd('vmss list --resource-group {}'.format(self.resource_group), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', vmss_name),
            JMESPathCheck('[0].resourceGroup', self.resource_group)
        ])
        self.cmd('vmss list-skus --resource-group {} --name {}'.format(self.resource_group, vmss_name),
                 checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('vmss show --resource-group {} --name {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', vmss_name),
            JMESPathCheck('resourceGroup', self.resource_group)
        ])
        result = self.cmd('vmss list-instances --resource-group {} --name {} --query "[].instanceId"'.format(self.resource_group, vmss_name))
        instance_ids = result[3] + ' ' + result[4]
        self.cmd('vmss update-instances --resource-group {} --name {} --instance-ids {}'.format(self.resource_group, vmss_name, instance_ids))
        self.cmd('vmss get-instance-view --resource-group {} --name {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type(virtualMachine)', 'object'),
            JMESPathCheck('type(statuses)', 'array')
        ])

        self.cmd('vmss stop --resource-group {} --name {}'.format(self.resource_group, vmss_name))
        self.cmd('vmss start --resource-group {} --name {}'.format(self.resource_group, vmss_name))
        self.cmd('vmss restart --resource-group {} --name {}'.format(self.resource_group, vmss_name))

        self.cmd('vmss scale --resource-group {} --name {} --new-capacity {}'.format(self.resource_group, vmss_name, new_instance_count))
        self.cmd('vmss show --resource-group {} --name {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('sku.capacity', new_instance_count),
            JMESPathCheck('virtualMachineProfile.osProfile.windowsConfiguration.enableAutomaticUpdates', True)
        ])

        result = self.cmd('vmss list-instances --resource-group {} --name {} --query "[].instanceId"'.format(self.resource_group, vmss_name))
        instance_ids = result[2] + ' ' + result[3]
        self.cmd('vmss delete-instances --resource-group {} --name {} --instance-ids {}'.format(self.resource_group, vmss_name, instance_ids))
        self.cmd('vmss get-instance-view --resource-group {} --name {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('type(virtualMachine)', 'object'),
            JMESPathCheck('virtualMachine.statusesSummary[0].count', new_instance_count - 2)
        ])
        self.cmd('vmss deallocate --resource-group {} --name {}'.format(self.resource_group, vmss_name))
        self.cmd('vmss delete --resource-group {} --name {}'.format(self.resource_group, vmss_name))
        self.cmd('vmss list --resource-group {}'.format(self.resource_group), checks=NoneCheck())


class VMSSCreateOptions(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSCreateOptions, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_options')
        self.ip_name = 'vrfpubip'

    def set_up(self):
        super(VMSSCreateOptions, self).set_up()
        self.cmd('network public-ip create --name {} -g {}'.format(self.ip_name, self.resource_group))

    def test_vmss_create_options(self):
        self.execute()

    def body(self):
        vmss_name = 'vrfvmss'
        instance_count = 2
        caching = 'ReadWrite'
        upgrade_policy = 'automatic'

        self.cmd('vmss create --image Debian --admin-password testPassword0 -l westus'
                 ' -g {} -n {} --disable-overprovision --instance-count {}'
                 ' --os-disk-caching {} --upgrade-policy-mode {}'
                 ' --authentication-type password --admin-username myadmin --public-ip-address {}'
                 ' --data-disk-sizes-gb 1 --vm-sku Standard_D2_v2'
                 .format(self.resource_group, vmss_name, instance_count, caching,
                         upgrade_policy, self.ip_name))
        self.cmd('network lb show -g {} -n {}lb '.format(self.resource_group, vmss_name),
                 checks=JMESPathCheck('frontendIpConfigurations[0].publicIpAddress.id.ends_with(@, \'{}\')'.format(self.ip_name), True))
        self.cmd('vmss show -g {} -n {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('sku.capacity', instance_count),
            JMESPathCheck('virtualMachineProfile.storageProfile.osDisk.caching', caching),
            JMESPathCheck('upgradePolicy.mode', upgrade_policy.title()),
            JMESPathCheck('singlePlacementGroup', True),
        ])
        result = self.cmd('vmss list-instances -g {} -n {} --query "[].instanceId"'.format(self.resource_group, vmss_name))
        self.cmd('vmss show -g {} -n {} --instance-id {}'.format(self.resource_group, vmss_name, result[0]),
                 checks=JMESPathCheck('instanceId', result[0]))

        self.cmd('vmss disk attach -g {} -n {} --size-gb 3'.format(self.resource_group, vmss_name))
        self.cmd('vmss show -g {} -n {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('length(virtualMachineProfile.storageProfile.dataDisks)', 2),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Standard_LRS'),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[1].diskSizeGb', 3),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.storageAccountType', 'Standard_LRS'),
        ])
        self.cmd('vmss disk detach -g {} -n {} --lun 1'.format(self.resource_group, vmss_name))
        self.cmd('vmss show -g {} -n {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].lun', 0),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1)
        ])


class VMSSCreateBalancerOptionsTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer()
    def test_vmss_create_none_options(self, resource_group):
        vmss_name = 'vmss1'
        self.cmd('vmss create -n {0} -g {1} --image Debian --load-balancer {3} --admin-username ubuntu'
                 ' --ssh-key-value \'{2}\' --public-ip-address {3} --tags {3} --vm-sku Basic_A1'
                 .format(vmss_name, resource_group, TEST_SSH_KEY_PUB, '""' if platform.system() == 'Windows' else "''"))
        self.cmd('vmss show -n {} -g {}'.format(vmss_name, resource_group), [
            JMESPathCheckV2('tags', {}),
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations.ipConfigurations.loadBalancerBackendAddressPools', None),
            JMESPathCheckV2('sku.name', 'Basic_A1'),
            JMESPathCheckV2('sku.tier', 'Basic')
        ])
        self.cmd('vmss update -g {} -n {} --set tags.test=success'.format(resource_group, vmss_name),
                 checks=JMESPathCheckV2('tags.test', 'success'))
        self.cmd('network public-ip show -n {}PublicIP -g {}'.format(vmss_name, resource_group), checks=NoneCheckV2())

    @ResourceGroupPreparer()
    def test_vmss_create_with_app_gateway(self, resource_group):
        vmss_name = 'vmss1'
        self.cmd("vmss create -n {0} -g {1} --image Debian --admin-username clittester --ssh-key-value '{2}' --app-gateway apt1 --instance-count 5".format(vmss_name, resource_group, TEST_SSH_KEY_PUB), checks=[
            JMESPathCheckV2('vmss.provisioningState', 'Succeeded')
        ])
        # spot check it is using gateway
        self.cmd('vmss show -n {} -g {}'.format(vmss_name, resource_group), checks=[
            JMESPathCheckV2('sku.capacity', 5),
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].ipConfigurations[0].applicationGatewayBackendAddressPools[0].resourceGroup', resource_group)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_lb')
    def test_vmss_existing_lb(self, resource_group):
        vmss_name = 'vmss1'
        lb_name = 'lb1'
        self.cmd('network lb create -g {} -n {} --backend-pool-name test'.format(resource_group, lb_name))
        self.cmd('vmss create -g {} -n {} --load-balancer {} --image UbuntuLTS --admin-username clitester --admin-password TestTest12#$'.format(resource_group, vmss_name, lb_name))


# TODO: change back to ScenarioTest and re-record when issue #5111 is fixed
class VMSSCreatePublicIpPerVm(LiveScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer()
    def test_vmss_public_ip_per_vm_custom_domain_name(self, resource_group):
        vmss_name = 'vmss1'
        nsg_nam = 'testnsg'
        nsg_result = self.cmd('network nsg create -g {} -n {}'.format(resource_group, nsg_nam)).get_output_in_json()
        self.cmd("vmss create -n {0} -g {1} --image Debian --admin-username clittester --ssh-key-value '{2}' --vm-domain-name clitestnewnetwork --public-ip-per-vm --dns-servers 10.0.0.6 10.0.0.5 --nsg {3}".format(
            vmss_name, resource_group, TEST_SSH_KEY_PUB, nsg_nam), checks=[JMESPathCheckV2('vmss.provisioningState', 'Succeeded')])
        result = self.cmd("vmss show -n {0} -g {1}".format(vmss_name, resource_group), checks=[
            JMESPathCheckV2('length(virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers)', 2),
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers[0]', '10.0.0.6'),
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].dnsSettings.dnsServers[1]', '10.0.0.5'),
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].networkSecurityGroup.id', nsg_result['NewNSG']['id'])
        ])
        # spot check we have the domain name and have a public ip
        result = self.cmd('vmss list-instance-public-ips -n {} -g {}'.format(vmss_name, resource_group)).get_output_in_json()
        self.assertEqual(len(result[0]['ipAddress'].split('.')), 4)
        self.assertTrue(result[0]['dnsSettings']['domainNameLabel'].endswith('.clitestnewnetwork'))


class VMSSCreateAcceleratedNetworkingTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vmss_accelerated_networking(self, resource_group):
        vmss_name = 'vmss1'
        self.cmd("vmss create -n {0} -g {1} --vm-sku Standard_DS4_v2 --image Win2016Datacenter --admin-username clittester --admin-password Test12345678!!! --accelerated-networking --instance-count 1".format(vmss_name, resource_group))
        self.cmd('vmss show -n {} -g {}'.format(vmss_name, resource_group), checks=[
            JMESPathCheckV2('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].enableAcceleratedNetworking', True)
        ])


class SecretsScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer()
    def test_vm_create_linux_secrets(self, resource_group, resource_group_location):
        admin_username = 'ubuntu'
        resource_group_location = 'westus'
        vm_image = 'UbuntuLTS'
        auth_type = 'ssh'
        vm_name = 'vm-name'
        bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}])
        vault_name = self.create_random_name('vmlinuxkv', 20)

        message = 'Secret is missing vaultCertificates array or it is empty at index 0'
        with six.assertRaisesRegex(self, CLIError, message):
            self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' -l {location} --secrets \'{secrets}\''.format(
                rg=resource_group,
                admin=admin_username,
                image=vm_image,
                vm_name=vm_name,
                auth_type=auth_type,
                ssh_key=TEST_SSH_KEY_PUB,
                location=resource_group_location,
                secrets=bad_secrets
            ))

        vault_out = self.cmd('keyvault create -g {rg} -n {name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true'.format(
            rg=resource_group,
            name=vault_name,
            loc=resource_group_location
        )).get_output_in_json()

        time.sleep(60)

        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(
            vault_name,
            policy_path))
        secret_out = self.cmd('keyvault secret list-versions --vault-name {} -n cert1 --query "[?attributes.enabled].id" -o tsv'.format(vault_name)).output.strip()
        vm_format = self.cmd('vm format-secret -s {0}'.format(secret_out)).get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' -l {location} --secrets \'{secrets}\''.format(
            rg=resource_group,
            admin=admin_username,
            image=vm_image,
            vm_name=vm_name,
            auth_type=auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=resource_group_location,
            secrets=json.dumps(vm_format)
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=resource_group, vm_name=vm_name), checks=[
            JMESPathCheckV2('provisioningState', 'Succeeded'),
            JMESPathCheckV2('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            JMESPathCheckV2('osProfile.secrets[0].vaultCertificates[0].certificateUrl', secret_out)
        ])

    @ResourceGroupPreparer()
    def test_vm_create_windows_secrets(self, resource_group, resource_group_location):
        admin_username = 'windowsUser'
        resource_group_location = 'westus'
        vm_image = 'Win2012R2Datacenter'
        vm_name = 'vm-name'
        bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': [{'certificateUrl': 'certurl'}]}])
        vault_name = self.create_random_name('vmkeyvault', 20)

        message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
                  'vaultCertificate index 0'
        with six.assertRaisesRegex(self, CLIError, message):
            self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {location} --secrets \'{secrets}\''.format(
                rg=resource_group,
                admin=admin_username,
                image=vm_image,
                vm_name=vm_name,
                location=resource_group_location,
                secrets=bad_secrets
            ))

        vault_out = self.cmd(
            'keyvault create -g {rg} -n {name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true'.format(
                rg=resource_group,
                name=vault_name,
                loc=resource_group_location
            )).get_output_in_json()

        time.sleep(60)

        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(
            vault_name,
            policy_path))

        secret_out = self.cmd('keyvault secret list-versions --vault-name {} -n cert1 --query "[?attributes.enabled].id" -o tsv'.format(vault_name)).output.strip()
        vm_format = self.cmd('vm format-secret -s {0} --certificate-store "My"'.format(secret_out)).get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {location} --secrets \'{secrets}\''.format(
            rg=resource_group,
            admin=admin_username,
            image=vm_image,
            vm_name=vm_name,
            location=resource_group_location,
            secrets=json.dumps(vm_format)
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=resource_group, vm_name=vm_name), checks=[
            JMESPathCheckV2('provisioningState', 'Succeeded'),
            JMESPathCheckV2('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            JMESPathCheckV2('osProfile.secrets[0].vaultCertificates[0].certificateUrl', secret_out),
            JMESPathCheckV2('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
        ])


class VMSSCreateLinuxSecretsScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMSSCreateLinuxSecretsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_linux_secrets')
        self.vmss_name = 'vmss1-name'
        self.bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}])
        self.vault_name = 'vmcreatelinuxsecret3334'
        self.secret_name = 'mysecret'

    def test_vmss_create_linux_secrets(self):
        self.execute()

    def set_up(self):
        super(VMSSCreateLinuxSecretsScenarioTest, self).set_up()

    def body(self):
        vault_out = self.cmd('keyvault create -g {rg} -n {name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true'.format(
            rg=self.resource_group,
            name=self.vault_name,
            loc=self.location
        ))

        time.sleep(60)

        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(
            self.vault_name,
            policy_path))

        secret_out = self.cmd('keyvault secret list-versions --vault-name {} -n cert1 --query "[?attributes.enabled].id" -o tsv'.format(self.vault_name))
        vm_format = self.cmd('vm format-secret -s {0}'.format(secret_out))

        self.cmd('vmss create -n {name} -g {rg} --image Debian --admin-username deploy --ssh-key-value \'{ssh}\' --secrets \'{secrets}\''.format(
            name=self.vmss_name,
            rg=self.resource_group,
            ssh=TEST_SSH_KEY_PUB,
            secrets=json.dumps(vm_format)))

        self.cmd('vmss show -n {} -g {}'.format(self.vmss_name, self.resource_group), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('virtualMachineProfile.osProfile.secrets[0].sourceVault.id', vault_out['id']),
            JMESPathCheck('virtualMachineProfile.osProfile.secrets[0].vaultCertificates[0].certificateUrl', secret_out)
        ])


class VMSSCreateExistingOptions(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMSSCreateExistingOptions, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_existing_options')
        self.vnet_name = 'vrfvnet'
        self.subnet_name = 'vrfsubnet'
        self.lb_name = 'vrflb'
        self.bepool_name = 'mybepool'

    def set_up(self):
        super(VMSSCreateExistingOptions, self).set_up()
        self.cmd('network vnet create -n {} -g {} --subnet-name {}'
                 .format(self.vnet_name, self.resource_group, self.subnet_name))
        self.cmd('network lb create --name {} -g {} --backend-pool-name {}'
                 .format(self.lb_name, self.resource_group, self.bepool_name))

    def test_vmss_create_existing_options(self):
        self.execute()

    def body(self):
        vmss_name = 'vrfvmss'
        os_disk_name = 'vrfosdisk'
        container_name = 'vrfcontainer'
        sku_name = 'Standard_A3'

        self.cmd('vmss create --image CentOS --os-disk-name {} --admin-username ubuntu'
                 ' --vnet-name {} --subnet {} -l "West US" --vm-sku {}'
                 ' --storage-container-name {} -g {} --name {} --load-balancer {}'
                 ' --ssh-key-value \'{}\' --backend-pool-name {}'
                 ' --use-unmanaged-disk'
                 .format(os_disk_name, self.vnet_name, self.subnet_name, sku_name, container_name,
                         self.resource_group, vmss_name, self.lb_name, TEST_SSH_KEY_PUB,
                         self.bepool_name))
        self.cmd('vmss show --name {} -g {}'.format(vmss_name, self.resource_group), checks=[
            JMESPathCheck('sku.name', sku_name),
            JMESPathCheck('virtualMachineProfile.storageProfile.osDisk.name', os_disk_name),
            JMESPathCheck('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{}\')'
                          .format(container_name), True)
        ])
        self.cmd('network lb show --name {} -g {}'.format(self.lb_name, self.resource_group),
                 checks=JMESPathCheck('backendAddressPools[0].backendIpConfigurations[0].id.contains(@, \'{}\')'.format(vmss_name), True))
        self.cmd('network vnet show --name {} -g {}'.format(self.vnet_name, self.resource_group),
                 checks=JMESPathCheck('subnets[0].ipConfigurations[0].id.contains(@, \'{}\')'.format(vmss_name), True))


class VMSSCreateExistingIdsOptions(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSCreateExistingIdsOptions, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_existing_ids_options')
        self.vnet_name = 'vrfvnet'
        self.subnet_name = 'vrfsubnet'
        self.lb_name = 'vrflb'
        self.bepool_name = 'mybepool'

    def set_up(self):
        super(VMSSCreateExistingIdsOptions, self).set_up()
        self.cmd('network vnet create -n {} -g {} --subnet-name {}'
                 .format(self.vnet_name, self.resource_group, self.subnet_name))
        self.cmd('network lb create --name {} -g {} --backend-pool-name {}'
                 .format(self.lb_name, self.resource_group, self.bepool_name))

    def test_vmss_create_existing_ids_options(self):
        self.execute()

    def body(self):
        from azure.cli.core.commands.client_factory import get_subscription_id
        from msrestazure.tools import resource_id, is_valid_resource_id
        subscription_id = get_subscription_id()
        rg = self.resource_group
        vmss_name = 'vrfvmss'
        os_disk_name = 'vrfosdisk'
        container_name = 'vrfcontainer'
        sku_name = 'Standard_A3'

        subnet = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='virtualNetworks', child_type_1='subnets', name=self.vnet_name, child_name_1=self.subnet_name)
        lb = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='loadBalancers', name=self.lb_name)

        assert is_valid_resource_id(subnet)
        assert is_valid_resource_id(lb)

        self.cmd('vmss create --image CentOS --os-disk-name {} --admin-username ubuntu'
                 ' --subnet {} -l "West US" --vm-sku {}'
                 ' --storage-container-name {} -g {} --name {} --load-balancer {}'
                 ' --ssh-key-value \'{}\' --backend-pool-name {}'
                 ' --use-unmanaged-disk'
                 .format(os_disk_name, subnet, sku_name, container_name,
                         self.resource_group, vmss_name, lb, TEST_SSH_KEY_PUB, self.bepool_name))
        self.cmd('vmss show --name {} -g {}'.format(vmss_name, self.resource_group), checks=[
            JMESPathCheck('sku.name', sku_name),
            JMESPathCheck('virtualMachineProfile.storageProfile.osDisk.name', os_disk_name),
            JMESPathCheck('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0].ends_with(@, \'{}\')'
                          .format(container_name), True)
        ])
        self.cmd('network lb show --name {} -g {}'.format(self.lb_name, self.resource_group),
                 checks=JMESPathCheck('backendAddressPools[0].backendIpConfigurations[0].id.contains(@, \'{}\')'.format(vmss_name), True))
        self.cmd('network vnet show --name {} -g {}'.format(self.vnet_name, self.resource_group),
                 checks=JMESPathCheck('subnets[0].ipConfigurations[0].id.contains(@, \'{}\')'.format(vmss_name), True))


class VMSSVMsScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSVMsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_vms')
        self.ss_name = 'vmss1'
        self.vm_count = 2
        self.instance_ids = []

    def set_up(self):
        super(VMSSVMsScenarioTest, self).set_up()
        self.cmd('vmss create -g {} -n {} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password TestTest12#$ --instance-count {}'.format(self.resource_group, self.ss_name, self.vm_count))

    def test_vmss_vms(self):
        self.execute()

    def _check_vms_power_state(self, *args):
        for iid in self.instance_ids:
            result = self.cmd('vmss get-instance-view --resource-group {} --name {} --instance-id {}'.format(self.resource_group, self.ss_name, iid))
            self.assertTrue(result['statuses'][1]['code'] in args)

    def body(self):
        instance_list = self.cmd('vmss list-instances --resource-group {} --name {}'.format(self.resource_group, self.ss_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck('length(@)', self.vm_count),
            JMESPathCheck("[].name.starts_with(@, '{}')".format(self.ss_name), [True] * self.vm_count)
        ])

        self.instance_ids = [x['instanceId'] for x in instance_list]

        self.cmd('vmss show --resource-group {} --name {} --instance-id {}'.format(self.resource_group, self.ss_name, self.instance_ids[0]), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('instanceId', str(self.instance_ids[0]))
        ])
        result = self.cmd('vmss list-instance-connection-info --resource-group {} --name {}'.format(self.resource_group, self.ss_name))
        self.assertTrue(result['instance 0'].split('.')[1], '5000')
        self.cmd('vmss restart --resource-group {} --name {} --instance-ids *'.format(self.resource_group, self.ss_name))
        self._check_vms_power_state('PowerState/running', 'PowerState/starting')
        self.cmd('vmss stop --resource-group {} --name {} --instance-ids *'.format(self.resource_group, self.ss_name))
        self._check_vms_power_state('PowerState/stopped')
        self.cmd('vmss start --resource-group {} --name {} --instance-ids *'.format(self.resource_group, self.ss_name))
        self._check_vms_power_state('PowerState/running', 'PowerState/starting')
        self.cmd('vmss deallocate --resource-group {} --name {} --instance-ids *'.format(self.resource_group, self.ss_name))
        self._check_vms_power_state('PowerState/deallocated')
        self.cmd('vmss delete-instances --resource-group {} --name {} --instance-ids *'.format(self.resource_group, self.ss_name))
        self.cmd('vmss list-instances --resource-group {} --name {}'.format(self.resource_group, self.ss_name))


class VMSSCustomDataScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMSSCustomDataScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_custom_data')

    def test_vmss_create_custom_data(self):
        self.execute()

    def body(self):
        vmss_name = 'vmss-custom-data'

        self.cmd('vmss create -n {0} -g {1} --image Debian --admin-username deploy --ssh-key-value \'{2}\' '
                 '--custom-data \'#cloud-config\nhostname: myVMhostname\' '
                 .format(vmss_name, self.resource_group, TEST_SSH_KEY_PUB))

        # custom data is write only, hence we have no automatic way to cross check. Here we just verify VM was provisioned
        self.cmd('vmss show -n {} -g {}'.format(vmss_name, self.resource_group), [
            JMESPathCheck('provisioningState', 'Succeeded'),
        ])


class VMSSNicScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMSSNicScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_nics')
        self.vmss_name = 'vmss1'
        self.instance_id = 0

    def test_vmss_nics(self):
        self.execute()

    def set_up(self):
        super(VMSSNicScenarioTest, self).set_up()
        self.cmd('vmss create -g {} -n {} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter'.format(self.resource_group, self.vmss_name))

    def body(self):
        self.cmd('vmss nic list -g {} --vmss-name {}'.format(self.resource_group, self.vmss_name), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        nic_list = self.cmd('vmss nic list-vm-nics -g {} --vmss-name {} --instance-id {}'.format(self.resource_group, self.vmss_name, self.instance_id), checks=[
            JMESPathCheck('type(@)', 'array'),
            JMESPathCheck("length([?resourceGroup == '{}']) == length(@)".format(self.resource_group), True)
        ])
        nic_name = nic_list[0].get('name')
        self.cmd('vmss nic show --resource-group {} --vmss-name {} --instance-id {} -n {}'.format(self.resource_group, self.vmss_name, self.instance_id, nic_name), checks=[
            JMESPathCheck('type(@)', 'object'),
            JMESPathCheck('name', nic_name),
            JMESPathCheck('resourceGroup', self.resource_group),
        ])


class VMSSCreateIdempotentTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_idempotent')
    def test_vmss_create_idempotent(self, resource_group):
        vmss_name = 'vmss1'

        # run the command twice with the same parameters and verify it does not fail
        self.cmd('vmss create -g {} -n {} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image UbuntuLTS --use-unmanaged-disk'.format(resource_group, vmss_name))
        self.cmd('vmss create -g {} -n {} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image UbuntuLTS --use-unmanaged-disk'.format(resource_group, vmss_name))


class VMSSILBSceanrioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vmss_with_ilb(self, resource_group):
        vmss_name = 'vmss1'
        self.cmd('vmss create -g {} -n {} --admin-username admin123 --admin-password PasswordPassword1! --image centos --instance-count 1 --public-ip-address ""'.format(resource_group, vmss_name))
        # list connection information should fail
        with self.assertRaises(CLIError) as err:
            self.cmd('vmss list-instance-connection-info -g {} -n {}'.format(resource_group, vmss_name))
        self.assertTrue('internal load balancer' in str(err.exception))


@api_version_constraint(ResourceType.MGMT_NETWORK, min_api='2017-08-01')
class VMSSLoadBalancerWithSku(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_lb_sku')
    def test_vmss_lb_sku(self, resource_group):

        kwargs = {
            'rg': resource_group,
            'vmss': 'vmss1',
            'lb': 'lb1',
            'ip': 'pubip1',
            'sku': 'standard',
            'location': 'eastus2'
        }

        self.cmd('vmss create -g {rg} -l {location} -n {vmss} --lb {lb} --lb-sku {sku} --public-ip-address {ip} --image UbuntuLTS --admin-username admin123 --admin-password PasswordPassword1!'.format(**kwargs))
        self.cmd('network lb show -g {rg} -n {lb}'.format(**kwargs), checks=[
            JMESPathCheckV2('sku.name', 'Standard')
        ])
        self.cmd('network public-ip show -g {rg} -n {ip}'.format(**kwargs), checks=[
            JMESPathCheckV2('sku.name', 'Standard'),
            JMESPathCheckV2('publicIpAllocationMethod', 'Static')
        ])


class MSIScenarioTest(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_msi(self, resource_group):
        subscription_id = self.get_subscription_id()

        default_scope = '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)
        vm1 = 'vm1'
        vm1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachines/{}'.format(subscription_id, resource_group, vm1)
        vm2 = 'vm2'
        vm3 = 'vm3'

        # Fixing the role assignment guids so test can run under playback. The assignments will
        # be auto-deleted when the RG gets recycled, so the same ids can be reused.
        guids = [uuid.UUID('88DAAF5A-EA86-4A68-9D45-477538D41732'),
                 uuid.UUID('13ECC8E1-A3AA-40CE-95E9-1313957D6CF3')]
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=guids, autospec=True):
            # create a linux vm with default configuration
            self.cmd('vm create -g {} -n {} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {}'.format(resource_group, vm1, default_scope), checks=[
                JMESPathCheckV2('identity.role', 'Contributor'),
                JMESPathCheckV2('identity.scope', '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)),
                JMESPathCheckV2('identity.port', 50342)
            ])

            self.cmd('vm extension list -g {} --vm-name {}'.format(resource_group, vm1), checks=[
                JMESPathCheckV2('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
                JMESPathCheckV2('[0].settings.port', 50342)
            ])

            # create a windows vm with reader role on the linux vm
            self.cmd('vm create -g {} -n {} --image Win2016Datacenter --assign-identity --scope {} --role reader --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vm2, vm1_id), checks=[
                JMESPathCheckV2('identity.role', 'reader'),
                JMESPathCheckV2('identity.scope', vm1_id),
                JMESPathCheckV2('identity.port', 50342)
            ])

            self.cmd('vm extension list -g {} --vm-name {}'.format(resource_group, vm2), checks=[
                JMESPathCheckV2('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForWindows'),
                JMESPathCheckV2('[0].publisher', 'Microsoft.ManagedIdentity'),
                JMESPathCheckV2('[0].settings.port', 50342)
            ])

            # create a linux vm w/o identity and later enable it
            vm3_result = self.cmd('vm create -g {} -n {} --image debian --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vm3)).get_output_in_json()
            self.assertIsNone(vm3_result.get('identity'))
            self.cmd('vm assign-identity -g {} -n {} --scope {} --role reader --port 50343'.format(resource_group, vm3, vm1_id), checks=[
                JMESPathCheckV2('role', 'reader'),
                JMESPathCheckV2('scope', vm1_id),
                JMESPathCheckV2('port', 50343)
            ])

            self.cmd('vm extension list -g {} --vm-name {}'.format(resource_group, vm3), checks=[
                JMESPathCheckV2('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
                JMESPathCheckV2('[0].publisher', 'Microsoft.ManagedIdentity'),
                JMESPathCheckV2('[0].settings.port', 50343)
            ])

    @ResourceGroupPreparer(random_name_length=20)
    def test_vmss_msi(self, resource_group):
        subscription_id = self.get_subscription_id()

        default_scope = '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)
        vmss1 = 'vmss11'
        vmss1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/virtualMachineScaleSets/{}'.format(subscription_id, resource_group, vmss1)
        vmss2 = 'vmss2'
        vmss3 = 'vmss3'
        # Fixing the role assignment guids so test can run under playback. The assignments will
        # be auto-deleted when the RG gets recycled, so the same ids can be reused.
        guids = [uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C138'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C137'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C136'),
                 uuid.UUID('CD58500A-F421-4815-B5CF-A36A1E16C135')]
        with mock.patch('azure.cli.command_modules.vm.custom._gen_guid', side_effect=guids, autospec=True):
            # create linux vm with default configuration
            self.cmd('vmss create -g {} -n {} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {}'.format(resource_group, vmss1, default_scope), checks=[
                JMESPathCheckV2('vmss.identity.role', 'Contributor'),
                JMESPathCheckV2('vmss.identity.scope', '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)),
                JMESPathCheckV2('vmss.identity.port', 50342)
            ])

            self.cmd('vmss extension list -g {} --vmss-name {}'.format(resource_group, vmss1), checks=[
                JMESPathCheckV2('[0].type', 'ManagedIdentityExtensionForLinux'),
                JMESPathCheckV2('[0].publisher', 'Microsoft.ManagedIdentity'),
                JMESPathCheckV2('[0].settings.port', 50342)
            ])

            # create a windows vm with reader role on the linux vm
            self.cmd('vmss create -g {} -n {} --image Win2016Datacenter --instance-count 1 --assign-identity --scope {} --role reader --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vmss2, vmss1_id), checks=[
                JMESPathCheckV2('vmss.identity.role', 'reader'),
                JMESPathCheckV2('vmss.identity.scope', vmss1_id),
                JMESPathCheckV2('vmss.identity.port', 50342)
            ])
            self.cmd('vmss extension list -g {} --vmss-name {}'.format(resource_group, vmss2), checks=[
                JMESPathCheckV2('[0].type', 'ManagedIdentityExtensionForWindows'),
                JMESPathCheckV2('[0].publisher', 'Microsoft.ManagedIdentity'),
                JMESPathCheckV2('[0].settings.port', 50342)
            ])

            # create a linux vm w/o identity and later enable it
            vmss3_result = self.cmd('vmss create -g {} -n {} --image debian --instance-count 1 --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vmss3)).get_output_in_json()['vmss']
            self.assertIsNone(vmss3_result.get('identity'))

            # skip playing back till the test issue gets addressed https://github.com/Azure/azure-cli/issues/4016
            if self.is_live:
                self.cmd('vmss assign-identity -g {} -n {} --scope "{}" --role reader --port 50343'.format(resource_group, vmss3, vmss1_id), checks=[
                    JMESPathCheckV2('role', 'reader'),
                    JMESPathCheckV2('scope', vmss1_id),
                    JMESPathCheckV2('port', 50343)
                ])

                self.cmd('vmss extension list -g {} --vmss-name {}'.format(resource_group, vmss3), checks=[
                    JMESPathCheckV2('[0].type', 'ManagedIdentityExtensionForLinux'),
                    JMESPathCheckV2('[0].settings.port', 50343)
                ])

    @ResourceGroupPreparer()
    def test_msi_no_scope(self, resource_group):
        vm1 = 'vm1'
        vmss1 = 'vmss1'
        vm2 = 'vm2'
        vmss2 = 'vmss2'

        # create a linux vm with identity but w/o a role assignment (--scope "")
        self.cmd('vm create -g {} -n {} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vm1), checks=[
            JMESPathCheckV2('identity.scope', ''),
            JMESPathCheckV2('identity.port', 50342)
        ])
        # the extension should still get provisioned
        self.cmd('vm extension list -g {} --vm-name {}'.format(resource_group, vm1), checks=[
            JMESPathCheckV2('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
            JMESPathCheckV2('[0].settings.port', 50342)
        ])

        # create a vmss with identity but w/o a role assignment (--scope "")
        self.cmd('vmss create -g {} -n {} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vmss1), checks=[
            JMESPathCheckV2('vmss.identity.scope', ''),
            JMESPathCheckV2('vmss.identity.port', 50342)
        ])

        # the extension should still get provisioned
        self.cmd('vmss extension list -g {} --vmss-name {}'.format(resource_group, vmss1), checks=[
            JMESPathCheckV2('[0].type', 'ManagedIdentityExtensionForLinux'),
            JMESPathCheckV2('[0].settings.port', 50342)
        ])

        # create a vm w/o identity
        self.cmd('vm create -g {} -n {} --image debian --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vm2))
        # assign identity but w/o a role assignment
        self.cmd('vm assign-identity -g {} -n {}'.format(resource_group, vm2), checks=[
            JMESPathCheckV2('scope', ''),
            JMESPathCheckV2('port', 50342)
        ])
        # the extension should still get provisioned
        self.cmd('vm extension list -g {} --vm-name {}'.format(resource_group, vm2), checks=[
            JMESPathCheckV2('[0].virtualMachineExtensionType', 'ManagedIdentityExtensionForLinux'),
            JMESPathCheckV2('[0].settings.port', 50342)
        ])

        self.cmd('vmss create -g {} -n {} --image debian --admin-username admin123 --admin-password PasswordPassword1!'.format(resource_group, vmss2))
        # skip playing back till the test issue gets addressed https://github.com/Azure/azure-cli/issues/4016
        if self.is_live:
            self.cmd('vmss assign-identity -g {} -n {}'.format(resource_group, vmss2), checks=[
                JMESPathCheckV2('scope', ''),
                JMESPathCheckV2('port', 50342)
            ])

            self.cmd('vmss extension list -g {} --vmss-name {}'.format(resource_group, vmss2), checks=[
                JMESPathCheckV2('[0].type', 'ManagedIdentityExtensionForLinux'),
                JMESPathCheckV2('[0].settings.port', 50342)
            ])

    @ResourceGroupPreparer(random_name_length=20, location='westcentralus')
    def test_vm_explicit_msi(self, resource_group):
        emsi = 'id1'
        emsi2 = 'id2'
        vm = 'vm1'
        subscription_id = self.get_subscription_id()
        default_scope = '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)

        # create a managed identity
        emsi_result = self.cmd('identity create -g {} -n {}'.format(resource_group, emsi), checks=[
            JMESPathCheckV2('name', emsi)
        ]).get_output_in_json()
        emsi2_result = self.cmd('identity create -g {} -n {}'.format(resource_group, emsi2)).get_output_in_json()

        # create a vm with system + user assigned identities
        result = self.cmd('vm create -g {} -n {} --image ubuntults --assign-identity {} [system] --role reader --scope {} --generate-ssh-keys'.format(
            resource_group, vm, emsi, default_scope)).get_output_in_json()
        self.assertEqual(result['identity']['externalIdentities'][0].lower(), emsi_result['id'].lower())
        result = self.cmd('vm show -g {} -n {}'.format(resource_group, vm), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 1),
            JMESPathCheckV2('identity.type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi_result['id'].lower())
        # assign a new managed identity
        self.cmd('vm assign-identity -g {} -n {} --identities {}'.format(resource_group, vm, emsi2))
        self.cmd('vm show -g {} -n {}'.format(resource_group, vm), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 2),
        ])
        # remove the 1st user assigned identity
        self.cmd('vm remove-identity -g {} -n {} --identities {}'.format(resource_group, vm, emsi))
        result = self.cmd('vm show -g {} -n {}'.format(resource_group, vm), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 1),
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi2_result['id'].lower())

        # remove the 2nd
        self.cmd('vm remove-identity -g {} -n {} --identities {}'.format(resource_group, vm, emsi2))
        # verify the VM still has the system assigned identity
        result = self.cmd('vm show -g {} -n {}'.format(resource_group, vm), checks=[
            # blocked by https://github.com/Azure/azure-cli/issues/5103
            # JMESPathCheckV2('length(identity.identityIds)', 0)
            JMESPathCheckV2('identity.type', 'SystemAssigned'),
        ])
        pass

    @ResourceGroupPreparer(random_name_length=20, location='westcentralus')
    def test_vmss_explicit_msi(self, resource_group):
        emsi = 'id1'
        emsi2 = 'id2'
        vmss = 'vmss1'
        subscription_id = self.get_subscription_id()
        default_scope = '/subscriptions/{}/resourceGroups/{}'.format(subscription_id, resource_group)

        # create a managed identity
        emsi_result = self.cmd('identity create -g {} -n {}'.format(resource_group, emsi)).get_output_in_json()
        emsi2_result = self.cmd('identity create -g {} -n {}'.format(resource_group, emsi2)).get_output_in_json()

        # create a vmss with system + user assigned identities
        result = self.cmd('vmss create -g {} -n {} --image ubuntults --assign-identity {} [system] --role reader --scope {} --instance-count 1 --generate-ssh-keys'.format(
            resource_group, vmss, emsi, default_scope)).get_output_in_json()
        self.assertEqual(result['vmss']['identity']['externalIdentities'][0].lower(), emsi_result['id'].lower())

        result = self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 1),
            JMESPathCheckV2('identity.type', 'SystemAssigned, UserAssigned')
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi_result['id'].lower())

        # assign a new managed identity
        self.cmd('vmss assign-identity -g {} -n {} --identities {}'.format(resource_group, vmss, emsi2))
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 2)
        ])

        # update instances
        self.cmd('vmss update-instances -g {} -n {} --instance-ids *'.format(resource_group, vmss))

        # remove the 1st user assigned identity
        self.cmd('vmss remove-identity -g {} -n {} --identities {}'.format(resource_group, vmss, emsi))
        result = self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss), checks=[
            JMESPathCheckV2('length(identity.identityIds)', 1)
        ]).get_output_in_json()
        self.assertEqual(result['identity']['identityIds'][0].lower(), emsi2_result['id'].lower())

        # remove the 2nd
        self.cmd('vmss remove-identity -g {} -n {} --identities {}'.format(resource_group, vmss, emsi2))
        # verify the vmss still has the system assigned identity
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss), checks=[
            # blocked by https://github.com/Azure/azure-cli/issues/5103
            # JMESPathCheckV2('length(identity.identityIds)', 0)
            JMESPathCheckV2('identity.type', 'SystemAssigned'),
        ])


class VMLiveScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging
        vm_name = 'vm123'
        with force_progress_logging() as test_io:
            self.cmd('vm create -g {} -n vm123 --admin-username {} --admin-password PasswordPassword1! --image debian'.format(resource_group, vm_name))

        content = test_io.getvalue()
        # check log has okay format
        lines = content.splitlines()
        for l in lines:
            self.assertTrue(l.split(':')[0] in ['Accepted', 'Succeeded'])
        # spot check we do have relevant messages coming out
        self.assertTrue('Succeeded: {}VMNic (Microsoft.Network/networkInterfaces)'.format(vm_name) in lines)
        self.assertTrue('Succeeded: {} (Microsoft.Compute/virtualMachines)'.format(vm_name) in lines)


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMZoneScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(location='eastus2')
    def test_vm_create_zones(self, resource_group, resource_group_location):
        zones = '2'
        vm_name = 'vm123'
        ip_name = 'vm123ip'
        self.cmd('vm create -g {} -n {} --admin-username clitester --admin-password PasswordPassword1! --image debian --zone {} --public-ip-address {}'.format(resource_group, vm_name, zones, ip_name), checks=[
            JMESPathCheckV2('zones', zones)
        ])
        self.cmd('network public-ip show -g {} -n {}'.format(resource_group, ip_name),
                 checks=JMESPathCheckV2('zones[0]', zones))
        # Test VM's specific table output
        result = self.cmd('vm show -g {} -n {} -otable'.format(resource_group, vm_name))
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, zones]).issubset(table_output))

    @ResourceGroupPreparer(location='eastus2')
    def test_vmss_create_zones(self, resource_group, resource_group_location):
        zones = '2'
        vmss_name = 'vmss123'
        self.cmd('vmss create -g {} -n {} --admin-username clitester --admin-password PasswordPassword1! --image debian --zones {}'.format(resource_group, vmss_name, zones))
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('zones[0]', zones)
        ])
        result = self.cmd('vmss show -g {} -n {} -otable'.format(resource_group, vmss_name))
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, vmss_name, zones]).issubset(table_output))
        result = self.cmd('vmss list -g {} -otable'.format(resource_group, vmss_name))
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group_location, vmss_name, zones]).issubset(table_output))

    @ResourceGroupPreparer(location='eastus2')
    def test_disk_create_zones(self, resource_group, resource_group_location):
        zones = '2'
        disk_name = 'disk123'
        size = 1
        self.cmd('disk create -g {} -n {} --size-gb {} --zone {}'.format(resource_group, disk_name, size, zones), checks=[
            JMESPathCheckV2('zones[0]', zones)
        ])
        self.cmd('disk show -g {} -n {}'.format(resource_group, disk_name), checks=[
            JMESPathCheckV2('zones[0]', zones)
        ])
        result = self.cmd('disk show -g {} -n {} -otable'.format(resource_group, disk_name))
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group, resource_group_location, disk_name, zones, str(size), 'Premium_LRS']).issubset(table_output))
        result = self.cmd('disk list -g {} -otable'.format(resource_group))
        table_output = set(result.output.splitlines()[2].split())
        self.assertTrue(set([resource_group, resource_group_location, disk_name, zones]).issubset(table_output))

    def test_list_skus_contains_zone_info(self):
        from azure_devtools.scenario_tests import LargeResponseBodyProcessor
        large_resp_body = next((r for r in self.recording_processors if isinstance(r, LargeResponseBodyProcessor)), None)
        if large_resp_body:
            large_resp_body._max_response_body = 2048
        # we pick eastus2 as it is one of 3 regions so far with zone support
        location = 'eastus2'
        result = self.cmd('vm list-skus -otable -l {} -otable'.format(location))
        self.assertTrue(next(l for l in result.output.splitlines() if '1,2,3' in l).split()[-1] == '1,2,3')


class VMRunCommandScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_run_command_e2e(self, resource_group, resource_group_location):
        vm = 'test-run-command-vm'
        self.cmd('vm run-command list -l ' + resource_group_location)
        self.cmd('vm run-command show --command-id RunShellScript -l ' + resource_group_location)
        public_ip = self.cmd('vm create -g {} -n {} --image ubuntults --admin-username clitest1 --admin-password Test12345678!!'.format(resource_group, vm)).get_output_in_json()['publicIpAddress']

        self.cmd('vm open-port -g {} -n {} --port 80'.format(resource_group, vm))
        self.cmd('vm run-command invoke -g {} -n{} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"'.format(resource_group, vm))
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx!' in str(r.content))

    @ResourceGroupPreparer()
    def test_run_command_with_parameters(self, resource_group):
        vm = 'test-run-command-vm2'
        self.cmd('vm create -g {} -n {} --image debian --admin-username clitest1 --admin-password Test12345678!!'.format(resource_group, vm))
        self.cmd('vm run-command invoke -g {} -n{} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world'.format(resource_group, vm))


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMSSDiskEncryptionTest(ScenarioTest):
    @ResourceGroupPreparer(location='eastus2euap')  # the feature is only available in canary, should rollout to public soon
    def test_vmss_disk_encryption_e2e(self, resource_group, resource_group_location):
        vault_name = self.create_random_name('vault', 10)
        vmss_name = 'vmss1'
        self.cmd('keyvault create -g {} -n {} --enabled-for-disk-encryption "true"'.format(resource_group, vault_name))
        self.cmd('vmss create -g {} -n {} --image win2016datacenter --instance-count 1 --admin-username clitester1 --admin-password Test123456789!'.format(resource_group, vmss_name))
        self.cmd('vmss encryption enable -g {} -n {} --disk-encryption-keyvault {}'.format(resource_group, vmss_name, vault_name))
        self.cmd('vmss update-instances -g {} -n {}  --instance-ids "*"'.format(resource_group, vmss_name))
        self.cmd('vmss encryption show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('[0].disks[0].statuses[0].code', 'EncryptionState/encrypted')
        ])
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'EnableEncryption'),
            JMESPathCheckV2('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
        ])
        self.cmd('vmss encryption disable -g {} -n {}'.format(resource_group, vmss_name))
        self.cmd('vmss update-instances -g {} -n {}  --instance-ids "*"'.format(resource_group, vmss_name))
        self.cmd('vmss encryption show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('[0].disks[0].statuses[0].code', 'EncryptionState/notEncrypted')
        ])
        self.cmd('vmss show -g {} -n {}'.format(resource_group, vmss_name), checks=[
            JMESPathCheckV2('virtualMachineProfile.extensionProfile.extensions[0].settings.EncryptionOperation', 'DisableEncryption'),
            JMESPathCheckV2('virtualMachineProfile.extensionProfile.extensions[0].settings.VolumeType', 'ALL')
        ])


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMSSRollingUpgrade(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vmss_rolling_upgrade(self, resource_group):
        lb_name = 'lb1'
        probe_name = 'probe1'
        vmss_name = 'vmss1'

        # set up a LB with the probe for rolling upgrade
        self.cmd('network lb create -g {} -n {}'.format(resource_group, lb_name))
        self.cmd('network lb probe create -g {} --lb-name {} -n {} --protocol http --port 80 --path /'.format(resource_group, lb_name, probe_name))
        self.cmd('network lb rule create -g {} --lb-name {} -n rule1 --protocol tcp --frontend-port 80 --backend-port 80 --probe-name {}'.format(resource_group, lb_name, probe_name))
        self.cmd('network lb inbound-nat-pool create -g {} --lb-name {} -n nat-pool1 --backend-port 22 --frontend-port-range-start 50000 --frontend-port-range-end 50119 --protocol Tcp --frontend-ip-name LoadBalancerFrontEnd'.format(resource_group, lb_name))

        # create a scaleset to use the LB, note, we start with the manual mode as we are not done with the setup yet
        self.cmd('vmss create -g {} -n {} --image ubuntults --admin-username clitester1 --admin-password Testqwer1234! --lb {} --health-probe {}'.format(resource_group, vmss_name, lb_name, probe_name))

        # install the web server
        _, settings_file = tempfile.mkstemp()
        with open(settings_file, 'w') as outfile:
            json.dump({
                "commandToExecute": "sudo apt-get install -y nginx",
            }, outfile)
        settings_file = settings_file.replace('\\', '\\\\')
        self.cmd('vmss extension set -g {} --vmss-name {} -n customScript --publisher Microsoft.Azure.Extensions --settings {} --version 2.0'.format(resource_group, vmss_name, settings_file))
        self.cmd('vmss update-instances -g {} -n {} --instance-ids "*"'.format(resource_group, vmss_name))

        # now we are ready for the rolling upgrade mode
        self.cmd('vmss update -g {} -n {} --set upgradePolicy.mode=rolling'.format(resource_group, vmss_name))

        # make sure the web server works
        result = self.cmd('vmss list-instance-connection-info -g {} -n {} -o tsv'.format(resource_group, vmss_name))
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + result.output.split(':')[0])
        self.assertTrue('Welcome to nginx!' in str(r.content))

        # do some rolling upgrade, maybe nonsense, but we need to test the command anyway
        self.cmd('vmss rolling-upgrade start -g {} -n {}'.format(resource_group, vmss_name))
        result = self.cmd('vmss rolling-upgrade get-latest -g {} -n {}'.format(resource_group, vmss_name)).get_output_in_json()
        self.assertTrue(('policy' in result) and ('progress' in result))  # spot check that it is about rolling upgrade

        # 'cancel' should fail as we have no active upgrade to cancel
        self.cmd('vmss rolling-upgrade cancel -g {} -n {}'.format(resource_group, vmss_name), expect_failure=True)


class VMLBIntegrationTesting(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_lb_integration(self, resource_group):
        lb_name = 'lb1'
        vm1 = 'vm1'
        vm2 = 'vm2'
        av_set = 'av1'
        # provision 2 web servers
        self.cmd('vm availability-set create -g {} -n {}'.format(resource_group, av_set))
        self.cmd('vm create -g {} -n {} --image ubuntults --public-ip-address "" --availability-set {} --generate-ssh-keys'.format(resource_group, vm1, av_set))
        self.cmd('vm open-port -g {} -n {} --port 80'.format(resource_group, vm1))
        self.cmd('vm create -g {} -n {} --image ubuntults --public-ip-address "" --availability-set {} --generate-ssh-keys'.format(resource_group, vm2, av_set))
        self.cmd('vm open-port -g {} -n {} --port 80'.format(resource_group, vm2))

        # provision 1 LB
        self.cmd('network lb create -g {} -n {}'.format(resource_group, lb_name))

        # create LB probe and rule
        self.cmd('network lb probe create -g {} --lb-name {} -n probe1 --protocol Http --port 80 --path /'.format(resource_group, lb_name))
        self.cmd('network lb rule create -g {} --lb-name {} -n rule1 --protocol Tcp --frontend-port 80 --backend-port 80'.format(resource_group, lb_name))

        # add 2 vm into BE Pool
        self.cmd('network nic ip-config address-pool add -g {0} --lb-name {1} --address-pool {1}bepool --nic-name {2}VMNic --ip-config-name ipconfig{2}'.format(resource_group, lb_name, vm1))
        self.cmd('network nic ip-config address-pool add -g {0} --lb-name {1} --address-pool {1}bepool --nic-name {2}VMNic --ip-config-name ipconfig{2}'.format(resource_group, lb_name, vm2))

        # Create Inbound Nat Rules so each VM can be accessed through SSH
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n inbound-nat-rule1 --frontend-port 50000 --backend-port 22  --protocol Tcp'.format(resource_group, lb_name))
        self.cmd('network nic ip-config inbound-nat-rule add -g {0} --lb-name {1} --nic-name {2}VMNic --ip-config-name ipconfig{2} --inbound-nat-rule inbound-nat-rule1'.format(resource_group, lb_name, vm1))
        self.cmd('network lb inbound-nat-rule create -g {} --lb-name {} -n inbound-nat-rule2 --frontend-port 50001 --backend-port 22  --protocol Tcp'.format(resource_group, lb_name))
        self.cmd('network nic ip-config inbound-nat-rule add -g {0} --lb-name {1} --nic-name {2}VMNic --ip-config-name ipconfig{2} --inbound-nat-rule inbound-nat-rule2'.format(resource_group, lb_name, vm2))

        # install nginx web servers
        self.cmd('vm run-command invoke -g {} -n {} --command-id RunShellScript --scripts "sudo apt-get install -y nginx"'.format(resource_group, vm1))
        self.cmd('vm run-command invoke -g {} -n {} --command-id RunShellScript --scripts "sudo apt-get install -y nginx"'.format(resource_group, vm2))

        # ensure all pieces are working together
        result = self.cmd('network public-ip show -g {} -n PublicIP{}'.format(resource_group, lb_name)).get_output_in_json()
        pip = result['ipAddress']
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + pip)
        self.assertTrue('Welcome to nginx!' in str(r.content))


class VMScaffoldingTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_create_vm_from_existing_nic(self, resource_group):
        import re
        self.cmd('network public-ip create -g {} -n my-pip'.format(resource_group))
        self.cmd('network vnet create -g {} -n my-vnet --subnet-name my-subnet1'.format(resource_group))
        self.cmd('network nic create -g {} -n my-nic --subnet my-subnet1 --vnet-name my-vnet --public-ip-address my-pip'.format(resource_group))
        self.cmd('network nic ip-config create -n my-ipconfig2 -g {} --nic-name my-nic --private-ip-address-version IPv6'.format(resource_group))
        self.cmd('vm create -g {} -n vm1 --image ubuntults --nics my-nic --generate-ssh-keys'.format(resource_group))
        result = self.cmd('vm show -g {} -n vm1 -d'.format(resource_group)).get_output_in_json()
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['publicIps']))
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['privateIps']))


class VMSecretTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_vm_secret_e2e_test(self, resource_group, resource_group_location):
        vm = 'vm1'
        vault_name = self.create_random_name('vmsecretkv', 20)
        certificate = 'vm-secrt-cert'

        vault_result = self.cmd('keyvault create -g {rg} -n {name} -l {loc} --enabled-for-disk-encryption true --enabled-for-deployment true'.format(
            rg=resource_group,
            name=vault_name,
            loc=resource_group_location
        )).get_output_in_json()
        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')

        self.cmd('vm create -g {} -n {} --image rhel'.format(resource_group, vm))
        time.sleep(60)  # ensure we don't hit the DNS exception (ignored under playback)

        self.cmd('keyvault certificate create --vault-name {} -n {} -p @"{}"'.format(vault_name, certificate, policy_path))
        secret_result = self.cmd('vm secret add -g {} -n {} --keyvault {} --certificate {}'.format(resource_group, vm, vault_name, certificate), checks=[
            JMESPathCheckV2('length([])', 1),
            JMESPathCheckV2('[0].sourceVault.id', vault_result['id']),
            JMESPathCheckV2('length([0].vaultCertificates)', 1),
        ]).get_output_in_json()
        self.assertTrue('https://{}.vault.azure.net/secrets/{}/'.format(vault_name, certificate) in secret_result[0]['vaultCertificates'][0]['certificateUrl'])
        self.cmd('vm secret list -g {} -n {}'.format(resource_group, vm))
        self.cmd('vm secret remove -g {} -n {} --keyvault {} --certificate {}'.format(resource_group, vm, vault_name, certificate))

        self.cmd('vm secret list -g {} -n {}'.format(resource_group, vm), checks=[
            JMESPathCheckV2('length([])', 0)
        ])
# endregion


if __name__ == '__main__':
    unittest.main()
