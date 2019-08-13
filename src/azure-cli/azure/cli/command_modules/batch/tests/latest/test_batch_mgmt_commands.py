# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import mock
import os
import tempfile
import time

from knack.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk import (
    ScenarioTest, ResourceGroupPreparer, LiveScenarioTest)
from .batch_preparers import BatchAccountPreparer, BatchScenarioMixin
from azure.cli.core.profiles import ResourceType, get_sdk


class BatchMgmtScenarioTests(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(location='northeurope')
    def test_batch_account_cmd(self, resource_group):

        self.kwargs.update({
            'rg': resource_group,
            'str_n': 'clibatchteststorage1',
            'loc': 'northeurope',
            'acc': 'clibatchtest1'
        })

        # test create storage account with default set
        result = self.cmd('storage account create -g {rg} -n {str_n} -l {loc} --sku Standard_LRS').assert_with_checks([
            self.check('name', '{str_n}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')])
        storage_id = result.get_output_in_json()['id']

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

        self.assertTrue(keys.get_output_in_json()['primary'] !=
                        keys2.get_output_in_json()['primary'])

        self.cmd('batch account login -g {rg} -n {acc}').assert_with_checks(self.is_empty())
        self.assertEqual(self.cli_ctx.config.get('batch', 'auth_mode'), 'aad')
        self.assertEqual(self.cli_ctx.config.get('batch', 'account'), self.kwargs['acc'])

        self.cmd('batch account login -g {rg} -n {acc} --shared-key-auth').assert_with_checks(self.is_empty())
        self.assertEqual(self.cli_ctx.config.get('batch', 'auth_mode'), 'shared_key')
        self.assertEqual(self.cli_ctx.config.get('batch', 'account'), self.kwargs['acc'])
        self.assertEqual(self.cli_ctx.config.get('batch', 'access_key'), keys2.get_output_in_json()['primary'])

        # test batch account delete
        self.cmd('batch account delete -g {rg} -n {acc} --yes')
        self.cmd('batch account list -g {rg}').assert_with_checks(self.is_empty())

        self.cmd('batch location quotas show -l {loc}').assert_with_checks(
            [self.check('accountQuota', 3)])


class BatchMgmtApplicationScenarioTests(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(location='ukwest')
    def test_batch_application_cmd(self, resource_group):
        _, package_file_name = tempfile.mkstemp()
        self.kwargs.update({
            'rg': resource_group,
            'str_n': 'clibatchteststorage7',
            'loc': 'ukwest',
            'acc': 'clibatchtest7',
            'app': 'testapp',
            'app_p': '1.0',
            'app_f': package_file_name
        })

        # test create account with default set
        self.cmd('storage account create -g {rg} -n {str_n} -l {loc} --sku Standard_LRS').assert_with_checks([
            self.check('name', '{str_n}'),
            self.check('location', '{loc}'),
            self.check('resourceGroup', '{rg}')])

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
                     self.check('name', '{app}'),
                     self.check('storageUrl != null', True),
                     self.check('state', 'Active')])

        self.cmd('batch application package activate -g {rg} -n {acc} --application-name {app}'
                 ' --version {app_p} --format zip')

        self.cmd('batch application package show -g {rg} -n {acc} '
                 '--application-name {app} --version {app_p}').assert_with_checks([
                     self.check('name', '{app}'),
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
        self.cmd('storage account delete -g {rg} -n {str_n} --yes')


# These tests have requirements which cannot be met by CLI team so reserved for live testing.
class BatchMgmtLiveScenarioTests(LiveScenarioTest):
    @ResourceGroupPreparer(location='northeurope')
    def test_batch_byos_account_cmd(self, resource_group):
        SecretPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT,
                                    'models.key_vault_management_client_enums#SecretPermissions')
        KeyPermissions = get_sdk(self.cli_ctx, ResourceType.MGMT_KEYVAULT,
                                 'models.key_vault_management_client_enums#KeyPermissions')
        ALL_SECRET_PERMISSIONS = ' '.join(
            [perm.value for perm in SecretPermissions])
        ALL_KEY_PERMISSIONS = ' '.join([perm.value for perm in KeyPermissions])

        self.kwargs.update({
            'rg': resource_group,
            'str_n': 'clibatchteststorage1',
            'byos_n': 'clibatchtestuser1',
            'byos_l': 'southindia',
            'kv': 'clibatchtestkeyvault1',
            'obj_id': 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a',
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
