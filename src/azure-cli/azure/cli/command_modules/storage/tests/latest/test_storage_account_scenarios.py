# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import time
import unittest

from azure.cli.testsdk import (ScenarioTest, LocalContextScenarioTest, JMESPathCheck, ResourceGroupPreparer,
                               StorageAccountPreparer, api_version_constraint, live_only, LiveScenarioTest,
                               record_only, KeyVaultPreparer)
from azure.cli.testsdk.decorators import serial_test
from azure.cli.core.profiles import ResourceType
from ..storage_test_util import StorageScenarioMixin
from knack.util import CLIError
from datetime import datetime, timedelta
from azure.cli.testsdk.scenario_tests import AllowLargeResponse


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-12-01')
class StorageAccountTests(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_service_endpoints')
    def test_storage_account_service_endpoints(self, resource_group):
        kwargs = {
            'rg': resource_group,
            'acc': self.create_random_name(prefix='cli', length=24),
            'vnet': 'vnet1',
            'subnet': 'subnet1'
        }
        self.cmd('storage account create -g {rg} -n {acc} --bypass Metrics --default-action Deny --https-only'.format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Metrics'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Deny')])
        self.cmd('storage account update -g {rg} -n {acc} --bypass Logging --default-action Allow'.format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Logging'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Allow')])
        self.cmd('storage account update -g {rg} -n {acc} --set networkRuleSet.default_action=deny'.format(**kwargs),
                 checks=[
                     JMESPathCheck('networkRuleSet.bypass', 'Logging'),
                     JMESPathCheck('networkRuleSet.defaultAction', 'Deny')])

        self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}'.format(**kwargs))
        self.cmd(
            'network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints Microsoft.Storage'.format(
                **kwargs))

        self.cmd('storage account network-rule add -g {rg} --account-name {acc} --ip-address 25.1.2.3'.format(**kwargs))
        # test network-rule add idempotent
        self.cmd('storage account network-rule add -g {rg} --account-name {acc} --ip-address 25.1.2.3'.format(**kwargs))
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {acc} --ip-address 25.2.0.0/24'.format(**kwargs))
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {acc} --vnet-name {vnet} --subnet {subnet}'.format(
                **kwargs))
        self.cmd('storage account network-rule list -g {rg} --account-name {acc}'.format(**kwargs), checks=[
            JMESPathCheck('length(ipRules)', 2),
            JMESPathCheck('length(virtualNetworkRules)', 1)
        ])
        # test network-rule add idempotent
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {acc} --vnet-name {vnet} --subnet {subnet}'.format(
                **kwargs))
        self.cmd('storage account network-rule list -g {rg} --account-name {acc}'.format(**kwargs), checks=[
            JMESPathCheck('length(ipRules)', 2),
            JMESPathCheck('length(virtualNetworkRules)', 1)
        ])
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {acc} --ip-address 25.1.2.3'.format(**kwargs))
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {acc} --vnet-name {vnet} --subnet {subnet}'.format(
                **kwargs))
        self.cmd('storage account network-rule list -g {rg} --account-name {acc}'.format(**kwargs), checks=[
            JMESPathCheck('length(ipRules)', 1),
            JMESPathCheck('length(virtualNetworkRules)', 0)
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_service_endpoints')
    @StorageAccountPreparer()
    def test_storage_account_resource_access_rules(self, resource_group, storage_account):
        self.kwargs = {
            'rg': resource_group,
            'sa': storage_account,
            'rid1': "/subscriptions/a7e99807-abbf-4642-bdec-2c809a96a8bc/resourceGroups/res9407/providers/Microsoft.Synapse/workspaces/testworkspace1",
            'rid2': "/subscriptions/a7e99807-abbf-4642-bdec-2c809a96a8bc/resourceGroups/res9407/providers/Microsoft.Synapse/workspaces/testworkspace2",
            'rid3': "/subscriptions/a7e99807-abbf-4642-bdec-2c809a96a8bc/resourceGroups/res9407/providers/Microsoft.Synapse/workspaces/testworkspace3",
            'tid1': "72f988bf-86f1-41af-91ab-2d7cd011db47",
            'tid2': "72f988bf-86f1-41af-91ab-2d7cd011db47"
        }

        self.cmd(
            'storage account network-rule add -g {rg} --account-name {sa} --resource-id {rid1} --tenant-id {tid1}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 1)
        ])

        # test network-rule add idempotent
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {sa} --resource-id {rid1} --tenant-id {tid1}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 1)
        ])

        # test network-rule add more
        self.cmd(
            'storage account network-rule add -g {rg} --account-name {sa} --resource-id {rid2} --tenant-id {tid1}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 2)
        ])

        self.cmd(
            'storage account network-rule add -g {rg} --account-name {sa} --resource-id {rid3} --tenant-id {tid2}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 3)
        ])

        # remove network-rule
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {sa} --resource-id {rid1} --tenant-id {tid1}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 2)
        ])
        self.cmd(
            'storage account network-rule remove -g {rg} --account-name {sa} --resource-id {rid2} --tenant-id {tid2}')
        self.cmd('storage account network-rule list -g {rg} --account-name {sa}', checks=[
            JMESPathCheck('length(resourceAccessRules)', 1)
        ])

    @serial_test()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_create_storage_account_with_assigned_identity(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        cmd = 'az storage account create -n {} -g {} --sku Standard_LRS --assign-identity'.format(name, resource_group)
        result = self.cmd(cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

    @serial_test()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-06-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_update_storage_account_with_assigned_identity(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --sku Standard_LRS'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('identity', None)])

        update_cmd = 'az storage account update -n {} -g {} --assign-identity'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('identity', result)
        self.assertTrue(result['identity']['principalId'])
        self.assertTrue(result['identity']['tenantId'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    @ResourceGroupPreparer(location='eastus2euap')
    def test_create_storage_account_with_public_network_access(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        result = self.cmd(cmd).get_output_in_json()

        self.assertIn('publicNetworkAccess', result)
        self.assertTrue(result['publicNetworkAccess'] is None)

        name = self.create_random_name(prefix='cli', length=24)
        cmd = 'az storage account create -n {} -g {} --public-network-access Disabled'.format(name, resource_group)
        result = self.cmd(cmd).get_output_in_json()

        self.assertIn('publicNetworkAccess', result)
        self.assertTrue(result['publicNetworkAccess'] == 'Disabled')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    @ResourceGroupPreparer(location='eastus2euap')
    def test_update_storage_account_with_public_network_access(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --public-network-access Enabled'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()
        self.assertIn('publicNetworkAccess', result)
        self.assertTrue(result['publicNetworkAccess'] == 'Enabled')

        update_cmd = 'az storage account update -n {} -g {} --public-network-access Disabled'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('publicNetworkAccess', result)
        self.assertTrue(result['publicNetworkAccess'] == 'Disabled')

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_create_storage_account(self, resource_group, location):
        name = self.create_random_name(prefix='cli', length=24)

        self.cmd('az storage account create -n {} -g {} --sku {} -l {}'.format(
            name, resource_group, 'Standard_LRS', location))

        self.cmd('storage account check-name --name {}'.format(name), checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])

        self.cmd('storage account list -g {}'.format(resource_group), checks=[
            JMESPathCheck('[0].location', 'westus'),
            JMESPathCheck('[0].sku.name', 'Standard_LRS'),
            JMESPathCheck('[0].resourceGroup', resource_group)
        ])

        self.cmd('az storage account show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', location),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('kind', 'StorageV2')
        ])

        self.cmd('az storage account show -n {}'.format(name), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('location', location),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('kind', 'StorageV2')
        ])

        self.cmd('storage account show-connection-string -g {} -n {} --protocol http'.format(
            resource_group, name), checks=[
            JMESPathCheck("contains(connectionString, 'https')", False),
            JMESPathCheck("contains(connectionString, '{}')".format(name), True)])

        self.cmd('storage account update -g {} -n {} --tags foo=bar cat'
                 .format(resource_group, name),
                 checks=JMESPathCheck('tags', {'cat': '', 'foo': 'bar'}))
        self.cmd('storage account update -g {} -n {} --sku Standard_GRS --tags'
                 .format(resource_group, name),
                 checks=[JMESPathCheck('tags', {}),
                         JMESPathCheck('sku.name', 'Standard_GRS')])
        self.cmd('storage account update -g {} -n {} --set tags.test=success'
                 .format(resource_group, name),
                 checks=JMESPathCheck('tags', {'test': 'success'}))
        self.cmd('storage account delete -g {} -n {} --yes'.format(resource_group, name))
        self.cmd('storage account check-name --name {}'.format(name),
                 checks=JMESPathCheck('nameAvailable', True))

        large_file_name = self.create_random_name(prefix='cli', length=24)
        self.cmd('storage account create -g {} -n {} --sku {} --enable-large-file-share'.format(
            resource_group, large_file_name, 'Standard_LRS'))
        self.cmd('az storage account show -n {} -g {}'.format(large_file_name, resource_group), checks=[
            JMESPathCheck('name', large_file_name),
            JMESPathCheck('sku.name', 'Standard_LRS'),
            JMESPathCheck('largeFileSharesState', 'Enabled')
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(location='eastus2euap')
    def test_create_storage_account_with_double_encryption(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {} --require-infrastructure-encryption'.format(
            name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('encryption.requireInfrastructureEncryption', True)
        ])
        self.cmd('az storage account show -n {} -g {}'.format(name, resource_group), checks=[
            JMESPathCheck('name', name),
            JMESPathCheck('encryption.requireInfrastructureEncryption', True)
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(parameter_name_for_location='location', location='southcentralus')
    def test_create_storage_account_v2(self, resource_group, location):
        self.kwargs.update({
            'name': self.create_random_name(prefix='cli', length=24),
            'loc': location
        })

        self.cmd('storage account create -n {name} -g {rg} -l {loc} --kind StorageV2',
                 checks=[JMESPathCheck('kind', 'StorageV2')])

        self.cmd('storage account check-name --name {name}', checks=[
            JMESPathCheck('nameAvailable', False),
            JMESPathCheck('reason', 'AlreadyExists')
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2016-01-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_sku(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('sku.name', 'Standard_RAGRS')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2017-10-01')
    @ResourceGroupPreparer(location='southcentralus')
    def test_storage_create_default_kind(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('kind', 'StorageV2')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', True)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns true'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', True)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2018-02-01')
    @ResourceGroupPreparer(location='southcentralus', name_prefix='cli_storage_account_hns')
    def test_storage_create_with_hns_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 --hns false'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('isHnsEnabled', False)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(location='eastus2euap', name_prefix='cli_storage_account_encryption')
    def test_storage_create_with_encryption_key_type(self, resource_group):
        name = self.create_random_name(prefix='cliencryption', length=24)
        create_cmd = 'az storage account create -n {} -g {} --kind StorageV2 -t Account -q Service'.format(
            name, resource_group)
        self.cmd(create_cmd, checks=[
            JMESPathCheck('encryption.services.queue', None),
            JMESPathCheck('encryption.services.table.enabled', True),
            JMESPathCheck('encryption.services.table.keyType', 'Account'),
        ])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    def test_storage_create_with_public_access(self, resource_group):
        name1 = self.create_random_name(prefix='cli', length=24)
        name2 = self.create_random_name(prefix='cli', length=24)
        name3 = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {} --allow-blob-public-access'.format(name1, resource_group),
                 checks=[JMESPathCheck('allowBlobPublicAccess', True)])

        self.cmd('az storage account create -n {} -g {} --allow-blob-public-access true'.format(name2, resource_group),
                 checks=[JMESPathCheck('allowBlobPublicAccess', True)])

        self.cmd('az storage account create -n {} -g {} --allow-blob-public-access false'.format(name3, resource_group),
                 checks=[JMESPathCheck('allowBlobPublicAccess', False)])

    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    @StorageAccountPreparer(name_prefix='blob')
    def test_storage_update_with_public_access(self, storage_account):
        self.cmd('az storage account update -n {} --allow-blob-public-access'.format(storage_account),
                 checks=[JMESPathCheck('allowBlobPublicAccess', True)])

        self.cmd('az storage account update -n {} --allow-blob-public-access true'.format(storage_account),
                 checks=[JMESPathCheck('allowBlobPublicAccess', True)])

        self.cmd('az storage account update -n {} --allow-blob-public-access false'.format(storage_account),
                 checks=[JMESPathCheck('allowBlobPublicAccess', False)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    def test_storage_create_with_min_tls(self, resource_group):
        name1 = self.create_random_name(prefix='cli', length=24)
        name2 = self.create_random_name(prefix='cli', length=24)
        name3 = self.create_random_name(prefix='cli', length=24)
        name4 = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {}'.format(name1, resource_group),
                 checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_0')])

        self.cmd('az storage account create -n {} -g {} --min-tls-version TLS1_0'.format(name2, resource_group),
                 checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_0')])

        self.cmd('az storage account create -n {} -g {} --min-tls-version TLS1_1'.format(name3, resource_group),
                 checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_1')])

        self.cmd('az storage account create -n {} -g {} --min-tls-version TLS1_2'.format(name4, resource_group),
                 checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_2')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    @StorageAccountPreparer(name_prefix='tls')
    def test_storage_update_with_min_tls(self, storage_account, resource_group):
        self.cmd('az storage account show -n {} -g {}'.format(storage_account, resource_group),
                 checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_0')])

        self.cmd('az storage account update -n {} -g {} --min-tls-version TLS1_1'.format(
            storage_account, resource_group), checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_1')])

        self.cmd('az storage account update -n {} -g {} --min-tls-version TLS1_2'.format(
            storage_account, resource_group), checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_2')])

        self.cmd('az storage account update -n {} -g {} --min-tls-version TLS1_0'.format(
            storage_account, resource_group), checks=[JMESPathCheck('minimumTlsVersion', 'TLS1_0')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account_routing')
    def test_storage_account_with_routing_preference(self, resource_group):
        # Create Storage Account with Publish MicrosoftEndpoint, choose MicrosoftRouting
        name1 = self.create_random_name(prefix='clirouting', length=24)
        create_cmd1 = 'az storage account create -n {} -g {} --routing-choice MicrosoftRouting --publish-microsoft-endpoint true'.format(
            name1, resource_group)
        self.cmd(create_cmd1, checks=[
            JMESPathCheck('routingPreference.publishInternetEndpoints', None),
            JMESPathCheck('routingPreference.publishMicrosoftEndpoints', True),
            JMESPathCheck('routingPreference.routingChoice', 'MicrosoftRouting'),
        ])

        # Update Storage Account with Publish InternetEndpoint
        update_cmd1 = 'az storage account update -n {} -g {} --routing-choice InternetRouting --publish-microsoft-endpoint false --publish-internet-endpoint true'.format(
            name1, resource_group)
        self.cmd(update_cmd1, checks=[
            JMESPathCheck('routingPreference.publishInternetEndpoints', True),
            JMESPathCheck('routingPreference.publishMicrosoftEndpoints', False),
            JMESPathCheck('routingPreference.routingChoice', 'InternetRouting'),
        ])

        # Create Storage Account with Publish InternetEndpoint, choose InternetRouting
        name2 = self.create_random_name(prefix='clirouting', length=24)
        create_cmd2 = 'az storage account create -n {} -g {} --routing-choice InternetRouting --publish-internet-endpoints true --publish-microsoft-endpoints false'.format(
            name2, resource_group)
        self.cmd(create_cmd2, checks=[
            JMESPathCheck('routingPreference.publishInternetEndpoints', True),
            JMESPathCheck('routingPreference.publishMicrosoftEndpoints', False),
            JMESPathCheck('routingPreference.routingChoice', 'InternetRouting'),
        ])

        # Update Storage Account with MicrosoftRouting routing choice
        update_cmd2 = 'az storage account update -n {} -g {} --routing-choice MicrosoftRouting'\
            .format(name2, resource_group)

        self.cmd(update_cmd2, checks=[
            JMESPathCheck('routingPreference.routingChoice', 'MicrosoftRouting'),
        ])

        # Create without any routing preference
        name3 = self.create_random_name(prefix='clirouting', length=24)
        create_cmd3 = 'az storage account create -n {} -g {}'.format(
            name3, resource_group)
        self.cmd(create_cmd3, checks=[
            JMESPathCheck('routingPreference', None),
        ])

        # Update Storage Account with Publish MicrosoftEndpoint, choose MicrosoftRouting
        update_cmd3 = 'az storage account update -n {} -g {} --routing-choice MicrosoftRouting --publish-internet-endpoints false --publish-microsoft-endpoints true'\
            .format(name3, resource_group)

        self.cmd(update_cmd3, checks=[
            JMESPathCheck('routingPreference.publishInternetEndpoints', False),
            JMESPathCheck('routingPreference.publishMicrosoftEndpoints', True),
            JMESPathCheck('routingPreference.routingChoice', 'MicrosoftRouting'),
        ])

    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-01-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    def test_storage_account_with_shared_key_access(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {} --allow-shared-key-access'.format(name, resource_group),
                 checks=[JMESPathCheck('allowSharedKeyAccess', True)])

        self.cmd('az storage account create -n {} -g {} --allow-shared-key-access false'.format(name, resource_group),
                 checks=[JMESPathCheck('allowSharedKeyAccess', False)])

        self.cmd('az storage account create -n {} -g {} --allow-shared-key-access true'.format(name, resource_group),
                 checks=[JMESPathCheck('allowSharedKeyAccess', True)])

        self.cmd('az storage account update -n {} --allow-shared-key-access false'.format(name),
                 checks=[JMESPathCheck('allowSharedKeyAccess', False)])

        self.cmd('az storage account update -n {} --allow-shared-key-access true'.format(name),
                 checks=[JMESPathCheck('allowSharedKeyAccess', True)])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-02-01')
    @ResourceGroupPreparer(location='eastus', name_prefix='cli_storage_account')
    def test_storage_account_with_key_and_sas_policy(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.cmd('az storage account create -n {} -g {}'.format(name, resource_group),
                 checks=[JMESPathCheck('keyPolicy', None),
                         JMESPathCheck('sasPolicy', None)])

        self.cmd('az storage account create -n {} -g {} --key-exp-days 3'.format(name, resource_group),
                 checks=[JMESPathCheck('keyPolicy.keyExpirationPeriodInDays', 3),
                         JMESPathCheck('sasPolicy', None)])

        self.cmd('az storage account create -n {} -g {} --sas-exp 1.23:59:59'.format(name, resource_group),
                 checks=[JMESPathCheck('keyPolicy.keyExpirationPeriodInDays', 3),
                         JMESPathCheck('sasPolicy.sasExpirationPeriod', '1.23:59:59')])

        self.cmd('az storage account update -n {} -g {} --key-exp-days 100000'.format(name, resource_group),
                 checks=[JMESPathCheck('keyPolicy.keyExpirationPeriodInDays', 100000),
                         JMESPathCheck('sasPolicy.sasExpirationPeriod', '1.23:59:59')])

        self.cmd('az storage account update -n {} -g {} --sas-exp 100000.00:00:00'.format(name, resource_group),
                 checks=[JMESPathCheck('keyPolicy.keyExpirationPeriodInDays', 100000),
                         JMESPathCheck('sasPolicy.sasExpirationPeriod', '100000.00:00:00')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer()
    def test_storage_account_with_default_share_permission(self, resource_group):
        self.kwargs = {
            'name': self.create_random_name(prefix='cli', length=24),
            'rg': resource_group}

        self.cmd('az storage account create -n {name} -g {rg}',
                 checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        self.cmd('az storage account create -n {name} -g {rg} --default-share-permission StorageFileDataSmbShareReader',
                 checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication.defaultSharePermission',
                                       'StorageFileDataSmbShareReader')])

        self.cmd('az storage account update -n {name} -g {rg} --default-share-permission None',
                 checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication.defaultSharePermission',
                                       'None')])

    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-01-01')
    @ResourceGroupPreparer(location='westus', name_prefix='cli_storage_account')
    def test_storage_account_with_nfs(self, resource_group):
        self.kwargs = {
            'name1': self.create_random_name(prefix='sa1', length=24),
            'name2': self.create_random_name(prefix='sa2', length=24),
            'name3': self.create_random_name(prefix='sa3', length=24),
            'vnet': self.create_random_name(prefix='vnet', length=10),
            'subnet': self.create_random_name(prefix='subnet', length=10),
            'rg': resource_group
        }

        result = self.cmd('network vnet create -g {rg} -n {vnet} --subnet-name {subnet}').get_output_in_json()
        self.kwargs['subnet_id'] = result['newVNet']['subnets'][0]['id']
        self.cmd(
            'network vnet subnet update -g {rg} --vnet-name {vnet} -n {subnet} --service-endpoints Microsoft.Storage')
        self.cmd('storage account create -n {name1} -g {rg} --subnet {subnet_id} '
                 '--default-action Deny --hns --sku Standard_LRS --enable-nfs-v3 true',
                 checks=[JMESPathCheck('enableNfsV3', True)])

        self.cmd('storage account create -n {name2} -g {rg} --enable-nfs-v3 false',
                 checks=[JMESPathCheck('enableNfsV3', False)])

        self.cmd('storage account create -n {name3} -g {rg} --enable-nfs-v3 --vnet-name {vnet} '
                 '--subnet {subnet} --default-action Deny --hns --sku Standard_LRS ',
                 checks=[JMESPathCheck('enableNfsV3', True)])

    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    @ResourceGroupPreparer(location='centraluseuap', name_prefix='cli_storage_account')
    def test_storage_account_with_alw(self, resource_group):
        self.kwargs = {
            'name1': self.create_random_name(prefix='sa1', length=24),
            'name2': self.create_random_name(prefix='sa2', length=24),
            'rg': resource_group
        }

        # test success case during create
        result = self.cmd('storage account create -n {name1} -g {rg} --enable-alw --immutability-period 10 '
                 '--immutability-state Disabled --allow-append').get_output_in_json()
        self.assertIn('immutableStorageWithVersioning', result)
        self.assertEqual(result['immutableStorageWithVersioning']['enabled'], True)
        self.assertEqual(result['immutableStorageWithVersioning']['immutabilityPolicy']['allowProtectedAppendWrites'], True)
        self.assertEqual(result['immutableStorageWithVersioning']['immutabilityPolicy']['immutabilityPeriodSinceCreationInDays'], 10)
        self.assertEqual(result['immutableStorageWithVersioning']['immutabilityPolicy']['state'], 'Disabled')

        # test failure cases during create
        from azure.cli.core.azclierror import InvalidArgumentValueError
        from azure.core.exceptions import HttpResponseError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('storage account create -n {name2} -g {rg} --enable-alw false --immutability-period 10 '
                              '--immutability-state Disabled --allow-append')

        # missing required parameter --immutability-state
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account create -n {name2} -g {rg} --enable-alw --immutability-period 10  --allow-append')

        # cannot have create policy with Locked state
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account create -n {name2} -g {rg} --enable-alw --immutability-period 10 '
                              '--immutability-state Locked --allow-append')

        # test success case during update
        result = self.cmd('storage account update -n {name1} --immutability-period 15 '
                          '--immutability-state Unlocked --allow-append false').get_output_in_json()
        self.assertEqual(result['immutableStorageWithVersioning']['immutabilityPolicy']['allowProtectedAppendWrites'],
                         False)
        self.assertEqual(
            result['immutableStorageWithVersioning']['immutabilityPolicy']['immutabilityPeriodSinceCreationInDays'], 15)
        self.assertEqual(result['immutableStorageWithVersioning']['immutabilityPolicy']['state'], 'Unlocked')

        # test failure cases during update
        self.cmd('storage account create -n {name2} -g {rg} --enable-alw false')

        # cannot add policy when alw is disabled
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account update -n {name2} --immutability-period 10 '
                     '--immutability-state Disabled --allow-append')

        self.cmd('storage account update -n {name1} --immutability-state Disabled')

        # cannot directly change the state to Locked from Disabled
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account update -n {name1} --immutability-state Locked')

        self.cmd('storage account update -n {name1} --immutability-state UnLocked')
        self.cmd('storage account update -n {name1} --immutability-state Locked')

        # cannot reduce immutability-period when locked
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account update -n {name1} --immutability-period 10')

        # cannot unlock a locked policy
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account update -n {name1} --immutability-state UnLocked')

        # cannot changed allowProtectedAppendWrites for locked policy
        with self.assertRaises(HttpResponseError):
            self.cmd('storage account update -n {name1} --allow-append')

    def test_show_usage(self):
        self.cmd('storage account show-usage -l westus', checks=JMESPathCheck('name.value', 'StorageAccounts'))

    def test_show_usage_no_location(self):
        with self.assertRaises(SystemExit):
            self.cmd('storage account show-usage')

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_logging_operations(self, resource_group, storage_account):
        connection_string = self.cmd(
            'storage account show-connection-string -g {} -n {} -otsv'.format(resource_group, storage_account)).output

        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('blob.read', False),
            JMESPathCheck('blob.retentionPolicy.enabled', False)
        ])

        self.cmd('storage logging update --services b --log r --retention 1 '
                 '--service b --connection-string {}'.format(connection_string))

        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('blob.read', True),
            JMESPathCheck('blob.retentionPolicy.enabled', True),
            JMESPathCheck('blob.retentionPolicy.days', 1)
        ])

        self.cmd('storage logging off --connection-string {}'.format(connection_string))

        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('blob.delete', False),
            JMESPathCheck('blob.write', False),
            JMESPathCheck('blob.read', False),
            JMESPathCheck('blob.retentionPolicy.enabled', False),
            JMESPathCheck('blob.retentionPolicy.days', None),
            JMESPathCheck('queue.delete', False),
            JMESPathCheck('queue.write', False),
            JMESPathCheck('queue.read', False),
            JMESPathCheck('queue.retentionPolicy.enabled', False),
            JMESPathCheck('queue.retentionPolicy.days', None),
            JMESPathCheck('table.delete', False),
            JMESPathCheck('table.write', False),
            JMESPathCheck('table.read', False),
            JMESPathCheck('table.retentionPolicy.enabled', False),
            JMESPathCheck('table.retentionPolicy.days', None)
        ])

        # Table service
        with self.assertRaisesRegex(CLIError, "incorrect usage: for table service, the supported version for logging is `1.0`"):
            self.cmd('storage logging update --services t --log r --retention 1 '
                     '--version 2.0 --connection-string {}'.format(connection_string))

        # Set version to 1.0
        self.cmd('storage logging update --services t --log r --retention 1 --version 1.0 --connection-string {} '
                 .format(connection_string))
        time.sleep(10)
        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('table.version', '1.0'),
            JMESPathCheck('table.delete', False),
            JMESPathCheck('table.write', False),
            JMESPathCheck('table.read', True),
            JMESPathCheck('table.retentionPolicy.enabled', True),
            JMESPathCheck('table.retentionPolicy.days', 1)
        ])

        # Use default version
        self.cmd('storage logging update --services t --log r --retention 1 --connection-string {}'.format(
            connection_string))
        time.sleep(10)
        self.cmd('storage logging show --connection-string {}'.format(connection_string), checks=[
            JMESPathCheck('table.version', '1.0'),
            JMESPathCheck('table.delete', False),
            JMESPathCheck('table.write', False),
            JMESPathCheck('table.read', True),
            JMESPathCheck('table.retentionPolicy.enabled', True),
            JMESPathCheck('table.retentionPolicy.days', 1)
        ])

    @live_only()
    @ResourceGroupPreparer()
    def test_logging_error_operations(self, resource_group):
        # BlobStorage doesn't support logging for some services
        blob_storage = self.create_random_name(prefix='blob', length=24)
        self.cmd('storage account create -g {} -n {} --kind BlobStorage --access-tier hot --https-only'.format(
            resource_group, blob_storage))

        blob_connection_string = self.cmd(
            'storage account show-connection-string -g {} -n {} -otsv'.format(resource_group, blob_storage)).output
        with self.assertRaisesRegex(CLIError, "Your storage account doesn't support logging"):
            self.cmd('storage logging show --services q --connection-string {}'.format(blob_connection_string))

        # PremiumStorage doesn't support logging for some services
        premium_storage = self.create_random_name(prefix='premium', length=24)
        self.cmd('storage account create -g {} -n {} --sku Premium_LRS --https-only'.format(
            resource_group, premium_storage))

        premium_connection_string = self.cmd(
            'storage account show-connection-string -g {} -n {} -otsv'.format(resource_group, premium_storage)).output
        with self.assertRaisesRegex(CLIError, "Your storage account doesn't support logging"):
            self.cmd('storage logging show --services q --connection-string {}'.format(premium_connection_string))

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_metrics_operations(self, resource_group, storage_account_info):
        self.storage_cmd('storage metrics show', storage_account_info) \
            .assert_with_checks(JMESPathCheck('file.hour.enabled', True),
                                JMESPathCheck('file.minute.enabled', False))

        self.storage_cmd('storage metrics update --services f --api true --hour true --minute true --retention 1 ',
                         storage_account_info)

        self.storage_cmd('storage metrics show', storage_account_info).assert_with_checks(
            JMESPathCheck('file.hour.enabled', True),
            JMESPathCheck('file.minute.enabled', True))

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer(parameter_name='account_1')
    @StorageAccountPreparer(parameter_name='account_2')
    def test_list_storage_accounts(self, account_1, account_2):
        accounts_list = self.cmd('az storage account list').get_output_in_json()
        assert len(accounts_list) >= 2
        assert next(acc for acc in accounts_list if acc['name'] == account_1)
        assert next(acc for acc in accounts_list if acc['name'] == account_2)

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_renew_account_key(self, resource_group, storage_account):
        original_keys = self.cmd('storage account keys list -g {} -n {}'
                                 .format(resource_group, storage_account)).get_output_in_json()
        # key1 = keys_result[0]
        # key2 = keys_result[1]
        assert original_keys[0] and original_keys[1]

        renewed_keys = self.cmd('storage account keys renew -g {} -n {} --key primary'
                                .format(resource_group, storage_account)).get_output_in_json()
        print(renewed_keys)
        print(original_keys)
        assert renewed_keys[0] != original_keys[0]
        assert renewed_keys[1] == original_keys[1]

        original_keys = renewed_keys
        renewed_keys = self.cmd('storage account keys renew -g {} -n {} --key secondary'
                                .format(resource_group, storage_account)).get_output_in_json()
        assert renewed_keys[0] == original_keys[0]
        assert renewed_keys[1] != original_keys[1]

    @record_only()   # Need to configure domain service first
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_renew_account_kerb_key(self, resource_group):
        name = self.create_random_name(prefix='clistoragekerbkey', length=24)
        self.kwargs = {'sc': name, 'rg': resource_group}
        self.cmd('storage account create -g {rg} -n {sc} -l eastus2euap --enable-files-aadds')
        self.cmd('storage account keys list -g {rg} -n {sc}', checks=JMESPathCheck('length(@)', 4))
        original_keys = self.cmd('storage account keys list -g {rg} -n {sc} --expand-key-type kerb',
                                 checks=JMESPathCheck('length(@)', 4)).get_output_in_json()

        renewed_access_keys = self.cmd('storage account keys renew -g {rg} -n {sc} --key secondary').get_output_in_json()
        assert renewed_access_keys[0] == original_keys[0]
        assert renewed_access_keys[1] != original_keys[1]
        renewed_kerb_keys = self.cmd(
            'storage account keys renew -g {rg} -n {sc} --key primary --key-type kerb').get_output_in_json()
        assert renewed_kerb_keys[2] != original_keys[2]
        assert renewed_kerb_keys[3] == original_keys[3]

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_create_account_sas(self, storage_account_info):
        from azure.cli.core.azclierror import RequiredArgumentMissingError
        with self.assertRaises(RequiredArgumentMissingError):
            self.cmd('storage account generate-sas --resource-types o --services b --expiry 2000-01-01 '
                     '--permissions r --account-name ""')

        invalid_connection_string = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;"
        with self.assertRaises(RequiredArgumentMissingError):
            self.cmd('storage account generate-sas --resource-types o --services b --expiry 2000-01-01 '
                     '--permissions r --connection-string {}'.format(invalid_connection_string))

        sas = self.storage_cmd('storage account generate-sas --resource-types o --services b '
                               '--expiry 2046-12-31T08:23Z --permissions r --https-only ',
                               storage_account_info).output
        self.assertIn('sig=', sas, 'SAS token {} does not contain sig segment'.format(sas))
        self.assertIn('se=', sas, 'SAS token {} does not contain se segment'.format(sas))

    def test_list_locations(self):
        self.cmd('az account list-locations',
                 checks=[JMESPathCheck("[?name=='westus'].displayName | [0]", 'West US')])

    @ResourceGroupPreparer(location='southcentralus')
    @StorageAccountPreparer(location='southcentralus')
    @KeyVaultPreparer(location='southcentralus')
    def test_customer_managed_key(self, resource_group, storage_account, key_vault):
        self.kwargs = {'rg': resource_group, 'sa': storage_account, 'vt': key_vault}

        keyvault_result = self.cmd('az keyvault show -n {vt} -g {rg}').get_output_in_json()
        self.kwargs['vid'] = keyvault_result['id']
        self.kwargs['vtn'] = keyvault_result['properties']['vaultUri']

        self.kwargs['ver'] = self.cmd("az keyvault key create -n testkey -p software --vault-name {vt} "
                                      "-otsv --query 'key.kid'").output.rsplit('/', 1)[1].rstrip('\n')
        self.kwargs['oid'] = self.cmd("az storage account update -n {sa} -g {rg} --assign-identity "
                                      "-otsv --query 'identity.principalId'").output.strip('\n')

        self.cmd('az keyvault set-policy -n {vt} --object-id {oid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')
        self.cmd('az keyvault update -n {vt} -g {rg} --set properties.enableSoftDelete=true')
        self.cmd('az resource update --id {vid} --set properties.enablePurgeProtection=true')

        # Enable key auto-rotation
        result = self.cmd('az storage account update -n {sa} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey ').get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Pin to a version and opt out for key auto-rotation
        result = self.cmd('az storage account update -n {sa} -g {rg} '
                          '--encryption-key-version {ver}').get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], self.kwargs['ver'])
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Enable key auto-rotation again
        result = self.cmd('az storage account update -n {sa} -g {rg} '
                          '--encryption-key-version ""').get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], "")
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Change Key name
        self.cmd("az keyvault key create -n newkey -p software --vault-name {vt} ")
        result = self.cmd('az storage account update -n {sa} -g {rg} '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name "newkey"').get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'newkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], "")
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Change Key source
        result = self.cmd('az storage account update -n {sa} -g {rg} '
                          '--encryption-key-source Microsoft.Storage').get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Storage")

    @ResourceGroupPreparer(location='eastus2euap')
    @KeyVaultPreparer(location='eastus2euap')
    def test_user_assigned_identity(self, resource_group, key_vault):
        self.kwargs = {
            'rg': resource_group,
            'sa1': self.create_random_name(prefix='sa1', length=24),
            'sa2': self.create_random_name(prefix='sa2', length=24),
            'sa3': self.create_random_name(prefix='sa3', length=24),
            'identity': self.create_random_name(prefix='id', length=24),
            'vt': key_vault
        }
        # Prepare managed identity
        identity = self.cmd('az identity create -n {identity} -g {rg}').get_output_in_json()
        self.kwargs['iid'] = identity['id']
        self.kwargs['oid'] = identity['principalId']

        # Prepare key vault
        keyvault = self.cmd('az keyvault show -n {vt} -g {rg} ').get_output_in_json()
        self.kwargs['vid'] = keyvault['id']
        self.kwargs['vtn'] = keyvault['properties']['vaultUri']

        self.kwargs['ver'] = self.cmd("az keyvault key create -n testkey -p software --vault-name {vt} "
                                      "-otsv --query 'key.kid'").output.rsplit('/', 1)[1].rstrip('\n')

        # Make UAI access to keyvault
        self.cmd('az keyvault set-policy -n {vt} --object-id {oid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')
        self.cmd('az keyvault update -n {vt} -g {rg} --set properties.enableSoftDelete=true')
        self.cmd('az resource update --id {vid} --set properties.enablePurgeProtection=true')

        # CMK at create with UAI
        result = self.cmd('az storage account create -n {sa1} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--key-vault-user-identity-id {iid} '
                          '--identity-type UserAssigned '
                          '--user-identity-id {iid}').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['identity']['type'], 'UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Clear a UserAssigned identity when in use with CMK will break access to the account
        result = self.cmd('az storage account update -n {sa1} -g {rg} --identity-type None ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['identity']['type'], 'None')
        self.assertEqual(result['identity']['userAssignedIdentities'], None)

        # Recover from Identity clear
        result = self.cmd('az storage account update -n {sa1} -g {rg} --identity-type UserAssigned --user-identity-id {iid}').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['identity']['type'], 'UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # CMK with UAI -> CMK with SAI
        # 1. Add System Assigned Identity if it does not exist.
        result = self.cmd('az storage account update -n {sa1} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--identity-type SystemAssigned,UserAssigned ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned,UserAssigned')

        # 2. Add GET/WRAP/UNWRAP permissions on $KeyVaultUri for System Assigned identity.
        self.kwargs['oid'] = self.cmd("az storage account update -n {sa1} -g {rg} --assign-identity "
                                      "-otsv --query 'identity.principalId'").output.strip('\n')

        self.cmd('az keyvault set-policy -n {vt} --object-id {oid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')

        # 3. Update encryption.identity to use the SystemAssigned identity. SAI must have access to existing KeyVault.
        result = self.cmd('az storage account update -n {sa1} -g {rg} '
                          '--key-vault-user-identity-id "" ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned')
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], "")

        # CMK with SAI -> MMK
        result = self.cmd('az storage account update -n {sa1} -g {rg} '
                          '--encryption-key-source Microsoft.Storage ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa1'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Storage")
        self.assertEqual(result['encryption']['keyVaultProperties'], None)

        # MMK at create
        result = self.cmd('az storage account create -n {sa2} -g {rg} --encryption-key-source Microsoft.Storage')\
            .get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Storage")
        self.assertEqual(result['encryption']['keyVaultProperties'], None)

        # CMK with UAI and add SAI at create
        result = self.cmd('az storage account create -n {sa3} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--key-vault-user-identity-id {iid} '
                          '--identity-type SystemAssigned,UserAssigned '
                          '--user-identity-id {iid}').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa3'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned,UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'],
                         self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # MMK -> CMK wth UAI
        self.kwargs['sid'] = self.cmd("az storage account update -n {sa2} -g {rg} --assign-identity "
                                      "-otsv --query 'identity.principalId'").output.strip('\n')
        self.cmd('az keyvault set-policy -n {vt} --object-id {sid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')
        self.cmd('az keyvault set-policy -n {vt} --object-id {sid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')

        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--identity-type SystemAssigned ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned')
        self.assertEqual(result['identity']['principalId'], self.kwargs['sid'])
        self.assertEqual(result['encryption']['encryptionIdentity'], None)
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # CMK wth UAI -> MMK
        result = self.cmd('az storage account create -n {sa2} -g {rg} --encryption-key-source Microsoft.Storage')\
            .get_output_in_json()

        self.assertEqual(result['encryption']['keySource'], "Microsoft.Storage")
        self.assertEqual(result['encryption']['keyVaultProperties'], None)

        # MMK -> CMK wth SAI
        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--identity-type SystemAssigned ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned')
        self.assertEqual(result['identity']['principalId'], self.kwargs['sid'])
        self.assertEqual(result['encryption']['encryptionIdentity'], None)
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Clear a SystemAssigned identity when in use with CMK will break access to the account
        result = self.cmd('az storage account update -n {sa2} -g {rg} --identity-type None ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'None')
        self.assertEqual(result['identity']['userAssignedIdentities'], None)

        # Recover account if SystemAssignedIdentity used for CMK is cleared
        # 1. Create a new $UserAssignedIdentity that has access to $KeyVaultUri and update the account to use the new $UserAssignedIdentity for encryption (if not present already).
        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--identity-type UserAssigned '
                          '--user-identity-id {iid} '
                          '--key-vault-user-identity-id {iid} ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # 2. Update account to use SAI,UAI identity.
        result = self.cmd('az storage account update -n {sa2} -g {rg} --identity-type SystemAssigned,UserAssigned')\
            .get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned,UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # 3. Clear the $UserAssignedIdentity used for encryption.
        result = self.cmd('az storage account update -n {sa2} -g {rg} --key-vault-user-identity-id ""')\
            .get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned,UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], '')
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # 4. Remove $UserAssignedIdentity from the top level identity bag.
        result = self.cmd('az storage account update -n {sa2} -g {rg} --identity-type SystemAssigned')\
            .get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned')
        self.assertEqual(result['identity']['userAssignedIdentities'], None)
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], '')
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        self.kwargs['sid'] = result['identity']['principalId']

        # CMK with SAI -> CMK with UAI
        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--key-vault-user-identity-id {iid} '
                          '--identity-type SystemAssigned,UserAssigned '
                          '--user-identity-id {iid}').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'SystemAssigned,UserAssigned')
        self.assertIn(self.kwargs['iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # CMK with UAI1 -> CMK with UAI2
        self.kwargs['new_id'] = self.create_random_name(prefix='newid', length=24)
        identity = self.cmd('az identity create -n {new_id} -g {rg}').get_output_in_json()
        self.kwargs['new_iid'] = identity['id']
        self.kwargs['new_oid'] = identity['principalId']

        self.cmd('az keyvault set-policy -n {vt} --object-id {new_oid} -g {rg} '
                 '--key-permissions get wrapKey unwrapKey recover')

        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--encryption-key-source Microsoft.Keyvault '
                          '--encryption-key-vault {vtn} '
                          '--encryption-key-name testkey '
                          '--key-vault-user-identity-id {new_iid} '
                          '--identity-type UserAssigned '
                          '--user-identity-id {new_iid}').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'UserAssigned')
        self.assertIn(self.kwargs['new_iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['new_iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

        # Clear a UserAssigned identity when in use with CMK will break access to the account
        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--identity-type None ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'None')
        self.assertEqual(result['identity']['userAssignedIdentities'], None)

        # Recover from Identity clear
        result = self.cmd('az storage account update -n {sa2} -g {rg} '
                          '--identity-type UserAssigned '
                          '--user-identity-id {new_iid} '
                          '--key-vault-user-identity-id {new_iid} ').get_output_in_json()

        self.assertEqual(result['name'], self.kwargs['sa2'])
        self.assertEqual(result['identity']['type'], 'UserAssigned')
        self.assertIn(self.kwargs['new_iid'], result['identity']['userAssignedIdentities'])
        self.assertEqual(result['encryption']['encryptionIdentity']['encryptionUserAssignedIdentity'], self.kwargs['new_iid'])
        self.assertEqual(result['encryption']['keySource'], "Microsoft.Keyvault")
        self.assertEqual(result['encryption']['keyVaultProperties']['keyName'], 'testkey')
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVaultUri'], self.kwargs['vtn'])
        self.assertEqual(result['encryption']['keyVaultProperties']['keyVersion'], None)
        self.assertIn('lastKeyRotationTimestamp', result['encryption']['keyVaultProperties'])

    @ResourceGroupPreparer()
    @StorageAccountPreparer()
    def test_storage_account_show_exit_codes(self, resource_group, storage_account):
        self.kwargs = {'rg': resource_group, 'sa': storage_account}

        self.assertEqual(self.cmd('storage account show -g {rg} -n {sa}').exit_code, 0)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show text_causing_parsing_error')
        self.assertEqual(ex.exception.code, 2)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show -g fake_group -n {sa}')
        self.assertEqual(ex.exception.code, 3)

        with self.assertRaises(SystemExit) as ex:
            self.cmd('storage account show -g {rg} -n fake_account')
        self.assertEqual(ex.exception.code, 3)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind='StorageV2')
    def test_management_policy(self, resource_group, storage_account):
        import os
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        policy_file = os.path.join(curr_dir, 'mgmt_policy.json').replace('\\', '\\\\')

        self.kwargs = {'rg': resource_group, 'sa': storage_account, 'policy': policy_file}
        result = self.cmd('storage account blob-service-properties update --enable-last-access-tracking true -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['enable'], True)

        self.cmd('storage account management-policy create --account-name {sa} -g {rg} --policy @"{policy}"',
                 checks=[JMESPathCheck('policy.rules[0].name', 'olcmtest'),
                         JMESPathCheck('policy.rules[0].enabled', True),
                         JMESPathCheck('policy.rules[0].definition.actions.baseBlob.tierToCool.daysAfterLastAccessTimeGreaterThan', 30),
                         JMESPathCheck('policy.rules[0].definition.actions.baseBlob.tierToArchive.daysAfterModificationGreaterThan', 90),
                         JMESPathCheck('policy.rules[0].definition.actions.baseBlob.delete.daysAfterModificationGreaterThan', 1000),
                         JMESPathCheck('policy.rules[0].definition.actions.snapshot.tierToCool.daysAfterCreationGreaterThan', 30),
                         JMESPathCheck('policy.rules[0].definition.actions.snapshot.tierToArchive.daysAfterCreationGreaterThan', 90),
                         JMESPathCheck('policy.rules[0].definition.actions.snapshot.delete.daysAfterCreationGreaterThan', 1000),
                         JMESPathCheck('policy.rules[0].definition.actions.version.tierToCool.daysAfterCreationGreaterThan', 30),
                         JMESPathCheck('policy.rules[0].definition.actions.version.tierToArchive.daysAfterCreationGreaterThan', 90),
                         JMESPathCheck('policy.rules[0].definition.actions.version.delete.daysAfterCreationGreaterThan', 1000),
                         JMESPathCheck('policy.rules[0].definition.filters.blobTypes[0]', "blockBlob"),
                         JMESPathCheck('policy.rules[0].definition.filters.prefixMatch[0]', "olcmtestcontainer1")])

        self.cmd('storage account management-policy update --account-name {sa} -g {rg}'
                 ' --set "policy.rules[0].name=newname"')
        self.cmd('storage account management-policy show --account-name {sa} -g {rg}',
                 checks=JMESPathCheck('policy.rules[0].name', 'newname'))
        self.cmd('storage account management-policy delete --account-name {sa} -g {rg}')
        self.cmd('storage account management-policy show --account-name {sa} -g {rg}', expect_failure=True)

    @record_only()   # Need to configure domain service first
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds false'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @record_only()  # Need to configure domain service first
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_aadds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {}'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-aadds true'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @record_only()  # Need to configure domain service first
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds false'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @record_only()  # Need to configure domain service first
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_aadds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} --enable-files-aadds true'.format(name, resource_group)
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AADDS')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds --domain-name
        {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid
        {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name
        })
        result = self.cmd("storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds false").get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_create_storage_account_with_files_adds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds true --domain-name
        {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid
        {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(create_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}
        --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}
        --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds_false(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])

        update_cmd = 'az storage account update -n {} -g {} --enable-files-adds false'.format(name, resource_group)
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'None')

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer()
    def test_update_storage_account_with_files_adds_true(self, resource_group):
        name = self.create_random_name(prefix='cli', length=24)
        create_cmd = 'az storage account create -n {} -g {} -l eastus2euap'.format(name, resource_group)
        self.cmd(create_cmd, checks=[JMESPathCheck('azureFilesIdentityBasedAuthentication', None)])
        self.kwargs.update({
            'rg': resource_group,
            'sc': name,
            'domain_name': 'mydomain.com',
            'net_bios_domain_name': 'mydomain.com',
            'forest_name': 'mydomain.com',
            'domain_guid': '12345678-1234-1234-1234-123456789012',
            'domain_sid': 'S-1-5-21-1234567890-1234567890-1234567890',
            'azure_storage_sid': 'S-1-5-21-1234567890-1234567890-1234567890-1234'
        })
        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds true --domain-name {domain_name}
        --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}
        --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""
        result = self.cmd(update_cmd).get_output_in_json()

        self.assertIn('azureFilesIdentityBasedAuthentication', result)
        self.assertEqual(result['azureFilesIdentityBasedAuthentication']['directoryServiceOptions'], 'AD')
        activeDirectoryProperties = result['azureFilesIdentityBasedAuthentication']['activeDirectoryProperties']
        self.assertEqual(activeDirectoryProperties['azureStorageSid'], self.kwargs['azure_storage_sid'])
        self.assertEqual(activeDirectoryProperties['domainGuid'], self.kwargs['domain_guid'])
        self.assertEqual(activeDirectoryProperties['domainName'], self.kwargs['domain_name'])
        self.assertEqual(activeDirectoryProperties['domainSid'], self.kwargs['domain_sid'])
        self.assertEqual(activeDirectoryProperties['forestName'], self.kwargs['forest_name'])
        self.assertEqual(activeDirectoryProperties['netBiosDomainName'], self.kwargs['net_bios_domain_name'])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer(location='westus', name_prefix='cliedgezone')
    def test_storage_account_extended_location(self, resource_group):
        self.kwargs = {
            'sa1': self.create_random_name(prefix='edge1', length=12),
            'sa2': self.create_random_name(prefix='edge2', length=12),
            'rg': resource_group
        }
        self.cmd('storage account create -n {sa1} -g {rg} --edge-zone microsoftrrdclab1 -l eastus2euap --sku Premium_LRS',
                 checks=[
                     JMESPathCheck('extendedLocation.name', 'microsoftrrdclab1'),
                     JMESPathCheck('extendedLocation.type', 'EdgeZone')
                 ])
        self.cmd('storage account create -n {sa2} -g {rg} --edge-zone microsoftlosangeles1 --sku Premium_LRS',
                 checks=[
                     JMESPathCheck('extendedLocation.name', 'microsoftlosangeles1'),
                     JMESPathCheck('extendedLocation.type', 'EdgeZone')
                 ])


class RoleScenarioTest(LiveScenarioTest):
    def run_under_service_principal(self):
        account_info = self.cmd('account show').get_output_in_json()
        return account_info['user']['type'] == 'servicePrincipal'


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
class RevokeStorageAccountTests(StorageScenarioMixin, RoleScenarioTest, LiveScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_storage_revoke_keys')
    @StorageAccountPreparer()
    def test_storage_account_revoke_delegation_keys(self, resource_group, storage_account):
        if self.run_under_service_principal():
            return  # this test delete users which are beyond a SP's capacity, so quit...
        from datetime import datetime, timedelta
        import time

        expiry = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
        account_info = self.get_account_info(resource_group, storage_account)
        c = self.create_container(account_info)
        b = self.create_random_name('blob', 24)
        local_file = self.create_temp_file(128, full_random=False)
        self.kwargs.update({
            'expiry': expiry,
            'account': storage_account,
            'container': c,
            'local_file': local_file,
            'blob': b,
            'rg': resource_group
        })
        result = self.cmd('storage account show -n {account} -g {rg}').get_output_in_json()
        self.kwargs['sc_id'] = result['id']

        user = self.create_random_name('testuser', 15)
        self.kwargs['upn'] = user + '@azuresdkteam.onmicrosoft.com'
        self.cmd('ad user create --display-name tester123 --password Test123456789 --user-principal-name {upn}')
        time.sleep(15)  # By-design, it takes some time for RBAC system propagated with graph object change

        self.cmd('role assignment create --assignee {upn} --role "Storage Blob Data Contributor" --scope {sc_id}')

        container_sas = self.cmd('storage blob generate-sas --account-name {account} -n {blob} -c {container} --expiry {expiry} --permissions '
                                 'rw --https-only --as-user --auth-mode login -otsv').output
        self.kwargs['container_sas'] = container_sas
        self.cmd('storage blob upload -c {container} -n {blob} -f "{local_file}" --account-name {account} --sas-token {container_sas}')

        blob_sas = self.cmd('storage blob generate-sas --account-name {account} -n {blob} -c {container} --expiry {expiry} --permissions '
                            'r --https-only --as-user --auth-mode login -otsv').output
        self.kwargs['blob_sas'] = blob_sas
        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}') \
            .assert_with_checks(JMESPathCheck('name', b))

        self.cmd('storage account revoke-delegation-keys -n {account} -g {rg}')

        time.sleep(60)  # By-design, it takes some time for RBAC system propagated with graph object change

        self.cmd('storage blob show -c {container} -n {blob} --account-name {account} --sas-token {blob_sas}', expect_failure=True)


@api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
class BlobServicePropertiesTests(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix='cli_storage_account_update_change_feed')
    @StorageAccountPreparer(kind='StorageV2', name_prefix='clitest', location="eastus2euap")
    def test_storage_account_update_change_feed(self, resource_group, storage_account):
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'cmd': 'storage account blob-service-properties update'
        })

        from azure.cli.core.azclierror import InvalidArgumentValueError
        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('{cmd} --enable-change-feed false --change-feed-retention-days 14600 -n {sa} -g {rg}')

        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('{cmd} --change-feed-retention-days 1 -n {sa} -g {rg}')

        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days -1 -n {sa} -g {rg}')

        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days 0 -n {sa} -g {rg}')

        with self.assertRaises(InvalidArgumentValueError):
            self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days 146001 -n {sa} -g {rg}')

        result = self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days 1 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)
        self.assertEqual(result['changeFeed']['retentionInDays'], 1)

        result = self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days 100 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)
        self.assertEqual(result['changeFeed']['retentionInDays'], 100)

        result = self.cmd('{cmd} --enable-change-feed true --change-feed-retention-days 14600 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], True)
        self.assertEqual(result['changeFeed']['retentionInDays'], 14600)

        result = self.cmd('{cmd} --enable-change-feed false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['changeFeed']['enabled'], False)
        self.assertEqual(result['changeFeed']['retentionInDays'], None)

    @ResourceGroupPreparer(name_prefix='cli_storage_account_update_delete_retention_policy')
    @StorageAccountPreparer()
    def test_storage_account_update_delete_retention_policy(self, resource_group, storage_account):
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'cmd': 'storage account blob-service-properties update'
        })

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-delete-retention true -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-delete-retention false --delete-retention-days 365 -n {sa} -g {rg}').get_output_in_json()

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --delete-retention-days 1 -n {sa} -g {rg}').get_output_in_json()

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-delete-retention true --delete-retention-days -1 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-delete-retention true --delete-retention-days 0 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-delete-retention true --delete-retention-days 366 -n {sa} -g {rg}')

        result = self.cmd('{cmd} --enable-delete-retention true --delete-retention-days 1 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['deleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['deleteRetentionPolicy']['days'], 1)

        result = self.cmd('{cmd} --enable-delete-retention true --delete-retention-days 100 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['deleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['deleteRetentionPolicy']['days'], 100)

        result = self.cmd('{cmd} --enable-delete-retention true --delete-retention-days 365 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['deleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['deleteRetentionPolicy']['days'], 365)

        result = self.cmd('{cmd} --enable-delete-retention false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['deleteRetentionPolicy']['enabled'], False)
        self.assertEqual(result['deleteRetentionPolicy']['days'], None)

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix="cli_test_sa_versioning")
    @StorageAccountPreparer(location="eastus2euap", kind="StorageV2")
    def test_storage_account_update_versioning(self):
        result = self.cmd('storage account blob-service-properties update --enable-versioning true -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['isVersioningEnabled'], True)

        result = self.cmd('storage account blob-service-properties update --enable-versioning false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['isVersioningEnabled'], False)

        result = self.cmd('storage account blob-service-properties update --enable-versioning -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['isVersioningEnabled'], True)

        result = self.cmd('storage account blob-service-properties show -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['isVersioningEnabled'], True)

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix='cli_storage_account_update_delete_retention_policy')
    @StorageAccountPreparer(kind='StorageV2', name_prefix='clitest', location='eastus2euap')
    def test_storage_account_update_container_delete_retention_policy(self, resource_group, storage_account):
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'cmd': 'storage account blob-service-properties update'
        })

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-container-delete-retention true -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-container-delete-retention false --container-delete-retention-days 365 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --container-delete-retention-days 1 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days -1 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days 0 -n {sa} -g {rg}')

        with self.assertRaises(SystemExit):
            self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days 366 -n {sa} -g {rg}')

        result = self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days 1 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['containerDeleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['containerDeleteRetentionPolicy']['days'], 1)

        result = self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days 100 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['containerDeleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['containerDeleteRetentionPolicy']['days'], 100)

        result = self.cmd('{cmd} --enable-container-delete-retention true --container-delete-retention-days 365 -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['containerDeleteRetentionPolicy']['enabled'], True)
        self.assertEqual(result['containerDeleteRetentionPolicy']['days'], 365)

        result = self.cmd('{cmd} --enable-container-delete-retention false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['containerDeleteRetentionPolicy']['enabled'], False)
        self.assertEqual(result['containerDeleteRetentionPolicy']['days'], None)

    @ResourceGroupPreparer()
    @StorageAccountPreparer(kind="StorageV2")
    def test_storage_account_default_service_properties(self):
        from azure.cli.core.azclierror import InvalidArgumentValueError
        self.cmd('storage account blob-service-properties show -n {sa} -g {rg}', checks=[
            self.check('defaultServiceVersion', None)])

        with self.assertRaisesRegex(InvalidArgumentValueError, 'Valid example: 2008-10-27'):
            self.cmd('storage account blob-service-properties update --default-service-version 2018 -n {sa} -g {rg}')

        self.cmd('storage account blob-service-properties update --default-service-version 2018-11-09 -n {sa} -g {rg}',
                 checks=[self.check('defaultServiceVersion', '2018-11-09')])

        self.cmd('storage account blob-service-properties show -n {sa} -g {rg}',
                 checks=[self.check('defaultServiceVersion', '2018-11-09')])

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix="cli_test_sa_versioning")
    @StorageAccountPreparer(location="eastus2", kind="StorageV2")
    def test_storage_account_update_last_access(self):
        result = self.cmd('storage account blob-service-properties update --enable-last-access-tracking true -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['enable'], True)

        result = self.cmd(
            'storage account blob-service-properties show -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['enable'], True)
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['name'], "AccessTimeTracking")
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['trackingGranularityInDays'], 1)
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['blobType'][0], "blockBlob")

        result = self.cmd('storage account blob-service-properties update --enable-last-access-tracking false -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy'], None)

        result = self.cmd('storage account blob-service-properties update --enable-last-access-tracking -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['enable'], True)

        result = self.cmd('storage account blob-service-properties show -n {sa} -g {rg}').get_output_in_json()
        self.assertEqual(result['lastAccessTimeTrackingPolicy']['enable'], True)


class FileServicePropertiesTests(StorageScenarioMixin, ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_file_soft_delete')
    @StorageAccountPreparer(name_prefix='filesoftdelete', kind='StorageV2', location='eastus2euap')
    def test_storage_account_file_delete_retention_policy(self, resource_group, storage_account):
        from azure.cli.core.azclierror import ValidationError
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'cmd': 'storage account file-service-properties'
        })
        self.cmd('{cmd} show --account-name {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7))

        # Test update without properties
        self.cmd('{cmd} update --account-name {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7))

        self.cmd('{cmd} update --enable-delete-retention false -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', False),
            JMESPathCheck('shareDeleteRetentionPolicy.days', None))

        self.cmd('{cmd} show -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', False),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 0))

        # Test update without properties
        self.cmd('{cmd} update --account-name {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', False),
            JMESPathCheck('shareDeleteRetentionPolicy.days', None))

        with self.assertRaises(ValidationError):
            self.cmd('{cmd} update --enable-delete-retention true -n {sa} -g {rg}')

        with self.assertRaisesRegex(ValidationError, "Delete Retention Policy hasn't been enabled,"):
            self.cmd('{cmd} update --delete-retention-days 1 -n {sa} -g {rg} -n {sa} -g {rg}')

        with self.assertRaises(ValidationError):
            self.cmd('{cmd} update --enable-delete-retention false --delete-retention-days 1 -n {sa} -g {rg}')

        self.cmd(
            '{cmd} update --enable-delete-retention true --delete-retention-days 10 -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 10))

        self.cmd('{cmd} update --delete-retention-days 1 -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 1))

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer(name_prefix='cli_file_smb')
    @StorageAccountPreparer(parameter_name='storage_account1', name_prefix='filesmb1', kind='FileStorage',
                            sku='Premium_LRS', location='centraluseuap')
    @StorageAccountPreparer(parameter_name='storage_account2', name_prefix='filesmb2', kind='StorageV2')
    def test_storage_account_file_smb_multichannel(self, resource_group, storage_account1, storage_account2):

        from azure.core.exceptions import ResourceExistsError
        self.kwargs.update({
            'sa': storage_account1,
            'sa2': storage_account2,
            'rg': resource_group,
            'cmd': 'storage account file-service-properties'
        })

        with self.assertRaisesRegex(ResourceExistsError, "SMB Multichannel is not supported for the account."):
            self.cmd('{cmd} update --mc -n {sa2} -g {rg}')

        self.cmd('{cmd} show -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7),
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', False))

        self.cmd('{cmd} show -n {sa2} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7),
            JMESPathCheck('protocolSettings.smb.multichannel', None))

        self.cmd(
            '{cmd} update --enable-smb-multichannel -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', True))

        self.cmd(
            '{cmd} update --enable-smb-multichannel false -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', False))

        self.cmd(
            '{cmd} update --enable-smb-multichannel true -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', True))

    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer(name_prefix='cli_file_smb')
    @StorageAccountPreparer(name_prefix='filesmb', kind='FileStorage', sku='Premium_LRS', location='centraluseuap')
    def test_storage_account_file_secured_smb(self, resource_group, storage_account):
        self.kwargs.update({
            'sa': storage_account,
            'rg': resource_group,
            'cmd': 'storage account file-service-properties'
        })

        self.cmd('{cmd} show -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7),
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', False),
            JMESPathCheck('protocolSettings.smb.authenticationMethods', None),
            JMESPathCheck('protocolSettings.smb.channelEncryption', None),
            JMESPathCheck('protocolSettings.smb.kerberosTicketEncryption', None),
            JMESPathCheck('protocolSettings.smb.versions', None))

        self.cmd(
            '{cmd} update --versions "SMB2.1;SMB3.0;SMB3.1.1" --auth-methods "NTLMv2;Kerberos" '
            '--kerb-ticket-encryption "RC4-HMAC;AES-256" --channel-encryption "AES-128-CCM;AES-128-GCM;AES-256-GCM"'
            ' -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('protocolSettings.smb.authenticationMethods', "NTLMv2;Kerberos"),
            JMESPathCheck('protocolSettings.smb.channelEncryption', "AES-128-CCM;AES-128-GCM;AES-256-GCM"),
            JMESPathCheck('protocolSettings.smb.kerberosTicketEncryption', "RC4-HMAC;AES-256"),
            JMESPathCheck('protocolSettings.smb.versions', "SMB2.1;SMB3.0;SMB3.1.1"))

        self.cmd('{cmd} show -n {sa} -g {rg}').assert_with_checks(
            JMESPathCheck('shareDeleteRetentionPolicy.enabled', True),
            JMESPathCheck('shareDeleteRetentionPolicy.days', 7),
            JMESPathCheck('protocolSettings.smb.multichannel.enabled', False),
            JMESPathCheck('protocolSettings.smb.authenticationMethods', "NTLMv2;Kerberos"),
            JMESPathCheck('protocolSettings.smb.channelEncryption', "AES-128-CCM;AES-128-GCM;AES-256-GCM"),
            JMESPathCheck('protocolSettings.smb.kerberosTicketEncryption', "RC4-HMAC;AES-256"),
            JMESPathCheck('protocolSettings.smb.versions', "SMB2.1;SMB3.0;SMB3.1.1"))


class StorageAccountPrivateLinkScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sa_plr')
    @StorageAccountPreparer(name_prefix='saplr', kind='StorageV2', sku='Standard_LRS')
    def test_storage_account_private_link(self, storage_account):
        self.kwargs.update({
            'sa': storage_account
        })
        self.cmd('storage account private-link-resource list --account-name {sa} -g {rg}', checks=[
            self.check('length(@)', 6)])


class StorageAccountPrivateEndpointScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(name_prefix='cli_test_sa_pe')
    @StorageAccountPreparer(name_prefix='saplr', kind='StorageV2')
    def test_storage_account_private_endpoint(self, storage_account):
        self.kwargs.update({
            'sa': storage_account,
            'loc': 'eastus',
            'vnet': self.create_random_name('cli-vnet-', 24),
            'subnet': self.create_random_name('cli-subnet-', 24),
            'pe': self.create_random_name('cli-pe-', 24),
            'pe_connection': self.create_random_name('cli-pec-', 24),
        })

        # Prepare network
        self.cmd('network vnet create -n {vnet} -g {rg} -l {loc} --subnet-name {subnet}',
                 checks=self.check('length(newVNet.subnets)', 1))
        self.cmd('network vnet subnet update -n {subnet} --vnet-name {vnet} -g {rg} '
                 '--disable-private-endpoint-network-policies true',
                 checks=self.check('privateEndpointNetworkPolicies', 'Disabled'))

        # Create a private endpoint connection
        pr = self.cmd('storage account private-link-resource list --account-name {sa} -g {rg}').get_output_in_json()
        self.kwargs['group_id'] = pr[0]['groupId']

        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.kwargs['sa_id'] = storage['id']
        private_endpoint = self.cmd(
            'network private-endpoint create -g {rg} -n {pe} --vnet-name {vnet} --subnet {subnet} -l {loc} '
            '--connection-name {pe_connection} --private-connection-resource-id {sa_id} '
            '--group-ids blob').get_output_in_json()
        self.assertEqual(private_endpoint['name'], self.kwargs['pe'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['name'], self.kwargs['pe_connection'])
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['privateLinkServiceConnectionState']['status'], 'Approved')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['provisioningState'], 'Succeeded')
        self.assertEqual(private_endpoint['privateLinkServiceConnections'][0]['groupIds'][0], self.kwargs['group_id'])
        self.kwargs['pe_id'] = private_endpoint['privateLinkServiceConnections'][0]['id']

        # Show the connection at storage account
        storage = self.cmd('storage account show -n {sa} -g {rg}').get_output_in_json()
        self.assertIn('privateEndpointConnections', storage)
        self.assertEqual(len(storage['privateEndpointConnections']), 1)
        self.assertEqual(storage['privateEndpointConnections'][0]['privateLinkServiceConnectionState']['status'],
                         'Approved')

        self.kwargs['sa_pec_id'] = storage['privateEndpointConnections'][0]['id']
        self.kwargs['sa_pec_name'] = storage['privateEndpointConnections'][0]['name']

        self.cmd('storage account private-endpoint-connection show --account-name {sa} -g {rg} --name {sa_pec_name}',
                 checks=self.check('id', '{sa_pec_id}'))
        with self.assertRaisesRegex(CLIError, 'Your connection is already approved. No need to approve again.'):
            self.cmd('storage account private-endpoint-connection approve --account-name {sa} -g {rg} --name {sa_pec_name}')

        self.cmd('storage account private-endpoint-connection reject --account-name {sa} -g {rg} --name {sa_pec_name}',
                 checks=[self.check('privateLinkServiceConnectionState.status', 'Rejected')])

        with self.assertRaisesRegex(CLIError, 'You cannot approve the connection request after rejection.'):
            self.cmd('storage account private-endpoint-connection approve --account-name {sa} -g {rg} --name {sa_pec_name}')

        self.cmd('storage account private-endpoint-connection delete --id {sa_pec_id} -y')


class StorageAccountSkuScenarioTest(ScenarioTest):
    @unittest.skip('Storage account type Standard_ZRS cannot be changed to Standard_GZRS')
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(name_prefix='clistorage', location='eastus2')
    @StorageAccountPreparer(name_prefix='clistoragesku', location='eastus2euap', kind='StorageV2', sku='Standard_ZRS')
    def test_storage_account_sku(self, resource_group, storage_account):
        self.kwargs = {
            'gzrs_sa': self.create_random_name(prefix='cligzrs', length=24),
            'GZRS': 'Standard_GZRS',
            'rg': resource_group,
            'sa': storage_account
        }

        # Create storage account with GZRS
        self.cmd('az storage account create -n {gzrs_sa} -g {rg} --sku {GZRS} --https-only --kind StorageV2', checks=[
            self.check('sku.name', '{GZRS}'),
            self.check('name', '{gzrs_sa}')
        ])

        # Convert ZRS to GZRS
        self.cmd('az storage account show -n {sa} -g {rg}', checks=[
            self.check('sku.name', 'Standard_ZRS'),
            self.check('name', '{sa}')
        ])

        self.cmd('az storage account update -n {sa} -g {rg} --sku {GZRS}', checks=[
            self.check('sku.name', '{GZRS}'),
            self.check('name', '{sa}'),
        ])

        self.cmd('az storage account show -n {sa} -g {rg}', checks=[
            self.check('sku.name', '{GZRS}'),
            self.check('name', '{sa}')
        ])

        self.cmd('az storage account delete -n {gzrs_sa} -g {rg} -y')


class StorageAccountFailoverScenarioTest(ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-04-01')
    @ResourceGroupPreparer(name_prefix='clistorage', location='westus2')
    def test_storage_account_failover(self, resource_group):
        self.kwargs = {
            'sa': self.create_random_name(prefix="storagegrzs", length=24),
            'rg': resource_group
        }
        self.cmd('storage account create -n {sa} -g {rg} -l eastus2euap --kind StorageV2 --sku Standard_RAGRS --https-only',
                 checks=[self.check('name', '{sa}'),
                         self.check('sku.name', 'Standard_RAGRS')])

        while True:
            can_failover = self.cmd('storage account show -n {sa} -g {rg} --expand geoReplicationStats --query '
                                    'geoReplicationStats.canFailover -o tsv').output.strip('\n')
            if can_failover == 'true':
                break
            time.sleep(10)

        self.cmd('storage account show -n {sa} -g {rg} --expand geoReplicationStats', checks=[
            self.check('geoReplicationStats.canFailover', True),
            self.check('failoverInProgress', None)
        ])

        time.sleep(900)
        self.cmd('storage account failover -n {sa} -g {rg} --no-wait -y')

        self.cmd('storage account show -n {sa} -g {rg} --expand geoReplicationStats', checks=[
            self.check('name', '{sa}'),
            self.check('failoverInProgress', True)
        ])


class StorageAccountLocalContextScenarioTest(LocalContextScenarioTest):

    @ResourceGroupPreparer(name_prefix='clistorage', location='westus2')
    def test_storage_account_local_context(self):
        self.kwargs.update({
            'account_name': self.create_random_name(prefix='cli', length=24)
        })
        self.cmd('storage account create -g {rg} -n {account_name} --https-only',
                 checks=[self.check('name', self.kwargs['account_name'])])
        self.cmd('storage account show',
                 checks=[self.check('name', self.kwargs['account_name'])])
        with self.assertRaises(CLIError):
            self.cmd('storage account delete')
        self.cmd('storage account delete -n {account_name} -y')


class StorageAccountORScenarioTest(StorageScenarioMixin, ScenarioTest):
    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2019-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_account_ors', location='eastus2')
    @StorageAccountPreparer(parameter_name='source_account', location='eastus2', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='destination_account', location='eastus2', kind='StorageV2')
    @StorageAccountPreparer(parameter_name='new_account', location='eastus2', kind='StorageV2')
    def test_storage_account_or_policy(self, resource_group, source_account, destination_account,
                                       new_account):
        src_account_info = self.get_account_info(resource_group, source_account)
        src_container = self.create_container(src_account_info)
        dest_account_info = self.get_account_info(resource_group, destination_account)
        dest_container = self.create_container(dest_account_info)
        self.kwargs.update({
            'rg': resource_group,
            'src_sc': source_account,
            'src_sc_id': self.get_account_id(resource_group, source_account),
            'dest_sc': destination_account,
            'dest_sc_id': self.get_account_id(resource_group, destination_account),
            'new_sc': new_account,
            'new_sc_id': self.get_account_id(resource_group, new_account),
            'scont': src_container,
            'dcont': dest_container,
        })

        # Enable ChangeFeed for Source Storage Accounts
        self.cmd('storage account blob-service-properties update -n {src_sc} -g {rg} --enable-change-feed', checks=[
                 JMESPathCheck('changeFeed.enabled', True)])

        # Enable Versioning for two Storage Accounts
        self.cmd('storage account blob-service-properties update -n {src_sc} -g {rg} --enable-versioning', checks=[
                 JMESPathCheck('isVersioningEnabled', True)])

        self.cmd('storage account blob-service-properties update -n {dest_sc} -g {rg} --enable-versioning', checks=[
                 JMESPathCheck('isVersioningEnabled', True)])

        # Create ORS policy on destination account
        result = self.cmd('storage account or-policy create -n {dest_sc} -s {src_sc} --dcont {dcont} '
                          '--scont {scont} -t "2020-02-19T16:05:00Z"').get_output_in_json()
        self.assertIn('policyId', result)
        self.assertIn('ruleId', result['rules'][0])
        self.assertEqual(result["rules"][0]["filters"]["minCreationTime"], "2020-02-19T16:05:00Z")

        self.kwargs.update({
            'policy_id': result["policyId"],
            'rule_id': result["rules"][0]["ruleId"]
        })

        # Get policy properties from destination account
        self.cmd('storage account or-policy show -g {rg} -n {dest_sc} --policy-id {policy_id}') \
            .assert_with_checks(JMESPathCheck('type', "Microsoft.Storage/storageAccounts/objectReplicationPolicies")) \
            .assert_with_checks(JMESPathCheck('sourceAccount', self.kwargs['src_sc_id'])) \
            .assert_with_checks(JMESPathCheck('destinationAccount', self.kwargs['dest_sc_id'])) \
            .assert_with_checks(JMESPathCheck('rules[0].sourceContainer', src_container)) \
            .assert_with_checks(JMESPathCheck('rules[0].destinationContainer', dest_container))

        # Add rules
        src_container1 = self.create_container(src_account_info)
        dest_container1 = self.create_container(dest_account_info)
        self.cmd('storage account or-policy rule list -g {rg} -n {dest_sc} --policy-id {policy_id}')\
            .assert_with_checks(JMESPathCheck('length(@)', 1))
        self.cmd('storage account or-policy rule show -g {rg} -n {dest_sc} --rule-id {rule_id} --policy-id {policy_id}')\
            .assert_with_checks(JMESPathCheck('ruleId', result["rules"][0]["ruleId"])) \
            .assert_with_checks(JMESPathCheck('sourceContainer', src_container)) \
            .assert_with_checks(JMESPathCheck('destinationContainer', dest_container))

        result = self.cmd('storage account or-policy rule add -g {} -n {} --policy-id {} -d {} -s {} -t "2020-02-19T16:05:00Z"'.format(
            resource_group, self.kwargs["dest_sc"], self.kwargs["policy_id"], dest_container1, src_container1)).get_output_in_json()
        self.assertEqual(result["rules"][0]["filters"]["minCreationTime"], "2020-02-19T16:05:00Z")

        self.cmd('storage account or-policy rule list -g {rg} -n {dest_sc} --policy-id {policy_id}')\
            .assert_with_checks(JMESPathCheck('length(@)', 2))

        # Update rules
        self.cmd('storage account or-policy rule update -g {} -n {} --policy-id {} --rule-id {} --prefix-match blobA blobB -t "2020-02-20T16:05:00Z"'.format(
            resource_group, self.kwargs["dest_sc"], result['policyId'], result['rules'][1]['ruleId'])) \
            .assert_with_checks(JMESPathCheck('filters.prefixMatch[0]', 'blobA')) \
            .assert_with_checks(JMESPathCheck('filters.prefixMatch[1]', 'blobB')) \
            .assert_with_checks(JMESPathCheck('filters.minCreationTime', '2020-02-20T16:05:00Z'))

        self.cmd('storage account or-policy rule show -g {} -n {} --policy-id {} --rule-id {}'.format(
            resource_group, self.kwargs["dest_sc"], result['policyId'], result['rules'][1]['ruleId'])) \
            .assert_with_checks(JMESPathCheck('filters.prefixMatch[0]', 'blobA')) \
            .assert_with_checks(JMESPathCheck('filters.prefixMatch[1]', 'blobB')) \
            .assert_with_checks(JMESPathCheck('filters.minCreationTime', '2020-02-20T16:05:00Z'))

        # Remove rules
        self.cmd('storage account or-policy rule remove -g {} -n {} --policy-id {} --rule-id {}'.format(
            resource_group, self.kwargs["dest_sc"], result['policyId'], result['rules'][1]['ruleId']))
        self.cmd('storage account or-policy rule list -g {rg} -n {dest_sc} --policy-id {policy_id}') \
            .assert_with_checks(JMESPathCheck('length(@)', 1))

        # Set ORS policy to source account
        with self.assertRaisesRegex(CLIError, 'ValueError: Please specify --policy-id with auto-generated policy id'):
            self.cmd('storage account or-policy create -g {rg} -n {src_sc} -d {dest_sc} -s {src_sc} --dcont {dcont} --scont {scont}')

        import json
        temp_dir = self.create_temp_dir()
        policy_file = os.path.join(temp_dir, "policy.json")
        with open(policy_file, "w") as f:
            policy = self.cmd('storage account or-policy show -g {rg} -n {dest_sc} --policy-id {policy_id}')\
                .get_output_in_json()
            json.dump(policy, f)
        self.kwargs['policy'] = policy_file
        result = self.cmd('storage account or-policy create -g {rg} -n {src_sc} -p @"{policy}"').get_output_in_json()
        self.assertEqual(result['type'], "Microsoft.Storage/storageAccounts/objectReplicationPolicies")
        self.assertIn(self.kwargs['src_sc'], result['sourceAccount'])
        self.assertIn(self.kwargs['dest_sc'], result['destinationAccount'])
        self.assertEqual(result['rules'][0]['sourceContainer'], src_container)
        self.assertEqual(result['rules'][0]['destinationContainer'], dest_container)
        self.assertEqual(result['rules'][0]['filters']['minCreationTime'], '2020-02-19T16:05:00Z')

        # Update ORS policy
        result = self.cmd('storage account or-policy update -g {} -n {} --policy-id {} --source-account {}'.format(
            resource_group, self.kwargs["dest_sc"], self.kwargs["policy_id"], self.kwargs['new_sc'])).get_output_in_json()
        self.assertIn(self.kwargs['new_sc'], result['sourceAccount'])

        # Delete policy from destination and source account
        self.cmd('storage account or-policy delete -g {rg} -n {src_sc} --policy-id {policy_id}')
        self.cmd('storage account or-policy list -g {rg} -n {src_sc}') \
            .assert_with_checks(JMESPathCheck('length(@)', 0))

        self.cmd('storage account or-policy delete -g {rg} -n {dest_sc} --policy-id {policy_id}')
        self.cmd('storage account or-policy list -g {rg} -n {dest_sc}') \
            .assert_with_checks(JMESPathCheck('length(@)', 0))

    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-04-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_account_ors', location='eastus2')
    def test_storage_account_allow_cross_tenant_replication(self, resource_group):
        self.kwargs.update({
            'rg': resource_group,
            'src_sc': self.create_random_name(prefix='clicor', length=24),
        })

        self.cmd('storage account create -n {src_sc} -g {rg} ', checks=[
            JMESPathCheck('allowCrossTenantReplication', None)])

        self.cmd('storage account update -n {src_sc} -g {rg} -r false', checks=[
            JMESPathCheck('allowCrossTenantReplication', False)])

        self.cmd('storage account update -n {src_sc} -g {rg} -r true', checks=[
            JMESPathCheck('allowCrossTenantReplication', True)])

        self.cmd('storage account create -n {src_sc} -g {rg} -r false', checks=[
            JMESPathCheck('allowCrossTenantReplication', False)])

        self.cmd('storage account create -n {src_sc} -g {rg} -r true', checks=[
            JMESPathCheck('allowCrossTenantReplication', True)])

    @record_only()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-04-01')
    @ResourceGroupPreparer(name_prefix='cli_test_storage_account_ors', location='eastus2')
    @StorageAccountPreparer(parameter_name='destination_account', location='eastus2euap', kind='StorageV2')
    def test_storage_account_cross_tenant_or_policy(self, resource_group, destination_account):

        dest_account_info = self.get_account_info(resource_group, destination_account)
        dest_container = self.create_container(dest_account_info)
        self.kwargs.update({
            'rg': resource_group,
            'dest_sc': destination_account,
            'scont': 'scont',
            'dcont': dest_container,
        })

        self.cmd('storage account blob-service-properties update -n {dest_sc} -g {rg} --enable-versioning', checks=[
                 JMESPathCheck('isVersioningEnabled', True)])

        # Create ORS policy on destination account with cross tenant account as source account
        result = self.cmd('storage account or-policy create -n {dest_sc} '
                          '-s /subscriptions/1c638cf4-608f-4ee6-b680-c329e824c3a8/resourcegroups/clitest/providers/Microsoft.Storage/storageAccounts/clitestcor '
                          '--dcont {dcont} --scont {scont} -t "2020-02-19T16:05:00Z"').get_output_in_json()
        self.assertIn('policyId', result)
        self.assertIn('ruleId', result['rules'][0])
        self.assertEqual(result["rules"][0]["filters"]["minCreationTime"], "2020-02-19T16:05:00Z")


class StorageAccountBlobInventoryScenarioTest(StorageScenarioMixin, ScenarioTest):
    @AllowLargeResponse()
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2020-08-01-preview')
    @ResourceGroupPreparer(name_prefix='cli_test_blob_inventory', location='eastus2')
    @StorageAccountPreparer(location='eastus2', kind='StorageV2')
    def test_storage_account_blob_inventory_policy(self, resource_group, storage_account):
        import os
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        policy_file = os.path.join(curr_dir, 'blob_inventory_policy.json').replace('\\', '\\\\')
        policy_file_no_type = os.path.join(curr_dir, 'blob_inventory_policy_no_type.json').replace('\\', '\\\\')
        self.kwargs = {'rg': resource_group,
                       'sa': storage_account,
                       'policy': policy_file,
                       'policy_no_type': policy_file_no_type}
        account_info = self.get_account_info(resource_group, storage_account)
        self.storage_cmd('storage container create -n mycontainer', account_info)

        # Create policy without type specified
        self.cmd('storage account blob-inventory-policy create --account-name {sa} -g {rg} --policy @"{policy_no_type}"',
                 checks=[JMESPathCheck("name", "DefaultInventoryPolicy"),
                         JMESPathCheck("policy.rules[0].destination", "mycontainer"),
                         JMESPathCheck("policy.enabled", True),
                         JMESPathCheck("policy.rules[0].definition.filters", None),
                         JMESPathCheck("policy.rules[0].definition.format", "Parquet"),
                         JMESPathCheck("policy.rules[0].definition.objectType", "Container"),
                         JMESPathCheck("policy.rules[0].definition.schedule", "Weekly"),
                         JMESPathCheck("policy.rules[0].definition.schemaFields[0]", "Name"),
                         JMESPathCheck("policy.rules[0].enabled", True),
                         JMESPathCheck("policy.rules[0].name", "inventoryPolicyRule1"),
                         JMESPathCheck("policy.type", "Inventory"),
                         JMESPathCheck("resourceGroup", resource_group),
                         JMESPathCheck("systemData", None)])

        self.cmd('storage account blob-inventory-policy show --account-name {sa} -g {rg}',
                 checks=[JMESPathCheck("name", "DefaultInventoryPolicy"),
                         JMESPathCheck("policy.rules[0].destination", "mycontainer"),
                         JMESPathCheck("policy.enabled", True),
                         JMESPathCheck("policy.rules[0].definition.filters", None),
                         JMESPathCheck("policy.rules[0].definition.format", "Parquet"),
                         JMESPathCheck("policy.rules[0].definition.objectType", "Container"),
                         JMESPathCheck("policy.rules[0].definition.schedule", "Weekly"),
                         JMESPathCheck("policy.rules[0].definition.schemaFields[0]", "Name"),
                         JMESPathCheck("policy.rules[0].enabled", True),
                         JMESPathCheck("policy.rules[0].name", "inventoryPolicyRule1"),
                         JMESPathCheck("policy.type", "Inventory"),
                         JMESPathCheck("resourceGroup", resource_group),
                         JMESPathCheck("systemData", None)])

        # Enable Versioning for Storage Account when includeBlobInventory=true in policy
        self.cmd('storage account blob-service-properties update -n {sa} -g {rg} --enable-versioning', checks=[
                 JMESPathCheck('isVersioningEnabled', True)])

        self.cmd('storage account blob-inventory-policy create --account-name {sa} -g {rg} --policy @"{policy}"',
                 checks=[JMESPathCheck("name", "DefaultInventoryPolicy"),
                         JMESPathCheck("policy.rules[0].destination", "mycontainer"),
                         JMESPathCheck("policy.enabled", True),
                         JMESPathCheck("policy.rules[0].definition.filters.blobTypes[0]", "blockBlob"),
                         JMESPathCheck("policy.rules[0].definition.filters.includeBlobVersions", True),
                         JMESPathCheck("policy.rules[0].definition.filters.includeSnapshots", True),
                         JMESPathCheck("policy.rules[0].definition.filters.prefixMatch[0]", "inventoryprefix1"),
                         JMESPathCheck("policy.rules[0].definition.filters.prefixMatch[1]", "inventoryprefix2"),
                         JMESPathCheck("policy.rules[0].definition.format", "Csv"),
                         JMESPathCheck("policy.rules[0].definition.objectType", "Blob"),
                         JMESPathCheck("policy.rules[0].definition.schedule", "Daily"),
                         JMESPathCheck("policy.rules[0].definition.schemaFields[0]", "Name"),
                         JMESPathCheck("policy.rules[0].enabled", True),
                         JMESPathCheck("policy.rules[0].name", "inventoryPolicyRule2"),
                         JMESPathCheck("policy.type", "Inventory"),
                         JMESPathCheck("resourceGroup", resource_group),
                         JMESPathCheck("systemData", None)])

        self.cmd('storage account blob-inventory-policy show --account-name {sa} -g {rg}',
                 checks=[JMESPathCheck("name", "DefaultInventoryPolicy"),
                         JMESPathCheck("policy.rules[0].destination", "mycontainer"),
                         JMESPathCheck("policy.enabled", True),
                         JMESPathCheck("policy.rules[0].definition.filters.blobTypes[0]", "blockBlob"),
                         JMESPathCheck("policy.rules[0].definition.filters.includeBlobVersions", True),
                         JMESPathCheck("policy.rules[0].definition.filters.includeSnapshots", True),
                         JMESPathCheck("policy.rules[0].definition.filters.prefixMatch[0]", "inventoryprefix1"),
                         JMESPathCheck("policy.rules[0].definition.filters.prefixMatch[1]", "inventoryprefix2"),
                         JMESPathCheck("policy.rules[0].definition.format", "Csv"),
                         JMESPathCheck("policy.rules[0].definition.objectType", "Blob"),
                         JMESPathCheck("policy.rules[0].definition.schedule", "Daily"),
                         JMESPathCheck("policy.rules[0].definition.schemaFields[0]", "Name"),
                         JMESPathCheck("policy.rules[0].enabled", True),
                         JMESPathCheck("policy.rules[0].name", "inventoryPolicyRule2"),
                         JMESPathCheck("policy.type", "Inventory"),
                         JMESPathCheck("resourceGroup", resource_group),
                         JMESPathCheck("systemData", None)])

        self.cmd('storage account blob-inventory-policy update --account-name {sa} -g {rg}'
                 ' --set "policy.rules[0].name=newname"')
        self.cmd('storage account blob-inventory-policy show --account-name {sa} -g {rg}',
                 checks=JMESPathCheck('policy.rules[0].name', 'newname'))

        self.cmd('storage account blob-inventory-policy delete --account-name {sa} -g {rg} -y')
        self.cmd('storage account blob-inventory-policy show --account-name {sa} -g {rg}', expect_failure=True)


class StorageAccountHNSMigrationScenarioTest(StorageScenarioMixin, ScenarioTest):
    @api_version_constraint(ResourceType.MGMT_STORAGE, min_api='2021-06-01')
    @ResourceGroupPreparer(name_prefix='cli_test_hns_migrate', location='eastus2')
    @StorageAccountPreparer(location='eastus2', kind='StorageV2', key='sa1', parameter_name='storage_account1')
    @StorageAccountPreparer(location='eastus2', kind='StorageV2', key='sa2', parameter_name='storage_account2')
    def test_storage_account_start_hns_migration(self, resource_group, storage_account1, storage_account2):
        # test migration validation
        self.cmd('storage account hns-migration start --request-type validation -n {sa1} -g {rg}')
        # test migration
        self.cmd('storage account hns-migration start --request-type upgrade -n {sa1} -g {rg}')
        # test aborting migration
        self.cmd('storage account hns-migration start --request-type validation -n {sa2} -g {rg}')
        self.cmd('storage account hns-migration start --request-type upgrade -n {sa2} -g {rg} --no-wait')
        retry = 0
        while True:
            from azure.core.exceptions import HttpResponseError
            try:
                self.cmd('storage account hns-migration stop -n {sa2} -g {rg}')
                break
            except HttpResponseError as ex:
                if retry > 5:
                    raise ex
                if ex.reason == 'Hns migration for the account: {} is not found.'.format(storage_account2):
                    retry += 1
                    time.sleep(30)
