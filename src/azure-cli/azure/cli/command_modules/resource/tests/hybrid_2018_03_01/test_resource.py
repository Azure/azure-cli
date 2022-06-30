# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import unittest

from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import ScenarioTest, LiveScenarioTest, ResourceGroupPreparer, create_random_name, live_only
from azure.cli.core.util import get_file_json

from knack.util import CLIError

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

    def test_resource_group_empty_string_arg(self):
        expected_msg = "{} can't be an empty string"
        with self.assertRaisesRegex(CLIError, expected_msg.format("-n")):
            self.cmd('group create -n "" -l westus')
        with self.assertRaisesRegex(CLIError, expected_msg.format("-g")):
            self.cmd('group exists -g ""')
        with self.assertRaisesRegex(CLIError, expected_msg.format("--name")):
            self.cmd('group show --name ""')
        with self.assertRaisesRegex(CLIError, expected_msg.format("--resource-group")):
            self.cmd('group delete --resource-group ""')


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
        self.cmd('provider operation show --namespace microsoft.storage')


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
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment'
        })
        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
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


# TODO: convert back to ScenarioTest when #5740 is fixed.
class DeploymentThruUriTest(LiveScenarioTest):

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

    @AllowLargeResponse(8192)
    @ResourceGroupPreparer(name_prefix='cli_test_policy')
    def test_resource_policy(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'pn': self.create_random_name('azure-cli-test-policy', 30),
            'pdn': self.create_random_name('test_policy', 20),
            'desc': 'desc_for_test_policy_123',
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'sample_policy_param.json').replace('\\', '\\\\'),
            'mode': 'Indexed',
        })

        # create a policy
        self.cmd('policy definition create -n {pn} --rules {rf} --params {pdf} --display-name {pdn} --description {desc} --mode {mode}', checks=[
            self.check('name', '{pn}'),
            self.check('displayName', '{pdn}'),
            self.check('description', '{desc}'),
            self.check('mode', '{mode}')
        ])

        # update it
        self.kwargs['desc'] = self.kwargs['desc'] + '_new'
        self.cmd('policy definition update -n {pn} --description {desc}', checks=[
            self.check('description', '{desc}')
        ])

        # list and show it
        self.cmd('policy definition list',
                 checks=self.check("length([?name=='{pn}'])", 1))
        self.cmd('policy definition show -n {pn}', checks=[
            self.check('name', '{pn}'),
            self.check('displayName', '{pdn}')
        ])

        # create a policy assignment on a resource group
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'padn': self.create_random_name('test_assignment', 20)
        })
        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --params {params}', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}')
        ])

        # create a policy assignment with not scopes and standard sku
        self.kwargs.update({
            'vnet': self.create_random_name('azurecli-test-policy-vnet', 40),
            'subnet': self.create_random_name('azurecli-test-policy-subnet', 40),
            'sub': self.get_subscription_id()
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.kwargs['notscope'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks'.format(**self.kwargs)
        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --not-scopes {notscope} --params {params}', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}')
        ])

        # listing at subscription level won't find the assignment made at a resource group
        import jmespath
        try:
            self.cmd('policy assignment list',
                     checks=self.check("length([?name=='{pan}'])", 0))
        except jmespath.exceptions.JMESPathTypeError:  # ok if query fails on None result
            pass

        # but enable --show-all works
        self.cmd('policy assignment list --disable-scope-strict-match',
                 checks=self.check("length([?name=='{pan}'])", 1))

        # delete the assignment
        self.cmd('policy assignment delete -n {pan} -g {rg}')
        self.cmd('policy assignment list --disable-scope-strict-match')

        # delete the policy
        self.cmd('policy definition delete -n {pn}')
        time.sleep(10)  # ensure the policy is gone when run live.
        self.cmd('policy definition list',
                 checks=self.check("length([?name=='{pn}'])", 0))


# TODO: Change back to ScenarioTest and re-record when issue #5110 is fixed.
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
    @ResourceGroupPreparer(name_prefix='cli_test_invoke_action', location='eastus')
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


if __name__ == '__main__':
    unittest.main()
