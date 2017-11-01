# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import tempfile
import os
import mock

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck, NoneCheck
from .batch_preparers import BatchAccountPreparer, BatchScenarioMixin
from azure.mgmt.keyvault.models import SecretPermissions, KeyPermissions

# Key Vault permissions
ALL_SECRET_PERMISSIONS = ' '.join([perm.value for perm in SecretPermissions])
ALL_KEY_PERMISSIONS = ' '.join([perm.value for perm in KeyPermissions])

class BatchMgmtScenarioTests(ScenarioTest):  # pylint: disable=too-many-instance-attributes

    @ResourceGroupPreparer(location='northeurope')
    def test_batch_account_cmd(self, resource_group):
        config_dir = tempfile.mkdtemp()
        config_path = os.path.join(config_dir, CONFIG_FILE_NAME)
        storage_account_name = 'clibatchteststorage1'
        location = 'northeurope'
        account_name = 'clibatchtest1'
        byos_account_name = 'clibatchtestuser1'
        byos_location = 'uksouth'
        keyvault_name = 'clibatchtestkeyvault1'
        object_id = 'f520d84c-3fd3-4cc8-88d4-2ed25b00d27a'

        # test create storage account with default set
        result = self.cmd('storage account create -g {} -n {} -l {} --sku Standard_LRS'.format(
            resource_group, storage_account_name, location)).assert_with_checks([
                JMESPathCheck('name', storage_account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group)])
        storage_id = result.get_output_in_json()['id']

        # test create keyvault for use with BYOS account
        self.cmd('keyvault create -g {} -n {} -l {} --enabled-for-deployment true --enabled-for'
                 '-disk-encryption true --enabled-for-template-deployment true'.format(
                     resource_group, keyvault_name, byos_location)).assert_with_checks([
                         JMESPathCheck('name', keyvault_name),
                         JMESPathCheck('location', byos_location),
                         JMESPathCheck('resourceGroup', resource_group),
                         JMESPathCheck('type(properties.accessPolicies)', 'array'),
                         JMESPathCheck('length(properties.accessPolicies)', 1),
                         JMESPathCheck('properties.sku.name', 'standard')])
        self.cmd('keyvault set-policy -g {} -n {} --object-id {} --key-permissions {} '
                 '--secret-permissions {}'.format(resource_group,
                                                  keyvault_name,
                                                  object_id,
                                                  ALL_KEY_PERMISSIONS,
                                                  ALL_SECRET_PERMISSIONS))

        # test create account with default set
        self.cmd('batch account create -g {} -n {} -l {}'.format(
            resource_group, account_name, location)).assert_with_checks([
                JMESPathCheck('name', account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group)])

        # test create account with BYOS
        self.cmd('batch account create -g {} -n {} -l {} --keyvault {}'.format(
            resource_group, byos_account_name, byos_location, keyvault_name)).assert_with_checks([
                JMESPathCheck('name', byos_account_name),
                JMESPathCheck('location', byos_location),
                JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('batch account set -g {} -n {} --storage-account {}'.format(
            resource_group, account_name, storage_account_name)).assert_with_checks([
                JMESPathCheck('name', account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('batch account show -g {} -n {}'.format(
            resource_group, account_name)).assert_with_checks([
                JMESPathCheck('name', account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group),
                JMESPathCheck('autoStorage.storageAccountId', storage_id)])

        self.cmd('batch account autostorage-keys sync -g {} -n {}'.format(
            resource_group, account_name))

        keys = self.cmd('batch account keys list -g {} -n {}'.format(
            resource_group, account_name)).assert_with_checks([
                JMESPathCheck('primary != null', True),
                JMESPathCheck('secondary != null', True)])

        keys2 = self.cmd('batch account keys renew -g {} -n {} --key-name primary'.format(
            resource_group, account_name)).assert_with_checks([
                JMESPathCheck('primary != null', True),
                JMESPathCheck('secondary', keys.get_output_in_json()['secondary'])])

        self.assertTrue(keys.get_output_in_json()['primary'] !=
                        keys2.get_output_in_json()['primary'])

        with mock.patch('azure.cli.core._config.GLOBAL_CONFIG_DIR', config_dir), \
                mock.patch('azure.cli.core._config.GLOBAL_CONFIG_PATH', config_path):
            self.cmd('batch account login -g {} -n {}'.
                     format(resource_group, account_name)).assert_with_checks(NoneCheck())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'aad')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), account_name)
            self.assertFalse(az_config.config_parser.has_option('batch', 'access_key'))

            self.cmd('batch account login -g {} -n {} --shared-key-auth'.
                     format(resource_group, account_name)).assert_with_checks(NoneCheck())
            self.assertEqual(az_config.config_parser.get('batch', 'auth_mode'), 'shared_key')
            self.assertEqual(az_config.config_parser.get('batch', 'account'), account_name)
            self.assertEqual(az_config.config_parser.get('batch', 'access_key'),
                             keys2.get_output_in_json()['primary'])

        # test batch account delete
        self.cmd('batch account delete -g {} -n {} --yes'.format(resource_group, account_name))
        self.cmd('batch account delete -g {} -n {} --yes'.format(
            resource_group, byos_account_name))
        self.cmd('batch account list -g {}'.format(
            resource_group)).assert_with_checks(NoneCheck())

        self.cmd('batch location quotas show -l {}'.format(location)).assert_with_checks(
            [JMESPathCheck('accountQuota', 1)])

    @ResourceGroupPreparer(location='ukwest')
    def test_batch_application_cmd(self, resource_group):
        account_name = 'clibatchtest7'
        location = 'ukwest'
        storage_account_name = 'clibatchteststorage7'
        application_name = 'testapp'
        application_package_name = '1.0'
        _, package_file_name = tempfile.mkstemp()

        # test create account with default set
        result = self.cmd('storage account create -g {} -n {} -l {} --sku Standard_LRS'.format(
            resource_group, storage_account_name, location)).assert_with_checks([
                JMESPathCheck('name', storage_account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group)])

        self.cmd('batch account create -g {} -n {} -l {} --storage-account {}'.format(
            resource_group, account_name, location,
            result.get_output_in_json()['id'])).assert_with_checks([
                JMESPathCheck('name', account_name),
                JMESPathCheck('location', location),
                JMESPathCheck('resourceGroup', resource_group)])

        with open(package_file_name, 'w') as f:
            f.write('storage blob test sample file')

        # test create application with default set
        self.cmd('batch application create -g {} -n {} --application-id {} '
                 '--allow-updates'.format(
                     resource_group, account_name, application_name)).assert_with_checks([
                         JMESPathCheck('id', application_name),
                         JMESPathCheck('allowUpdates', True)])

        self.cmd('batch application list -g {} -n {}'.format(
            resource_group, account_name)).assert_with_checks([
                JMESPathCheck('length(@)', 1),
                JMESPathCheck('[0].id', application_name)])

        self.cmd('batch application package create -g {} -n {} --application-id {}'
                 ' --version {} --package-file "{}"'.format(
                     resource_group, account_name, application_name, application_package_name,
                     package_file_name)).assert_with_checks([
                         JMESPathCheck('id', application_name),
                         JMESPathCheck('storageUrl != null', True),
                         JMESPathCheck('version', application_package_name),
                         JMESPathCheck('state', 'active')])

        self.cmd('batch application package activate -g {} -n {} --application-id {}'
                 ' --version {} --format zip'.format(resource_group, account_name,
                                                     application_name, application_package_name))

        self.cmd('batch application package show -g {} -n {} --application-id {} --version {}'.
                 format(resource_group, account_name, application_name,
                        application_package_name)).assert_with_checks([
                            JMESPathCheck('id', application_name),
                            JMESPathCheck('format', 'zip'),
                            JMESPathCheck('version', application_package_name),
                            JMESPathCheck('state', 'active')])

        self.cmd('batch application set -g {} -n {} --application-id {} '
                 '--default-version {}'.format(
                     resource_group, account_name, application_name, application_package_name))

        self.cmd('batch application show -g {} -n {} --application-id {}'.format(
            resource_group, account_name, application_name)).assert_with_checks([
                JMESPathCheck('id', application_name),
                JMESPathCheck('defaultVersion', application_package_name),
                JMESPathCheck('packages[0].format', 'zip'),
                JMESPathCheck('packages[0].state', 'active')])

        # test batch applcation delete
        self.cmd('batch application package delete -g {} -n {} --application-id {} '
                 '--version {} --yes'.format(resource_group, account_name, application_name,
                                             application_package_name))
        self.cmd('batch application delete -g {} -n {} --application-id {} --yes'.format(
            resource_group, account_name, application_name))
        self.cmd('batch application list -g {} -n {}'.format(
            resource_group, account_name)).assert_with_checks(NoneCheck())

        self.cmd('storage account delete -g {} -n {} --yes'.format(
            resource_group, storage_account_name))
