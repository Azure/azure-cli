# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import unittest

from azure.cli.testsdk import (ScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               JMESPathCheck as JCheck, create_random_name)
from azure.cli.core.util import get_file_json
# AZURE CLI RESOURCE TEST DEFINITIONS
from azure.cli.testsdk.vcr_test_base import (VCRTestBase, JMESPathCheck, NoneCheck,
                                             BooleanCheck,
                                             ResourceGroupVCRTestBase,
                                             MOCKED_SUBSCRIPTION_ID)


class ResourceGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group(self, resource_group):
        s = self
        rg = resource_group
        s.cmd('group delete -n {} --yes'.format(rg))
        s.cmd('group exists -n {}'.format(rg), checks=NoneCheck())

        s.cmd('group create -n {} -l westus --tag a=b c'.format(rg), checks=[
            JCheck('name', rg),
            JCheck('tags', {'a': 'b', 'c': ''})
        ])
        s.cmd('group exists -n {}'.format(rg), checks=BooleanCheck(True))
        s.cmd('group show -n {}'.format(rg), checks=[
            JCheck('name', rg),
            JCheck('tags', {'a': 'b', 'c': ''})
        ])
        s.cmd('group list --tag a=b', checks=[
            JCheck('[0].name', rg),
            JCheck('[0].tags', {'a': 'b', 'c': ''})
        ])


class ResourceGroupNoWaitScenarioTest(VCRTestBase):
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
        super(ResourceScenarioTest, self).__init__(__file__, test_method,
                                                   resource_group='cli_test_resource_scenario')
        self.vnet_name = 'cli-test-vnet1'
        self.subnet_name = 'cli-test-subnet1'

    def set_up(self):
        super(ResourceScenarioTest, self).set_up()

    def body(self):
        s = self
        rg = self.resource_group
        vnet_count = s.cmd(
            "resource list --query \"length([?name=='{}'])\"".format(self.vnet_name)) or 0
        self.cmd('network vnet create -g {} -n {} --subnet-name {} --tags cli-test=test'.format(
            self.resource_group, self.vnet_name, self.subnet_name))
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
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'.format(
            self.vnet_name, rg), checks=[
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('location', 'westus'),
            JMESPathCheck('resourceGroup', rg),
            JMESPathCheck('tags', {'cli-test': 'test'})
        ])
        # check for child resource
        s.cmd(
            'resource show -n {} -g {} --namespace Microsoft.Network --parent virtualNetworks/{}'
            ' --resource-type subnets'.format(
                self.subnet_name, self.resource_group, self.vnet_name), checks=[
                JMESPathCheck('name', self.subnet_name),
                JMESPathCheck('resourceGroup', rg),
            ])

        # clear tag and verify
        s.cmd('resource tag -n {} -g {} --resource-type Microsoft.Network/virtualNetworks --tags'
              .format(self.vnet_name, rg))
        s.cmd('resource show -n {} -g {} --resource-type Microsoft.Network/virtualNetworks'
              .format(self.vnet_name, rg), checks=JMESPathCheck('tags', {}))


class ResourceIDScenarioTest(ResourceGroupVCRTestBase):
    def test_resource_id_scenario(self):
        self.execute()

    def __init__(self, test_method):
        super(ResourceIDScenarioTest, self).__init__(__file__, test_method,
                                                     resource_group='cli_test_resource_id')
        self.vnet_name = 'cli_test_resource_id_vnet'
        self.subnet_name = 'cli_test_resource_id_subnet'

    def set_up(self):
        super(ResourceIDScenarioTest, self).set_up()
        self.cmd('network vnet create -g {} -n {} --subnet-name {}'.format(self.resource_group,
                                                                           self.vnet_name,
                                                                           self.subnet_name))

    def body(self):
        if self.playback:
            subscription_id = MOCKED_SUBSCRIPTION_ID
        else:
            subscription_id = self.cmd('account list --query "[?isDefault].id" -o tsv')

        s = self
        vnet_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/' \
                           'virtualNetworks/{}'.format(subscription_id,
                                                       self.resource_group,
                                                       self.vnet_name)
        s.cmd('resource tag --id {} --tags {}'.format(vnet_resource_id, 'tag-vnet'))
        s.cmd('resource show --id {}'.format(vnet_resource_id), checks=[
            JMESPathCheck('name', self.vnet_name),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('tags', {'tag-vnet': ''})
        ])

        subnet_resource_id = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/' \
                             'virtualNetworks/{}/subnets/{}'.format(subscription_id,
                                                                    self.resource_group,
                                                                    self.vnet_name,
                                                                    self.subnet_name)
        s.cmd('resource show --id {}'.format(subnet_resource_id), checks=[
            JMESPathCheck('name', self.subnet_name),
            JMESPathCheck('resourceGroup', self.resource_group),
            JMESPathCheck('properties.addressPrefix', '10.0.0.0/24')
        ])

        s.cmd('resource update --id {} --set properties.addressPrefix=10.0.0.0/22'.format(
            subnet_resource_id), checks=[
            JMESPathCheck('properties.addressPrefix', '10.0.0.0/22')
        ])

        s.cmd('resource delete --id {}'.format(subnet_resource_id), checks=NoneCheck())
        s.cmd('resource delete --id {}'.format(vnet_resource_id), checks=NoneCheck())


class ResourceCreateScenarioTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(ResourceCreateScenarioTest, self).__init__(__file__, test_method,
                                                         resource_group='cli_test_resource_create')

    def test_resource_create(self):
        self.execute()

    def body(self):
        appservice_plan = 'cli_res_create_plan'
        webapp = 'clirescreateweb'

        self.cmd('resource create -g {} -n {} --resource-type Microsoft.web/serverFarms '
                 '--is-full-object --properties "{{\\"location\\":\\"{}\\",\\"sku\\":{{\\"name\\":'
                 '\\"B1\\",\\"tier\\":\\"BASIC\\"}}}}"'.format(self.resource_group,
                                                               appservice_plan,
                                                               self.location),
                 checks=[JMESPathCheck('name', appservice_plan)])

        result = self.cmd(
            'resource create -g {} -n {} --resource-type Microsoft.web/sites --properties '
            '"{{\\"serverFarmId\\":\\"{}\\"}}"'.format(self.resource_group,
                                                       webapp,
                                                       appservice_plan),
            checks=[JMESPathCheck('name', webapp)])

        app_settings_id = result['id'] + '/config/appsettings'
        self.cmd('resource create --id {} --properties "{{\\"key2\\":\\"value12\\"}}"'.format(
            app_settings_id), checks=[JMESPathCheck('properties.key2', 'value12')])


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


class ProviderRegistrationTest(VCRTestBase):
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


class ProviderOperationTest(VCRTestBase):
    def __init__(self, test_method):
        super(ProviderOperationTest, self).__init__(__file__, test_method)

    def test_provider_operation(self):
        self.execute()

    def body(self):
        self.cmd('provider operation show --namespace microsoft.compute', checks=[
            JMESPathCheck('id',
                          '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
            JMESPathCheck('type', 'Microsoft.Authorization/providerOperations')
        ])
        self.cmd('provider operation show --namespace microsoft.compute --api-version 2015-07-01',
                 checks=[
                     JMESPathCheck(
                         'id',
                         '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
                     JMESPathCheck('type', 'Microsoft.Authorization/providerOperations')
                 ])


class DeploymentTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_lite')
    def test_group_deployment_lite(self, resource_group):
        # ensures that a template that is missing "parameters" or "resources" still deploys
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\')
        deployment_name = self.create_random_name('azure-cli-deployment', 30)

        self.cmd('group deployment create -g {} -n {} --template-file {}'.format(
            resource_group, deployment_name, template_file), checks=[
            JCheck('properties.provisioningState', 'Succeeded'),
            JCheck('resourceGroup', resource_group),
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment')
    def test_group_deployment(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\')
        object_file = os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\')
        deployment_name = 'azure-cli-deployment'

        subnet_id = self.cmd('network vnet create -g {} -n vnet1 --subnet-name subnet1'.format(resource_group)).get_output_in_json()['newVNet']['subnets'][0]['id']

        self.cmd('group deployment validate -g {} --template-file {} --parameters @"{}" --parameters subnetId="{}" --parameters backendAddressPools=@"{}"'.format(
            resource_group, template_file, parameters_file, subnet_id, object_file), checks=[
            JCheck('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {} -n {} --template-file {} --parameters @"{}" --parameters subnetId="{}" --parameters backendAddressPools=@"{}"'.format(
            resource_group, deployment_name, template_file, parameters_file, subnet_id, object_file), checks=[
            JCheck('properties.provisioningState', 'Succeeded'),
            JCheck('resourceGroup', resource_group),
        ])
        self.cmd('network lb show -g {} -n test-lb'.format(resource_group), checks=[
            JCheck('tags', {'key': 'super=value'})
        ])

        self.cmd('group deployment list -g {}'.format(resource_group), checks=[
            JCheck('[0].name', deployment_name),
            JCheck('[0].resourceGroup', resource_group)
        ])
        self.cmd('group deployment show -g {} -n {}'.format(resource_group, deployment_name), checks=[
            JCheck('name', deployment_name),
            JCheck('resourceGroup', resource_group)
        ])
        self.cmd('group deployment operation list -g {} -n {}'.format(resource_group, deployment_name), checks=[
            JCheck('length([])', 2),
            JCheck('[0].resourceGroup', resource_group)
        ])


class DeploymentLiveTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_group_deployment_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\')
        object_file = os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\')
        deployment_name = 'azure-cli-deployment2'

        subnet_id = self.cmd('network vnet create -g {} -n vnet1 --subnet-name subnet1'.format(resource_group)).get_output_in_json()['newVNet']['subnets'][0]['id']

        with force_progress_logging() as test_io:
            self.cmd('group deployment create --verbose -g {} -n {} --template-file {} --parameters @"{}" --parameters subnetId="{}" --parameters backendAddressPools=@"{}"'.format(
                resource_group, deployment_name, template_file, parameters_file, subnet_id, object_file))

        # very the progress
        lines = test_io.getvalue().splitlines()
        for l in lines:
            self.assertTrue(l.split(':')[0] in ['Accepted', 'Succeeded'])
        self.assertTrue('Succeeded: {} (Microsoft.Resources/deployments)'.format(deployment_name), lines)


class DeploymentnoWaitTest(ResourceGroupVCRTestBase):
    def __init__(self, test_method):
        super(DeploymentnoWaitTest, self).__init__(__file__, test_method,
                                                   resource_group='azure-cli-deployment-test')

    def test_group_deployment_no_wait(self):
        self.execute()

    def body(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\')
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\',
                                                                                          '\\\\')
        deployment_name = 'azure-cli-deployment'

        self.cmd('group deployment create -g {} -n {} --template-file {} --parameters @{} '
                 '--no-wait'.format(self.resource_group,
                                    deployment_name,
                                    template_file,
                                    parameters_file),
                 checks=NoneCheck())

        self.cmd('group deployment wait -g {} -n {} --created'.format(self.resource_group,
                                                                      deployment_name),
                 checks=NoneCheck())

        self.cmd('group deployment show -g {} -n {}'.format(self.resource_group, deployment_name),
                 checks=[
                     JMESPathCheck('properties.provisioningState', 'Succeeded')
                 ])


class DeploymentThruUriTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_uri')
    def test_group_deployment_thru_uri(self, resource_group):
        self.resource_group = resource_group
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        # same copy of the sample template file under current folder, but it is uri based now
        template_uri = 'https://raw.githubusercontent.com/Azure/azure-cli/master/src/' \
                       'command_modules/azure-cli-resource/azure/cli/command_modules/resource/tests/simple_deploy.json'
        parameters_file = os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\',
                                                                                          '\\\\')
        result = self.cmd('group deployment create -g {} --template-uri {} --parameters @{}'.format(
            self.resource_group, template_uri, parameters_file), checks=[
            JCheck('properties.provisioningState', 'Succeeded'),
            JCheck('resourceGroup', self.resource_group),
        ]).get_output_in_json()

        deployment_name = result['name']
        result = self.cmd(
            'group deployment show -g {} -n {}'.format(self.resource_group, deployment_name), checks=JCheck('name', deployment_name))

        self.cmd('group deployment delete -g {} -n {}'.format(self.resource_group, deployment_name))
        self.cmd('group deployment list -g {}'.format(self.resource_group), checks=NoneCheck())


class ResourceMoveScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_resource_move_dest', parameter_name='resource_group_dest')
    @ResourceGroupPreparer(name_prefix='cli_test_resource_move_source')
    def test_resource_move(self, resource_group, resource_group_dest):
        nsg1_name = self.create_random_name('nsg-move', 20)
        nsg2_name = self.create_random_name('nsg-move', 20)

        nsg1 = self.cmd('network nsg create -n {} -g {}'.format(nsg1_name, resource_group)).get_output_in_json()
        nsg2 = self.cmd('network nsg create -n {} -g {}'.format(nsg2_name, resource_group)).get_output_in_json()

        nsg1_id = nsg1['NewNSG']['id']
        nsg2_id = nsg2['NewNSG']['id']

        self.cmd('resource move --ids {} {} --destination-group {}'.format(nsg1_id, nsg2_id, resource_group_dest))

        self.cmd('network nsg show -g {} -n {}'.format(resource_group_dest, nsg1_name), checks=[
            JCheck('name', nsg1_name)])
        self.cmd('network nsg show -g {} -n {}'.format(resource_group_dest, nsg2_name), checks=[
            JCheck('name', nsg2_name)])


class FeatureScenarioTest(VCRTestBase):
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


class PolicyScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_policy')
    def test_resource_policy(self, resource_group):
        policy_name = self.create_random_name('azure-cli-test-policy', 30)
        policy_display_name = self.create_random_name('test_policy', 20)
        policy_description = 'desc_for_test_policy_123'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        rules_file = os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\')
        params_def_file = os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\')
        params_file = os.path.join(curr_dir, 'sample_policy_param.json').replace('\\', '\\\\')
        mode = 'Indexed'

        # create a policy
        self.cmd('policy definition create -n {} --rules {} --params {} --display-name {} --description {} --mode {}'.format(
            policy_name, rules_file, params_def_file, policy_display_name, policy_description, mode),
            checks=[
                        JCheck('name', policy_name),
                        JCheck('displayName', policy_display_name),
                        JCheck('description', policy_description),
                        JCheck('mode', mode)
                   ]
        )

        # update it
        new_policy_description = policy_description + '_new'
        self.cmd('policy definition update -n {} --description {}'.format(policy_name, new_policy_description),
                 checks=JCheck('description', new_policy_description))

        # list and show it
        self.cmd('policy definition list', checks=JMESPathCheck("length([?name=='{}'])".format(policy_name), 1))
        self.cmd('policy definition show -n {}'.format(policy_name), checks=[
            JCheck('name', policy_name),
            JCheck('displayName', policy_display_name)
        ])

        # create a policy assignment on a resource group
        policy_assignment_name = self.create_random_name('azurecli-test-policy-assignment', 40)
        policy_assignment_display_name = self.create_random_name('test_assignment', 20)
        self.cmd('policy assignment create --policy {} -n {} --display-name {} -g {} --params {}'.format(
                 policy_name, policy_assignment_name, policy_assignment_display_name, resource_group, params_file),
                 checks=[
                    JCheck('name', policy_assignment_name),
                    JCheck('displayName', policy_assignment_display_name),
                    JCheck('sku.name', 'A0'),
                    JCheck('sku.tier', 'Free'),
                 ])

        # create a policy assignment with not scopes and standard sku
        get_cmd = 'group show -n {}'
        rg = self.cmd(get_cmd.format(resource_group)).get_output_in_json()
        vnet_name = self.create_random_name('azurecli-test-policy-vnet', 40)
        subnet_name = self.create_random_name('azurecli-test-policy-subnet', 40)
        vnetcreatecmd = 'network vnet create -g {} -n {} --subnet-name {}'
        self.cmd(vnetcreatecmd.format(resource_group, vnet_name, subnet_name))
        notscope = '/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/virtualNetworks'.format(rg['id'].split("/")[2], resource_group)
        self.cmd('policy assignment create --policy {} -n {} --display-name {} -g {} --not-scopes {} --params {} --sku {}'.format(
                 policy_name, policy_assignment_name, policy_assignment_display_name, resource_group, notscope, params_file, 'standard'),
                 checks=[
                    JCheck('name', policy_assignment_name),
                    JCheck('displayName', policy_assignment_display_name),
                    JCheck('sku.name', 'A1'),
                    JCheck('sku.tier', 'Standard'),
                    JCheck('notScopes[0]', notscope)
                 ])

        # listing at subscription level won't find the assignment made at a resource group
        import jmespath
        try:
            self.cmd('policy assignment list', checks=JCheck("length([?name=='{}'])".format(policy_assignment_name), 0))
        except jmespath.exceptions.JMESPathTypeError:  # ok if query fails on None result
            pass

        # but enable --show-all works
        self.cmd('policy assignment list --disable-scope-strict-match',
                 checks=JCheck("length([?name=='{}'])".format(policy_assignment_name), 1))

        # delete the assignment
        self.cmd('policy assignment delete -n {} -g {}'.format(policy_assignment_name, resource_group))
        self.cmd('policy assignment list --disable-scope-strict-match')

        # delete the policy
        self.cmd('policy definition delete -n {}'.format(policy_name))
        time.sleep(10)  # ensure the policy is gone when run live.
        self.cmd('policy definition list', checks=JCheck("length([?name=='{}'])".format(policy_name), 0))

    @ResourceGroupPreparer(name_prefix='cli_test_policy')
    def test_resource_policyset(self, resource_group):
        policy_name = self.create_random_name('azure-cli-test-policy', 30)
        policy_display_name = self.create_random_name('test_policy', 20)
        policy_description = 'desc_for_test_policy_123'
        policyset_name = self.create_random_name('azure-cli-test-policyset', 30)
        policyset_display_name = self.create_random_name('test_policyset', 20)
        policyset_description = 'desc_for_test_policyset_123'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        rules_file = os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\')
        policyset_file = os.path.join(curr_dir, 'sample_policy_set.json').replace('\\', '\\\\')
        params_def_file = os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\')

        # create a policy
        policycreatecmd = 'policy definition create -n {} --rules {} --params {} --display-name {} --description {}'
        policy = self.cmd(policycreatecmd.format(policy_name, rules_file, params_def_file, policy_display_name,
                                                 policy_description)).get_output_in_json()

        # create a policy set
        policyset = get_file_json(policyset_file)
        policyset[0]['policyDefinitionId'] = policy['id']
        with open(os.path.join(curr_dir, 'sample_policy_set.json'), 'w') as outfile:
            json.dump(policyset, outfile)
        self.cmd('policy set-definition create -n {} --definitions @"{}" --display-name {} --description {}'.format(
                 policyset_name, policyset_file, policyset_display_name, policyset_description),
                 checks=[
                    JCheck('name', policyset_name),
                    JCheck('displayName', policyset_display_name),
                    JCheck('description', policyset_description)
                ])

        # update it
        new_policyset_description = policy_description + '_new'
        self.cmd('policy set-definition update -n {} --description {}'.format(policyset_name, new_policyset_description),
                 checks=JCheck('description', new_policyset_description))

        # list and show it
        self.cmd('policy set-definition list', checks=JMESPathCheck("length([?name=='{}'])".format(policyset_name), 1))
        self.cmd('policy set-definition show -n {}'.format(policyset_name), checks=[
            JCheck('name', policyset_name),
            JCheck('displayName', policyset_display_name)
        ])

        # create a policy assignment on a resource group
        policy_assignment_name = self.create_random_name('azurecli-test-policy-assignment', 40)
        policy_assignment_display_name = self.create_random_name('test_assignment', 20)
        self.cmd('policy assignment create -d {} -n {} --display-name {} -g {}'.format(
                 policyset_name, policy_assignment_name, policy_assignment_display_name, resource_group),
                 checks=[
                    JCheck('name', policy_assignment_name),
                    JCheck('displayName', policy_assignment_display_name),
                    JCheck('sku.name', 'A0'),
                    JCheck('sku.tier', 'Free'),
                 ])

        # delete the assignment
        self.cmd('policy assignment delete -n {} -g {}'.format(policy_assignment_name, resource_group))
        self.cmd('policy assignment list --disable-scope-strict-match')

        # delete the policy set
        self.cmd('policy set-definition delete -n {}'.format(policyset_name))
        time.sleep(10)  # ensure the policy is gone when run live.
        self.cmd('policy set-definition list', checks=JCheck("length([?name=='{}'])".format(policyset_name), 0))

    def test_show_built_in_policy(self):
        result = self.cmd('policy definition list --query "[?policyType==\'BuiltIn\']|[0]"').get_output_in_json()
        policy_name = result['name']
        self.cmd('policy definition show -n ' + policy_name, checks=[
            JCheck('name', policy_name)
        ])


class ManagedAppDefinitionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_managedappdef(self, resource_group):
        location = 'eastus2euap'
        appdef_name = self.create_random_name('testappdefname', 20)
        appdef_display_name = self.create_random_name('test_appdef', 20)
        appdef_description = 'test_appdef_123'
        packageUri = 'https:\/\/testclinew.blob.core.windows.net\/files\/vivekMAD.zip'
        auth = '5e91139a-c94b-462e-a6ff-1ee95e8aac07:8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
        lock = 'None'

        # create a managedapp definition
        create_cmd = 'managedapp definition create -n {} --package-file-uri {} --display-name {} --description {} -l {} -a {} --lock-level {} -g {}'
        appdef = self.cmd(create_cmd.format(appdef_name, packageUri, appdef_display_name, appdef_description, location, auth, lock, resource_group), checks=[
            JCheck('name', appdef_name),
            JCheck('displayName', appdef_display_name),
            JCheck('description', appdef_description),
            JCheck('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            JCheck('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            JCheck('artifacts[0].name', 'ApplianceResourceTemplate'),
            JCheck('artifacts[0].type', 'Template'),
            JCheck('artifacts[1].name', 'CreateUiDefinition'),
            JCheck('artifacts[1].type', 'Custom')
        ]).get_output_in_json()

        # list and show it
        list_cmd = 'managedapp definition list -g {}'
        self.cmd(list_cmd.format(resource_group), checks=[
            JCheck('[0].name', appdef_name)
        ])

        show_cmd = 'managedapp definition show --ids {}'
        self.cmd(show_cmd.format(appdef['id']), checks=[
            JCheck('name', appdef_name),
            JCheck('displayName', appdef_display_name),
            JCheck('description', appdef_description),
            JCheck('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            JCheck('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            JCheck('artifacts[0].name', 'ApplianceResourceTemplate'),
            JCheck('artifacts[0].type', 'Template'),
            JCheck('artifacts[1].name', 'CreateUiDefinition'),
            JCheck('artifacts[1].type', 'Custom')
        ])

        # delete
        self.cmd('managedapp definition delete -g {} -n {}'.format(resource_group, appdef_name))
        self.cmd('managedapp definition list -g {}'.format(resource_group), checks=NoneCheck())

    @ResourceGroupPreparer()
    def test_managedappdef_inline(self, resource_group):
        location = 'eastus2euap'
        appdef_name = self.create_random_name('testappdefname', 20)
        appdef_display_name = self.create_random_name('test_appdef', 20)
        appdef_description = 'test_appdef_123'
        auth = '5e91139a-c94b-462e-a6ff-1ee95e8aac07:8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
        lock = 'None'
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        createUiDef_file = os.path.join(curr_dir, 'sample_create_ui_definition.json').replace('\\', '\\\\')
        mainTemplate_file = os.path.join(curr_dir, 'sample_main_template.json').replace('\\', '\\\\')

        # create a managedapp definition with inline params for create-ui-definition and main-template
        create_cmd = 'managedapp definition create -n {} --create-ui-definition @"{}" --main-template @"{}" --display-name {} --description {} -l {} -a {} --lock-level {} -g {}'
        appdef = self.cmd(create_cmd.format(appdef_name, createUiDef_file, mainTemplate_file, appdef_display_name, appdef_description, location, auth, lock, resource_group), checks=[
            JCheck('name', appdef_name),
            JCheck('displayName', appdef_display_name),
            JCheck('description', appdef_description),
            JCheck('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            JCheck('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            JCheck('artifacts[0].name', 'ApplicationResourceTemplate'),
            JCheck('artifacts[0].type', 'Template'),
            JCheck('artifacts[1].name', 'CreateUiDefinition'),
            JCheck('artifacts[1].type', 'Custom')
        ]).get_output_in_json()

        # list and show it
        list_cmd = 'managedapp definition list -g {}'
        self.cmd(list_cmd.format(resource_group), checks=[
            JCheck('[0].name', appdef_name)
        ])

        show_cmd = 'managedapp definition show --ids {}'
        self.cmd(show_cmd.format(appdef['id']), checks=[
            JCheck('name', appdef_name),
            JCheck('displayName', appdef_display_name),
            JCheck('description', appdef_description),
            JCheck('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            JCheck('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            JCheck('artifacts[0].name', 'ApplicationResourceTemplate'),
            JCheck('artifacts[0].type', 'Template'),
            JCheck('artifacts[1].name', 'CreateUiDefinition'),
            JCheck('artifacts[1].type', 'Custom')
        ])

        # delete
        self.cmd('managedapp definition delete -g {} -n {}'.format(resource_group, appdef_name))
        self.cmd('managedapp definition list -g {}'.format(resource_group), checks=NoneCheck())


class ManagedAppScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_managedapp(self, resource_group):
        location = 'westcentralus'
        appdef_name = 'testappdefname'
        appdef_display_name = 'test_appdef_123'
        appdef_description = 'test_appdef_123'
        packageUri = 'https:\/\/wud.blob.core.windows.net\/appliance\/SingleStorageAccount.zip'
        auth = '5e91139a-c94b-462e-a6ff-1ee95e8aac07:8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
        lock = 'None'

        # create a managedapp definition
        create_cmd = 'managedapp definition create -n {} --package-file-uri {} --display-name {} --description {} -l {} -a {} --lock-level {} -g {}'
        managedappdef = self.cmd(create_cmd.format(appdef_name, packageUri, appdef_display_name,
                                                   appdef_description, location, auth, lock, resource_group)).get_output_in_json()

        # create a managedapp
        managedapp_name = 'mymanagedapp'
        managedapp_loc = 'westcentralus'
        managedapp_kind = 'servicecatalog'
        newrg = self.create_random_name('climanagedapp', 25)
        managedrg = '/subscriptions/{}/resourceGroups/{}'.format(managedappdef['id'].split("/")[2], newrg)
        create_cmd = 'managedapp create -n {} -g {} -l {} --kind {} -m {} -d {}'
        app = self.cmd(create_cmd.format(managedapp_name, resource_group, managedapp_loc, managedapp_kind, managedrg, managedappdef['id']), checks=[
            JCheck('name', managedapp_name),
            JCheck('type', 'Microsoft.Solutions/applications'),
            JCheck('kind', 'servicecatalog'),
            JCheck('managedResourceGroupId', managedrg)
        ]).get_output_in_json()

        # list and show
        list_byrg_cmd = 'managedapp list -g {}'
        self.cmd(list_byrg_cmd.format(resource_group), checks=[
            JCheck('[0].name', managedapp_name)
        ])

        show_cmd = 'managedapp show --ids {}'
        self.cmd(show_cmd.format(app['id']), checks=[
            JCheck('name', managedapp_name),
            JCheck('type', 'Microsoft.Solutions/applications'),
            JCheck('kind', 'servicecatalog'),
            JCheck('managedResourceGroupId', managedrg)
        ])

        # delete
        self.cmd('managedapp delete -g {} -n {}'.format(resource_group, managedapp_name))
        self.cmd('managedapp list -g {}'.format(resource_group), checks=NoneCheck())


class CrossRGDeploymentScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_alt', parameter_name='resource_group_cross')
    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_deploy')
    def test_group_deployment_crossrg(self, resource_group, resource_group_cross):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        template_file = os.path.join(curr_dir, 'crossrg_deploy.json').replace('\\', '\\\\')
        deployment_name = self.create_random_name('azure-cli-crossrgdeployment', 40)
        storage_account_1 = create_random_name(prefix='crossrg')
        storage_account_2 = create_random_name(prefix='crossrg')

        self.cmd('group deployment validate -g {} --template-file {} --parameters CrossRg={} StorageAccountName1={} StorageAccountName2={}'.format(
            resource_group, template_file, resource_group_cross, storage_account_1, storage_account_2), checks=[
            JCheck('properties.provisioningState', 'Succeeded')
        ])
        self.cmd('group deployment create -g {} -n {} --template-file {} --parameters CrossRg={}'.format(
            resource_group, deployment_name, template_file, resource_group_cross), checks=[
            JCheck('properties.provisioningState', 'Succeeded'),
            JCheck('resourceGroup', resource_group),
        ])
        self.cmd('group deployment list -g {}'.format(resource_group), checks=[
            JCheck('[0].name', deployment_name),
            JCheck('[0].resourceGroup', resource_group)
        ])
        self.cmd('group deployment show -g {} -n {}'.format(resource_group, deployment_name), checks=[
            JCheck('name', deployment_name),
            JCheck('resourceGroup', resource_group)
        ])
        self.cmd('group deployment operation list -g {} -n {}'.format(resource_group, deployment_name), checks=[
            JCheck('length([])', 3),
            JCheck('[0].resourceGroup', resource_group)
        ])


class InvokeActionTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_invoke_action')
    def test_invoke_action(self, resource_group):
        vm_name = self.create_random_name('cli-test-vm', 30)
        username = 'ubuntu'
        password = self.create_random_name('Longpassword#1', 30)

        vm_json = self.cmd('vm create -g {} -n {} --use-unmanaged-disk --image UbuntuLTS --admin-username {} '
                           '--admin-password {} --authentication-type {}'
                           .format(resource_group, vm_name, username, password, 'password')).get_output_in_json()

        vm_id = vm_json.get('id', None)

        self.cmd('resource invoke-action --action powerOff --ids {}'.format(vm_id))
        self.cmd('resource invoke-action --action generalize --ids {}'.format(vm_id))
        self.cmd('resource invoke-action --action deallocate --ids {}'.format(vm_id))

        request_body = '{\\"vhdPrefix\\":\\"myPrefix\\",\\"destinationContainerName\\":\\"container\\",' \
                       '\\"overwriteVhds\\":\\"true\\"}'

        self.cmd('resource invoke-action --action capture --ids {} --request-body {}'.format(vm_id, request_body))


if __name__ == '__main__':
    unittest.main()
