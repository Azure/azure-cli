#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
# AZURE CLI RESOURCE TEST DEFINITIONS

from azure.cli.utils.vcr_test_base import (VCRTestBase, JMESPathCheck, NoneCheck, BooleanCheck,
                                           ResourceGroupVCRTestBase, MOCKED_SUBSCRIPTION_ID)

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
        all_resources = s.cmd('resource list')
        some_resources = s.cmd('resource list -l centralus')
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

        all_tagged_displayname = s.cmd('resource list --tag displayName')
        storage_acc_tagged_displayname = \
            s.cmd('resource list --tag displayName=StorageAccount')
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
        tags = self.cmd('tag list --query "[?tagName == \'{}\'].values[].tagValue"'.format(tn))
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

class ProviderRegistrationTest(VCRTestBase):
    def __init__(self, test_method):
        super(ProviderRegistrationTest, self).__init__(__file__, test_method)

    def test_provider_registration(self):
        self.execute()

    def body(self):
        provider = 'TrendMicro.DeepSecurity'
        result = self.cmd('resource provider show -n {}'.format(provider), checks=None)
        if result['registrationState'] == 'Unregistered':
            self.cmd('resource provider register -n {}'.format(provider), checks=None)
            self.cmd('resource provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Registered')])
            self.cmd('resource provider unregister -n {}'.format(provider), checks=None)
            self.cmd('resource provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Unregistered')])
        else:
            self.cmd('resource provider unregister -n {}'.format(provider), checks=None)
            self.cmd('resource provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Unregistered')])
            self.cmd('resource provider register -n {}'.format(provider), checks=None)
            self.cmd('resource provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Registered')])

class DeploymentTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentTest, self).__init__(__file__, test_method)
        self.resource_group = 'azure-cli-deployment-test'

    def test_group_deployment(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        deployment_name = 'azure-cli-deployment'
        result = self.cmd('resource group deployment validate -g {} --template-file-path {} --parameters-file-path {}'.format(
            self.resource_group, template_file, parameters_file), checks=None)
        self.assertEqual('Accepted', result['properties']['provisioningState'])
        result = self.cmd('resource group deployment create -g {} -n {} --template-file-path {} --parameters-file-path {}'.format(
            self.resource_group, deployment_name, template_file, parameters_file), checks=None)
        self.assertEqual('Succeeded', result['properties']['provisioningState'])
        self.assertEqual(self.resource_group, result['resourceGroup'])
        result = self.cmd('resource group deployment list -g {}'.format(self.resource_group), checks=None)
        self.assertEqual(deployment_name, result[0]['name'])
        self.assertEqual(self.resource_group, result[0]['resourceGroup'])
        result = self.cmd('resource group deployment show -g {} -n {}'.format(self.resource_group, deployment_name), checks=None)
        self.assertEqual(deployment_name, result['name'])
        self.assertEqual(self.resource_group, result['resourceGroup'])
        result = self.cmd('resource group deployment exists -g {} -n {}'.format(self.resource_group, deployment_name), checks=None)
        self.assertTrue(result)
        result = self.cmd('resource group deployment operation list -g {} -n {}'.format(self.resource_group, deployment_name), checks=None)
        self.assertEqual(2, len(result))
        self.assertEqual(self.resource_group, result[0]['resourceGroup'])

class ResourceMoveScenarioTest(VCRTestBase):

    def __init__(self, test_method):
        super(ResourceMoveScenarioTest, self).__init__(__file__, test_method)    
        self.source_group = 'res_move_src_group'
        self.destination_group = 'res_move_dest_group'
       
    def test_resource_move(self):
        self.execute()

    def set_up(self):
        self.cmd('resource group create --location westus --name {}'.format(self.source_group))
        self.cmd('resource group create --location westus --name {}'.format(self.destination_group))

    def tear_down(self):
        self.cmd('resource group delete --name {}'.format(self.source_group))
        self.cmd('resource group delete --name {}'.format(self.destination_group))

    def body(self):
        if self.playback:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        else:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv')

        #use 'network security group' for testing as it is fast to create
        nsg1 = 'nsg1'
        nsg1_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/networkSecurityGroups/{}'.format(
            subscription_id, self.source_group, nsg1)
        nsg2 = 'nsg2'
        nsg2_id = nsg1_id.replace(nsg1, nsg2)

        self.cmd('network nsg create -g {} --name {}'.format(self.source_group, nsg1))
        self.cmd('network nsg create -g {} --name {}'.format(self.source_group, nsg2))

        #move
        self.cmd('resource move --ids {} {} --destination-group {}'.format(nsg1_id, nsg2_id, self.destination_group))

        #see they show up at destination
        self.cmd('network nsg show -g {} -n {}'.format(self.destination_group, nsg1), [JMESPathCheck('name', nsg1)])
        self.cmd('network nsg show -g {} -n {}'.format(self.destination_group, nsg2), [JMESPathCheck('name', nsg2)])
