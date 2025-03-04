# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json
import os
import time

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest, KeyVaultPreparer, live_only)
from azure.cli.command_modules.appconfig._constants import KeyVaultConstants
from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigKVScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_kv(self, resource_group, location):
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

        entry_key = "Color"
        entry_label = 'v1.0.0'

        self.kwargs.update({
            'key': entry_key,
            'label': entry_label
        })

        # add a new key-value entry
        self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} -y',
                 checks=[self.check('contentType', ""),
                         self.check('key', entry_key),
                         self.check('value', ""),
                         self.check('label', entry_label)])

        # edit a key-value entry
        updated_entry_value = "Green"
        entry_content_type = "text"

        self.kwargs.update({
            'value': updated_entry_value,
            'content_type': entry_content_type
        })

        self.cmd('appconfig kv set -n {config_store_name} --key {key} --value {value} --content-type {content_type} --label {label} -y',
                 checks=[self.check('contentType', entry_content_type),
                         self.check('key', entry_key),
                         self.check('value', updated_entry_value),
                         self.check('label', entry_label)])

        # add a new label
        updated_label = 'newlabel'
        self.kwargs.update({
            'label': updated_label
        })

        self.cmd('appconfig kv set -n {config_store_name} --key {key} --value {value} --content-type {content_type} --label {label} -y',
                 checks=[self.check('contentType', entry_content_type),
                         self.check('key', entry_key),
                         self.check('value', updated_entry_value),
                         self.check('label', updated_label)])

        # show a key-value
        self.cmd('appconfig kv show -n {config_store_name} --key {key} --label {label}',
                 checks=[self.check('contentType', entry_content_type),
                         self.check('value', updated_entry_value),
                         self.check('label', updated_label)])

        list_keys = self.cmd(
            'appconfig kv list -n {config_store_name}').get_output_in_json()
        assert len(list_keys) == 2

        revisions = self.cmd(
            'appconfig revision list -n {config_store_name} --key {key} --label *').get_output_in_json()
        assert len(revisions) == 3

        # Confirm that delete action errors out for empty or whitespace key
        with self.assertRaisesRegex(RequiredArgumentMissingError, "Key cannot be empty."):
            self.cmd('appconfig kv delete -n {config_store_name} --key " " -y')

        # IN CLI, since we support delete by key/label filters, return is a list of deleted items
        deleted = self.cmd('appconfig kv delete -n {config_store_name} --key {key} --label {label} -y',
                           checks=[self.check('[0].key', entry_key),
                                   self.check('[0].contentType', entry_content_type),
                                   self.check('[0].value', updated_entry_value),
                                   self.check('[0].label', updated_label)]).get_output_in_json()

        deleted_time = deleted[0]['lastModified']

        # sleep a little over 1 second
        time.sleep(1.1)

        # set key-value entry with connection string, but to the original value
        # take a note of the deleted_time
        entry_value = "Red"

        self.kwargs.update({
            'value': entry_value,
            'timestamp': deleted_time
        })

        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })
        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --content-type {content_type} --label {label} -y',
                 checks=[self.check('contentType', entry_content_type),
                         self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', updated_label)])

        # Now restore to last modified and ensure that we find updated_entry_value
        self.cmd('appconfig kv restore -n {config_store_name} --key {key} --label {label} --datetime {timestamp} -y')
        self.cmd('appconfig kv list -n {config_store_name} --key {key} --label {label}',
                 checks=[self.check('[0].contentType', entry_content_type),
                         self.check('[0].key', entry_key),
                         self.check('[0].value', updated_entry_value),
                         self.check('[0].label', updated_label)])

        # KeyVault reference tests
        keyvault_key = "HostSecrets"
        keyvault_id = "https://fake.vault.azure.net/secrets/fakesecret"
        keyvault_value = f"{{{json.dumps({'uri': keyvault_id})}}}"

        self.kwargs.update({
            'key': keyvault_key,
            'secret_identifier': keyvault_id
        })

        # Add new KeyVault ref
        self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --secret-identifier {secret_identifier} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', keyvault_key),
                         self.check('value', keyvault_value)])

        # Update existing key to KeyVault ref
        self.kwargs.update({
            'key': entry_key,
            'label': updated_label
        })

        self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --label {label} --secret-identifier {secret_identifier} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', entry_key),
                         self.check('value', keyvault_value),
                         self.check('label', updated_label)])

        # Delete KeyVault ref
        self.cmd('appconfig kv delete --connection-string {connection_string} --key {key} --label {label} -y',
                 checks=[self.check('[0].key', entry_key),
                         self.check('[0].contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('[0].value', keyvault_value),
                         self.check('[0].label', updated_label)])

        # add a key-value with null label
        kv_with_null_label = 'KvWithNullLabel'
        self.kwargs.update({
            'key': kv_with_null_label
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} -y',
                 checks=[self.check('key', kv_with_null_label),
                         self.check('label', None)])

        # List key-values with null label
        null_label_pattern = "\\0"
        self.kwargs.update({
            'null_label': null_label_pattern
        })
        list_keys = self.cmd(
            'appconfig kv list --connection-string {connection_string} --label "{null_label}"').get_output_in_json()
        assert len(list_keys) == 2

        # List key-values with multiple labels
        multi_labels = entry_label + ',' + null_label_pattern
        self.kwargs.update({
            'multi_labels': multi_labels
        })
        list_keys = self.cmd(
            'appconfig kv list --connection-string {connection_string} --label "{multi_labels}"').get_output_in_json()
        assert len(list_keys) == 3
    
        # # Filter by tags test

        # Set key-value with 5 tags
        key_with_tags = "KeyWithTags"
        label_with_tags = "labelWithTags"
        tags = {
            "tag1": "value1",
            "tag2": "value2",
            "tag3": "value3",
            "tag4": "value4",
            "tag5": "value5"
        }
        tags_str = ' '.join([f"{k}={v}" for k, v in tags.items()])

        self.kwargs.update({
            'key': key_with_tags,
            'label': label_with_tags,
            'tags': tags_str
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --label {label} --tags {tags} -y',
             checks=[self.check('key', key_with_tags),
             self.check('label', label_with_tags),
            self.check('tags', tags)])

        # List key-values with 5 tags
        list_keys = self.cmd('appconfig kv list --connection-string {connection_string} --key {key} --tags {tags}').get_output_in_json()
        assert(list_keys[0]['key'] == key_with_tags)
        assert(list_keys[0]['label'] == label_with_tags)
        assert(list_keys[0]['tags'] == tags)
        assert len(list_keys) == 1

        # Set key-value with tag1 only
        tag1_dict = {"tag1": "value1"}
        tag1 = ' '.join([f"{k}={v}" for k, v in tag1_dict.items()])
        label_with_tag1 = "labelWithTag1"
        self.kwargs.update({
            'label': label_with_tag1,
            'tag1': tag1
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --label {label} --tags {tag1} -y',
             checks=[self.check('key', key_with_tags),
                 self.check('label', label_with_tag1),
                 self.check('tags', tag1_dict)])

        # List key-values with tag1
        list_keys = self.cmd('appconfig kv list --connection-string {connection_string} --key {key} --tags {tag1}').get_output_in_json()
        assert len(list_keys) == 2

        # Set key with tags with null value
        # tag_with_null_value_dict = {"tag1": "\\0"}
        # tag_with_null_value = ' '.join([f"{k}={v}" for k, v in tag_with_null_value_dict.items()])
        # new_label_for_null_tag = "newLabelForNullTag"
        # self.kwargs.update({
        #     'label': new_label_for_null_tag,
        #     'tag_with_null_value': tag_with_null_value
        # })

        # self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --label {label} --tags "{tag_with_null_value}" -y',
        #      checks=[self.check('key', key_with_tags),
        #      self.check('label', new_label_for_null_tag),
        #      self.check('tags', tag_with_null_value_dict)])

        # # List key-values with tag with null value
        # list_keys = self.cmd('appconfig kv list --connection-string {connection_string} --key {key} --tags "{tag_with_null_value}"').get_output_in_json()
        # assert len(list_keys) == 1

        # Set key-value with empty tag value
        empty_tag_value_dict = {"tag1": ""}
        tag_with_empty_value = ' '.join([f"{k}={v}" for k, v in empty_tag_value_dict.items()])
        label_with_empty_tag_value = "labelWithEmptyTagValue"
        self.kwargs.update({
            'label': label_with_empty_tag_value,
            'tag_with_empty_value': tag_with_empty_value
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --label {label} --tags {tag_with_empty_value} -y',
             checks=[self.check('key', key_with_tags),
                 self.check('label', label_with_empty_tag_value),
                 self.check('tags', empty_tag_value_dict)])

        # List key-values with tag with empty value
        list_keys = self.cmd('appconfig kv list --connection-string {connection_string} --key {key} --tags {tag_with_empty_value}').get_output_in_json()
        assert len(list_keys) == 1

        # Get all key-values with all tags
        list_keys = self.cmd('appconfig kv list --connection-string {connection_string} --key {key}').get_output_in_json()
        assert len(list_keys) == 3

        # Delete key-values with tags tag1=value1
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {connection_string} --key {key} --label {label} --tags {tag1} -y',
             checks=[self.check('[0].key', key_with_tags),
                    self.check('[0].label', label_with_tag1),
                    self.check('[0].tags', tag1_dict)])
        assert(len(deleted_kvs) == 2)


    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @KeyVaultPreparer(additional_params="--enable-rbac-authorization false")
    @live_only()
    def test_resolve_keyvault(self, key_vault, resource_group):
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

        # Export secret test
        secret_name = 'testSecret'
        secret_value = 'testValue'
        self.kwargs.update({
            'secret_name': secret_name,
            'secret_value': secret_value,
            'keyvault_name': key_vault
        })

        secret = self.cmd('az keyvault secret set --vault-name {keyvault_name} -n {secret_name} --value {secret_value}').get_output_in_json()
        self.kwargs.update({
            'secret_identifier': secret["id"]
        })

        self.cmd('appconfig kv set-keyvault -n {config_store_name} --key {secret_name} --secret-identifier {secret_identifier} -y')

        self.cmd('appconfig kv list -n {config_store_name} --resolve-keyvault',
                 checks=[self.check('[0].key', secret_name),
                         self.check('[0].value', secret_value)])

        exported_file_path = os.path.join(TEST_DIR, 'export_keyvault.json')

        self.kwargs.update({
            'import_source': 'file',
            'exported_file_path': exported_file_path,
            'imported_format': 'json',
        })

        self.cmd('appconfig kv export -n {config_store_name} -d file --path "{exported_file_path}" --format json --resolve-keyvault -y')
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)

        assert len(exported_kvs) == 1
        assert exported_kvs[secret_name] == secret_value
        os.remove(exported_file_path)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_kv_revision_list(self, resource_group, location):
        config_store_prefix = get_resource_name_prefix('KVRevisionTest')
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

        entry_key = "Color"
        entry_label = 'v1.0.0'

        self.kwargs.update({
            'key': entry_key,
            'label': entry_label
        })

        # add a new key-value entry
        self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} -y',
                 checks=[self.check('contentType', ""),
                         self.check('key', entry_key),
                         self.check('value', ""),
                         self.check('label', entry_label)])

        # edit a key-value entry
        updated_entry_value = "Green"
        entry_content_type = "text"

        self.kwargs.update({
            'value': updated_entry_value,
            'content_type': entry_content_type
        })

        self.cmd(
            'appconfig kv set -n {config_store_name} --key {key} --value {value} --content-type {content_type} --label {label} -y',
            checks=[self.check('contentType', entry_content_type),
                    self.check('key', entry_key),
                    self.check('value', updated_entry_value),
                    self.check('label', entry_label)])

        # add a new label
        updated_label = 'newlabel'
        self.kwargs.update({
            'label': updated_label
        })

        self.cmd(
            'appconfig kv set -n {config_store_name} --key {key} --value {value} --content-type {content_type} --label {label} -y',
            checks=[self.check('contentType', entry_content_type),
                    self.check('key', entry_key),
                    self.check('value', updated_entry_value),
                    self.check('label', updated_label)])

        revisions = self.cmd('appconfig revision list -n {config_store_name} --key {key} --label * --top 2 --fields content_type etag label last_modified value').get_output_in_json()
        assert len(revisions) == 2

        assert revisions[0]['content_type'] == 'text'
        assert revisions[1]['content_type'] == 'text'
        assert revisions[0]['label'] == 'newlabel'
        assert revisions[1]['label'] == 'v1.0.0'
        assert revisions[0]['value'] == 'Green'
        assert revisions[1]['value'] == 'Green'
        assert revisions[0]['last_modified'] is not None
        assert revisions[1]['last_modified'] is not None
        assert revisions[1]['etag'] is not None
        assert revisions[0]['etag'] is not None
        assert 'key' not in revisions[0]
        assert 'key' not in revisions[1]
        assert 'locked' not in revisions[0]
        assert 'locked' not in revisions[1]
        assert 'tags' not in revisions[0]
        assert 'tags' not in revisions[1]

        # Filter by tags test
        key_with_tags = "KeyWithTags"
        label_with_tags = "labelWithTags"
        tags = {
            "tag1": "value1",
            "tag2": "value2",
            "tag3": "value3",
            "tag4": "value4",
            "tag5": "value5"
        }
        tags_str = ' '.join([f"{k}={v}" for k, v in tags.items()])

        self.kwargs.update({
            'key': key_with_tags,
            'label': label_with_tags,
            'tags': tags_str
        })

        self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} --tags {tags} -y',
             checks=[self.check('key', key_with_tags),
                 self.check('label', label_with_tags),
                 self.check('tags', tags)])

        # List revisions with 5 tags
        list_keys = self.cmd('appconfig revision list -n {config_store_name} --key {key} --tags {tags}').get_output_in_json()
        assert len(list_keys) == 1

        # Set key-value with tag1 only
        tag1_dict = {"tag1": "value1"}
        tag1 = ' '.join([f"{k}={v}" for k, v in tag1_dict.items()])
        label_with_tag1 = "labelWithTag1"
        self.kwargs.update({
            'label': label_with_tag1,
            'tag1': tag1
        })

        self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} --tags {tag1} -y',
             checks=[self.check('key', key_with_tags),
                 self.check('label', label_with_tag1),
                    self.check('tags', tag1_dict)])

        # List revisions with tag1 = value1
        list_keys = self.cmd('appconfig revision list -n {config_store_name} --key {key} --tags {tag1}').get_output_in_json()
        assert len(list_keys) == 2

        # # Set key with tags with null value
        # tag_null_value_dict = {"tag1": "\\0"}
        # tag_with_null_value = ' '.join([f"{k}={v}" for k, v in tag_null_value_dict.items()])
        # self.kwargs.update({
        #     'tag_with_null_value': tag_with_null_value
        # })

        # self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} --tags "{tag_with_null_value}" -y',
        #      checks=[self.check('key', key_with_tags),
        #             self.check('tags', tag_null_value_dict)])

        # # List revisions with tag with null value
        # list_keys = self.cmd('appconfig revision list -n {config_store_name} --key {key} --tags "{tag_with_null_value}"').get_output_in_json()
        # assert len(list_keys) == 1

        # Set key-value with empty tag value
        empty_tag_value_dict = {"tag1": ""}
        tag_with_empty_value = ' '.join([f"{k}={v}" for k, v in empty_tag_value_dict.items()])
        self.kwargs.update({
            'tag_with_empty_value': tag_with_empty_value
        })

        self.cmd('appconfig kv set -n {config_store_name} --key {key} --label {label} --tags {tag_with_empty_value} -y',
             checks=[self.check('key', key_with_tags),
                    self.check('tags', empty_tag_value_dict)])

        # List revisions with tag with empty value
        list_keys = self.cmd('appconfig revision list -n {config_store_name} --key {key} --tags {tag_with_empty_value}').get_output_in_json()
        assert len(list_keys) == 1

        # Get all key-value revisions for key with all tags
        revisions = self.cmd('appconfig revision list -n {config_store_name} --key {key} --label *').get_output_in_json()
        assert len(revisions) == 3
