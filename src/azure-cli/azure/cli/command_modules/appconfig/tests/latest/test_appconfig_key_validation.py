# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import os

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigKeyValidationScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_key_validation(self, resource_group, location):
        config_store_prefix = get_resource_name_prefix('KVTest')
        config_store_name = self.create_random_name(prefix=config_store_prefix, length=36)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

        # get connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })

        # validate key
        self.kwargs.update({
            'key': "Col%%or",
            'value': "Red"
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        self.kwargs.update({
            'key': ""
        })
        with self.assertRaisesRegex(CLIError, "Key cannot be empty."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key "{key}" --value {value} -y')

        self.kwargs.update({
            'key': "."
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        # validate key for KeyVault ref
        self.kwargs.update({
            'key': "%KeyVault",
            'secret_identifier': "https://fake.vault.azure.net/secrets/fakesecret"
        })
        with self.assertRaisesRegex(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --secret-identifier {secret_identifier} -y')

        # validate feature name
        self.kwargs.update({
            'feature': 'Beta%'
        })
        with self.assertRaisesRegex(CLIError, "Feature name cannot contain the following characters: '%', ':'."):
            self.cmd('appconfig feature set --connection-string {connection_string} --feature {feature} -y')

        self.kwargs.update({
            'feature': ''
        })
        with self.assertRaisesRegex(CLIError, "Feature name cannot be empty."):
            self.cmd('appconfig feature set --connection-string {connection_string} --feature "{feature}" -y')

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
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} -y')
        with open(expected_export_file_path) as json_file:
            expected_export = json.load(json_file)
        with open(actual_export_file_path) as json_file:
            actual_export = json.load(json_file)
        assert expected_export == actual_export
        os.remove(actual_export_file_path)
