import json
# AZURE CLI RESOURCE TEST DEFINITIONS

from azure.cli.utils.command_test_script import CommandTestScript, JMESPathComparator

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

class ResourceScenarioTest(CommandTestScript):

    def test_body(self):
        s = self
        rg = 'travistestresourcegroup'
        all_resources = json.loads(s.run('resource list -o json'))
        some_resources = json.loads(s.run('resource list -l centralus -o json'))
        assert len(all_resources) > len(some_resources)

        s.test('resource list -l centralus',
            [
                JMESPathComparator('[0].location', 'centralus'),
            ])

        s.test('resource list --tag displayName=PublicIPAddress',
            [
                JMESPathComparator('[0].type', 'Microsoft.Network/publicIPAddresses')
            ])

        s.test('resource list --resource-type Microsoft.Network/networkInterfaces',
            [
                JMESPathComparator('[0].type', 'Microsoft.Network/networkInterfaces')
            ])

        s.test('resource list --name TravisTestResourceGroup',
            [
                JMESPathComparator('[0].name', 'TravisTestResourceGroup')
            ])

        all_tagged_displayname = json.loads(s.run('resource list --tag displayName -o json'))
        storage_acc_tagged_displayname = \
            json.loads(s.run('resource list --tag displayName=StorageAccount -o json'))
        assert len(all_tagged_displayname) > len(storage_acc_tagged_displayname)

        s.test('resource show -n xplatvmExt1314 --resource-group XPLATTESTGEXTENSION9085 ' + \
               '--resource-type Microsoft.Compute/virtualMachines',
               {'name': 'xplatvmExt1314', 'location': 'southeastasia'}
        )

    def __init__(self):
        super(ResourceScenarioTest, self).__init__(None, self.test_body, None)

ENV_VAR = {}

TEST_DEF = [
    #{
    #    'test_name': 'resource_group_scenario',
    #    'script': ResourceGroupScenarioTest()
    #},
    #{
    #    'test_name': 'resource_scenario',
    #    'script': ResourceScenarioTest()
    #},
]

