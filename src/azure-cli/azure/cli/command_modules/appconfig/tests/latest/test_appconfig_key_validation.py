# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import os

from knack.util import CLIError
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix, get_test_resource_group, register_appconfig_query_matcher, register_appconfig_recording_processors

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigKeyValidationScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
        register_appconfig_query_matcher(self)
        register_appconfig_recording_processors(self)
    
    @AllowLargeResponse()
    # Uses Entra ID auth (store created with local auth disabled); target a resource group where the
    # recording principal holds "App Configuration Data Owner". Override via AZURE_CLI_APPCONFIG_TEST_RG.
    def test_azconfig_key_validation(self):
        config_store_prefix = get_resource_name_prefix('kvtest')
        config_store_name = self.create_random_name(prefix=config_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': get_test_resource_group(),
            'sku': sku,
            'endpoint': 'https://' + config_store_name + '.azconfig.io'
        })
        create_config_store(self, self.kwargs, disable_local_auth=True)

        # validate key
        self.kwargs.update({
            'key': "Col%%or",
            'value': "Red"
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} -y')

        self.kwargs.update({
            'key': ""
        })
        with self.assertRaisesRegex(CLIError, "Key cannot be empty."):
            self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key "{key}" --value {value} -y')

        self.kwargs.update({
            'key': "."
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} -y')

        # validate key for KeyVault ref
        self.kwargs.update({
            'key': "%KeyVault",
            'secret_identifier': "https://fake.vault.azure.net/secrets/fakesecret"
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set-keyvault --endpoint {endpoint} --auth-mode login --key {key} --secret-identifier {secret_identifier} -y')

        # validate feature name
        self.kwargs.update({
            'feature': 'Beta%'
        })
        with self.assertRaisesRegex(CLIError, "Feature name cannot contain the following characters: '%', ':'."):
            self.cmd('appconfig feature set --endpoint {endpoint} --auth-mode login --feature {feature} -y')

        self.kwargs.update({
            'feature': ''
        })
        with self.assertRaisesRegex(CLIError, "Feature name cannot be empty."):
            self.cmd('appconfig feature set --endpoint {endpoint} --auth-mode login --feature "{feature}" -y')

        # validate keys and features during file import
        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'True'
        imported_file_path = os.path.join(TEST_DIR, 'import_invalid_kv_and_features.json')
        expected_export_file_path = os.path.join(TEST_DIR, 'expected_export_valid_kv_and_features.json')
        actual_export_file_path = os.path.join(TEST_DIR, 'actual_export_valid_kv_and_features.json')
        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'imported_file_path': imported_file_path,
            'exported_file_path': actual_export_file_path
        })
        self.cmd(
            'appconfig kv import --endpoint {endpoint} --auth-mode login -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')
        self.cmd(
            'appconfig kv export --endpoint {endpoint} --auth-mode login -d {import_source} --path "{exported_file_path}" --format {imported_format} -y')
        with open(expected_export_file_path) as json_file:
            expected_export = json.load(json_file)
        with open(actual_export_file_path) as json_file:
            actual_export = json.load(json_file)
        assert expected_export == actual_export
        os.remove(actual_export_file_path)
