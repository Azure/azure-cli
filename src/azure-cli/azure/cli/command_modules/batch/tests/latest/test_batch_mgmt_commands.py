# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import time
import sys
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer, LiveScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.profiles import ResourceType, get_sdk

from .recording_processors import BatchAccountKeyReplacer, StorageSASReplacer


class BatchMgmtScenarioTests(ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            BatchAccountKeyReplacer(),
            StorageSASReplacer()
        ])

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus', name_prefix='clibatchteststor')
    def test_batch_general_arm_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)

        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus',
            'acc': account_name,
            'ip': resource_group + 'ip',
            'poolname': 'batch_account_cmd_pool'
        })

        # test create storage account with default set
        storage_id = f"/subscriptions/{self.get_subscription_id()}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{storage_account}"

        # test create account with default set
        self.cmd('batch account create -g {rg} -n {acc} -l {loc}').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')])

        time.sleep(100)

        self.cmd('batch account set -g {rg} -n {acc} --storage-account {str_n}').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')])

        self.cmd('batch account show -g {rg} -n {acc}').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('autoStorage.storageAccountId', storage_id)])

        self.cmd('batch account autostorage-keys sync -g {rg} -n {acc}')

        keys = self.cmd('batch account keys list -g {rg} -n {acc}').assert_with_checks([
            self.check('primary != null', True),
            self.check('secondary != null', True)])

        keys2 = self.cmd('batch account keys renew -g {rg} -n {acc} --key-name primary').assert_with_checks([
            self.check('primary != null', True),
            self.check('secondary', keys.get_output_in_json()['secondary'])])

        self.assertNotEqual(keys.get_output_in_json()['primary'], keys2.get_output_in_json()['primary'])

        self.cmd('batch account login -g {rg} -n {acc}').assert_with_checks(self.is_empty())
        self.assertEqual(self.cli_ctx.config.get('batch', 'auth_mode'), 'aad')
        self.assertEqual(self.cli_ctx.config.get('batch', 'account'), self.kwargs['acc'])

        self.cmd('batch account login -g {rg} -n {acc} --shared-key-auth').assert_with_checks(self.is_empty())
        self.assertEqual(self.cli_ctx.config.get('batch', 'auth_mode'), 'shared_key')
        self.assertEqual(self.cli_ctx.config.get('batch', 'account'), self.kwargs['acc'])
        self.assertEqual(self.cli_ctx.config.get('batch', 'access_key'), keys2.get_output_in_json()['primary'])

        self.cmd('batch account outbound-endpoints -g {rg} -n {acc}').assert_with_checks([
            self.check('length(@)', 4),
            self.check('[0].category', 'Azure Batch'),
            self.check('[1].category', 'Azure Storage'),
            self.check('[2].category', 'Microsoft Package Repository'),
            self.check('[3].category', 'Azure Key Vault'),
            self.check('length([0].endpoints)', 2),
            self.check('ends_with([0].endpoints[0].domainName, `batch.azure.com`)', True) 
        ])

        # test batch account delete
        self.cmd('batch account delete -g {rg} -n {acc} --yes')
        self.cmd('batch account list -g {rg}').assert_with_checks(self.is_empty())

        self.cmd('batch location quotas show -l {loc}').assert_with_checks(
            [self.check('accountQuota', 1)])

        self.cmd('batch location list-skus -l {loc} --query "[0:20]"').assert_with_checks([
            self.check('length(@)', 20), # Ensure at least 20 entries
            self.check('[?name==`Basic_A2`] | [0].familyName', 'basicAFamily'),
            self.check('[?name==`Basic_A2`] | [0].capabilities[?name==`vCPUs`] | [0].value', 2)
        ])


class BatchMgmtApplicationScenarioTests(ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            StorageSASReplacer()
        ])


    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus', name_prefix='clibatchteststor')
    def test_batch_privateendpoint_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        vnet_name = self.create_random_name(prefix='clibatchtestvn', length=24)
        pe_name = self.create_random_name(prefix='clibatchtestpe', length=24)

        _, package_file_name = tempfile.mkstemp()

        
        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus',
            'acc': account_name,
            'app': 'testapp',
            'app_p': '1.0',
            'app_f': package_file_name,
            'vnetname': vnet_name,
            'pename': pe_name
        })

        # test create account with default set
        batchaccount = self.cmd('batch account create -g {rg} -n {acc} -l {loc} --storage-account {str_n} --public-network-access Disabled').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')]).get_output_in_json()
        
        self.kwargs['accountId'] = batchaccount['id']

        # create private endpoint
        self.cmd('network vnet create --resource-group {rg} --name {vnetname} -l {loc}')
        self.cmd('network vnet subnet create --resource-group {rg} --name default --vnet-name {vnetname} --address-prefixes 10.0.0.0/24')
        self.cmd('network vnet subnet update --name default --resource-group {rg} --vnet-name {vnetname} --disable-private-endpoint-network-policies true')
        self.cmd('network private-endpoint create -g {rg} -n {pename} --vnet-name {vnetname} --subnet default --private-connection-resource-id {accountId} --group-id batchAccount --connection-name {pename} -l {loc}')
       
        self.cmd('batch private-link-resource list --account-name {acc} --resource-group {rg}').assert_with_checks([
             self.check('length(@)', 1),
            self.check('[0].name', '{acc}')])

        self.cmd('batch private-link-resource show --account-name {acc} --resource-group {rg} --private-link-resource {acc}').assert_with_checks([
             self.check('name', '{acc}')])

        endpoints = self.cmd('batch private-endpoint-connection list --account-name {acc} --resource-group {rg}').get_output_in_json()
        self.kwargs['endpointId'] = endpoints[0]['name']
        self.cmd('batch private-endpoint-connection show --account-name {acc} --resource-group {rg} --private-endpoint-connection-name {endpointId}').assert_with_checks([
             self.check('name', '{endpointId}')])


    @ResourceGroupPreparer(location='eastus')
    @StorageAccountPreparer(location='eastus', name_prefix='clibatchteststor')
    def test_batch_application_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)

        
        _, package_file_name = tempfile.mkstemp()

        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus',
            'acc': account_name,
            'app': 'testapp',
            'app_p': '1.0',
            'app_f': package_file_name
        })

        # test create account with default set
        self.cmd('batch account create -g {rg} -n {acc} -l {loc} --storage-account {str_n}').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')])

        with open(package_file_name, 'w') as f:
            f.write('storage blob test sample file')

        # test create application with default set
        self.cmd('batch application create -g {rg} -n {acc} --application-name {app} ').assert_with_checks(
            [self.check('name', '{app}')])

        self.cmd('batch application list -g {rg} -n {acc}').assert_with_checks([
            self.check('length(@)', 1),
            self.check('[0].name', '{app}')])

        self.cmd('batch application package create -g {rg} -n {acc} --application-name {app}'
                 ' --version {app_p} --package-file "{app_f}"').assert_with_checks([
                     self.check('name', '{app_p}'),
                     self.check('storageUrl != null', True),
                     self.check('state', 'Active')])

        self.cmd('batch application package activate -g {rg} -n {acc} --application-name {app}'
                 ' --version {app_p} --format zip')

        self.cmd('batch application package show -g {rg} -n {acc} '
                 '--application-name {app} --version {app_p}').assert_with_checks([
                     self.check('name', '{app_p}'),
                     self.check('format', 'zip'),
                     self.check('state', 'Active')])

        self.cmd('batch application set -g {rg} -n {acc} --application-name {app} '
                 '--default-version {app_p}')

        self.cmd('batch application show -g {rg} -n {acc} --application-name {app}').assert_with_checks([
            self.check('name', '{app}'),
            self.check('defaultVersion', '{app_p}')])

        # test batch applcation delete
        self.cmd('batch application package delete -g {rg} -n {acc} --application-name {app} '
                 '--version {app_p} --yes')
        self.cmd('batch application delete -g {rg} -n {acc} --application-name {app} --yes')
        self.cmd('batch application list -g {rg} -n {acc}').assert_with_checks(self.is_empty())


# These tests have requirements which cannot be met by CLI team so reserved for live testing.
class BatchMgmtLiveScenarioTests(LiveScenarioTest):
    @ResourceGroupPreparer(location='northeurope')
    def test_batch_byos_account_cmd(self, resource_group):
        storage_name = self.create_random_name(prefix='clibatchteststor', length=24)
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        kv_name = self.create_random_name('clibatchtestkv', 24)

        SecretPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT,
                                    'models._key_vault_management_client_enums#SecretPermissions')
        KeyPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT,
                                 'models._key_vault_management_client_enums#KeyPermissions')
        ALL_SECRET_PERMISSIONS = ' '.join(
            [perm.value for perm in SecretPermissions])
        ALL_KEY_PERMISSIONS = ' '.join([perm.value for perm in KeyPermissions])

        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_name,
            'byos_n': account_name,
            'byos_l': 'southindia',
            'kv': kv_name,
            'obj_id': 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a',  # object id for Microsoft Azure Batch
            'perm_k': ALL_KEY_PERMISSIONS,
            'perm_s': ALL_SECRET_PERMISSIONS
        })

        # test create keyvault for use with BYOS account
        self.cmd(
            'keyvault create -g {rg} -n {kv} -l {byos_l} --enabled-for-deployment true --enabled-for'
            '-disk-encryption true --enabled-for-template-deployment true').assert_with_checks(
            [
                self.check('name', '{kv}'),
                self.check('location', '{byos_l}'),
                self.check('resourceGroup', '{rg}'),
                self.check('type(properties.accessPolicies)', 'array'),
                self.check('length(properties.accessPolicies)', 1),
                self.check('properties.sku.name', 'standard')])
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {obj_id} '
                 '--key-permissions {perm_k} --secret-permissions {perm_s}')

        time.sleep(100)

        # test create account with BYOS
        self.cmd(
            'batch account create -g {rg} -n {byos_n} -l {byos_l} --keyvault {kv}').assert_with_checks(
            [
                self.check('name', '{byos_n}'),
                self.check('location', '{byos_l}'),
                self.check('resourceGroup', '{rg}')])

        # test batch account delete
        self.cmd('batch account delete -g {rg} -n {byos_n} --yes')
        self.cmd('batch account list -g {rg}').assert_with_checks(self.is_empty())
