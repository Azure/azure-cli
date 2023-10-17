# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import platform
import shutil
import time
from unittest import mock
import unittest
from pathlib import Path
import logging

from azure.cli.core.parser import IncorrectUsageError, InvalidArgumentValueError
from azure.cli.testsdk.scenario_tests.const import MOCKED_SUBSCRIPTION_ID
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, LiveScenarioTest, ResourceGroupPreparer, StorageAccountPreparer,
                               create_random_name, live_only, record_only)
from azure.cli.testsdk.constants import AUX_SUBSCRIPTION, AUX_TENANT
from azure.cli.core.util import get_file_json
from knack.util import CLIError
from azure.cli.core.azclierror import ResourceNotFoundError


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
        self.cmd('group list --tag a', checks=[
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

    @ResourceGroupPreparer(name_prefix='cli_test_rg_scenario')
    def test_resource_group_force_deletion_type(self, resource_group):

        self.cmd('group create -n testrg -l westus --tag a=b c --managed-by test_admin', checks=[
            self.check('name', 'testrg'),
            self.check('tags', {'a': 'b', 'c': ''}),
            self.check('managedBy', 'test_admin')
        ])

        self.cmd('group delete -n testrg -f Microsoft.Compute/virtualMachines --yes')
        self.cmd('group exists -n testrg',
                 checks=self.check('@', False))


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
        self.cmd('resource delete -n {vnet} -g {rg} --resource-type {rt} --no-wait')
        time.sleep(10)
        self.cmd('resource list', checks=self.check("length([?name=='{vnet}'])", 0))


class ResourceIDScenarioTest(ScenarioTest):

    @AllowLargeResponse()
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


class ResourcePatchTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resource_patch_')
    def test_resource_patch(self, resource_group):
        self.kwargs.update({
            'vm': 'vm'
        })
        self.kwargs['vm_id'] = self.cmd(
            'vm create -g {rg} -n {vm} --image UbuntuLTS --size Standard_D2s_v3 --v-cpus-available 1 '
            '--v-cpus-per-core 1 --admin-username vmtest --generate-ssh-keys --nsg-rule NONE',
        ).get_output_in_json()['id']

        self.cmd('vm show -g {rg} -n {vm}', checks=[
            self.check('hardwareProfile.vmSize', 'Standard_D2s_v3'),
            self.check('hardwareProfile.vmSizeProperties.vCpusAvailable', '1'),
            self.check('hardwareProfile.vmSizeProperties.vCpusPerCore', '1'),
            self.check('osProfile.adminUsername', 'vmtest'),
            self.check('osProfile.allowExtensionOperations', True),
            self.check('identity', None),
        ])

        self.cmd(
            'resource patch --id {vm_id} --is-full-object --properties "{{\\"identity\\":{{\\"type\\":\\"SystemAssigned\\"}},'
            ' \\"properties\\":{{\\"osProfile\\":{{\\"allowExtensionOperations\\":\\"false\\"}}}}}}"',
            checks=[
                self.check('id', '{vm_id}'),
                self.check('properties.osProfile.allowExtensionOperations', False),
                self.check('identity.type', 'SystemAssigned'),
            ])


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

        self.cmd('resource wait --id {app_settings_id} --created')

        self.cmd('resource wait --id {app_settings_id} --exists')

        self.cmd('resource show --id {app_config_id}',
                 checks=self.check('properties.publishingUsername', '${app}'))
        self.cmd('resource show --id {app_config_id} --include-response-body',
                 checks=self.check('responseBody.properties.publishingUsername', '${app}'))


class TagScenarioTest(ScenarioTest):

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, random_config_dir=True, **kwargs)

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

    @AllowLargeResponse()
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
                '--is-full-object -p "{{\\"properties\\":{{\\"publicNetworkAccess\\":\\"Enabled\\"}},\\"location\\":\\"{loc}\\",'
                         '\\"sku\\":{{\\"name\\":\\"Standard\\"}}}}"',
                         checks=self.check('name', '{vault}')).get_output_in_json()
        self.kwargs['vault_id'] = vault['id']
        self.cmd('resource tag --ids {vault_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))
        self.cmd('resource tag --ids {vault_id} --tags', checks=self.check('tags', {}))

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
            'sku': 'Standard',
            'ip_name': self.create_random_name('cli_ip', 20)
        })

        self.cmd('acr create -n {registry_name} -g {rg} -l {rg_loc} --sku {sku}',
                 checks=[self.check('name', '{registry_name}')])
        webhook = self.cmd('acr webhook create -n {webhook_name} -r {registry_name} --uri {uri} --actions {actions}',
                           checks=[self.check('name', '{webhook_name}')]).get_output_in_json()
        self.kwargs['webhook_id'] = webhook['id']
        self.cmd('resource tag --ids {webhook_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))
        self.cmd('resource tag --ids {webhook_id} --tags', checks=self.check('tags', {}))

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

        self.cmd('resource tag --ids {vault_id} {webhook_id} {container_id} --tags {tag}', checks=[
            self.check('length(@)', 3),
            self.check('[0].tags', {'cli-test': 'test'})
        ])

        # Test Microsoft.Network/publicIPAddresses
        public_ip = self.cmd('network public-ip create -g {rg} -n {ip_name} --location {loc} --sku Standard ').\
            get_output_in_json()
        self.kwargs['public_ip_id'] = public_ip['publicIp']['id']
        self.cmd('resource tag --ids {public_ip_id} --tags {tag}', checks=self.check('tags', {'cli-test': 'test'}))

        self.cmd('resource delete --id {vault_id}', checks=self.is_empty())
        self.cmd('resource delete --id {webhook_id}', checks=self.is_empty())
        self.cmd('resource delete --id {public_ip_id}', checks=self.is_empty())

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

        self.cmd('resource delete --id {vault_id} --no-wait', checks=self.is_empty())

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

    def test_provider_registration_rpaas(self):
        self.kwargs.update({'prov': 'Microsoft.Confluent'})

        result = self.cmd('provider show -n {prov}').get_output_in_json()
        if result['registrationState'] == 'Unregistered':
            self.cmd('provider register -n {prov} --accept-terms')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
        else:
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
            self.cmd('provider register -n {prov} --accept-terms')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')

    def test_provider_registration_rpaas_no_accept_terms(self):
        self.kwargs.update({'prov': 'Microsoft.Confluent'})

        result = self.cmd('provider show -n {prov}').get_output_in_json()
        if result['registrationState'] == 'Unregistered':
            self.cmd('provider register -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
        else:
            self.cmd('provider unregister -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'] in ['Unregistering', 'Unregistered'])
            self.cmd('provider register -n {prov}')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')

    def test_provider_registration_mg(self):
        self.kwargs.update({'prov': 'Microsoft.ClassicInfrastructureMigrate'})

        result = self.cmd('provider register -n {prov} --m testmg')
        self.assertTrue(result, None)

    def test_register_consent_to_permissions(self):

        self.kwargs = {
            'prov': "Microsoft.ClassicInfrastructureMigrate"
        }

        result = self.cmd('provider show -n {prov}').get_output_in_json()
        if result['registrationState'] == 'Unregistered':
            self.cmd('provider register -n {prov} --consent-to-permissions')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')
            result = self.cmd('provider permission list -n {prov}').get_output_in_json()
            self.assertGreaterEqual(len(result['value']), 1)
            self.cmd('provider unregister -n {prov}')
        else:
            self.cmd('provider unregister -n {prov}')
            self.cmd('provider register -n {prov} --consent-to-permissions')
            result = self.cmd('provider show -n {prov}').get_output_in_json()
            self.assertTrue(result['registrationState'], 'Registered')
            result = self.cmd('provider permission list -n {prov}').get_output_in_json()
            self.assertGreaterEqual(len(result['value']), 1)


class ProviderOperationTest(ScenarioTest):

    @AllowLargeResponse(size_kb=99999)
    def test_provider_operation(self):
        result = self.cmd('provider operation list').get_output_in_json()
        self.assertGreater(len(result), 0)

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
        self.cmd('feature unregister --namespace Microsoft.Network --name AllowLBPreview', checks=[
            self.check_pattern('properties.state', 'Unregistering|Unregistered')
        ])

    @AllowLargeResponse(8192)
    def test_feature_registration_list(self):
        self.cmd('feature registration list', checks=self.check("length([?name=='Microsoft.Network/SkipPseudoVipGeneration'])", 1))

        self.cmd('feature registration show --provider-namespace Microsoft.Network -n AllowLBPreview')

    @AllowLargeResponse(8192)
    def test_feature_registration_create(self):
        self.cmd('feature registration create --namespace Microsoft.Network --name AllowLBPreview', checks=[
            self.check_pattern('properties.state', 'Registering|Registered')
        ])

    @AllowLargeResponse(8192)
    def test_feature_registration_delete(self):
        self.cmd('feature registration delete --namespace Microsoft.Network --name AllowLBPreview --yes')

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

        # create a policy assignment with invalid not scopes
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --params "{params}" --description "Policy description" --not-scopes "invalid"')

        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --params "{params}" --description "Policy description"', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('description', 'Policy description')
        ])

        # create a policy assignment with not scopes and standard sku
        self.kwargs.update({
            'vnet': self.create_random_name('azurecli-test-policy-vnet', 40),
            'subnet': self.create_random_name('azurecli-test-policy-subnet', 40),
            'sub': self.get_subscription_id()
        })

        self.kwargs['notscope'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/virtualNetworks/vnetFoo'.format(**self.kwargs)

        self.cmd('policy assignment create --policy {pn} -n {pan} --display-name {padn} -g {rg} --not-scopes {notscope} --params "{params}"', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('notScopes[0]', '{notscope}')
        ])

        # update not scopes using the update command
        self.kwargs['notscope2'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/virtualMachines/foo'.format(**self.kwargs)
        self.cmd('policy assignment update -n {pan} -g {rg} --not-scopes "{notscope} {notscope2}" --params "{params}"', checks=[
            self.check('name', '{pan}'),
            self.check('displayName', '{padn}'),
            self.check('notScopes[0]', '{notscope}'),
            self.check('notScopes[1]', '{notscope2}'),
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

    def applyPolicyAtScope(self, scope, policyId, enforcementMode='Default', atMGLevel=False):
        # create a policy assignment at the given scope
        self.kwargs.update({
            'pol': policyId,
            'pan': self.create_random_name('cli-test-polassg', 24),   # limit is 24 characters at MG scope
            'padn': self.create_random_name('test_assignment', 20),
            'scope': scope,
            'em': enforcementMode
        })

        # Not set not scope for MG level assignment
        if atMGLevel:
            self.cmd('policy assignment create --policy {pol} -n {pan} --display-name {padn} --params "{params}" --scope {scope} --enforcement-mode {em}', checks=[
                self.check('name', '{pan}'),
                self.check('displayName', '{padn}'),
                self.check('enforcementMode', '{em}')
            ])
        else:
            self.cmd('policy assignment create --policy {pol} -n {pan} --display-name {padn} --params "{params}" --scope {scope} --enforcement-mode {em} --not-scopes "{scope}/providers/Microsoft.Compute/virtualMachines/myVm"', checks=[
                self.check('name', '{pan}'),
                self.check('displayName', '{padn}'),
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
            self.applyPolicyAtScope(scope, policy, atMGLevel=True)
        elif subscription:
            policy = '/subscriptions/{sub}/providers/Microsoft.Authorization/policyDefinitions/{pn}'.format(sub=subscription, pn=self.kwargs['pn'])
            self.applyPolicyAtScope('/subscriptions/{sub}'.format(sub=subscription), policy, 'DoNotEnforce')
        else:
            self.applyPolicy()

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
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
            'dp_mode': 'Microsoft.KeyVault.Data',
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

        if not self.in_recording:
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
                self.check('displayName', '{padn}')
            ])

            # ensure the assignment appears in the list results
            self.cmd('policy assignment list --resource-group {rg}', checks=self.check("length([?name=='{pan}'])", 1))

            # delete the assignment and validate it's gone
            self.cmd('policy assignment delete -n {pan} -g {rg}')
            self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))

        # delete the policy set
        cmd = self.cmdstring('policy set-definition delete -n {psn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
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
            self.check('parameters.allowedLocations.type', 'array'),
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
        if not self.in_recording:
            time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
            time.sleep(10)

        # delete the data policy
        cmd = self.cmdstring('policy definition delete -n {dpn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
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

        # ensure the managed identity is not touched during update
        self.cmd('policy assignment update -n {pan} -g {rg} --description "New description"', checks=[
            self.check('description', 'New description'),
            self.check('identity.type', 'SystemAssigned'),
            self.exists('identity.principalId'),
            self.exists('identity.tenantId')
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

    @ResourceGroupPreparer(name_prefix='cli_test_policy_identity_systemassigned')
    @AllowLargeResponse(8192)
    def test_resource_policy_identity_systemassigned(self, resource_group, resource_group_location):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d',
            'sub': self.get_subscription_id(),
            'location': resource_group_location,
            'em': 'DoNotEnforce'
        })

        # create a policy assignment with managed identity using a built in policy definition
        assignmentIdentity = self.cmd('policy assignment create --policy {bip} -n {pan} -g {rg} --location {location} --mi-system-assigned --enforcement-mode {em}', checks=[
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

        # ensure the managed identity is not touched during update
        self.cmd('policy assignment update -n {pan} -g {rg} --description "New description"', checks=[
            self.check('description', 'New description'),
            self.check('identity.type', 'SystemAssigned'),
            self.exists('identity.principalId'),
            self.exists('identity.tenantId')
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
        self.cmd('policy assignment identity assign --system-assigned -n {pan} -g {rg}', checks=[
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

        # create a role assignment for the identity using --mi-system-assigned
        self.kwargs.update({
            'idScope': '/subscriptions/{sub}/resourceGroups/{rg}'.format(**self.kwargs),
            'idRole': 'Reader'
        })
        with mock.patch('azure.cli.core.commands.arm._gen_guid', side_effect=self.create_guid):
            assignmentIdentity = self.cmd('policy assignment create --policy {bip} -n {pan} -g {rg} --location {location} --mi-system-assigned --identity-scope {idScope} --role {idRole}', checks=[
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
            assignmentIdentity = self.cmd('policy assignment identity assign -n {pan} -g {rg} --system-assigned --identity-scope {idScope} --role {idRole}', checks=[
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

    @ResourceGroupPreparer(name_prefix='cli_test_policy_identity_userassigned')
    @AllowLargeResponse(8192)
    def test_resource_policy_identity_userassigned(self, resource_group, resource_group_location):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-assignment', 40),
            'bip': '06a78e20-9358-41c9-923c-fb736d382a4d',
            'sub': self.get_subscription_id(),
            'location': resource_group_location,
            'em': 'DoNotEnforce',
            'msi': 'policyCliTestMsi'
        })

        # create a managed identity
        msi_result = self.cmd('identity create -g {rg} -n {msi} --tags tag1=d1', checks=[
            self.check('name', '{msi}')]).get_output_in_json()
        self.kwargs['fullQualifiedMsi'] = msi_result['id']

        # create a policy assignment with user assigned managed identity using a built in policy definition
        assignmentIdentity = self.cmd('policy assignment create --policy {bip} -n {pan} -g {rg} --location {location} --mi-user-assigned {msi} --enforcement-mode {em}', checks=[
            self.check('name', '{pan}'),
            self.check('location', '{location}'),
            self.check('identity.type', 'UserAssigned'),
            self.exists('identity.userAssignedIdentities')
        ]).get_output_in_json()['identity']
        msis = [x.lower() for x in assignmentIdentity['userAssignedIdentities'].keys()]
        self.assertEqual(msis[0], msi_result['id'].lower())

        # ensure managed identity details are retrievable directly through 'policy assignment identity' commands
        assignmentIdentity = self.cmd('policy assignment identity show -n {pan} -g {rg}', checks=[
            self.check('type', assignmentIdentity['type']),
            self.exists('userAssignedIdentities')
        ]).get_output_in_json()
        msis = [x.lower() for x in assignmentIdentity['userAssignedIdentities'].keys()]
        self.assertEqual(msis[0], msi_result['id'].lower())

        # ensure the managed identity is not touched during update
        self.cmd('policy assignment update -n {pan} -g {rg} --description "New description"', checks=[
            self.check('description', 'New description'),
            self.check('identity.type', 'UserAssigned'),
            self.exists('identity.userAssignedIdentities')
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
        assignmentIdentity = self.cmd('policy assignment identity assign --user-assigned {fullQualifiedMsi} -n {pan} -g {rg}', checks=[
            self.check('type', 'UserAssigned'),
            self.exists('userAssignedIdentities')
        ]).get_output_in_json()
        msis = [x.lower() for x in assignmentIdentity['userAssignedIdentities'].keys()]
        self.assertEqual(msis[0], msi_result['id'].lower())

        assignmentIdentity = self.cmd('policy assignment show -n {pan} -g {rg}', checks=[
            self.check('name', '{pan}'),
            self.check('identity.type', 'UserAssigned'),
            self.exists('identity.userAssignedIdentities')
        ]).get_output_in_json()['identity']
        msis = [x.lower() for x in assignmentIdentity['userAssignedIdentities'].keys()]
        self.assertEqual(msis[0], msi_result['id'].lower())

        # replace an identity with system assigned msi
        self.cmd('policy assignment identity assign --system-assigned -n {pan} -g {rg}', checks=[
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
        self.cmd('policy assignment delete -n {pan} -g {rg}')

    @ResourceGroupPreparer(name_prefix='cli_test_policy_ncm')
    @AllowLargeResponse(8192)
    def test_resource_policy_non_compliance_messages(self, resource_group, resource_group_location):
        self.kwargs.update({
            'pan': self.create_random_name('azurecli-test-policy-assignment', 40),
            'bip': '095e4ed9-c835-4ab6-9439-b5644362a06c',
            'sub': self.get_subscription_id(),
            'location': resource_group_location,
            'em': 'DoNotEnforce',
            'drid': 'AINE_MaximumPasswordAge'
        })

        # create a policy assignment of a built-in policy set
        self.cmd('policy assignment create -d {bip} -n {pan} -g {rg} --enforcement-mode {em}', checks=[
            self.check('name', '{pan}'),
            self.not_exists('nonComplianceMessages')
        ])

        # list the non-compliance messages, should be none
        self.cmd('policy assignment non-compliance-message list -n {pan} -g {rg}', checks=[
            self.is_empty()
        ])

        # Add two non-compliance messages
        self.cmd('policy assignment non-compliance-message create -n {pan} -g {rg} -m "General message"', checks=[
            self.check('length([])', 1),
            self.check('[0].message', 'General message'),
            self.not_exists('[0].policyDefinitionReferenceId')
        ])

        self.cmd('policy assignment non-compliance-message create -n {pan} -g {rg} -m "Specific message" -r {drid}', checks=[
            self.check('length([])', 2),
            self.check('[0].message', 'General message'),
            self.not_exists('[0].policyDefinitionReferenceId'),
            self.check('[1].message', 'Specific message'),
            self.check('[1].policyDefinitionReferenceId', '{drid}')
        ])

        # list the non-compliance messages, should be two
        self.cmd('policy assignment non-compliance-message list -n {pan} -g {rg}', checks=[
            self.check('length([])', 2),
            self.check('[0].message', 'General message'),
            self.not_exists('[0].policyDefinitionReferenceId'),
            self.check('[1].message', 'Specific message'),
            self.check('[1].policyDefinitionReferenceId', '{drid}')
        ])

        # show the assignment, should contain non-compliance messages
        self.cmd('policy assignment show -n {pan} -g {rg}', checks=[
            self.check('name', '{pan}'),
            self.check('length(nonComplianceMessages)', 2),
            self.check('nonComplianceMessages[0].message', 'General message'),
            self.not_exists('nonComplianceMessages[0].policyDefinitionReferenceId'),
            self.check('nonComplianceMessages[1].message', 'Specific message'),
            self.check('nonComplianceMessages[1].policyDefinitionReferenceId', '{drid}')
        ])

        # update the assignment, should not touch non-compliance messages
        self.cmd('policy assignment update -n {pan} -g {rg} --description "New description"', checks=[
            self.check('name', '{pan}'),
            self.check('description', 'New description'),
            self.check('length(nonComplianceMessages)', 2),
            self.check('nonComplianceMessages[0].message', 'General message'),
            self.not_exists('nonComplianceMessages[0].policyDefinitionReferenceId'),
            self.check('nonComplianceMessages[1].message', 'Specific message'),
            self.check('nonComplianceMessages[1].policyDefinitionReferenceId', '{drid}')
        ])

        # remove a non-compliance message that does not exist
        self.cmd('policy assignment non-compliance-message delete -n {pan} -g {rg} -m "Unknown message"', checks=[
            self.check('length([])', 2),
            self.check('[0].message', 'General message'),
            self.not_exists('[0].policyDefinitionReferenceId'),
            self.check('[1].message', 'Specific message'),
            self.check('[1].policyDefinitionReferenceId', '{drid}')
        ])

        # remove a non-compliance message that exists but without the right reference ID
        self.cmd('policy assignment non-compliance-message delete -n {pan} -g {rg} -m "Specific message"', checks=[
            self.check('length([])', 2),
            self.check('[0].message', 'General message'),
            self.not_exists('[0].policyDefinitionReferenceId'),
            self.check('[1].message', 'Specific message'),
            self.check('[1].policyDefinitionReferenceId', '{drid}')
        ])

        # remove a non-compliance message
        self.cmd('policy assignment non-compliance-message delete -n {pan} -g {rg} -m "General message"', checks=[
            self.check('length([])', 1),
            self.check('[0].message', 'Specific message'),
            self.check('[0].policyDefinitionReferenceId', '{drid}')
        ])

        # remove a non-compliance message with a reference ID
        self.cmd('policy assignment non-compliance-message delete -n {pan} -g {rg} -m "Specific message" -r {drid}', checks=[
            self.is_empty()
        ])

        # list the non-compliance messages, should be 0
        self.cmd('policy assignment non-compliance-message list -n {pan} -g {rg}', checks=[
            self.is_empty()
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

    @live_only()
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

        if not self.in_recording:
            time.sleep(10)  # ensure the policy is gone when run live.

        self.cmd('policy set-definition list',
                 checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        self.cmd('policy definition delete -n {pn}')

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
            self.check('displayName', '{padn}')
        ]).get_output_in_json()['name']

        # clean policy assignment and policy
        self.cmd('policy assignment delete -n {pan_random} -g {rg}')
        self.cmd('policy assignment list --disable-scope-strict-match',
                 checks=self.check("length([?name=='{pan_random}'])", 0))
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)

        if not self.in_recording:
            time.sleep(10)

        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))

    def resource_policyexemption_operations(self, resource_group, management_group=None, subscription=None):
        curr_dir = os.path.dirname(os.path.realpath(__file__))

        self.kwargs.update({
            'pn': self.create_random_name('clitest', 30),
            'pdn': self.create_random_name('clitest', 20),
            'desc': 'desc_for_test_policy_123',
            'dpn': self.create_random_name('clitest-dp', 30),
            'dpdn': self.create_random_name('clitest_dp', 20),
            'dp_desc': 'desc_for_clitest_data_policy_123',
            'dp_mode': 'Microsoft.KeyVault.Data',
            'psn': self.create_random_name('clitest', 30),
            'psdn': self.create_random_name('clitest', 20),
            'pan': self.create_random_name('clitest', 24),
            'padn': self.create_random_name('clitest', 20),
            'pen': self.create_random_name('clitest', 24),
            'pedn': self.create_random_name('clitest', 20),
            'pe_desc': 'desc_for_clitest_policyexemption_123',
            'rf': os.path.join(curr_dir, 'sample_policy_rule.json').replace('\\', '\\\\'),
            'dprf': os.path.join(curr_dir, 'sample_data_policy_rule.json').replace('\\', '\\\\'),
            'psf': os.path.join(curr_dir, 'sample_policy_set_exemption_test.json').replace('\\', '\\\\'),
            'pdf': os.path.join(curr_dir, 'sample_policy_param_def.json').replace('\\', '\\\\'),
            'metadata': 'test',
            'updated_metadata': 'test2',
        })
        if (management_group):
            self.kwargs.update({'mg': management_group})
        if (subscription):
            self.kwargs.update({'sub': subscription})

        if not self.in_recording:
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
        with open(os.path.join(curr_dir, 'sample_policy_set_exemption_test.json'), 'w') as outfile:
            json.dump(policyset, outfile)

        cmd = self.cmdstring('policy set-definition create -n {psn} --definitions @"{psf}" --display-name {psdn}', management_group, subscription)
        policyset = self.cmd(cmd).get_output_in_json()
        self.kwargs.update({'prids': policyset['policyDefinitions'][0]['policyDefinitionReferenceId']})

        scope = None
        if management_group:
            scope = '/providers/Microsoft.Management/managementGroups/{mg}'.format(mg=management_group)
        elif subscription:
            scope = '/subscriptions/{sub}'.format(sub=subscription)

        if scope:
            self.kwargs.update({'scope': scope})
            assignment = self.cmd('policy assignment create -d {psid} -n {pan} --scope {scope} --display-name {padn}'.format(psid=policyset['id'], **self.kwargs)).get_output_in_json()
            cmd = self.cmdstring('policy exemption create -n {pen} -a {pa} -e waiver --scope {scope} --display-name {pedn} --description {pe_desc} --metadata category={metadata}'.format(pa=assignment['id'], **self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Waiver'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{metadata}')
            ]).get_output_in_json()

            # ensure the exemption appears in the list results
            self.cmd('policy exemption list --scope {scope}'.format(**self.kwargs), checks=self.check("length([?name=='{pen}'])", 1))

            # update the exemption
            self.kwargs['pe_desc'] = self.kwargs['pe_desc'] + '_new'
            self.kwargs['pedn'] = self.kwargs['pedn'] + '_new'
            self.kwargs['expiration'] = '3021-04-05T00:45:13+00:00'
            cmd = self.cmdstring('policy exemption update -n {pen} -e mitigated --scope {scope} -r {prids} --expires-on {expiration} --display-name {pedn} --description {pe_desc} --metadata category={updated_metadata}'.format(**self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Mitigated'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{updated_metadata}'),
                self.check('policyDefinitionReferenceIds[0]', '{prids}'),
                self.check('expiresOn', '{expiration}')
            ])

            cmd = self.cmdstring('policy exemption show -n {pen} --scope {scope}'.format(**self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Mitigated'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{updated_metadata}'),
                self.check('policyDefinitionReferenceIds[0]', '{prids}'),
                self.check('expiresOn', '{expiration}')
            ])

            # delete the exemption and validate it's gone
            self.cmd('policy exemption delete -n {pen} --scope {scope}'.format(**self.kwargs))
            self.cmd('policy assignment delete -n {pan} --scope {scope}'.format(**self.kwargs))
            self.cmd('policy exemption list --disable-scope-strict-match', checks=self.check("length([?name=='{pen}'])", 0))
            self.cmd('policy assignment list --disable-scope-strict-match', checks=self.check("length([?name=='{pan}'])", 0))
        else:
            assignment = self.cmd('policy assignment create -d {psn} -n {pan} -g {rg} --display-name {padn}'.format(**self.kwargs), checks=[
                self.check('name', '{pan}'),
                self.check('displayName', '{padn}')
            ]).get_output_in_json()

            # ensure the assignment appears in the list results
            self.cmd('policy assignment list --resource-group {rg}', checks=self.check("length([?name=='{pan}'])", 1))

            cmd = self.cmdstring('policy exemption create -n {pen} -a {pa} -e waiver -g {rg} --display-name {pedn} --description {pe_desc} --metadata category={metadata}'.format(pa=assignment['id'], **self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Waiver'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{metadata}')
            ]).get_output_in_json()

            # ensure the exemption appears in the list results
            self.cmd('policy exemption list --resource-group {rg}', checks=self.check("length([?name=='{pen}'])", 1))

            # update the exemption
            self.kwargs['pe_desc'] = self.kwargs['pe_desc'] + '_new'
            self.kwargs['pedn'] = self.kwargs['pedn'] + '_new'
            self.kwargs['expiration'] = '3021-04-05T00:45:13+00:00'
            cmd = self.cmdstring('policy exemption update -n {pen} -e mitigated -g {rg} -r {prids} --expires-on {expiration} --display-name {pedn} --description {pe_desc} --metadata category={updated_metadata}'.format(**self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Mitigated'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{updated_metadata}'),
                self.check('policyDefinitionReferenceIds[0]', '{prids}'),
                self.check('expiresOn', '{expiration}')
            ])

            cmd = self.cmdstring('policy exemption show -n {pen} -g {rg}'.format(**self.kwargs))
            self.cmd(cmd, checks=[
                self.check('name', '{pen}'),
                self.check('displayName', '{pedn}'),
                self.check('exemptionCategory', 'Mitigated'),
                self.check('description', '{pe_desc}'),
                self.check('metadata.category', '{updated_metadata}'),
                self.check('policyDefinitionReferenceIds[0]', '{prids}'),
                self.check('expiresOn', '{expiration}')
            ])

            # delete the exemption and validate it's gone
            self.cmd('policy exemption delete -n {pen} -g {rg}'.format(**self.kwargs))
            self.cmd('policy assignment delete -n {pan} -g {rg}'.format(**self.kwargs))
            self.cmd('policy exemption list', checks=self.check("length([?name=='{pen}'])", 0))

        # list and show it
        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 1))

        cmd = self.cmdstring('policy set-definition show -n {psn}', management_group, subscription)
        self.cmd(cmd, checks=[
            self.check('name', '{psn}'),
            self.check('displayName', '{psdn}')
        ])

        # delete the policy set
        cmd = self.cmdstring('policy set-definition delete -n {psn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
            time.sleep(10)  # ensure the policy is gone when run live.

        cmd = self.cmdstring('policy set-definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{psn}'])", 0))

        # delete the policy
        cmd = self.cmdstring('policy definition delete -n {pn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
            time.sleep(10)

        # delete the data policy
        cmd = self.cmdstring('policy definition delete -n {dpn}', management_group, subscription)
        self.cmd(cmd)
        if not self.in_recording:
            time.sleep(10)

        # ensure the policy is gone when run live.
        cmd = self.cmdstring('policy definition list', management_group, subscription)
        self.cmd(cmd, checks=self.check("length([?name=='{pn}'])", 0))
        self.cmd(cmd, checks=self.check("length([?name=='{dpn}'])", 0))

    @ResourceGroupPreparer(name_prefix='cli_test_policyexemption')
    @AllowLargeResponse(4096)
    def test_resource_policyexemption_default(self, resource_group):
        self.resource_policyexemption_operations(resource_group)

    @ResourceGroupPreparer(name_prefix='cli_test_policyexemption_management_group')
    @AllowLargeResponse(4096)
    def test_resource_policyexemption_management_group(self, resource_group):
        management_group_name = self.create_random_name('cli-test-mgmt-group', 30)
        self.cmd('account management-group create -n ' + management_group_name)
        try:
            self.resource_policyexemption_operations(resource_group, management_group_name)
        finally:
            self.cmd('account management-group delete -n ' + management_group_name)

    # mock doesnt work when the subscription comes from --scope, so it cannot be rerecord.
    @live_only()
    @ResourceGroupPreparer(name_prefix='cli_test_policyexemption_subscription')
    @AllowLargeResponse(4096)
    def test_resource_policyexemption_subscription(self, resource_group):
        # under playback, we mock it so the subscription id will be '00000000...' and it will match
        # the same sanitized value in the recording
        if not self.in_recording:
            with mock.patch('azure.cli.command_modules.resource.custom._get_subscription_id_from_subscription',
                            return_value=MOCKED_SUBSCRIPTION_ID):
                self.resource_policyexemption_operations(resource_group, None, '0b1f6471-1bf0-4dda-aec3-cb9272f09590')
        else:
            self.resource_policyexemption_operations(resource_group, None, '0b1f6471-1bf0-4dda-aec3-cb9272f09590')


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
        principal_id = user_principal['id']

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
            'new_ad_desc': 'new_test_appdef_123',
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

        # update a managedapp definition
        self.cmd('managedapp definition update -n {adn} --package-file-uri {uri} --display-name {addn} --description {new_ad_desc} -l {loc} -a {auth} --lock-level {lock} -g {rg}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{new_ad_desc}'),
            self.check('authorizations[0].principalId', principal_id),
            self.check('authorizations[0].roleDefinitionId', role_definition_id),
            self.check('artifacts[0].name', 'ApplicationResourceTemplate'),
            self.check('artifacts[0].type', 'Template'),
            self.check('artifacts[1].name', 'CreateUiDefinition'),
            self.check('artifacts[1].type', 'Custom')
        ])

        self.cmd('managedapp definition list -g {rg}',
                 checks=self.check('[0].name', '{adn}'))

        self.cmd('managedapp definition show --ids {ad_id}', checks=[
            self.check('name', '{adn}'),
            self.check('displayName', '{addn}'),
            self.check('description', '{new_ad_desc}'),
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
        self.cmd('ad user delete --id {upn}')

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
        principal_id = user_principal['id']

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
        self.cmd('ad user delete --id {upn}')

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    def test_managed_app_def_deployment_mode(self):
        self.kwargs.update({
            'upn': self.create_random_name('testuser', 15) + '@azuresdkteam.onmicrosoft.com',
            'sub': self.get_subscription_id()
        })
        user_principal = self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}').get_output_in_json()
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change
        principal_id = user_principal['id']
        with mock.patch('azure.cli.command_modules.role.custom._gen_guid', side_effect=self.create_guid):
            role_assignment = self.cmd(
                'role assignment create --assignee {upn} --role contributor --scope "/subscriptions/{sub}" ').get_output_in_json()
        from msrestazure.tools import parse_resource_id
        role_definition_id = parse_resource_id(role_assignment['roleDefinitionId'])['name']
        self.kwargs.update({
            'app_def': self.create_random_name('def', 10),
            'auth': principal_id + ':' + role_definition_id,
            'addn': self.create_random_name('test_appdef', 20),
            'uri': 'https://raw.githubusercontent.com/Azure/azure-managedapp-samples/master/Managed%20Application%20Sample%20Packages/201-managed-storage-account/managedstorage.zip',
        })
        self.cmd('managedapp definition create -n {app_def} -g {rg} --display-name {addn} --description test -a {auth} --package-file-uri {uri} --lock-level None --deployment-mode Incremental', checks=[
            self.check('deploymentPolicy.deploymentMode', 'Incremental')
        ])
        self.cmd('managedapp definition update -n {app_def} -g {rg} --display-name {addn} --description test -a {auth} --package-file-uri {uri} --lock-level None --deployment-mode Complete', checks=[
            self.check('deploymentPolicy.deploymentMode', 'Complete')
        ])
        self.cmd('role assignment delete --assignee {upn} --role contributor ')
        self.cmd('ad user delete --id {upn}')

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
            'auth': user_principal['id'] + ':' + role_definition_id,
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
            # self.check('type', 'Microsoft.Solutions/applications'),     # ARM bug, response resource type is all lower case
            self.check('kind', 'servicecatalog'),
            self.check('managedResourceGroupId', '{ma_rg_id}'),
            self.check('tags', {'key': 'val'})
        ]).get_output_in_json()['id']

        self.cmd('managedapp list -g {rg}')    # skip check, for ARM bug, return empty list after create succeeded

        self.cmd('managedapp show --ids {ma_id}', checks=[
            self.check('name', '{man}'),
            # self.check('type', 'Microsoft.Solutions/applications'),     # ARM bug, response resource type is all lower case
            self.check('kind', 'servicecatalog'),
            self.check('managedResourceGroupId', '{ma_rg_id}')
        ])

        self.cmd('managedapp delete -g {rg} -n {man}')
        self.cmd('managedapp list -g {rg}', checks=self.is_empty())

        self.cmd('role assignment delete --assignee {upn} --role contributor ')
        self.cmd('ad user delete --id {upn}')


class InvokeActionTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_invoke_action')
    def test_invoke_action(self, resource_group):

        self.kwargs.update({
            'vm': self.create_random_name('cli-test-vm', 30),
            'user': 'ubuntu',
            'pass': self.create_random_name('Longpassword#1', 30)
        })

        self.kwargs['vm_id'] = self.cmd('vm create -g {rg} -n {vm} --use-unmanaged-disk --image UbuntuLTS --admin-username {user} --admin-password {pass} --authentication-type password --nsg-rule None').get_output_in_json()['id']

        self.cmd('resource invoke-action --action powerOff --ids {vm_id} --no-wait')
        time.sleep(20)
        self.cmd('vm get-instance-view -g {rg} -n {vm}', checks=[
            self.check('instanceView.statuses[1].code', 'PowerState/stopped')
        ])
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
        with self.assertRaisesRegex(SystemExit, '2'):
            self.cmd('group delete')
        self.cmd('group delete -n {group1} -y')
        self.cmd('group create -n {group2}', checks=[
            self.check('name', self.kwargs['group2']),
            self.check('location', self.kwargs['location'])
        ])
        self.cmd('group delete -n {group2} -y')


class BicepScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    def test_bicep_list_versions(self):
        self.cmd('az bicep list-versions', checks=[
            self.greater_than('length(@)', 0)
        ])

class BicepDecompileParamsTest(LiveScenarioTest):
    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_bicep_decompile_params_file(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'test-params.json').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'test-params.bicepparam').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep decompile-params --file {tf}')

        if os.path.exists(params_path):
            os.remove(params_path)

class BicepBuildParamsTest(LiveScenarioTest):
    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_bicep_build_params_file(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'sample_params.bicepparam').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep build-params --file {tf}')

        if os.path.exists(params_path):
            os.remove(params_path)

    def test_bicep_build_params_file_outfile(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'sample_params.bicepparam').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep build-params --file {tf} --outfile {params_path}')

        if os.path.exists(params_path):
            os.remove(params_path)

# Because don't want to record bicep cli binary
class BicepBuildTest(LiveScenarioTest):

    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_bicep_build_decompile(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'storage_account_deploy.bicep').replace('\\', '\\\\')
        build_path = os.path.join(curr_dir, 'test.json').replace('\\', '\\\\')
        decompile_path = os.path.join(curr_dir, 'test.bicep').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'build_path': build_path,
            'decompile_path': decompile_path
        })

        self.cmd('az bicep build -f {tf} --outfile {build_path}')
        self.cmd('az bicep decompile -f {build_path}')
        self.cmd('az bicep decompile -f {build_path} --force')

        if os.path.exists(build_path):
            os.remove(build_path)
        if os.path.exists(decompile_path):
            os.remove(decompile_path)

class BicepGenerateParamsTest(LiveScenarioTest):
    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_bicep_generate_params_output_format_only(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep generate-params -f {tf} --outfile {params_path} --output-format json')

        if os.path.exists(params_path):
            os.remove(params_path)

    def test_bicep_generate_params_include_params_only(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep generate-params -f {tf} --outfile {params_path} --include-params all')

        if os.path.exists(params_path):
            os.remove(params_path)

    def test_bicep_generate_params(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        tf = os.path.join(curr_dir, 'sample_params.bicep').replace('\\', '\\\\')
        params_path = os.path.join(curr_dir, 'sample_params.parameters.json').replace('\\', '\\\\')
        self.kwargs.update({
            'tf': tf,
            'params_path': params_path,
        })

        self.cmd('az bicep generate-params -f {tf} --outfile {params_path}')

        if os.path.exists(params_path):
            os.remove(params_path)

class BicepInstallationTest(LiveScenarioTest):
    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_install_and_upgrade(self):
        self.cmd('az bicep install')
        self.cmd('az bicep version')

        self.cmd('az bicep uninstall')

        self.cmd('az bicep install --target-platform win-x64')
        self.cmd('az bicep version')

        self.cmd('az bicep uninstall')

        self.cmd('az bicep install --version v0.4.63')
        self.cmd('az bicep upgrade')
        self.cmd('az bicep version')

        self.cmd('az bicep uninstall')

        self.cmd('az bicep install --version v0.4.63')
        self.cmd('az bicep upgrade -t win-x64')
        self.cmd('az bicep version')


class BicepRestoreTest(LiveScenarioTest):

    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_restore(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        bf = os.path.join(curr_dir, 'data', 'external_modules.bicep').replace('\\', '\\\\')
        out_path = os.path.join(curr_dir, 'data', 'external_modules.json').replace('\\', '\\\\')
        self.kwargs.update({
            'bf': bf,
            'out_path': out_path,
        })

        self.cmd('az bicep restore -f {bf}')
        self.cmd('az bicep restore -f {bf} --force')
        self.cmd('az bicep build -f {bf} --no-restore')

        if os.path.exists(out_path):
            os.remove(out_path)


class BicepFormatTest(LiveScenarioTest):

    def setup(self):
        super().setup()
        self.cmd('az bicep uninstall')

    def tearDown(self):
        super().tearDown()
        self.cmd('az bicep uninstall')

    def test_format(self):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        bf = os.path.join(curr_dir, 'storage_account_deploy.bicep').replace('\\', '\\\\')
        out_file = os.path.join(curr_dir, 'storage_account_deploy.formatted.bicep').replace('\\', '\\\\')
        self.kwargs.update({
            'bf': bf,
            'out_file': out_file,
        })

        self.cmd('az bicep format --file {bf} --outfile {out_file} --newline lf --indent-kind space --indent-size 2 --insert-final-newline')

        if os.path.exists(out_file):
            os.remove(out_file)


class ResourceManagementPrivateLinkTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_get', location='westus')
    def test_get_resourcemanagementprivatelink(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30)
        })
        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}')
        self.cmd('resourcemanagement private-link show -g {rg} -n {n}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_create', location='westus')
    def test_create_resourcemanagementprivatelink(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30)
        })
        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_delete', location='westus')
    def test_delete_resourcemanagementprivatelink(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30)
        })
        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_list', location='westus')
    def test_list_resourcemanagementprivatelink(self, resource_group, resource_group_location):
        self.kwargs.update({
            'loc': resource_group_location,
            'name1': self.create_random_name('privatelink', 30),
            'name2': self.create_random_name('privatelink', 30)
        })
        self.cmd('resourcemanagement private-link create -g {rg} -n {name1} -l {loc}')
        self.cmd('resourcemanagement private-link create -g {rg} -n {name2} -l {loc}')
        self.cmd('resourcemanagement private-link list -g {rg}', checks=[
            self.check('value[0].name', '{name1}'),
            self.check('value[1].name', '{name2}'),
            self.check('value[0].location', '{loc}'),
            self.check('value[1].location', '{loc}')
        ])
        self.cmd('resourcemanagement private-link delete -g {rg} -n {name1} --yes', checks=self.is_empty())
        self.cmd('resourcemanagement private-link delete -g {rg} -n {name2} --yes', checks=self.is_empty())

class PrivateLinkAssociationTest(ScenarioTest):

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_get', location='westus')
    def test_get_privatelinkassociation(self, resource_group, resource_group_location):
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30),
            'mg': tenant_id,
            'pla': self.create_guid(),
            'sub': self.get_subscription_id()
        })

        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.kwargs['pl'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{n}'.format(
            **self.kwargs)


        self.cmd('private-link association create -m {mg} -n {pla} --privatelink {pl} --public-network-access enabled', checks=[])

        self.cmd('private-link association show -m {mg} -n {pla}', checks=[
            self.check('name', '{pla}'),
            self.check('properties.publicNetworkAccess', 'Enabled'),
            self.check('properties.privateLink', '{pl}')
        ])

        # clean
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())
        self.cmd('private-link association delete -m {mg} -n {pla} --yes', self.is_empty())


    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_create', location='westus')
    def test_create_privatelinkassociation(self, resource_group, resource_group_location):
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30),
            'mg': tenant_id,
            'pla': self.create_guid(),
            'sub': self.get_subscription_id()
        })

        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.kwargs['pl'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{n}'.format(
            **self.kwargs)

        self.cmd('private-link association create -m {mg} -n {pla} --privatelink {pl} --public-network-access enabled', checks=[
            self.check('name', '{pla}'),
            self.check('properties.publicNetworkAccess', 'Enabled'),
            self.check('properties.privateLink', '{pl}')
        ])


        # clean
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())
        self.cmd('private-link association delete -m {mg} -n {pla} --yes', self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_delete', location='westus')
    def test_delete_privatelinkassociation(self, resource_group, resource_group_location):
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30),
            'mg': tenant_id,
            'pla': self.create_guid(),
            'sub': self.get_subscription_id()
        })

        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.kwargs['pl'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{n}'.format(
            **self.kwargs)


        self.cmd('private-link association create -m {mg} -n {pla} --privatelink {pl} --public-network-access enabled', checks=[
            self.check('name', '{pla}'),
            self.check('properties.publicNetworkAccess', 'Enabled'),
            self.check('properties.privateLink', '{pl}')
        ])

        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())

        # clean
        self.cmd('private-link association delete -m {mg} -n {pla} --yes', self.is_empty())

    @ResourceGroupPreparer(name_prefix='cli_test_resourcemanager_privatelink_list', location='westus')
    def test_list_privatelinkassociation(self, resource_group, resource_group_location):
        account = self.cmd("account show").get_output_in_json()
        tenant_id = account["tenantId"]
        self.kwargs.update({
            'loc': resource_group_location,
            'n': self.create_random_name('privatelink', 30),
            'mg': tenant_id,
            'pla': self.create_guid(),
            'sub': self.get_subscription_id()
        })

        self.cmd('resourcemanagement private-link create -g {rg} -n {n} -l {loc}', checks=[
            self.check('name', '{n}'),
            self.check('location', '{loc}')
        ])
        self.kwargs['pl'] = '/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Authorization/resourceManagementPrivateLinks/{n}'.format(
            **self.kwargs)

        self.cmd('private-link association create -m {mg} -n {pla} --privatelink {pl} --public-network-access enabled', checks=[])

        self.cmd('private-link association list -m {mg}', checks=[
            self.check('value[5].name', '{pla}'),
            self.check('value[5].properties.publicNetworkAccess', 'Enabled'),
            self.check('value[5].properties.privateLink', '{pl}')
        ])


        # clean
        self.cmd('resourcemanagement private-link delete -g {rg} -n {n} --yes', checks=self.is_empty())
        self.cmd('private-link association delete -m {mg} -n {pla} --yes', self.is_empty())


class PrivateLinkAssociationTest(ScenarioTest):
    def test_list_locations(self):
        result = self.cmd('account list-locations').get_output_in_json()
        extended_result = self.cmd('account list-locations --include-extended-locations').get_output_in_json()
        assert isinstance(result, list)
        assert len(extended_result) >= len(result)
        # Verify there is an item with displayName 'East US'.
        assert any('East US' == loc['displayName'] for loc in result)
        assert any('geography' in loc['metadata'] for loc in result)
        assert any('availabilityZoneMappings' in loc for loc in result)


if __name__ == '__main__':
    unittest.main()
