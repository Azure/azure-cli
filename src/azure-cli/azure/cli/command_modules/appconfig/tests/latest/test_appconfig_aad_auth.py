# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import os
import time
import unittest

from azure.cli.command_modules.appconfig._credential import AppConfigurationCliCredential
from azure.cli.command_modules.appconfig._utils import get_appconfig_data_client
from azure.cli.core._profile import Profile
from azure.cli.core.auth.credential_adaptor import CredentialAdaptor
from azure.cli.core.auth.adal_authentication import MSIAuthenticationWrapper
from azure.cli.core.cloud import get_active_cloud
from azure.cli.core.mock import DummyCli
from knack.util import CLIError
from unittest import mock
from azure.cli.testsdk import (ResourceGroupPreparer, live_only, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants, KeyVaultConstants

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
APPCONFIG_AUTH_TOKEN_AUDIENCE = "https://appconfig.azure.com"

TEST_MI_SUBSCRIPTION = {
    "id": "00000000-0000-0000-0000-000000000000",
    "name": "MSI subscription",
    "isDefault": True,
    "state": "Enabled",
    "user": {
        "name": "systemAssignedIdentity"
    },
    "tenantId": "00000000-0000-0000-0000-000000000000",
    "environmentName": "AzureCloud",
    "homeTenantId": "00000000-0000-0000-0000-000000000000",
    "managedByTenants": []
}

TEST_USER_SUBSCRIPTION = {
    "id": "00000000-0000-0000-0000-000000000000",
    "name": "Service Principal Subscription",
    "state": "Enabled",
    "isDefault": True,
     "user": {
    "name": "tst_user@microsoft.com",
    "type": "user"
  },
    "tenantId": "00000000-0000-0000-0000-000000000000",
    "environmentName": "AzureCloud",
    "homeTenantId": "00000000-0000-0000-0000-000000000000",
    "managedByTenants": []
}

def mock_get_active_cloud(cli_ctx=None):
    cloud = get_active_cloud(cli_ctx)
    cloud.endpoints.appconfig_auth_token_audience = APPCONFIG_AUTH_TOKEN_AUDIENCE
    return cloud

class AppConfigAadAuthLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
    
    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_aad_auth(self, resource_group, location):
        aad_store_prefix = get_resource_name_prefix('AADStore')
        config_store_name = self.create_random_name(prefix=aad_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

        # Get connection string and add a key-value and feature flag using the default "key" auth mode
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })

        # Add a key-value
        entry_key = "Color"
        entry_value = "Red"
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value
        })
        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value)])

        # add a feature flag
        entry_feature = 'Beta'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + entry_feature
        default_description = ""
        default_conditions = "{{\'client_filters\': []}}"
        default_locked = False
        default_state = "off"
        self.kwargs.update({
            'feature': entry_feature,
            'description': default_description
        })
        self.cmd('appconfig feature set --connection-string {connection_string} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Get information about account logged in with 'az login'
        appconfig_id = self.cmd('appconfig show -n {config_store_name} -g {rg}').get_output_in_json()['id']
        account_info = self.cmd('account show').get_output_in_json()
        endpoint = "https://" + config_store_name + ".azconfig.io"
        self.kwargs.update({
            'appconfig_id': appconfig_id,
            'user_id': account_info['user']['name'],
            'endpoint': endpoint
        })

        # Before assigning data reader role, read operation should fail with AAD auth.
        # The exception really depends on the which identity is used to run this testcase.
        with self.assertRaisesRegex(CLIError, "Operation returned an invalid status 'Forbidden'"):
            self.cmd('appconfig kv show --endpoint {endpoint} --auth-mode login --key {key}')

        # Assign data reader role to current user
        self.cmd('role assignment create --assignee {user_id} --role "App Configuration Data Reader" --scope {appconfig_id}')
        time.sleep(900)  # It takes around 15 mins for RBAC permissions to propagate

        # After asssigning data reader role, read operation should succeed
        self.cmd('appconfig kv show --endpoint {endpoint} --auth-mode login --key {key}',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value)])

        # Since the logged in account also has "Contributor" role, providing --name instead of --endpoint should succeed
        self.cmd('appconfig feature show --name {config_store_name} --auth-mode login --feature {feature}',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Write operations should fail with "Forbidden" error
        updated_value = "Blue"
        self.kwargs.update({
            'value': updated_value
        })
        with self.assertRaisesRegex(CLIError, "Operation returned an invalid status 'Forbidden'"):
            self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} -y')

        # Export from appconfig to file should succeed
        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'True'
        exported_file_path = os.path.join(TEST_DIR, 'export_aad_1.json')
        expected_exported_file_path = os.path.join(TEST_DIR, 'expected_export_aad_1.json')
        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'separator': '/',
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv export --endpoint {endpoint} --auth-mode login -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} -y')
        with open(expected_exported_file_path) as json_file:
            expected_exported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert expected_exported_kvs == exported_kvs
        os.remove(exported_file_path)

        # Assign data owner role to current user
        self.cmd('role assignment create --assignee {user_id} --role "App Configuration Data Owner" --scope {appconfig_id}')
        time.sleep(900)  # It takes around 15 mins for RBAC permissions to propagate

        # After assigning data owner role, write operation should succeed
        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', updated_value)])

        # Add a KeyVault reference
        keyvault_key = "HostSecrets"
        keyvault_id = "https://fake.vault.azure.net/secrets/fakesecret"
        appconfig_keyvault_value = f"{{{json.dumps({'uri': keyvault_id})}}}"
        self.kwargs.update({
            'key': keyvault_key,
            'secret_identifier': keyvault_id
        })
        self.cmd('appconfig kv set-keyvault --endpoint {endpoint} --auth-mode login --key {key} --secret-identifier {secret_identifier} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', keyvault_key),
                         self.check('value', appconfig_keyvault_value)])

        # Import to appconfig should succeed
        imported_file_path = os.path.join(TEST_DIR, 'import_aad.json')
        exported_file_path = os.path.join(TEST_DIR, 'export_aad_2.json')
        expected_exported_file_path = os.path.join(TEST_DIR, 'expected_export_aad_2.json')
        self.kwargs.update({
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import --endpoint {endpoint} --auth-mode login -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} -y')

        # Export from appconfig to file should succeed
        self.cmd(
            'appconfig kv export --endpoint {endpoint} --auth-mode login -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} -y')
        with open(expected_exported_file_path) as json_file:
            expected_exported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert expected_exported_kvs == exported_kvs
        os.remove(exported_file_path)

    @unittest.skip("Incorrect test case")
    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper.set_token')
    @mock.patch('azure.cli.core.auth.adal_authentication.MSIAuthenticationWrapper.get_token')
    @mock.patch('azure.cli.core._profile.Profile.get_subscription')
    def test_azconfig_mi_token_override(self, get_subscriptions_mock, msi_get_token_mock, msi_set_token_mock):
        get_subscriptions_mock.return_value = TEST_MI_SUBSCRIPTION
        msi_get_token_mock.return_value = { "token": "mocked_token", "expires_on": 1234567890 }

        mock_cmd = mock.MagicMock()
        profile = Profile(cli_ctx=mock_cmd.cli_ctx)
        cred, _, _ = profile.get_login_credentials()

        appconfig_credential = AppConfigurationCliCredential(cred, APPCONFIG_AUTH_TOKEN_AUDIENCE)
        
        self.assertIsInstance(appconfig_credential._impl, MSIAuthenticationWrapper)
        self.assertTrue(hasattr(appconfig_credential._impl, 'get_token'))
        
        # Call get_token with an arbitrary scope
        _ = appconfig_credential.get_token("some_scope")

        # Assert that get_token was called with the correct scope
        appconfig_credential._impl.get_token.assert_called_once_with(f"{APPCONFIG_AUTH_TOKEN_AUDIENCE}/.default")

    @unittest.skip("Incorrect test case")
    @mock.patch('azure.cli.core.auth.msal_credentials.UserCredential')
    @mock.patch('azure.cli.core.auth.credential_adaptor.CredentialAdaptor.get_token')
    @mock.patch('azure.cli.core._profile.Profile.get_subscription')
    def test_azconfig_credential_adaptor_token_override(self, get_subscription_mock, get_token_mock, user_cred_mock):
        get_subscription_mock.return_value = TEST_USER_SUBSCRIPTION
        get_token_mock.return_value = { "token": "mocked_token", "expires_on": 1234567890 }

        profile = Profile(cli_ctx=DummyCli())
        cred, _, _ = profile.get_login_credentials()

        appconfig_credential = AppConfigurationCliCredential(cred, APPCONFIG_AUTH_TOKEN_AUDIENCE)
        
        self.assertIsInstance(appconfig_credential._impl, CredentialAdaptor)
        self.assertTrue(hasattr(appconfig_credential._impl, 'get_token'))
        
        # Call get_token with an arbitrary scope
        _ = appconfig_credential.get_token("some_scope")

        # Assert that get_token was called with the correct scope
        appconfig_credential._impl.get_token.assert_called_once_with(f"{APPCONFIG_AUTH_TOKEN_AUDIENCE}/.default")


    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_user_token_audience(self, resource_group, location):
        aad_store_prefix = get_resource_name_prefix('AADStore')
        config_store_name = self.create_random_name(prefix=aad_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        entry_key = "Color"
        entry_value = "Red"

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)
        
        appconfig_id = self.cmd('appconfig show -n {config_store_name} -g {rg}').get_output_in_json()['id']
        account_info = self.cmd('account show').get_output_in_json()
        endpoint = "https://" + config_store_name + ".azconfig.io"
        self.kwargs.update({
            'appconfig_id': appconfig_id,
            'user_id': account_info['user']['name'],
            'endpoint': endpoint
        })

        # Assign data reader role to current user
        self.cmd('role assignment create --assignee {user_id} --role "App Configuration Data Reader" --scope {appconfig_id}')

        self.kwargs.update({
            'entry_key': entry_key,
            'entry_value': entry_value
        })
        
        with mock.patch('azure.cli.command_modules.appconfig._credential.AppConfigurationCliCredential', wraps=AppConfigurationCliCredential) as cred_mock:
            try:
                self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {entry_key} --value {entry_value} -y',
                        checks=[self.check('key', entry_key),
                                self.check('value', entry_value)])
            
            # Might return 403 forbidden error if the role assignment is not propagated yet
            # This is expected behavior, so we can ignore it
            except CLIError as e:
                if "Operation returned an invalid status 'Forbidden'" not in str(e):
                    raise e

            # Assert that the ClientCredential was instantiated with no custom scope
            cred_mock.assert_called_with(mock.ANY, None)

            # Mock the get_active_cloud function to return a custom cloud with a custom token audience
            with mock.patch('azure.cli.core.cloud.get_active_cloud', new=mock_get_active_cloud):
                try:
                    self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {entry_key} --value {entry_value} -y',
                            checks=[self.check('key', entry_key),
                                    self.check('value', entry_value)])
            
                except CLIError as e:
                    if "Operation returned an invalid status 'Forbidden'" not in str(e):
                        raise e

                # Assert that the ClientCredential was instantiated with the correct scope
                cred_mock.assert_called_with(mock.ANY, APPCONFIG_AUTH_TOKEN_AUDIENCE)
