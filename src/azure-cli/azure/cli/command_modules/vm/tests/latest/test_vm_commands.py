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

from azure.cli.testsdk.exceptions import JMESPathCheckAssertionError
from knack.util import CLIError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, record_only, live_only
from azure.cli.core.azclierror import ArgumentUsageError, RequiredArgumentMissingError, MutuallyExclusiveArgumentError
from azure.cli.core.profiles import ResourceType
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest, api_version_constraint,
    StorageAccountPreparer, JMESPathCheck, StringContainCheck, VirtualNetworkPreparer, KeyVaultPreparer)
from azure.cli.testsdk.constants import AUX_SUBSCRIPTION, AUX_TENANT
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

    @AllowLargeResponse()
    def test_vm_images_list_thru_services_edge_zone(self):
        result = self.cmd('vm image list --edge-zone microsoftlosangeles1 --offer CentOs --publisher OpenLogic --sku 7.7 -o tsv --all').output
        assert result.index('7.7') >= 0


class VMOpenPortTest(ScenarioTest):

    @record_only()
    @ResourceGroupPreparer(name_prefix='cli_test_open_port')
    def test_vm_open_port(self, resource_group):

        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -l westus -n {vm} --admin-username ubuntu --image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password @PasswordPassword1! --public-ip-address-allocation dynamic --authentication-type password --nsg-rule NONE')

        # min params - test list of ports
        self.kwargs['nsg_list_id'] = self.cmd('vm open-port -g {rg} -n {vm} --port 555,556,557-559 --priority 800').get_output_in_json()['id']
        self.kwargs['nsg_list'] = os.path.split(self.kwargs['nsg_list_id'])[1]
        self.cmd('network nsg show -g {rg} -n {nsg_list}',
                 checks=self.check("length(securityRules[?name == 'open-port-555_556_557-559'])", 1))

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


    def test_vm_image_list_offers_edge_zone(self):
        self.kwargs.update({
            'loc': 'westus',
            'pub': 'OpenLogic',
            'edge_zone': 'microsoftlosangeles1'
        })

        result = self.cmd('vm image list-offers --location {loc} --publisher {pub} --edge-zone {edge_zone}').get_output_in_json()
        self.assertTrue(len(result) > 0)
        self.assertTrue([i for i in result if i['extendedLocation']['name'] == self.kwargs['edge_zone']])
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

    @AllowLargeResponse()
    def test_vm_image_list_publishers_edge_zone(self):
        self.kwargs.update({
            'loc': 'westus',
            'edge_zone': 'microsoftlosangeles1'
        })

        result = self.cmd('vm image list-publishers --location {loc} --edge-zone {edge_zone}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?location == '{loc}']) == length(@)", True),
        ]).get_output_in_json()
        self.assertTrue([i for i in result if i['extendedLocation']['name'] == self.kwargs['edge_zone']])


class VMImageListSkusScenarioTest(ScenarioTest):

    def test_vm_image_list_skus(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'Canonical',
            'offer': 'UbuntuServer'
        })

        result = self.cmd("vm image list-skus --location {loc} -p {pub} --offer {offer} --query \"length([].id.contains(@, '/Publishers/{pub}/ArtifactTypes/VMImage/Offers/{offer}/Skus/'))\"").get_output_in_json()
        self.assertTrue(result > 0)


    def test_vm_image_list_skus_edge_zone(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'OpenLogic',
            'offer': 'CentOs',
            'edge_zone': 'microsoftlosangeles1'
        })

        result = self.cmd('vm image list-skus --location {loc} --edge-zone {edge_zone} --offer {offer} --publisher {pub} --edge-zone {edge_zone}', checks=[
            self.check('type(@)', 'array'),
            self.check("length([?location == '{loc}']) == length(@)", True),
        ]).get_output_in_json()
        self.assertTrue(len(result) > 0)
        self.assertTrue([i for i in result if i['extendedLocation']['name'] == self.kwargs['edge_zone']])


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


    def test_vm_image_show_edge_zone(self):

        self.kwargs.update({
            'loc': 'westus',
            'pub': 'OpenLogic',
            'offer': 'CentOs',
            'sku': '7.7',
            'edge_zone': 'microsoftlosangeles1',
            'ver': '7.7.2021020400'
        })

        self.cmd('vm image show --offer {offer} --publisher {pub} --sku {sku} --version {ver} -l {loc} --edge-zone {edge_zone}', checks=[
            self.check('type(@)', 'object'),
            self.check('location', '{loc}'),
            self.check('name', '{ver}'),
            self.check("contains(id, '/Publishers/{pub}/ArtifactTypes/VMImage/Offers/{offer}/Skus/{sku}/Versions/{ver}')", True),
            self.check('extendedLocation.name', '{edge_zone}'),
            self.check('extendedLocation.type', 'EdgeZone')
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
            self.check('hyperVGeneration', 'V1')
        ])
        # Create image from vm id
        self.cmd('image create -g {rg} -n {image2} --source {vm_id}', checks=[
            self.check("sourceVirtualMachine.id", '{vm_id}'),
            self.check("storageProfile.osDisk.managedDisk", None),
            self.check('hyperVGeneration', 'V1')
        ])
        # Create image from disk id
        self.cmd('image create -g {rg} -n {image3} --source {os_disk_id} --os-type linux --hyper-v-generation "V1"', checks=[
            self.check("sourceVirtualMachine", None),
            self.check("storageProfile.osDisk.managedDisk.id", '{os_disk_id}'),
            self.check('hyperVGeneration', 'V1')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_custom_image_mgmt_')
    def test_vm_custom_image_management(self, resource_group):
        self.kwargs.update({
            'vm1':'vm1',
            'vm2':'vm2',
            'image1':'myImage1',
            'image2':'myImage2'
        })

        vm1 = self.cmd('vm create -g {rg} -n {vm1} --admin-username theuser --image centos --admin-password testPassword0 --authentication-type password --nsg-rule NONE').get_output_in_json()
        self.cmd('vm deallocate -g {rg} -n {vm1}')
        self.cmd('vm generalize -g {rg} -n {vm1}')    

        self.cmd('image create -g {rg} -n {image1} --source {vm1}')

        self.cmd('image list -g {rg}', checks=self.check('length(@)', 1))
        self.cmd('image update -n {image1} -g {rg} --tags foo=bar', checks=self.check('tags.foo', 'bar'))
        self.cmd('image delete -n {image1} -g {rg}')
        self.cmd('image list -g {rg}', checks=self.check('length(@)', 0))


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
        self.cmd('vm unmanaged-disk list -g {rg} --vm-name {vm}', checks=self.check('length(@)', 2))
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


class VMRedeployTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_vm_redeploy_')
    def test_vm_redeploy(self, resource_group):
        self.kwargs.update({
            'vm':'myvm'
        })        

        self.cmd('vm create -g {rg} -n {vm} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm reapply -n {vm} -g {rg}')
        self.cmd('vm redeploy -n {vm} -g {rg}')


class VMConvertTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='test_vm_convert_')
    def test_vm_convert(self, resource_group):
        self.kwargs.update({
            'vm':'myvm'
        })

        self.cmd('vm create -g {rg} -n {vm} --image debian --use-unmanaged-disk --admin-username ubuntu --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm unmanaged-disk attach -g {rg} --vm-name {vm} --new --size-gb 1')

        output = self.cmd('vm unmanaged-disk list --vm-name {vm} -g {rg}').get_output_in_json()
        self.assertFalse(output[0]['managedDisk'])
        self.assertTrue(output[0]['vhd'])

        self.cmd('vm deallocate -n {vm} -g {rg}')
        self.cmd('vm convert -n {vm} -g {rg}')
        
        converted = self.cmd('vm unmanaged-disk list --vm-name {vm} -g {rg}').get_output_in_json()
        self.assertTrue(converted[0]['managedDisk'])
        self.assertFalse(converted[0]['vhd'])


class TestSnapShotAccess(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='test_snapshot_access_')
    def test_snapshot_access(self, resource_group):
        self.kwargs.update({
            'snapshot':'snapshot'
        })
        
        self.cmd('snapshot create -n {snapshot} -g {rg} --size-gb 1', checks=self.check('diskState', 'Unattached'))
        self.cmd('snapshot grant-access --duration-in-seconds 600 -n {snapshot} -g {rg}')
        self.cmd('snapshot show -n {snapshot} -g {rg}', checks=self.check('diskState', 'ActiveSAS'))
        self.cmd('snapshot revoke-access -n {snapshot} -g {rg}')
        self.cmd('snapshot show -n {snapshot} -g {rg}', checks=self.check('diskState', 'Unattached'))


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
        self.cmd('snapshot create -g {rg} -n {os_snapshot} --source {origin_os_disk} --no-wait')
        self.cmd('disk create -g {rg} -n {os_disk} --source {os_snapshot} --no-wait')
        self.cmd('snapshot create -g {rg} -n {data_snapshot} --source {origin_data_disk} --no-wait')
        self.cmd('disk create -g {rg} -n {data_disk} --source {data_snapshot} --no-wait')

        self.cmd('snapshot wait --created -g {rg} -n {os_snapshot}')
        self.cmd('disk wait --created -g {rg} -n {os_disk}')
        self.cmd('snapshot wait --created -g {rg} -n {data_snapshot}')
        self.cmd('disk wait --created -g {rg} -n {data_disk}')

        # rebuild a new vm
        # (os disk can be resized)
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk} --os-disk-delete-option Delete '
                 '--attach-data-disks {data_disk} --data-disk-delete-option Detach --data-disk-sizes-gb 3 '
                 '--os-disk-size-gb 100 --os-type linux --nsg-rule NONE',
                 checks=self.check('powerState', 'VM running'))
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check('length(storageProfile.dataDisks)', 2),
            self.check('storageProfile.dataDisks[0].diskSizeGb', 3),
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('storageProfile.dataDisks[0].deleteOption', 'Detach'),
            self.check('storageProfile.dataDisks[1].deleteOption', 'Detach'),
            self.check('storageProfile.osDisk.diskSizeGb', 100),
            self.check('storageProfile.osDisk.deleteOption', 'Delete')
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

    @ResourceGroupPreparer()
    def test_vm_create_data_disk_delete_option(self, resource_group):
        self.cmd('vm create -n Delete_CLI1 -g {rg} --image RedHat:RHEL:7-RAW:7.4.2018010506 -l northeurope '
                 '--size Standard_E8as_v4 --generate-ssh-keys --public-ip-address "" --os-disk-size-gb 64 '
                 '--data-disk-sizes-gb 200 --data-disk-delete-option Delete --admin-username vmtest',
                 checks=self.check('powerState', 'VM running'))
        result = self.cmd('vm show -g {rg} -n Delete_CLI1').get_output_in_json()
        self.assertEqual(result['storageProfile']['dataDisks'][0]['deleteOption'], 'Delete')

        # creating a vm
        self.cmd(
            'vm create -g {rg} -n vm1 --image centos --admin-username centosadmin --admin-password testPassword0 --authentication-type password --data-disk-sizes-gb 2 --nsg-rule NONE --admin-username vmtest')
        result = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()

        self.kwargs.update({
            'origin_os_disk': result['storageProfile']['osDisk']['name'],
            'origin_data_disk': result['storageProfile']['dataDisks'][0]['name'],
            # snapshot the os & data disks
            'os_snapshot': 'oSnapshot',
            'os_disk': 'sDisk',
            'data_snapshot': 'dSnapshot',
            'data_disk': 'dDisk',
            'data_disk2': 'dDisk2'
        })
        self.cmd('snapshot create -g {rg} -n {os_snapshot} --source {origin_os_disk}')
        self.cmd('disk create -g {rg} -n {os_disk} --source {os_snapshot}')
        self.cmd('snapshot create -g {rg} -n {data_snapshot} --source {origin_data_disk}')
        self.cmd('disk create -g {rg} -n {data_disk} --source {data_snapshot}')
        self.cmd('disk create -g {rg} -n {data_disk2} --source {data_snapshot}')

        # rebuild a new vm
        # (os disk can be resized)
        self.cmd('vm create -g {rg} -n vm2 --attach-os-disk {os_disk} --os-disk-delete-option Delete '
                 '--attach-data-disks {data_disk} {data_disk2} --data-disk-delete-option {data_disk}=Delete {data_disk2}=Detach '
                 '--os-disk-size-gb 100 --os-type linux --nsg-rule NONE',
                 checks=self.check('powerState', 'VM running'))
        self.cmd('vm show -g {rg} -n vm2', checks=[
            self.check('length(storageProfile.dataDisks)', 2),
            self.check('storageProfile.dataDisks[0].deleteOption', 'Delete'),
            self.check('storageProfile.dataDisks[1].deleteOption', 'Detach'),
        ])


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

    @ResourceGroupPreparer(name_prefix='cli_test_vm_snapshot_copy_start_')
    def test_vm_snapshot_copy_start_detection(self, resource_group):
        self.kwargs.update({
            'disk': self.create_random_name('testdisk-', length=24),
            'snapshot1': self.create_random_name('testsnap1-', length=24),
            'snapshot2': self.create_random_name('testsnap2-', length=24)
        })

        self.cmd('disk create -g {rg} -n {disk} --size-gb 10 -l westus')
        # in the same region, it should default copyStart as false
        self.cmd('snapshot create -g {rg} -n {snapshot1} --source {disk}',
                 checks=[self.check('creationData.createOption', 'Copy')])
        # in different region, it should default copyStart as True
        # TODO: should not throw exception after feature GA
        from azure.core.exceptions import ResourceExistsError
        with self.assertRaisesRegex(ResourceExistsError, 'CopyStart creation is not supported for this subscription'):
            self.cmd('snapshot create -g {rg} -n {snapshot2} --source {disk} -l eastus')

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
            self.check('diskMBpsReadOnly', 30)
        ])

        self.cmd('disk update -g {rg} -n {disk1} --disk-iops-read-only 250 --disk-mbps-read-only 40', checks=[
            self.check('diskIopsReadOnly', 250),
            self.check('diskMBpsReadOnly', 40)
        ])

        self.cmd('disk create -g {rg} -n {disk2} --image-reference {image}', checks=[
            self.check('creationData.imageReference.id', '{image}')
        ])

        self.cmd('disk create -g {rg} -n {disk3} --image-reference Canonical:UbuntuServer:18.04-LTS:18.04.202002180', checks=[
            self.check('creationData.imageReference.id', '{image}')
        ])

        self.cmd('sig create -g {rg} --gallery-name {g1}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {g1} --gallery-image-definition image --os-type linux -p publisher1 -f offer1 -s sku1 --features "IsAcceleratedNetworkSupported=true" --hyper-v-generation V2', checks=[
            self.check('features[0].name', 'IsAcceleratedNetworkSupported'),
            self.check('features[0].value', 'true', False)
        ])
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

        self.cmd('disk update -g {rg} -n {disk6} --max-shares 1', checks=[
            self.check('maxShares', 1)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_create_disk_from_diff_gallery_image_version_', location='westus')
    def test_create_disk_from_diff_gallery_image_version(self):
        self.kwargs.update({
            'location': 'westus',
            'vm': 'vm1',
            'gallery1': self.create_random_name('gallery1', 16),
            'gallery2': self.create_random_name('gallery2', 16),
            'image1': 'image1',
            'image2': 'image2',
            'version': '1.1.2',
            'disk1': 'disk1',
            'disk2': 'disk2',
            'disk3': 'disk3',
            'subId': '0b1f6471-1bf0-4dda-aec3-cb9272f09590',
            'tenantId': '54826b22-38d6-4fb2-bad9-b7b93a3e9c5a'
        })

        self.kwargs['vm_id'] = \
            self.cmd('vm create -g {rg} -n {vm} --image debian --data-disk-sizes-gb 10 --admin-username clitest1 '
                     '--generate-ssh-key --nsg-rule NONE').get_output_in_json()['id']
        time.sleep(70)

        self.cmd('sig create -g {rg} --gallery-name {gallery1} --permissions community --publisher-uri publisher1 '
                 '--publisher-email test@microsoft.com --eula eula1 --public-name-prefix name1')
        self.cmd('sig share enable-community -g {rg} -r {gallery1}')

        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery1} --gallery-image-definition {image1} '
                 '--os-type linux --os-state Specialized -p publisher1 -f offer1 -s sku1')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery1} --gallery-image-definition {image1} '
                 '--gallery-image-version {version} --virtual-machine {vm_id}')

        self.kwargs['public_name'] = self.cmd('sig show --gallery-name {gallery1} --resource-group {rg} --select Permissions', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('length(sharingProfile.communityGalleryInfo.publicNames)', '1')
        ]).get_output_in_json()['sharingProfile']['communityGalleryInfo']['publicNames'][0]
        community_gallery_image_version = self.cmd(
            'sig image-version show-community --gallery-image-definition {image1} --public-gallery-name {public_name} '
            '--location {location} --gallery-image-version {version}').get_output_in_json()['uniqueId']
        self.kwargs.update({'community_gallery_image_version': community_gallery_image_version})

        # test creating disk from community gallery image version
        self.cmd('disk create -g {rg} -n {disk1} --gallery-image-reference {community_gallery_image_version}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('creationData.galleryImageReference.communityGalleryImageId', '{community_gallery_image_version}')
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery1} -g {rg}')
        self.cmd('sig show --gallery-name {gallery1} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
        ])

        self.cmd('sig create -g {rg} --gallery-name {gallery2} --permissions groups')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery2} --gallery-image-definition {image2} '
                 '--os-type linux --os-state Specialized -p publisher1 -f offer1 -s sku1')

        compute_gallery_image_version = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery2} --gallery-image-definition {image2} '
            '--gallery-image-version {version} --virtual-machine {vm_id}',
            checks=[self.check('provisioningState', 'Succeeded')]).get_output_in_json()['id']
        self.kwargs.update({'compute_gallery_image_version': compute_gallery_image_version})

        # test creating disk from compute gallery image version
        self.cmd('disk create -g {rg} -n {disk2} --gallery-image-reference {compute_gallery_image_version}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('creationData.galleryImageReference.id', '{compute_gallery_image_version}')
        ])

        unique_name = self.cmd('sig show --gallery-name {gallery2} --resource-group {rg} --select Permissions') \
            .get_output_in_json()['identifier']['uniqueName']
        self.kwargs.update({'unique_name': unique_name})

        self.cmd('sig share add --gallery-name {gallery2} -g {rg} --subscription-ids {subId} --tenant-ids {tenantId}')
        shared_gallery_image_version = \
            self.cmd('sig image-version show-shared --gallery-image-definition {image2} --gallery-unique-name '
                     '{unique_name} --location {location} --gallery-image-version {version}') \
                .get_output_in_json()['uniqueId']
        self.kwargs.update({'shared_gallery_image_version': shared_gallery_image_version})

        # test creating disk from invalid gallery image version
        self.kwargs.update({'invalid_gallery_image_version': shared_gallery_image_version.replace('SharedGalleries', 'Shared')})
        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('disk create -g {rg} -n {disk3} --gallery-image-reference {invalid_gallery_image_version}')

        # test creating disk from shared gallery image version
        self.cmd('disk create -g {rg} -n {disk3} --gallery-image-reference {shared_gallery_image_version}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('creationData.galleryImageReference.sharedGalleryImageId', '{shared_gallery_image_version}')
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery2} -g {rg}')
        self.cmd('sig show --gallery-name {gallery2} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
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

    @AllowLargeResponse()
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
        self.cmd('vm create --resource-group {rg} --location {loc} --name {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --tags firsttag=1 secondtag=2 thirdtag --nsg {nsg} --public-ip-address {ip} --vnet-name {vnet} --storage-account {sa} --use-unmanaged-disk --nsg-rule NONE')

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
        for i in range(5):
            try:
                self._check_vm_power_state('PowerState/running')
                break
            except JMESPathCheckAssertionError:
                time.sleep(30)
        self.cmd('vm restart --resource-group {rg} --name {vm} --force')
        for i in range(5):
            try:
                self._check_vm_power_state('PowerState/running')
                break
            except JMESPathCheckAssertionError:
                time.sleep(30)
        self.cmd('vm deallocate --resource-group {rg} --name {vm}')
        self._check_vm_power_state('PowerState/deallocated')
        self.cmd('vm resize -g {rg} -n {vm} --size Standard_DS2_v2',
                 checks=self.check('hardwareProfile.vmSize', 'Standard_DS2_v2'))
        self.cmd('vm delete --resource-group {rg} --name {vm} --yes')
        # Expecting no results
        self.cmd('vm list --resource-group {rg}', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_vm_user_update_win_')
    def test_vm_user_update_win(self, resource_group):
        self.cmd('vm create -g {rg} -n vm --image Win2022Datacenter --admin-username AzureUser --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm user update -g {rg} -n vm --username AzureUser --password testPassword1')

    @ResourceGroupPreparer(name_prefix='cli_test_vm_size_properties')
    def test_vm_size_properties(self, resource_group):
        self.kwargs.update({
            'vm': self.create_random_name('vm-', 10),
            'vmss': self.create_random_name('vmss', 10)
        })

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --size Standard_D2s_v3 --v-cpus-available 1 --v-cpus-per-core 1 --admin-username vmtest --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {vm} ', checks=[
            self.check('hardwareProfile.vmSizeProperties.vCpusAvailable', 1),
            self.check('hardwareProfile.vmSizeProperties.vCpusPerCore', 1)
        ])
        self.cmd('vm update -g {rg} -n {vm} --v-cpus-available 2 --v-cpus-per-core 2', checks=[
            self.check('hardwareProfile.vmSizeProperties.vCpusAvailable', 2),
            self.check('hardwareProfile.vmSizeProperties.vCpusPerCore', 2)
        ])

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --vm-sku Standard_D2s_v3 --v-cpus-available 1 --v-cpus-per-core 1 --admin-username vmtest --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {vmss} ', checks=[
            self.check('virtualMachineProfile.hardwareProfile.vmSizeProperties.vCpusAvailable', 1),
            self.check('virtualMachineProfile.hardwareProfile.vmSizeProperties.vCpusPerCore', 1)
        ])
        self.cmd('vmss update -g {rg} -n {vmss} --v-cpus-available 2 --v-cpus-per-core 2', checks=[
            self.check('virtualMachineProfile.hardwareProfile.vmSizeProperties.vCpusAvailable', 2),
            self.check('virtualMachineProfile.hardwareProfile.vmSizeProperties.vCpusPerCore', 2)
        ])


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
        self.cmd('vm create --resource-group {rg} --name {vm1} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Regular --nsg-rule NONE')
        self.cmd('vm simulate-eviction --resource-group {rg} --name {vm1}', expect_failure=True)

        # simulate-eviction on a Spot VM with Deallocate policy, expect VM to be deallocated
        self.cmd('vm create --resource-group {rg} --name {vm2} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Spot --eviction-policy Deallocate --nsg-rule NONE')
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
        self.cmd('vm create --resource-group {rg} --name {vm3} --admin-username azureuser --admin-password testPassword0 --authentication-type password --location {loc} --image Centos --priority Spot --eviction-policy Delete --nsg-rule NONE')
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
        time.sleep(30)
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

    @AllowLargeResponse(size_kb=99999)
    def test_list_compute_skus_partially_unavailable(self):
        result = self.cmd('vm list-skus -l eastus --query "[?name==\'Standard_M64m\']"').get_output_in_json()
        self.assertTrue(result and result[0]["restrictions"] and result[0]["restrictions"][0]["reasonCode"] == 'NotAvailableForSubscription')


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
        self.cmd('vm extension set -n {ext} --publisher {pub} --version 1.2 --vm-name {vm} --resource-group {rg} --protected-settings "{config}" --force-update --enable-auto-upgrade false --no-wait')
        self.cmd('vm extension wait --created -n {ext} -g {rg} --vm-name {vm}')
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
            self.check('enableAutomaticUpgrade', False)
        ]).get_output_in_json()
        uuid.UUID(result['forceUpdateTag'])
        self.cmd('vm extension show --resource-group {rg} --vm-name {vm} --name {ext} --instance-view', checks=[
            self.check('instanceView.name', 'VMAccessForLinux'),
            self.check('instanceView.statuses[0].displayStatus', 'Provisioning succeeded'),
        ])
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

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_ephemeral_os_disk_placement')
    def test_vm_create_ephemeral_os_disk_placement(self, resource_group, resource_group_location):
        self.kwargs.update({
            'base': 'cli-test-vm-local-base',
            'vm': 'cli-test-vm-local-1',
            'vm_2': 'cli-test-vm-local-2',
            'image': 'UbuntuLTS',
            'ssh_key': TEST_SSH_KEY_PUB,
            'loc': resource_group_location,
            'user': 'user_1',
            'placement1': 'ResourceDisk',
            'placement2': 'CacheDisk',
        })

        # check base
        self.cmd('vm create -n {base} -g {rg} --image {image} --size Standard_DS4_v2 --location {loc} --ephemeral-os-disk --ephemeral-os-disk-placement {placement1} --admin-username {user}')
        self.cmd('vm show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.caching', 'ReadOnly'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
        ])

        # check that we can create a vm with ResourceDisk.
        self.cmd(
            'vm create --resource-group {rg} --name {vm} --image {image} --size Standard_DS4_v2 --ssh-key-value \'{ssh_key}\' --location {loc} --ephemeral-os-disk --ephemeral-os-disk-placement {placement1} --admin-username {user} --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.caching', 'ReadOnly'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
        ])

        # check that we can create a vm with CacheDisk.
        self.cmd(
            'vm create --resource-group {rg} --name {vm_2} --image {image} --ssh-key-value \'{ssh_key}\' --location {loc} --ephemeral-os-disk --ephemeral-os-disk-placement {placement2} --os-disk-caching ReadOnly --admin-username {user} --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm_2}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.caching', 'ReadOnly'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
            self.check('osProfile.computerName', '{vm_2}'),  # check that --computer-name defaults to --name here.
        ])


class VMUpdateTests(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_update_size_', location='westus2')
    def test_vm_update_size(self, resource_group, resource_group_location):
        self.kwargs.update({
            'base': 'cli-test-vm-local-base',
            'base2': 'cli-test-vm-local-base2',
            'image': 'UbuntuLTS',
            'loc': resource_group_location,
            'size': 'Standard_DS5_v2',
        })

        # check base
        self.cmd('vm create -n {base} -g {rg} --image {image} --size Standard_DS4_v2 --location {loc} --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # check that we can update a vm to another size.
        self.cmd('vm update --resource-group {rg} --name {base} --size {size} --set tags.tagName=tagValue')
        self.cmd('vm show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('hardwareProfile.vmSize', '{size}'),
            self.check('tags.tagName', 'tagValue'),
        ])

        # check not modify size value
        self.cmd('vm update --resource-group {rg} --name {base} --size {size} --set tags.tagName=tagValue')
        self.cmd('vm show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('hardwareProfile.vmSize', '{size}'),
            self.check('tags.tagName', 'tagValue'),
        ])

        # check create with default size
        self.cmd('vm create -n {base2} -g {rg} --image {image}  --location {loc} --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {base2}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # check that we can update a vm from default size.
        self.cmd('vm update --resource-group {rg} --name {base2} --size {size}')
        self.cmd('vm show -g {rg} -n {base2}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('hardwareProfile.vmSize', '{size}'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_update_ephemeral_os_disk_placement_', location='westus2')
    def test_vm_update_ephemeral_os_disk_placement(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm1': 'cli-test-vm-local-vm1',
            'vm2': 'cli-test-vm-local-vm2',
            'image': 'UbuntuLTS',
            'ssh_key': TEST_SSH_KEY_PUB,
            'loc': resource_group_location,
            'user': 'user_1',
            'placement1': 'ResourceDisk',
            'placement2': 'CacheDisk',
            'size1': 'Standard_DS5_v2',
            'size2': 'Standard_DS4_v2',
        })

        # check create base1
        self.cmd('vm create -n {vm1} -g {rg} --image {image} --size Standard_DS4_v2 --location {loc} --ephemeral-os-disk --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
        ])

        # check that we can update size1 and placement1.
        self.cmd('vm update --resource-group {rg} --name {vm1} --size {size1} --ephemeral-os-disk-placement {placement1}')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
        ])

        # check that we can update size2 and placement2.
        self.cmd('vm update --resource-group {rg} --name {vm1} --size {size2} --ephemeral-os-disk-placement {placement2} --set tags.tagName=tagValue')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
            self.check('tags.tagName', 'tagValue'),
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

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --nics nic1 nic2 nic3 nic4 --nic-delete-option nic1=Delete nic3=Delete --admin-username user11 --size Standard_DS3 --ssh-key-value \'{ssh_key}\'')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check("networkProfile.networkInterfaces[0].id.ends_with(@, 'nic1')", True),
            self.check("networkProfile.networkInterfaces[0].deleteOption", 'Delete'),
            self.check("networkProfile.networkInterfaces[1].id.ends_with(@, 'nic2')", True),
            self.check("networkProfile.networkInterfaces[1].deleteOption", None),
            self.check("networkProfile.networkInterfaces[2].id.ends_with(@, 'nic3')", True),
            self.check("networkProfile.networkInterfaces[2].deleteOption", 'Delete'),
            self.check("networkProfile.networkInterfaces[3].id.ends_with(@, 'nic4')", True),
            self.check("networkProfile.networkInterfaces[3].deleteOption", None),
            self.check('length(networkProfile.networkInterfaces)', 4)
        ])

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --nics nic1 nic2 nic3 nic4 --nic-delete-option Detach --admin-username user11 --size Standard_DS3 --ssh-key-value \'{ssh_key}\'')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check("networkProfile.networkInterfaces[0].id.ends_with(@, 'nic1')", True),
            self.check("networkProfile.networkInterfaces[0].deleteOption", 'Detach'),
            self.check("networkProfile.networkInterfaces[1].id.ends_with(@, 'nic2')", True),
            self.check("networkProfile.networkInterfaces[1].deleteOption", 'Detach'),
            self.check("networkProfile.networkInterfaces[2].id.ends_with(@, 'nic3')", True),
            self.check("networkProfile.networkInterfaces[2].deleteOption", 'Detach'),
            self.check("networkProfile.networkInterfaces[3].id.ends_with(@, 'nic4')", True),
            self.check("networkProfile.networkInterfaces[3].deleteOption", 'Detach'),
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
        from azure.cli.command_modules.vm.tests.latest._test_util import TimeSpanProcessor
        TIMESPANTEMPLATE = '0000-00-00'
        super(VMMonitorTestDefault, self).__init__(
            method_name,
            recording_processors=[TimeSpanProcessor(TIMESPANTEMPLATE)],
            replay_processors=[TimeSpanProcessor(TIMESPANTEMPLATE)]
        )

    @AllowLargeResponse()
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

    @AllowLargeResponse()
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
    @AllowLargeResponse()
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

    @AllowLargeResponse()
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
            self.cmd('vm create -n {vm} -g {rg} --image Win2022Datacenter --workspace {workspace} --admin-username azureuser --admin-password AzureCLI@1224 --nsg {nsg}')

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

    @AllowLargeResponse()
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

    @AllowLargeResponse()
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
        self.cmd('vm create -n {vm} -g {rg} --image Win2022Datacenter --admin-password AzureCLI@1224 --nsg {nsg} --admin-username azureuser')
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
    @StorageAccountPreparer(name_prefix='clitestbootdiag', sku='Standard_LRS')
    @AllowLargeResponse()
    def test_vm_boot_diagnostics(self, resource_group, storage_account):

        self.kwargs.update({
            'vm': 'myvm',
            'vm2': 'myvm2'
        })
        self.kwargs['storage_uri'] = 'https://{}.blob.core.windows.net/'.format(self.kwargs['sa'])

        self.cmd('vm create -n {vm} -g {rg} --image UbuntuLTS --authentication-type password --admin-username user11 --admin-password testPassword0 --nsg-rule NONE')

        self.cmd('vm boot-diagnostics enable -g {rg} -n {vm}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('diagnosticsProfile.bootDiagnostics.enabled', True),
            self.check('diagnosticsProfile.bootDiagnostics.storageUri', None)
        ])
        self.cmd('vm boot-diagnostics get-boot-log-uris -g {rg} -n {vm} --expire 100', checks=[
            self.exists('consoleScreenshotBlobUri'),
            self.exists('serialConsoleLogBlobUri')
        ])
        self.cmd('vm boot-diagnostics get-boot-log -g {rg} -n {vm}')

        self.cmd('vm boot-diagnostics enable -g {rg} -n {vm} --storage {sa}')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('diagnosticsProfile.bootDiagnostics.enabled', True),
            self.check('diagnosticsProfile.bootDiagnostics.storageUri', '{storage_uri}')
        ])

        self.cmd('vm boot-diagnostics disable -g {rg} -n {vm}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('diagnosticsProfile.bootDiagnostics.enabled', False))

        # try enable it at the create
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username user11 --admin-password testPassword0 --boot-diagnostics-storage {sa} --nsg-rule NONE')
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

        self.cmd('vmss create -n {vmss} -g {rg} --image UbuntuLTS --authentication-type password --admin-username admin123 --admin-password testPassword0 --instance-count 1 --no-wait')
        self.cmd('vmss wait --created -n {vmss} -g {rg}')

        self.cmd('vmss extension set -n {net-ext} --publisher {net-pub} --version 1.4  --vmss-name {vmss} --resource-group {rg} --protected-settings "{config_file}" --force-update --enable-auto-upgrade false')
        self.cmd('vmss extension list --vmss-name {vmss} -g {rg}', checks=[
            self.check('length(@)', 1)
        ])
        result = self.cmd('vmss extension show --resource-group {rg} --vmss-name {vmss} --name {net-ext}', checks=[
            self.check('type(@)', 'object'),
            self.check('name', '{net-ext}'),
            self.check('publisher', '{net-pub}'),
            self.check('provisionAfterExtensions', None),
            self.check('enableAutomaticUpgrade', False)
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

        self.cmd('vmss extension upgrade -g {rg} -n {vmss}')

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
            self.check('typePropertiesType', '{ext_type}')
        ])
        self.cmd('vmss extension delete --resource-group {rg} --vmss-name {vmss} --name {ext_name}')


class VMSSExtensionImageTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_extension_image_')
    def test_vmss_extension_image(self, resource_group):
        self.kwargs.update({
            'pub': 'Microsoft.Azure.NetworkWatcher',
            'name': 'NetworkWatcherAgentLinux',
            'location': 'eastus',
            'ver': '1.4.905.2'
        })
        
        self.cmd('vmss extension image list -p {pub}', checks=[
            self.check('[0].publisher', self.kwargs['pub'])
        ])

        result = self.cmd('vmss extension image list-names -p {pub} -l {location}', checks=[
            self.check('[0].location', self.kwargs['location'])
        ]).get_output_in_json()
        self.assertTrue([n for n in result if n['name'] == self.kwargs['name']])

        result = self.cmd('vmss extension image list-versions -n {name} -p {pub} -l {location}', checks=[
            self.check('[0].location', self.kwargs['location']),
        ]).get_output_in_json()
        self.assertTrue([v for v in result if v['name'] == self.kwargs['ver']])

        self.cmd('vmss extension image show -n {name} -p {pub} -l {location} --version {ver}', checks=[
            self.check('location', self.kwargs['location']),
            self.check('name', self.kwargs['ver']),
            self.check('operatingSystem', 'Linux')
        ])

        # not existing image
        self.cmd('vmss extension image show -n fooBAR -p fooBAR -l {location} --version 0', expect_failure=True)


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

        self.cmd('vm create --image UbuntuLTS --os-disk-name {disk} --os-disk-delete-option Delete --vnet-name {vnet} --subnet {subnet} --availability-set {availset} --public-ip-address {pubip} -l "West US" --nsg {nsg} --use-unmanaged-disk --size Standard_DS2 --admin-username user11 --storage-account {sa} --storage-container-name {container} -g {rg} --name {vm} --ssh-key-value \'{ssh_key}\'')

        self.cmd('vm availability-set show -n {availset} -g {rg}',
                 checks=self.check('virtualMachines[0].id.ends_with(@, \'{}\')'.format(self.kwargs['vm'].upper()), True))
        self.cmd('network nsg show -n {nsg} -g {rg}',
                 checks=self.check('networkInterfaces[0].id.ends_with(@, \'{vm}VMNic\')', True))
        self.cmd('network nic show -n {vm}VMNic -g {rg}',
                 checks=self.check('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{pubip}\')', True))
        self.cmd('vm show -n {vm} -g {rg}',
                 checks=[self.check('storageProfile.osDisk.vhd.uri', 'https://{sa}.blob.core.windows.net/{container}/{disk}.vhd'),
                         self.check('storageProfile.osDisk.deleteOption', 'Delete')])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_provision_vm_agent_')
    def test_vm_create_provision_vm_agent(self, resource_group):
        self.kwargs.update({
            'vm1': 'vm1',
            'vm2': 'vm2',
            'pswd': 'qpwWfn1qwernv#xnklwezxcvslkdfj'
        })

        self.cmd('vm create -g {rg} -n {vm1} --image UbuntuLTS --enable-agent --admin-username azureuser --admin-password {pswd} --authentication-type password --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('osProfile.linuxConfiguration.provisionVmAgent', True)
        ])

        self.cmd('vm create -g {rg} -n {vm2} --image Win2022Datacenter --admin-username azureuser --admin-password {pswd} --authentication-type password --enable-agent false --nsg-rule NONE')
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

    @AllowLargeResponse()
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

    @ResourceGroupPreparer(name_prefix='cli-test-disk-attach-multiple-disks')
    def test_vm_disk_attach_multiple_disks(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-attach-multiple-disks-test',
            'disk1': 'd1',
            'disk2': 'd2',
            'disk3': 'd3'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username admin123 --image centos --admin-password testPassword0 --authentication-type password --nsg-rule NONE')

        with self.assertRaisesRegex(RequiredArgumentMissingError, 'Please use --name or --disks to specify the disk names'):
            self.cmd('vm disk attach -g {rg} --vm-name {vm} --new --size-gb 1 ')

        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'You can only specify one of --name and --disks'):
            self.cmd('vm disk attach -g {rg} --name {disk1} --disks {disk1} {disk2} {disk3} --vm-name {vm} --new --size-gb 1 ')

        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'You cannot specify the --lun for multiple disks'):
            self.cmd('vm disk attach -g {rg} --disks {disk1} {disk2} {disk3} --vm-name {vm} --new --size-gb 1 --lun 2')

        self.cmd('vm disk attach -g {rg} --vm-name {vm} --disks {disk1} {disk2} {disk3} --new --size-gb 1 ')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('length(storageProfile.dataDisks)', 3),
            self.check('storageProfile.dataDisks[0].name', '{disk1}'),
            self.check('storageProfile.dataDisks[0].lun', 0),
            self.check('storageProfile.dataDisks[1].name', '{disk2}'),
            self.check('storageProfile.dataDisks[1].lun', 1),
            self.check('storageProfile.dataDisks[2].name', '{disk3}'),
            self.check('storageProfile.dataDisks[2].lun', 2)
        ])

        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk1}')
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk2}')
        self.cmd('vm disk detach -g {rg} --vm-name {vm} -n {disk3}')
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('length(storageProfile.dataDisks)', 0))

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

    @ResourceGroupPreparer(name_prefix='cli-test-stdssdk2', location='eastus2euap')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_disk_storage_sku2(self, resource_group):

        self.kwargs.update({
            'vm': 'vm-storage-sku-test',
            'disk1': 'd1',
            'disk2': 'd2',
            'snapshot1': 's1',
            'image1': 'i1',
        })

        self.cmd('vm create -g {rg}  -n {vm} --admin-username admin123 --admin-password testPassword0 --image debian '
                 '--storage-sku os=Premium_LRS 0=PremiumV2_LRS --data-disk-sizes-gb 4 --zone 1 --nsg-rule NONE')
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 4 --sku PremiumV2_LRS --zone 1')
        self.cmd('vm disk attach -g {rg} --vm-name {vm} --name {disk1}')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('storageProfile.dataDisks[0].managedDisk.storageAccountType', 'PremiumV2_LRS'),
            self.check('storageProfile.dataDisks[1].managedDisk.storageAccountType', 'PremiumV2_LRS'),
        ])

        # create a snpashot
        self.cmd('snapshot create -g {rg} -n {snapshot1} --size-gb 4 --sku Standard_LRS --tags tag1=s1', checks=[
            self.check('sku.name', 'Standard_LRS'),
            self.check('diskSizeGb', 4),
            self.check('tags.tag1', 's1')
        ])

        # test that images can be created with different storage skus and os disk caching settings.
        self.cmd('image create -g {rg} -n {image1} --source {snapshot1} --storage-sku PremiumV2_LRS --os-type linux',
                 checks=[
                     self.check('storageProfile.osDisk.storageAccountType', 'PremiumV2_LRS'),
                 ])

    @unittest.skip('VMSS is not support PremiumV2_LRS yet')
    @ResourceGroupPreparer(name_prefix='cli-test-stdssdk3', location='eastus2euap')
    @AllowLargeResponse(size_kb=99999)
    def test_vmss_disk_storage_sku(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss-storage-sku-test',
            'disk1': 'd1',
            'disk2': 'd2',
        })
        self.cmd('vmss create -g {rg} -n {vmss} --admin-username admin123 --admin-password testPassword0 --image debian '
                 '--storage-sku os=Premium_LRS 0=PremiumV2_LRS --data-disk-sizes-gb 4 --zone 1')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'PremiumV2_LRS'),
        ])
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 4 --sku PremiumV2_LRS --zone 1')
        self.cmd('vmss disk attach -g {rg} --vmss-name {vmss} --disk {disk1}')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'PremiumV2_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[1].managedDisk.storageAccountType', 'PremiumV2_LRS'),
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
            self.check('diskMBpsReadWrite', 10)
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
                 ' --data-disk-sizes-gb 4 --zone 2 --location eastus --vm-sku Standard_D2s_v3 --instance-count 1 --lb ""')

        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])
        self.cmd('vmss create -g {rg} -n {vmss2} --admin-username admin123 --admin-password testPassword0 --image debian --ultra-ssd-enabled --zone 2 --location eastus --vm-sku Standard_D2s_v3 --lb ""')
        self.cmd('vmss disk attach -g {rg} --vmss-name {vmss2} --size-gb 5 --sku UltraSSD_LRS')
        self.cmd('vmss show -g {rg} -n {vmss2}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType', 'UltraSSD_LRS'),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_vmss_update_ultra_ssd_enabled_', location='eastus2')
    @AllowLargeResponse(size_kb=99999)
    def test_vm_vmss_update_ultra_ssd_enabled(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vmss': 'vmss1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image centos --size Standard_D2s_v3 --zone 2 --admin-username azureuser --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm update -g {rg} -n {vm} --ultra-ssd-enabled', checks=[
            self.check('additionalCapabilities.ultraSsdEnabled', True)
        ])

        self.cmd('vmss create -g {rg} -n {vmss} --image centos --vm-sku Standard_D2s_v3 --zone 2 --admin-username azureuser --admin-password testPassword0 --authentication-type password --lb ""')
        self.cmd('vmss deallocate -g {rg} -n {vmss}')
        self.cmd('vmss update -g {rg} -n {vmss} --ultra-ssd-enabled', checks=[
            self.check('additionalCapabilities.ultraSsdEnabled', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_hibernation_enabled', location='eastus2')
    def test_vm_hibernation_enabled(self, resource_group):
        self.kwargs.update({
            'vm': self.create_random_name('vm-', 10)
        })

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --enable-hibernation True --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('additionalCapabilities.hibernationEnabled', True)
        ])
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm update -g {rg} -n {vm} --enable-hibernation False', checks=[
            self.check('additionalCapabilities.hibernationEnabled', False)
        ])


class VMUnmanagedDataDiskTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli-test-disk')
    def test_vm_data_unmanaged_disk(self, resource_group):

        self.kwargs.update({
            'loc': 'westus',
            'vm': 'vm-datadisk-test',
            'disk': 'd7'
        })

        self.cmd('vm create -g {rg} --location {loc} -n {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --use-unmanaged-disk --nsg-rule NONE')

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

        self.cmd('vm create -g {rg} -n {vm} --admin-username {username} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --custom-data \'{custom_data}\' --nsg-rule NONE')

        # custom data is write only, hence we have no automatic way to cross check. Here we just verify VM was provisioned
        self.cmd('vm show -g {rg} -n {vm}',
                 checks=self.check('provisioningState', 'Succeeded'))

    @ResourceGroupPreparer(name_prefix='cli_test_create_vm_user_data')
    def test_vm_create_user_data(self, resource_group):

        from azure.cli.core.util import b64encode

        user_data = '#cloud-config\nhostname: myVMhostname'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        user_data_file = os.path.join(curr_dir, 'user_data.json').replace('\\', '\\\\')

        self.kwargs.update({
            'username': 'ubuntu',
            'loc': 'westus',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'vm': 'vm-name',
            'user_data': user_data,
            'ssh_key': TEST_SSH_KEY_PUB,
            'user_data_file': user_data_file
        })

        self.cmd('vm create -g {rg} -n {vm} --admin-username {username} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --user-data \'{user_data}\' --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', b64encode(user_data)),
        ])

        self.cmd('vm show -g {rg} -n {vm} --include-user-data --show-details', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', b64encode(user_data)),
        ])

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', None),
        ])

        self.cmd('vm show -g {rg} -n {vm} --show-details', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', None),
        ])

        self.cmd('vm update -g {rg} -n {vm} --user-data @"{user_data_file}"')

        with open(user_data_file) as file_obj:
            file_content = file_obj.read()

        self.cmd('vm show -g {rg} -n {vm} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', b64encode(file_content)),
        ])

        # Clear the existing data
        self.cmd('vm update -g {rg} -n {vm} --user-data ""')

        self.cmd('vm show -g {rg} -n {vm} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('userData', None),
        ])


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
        self.cmd('vmss update -g {rg} -n {vmss} --force-deletion', checks=[
            self.check('scaleInPolicy.forceDeletion', True)
        ])


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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_with_policy_setting')
    def test_vmss_create_with_policy_setting(self, resource_group):

        maxBIP, maxUIP, maxUUIP, PTB = 40, 40, 40, 'PT1S'
        self.kwargs.update({
            'vmss': 'vrfvmss',
            'maxBIP': maxBIP,
            'maxUIP': maxUIP,
            'maxUUIP': maxUUIP,
            'PTB': PTB
        })

        self.cmd('vmss create --image Debian --admin-password testPassword0 -g {rg} -n {vmss} --instance-count 1 --generate-ssh-keys --admin-username myadmin --max-batch-instance-percent {maxBIP} --max-unhealthy-instance-percent {maxUIP} --max-unhealthy-upgraded-instance-percent {maxUUIP} --pause-time-between-batches {PTB} --prioritize-unhealthy-instances true')

        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('upgradePolicy.rollingUpgradePolicy.maxBatchInstancePercent', maxBIP),
            self.check('upgradePolicy.rollingUpgradePolicy.maxUnhealthyInstancePercent', maxUIP),
            self.check('upgradePolicy.rollingUpgradePolicy.maxUnhealthyInstancePercent', maxUUIP),
            self.check('upgradePolicy.rollingUpgradePolicy.pauseTimeBetweenBatches', PTB),
            self.check('upgradePolicy.rollingUpgradePolicy.prioritizeUnhealthyInstances', True)
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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_ephemeral_os_disk_placement')
    def test_vmss_create_ephemeral_os_disk_placement(self, resource_group):
        self.kwargs.update({
            'base': 'cli-test-vmss-local-base',
            'vmss': 'cli-test-vmss-local-1',
            'vmss_2': 'cli-test-vmss-local-2',
            'image': 'UbuntuLTS',
            'count': 2,
            'caching': 'ReadOnly',
            'user': 'user_1',
            'password': 'testPassword09',
            'placement1': 'ResourceDisk',
            'placement2': 'CacheDisk',
        })

        # check base
        self.cmd(
            'vmss create -n {base} -g {rg} --image {image} --vm-sku Standard_DS4_v2 --ephemeral-os-disk --ephemeral-os-disk-placement {placement1} --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {base}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
        ])

        # check that we can create a vmss with ResourceDisk.
        self.cmd(
            'vmss create --resource-group {rg} --name {vmss} --image {image} --vm-sku Standard_DS4_v2 --ephemeral-os-disk --ephemeral-os-disk-placement {placement1} --disable-overprovision '
            '--instance-count {count} --data-disk-sizes-gb 1 --storage-sku os=standard_lrs 0=premium_lrs --admin-username {user} --admin-password {password} --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Standard_LRS'),
            self.check('length(virtualMachineProfile.storageProfile.dataDisks)', 1),
            self.check('virtualMachineProfile.storageProfile.dataDisks[0].managedDisk.storageAccountType',
                       'Premium_LRS')
        ])

        # check that we can create a vmss with CacheDisk.
        self.cmd('vmss create --resource-group {rg} --name {vmss_2} --image {image} --ephemeral-os-disk --ephemeral-os-disk-placement {placement2} '
                 '--os-disk-caching {caching} --disable-overprovision --instance-count {count} --admin-username {user} --admin-password {password} --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {vmss_2}', checks=[
            self.check('virtualMachineProfile.storageProfile.osDisk.caching', '{caching}'),
            self.check('virtualMachineProfile.storageProfile.osDisk.createOption', 'FromImage'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
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

        res = self.cmd('vmss create -g {rg} --name {vmss} --validate --image UbuntuLTS --disable-overprovision --instance-count 101 --single-placement-group false '
                       '--admin-username ubuntuadmin --generate-ssh-keys --lb ""').get_output_in_json()
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

    @record_only()
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
            'vmss': self.create_random_name('vmsswithip', 20),
            'flex_vmss': self.create_random_name('flexvmsswithip', 20),
            'nsg': 'testnsg',
            'ssh_key': TEST_SSH_KEY_PUB,
            'dns_label': self.create_random_name('clivmss', 20)
        })
        nsg_result = self.cmd('network nsg create -g {rg} -n {nsg}').get_output_in_json()
        self.cmd("vmss create -n {vmss} -g {rg} --image Debian --admin-username clittester --ssh-key-value '{ssh_key}' --vm-domain-name {dns_label} --public-ip-per-vm --dns-servers 10.0.0.6 10.0.0.5 --nsg {nsg} --admin-username vmtest",
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

        self.cmd('vmss create -g {rg} -n {flex_vmss} --image UbuntuLTS --orchestration-mode Flexible --admin-username vmtest')
        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vmss list-instance-public-ips -n {flex_vmss} -g {rg}')


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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_policy_')
    def test_vmss_update_policy(self, resource_group):

        maxBIP, maxUIP, maxUUIP, PTB = 40, 40, 40, 'PT1S'
        self.kwargs.update({
            'vmss': 'winvmss',
            'maxBIP': maxBIP,
            'maxUIP': maxUIP,
            'maxUUIP': maxUUIP,
            'PTB': PTB,
            'prioritizeUI': True,
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --instance-count 1 --generate-ssh-keys')
        # test rolling upgrade policy
        self.cmd('vmss update -g {rg} -n {vmss} --max-batch-instance-percent {maxBIP} --max-unhealthy-instance-percent {maxUIP} --max-unhealthy-upgraded-instance-percent {maxUUIP} --pause-time-between-batches {PTB} --prioritize-unhealthy-instances true', checks=[
            self.check('upgradePolicy.rollingUpgradePolicy.maxBatchInstancePercent', maxBIP),
            self.check('upgradePolicy.rollingUpgradePolicy.maxUnhealthyInstancePercent', maxUIP),
            self.check('upgradePolicy.rollingUpgradePolicy.maxUnhealthyInstancePercent', maxUUIP),
            self.check('upgradePolicy.rollingUpgradePolicy.pauseTimeBetweenBatches', PTB),
            self.check('upgradePolicy.rollingUpgradePolicy.prioritizeUnhealthyInstances', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_image_')
    def test_vmss_update_image(self):
        self.kwargs.update({
            'vm': 'vm1',
            'img': 'img1',
            'vmss': 'vmss1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image centos --admin-username clitest1 --generate-ssh-key --nsg-rule None --admin-username vmtest')
        self.cmd('vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')
        res = self.cmd('image create -g {rg} -n {img} --source {vm}').get_output_in_json()
        self.kwargs.update({
            'image_id': res['id']
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image {image_id} --admin-username vmtest')
        self.cmd('vmss update -g {rg} -n {vmss} --set tags.foo=bar', checks=[
            self.check('tags.foo', 'bar')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_vm_sku_', location='westus2')
    def test_vmss_update_vm_sku(self, resource_group, resource_group_location):
        self.kwargs.update({
            'base': 'cli-test-vmss-local-base',
            'base2': 'cli-test-vmss-local-base2',
            'image': 'UbuntuLTS',
            'vm_sku': 'Standard_DS5_v2',
            'loc': resource_group_location,
        })

        # check base
        self.cmd('vmss create -n {base} -g {rg} --image {image} --vm-sku Standard_DS4_v2 --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # check that we can update vmss to another size.
        self.cmd('vmss update --resource-group {rg} --name {base} --vm-sku {vm_sku} --set tags.tagName=tagValue')
        self.cmd('vmss show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{vm_sku}'),
            self.check('tags.tagName', 'tagValue'),
        ])

        # check not modify size value
        self.cmd('vmss update --resource-group {rg} --name {base} --vm-sku {vm_sku} --set tags.tagName=tagValue')
        self.cmd('vmss show -g {rg} -n {base}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{vm_sku}'),
            self.check('tags.tagName', 'tagValue'),
        ])

        # check create with default size
        self.cmd('vmss create -n {base2} -g {rg} --image {image}  --location {loc} --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {base2}', checks=[
            self.check('provisioningState', 'Succeeded'),
        ])

        # check that we can update a vmss from default size.
        self.cmd('vmss update --resource-group {rg} --name {base2} --vm-sku {vm_sku}')
        self.cmd('vmss show -g {rg} -n {base2}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('sku.name', '{vm_sku}'),
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_ephemeral_os_disk_placement_', location='westus2')
    def test_vmss_update_ephemeral_os_disk_placement(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm1': 'cli-test-vm-local-vm1',
            'vm2': 'cli-test-vm-local-vm2',
            'image': 'UbuntuLTS',
            'placement1': 'ResourceDisk',
            'placement2': 'CacheDisk',
            'size1': 'Standard_DS5_v2',
            'size2': 'Standard_DS4_v2',
            'loc': resource_group_location,
        })

        # check create base1
        self.cmd('vmss create -n {vm1} -g {rg} --image {image} --vm-sku Standard_DS4_v2 --ephemeral-os-disk --admin-username vmtest')
        self.cmd('vmss show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
        ])

        # check that we can update size1 and placement1.
        self.cmd('vmss update --resource-group {rg} --name {vm1} --vm-sku {size1} --ephemeral-os-disk-placement {placement1}')
        self.cmd('vmss show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'ResourceDisk'),
        ])

        # check that we can update size2 and placement2.
        self.cmd('vmss update --resource-group {rg} --name {vm1} --vm-sku {size2} --ephemeral-os-disk-placement {placement2} --set tags.tagName=tagValue')
        self.cmd('vmss show -g {rg} -n {vm1}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.option', 'Local'),
            self.check('virtualMachineProfile.storageProfile.osDisk.diffDiskSettings.placement', 'CacheDisk'),
            self.check('tags.tagName', 'tagValue'),
        ])


class AcceleratedNetworkingTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_accelerated_networking')
    def test_vmss_accelerated_networking(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd("vmss create -n {vmss} -g {rg} --vm-sku Standard_DS4_v2 --image Win2022Datacenter --admin-username clittester --admin-password Test12345678!!! --accelerated-networking --instance-count 1")
        self.cmd('vmss show -n {vmss} -g {rg}',
                 checks=self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].enableAcceleratedNetworking', True))

    @ResourceGroupPreparer()
    def test_vm_accelerated_networking(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })
        # Note: CLI turns sets accelerated_networking to true based on vm size and os image.
        # See _validate_vm_vmss_accelerated_networking for more info.
        self.cmd("vm create -n {vm} -g {rg} --size Standard_DS4_v2 --image ubuntults --admin-username clittester --generate-ssh-keys --nsg-rule NONE")
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
        self.cmd('vm create -g {rg} -n {vm} --image debian --asgs {asg} --admin-username clittester --generate-ssh-keys --nsg-rule NONE').get_output_in_json()
        self.cmd('vmss show -g {rg} -n {vmss}', checks=self.check('virtualMachineProfile.networkProfile.networkInterfaceConfigurations[0].ipConfigurations[0].applicationSecurityGroups[0].id', asg_id))
        self.cmd('network nic show -g {rg} -n {vm}VMNIC', checks=self.check('ipConfigurations[0].applicationSecurityGroups[0].id', asg_id))


class SecretsScenarioTest(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(name_prefix='cli_test_vm_secrets')
    @KeyVaultPreparer(name_prefix='vmlinuxkv', name_len=20, key='vault',
                      additional_params='--enabled-for-deployment true --enabled-for-template-deployment true')
    def test_vm_create_linux_secrets(self, resource_group, resource_group_location, key_vault):

        self.kwargs.update({
            'admin': 'ubuntu',
            'loc': 'westus',
            'image': 'UbuntuLTS',
            'auth': 'ssh',
            'ssh_key': TEST_SSH_KEY_PUB,
            'vm': 'vm-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}])
        })

        message = 'Secret is missing vaultCertificates array or it is empty at index 0'
        with self.assertRaisesRegex(CLIError, message):
            self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

        vault_out = self.cmd('keyvault show -g {rg} -n {vault}').get_output_in_json()

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')
        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        vm_format = self.cmd('vm secret format -s {secret_out}').get_output_in_json()
        self.kwargs['secrets'] = json.dumps(vm_format)

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', '{secret_out}')
        ])

    @ResourceGroupPreparer()
    @KeyVaultPreparer(name_prefix='vmkeyvault', name_len=20, key='vault',
                      additional_params='--enabled-for-deployment true --enabled-for-template-deployment true')
    def test_vm_create_windows_secrets(self, resource_group, resource_group_location, key_vault):

        self.kwargs.update({
            'admin': 'windowsUser',
            'loc': 'westus',
            'image': 'Win2012R2Datacenter',
            'vm': 'vm-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': [{'certificateUrl': 'certurl'}]}])
        })

        message = 'Secret is missing certificateStore within vaultCertificates array at secret index 0 and ' \
                  'vaultCertificate index 0'
        with self.assertRaisesRegex(CLIError, message):
            self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets \'{secrets}\' --nsg-rule NONE')

        vault_out = self.cmd('keyvault show -g {rg} -n {vault}').get_output_in_json()

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')
        self.cmd('keyvault certificate create --vault-name {vault} -n cert1 -p @"{policy_path}"')

        self.kwargs['secret_out'] = self.cmd('keyvault secret list-versions --vault-name {vault} -n cert1 --query "[?attributes.enabled].id" -o tsv').output.strip()
        self.kwargs['secrets'] = self.cmd('vm secret format -s {secret_out} --certificate-store "My"').get_output_in_json()

        self.cmd('vm create -g {rg} -n {vm} --admin-username {admin} --admin-password VerySecret!12 --image {image} -l {loc} --secrets "{secrets}" --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('osProfile.secrets[0].sourceVault.id', vault_out['id']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateUrl', self.kwargs['secret_out']),
            self.check('osProfile.secrets[0].vaultCertificates[0].certificateStore', 'My')
        ])


class VMSSCreateLinuxSecretsScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_linux_secrets')
    @KeyVaultPreparer(name_prefix='vmsslinuxkv', name_len=20, key='vault', additional_params='--enabled-for-deployment true --enabled-for-template-deployment true')
    @AllowLargeResponse()
    def test_vmss_create_linux_secrets(self, resource_group, key_vault):
        self.kwargs.update({
            'loc': 'westus',
            'vmss': 'vmss1-name',
            'secrets': json.dumps([{'sourceVault': {'id': 'id'}, 'vaultCertificates': []}]),
            'secret': 'mysecret',
            'ssh_key': TEST_SSH_KEY_PUB
        })

        vault_out = self.cmd('keyvault show -g {rg} -n {vault}').get_output_in_json()

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

    @AllowLargeResponse()
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
            'vmss': self.create_random_name('clitestvmss', 20),
            'flex_vmss': self.create_random_name('clitestflexvms', 20),
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

        self.cmd('vmss create -g {rg} -n {flex_vmss} --image UbuntuLTS --orchestration-mode Flexible --admin-username vmtest')
        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vmss list-instance-connection-info --resource-group {rg} --name {flex_vmss}')


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
        self.cmd('vmss create --resource-group {rg} --name {vmss1} --location {loc} --instance-count 2 --image Centos --priority Regular --admin-username vmtest')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss1}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss1} --instance-id {id}', expect_failure=True)

        # simulate-eviction on a Spot VMSS with Deallocate policy, expect VMSS instance to be deallocated
        self.cmd('vmss create --resource-group {rg} --name {vmss2} --location {loc} --instance-count 2 --image Centos --priority Spot --eviction-policy Deallocate --single-placement-group True --admin-username vmtest')
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
        self.cmd('vmss create --resource-group {rg} --name {vmss3} --location {loc} --instance-count 2 --image Centos --priority Spot --eviction-policy Delete --single-placement-group True --admin-username vmtest')
        instance_list = self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}').get_output_in_json()
        self.kwargs['instance_ids'] = [x['instanceId'] for x in instance_list]
        self.kwargs['id'] = self.kwargs['instance_ids'][0]
        self.cmd('vmss simulate-eviction --resource-group {rg} --name {vmss3} --instance-id {id}')
        time.sleep(180)
        self.cmd('vmss list-instances --resource-group {rg} --name {vmss3}', checks=[self.check('length(@)', len(self.kwargs['instance_ids']) - 1)])
        self.cmd('vmss get-instance-view --resource-group {rg} --name {vmss3} --instance-id {id}', expect_failure=True)

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_spot_restore')
    def test_spot_restore_policy(self, resource_group):
        self.kwargs.update({
            'loc': 'NorthEurope',
            'spot_vmss_name': 'vmss-spot1',
            'enabled_1': 'True',
            'enabled_2': 'False',
            'restore_timeout1': 'PT1H',
            'restore_timeout2': 'PT2H'

        })
        self.cmd('vmss create -g {rg} -n {spot_vmss_name} --location NorthEurope --instance-count 2 --image Centos --priority Spot --eviction-policy Deallocate --single-placement-group True --enable-spot-restore {enabled_1} --spot-restore-timeout {restore_timeout1} --admin-username vmtest', checks=[
            self.check('vmss.spotRestorePolicy.enabled', True),
            self.check('vmss.spotRestorePolicy.restoreTimeout', '{restore_timeout1}')
        ])
        self.cmd('vmss update -g {rg} -n {spot_vmss_name} --enable-spot-restore {enabled_2} --spot-restore-timeout {restore_timeout2}', checks=[
            self.check('spotRestorePolicy.enabled', False),
            self.check('spotRestorePolicy.restoreTimeout', '{restore_timeout2}')
        ])


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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_create_user_data')
    def test_vmss_create_user_data(self):

        from azure.cli.core.util import b64encode

        user_data = '#cloud-config\nhostname: myVMhostname'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        user_data_file = os.path.join(curr_dir, 'user_data.json').replace('\\', '\\\\')

        self.kwargs.update({
            'vmss': 'vmss-custom-data',
            'ssh_key': TEST_SSH_KEY_PUB,
            'user_data': user_data,
            'user_data_file': user_data_file
        })

        self.cmd('vmss create -n {vmss} -g {rg} --image Debian --admin-username deploy --ssh-key-value "{ssh_key}" --user-data "{user_data}"')

        self.cmd('vmss show -n {vmss} -g {rg} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.userData', b64encode(user_data)),
        ])

        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.userData', None),
        ])

        self.kwargs['instance_id'] = self.cmd('vmss list-instances -g {rg} -n {vmss} --query "[].instanceId"').get_output_in_json()[0]

        self.cmd('vmss show -g {rg} -n {vmss} --instance-id {instance_id} --include-user-data',checks=[
            self.check('instanceId', '{instance_id}'),
            self.check('userData', b64encode(user_data)),
        ])

        self.cmd('vmss show -g {rg} -n {vmss} --instance-id {instance_id}',checks=[
            self.check('instanceId', '{instance_id}'),
            self.check('userData', None),
        ])

        with open(user_data_file) as file_obj:
            file_content = file_obj.read()

        self.cmd('vmss update -g {rg} -n {vmss} --user-data @"{user_data_file}"')

        self.cmd('vmss show -n {vmss} -g {rg} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.userData', b64encode(file_content)),
        ])

        self.cmd('vmss update -g {rg} -n {vmss} --instance-id {instance_id} --user-data "user_data"')

        self.cmd('vmss show -g {rg} -n {vmss} --instance-id {instance_id} --include-user-data',checks=[
            self.check('instanceId', '{instance_id}'),
            self.check('userData', b64encode(user_data)),
        ])

        # Clear the existing data
        self.cmd('vmss update -g {rg} -n {vmss} --user-data ""')

        self.cmd('vmss show -n {vmss} -g {rg} --include-user-data', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.userData', None),
        ])


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

    @unittest.skip('Can\'t test due to no qualified subscription')
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

        with self.assertRaisesRegex(ArgumentUsageError, "please specify both --role and --scope"):
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE --scope {scope}')

        with self.assertRaisesRegex(ArgumentUsageError, "please specify both --role and --scope"):
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE --role Contributor')

        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            # create a linux vm with default configuration
            self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope} --role Contributor --nsg-rule NONE', checks=[
                self.check('identity.role', 'Contributor'),
                self.check('identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vm create -g {rg} -n {vm2} --image Win2022Datacenter --assign-identity --scope {vm1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE', checks=[
                self.check('identity.role', 'reader'),
                self.check('identity.scope', '{vm1_id}'),
            ])
            uuid.UUID(result.get_output_in_json()['identity']['systemAssignedIdentity'])

            # create a linux vm w/o identity and later enable it
            vm3_result = self.cmd('vm create -g {rg} -n {vm3} --image debian --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE').get_output_in_json()
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

        with self.assertRaisesRegex(ArgumentUsageError, "please specify both --role and --scope"):
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope}')

        with self.assertRaisesRegex(ArgumentUsageError, "please specify both --role and --scope"):
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --role Contributor')

        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            # create linux vm with default configuration
            self.cmd('vmss create -g {rg} -n {vmss1} --image debian --instance-count 1 --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --scope {scope} --role Contributor', checks=[
                self.check('vmss.identity.role', 'Contributor'),
                self.check('vmss.identity.scope', '/subscriptions/{sub}/resourceGroups/{rg}'),
            ])

            # create a windows vm with reader role on the linux vm
            result = self.cmd('vmss create -g {rg} -n {vmss2} --image Win2022Datacenter --instance-count 1 --assign-identity --scope {vmss1_id} --role reader --admin-username admin123 --admin-password PasswordPassword1!', checks=[
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
        self.cmd('vm create -g {rg} -n {vm1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE', checks=[
            self.check('identity.scope', None),
            self.check('identity.role', None),
        ])

        # create a vmss with identity but w/o a role assignment (--scope "")
        self.cmd('vmss create -g {rg} -n {vmss1} --image debian --assign-identity --admin-username admin123 --admin-password PasswordPassword1!', checks=[
            self.check('vmss.identity.scope', None),
        ])

        # create a vm w/o identity
        self.cmd('vm create -g {rg} -n {vm2} --image debian --admin-username admin123 --admin-password PasswordPassword1! --nsg-rule NONE')
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
        result = self.cmd('vm create -g {rg} -n vm2 --image ubuntults --assign-identity {emsi} --generate-ssh-keys --admin-username {user} --nsg-rule NONE', checks=[
            self.check('identity.role', None),
            self.check('identity.scope', None),
        ]).get_output_in_json()
        emsis = [x.lower() for x in result['identity']['userAssignedIdentities'].keys()]
        self.assertEqual(emsis, [emsi_result['id'].lower()])
        self.assertFalse(result['identity']['systemAssignedIdentity'])

        # create a vm with system + user assigned identities
        result = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --assign-identity {emsi} [system] --role reader --scope {scope} --generate-ssh-keys --admin-username {user} --nsg-rule NONE').get_output_in_json()
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

    @unittest.skip('Not necessary')
    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_progress')
    def test_vm_create_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging

        self.kwargs.update({'vm': 'vm123'})

        with force_progress_logging() as test_io:
            self.cmd('vm create -g {rg} -n {vm} --admin-username {vm} --admin-password PasswordPassword1! --authentication-type password --image debian --nsg-rule NONE')

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
        self.cmd('vm create -g {rg} -n {vm} --admin-username clitester --admin-password PasswordPassword1! --image debian --zone {zones} --public-ip-address {ip} --nsg-rule NONE',
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

    @unittest.skip('Can\'t test due to no qualified subscription')
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

    @unittest.skip('Can\'t test due to no qualified subscription')
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

    @unittest.skip('Can\'t test due to no qualified subscription')
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

    @unittest.skip('Can\'t test open-port. It is not allowed in our subscription')
    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command')
    def test_vm_run_command_e2e(self, resource_group, resource_group_location):

        self.kwargs.update({
            'vm': 'test-run-command-vm',
            'loc': resource_group_location
        })

        self.cmd('vm run-command list -l {loc}')
        self.cmd('vm run-command show --command-id RunShellScript -l {loc}')
        public_ip = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --admin-password Test12345678!! --generate-ssh-keys --nsg-rule NONE').get_output_in_json()['publicIpAddress']

        self.cmd('vm open-port -g {rg} -n {vm} --port 80')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript --script "sudo apt-get update && sudo apt-get install -y nginx"')
        time.sleep(15)  # 15 seconds should be enough for nginx started(Skipped under playback mode)
        import requests
        r = requests.get('http://' + public_ip)
        self.assertTrue('Welcome to nginx' in str(r.content))

    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command_w_params')
    def test_vm_run_command_with_parameters(self, resource_group):
        self.kwargs.update({'vm': 'test-run-command-vm2'})
        self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username clitest1 --admin-password Test12345678!! --generate-ssh-keys --nsg-rule NONE')
        self.cmd('vm run-command invoke -g {rg} -n{vm} --command-id RunShellScript  --scripts "echo $0 $1" --parameters hello world')


    @ResourceGroupPreparer(name_prefix='cli_test_vm_run_command_v2')
    def test_run_command_v2(self, resource_group):
        self.kwargs.update({
            'vm': self.create_random_name('vm-', 10),
            'run_cmd': self.create_random_name('cmd-', 10)
        })
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username vmtest')
        self.cmd('vm run-command create -g {rg} --vm-name {vm} --name {run_cmd}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', None),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 0),
            self.check('type', 'Microsoft.Compute/virtualMachines/runCommands')
        ])
        self.cmd('vm run-command show --vm-name {vm} --name {run_cmd} -g {rg} --instance-view', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('instanceView.executionState', 'Running')
        ])
        self.cmd('vm run-command update -g {rg} --vm-name {vm} --name {run_cmd}  --vm-name {vm} --script script1 --parameters arg1=f1 --run-as-user user1 --timeout-in-seconds 3600', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', 'script1'),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 3600),
            self.check('type', 'Microsoft.Compute/virtualMachines/runCommands')
            ])
        self.cmd('vm run-command list --vm-name {vm} -g {rg}', checks=[
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].name', '{run_cmd}'),
            self.check('[0].source.script', 'script1'),
            self.check('[0].asyncExecution', False),
            self.check('[0].timeoutInSeconds', 3600)
        ])
        self.cmd('vm run-command show --vm-name {vm} --name {run_cmd} -g {rg}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', 'script1'),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 3600)
        ])
        self.cmd('vm run-command delete --vm-name {vm} --name {run_cmd} -g {rg} -y')
        self.cmd('vm run-command list --vm-name {vm} -g {rg}', checks=self.is_empty())


class VMSSRunCommandScenarioTest(ScenarioTest):
    @unittest.skip('Can\'t test it. We are not allowed to open ports.')
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

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_run_command_v2')
    def test_vmss_run_command_v2(self, resource_group):
        self.kwargs.update({
            'vmss': self.create_random_name('vmss-', 10),
            'run_cmd': self.create_random_name('cmd_', 10),
            'user': self.create_random_name('user-', 10)
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image ubuntults --admin-username {user} --generate-ssh-keys')
        instace_ids = self.cmd('vmss list-instances --resource-group {rg} --name {vmss} --query "[].instanceId"').get_output_in_json()
        self.kwargs.update({
            'instance_id': instace_ids[0]
        })
        self.cmd('vmss run-command create --name {run_cmd} -g {rg} --vmss-name {vmss} --instance-id {instance_id}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', None),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 0),
            self.check('type', 'Microsoft.Compute/virtualMachineScaleSets/virtualMachines/runCommands')
        ])
        self.cmd('vmss run-command show --vmss-name {vmss} --name {run_cmd} --instance-id {instance_id} -g {rg} --instance-view', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('instanceView.executionState', 'Running')
        ])
        self.cmd('vmss run-command update --name {run_cmd} -g {rg} --vmss-name {vmss} --instance-id {instance_id} --script script1 --parameters arg1=f1 --run-as-user user1 --timeout-in-seconds 3600', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', 'script1'),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 3600),
            ])
        self.cmd('vmss run-command list --vmss-name {vmss} -g {rg} --instance-id {instance_id}', checks=[
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].name', '{run_cmd}'),
            self.check('[0].source.script', 'script1'),
            self.check('[0].asyncExecution', False),
            self.check('[0].timeoutInSeconds', 3600)
        ])
        self.cmd('vmss run-command show --vmss-name {vmss} --name {run_cmd} --instance-id {instance_id} -g {rg}', checks=[
            self.check('resourceGroup', '{rg}'),
            self.check('name', '{run_cmd}'),
            self.check('source.script', 'script1'),
            self.check('asyncExecution', False),
            self.check('timeoutInSeconds', 3600)
        ])
        self.cmd('vmss run-command delete --vmss-name {vmss} --name {run_cmd} --instance-id {instance_id} -g {rg} -y')
        self.cmd('vmss run-command list --vmss-name {vmss} --instance-id {instance_id} -g {rg}', checks=self.is_empty())

@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMDiskEncryptionTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_encryption', location='westus')
    @KeyVaultPreparer(name_prefix='vault', name_len=20, key='vault', additional_params='--enabled-for-disk-encryption true')
    def test_vmss_disk_encryption_e2e(self, resource_group, resource_group_location, key_vault):
        self.kwargs.update({
            'vmss': 'vmss1'
        })
        self.cmd('vmss create -g {rg} -n {vmss} --image Win2022Datacenter --instance-count 1 --admin-username clitester1 --admin-password Test123456789!')
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
    @KeyVaultPreparer(name_prefix='vault', name_len=10, key='vault',
                      additional_params='--enabled-for-disk-encryption true')
    def test_vm_disk_encryption_e2e(self, resource_group, resource_group_location, key_vault):
        self.kwargs.update({
            'vm': 'vm1'
        })
        self.cmd('vm create -g {rg} -n {vm} --image win2012datacenter --admin-username clitester1 --admin-password Test123456789! --nsg-rule NONE')
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
        self.cmd('vmss update -g {rg} -n {vmss} --set tags.rule=test')


@api_version_constraint(ResourceType.MGMT_COMPUTE, min_api='2017-03-30')
class VMSSRollingUpgrade(ScenarioTest):

    @unittest.skip('Cannot open ports in our subscription')
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
    @unittest.skip('Cannot test lb')
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

    @unittest.skip('Can\'t test lb')
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
        self.cmd('network nsg create -g {rg} -n nsg')
        self.cmd('network nic create -g {rg} -n my-nic --subnet my-subnet1 --vnet-name my-vnet --public-ip-address my-pip --network-security-group nsg')
        self.cmd('network nic ip-config create -n my-ipconfig2 -g {rg} --nic-name my-nic --private-ip-address-version IPv6')
        self.cmd('vm create -g {rg} -n vm1 --image centos --nics my-nic --generate-ssh-keys --admin-username ubuntuadmin')
        result = self.cmd('vm show -g {rg} -n vm1 -d').get_output_in_json()
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['publicIps']))
        self.assertTrue(re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', result['privateIps']))


class VMSecretTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_secrets')
    @KeyVaultPreparer(name_prefix='vmsecretkv', name_len=20, key='vault', additional_params='--enabled-for-disk-encryption true --enabled-for-deployment true')
    def test_vm_secret_e2e_test(self, resource_group, resource_group_location, key_vault):
        self.kwargs.update({
            'vm': 'vm1',
            'cert': 'vm-secrt-cert',
            'loc': resource_group_location
        })

        self.kwargs['policy_path'] = os.path.join(TEST_DIR, 'keyvault', 'policy.json')

        self.cmd('vm create -g {rg} -n {vm} --image rhel --generate-ssh-keys --admin-username rheladmin --nsg-rule NONE')
        time.sleep(60)  # ensure we don't hit the DNS exception (ignored under playback)

        self.cmd('keyvault certificate create --vault-name {vault} -n {cert} -p @"{policy_path}"')
        secret_result = self.cmd('vm secret add -g {rg} -n {vm} --keyvault {vault} --certificate {cert}', checks=[
            self.check('length([])', 1),
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

        self.cmd('vm create -g {rg} -n {vm} --image debian --data-disk-sizes-gb 1 2 --admin-username cligenerics --generate-ssh-keys --nsg-rule NONE')

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
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus')
    def test_shared_gallery(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': 'vm1',
            'gallery': self.create_random_name('gellery', 16),
            'image': 'image1',
            'version': '1.1.2',
            'captured': 'managedImage1',
            'location': resource_group_location,
            'subId': '0b1f6471-1bf0-4dda-aec3-cb9272f09590',  # share the gallery to tester's subscription, so the tester can get shared galleries
            'tenantId': '2f4a9838-26b7-47ee-be60-ccc1fdec5953',
            'sharedSubId': '34a4ab42-0d72-47d9-bd1a-aed207386dac'
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --permissions groups')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image}')
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --data-disk-sizes-gb 10 --admin-username clitest1 '
                 '--generate-ssh-key --nsg-rule NONE')
        self.cmd('vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts '
                 '"echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes"')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')
        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} '
                 '--gallery-image-version {version} --managed-image {captured} --replica-count 1')

        # Test shared gallery
        # service team has temporarily disable the feature of updating permissions and will enable it in a few months
        # self.cmd('sig update --gallery-name {gallery} --resource-group {rg} --permissions groups')
        res = self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Groups')
        ]).get_output_in_json()

        self.kwargs['unique_name'] = res['identifier']['uniqueName']

        self.cmd('sig share add --gallery-name {gallery} -g {rg} --subscription-ids {subId} {sharedSubId} --tenant-ids {tenantId}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.groups[0].ids[0]', self.kwargs['subId']),
            self.check('sharingProfile.groups[0].ids[1]', self.kwargs['sharedSubId']),
            self.check('sharingProfile.groups[0].type', 'Subscriptions'),
            self.check('sharingProfile.groups[1].ids[0]', self.kwargs['tenantId']),
            self.check('sharingProfile.groups[1].type', 'AADTenants')
        ])

        self.cmd('sig share remove --gallery-name {gallery} -g {rg} --subscription-ids {sharedSubId} --tenant-ids {tenantId}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.groups[0].ids[0]', self.kwargs['subId']),
            self.check('length(sharingProfile.groups)', 1),
        ])

        # Check result by shared user
        self.cmd('sig list-shared --location {location}', checks=[
            self.check('[0].location', '{location}'),
            self.check('[0].name', '{unique_name}'),
            self.check('[0].uniqueId', '/SharedGalleries/{unique_name}')
        ])

        self.cmd('sig show-shared --location {location} --gallery-unique-name {unique_name}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{unique_name}'),
            self.check('uniqueId', '/SharedGalleries/{unique_name}')
        ])

        self.cmd('sig image-definition list-shared --gallery-unique-name {unique_name} --location {location}', checks=[
            self.check('[0].location', '{location}'),
            self.check('[0].name', '{image}'),
            self.check('[0].uniqueId', '/SharedGalleries/{unique_name}/Images/{image}')
        ])

        self.cmd('sig image-definition show-shared --gallery-image-definition {image} '
                 '--gallery-unique-name {unique_name} --location {location}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{image}'),
            self.check('uniqueId', '/SharedGalleries/{unique_name}/Images/{image}')
        ])

        self.cmd('sig image-version list-shared --gallery-image-definition {image} --gallery-unique-name {unique_name} '
                 '--location {location}', checks=[
            self.check('[0].location', '{location}'),
            self.check('[0].name', '{version}'),
            self.check('[0].uniqueId', '/SharedGalleries/{unique_name}/Images/{image}/Versions/{version}')
        ])

        self.cmd('sig image-version show-shared --gallery-image-definition {image} --gallery-unique-name {unique_name} '
                 '--location {location} --gallery-image-version {version}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{version}'),
            self.check('uniqueId', '/SharedGalleries/{unique_name}/Images/{image}/Versions/{version}')
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery} -g {rg}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_image_version_create_', location='westus')
    def test_image_version_create_for_diff_source(self, resource_group_location):
        self.kwargs.update({
            'vm': 'vm1',
            'gallery': self.create_random_name('gallery', 16),
            'image1': 'image1',
            'image2': 'image2',
            'version1': '1.1.2',
            'version2': '1.1.1',
            'captured': 'managedImage1',
            'subId': '0b1f6471-1bf0-4dda-aec3-cb9272f09590'
            # share the gallery to tester's subscription, so the tester can get shared galleries
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image1} '
                 '--os-type linux --os-state Specialized -p publisher1 -f offer1 -s sku1')
        vm_id = self.cmd('vm create -g {rg} -n {vm} --image ubuntults --data-disk-sizes-gb 10 --admin-username clitest1'
                         ' --generate-ssh-key --nsg-rule NONE').get_output_in_json()['id']
        time.sleep(70)
        self.kwargs.update({"vm_id": vm_id})

        # test the result of creating image version for virtual machine source
        image_version_id = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image1} '
            '--gallery-image-version {version1} --virtual-machine {vm_id}',
            checks=[
                self.check('location', resource_group_location),
                self.check('name', self.kwargs['version1']),
                self.check('provisioningState', 'Succeeded')
            ]).get_output_in_json()['id']

        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image2} '
                 '--os-type linux -p publisher2 -f offer2 -s sku2')
        self.kwargs.update({"image_version_id": image_version_id})

        # test the format check of virtual machine source and image version source
        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image1} '
                     '--gallery-image-version {version1} --image-version {vm_id}')
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image2} '
                     '--gallery-image-version {version1} --virtual-machine {image_version_id}')

        # test the result of more than one source are provided
        from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
        with self.assertRaises(MutuallyExclusiveArgumentError):
            self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image1} '
                     '--gallery-image-version {version1} --virtual-machine {vm_id} --image-version {image_version_id}')

        # test the result of creating image version for gallery image version source
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image1} '
                 '--gallery-image-version {version2} --image-version {image_version_id}',
                 checks=[
                     self.check('location', resource_group_location),
                     self.check('name', self.kwargs['version2']),
                     self.check('provisioningState', 'Succeeded')
                 ])

        # test the result of creating image version for managed image source
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')
        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image2} '
                 '--gallery-image-version {version1} --managed-image {captured}',
                 checks=[
                     self.check('location', resource_group_location),
                     self.check('name', self.kwargs['version1']),
                     self.check('provisioningState', 'Succeeded')
                 ])

    @ResourceGroupPreparer(location='eastus2')
    @KeyVaultPreparer(name_prefix='vault-', name_len=20, key='vault', location='eastus2', additional_params='--enable-purge-protection true --enable-soft-delete true')
    def test_gallery_e2e(self, resource_group, resource_group_location, key_vault):
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_gallery_image_version_vhd')
    def test_gallery_image_version_vhd(self, resource_group):
        self.kwargs.update({
            'gallery': self.create_random_name(prefix='gallery_', length=20)
        })

        self.cmd('vm create -g {rg} -n vm1 --image centos --use-unmanaged-disk --nsg-rule NONE --generate-ssh-key --admin-username vmtest')
        vhd_uri = self.cmd('vm show -g {rg} -n vm1').get_output_in_json()['storageProfile']['osDisk']['vhd']['uri']
        storage_account_os = vhd_uri.split('.')[0].split('/')[-1]
        self.kwargs.update({
            'vhd': vhd_uri,
            'stac': storage_account_os
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition image1 '
                 '--os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('disk create -g {rg} -n d1 --size-gb 10')
        self.cmd('disk create -g {rg} -n d2 --size-gb 10')
        s1_id = self.cmd('snapshot create -g {rg} -n s1 --source d1').get_output_in_json()['id']
        s2_id = self.cmd('snapshot create -g {rg} -n s2 --source d2').get_output_in_json()['id']
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition image1 '
                 '--gallery-image-version 1.0.0 --os-snapshot s1 --data-snapshot-luns 0 --data-snapshots s2 '
                 '--data-vhds-luns 1 --data-vhds-sa {stac} --data-vhds-uris {vhd}',
                 checks=[
                     self.check('storageProfile.osDiskImage.source.id', s1_id),
                     self.check('storageProfile.dataDiskImages[0].source.id', s2_id),
                     self.check('storageProfile.dataDiskImages[0].lun', 0),
                     self.check('storageProfile.dataDiskImages[1].source.uri', vhd_uri),
                     self.check('storageProfile.dataDiskImages[1].lun', 1)])

    @ResourceGroupPreparer(random_name_length=15, location='CentralUSEUAP')
    @KeyVaultPreparer(name_prefix='vault-', name_len=20, key='vault', location='CentralUSEUAP',
                      additional_params='--enable-purge-protection true --enable-soft-delete true')
    def test_create_image_version_with_region_cvm_encryptio(self, resource_group, resource_group_location, key_vault):
        self.kwargs.update({
            'vm': 'vm1',
            'gallery': self.create_random_name(prefix='gallery_', length=20),
            'image': 'image1',
            'version': '1.1.1',
            'captured': 'managedImage1',
            'location': resource_group_location,
            'key': self.create_random_name(prefix='key-', length=20),
            'disk1': self.create_random_name(prefix='disk', length=20),
            'snapshot1': self.create_random_name(prefix='snp', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type windows -p publisher1 -f offer1 -s sku1 --os-state Specialized --features SecurityType=ConfidentialVm --hyper-v-generation v2', checks=[
            self.check('name', self.kwargs['image']),
            self.check('features[0].name', 'SecurityType'),
            self.check('features[0].value', 'ConfidentialVM'),
            self.check('hyperVGeneration', 'V2')
        ])

        # Create disk encryption set
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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')

        self.cmd('disk create -g {rg} -n {disk1} --image-reference MicrosoftWindowsServer:WindowsServer:2022-datacenter-smalldisk-g2:latest --hyper-v-generation V2  --security-type ConfidentialVM_VMGuestStateOnlyEncryptedWithPlatformKey --disk-encryption-set {des1_id}')
        self.cmd('snapshot create -g {rg} -n {snapshot1} --source {disk1}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --target-regions {location}=1 --target-region-encryption {des1},0,{des1} --target-region-cvm-encryption EncryptedVMGuestStateOnlyWithPmk, --os-snapshot {snapshot1} --replica-count 1', checks=[
            self.check('publishingProfile.targetRegions[0].name', 'Central US EUAP'),
            self.check('publishingProfile.targetRegions[0].regionalReplicaCount', 1),
            self.check('publishingProfile.targetRegions[0].encryption.osDiskImage.diskEncryptionSetId', '{des1_id}'),
            self.check('publishingProfile.targetRegions[0].encryption.dataDiskImages[0].lun', 0),
            self.check('publishingProfile.targetRegions[0].encryption.dataDiskImages[0].diskEncryptionSetId', '{des1_id}')
        ])

        self.cmd('sig image-version delete -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version}')
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
                         self.check('hyperVGeneration', 'V2')])
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
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux --os-state specialized -p publisher1 -f offer1 -s sku1 --features "IsAcceleratedNetworkSupported=true"', checks=[
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
    @ResourceGroupPreparer(name_prefix='cli_test_image_version_', location='westus2',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_sig_image_version_cross_tenant(self, resource_group, another_resource_group):
        self.kwargs.update({
            'location': 'westus2',
            'rg': resource_group,
            'another_rg': another_resource_group,
            'vm': self.create_random_name('cli_test_image_version_', 40),
            'image_name': self.create_random_name('cli_test_image_version_', 40),
            'aux_sub': AUX_SUBSCRIPTION,
            'aux_tenant': AUX_TENANT,
            'sig_name': self.create_random_name('cli_test_image_version_', 40),
            'image_definition_name': self.create_random_name('cli_test_image_version_', 40),
            'version': '0.1.0'
        })

        # Prepare image in another tenant
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


    @ResourceGroupPreparer(location='eastus')
    def test_create_vm_with_shared_gallery_image(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': self.create_random_name('vm', 16),
            'vm_with_shared_gallery': self.create_random_name('vm_sg', 16),
            'vm_with_shared_gallery_version': self.create_random_name('vm_sgv', 16),
            'vm_with_shared_gallery_version2': self.create_random_name('vm_sgv2', 16),
            'vmss_with_shared_gallery_version': self.create_random_name('vmss', 16),
            'gallery': self.create_random_name('gellery', 16),
            'image': self.create_random_name('image', 16),
            'version': '1.1.2',
            'captured': 'managedImage1',
            'location': resource_group_location,
            'subId': '0b1f6471-1bf0-4dda-aec3-cb9272f09590',  # share the gallery to tester's subscription, so the tester can get shared galleries
            'tenantId': '2f4a9838-26b7-47ee-be60-ccc1fdec5953',
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --permissions groups')
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --data-disk-sizes-gb 10 --admin-username clitest1 --generate-ssh-key --nsg-rule None')
        if self.is_live:
            time.sleep(70)
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')

        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1')
        self.kwargs['unique_name'] = self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions').get_output_in_json()['identifier']['uniqueName']

        self.cmd('sig share add --gallery-name {gallery} -g {rg} --subscription-ids {subId} --tenant-ids {tenantId}')

        self.kwargs['shared_gallery_image_version'] = self.cmd('sig image-version show-shared --gallery-image-definition {image} --gallery-unique-name {unique_name} --location {location} --gallery-image-version {version}').get_output_in_json()['uniqueId']

        self.cmd('vm create -g {rg} -n {vm_with_shared_gallery_version} --image {shared_gallery_image_version} --admin-username clitest1 --generate-ssh-key --nsg-rule None')

        self.cmd('vm show -g {rg} -n {vm_with_shared_gallery_version}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('storageProfile.imageReference.sharedGalleryImageId', '{shared_gallery_image_version}'),
        ])

        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vm create -g {rg} -n {vm_with_shared_gallery_version2} --image {shared_gallery_image_version} --admin-username clitest1 --generate-ssh-key --nsg-rule None --os-type windows')

        self.cmd('vmss create -g {rg} -n {vmss_with_shared_gallery_version} --image {shared_gallery_image_version} --generate-ssh-keys --admin-username clitest1 ')

        self.cmd('vmss show -g {rg} -n {vmss_with_shared_gallery_version}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.storageProfile.imageReference.sharedGalleryImageId', '{shared_gallery_image_version}'),
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery} -g {rg}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
        ])


    @ResourceGroupPreparer(location='westus')
    def test_gallery_soft_delete(self, resource_group):
        self.kwargs.update({
            'gallery_name': self.create_random_name('sig_', 10)
        })

        self.cmd('sig create -g {rg} -r {gallery_name} --soft-delete True', checks=[
            self.check('location', 'westus'),
            self.check('name', '{gallery_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('softDeletePolicy.isSoftDeleteEnabled', True)
        ])

        self.cmd('sig show -g {rg} -r {gallery_name} --sharing-groups', checks=[
            self.check('location', 'westus'),
            self.check('name', '{gallery_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('softDeletePolicy.isSoftDeleteEnabled', True),
            self.check('sharingProfile.groups', None)
        ])

        self.cmd('sig update -g {rg} -r {gallery_name} --soft-delete False', checks=[
            self.check('location', 'westus'),
            self.check('name', '{gallery_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('softDeletePolicy.isSoftDeleteEnabled', False)
        ])

        self.cmd('sig show -g {rg} -r {gallery_name}', checks=[
            self.check('location', 'westus'),
            self.check('name', '{gallery_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('softDeletePolicy.isSoftDeleteEnabled', False)
        ])

        self.cmd('sig delete -g {rg} -r {gallery_name}')


    @ResourceGroupPreparer(location='eastus')
    def test_replication_mode(self, resource_group):
        self.kwargs.update({
            'sig_name': self.create_random_name('sig_', 10),
            'img_def_name': self.create_random_name('def_', 10),
            'pub_name': self.create_random_name('pub_', 10),
            'of_name': self.create_random_name('of_', 10),
            'sku_name': self.create_random_name('sku_', 10),
            'vm_name': self.create_random_name('vm_', 10),
            'img_name': self.create_random_name('img_', 10),
            'img_ver_name': self.create_random_name('ver_', 10)
        })
        self.cmd('sig create -g {rg} -r {sig_name}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {sig_name} '
                 '--gallery-image-definition {img_def_name} --os-type linux -p {pub_name} -f {of_name} -s {sku_name}')
        self.cmd('vm create -g {rg} -n {vm_name} --image Ubuntults --admin-username vmtest')
        self.cmd('vm deallocate -g {rg} -n {vm_name}')
        self.cmd('vm generalize -g {rg} -n {vm_name}')
        self.cmd('image create -g {rg} -n {img_name} --source {vm_name}')
        self.cmd('sig image-version create --replication-mode Full -g {rg} -r {sig_name}'
                 ' -i {img_def_name} -e 1.1.1 --managed-image {img_name}', checks=[
            self.check('name', '1.1.1'),
            self.check('publishingProfile.replicationMode', 'Full')
        ])
        self.cmd('sig image-version show -g {rg} -r {sig_name} -i {img_def_name} -e 1.1.1', checks=[
            self.check('name', '1.1.1'),
            self.check('publishingProfile.replicationMode', 'Full')
        ])
        self.cmd('sig image-version create --replication-mode Shallow -g {rg} -r {sig_name}'
                 ' -i {img_def_name} -e 1.1.2 --managed-image {img_name}', checks=[
            self.check('name', '1.1.2'),
            self.check('publishingProfile.replicationMode', 'Shallow')
        ])
        self.cmd('sig image-version show -g {rg} -r {sig_name} -i {img_def_name} -e 1.1.2', checks=[
            self.check('name', '1.1.2'),
            self.check('publishingProfile.replicationMode', 'Shallow')
        ])

    @ResourceGroupPreparer(location='CentralUSEUAP')
    def test_community_gallery_operations(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': self.create_random_name('vm', 16),
            'gallery': self.create_random_name('gellery', 16),
            'image': self.create_random_name('image', 16),
            'version': '1.1.2',
            'captured': 'managedImage1',
            'location': resource_group_location,
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --permissions Community --publisher-uri puburi --publisher-email abc@123.com --eula eula --public-name-prefix pubname')
        self.cmd('sig share enable-community -r {gallery} -g {rg}')

        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username gallerytest --generate-ssh-keys --nsg-rule None')
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')

        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1')
        self.kwargs['public_name'] = self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions').get_output_in_json()['sharingProfile']['communityGalleryInfo']['publicNames'][0]

        self.cmd('sig show-community --location {location} --public-gallery-name {public_name}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{public_name}'),
            self.check('uniqueId', '/CommunityGalleries/{public_name}')
        ])

        self.cmd('sig image-definition show-community --gallery-image-definition {image} --public-gallery-name {public_name} --location {location}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{image}'),
            self.check('uniqueId', '/CommunityGalleries/{public_name}/Images/{image}')
        ])

        self.cmd('sig image-definition list-community --public-gallery-name {public_name} --location {location}', checks=[
            self.check('[0].location', '{location}'),
            self.check('[0].name', '{image}'),
            self.check('[0].uniqueId', '/CommunityGalleries/{public_name}/Images/{image}')
        ])

        self.kwargs['community_gallery_image_version'] = self.cmd('sig image-version show-community --gallery-image-definition {image} --public-gallery-name {public_name} --location {location} --gallery-image-version {version}', checks=[
            self.check('location', '{location}'),
            self.check('name', '{version}'),
            self.check('uniqueId', '/CommunityGalleries/{public_name}/Images/{image}/Versions/{version}')
        ]).get_output_in_json()['uniqueId']

        self.cmd('sig image-version list-community --gallery-image-definition {image} --public-gallery-name {public_name} '
                 '--location {location}', checks=[
            self.check('[0].location', '{location}'),
            self.check('[0].name', '{version}'),
            self.check('[0].uniqueId', '/CommunityGalleries/{public_name}/Images/{image}/Versions/{version}')
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery} -g {rg}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
        ])

    @ResourceGroupPreparer(location='eastus2')
    def test_create_vm_with_community_gallery_image(self, resource_group, resource_group_location):
        self.kwargs.update({
            'vm': self.create_random_name('vm', 16),
            'vm_with_community_gallery': self.create_random_name('vm_sg', 16),
            'vmss_with_community_gallery_version': self.create_random_name('vmss', 16),
            'gallery': self.create_random_name('gellery', 16),
            'image': self.create_random_name('image', 16),
            'version': '1.1.2',
            'captured': 'managedImage1'
        })

        self.cmd('sig create -g {rg} --gallery-name {gallery} --permissions Community --publisher-uri puburi --publisher-email abc@123.com --eula eula --public-name-prefix pubname')
        self.cmd('sig share enable-community -r {gallery} -g {rg}')

        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1')
        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username gallerytest --generate-ssh-keys --nsg-rule None')
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm generalize -g {rg} -n {vm}')

        self.cmd('image create -g {rg} -n {captured} --source {vm}')
        self.cmd('sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1')
        self.kwargs['public_name'] = self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions').get_output_in_json()['sharingProfile']['communityGalleryInfo']['publicNames'][0]

        self.cmd('sig image-version show-community --gallery-image-definition {image} --public-gallery-name {public_name} -l eastus2 --gallery-image-version {version}',
            checks=[
                self.check('name', '{version}'),
                self.check('uniqueId', '/CommunityGalleries/{public_name}/Images/{image}/Versions/{version}')
            ])

        self.kwargs['community_gallery_image_version'] = self.cmd('sig image-version show-community --gallery-image-definition {image} --public-gallery-name {public_name} --location eastus2 --gallery-image-version {version}').get_output_in_json()['uniqueId']
        self.cmd('vm create -g {rg} -n {vm_with_community_gallery} --image {community_gallery_image_version} --admin-username gallerytest --generate-ssh-keys --nsg-rule None --accept-term')

        self.cmd('vm show -g {rg} -n {vm_with_community_gallery}', checks=[
            self.check('storageProfile.imageReference.exactVersion','{version}'),
            self.check('storageProfile.imageReference.communityGalleryImageId', '{community_gallery_image_version}')
        ])

        self.cmd('vmss create -g {rg} -n {vmss_with_community_gallery_version} --admin-username gallerytest --generate-ssh-keys --image {community_gallery_image_version} --accept-term')

        self.cmd('vmss show -g {rg} -n {vmss_with_community_gallery_version}', checks=[
            self.check('virtualMachineProfile.storageProfile.imageReference.communityGalleryImageId', '{community_gallery_image_version}')
        ])

        # gallery permissions must be reset, or the resource group can't be deleted
        self.cmd('sig share reset --gallery-name {gallery} -g {rg}')
        self.cmd('sig show --gallery-name {gallery} --resource-group {rg} --select Permissions', checks=[
            self.check('sharingProfile.permissions', 'Private')
        ])


class VMGalleryApplication(ScenarioTest):
    @ResourceGroupPreparer(location='eastus')
    def test_gallery_application(self, resource_group, resource_group_location):
        self.kwargs.update({
            'app_name': self.create_random_name('app', 10),
            'gallery': self.create_random_name('gellery', 16),
        })

        self.cmd('sig create -r {gallery} -g {rg}')
        self.cmd('sig gallery-application create -n {app_name} -r {gallery} --os-type windows -g {rg}', checks=[
            self.check('name', '{app_name}'),
            self.check('supportedOsType', 'Windows'),
            self.check('description', None),
            self.check('tags', None),
            self.check('type', 'Microsoft.Compute/galleries/applications')
        ])
        self.cmd('sig create -r {gallery} -g {rg}')
        self.cmd('sig gallery-application update -n {app_name} -r {gallery} -g {rg} --description test --tags tag=test', checks=[
            self.check('name', '{app_name}'),
            self.check('supportedOsType', 'Windows'),
            self.check('description', 'test'),
            self.check('tags', {'tag': 'test'})
        ])
        self.cmd('sig gallery-application list -r {gallery} -g {rg}', checks=[
            self.check('[0].name', '{app_name}'),
            self.check('[0].supportedOsType', 'Windows'),
            self.check('[0].description', 'test'),
            self.check('[0].tags', {'tag': 'test'})
            ])
        self.cmd('sig gallery-application show -n {app_name} -r {gallery} -g {rg}', checks=[
            self.check('name', '{app_name}'),
            self.check('supportedOsType', 'Windows'),
            self.check('description', 'test'),
            self.check('tags', {'tag': 'test'})
        ])
        self.cmd('sig gallery-application delete -n {app_name} -r {gallery} -g {rg} -y')
        self.cmd('sig gallery-application list -r {gallery} -g {rg}', checks=self.is_empty())

    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus', name_prefix='account', length=15)
    def test_gallery_application_version(self, resource_group, resource_group_location, storage_account_info):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'app_name': self.create_random_name('app', 10),
            'gallery': self.create_random_name('gellery', 15),
            'ver_name': "1.0.0",
            'account': storage_account_info[0],
            'storage_key': storage_account_info[1],
            'container': self.create_random_name('container', 15),
            'blob': self.create_random_name('blob', 15),
            'f1': os.path.join(curr_dir, 'my_app_installer.txt').replace('\\', '\\\\')
        })
        self.cmd('sig create -r {gallery} -g {rg}')
        self.cmd('sig gallery-application create -n {app_name} -r {gallery} --os-type windows -g {rg}', checks=[
            self.check('name', '{app_name}'),
            self.check('supportedOsType', 'Windows'),
            self.check('description', None),
            self.check('tags', None),
            self.check('type', 'Microsoft.Compute/galleries/applications')
        ])
        self.cmd('storage container create -g {rg} --account-name {account} -n {container} --public-access blob --account-key {storage_key}')
        self.cmd('storage blob upload -n {blob} --account-name {account} --container-name {container} --file {f1} --type page --account-key {storage_key}')
        self.cmd('sig gallery-application version create -n {ver_name} --application-name {app_name} -r {gallery} -g {rg} --package-file-link https://{account}.blob.core.windows.net/{container}/{blob} --install-command install  --remove-command remove', checks=[
             self.check('name', '1.0.0'),
             self.check('publishingProfile.manageActions.install', 'install'),
             self.check('publishingProfile.manageActions.remove', 'remove'),
             self.check('type', 'Microsoft.Compute/galleries/applications/versions')
        ])
        self.cmd('sig gallery-application version update -n {ver_name} --application-name {app_name} -r {gallery} -g {rg} --package-file-link https://{account}.blob.core.windows.net/{container}/{blob} --tags tag=test', checks=[
            self.check('name', '1.0.0'),
            self.check('publishingProfile.manageActions.install', 'install'),
            self.check('publishingProfile.manageActions.remove', 'remove'),
            self.check('tags', {'tag': 'test'})
        ])
        self.cmd('sig gallery-application version list -r {gallery} --application-name {app_name} -g {rg}', checks=[
            self.check('[0].name', '1.0.0'),
            self.check('[0].publishingProfile.manageActions.install', 'install'),
            self.check('[0].publishingProfile.manageActions.remove', 'remove'),
            self.check('[0].tags', {'tag': 'test'}),
        ])
        self.cmd('sig gallery-application version show -n {ver_name} --application-name {app_name} -r {gallery} -g {rg}', checks=[
            self.check('name', '1.0.0'),
            self.check('publishingProfile.manageActions.install', 'install'),
            self.check('publishingProfile.manageActions.remove', 'remove'),
            self.check('tags', {'tag': 'test'}),
        ])
        self.cmd('sig gallery-application version delete -n {ver_name} --application-name {app_name} -r {gallery} -g {rg} -y')
        self.cmd('sig gallery-application version list -r {gallery} --application-name {app_name} -g {rg}', checks=self.is_empty())
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
            'ssh_key': TEST_SSH_KEY_PUB
        })

        self.kwargs['ppg_id'] = self.cmd('ppg create -n {ppg} -t standard -g {rg}').get_output_in_json()['id']

        self.kwargs['vm_id'] = self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\' --ppg {ppg} --nsg-rule NONE').get_output_in_json()['id']

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

        self.cmd('vm create -g {rg} -n {vm} --image debian --admin-username debian --ssh-key-value \'{ssh_key}\' --nsg-rule NONE')
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

    @ResourceGroupPreparer(name_prefix='cli_test_vm_host_ultra_ssd_')
    def test_vm_host_ultra_ssd(self, resource_group):
        self.kwargs.update({
            'host-group': self.create_random_name('host', 10)
        })
        self.cmd('vm host group create -n {host-group} -g {rg} --ultra-ssd-enabled true -c 1 -l eastus2euap --zone 3', checks=[
            self.check('additionalCapabilities.ultraSsdEnabled', True)
        ])

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

        self.cmd('vm create -n {vm-name} --image debian -g {rg} --size Standard_D4s_v3 '
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
        self.cmd('vm create -g {rg} -n vm1 --image centos --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
        self.cmd('vm create -g {rg} -n vm2 --image centos --size Standard_D4s_v3 --nsg-rule NONE --generate-ssh-keys --admin-username azureuser')
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
        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --priority Low --eviction-policy Deallocate --max-price 50 --admin-username azureuser --admin-password testPassword0 --authentication-type password --nsg-rule NONE')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('priority', 'Low'),
            self.check('evictionPolicy', 'Deallocate'),
            self.check('billingProfile.maxPrice', 50)
        ])

        # Can't create lb in testing subscription
        # vmss create
        # self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --lb-sku Standard --priority Low --eviction-policy Deallocate --max-price 50 --admin-username azureuser --admin-password testPassword0 --authentication-type password', checks=[
        #     self.check('vmss.virtualMachineProfile.priority', 'Low'),
        #     self.check('vmss.virtualMachineProfile.evictionPolicy', 'Deallocate'),
        #     self.check('vmss.virtualMachineProfile.billingProfile.maxPrice', 50)
        # ])

        # vm update
        self.cmd('vm deallocate -g {rg} -n {vm}')
        self.cmd('vm update -g {rg} -n {vm} --priority Spot --max-price 100', checks=[
            self.check('priority', 'Spot'),
            self.check('billingProfile.maxPrice', 100)
        ])

        # vmss update
        # self.cmd('vmss deallocate -g {rg} -n {vmss}')
        # self.cmd('vmss update -g {rg} -n {vmss} --priority Spot --max-price 100', checks=[
        #     self.check('virtualMachineProfile.priority', 'Spot'),
        #     self.check('virtualMachineProfile.billingProfile.maxPrice', 100)
        # ])


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

        self.cmd('vm create -g {rg} -n {vm} --image UbuntuLTS --admin-username azureuser --admin-password testPassword0 --authentication-type password --nsg-rule NONE')
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
    @KeyVaultPreparer(name_prefix='vault-', name_len=20, key='vault', location='westcentralus', additional_params='--enable-purge-protection')
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
    @KeyVaultPreparer(name_prefix='vault1-', name_len=20, key='vault1', parameter_name='key_vault1', location='westcentralus', additional_params='--enable-purge-protection')
    @KeyVaultPreparer(name_prefix='vault2-', name_len=20, key='vault2', parameter_name='key_vault2', location='westcentralus', additional_params='--enable-purge-protection')
    @KeyVaultPreparer(name_prefix='vault3-', name_len=20, key='vault3', parameter_name='key_vault3', location='westcentralus', additional_params='--enable-purge-protection')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_update(self, resource_group, key_vault1, key_vault2):

        self.kwargs.update({
            'key1': self.create_random_name(prefix='key1-', length=20),
            'key2': self.create_random_name(prefix='key2-', length=20),
            'key3': self.create_random_name(prefix='key3-', length=20),
            'des': self.create_random_name(prefix='des-', length=20),
            'des2': self.create_random_name(prefix='des-', length=20)
        })

        kid1 = self.cmd('keyvault key create -n {key1} --vault {vault1} --protection software').get_output_in_json()['key']['kid']
        vault2_id = self.cmd('keyvault show -g {rg} -n {vault2}').get_output_in_json()['id']
        vault3_id = self.cmd('keyvault show -g {rg} -n {vault3}').get_output_in_json()['id']
        kid2 = self.cmd('keyvault key create -n {key2} --vault {vault2} --protection software').get_output_in_json()['key']['kid']
        kid3 = self.cmd('keyvault key create -n {key3} --vault {vault3} --protection software').get_output_in_json()['key']['kid']

        self.kwargs.update({
            'kid1': kid1,
            'vault2_id': vault2_id,
            'vault3_id': vault3_id,
            'kid2': kid2,
            'kid3': kid3
        })

        self.cmd('disk-encryption-set create -g {rg} -n {des} --key-url {kid1} --source-vault {vault1} --enable-auto-key-rotation true')
        des_show_output = self.cmd('disk-encryption-set show -g {rg} -n {des}').get_output_in_json()
        self.assertEqual(des_show_output['rotationToLatestKeyVersionEnabled'], True)
        des_sp_id = des_show_output['identity']['principalId']
        des_id = des_show_output['id']
        self.kwargs.update({
            'des_sp_id': des_sp_id,
            'des_id': des_id
        })

        self.cmd('keyvault set-policy -n {vault2} --object-id {des_sp_id} --key-permissions wrapKey unwrapKey get')
        time.sleep(30)
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des_sp_id} --role Reader --scope {vault2_id}')
        time.sleep(30)

        self.cmd('disk-encryption-set update -g {rg} -n {des} --source-vault {vault2} --key-url {kid2} --enable-auto-key-rotation false', checks=[
            self.check('activeKey.keyUrl', '{kid2}'),
            self.check('activeKey.sourceVault.id', '{vault2_id}'),
            self.check('rotationToLatestKeyVersionEnabled', False)
        ])

        self.cmd('disk-encryption-set delete -g {rg} -n {des}')

        self.cmd('disk-encryption-set create -g {rg} -n {des2} --key-url {kid3} --enable-auto-key-rotation true', checks=[
            self.check('activeKey.sourceVault', None)
        ])

        des2_sp_id = self.cmd('disk-encryption-set show -g {rg} -n {des2}').get_output_in_json()['identity']['principalId']
        self.kwargs.update({
            'des2_sp_id': des2_sp_id,
        })
        self.cmd('keyvault set-policy -n {vault3} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('disk-encryption-set update -g {rg} -n {des2} --source-vault {vault3}', checks=[
            self.check('activeKey.sourceVault.id', '{vault3_id}')
        ])
        self.cmd('disk-encryption-set delete -n {des2} -g{rg}')

        self.cmd('disk-encryption-set create -g {rg} -n {des2} --key-url {kid3} --enable-auto-key-rotation true',
                 checks=[
                     self.check('activeKey.sourceVault', None)
                 ])

        des2_sp_id = self.cmd('disk-encryption-set show -g {rg} -n {des2}').get_output_in_json()['identity'][
            'principalId']
        self.kwargs.update({
            'des2_sp_id': des2_sp_id,
        })
        self.cmd('keyvault set-policy -n {vault2} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('disk-encryption-set update -g {rg} -n {des2} --key-url {kid2}', checks=[
            self.check('activeKey.keyUrl', '{kid2}'),
            self.check('activeKey.sourceVault', None)
        ])
        self.cmd('keyvault set-policy -n {vault3} --object-id {des2_sp_id} --key-permissions wrapKey unwrapKey get')
        self.cmd('disk-encryption-set update -g {rg} -n {des2} --key-url {kid3} --source-vault {vault3} --enable-auto-key-rotation false', checks=[
            self.check('activeKey.keyUrl', '{kid3}'),
            self.check('activeKey.sourceVault.id', '{vault3_id}'),
            self.check('rotationToLatestKeyVersionEnabled', False)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_disk_update_', location='eastus')
    @KeyVaultPreparer(name_prefix='vault3-', name_len=20, key='vault', location='eastus', additional_params='--enable-purge-protection')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_disk_update(self, resource_group, key_vault):
        self.kwargs.update({
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'image-reference': 'Debian:debian-10:10:latest',
            'disk': self.create_random_name(prefix='disk-', length=20),
            'disk2': self.create_random_name(prefix='disk-', length=20),
        })

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

        self.cmd('keyvault set-policy -n {vault} --object-id {des1_sp_id} --key-permissions wrapKey unwrapKey get')

        time.sleep(15)

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            self.cmd('role assignment create --assignee {des1_sp_id} --role Reader --scope {vault_id}')

        time.sleep(15)

        self.kwargs.update({
            'des1_pattern': '.*/{}$'.format(self.kwargs['des1'])
        })

        self.cmd('disk create -g {rg} -n {disk} --image-reference {image-reference}')
        self.cmd('disk update -g {rg} -n {disk} --disk-encryption-set {des1} --encryption-type EncryptionAtRestWithCustomerKey', checks=[
            self.check_pattern('encryption.diskEncryptionSetId', self.kwargs['des1_pattern']),
            self.check('encryption.type', 'EncryptionAtRestWithCustomerKey')
        ])

        self.cmd('disk create -g {rg} -n {disk2} --source {disk} --encryption-type EncryptionAtRestWithPlatformKey', checks=[
            self.check('encryption.diskEncryptionSetId', 'None'),
            self.check('encryption.type', 'EncryptionAtRestWithPlatformKey')
        ])
        self.cmd('disk update -g {rg} -n {disk} --encryption-type EncryptionAtRestWithPlatformKey', checks=[
            self.check('encryption.diskEncryptionSetId', 'None'),
            self.check('encryption.type', 'EncryptionAtRestWithPlatformKey')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_encryption_set_snapshot_', location='westcentralus')
    @KeyVaultPreparer(name_prefix='vault4-', name_len=20, key='vault', location='westcentralus', additional_params='--enable-purge-protection')
    @AllowLargeResponse(size_kb=99999)
    def test_disk_encryption_set_snapshot(self, resource_group, key_vault):
        self.kwargs.update({
            'key': self.create_random_name(prefix='key-', length=20),
            'des1': self.create_random_name(prefix='des1-', length=20),
            'des2': self.create_random_name(prefix='des2-', length=20),
            'snapshot1': self.create_random_name(prefix='snapshot1-', length=20),
            'snapshot2': self.create_random_name(prefix='snapshot2-', length=20),
        })

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

        self.cmd('disk-encryption-set list-associated-resources -g {rg} -n {des2}', checks=[
            self.check('length(@)', 1)
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
            self.check('name', '{disk}'),
            self.check('networkAccessPolicy', 'AllowPrivate')
        ])

        self.cmd('snapshot create -g {rg} -n {snapshot} --size-gb 10 --network-access-policy AllowPrivate --disk-access {diskaccess}')

        self.cmd('snapshot update -g {rg} -n {snapshot} --network-access-policy AllowPrivate --disk-access {disk_access_id}')

        self.cmd('snapshot show -g {rg} -n {snapshot}', checks=[
            self.check('name', '{snapshot}'),
            self.check('networkAccessPolicy', 'AllowPrivate')
        ])

        self.cmd('disk delete -g {rg} -n {disk} --yes')
        self.cmd('snapshot delete -g {rg} -n {snapshot}')
        self.cmd('disk-access delete -g {rg} -n {diskaccess}')
        self.cmd('disk-access list -g {rg}', checks=[
            self.check('length(@)', 0)
        ])


class DiskBurstingTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_disk_busrting_', location='eastus')
    def test_disk_bursting(self, resource_group):
        self.kwargs.update({
            'disk1': 'mydisk1',
            'disk2': 'mydisk2'
        })

        self.cmd('disk create -g {rg} -n {disk1} --size-gb 1024 --location centraluseuap --enable-bursting')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('burstingEnabled', True)
        ])
        self.cmd('disk create -g {rg} -n {disk2} --size-gb 1024 --location centraluseuap')
        self.cmd('disk show -g {rg} -n {disk2}', checks=[
            self.check('name', '{disk2}'),
            self.check('burstingEnabled', None)
        ])
        self.cmd('disk update -g {rg} -n {disk2} --enable-bursting')
        self.cmd('disk show -g {rg} -n {disk2}', checks=[
            self.check('name', '{disk2}'),
            self.check('burstingEnabled', True)
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
                 '--storage-sku UltraSSD_LRS --location eastus --admin-username azureuser --lb ""',
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
                     self.check('virtualMachineProfile.storageProfile.dataDisks[0].diskMBpsReadWrite', '66'),
                     self.check('virtualMachineProfile.storageProfile.dataDisks[1].diskMBpsReadWrite', '77'),
                 ])


class VMCreateAutoCreateSubnetScenarioTest(ScenarioTest):

    @AllowLargeResponse()
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
        self.cmd('vm create --resource-group {rg} --location {loc} --name {vm} --admin-username ubuntu --image UbuntuLTS --admin-password testPassword0 --authentication-type password --vnet-name {vnet} --nsg-rule NONE')

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
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --automatic-repairs-grace-period 30 --admin-username azureuser')
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --load-balancer {lb} --automatic-repairs-grace-period 30 --admin-username azureuser')
        with self.assertRaises(ArgumentUsageError):
            self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --health-probe {probe} --automatic-repairs-grace-period 30 --admin-username azureuser')

        # Prepare health probe
        self.cmd('network lb create -g {rg} -n {lb}')
        self.cmd('network lb probe create -g {rg} --lb-name {lb} -n {probe} --protocol Tcp --port 80')
        self.cmd('network lb rule create -g {rg} --lb-name {lb} -n {lbrule} --probe-name {probe} --protocol Tcp --frontend-port 80 --backend-port 80')
        # Test enable automatic repairs with a health probe when create vmss
        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --load-balancer {lb} --health-probe {probe} --automatic-repairs-grace-period 30  --automatic-repairs-action restart --admin-username azureuser',
                 checks=[
                     self.check('vmss.automaticRepairsPolicy.enabled', True),
                     self.check('vmss.automaticRepairsPolicy.gracePeriod', 'PT30M'),
                     self.check('vmss.automaticRepairsPolicy.repairAction', 'Restart')
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
        with self.assertRaises(ArgumentUsageError):
            self.cmd(
                'vmss update -g {rg} -n {vmss} --enable-automatic-repairs false --automatic-repairs-grace-period 30')
        with self.assertRaises(ArgumentUsageError):
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
        self.cmd('vmss update -g {rg} -n {vmss} --enable-automatic-repairs true --automatic-repairs-grace-period 30 --automatic-repairs-action restart',
                 checks=[
                     self.check('automaticRepairsPolicy.enabled', True),
                     self.check('automaticRepairsPolicy.gracePeriod', 'PT30M'),
                     self.check('automaticRepairsPolicy.repairAction', 'Restart')
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

        self.cmd('vm auto-shutdown -g {rg} -n {vm} --time 1730 --email "foo2@bar.com" ', checks=[
            self.check('name', 'shutdown-computevm-{vm}'),
            self.check('taskType', 'ComputeVmShutdownTask'),
            self.check('status', 'Enabled'),
            self.check('dailyRecurrence.time', '1730'),
            self.check('notificationSettings.status', 'Enabled'),
            self.check('notificationSettings.emailRecipient', 'foo2@bar.com')
        ])

        self.cmd('vm auto-shutdown -g {rg} -n {vm} --off')


class VMSSOrchestrationModeScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_orchestration_mode_', location='westus')
    def test_vmss_simple_orchestration_mode(self, resource_group):
        self.kwargs.update({
            'ppg': 'ppg1',
            'vmss': 'vmss1',
            'vm': 'vm1'
        })

        self.cmd('ppg create -g {rg} -n {ppg}')
        self.cmd('vmss create -g {rg} -n {vmss} --orchestration-mode Flexible --single-placement-group false '
                 '--ppg {ppg} --platform-fault-domain-count 3',
                 checks=[
                     self.check('vmss.singlePlacementGroup', False),
                     self.check('vmss.platformFaultDomainCount', 3)
                 ])

        self.cmd('vm create -g {rg} -n {vm} --image centos --platform-fault-domain 0 --vmss {vmss} --generate-ssh-keys --nsg-rule None --admin-username vmtest')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('platformFaultDomain', 0)
        ])


    @ResourceGroupPreparer(name_prefix='cli_test_simple_placement')
    def test_vmss_simple_placement(self, resource_group):
        self.kwargs.update({
            'vmss': self.create_random_name('vmss', 10),
        })
        self.cmd('vmss create -g {rg} -n {vmss} --orchestration-mode Flexible --platform-fault-domain-count 2 '
                 '--single-placement-group true --image UbuntuLTS --vm-sku Standard_M8ms --admin-username clitest '
                 '-l eastus2euap --upgrade-policy-mode automatic', checks=[
            self.check('vmss.singlePlacementGroup', True),
            self.check('vmss.platformFaultDomainCount', 2),
        ])


    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_orchestration_mode_', location='eastus2euap')
    @VirtualNetworkPreparer(location='eastus2euap', parameter_name='virtual_network')
    def test_vmss_complex_orchestration_mode(self, resource_group, virtual_network):

        self.kwargs.update({
            'vmss0': self.create_random_name(prefix='vmss0', length=10),
            'vmss1': self.create_random_name(prefix='vmss1', length=10),
            'vnet_name': virtual_network,
            'vmss2': self.create_random_name(prefix='vmss2', length=10),
            'vmss3': self.create_random_name(prefix='vmss3', length=10),
            'vmss4': self.create_random_name(prefix='vmss4', length=10),
            'vmss5': self.create_random_name(prefix='vmss5', length=10),
            'ssh_key': TEST_SSH_KEY_PUB
        })

        # test without authentication info
        self.cmd('vmss create -n {vmss0} -g {rg} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --image ubuntults '
                 '--computer-name-prefix testvmss --vnet-name {vnet_name} --subnet default --network-api-version '
                 '2020-11-01 --admin-username testvmss ')

        self.cmd('vmss show -g {rg} -n {vmss0}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.exists('virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux')
        ])

        # test with password
        self.cmd('vmss create -g {rg} -n {vmss1} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --admin-username testvmss '
                 '--admin-password This!s@Terr!bleP@ssw0rd --computer-name-prefix testvmss --image debian '
                 '--vnet-name {vnet_name} --subnet default --network-api-version 2020-11-01')

        self.cmd('vmss show -g {rg} -n {vmss1}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux'),
        ])

        # test with ssh
        self.cmd('vmss create -n {vmss2} -g {rg} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --image ubuntults '
                 '--computer-name-prefix testvmss --vnet-name {vnet_name} --subnet default --network-api-version '
                 '2020-11-01 --admin-username testvmss --generate-ssh-keys ')

        self.cmd('vmss show -g {rg} -n {vmss2}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.exists('virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux')
        ])

        # test with ssh path
        self.cmd('vmss create -n {vmss3} -g {rg} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --image ubuntults '
                 '--computer-name-prefix testvmss --vnet-name {vnet_name} --subnet default --network-api-version '
                 '2020-11-01 --admin-username testvmss --generate-ssh-keys ')

        self.cmd('vmss show -g {rg} -n {vmss3}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.exists('virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux')
        ])

        # test with ssh value
        self.cmd('vmss create -n {vmss4} -g {rg} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --image ubuntults '
                 '--computer-name-prefix testvmss --vnet-name {vnet_name} --subnet default --network-api-version '
                 '2020-11-01 --admin-username testvmss --ssh-key-value \'{ssh_key}\' ')

        self.cmd('vmss show -g {rg} -n {vmss4}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.exists('virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux')
        ])

        # test with authentication type
        self.cmd('vmss create -n {vmss5} -g {rg} --orchestration-mode Flexible --single-placement-group false '
                 '--platform-fault-domain-count 1 --vm-sku Standard_DS1_v2 --instance-count 0 --image ubuntults '
                 '--computer-name-prefix testvmss --vnet-name {vnet_name} --subnet default --network-api-version '
                 '2020-11-01 --admin-username testvmss --authentication-type ssh ')

        self.cmd('vmss show -g {rg} -n {vmss5}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('platformFaultDomainCount', 1),
            self.check('singlePlacementGroup', False),
            self.check('sku.capacity', 0),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('virtualMachineProfile.osProfile.adminUsername', 'testvmss'),
            self.exists('virtualMachineProfile.osProfile.linuxConfiguration.ssh.publicKeys'),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', 'testvmss'),
            self.check('virtualMachineProfile.storageProfile.osDisk.managedDisk.storageAccountType', 'Premium_LRS'),
            self.check('virtualMachineProfile.storageProfile.osDisk.osType', 'Linux')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_quick_create_flexible_vmss_', location='eastus2euap')
    def test_quick_create_flexible_vmss(self, resource_group):

        self.kwargs.update({
            'vmss': 'vmsslongnametest',
        })

        from azure.cli.core.azclierror import ArgumentUsageError
        with self.assertRaisesRegex(ArgumentUsageError, 'please specify the --image when you want to specify the VM SKU'):
            self.cmd('vmss create -n {vmss} -g {rg} --orchestration-mode Flexible --platform-fault-domain-count 1 --zones 1 --instance-count 3 --vm-sku Standard_D1_v2')

        self.cmd('vmss create -n {vmss} -g {rg} --image ubuntults --orchestration-mode flexible --admin-username vmtest')

        self.cmd('vmss show -g {rg} -n {vmss}', checks=[
            self.check('orchestrationMode', 'Flexible'),
            self.check('sku.capacity', 2),
            self.check('sku.name', "Standard_DS1_v2"),
            self.check('sku.tier', "Standard"),
            self.check('singlePlacementGroup', False),
            self.check('virtualMachineProfile.networkProfile.networkApiVersion', '2020-11-01'),
            self.check('platformFaultDomainCount', 1),
            self.check('virtualMachineProfile.osProfile.computerNamePrefix', self.kwargs['vmss'][:8]),
        ])


class VMCrossTenantUpdateScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_', location='westus2')
    @ResourceGroupPreparer(name_prefix='cli_test_vm_cross_tenant_', location='westus2',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_vm_cross_tenant_update(self, resource_group, another_resource_group):
        self.kwargs.update({
            'location': 'westus2',
            'rg': resource_group,
            'another_rg': another_resource_group,
            'another_vm': self.create_random_name('cli_test_vm_cross_tenant_', 40),
            'image_name': self.create_random_name('cli_test_vm_cross_tenant_', 40),
            'aux_sub': AUX_SUBSCRIPTION,
            'aux_tenant': AUX_TENANT,
            'vm': self.create_random_name('cli_test_vm_cross_tenant_', 40)
        })

        # Prepare sig in another tenant
        self.cmd(
            'vm create -g {another_rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-keys --subscription {aux_sub}')
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


class VMSSCrossTenantUpdateScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_', location='westus2')
    @ResourceGroupPreparer(name_prefix='cli_test_vmss_update_', location='westus2',
                           parameter_name='another_resource_group', subscription=AUX_SUBSCRIPTION)
    def test_vmss_cross_tenant_update(self, resource_group, another_resource_group):
        self.kwargs.update({
            'location': 'westus2',
            'rg': resource_group,
            'another_rg': another_resource_group,
            'vm': self.create_random_name('cli_test_vmss_update_', 40),
            'image_name': self.create_random_name('cli_test_vmss_update_', 40),
            'aux_sub': AUX_SUBSCRIPTION,
            'aux_tenant': AUX_TENANT,
            'sig_name': self.create_random_name('cli_test_vmss_update_', 40),
            'image_definition_name_1': self.create_random_name('cli_test_vmss_update_', 40),
            'image_definition_name_2': self.create_random_name('cli_test_vmss_update_', 40),
            'version': '0.1.0',
            'vmss': 'cross_tenant_vmss',
        })

        # Prepare sig in another tenant
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

        # Test vmss can be update even if the image reference is not available
        self.cmd('vmss update -g {rg} -n {vmss} --set tags.foo=bar', checks=[
            self.check('tags.foo', 'bar')
        ])


class VMAutoUpdateScenarioTest(ScenarioTest):

    @unittest.skip('The selected VM image is not supported for hotpatching')
    @ResourceGroupPreparer(name_prefix='cli_test_vm_auto_update_')
    def test_vm_auto_update(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })

        self.cmd('vm create -g {rg} -n {vm} --image Win2022Datacenter --enable-agent --enable-auto-update --patch-mode AutomaticByPlatform --enable-hotpatching true --admin-username azureuser --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('osProfile.windowsConfiguration.enableAutomaticUpdates', True),
            self.check('osProfile.windowsConfiguration.patchSettings.patchMode', 'AutomaticByPlatform'),
            self.check('osProfile.windowsConfiguration.patchSettings.enableHotpatching', True)
        ])
        self.cmd('vm assess-patches -g {rg} -n {vm}', checks=[
            self.check('status', 'Succeeded')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_linux_vm_patch_mode_')
    def test_linux_vm_patch_mode(self, resource_group):
        self.cmd('vm create -g {rg} -n vm1 --image UbuntuLTS --enable-agent --patch-mode AutomaticByPlatform --generate-ssh-keys --nsg-rule NONE --admin-username vmtest')
        self.cmd('vm show -g {rg} -n vm1', checks=[
            self.check('osProfile.linuxConfiguration.patchSettings.patchMode', 'AutomaticByPlatform')
        ])


class VMSSPatchModeScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_window_patch_mode_')
    def test_vmss_windows_patch_mode(self, resource_group):
        self.kwargs.update({
            'vmss': self.create_random_name('clitestvmss', 20),
            'rg': resource_group
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image Win2022Datacenter --enable-agent --enable-auto-update false --patch-mode Manual --orchestration-mode Flexible --admin-username azureuser --admin-password testPassword0')
        vm = self.cmd('vmss list-instances -g {rg} -n {vmss}').get_output_in_json()[0]['name']
        self.kwargs['vm'] = vm

        # Due to the service bug that patch mode is not returned in response body, we need verify the patch mode of virtual machines inside the VMSS as a workaround.
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('osProfile.windowsConfiguration.enableAutomaticUpdates', False),
            self.check('osProfile.windowsConfiguration.patchSettings.patchMode', 'Manual')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_linux_patch_mode_')
    def test_vmss_linux_patch_mode(self, resource_group):
        self.kwargs.update({
            'vmss': self.create_random_name('clitestvmss', 20),
            'rg': resource_group
        })

        self.cmd('vmss create -g {rg} -n {vmss} --image UbuntuLTS --enable-agent --patch-mode ImageDefault --orchestration-mode Flexible --generate-ssh-keys --instance-count 0 --admin-username vmtest')

        curr_dir = os.path.dirname(os.path.realpath(__file__))
        health_extension_file = os.path.join(curr_dir, 'health_extension.json').replace('\\', '\\\\')
        self.kwargs['extension_file'] = health_extension_file

        # Health extension is required for the patch mode "AutomaticByPlatform".
        self.cmd('vmss extension set --name ApplicationHealthLinux --publisher Microsoft.ManagedServices --version 1.0 --resource-group {rg} --vmss-name {vmss} --settings {extension_file}')

        self.cmd('vmss update --name {vmss} --resource-group {rg} --set virtualMachineProfile.osProfile.linuxConfiguration.patchSettings.patchMode=AutomaticByPlatform')

        # Create a new VM to apply the new patch mode "AutomaticByPlatform".
        self.cmd('vmss scale --name {vmss} --new-capacity 1 --resource-group {rg}')

        vm = self.cmd('vmss list-instances -g {rg} -n {vmss}').get_output_in_json()[0]['name']
        self.kwargs['vm'] = vm

        # Due to the service bug that patch mode is not returned in response body, we need verify the patch mode of virtual machines inside the VMSS as a workaround.
        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('osProfile.linuxConfiguration.patchSettings.patchMode', 'AutomaticByPlatform')
        ])


class VMDiskLogicalSectorSize(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vm_disk_logical_sector_size_')
    def test_vm_disk_logical_sector_size(self, resource_group):
        self.cmd('disk create -g {rg} -n d1 --size-gb 10 --logical-sector-size 4096 --sku UltraSSD_LRS', checks=[
            self.check('creationData.logicalSectorSize', 4096)
        ])
        self.cmd('disk create -g {rg} -n d2 --size-gb 10 --tier P4', checks=[
            self.check('tier', 'P4')
        ])


class VMSSReimageScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_reimage_')
    def test_vmss_reimage(self, resource_group):
        self.cmd('vmss create -g {rg} -n vmss1 --image centos --admin-username vmtest')
        self.cmd('vmss reimage -g {rg} -n vmss1 --instance-id 1')
        self.cmd('vmss reimage -g {rg} -n vmss1')


class VMSSHKeyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_vm_ssh_key_')
    def test_vm_ssh_key(self, resource_group):
        self.kwargs.update({
            'key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC+MQ7LmEsaB7e/H63lCxJzrWdaLVhuUsnwXD5Eo7QpNhG6g9Oj9fKmZTSdHRpnUdVGtyRUJbmEHoeqFBBAt8bHu2bneEJeh8qfRmj0lCJA2QTZsdGlCsVlfSQzMjv/2WiOZ07pPGFVKvwsNS3dYQ1LtsNDAT4KE7ITlCcNjc+BjfWFTYOplAO++nruv+mD8zF1wwgTln/tHs7Ieja9Noon4PqnvyTYExPx7pclDjIPC+FzBrd9JBk+IUZyYPETO5F/LWh0M/+R656SCvHnXZ+xgan+V6nFJ0mGMErUrXUYMyYp8n/k5G5uxAiHjbS6b/+7HGbGLC0OUCBXLB0UyfIBo5ZtOgH9JKbRd2u7hjPBza7SY52JUsHbt7gZU46W35WjbDnW+clB+qLArHrsGr3YvkrEFn0IaD8y/7O9DW0PJFHM8iFZdZqmT+zM/BFse+p9El08MjPydTfKrZW4fzSBogI4oxY42CRDzxTl/WbpuGkjfcGfKwSoDbSy9jqjD/0=',
            'updated-key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC+4oSAGj8KYVXKmikS/sCD9zCTq1AqpK/jzKGhe6ujvl8B1JelAij9qkS7Maf6HdPjZmgChTbDcZmbfrOcT6opL/SCiFiGKgKi7cpL4Vo4K6DecHOtQ5cg4lUJrCDtSjuwwnuTsJvPym/AnBSW+OCGDkLC8CUdaMtdwLo6yYTSZ2fiRVTKz8/Kqv2HmXk4+M4T4U4V9enDepaCyZrFPdqaCZxzcQNQxNJhGpTGahDsCoFwsL8KNNPV3fXe12K0xJ1QEhd2MeCofDE1xkD0wr1BO5hMh7x5ui2JwOK/7BYyPNZ5Cr2UxzA/ty/L/I/qHTVoDCmaZT0gjXNp6zMz1bApJ91iGtQAr+WNsOhvXRYcTmwBzzBtMaFEYxNgv+O1qi8h++E+GH3d62NIp8rIya7JgBzjhmArefO4xSDqlQrl9vHliTBW8+58Mm0zWGMqODD3B13FG5B0f4KaZWiniDWiKNLosKsV08yK+eMulIuY2s8XvjqDifx8YPOQv+bYGL0='
        })
        self.cmd('sshkey create -g {rg} -n k1')
        self.cmd('sshkey list')
        self.cmd('sshkey show -g {rg} -n k1', checks=[
            self.check('name', 'k1'),
            self.exists('publicKey')
        ])
        self.cmd('sshkey create -g {rg} -n k2 --public-key "{key}"')
        self.cmd('sshkey update -g {rg} -n k2 --public-key "{updated-key}"')

        self.cmd('sshkey list -g {rg}', checks=[
            self.check('length(@)', 2)
        ])
        self.cmd('sshkey delete -g {rg} -n k2 --yes')
        self.cmd('sshkey list -g {rg}', checks=[
            self.check('length(@)', 1)
        ])

        # Use existing key
        self.cmd('vm create -g {rg} -n vm1 --image centos --nsg-rule None --ssh-key-name k1 --admin-username vmtest')

        # Create new one
        self.cmd('vm create -g {rg} -n vm3 --image centos --nsg-rule None --ssh-key-name k3 --generate-ssh-keys --admin-username vmtest')
        self.cmd('sshkey show -g {rg} -n k3')


class VMInstallPatchesScenarioTest(ScenarioTest):
    @unittest.skip('The selected VM image is not supported for VM Guest patch operations')
    @ResourceGroupPreparer(name_prefix='cli_test_vm_install_patches_')
    def test_vm_install_patches(self, resource_group):
        # Create new one
        self.cmd('vm create -g {rg} -n vm --image Win2022Datacenter --enable-hotpatching true --admin-username azureuser --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm install-patches -g {rg} -n vm --maximum-duration PT4H --reboot-setting IfRequired --classifications-to-include-win Critical Security --exclude-kbs-requiring-reboot true', checks=[
            self.check('status', 'Succeeded')
        ])

        self.cmd('vm create -g {rg} -n vm2 --image UbuntuLTS --enable-hotpatching true --admin-username azureuser --admin-password testPassword0 --nsg-rule NONE')
        self.cmd('vm install-patches -g {rg} -n vm2 --maximum-duration PT4H --reboot-setting IfRequired --classifications-to-include-linux Critical Security', checks=[
            self.check('status', 'Succeeded')
        ])


class VMTrustedLaunchScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_vm_trusted_launch_', location='southcentralus')
    def test_vm_trusted_launch(self, resource_group):
        self.cmd('vm create -g {rg} -n vm --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --enable-secure-boot true --enable-vtpm true --admin-username azureuser --admin-password testPassword0 --nsg-rule None --disable-integrity-monitoring')
        self.cmd('vm show -g {rg} -n vm', checks=[
            self.check('securityProfile.securityType', 'TrustedLaunch'),
            self.check('securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('securityProfile.uefiSettings.vTpmEnabled', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vm_trusted_launch_update_', location='southcentralus')
    def test_vm_trusted_launch_update(self, resource_group):
        self.cmd('vm create -g {rg} -n vm --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --admin-username azureuser --admin-password testPassword0 --nsg-rule None --disable-integrity-monitoring')
        self.cmd('vm update -g {rg} -n vm --enable-secure-boot true --enable-vtpm true')
        self.cmd('vm show -g {rg} -n vm', checks=[
            self.check('securityProfile.securityType', 'TrustedLaunch'),
            self.check('securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('securityProfile.uefiSettings.vTpmEnabled', True)
        ])

    # @unittest.skip('Service does not work')
    @ResourceGroupPreparer(name_prefix='cli_test_disk_trusted_launch_', location='southcentralus')
    def test_disk_trusted_launch(self):
        self.cmd('disk create -g {rg} -n d1 --image-reference Canonical:UbuntuServer:18_04-lts-gen2:18.04.202004290 --hyper-v-generation V2 --security-type TrustedLaunch', checks=[
            self.check('securityProfile.securityType', 'TrustedLaunch')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_trusted_launch_', location='southcentralus')
    def test_vmss_trusted(self, resource_group):
        self.cmd('vmss create -g {rg} -n vm --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --admin-username azureuser --admin-password testPassword0 --disable-integrity-monitoring')
        self.cmd('vmss update -g {rg} -n vm --enable-secure-boot true --enable-vtpm true')
        self.cmd('vmss show -g {rg} -n vm', checks=[
            self.check('virtualMachineProfile.securityProfile.securityType', 'TrustedLaunch'),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.vTpmEnabled', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_guest_attestation_extension_and_msi', location='westus')
    @AllowLargeResponse()
    def test_guest_attestation_extension_and_msi(self, resource_group):
        self.kwargs.update({
            'vm1': self.create_random_name('vm', 10),
            'vm2': self.create_random_name('vm', 10),
            'vm3': self.create_random_name('vm', 10),
            'id1': self.create_random_name('id', 10),
            'vmss1': self.create_random_name('vmss', 10),
            'vmss2': self.create_random_name('vmss', 10),

        })
        self.cmd('identity create -g {rg} -n {id1}')
        self.cmd('vm create --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --assign-identity {id1} [system] --admin-username azureuser -g {rg} -n {vm1} --enable-secure-boot --enable-vtpm')
        self.cmd('vm show -g {rg} -n {vm1}', checks=[
            self.check('identity.type', 'SystemAssigned, UserAssigned'),
            self.check('resources[0].name', 'GuestAttestation'),
            self.check('resources[0].publisher', 'Microsoft.Azure.Security.LinuxAttestation'),
            self.check('securityProfile.securityType', 'TrustedLaunch'),
            self.check('securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('securityProfile.uefiSettings.vTpmEnabled', True)

        ])
        self.cmd('vm create --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --admin-username azureuser -g {rg} -n {vm2} --enable-secure-boot --enable-vtpm --disable-integrity-monitoring')
        self.cmd('vm show -g {rg} -n {vm2}', checks=[
            self.check('resources', None),
            self.check('identity', None),
            self.check('securityProfile.securityType', 'TrustedLaunch'),
            self.check('securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('securityProfile.uefiSettings.vTpmEnabled', True)
        ])
        self.cmd('vm create --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --security-type TrustedLaunch --assign-identity {id1} --admin-username azureuser -g {rg} -n {vm3} --enable-secure-boot --enable-vtpm')
        self.cmd('vm show -g {rg} -n {vm3}', checks=[
            self.check('identity.type', 'SystemAssigned, UserAssigned'),
            self.check('resources[0].name', 'GuestAttestation'),
            self.check('resources[0].publisher', 'Microsoft.Azure.Security.LinuxAttestation'),
            self.check('securityProfile.securityType', 'TrustedLaunch'),
            self.check('securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('securityProfile.uefiSettings.vTpmEnabled', True)

        ])
        self.cmd('vmss create -g {rg} -n {vmss1} --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --admin-username azureuser --security-type TrustedLaunch --enable-secure-boot --enable-vtpm')
        self.cmd('vmss show -g {rg} -n {vmss1}', checks=[
            self.check('identity.type', 'SystemAssigned'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].name', 'GuestAttestation'),
            self.check('virtualMachineProfile.extensionProfile.extensions[0].publisher', 'Microsoft.Azure.Security.LinuxAttestation'),
            self.check('virtualMachineProfile.securityProfile.securityType', 'TrustedLaunch'),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.vTpmEnabled', True)
        ])
        self.cmd('vmss list-instances -n {vmss1} -g {rg}', checks=[
            self.check('[0].resources[0].name', 'GuestAttestation'),
            self.check('[0].resources[0].publisher', 'Microsoft.Azure.Security.LinuxAttestation')
        ])
        self.cmd('vmss create -g {rg} -n {vmss2} --image canonical:0001-com-ubuntu-server-focal:20_04-lts-gen2:latest --admin-username azureuser --security-type TrustedLaunch --enable-secure-boot --enable-vtpm --disable-integrity-monitoring')
        self.cmd('vmss show -g {rg} -n {vmss2}', checks=[
            self.check('identity', None),
            self.check('virtualMachineProfile.extensionProfile', 'None'),
            self.check('virtualMachineProfile.securityProfile.securityType', 'TrustedLaunch'),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.secureBootEnabled', True),
            self.check('virtualMachineProfile.securityProfile.uefiSettings.vTpmEnabled', True)
        ])


class DiskHibernationScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_disk_hibernation_')
    def test_disk_hibernation(self):
        self.cmd('disk create -g {rg} -n d1 --size-gb 10 --support-hibernation true', checks=[
            self.check('supportsHibernation', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_disk_data_access_auth_mode_', location='eastus2euap')
    def test_disk_data_access_auth_mode(self):
        self.kwargs.update({
            'disk': self.create_random_name('disk-', 10),
            'disk1': self.create_random_name('disk-', 10)
        })
        self.cmd('disk create -g {rg} -n {disk} --size-gb 10 --data-access-auth-mode AzureActiveDirectory', checks=[
            self.check('dataAccessAuthMode', 'AzureActiveDirectory')
        ])
        self.cmd('disk create -g {rg} -n {disk1} --size-gb 10 --data-access-auth-mode None', checks=[
            self.check('dataAccessAuthMode', 'None')
        ])


class VMCreateCountScenarioTest(ScenarioTest):
    @AllowLargeResponse()
    @ResourceGroupPreparer(name_prefix='cli_test_vm_create_count_', location='eastus')
    def test_vm_create_count(self, resource_group):
        self.cmd('az network vnet create -g {rg} -n vnet --address-prefix 10.0.0.0/16')
        self.cmd('az network vnet subnet create -g {rg} --vnet-name vnet -n subnet1 --address-prefixes 10.0.0.0/24')
        self.cmd('az network vnet subnet create -g {rg} --vnet-name vnet -n subnet2 --address-prefixes 10.0.1.0/24')
        self.cmd('vm create -g {rg} -n vma --image ubuntults --count 3 --vnet-name vnet --subnet subnet1 --nsg-rule None '
                 '--generate-ssh-keys --nic-delete-option Delete --admin-username vmtest')
        self.cmd('vm list -g {rg}', checks=[
            self.check('length(@)', 3),
            self.check('[0].networkProfile.networkInterfaces[0].deleteOption', 'Delete'),
            self.check('[1].networkProfile.networkInterfaces[0].deleteOption', 'Delete'),
            self.check('[2].networkProfile.networkInterfaces[0].deleteOption', 'Delete')
        ])

        self.cmd('vm create -g {rg} -n vmb --image ubuntults --count 3 --vnet-name vnet --subnet subnet2 --nsg-rule None --generate-ssh-keys --admin-username vmtest')
        self.cmd('vm list -g {rg}', checks=[
            self.check('length(@)', 6)
        ])


class ExtendedLocation(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_vm_extended_location_')
    def test_vm_extended_location(self, resource_group):
        self.cmd('vm create -g {rg} -n vm --image ubuntults --nsg-rule None --generate-ssh-keys --admin-username vmtest '
                 '--edge-zone microsoftlosangeles1 --public-ip-sku Standard')
        self.cmd('vm show -g {rg} -n vm', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network vnet show -g {rg} -n vmVNET', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network nic show -g {rg} -n vmVMNic', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network public-ip show -n vmPublicIP -g {rg}', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_vmss_extended_location_')
    def test_vmss_extended_location(self, resource_group):
        self.cmd('vmss create -g {rg} -n vmss --image ubuntults --generate-ssh-keys --admin-username vmtest '
                 '--edge-zone microsoftlosangeles1 --lb-sku Standard')
        self.cmd('vmss show -g {rg} -n vmss', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network vnet show -g {rg} -n vmssVNET', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network lb show -g {rg} -n vmssLB', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

        self.cmd('network public-ip show -n vmssLBPublicIP -g {rg}', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_other_extended_location_')
    def test_other_extended_location(self, resource_group):
        self.cmd('disk create -g {rg} -n d1 --size-gb 10 --edge-zone microsoftlosangeles1', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])
        self.cmd('snapshot create -g {rg} -n s1 --size-gb 10 --edge-zone microsoftlosangeles1 --sku Premium_LRS', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])
        self.cmd('image create -g {rg} -n image --os-type linux --source d1 --edge-zone microsoftlosangeles1', checks=[
            self.check('extendedLocation.name', 'microsoftlosangeles1'),
            self.check('extendedLocation.type', 'EdgeZone')
        ])


class DiskZRSScenarioTest(ScenarioTest):
    @AllowLargeResponse(size_kb=99999)
    @ResourceGroupPreparer(name_prefix='cli_test_disk_zrs_', location='westus2')
    def test_disk_zrs(self, resource_group):
        # az feature register --namespace Microsoft.Compute -n SharedDisksForStandardSSD
        # az provider register -n Microsoft.Compute
        self.cmd('disk create -g {rg} -n d1 --size-gb 1024 --sku StandardSSD_ZRS --max-shares 3', checks=[
            self.check('sku.name', 'StandardSSD_ZRS')
        ])
        self.cmd('disk update -g {rg} -n d1 --sku Premium_ZRS', checks=[
            self.check('sku.name', 'Premium_ZRS')
        ])
        self.cmd('vm create -g {rg} -n d1 --image ubuntults --zone 1 --attach-data-disks d1 --generate-ssh-keys --nsg-rule None --admin-username vmtest')
        # ZRS disks cannot be pinned with a zone
        self.cmd('disk create -g {rg} -n d1 --size-gb 10 --sku StandardSSD_ZRS --zone 1', expect_failure=True)


class CapacityReservationScenarioTest(ScenarioTest):

    # Due to the bug in service, the resources generated by the test cannot be deleted normally.
    # The public IP generated by this test will cause the ICM with serv 2. Therefore, disable this test for now
    @unittest.skip('Service bug')
    @AllowLargeResponse(size_kb=99999)
    @ResourceGroupPreparer(name_prefix='cli_test_capacity_reservation_', location='centraluseuap')
    def test_capacity_reservation(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'reservation_group': self.create_random_name('cli_reservation_group_', 40),
            'reservation_name': self.create_random_name('cli_reservation_name_', 40),
            'reservation_group2': self.create_random_name('cli_reservation_group2_', 40),
            'reservation_name2': self.create_random_name('cli_reservation_name2_', 40),
            'sku': 'Standard_DS1_v2',
            'vm': self.create_random_name('vm', 10),
            'vmss': self.create_random_name('vmss', 10),
            'username': 'ubuntu',
            'auth': 'ssh',
            'image': 'UbuntuLTS',
            'ssh_key': TEST_SSH_KEY_PUB,
        })

        self.kwargs['reservation_group_id1'] = self.cmd('capacity reservation group create -n {reservation_group} -g {rg} --tags key=val --zones 1 2', checks=[
            self.check('name', '{reservation_group}'),
            self.check('zones', ['1', '2']),
            self.check('tags', {'key': 'val'})
        ]).get_output_in_json()['id']

        self.cmd('capacity reservation group update -n {reservation_group} -g {rg} --tags key=val key1=val1', checks=[
            self.check('name', '{reservation_group}'),
            self.check('tags', {'key': 'val', 'key1': 'val1'})
        ])

        self.cmd('capacity reservation group show -n {reservation_group} -g {rg}', checks=[
            self.check('name', '{reservation_group}'),
            self.check('zones', ['1', '2']),
            self.check('tags', {'key': 'val', 'key1': 'val1'})
        ])

        self.cmd('capacity reservation group list -g {rg} --query "[?name==\'{reservation_group}\']" ', checks=[
            self.check('[0].name', '{reservation_group}'),
            self.check('[0].zones', ['1', '2']),
            self.check('[0].tags', {'key': 'val', 'key1': 'val1'})
        ])

        self.cmd('capacity reservation create -c {reservation_group} -n {reservation_name} -g {rg} --sku {sku} --capacity 5 --zone 1 --tags key=val', checks=[
            self.check('name', '{reservation_name}'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', 5),
            self.check('zones', ['1']),
            self.check('tags', {'key': 'val'}),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('capacity reservation update -c {reservation_group} -n {reservation_name} -g {rg} --capacity 3 --tags key=val key1=val1', checks=[
            self.check('name', '{reservation_name}'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', 3),
            self.check('tags', {'key': 'val', 'key1': 'val1'}),
            self.check('provisioningState', 'Succeeded')
        ])

        self.cmd('capacity reservation show -c {reservation_group} -n {reservation_name} -g {rg} --instance-view', checks=[
            self.check('name', '{reservation_name}'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', 3),
            self.check('tags', {'key': 'val', 'key1': 'val1'}),
            self.check('zones', ['1']),
            self.check('provisioningState', 'Succeeded'),
            self.check('instanceView.statuses[0].code', 'ProvisioningState/succeeded')
        ])

        self.cmd('capacity reservation list -c {reservation_group} -g {rg} --query "[?name==\'{reservation_name}\']" ', checks=[
            self.check('[0].name', '{reservation_name}'),
            self.check('[0].sku.name', '{sku}'),
            self.check('[0].sku.capacity', 3),
            self.check('[0].tags', {'key': 'val', 'key1': 'val1'}),
            self.check('[0].zones', ['1']),
            self.check('[0].provisioningState', 'Succeeded')
        ])

        self.cmd('capacity reservation group show -n {reservation_group} -g {rg} --instance-view', checks=[
            self.check('name', '{reservation_group}'),
            self.check('zones', ['1', '2']),
            self.check('tags', {'key': 'val', 'key1': 'val1'}),
            self.check('instanceView.capacityReservations[0].name', '{reservation_name}')
        ])

        self.cmd('vm create -g {rg} -n {vm} --admin-username {username} --authentication-type {auth} --image {image} --ssh-key-value \'{ssh_key}\' --nsg-rule None --capacity-reservation-group {reservation_group} --zone 1 ')

        self.kwargs['vm_id'] = self.cmd('vm show -g {rg} -n {vm} ', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('capacityReservation.capacityReservationGroup.id', '{reservation_group_id1}', case_sensitive=False),
        ]).get_output_in_json()['id']

        self.cmd('vmss create -n {vmss} -g {rg} --image {image} --admin-username deploy --ssh-key-value "{ssh_key}" --capacity-reservation-group {reservation_group} --zone 1 ', checks=[
            self.check('vmss.provisioningState', 'Succeeded'),
            self.check('vmss.virtualMachineProfile.capacityReservation.capacityReservationGroup.id', '{reservation_group_id1}', case_sensitive=False),
        ])

        self.kwargs['vmss_id'] = self.cmd('vmss show -g {rg} -n {vmss} ', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.capacityReservation.capacityReservationGroup.id', '{reservation_group_id1}', case_sensitive=False),
        ]).get_output_in_json()['id']

        vm_associated = self.cmd('capacity reservation group list -g {rg} --query "[?name==\'{reservation_group}\']" --vm-instance --vmss-instance', checks=[
            self.check('[0].name', '{reservation_group}'),
            self.check('[0].zones', ['1', '2']),
            self.check('[0].tags', {'key': 'val', 'key1': 'val1'})
        ]).get_output_in_json()[0]['virtualMachinesAssociated']

        vm_associated_list = [i['id'].lower() for i in vm_associated]
        self.assertTrue(self.kwargs['vm_id'].lower() in vm_associated_list)
        contains_vmss_id = False
        for id in vm_associated_list:
            if self.kwargs['vmss_id'].lower() in id:
                contains_vmss_id = True
                break
        self.assertTrue(contains_vmss_id)

        self.kwargs['reservation_group_id2'] = self.cmd('capacity reservation group create -n {reservation_group2} -g {rg} --tags key=val --zones 1 2', checks=[
            self.check('name', '{reservation_group2}'),
            self.check('zones', ['1', '2']),
            self.check('tags', {'key': 'val'})
        ]).get_output_in_json()['id']

        self.cmd('capacity reservation create -c {reservation_group2} -n {reservation_name2} -g {rg} --sku {sku} --capacity 5 --zone 1 --tags key=val', checks=[
            self.check('name', '{reservation_name2}'),
            self.check('sku.name', '{sku}'),
            self.check('sku.capacity', 5),
            self.check('zones', ['1']),
            self.check('tags', {'key': 'val'}),
            self.check('provisioningState', 'Succeeded')
        ])

        # Updating capacity reservation group requires the VM(s) to be deallocated.
        self.cmd('vm deallocate -g {rg} -n {vm}')

        self.cmd('vm update -g {rg} -n {vm} --capacity-reservation-group {reservation_group2}')

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('capacityReservation.capacityReservationGroup.id', '{reservation_group_id2}', case_sensitive=False),
        ])

        self.cmd('vmss update -g {rg} -n {vmss} --capacity-reservation-group {reservation_group2}')

        self.cmd('vmss show -n {vmss} -g {rg}', checks=[
            self.check('provisioningState', 'Succeeded'),
            self.check('virtualMachineProfile.capacityReservation.capacityReservationGroup.id', '{reservation_group_id2}', case_sensitive=False),
        ])

        # Updating capacity reservation group requires the VM(s) to be deallocated.
        self.cmd('vm deallocate -g {rg} -n {vm}')

        # Before delete the capacity reservation that has been associated with VM/VMSS, we need to disassociate the capacity reservation group first
        self.cmd('vm update -g {rg} -n {vm} --capacity-reservation-group None')

        self.cmd('vmss update -g {rg} -n {vmss} --capacity-reservation-group None')

        self.cmd('capacity reservation delete -c {reservation_group} -n {reservation_name} -g {rg} --yes')
        self.cmd('capacity reservation delete -c {reservation_group2} -n {reservation_name2} -g {rg} --yes')

        self.cmd('capacity reservation group delete -n {reservation_group} -g {rg} --yes')
        self.cmd('capacity reservation group delete -n {reservation_group2} -g {rg} --yes')


class VMVMSSAddApplicationTestScenario(ScenarioTest):

    @ResourceGroupPreparer()
    def test_vm_add_application_empty_version_ids(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1'
        })
        # Prepare VM
        self.cmd('vm create -l eastus -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --nsg-rule NONE')

        self.cmd('vm application set -g {rg} -n {vm} --app-version-ids')

        self.cmd('vm application list -g {rg} -n {vm}')

    # Need prepare app versions
    @ResourceGroupPreparer()
    def test_vm_add_application(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
        })
        # Prepare VM
        self.cmd('vm create -l eastus -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --nsg-rule NONE')

        self.cmd('vm application set -g {rg} -n {vm} --app-version-ids {vid1} {vid2}')

        self.cmd('vm application list -g {rg} -n {vm}')

    @ResourceGroupPreparer()
    def test_vm_add_application_with_order_application(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
        })
        # Prepare VM
        self.cmd('vm create -l eastus -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --nsg-rule NONE')

        self.cmd('vm application set -g {rg} -n {vm} --app-version-ids {vid1} {vid2} --order-applications', checks=[
            self.check('applicationProfile.galleryApplications[0].order', 1),
            self.check('applicationProfile.galleryApplications[1].order', 2)
        ])

        self.cmd('vm application list -g {rg} -n {vm}')

    @ResourceGroupPreparer()
    def test_vm_add_application_with_config_override(self, resource_group):
        self.kwargs.update({
            'vm': 'vm1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
            'config': 'https://galleryappaccount.blob.core.windows.net/gallerytest/MyAppConfig'
        })
        # Prepare VM
        self.cmd('vm create -l eastus -g {rg} -n {vm} --image Win2012R2Datacenter --admin-username clitest1234 --admin-password Test123456789# --license-type Windows_Server --nsg-rule NONE')

        # wrong length of config-overrides
        message = 'usage error: --app-config-overrides should have the same number of items as --application-version-ids'
        with self.assertRaisesRegex(ArgumentUsageError, message):
            self.cmd('vm application set -g {rg} -n {vm} --app-version-ids {vid1} {vid2} --app-config-overrides {config}')

        self.cmd('vm application set -g {rg} -n {vm} --app-version-ids {vid1} {vid2} --app-config-overrides null {config}', checks=[
            self.check('applicationProfile.galleryApplications[0].configurationReference', 'null'),
            self.check('applicationProfile.galleryApplications[1].configurationReference', '{config}')
        ])

        self.cmd('vm application list -g {rg} -n {vm}')

    # Need prepare app versions
    @ResourceGroupPreparer()
    def test_vmss_add_application_empty_version_ids(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1'
        })

        # Prepare VMSS
        self.cmd('vmss create -l eastus -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        self.cmd('vmss application set -g {rg} -n {vmss} --app-version-ids')

        self.cmd('vmss application list -g {rg} --name {vmss}')

    # Need prepare app versions
    @ResourceGroupPreparer()
    def test_vmss_add_application(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
        })

        # Prepare VMSS
        self.cmd('vmss create -l eastus -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        self.cmd('vmss application set -g {rg} -n {vmss} --app-version-ids {vid1} {vid2}')

        self.cmd('vmss application list -g {rg} --name {vmss}')

    # Need prepare app versions
    @ResourceGroupPreparer()
    def test_vmss_add_application_with_order_application(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
        })

        # Prepare VMSS
        self.cmd('vmss create -l eastus -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        self.cmd('vmss application set -g {rg} -n {vmss} --app-version-ids {vid1} {vid2} --order-applications', checks=[
            self.check('virtualMachineProfile.applicationProfile.galleryApplications[0].order', 1),
            self.check('virtualMachineProfile.applicationProfile.galleryApplications[1].order', 2)
        ])

        self.cmd('vmss application list -g {rg} --name {vmss}')

    # Need prepare app versions
    @ResourceGroupPreparer()
    def test_vmss_add_application_with_config_override(self, resource_group):
        self.kwargs.update({
            'vmss': 'vmss1',
            'vid1': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MyFirstApp/versions/1.0.0'.format(
                sub=self.get_subscription_id()
            ),
            'vid2': '/subscriptions/{sub}/resourceGroups/galleryappaccount/providers/Microsoft.Compute/galleries/MyGallery/applications/MySecondApp/versions/1.0.1'.format(
                sub=self.get_subscription_id()
            ),
            'config': 'https://galleryappaccount.blob.core.windows.net/gallerytest/MyAppConfig'
        })

        # Prepare VMSS
        self.cmd('vmss create -l eastus -g {rg} -n {vmss} --authentication-type password --admin-username admin123 --admin-password PasswordPassword1!  --image Win2012R2Datacenter')

        # wrong length of config-overrides
        message = 'usage error: --app-config-overrides should have the same number of items as --application-version-ids'
        with self.assertRaisesRegex(ArgumentUsageError, message):
            self.cmd('vmss application set -g {rg} -n {vmss} --app-version-ids {vid1} {vid2} --app-config-overrides {config}')

        self.cmd('vmss application set -g {rg} -n {vmss} --app-version-ids {vid1} {vid2} --app-config-overrides null {config}', checks=[
            self.check('virtualMachineProfile.applicationProfile.galleryApplications[0].configurationReference', 'null'),
            self.check('virtualMachineProfile.applicationProfile.galleryApplications[1].configurationReference', '{config}')
        ])

        self.cmd('vmss application list -g {rg} --name {vmss}')


class DiskRPTestScenario(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_public_network_access')
    def test_public_network_access(self, resource_group):
        self.kwargs.update({
            'disk1': 'disk1',
            'disk2': 'disk2',
            'disk3': 'disk3',
            'snapshot1': 'snapshot1',
            'snapshot2': 'snapshot2',
            'snapshot3': 'snapshot3',
        })

        self.cmd('disk create --public-network-access Enabled --size-gb 5 -n {disk1} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('publicNetworkAccess', 'Enabled')
        ])
        self.cmd('disk update --public-network-access Disabled -n {disk1} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('publicNetworkAccess', 'Disabled')
        ])
        self.cmd('disk create --network-access-policy AllowAll --public-network-access Disabled --size-gb 5 -n {disk2} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk2}', checks=[
            self.check('name', '{disk2}'),
            self.check('publicNetworkAccess', 'Disabled')
        ])
        self.cmd('disk-access create -g {rg} -n diskaccess')
        self.cmd('snapshot create --network-access-policy AllowPrivate --disk-access diskaccess --public-network-access Enabled --size-gb 5 -n {disk3} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {disk3}', checks=[
            self.check('name', '{disk3}'),
            self.check('publicNetworkAccess', 'Enabled')
        ])

        self.cmd('snapshot create --public-network-access Enabled --size-gb 5 -n {snapshot1} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot1}', checks=[
            self.check('name', '{snapshot1}'),
            self.check('publicNetworkAccess', 'Enabled')
        ])
        self.cmd('snapshot update --public-network-access Disabled -n {snapshot1} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot1}', checks=[
            self.check('name', '{snapshot1}'),
            self.check('publicNetworkAccess', 'Disabled')
        ])
        self.cmd('snapshot create --network-access-policy AllowAll --public-network-access Disabled --size-gb 5 -n {snapshot2} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot2}', checks=[
            self.check('name', '{snapshot2}'),
            self.check('publicNetworkAccess', 'Disabled')
        ])
        self.cmd('disk-access create -g {rg} -n diskaccess')
        self.cmd('snapshot create --network-access-policy AllowPrivate --disk-access diskaccess --public-network-access Enabled --size-gb 5 -n {snapshot3} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot3}', checks=[
            self.check('name', '{snapshot3}'),
            self.check('publicNetworkAccess', 'Enabled')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_accelerated_network')
    def test_accelerated_network(self, resource_group):
        self.kwargs.update({
            'disk1': 'disk1',
            'disk2': 'disk2',
            'snapshot1': 'snapshot1',
            'snapshot2': 'snapshot2',
        })

        self.cmd('disk create --accelerated-network true --size-gb 5 -n {disk1} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('supportedCapabilities.acceleratedNetwork', True)
        ])
        self.cmd('disk update --accelerated-network false -n {disk1} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('supportedCapabilities.acceleratedNetwork', False)
        ])
        self.cmd('disk create --size-gb 5 -n {disk2} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk2}', checks=[
            self.check('name', '{disk2}'),
            self.check('supportedCapabilities', None)
        ])
        self.cmd('disk update --accelerated-network true -n {disk1} -g {rg}')
        self.cmd('disk show -g {rg} -n {disk1}', checks=[
            self.check('name', '{disk1}'),
            self.check('supportedCapabilities.acceleratedNetwork', True)
        ])

        self.cmd('snapshot create --accelerated-network true --size-gb 5 -n {snapshot1} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot1}', checks=[
            self.check('name', '{snapshot1}'),
            self.check('supportedCapabilities.acceleratedNetwork', True)
        ])
        self.cmd('snapshot update --accelerated-network false -n {snapshot1} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot1}', checks=[
            self.check('name', '{snapshot1}'),
            self.check('supportedCapabilities.acceleratedNetwork', False)
        ])
        self.cmd('snapshot create --size-gb 5 -n {snapshot2} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot2}', checks=[
            self.check('name', '{snapshot2}'),
            self.check('supportedCapabilities', None)
        ])
        self.cmd('snapshot update --accelerated-network true -n {snapshot2} -g {rg}')
        self.cmd('snapshot show -g {rg} -n {snapshot2}', checks=[
            self.check('name', '{snapshot2}'),
            self.check('supportedCapabilities.acceleratedNetwork', True)
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_completion_percent1_', location='westus')
    @ResourceGroupPreparer(name_prefix='cli_test_completion_percent2_', location='eastus', key='rg2')
    def test_completion_percent(self, resource_group):
        # Create a random empty disk
        self.cmd('disk create -g {rg} -n disk1 --size-gb 200 -l westus')
        # Create a snapshot A from a empty disk with createOption as "Copy"
        self.kwargs['source'] = self.cmd('snapshot create -g {rg} -n snapa --source disk1 -l westus --incremental true').get_output_in_json()['id']
        # Create a snapshot B in different region with createOption as "CopyStart" with snapshot A as source
        self.cmd('snapshot create -g {rg2} -n snapb --copy-start true --incremental true --source {source} -l eastus')
        # show snapshot B, check completionPercent
        self.cmd('snapshot show -g {rg2} -n snapb', checks=[
            self.check_pattern('completionPercent', '\d?.\d?')
        ])


class RestorePointScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_restore_point_collections', location='westus')
    def test_restore_point(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'collection_name': self.create_random_name('collection_', 20),
            'point_name': self.create_random_name('point_', 15),
            'vm_name': self.create_random_name('vm_', 15)
        })

        vm = self.cmd('vm create -n {vm_name} -g {rg} --image UbuntuLTS --admin-username vmtest').get_output_in_json()
        self.kwargs.update({
            'vm_id': vm['id']
        })

        self.cmd('restore-point collection create -g {rg} --collection-name {collection_name} --source-id {vm_id} -l eastus', checks=[
            self.check('location', 'eastus'),
            self.check('name', '{collection_name}'),
            self.check('resourceGroup', '{rg}')
        ])

        point = self.cmd('restore-point create -g {rg} -n {point_name} --collection-name {collection_name}', checks=[
            self.check('name', '{point_name}'),
            self.check('resourceGroup', '{rg}')
        ]).get_output_in_json()

        self.kwargs.update({
            'point_id': point['id']
        })

        self.cmd('restore-point show -g {rg} -n {point_name} --collection-name {collection_name} --instance-view', checks=[
            self.check('id', '{point_id}'),
            self.check('name', '{point_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('instanceView.diskRestorePoints[0].replicationStatus.status.code', 'ReplicationState/replicating')
        ])

        self.cmd('restore-point collection show -g {rg} --collection-name {collection_name} --restore-points', checks=[
            self.check('location', 'eastus'),
            self.check('name', '{collection_name}'),
            self.check('restorePoints[0].id', '{point_id}'),
            self.check('restorePoints[0].name', '{point_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('source.id', '{vm_id}')
        ])

        self.cmd('restore-point delete -g {rg} -n {point_name} --collection-name {collection_name} -y')


    @ResourceGroupPreparer(name_prefix='cli_test_restore_point_collection', location='westus')
    def test_restore_point_collection(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'collection_name': self.create_random_name('point_', 15),
            'vm_name': self.create_random_name('vm_', 15)
        })

        vm = self.cmd('vm create -n {vm_name} -g {rg} --image UbuntuLTS --admin-username vmtest').get_output_in_json()
        self.kwargs.update({
            'vm_id': vm['id']
        })

        self.cmd('restore-point collection create -g {rg} --collection-name {collection_name} --source-id {vm_id}', checks=[
            self.check('location', 'westus'),
            self.check('name', '{collection_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('source.id', '{vm_id}'),
            self.check('tags', None),
            self.check('type', 'Microsoft.Compute/restorePointCollections')
        ])

        self.cmd('restore-point collection update -g {rg} --collection-name {collection_name} --tags tag=test', checks=[
            self.check('tags', {'tag': 'test'})
        ])

        self.cmd('restore-point collection show -g {rg} --collection-name {collection_name}', checks=[
            self.check('location', 'westus'),
            self.check('name', '{collection_name}'),
            self.check('resourceGroup', '{rg}'),
            self.check('source.id', '{vm_id}'),
            self.check('tags', {'tag': 'test'}),
            self.check('type', 'Microsoft.Compute/restorePointCollections')
        ])

        self.cmd('restore-point collection list -g {rg}', checks=[
            self.check('[0].location', 'westus'),
            self.check('[0].name', '{collection_name}'),
            self.check('[0].resourceGroup', '{rg}'),
            self.check('[0].source.id', '{vm_id}'),
            self.check('[0].tags', {'tag': 'test'}),
            self.check('[0].type', 'Microsoft.Compute/restorePointCollections')
        ])

        self.cmd('restore-point collection list-all', checks=[
            self.check('type(@)', 'array')
        ])

        self.cmd('restore-point collection delete -g {rg} --collection-name {collection_name} -y')

    @ResourceGroupPreparer(name_prefix='cli_test_copy_vm_restore_point', location='westus')
    def test_copy_vm_restore_point(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'collection_name': self.create_random_name('collection_', 20),
            'collection_name1': self.create_random_name('collection_', 20),
            'point_name': self.create_random_name('point_', 15),
            'point_name1': self.create_random_name('point_', 15),
            'vm_name': self.create_random_name('vm_', 15)
        })

        vm = self.cmd('vm create -n {vm_name} -g {rg} --image UbuntuLTS --admin-username vmtest').get_output_in_json()
        self.kwargs.update({
            'vm_id': vm['id']
        })

        collection = self.cmd('restore-point collection create -g {rg} --collection-name {collection_name} --source-id {vm_id}').get_output_in_json()
        self.kwargs.update({
            'collection_id': collection['id']
        })

        self.cmd('restore-point collection create -g {rg} --collection-name {collection_name1} --source-id {collection_id} -l eastus', checks=[
            self.check('location', 'eastus'),
            self.check('source.id', '{collection_id}'),
            self.check('source.location', 'westus')
        ])

        point = self.cmd('restore-point create -g {rg} -n {point_name} --collection-name {collection_name}').get_output_in_json()
        self.kwargs.update({
            'point_id': point['id']
        })

        self.cmd('restore-point create -g {rg} -n {point_name1} --collection-name {collection_name1} --source-restore-point {point_id}', checks=[
            self.check('sourceRestorePoint.id', '{point_id}')
        ])


class ArchitectureScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(location='westus')
    def test_architecture(self, resource_group):
        self.kwargs.update({
            'sig_name': self.create_random_name('sig_', 10),
            'img_def_name': self.create_random_name('def_', 10),
            'pub_name': self.create_random_name('pub_', 10),
            'of_name': self.create_random_name('of_', 10),
            'sku_name': self.create_random_name('sku_', 10),
            'disk_name': self.create_random_name('disk_', 10),
            'snap_name': self.create_random_name('snap_', 10)
        })
        self.cmd('sig create -g {rg} -r {sig_name}')
        self.cmd('sig image-definition create -g {rg} --gallery-name {sig_name} --architecture x64 --gallery-image-definition {img_def_name} --os-type linux -p {pub_name} -f {of_name} -s {sku_name}', checks=[
            self.check('architecture', 'x64')
        ])

        self.cmd('disk create -g {rg} -n {disk_name} --architecture x64 --size-gb 20', checks=[
            self.check('supportedCapabilities.architecture', 'x64')
        ])
        self.cmd('disk update -g {rg} -n {disk_name} --architecture Arm64', checks=[
            self.check('supportedCapabilities.architecture', 'Arm64')
        ])

        self.cmd('snapshot create -n {snap_name} -g {rg} --size-gb 1 --architecture x64', checks=[
            self.check('supportedCapabilities.architecture', 'x64')
        ])
        self.cmd('snapshot update -n {snap_name} -g {rg} --architecture Arm64', checks=[
            self.check('supportedCapabilities.architecture', 'Arm64')
        ])


if __name__ == '__main__':
    unittest.main()
