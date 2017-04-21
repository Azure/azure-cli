# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
import unittest
# AZURE CLI RESOURCE TEST DEFINITIONS
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
        if self.cmd('group exists -n {}'.format(self.resource_group)):
            self.cmd('group delete -n {} --yes'.format(self.resource_group))

    def body(self):
        s = self
        rg = self.resource_group
        s.cmd('group create -n {} -l westus --tag a=b c'.format(rg), checks=[
            JMESPathCheck('name', rg),
            JMESPathCheck('tags', {'a':'b', 'c':''})
        ])
        s.cmd('group exists -n {}'.format(rg), checks=BooleanCheck(True))
        s.cmd('group show -n {}'.format(rg), checks=[
            JMESPathCheck('name', rg),
            JMESPathCheck('tags', {'a':'b', 'c':''})
        ])
        s.cmd('group list --tag a=b', checks=[
            JMESPathCheck('[0].name', rg),
            JMESPathCheck('[0].tags', {'a':'b', 'c':''})
        ])
        s.cmd('group delete -n {} --yes'.format(rg))
        s.cmd('group exists -n {}'.format(rg), checks=NoneCheck())

    def tear_down(self):
        if self.cmd('group exists -n {}'.format(self.resource_group)):
            self.cmd('group delete -n {} --yes'.format(self.resource_group))

class ResourceGroupNoWaitScenarioTest(VCRTestBase): # Not RG test base because it tests the actual deletion of a resource group

    def test_resource_group_no_wait(self):
        self.execute()

    def __init__(self, test_method):
        self.resource_group = 'cli_rg_nowait_test'
        super(ResourceGroupNoWaitScenarioTest, self).__init__(__file__, test_method)

    def set_up(self):
        if self.cmd('group exists -n {}'.format(self.resource_group)):
            self.cmd('group delete -n {} --yes'.format(self.resource_group))

    def body(self):
        s = self
        rg = self.resource_group
        s.cmd('group create -n {} -l westus'.format(rg), checks=[
            JMESPathCheck('name', rg),
        ])
        s.cmd('group exists -n {}'.format(rg), checks=BooleanCheck(True))
        s.cmd('group wait --exists -n {}'.format(rg), checks=NoneCheck())
        s.cmd('group delete -n {} --no-wait --yes'.format(rg), checks=NoneCheck())
        s.cmd('group wait --deleted -n {}'.format(rg), checks=NoneCheck())
        s.cmd('group exists -n {}'.format(rg), checks=NoneCheck())

class ResourceScenarioTest(ResourceGroupVCRTestBase):

    def test_resource_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(ResourceScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_resource_scenario')
        self.vnet_name = 'cli-test-vnet1'
        self.subnet_name = 'cli-test-subnet1'

    def set_up(self):
        super(ResourceScenarioTest, self).set_up()

    def body(self):
        s = self
        rg = self.resource_group
        vnet_count = s.cmd("resource list --query \"length([?name=='{}'])\"".format(self.vnet_name)) or 0
        self.cmd('network vnet create -g {} -n {} --subnet-name {} --tags cli-test=test'.format(self.resource_group, self.vnet_name, self.subnet_name))
        vnet_count += 1

        s.cmd('resource list',
              checks=JMESPathCheck("length([?name=='{}'])".format(self.vnet_name), vnet_count))
        s.cmd('resource list -l centralus',
              checks=JMESPathCheck("length([?location == 'centralus']) == length(@)", True))
        s.cmd('resource list --resource-type Microsoft.Network/virtualNetworks',
              checks=JMESPathCheck("length([?name=='{}'])".format(self.vnet_name), vnet_count))
        s.cmd('resource list --name {}'.format(self.vnet_name),
              checks=JMESPathCheck("length([?name=='{}'])".format(self.vnet_name), vnet_count))
        s.cmd('resource list --tag cli-test',
              checks=JMESPathCheck("length([?name=='{}'])".format(self.vnet_name), vnet_count))
        s.cmd('resource list --tag cli-test=test',
              checks=JMESPathCheck("length([?name=='{}'])".format(self.vnet_name), vnet_count))

        # check for simple resource with tag
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'.format(self.vnet_name, rg), checks=[
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('tags', {'cli-test': 'test'})
        ])
        #check for child resource
        s.cmd('resource show -n {} -g {} --namespace Microsoft.Network --parent virtualNetworks/{} --resource-type subnets'.format(
            self.subnet_name, self.resource_group, self.vnet_name), checks=[
                JMESPathCheck('name', self.subnet_name),
                JMESPathCheck('resourceGroup', rg),
            ])

        # clear tag and verify
        s.cmd('resource tag -n {} -g {} --resource-type Microsoft.Network/virtualNetworks --tags'.format(self.vnet_name, rg))
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'.format(self.vnet_name, rg),
              checks=JMESPathCheck('tags', {}))

class ResourceIDScenarioTest(ResourceGroupVCRTestBase):

    def test_resource_id_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(ResourceIDScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_resource_id')
        self.vnet_name = 'cli_test_resource_id_vnet'
        self.subnet_name = 'cli_test_resource_id_subnet'

    def set_up(self):
        super(ResourceIDScenarioTest, self).set_up()
        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(self.resource_group, self.vnet_name, self.subnet_name))

    def body(self):
        if self.playback:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        else:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv')

        s = self
        vnet_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}'.format(
            subscription_id, self.resource_group, self.vnet_name)
        s.cmd('resource tag --id {} --tags {}'.format(vnet_resource_id, 'tag-vnet'))
        s.cmd('resource show --id {}'.format(vnet_resource_id), checks=[
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('tags', {'tag-vnet': ''})
        ])

        subnet_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks/{}/subnets/{}'.format(
            subscription_id, self.resource_group, self.vnet_name, self.subnet_name)
        s.cmd('resource show --id {}'.format(subnet_resource_id), checks=[
            JMESPathCheck('name', self.subnet_name),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('properties.addressPrefix', '10.0.0.0/24')
        ])

        s.cmd('resource update --id {} --set properties.addressPrefix=10.0.0.0/22'.format(subnet_resource_id), checks=[
            JMESPathCheck('properties.addressPrefix', '10.0.0.0/22')
            ])

        s.cmd('resource delete --id {}'.format(subnet_resource_id), checks=NoneCheck())
        s.cmd('resource delete --id {}'.format(vnet_resource_id), checks=NoneCheck())


class ResourceCreateScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(ResourceCreateScenarioTest, self).__init__(__file__, test_method, resource_group='cli_test_resource_create')

    def test_resource_create(self):
        self.execute()

    def body(self):
        appservice_plan = 'cli_res_create_plan'
        webapp = 'clirescreateweb'

        self.cmd('resource create -g {} -n {} --resource-type Microsoft.web/serverFarms --is-full-object --properties "{{\\"location\\":\\"{}\\",\\"sku\\":{{\\"name\\":\\"B1\\",\\"tier\\":\\"BASIC\\"}}}}"'.format(
            self.resource_group, appservice_plan, self.location), checks=[JMESPathCheck('name', appservice_plan)])

        result = self.cmd('resource create -g {} -n {} --resource-type Microsoft.web/sites --properties "{{\\"serverFarmId\\":\\"{}\\"}}"'.format(
            self.resource_group, webapp, appservice_plan), checks=[JMESPathCheck('name', webapp)])

        app_settings_id = result['id'] + '/config/appsettings'
        self.cmd('resource create --id {} --properties "{{\\"key2\\":\\"value12\\"}}"'.format(
            app_settings_id), checks=[JMESPathCheck('properties.key2', 'value12')])


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
            JMESPathCheck('count.value', 0)
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
            result = self.cmd('provider show -n {}'.format(provider))
            self.assertTrue(result['registrationState'] in ['Registering', 'Registered'])
            self.cmd('provider unregister -n {}'.format(provider), checks=None)
            result = self.cmd('provider show -n {}'.format(provider))
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
        else:
            self.cmd('provider unregister -n {}'.format(provider), checks=None)
            result = self.cmd('provider show -n {}'.format(provider))
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
            self.cmd('provider register -n {}'.format(provider), checks=None)
            result = self.cmd('provider show -n {}'.format(provider))
            self.assertTrue(result['registrationState'] in ['Registering', 'Registered'])


class ProviderOperationTest(VCRTestBase): # Not RG test base because it operates only on the subscription
    def __init__(self, test_method):
        super(ProviderOperationTest, self).__init__(__file__, test_method)

    def test_provider_operation(self):
        self.execute()

    def body(self):
        self.cmd('provider operation show --namespace microsoft.compute', checks=[
            JMESPathCheck('id', '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
            JMESPathCheck('type', 'Microsoft.Authorization/providerOperations')
        ]) 
        self.cmd('provider operation show --namespace microsoft.compute --api-version 2015-07-01', checks=[
            JMESPathCheck('id', '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
            JMESPathCheck('type', 'Microsoft.Authorization/providerOperations')
        ])


class DeploymentTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentTest, self).__init__(__file__, test_method, resource_group='azure-cli-deployment-test')

    def test_group_deployment(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        deployment_name = 'azure-cli-deployment'

        self.cmd('group deployment validate -g {} --template-file {} --parameters @{}'.format(
            self.resource_group, template_file, parameters_file), checks=[
                JMESPathCheck('properties.provisioningState', 'Accepted')
                ])
        self.cmd('group deployment create -g {} -n {} --template-file {} --parameters @{}'.format(
            self.resource_group, deployment_name, template_file, parameters_file), checks=[
                JMESPathCheck('properties.provisioningState', 'Succeeded'),
                JMESPathCheck('resourceGroup', self.resource_group),
                ])
        self.cmd('group deployment list -g {}'.format(self.resource_group), checks=[
            JMESPathCheck('[0].name', deployment_name),
            JMESPathCheck('[0].resourceGroup', self.resource_group)
            ])
        self.cmd('group deployment show -g {} -n {}'.format(self.resource_group, deployment_name), checks=[
            JMESPathCheck('name', deployment_name),
            JMESPathCheck('resourceGroup', self.resource_group)
            ])
        self.cmd('group deployment operation list -g {} -n {}'.format(self.resource_group, deployment_name), checks=[
            JMESPathCheck('length([])', 2),
            JMESPathCheck('[0].resourceGroup', self.resource_group)
            ])

class DeploymentnoWaitTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentnoWaitTest, self).__init__(__file__, test_method, resource_group='azure-cli-deployment-test')

    def test_group_deployment_no_wait(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        deployment_name = 'azure-cli-deployment'

        self.cmd('group deployment create -g {} -n {} --template-file {} --parameters @{} --no-wait'.format(
            self.resource_group, deployment_name, template_file, parameters_file), checks=NoneCheck())

        self.cmd('group deployment wait -g {} -n {} --created'.format(self.resource_group, deployment_name), checks=NoneCheck())

        self.cmd('group deployment show -g {} -n {}'.format(self.resource_group, deployment_name), checks=[
            JMESPathCheck('properties.provisioningState', 'Succeeded')
            ])

class DeploymentThruUriTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentThruUriTest, self).__init__(__file__, test_method, resource_group='azure-cli-deployment-uri-test')

    def test_group_deployment_thru_uri(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        #same copy of the sample template file under current folder, but it is uri based now
        template_uri = 'https://raw.githubusercontent.com/Azure/azure-cli/master/src/command_modules/azure-cli-resource/azure/cli/command_modules/resource/tests/simple_deploy.json'
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        deployment_name = 'simple_deploy' #auto-gen'd by command
        result = self.cmd('group deployment create -g {} --template-uri {} --parameters @{}'.format(
            self.resource_group, template_uri, parameters_file), checks=[
                JMESPathCheck('properties.provisioningState', 'Succeeded'),
                JMESPathCheck('resourceGroup', self.resource_group),
                ])

        result = self.cmd('group deployment show -g {} -n {}'.format(self.resource_group, deployment_name), checks=[
            JMESPathCheck('name', deployment_name)
            ])

        self.cmd('group deployment delete -g {} -n {}'.format(self.resource_group, deployment_name))
        result = self.cmd('group deployment list -g {}'.format(self.resource_group))
        self.assertFalse(bool(result))

class ResourceMoveScenarioTest(VCRTestBase): # Not RG test base because it uses two RGs and manually cleans them up

    def __init__(self, test_method):
        super(ResourceMoveScenarioTest, self).__init__(__file__, test_method)
        self.source_group = 'res_move_src_group'
        self.destination_group = 'res_move_dest_group'

    def test_resource_move(self):
        self.execute()

    def set_up(self):
        self.cmd('group create --location westus --name {}'.format(self.source_group))
        self.cmd('group create --location westus --name {}'.format(self.destination_group))

    def tear_down(self):
        self.cmd('group delete --name {} --yes'.format(self.source_group))
        self.cmd('group delete --name {} --yes'.format(self.destination_group))

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
        self.cmd('feature list', checks=[
            JMESPathCheck("length([?name=='Microsoft.Xrm/uxdevelopment'])", 1)
            ])

        self.cmd('feature list --namespace {}'.format('Microsoft.Network'), checks=[
            JMESPathCheck("length([?name=='Microsoft.Network/SkipPseudoVipGeneration'])", 1)
            ])

class PolicyScenarioTest(ResourceGroupVCRTestBase):

    def __init__(self, test_method):
        super(PolicyScenarioTest, self).__init__(__file__, test_method, resource_group='azure-cli-policy-test-group')

    def test_resource_policy(self):
        self.execute()

    def body(self):
        policy_name = 'azure-cli-test-policy'
        policy_display_name = 'test_policy_123'
        policy_description = 'test_policy_123'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        rules_file = os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\')
        #create a policy
        self.cmd('policy definition create -n {} --rules {} --display-name {} --description {}'.format(
            policy_name, rules_file, policy_display_name, policy_description), checks=[
                JMESPathCheck('name', policy_name),
                JMESPathCheck('displayName', policy_display_name),
                JMESPathCheck('description', policy_description)
                ])

        #update it
        new_policy_description = policy_description + '_new'
        self.cmd('policy definition update -n {} --description {}'.format(policy_name, new_policy_description), checks=[
            JMESPathCheck('description', new_policy_description)
            ])

        #list and show it
        self.cmd('policy definition list', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_name), 1)
            ])
        self.cmd('policy definition show -n {}'.format(policy_name), checks=[
            JMESPathCheck('name', policy_name),
            JMESPathCheck('displayName', policy_display_name)
            ])

        #create a policy assignment on a resource group
        policy_assignment_name = 'azurecli-test-policy-assignment'
        policy_assignment_display_name = 'test_assignment_123'
        self.cmd('policy assignment create --policy {} -n {} --display-name {} -g {}'.format(
            policy_name, policy_assignment_name, policy_assignment_display_name, self.resource_group), checks=[
                JMESPathCheck('name', policy_assignment_name),
                JMESPathCheck('displayName', policy_assignment_display_name),
                ])

        # listing at subscription level won't find the assignment made at a resource group
        import jmespath
        try:
            self.cmd('policy assignment list', checks=[
                JMESPathCheck("length([?name=='{}'])".format(policy_assignment_name), 0),
                ])
        except jmespath.exceptions.JMESPathTypeError: #ok if query fails on None result
            pass

        # but enable --show-all works
        self.cmd('policy assignment list --disable-scope-strict-match', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_assignment_name), 1),
            ])

        # delete the assignment
        self.cmd('policy assignment delete -n {} -g {}'.format(
            policy_assignment_name, self.resource_group))
        self.cmd('policy assignment list --disable-scope-strict-match')

        # delete the policy
        self.cmd('policy definition delete -n {}'.format(policy_name))
        time.sleep(10) # ensure the policy is gone when run live.
        self.cmd('policy definition list', checks=[
            JMESPathCheck("length([?name=='{}'])".format(policy_name), 0)])

if __name__ == '__main__':
    unittest.main()
