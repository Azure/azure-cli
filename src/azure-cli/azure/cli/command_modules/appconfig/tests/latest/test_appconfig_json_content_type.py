# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import os

from unittest import TestCase
import yaml

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix
from azure.cli.command_modules.appconfig._constants import AIConfigConstants, FeatureFlagConstants, KeyVaultConstants

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigJsonContentTypeScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_json_content_type(self, resource_group, location):
        src_config_store_prefix = get_resource_name_prefix('Source')
        dest_config_store_prefix = get_resource_name_prefix('Destination')
        src_config_store_name = self.create_random_name(prefix=src_config_store_prefix, length=24)
        dest_config_store_name = self.create_random_name(prefix=dest_config_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': src_config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

        # Get src connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'src_connection_string': credential_list[0]['connectionString'],
            'config_store_name': dest_config_store_name
        })
        create_config_store(self, self.kwargs)

        # Get dest connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'dest_connection_string': credential_list[0]['connectionString']
        })

        """
        Test Scenario 1: Create settings with JSON Content Type
            - Create settings in Src AppConfig store with JSON Content type
            - Make sure that input value is in valid JSON format
        """

        entry_key = "Key01"
        entry_value = '\\"Red\\"'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_01 = 'application/json'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_01
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_01)])

        entry_key = "Key02"
        entry_value = '\\"Red\\Robin\\Hood\\"'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_02 = 'application/json;charset=utf-8'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_02
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_02)])

        entry_key = "Key03"
        entry_value = 'true'
        json_content_type_03 = 'application/boolean+json;'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_03
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('contentType', json_content_type_03)])

        entry_key = "Key04"
        entry_value = '45.6'
        json_content_type_04 = 'application/json+text+number;charset=utf-8;param1=value1'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_04
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('contentType', json_content_type_04)])

        entry_key = "Key05"
        entry_value = '\\"true\\"'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_05 = 'application/string+json;'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_05
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_05)])

        entry_key = "Key06"
        entry_value = '\\"999\\"'
        appconfig_value = entry_value.replace('\\', '')
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_05)])

        entry_key = "Key07"
        entry_value = 'null'
        json_content_type_07 = 'application/json+null;charset=utf-8;'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_07
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('contentType', json_content_type_07)])

        entry_key = "Key08"
        entry_value = '[1,2,3,4]'
        json_content_type_08 = 'application/vnd.numericarray+json'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_08
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('contentType', json_content_type_08)])

        entry_key = "Key09"
        entry_value = '[\\"abc\\",\\"def\\"]'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_09 = 'application/vnd.stringarray+json'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_09
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_09)])

        entry_key = "Key10"
        entry_value = '[\\"text\\",true,null]'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_10 = 'application/json+hybridarray'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_10
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_10)])

        entry_key = "Key11"
        entry_value = '{\\"Name\\":\\"Value\\"}'
        appconfig_value = entry_value.replace('\\', '')
        json_content_type_11 = 'application/json'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'appconfig_value': appconfig_value,
            'content_type': json_content_type_11
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', '{appconfig_value}'),
                         self.check('contentType', json_content_type_11)])

        entry_key = "Key12"
        entry_value = '{\\"MyNullValue\\":null,\\"MyObject\\":{\\"Property\\":{\\"Name\\":{\\"Name1\\":\\"Value1\\",\\"Name2\\":[\\"qqq\\",\\"rrr\\"]}}},\\"MyArray\\":[1,2,3]}'
        appconfig_value = entry_value.replace('\\', '')
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'appconfig_value': appconfig_value
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', '{appconfig_value}'),
                         self.check('contentType', json_content_type_11)])

        # Treat missing value argument as null value
        entry_key = "Key13"
        appconfig_value = "null"
        json_content_type_13 = 'application/null+json+empty'
        self.kwargs.update({
            'key': entry_key,
            'content_type': json_content_type_13
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', appconfig_value),
                         self.check('contentType', json_content_type_13)])

        # Validate that input value is in JSON format
        entry_key = "Key14"
        entry_value = 'Red'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'content_type': json_content_type_01
        })
        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')

        self.kwargs.update({
            'value': '[abc,def]'
        })
        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')

        self.kwargs.update({
            'value': 'True'
        })
        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')

        # Create a non-JSON key-value and update its content type in subsequent command
        self.kwargs.update({
            'value': entry_value
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value)])

        with self.assertRaisesRegex(CLIError, "Set the value again in valid JSON format."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --content-type {content_type} -y')

        # Create a JSON value with both single-line and multiline comments and confirm it can be successfully set though sanitized
        entry_key = "Key15"

        json_with_comments = """{"key1": "value1 is of the type \\"string\\"",// single-line comment\n"key2": "value2"
/* multiline 
 comment */}"""

        self.kwargs.update({
            'key': entry_key,
            'value': json.dumps(json_with_comments).replace('\\n', '\n'), # Escape quotes again to pass as input to CLI command template
            'content_type': json_content_type_01
        })

        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', f"{{{json_with_comments}}}"),
                         self.check('contentType', json_content_type_01)])
        
        # Ensure this request fails with keyvault content type
        self.kwargs.update({
            'content_type': KeyVaultConstants.KEYVAULT_CONTENT_TYPE
        })

        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')

        # Ensure this request fails with Feature flag content type
        self.kwargs.update({
            'content_type': FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE
        })

        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')
        

        # Ensure this request fails with AI Chat Completion content type
        self.kwargs.update({
            'content_type': AIConfigConstants.AI_CHAT_COMPLETION_CONTENT_TYPE
        })

        with self.assertRaisesRegex(CLIError, "is not a valid JSON object, which conflicts with the content type."):
            self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --content-type {content_type} -y')


        """
        Test Scenario 2: AppConfig <--> AppConfig Import/Export
            - Add Feature Flag and Key vault Reference
            - Import settings from Src to Dest AppConfig store with JSON content type
            - Export to JSON file from src config store
            - Export to JSON file from dest config store
            - Compare both exported files
            - Delete all settings from dest config store
            - Export settings from Src to Dest AppConfig store
            - Export to JSON file from src config store
            - Export to JSON file from dest config store
            - Compare both exported files
            - Delete all settings from both stores
        """

        # Add a new feature flag
        entry_feature = 'Beta'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + entry_feature
        default_description = ""
        default_conditions = "{{\'client_filters\': []}}"
        default_locked = False
        default_state = "off"
        self.kwargs.update({
            'feature': entry_feature
        })
        self.cmd('appconfig feature set --connection-string {src_connection_string} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Add new KeyVault reference
        keyvault_key = "HostSecrets"
        keyvault_id = "https://fake.vault.azure.net/secrets/fakesecret"
        keyvault_value = f"{{{json.dumps({'uri': keyvault_id})}}}"
        self.kwargs.update({
            'key': keyvault_key,
            'secret_identifier': keyvault_id
        })
        self.cmd('appconfig kv set-keyvault --connection-string {src_connection_string} --key {key} --secret-identifier {secret_identifier} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', keyvault_key),
                         self.check('value', keyvault_value)])

        # Test IMPORT function by importing all settings from src config store to dest config store
        self.kwargs.update({
            'import_source': 'appconfig'
        })
        self.cmd(
            'appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --content-type {content_type} -y')

        # Export to JSON file from src config store
        exported_src_file_path = os.path.join(TEST_DIR, 'json_export_src.json')
        self.kwargs.update({
            'export_dest': 'file',
            'export_format': 'json',
            'separator': ':',
            'exported_file_path': exported_src_file_path,
        })
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {export_dest} --path "{exported_file_path}" --format {export_format} --separator {separator} -y')

        # Export to JSON file from dest config store
        exported_dest_file_path = os.path.join(TEST_DIR, 'json_export_dest.json')
        self.kwargs.update({
            'exported_file_path': exported_dest_file_path
        })
        self.cmd(
            'appconfig kv export --connection-string {dest_connection_string} -d {export_dest} --path "{exported_file_path}" --format {export_format} --separator {separator} -y')
        with open(exported_src_file_path) as json_file:
            src_kvs = json.load(json_file)
        with open(exported_dest_file_path) as json_file:
            dest_kvs = json.load(json_file)
        assert src_kvs == dest_kvs

        # Delete all settings from dest config store
        any_key_pattern = '*'
        any_label_pattern = '*'
        self.kwargs.update({
            'key': any_key_pattern,
            'label': any_label_pattern
        })
        self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y')

        # Test EXPORT function by exporting all settings from src config store to dest config store
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} -y')

        # Export to JSON file from src config store
        exported_src_file_path = os.path.join(TEST_DIR, 'json_export_src.json')
        self.kwargs.update({
            'export_dest': 'file',
            'export_format': 'json',
            'separator': ':',
            'exported_file_path': exported_src_file_path,
        })
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {export_dest} --path "{exported_file_path}" --format {export_format} --separator {separator} -y')

        # Export to JSON file from dest config store
        exported_dest_file_path = os.path.join(TEST_DIR, 'json_export_dest.json')
        self.kwargs.update({
            'exported_file_path': exported_dest_file_path
        })
        self.cmd(
            'appconfig kv export --connection-string {dest_connection_string} -d {export_dest} --path "{exported_file_path}" --format {export_format} --separator {separator} -y')
        with open(exported_src_file_path) as json_file:
            src_kvs = json.load(json_file)
        with open(exported_dest_file_path) as json_file:
            dest_kvs = json.load(json_file)
        assert src_kvs == dest_kvs
        os.remove(exported_dest_file_path)
        os.remove(exported_src_file_path)

        # Delete all settings from both config stores
        self.cmd('appconfig kv delete --connection-string {src_connection_string} --key {key} --label {label} -y')
        self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y')

        """
        Test Scenario 3: File <--> AppConfig Import/Export
            - Import settings to config store from JSON file with JSON content type
            - Export settings from config store to JSON file
            - Compare imported and exported files
            - Delete all settings from both stores
        """

        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'True'
        imported_file_path = os.path.join(TEST_DIR, 'json_import.json')
        exported_file_path = os.path.join(TEST_DIR, 'json_export.json')
        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'separator': ':',
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import --connection-string {src_connection_string} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} --content-type {content_type} -y')
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} -y')
        with open(exported_file_path) as json_file:
            exported_file = json.load(json_file)
        with open(imported_file_path) as json_file:
            imported_file = json.load(json_file)
        assert exported_file == imported_file

        """
        Test Scenario 4: JSON Content Type and YAML files
            - Import settings from YAML file with JSON content type should fail
            - Export settings to YAML file should not fail even though settings have JSON content type
            - Compare previously exported settings in json format with the newly exported settings in YAML format
            - Delete all settings from config store
        """

        imported_file_path = os.path.join(TEST_DIR, 'yaml_import.json')
        exported_yaml_file_path = os.path.join(TEST_DIR, 'yaml_export.json')
        self.kwargs.update({
            'imported_format': 'yaml',
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_yaml_file_path
        })
        with self.assertRaisesRegex(CLIError, "Please provide JSON file format to match your content type."):
            self.cmd('appconfig kv import --connection-string {src_connection_string} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} --content-type {content_type} -y')

        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} -y')
        exported_yaml_file = {}
        exported_json_file = {}
        with open(exported_yaml_file_path) as yaml_file:
            for yaml_data in list(yaml.safe_load_all(yaml_file)):
                exported_yaml_file.update(yaml_data)
        with open(exported_file_path) as json_file:
            exported_json_file = json.load(json_file)
        assert exported_yaml_file == exported_json_file
        os.remove(exported_yaml_file_path)
        os.remove(exported_file_path)

class AppConfigJsonCommentsTest(TestCase):
    def test_azconfig_strip_json_comments(self):
        from azure.cli.command_modules.appconfig._json import parse_json_with_comments

        json_with_comments_file_path = os.path.join(TEST_DIR, 'json_with_comments.json')
        clean_json_file_path = os.path.join(TEST_DIR, 'json_with_comments_stripped.json')

        with open(json_with_comments_file_path) as json_file:
            parsed_json = parse_json_with_comments(json_file.read())

        with open(clean_json_file_path) as json_file:
            expected_json = json.load(json_file)

        self.assertEqual(parsed_json, expected_json)
