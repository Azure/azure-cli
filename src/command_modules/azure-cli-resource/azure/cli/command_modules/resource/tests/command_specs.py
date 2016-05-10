# AZURE CLI RESOURCE TEST DEFINITIONS

from azure.cli.utils.command_test_script import CommandTestScript

#pylint: disable=method-hidden
class ResourceGroupScenarioTest(CommandTestScript):

    def set_up(self):
        self.resource_group = 'travistestrg'
        if self.run('resource group exists -n {}'.format(self.resource_group)):
            self.run('resource group delete -n {}'.format(self.resource_group))

    def test_body(self):
        s = self
        rg = self.resource_group
        s.test('resource group create -n {} -l westus --tag a=b;c'.format(rg),
            {'name':'{}'.format(rg), 'tags': {'a':'b', 'c':''}})
        s.test('resource group exists -n {}'.format(rg), True)
        s.test('resource group show -n {}'.format(rg),
            {'name': rg, 'tags': {'a':'b', 'c':''}})
        s.test('resource group list --tag a=b', {'name': rg, 'tags': {'a':'b', 'c':''}})
        s.run('resource group delete -n {}'.format(rg))
        s.test('resource group exists -n {}'.format(rg), None)

    def tear_down(self):
        if self.run('resource group exists -n {}'.format(self.resource_group)):
            self.run('resource group delete -n {}'.format(self.resource_group))

    def __init__(self):
        super(ResourceGroupScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'resource_group_scenario',
        'script': ResourceGroupScenarioTest()
    },
    {
        'test_name': 'resource_show_under_group',
        'command': 'resource show -n xplatvmExt1314 --resource-group XPLATTESTGEXTENSION9085 --resource-type Microsoft.Compute/virtualMachines --output json'
    }
]

