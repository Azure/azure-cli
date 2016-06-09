import json
# AZURE CLI RESOURCE TEST DEFINITIONS

from azure.cli.utils.vcr_test_base import VCRTestBase, JMESPathCheck, NoneCheck, BooleanCheck

#pylint: disable=method-hidden
class ResourceGroupScenarioTest(VCRTestBase):

    def test_resource_group(self):
        self.execute()

    def __init__(self, test_method):
        self.resource_group = 'travistestrg'
        super(ResourceGroupScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        if self.cmd('resource group exists -n {}'.format(self.resource_group)):
            self.cmd('resource group delete -n {}'.format(self.resource_group))

    def body(self):
        s = self
        rg = self.resource_group
        s.cmd('resource group create -n {} -l westus --tag a=b;c'.format(rg), checks=[
            JMESPathCheck('name', rg),
            JMESPathCheck('tags', {'a':'b', 'c':''})
        ])
        s.cmd('resource group exists -n {}'.format(rg), checks=BooleanCheck(True))
        s.cmd('resource group show -n {}'.format(rg), checks=[
            JMESPathCheck('name', rg),
            JMESPathCheck('tags', {'a':'b', 'c':''})
        ])
        s.cmd('resource group list --tag a=b', checks=[
            JMESPathCheck('[0].name', rg),
            JMESPathCheck('[0].tags', {'a':'b', 'c':''})
        ])
        s.cmd('resource group delete -n {}'.format(rg))
        s.cmd('resource group exists -n {}'.format(rg), checks=NoneCheck())

    def tear_down(self):
        if self.cmd('resource group exists -n {}'.format(self.resource_group)):
            self.cmd('resource group delete -n {}'.format(self.resource_group))

class ResourceScenarioTest(VCRTestBase):

    def test_resource_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(ResourceScenarioTest, self).__init__(__file__, test_method)

    def body(self):
        s = self
        rg = 'travistestresourcegroup'
        all_resources = s.cmd('resource list -o json')
        some_resources = s.cmd('resource list -l centralus -o json')
        assert len(all_resources) > len(some_resources)

        s.cmd('resource list -l centralus',
            checks=JMESPathCheck("length([?location == 'centralus']) == length(@)", True))
        s.cmd('resource list --tag displayName=PublicIPAddress',
            checks=JMESPathCheck("length([?type == 'Microsoft.Network/publicIPAddresses']) == length(@)", True))
        s.cmd('resource list --resource-type Microsoft.Network/networkInterfaces',
            checks=JMESPathCheck("length([?type == 'Microsoft.Network/networkInterfaces']) == length(@)", True))

        s.cmd('resource list --name TravisTestResourceGroup',
            checks=JMESPathCheck("length([?name == 'TravisTestResourceGroup']) == length(@)", True))

        s.cmd('resource list -g yugangw',
            checks=JMESPathCheck("length([?resourceGroup == 'yugangw']) == length(@)", True))

        all_tagged_displayname = s.cmd('resource list --tag displayName -o json')
        storage_acc_tagged_displayname = \
            s.cmd('resource list --tag displayName=StorageAccount -o json')
        assert len(all_tagged_displayname) > len(storage_acc_tagged_displayname)

        s.cmd('resource tag -n testserver23456 -g {} --resource-type Microsoft.Sql/servers --tags test=pass'.format(rg))

        # check for simple resource with tag
        s.cmd('resource show -n testserver23456 -g {} --resource-type Microsoft.Sql/servers'.format(rg), checks=[
            JMESPathCheck('name', 'testserver23456'),
            JMESPathCheck('location', 'West US'),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('tags', {'test': 'pass'})
        ])

        # check for child resource
        s.cmd('resource show -n testsql23456 -g {} --parent servers/testserver23456 --resource-type Microsoft.Sql/databases'.format(rg), checks=[
            JMESPathCheck('name', 'testsql23456'),
            JMESPathCheck('location', 'West US'),
            JMESPathCheck('resourceGroup', rg)
        ])

        # Check that commands succeeds regardless of parameter order
        s.cmd('resource show -n testsql23456 -g {} --resource-type Microsoft.Sql/databases --parent servers/testserver23456 '.format(rg), checks=[
            JMESPathCheck('name', 'testsql23456'),
            JMESPathCheck('location', 'West US'),
            JMESPathCheck('resourceGroup', rg)
        ])

        # clear tag and verify
        s.cmd('resource tag -n testserver23456 -g {} --resource-type Microsoft.Sql/servers --tags'.format(rg))
        s.cmd('resource show -n testserver23456 -g {} --resource-type Microsoft.Sql/servers'.format(rg),
            checks=JMESPathCheck('tags', {}))

class TagScenarioTest(VCRTestBase):

    def test_tag_scenario(self):
        self.execute()

    def __init__(self, test_method):
        self.tag_name = 'travistesttag'
        super(TagScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        tn = self.tag_name
        tags = self.cmd('tag list --query "[?tagName == \'{}\'].values[].tagValue" -o json'.format(tn))
        for tag in tags:
            self.cmd('tag remove-value -n {} --value {}'.format(tn, tag))
        self.cmd('tag delete -n {}'.format(tn))

    def body(self):
        s = self
        tn = s.tag_name

        s.cmd('tag list --query "[?tagName == \'{}\']"'.format(tn), checks=NoneCheck())
        s.cmd('tag create -n {}'.format(tn), checks=[
            JMESPathCheck('tagName', tn),
            JMESPathCheck('values', []),
            JMESPathCheck('count.value', '0')
        ])
        s.cmd('tag add-value -n {} --value test'.format(tn))
        s.cmd('tag add-value -n {} --value test2'.format(tn))
        s.cmd('tag list --query "[?tagName == \'{}\']"'.format(tn), checks=[
            JMESPathCheck('[].values[].tagValue', [u'test', u'test2'])
        ])
        s.cmd('tag remove-value -n {} --value test'.format(tn))
        s.cmd('tag list --query "[?tagName == \'{}\']"'.format(tn), checks=[
            JMESPathCheck('[].values[].tagValue', [u'test2'])
        ])
        s.cmd('tag remove-value -n {} --value test2'.format(tn))
        s.cmd('tag list --query "[?tagName == \'{}\']"'.format(tn), checks=[
            JMESPathCheck('[].values[].tagValue', [])
        ])
        s.cmd('tag delete -n {}'.format(tn))
        s.cmd('tag list --query "[?tagName == \'{}\']"'.format(self.tag_name), checks=NoneCheck())        
