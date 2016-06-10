﻿# AZURE CLI VM TEST DEFINITIONS
import json
import os
import tempfile

from azure.cli.utils.vcr_test_base import VCRTestBase, JMESPathComparator

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

#pylint: disable=method-hidden
#pylint: disable=line-too-long
#pylint: disable=bad-continuation
#pylint: disable=too-many-lines

TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"

class ResourceGroupVCRTestBase(VCRTestBase):
    def __init__(self, test_file, test_name, debug=False):
        super(ResourceGroupVCRTestBase, self).__init__(test_file, test_name, debug)
        self.resource_group = 'vcr_resource_group'
        self.location = 'westus'

    def set_up(self):
        self.run_command_no_verify('resource group create --location {} --name {}'
                                   .format(self.location, self.resource_group))

    def tear_down(self):
        self.run_command_no_verify('resource group delete --name {}'.format(self.resource_group))

class VMImageListByAliasesScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListByAliasesScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_list_by_alias(self):
        self.execute(verify_test_output=False)

    def body(self):
        result = self.run_command_no_verify('vm image list --offer ubuntu -o tsv')
        assert result.index('14.04.4-LTS') >= 0


class VMUsageScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMUsageScenarioTest, self).__init__(__file__, test_method)

    def test_vm_usage(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm usage list --location westus',
                                    JMESPathComparator('type(@)', 'array'))

class VMImageListThruServiceScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMImageListThruServiceScenarioTest, self).__init__(__file__, test_method)

    def test_vm_images_list_thru_services(self):
        self.execute(verify_test_output=False)

    def body(self):
        cmd = ('vm image list -l westus --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run_command_no_verify(cmd)
        assert result.index('15.04') >= 0

        cmd = ('vm image list --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run_command_no_verify(cmd)
        assert result.index('15.04') >= 0

class VMCombinedListTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMCombinedListTest, self).__init__(__file__, test_method)

    def test_vm_combined_list(self):
        self.execute(verify_test_output=False)

    def body(self):
        all_vms = self.run_command_no_verify('vm list -o json')
        some_vms = self.run_command_no_verify('vm list -g travistestresourcegroup -o json')
        assert len(all_vms) > len(some_vms)

class VMResizeTest(VCRTestBase):
    def __init__(self, test_method):
        super(VMResizeTest, self).__init__(__file__, test_method)

    def test_vm_resize(self):
        self.execute(verify_test_output=True)

    def body(self):
        group = 'yugangw4'
        vm_name = 'yugangw4-1'
        vm = self.run_command_no_verify('vm show -g {} -n {} -o json'.format(group, vm_name))
        new_size = 'Standard_A4' if vm['hardwareProfile']['vmSize'] == 'Standard_A3' else 'Standard_A3'
        check = [JMESPathComparator('hardwareProfile.vmSize', new_size)]
        self.run_command_and_verify('vm resize -g {} -n {} --size {}'.format(group, vm_name, new_size), check)

class VMShowListSizesListIPAddressesScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMShowListSizesListIPAddressesScenarioTest, self).__init__(__file__, test_method)
        self.deployment_name = 'azurecli-test-deployment-vm-list-ips'
        self.resource_group = 'cliTestRg_VmListIpAddresses'
        self.location = 'westus'
        self.vm_name = 'vm-with-public-ip'
        self.ip_allocation_method = 'dynamic'

    def test_vm_show_list_sizes_list_ip_addresses(self):
        self.execute(verify_test_output=True)

    def body(self):
        # Expecting no results at the beginning
        self.run_command_and_verify('vm list-ip-addresses --resource-group {}'.format(self.resource_group), None)
        self.run_command_no_verify('vm create --resource-group {0} --location {1} -n {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--deployment-name {3} --public-ip-address-allocation {4} '
                 '--public-ip-address-type new --authentication-type password'.format(
                     self.resource_group, self.location, self.vm_name, self.deployment_name,
                     self.ip_allocation_method))
        self.run_command_and_verify('vm show --resource-group {} --name {} --expand instanceView'.format(
            self.resource_group, self.vm_name),
                  [
                      JMESPathComparator('type(@)', 'object'),
                      JMESPathComparator('name', self.vm_name),
                      JMESPathComparator('location', self.location),
                      JMESPathComparator('resourceGroup', self.resource_group),
                  ])
        self.run_command_and_verify('vm list-sizes --resource-group {} --name {}'.format(
            self.resource_group,
            self.vm_name),
                  JMESPathComparator('type(@)', 'array'))
        # Expecting the one we just added
        self.run_command_and_verify('vm list-ip-addresses --resource-group {}'.format(self.resource_group),
                  [
                      JMESPathComparator('length(@)', 1),
                      JMESPathComparator('[0].virtualMachine.name', self.vm_name),
                      JMESPathComparator('[0].virtualMachine.resourceGroup', self.resource_group),
                      JMESPathComparator(
                          'length([0].virtualMachine.network.publicIpAddresses)',
                          1),
                      JMESPathComparator(
                          '[0].virtualMachine.network.publicIpAddresses[0].ipAllocationMethod',
                          self.ip_allocation_method.title()),
                      JMESPathComparator(
                          'type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)',
                          'string')]
                 )

class VMSizeListScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMSizeListScenarioTest, self).__init__(__file__, test_method)

    def test_vm_size_list(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm size list --location westus', JMESPathComparator('type(@)', 'array'))


class VMImageListOffersScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        super(VMImageListOffersScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_list_offers(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm image list-offers --location {} --publisher-name {}'.format(
            self.location, self.publisher_name),
                  [
                      JMESPathComparator('type(@)', 'array'),
                      # all results should have location has set in the test
                      JMESPathComparator("length([?location == '{}']) == length(@)".format(
                          self.location),
                                         True),
                      # all results should have the correct publisher name
                      JMESPathComparator(
                          "length([].id.contains(@, '/Publishers/{}'))".format(self.publisher_name),
                          6),
                  ])

class VMImageListPublishersScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.location = 'westus'
        super(VMImageListPublishersScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_list_publishers(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm image list-publishers --location {}'.format(self.location),
                  [
                      JMESPathComparator('type(@)', 'array'),
                      # all results should have location has set in the test
                      JMESPathComparator("length([?location == '{}']) == length(@)".format(
                          self.location),
                                         True),
                  ])

class VMImageListSkusScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'
        super(VMImageListSkusScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_list_skus(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm image list-skus --location {} --publisher-name {} --offer {}'.format(
            self.location, self.publisher_name, self.offer),
                  [
                      JMESPathComparator('type(@)', 'array'),
                      # all results should have location has set in the test
                      JMESPathComparator("length([?location == '{}']) == length(@)".format(
                          self.location),
                                         True),
                      # all results should have the correct publisher name
                      JMESPathComparator(
                          "length([].id.contains(@, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/'))".format(
                              self.publisher_name, self.offer),
                          27),
                  ])

class VMImageShowScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'
        self.skus = '14.04.2-LTS'
        self.version = '14.04.201503090'
        super(VMImageShowScenarioTest, self).__init__(__file__, test_method)

    def test_vm_image_show(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm image show --location {} --publisher-name {} --offer {} --skus {} --version {}'.format(
            self.location, self.publisher_name, self.offer, self.skus, self.version),
                  [
                      JMESPathComparator('type(@)', 'object'),
                      JMESPathComparator('location', self.location),
                      JMESPathComparator('name', self.version),
                      # all results should have the correct publisher name
                      JMESPathComparator(
                          "contains(id, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/{}/Versions/{}')".format(
                              self.publisher_name, self.offer, self.skus, self.version),
                          True),
                  ])

class VMGeneralizeScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMGeneralizeScenarioTest, self).__init__(__file__, test_method)
        self.deployment_name = 'azurecli-test-deployment-vm-generalize'
        self.resource_group = 'cliTestRg_VmGeneralize'
        self.location = 'westus'
        self.vm_name = 'vm-generalize'

    def body(self):
        self.run_command_no_verify('vm create --resource-group {0} --location {1} --name {2} --admin-username ubuntu '
                 '--image UbuntuLTS --admin-password testPassword0 --authentication-type password '
                 '--deployment-name azurecli_test_vm_generalize'
                 .format(
                     self.resource_group, self.location, self.vm_name))

        self.run_command_no_verify('vm power-off --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        # Should be able to generalize the VM after it has been stopped
        self.run_command_and_verify(
            'vm generalize --resource-group {} --name {}'.format(
                self.resource_group,
                self.vm_name), None)

        self.run_command_and_verify(
            'vm capture --resource-group {} --name {} --vhd-name-prefix vmtest'.format(
                self.resource_group,
                self.vm_name), None)

    def test_vm_generalize(self):
        self.execute(verify_test_output=True)

class VMCreateAndStateModificationsScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(VMCreateAndStateModificationsScenarioTest, self).__init__(__file__, test_method)
        self.deployment_name = 'azurecli-test-deployment-vm-state-mod'
        self.resource_group = 'cliTestRg_VmStateMod'
        self.location = 'westus'
        self.vm_name = 'vm-state-mod'

    def test_vm_create_state_modifications(self):
        self.execute(verify_test_output=True)

    def _check_vm_power_state(self, expected_power_state):
        self.run_command_and_verify(
            'vm show --resource-group {} --name {} --expand instanceView'.format(
                self.resource_group,
                self.vm_name),
            [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.vm_name),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('length(instanceView.statuses)', 2),
                JMESPathComparator(
                    'instanceView.statuses[0].code',
                    'ProvisioningState/succeeded'),
                JMESPathComparator('instanceView.statuses[1].code', expected_power_state),
            ])

    def body(self):
        # Expecting no results
        self.run_command_and_verify('vm list --resource-group {}'.format(self.resource_group), None)
        self.run_command_no_verify('vm create --resource-group {0} --location {1} --name {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--deployment-name {3} --authentication-type password'.format(
                     self.resource_group, self.location, self.vm_name, self.deployment_name))
        # Expecting one result, the one we created
        self.run_command_and_verify('vm list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('length(@)', 1),
            JMESPathComparator('[0].resourceGroup', self.resource_group),
            JMESPathComparator('[0].name', self.vm_name),
            JMESPathComparator('[0].location', self.location),
            JMESPathComparator('[0].provisioningState', 'Succeeded'),
        ])
        self._check_vm_power_state('PowerState/running')
        self.run_command_no_verify('vm power-off --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/stopped')
        self.run_command_no_verify('vm start --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.run_command_no_verify('vm restart --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.run_command_no_verify('vm deallocate --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/deallocated')
        self.run_command_no_verify('vm delete --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        # Expecting no results
        self.run_command_and_verify('vm list --resource-group {}'.format(self.resource_group), None)

class VMAvailSetScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'cliTestRg_Availset'
        self.location = 'westus'
        self.name = 'availset-test'
        super(VMAvailSetScenarioTest, self).__init__(__file__, test_method)

    def test_vm_availset(self):
        self.execute(verify_test_output=True)

    def set_up(self):
        # TODO Create the resource group and availability set here once the command exists
        pass

    def body(self):
        self.run_command_and_verify('vm availability-set list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('length(@)', 1),
            JMESPathComparator('[0].name', self.name),
            JMESPathComparator('[0].resourceGroup', self.resource_group),
            JMESPathComparator('[0].location', self.location),
        ])
        self.run_command_and_verify('vm availability-set list-sizes --resource-group {} --name {}'.format(
            self.resource_group, self.name), JMESPathComparator('type(@)', 'array'))
        self.run_command_and_verify('vm availability-set show --resource-group {} --name {}'.format(
            self.resource_group, self.name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.name),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('location', self.location)])
        self.run_command_and_verify('vm availability-set delete --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        self.run_command_and_verify('vm availability-set list --resource-group {}'.format(
            self.resource_group), None)


class VMExtensionsScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'cliTestRg_VMExtensions'
        self.location = 'westus'
        self.vm_name = 'windows-ext'
        self.extension_name = 'IaaSDiagnostics'
        super(VMExtensionsScenarioTest, self).__init__(__file__, test_method)

    def test_vm_extension(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm extension show --resource-group {} --vm-name {} --name {}'.format(
            self.resource_group, self.vm_name, self.extension_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.extension_name),
                JMESPathComparator('resourceGroup', self.resource_group)])
        self.run_command_and_verify('vm extension delete --resource-group {} --vm-name {} --name {}'.format(
            self.resource_group, self.vm_name, self.extension_name),
                  None)


class VMMachineExtensionImageScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.location = 'westus'
        self.publisher = 'Microsoft.Azure.Diagnostics'
        self.name = 'IaaSDiagnostics'
        self.version = '1.6.4.0'
        super(VMMachineExtensionImageScenarioTest, self).__init__(__file__, test_method)

    def test_vm_machine_extension_image(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm extension image list-names --location {} --publisher {}'.format(
            self.location, self.publisher), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?location == '{}']) == length(@)".format(self.location),
                                   True),
            ])
        self.run_command_and_verify('vm extension image list-versions --location {} --publisher {} --name {}'.format(
            self.location, self.publisher, self.name), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?location == '{}']) == length(@)".format(self.location),
                                   True),
            ])
        self.run_command_and_verify('vm extension image show --location {} --publisher {} --name {} --version {}'.format(
            self.location, self.publisher, self.name, self.version), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('location', self.location),
                JMESPathComparator("contains(id, '/Providers/Microsoft.Compute/Locations/{}/Publishers/{}/ArtifactTypes/VMExtension/Types/{}/Versions/{}')".format(
                    self.location, self.publisher, self.name, self.version
                ), True)])


class VMExtensionImageSearchScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMExtensionImageSearchScenarioTest, self).__init__(__file__, test_method)

    def test_vm_extension_image_search(self):
        self.execute(verify_test_output=True)

    def body(self):
        #pick this specific name, so the search will be under one publisher. This avoids
        #the parallel searching behavior that causes incomplete VCR recordings.
        publisher = 'Vormetric.VormetricTransparentEncryption'
        image_name = 'VormetricTransparentEncryptionAgent'
        verification = [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?name == '{}']) == length(@)".format(image_name), True),
            ]
        cmd = ('vm extension image list -l westus --publisher {} --name {} -o json'.format(publisher, image_name))
        self.run_command_and_verify(cmd, verification)

        cmd = ('vm extension image list -l westus --publisher {} --name {} --latest -o json'.format(publisher, image_name))
        result = self.run_command_no_verify(cmd)
        assert len(result) == 1


class VMScaleSetGetsScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'CLI_TEST1'
        self.ss_name = 'clitestvm'
        self.location = 'westus'
        super(VMScaleSetGetsScenarioTest, self).__init__(__file__, test_method)

    def test_vm_scaleset_gets(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm scaleset list-all', [
            JMESPathComparator('type(@)', 'array')])
        self.run_command_and_verify('vm scaleset list --resource-group {}'.format(
            self.resource_group), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator('[0].name', self.ss_name),
                JMESPathComparator('[0].location', self.location),
                JMESPathComparator('[0].resourceGroup', self.resource_group)])
        self.run_command_and_verify('vm scaleset list-skus --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name),
                  JMESPathComparator('type(@)', 'array'))
        self.run_command_and_verify('vm scaleset show --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.ss_name),
                JMESPathComparator('location', self.location),
                JMESPathComparator('resourceGroup', self.resource_group)])
        self.run_command_and_verify('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('type(statuses)', 'array')])

class VMScaleSetStatesScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'cliTestRg_ScaleSet1'
        self.ss_name = 'scaleset1'
        super(VMScaleSetStatesScenarioTest, self).__init__(__file__, test_method)

    def test_vm_scaleset_states(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_no_verify('vm scaleset power-off --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name))
        self.run_command_and_verify('vm scaleset start --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.run_command_and_verify('vm scaleset restart --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.run_command_and_verify('vm scaleset update-instances --resource-group {} --name {} --instance-ids 0'.format(
            self.resource_group, self.ss_name), None)

class VMScaleSetScaleUpScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'yugangwvmss'
        self.ss_name = 'yugangwvm'
        super(VMScaleSetScaleUpScenarioTest, self).__init__(__file__, test_method)

    def test_vm_scaleset_scaleup(self):
        self.execute(verify_test_output=False)

    def body(self):
        result = self.run_command_no_verify('vm scaleset show --resource-group {} --name {} -o json'.format(
            self.resource_group, self.ss_name))
        capacity = result['sku']['capacity']
        new_capacity = capacity + 1 if capacity < 3 else capacity-1
        self.run_command_no_verify('vm scaleset scale --resource-group {} --name {} --new-capacity {}'.format(
            self.resource_group, self.ss_name, new_capacity))
        result = self.run_command_no_verify('vm scaleset show --resource-group {} --name {} -o json'.format(
            self.resource_group, self.ss_name))
        assert result['sku']['capacity'] == new_capacity

class VMScaleSetDeleteScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'yugangwvmss'
        self.ss_name = 'yugangwvm'
        self.vm_count = 3
        self.instance_id_to_delete = 2
        super(VMScaleSetDeleteScenarioTest, self).__init__(__file__, test_method)

    def test_vm_scaleset_delete(self):
        self.execute(verify_test_output=True)

    def body(self):
        self.run_command_and_verify('vm scaleset list --resource-group {}'.format(
            self.resource_group), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator('[0].name', self.ss_name),
                JMESPathComparator('[0].resourceGroup', self.resource_group)])
        self.run_command_and_verify('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('virtualMachine.statusesSummary[0].count', self.vm_count)])
        #Existing issues, the instance delete command has not been recorded
        self.run_command_and_verify('vm scaleset delete-instances --resource-group {} --name {} --instance-ids {}'.format(
            self.resource_group, self.ss_name, self.instance_id_to_delete), None)
        self.run_command_and_verify('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('virtualMachine.statusesSummary[0].count', self.vm_count-1)])
        self.run_command_and_verify('vm scaleset deallocate --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.run_command_and_verify('vm scaleset delete --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.run_command_and_verify('vm scaleset list --resource-group {}'.format(
            self.resource_group), None)

class VMScaleSetVMsScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        self.resource_group = 'cliTestRg_ScaleSet3'
        self.ss_name = 'scaleset3'
        self.vm_count = 5
        self.instance_ids = ['1', '2', '3', '6', '7']
        super(VMScaleSetVMsScenarioTest, self).__init__(__file__, test_method)

    def test_vm_scaleset_vms(self):
        self.execute(verify_test_output=True)

    def _check_vms_power_state(self, expected_power_state):
        for iid in self.instance_ids:
            self.run_command_and_verify('vm scaleset get-instance-view --resource-group {} --name {} --instance-id {}'.format(
                self.resource_group,
                self.ss_name,
                iid),
                      JMESPathComparator('statuses[1].code', expected_power_state))

    def body(self):
        self.run_command_and_verify('vm scaleset show-instance --resource-group {} --name {} --instance-id {}'.format(
            self.resource_group, self.ss_name, self.instance_ids[0]), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('instanceId', str(self.instance_ids[0]))])
        self.run_command_and_verify('vm scaleset list-instances --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', self.vm_count),
                JMESPathComparator("[].name.starts_with(@, '{}')".format(self.ss_name),
                                   [True]*self.vm_count)])
        self._check_vms_power_state('PowerState/running')
        self.run_command_and_verify('vm scaleset power-off --resource-group {} --name {} --instance-ids *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/stopped')
        self.run_command_and_verify('vm scaleset start --resource-group {} --name {} --instance-ids *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/running')
        self.run_command_and_verify('vm scaleset restart --resource-group {} --name {} --instance-ids *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/running')
        self.run_command_and_verify('vm scaleset deallocate --resource-group {} --name {} --instance-ids *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/deallocated')
        self.run_command_and_verify('vm scaleset delete-instances --resource-group {} --name {} --instance-ids *'.format(
            self.resource_group, self.ss_name), None)
        self.run_command_and_verify('vm scaleset list-instances --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)

class VMScaleSetCreateSimple(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMScaleSetCreateSimple, self).__init__(__file__, test_method)
        self.resource_group = 'scaleset_create_simple_rg'

    def test_vm_scaleset_create_simple(self):
        self.execute(verify_test_output=True)

    def body(self):
        vmss_name = 'vrfvmss'
        # Note: all parameters that are dynamically generated client-side must be overridden here.
        # This includes deployment name, admin name and ssh key.
        self.run_command_no_verify('vm scaleset create --admin-password Test1234@! --name {vmss_name} -g {resource_group}'
                                   ' --admin-username myadmin --deployment-name deployment'
                                   .format(resource_group=self.resource_group, vmss_name=vmss_name))

        self.run_command_and_verify('vm scaleset show --name {vmss_name} -g {resource_group}'
                                    .format(resource_group=self.resource_group, vmss_name=vmss_name), [
                                        JMESPathComparator('virtualMachineProfile.osProfile.windowsConfiguration.enableAutomaticUpdates',
                                                           True)
                                        ])

class VMScaleSetCreateOptions(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMScaleSetCreateOptions, self).__init__(__file__, test_method)
        self.resource_group = 'scaleset_create_options_rg'

    def test_vm_scaleset_create_options(self):
        self.execute(verify_test_output=True)

    def body(self):
        vmss_name = 'vrfvmss'
        instance_count = 4
        caching = 'ReadWrite'
        upgrade_policy = 'automatic'
        ip_name = 'vrfpubip'

        self.run_command_no_verify('network public-ip create --name {ip_name} -g {resource_group} --deployment-name deployment1'
                                   .format(ip_name=ip_name, resource_group=self.resource_group))

        self.run_command_no_verify('vm scaleset create --image Win2012R2Datacenter --admin-password Test1234@! -l westus'
                                   ' --name {vmss_name} -g {resource_group} --disable-overprovision --instance-count {instance_count}'
                                   ' --storage-caching {caching} --upgrade-policy-mode {upgrade_policy}'
                                   ' --private-ip-address-allocation static --private-ip-address 10.0.0.5 --admin-username myadmin'
                                   ' --public-ip-address-type existing --public-ip-address-name {ip_name} --deployment-name deployment2'
                                   .format(vmss_name=vmss_name, resource_group=self.resource_group, instance_count=instance_count,
                                           caching=caching, upgrade_policy=upgrade_policy, ip_name=ip_name))

        self.run_command_and_verify('network lb show --name {vmss_name}lb -g {resource_group}'
                                    .format(vmss_name=vmss_name, resource_group=self.resource_group), [
                                        JMESPathComparator('frontendIpConfigurations[0].publicIpAddress.id.ends_with(@, \'{ip_name}\')'
                                                           .format(ip_name=ip_name), True)
                                        ])

        self.run_command_and_verify('vm scaleset show --name {vmss_name} -g {resource_group}'
                                    .format(resource_group=self.resource_group, vmss_name=vmss_name), [
                                        JMESPathComparator('sku.capacity', instance_count),
                                        JMESPathComparator('virtualMachineProfile.storageProfile.osDisk.caching', caching),
                                        JMESPathComparator('upgradePolicy.mode', upgrade_policy.title())
                                        ])

        self.run_command_and_verify('vm scaleset show-instance -n {vmss_name} -g {resource_group} --instance-id 0'
                                    .format(vmss_name=vmss_name, resource_group=self.resource_group), [
                                        JMESPathComparator('osProfile.windowsConfiguration.provisionVmAgent', True)
                                        ])

class VMScaleSetCreateExistingOptions(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMScaleSetCreateExistingOptions, self).__init__(__file__, test_method)
        self.resource_group = 'scaleset_create_existing_options_rg'

    def test_vm_scaleset_create_existing_options(self):
        self.execute(verify_test_output=True)

    def body(self):
        vmss_name = 'vrfvmss'
        vnet_name = 'vrfvnet'
        subnet_name = 'vrfsubnet'
        lb_name = 'vrflb'
        os_disk_name = 'vrfosdisk'
        container_name = 'vrfcontainer'
        be_pool_name = 'vrflbbepool'
        nat_pool_name = 'vrflbnatpool'
        sku_name = 'Standard_A3'


        self.run_command_no_verify('network vnet create -n {vnet_name} -g {resource_group} --subnet-name {subnet_name}'
                                   ' --deployment-name deployment'
                                   .format(vnet_name=vnet_name, resource_group=self.resource_group, subnet_name=subnet_name))
        self.run_command_no_verify('network lb create --name {lb_name} -g {resource_group} --deployment-name deployment2'
                                   ' --nat-pool-name {nat_pool_name} --backend-pool-name {be_pool_name}'
                                   .format(lb_name=lb_name, resource_group=self.resource_group,
                                           nat_pool_name=nat_pool_name, be_pool_name=be_pool_name))

        self.run_command_no_verify('vm scaleset create --image CentOS --os-disk-name {os_disk_name}'
                                   ' --virtual-network-type existing --virtual-network-name {vnet_name}'
                                   ' --subnet-name {subnet_name} -l "West US" --vm-sku {sku_name}'
                                   ' --storage-container-name {container_name} -g {resource_group} --name {vmss_name}'
                                   ' --load-balancer-type existing --load-balancer-name {lb_name}'
                                   ' --ssh-key-value \'{key_value}\' --deployment-name deployment3a'
                                   ' --load-balancer-backend-pool-name {be_pool_name} --load-balancer-nat-pool-name {nat_pool_name}'
                                   .format(os_disk_name=os_disk_name, vnet_name=vnet_name, subnet_name=subnet_name, lb_name=lb_name,
                                           container_name=container_name, resource_group=self.resource_group, vmss_name=vmss_name,
                                           key_value=TEST_SSH_KEY_PUB, nat_pool_name=nat_pool_name, be_pool_name=be_pool_name,
                                           sku_name=sku_name))

        self.run_command_and_verify('vm scaleset show --name {vmss_name} -g {resource_group}'
                                    .format(resource_group=self.resource_group, vmss_name=vmss_name), [
                                        JMESPathComparator('sku.name', sku_name),
                                        JMESPathComparator('virtualMachineProfile.storageProfile.osDisk.name', os_disk_name),
                                        JMESPathComparator('virtualMachineProfile.storageProfile.osDisk.vhdContainers[0]'
                                                           '.ends_with(@, \'{container_name}\')'
                                                           .format(container_name=container_name), True)
                                        ])
        self.run_command_and_verify('network lb show --name {lb_name} -g {resource_group}'
                                    .format(resource_group=self.resource_group, lb_name=lb_name), [
                                        JMESPathComparator('backendAddressPools[0].backendIpConfigurations[0].id.contains(@, \'{vmss_name}\')'
                                                           .format(vmss_name=vmss_name), True)
                                        ])
        self.run_command_and_verify('network vnet show --name {vnet_name} -g {resource_group}'
                                    .format(resource_group=self.resource_group, vnet_name=vnet_name), [
                                        JMESPathComparator('subnets[0].ipConfigurations[0].id.contains(@, \'{vmss_name}\')'
                                                           .format(vmss_name=vmss_name), True)
                                        ])

class VMAccessAddRemoveLinuxUser(VCRTestBase):

    def __init__(self, test_method):
        super(VMAccessAddRemoveLinuxUser, self).__init__(__file__, test_method)

    def test_vm_add_remove_linux_user(self):
        self.execute(verify_test_output=True)

    def body(self):
        common_part = '-g yugangw4 -n yugangw4-1 -u foouser1'
        verification = [JMESPathComparator('provisioningState', 'Succeeded'),
                        JMESPathComparator('name', 'VMAccessForLinux')]
        self.run_command_and_verify('vm access set-linux-user {} -p Foo12345 '.format(common_part),
                  verification)
        #Ensure to get rid of the user
        self.run_command_and_verify('vm access delete-linux-user {}'.format(common_part),
                  verification)

class VMCreateUbuntuScenarioTest(ResourceGroupVCRTestBase): #pylint: disable=too-many-instance-attributes

    def __init__(self, test_method):
        super(VMCreateUbuntuScenarioTest, self).__init__(__file__, test_method)
        self.deployment_name = 'azurecli-test-deployment-vm-create-ubuntu'
        self.resource_group = 'cliTestRg_VMCreate_Ubuntu'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_names = ['cli-test-vm1']
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'
        self.pub_ssh_filename = None

    def test_vm_create_ubuntu(self):
        self.execute(verify_test_output=True)

    def set_up(self):
        super(VMCreateUbuntuScenarioTest, self).set_up()
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)
        self.pub_ssh_filename = pathname

    def body(self):
        self.run_command_and_verify('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value {ssh_key} --location {location} --deployment-name {deployment}'.format(
            rg=self.resource_group,
            admin=self.admin_username,
            vm_name=self.vm_names[0],
            image=self.vm_image,
            auth_type=self.auth_type,
            ssh_key=self.pub_ssh_filename,
            location=self.location,
            deployment=self.deployment_name,
        ), [
            JMESPathComparator('type(@)', 'object'),
            JMESPathComparator('vm.value.provisioningState', 'Succeeded'),
            JMESPathComparator('vm.value.osProfile.adminUsername', self.admin_username),
            JMESPathComparator('vm.value.osProfile.computerName', self.vm_names[0]),
            JMESPathComparator(
                'vm.value.osProfile.linuxConfiguration.disablePasswordAuthentication',
                True),
            JMESPathComparator(
                'vm.value.osProfile.linuxConfiguration.ssh.publicKeys[0].keyData',
                TEST_SSH_KEY_PUB),
        ])

class VMBootDiagnostics(VCRTestBase):

    def __init__(self, test_method):
        super(VMBootDiagnostics, self).__init__(__file__, test_method)

    def test_vm_enable_disable_boot_diagnostic(self):
        self.execute(verify_test_output=True)

    def body(self):
        common_part = '-g yugangwtest -n yugangwtest-1'
        storage_account = 'yugangwstorage'
        storage_uri = 'https://{}.blob.core.windows.net/'.format(storage_account)
        self.run_command_no_verify('vm boot-diagnostics enable {} --storage {}'.format(common_part, storage_account))
        verification = [JMESPathComparator('diagnosticsProfile.bootDiagnostics.enabled', True),
                        JMESPathComparator('diagnosticsProfile.bootDiagnostics.storageUri', storage_uri)]
        self.run_command_and_verify('vm show {}'.format(common_part), verification)

        #will uncomment after #302 gets addressed
        #self.run('vm boot-diagnostics get-boot-log {}'.format(common_part))

        self.run_command_no_verify('vm boot-diagnostics disable {}'.format(common_part))
        verification = [JMESPathComparator('diagnosticsProfile.bootDiagnostics.enabled', False)]
        self.run_command_and_verify('vm show {}'.format(common_part), verification)

class VMExtensionInstallTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMExtensionInstallTest, self).__init__(__file__, test_method)

    def test_vm_extension_install(self):
        self.execute(verify_test_output=True)

    def body(self):
        publisher = 'Microsoft.OSTCExtensions'
        extension_name = 'VMAccessForLinux'
        vm_name = 'yugangw8-1'
        resource_group = 'yugangw8'
        public_key = ('ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC8InHIPLAu6lMc0d+5voyXqigZfT5r6fAM1+FQAi+mkPDdk2hNq1BG0Bwfc88G'
                      'm7BImw8TS+x2bnZmhCbVnHd6BPCDY7a+cHCSqrQMW89Cv6Vl4ueGOeAWHpJTV9CTLVz4IY1x4HBdkLI2lKIHri9+z7NIdvFk7iOk'
                      'MVGyez5H1xDbF2szURxgc4I2/o5wycSwX+G8DrtsBvWLmFv9YAPx+VkEHQDjR0WWezOjuo1rDn6MQfiKfqAjPuInwNOg5AIxXAOR'
                      'esrin2PUlArNtdDH1zlvI4RZi36+tJO7mtm3dJiKs4Sj7G6b1CjIU6aaj27MmKy3arIFChYav9yYM3IT')
        user_name = 'yugangw'
        config_file_name = 'private_config.json'
        config = {
            'username': user_name,
            'ssh_key': public_key
            }
        config_file = os.path.join(TEST_DIR, config_file_name)
        with open(config_file, 'w') as outfile:
            json.dump(config, outfile)

        try:
            set_cmd = ('vm extension set -n {} --publisher {} --version 1.4  --vm-name {} --resource-group {} --private-config {}'
                       .format(extension_name, publisher, vm_name, resource_group, config_file))
            self.run_command_no_verify(set_cmd)
            self.run_command_and_verify('vm extension show --resource-group {} --vm-name {} --name {}'.format(
                resource_group, vm_name, extension_name), [
                    JMESPathComparator('type(@)', 'object'),
                    JMESPathComparator('name', extension_name),
                    JMESPathComparator('resourceGroup', resource_group)])
        finally:
            os.remove(config_file)

class VMDiagnosticsInstallTest(VCRTestBase):

    def __init__(self, test_method):
        super(VMDiagnosticsInstallTest, self).__init__(__file__, test_method)

    def test_vm_diagnostics_install(self):
        self.execute(verify_test_output=True)

    def body(self):
        #pylint: disable=line-too-long
        vm_name = 'linuxtestvm'
        resource_group = 'travistestresourcegroup'
        storage_account = 'travistestresourcegr3014'
        extension_name = 'LinuxDiagnostic'
        set_cmd = ('vm diagnostics set --vm-name {} --resource-group {} --storage-account {}'
                   .format(vm_name, resource_group, storage_account))
        self.run_command_no_verify(set_cmd)
        self.run_command_and_verify('vm extension show --resource-group {} --vm-name {} --name {}'.format(
            resource_group, vm_name, extension_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', extension_name),
                JMESPathComparator('resourceGroup', resource_group)])

class VMCreateExistingOptions(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMCreateExistingOptions, self).__init__(__file__, test_method, debug=True)
        self.resource_group = 'vm_create_existing_options_rg'

    def test_vm_create_existing_options(self):
        self.execute(verify_test_output=True)

    def body(self):
        availset_name = 'vrfavailset'
        pubip_name = 'vrfpubip'
        storage_name = 'vrfstorage00110011'
        vnet_name = 'vrfvnet'
        subnet_name = 'vrfsubnet'
        nsg_name = 'vrfnsg'
        vm_name = 'vrfvm'
        disk_name = 'vrfosdisk'
        container_name = 'vrfcontainer'

        self.run_command_no_verify('vm availability-set create --name {} -g {} --deployment-name deployment1'.format(availset_name, self.resource_group))
        self.run_command_no_verify('network public-ip create --name {} -g {} --deployment-name deployment2'.format(pubip_name, self.resource_group))
        self.run_command_no_verify('storage account create --name {} -g {} -l westus -t Standard_LRS'.format(storage_name, self.resource_group))
        self.run_command_no_verify('network vnet create --name {} -g {} --subnet-name {} --deployment-name deployment3'
                 .format(vnet_name, self.resource_group, subnet_name))
        self.run_command_no_verify('network nsg create --name {} -g {} --deployment-name deploymet4'
                                   .format(nsg_name, self.resource_group))

        self.run_command_no_verify('vm create --image UbuntuLTS --os-disk-name {disk_name} --virtual-network-type existing'
                 ' --virtual-network-name {vnet_name} --subnet-name {subnet_name} --availability-set-type existing'
                 ' --availability-set-id {availset_name} --public-ip-address-type existing'
                 ' --public-ip-address-name {pubip_name} -l "West US" --deployment-name deployment4'
                 ' --network-security-group-name {nsg_name} --network-security-group-type existing'
                 ' --size Standard_A3 --storage-account-type existing'
                 ' --storage-account-name {storage_name} --storage-container-name {container_name} -g {resource_group}'
                 ' --name {vm_name} --ssh-key-value \'{key_value}\''
                 .format(vnet_name=vnet_name, subnet_name=subnet_name, availset_name=availset_name,
                         pubip_name=pubip_name, resource_group=self.resource_group, nsg_name=nsg_name,
                         vm_name=vm_name, disk_name=disk_name, container_name=container_name,
                         storage_name=storage_name, key_value=TEST_SSH_KEY_PUB))

        self.run_command_and_verify('vm availability-set show -n {availset_name} -g {resource_group}'
                  .format(availset_name=availset_name, resource_group=self.resource_group), [
                      JMESPathComparator('virtualMachines[0].id.ends_with(@, \'{}\')'
                                         .format(vm_name.upper()), True),
                      ])
        self.run_command_and_verify('network nsg show -n {nsg_name} -g {resource_group}'
                  .format(nsg_name=nsg_name, resource_group=self.resource_group), [
                      JMESPathComparator('networkInterfaces[0].id.ends_with(@, \'{}\')'
                                         .format(vm_name + 'VMNic'), True)
                      ])
        self.run_command_and_verify('network nic show -n {vm_name}VMNic -g {resource_group}'
                  .format(vm_name=vm_name, resource_group=self.resource_group), [
                      JMESPathComparator('ipConfigurations[0].publicIpAddress.id.ends_with(@, \'{}\')'
                                         .format(pubip_name), True)
                      ])
        self.run_command_and_verify('vm show -n {vm_name} -g {resource_group}'
                                    .format(vm_name=vm_name, resource_group=self.resource_group), [
                                        JMESPathComparator('storageProfile.osDisk.vhd.uri',
                                                           'http://{storage_name}.blob.core.windows.net/{container_name}/{disk_name}.vhd'
                                                           .format(storage_name=storage_name,
                                                                   container_name=container_name,
                                                                   disk_name=disk_name))
                      ])

class VMCreateCustomIP(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(VMCreateCustomIP, self).__init__(__file__, test_method)
        self.resource_group = 'vm_create_custom_ip_rg'

    def test_vm_create_custom_ip(self):
        self.execute(verify_test_output=True)

    def body(self):
        vm_name = 'vrfvm'
        dns_name = 'vrfmyvm00110011'

        self.run_command_no_verify('vm create -n {vm_name} -g {resource_group} --image openSUSE --private-ip-address-allocation static'
                                   ' --private-ip-address 10.0.0.5 --public-ip-address-allocation static --deployment-name deployment'
                                   ' --dns-name-for-public-ip {dns_name} --ssh-key-value \'{key_value}\''
                                   .format(vm_name=vm_name, resource_group=self.resource_group, dns_name=dns_name, key_value=TEST_SSH_KEY_PUB))

        self.run_command_and_verify('network public-ip show -n {vm_name}PublicIP -g {resource_group}'
                                    .format(vm_name=vm_name, resource_group=self.resource_group), [
                                        JMESPathComparator('publicIpAllocationMethod', 'Static'),
                                        JMESPathComparator('dnsSettings.domainNameLabel', dns_name)
                                        ])
        self.run_command_and_verify('network nic show -n {vm_name}VMNic -g {resource_group}'
                                    .format(vm_name=vm_name, resource_group=self.resource_group), [
                                        JMESPathComparator('ipConfigurations[0].privateIpAllocationMethod', 'Static')
                                        ])
