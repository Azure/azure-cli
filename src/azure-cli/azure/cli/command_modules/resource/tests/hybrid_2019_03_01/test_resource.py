# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
from unittest import mock
import unittest

from azure.cli.testsdk.scenario_tests.const import MOCKED_SUBSCRIPTION_ID
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, create_random_name, live_only, record_only
from azure.cli.core.util import get_file_json


class ResourceGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group(self, resource_group):

        self.cmd('group delete -n {rg} --yes')
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', False))

        self.cmd('group create -n {rg} -l westus --tag a=b c', checks=[
            self.check('name', '{rg}'),
            self.check('tags', {'a': 'b', 'c': ''})
        ])
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', True))
        self.cmd('group show -n {rg}', checks=[
            self.check('name', '{rg}'),
            self.check('tags', {'a': 'b', 'c': ''})
        ])
        self.cmd('group list --tag a=b', checks=[
            self.check('[0].name', '{rg}'),
            self.check('[0].tags', {'a': 'b', 'c': ''})
        ])
        # test --force-string
        self.kwargs.update({'tag': "\"{\\\"k\\\":\\\"v\\\"}\""})
        self.cmd('group update -g {rg} --tags ""',
                 checks=self.check('tags', {}))
        self.cmd('group update -g {rg} --set tags.a={tag}',
                 checks=self.check('tags.a', "{{'k': 'v'}}"))
        self.cmd('group update -g {rg} --set tags.b={tag} --force-string',
                 checks=self.check('tags.b', '{{\"k\":\"v\"}}'))


class ResourceGroupNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_rg_nowait_test')
    def test_resource_group_no_wait(self, resource_group):

        self.cmd('group delete -n {rg} --no-wait --yes',
                 checks=self.is_empty())
        self.cmd('group wait --deleted -n {rg}',
                 checks=self.is_empty())
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', False))
        self.cmd('group create -n {rg} -l westus',
                 checks=self.check('name', '{rg}'))
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', True))
        self.cmd('group wait --exists -n {rg}',
                 checks=self.is_empty())


class ResourceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_scenario', location='southcentralus')
    @AllowLargeResponse()
    def test_resource_scenario(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'vnet': self.create_random_name('vnet-', 30),
            'subnet': self.create_random_name('subnet-', 30),
            'rt': 'Microsoft.Network/virtualNetworks'
        })
        vnet_count = self.cmd("resource list --query \"length([?name=='{vnet}'])\"").get_output_in_json() or 0
        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet} --tags cli-test=test')
        vnet_count += 1

        self.cmd('resource list',
                 checks=self.check("length([?name=='{vnet}'])", vnet_count))
        self.cmd('resource list -l {loc}',
                 checks=self.check("length([?location == '{loc}']) == length(@)", True))
        self.cmd('resource list --resource-type {rt}',
                 checks=self.check("length([?name=='{vnet}'])", vnet_count))
        self.cmd('resource list --name {vnet}', checks=[
            self.check("length([?name=='{vnet}'])", vnet_count),
            self.check('[0].provisioningState', 'Succeeded')
        ])
        self.cmd('resource list --tag cli-test',
                 checks=self.check("length([?name=='{vnet}'])", vnet_count))
        self.cmd('resource list --tag cli-test=test',
                 checks=self.check("length([?name=='{vnet}'])", vnet_count))

        # check for simple resource with tag
        self.cmd('resource show -n {vnet} -g {rg} --resource-type Microsoft.Network/virtualNetworks', checks=[
            self.check('name', '{vnet}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags', {'cli-test': 'test'})
        ])
        # check for child resource
        self.cmd('resource show -n {subnet} -g {rg} --namespace Microsoft.Network --parent virtualNetworks/{vnet} --resource-type subnets', checks=[
            self.check('name', '{subnet}'),
            self.check('resourceGroup', '{rg}')
        ])

        # clear tag and verify
        self.cmd('resource tag -n {vnet} -g {rg} --resource-type Microsoft.Network/virtualNetworks --tags')
        self.cmd('resource show -n {vnet} -g {rg} --resource-type Microsoft.Network/virtualNetworks',
                 checks=self.check('tags', {}))

        # delete and verify
        self.cmd('resource delete -n {vnet} -g {rg} --resource-type {rt}')
        time.sleep(10)
        self.cmd('resource list', checks=self.check("length([?name=='{vnet}'])", 0))


class ResourceIDScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_id')
    def test_resource_id_scenario(self, resource_group):

        self.kwargs.update({
            'vnet': 'cli_test_resource_id_vnet',
            'subnet': 'cli_test_resource_id_subnet'
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')

        self.kwargs['sub'] = self.get_subscription_id()

        self.kwargs['vnet_id'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}'.format(
            **self.kwargs)
        self.cmd('resource tag --id {vnet_id} --tags tag-vnet')
        self.cmd('resource show --id {vnet_id}', checks=[
            self.check('name', '{vnet}'),
            self.check('resourceGroup', '{rg}'),
            self.check('tags', {'tag-vnet': ''})
        ])

        self.kwargs['subnet_id'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/{vnet}/subnets/{subnet}'.format(
            **self.kwargs)
        self.cmd('resource show --id {subnet_id}', checks=[
            self.check('name', '{subnet}'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.addressPrefix', '10.0.0.0/24')
        ])

        self.cmd('resource update --id {subnet_id} --set properties.addressPrefix=10.0.0.0/22',
                 checks=self.check('properties.addressPrefix', '10.0.0.0/22'))

        self.cmd('resource delete --id {subnet_id}', checks=self.is_empty())
        self.cmd('resource delete --id {vnet_id}', checks=self.is_empty())


class ResourceGenericUpdate(LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_resource_id')
    def test_resource_id_scenario(self, resource_group):
        self.kwargs.update({
            'stor_1': self.create_random_name(prefix='stor1', length=10),
            'stor_2': self.create_random_name(prefix='stor2', length=10)
        })

        # create storage accounts
        self.cmd('az storage account create -g {rg} -n {stor_1}')
        self.cmd('az storage account create -g {rg} -n {stor_2}')

        # get ids
        self.kwargs['stor_ids'] = " ".join(self.cmd('az storage account list -g {rg} --query "[].id"').get_output_in_json())

        # update tags
        self.cmd('az storage account update --ids {stor_ids} --set tags.isTag=True tags.isNotTag=False')

        self.cmd('az storage account show --name {stor_1} -g {rg}', checks=[
            self.check('tags.isTag', 'True'),
            self.check('tags.isNotTag', 'False')
        ])
        self.cmd('az storage account show --name {stor_2} -g {rg}', checks=[
            self.check('tags.isTag', 'True'),
            self.check('tags.isNotTag', 'False')
        ])

        # delete tags.isTag
        self.cmd('az storage account update --ids {stor_ids} --remove tags.isTag')

        self.cmd('az storage account show --name {stor_1} -g {rg} --query "tags"', checks=[
            self.check('isNotTag', 'False'),
            self.check('isTag', None)
        ])
        self.cmd('az storage account show --name {stor_2} -g {rg} --query "tags"', checks=[
            self.check('isNotTag', 'False'),
            self.check('isTag', None)
        ])

        # delete tags.isNotTag
        self.cmd('az storage account update --ids {stor_ids} --remove tags.isNotTag')

        # check tags is empty.
        self.cmd('az storage account show --name {stor_1} -g {rg} --query "tags"', checks=self.is_empty())
        self.cmd('az storage account show --name {stor_2} -g {rg} --query "tags"', checks=self.is_empty())


class ResourceCreateAndShowScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_create')
    def test_resource_create_and_show(self, resource_group, resource_group_location):

        self.kwargs.update({
            'plan': 'cli_res_create_plan',
            'app': 'clirescreateweb',
            'loc': resource_group_location
        })

        self.cmd('resource create -g {rg} -n {plan} --resource-type Microsoft.web/serverFarms --is-full-object --properties "{{\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"B1\\",\\"tier\\":\\"BASIC\\"}}}}"',
                 checks=self.check('name', '{plan}'))

        result = self.cmd('resource create -g {rg} -n {app} --resource-type Microsoft.web/sites --properties "{{\\"serverFarmId\\":\\"{plan}\\"}}"',
                          checks=self.check('name', '{app}')).get_output_in_json()

        self.kwargs['app_settings_id'] = result['id'] + '/config/appsettings'
        self.kwargs['app_config_id'] = result['id'] + '/config/web'
        self.cmd('resource create --id {app_settings_id} --properties "{{\\"key2\\":\\"value12\\"}}"',
                 checks=[self.check('properties.key2', 'value12')])

        self.cmd('resource show --id {app_config_id}',
                 checks=self.check('properties.publishingUsername', '${app}'))
        self.cmd('resource show --id {app_config_id} --include-response-body',
                 checks=self.check('responseBody.properties.publishingUsername', '${app}'))


class TagScenarioTest(ScenarioTest):

    def test_tag_scenario(self):

        self.kwargs.update({
            'tag': 'cli_test_tag'
        })

        tag_values = self.cmd('tag list --query "[?tagName == \'{tag}\'].values[].tagValue"').get_output_in_json()
        for tag_value in tag_values:
            self.cmd('tag remove-value --value {} -n {{tag}}'.format(tag_value))
        self.cmd('tag delete -n {tag} -y')

        self.cmd('tag list --query "[?tagName == \'{tag}\']"', checks=self.is_empty())
        self.cmd('tag create -n {tag}', checks=[
            self.check('tagName', '{tag}'),
            self.check('values', []),
            self.check('count.value', 0)
        ])
        self.cmd('tag add-value -n {tag} --value test')
        self.cmd('tag add-value -n {tag} --value test2')
        self.cmd('tag list --query "[?tagName == \'{tag}\']"',
                 checks=self.check('[].values[].tagValue', [u'test', u'test2']))
        self.cmd('tag remove-value -n {tag} --value test')
        self.cmd('tag list --query "[?tagName == \'{tag}\']"',
                 checks=self.check('[].values[].tagValue', [u'test2']))
        self.cmd('tag remove-value -n {tag} --value test2')
        self.cmd('tag list --query "[?tagName == \'{tag}\']"',
                 checks=self.check('[].values[].tagValue', []))
        self.cmd('tag delete -n {tag} -y')
        self.cmd('tag list --query "[?tagName == \'{tag}\']"',
                 checks=self.is_empty())


class ProviderRegistrationTest(ScenarioTest):

    def test_provider_registration(self):

        self.kwargs.update({'prov': 'Microsoft.ClassicInfrastructureMigrate'})

        result = self.cmd('provider show -n {prov}').get_output_in_json()
        if result['registrationState'] == 'Unregistered':
            self.cmd('provider register -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Registering', 'Registered'])
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
        else:
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
            self.cmd('provider register -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Registering', 'Registered'])


class ProviderOperationTest(ScenarioTest):

    def test_provider_operation(self):
        self.cmd('provider operation show --namespace microsoft.compute', checks=[
            self.check('id', '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
            self.check('type', 'Microsoft.Authorization/providerOperations')
        ])
        self.cmd('provider operation show --namespace microsoft.compute', checks=[
            self.check('id', '/providers/Microsoft.Authorization/providerOperations/Microsoft.Compute'),
            self.check('type', 'Microsoft.Authorization/providerOperations')
        ])
        self.cmd('provider operation show --namespace microsoft.storage', checks=[
            self.check('id', '/providers/Microsoft.Authorization/providerOperations/Microsoft.Storage'),
            self.check('type', 'Microsoft.Authorization/providerOperations')
        ])


class SubscriptionLevelDeploymentTest(LiveScenarioTest):
    def tearDown(self):
        self.cmd('policy assignment delete -n location-lock')
        self.cmd('policy definition delete -n policy2')

    def test_subscription_level_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/command_modules/azure-cli-resource/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': self.create_random_name('azure-cli-sub-level-desubscription_level_parametersployment', 40)
        })

        self.cmd('group create --name cli_test_subscription_level_deployment --location WestUS', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters @"{params_uri}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment create -n {dn} --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment list', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment export -n {dn}', checks=[
        ])

        self.cmd('deployment operation list -n {dn}', checks=[
            self.check('length([])', 4)
        ])


class DeploymentTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_lite')
    def test_group_deployment_lite(self, resource_group):
        # ensures that a template that is missing "parameters" or "resources" still deploys
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment')
    def test_group_deployment(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the test_params.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/test-params.json',
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment'
        })
        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters "{params_uri}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('network lb show -g {rg} -n test-lb',
                 checks=self.check('tags', {'key': 'super=value'}))

        self.cmd('group deployment list -g {rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{rg}')
        ])
        self.cmd('group deployment show -g {rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{rg}')
        ])
        self.cmd('group deployment operation list -g {rg} -n {dn}', checks=[
            self.check('length([])', 2),
            self.check('[0].resourceGroup', '{rg}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_on_error_deployment_lastsuccessful')
    def test_group_on_error_deployment_lastsuccessful(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30),
            'onErrorType': 'LastSuccessful',
            'sdn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment', None)
        ])

        self.cmd('group deployment create -g {rg} -n {sdn} --template-file "{tf}" --rollback-on-error', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment.deploymentName', '{dn}'),
            self.check('properties.onErrorDeployment.type', '{onErrorType}')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_on_error_deployment_specificdeployment')
    def test_group_on_error_deployment_specificdeployment(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template-lite.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-deployment', 30),
            'onErrorType': 'SpecificDeployment',
            'sdn': self.create_random_name('azure-cli-deployment', 30)
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment', None)
        ])

        self.cmd('group deployment create -g {rg} -n {sdn} --template-file "{tf}" --rollback-on-error {dn}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.onErrorDeployment.deploymentName', '{dn}'),
            self.check('properties.onErrorDeployment.type', '{onErrorType}')
        ])


class DeploymentLiveTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_group_deployment_progress(self, resource_group):
        from azure.cli.testsdk.utilities import force_progress_logging
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'test-template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\'),
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment2'
        })

        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        with force_progress_logging() as test_io:
            self.cmd('group deployment create --verbose -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"')

        # very the progress
        lines = test_io.getvalue().splitlines()
        for line in lines:
            self.assertTrue(line.split(':')[0] in ['Accepted', 'Succeeded'])
        self.assertTrue('Succeeded: {} (Microsoft.Resources/deployments)'.format(self.kwargs['dn']), lines)


class DeploymentNoWaitTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_group_deployment_no_wait')
    def test_group_deployment_no_wait(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment'
        })

        self.cmd('group deployment create -g {rg} -n {dn} --template-file "{tf}" --parameters @"{params}" --no-wait',
                 checks=self.is_empty())

        self.cmd('group deployment wait -g {rg} -n {dn} --created',
                 checks=self.is_empty())

        self.cmd('group deployment show -g {rg} -n {dn}',
                 checks=self.check('properties.provisioningState', 'Succeeded'))


class DeploymentThruUriTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_uri')
    def test_group_deployment_thru_uri(self, resource_group):
        self.resource_group = resource_group
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        # same copy of the sample template file under current folder, but it is uri based now
        self.kwargs.update({
            'tf': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/simple_deploy.json',
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\')
        })
        self.kwargs['dn'] = self.cmd('group deployment create -g {rg} --template-uri "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
        ]).get_output_in_json()['name']

        self.cmd('group deployment show -g {rg} -n {dn}',
                 checks=self.check('name', '{dn}'))

        self.cmd('group deployment delete -g {rg} -n {dn}')
        self.cmd('group deployment list -g {rg}',
                 checks=self.is_empty())


class ResourceMoveScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_resource_move_dest', parameter_name='resource_group_dest', key='rg2')
    @ResourceGroupPreparer(name_prefix='cli_test_resource_move_source', key='rg1')
    def test_resource_move(self, resource_group, resource_group_dest):
        self.kwargs.update({
            'nsg1': self.create_random_name('nsg-move', 20),
            'nsg2': self.create_random_name('nsg-move', 20)
        })

        self.kwargs['nsg1_id'] = self.cmd('network nsg create -n {nsg1} -g {rg1}').get_output_in_json()['NewNSG']['id']
        self.kwargs['nsg2_id'] = self.cmd('network nsg create -n {nsg2} -g {rg1}').get_output_in_json()['NewNSG']['id']

        self.cmd('resource move --ids {nsg1_id} {nsg2_id} --destination-group {rg2}')

        self.cmd('network nsg show -g {rg2} -n {nsg1}', checks=[
            self.check('name', '{nsg1}')])
        self.cmd('network nsg show -g {rg2} -n {nsg2}', checks=[
                 self.check('name', '{nsg2}')])


class PolicyScenarioTest(ScenarioTest):

    def cmdstring(self, basic, management_group=None, subscription=None):
        cmd = basic
        if (management_group):
            cmd = cmd + ' --management-group {mg}'
        if (subscription):
            cmd = cmd + ' --subscription {sub}'
        return cmd

    def applyPolicy(self):
        # create a policy assignment on a resource group
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'padn': self.create_random_name('test_assignment', 20)
        })

        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --params {params}', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}')
        ])

        # create a policy assignment using a built in policy definition name
        self.kwargs['pan2'] = self.create_random_name('azurecli-test-policy-assignment2', 40)
        self.kwargs['bip'] = '06a78e20-9358-41c9-923c-fb736d382a4d'

        self.cmd('policy assignment create --policy {bip} -n {pan2} --display-name {padn} -g {rg}', checks=[
            self.check('name', '{pan2}'),
            self.check('displayName', '{padn}')
        ])

        self.cmd('policy assignment delete -n {pan2} -g {rg}')

        # listing at subscription level won't find the assignment made at a resource group
        import jmespath
        try:
            self.cmd('policy assignment list', checks=self.check("length([?name=='{pan}'])", 0))
        except jmespath.exceptions.JMESPathTypeError:  # ok if query fails on None result
            pass

        # but enable --show-all works
        self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 1))

        # delete the assignment and validate it's gone
        self.cmd('policy assignment delete -n {pan} -g {rg}')
        self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))

    def applyPolicyAtScope(self, scope, policyId):
        # create a policy assignment at the given scope
        self.kwargs.update({
            'pol': policyId,
            'pan': self.create_random_name('cli-test-polassg', 24),   # limit is 24 characters at MG scope
            'padn': self.create_random_name('test_assignment', 20),
            'scope': scope
        })

        self.cmd('policy assignment create --policy {pol} -n {pan} --display-name {padn} --params {params} --scope {scope}', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('sku.name', 'A0'),
            self.check('sku.tier', 'Free')
        ])

        # delete the assignment and validate it's gone
        self.cmd('policy assignment delete -n {pan} --scope {scope}')
        self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))

    def resource_policy_operations(self, resource_group, management_group=None, subscription=None):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'pn': self.create_random_name('azure-cli-test-policy', 30),
            'pdn': self.create_random_name('test_policy', 20),
            'desc': 'desc_for_test_policy_123',
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'sample_policy_param.json').replace('\\', '\\\\'),
            'mode': 'Indexed'
        })
        if (management_group):
            self.kwargs.update({'mg': management_group})
        if (subscription):
            self.kwargs.update({'sub': subscription})

        # create a policy
        cmd = self.cmdstring('policy definition create -n {pn} --rules {rf} --params {pdf} --display-name {pdn} --description {desc} --mode {mode}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{pn}'),
            self.check('displayName', '{pdn}'),
            self.check('description', '{desc}'),
            self.check('mode', '{mode}')
        ])

        # update it
        self.kwargs['desc'] = self.kwargs['desc'] + '_new'
        self.kwargs['pdn'] = self.kwargs['pdn'] + '_new'

        cmd = self.cmdstring('policy definition update -n {pn} --description {desc} --display-name {pdn}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('description', '{desc}'),
            self.check('displayName', '{pdn}')
        ])

        # list and show it
        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 1))

        cmd = self.cmdstring('policy definition show -n {pn}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{pn}'),
            self.check('displayName', '{pdn}')
        ])

        # apply assignments
        if management_group:
            scope = '/providers/Microsoft.Management/managementGroups/{mg}'.format(mg=management_group)
            policy = '{scope}/providers/Microsoft.Authorization/policyDefinitions/{pn}'.format(pn=self.kwargs['pn'], scope=scope)
            self.applyPolicyAtScope(scope, policy)
        elif subscription:
            policy = '/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions/{pn}'.format(sub=subscription, pn=self.kwargs['pn'])
            self.applyPolicyAtScope('/subscriptions/{sub}'.format(sub=subscription), policy)
        else:
            self.applyPolicy()

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))

    def resource_policyset_operations(self, resource_group, management_group=None, subscription=None):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'pn': self.create_random_name('azure-cli-test-policy', 30),
            'pdn': self.create_random_name('test_policy', 20),
            'desc': 'desc_for_test_policy_123',
            'psn': self.create_random_name('azure-cli-test-policyset', 30),
            'psdn': self.create_random_name('test_policyset', 20),
            'ps_desc': 'desc_for_test_policyset_123',
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'psf': os.path.join(curr_dir, 'sample_policy_set.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\')
        })
        if (management_group):
            self.kwargs.update({'mg': management_group})
        if (subscription):
            self.kwargs.update({'sub': subscription})

        # create a policy
        cmd = self.cmdstring('policy definition create -n {pn} --rules {rf} --params {pdf} --display-name {pdn} --description {desc}', management_group, subscription)
        policy = self.cmd(cmd).get_output_in_json()

        # create a policy set
        policyset = get_file_json(self.kwargs['psf'])
        policyset[0]['policyDefinitionId'] = policy['id']
        with open(os.path.join(curr_dir, 'sample_policy_set.json'), 'w') as outfile:
            json.dump(policyset, outfile)

        cmd = self.cmdstring('policy set-definition create -n {psn} --definitions @"{psf}" --display-name {psdn} --description {ps_desc}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}'),
            self.check('description', '{ps_desc}')
        ])

        # update it
        self.kwargs['ps_desc'] = self.kwargs['ps_desc'] + '_new'
        self.kwargs['psdn'] = self.kwargs['psdn'] + '_new'

        cmd = self.cmdstring('policy set-definition update -n {psn} --display-name {psdn} --description {ps_desc}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('description', '{ps_desc}'),
            self.check('displayName', '{psdn}')
        ])

        # list and show it
        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 1))

        cmd = self.cmdstring('policy set-definition show -n {psn}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}')
        ])

        # create a policy assignment on a resource group
        if not management_group and not subscription:
            self.kwargs.update({
                'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
                'padn': self.create_random_name('test_assignment', 20)
            })

            self.cmd('policy assignment create -d {psn} -n {pan} --display-name {padn} -g {rg}', checks=[
                self.check('name', '{pan}'),
                self.check('displayName', '{padn}'),
                self.check('sku.name', 'A0'),
                self.check('sku.tier', 'Free'),
            ])

            # delete the assignment and validate it's gone
            self.cmd('policy assignment delete -n {pan} -g {rg}')
            self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))

        # delete the policy set
        cmd = self.cmdstring('policy set-definition delete -n {psn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))

    @ResourceGroupPreparer(name_prefix='cli_test_policy')
    @AllowLargeResponse(8192)
    def test_resource_policy_default(self, resource_group):
        self.resource_policy_operations(resource_group)

    @record_only()
    @unittest.skip('mock doesnt work when the subscription comes from --scope')
    @ResourceGroupPreparer(name_prefix='cli_test_policy_subscription_id')
    @AllowLargeResponse()
    def test_resource_policy_subscription_id(self, resource_group):
        # under playback, we mock it so the subscription id will be '00000000...' and it will match
        # the same sanitized value in the recording
        if not self.in_recording:
            with mock.patch('azure.cli.command_modules.resource.custom._get_subscription_id_from_subscription',
                            return_value=MOCKED_SUBSCRIPTION_ID):
                self.resource_policy_operations(resource_group, None, 'e8a0d3c2-c26a-4363-ba6b-f56ac74c5ae0')
        else:
            self.resource_policy_operations(resource_group, None, 'e8a0d3c2-c26a-4363-ba6b-f56ac74c5ae0')

    @AllowLargeResponse(8192)
    def test_show_built_in_policy(self):
        # get the list of builtins, then retrieve each via show and validate the results match
        results = self.cmd('policy definition list --query "[?policyType==\'BuiltIn\']"').get_output_in_json()
        if results:
            result = results[0]
            self.kwargs['pn'] = result['name']
            self.kwargs['dn'] = result['displayName']
            self.kwargs['desc'] = result['description']
            self.kwargs['id'] = result['id']
            self.cmd('policy definition show -n {pn}', checks=[
                self.check('name', '{pn}'),
                self.check('description', '{desc}'),
                self.check('displayName', '{dn}'),
                self.check('id', '{id}')
            ])


class ManagedAppDefinitionScenarioTest(ScenarioTest):
    @ResourceGroupPreparer()
    def test_managedappdef_inline(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'loc': 'eastus',
            'adn': self.create_random_name('testappdefname', 20),
            'addn': self.create_random_name('test_appdef', 20),
            'ad_desc': 'test_appdef_123',
            'auth': '5e91139a-c94b-462e-a6ff-1ee95e8aac07:8e3af657-a8ff-443c-a75c-2fe8c4bcb635',
            'lock': 'None',
            'ui_file': os.path.join(curr_dir, 'sample_create_ui_definition.json').replace('\\', '\\\\'),
            'main_file': os.path.join(curr_dir, 'sample_main_template.json').replace('\\', '\\\\')
        })

        # create a managedapp definition with inline params for create-ui-definition and main-template
        self.kwargs['ad_id'] = self.cmd('managedapp definition create -n {adn} --create-ui-definition @"{ui_file}" --main-template @"{main_file}" --display-name {addn} --description {ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{ad_desc}'),
            self.check('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            self.check('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            self.check('artifacts[0].name', 'ApplicationResourceTemplate'),
            self.check('artifacts[0].type', 'Template'),
            self.check('artifacts[1].name', 'CreateUiDefinition'),
            self.check('artifacts[1].type', 'Custom')
        ]).get_output_in_json()['id']

        self.cmd('managedapp definition list -g {rg}',
                 checks=self.check('[0].name', '{adn}'))

        self.cmd('managedapp definition show --ids {ad_id}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{ad_desc}'),
            self.check('authorizations[0].principalId', '5e91139a-c94b-462e-a6ff-1ee95e8aac07'),
            self.check('authorizations[0].roleDefinitionId', '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'),
            self.check('artifacts[0].name', 'ApplicationResourceTemplate'),
            self.check('artifacts[0].type', 'Template'),
            self.check('artifacts[1].name', 'CreateUiDefinition'),
            self.check('artifacts[1].type', 'Custom')
        ])

        self.cmd('managedapp definition delete -g {rg} -n {adn}')
        self.cmd('managedapp definition list -g {rg}', checks=self.is_empty())


# TODO: Change back to ScenarioTest and re-record when issue #5110 is fixed.
class ManagedAppScenarioTest(LiveScenarioTest):
    @ResourceGroupPreparer()
    def test_managedapp(self, resource_group):

        self.kwargs.update({
            'loc': 'westcentralus',
            'adn': 'testappdefname',
            'addn': 'test_appdef_123',
            'ad_desc': 'test_appdef_123',
            'uri': 'https://wud.blob.core.windows.net/appliance/SingleStorageAccount.zip',
            'auth': '5e91139a-c94b-462e-a6ff-1ee95e8aac07:8e3af657-a8ff-443c-a75c-2fe8c4bcb635',
            'lock': 'None',
            'sub': self.get_subscription_id()
        })

        self.kwargs['ad_id'] = self.cmd('managedapp definition create -n {adn} --package-file-uri {uri} --display-name {addn} --description {ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}').get_output_in_json()['id']

        # create a managedapp
        self.kwargs.update({
            'man': 'mymanagedapp',
            'ma_loc': 'westcentralus',
            'ma_kind': 'servicecatalog',
            'ma_rg': self.create_random_name('climanagedapp', 25)
        })
        self.kwargs['ma_rg_id'] = '/subscriptions/{sub}/resourceGroups/{ma_rg}'.format(**self.kwargs)

        self.kwargs['ma_id'] = self.cmd('managedapp create -n {man} -g {rg} -l {ma_loc} --kind {ma_kind} -m {ma_rg_id} -d {ad_id}', checks=[
            self.check('name', '{man}'),
            self.check('type', 'Microsoft.Solutions/applications'),
            self.check('kind', 'servicecatalog'),
            self.check('managedResourceGroupId', '{ma_rg_id}')
        ]).get_output_in_json()['id']

        self.cmd('managedapp list -g {rg}', checks=self.check('[0].name', '{man}'))

        self.cmd('managedapp show --ids {ma_id}', checks=[
            self.check('name', '{man}'),
            self.check('type', 'Microsoft.Solutions/applications'),
            self.check('kind', 'servicecatalog'),
            self.check('managedResourceGroupId', '{ma_rg_id}')
        ])

        self.cmd('managedapp delete -g {rg} -n {man}')
        self.cmd('managedapp list -g {rg}', checks=self.is_empty())


class CrossRGDeploymentScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_alt', parameter_name='resource_group_cross')
    @ResourceGroupPreparer(name_prefix='cli_test_cross_rg_deploy')
    def test_group_deployment_crossrg(self, resource_group, resource_group_cross):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'rg1': resource_group,
            'rg2': resource_group_cross,
            'tf': os.path.join(curr_dir, 'crossrg_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-crossrgdeployment', 40),
            'sa1': create_random_name(prefix='crossrg'),
            'sa2': create_random_name(prefix='crossrg')
        })

        self.cmd('group deployment validate -g {rg1} --template-file "{tf}" --parameters CrossRg={rg2} StorageAccountName1={sa1} StorageAccountName2={sa2}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])
        self.cmd('group deployment create -g {rg1} -n {dn} --template-file "{tf}" --parameters CrossRg={rg2}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg1}'),
        ])
        self.cmd('group deployment list -g {rg1}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{rg1}')
        ])
        self.cmd('group deployment show -g {rg1} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{rg1}')
        ])
        self.cmd('group deployment operation list -g {rg1} -n {dn}', checks=[
            self.check('length([])', 3),
            self.check('[0].resourceGroup', '{rg1}')
        ])


class InvokeActionTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_invoke_action')
    def test_invoke_action(self, resource_group):

        self.kwargs.update({
            'vm': self.create_random_name('cli-test-vm', 30),
            'user': 'ubuntu',
            'pass': self.create_random_name('Longpassword#1', 30)
        })

        self.kwargs['vm_id'] = self.cmd('vm create -g {rg} -n {vm} --use-unmanaged-disk --image UbuntuLTS --admin-username {user} --admin-password {pass} --authentication-type password --nsg-rule None').get_output_in_json()['id']

        self.cmd('resource invoke-action --action powerOff --ids {vm_id}')
        self.cmd('resource invoke-action --action generalize --ids {vm_id}')
        self.cmd('resource invoke-action --action deallocate --ids {vm_id}')

        self.kwargs['request_body'] = '{\\"vhdPrefix\\":\\"myPrefix\\",\\"destinationContainerName\\":\\"container\\",\\"overwriteVhds\\":\\"true\\"}'

        self.cmd('resource invoke-action --action capture --ids {vm_id} --request-body {request_body}')


class GlobalIdsScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_global_ids')
    def test_global_ids(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1'
        })
        self.kwargs['vnet_id'] = self.cmd('network vnet create -g {rg} -n {vnet}').get_output_in_json()['newVNet']['id']
        # command will fail if the other parameters were actually used
        self.cmd('network vnet show --subscription fakesub --resource-group fakerg -n fakevnet --ids {vnet_id}')


if __name__ == '__main__':
    unittest.main()
