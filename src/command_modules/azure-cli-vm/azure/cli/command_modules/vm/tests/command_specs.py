# AZURE CLI VM TEST DEFINITIONS
import json
import os
import tempfile

from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

#pylint: disable=method-hidden
class VMImageListByAliasesScenarioTest(CommandTestScript):

    def test_body(self):
        result = self.run('vm image list --offer ubuntu -o tsv')
        assert result.index('14.04.4-LTS') >= 0

    def __init__(self):
        super(VMImageListByAliasesScenarioTest, self).__init__(None, self.test_body, None)

class VMUsageScenarioTest(CommandTestScript):

    def __init__(self):
        super(VMUsageScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm usage list --location westus', JMESPathComparator('type(@)', 'array'))

class VMImageListThruServiceScenarioTest(CommandTestScript):

    def test_body(self):
        cmd = ('vm image list -l westus --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run(cmd)
        assert result.index('15.04') >= 0

        cmd = ('vm image list --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run(cmd)
        assert result.index('15.04') >= 0

    def __init__(self):
        super(VMImageListThruServiceScenarioTest, self).__init__(None, self.test_body, None)

class VMListFoldedScenarioTest(CommandTestScript):

    def __init__(self):
        super(VMListFoldedScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        all_vms = self.run('vm list -o json')
        some_vms = self.run('vm list -g travistestresourcegroup -o json')
        assert len(all_vms) > len(some_vms)

class VMShowListSizesListIPAddressesScenarioTest(CommandTestScript):

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-list-ips'
        self.resource_group = 'cliTestRg_VmListIpAddresses'
        self.location = 'westus'
        self.vm_name = 'vm-with-public-ip'
        self.ip_allocation_method = 'Dynamic'
        super(VMShowListSizesListIPAddressesScenarioTest, self).__init__(
            self.set_up,
            self.test_body,
            self.tear_down)

    def set_up(self):
        self.run('resource group create --location {} --name {}'.format(
            self.location,
            self.resource_group))

    def test_body(self):
        # Expecting no results at the beginning
        self.test('vm list-ip-addresses --resource-group {}'.format(self.resource_group), None)
        self.run('vm create --resource-group {0} --location {1} -n {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--deployment-name {3} --public-ip-address-allocation {4} '
                 '--public-ip-address-type new'.format(
                     self.resource_group, self.location, self.vm_name, self.deployment_name,
                     self.ip_allocation_method))
        self.test('vm show --resource-group {} --name {} --expand instanceView'.format(
            self.resource_group, self.vm_name),
                  [
                      JMESPathComparator('type(@)', 'object'),
                      JMESPathComparator('name', self.vm_name),
                      JMESPathComparator('location', self.location),
                      JMESPathComparator('resourceGroup', self.resource_group),
                  ])
        self.test('vm list-sizes --resource-group {} --name {}'.format(
            self.resource_group,
            self.vm_name),
                  JMESPathComparator('type(@)', 'array'))
        # Expecting the one we just added
        self.test('vm list-ip-addresses --resource-group {}'.format(self.resource_group),
                  [
                      JMESPathComparator('length(@)', 1),
                      JMESPathComparator('[0].virtualMachine.name', self.vm_name),
                      JMESPathComparator('[0].virtualMachine.resourceGroup', self.resource_group),
                      JMESPathComparator(
                          'length([0].virtualMachine.network.publicIpAddresses)',
                          1),
                      JMESPathComparator(
                          '[0].virtualMachine.network.publicIpAddresses[0].ipAllocationMethod',
                          self.ip_allocation_method),
                      JMESPathComparator(
                          'type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)',
                          'string')]
                 )

    def tear_down(self):
        self.run('resource group delete --name {}'.format(self.resource_group))

class VMSizeListScenarioTest(CommandTestScript):

    def __init__(self):
        super(VMSizeListScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm size list --location westus', JMESPathComparator('type(@)', 'array'))

class VMImageListOffersScenarioTest(CommandTestScript):

    def __init__(self):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        super(VMImageListOffersScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm image list-offers --location {} --publisher-name {}'.format(
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

class VMImageListPublishersScenarioTest(CommandTestScript):

    def __init__(self):
        self.location = 'westus'
        super(VMImageListPublishersScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm image list-publishers --location {}'.format(self.location),
                  [
                      JMESPathComparator('type(@)', 'array'),
                      # all results should have location has set in the test
                      JMESPathComparator("length([?location == '{}']) == length(@)".format(
                          self.location),
                                         True),
                  ])

class VMImageListSkusScenarioTest(CommandTestScript):

    def __init__(self):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'
        super(VMImageListSkusScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm image list-skus --location {} --publisher-name {} --offer {}'.format(
            self.location, self.publisher_name, self.offer),
                  [
                      JMESPathComparator('type(@)', 'array'),
                      # all results should have location has set in the test
                      JMESPathComparator("length([?location == '{}']) == length(@)".format(
                          self.location),
                                         True),
                      # all results should have the correct publisher name
                      JMESPathComparator(
                          "length([].id.contains(@, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/'))".format( #pylint: disable=line-too-long
                              self.publisher_name, self.offer),
                          27),
                  ])

class VMImageShowScenarioTest(CommandTestScript):

    def __init__(self):
        self.location = 'westus'
        self.publisher_name = 'Canonical'
        self.offer = 'UbuntuServer'
        self.skus = '14.04.2-LTS'
        self.version = '14.04.201503090'
        super(VMImageShowScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm image show --location {} --publisher-name {} --offer {} --skus {} --version {}'.format( #pylint: disable=line-too-long
            self.location, self.publisher_name, self.offer, self.skus, self.version),
                  [
                      JMESPathComparator('type(@)', 'object'),
                      JMESPathComparator('location', self.location),
                      JMESPathComparator('name', self.version),
                      # all results should have the correct publisher name
                      JMESPathComparator(
                          "contains(id, '/Publishers/{}/ArtifactTypes/VMImage/Offers/{}/Skus/{}/Versions/{}')".format( #pylint: disable=line-too-long
                              self.publisher_name, self.offer, self.skus, self.version),
                          True),
                  ])

class VMGeneralizeScenarioTest(CommandTestScript):

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-generalize'
        self.resource_group = 'cliTestRg_VmGeneralize'
        self.location = 'westus'
        self.vm_name = 'vm-generalize'
        super(VMGeneralizeScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

    def set_up(self):
        self.run('resource group create --location {} --name {}'.format(
            self.location,
            self.resource_group))

    def test_body(self):
        self.run('vm create --resource-group {0} --location {1} --name {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--deployment-name {3}'.format(
                     self.resource_group, self.location, self.vm_name, self.deployment_name))
        self.run('vm power-off --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        # Should be able to generalize the VM after it has been stopped
        self.test(
            'vm generalize --resource-group {} --name {}'.format(
                self.resource_group,
                self.vm_name), None)

    def tear_down(self):
        self.run('resource group delete --name {}'.format(self.resource_group))

class VMCreateAndStateModificationsScenarioTest(CommandTestScript):

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-state-mod'
        self.resource_group = 'cliTestRg_VmStateMod'
        self.location = 'westus'
        self.vm_name = 'vm-state-mod'
        super(VMCreateAndStateModificationsScenarioTest, self).__init__(
            self.set_up,
            self.test_body,
            self.tear_down)

    def set_up(self):
        self.run('resource group create --location {} --name {}'.format(
            self.location,
            self.resource_group))

    def _check_vm_power_state(self, expected_power_state):
        self.test(
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

    def test_body(self):
        # Expecting no results
        self.test('vm list --resource-group {}'.format(self.resource_group), None)
        self.run('vm create --resource-group {0} --location {1} --name {2} --admin-username ubuntu '
                 '--image Canonical:UbuntuServer:14.04.4-LTS:latest --admin-password testPassword0 '
                 '--deployment-name {3}'.format(
                     self.resource_group, self.location, self.vm_name, self.deployment_name))
        # Expecting one result, the one we created
        self.test('vm list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('length(@)', 1),
            JMESPathComparator('[0].resourceGroup', self.resource_group),
            JMESPathComparator('[0].name', self.vm_name),
            JMESPathComparator('[0].location', self.location),
            JMESPathComparator('[0].provisioningState', 'Succeeded'),
        ])
        self._check_vm_power_state('PowerState/running')
        self.run('vm power-off --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/stopped')
        self.run('vm start --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.run('vm restart --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/running')
        self.run('vm deallocate --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        self._check_vm_power_state('PowerState/deallocated')
        self.run('vm delete --resource-group {} --name {}'.format(
            self.resource_group, self.vm_name))
        # Expecting no results
        self.test('vm list --resource-group {}'.format(self.resource_group), None)

    def tear_down(self):
        self.run('resource group delete --name {}'.format(self.resource_group))

class VMAvailSetScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_Availset'
        self.location = 'westus'
        self.name = 'availset-test'
        super(VMAvailSetScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

    def set_up(self):
        # TODO Create the resource group and availability set here once the command exists
        pass

    def test_body(self):
        self.test('vm availability-set list --resource-group {}'.format(self.resource_group), [
            JMESPathComparator('length(@)', 1),
            JMESPathComparator('[0].name', self.name),
            JMESPathComparator('[0].resourceGroup', self.resource_group),
            JMESPathComparator('[0].location', self.location),
        ])
        self.test('vm availability-set list-sizes --resource-group {} --name {}'.format(
            self.resource_group, self.name), JMESPathComparator('type(@)', 'array'))
        self.test('vm availability-set show --resource-group {} --name {}'.format(
            self.resource_group, self.name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.name),
                JMESPathComparator('resourceGroup', self.resource_group),
                JMESPathComparator('location', self.location)])
        self.test('vm availability-set delete --resource-group {} --name {}'.format(
            self.resource_group, self.name), None)
        self.test('vm availability-set list --resource-group {}'.format(
            self.resource_group), None)

    def tear_down(self):
        pass

class VMExtensionsScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_VMExtensions'
        self.location = 'westus'
        self.vm_name = 'windows-ext'
        self.extension_name = 'IaaSDiagnostics'
        super(VMExtensionsScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

    def set_up(self):
        # TODO Create the resource group and VM with extension here once the command exists
        pass

    def test_body(self):
        self.test('vm extension show --resource-group {} --vm-name {} --name {}'.format(
            self.resource_group, self.vm_name, self.extension_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.extension_name),
                JMESPathComparator('resourceGroup', self.resource_group)])
        self.test('vm extension delete --resource-group {} --vm-name {} --name {}'.format(
            self.resource_group, self.vm_name, self.extension_name),
                  None)

    def tear_down(self):
        pass


class VMMachineExtensionImageScenarioTest(CommandTestScript):

    def __init__(self):
        self.location = 'westus'
        self.publisher = 'Microsoft.Azure.Diagnostics'
        self.type = 'IaaSDiagnostics'
        self.version = '1.6.4.0'
        super(VMMachineExtensionImageScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm extension image list-types --location {} --publisher-name {}'.format(
            self.location, self.publisher), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?location == '{}']) == length(@)".format(self.location),
                                   True),
            ])
        self.test('vm extension image list-versions --location {} --publisher-name {} --type {}'.format( #pylint: disable=line-too-long
            self.location, self.publisher, self.type), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator("length([?location == '{}']) == length(@)".format(self.location),
                                   True),
            ])
        self.test('vm extension image show --location {} --publisher-name {} --type {} --version {}'.format( #pylint: disable=line-too-long
            self.location, self.publisher, self.type, self.version), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('location', self.location),
                JMESPathComparator("contains(id, '/Providers/Microsoft.Compute/Locations/{}/Publishers/{}/ArtifactTypes/VMExtension/Types/{}/Versions/{}')".format( #pylint: disable=line-too-long
                    self.location, self.publisher, self.type, self.version
                ), True)])


class VMExtensionImageSearchScenarioTest(CommandTestScript):

    def __init__(self):
        super(VMExtensionImageSearchScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        #pick this specific name, so the search will be under one publisher. This avoids
        #the parallel searching behavior that causes incomplete VCR recordings.
        publisher = 'Vormetric.VormetricTransparentEncryption'
        image_name = 'VormetricTransparentEncryptionAgent'
        verification = [
            JMESPathComparator('type(@)', 'array'),
            JMESPathComparator("length([?name == '{}']) == length(@)".format(image_name), True),
            ]
        cmd = ('vm extension image list -l westus --publisher {} --name {} -o json'.format(publisher, image_name))#pylint: disable=line-too-long
        self.test(cmd, verification)


class VMScaleSetGetsScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'CLI_TEST1'
        self.ss_name = 'clitestvm'
        self.location = 'westus'
        super(VMScaleSetGetsScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm scaleset list-all', [
            JMESPathComparator('type(@)', 'array')])
        self.test('vm scaleset list --resource-group {}'.format(
            self.resource_group), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator('[0].name', self.ss_name),
                JMESPathComparator('[0].location', self.location),
                JMESPathComparator('[0].resourceGroup', self.resource_group)])
        self.test('vm scaleset list-skus --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name),
                  JMESPathComparator('type(@)', 'array'))
        self.test('vm scaleset show --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', self.ss_name),
                JMESPathComparator('location', self.location),
                JMESPathComparator('resourceGroup', self.resource_group)])
        self.test('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('type(statuses)', 'array')])

class VMScaleSetStatesScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_ScaleSet1'
        self.ss_name = 'scaleset1'
        super(VMScaleSetStatesScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm scaleset power-off --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset start --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset restart --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset update-instances --resource-group {} --name {} --instance-ids 0'.format( #pylint: disable=line-too-long
            self.resource_group, self.ss_name), None)

class VMScaleSetDeleteScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_ScaleSet1'
        self.ss_name = 'scaleset1'
        self.vm_count = 5
        self.instance_id_to_delete = 2
        super(VMScaleSetDeleteScenarioTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        self.test('vm scaleset list --resource-group {}'.format(
            self.resource_group), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', 1),
                JMESPathComparator('[0].name', self.ss_name),
                JMESPathComparator('[0].resourceGroup', self.resource_group)])
        self.test('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('virtualMachine.statusesSummary[0].count', self.vm_count)])
        self.test('vm scaleset delete-instances --resource-group {} --name {} --instance-ids {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.ss_name, self.instance_id_to_delete), None)
        self.test('vm scaleset get-instance-view --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('type(virtualMachine)', 'object'),
                JMESPathComparator('virtualMachine.statusesSummary[0].count', self.vm_count-1)])
        self.test('vm scaleset deallocate --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset delete --resource-group {} --name {}'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset list --resource-group {}'.format(
            self.resource_group), None)

class VMScaleSetVMsScenarioTest(CommandTestScript):

    def __init__(self):
        self.resource_group = 'cliTestRg_ScaleSet3'
        self.ss_name = 'scaleset3'
        self.vm_count = 5
        self.instance_ids = ['1', '2', '3', '6', '7']
        super(VMScaleSetVMsScenarioTest, self).__init__(None, self.test_body, None)

    def _check_vms_power_state(self, expected_power_state):
        for iid in self.instance_ids:
            self.test('vm scaleset-vm get-instance-view --resource-group {} --name {} --instance-id {}'.format( #pylint: disable=line-too-long
                self.resource_group,
                self.ss_name,
                iid),
                      JMESPathComparator('statuses[1].code', expected_power_state))

    def test_body(self):
        self.test('vm scaleset-vm show --resource-group {} --name {} --instance-id {}'.format(
            self.resource_group, self.ss_name, self.instance_ids[0]), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('instanceId', str(self.instance_ids[0]))])
        self.test('vm scaleset-vm list --resource-group {} --virtual-machine-scale-set-name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.ss_name), [
                JMESPathComparator('type(@)', 'array'),
                JMESPathComparator('length(@)', self.vm_count),
                JMESPathComparator("[].name.starts_with(@, '{}')".format(self.ss_name),
                                   [True]*self.vm_count)])
        self._check_vms_power_state('PowerState/running')
        self.test('vm scaleset-vm power-off --resource-group {} --name {} --instance-id *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/stopped')
        self.test('vm scaleset-vm start --resource-group {} --name {} --instance-id *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/running')
        self.test('vm scaleset-vm restart --resource-group {} --name {} --instance-id *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/running')
        self.test('vm scaleset-vm deallocate --resource-group {} --name {} --instance-id *'.format(
            self.resource_group, self.ss_name), None)
        self._check_vms_power_state('PowerState/deallocated')
        self.test('vm scaleset-vm delete --resource-group {} --name {} --instance-id *'.format(
            self.resource_group, self.ss_name), None)
        self.test('vm scaleset-vm list --resource-group {} --virtual-machine-scale-set-name {}'.format( #pylint: disable=line-too-long
            self.resource_group, self.ss_name), None)

class VMAccessAddRemoveLinuxUser(CommandTestScript):

    def __init__(self):
        super(VMAccessAddRemoveLinuxUser, self).__init__(None, self.test_body, None)

    def test_body(self):
        common_part = '-g yugangw4 -n yugangw4-1 -u foouser1'
        verification = [JMESPathComparator('provisioningState', 'Succeeded'),
                        JMESPathComparator('name', 'VMAccessForLinux')]
        self.test('vm access set-linux-user {} -p Foo12345 '.format(common_part),
                  verification)
        #Ensure to get rid of the user
        self.test('vm access delete-linux-user {}'.format(common_part),
                  verification)

class VMCreateUbuntuScenarioTest(CommandTestScript): #pylint: disable=too-many-instance-attributes

    TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n" #pylint: disable=line-too-long

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-create-ubuntu'
        self.resource_group = 'cliTestRg_VMCreate_Ubuntu'
        self.admin_username = 'ubuntu'
        self.location = 'westus'
        self.vm_names = ['cli-test-vm1']
        self.vm_image = 'UbuntuLTS'
        self.auth_type = 'ssh'
        self.pub_ssh_filename = None
        super(VMCreateUbuntuScenarioTest, self).__init__(
            self.set_up,
            self.test_body,
            self.tear_down)

    def set_up(self):
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(VMCreateUbuntuScenarioTest.TEST_SSH_KEY_PUB)
        self.pub_ssh_filename = pathname
        self.run('resource group create --location {} --name {}'.format(
            self.location,
            self.resource_group))

    def test_body(self):
        self.test('vm create --resource-group {rg} --admin-username {admin} --name {vm_name} --authentication-type {auth_type} --image {image} --ssh-key-value {ssh_key} --location {location} --deployment-name {deployment}'.format( #pylint: disable=line-too-long
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
                VMCreateUbuntuScenarioTest.TEST_SSH_KEY_PUB),
        ])

    def tear_down(self):
        self.run('resource group delete --name {}'.format(self.resource_group))

class VMBootDiagnostics(CommandTestScript):

    def __init__(self):
        super(VMBootDiagnostics, self).__init__(None, self.test_body, None)

    def test_body(self):
        common_part = '-g yugangw5 -n yugangw5-1'
        #pylint: disable=line-too-long
        storage_uri = 'https://yugangwstorage.blob.core.windows.net/'
        self.run('vm boot-diagnostics enable {} --storage-uri {}'.format(common_part, storage_uri))
        verification = [JMESPathComparator('diagnosticsProfile.bootDiagnostics.enabled', True),
                        JMESPathComparator('diagnosticsProfile.bootDiagnostics.storageUri', storage_uri)]
        self.test('vm show {}'.format(common_part), verification)

        #will uncomment after #302 gets addressed
        #self.run('vm boot-diagnostics get-boot-log {}'.format(common_part))

        self.run('vm boot-diagnostics disable {}'.format(common_part))
        verification = [JMESPathComparator('diagnosticsProfile.bootDiagnostics.enabled', False)]
        self.test('vm show {}'.format(common_part), verification)


class VMExtensionInstallTest(CommandTestScript):

    def __init__(self):
        super(VMExtensionInstallTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        #pylint: disable=line-too-long
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
            self.run(set_cmd)
            self.test('vm extension show --resource-group {} --vm-name {} --name {}'.format(
                resource_group, vm_name, extension_name), [
                    JMESPathComparator('type(@)', 'object'),
                    JMESPathComparator('name', extension_name),
                    JMESPathComparator('resourceGroup', resource_group)])
        finally:
            os.remove(config_file)

class VMDiagnosticsTest(CommandTestScript):

    def __init__(self):
        super(VMDiagnosticsTest, self).__init__(None, self.test_body, None)

    def test_body(self):
        #pylint: disable=line-too-long
        vm_name = 'yugangwtest-1'
        resource_group = 'yugangwtest'
        storage_account = 'vhdstorage4jjdhrm754a5g'
        extension_name = 'LinuxDiagnostic'
        set_cmd = ('vm diagnostics set --vm-name {} --resource-group {} --storage-account {}'
                   .format(vm_name, resource_group, storage_account))
        self.run(set_cmd)
        self.test('vm extension show --resource-group {} --vm-name {} --name {}'.format(
            resource_group, vm_name, extension_name), [
                JMESPathComparator('type(@)', 'object'),
                JMESPathComparator('name', extension_name),
                JMESPathComparator('resourceGroup', resource_group)])


ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': VMUsageScenarioTest()
    },
    {
        'test_name': 'vm_show_list_sizes_list_ip_addresses',
        'command': VMShowListSizesListIPAddressesScenarioTest()
    },
    {
        'test_name': 'vm_images_list_by_aliases',
        'command': VMImageListByAliasesScenarioTest()
    },
    {
        'test_name': 'vm_images_list_thru_services',
        'command': VMImageListThruServiceScenarioTest()
    },
    {
        'test_name': 'vm_size_list',
        'command': VMSizeListScenarioTest()
    },
    {
        'test_name': 'vm_image_list_offers',
        'command': VMImageListOffersScenarioTest()
    },
    {
        'test_name': 'vm_image_list_publishers',
        'command': VMImageListPublishersScenarioTest()
    },
    {
        'test_name': 'vm_image_list_skus',
        'command': VMImageListSkusScenarioTest()
    },
    {
        'test_name': 'vm_image_show',
        'command': VMImageShowScenarioTest()
    },
    {
        'test_name': 'vm_generalize',
        'command': VMGeneralizeScenarioTest()
    },
    {
        'test_name': 'vm_create_state_modifications',
        'command': VMCreateAndStateModificationsScenarioTest()
    },
    {
        'test_name': 'vm_availset',
        'command': VMAvailSetScenarioTest()
    },
    {
        'test_name': 'vm_extension',
        'command': VMExtensionsScenarioTest()
    },
    {
        'test_name': 'vm_machine_extension_image',
        'command': VMMachineExtensionImageScenarioTest()
    },
    {
        'test_name': 'vm_extension_image_search',
        'command': VMExtensionImageSearchScenarioTest()
    },
    {
        'test_name': 'vm_combined_list',
        'command': VMListFoldedScenarioTest()
    },
    {
        'test_name': 'vm_scaleset_gets',
        'command': VMScaleSetGetsScenarioTest()
    },
    {
        'test_name': 'vm_scaleset_states',
        'command': VMScaleSetStatesScenarioTest()
    },
    {
        'test_name': 'vm_scaleset_delete',
        'command': VMScaleSetDeleteScenarioTest()
    },
    {
        'test_name': 'vm_scaleset_vms',
        'command': VMScaleSetVMsScenarioTest()
    },
    {
        'test_name': 'vm_add_remove_linux_user',
        'command': VMAccessAddRemoveLinuxUser()
    },
    {
        'test_name': 'vm_create_ubuntu',
        'command': VMCreateUbuntuScenarioTest()
    },
    {
        'test_name': 'vm_enable_disable_boot_diagnostic',
        'command': VMBootDiagnostics()
    },
    {
        'test_name': 'vm_extension_install',
        'command': VMExtensionInstallTest()
    },
    {
        'test_name': 'vm_diagnostics_install',
        'command': VMDiagnosticsTest()
    }
]
