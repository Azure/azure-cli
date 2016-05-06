# AZURE CLI VM TEST DEFINITIONS
from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

#pylint: disable=method-hidden
class VMImageListByAliasesScenarioTest(CommandTestScript):

    def test_body(self):
        result = self.run('vm image list --offer ubuntu -o tsv')
        assert result.index('14.04.4-LTS') >= 0

    def __init__(self):
        super(VMImageListByAliasesScenarioTest, self).__init__(None, self.test_body, None)

class VMImageListThruServiceScenarioTest(CommandTestScript):

    def test_body(self):
        cmd = ('vm image list -l westus --publisher Canonical --offer '
               'Ubuntu_Snappy_Core -o tsv --all')
        result = self.run(cmd)
        assert result.index('15.04') >= 0

    def __init__(self):
        super(VMImageListThruServiceScenarioTest, self).__init__(None, self.test_body, None)

class VMListIPAddressesScenarioTest(CommandTestScript):

    def __init__(self):
        self.deployment_name = 'azurecli-test-deployment-vm-list-ips'
        self.resource_group = 'cliTestRg_VmListIpAddresses'
        self.vm_name = 'vm-with-public-ip'
        self.ip_allocation_method = 'Dynamic'
        super(VMListIPAddressesScenarioTest, self).__init__(
            self.set_up,
            self.test_body,
            self.tear_down)

    def set_up(self):
        # TODO Create the resource group
        # (e.g. az resource group create --name cliTestRg_VmListIpAddresses)
        pass

    def test_body(self):
        # Expecting no results at the beginning
        self.test('vm list-ip-addresses --resource-group {}'.format(self.resource_group), None)
        self.run(['vm', 'create', '-g', self.resource_group, '-l', 'West US', '-n', self.vm_name,
                  '--admin-username', 'ubuntu', '--image', 'UbuntuLTS', '--admin-password',
                  'testPassword0', '--deployment-name', self.deployment_name,
                  '--public-ip-address-allocation', self.ip_allocation_method,
                  '--public-ip-address-type', 'new'])
        # Expecting the one we just added
        self.test('vm list-ip-addresses --resource-group {}'.format(self.resource_group),
                  [
                      JMESPathComparator('length(@)', 1),
                      JMESPathComparator('[0].virtualMachine.name', self.vm_name),
                      JMESPathComparator('[0].virtualMachine.resourceGroup', self.resource_group),
                      JMESPathComparator('length([0].virtualMachine.network.publicIpAddresses)', 1),
                      JMESPathComparator(
                          '[0].virtualMachine.network.publicIpAddresses[0].ipAllocationMethod',
                          self.ip_allocation_method),
                      JMESPathComparator(
                          'type([0].virtualMachine.network.publicIpAddresses[0].ipAddress)',
                          'string')]
                 )

    def tear_down(self):
        # TODO Delete the resource group instead
        self.run('vm delete --resource-group {} --name {}'.format(
            self.resource_group,
            self.vm_name))

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'vm_usage_list_westus',
        'command': 'vm usage list --location westus --output json',
    },
    {
        'test_name': 'vm_list_from_group',
        'command': 'vm list --resource-group XPLATTESTGEXTENSION9085',
    },
    {
        'test_name': 'vm_list_ip_addresses',
        'command': VMListIPAddressesScenarioTest()
    },
    {
        'test_name': 'vm_images_list_by_aliases',
        'command': VMImageListByAliasesScenarioTest()
    },
    {
        'test_name': 'vm_images_list_thru_services',
        'command': VMImageListThruServiceScenarioTest()
    }
]


