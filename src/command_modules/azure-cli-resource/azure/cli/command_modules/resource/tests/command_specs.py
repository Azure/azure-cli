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
        all_resources = s.run('resource list -o json')
        some_resources = s.run('resource list -l centralus -o json')
        assert len(all_resources) > len(some_resources)

        s.test('resource list -l centralus',
            [
                JMESPathComparator("length([?location == 'centralus']) == length(@)", True)
            ])

        s.test('resource list --tag displayName=PublicIPAddress',
            [
                JMESPathComparator("length([?type == 'Microsoft.Network/publicIPAddresses']) == length(@)", True)
            ])

        s.test('resource list --resource-type Microsoft.Network/networkInterfaces',
            [
                JMESPathComparator("length([?type == 'Microsoft.Network/networkInterfaces']) == length(@)", True)
            ])

        s.test('resource list --name TravisTestResourceGroup',
            [
                JMESPathComparator("length([?name == 'TravisTestResourceGroup']) == length(@)", True)
            ])

        s.test('resource list -g yugangw',
            [
                JMESPathComparator("length([?resourceGroup == 'yugangw']) == length(@)", True)
            ])

        all_tagged_displayname = s.run('resource list --tag displayName -o json')
        storage_acc_tagged_displayname = \
            s.run('resource list --tag displayName=StorageAccount -o json')
        assert len(all_tagged_displayname) > len(storage_acc_tagged_displayname)

        s.run('resource set -n testserver23456 -g {} --resource-type '
               'Microsoft.Sql/servers --tags test=pass'.format(rg))

        # check for simple resource with tag
        s.test('resource show -n testserver23456 -g {} --resource-type '
               'Microsoft.Sql/servers'.format(rg), {
                    'name': 'testserver23456', 'location': 'West US', 'resourceGroup': rg,
                    'tags': {'test': 'pass'}
                })

        # check for child resource
        s.test('resource show -n testsql23456 -g {} --parent servers/testserver23456 '
               '--resource-type Microsoft.Sql/databases'.format(rg),
            {'name': 'testsql23456', 'location': 'West US', 'resourceGroup': rg})

        # Check that commands succeeds regardless of parameter order
        s.test('resource show -n testsql23456 -g {} --resource-type Microsoft.Sql/databases '
               '--parent servers/testserver23456 '.format(rg),
            {'name': 'testsql23456', 'location': 'West US', 'resourceGroup': rg})

        # clear tag and verify
        s.run('resource set -n testserver23456 -g {} --resource-type '
               'Microsoft.Sql/servers --tags'.format(rg))
        s.test('resource show -n testserver23456 -g {} --resource-type '
               'Microsoft.Sql/servers'.format(rg), {'tags': {}})

    def __init__(self):
        super(ResourceScenarioTest, self).__init__(None, self.test_body, None)

class TagScenarioTest(CommandTestScript):

    def set_up(self):
        tn = self.tag_name

    def test_body(self):
        s = self
        tn = s.tag_name

        s.test('tag list --query "[?tagName == \'{}\']"'.format(tn), None)
        s.run('tag create -n {}'.format(tn))
        s.test('tag list --query "[?tagName == \'{}\']"'.format(tn),
            {'tagName': tn, 'values': [], 'count': {'value': "0"}})
        s.run('tag add-value -n {} --value test'.format(tn))
        s.run('tag add-value -n {} --value test2'.format(tn))
        s.test('tag list --query "[?tagName == \'{}\']"'.format(tn),
            [
                JMESPathComparator('[].values[].tagValue', [u'test', u'test2'])
            ])
        s.run('tag remove-value -n {} --value test'.format(tn))
        s.test('tag list --query "[?tagName == \'{}\']"'.format(tn),
            [
                JMESPathComparator('[].values[].tagValue', [u'test2'])
            ])
        s.run('tag remove-value -n {} --value test2'.format(tn))
        s.test('tag list --query "[?tagName == \'{}\']"'.format(tn),
            [
                JMESPathComparator('[].values[].tagValue', [])
            ])
        s.run('tag delete -n {}'.format(tn))
        s.test('tag list --query "[?tagName == \'{}\']"'.format(self.tag_name), None)        

    def tear_down(self):
        tn = self.tag_name
        tags = self.run('tag list --query "[?tagName == \'{}\'].values[].tagValue" -o json'.format(tn))
        for tag in tags:
            self.run('tag remove-value -n {} --value {}'.format(tn, tag))
        self.run('tag delete -n {}'.format(tn))

    def __init__(self):
        self.tag_name = 'travistesttag'
        super(TagScenarioTest, self).__init__(self.set_up, self.test_body, self.tear_down)

ENV_VAR = {}

TEST_DEF = [
    {
        'test_name': 'resource_group_scenario',
        'script': ResourceGroupScenarioTest()
    },
    {
        'test_name': 'resource_scenario',
        'script': ResourceScenarioTest()
    },
    {
        'test_name': 'tag_scenario',
        'script': TagScenarioTest()
    },
]

