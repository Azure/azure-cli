#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import os
import time
# AZURE CLI RESOURCE TEST DEFINITIONS
import six
from azure.cli.core.test_utils.vcr_test_base import (VCRTestBase, JMESPathCheck, NoneCheck,
                                                     BooleanCheck,
                                                     ResourceGroupVCRTestBase,
                                                     MOCKED_SUBSCRIPTION_ID)

#pylint: disable=method-hidden, line-too-long
class ResourceGroupScenarioTest(VCRTestBase): # Not RG test base because it tests the actual deletion of a resource group

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

class ResourceScenarioTest(ResourceGroupVCRTestBase):

    def test_resource_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(ResourceScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'azure-cli-resource-test'
        self.vnet_name = 'cli-test-vnet1'
        self.subnet_name = 'cli-test-subnet1'

    def set_up(self):
        super(ResourceScenarioTest, self).set_up()
        rg = self.resource_group
        self.cmd('network vnet create -g {} -n {} --subnet-name {} --tags cli-test=test'.format(rg, self.vnet_name, self.subnet_name))

    def body(self):
        s = self
        rg = self.resource_group
        s.cmd('resource list')
        s.cmd('resource list -l centralus',
              checks=JMESPathCheck("length([?location == 'centralus']) == length(@)", True))
        s.cmd('resource list --tag displayName=PublicIPAddress',
              checks=JMESPathCheck("length([?type == 'Microsoft.Network/publicIPAddresses']) == length(@)", True))
        s.cmd('resource list --resource-type Microsoft.Network/networkInterfaces',
              checks=JMESPathCheck("length([?type == 'Microsoft.Network/networkInterfaces']) == length(@)", True))

        s.cmd('resource list --name {}'.format(self.vnet_name),
              checks=JMESPathCheck("length([?name == '{}']) == length(@)".format(self.vnet_name), True))

        all_tagged_displayname = s.cmd('resource list --tag displayName')
        storage_acc_tagged_displayname = \
            s.cmd('resource list --tag displayName=StorageAccount')
        assert len(all_tagged_displayname) > len(storage_acc_tagged_displayname)

        # check for simple resource with tag
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'.format(self.vnet_name, rg), checks=[
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('tags', {'cli-test': 'test'})
        ])

        # clear tag and verify
        s.cmd('resource tag -n {} -g {} --resource-type Microsoft.Network/virtualNetworks --tags'.format(self.vnet_name, rg))
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'.format(self.vnet_name, rg),
              checks=JMESPathCheck('tags', {}))

class TagScenarioTest(VCRTestBase): # Not RG test base because it operates only on the subscription

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

class ProviderRegistrationTest(VCRTestBase): # Not RG test base because it operates only on the subscription
    def __init__(self, test_method):
        super(ProviderRegistrationTest, self).__init__(__file__, test_method)

    def test_provider_registration(self):
        self.execute()

    def body(self):
        provider = 'TrendMicro.DeepSecurity'
        result = self.cmd('provider show -n {}'.format(provider), checks=None)
        if result['registrationState'] == 'Unregistered':
            self.cmd('provider register -n {}'.format(provider), checks=None)
            self.cmd('provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Registered')])
            self.cmd('provider unregister -n {}'.format(provider), checks=None)
            self.cmd('provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Unregistered')])
        else:
            self.cmd('provider unregister -n {}'.format(provider), checks=None)
            self.cmd('provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Unregistered')])
            self.cmd('provider register -n {}'.format(provider), checks=None)
            self.cmd('provider show -n {}'.format(provider), checks=[JMESPathCheck('registrationState', 'Registered')])

class DeploymentTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentTest, self).__init__(__file__, test_method)
        self.resource_group = 'azure-cli-deployment-test'

    def test_group_deployment(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        #test mainline scenario that the template is uri based
        template_file_basepath = os.path.join(curr_dir, 'simple_deploy.json')
        template_file = six.moves.urllib_parse.urljoin('file:', six.moves.urllib.request.pathname2url(template_file_basepath))

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
        result = self.cmd('resource group deployment operation list -g {} -n {}'.format(self.resource_group, deployment_name), checks=None)
        self.assertEqual(2, len(result))
        self.assertEqual(self.resource_group, result[0]['resourceGroup'])

class ResourceMoveScenarioTest(VCRTestBase): # Not RG test base because it uses two RGs and manually cleans them up

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

class FeatureScenarioTest(VCRTestBase): # Not RG test base because it operates only on the subscription
    def __init__(self, test_method):
        super(FeatureScenarioTest, self).__init__(__file__, test_method)

    def test_feature_list(self):
        self.execute()

    def body(self):
        self.cmd('resource feature list', checks=[
            JMESPathCheck("length([?name=='Microsoft.Xrm/uxdevelopment'])", 1)
            ])

        self.cmd('resource feature list --namespace {}'.format('Microsoft.Network'), checks=[
            JMESPathCheck("length([?name=='Microsoft.Network/SkipPseudoVipGeneration'])", 1)
            ])

class PolicyScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(PolicyScenarioTest, self).__init__(__file__, test_method)
        self.resource_group = 'azure-cli-policy-test-group'

    def test_resource_policy(self):
        self.execute()

    def body(self):
        policy_name = 'azure-cli-test-policy'
        policy_display_name = 'test_policy_123'
        policy_description = 'test_policy_123'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        rules_file = os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\')
        #create a policy
        self.cmd('resource policy definition create -n {} --rules {} --display-name {} --description {}'.format(
            policy_name, rules_file, policy_display_name, policy_description), checks=[
                JMESPathCheck('name', policy_name),
                JMESPathCheck('displayName', policy_display_name),
                JMESPathCheck('description', policy_description)
                ])

        #update it
        new_policy_description = policy_description + '_new'
        self.cmd('resource policy definition update -n {} --description {}'.format(policy_name, new_policy_description), checks=[
            JMESPathCheck('description', new_policy_description)
            ])

        #list and show it
        self.cmd('resource policy definition list', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_name), 1)
            ])
        self.cmd('resource policy definition show -n {}'.format(policy_name), checks=[
            JMESPathCheck('name', policy_name),
            JMESPathCheck('displayName', policy_display_name)
            ])

        #create a policy assignment on a resource group
        policy_assignment_name = 'azurecli-test-policy-assignment'
        policy_assignment_display_name = 'test_assignment_123'
        self.cmd('resource policy assignment create --policy {} -n {} --display-name {} -g {}'.format(
            policy_name, policy_assignment_name, policy_assignment_display_name, self.resource_group), checks=[
                JMESPathCheck('name', policy_assignment_name),
                JMESPathCheck('displayName', policy_assignment_display_name),
                ])

        # listing at subscription level won't find the assignment made at a resource group
        import jmespath
        try:
            self.cmd('resource policy assignment list', checks=[
                JMESPathCheck("length([?name=='{}'])".format(policy_assignment_name), 0),
                ])
        except jmespath.exceptions.JMESPathTypeError: #ok if query fails on None result
            pass

        # but enable --show-all works
        self.cmd('resource policy assignment list --disable-scope-strict-match', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_assignment_name), 1),
            ])

        # delete the assignment
        self.cmd('resource policy assignment delete -n {} -g {}'.format(
            policy_assignment_name, self.resource_group))
        self.cmd('resource policy assignment list --disable-scope-strict-match')

        # delete the policy
        self.cmd('resource policy definition delete -n {}'.format(policy_name))
        time.sleep(10) # ensure the policy is gone when run live.
        self.cmd('resource policy definition list', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_name), 0)])
