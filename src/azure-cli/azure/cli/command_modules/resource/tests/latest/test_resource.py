# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import time
import mock
import unittest

from azure.cli.core.parser import IncorrectUsageError
from azure_devtools.scenario_tests.const import MOCKED_SUBSCRIPTION_ID
from azure_devtools.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer,
                               create_random_name, live_only, record_only)
from azure.cli.core.util import get_file_json
from knack.util import CLIError


class ResourceGroupScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group(self, resource_group):

        self.cmd('group delete -n {rg} --yes')
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', False))

        self.cmd('group create -n {rg} -l westus --tag a=b c --managed-by test_admin', checks=[
            self.check('name', '{rg}'),
            self.check('tags', {'a': 'b', 'c': ''}),
            self.check('managedBy', 'test_admin')
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

        result = self.cmd('group export --name {rg} --query "contentVersion"')

        self.assertEqual('"1.0.0.0"\n', result.output)

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group_export_skip_all_params(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.kwargs['vnet_id'] = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()['id']
        result = self.cmd('group export --name {rg} --resource-ids "{vnet_id}" --skip-all-params --query "parameters"')

        self.assertEqual('{}\n', result.output)

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group_export_skip_resource_name_params(self, resource_group):

        self.kwargs.update({
            'vnet': 'vnet1'
        })

        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.kwargs['vnet_id'] = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()['id']
        result = self.cmd('group export --name {rg} --resource-ids "{vnet_id}" --skip-resource-name-params --query "parameters"')

        self.assertEqual('{}\n', result.output)


class ResourceGroupNoWaitScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_rg_nowait_test')
    def test_resource_group_no_wait(self, resource_group):

        self.cmd('group delete -n {rg} --no-wait --yes',
                 checks=self.is_empty())
        self.cmd('group wait --deleted -n {rg}',
                 checks=self.is_empty())
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', False))
        self.cmd('group create -n {rg} -l westus --managed-by test_admin', checks=[
            self.check('name', '{rg}'),
            self.check('managedBy', 'test_admin')
        ])
        self.cmd('group exists -n {rg}',
                 checks=self.check('@', True))
        self.cmd('group wait --exists -n {rg}',
                 checks=self.is_empty())


class ResourceLinkScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_link_scenario')
    def test_resource_link_scenario(self, resource_group):
        self.kwargs.update({
            'vnet': 'vnet1'
        })
        self.cmd('network vnet create -g {rg} -n {vnet}')
        self.kwargs['vnet_id'] = self.cmd('network vnet show -g {rg} -n {vnet}').get_output_in_json()['id']
        rg_id = self.cmd('group show -g {rg}').get_output_in_json()['id']
        self.kwargs['link_id'] = '{}/providers/Microsoft.Resources/links/link1'.format(rg_id)
        self.cmd('resource link create --link {link_id} --target {vnet_id} --notes "blah notes"')
        self.cmd('resource link show --link {link_id}', checks=[
            self.check('name', 'link1'),
            self.check('properties.notes', 'blah notes')
        ])
        self.cmd('resource link update --link {link_id} --target {vnet_id} --notes "group to vnet"')
        num_link = int(self.cmd('resource link list --query length(@) -o tsv').output)
        self.cmd('resource link show --link {link_id}', checks=[
            self.check('name', 'link1'),
            self.check('properties.notes', 'group to vnet')
        ])
        self.cmd('resource link delete --link {link_id}')
        self.cmd('resource link list',
                 checks=self.check('length(@)', num_link - 1))


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
        self.cmd('resource list --name {vnet}',
                 checks=self.check("length([?name=='{vnet}'])", vnet_count))
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

    @ResourceGroupPreparer(name_prefix='cli_test_generic_update')
    def test_resource_generic_update(self, resource_group):
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
            'app': 'clirescreateweb2',
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

    @ResourceGroupPreparer(name_prefix='cli_test_tag_update_by_patch', location='westus')
    def test_tag_update_by_patch(self, resource_group, resource_group_location):

        # Test Microsoft.RecoveryServices/vaults
        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30),
            'tag': 'cli-test=test',
            'resource_group_id': '/subscriptions/' + self.get_subscription_id() + '/resourceGroups/' + resource_group
        })

        vault = self.cmd('resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults '
                         '--is-full-object -p "{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",'
                         '\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
                         checks=self.check('name', '{vault}')).get_output_in_json()
        self.kwargs['vault_id'] = vault['id']
        self.cmd('resource tag --ids {vault_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))
        self.cmd('resource tag --ids {vault_id} --tags', checks=self.check('tags', {}))

        self.cmd('resource delete --id {vault_id}', checks=self.is_empty())

        # Test Microsoft.Resources/resourceGroups
        self.cmd('resource tag --ids {resource_group_id} --tags {tag}',
                 checks=self.check('tags', {'cli-test': 'test'}))

        # Test Microsoft.ContainerRegistry/registries/webhooks
        self.kwargs.update({
            'registry_name': self.create_random_name('clireg', 20),
            'webhook_name': 'cliregwebhook',
            'rg_loc': resource_group_location,
            'uri': 'http://www.microsoft.com',
            'actions': 'push',
            'sku': 'Standard'
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}')])
        webhook = self.cmd('acr webhook create -n {webhook_name} -r {registry_name} --uri {uri} --actions {actions}',
                           checks=[self.check('name', '{webhook_name}')]).get_output_in_json()
        self.kwargs['webhook_id'] = webhook['id']
        self.cmd('resource tag --ids {webhook_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))
        self.cmd('resource tag --ids {webhook_id} --tags', checks=self.check('tags', {}))

        self.cmd('resource delete --id {webhook_id}', checks=self.is_empty())

        # Test Microsoft.ContainerInstance/containerGroups
        self.kwargs.update({
            'container_group_name': self.create_random_name('clicontainer', 16),
            'image': 'nginx:latest',
        })

        container = self.cmd('container create -g {rg} -n {container_group_name} --image {image}',
                             checks=self.check('name', '{container_group_name}')).get_output_in_json()
        self.kwargs['container_id'] = container['id']
        self.cmd('resource tag --ids {container_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))
        self.cmd('resource tag --ids {container_id} --tags', checks=self.check('tags', {}))

    @ResourceGroupPreparer(name_prefix='cli_test_tag_incrementally', location='westus')
    def test_tag_incrementally(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30),
        })

        resource = self.cmd(
            'resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults --is-full-object -p "{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
            checks=self.check('name', '{vault}')).get_output_in_json()

        self.kwargs['vault_id'] = resource['id']

        self.cmd('resource tag --ids {vault_id} --tags cli-test=test cli-test2=test2', checks=self.check('tags', {'cli-test': 'test', 'cli-test2': 'test2'}))
        self.cmd('resource tag --ids {vault_id} --tags cli-test3=test3 cli-test4=test4', checks=self.check('tags', {'cli-test3': 'test3', 'cli-test4': 'test4'}))

        self.cmd('resource tag --ids {vault_id} --tags cli-test4=test4a cli-test5=test5 -i',
                 checks=self.check('tags', {'cli-test3': 'test3', 'cli-test4': 'test4a', 'cli-test5': 'test5'}))

        with self.assertRaises(CLIError):
            self.cmd('resource tag --ids {vault_id} --tags -i ')
        with self.assertRaises(CLIError):
            self.cmd('resource tag --ids {vault_id} --tags "" -i ')
        self.cmd('resource tag --ids {vault_id} --tags', checks=self.check('tags', {}))

        self.cmd('resource delete --id {vault_id}', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_tag_default_location_scenario', location='westus')
    def test_tag_default_location_scenario(self, resource_group, resource_group_location):

        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30),
            'tag': 'cli-test=test'
        })

        resource = self.cmd(
            'resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults --is-full-object -p '
            '"{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
            checks=self.check('name', '{vault}')).get_output_in_json()

        self.kwargs['vault_id'] = resource['id']

        self.cmd('resource tag --ids {vault_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))

        # Scenarios with default location
        self.cmd('configure --defaults location={loc}')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag}')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} -l westus')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} --l westus')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} --location westus')

        # Scenarios without default location
        self.cmd('configure --defaults location=""')

        self.cmd('resource list --tag {tag}', checks=self.check('[0].id', '{vault_id}'))

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} -l westus')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} --l westus')

        with self.assertRaises(IncorrectUsageError):
            self.cmd('resource list --tag {tag} --location westus')

        self.cmd('resource delete --id {vault_id}', checks=self.is_empty())

    def test_tag_create_or_update_subscription(self):
        subscription_id = '/subscriptions/' + self.get_subscription_id()
        self.utility_tag_create_or_update_scope(resource_id=subscription_id)

    @ResourceGroupPreparer(name_prefix='test_tag_create_or_update_resourcegroup', location='westus')
    def test_tag_create_or_update_resourcegroup(self, resource_group):
        resource_group_id = '/subscriptions/' + self.get_subscription_id() + '/resourceGroups/' + resource_group
        self.utility_tag_create_or_update_scope(resource_id=resource_group_id)

    @ResourceGroupPreparer(name_prefix='test_tag_create_or_update_resource', location='westus')
    def test_tag_create_or_update_resource(self, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30)
        })

        resource = self.cmd(
            'resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults --is-full-object -p "{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
            checks=self.check('name', '{vault}')).get_output_in_json()

        self.utility_tag_create_or_update_scope(resource_id=resource['id'])

    # Utility method to test CreateOrUpdate for Tags within subscription, resource group, and tracked resources.
    def utility_tag_create_or_update_scope(self, resource_id):
        self.kwargs.update({
            'resource_id': resource_id,
            'expected_tags1': 'cliName1=cliValue1 cliName2=cliValue2',
            'expected_tags2': 'cliName1=cliValue1 cliName2='
        })

        # 1. pass in an empty tag set, should throw error
        with self.assertRaises(IncorrectUsageError):
            self.cmd('tag create --resource-id {resource_id} --tags', checks=self.check('tags', {}))

        # 2. pass in a complete tag string
        tag_dict1 = {'cliName1': 'cliValue1', 'cliName2': 'cliValue2'}
        self.cmd('tag create --resource-id {resource_id} --tags {expected_tags1}', checks=[
            self.check('properties.tags', tag_dict1)
        ])

        # 3. pass in one incomplete tag string
        tag_dict2 = {'cliName1': 'cliValue1', 'cliName2': ''}
        self.cmd('tag create --resource-id {resource_id} --tags {expected_tags2}', checks=[
            self.check('properties.tags', tag_dict2)
        ])

        # 4. clean up: delete the existing tags
        self.cmd('tag delete --resource-id {resource_id} -y', checks=self.is_empty())

    def test_tag_update_subscription(self):
        subscription_id = '/subscriptions/' + self.get_subscription_id()
        self.utility_tag_update_scope(resource_id=subscription_id)

    @ResourceGroupPreparer(name_prefix='test_tag_update_resourcegroup', location='westus')
    def test_tag_update_resourcegroup(self, resource_group):
        resource_group_id = '/subscriptions/' + self.get_subscription_id() + '/resourceGroups/' + resource_group
        self.utility_tag_update_scope(resource_id=resource_group_id)

    @ResourceGroupPreparer(name_prefix='test_tag_update_resource', location='westus')
    def test_tag_update_resource(self, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30)
        })

        resource = self.cmd(
            'resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults --is-full-object -p "{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
            checks=self.check('name', '{vault}')).get_output_in_json()

        self.utility_tag_update_scope(resource_id=resource['id'])

    # Utility method to test updating tags on subscription, resource group and tracked resource, including Merge, Replace, and Delete Operation.
    def utility_tag_update_scope(self, resource_id):
        self.kwargs.update({
            'resource_id': resource_id,
            'original_tags': 'cliName1=cliValue1 cliName2=cliValue2',
            'merge_tags': 'cliName1=cliValue1 cliName3=cliValue3',
            'replace_tags': 'cliName1=cliValue1 cliName4=cliValue4',
            'delete_tags': 'cliName4=cliValue4',
            'merge_operation': 'merge',
            'replace_operation': 'replace',
            'delete_operation': 'delete'
        })

        # setup original
        self.cmd('tag create --resource-id {resource_id} --tags {original_tags}')

        # 1. test merge operation
        after_merge_tags_dict = {'cliName1': 'cliValue1', 'cliName2': 'cliValue2', 'cliName3': 'cliValue3'}
        self.cmd('tag update --resource-id {resource_id} --operation {merge_operation} --tags {merge_tags}', checks=[
            self.check('properties.tags', after_merge_tags_dict)
        ])

        # 2. test replace operation
        after_replace_tags_dict = {'cliName1': 'cliValue1', 'cliName4': 'cliValue4'}
        self.cmd('tag update --resource-id {resource_id} --operation {replace_operation} --tags {replace_tags}',
                 checks=[
                     self.check('properties.tags', after_replace_tags_dict)
                 ])

        # 3. test delete operation
        after_delete_tags_dict = {'cliName1': 'cliValue1'}
        self.cmd('tag update --resource-id {resource_id} --operation {delete_operation} --tags {delete_tags}', checks=[
            self.check('properties.tags', after_delete_tags_dict)
        ])

        # 4. clean up: delete the existing tags
        self.cmd('tag delete --resource-id {resource_id} -y', checks=self.is_empty())

    def test_tag_get_subscription(self):
        subscription_id = '/subscriptions/' + self.get_subscription_id()
        self.utility_tag_get_scope(resource_id=subscription_id)

    @ResourceGroupPreparer(name_prefix='test_tag_get_resourcegroup', location='westus')
    def test_tag_get_resourcegroup(self, resource_group):
        resource_group_id = '/subscriptions/' + self.get_subscription_id() + '/resourceGroups/' + resource_group
        self.utility_tag_get_scope(resource_id=resource_group_id)

    @ResourceGroupPreparer(name_prefix='test_tag_get_resource', location='westus')
    def test_tag_get_resource(self, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'vault': self.create_random_name('vault-', 30)
        })

        resource = self.cmd(
            'resource create -g {rg} -n {vault} --resource-type Microsoft.RecoveryServices/vaults --is-full-object -p "{{\\"properties\\":{{}},\\"location\\":\\"{loc}\\",\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
            checks=self.check('name', '{vault}')).get_output_in_json()

        self.utility_tag_get_scope(resource_id=resource['id'])

    # Utility method to test Get for Tags within subscription, resource group and tracked resource.
    def utility_tag_get_scope(self, resource_id):
        self.kwargs.update({
            'resource_id': resource_id,
            'original_tags': 'cliName1=cliValue1 cliName2=cliValue2'
        })

        # setup original
        self.cmd('tag create --resource-id {resource_id} --tags {original_tags}')

        # test get operation
        expected_tags_dict = {'cliName1': 'cliValue1', 'cliName2': 'cliValue2'}
        self.cmd('tag list --resource-id {resource_id}', checks=[
            self.check('properties.tags', expected_tags_dict)
        ])

        # clean up: delete the existing tags
        self.cmd('tag delete --resource-id {resource_id} -y', checks=self.is_empty())


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
            self.check("resourceTypes|[?name=='storageAccounts/blobServices/containers/blobs']|[0].operations[0].isDataAction", True),
        ])


class DeploymentTestAtSubscriptionScope(ScenarioTest):
    def tearDown(self):
        self.cmd('policy assignment delete -n location-lock')
        self.cmd('policy definition delete -n policy2')
        self.cmd('group delete -n cli_test_subscription_level_deployment --yes')

    @AllowLargeResponse(4096)
    def test_subscription_level_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'dn2': self.create_random_name('azure-cli-subscription_level_deployment', 60)
        })

        self.cmd('deployment sub validate --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub validate --location WestUS --template-file "{tf}" --parameters "{params_uri}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment sub create -n {dn} --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment sub list', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment sub list --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment sub show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment sub export -n {dn}', checks=[
        ])

        self.cmd('deployment operation sub list -n {dn}', checks=[
            self.check('length([])', 5)
        ])

        self.cmd('deployment sub create -n {dn2} --location WestUS --template-file "{tf}" --parameters @"{params}" --no-wait')

        self.cmd('deployment sub cancel -n {dn2}')

        self.cmd('deployment sub show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

    @AllowLargeResponse(4096)
    def test_subscription_level_deployment_old_command(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'subscription_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'subscription_level_parameters.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the subscription_level_parameters.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/subscription_level_parameters.json',
            'dn': self.create_random_name('azure-cli-subscription_level_deployment', 60),
            'dn2': self.create_random_name('azure-cli-subscription_level_deployment', 60)
        })

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment validate --location WestUS --template-file "{tf}" --parameters "{params_uri}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment create -n {dn} --location WestUS --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment list', checks=[
            self.check('[0].name', '{dn}'),
        ])
        self.cmd('deployment list --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])
        self.cmd('deployment show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment export -n {dn}', checks=[
        ])

        self.cmd('deployment operation list -n {dn}', checks=[
            self.check('length([])', 5)
        ])

        self.cmd('deployment create -n {dn2} --location WestUS --template-file "{tf}" --parameters @"{params}" --no-wait')

        self.cmd('deployment cancel -n {dn2}')

        self.cmd('deployment show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])


class DeploymentTestAtResourceGroup(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_group_deployment')
    def test_resource_group_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'simple_deploy.json').replace('\\', '\\\\'),
            'tf_invalid': os.path.join(curr_dir, 'simple_deploy_invalid.json').replace('\\', '\\\\'),
            'extra_param_tf': os.path.join(curr_dir, 'simple_extra_param_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'simple_deploy_parameters.json').replace('\\', '\\\\'),
            'params_invalid': os.path.join(curr_dir, 'simple_deploy_parameters_invalid.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'Japanese-characters-tf': os.path.join(curr_dir, 'Japanese-characters-template.json').replace('\\', '\\\\')
        })

        self.cmd('deployment group validate --resource-group {rg} --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group validate --resource-group {rg} --template-file "{Japanese-characters-tf}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt true')
            self.assertTrue("Deployment template validation failed" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}"')
            self.assertTrue("Missing input parameters" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate --resource-group {rg} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt false')
            self.assertTrue("Missing input parameters" in str(err.exception))

        self.cmd('deployment group create --resource-group {rg} -n {dn} --template-file "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt true')
            self.assertTrue("Deployment template validation failed" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}"')
            self.assertTrue("Missing input parameters" in str(err.exception))

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{extra_param_tf}" --parameters @"{params}" --no-prompt false')
            self.assertTrue("Missing input parameters" in str(err.exception))

        json_invalid_info = "Failed to parse '{}', please check whether it is a valid JSON format"

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate -g {rg} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group validate -g {rg} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create -g {rg} -n {dn} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('deployment group create -g {rg} -n {dn} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        self.cmd('deployment group list --resource-group {rg}', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group list --resource-group {rg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment group show --resource-group {rg} -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment group export --resource-group {rg} -n {dn}', checks=[
        ])

        self.cmd('deployment operation group list --resource-group {rg} -n {dn}', checks=[
            self.check('length([])', 2)
        ])

        self.cmd('deployment group create --resource-group {rg} -n {dn2} --template-file "{tf}" --parameters @"{params}" --no-wait')

        self.cmd('deployment group cancel -n {dn2} -g {rg}')

        self.cmd('deployment group show -n {dn2} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])


class DeploymentTestAtManagementGroup(ScenarioTest):

    def test_management_group_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'management_group_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'management_group_level_parameters.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-management-group-deployment', 60),
            'mg': self.create_random_name('azure-cli-management', 30),
            'sub-rg': self.create_random_name('azure-cli-sub-resource-group', 60),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment mg validate --management-group-id {mg} --location WestUS --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[self.check('properties.provisioningState', 'Succeeded'), ])

        self.cmd('deployment mg create --management-group-id {mg} --location WestUS -n {dn} --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[self.check('properties.provisioningState', 'Succeeded'), ])

        self.cmd('deployment mg list --management-group-id {mg}', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment mg list --management-group-id {mg} --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment mg show --management-group-id {mg} -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment mg export --management-group-id {mg} -n {dn}', checks=[
        ])

        self.cmd('deployment operation mg list --management-group-id {mg} -n {dn}', checks=[
            self.check('length([])', 4)
        ])

        self.cmd('deployment mg create --management-group-id {mg} --location WestUS -n {dn2} --template-file "{tf}" '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}" --no-wait')

        self.cmd('deployment mg cancel -n {dn2} --management-group-id {mg}')

        self.cmd('deployment mg show -n {dn2} --management-group-id {mg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

        # clean
        self.cmd('account management-group delete -n {mg}')


# TODO
class DeploymentTestAtTenantScope(ScenarioTest):

    def test_tenant_level_deployment(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'tenant_level_template.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-tenant-level-deployment', 60),
            'mg': self.create_random_name('azure-cli-management-group', 40),
            'dn2': self.create_random_name('azure-cli-resource-group-deployment', 60)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment tenant validate --location WestUS --template-file "{tf}" --parameters targetMG="{mg}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment tenant create --location WestUS -n {dn} --template-file "{tf}" --parameters targetMG="{mg}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
        ])

        self.cmd('deployment tenant list', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment tenant list --filter "provisioningState eq \'Succeeded\'"', checks=[
            self.check('[0].name', '{dn}'),
        ])

        self.cmd('deployment tenant show -n {dn}', checks=[
            self.check('name', '{dn}')
        ])

        self.cmd('deployment tenant export -n {dn}', checks=[
        ])

        self.cmd('deployment operation tenant list -n {dn}', checks=[
            self.check('length([])', 4)
        ])

        self.cmd('deployment tenant create --location WestUS -n {dn2} --template-file "{tf}" --parameters targetMG="{mg}" --no-wait')

        self.cmd('deployment tenant cancel -n {dn2}')

        self.cmd('deployment tenant show -n {dn2}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

        self.cmd('group delete -n cli_tenant_level_deployment --yes')
        self.cmd('account management-group delete -n {mg}')


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
            'tf_invalid': os.path.join(curr_dir, 'simple_deploy_invalid.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\'),
            'error_params': os.path.join(curr_dir, 'test-error-params.json').replace('\\', '\\\\'),
            'params_invalid': os.path.join(curr_dir, 'simple_deploy_parameters_invalid.json').replace('\\', '\\\\'),
            # params-uri below is the raw file url of the test_params.json above
            'params_uri': 'https://raw.githubusercontent.com/Azure/azure-cli/dev/src/azure-cli/azure/cli/command_modules/resource/tests/latest/test-params.json',
            'of': os.path.join(curr_dir, 'test-object.json').replace('\\', '\\\\'),
            'dn': 'azure-cli-deployment',
            'dn2': self.create_random_name('azure-cli-resource-group-deployment2', 60)
        })
        self.kwargs['subnet_id'] = self.cmd('network vnet create -g {rg} -n vnet1 --subnet-name subnet1').get_output_in_json()['newVNet']['subnets'][0]['id']

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters "{params_uri}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        with self.assertRaises(CLIError):
            self.cmd('group deployment validate -g {rg} --template-file "{tf}" --parameters @"{error_params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}"')

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
        self.cmd('group deployment list -g {rg} --filter "provisioningState eq \'Succeeded\'"', checks=[
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

        json_invalid_info = "Failed to parse '{}', please check whether it is a valid JSON format"

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment validate -g {rg} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment validate -g {rg} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment create -g {rg} -n {dn} -f "{tf_invalid}" -p @"{params}"')
            self.assertTrue(json_invalid_info.format('{tf_invalid}') == err.exception)

        with self.assertRaises(CLIError) as err:
            self.cmd('group deployment create -g {rg} -n {dn} -f "{tf}" -p @"{params_invalid}"')
            self.assertTrue(json_invalid_info.format('{params_invalid}') in err.exception)

        self.cmd('group deployment create -g {rg} -n {dn2} --template-file "{tf}" --parameters @"{params}" --parameters subnetId="{subnet_id}" --parameters backendAddressPools=@"{of}" --no-wait')

        self.cmd('group deployment cancel -n {dn2} -g {rg}')

        self.cmd('group deployment show -n {dn2} -g {rg}', checks=[
            self.check('properties.provisioningState', 'Canceled')
        ])

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_with_large_params')
    @AllowLargeResponse()
    def test_group_deployment_with_large_params(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'large_tf': os.path.join(curr_dir, 'test-largesize-template.json').replace('\\', '\\\\'),
            'large_params': os.path.join(curr_dir, 'test-largesize-parameters.json').replace('\\', '\\\\'),
            'app_name': self.create_random_name('cli', 30)
        })

        self.cmd('group deployment validate -g {rg} --template-file "{large_tf}" --parameters @"{large_params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment validate -g {rg} --template-file "{large_tf}" --parameters "{large_params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {rg} --template-file "{large_tf}" --parameters @"{large_params}" --parameters function-app-name="{app_name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
        ])

        self.cmd('group deployment create -g {rg} --template-file "{large_tf}" --parameters "{large_params}" --parameters function-app-name="{app_name}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}')
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
            self.check('properties.templateLink.uri', '{tf}'),
        ]).get_output_in_json()['name']

        self.cmd('group deployment show -g {rg} -n {dn}',
                 checks=self.check('name', '{dn}'))

        self.cmd('group deployment delete -g {rg} -n {dn}')
        self.cmd('group deployment list -g {rg}',
                 checks=self.is_empty())

        self.kwargs['dn'] = self.cmd('deployment group create -g {rg} --template-uri "{tf}" --parameters @"{params}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{rg}'),
            self.check('properties.templateLink.uri', '{tf}'),
        ]).get_output_in_json()['name']

        self.cmd('deployment group show -g {rg} -n {dn}',
                 checks=self.check('name', '{dn}'))

        self.cmd('deployment group delete -g {rg} -n {dn}')
        self.cmd('deployment group list -g {rg}',
                 checks=self.is_empty())


class DeploymentWhatIfAtResourceGroupScopeTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_what_if')
    def test_resource_group_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'storage_account_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'storage_account_deploy_parameters.json').replace('\\', '\\\\'),
        })

        deployment_output = self.cmd('deployment group create --resource-group {rg} --template-file "{tf}"').get_output_in_json()
        self.kwargs['storage_account_id'] = deployment_output['properties']['outputs']['storageAccountId']['value']

        self.cmd('deployment group what-if --resource-group {rg} --template-file "{tf}" --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{storage_account_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].before", 'Standard_LRS'),
            self.check("changes[?resourceId == '{storage_account_id}'] | [0].delta[?path == 'sku.name'] | [0].after", 'Standard_GRS')
        ])


class DeploymentWhatIfAtSubscriptionScopeTest(ScenarioTest):
    def test_subscription_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'policy_definition_deploy.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'policy_definition_deploy_parameters.json').replace('\\', '\\\\'),
        })

        deployment_output = self.cmd('deployment sub create --location westus --template-file "{tf}"').get_output_in_json()
        self.kwargs['policy_definition_id'] = deployment_output['properties']['outputs']['policyDefinitionId']['value']

        self.cmd('deployment sub what-if --location westus --template-file "{tf}" --parameters "{params}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("changes[?resourceId == '{policy_definition_id}'].changeType | [0]", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].propertyChangeType", 'Modify'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].before", 'northeurope'),
            self.check("changes[?resourceId == '{policy_definition_id}'] | [0].delta[?path == 'properties.policyRule.if.equals'] | [0].after", 'westeurope'),
        ])


class DeploymentWhatIfAtManagementGroupTest(ScenarioTest):
    def test_management_group_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'management_group_level_template.json').replace('\\', '\\\\'),
            'params': os.path.join(curr_dir, 'management_group_level_parameters.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-management-group-deployment', 60),
            'mg': self.create_random_name('azure-cli-management', 30),
            'sub-rg': self.create_random_name('azure-cli-sub-resource-group', 60),
            'storage-account-name': self.create_random_name('armbuilddemo', 20)
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment mg what-if --management-group-id {mg} --location WestUS --template-file "{tf}" --no-pretty-print '
                 '--parameters @"{params}" --parameters targetMG="{mg}" --parameters nestedRG="{sub-rg}" '
                 '--parameters storageAccountName="{storage-account-name}"',
                 checks=[
                     self.check('status', 'Succeeded'),
                     self.check("length(changes)", 4),
                     self.check("changes[0].changeType", "Create"),
                     self.check("changes[1].changeType", "Create"),
                     self.check("changes[2].changeType", "Create"),
                     self.check("changes[3].changeType", "Create"),
                 ])


class DeploymentWhatIfAtTenantScopeTest(ScenarioTest):
    def test_tenant_level_what_if(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'tenant_level_template.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('azure-cli-tenant-level-deployment', 60),
            'mg': self.create_random_name('azure-cli-management-group', 40),
        })

        self.cmd('account management-group create --name {mg}', checks=[])

        self.cmd('deployment tenant what-if --location WestUS --template-file "{tf}" --parameters targetMG="{mg}" --no-pretty-print', checks=[
            self.check('status', 'Succeeded'),
            self.check("length(changes)", 3),
            self.check("changes[0].changeType", "Create"),
            self.check("changes[1].changeType", "Create"),
            self.check("changes[2].changeType", "Create"),
        ])


class DeploymentScriptsTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts')
    def test_list_all_deployment_scripts(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        count = 0
        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", count))

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        count += 1

        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", count))

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts')
    def test_show_deployment_script(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        self.cmd("deployment-scripts show --resource-group {resource_group} --name {deployment_script_name}",
                 checks=self.check('name', '{deployment_script_name}'))

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts')
    def test_show_deployment_script_logs(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        deployment_script_logs = self.cmd("deployment-scripts show-log --resource-group {resource_group} --name {deployment_script_name}").get_output_in_json()

        self.assertTrue(deployment_script_logs['value'] is not None)

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_scripts')
    def test_delete_deployment_script(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'deployment_script_name': self.create_random_name('script', 20),
            'deployment_name': self.create_random_name('ds', 20),
            'resource_group': resource_group,
            'template_file': os.path.join(curr_dir, 'deployment-scripts-deploy.json').replace('\\', '\\\\'),
        })

        self.cmd('deployment group create -g {resource_group} -n {deployment_name} --template-file "{template_file}" --parameters scriptName={deployment_script_name}', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{resource_group}'),
        ])

        # making sure it exists first
        self.cmd("deployment-scripts show --resource-group {resource_group} --name {deployment_script_name}",
                 checks=self.check('name', '{deployment_script_name}'))

        self.cmd("deployment-scripts delete --resource-group {resource_group} --name {deployment_script_name} --yes")

        self.cmd('deployment-scripts list',
                 checks=self.check("length([?name=='{deployment_script_name}'])", 0))


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


class FeatureScenarioTest(ScenarioTest):

    @AllowLargeResponse(8192)
    def test_feature_list(self):
        self.cmd('feature list', checks=self.check("length([?name=='Microsoft.Xrm/uxdevelopment'])", 1))

        self.cmd('feature list --namespace Microsoft.Network',
                 checks=self.check("length([?name=='Microsoft.Network/SkipPseudoVipGeneration'])", 1))

        # Once a feature goes GA , it will be removed from the feature list. Once that happens, use other ones to test
        self.cmd('feature show --namespace Microsoft.Network -n AllowLBPreview')

    @AllowLargeResponse(8192)
    def test_feature_unregister(self):
        self.cmd('feature unregister --namespace Microsoft.Network --name AllowLBPreview', checks=self.check('properties.state', 'Unregistered'))


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

        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --params "{params}"', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('sku.name', 'A0'),
            self.check('sku.tier', 'Free')
        ])

        # create a policy assignment with not scopes and standard sku
        self.kwargs.update({
            'vnet': self.create_random_name('azurecli-test-policy-vnet', 40),
            'subnet': self.create_random_name('azurecli-test-policy-subnet', 40),
            'sub': self.get_subscription_id()
        })

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}')
        self.kwargs['notscope'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks'.format(**self.kwargs)

        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --not-scopes {notscope} --params "{params}" --sku standard', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('sku.name', 'A1'),
            self.check('sku.tier', 'Standard'),
            self.check('notScopes[0]', '{notscope}')
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

    def applyPolicyAtScope(self, scope, policyId, enforcementMode='Default'):
        # create a policy assignment at the given scope
        self.kwargs.update({
            'pol': policyId,
            'pan': self.create_random_name('cli-test-polassg', 24),   # limit is 24 characters at MG scope
            'padn': self.create_random_name('test_assignment', 20),
            'scope': scope,
            'em': enforcementMode
        })

        self.cmd('policy assignment create --policy {pol} -n {pan} --display-name {padn} --params "{params}" --scope {scope} --enforcement-mode {em}', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('sku.name', 'A0'),
            self.check('sku.tier', 'Free'),
            self.check('enforcementMode', '{em}')
        ])

        # ensure the policy assignment shows up in the list result
        self.cmd('policy assignment list --scope {scope}', checks=self.check("length([?name=='{pan}'])", 1))

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
            'mode': 'Indexed',
            'metadata': 'test',
            'updated_metadata': 'test2',
        })

        if (management_group):
            self.kwargs.update({'mg': management_group})
        if (subscription):
            self.kwargs.update({'sub': subscription})

        # create a policy
        cmd = self.cmdstring('policy definition create -n {pn} --rules "{rf}" --params "{pdf}" --display-name {pdn} --description {desc} --mode {mode} --metadata category={metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{pn}'),
            self.check('displayName', '{pdn}'),
            self.check('description', '{desc}'),
            self.check('mode', '{mode}'),
            self.check('metadata.category', '{metadata}')
        ])

        # update it
        self.kwargs['desc'] = self.kwargs['desc'] + '_new'
        self.kwargs['pdn'] = self.kwargs['pdn'] + '_new'

        cmd = self.cmdstring('policy definition update -n {pn} --description {desc} --display-name {pdn} --metadata category={updated_metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('description', '{desc}'),
            self.check('displayName', '{pdn}'),
            self.check('metadata.category', '{updated_metadata}')
        ])

        # update it with new parameters and a new rule
        self.kwargs['pdf'] = os.path.join(curr_dir, 'sample_policy_param_def_2.json').replace('\\', '\\\\')
        self.kwargs['rf'] = os.path.join(curr_dir, 'sample_policy_rule_2.json').replace('\\', '\\\\')

        cmd = self.cmdstring('policy definition update -n {pn} --description {desc} --display-name {pdn} --metadata category=test2 --params "{pdf}" --rules "{rf}"', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('description', '{desc}'),
            self.check('displayName', '{pdn}'),
            self.check('metadata.category', '{updated_metadata}'),
            self.check('parameters.allowedLocations.metadata.displayName', 'Allowed locations 2'),
            self.check('policyRule.then.effect', 'audit')
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
            self.applyPolicyAtScope('/subscriptions/{sub}'.format(sub=subscription), policy, 'DoNotEnforce')
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
            'dpn': self.create_random_name('azure-cli-test-data-policy', 30),
            'dpdn': self.create_random_name('test_data_policy', 20),
            'dp_desc': 'desc_for_test_data_policy_123',
            'dp_mode': 'Microsoft.DataCatalog.Data',
            'psn': self.create_random_name('azure-cli-test-policyset', 30),
            'psdn': self.create_random_name('test_policyset', 20),
            'ps_desc': 'desc_for_test_policyset_123',
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'dprf': os.path.join(curr_dir, 'sample_data_policy_rule.json').replace('\\', '\\\\'),
            'psf': os.path.join(curr_dir, 'sample_policy_set.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\'),
            'metadata': 'test',
            'updated_metadata': 'test2',
        })
        if (management_group):
            self.kwargs.update({'mg': management_group})
        if (subscription):
            self.kwargs.update({'sub': subscription})

        time.sleep(60)

        # create a policy
        cmd = self.cmdstring('policy definition create -n {pn} --rules "{rf}" --params "{pdf}" --display-name {pdn} --description {desc}', management_group, subscription)
        policy = self.cmd(cmd).get_output_in_json()

        # create a data policy
        cmd = self.cmdstring('policy definition create -n {dpn} --rules "{dprf}" --mode {dp_mode} --display-name {dpdn} --description {dp_desc}', management_group, subscription)
        datapolicy = self.cmd(cmd).get_output_in_json()

        # create a policy set
        policyset = get_file_json(self.kwargs['psf'])
        policyset[0]['policyDefinitionId'] = policy['id']
        policyset[1]['policyDefinitionId'] = datapolicy['id']
        with open(os.path.join(curr_dir, 'sample_policy_set.json'), 'w') as outfile:
            json.dump(policyset, outfile)

        cmd = self.cmdstring('policy set-definition create -n {psn} --definitions @"{psf}" --display-name {psdn} --description {ps_desc} --metadata category={metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}'),
            self.check('description', '{ps_desc}'),
            self.check('metadata.category', '{metadata}')
        ])

        # update it
        self.kwargs['ps_desc'] = self.kwargs['ps_desc'] + '_new'
        self.kwargs['psdn'] = self.kwargs['psdn'] + '_new'

        cmd = self.cmdstring('policy set-definition update -n {psn} --display-name {psdn} --description {ps_desc} --metadata category={updated_metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('description', '{ps_desc}'),
            self.check('displayName', '{psdn}'),
            self.check('metadata.category', '{updated_metadata}')
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

            # ensure the assignment appears in the list results
            self.cmd('policy assignment list --resource-group {rg}', checks=self.check("length([?name=='{pan}'])", 1))

            # delete the assignment and validate it's gone
            self.cmd('policy assignment delete -n {pan} -g {rg}')
            self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))

        # delete the policy set
        cmd = self.cmdstring('policy set-definition delete -n {psn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 0))

        # create a parameterized policy set
        self.kwargs['psf'] = os.path.join(curr_dir, 'sample_policy_set_parameterized.json').replace('\\', '\\\\')
        policyset = get_file_json(self.kwargs['psf'])
        policyset[0]['policyDefinitionId'] = policy['id']
        policyset[1]['policyDefinitionId'] = datapolicy['id']
        with open(os.path.join(curr_dir, 'sample_policy_set_parameterized.json'), 'w') as outfile:
            json.dump(policyset, outfile)

        cmd = self.cmdstring('policy set-definition create -n {psn} --definitions @"{psf}" --display-name {psdn} --description {ps_desc} --params "{pdf}" --metadata category={updated_metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}'),
            self.check('description', '{ps_desc}'),
            self.check('policyDefinitions[0].parameters.allowedLocations.value', "[parameters('allowedLocations')]"),
            self.check('parameters.allowedLocations.type', 'Array'),
            self.check('metadata.category', '{updated_metadata}')
        ])

        # update the parameters on the policy set
        self.kwargs['pdf'] = os.path.join(curr_dir, 'sample_policy_param_def_2.json').replace('\\', '\\\\')

        cmd = self.cmdstring('policy set-definition update -n {psn} --params "{pdf}" --metadata category={updated_metadata}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('parameters.allowedLocations.metadata.displayName', 'Allowed locations 2'),
            self.check('metadata.category', '{updated_metadata}')
        ])

        # delete the parameterized policy set
        cmd = self.cmdstring('policy set-definition delete -n {psn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)

        # delete the data policy
        cmd = self.cmdstring('policy definition delete -n {dpn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)

        # ensure the policy is gone when run live.
        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))
        self.cmd(cmd, checks=self.check("length([?name=='{dpn}'])", 0))

    @ResourceGroupPreparer(name_prefix='cli_test_policy')
    @AllowLargeResponse(8192)
    def test_resource_policy_default(self, resource_group):
        self.resource_policy_operations(resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_policy_identity')
    @AllowLargeResponse(8192)
    def test_resource_policy_identity(self, resource_group, resource_group_location):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d',
            'sub': self.get_subscription_id(),
            'location': resource_group_location,
            'em': 'DoNotEnforce'
        })

        with self.assertRaises(IncorrectUsageError):
            self.cmd('policy assignment create --policy \'test/error_policy\' -n {pan} -g {rg} --location {location} --assign-identity --enforcement-mode {em}')

        # create a policy assignment with managed identity using a built in policy definition
        assignmentIdentity = self.cmd('policy assignment create --policy {bip} -n {pan} -g {rg} --location {location} --assign-identity --enforcement-mode {em}', checks=[
            self.check('name', '{pan}'),
            self.check('location', '{location}'),
            self.check('identity.type', 'SystemAssigned'),
            self.exists('identity.principalId'),
            self.exists('identity.tenantId')
        ]).get_output_in_json()['identity']

        # ensure managed identity details are retrievable directly through 'policy assignment identity' commands
        self.cmd('policy assignment identity show -n {pan} -g {rg}', checks=[
            self.check('type', assignmentIdentity['type']),
            self.check('principalId', assignmentIdentity['principalId']),
            self.check('tenantId', assignmentIdentity['tenantId'])
        ])

        # remove the managed identity and ensure it is removed when retrieving the policy assignment
        self.cmd('policy assignment identity remove -n {pan} -g {rg}', checks=[
            self.check('type', 'None')
        ])
        self.cmd('policy assignment show -n {pan} -g {rg}', checks=[
            self.check('name', '{pan}'),
            self.check('identity.type', 'None')
        ])

        # add an identity using 'identity assign'
        self.cmd('policy assignment identity assign -n {pan} -g {rg}', checks=[
            self.check('type', 'SystemAssigned'),
            self.exists('principalId'),
            self.exists('tenantId')
        ])
        self.cmd('policy assignment show -n {pan} -g {rg}', checks=[
            self.check('name', '{pan}'),
            self.check('identity.type', 'SystemAssigned'),
            self.exists('identity.principalId'),
            self.exists('identity.tenantId')
        ])

        self.cmd('policy assignment identity remove -n {pan} -g {rg}', checks=[
            self.check('type', 'None')
        ])

        # create a role assignment for the identity using --assign-identity
        self.kwargs.update({
            'idScope': '/subscriptions/{sub}/resourceGroups/{rg}'.format(**self.kwargs),
            'idRole': 'Reader'
        })
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            assignmentIdentity = self.cmd('policy assignment create --policy {bip} -n {pan} -g {rg} --location {location} --assign-identity --identity-scope {idScope} --role {idRole}', checks=[
                self.check('name', '{pan}'),
                self.check('location', '{location}'),
                self.check('identity.type', 'SystemAssigned'),
                self.exists('identity.principalId'),
                self.exists('identity.tenantId')
            ]).get_output_in_json()['identity']

        self.kwargs['principalId'] = assignmentIdentity['principalId']
        self.cmd('role assignment list --resource-group {rg} --role {idRole}', checks=[
            self.check("length([?principalId == '{principalId}'])", 1),
            self.check("[?principalId == '{principalId}'].roleDefinitionName | [0]", '{idRole}')
        ])
        self.cmd('policy assignment identity remove -n {pan} -g {rg}', checks=[
            self.check('type', 'None')
        ])

        # create a role assignment for the identity using 'identity assign'
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            assignmentIdentity = self.cmd('policy assignment identity assign -n {pan} -g {rg} --identity-scope {idScope} --role {idRole}', checks=[
                self.check('type', 'SystemAssigned'),
                self.exists('principalId'),
                self.exists('tenantId')
            ]).get_output_in_json()

        self.kwargs['principalId'] = assignmentIdentity['principalId']
        self.cmd('role assignment list --resource-group {rg} --role {idRole}', checks=[
            self.check("length([?principalId == '{principalId}'])", 1),
            self.check("[?principalId == '{principalId}'].roleDefinitionName | [0]", '{idRole}')
        ])

        self.cmd('policy assignment delete -n {pan} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_policy_management_group')
    @AllowLargeResponse(4096)
    def test_resource_policy_management_group(self, resource_group):
        management_group_name = self.create_random_name('cli-test-mgmt-group', 30)
        self.cmd('account management-group create -n ' + management_group_name)
        try:
            self.resource_policy_operations(resource_group, management_group_name)

            # Attempt to get a policy definition at an invalid management group scope
            with self.assertRaises(IncorrectUsageError):
                self.cmd(self.cmdstring('policy definition show -n "/providers/microsoft.management/managementgroups/myMg/providers/microsoft.authorization/missingsegment"'))
        finally:
            self.cmd('account management-group delete -n ' + management_group_name)

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
                self.resource_policy_operations(resource_group, None, 'f67cc918-f64f-4c3f-aa24-a855465f9d41')
        else:
            self.resource_policy_operations(resource_group, None, 'f67cc918-f64f-4c3f-aa24-a855465f9d41')

    @ResourceGroupPreparer(name_prefix='cli_test_policyset')
    @AllowLargeResponse(4096)
    def test_resource_policyset_default(self, resource_group):
        self.resource_policyset_operations(resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_policyset_management_group')
    @AllowLargeResponse(4096)
    def test_resource_policyset_management_group(self, resource_group):
        management_group_name = self.create_random_name('cli-test-mgmt-group', 30)
        self.cmd('account management-group create -n ' + management_group_name)
        try:
            self.resource_policyset_operations(resource_group, management_group_name)
        finally:
            self.cmd('account management-group delete -n ' + management_group_name)

    @record_only()
    @ResourceGroupPreparer(name_prefix='cli_test_policyset_subscription_id')
    @AllowLargeResponse(4096)
    def test_resource_policyset_subscription_id(self, resource_group):
        # under playback, we mock it so the subscription id will be '00000000...' and it will match
        # the same sanitized value in the recording
        if not self.in_recording:
            with mock.patch('azure.cli.command_modules.resource.custom._get_subscription_id_from_subscription',
                            return_value=MOCKED_SUBSCRIPTION_ID):
                self.resource_policyset_operations(resource_group, None, '0b1f6471-1bf0-4dda-aec3-cb9272f09590')
        else:
            self.resource_policyset_operations(resource_group, None, '0b1f6471-1bf0-4dda-aec3-cb9272f09590')

    @ResourceGroupPreparer(name_prefix='cli_test_policyset_grouping')
    @AllowLargeResponse(4096)
    def test_resource_policyset_grouping(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'pn': self.create_random_name('azure-cli-test-policy', 30),
            'pdn': self.create_random_name('test_policy', 20),
            'psn': self.create_random_name('azure-cli-test-policyset', 30),
            'psdn': self.create_random_name('test_policyset', 20),
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'psf': os.path.join(curr_dir, 'sample_policy_set_grouping.json').replace('\\', '\\\\'),
            'pgf': os.path.join(curr_dir, 'sample_policy_groups_def.json').replace('\\', '\\\\'),
            'pgf2': os.path.join(curr_dir, 'sample_policy_groups_def2.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\')
        })

        # create a policy
        policy = self.cmd('policy definition create -n {pn} --rules "{rf}" --params "{pdf}" --display-name {pdn}').get_output_in_json()

        # create a policy set
        policyset = get_file_json(self.kwargs['psf'])
        policyset[0]['policyDefinitionId'] = policy['id']
        policyset[1]['policyDefinitionId'] = policy['id']
        with open(os.path.join(curr_dir, 'sample_policy_set_grouping.json'), 'w') as outfile:
            json.dump(policyset, outfile)

        self.cmd('policy set-definition create -n {psn} --definitions @"{psf}" --display-name {psdn} --definition-groups @"{pgf}"', checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}'),
            self.check('length(policyDefinitionGroups)', 2),
            self.check("length(policyDefinitionGroups[?name=='group1'])", 1),
            self.check("length(policyDefinitionGroups[?name=='group2'])", 1),
            self.check('length(policyDefinitions[0].groupNames)', 2),
            self.check('length(policyDefinitions[1].groupNames)', 1)
        ])

        # update the groups
        groups = get_file_json(self.kwargs['pgf'])
        groups[0]['displayName'] = "Updated display name"
        with open(os.path.join(curr_dir, 'sample_policy_groups_def2.json'), 'w') as outfile:
            json.dump(groups, outfile)

        self.cmd('policy set-definition update -n {psn} --definition-groups @"{pgf2}"', checks=[
            self.check('length(policyDefinitionGroups)', 2),
            self.check("length(policyDefinitionGroups[?name=='group1'])", 1),
            self.check("length(policyDefinitionGroups[?name=='group2'])", 1),
            self.check("length(policyDefinitionGroups[?displayName=='Updated display name\'])", 1)
        ])

        # show it
        self.cmd('policy set-definition show -n {psn}',
                 checks=self.check('length(policyDefinitionGroups)', 2))

        # delete the policy set
        self.cmd('policy set-definition delete -n {psn}')
        time.sleep(10)  # ensure the policy is gone when run live.

        self.cmd('policy set-definition list',
                 checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        self.cmd('policy definition delete -n {pn}')

    @AllowLargeResponse(8192)
    def test_show_built_in_policy(self):
        # get the list of builtins, then retrieve each via show and validate the results match
        results = self.cmd('policy definition list --query "[?policyType==\'BuiltIn\']"').get_output_in_json()
        for i, result in enumerate(results):
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

    # Because the policy assignment name is generated randomly and automatically, the value of each run is different,
    # so it cannot be rerecord.
    @ResourceGroupPreparer(name_prefix='cli_test_resource_create_policy_assignment_random')
    @AllowLargeResponse(4096)
    @live_only()
    def test_resource_create_policy_assignment_random(self, resource_group, management_group=None, subscription=None):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        self.kwargs.update({
            'pn': self.create_random_name('azure-cli-test-policy', 30),
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\'),
            'pdn': self.create_random_name('test_policy', 20),
            'desc': 'desc_for_test_policy_123',
            'padn': self.create_random_name('test_assignment', 20),
            'params': os.path.join(curr_dir, 'sample_policy_param.json').replace('\\', '\\\\')
        })

        self.cmd('policy definition create -n {pn} --rules "{rf}" --params "{pdf}" --display-name {pdn} --description {desc}', management_group, subscription)

        self.kwargs['pan_random'] = self.cmd('policy assignment create --policy {pn} --display-name {padn} -g {rg} --params "{params}"', checks=[
            self.check('displayName', '{padn}'),
            self.check('sku.name', 'A0'),
            self.check('sku.tier', 'Free'),
        ]).get_output_in_json()['name']

        # clean policy assignment and policy
        self.cmd('policy assignment delete -n {pan_random} -g {rg}')
        self.cmd('policy assignment list --disable-scope-strict-match',
                 checks=self.check("length([?name=='{pan_random}'])", 0))
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        time.sleep(10)
        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))


class ManagedAppDefinitionScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_managedappdef(self, resource_group):

        self.kwargs.update({
            'upn': self.create_random_name('testuser', 15) + '@azuresdkteam.onmicrosoft.com',
            'sub': self.get_subscription_id()
        })

        user_principal = self.cmd(
            'ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}').get_output_in_json()
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change
        principal_id = user_principal['objectId']

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            role_assignment = self.cmd(
                'role assignment create --assignee {upn} --role contributor --scope "/subscriptions/{sub}" ').get_output_in_json()
        from msrestazure.tools import parse_resource_id
        role_definition_id = parse_resource_id(role_assignment['roleDefinitionId'])['name']

        self.kwargs.update({
            'loc': 'eastus',
            'adn': self.create_random_name('testappdefname', 20),
            'addn': self.create_random_name('test_appdef', 20),
            'ad_desc': 'test_appdef_123',
            'uri': 'https://raw.githubusercontent.com/Azure/azure-managedapp-samples/master/Managed%20Application%20Sample%20Packages/201-managed-storage-account/managedstorage.zip',
            'auth': principal_id + ':' + role_definition_id,
            'lock': 'None'
        })

        # create a managedapp definition
        self.kwargs['ad_id'] = self.cmd('managedapp definition create -n {adn} --package-file-uri {uri} --display-name {addn} --description {ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{ad_desc}'),
            self.check('authorizations[0].principalId', principal_id),
            self.check('authorizations[0].roleDefinitionId', role_definition_id),
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
            self.check('authorizations[0].principalId', principal_id),
            self.check('authorizations[0].roleDefinitionId', role_definition_id),
            self.check('artifacts[0].name', 'ApplicationResourceTemplate'),
            self.check('artifacts[0].type', 'Template'),
            self.check('artifacts[1].name', 'CreateUiDefinition'),
            self.check('artifacts[1].type', 'Custom')
        ])

        self.cmd('managedapp definition delete -g {rg} -n {adn}')
        self.cmd('managedapp definition list -g {rg}', checks=self.is_empty())

        self.cmd('role assignment delete --assignee {upn} --role contributor ')
        self.cmd('ad user delete --upn-or-object-id {upn}')

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_managedappdef_inline(self, resource_group):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'upn': self.create_random_name('testuser', 15) + '@azuresdkteam.onmicrosoft.com',
            'sub': self.get_subscription_id()
        })

        user_principal = self.cmd(
            'ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}').get_output_in_json()
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change
        principal_id = user_principal['objectId']

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            role_assignment = self.cmd(
                'role assignment create --assignee {upn} --role contributor --scope "/subscriptions/{sub}" ').get_output_in_json()
        from msrestazure.tools import parse_resource_id
        role_definition_id = parse_resource_id(role_assignment['roleDefinitionId'])['name']

        self.kwargs.update({
            'loc': 'eastus',
            'adn': self.create_random_name('testappdefname', 20),
            'addn': self.create_random_name('test_appdef', 20),
            'ad_desc': 'test_appdef_123',
            'auth': principal_id + ':' + role_definition_id,
            'lock': 'None',
            'ui_file': os.path.join(curr_dir, 'sample_create_ui_definition.json').replace('\\', '\\\\'),
            'main_file': os.path.join(curr_dir, 'sample_main_template.json').replace('\\', '\\\\')
        })

        # create a managedapp definition with inline params for create-ui-definition and main-template
        self.kwargs['ad_id'] = self.cmd('managedapp definition create -n {adn} --create-ui-definition @"{ui_file}" --main-template @"{main_file}" --display-name {addn} --description {ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{ad_desc}'),
            self.check('authorizations[0].principalId', principal_id),
            self.check('authorizations[0].roleDefinitionId', role_definition_id),
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
            self.check('authorizations[0].principalId', principal_id),
            self.check('authorizations[0].roleDefinitionId', role_definition_id),
            self.check('artifacts[0].name', 'ApplicationResourceTemplate'),
            self.check('artifacts[0].type', 'Template'),
            self.check('artifacts[1].name', 'CreateUiDefinition'),
            self.check('artifacts[1].type', 'Custom')
        ])

        self.cmd('managedapp definition delete -g {rg} -n {adn}')
        self.cmd('managedapp definition list -g {rg}', checks=self.is_empty())

        self.cmd('role assignment delete --assignee {upn} --role contributor ')
        self.cmd('ad user delete --upn-or-object-id {upn}')


class ManagedAppScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_managedapp(self, resource_group):

        self.kwargs.update({
            'upn': self.create_random_name('testuser', 15) + '@azuresdkteam.onmicrosoft.com',
            'sub': self.get_subscription_id()
        })

        user_principal = self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}').get_output_in_json()
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            role_assignment = self.cmd('role assignment create --assignee {upn} --role contributor --scope "/subscriptions/{sub}" ').get_output_in_json()
        from msrestazure.tools import parse_resource_id
        role_definition_id = parse_resource_id(role_assignment['roleDefinitionId'])['name']

        self.kwargs.update({
            'loc': 'westcentralus',
            'adn': 'testappdefname',
            'addn': 'test_appdef_123',
            'ad_desc': 'test_appdef_123',
            'uri': 'https://github.com/Azure/azure-managedapp-samples/raw/master/Managed%20Application%20Sample%20Packages/201-managed-storage-account/managedstorage.zip',
            'auth': user_principal['objectId'] + ':' + role_definition_id,
            'lock': 'None',
            'rg': resource_group
        })

        self.kwargs['ad_id'] = self.cmd('managedapp definition create -n {adn} --package-file-uri {uri} --display-name {addn} --description {ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}').get_output_in_json()['id']

        # create a managedapp
        self.kwargs.update({
            'man': 'mymanagedapp',
            'ma_loc': 'westcentralus',
            'ma_kind': 'servicecatalog',
            'ma_rg': self.create_random_name('climanagedapp', 25),
            'param': '\'{\"storageAccountNamePrefix\": {\"value\": \"mytest\"}, \"storageAccountType\": {\"value\": \"Standard_LRS\"}}\''
        })
        self.kwargs['ma_rg_id'] = '/subscriptions/{sub}/resourceGroups/{ma_rg}'.format(**self.kwargs)

        self.kwargs['ma_id'] = self.cmd('managedapp create -n {man} -g {rg} -l {ma_loc} --kind {ma_kind} -m {ma_rg_id} -d {ad_id} --parameters {param} --tags "key=val" ', checks=[
            self.check('name', '{man}'),
            self.check('type', 'Microsoft.Solutions/applications'),
            self.check('kind', 'servicecatalog'),
            self.check('managedResourceGroupId', '{ma_rg_id}'),
            self.check('tags', {'key': 'val'})
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

        self.cmd('role assignment delete --assignee {upn} --role contributor ')
        self.cmd('ad user delete --upn-or-object-id {upn}')


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

        with self.assertRaises(CLIError):
            self.cmd('group deployment validate -g {rg1} --template-file "{tf}" --parameters CrossRg=SomeRandomRG StorageAccountName1={sa1} StorageAccountName2={sa2}')

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


class CrossTenantDeploymentScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_cross_tenant_deploy', location='eastus')
    def test_group_deployment_cross_tenant(self, resource_group):
        # Prepare Network Interface
        self.kwargs.update({
            'vm_rg': resource_group,
            'vnet': 'clivmVNET',
            'subnet': 'clivmSubnet',
            'nsg': 'clivmNSG',
            'ip': 'clivmPublicIp',
            'nic': 'clivmVMNic'
        })
        self.cmd('network vnet create -n {vnet} -g {vm_rg} --subnet-name {subnet}')
        self.cmd('network nsg create -n {nsg} -g {vm_rg}')
        self.cmd('network public-ip create -n {ip} -g {vm_rg} --allocation-method Dynamic')
        res = self.cmd('network nic create -n {nic} -g {vm_rg} --subnet {subnet} --vnet {vnet} --network-security-group {nsg} --public-ip-address {ip}').get_output_in_json()
        self.kwargs.update({
            'nic_id': res['NewNIC']['id']
        })

        # Prepare SIG in another tenant
        self.kwargs.update({
            'location': 'eastus',
            'vm': self.create_random_name('cli_crosstenantvm', 40),
            'gallery': self.create_random_name('cli_crosstenantgallery', 40),
            'image': self.create_random_name('cli_crosstenantimage', 40),
            'version': '1.1.2',
            'captured': self.create_random_name('cli_crosstenantmanagedimage', 40),
            'aux_sub': '1c638cf4-608f-4ee6-b680-c329e824c3a8',
            'rg': self.create_random_name('cli_test_cross_tenant_rg', 40),
            'aux_tenant': '72f988bf-86f1-41af-91ab-2d7cd011db47'
        })
        self.cmd('group create -g {rg} --location {location} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['rg']))
        self.cmd('sig create -g {rg} --gallery-name {gallery} --subscription {aux_sub}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1 --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))

        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('image create -g {rg} -n {captured} --source {vm} --subscription {aux_sub}')
        res = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1 --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'sig_id': res['id']
        })

        # Cross tenant deploy
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'crosstenant_vm_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('cli-crosstenantdeployment', 40),
            'dn1': self.create_random_name('cli-crosstenantdeployment1', 40),
            'dn2': self.create_random_name('cli-crosstenantdeployment2', 40),
            'dn3': self.create_random_name('cli-crosstenantdeployment3', 40)
        })

        self.cmd('group deployment validate -g {vm_rg} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn1} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn1}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn1}', checks=[
            self.check('name', '{dn1}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn2} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn2}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn2}', checks=[
            self.check('name', '{dn2}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('group deployment create -g {vm_rg} -n {dn3} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn3}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('group deployment show -g {vm_rg} -n {dn3}', checks=[
            self.check('name', '{dn3}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        with self.assertRaises(AssertionError):
            self.cmd('group deployment create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" --aux-subs "{aux_sub}"')

    @ResourceGroupPreparer(name_prefix='cli_test_deployment_group_cross_tenant', location='eastus')
    def test_deployment_group_cross_tenant(self, resource_group):
        # Prepare Network Interface
        self.kwargs.update({
            'vm_rg': resource_group,
            'vnet': 'clivmVNET',
            'subnet': 'clivmSubnet',
            'nsg': 'clivmNSG',
            'ip': 'clivmPublicIp',
            'nic': 'clivmVMNic'
        })
        self.cmd('network vnet create -n {vnet} -g {vm_rg} --subnet-name {subnet}')
        self.cmd('network nsg create -n {nsg} -g {vm_rg}')
        self.cmd('network public-ip create -n {ip} -g {vm_rg} --allocation-method Dynamic')
        res = self.cmd('network nic create -n {nic} -g {vm_rg} --subnet {subnet} --vnet {vnet} --network-security-group {nsg} --public-ip-address {ip}').get_output_in_json()
        self.kwargs.update({
            'nic_id': res['NewNIC']['id']
        })

        # Prepare SIG in another tenant
        self.kwargs.update({
            'location': 'eastus',
            'vm': self.create_random_name('cli_crosstenantvm', 40),
            'gallery': self.create_random_name('cli_crosstenantgallery', 40),
            'image': self.create_random_name('cli_crosstenantimage', 40),
            'version': '1.1.2',
            'captured': self.create_random_name('cli_crosstenantmanagedimage', 40),
            'aux_sub': '1c638cf4-608f-4ee6-b680-c329e824c3a8',
            'rg': self.create_random_name('cli_test_cross_tenant_rg', 40),
            'aux_tenant': '72f988bf-86f1-41af-91ab-2d7cd011db47'
        })
        self.cmd('group create -g {rg} --location {location} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['rg']))
        self.cmd('sig create -g {rg} --gallery-name {gallery} --subscription {aux_sub}', checks=self.check('name', self.kwargs['gallery']))
        self.cmd('sig image-definition create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --os-type linux -p publisher1 -f offer1 -s sku1 --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))
        self.cmd('sig image-definition show -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --subscription {aux_sub}',
                 checks=self.check('name', self.kwargs['image']))

        self.cmd('vm create -g {rg} -n {vm} --image ubuntults --admin-username clitest1 --generate-ssh-key --subscription {aux_sub}')
        self.cmd(
            'vm run-command invoke -g {rg} -n {vm} --command-id RunShellScript --scripts "echo \'sudo waagent -deprovision+user --force\' | at -M now + 1 minutes" --subscription {aux_sub}')
        time.sleep(70)

        self.cmd('vm deallocate -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('vm generalize -g {rg} -n {vm} --subscription {aux_sub}')
        self.cmd('image create -g {rg} -n {captured} --source {vm} --subscription {aux_sub}')
        res = self.cmd(
            'sig image-version create -g {rg} --gallery-name {gallery} --gallery-image-definition {image} --gallery-image-version {version} --managed-image {captured} --replica-count 1 --subscription {aux_sub}').get_output_in_json()
        self.kwargs.update({
            'sig_id': res['id']
        })

        # Cross tenant deploy
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'tf': os.path.join(curr_dir, 'crosstenant_vm_deploy.json').replace('\\', '\\\\'),
            'dn': self.create_random_name('cli-crosstenantdeployment', 40),
            'dn1': self.create_random_name('cli-crosstenantdeployment1', 40),
            'dn2': self.create_random_name('cli-crosstenantdeployment2', 40),
            'dn3': self.create_random_name('cli-crosstenantdeployment3', 40)
        })

        self.cmd('deployment group validate -g {vm_rg} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id}', checks=[
            self.check('properties.provisioningState', 'Succeeded')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn}', checks=[
            self.check('name', '{dn}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn1} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}"', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn1}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn1}', checks=[
            self.check('name', '{dn1}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn2} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-subs "{aux_sub}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn2}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn2}', checks=[
            self.check('name', '{dn2}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        self.cmd('deployment group create -g {vm_rg} -n {dn3} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" -j', checks=[
            self.check('properties.provisioningState', 'Succeeded'),
            self.check('resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group list -g {vm_rg}', checks=[
            self.check('[0].name', '{dn3}'),
            self.check('[0].resourceGroup', '{vm_rg}')
        ])
        self.cmd('deployment group show -g {vm_rg} -n {dn3}', checks=[
            self.check('name', '{dn3}'),
            self.check('resourceGroup', '{vm_rg}')
        ])

        with self.assertRaises(AssertionError):
            self.cmd('deployment group create -g {vm_rg} -n {dn} --template-file "{tf}" --parameters SIG_ImageVersion_id={sig_id} NIC_id={nic_id} --aux-tenants "{aux_tenant}" --aux-subs "{aux_sub}"')


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


class ResourceGroupLocalContextScenarioTest(LocalContextScenarioTest):

    def test_resource_group_local_context(self):
        self.kwargs.update({
            'group1': 'test_local_context_group_1',
            'group2': 'test_local_context_group_2',
            'location': 'eastasia'
        })
        self.cmd('group create -n {group1} -l {location}', checks=[
            self.check('name', self.kwargs['group1']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('group show', checks=[
            self.check('name', self.kwargs['group1']),
            self.check('location', self.kwargs['location'])
        ])
        with self.assertRaisesRegexp(SystemExit, '2'):
            self.cmd('group delete')
        self.cmd('group delete -n {group1} -y')
        self.cmd('group create -n {group2}', checks=[
            self.check('name', self.kwargs['group2']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('group delete -n {group2} -y')


if __name__ == '__main__':
    unittest.main()
