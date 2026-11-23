# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import tempfile
import time
import unittest
from unittest import mock

from azure.mgmt.batch.models import BatchAccount, BatchAccountIdentity
from azure.cli.core.mock import DummyCli
from azure.cli.core.util import rmtree_with_retry
from azure.cli.command_modules.batch import _client_factory
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, StorageAccountPreparer)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from .batch_preparers import BatchMgmtScenarioMixin
from .batch_request_matcher import register_batch_body_matcher

from .recording_processors import BatchAccountKeyReplacer, StorageSASReplacer


class BatchMgmtScenarioTests(ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            BatchAccountKeyReplacer(),
            StorageSASReplacer()
        ])
        register_batch_body_matcher(self.vcr)

    @AllowLargeResponse()
    @ResourceGroupPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2', name_prefix='clibatchteststor', kind='StorageV2')
    def test_batch_general_arm_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        account_name2 = self.create_random_name(prefix='clibatchtestacct', length=24)
        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus2',
            'acc': account_name,
            'acc2': account_name2,
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

         # test create account with default set
        self.cmd('batch account create -g {rg} -n {acc2} -l {loc} --encryption-key-source Microsoft.Batch').assert_with_checks([
            self.check('name', '{acc2}'),
            self.check('location', '{loc}'),
            self.check('encryption.keySource', 'Microsoft.Batch'),
            self.check('resourceGroup', '{rg}')])

        if self.is_live or self.in_recording:
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
        self.cmd('batch account delete -g {rg} -n {acc2} --yes')
        self.cmd('batch account show -g {rg} -n {acc}', expect_failure=True)
        self.cmd('batch account show -g {rg} -n {acc2}', expect_failure=True)

        self.cmd('batch location quotas show -l {loc}').assert_with_checks(
            [self.greater_than('accountQuota', 0)])

        self.cmd('batch location list-skus -l {loc}').assert_with_checks([
            self.check('length(@) >= `20`', True),  # Ensure at least 20 entries
            self.check('[?name==`Standard_D2s_v3`] | [0].familyName', 'standardDSv3Family'),
            self.check('[?name==`Standard_D2s_v3`] | [0].capabilities[?name==`vCPUs`] | [0].value', 2)
        ])


class BatchMgmtApplicationScenarioTests(ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name, recording_processors=[
            StorageSASReplacer()
        ])
        register_batch_body_matcher(self.vcr)

    def _download_package(self):
        """Download the newest blob of the application's packages from the account's storage account. The service
        doesn't return a package's storageUrl any more once it's active."""
        self.kwargs['container'] = self.cmd(
            'storage container list --account-name {str_n} --account-key "{str_k}" '
            '--query "[?starts_with(name, \'app-{app}-\')].name | [0]" -o tsv').output.strip()
        self.kwargs['blob'] = self.cmd(
            'storage blob list --account-name {str_n} --account-key "{str_k}" -c {container} '
            '--query "sort_by(@, &properties.lastModified)[-1].name" -o tsv').output.strip()
        _, self.kwargs['download_file_name'] = tempfile.mkstemp()
        self.cmd('storage blob download --account-name {str_n} --account-key "{str_k}" -c {container} -n {blob} '
                 '--file "{download_file_name}"')
        with open(self.kwargs['download_file_name'], 'r') as f:
            return f.read()


    @ResourceGroupPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2', name_prefix='clibatchteststor', kind='StorageV2')
    def test_batch_privateendpoint_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        vnet_name = self.create_random_name(prefix='clibatchtestvn', length=24)
        pe_name = self.create_random_name(prefix='clibatchtestpe', length=24)

        _, package_file_name = tempfile.mkstemp()


        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus2',
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
             self.check('length(@)', 2),
            self.check('[0].name', 'batchAccount')])

        self.cmd('batch private-link-resource show --account-name {acc} --resource-group {rg} --name batchAccount').assert_with_checks([
             self.check('name', 'batchAccount')])

        endpoints = self.cmd('batch private-endpoint-connection list --account-name {acc} --resource-group {rg}').get_output_in_json()
        self.kwargs['endpointId'] = endpoints[0]['name']
        self.cmd('batch private-endpoint-connection show --account-name {acc} --resource-group {rg} --name {endpointId}').assert_with_checks([
             self.check('name', '{endpointId}')])


    @ResourceGroupPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2', name_prefix='clibatchteststor', kind='StorageV2')
    def test_batch_network_profile_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        vnet_name = self.create_random_name(prefix='clibatchtestvn', length=24)
        pe_name = self.create_random_name(prefix='clibatchtestpe', length=24)

        _, package_file_name = tempfile.mkstemp()


        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus2',
            'acc': account_name,
            'app': 'testapp',
            'app_p': '1.0',
            'app_f': package_file_name,
            'vnetname': vnet_name,
            'pename': pe_name
        })

        # test create account with default set
        batchaccount = self.cmd('batch account create -g {rg} -n {acc} -l {loc} --storage-account {str_n} --public-network-access Enabled').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')]).get_output_in_json()

        self.kwargs['accountId'] = batchaccount['id']

        # create private endpoint
        output = self.cmd('batch account network-profile network-rule add -n {acc} -g {rg} --profile BatchAccount --ip-address 1.2.3.6').assert_with_checks([
            self.check('accountAccess.defaultAction', 'Allow'),
            self.check('accountAccess.ipRules[0].value', '1.2.3.6')]).get_output_in_json()


    @ResourceGroupPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2', name_prefix='clibatchteststor', kind='StorageV2')
    def test_batch_managed_identity_cmd(self, resource_group, storage_account):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        vnet_name = self.create_random_name(prefix='clibatchtestvn', length=24)
        pe_name = self.create_random_name(prefix='clibatchtestpe', length=24)

        _, package_file_name = tempfile.mkstemp()


        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'loc': 'eastus2',
            'acc': account_name,
            'app': 'testapp',
            'app_p': '1.0',
            'app_f': package_file_name,
            'vnetname': vnet_name,
            'pename': pe_name,
            'identity1': 'identity1',
            'identity2': 'identity2',
        })

        identity1_json = self. cmd('identity create -g {rg} -n {identity1}'). get_output_in_json()
        identity2_json = self. cmd('identity create -g {rg} -n {identity2}'). get_output_in_json()
        identity1_id = identity1_json['id']
        identity2_id = identity2_json['id']
        identity1_principalId = identity1_json['principalId']
        identity2_principalId = identity2_json['principalId']
        self. kwargs. update({
            'identity1_id': identity1_id,
            'identity1_principalId': identity1_principalId,
            'identity2_id': identity2_id,
            'identity2_principalId': identity2_principalId
        })

        # test create account with managed identity
        batchaccount = self.cmd('batch account create -g {rg} -n {acc} -l {loc} --storage-account {str_n} --mi-user-assigned {identity1_id}').assert_with_checks([
            self.check('name', '{acc}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}'),
            self.check('identity.type', 'UserAssigned'),
            self. check('length(identity.userAssignedIdentities)', 1)]).get_output_in_json()

        # display the managed identity
        self. cmd('batch account identity show -g {rg} -n {acc}', checks=[
        self.check('type', 'UserAssigned')])

        # delete specific managed identity
        self. cmd('batch account identity remove -g {rg} -n {acc} --user-assigned {identity1_id} --yes', checks=[
        self. check('type', 'None'),
        self. check('userAssignedIdentities', 'None')])

        # create a managed identity to an existing accountS
        self. cmd('batch account identity assign -g {rg} -n {acc} --user-assigned {identity2_id}', checks=[
        self. check('type', 'UserAssigned'),
        self. check('length(userAssignedIdentities)', 1)])

        # delete all the managed identity
        self. cmd('batch account identity remove -g {rg} -n {acc} --user-assigned --yes', checks=[
        self. check('type', 'None'),
        self. check('userAssignedIdentities', 'None')])

        # create a managed identity to an existing accountS
        self. cmd('batch account identity assign -g {rg} -n {acc} --user-assigned {identity2_id}', checks=[
        self. check('type', 'UserAssigned'),
        self. check('length(userAssignedIdentities)', 1)])


    @ResourceGroupPreparer(location='eastus2')
    @StorageAccountPreparer(location='eastus2', name_prefix='clibatchteststor', kind='StorageV2')
    def test_batch_application_cmd(self, resource_group, storage_account, storage_account_info):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)

        _, package_file_name = tempfile.mkstemp()

        self.kwargs.update({
            'rg': resource_group,
            'str_n': storage_account,
            'str_k': storage_account_info[1],
            'loc': 'eastus2',
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
                     self.check('state', 'Active')])

        # verify blob content
        self.assertEqual(self._download_package(), 'storage blob test sample file')

        # test overwriting blob content
        _, package_file_name_2 = tempfile.mkstemp()
        with open(package_file_name_2, 'w') as f:
            f.write('storage blob test overwrite file')
        self.kwargs.update({"package_file_name_2": package_file_name_2})

        self.cmd('batch application package create -g {rg} -n {acc} --application-name {app}'
                 ' --version {app_p} --package-file "{package_file_name_2}"').assert_with_checks([
            self.check('name', '{app_p}'),
            self.check('state', 'Active')])

        # verify blob content
        self.assertEqual(self._download_package(), 'storage blob test overwrite file')

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


class BatchMgmtByosScenarioTests(BatchMgmtScenarioMixin,ScenarioTest):

    def __init__(self, method_name):
        super().__init__(method_name)
        register_batch_body_matcher(self.vcr)

    # Note for this test to run you subscrition needs to give access to batch https://learn.microsoft.com/azure/batch/batch-account-create-portal#allow-batch-to-access-the-subscription
    @ResourceGroupPreparer(location='eastus2')
    def test_batch_byos_account_cmd(self, resource_group):
        account_name = self.create_random_name(prefix='clibatchtestacct', length=24)
        kv_name = self.create_random_name('clibatchtestkv', 24)

        self.kwargs.update({
            'rg': resource_group,
            'byos_n': account_name,
            'byos_l': 'eastus2',
            'kv': kv_name,
            'obj_id': 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a',  # object id for Microsoft Azure Batch
            'perm_s': "get list set delete recover",
        })

        # test create keyvault for use with BYOS account
        self.cmd(
            'keyvault create -g {rg} -n {kv} -l {byos_l} --enabled-for-deployment true --enabled-for'
            '-disk-encryption true --enabled-for-template-deployment true --enable-rbac-authorization false').assert_with_checks(
            [
                self.check('name', '{kv}'),
                self.check('location', '{byos_l}'),
                self.check('resourceGroup', '{rg}'),
                self.check('length(properties.accessPolicies)', 1),
                self.check('properties.sku.name', 'standard')])
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {obj_id} '
                 '--secret-permissions {perm_s}')

        # test create account with BYOS
        self.cmd(
            'batch account create -g {rg} -n {byos_n} -l {byos_l} --keyvault {kv}').assert_with_checks(
            [
                self.check('name', '{byos_n}'),
                self.check('location', '{byos_l}'),
                self.check('resourceGroup', '{rg}')])

        self.set_account_info(account_name, resource_group)    

        self.batch_cmd('batch pool create --id xplatCreatedPool --vm-size "standard_d2s_v3" '
                        '--image "canonical:0001-com-ubuntu-server-focal:20_04-lts" '
                        '--node-agent-sku-id "batch.node.ubuntu 20.04" ')

        # test batch account delete
        self.cmd('batch account delete -g {rg} -n {byos_n} --yes')
        #self.cmd('batch account list -g {rg}').assert_with_checks(self.is_empty())

class TestBatchAccountPublicNetworkAccess(unittest.TestCase):
    """Run the commands that update a Batch account with its management client mocked, and check whether the
    update they send sets public network access."""

    USER_IDENTITY = ('/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/'
                     'Microsoft.ManagedIdentity/userAssignedIdentities/identity1')

    def setUp(self):
        self.cli = DummyCli(random_config_dir=True)
        self.addCleanup(self.cli.env_patch.stop)
        self.addCleanup(rmtree_with_retry, self.cli.config.config_dir)
        self.client = mock.Mock()
        self.client.get.side_effect = self._account
        self.client.update.side_effect = self._account
        factory_patch = mock.patch.object(_client_factory, 'mgmt_batch_account_client_factory',
                                          return_value=self.client)
        factory_patch.start()
        self.addCleanup(factory_patch.stop)

    @staticmethod
    def _account(*_, **__):
        """An account with public network access disabled, new for each request"""
        return BatchAccount(location='eastus', public_network_access='Disabled',
                            identity=BatchAccountIdentity(type='SystemAssigned'))

    def _update_sent(self, command):
        """Run the command and return the body of the account update it sends."""
        self.client.update.reset_mock()
        self.assertEqual(self.cli.invoke(command.split(), out_file=io.StringIO()), 0)
        self.client.update.assert_called_once()
        return self.client.update.call_args.kwargs['parameters'].as_dict()

    def test_batch_account_identity_keeps_public_network_access(self):
        for command in ['batch account identity assign -g rg -n acc --system-assigned',
                        f'batch account identity assign -g rg -n acc --user-assigned {self.USER_IDENTITY}',
                        'batch account identity remove -g rg -n acc --system-assigned --yes']:
            with self.subTest(command=command):
                body = self._update_sent(command)
                self.assertIn('identity', body)
                self.assertNotIn('publicNetworkAccess', body.get('properties', {}))

    def test_batch_account_network_profile_enables_public_network_access(self):
        # The network profile only takes effect when public network access is enabled
        for command in ['batch account network-profile set -g rg -n acc --profile BatchAccount --default-action Deny',
                        'batch account network-profile network-rule add -g rg -n acc --profile BatchAccount '
                        '--ip-address 1.2.3.4',
                        'batch account network-profile network-rule delete -g rg -n acc --profile BatchAccount '
                        '--ip-address 1.2.3.4 --yes']:
            with self.subTest(command=command):
                body = self._update_sent(command)
                self.assertIn('networkProfile', body['properties'])
                self.assertEqual(body['properties']['publicNetworkAccess'], 'Enabled')


class TestBatchAccountRequestBodies(unittest.TestCase):
    """Run `batch account create` and `batch account set` with their management client mocked, and check the bodies
    they send when no account property is given. They match what the CLI sent with azure-mgmt-batch 17.3.0, which
    left out an empty 'properties' object."""

    def setUp(self):
        self.cli = DummyCli(random_config_dir=True)
        self.addCleanup(self.cli.env_patch.stop)
        self.addCleanup(rmtree_with_retry, self.cli.config.config_dir)
        self.client = mock.Mock()
        self.client.update.return_value = BatchAccount(location='eastus')
        factory_patch = mock.patch.object(_client_factory, 'mgmt_batch_account_client_factory',
                                          return_value=self.client)
        factory_patch.start()
        self.addCleanup(factory_patch.stop)

    def _sent(self, command, operation):
        """Run the command and return the body it sends with the given client operation."""
        self.assertEqual(self.cli.invoke(command.split(), out_file=io.StringIO()), 0)
        getattr(self.client, operation).assert_called_once()
        return getattr(self.client, operation).call_args.kwargs['parameters'].as_dict()

    def test_batch_account_create_without_account_properties(self):
        self.assertEqual(self._sent('batch account create -g rg -n acc -l eastus --no-wait', 'begin_create'),
                         {'location': 'eastus'})

    def test_batch_account_create_with_identity_and_tags(self):
        # The identity and tags aren't account properties
        self.assertEqual(self._sent('batch account create -g rg -n acc -l eastus --mi-system-assigned true --tags a=b '
                                    '--no-wait', 'begin_create'),
                         {'location': 'eastus', 'identity': {'type': 'SystemAssigned'}, 'tags': {'a': 'b'}})

    def test_batch_account_set_tags(self):
        self.assertEqual(self._sent('batch account set -g rg -n acc --tags x=y', 'update'), {'tags': {'x': 'y'}})
