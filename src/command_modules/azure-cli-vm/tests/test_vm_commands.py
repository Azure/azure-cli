# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# AZURE CLI VM TEST DEFINITIONS
import json
import os
import platform
import tempfile
import unittest

import six

from azure.cli.core.util import CLIError
from azure.cli.core.test_utils.vcr_test_base import (VCRTestBase,
                                                     ResourceGroupVCRTestBase,
                                                     JMESPathCheck,
                                                     NoneCheck)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

# pylint: disable=method-hidden
# pylint: disable=line-too-long
# pylint: disable=bad-continuation
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
        nsg_id = self.cmd('vm open-port -g {} -n {} --port * --priority 900'.format(rg, vm))['networkSecurityGroup']['id']
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
        vm1_info = self.cmd('vm show -g {} -n {}'.format(self.resource_group, vm1))
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
        data_disk = self.cmd('disk create -g {} -n {} --size-gb {}'.format(self.resource_group, disk_name, 1), checks=[
            JMESPathCheck('accountType', 'Premium_LRS'),
            JMESPathCheck('diskSizeGb', 1)
        ])
        self.cmd('disk update -g {} -n {} --size-gb {} --sku {}'.format(self.resource_group, disk_name, 10, 'Standard_LRS'), checks=[
            JMESPathCheck('accountType', 'Standard_LRS'),
            JMESPathCheck('diskSizeGb', 10)
        ])

        # create another disk by importing from the disk1
        data_disk2 = self.cmd('disk create -g {} -n {} --source {}'.format(self.resource_group, disk_name2, data_disk['id']))

        # create a snpashot
        os_snapshot = self.cmd('snapshot create -g {} -n {} --size-gb {} --sku {}'.format(
            self.resource_group, snapshot_name, 1, 'Premium_LRS'), checks=[
            JMESPathCheck('accountType', 'Premium_LRS'),
            JMESPathCheck('diskSizeGb', 1)
        ])
        # update the sku
        self.cmd('snapshot update -g {} -n {} --sku {}'.format(self.resource_group, snapshot_name, 'Standard_LRS'), checks=[
            JMESPathCheck('accountType', 'Standard_LRS'),
            JMESPathCheck('diskSizeGb', 1)
        ])

        # create another snapshot by importing from the disk1
        data_snapshot = self.cmd('snapshot create -g {} -n {} --source {} --sku {}'.format(
            self.resource_group, snapshot_name2, disk_name, 'Premium_LRS'))

        # till now, image creation doesn't inspect the disk for os, so the command below should succeed with junk disk
        # pylint: disable=too-many-format-args
        self.cmd('image create -g {} -n {} --source {} --data-disk-sources {} {} {} --os-type Linux'.format(
            self.resource_group, image_name, snapshot_name, disk_name, data_snapshot['id'], data_disk2['id']), checks=[
            JMESPathCheck('storageProfile.osDisk.osType', 'Linux'),
            JMESPathCheck('storageProfile.osDisk.snapshot.id', os_snapshot['id']),
            JMESPathCheck('length(storageProfile.dataDisks)', 3)
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
            self.resource_group, self.vm_name, 'Standard_A4'),
            checks=JMESPathCheck('hardwareProfile.vmSize', 'Standard_A4'))
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


class VMAvailSetScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMAvailSetScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_avail_set')
        self.location = 'westus'
        self.name = 'availset-test'

    def test_vm_availset(self):
        self.execute()

    def body(self):
        self.cmd('vm availability-set create -g {} -n {}'.format(
            self.resource_group, self.name), checks=[
                JMESPathCheck('name', self.name),
                JMESPathCheck('platformFaultDomainCount', 2),
                JMESPathCheck('platformUpdateDomainCount', 5),  # server defaults to 5
                JMESPathCheck('sku.managed', True)
        ])

        # create with explict UD count
        self.cmd('vm availability-set create -g {} -n avset2 --platform-fault-domain-count 2 --platform-update-domain-count 2'.format(
            self.resource_group), checks=[
                JMESPathCheck('platformFaultDomainCount', 2),
                JMESPathCheck('platformUpdateDomainCount', 2),
                JMESPathCheck('sku.managed', True)
        ])
        self.cmd('vm availability-set delete -g {} -n avset2'.format(self.resource_group))

        self.cmd('vm availability-set update -g {} -n {} --set tags.test=success'.format(self.resource_group, self.name),
                 checks=JMESPathCheck('tags.test', 'success'))
        self.cmd('vm availability-set list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('length(@)', 1),
            JMESPathCheck('[0].name', self.name),
        ])
        self.cmd('vm availability-set list-sizes -g {} -n {}'.format(
            self.resource_group, self.name), checks=JMESPathCheck('type(@)', 'array'))
        self.cmd('vm availability-set show -g {} -n {}'.format(
            self.resource_group, self.name), checks=[JMESPathCheck('name', self.name)])
        self.cmd('vm availability-set delete -g {} -n {}'.format(self.resource_group, self.name))
        self.cmd('vm availability-set list -g {}'.format(self.resource_group), checks=[JMESPathCheck('length(@)', 0)])


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


class VMCreateUbuntuScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateUbuntuScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_create_vm_ubuntu')
        self.deployment_name = 'azurecli-test-deployment-vm-create-ubuntu2'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_names = ['cli-test-vm2']
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'

    def test_vm_create_ubuntu(self):
        self.execute()

    def set_up(self):
        super(VMCreateUbuntuScenarioTest, self).set_up()

    def body(self):
        self.cmd('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' --location {location} --data-disk-sizes-gb 1'.format(
            rg=self.resource_group,
            admin=self.admin_username,
            vm_name=self.vm_names[0],
            image=self.vm_image,
            auth_type=self.auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=self.location
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=self.resource_group, vm_name=self.vm_names[0]), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osProfile.adminUsername', self.admin_username),
            JMESPathCheck('osProfile.computerName', self.vm_names[0]),
            JMESPathCheck('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            JMESPathCheck('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', TEST_SSH_KEY_PUB),
            JMESPathCheck('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            JMESPathCheck('storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
        ])


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

    def __init__(self, test_method):
        super(DiagnosticsExtensionInstallTest, self).__init__(__file__, test_method, resource_group='cli_test_vm_vmss_diagnostics_extension')
        self.storage_account = 'clitestdiagextsa20170227'
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
        storage_key = '123'  # use junk keys, do not retrieve real keys which will get into the recording
        _, protected_settings = tempfile.mkstemp()
        with open(protected_settings, 'w') as outfile:
            json.dump({
                "storageAccountName": self.storage_account,
                "storageAccountKey": storage_key,
                "storageAccountEndPoint": "https://{}.blob.core.windows.net/".format(self.storage_account)
            }, outfile)
        protected_settings = protected_settings.replace('\\', '\\\\')

        _, public_settings = tempfile.mkstemp()
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'sample-public.json').replace('\\', '\\\\')
        with open(template_file) as data_file:
            data = json.load(data_file)
        data["storageAccount"] = self.storage_account
        with open(public_settings, 'w') as outfile:
            json.dump(data, outfile)
        public_settings = public_settings.replace('\\', '\\\\')

        checks = [
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].name', "LinuxDiagnostic"),
            JMESPathCheck('virtualMachineProfile.extensionProfile.extensions[0].settings.storageAccount', self.storage_account)
        ]

        self.cmd("vmss diagnostics set -g {} --vmss-name {} --settings {} --protected-settings {}".format(
            self.resource_group, self.vmss, public_settings, protected_settings), checks=checks)

        self.cmd("vmss show -g {} -n {}".format(self.resource_group, self.vmss), checks=checks)

        self.cmd("vm diagnostics set -g {} --vm-name {} --settings {} --protected-settings {}".format(
            self.resource_group, self.vm, public_settings, protected_settings), checks=[
                JMESPathCheck('name', 'LinuxDiagnostic'),
                JMESPathCheck('settings.storageAccount', self.storage_account)
        ])

        self.cmd("vm show -g {} -n {}".format(self.resource_group, self.vm), checks=[
            JMESPathCheck('resources[0].name', 'LinuxDiagnostic'),
            JMESPathCheck('resources[0].settings.storageAccount', self.storage_account)
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
        self.storage_name = 'vcrstorage01234560'
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
        from azure.cli.core.commands.arm import resource_id, is_valid_resource_id
        subscription_id = get_subscription_id()
        rg = self.resource_group

        av_set = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Compute', type='availabilitySets', name=self.availset_name)
        pub_ip = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='publicIpAddresses', name=self.pubip_name)
        subnet = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='virtualNetworks', child_type='subnets', name=self.vnet_name, child_name=self.subnet_name)
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
        self.cmd('vm disk attach -g {} --vm-name {} --disk {} --new --size-gb 1'.format(
            self.resource_group, self.vm_name, disk_name))
        self.cmd('vm disk attach -g {} --vm-name {} --disk {} --new --size-gb 2 --lun 2'.format(
            self.resource_group, self.vm_name, disk_name2))
        self.cmd('vm show -g {} -n {}'.format(self.resource_group, self.vm_name), checks=[
            JMESPathCheck('length(storageProfile.dataDisks)', 2),
            JMESPathCheck('storageProfile.dataDisks[0].name', disk_name),
            JMESPathCheck('storageProfile.dataDisks[1].name', disk_name2),
            JMESPathCheck('storageProfile.dataDisks[1].lun', 2),
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
            JMESPathCheck('storageProfile.dataDisks[0].createOption', 'empty'),
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
                JMESPathCheck('storageProfile.dataDisks[0].createOption', 'attach')
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

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=self.resource_group, vm_name=self.vm_name), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osProfile.customData', 'I2Nsb3VkLWNvbmZpZwpob3N0bmFtZTogbXlWTWhvc3RuYW1l')
        ])


class VMCreateLinuxSecretsScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateLinuxSecretsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_create_vm_linux_secrets')
        self.deployment_name = 'azcli-test-dep-vm-create-linux-secret'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'
        self.vm_name = 'vm-name'
        self.secrets = None
        self.bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}])
        self.vault_name = 'vmcreatelinuxsecret7777'
        self.secret_name = 'mysecret'

    def test_vm_create_linux_secrets(self):
        self.execute()

    def set_up(self):
        super(VMCreateLinuxSecretsScenarioTest, self).set_up()

    def body(self):
        message = 'Secret is missing vaultCertificates array or it is empty at index 0'
        with six.assertRaisesRegex(self, CLIError, message):
            self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' -l {location} --secrets \'{secrets}\''.format(
                rg=self.resource_group,
                admin=self.admin_username,
                image=self.vm_image,
                vm_name=self.vm_name,
                auth_type=self.auth_type,
                ssh_key=TEST_SSH_KEY_PUB,
                location=self.location,
                secrets=self.bad_secrets
            ))

        vault_out = self.cmd('keyvault create -g {rg} -n {name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true'.format(
            rg=self.resource_group,
            name=self.vault_name,
            loc=self.location
        ))

        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(
            self.vault_name,
            policy_path))
        secret_out = self.cmd('keyvault secret list-versions --vault-name {} -n cert1 --query "[?attributes.enabled].id" -o tsv'.format(self.vault_name))
        vm_format = self.cmd('vm format-secret -s {0}'.format(secret_out))

        self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --authentication-type {auth_type} --image {image} --ssh-key-value \'{ssh_key}\' -l {location} --secrets \'{secrets}\''.format(
            rg=self.resource_group,
            admin=self.admin_username,
            image=self.vm_image,
            vm_name=self.vm_name,
            auth_type=self.auth_type,
            ssh_key=TEST_SSH_KEY_PUB,
            location=self.location,
            secrets=json.dumps(vm_format)
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=self.resource_group, vm_name=self.vm_name), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            JMESPathCheck('osProfile.secrets[0].vaultCertificates[0].certificateUrl', secret_out)
        ])


class VMCreateWindowsSecretsScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateWindowsSecretsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_create_vm_windows_secrets')
        self.deployment_name = 'azcli-test-dep-vm-create-win-secret'
        self.admin_username = 'windowsUser'
        self.location = 'westus'
        self.vm_image = 'Win2012R2Datacenter'
        self.vm_name = 'vm-name'
        self.bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': [{'certificateUrl': 'certurl'}]}])
        self.vault_name = 'vmcreatewinsecret7777'
        self.secret_name = 'mysecret'

    def test_vm_create_windows_secrets(self):
        self.execute()

    def set_up(self):
        super(VMCreateWindowsSecretsScenarioTest, self).set_up()

    def body(self):
        message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
                  'vaultCertificate index 0'
        with six.assertRaisesRegex(self, CLIError, message):
            self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {location} --secrets \'{secrets}\''.format(
                rg=self.resource_group,
                admin=self.admin_username,
                image=self.vm_image,
                vm_name=self.vm_name,
                location=self.location,
                secrets=self.bad_secrets
            ))

        vault_out = self.cmd(
            'keyvault create -g {rg} -n {name} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true'.format(
                rg=self.resource_group,
                name=self.vault_name,
                loc=self.location
            ))

        policy_path = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {} -n cert1 -p @"{}"'.format(
            self.vault_name,
            policy_path))

        secret_out = self.cmd('keyvault secret list-versions --vault-name {} -n cert1 --query "[?attributes.enabled].id" -o tsv'.format(self.vault_name))
        vm_format = self.cmd('vm format-secret -s {0} --certificate-store "My"'.format(secret_out))

        self.cmd('vm create -g {rg} -n {vm_name} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {location} --secrets \'{secrets}\''.format(
            rg=self.resource_group,
            admin=self.admin_username,
            image=self.vm_image,
            vm_name=self.vm_name,
            location=self.location,
            secrets=json.dumps(vm_format)
        ))

        self.cmd('vm show -g {rg} -n {vm_name}'.format(rg=self.resource_group, vm_name=self.vm_name), checks=[
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            JMESPathCheck('osProfile.secrets[0].vaultCertificates[0].certificateUrl', secret_out),
            JMESPathCheck('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
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

        self.cmd('vmss show --name {} -g {}'.format(vmss_name, self.resource_group),
                 )

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
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[1].diskSizeGb', 3)
        ])
        self.cmd('vmss disk detach -g {} -n {} --lun 1'.format(self.resource_group, vmss_name))
        self.cmd('vmss show -g {} -n {}'.format(self.resource_group, vmss_name), checks=[
            JMESPathCheck('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].lun', 0),
            JMESPathCheck('virtualMachineProfile.storageProfile.dataDisks[0].diskSizeGb', 1)
        ])


class VMSSCreateNoneOptionsTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMSSCreateNoneOptionsTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_none_options')

    def test_vmss_create_none_options(self):
        self.execute()

    def body(self):
        vmss_name = 'vmss1'

        self.cmd('vmss create -n {0} -g {1} --image Debian --load-balancer {3} --admin-username ubuntu'
                 ' --ssh-key-value \'{2}\' --public-ip-address {3} --tags {3}'
                 .format(vmss_name, self.resource_group, TEST_SSH_KEY_PUB, '""' if platform.system() == 'Windows' else "''"))
        self.cmd('vmss show -n {} -g {}'.format(vmss_name, self.resource_group), [
            JMESPathCheck('availabilitySet', None),
            JMESPathCheck('tags', {}),
            JMESPathCheck('virtualMachineProfile.networkProfile.networkInterfaceConfigurations.ipConfigurations.loadBalancerBackendAddressPools', None)
        ])
        self.cmd('vmss update -g {} -n {} --set tags.test=success'.format(self.resource_group, vmss_name),
                 checks=JMESPathCheck('tags.test', 'success'))
        self.cmd('network public-ip show -n {}PublicIP -g {}'.format(vmss_name, self.resource_group), checks=NoneCheck(), allowed_exceptions='was not found')


class VMSSCreateLinuxSecretsScenarioTest(ResourceGroupVCRTestBase):  # pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMSSCreateLinuxSecretsScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_vmss_create_linux_secrets')
        self.vmss_name = 'vmss1-name'
        self.bad_secrets = json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}])
        self.vault_name = 'vmcreatelinuxsecret3333'
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
        self.natpool_name = 'mynatpool'

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
                 ' --nat-pool-name {} --use-unmanaged-disk'
                 .format(os_disk_name, self.vnet_name, self.subnet_name, sku_name, container_name,
                         self.resource_group, vmss_name, self.lb_name, TEST_SSH_KEY_PUB,
                         self.bepool_name, self.natpool_name))
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
        self.natpool_name = 'mynatpool'

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
        from azure.cli.core.commands.arm import resource_id, is_valid_resource_id
        subscription_id = get_subscription_id()
        rg = self.resource_group
        vmss_name = 'vrfvmss'
        os_disk_name = 'vrfosdisk'
        container_name = 'vrfcontainer'
        sku_name = 'Standard_A3'

        subnet = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='virtualNetworks', child_type='subnets', name=self.vnet_name, child_name=self.subnet_name)
        lb = resource_id(subscription=subscription_id, resource_group=rg, namespace='Microsoft.Network', type='loadBalancers', name=self.lb_name)

        assert is_valid_resource_id(subnet)
        assert is_valid_resource_id(lb)

        self.cmd('vmss create --image CentOS --os-disk-name {} --admin-username ubuntu'
                 ' --subnet {} -l "West US" --vm-sku {}'
                 ' --storage-container-name {} -g {} --name {} --load-balancer {}'
                 ' --ssh-key-value \'{}\' --backend-pool-name {}'
                 ' --nat-pool-name {} --use-unmanaged-disk'
                 .format(os_disk_name, subnet, sku_name, container_name,
                         self.resource_group, vmss_name, lb, TEST_SSH_KEY_PUB,
                         self.bepool_name, self.natpool_name))
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

        self.cmd('vmss show -n {} -g {}'.format(vmss_name, self.resource_group), [
            JMESPathCheck('provisioningState', 'Succeeded'),
            JMESPathCheck('virtualMachineProfile.osProfile.customData', 'I2Nsb3VkLWNvbmZpZwpob3N0bmFtZTogbXlWTWhvc3RuYW1l')
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

# endregion


if __name__ == '__main__':
    unittest.main()
