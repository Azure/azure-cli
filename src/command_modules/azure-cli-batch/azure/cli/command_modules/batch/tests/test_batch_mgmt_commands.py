# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import os
import mock

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer
from .batch_preparers import BatchAccountPreparer, BatchScenarioMixin
from azure.mgmt.keyvault.models import SecretPermissions, KeyPermissions

# Key Vault permissions
ALL_SECRET_PERMISSIONS = ' '.join([perm.value for perm in SecretPermissions])
ALL_KEY_PERMISSIONS = ' '.join([perm.value for perm in KeyPermissions])

class BatchMgmtScenarioTests(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(location='northeurope')
    def test_batch_account_cmd(self, resource_group):
        self.skipTest("")
        config_dir = tempfile.mkdtemp()
        config_path = os.path.join(config_dir, 'config')

        self.kwargs.update({
            'str_n': 'clibatchteststorage1',
            'loc': 'northeurope',
            'acc': 'clibatchtest1',
            'byos_n': 'clibatchtestuser1',
            'byos_l': 'uksouth',
            'kv': 'clibatchtestkeyvault1',
            'obj_id': 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a',
            'perm_k': ALL_KEY_PERMISSIONS,
            'perm_s': ALL_SECRET_PERMISSIONS
        })

        # test create storage account with default set
        result = self.cmd('storage account create -g {rg} -n {str_n} -l {loc} --sku Standard_LRS').assert_with_checks([
                self.check('name', 'clibatchteststorage1'),
                self.check('location', 'northeurope'),
                self.check('resourceGroup', resource_group)])
        storage_id = result.get_output_in_json()['id']

        # test create keyvault for use with BYOS account
        self.cmd('keyvault create -g {rg} -n {kv} -l {byos_l} --enabled-for-deployment true --enabled-for'
                 '-disk-encryption true --enabled-for-template-deployment true').assert_with_checks([
                         self.check('name', 'clibatchtestkeyvault1'),
                         self.check('location', 'uksouth'),
                         self.check('resourceGroup', resource_group),
                         self.check('type(properties.accessPolicies)', 'array'),
                         self.check('length(properties.accessPolicies)', 1),
                         self.check('properties.sku.name', 'standard')])
        self.cmd('keyvault set-policy -g {rg} -n {kv} --object-id {obj_id} '
                 '--key-permissions {perm_k} --secret-permissions {perm_s}')

        # test create account with default set
        self.cmd('batch account create -g {rg} -n {acc} -l {loc}').assert_with_checks([
                self.check('name', 'clibatchtest1'),
                self.check('location', 'northeurope'),
                self.check('resourceGroup', resource_group)])

        # test create account with BYOS
        self.cmd('batch account create -g {rg} -n {byos_n} -l {byos_l} --keyvault {kv}').assert_with_checks([
                self.check('name', 'clibatchtestuser1'),
                self.check('location', 'uksouth'),
                self.check('resourceGroup', resource_group)])

        self.cmd('batch account set -g {rg} -n {acc} --storage-account {str_n}').assert_with_checks([
                self.check('name', 'clibatchtest1'),
                self.check('location', 'northeurope'),
                self.check('resourceGroup', resource_group)])

        self.cmd('batch account show -g {rg} -n {acc}').assert_with_checks([
                self.check('name', 'clibatchtest1'),
                self.check('location', 'northeurope'),
                self.check('resourceGroup', resource_group),
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

        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', config_dir), \
                mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', config_path):
            self.cmd('batch account login -g {rg} -n {acc}').assert_with_checks(self.is_empty())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'aad')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), account_name)
            self.assertFalse(az_config.config_parser.has_option('batch', 'access_key'))

            self.cmd('batch account login -g {rg} -n {acc} --shared-key-auth').assert_with_checks(self.is_empty())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'shared_key')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), 'clibatchtest1')
            self.assertEqual(az_config.config_parser.get('batch', 'access_key'),
                             keys2.get_output_in_json()['primary'])

        # test batch account delete
        self.cmd('batch account delete -g {rg} -n {acc} --yes')
        self.cmd('batch account delete -g {rg} -n {byos_n} --yes')
        self.cmd('batch account list -g {rg}').assert_with_checks(self.is_empty())

        self.cmd('batch location quotas show -l {loc}').assert_with_checks(
            [self.check('accountQuota', 1)])

    @ResourceGroupPreparer(location='ukwest')
    def test_batch_application_cmd(self, resource_group):
        application_name = 'testapp'
        application_package_name = '1.0'
        _, package_file_name = tempfile.mkstemp()

        self.kwargs.update({
            'str_n': 'clibatchteststorage7',
            'loc': 'ukwest',
            'acc': 'clibatchtest7',
            'app': application_name,
            'app_p': application_package_name,
            'app_f': package_file_name
        })

        # test create account with default set
        result = self.cmd('storage account create -g {rg} -n {str_n} -l {loc} --sku Standard_LRS').assert_with_checks([
                self.check('name', 'clibatchteststorage7'),
                self.check('location', 'ukwest'),
                self.check('resourceGroup', resource_group)])

        self.cmd('batch account create -g {rg} -n {acc} -l {loc} --storage-account {str_n}').assert_with_checks([
                self.check('name', 'clibatchtest7'),
                self.check('location', 'ukwest'),
                self.check('resourceGroup', resource_group)])

        with open(package_file_name, 'w') as f:
            f.write('storage blob test sample file')

        # test create application with default set
        self.cmd('batch application create -g {rg} -n {acc} --application-id {app} '
                 '--allow-updates').assert_with_checks([
                         self.check('id', application_name),
                         self.check('allowUpdates', True)])

        self.cmd('batch application list -g {rg} -n {acc}').assert_with_checks([
                self.check('length(@)', 1),
                self.check('[0].id', application_name)])

        self.cmd('batch application package create -g {rg} -n {acc} --application-id {app}'
                 ' --version {app_p} --package-file "{app_f}"').assert_with_checks([
                         self.check('id', application_name),
                         self.check('storageUrl != null', True),
                         self.check('version', application_package_name),
                         self.check('state', 'active')])

        self.cmd('batch application package activate -g {rg} -n {acc} --application-id {app}'
                 ' --version {app_p} --format zip')

        self.cmd('batch application package show -g {rg} -n {acc} '
                 '--application-id {app} --version {app_p}').assert_with_checks([
                            self.check('id', application_name),
                            self.check('format', 'zip'),
                            self.check('version', application_package_name),
                            self.check('state', 'active')])

        self.cmd('batch application set -g {rg} -n {acc} --application-id {app} '
                 '--default-version {app_p}')

        self.cmd('batch application show -g {rg} -n {acc} --application-id {app}').assert_with_checks([
                self.check('id', application_name),
                self.check('defaultVersion', application_package_name),
                self.check('packages[0].format', 'zip'),
                self.check('packages[0].state', 'active')])

        # test batch applcation delete
        self.cmd('batch application package delete -g {rg} -n {acc} --application-id {app} '
                 '--version {app_p} --yes')
        self.cmd('batch application delete -g {rg} -n {acc} --application-id {app} --yes')
        self.cmd('batch application list -g {rg} -n {acc}').assert_with_checks(self.is_empty())
        self.cmd('storage account delete -g {rg} -n {str_n} --yes')
