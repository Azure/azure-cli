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
from azure_devtools.scenario_tests import AllowLargeResponse, record_only
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer)
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

    @AllowLargeResponse()
    def test_vm_images_list_thru_services(self):
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

        self.cmd('vm create -g {rg} -l westus -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password @PasswordPassword1! --public-ip-address-allocation dynamic --authentication-type password --use-unmanaged-disk')

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
        self.cmd('vm create --resource-group {rg} --location {loc} -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 --public-ip-address-allocation {allocation} --authentication-type password --use-unmanaged-disk')
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

        self.cmd('vm create -g {rg} -n {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk')
        self.cmd('vm stop -g {rg} -n {vm}')
        # Should be able to generalize the VM after it has been stopped
        self.cmd('vm generalize -g {rg} -n {vm}', checks=self.is_empty())
        self.cmd('vm show -g {rg} -n {vm}').get_output_in_json()
        self.cmd('vm capture -g {rg} -n {vm} --vhd-name-prefix vmtest',
                 checks=self.is_empty())


class VMVMSSWindowsLicenseTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_windows_license_type')
    def test_vm_vmss_windows_license_type(self, resource_group):

        self.kwargs.update({
            'vm': 'winvm',
            'vmss': 'winvmss'
        })
        self.cmd('vm create -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --use-unmanaged-disk')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('licenseType', 'Windows_Server')
        ])
        self.cmd('vm update -g {rg} -n {vm} --license-type None', checks=[
            self.check('licenseType', 'None')
        ])
        self.cmd('vmss create -g {rg} -n {vmss} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1 --use-unmanaged-disk')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.licenseType', 'Windows_Server')
        ])


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

    @ResourceGroupPreparer(name_prefix='cli_test_vm_with_specialized_unmanaged_disk')
    def test_vm_create_with_unmanaged_data_disks(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1',
            'vm2': 'vm2'
        })

        # create a unmanaged bm with 2 unmanaged disks
        vm_create_cmd = 'vm create -g {rg} -n vm1 --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password'
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
        self.cmd('vm create -g {rg} -n {vm} --admin-username user12 --admin-password testPassword0 --authentication-type password --image UbuntuLTS --no-wait --use-unmanaged-disk',
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
            self.check('platformUpdateDomainCount', 5)  # server defaults to 5
        ])

        # create with explict UD count
        self.cmd('vm availability-set create -g {rg} -n avset2 --platform-fault-domain-count 2 --platform-update-domain-count 2', checks=[
            self.check('platformFaultDomainCount', 2),
            self.check('platformUpdateDomainCount', 2)
        ])
        self.cmd('vm availability-set delete -g {rg} -n avset2')

        self.cmd('vm availability-set update -g {rg} --availability-set-name {availset} -n {availset} --set tags.test=success',
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

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --use-unmanaged-disk')

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
            self.cmd('vm extension delete --resource-group {rg} --vm-name {vm} --name {ext}')
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

    @AllowLargeResponse()
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
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-caching ReadOnly --use-unmanaged-disk')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.adminUsername', '{username}'),
            self.check('osProfile.computerName', '{vm}'),
            self.check('osProfile.linuxConfiguration.disablePasswordAuthentication', True),
            self.check('osProfile.linuxConfiguration.ssh.publicKeys[0].keyData', '{ssh_key}')
        ])

        # test for idempotency--no need to reverify, just ensure the command doesn't fail
        self.cmd('vm create --resource-group {rg} --admin-username {username} --name {vm} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --data-disk-caching ReadOnly --use-unmanaged-disk')


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

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --nics nic1 nic2 nic3 nic4 --admin-username user11 --size Standard_DS3 --ssh-key-value \'{ssh_key}\' --use-unmanaged-disk')
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

        self.cmd('vm create -n {vm} -g {rg} --image Debian --availability-set {quotes} --nsg {quotes} --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --location {loc} --admin-username user11 --use-unmanaged-disk')

        self.cmd('vm show -n {vm} -g {rg}', checks=[
            self.check('availabilitySet', None),
            self.check('length(tags)', 0),
            self.check('location', '{loc}')
        ])
        self.cmd('network public-ip show -n {vm}PublicIP -g {rg}',
                 expect_failure=True)


class VMBootDiagnostics(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_diagnostics')
    @StorageAccountPreparer(name_prefix='clitestbootdiag')
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
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username user11 --admin-password testPassword0 --boot-diagnostics-storage {sa} --use-unmanaged-disk')
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
            'pub': 'Microsoft.Azure.NetworkWatcher',
            'ext': 'NetworkWatcherAgentLinux',
            'username': username,
            'config_file': config_file
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0 --instance-count 1 --use-unmanaged-disk')

        try:
            self.cmd('vmss extension set -n {ext} --publisher {pub} --version 1.4  --vmss-name {vmss} --resource-group {rg} --protected-settings "{config_file}"')
            self.cmd('vmss extension show --resource-group {rg} --vmss-name {vmss} --name {ext}', checks=[
                self.check('type(@)', 'object'),
                self.check('name', '{ext}'),
                self.check('publisher', '{pub}')
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

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password TestTest12#$ --use-unmanaged-disk')
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

        self.cmd('vm availability-set create --name {availset} -g {rg} --platform-fault-domain-count 3 --platform-update-domain-count 3')
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

        self.cmd('vm availability-set create --name {availset} -g {rg} --platform-fault-domain-count 3 --platform-update-domain-count 3')
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

        self.cmd('vm create -g {rg} -n {vm} --admin-username {username} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --custom-data \'{custom_data}\' --use-unmanaged-disk')

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

        self.cmd('vmss create --admin-password testPassword0 --name {vmss} -g {rg} --admin-username myadmin --image Win2012R2Datacenter --instance-count {count} --use-unmanaged-disk')

        self.cmd('vmss show --name {vmss} -g {rg}', checks=[
            self.check('virtualMachineProfile.priority', None)
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


class VMSSCreateBalancerOptionsTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_none')
    def test_vmss_create_none_options(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'ssh_key': TEST_SSH_KEY_PUB,
            'quotes': '""' if platform.system() == 'Windows' else "''"
        })
        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --load-balancer {quotes} --admin-username ubuntu --ssh-key-value \'{ssh_key}\' --public-ip-address {quotes} --tags {quotes} --vm-sku Basic_A1 --use-unmanaged-disk')
        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('tags', {}),
            self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations.ipConfigurations.loadBalancerBackendAddressPools', None),
            self.check('sku.name', 'Basic_A1'),
            self.check('sku.tier', 'Basic')
        ])
        self.cmd('vmss update -g {rg} -n {vmss} --set tags.test=success',
                 checks=self.check('tags.test', 'success'))
        self.cmd('network public-ip show -n {vmss}PublicIP -g {rg}',
                 expect_failure=True)

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_w_ag')
    def test_vmss_create_with_app_gateway(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'ssh_key': TEST_SSH_KEY_PUB
        })
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian --admin-username clittester --ssh-key-value '{ssh_key}' --app-gateway apt1 --instance-count 5 --use-unmanaged-disk",
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

        res = self.cmd("vmss create -g {rg} --name {vmss} --validate --image UbuntuLTS --disable-overprovision --instance-count 101 --single-placement-group false "
                       "--admin-username ubuntuadmin --generate-ssh-keys --use-unmanaged-disk").get_output_in_json()
        # Ensure generated template is valid. "Quota Exceeding" is expected on most subscriptions, so we allow that.
        self.assertTrue(not res['error'] or (res['error']['details'][0]['code'] == 'QuotaExceeded'))

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_existing_lb')
    def test_vmss_existing_lb(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'lb': 'lb1'
        })
        self.cmd('network lb create -g {rg} -n {lb} --backend-pool-name test')
        self.cmd('vmss create -g {rg} -n {vmss} --load-balancer {lb} --image UbuntuLTS --admin-username clitester --admin-password TestTest12#$ --use-unmanaged-disk')


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
        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --use-unmanaged-disk', expect_failure=True)

        vault_out = self.cmd('keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')
        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
        self.kwargs['secrets'] = json.dumps(vm_format)

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --use-unmanaged-disk')

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
        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets \'{secrets}\' --use-unmanaged-disk', expect_failure=True)

        vault_out = self.cmd(
            'keyvault create -g {rg} -n {vault} -l {loc} --enabled-for-deployment true --enabled-for-template-deployment true').get_output_in_json()

        time.sleep(60)

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        self.kwargs['secrets'] = self.cmd('vm secret format -s {secret_out} --certificate-store "My"').get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets "{secrets}" --use-unmanaged-disk')

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
            'vault': 'vmcreatelinuxsecret3334',
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

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --admin-username deploy --ssh-key-value \'{ssh_key}\' --secrets \'{secrets}\' --use-unmanaged-disk')

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

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password TestTest12#$ --instance-count {count} --use-unmanaged-disk')

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

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --admin-username deploy --ssh-key-value "{ssh_key}" --custom-data "#cloud-config\nhostname: myVMhostname" --use-unmanaged-disk')

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

        self.cmd('vmss create -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter --use-unmanaged-disk')

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

        self.cmd('vmss create -g {rg} -n {vmss} --admin-username admin123 --admin-password PasswordPassword1! --image centos --instance-count 1 --public-ip-address "" --use-unmanaged-disk')
        # TODO: restore error validation when #5155 is addressed
        # with self.assertRaises(AssertionError) as err:
        self.cmd('vmss list-instance-connection-info -g {rg} -n {vmss}', expect_failure=True)
        # self.assertTrue('internal load balancer' in str(err.exception))


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
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope} --use-unmanaged-disk', checks=[
                self.check('identity.role', 'Contributor'),
                self.check('identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vm create -g {rg} -n {vm2} --image Win2016Datacenter --assign-identity --scope {vm1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk', checks=[
                self.check('identity.role', 'reader'),
                self.check('identity.scope', '{vm1_id}'),
            ])
            uuid.UUID(result.get_output_in_json()['identity']['systemAssignedIdentity'])

            # create a linux vm w/o identity and later enable it
            vm3_result = self.cmd('vm create -g {rg} -n {vm3} --image debian --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk').get_output_in_json()
            self.assertIsNone(vm3_result.get('identity'))
            result = self.cmd('vm identity assign -g {rg} -n {vm3} --scope {vm1_id} --role reader', checks=[
                self.check('role', 'reader'),
                self.check('scope', '{vm1_id}'),
            ])
            uuid.UUID(result.get_output_in_json()['systemAssignedIdentity'])

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
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope} --use-unmanaged-disk', checks=[
                self.check('vmss.identity.role', 'Contributor'),
                self.check('vmss.identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vmss create -g {rg} -n {vmss2} --image Win2016Datacenter --instance-count 1 --assign-identity --scope {vmss1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk', checks=[
                self.check('vmss.identity.role', 'reader'),
                self.check('vmss.identity.scope', '{vmss1_id}'),
            ]).get_output_in_json()
            uuid.UUID(result['vmss']['identity']['systemAssignedIdentity'])

            # create a linux vm w/o identity and later enable it
            result = self.cmd('vmss create -g {rg} -n {vmss3} --image debian --instance-count 1 --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk').get_output_in_json()['vmss']
            self.assertIsNone(result.get('identity'))

            result = self.cmd('vmss identity assign -g {rg} -n {vmss3} --scope "{vmss1_id}" --role reader', checks=[
                self.check('role', 'reader'),
                self.check('scope', '{vmss1_id}'),
            ]).get_output_in_json()
            uuid.UUID(result['systemAssignedIdentity'])

    @ResourceGroupPreparer(name_prefix='cli_test_msi_no_scope')
    def test_msi_no_scope(self, resource_group):

        self.kwargs.update({
            'vm1': 'vm1',
            'vmss1': 'vmss1',
            'vm2': 'vm2',
            'vmss2': 'vmss2',
        })

        # create a linux vm with identity but w/o a role assignment (--scope "")
        self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk', checks=[
            self.check('identity.scope', None),
            self.check('identity.role', None),
        ])

        # create a vmss with identity but w/o a role assignment (--scope "")
        self.cmd('vmss create -g {rg} -n {vmss1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk', checks=[
            self.check('vmss.identity.scope', None),
        ])

        # create a vm w/o identity
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk')
        # assign identity but w/o a role assignment
        self.cmd('vm identity assign -g {rg} -n {vm2}', checks=[
            self.check('scope', None),
        ])

        self.cmd('vmss create -g {rg} -n {vmss2} --image debian --admin-username admin123 --admin-password PasswordPassword1! --use-unmanaged-disk')
        self.cmd('vmss identity assign -g {rg} -n {vmss2}', checks=[
            self.check('scope', None),
        ])


class VMLiveScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_progress')
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging

        self.kwargs.update({'vm': 'vm123'})

        with force_progress_logging() as test_io:
            self.cmd('vm create -g {rg} -n {vm} --admin-username {vm} --admin-password PasswordPassword1! --image debian --use-unmanaged-disk')

        content = test_io.getvalue()
        # check log has okay format
        lines = content.splitlines()
        for l in lines:
            self.assertTrue(l.split(':')[0] in ['Accepted', 'Succeeded'])
        # spot check we do have some relevant progress messages coming out
        # (Note, CLI's progress controller does routine "sleep" before sample the LRO response.
        # This has the consequence that it can't promise each resource's result wil be displayed)
        self.assertTrue('Accepted:'.format(**self.kwargs) in lines)
        self.assertTrue('Succeeded:'.format(**self.kwargs) in lines)


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
        self.cmd('vm create -g {rg} -n {vm1} --image ubuntults --public-ip-address "" --availability-set {avset} --generate-ssh-keys --admin-username ubuntuadmin --use-unmanaged-disk')
        self.cmd('vm open-port -g {rg} -n {vm1} --port 80')
        self.cmd('vm create -g {rg} -n {vm2} --image ubuntults --public-ip-address "" --availability-set {avset} --generate-ssh-keys --admin-username ubuntuadmin --use-unmanaged-disk')
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

        self.cmd('vm create -g {rg} -n {vm} --image rhel --generate-ssh-keys --admin-username rheladmin --use-unmanaged-disk')
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


# endregion


if __name__ == '__main__':
    unittest.main()
