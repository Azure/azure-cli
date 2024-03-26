# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import javaproperties
import json
import os
import sys
import time
import yaml

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest, KeyVaultPreparer, live_only, LiveScenarioTest)
from azure.cli.testsdk.checkers import NoneCheck
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants, KeyVaultConstants, ImportExportProfiles, AppServiceConstants
from azure.cli.testsdk.scenario_tests import AllowLargeResponse, RecordingProcessor
from azure.cli.testsdk.scenario_tests.utilities import is_json_payload
from azure.core.exceptions import ResourceNotFoundError
from azure.cli.core.azclierror import ResourceNotFoundError as CliResourceNotFoundError, RequiredArgumentMissingError, MutuallyExclusiveArgumentError
from azure.cli.core.util import shell_safe_json_parse

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class AppConfigMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_mgmt(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='MgmtTest', length=24)

        location = 'eastus'
        sku = 'standard'
        tag_key = "key"
        tag_value = "value"
        tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        system_assigned_identity = '[system]'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'tags': tag,
            'identity': system_assigned_identity,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        store = self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}',
                         checks=[self.check('name', '{config_store_name}'),
                                 self.check('location', '{rg_loc}'),
                                 self.check('resourceGroup', resource_group),
                                 self.check('provisioningState', 'Succeeded'),
                                 self.check('sku.name', sku),
                                 self.check('tags', structured_tag),
                                 self.check('identity.type', 'SystemAssigned'),
                                 self.check('softDeleteRetentionInDays', '{retention_days}'),
                                 self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()

        self.cmd('appconfig list -g {rg}',
                 checks=[self.check('[0].name', '{config_store_name}'),
                         self.check('[0].location', '{rg_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].sku.name', sku),
                         self.check('[0].tags', structured_tag),
                         self.check('[0].identity.type', 'SystemAssigned')])

        self.cmd('appconfig show -n {config_store_name} -g {rg}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('tags', structured_tag),
                         self.check('identity.type', 'SystemAssigned')])

        tag_key = "Env"
        tag_value = "Prod"
        updated_tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        self.kwargs.update({
            'updated_tag': updated_tag,
            'update_sku': sku   # we currently only can test on standard sku
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --tags {updated_tag} --sku {update_sku}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('tags', structured_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku)])

        keyvault_name = self.create_random_name(prefix='cmk-test-keyvault', length=24)
        encryption_key = 'key'
        system_assigned_identity_id = store['identity']['principalId']
        self.kwargs.update({
            'encryption_key': encryption_key,
            'keyvault_name': keyvault_name,
            'identity_id': system_assigned_identity_id
        })

        keyvault = _setup_key_vault(self, self.kwargs)
        keyvault_uri = keyvault['properties']['vaultUri']
        self.kwargs.update({
            'keyvault_uri': keyvault_uri,
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --encryption-key-name {encryption_key} --encryption-key-vault {keyvault_uri}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('tags', structured_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('encryption.keyVaultProperties.keyIdentifier', keyvault_uri.strip('/') + "/keys/{}/".format(encryption_key))])

        self.kwargs.update({
            'updated_tag': '""',
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --tags {updated_tag}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('tags', {}),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('sku.name', sku),
                    self.check('encryption.keyVaultProperties.keyIdentifier', keyvault_uri.strip('/') + "/keys/{}/".format(encryption_key))])

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        config_store_name = self.create_random_name(prefix='MgmtTestdel', length=24)

        self.kwargs.update({
            'config_store_name': config_store_name
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}')
        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        self.cmd('appconfig show-deleted -n {config_store_name}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('purgeProtectionEnabled', '{enable_purge_protection}')])

        deleted_stores = self.cmd('appconfig list-deleted').get_output_in_json()

        found = False
        for deleted_store in deleted_stores:
            if deleted_store['name'] == config_store_name:
                assert deleted_store['location'] == location
                found = True
                break
        assert found

        self.cmd('appconfig recover -n {config_store_name} -y')

        self.cmd('appconfig show -n {config_store_name}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}')])

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')

        self.cmd('appconfig purge -n {config_store_name} -y')

        with self.assertRaisesRegex(CLIError, f'Failed to find the deleted App Configuration store \'{config_store_name}\'.'):
            self.cmd('appconfig show-deleted -n {config_store_name}')

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_local_auth(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='DisableLocalAuth', length=24)

        location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'disable_local_auth': 'true',
            'retention_days': 1
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --disable-local-auth {disable_local_auth} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('disableLocalAuth', True)])

        self.kwargs.update({
            'key': 'test',
            'disable_local_auth': 'false'
        })

        with self.assertRaisesRegex(CLIError, "Cannot find a read write access key for the App Configuration {}".format(config_store_name)):
            self.cmd('appconfig kv set --key {key} -n {config_store_name} -y')

        self.cmd('appconfig update -n {config_store_name} -g {rg} --disable-local-auth {disable_local_auth}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('disableLocalAuth', False)])

        self.cmd('appconfig kv set --key {key} -n {config_store_name} -y',
                 checks=[self.check('key', '{key}')])

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_public_network_access(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='PubNetworkTrue', length=24)

        location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'enable_public_network': 'true',
            'retention_days': 1
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --enable-public-network {enable_public_network} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', 'Enabled')])

        config_store_name = self.create_random_name(prefix='PubNetworkNull', length=24)

        self.kwargs.update({
            'config_store_name': config_store_name
        })

        self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', None)])

        # Enable public network access with update command
        self.cmd('appconfig update -n {config_store_name} -g {rg} --enable-public-network',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('publicNetworkAccess', 'Enabled')])


class AppConfigCredentialScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_credential(self, resource_group, location):

        config_store_name = self.create_random_name(prefix='CredentialTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })

        _create_config_store(self, self.kwargs)

        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        assert len(credential_list) == 4
        assert next(credential['connectionString']
                    for credential in credential_list if not credential['readOnly'])

        self.kwargs.update({
            'id': credential_list[0]['id']
        })

        self.cmd('appconfig credential regenerate -n {config_store_name} -g {rg} --id {id}',
                 checks=[self.check('name', credential_list[0]['name'])])


class AppConfigIdentityScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_identity(self, resource_group, location):

        config_store_name = self.create_random_name(prefix='IdentityTest', length=24)

        location = 'eastus'
        sku = 'standard'
        identity_name = self.create_random_name(prefix='UserAssignedIdentity', length=24)

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'identity_name': identity_name
        })

        _create_config_store(self, self.kwargs)
        user_assigned_identity = _create_user_assigned_identity(self, self.kwargs)

        self.kwargs.update({
            'identity_id': user_assigned_identity['id']
        })

        self.cmd('appconfig identity assign -n {config_store_name} -g {rg}',
                 checks=[self.check('type', 'SystemAssigned'),
                         self.check('userAssignedIdentities', None)])

        self.cmd('appconfig identity assign -n {config_store_name} -g {rg} --identities {identity_id}',
                 checks=[self.check('type', 'SystemAssigned, UserAssigned')])

        self.cmd('appconfig identity remove -n {config_store_name} -g {rg} --identities {identity_id}')

        self.cmd('appconfig identity show -n {config_store_name} -g {rg}',
                 checks=[self.check('type', 'SystemAssigned'),
                         self.check('userAssignedIdentities', None)])


class AppConfigKVScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_kv(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='KVTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

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
            'timestamp': _format_datetime(deleted_time)
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
        keyvault_value = "{{\"uri\":\"https://fake.vault.azure.net/secrets/fakesecret\"}}"

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

    @AllowLargeResponse()
    @ResourceGroupPreparer()
    @KeyVaultPreparer()
    @live_only()
    def test_resolve_keyvault(self, key_vault, resource_group):
        config_store_name = self.create_random_name(prefix='KVTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

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
        config_store_name = self.create_random_name(prefix='KVRevisionTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

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


class AppConfigImportExportScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='ImportTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # File <--> AppConfig tests

        imported_file_path = os.path.join(TEST_DIR, 'import.json')
        imported_json_array = os.path.join(TEST_DIR, 'import_json_array.json')
        imported_plain_string_file_path = os.path.join(TEST_DIR, 'import_invalid_plain_string.json')
        exported_file_path = os.path.join(TEST_DIR, 'export.json')
        exported_json_object = os.path.join(TEST_DIR, 'export_changed_json.json')
        exported_json_object_reference = os.path.join(TEST_DIR, 'export_changed_json_ref.json')
 
        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'separator': '/',
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} -y')
        with open(imported_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # ignore already existing kvs
        ignore_match_file_path = os.path.join(TEST_DIR, 'ignore_match_import.json')
        key_name = 'BackgroundColor'
        self.kwargs.update({
            'key': key_name,
            'imported_file_path': ignore_match_file_path
        })

        background_color_kv = self.cmd('appconfig kv show -n {config_store_name} --key {key}').get_output_in_json()
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} -y')

        # Confirm that the key has the same etag after re-importing
        self.cmd('appconfig kv show -n {config_store_name} --key {key}',
                 checks=[
                     self.check('key', key_name),
                     self.check('etag', background_color_kv['etag']),
                     ])
        
        self.kwargs.update({
            'imported_file_path': imported_file_path
        })

        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} -y --import-mode all')
        
        updated_background_color_kv = self.cmd('appconfig kv show -n {config_store_name} --key {key}').get_output_in_json()

        self.assertNotEquals(background_color_kv['etag'], updated_background_color_kv['etag'])

        # skip key vault reference while exporting
        self.kwargs.update({
            'key': "key_vault_reference",
            'secret_identifier': "https://testkeyvault.vault.azure.net/secrets/mysecret"
        })
        self.cmd(
            'appconfig kv set-keyvault -n {config_store_name} --key {key} --secret-identifier {secret_identifier} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} --skip-keyvault -y')
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs
        os.remove(exported_file_path)

        # Error out when importing plain string.
        self.kwargs.update({
            'imported_file_path': imported_plain_string_file_path
        })

        with self.assertRaisesRegex(CLIError, "The input is not a well formatted json file.\nException: Json object required but type 'str' was given."):
            self.cmd(
                'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format}')

        '''
        1. Import configuration from JSON file which has a key "arr" with array values. Assign label "array_test" and separator "/"
        2. Add new value with the same prefix as the array data key but not continuous with array indices. (e.g., "arr/foo")
        3. Export configurations with the same label to a JSON file.
        4. Confirm that the value of "arr" is now a JSON object.
        '''
        self.kwargs.update({
            'imported_file_path': imported_json_array,
            'exported_file_path': exported_json_object,
            'key': 'arr/foo',
            'value': 'bar',
            'label': 'array_test'
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --separator {separator} --label {label} -y')
        self.cmd(
            'appconfig kv set -n {config_store_name} --key {key} --value {value} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --separator {separator} --label {label} -y')
        with open(exported_json_object) as json_file:
            exported_kvs = json.load(json_file)
        with open(exported_json_object_reference) as json_file:
            expected_exported_kvs = json.load(json_file)
        assert expected_exported_kvs == exported_kvs
        os.remove(exported_json_object)


        # Feature flags test
        imported_file_path = os.path.join(TEST_DIR, 'import_features.json')
        exported_file_path = os.path.join(TEST_DIR, 'export_features.json')
        key_filtered_features_file_path = os.path.join(TEST_DIR, 'key_filtered_features.json')
        prefix_added_features_file_path = os.path.join(TEST_DIR, 'prefix_added_features.json')
        skipped_features_file_path = os.path.join(TEST_DIR, 'skipped_features.json')
        export_separator_features_file_path = os.path.join(TEST_DIR, 'export_separator_features.json')
        import_separator_features_file_path = os.path.join(TEST_DIR, 'import_separator_features.json')
        import_features_alt_syntax_file_path = os.path.join(TEST_DIR, 'import_features_alt_syntax.json')
        import_features_random_conditions_file_path = os.path.join(TEST_DIR, 'import_features_random_conditions.json')
        import_features_invalid_requirement_type_file_path = os.path.join(TEST_DIR, 'import_features_invalid_requirement_type.json')

        self.kwargs.update({
            'label': 'KeyValuesWithFeatures',
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} -y')
        with open(imported_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # skip features while exporting
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --skip-features -y')
        with open(skipped_features_file_path) as json_file:
            only_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert only_kvs == exported_kvs

        # skip features while importing
        self.kwargs.update({
            'label': 'SkipFeatures'
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} --skip-features -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} -y')
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert only_kvs == exported_kvs

        # Prefix addition test
        self.kwargs.update({
            'label': 'PrefixTest',
            'prefix': 'Test'
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} --prefix {prefix} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} -y')
        with open(prefix_added_features_file_path) as json_file:
            prefix_added_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert prefix_added_kvs == exported_kvs

        # Prefix trimming test
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --prefix {prefix} -y')
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # Key filtering test
        self.kwargs.update({
            'label': 'KeyValuesWithFeatures',
            'key': 'Col*'
        })
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --key {key} -y')
        with open(key_filtered_features_file_path) as json_file:
            key_filtered_features = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert key_filtered_features == exported_kvs

        # Separator test
        self.kwargs.update({
            'label': 'SeparatorTest',
            'separator': ':',
            'imported_file_path': import_separator_features_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} --separator {separator} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --separator {separator} -y')
        with open(export_separator_features_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # Support alternative syntax for always ON/OFF features
        self.kwargs.update({
            'label': 'AltSyntaxTest',
            'imported_file_path': import_features_alt_syntax_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} --separator {separator} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --separator {separator} -y')
        with open(imported_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # Support including all properties in the feature flag conditions
        self.kwargs.update({
            'imported_file_path': import_features_random_conditions_file_path,
            'label': 'RandomConditionsTest',
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} -y')
        with open(import_features_random_conditions_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs
        os.remove(exported_file_path)

        self.kwargs.update({
            'imported_file_path': import_features_invalid_requirement_type_file_path
        })

        # Invalid requirement type should fail import
        with self.assertRaisesRegex(CLIError, "Feature 'Timestamp' must have an any/all requirement type"):
            self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_kvset(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='KVSetImportTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # File <--> AppConfig tests

        imported_file_path = os.path.join(TEST_DIR, 'kvset_import.json')
        exported_file_path = os.path.join(TEST_DIR, 'kvset_export.json')

        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'profile': ImportExportProfiles.KVSET,
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --profile {profile} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --label * --key * --path "{exported_file_path}" --format {imported_format} --profile {profile} -y')
        with open(imported_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs

        # export kvset with --skip-features option
        no_features_file_path = os.path.join(TEST_DIR, 'kvset_no_features.json')

        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --profile {profile} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --label * --key * --path "{exported_file_path}" --format {imported_format} --profile {profile} --skip-features -y')

        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        with open(no_features_file_path) as json_file:
            expected_kvs = json.load(json_file)
        assert exported_kvs == expected_kvs
        os.remove(exported_file_path)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_strict_import(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='StrictImportTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # File <--> AppConfig tests
        imported_file_path = os.path.join(TEST_DIR, 'kvset_import.json')
        exported_file_path = os.path.join(TEST_DIR, 'kvset_export.json')
        strict_import_file_path = os.path.join(TEST_DIR, 'strict_import.json')

        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'profile': ImportExportProfiles.KVSET,
            'imported_file_path': imported_file_path,
            'exported_file_path': exported_file_path,
            'strict_import_file_path': strict_import_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --profile {profile} -y')
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{strict_import_file_path}" --format {imported_format} --profile {profile} --strict -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --label * --key * --path "{exported_file_path}" --format {imported_format} --profile {profile} -y')
        with open(strict_import_file_path) as json_file:
            expected_kvs = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert expected_kvs == exported_kvs
        os.remove(exported_file_path)


class AppConfigAppServiceImportExportLiveScenarioTest(LiveScenarioTest):

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_appconfig_to_appservice_import_export(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='ImportExportTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # Get connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })

        # Create AppService plan and webapp
        webapp_name = self.create_random_name(prefix='WebApp', length=24)
        plan = self.create_random_name(prefix='Plan', length=24)
        # Require a standard sku to allow for deployment slots
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} -p {}'.format(resource_group, webapp_name, plan))

        # Create deployment slot
        slot = self.create_random_name(prefix='Slot', length=24)
        self.cmd('webapp deployment slot create -g {} -n {} -s {}'.format(resource_group, webapp_name, slot))

        # App configuration reference tests
        # Create new key-values
        entry_key = 'TestKey'
        entry_value = 'TestValue'
        entry_label = 'AppServiceReferenceExport'
        expected_reference = '{}(Endpoint=https://{}.azconfig.io; Key={}; Label={})'.format(
            AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX,
            config_store_name.lower(),
            entry_key,
            entry_label)

        entry_key2 = 'TestKey2'
        entry_value2 = 'TestValue2'
        expected_reference2 = '{}(Endpoint=https://{}.azconfig.io; Key={})'.format(
            AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX,
            config_store_name.lower(),
            entry_key2)

        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'label': entry_label
        })

        # Add a new key-value entry
        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', entry_label)])

        self.kwargs.update({
            'key': entry_key2,
            'value': entry_value2,
        })

        # Add second key-value entry (No label)
        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y',
                 checks=[self.check('key', entry_key2),
                         self.check('value', entry_value2)])

        # Export app configuration reference to App Service
        self.kwargs.update({
            'export_dest': 'appservice',
            'appservice_account': webapp_name
        })

         # Export snapshot kvs to app service as reference should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'Cannot export snapshot key-values as references to App Service.'):
            self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {appservice_account} -y --export-as-reference --snapshot dummy_snapshot')

        self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {appservice_account} --label {label} -y --export-as-reference')
        self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {appservice_account} -y --export-as-reference')

        # Assert first reference is in the right format
        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account}').get_output_in_json()
        exported_keys = next(x for x in app_settings if x['name'] == entry_key)
        self.assertEquals(exported_keys['name'], entry_key)
        self.assertEquals(exported_keys['value'], expected_reference)
        self.assertEquals(exported_keys['slotSetting'], False)

        # Assert second reference is of right format    
        exported_keys = next(x for x in app_settings if x['name'] == entry_key2)
        self.assertEquals(exported_keys['name'], entry_key2)
        self.assertEquals(exported_keys['value'], expected_reference2)
        self.assertEquals(exported_keys['slotSetting'], False)


        # Test to confirm the right app configuration reference
        # Verify that app configuration references are ignored during import
        ref_entry_key = entry_key
        entry_key = 'TestKey3'
        entry_value = 'TestValue3'
        import_label = 'AppServiceImport'

        self.kwargs.update({
            'key': entry_key,
            'value': entry_value
        })

        # Create new key-value in AppService
        self.cmd('webapp config appsettings set -g {rg} -n {appservice_account} --settings {key}={value}')

        # Verify that both the app configuration reference and key-value exist in app service
        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account}').get_output_in_json()
        app_setting_names = [setting["name"] for setting in app_settings]
        assert ref_entry_key in app_setting_names
        assert entry_key in app_setting_names

        # Import settings to app configuration
        self.kwargs.update({
            'label': import_label
        })
        self.cmd('appconfig kv import --connection-string {connection_string} -s {export_dest} --appservice-account {appservice_account} --label {label} -y')

        # Verfiy that app configuration reference does not exist in imported keys
        imported_config =  self.cmd('appconfig kv list --connection-string {connection_string} --label {label}').get_output_in_json()
        assert not any(setting['value'].lower().startswith(AppServiceConstants.APPSVC_CONFIG_REFERENCE_PREFIX.lower()) for setting in imported_config)


        # KeyVault reference tests
        keyvault_key = "HostSecrets"
        keyvault_id = "https://fake.vault.azure.net/secrets/fakesecret"
        appconfig_keyvault_value = "{{\"uri\":\"https://fake.vault.azure.net/secrets/fakesecret\"}}"
        appsvc_keyvault_value = "@Microsoft.KeyVault(SecretUri=https://fake.vault.azure.net/secrets/fakesecret)"
        label = 'ForExportToAppService'
        self.kwargs.update({
            'key': keyvault_key,
            'label': label,
            'secret_identifier': keyvault_id
        })

        # Add new KeyVault ref in AppConfig
        self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --secret-identifier {secret_identifier} --label {label} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', keyvault_key),
                         self.check('label', label),
                         self.check('value', appconfig_keyvault_value)])

        self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {appservice_account} --label {label} -y')

        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account}').get_output_in_json()
        exported_keys = next(x for x in app_settings if x['name'] == keyvault_key)
        self.assertEqual(exported_keys['name'], keyvault_key)
        self.assertEqual(exported_keys['value'], appsvc_keyvault_value)
        self.assertEqual(exported_keys['slotSetting'], False)

        self.kwargs.update({
            'slot': slot
        })

        # Verify that the slot configuration was not updated
        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account} -s {slot}').get_output_in_json()
        assert not any(True for elem in app_settings if elem['name'] == keyvault_key)

        # Import KeyVault ref from AppService
        updated_label = 'ImportedFromAppService'
        self.kwargs.update({
            'label': updated_label
        })
        self.cmd('appconfig kv import --connection-string {connection_string} -s {export_dest} --appservice-account {appservice_account} --label {label} -y')

        self.cmd('appconfig kv list --connection-string {connection_string} --label {label}',
                 checks=[self.check('[0].contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('[0].key', keyvault_key),
                         self.check('[0].value', appconfig_keyvault_value),
                         self.check('[0].label', updated_label)])

        # Get the slot ID
        slot_list = self.cmd('az webapp deployment slot list -g {rg} -n {appservice_account}').get_output_in_json()
        assert slot_list and len(slot_list) == 1
        slot_id = slot_list[0]['id']

        # Update keyvault reference for slot export / import testing
        slot_keyvault_id = "https://fake.vault.azure.net/secrets/slotsecret"
        appconfigslot_keyvault_value = "{{\"uri\":\"https://fake.vault.azure.net/secrets/slotsecret\"}}"
        appsvcslot_keyvault_value = "@Microsoft.KeyVault(SecretUri=https://fake.vault.azure.net/secrets/slotsecret)"
        label = 'ForExportToAppServiceSlot'
        self.kwargs.update({
            'label': label,
            'secret_identifier': slot_keyvault_id,
            'slot_id': slot_id
        })

        # Add new KeyVault ref in AppConfig for the slot
        self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --secret-identifier {secret_identifier} --label {label} -y',
                 checks=[self.check('contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('key', keyvault_key),
                         self.check('label', label),
                         self.check('value', appconfigslot_keyvault_value)])

        # Export KeyVault ref to AppService
        self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {slot_id} --label {label} -y')

        # Verify that the webapp configuration was not updated
        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account}').get_output_in_json()
        exported_keys = next(x for x in app_settings if x['name'] == keyvault_key)
        self.assertEqual(exported_keys['name'], keyvault_key)
        self.assertEqual(exported_keys['value'], appsvc_keyvault_value)
        self.assertEqual(exported_keys['slotSetting'], False)

        # Verify that the slot configuration was updated
        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account} -s {slot}').get_output_in_json()
        exported_keys = next(x for x in app_settings if x['name'] == keyvault_key)
        self.assertEqual(exported_keys['name'], keyvault_key)
        self.assertEqual(exported_keys['value'], appsvcslot_keyvault_value)
        self.assertEqual(exported_keys['slotSetting'], False)

        # Import KeyVault ref from AppService slot
        updated_label = 'ImportedFromAppServiceSlot'
        self.kwargs.update({
            'label': updated_label
        })
        self.cmd('appconfig kv import --connection-string {connection_string} -s {export_dest} --appservice-account {slot_id} --label {label} -y')

        self.cmd('appconfig kv list --connection-string {connection_string} --label {label}',
                 checks=[self.check('[0].contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('[0].key', keyvault_key),
                         self.check('[0].value', appconfigslot_keyvault_value),
                         self.check('[0].label', updated_label)])

        # Add keyvault ref to appservice in alt format and import to appconfig
        alt_label = 'ImportedAltSyntaxFromAppService'
        alt_keyvault_key = "AltKeyVault"
        alt_keyvault_value = "@Microsoft.KeyVault(VaultName=myvault;SecretName=mysecret;SecretVersion=ec96f02080254f109c51a1f14cdb1931)"
        appconfig_keyvault_value = "{{\"uri\":\"https://myvault.vault.azure.net/secrets/mysecret/ec96f02080254f109c51a1f14cdb1931\"}}"
        keyvault_ref = "{0}={1}".format(alt_keyvault_key, alt_keyvault_value)
        slotsetting_tag = {"AppService:SlotSetting": "true"}
        self.kwargs.update({
            'label': alt_label,
            'settings': keyvault_ref
        })
        self.cmd('webapp config appsettings set -g {rg} -n {appservice_account} --slot-settings {settings}')
        self.cmd('appconfig kv import --connection-string {connection_string} -s {export_dest} --appservice-account {appservice_account} --label {label} -y')
        self.cmd('appconfig kv list --connection-string {connection_string} --label {label}',
                 checks=[self.check('[0].contentType', KeyVaultConstants.KEYVAULT_CONTENT_TYPE),
                         self.check('[0].key', alt_keyvault_key),
                         self.check('[0].value', appconfig_keyvault_value),
                         self.check('[0].tags', slotsetting_tag),
                         self.check('[0].label', alt_label)])


class AppConfigImportExportNamingConventionScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_naming_conventions(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='NamingConventionTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        import_hyphen_path = os.path.join(TEST_DIR, 'import_features_hyphen.json')
        exported_file_path = os.path.join(TEST_DIR, 'export_features_naming.json')
        export_underscore_path = os.path.join(TEST_DIR, 'export_features_underscore.json')
        import_multiple_feature_sections_path = os.path.join(TEST_DIR, 'import_multiple_feature_sections.json')
        import_wrong_enabledfor_format_path = os.path.join(TEST_DIR, 'import_wrong_enabledfor_format.json')

        self.kwargs.update({
            'import_source': 'file',
            'imported_format': 'json',
            'label': 'NamingConventionTest',
            'naming_convention': 'underscore',
            'imported_file_path': import_hyphen_path,
            'exported_file_path': exported_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --naming-convention {naming_convention} -y')
        with open(export_underscore_path) as json_file:
            export_underscore_path = json.load(json_file)
        with open(exported_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert export_underscore_path == exported_kvs
        os.remove(exported_file_path)

        # Error if imported file has multiple feature sections
        self.kwargs.update({
            'imported_file_path': import_multiple_feature_sections_path
        })
        with self.assertRaisesRegex(CLIError, 'Unable to proceed because file contains multiple sections corresponding to "Feature Management".'):
            self.cmd('appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')

        # Error if imported file has "enabled for" in wrong format
        self.kwargs.update({
            'imported_file_path': import_wrong_enabledfor_format_path
        })
        with self.assertRaisesRegex(CLIError, 'definition or have a true/false value.'):
            self.cmd('appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')

        # Import/Export yaml file
        imported_yaml_file_path = os.path.join(TEST_DIR, 'import_features_yaml.json')
        exported_yaml_file_path = os.path.join(TEST_DIR, 'export_features_yaml.json')
        exported_hyphen_yaml_file_path = os.path.join(TEST_DIR, 'export_features_hyphen_yaml.json')

        self.kwargs.update({
            'label': 'YamlTests',
            'imported_format': 'yaml',
            'naming_convention': 'hyphen',
            'imported_file_path': imported_yaml_file_path,
            'exported_file_path': exported_yaml_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --naming-convention {naming_convention} -y')
        exported_yaml_file = {}
        exported_hyphen_yaml_file = {}
        with open(exported_yaml_file_path) as yaml_file:
            for yaml_data in list(yaml.safe_load_all(yaml_file)):
                exported_yaml_file.update(yaml_data)
        with open(exported_hyphen_yaml_file_path) as yaml_file:
            for yaml_data in list(yaml.safe_load_all(yaml_file)):
                exported_hyphen_yaml_file.update(yaml_data)
        assert exported_yaml_file == exported_hyphen_yaml_file
        os.remove(exported_yaml_file_path)

        # Import/Export properties file
        imported_prop_file_path = os.path.join(TEST_DIR, 'import_features_prop.json')
        exported_prop_file_path = os.path.join(TEST_DIR, 'export_features_prop.json')
        exported_as_kv_prop_file_path = os.path.join(TEST_DIR, 'export_as_kv_prop.json')

        self.kwargs.update({
            'label': 'PropertiesTests',
            'imported_format': 'properties',
            'imported_file_path': imported_prop_file_path,
            'exported_file_path': exported_prop_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} -y')
        with open(exported_prop_file_path) as prop_file:
            exported_prop_file = javaproperties.load(prop_file)
        with open(exported_as_kv_prop_file_path) as prop_file:
            exported_kv_prop_file = javaproperties.load(prop_file)
        assert exported_prop_file == exported_kv_prop_file
        os.remove(exported_prop_file_path)


class AppConfigToAppConfigImportExportScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_appconfig_to_appconfig_import_export(self, resource_group, location):
        src_config_store_name = self.create_random_name(prefix='Source', length=24)
        dest_config_store_name = self.create_random_name(prefix='Destination', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': src_config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # Get src connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'src_connection_string': credential_list[0]['connectionString'],
            'config_store_name': dest_config_store_name
        })
        _create_config_store(self, self.kwargs)

        # Get dest connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'dest_connection_string': credential_list[0]['connectionString']
        })

        # Add duplicate keys with different labels in src config store
        entry_key = "Color"
        entry_value = "Red"
        entry_label = 'v1'
        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'label': entry_label
        })
        # add a new key-value entry
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', entry_label)])
        # add a new label for same key
        updated_value = "Blue"
        updated_label = 'v2'
        self.kwargs.update({
            'value': updated_value,
            'label': updated_label
        })
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', updated_value),
                         self.check('label', updated_label)])

        # Add duplicate features with different labels in src config store
        entry_feature = 'Beta'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + entry_feature
        self.kwargs.update({
            'feature': entry_feature,
            'label': entry_label
        })
        # add a new feature flag entry
        self.cmd('appconfig feature set --connection-string {src_connection_string} --feature {feature} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('label', entry_label)])

        # add a new label for same feature
        self.kwargs.update({
            'label': updated_label
        })
        self.cmd('appconfig feature set --connection-string {src_connection_string} --feature {feature} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('label', updated_label)])

        # import all kv and features from src config store to dest config store
        any_key_pattern = '*'
        any_label_pattern = '*'
        null_label = None
        dest_label = 'DestLabel'
        self.kwargs.update({
            'import_source': 'appconfig',
            'label': dest_label,
            'src_label': any_label_pattern
        })

        # Importing with a new label should only import one KV and one feature as src labels will be overwritten in dest
        self.cmd(
            'appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --src-label {src_label} --label {label} -y')

        # Check kv and features that were imported to dest config store
        # We can check by deleting since its better to clear dest config store for next import test
        self.kwargs.update({
            'key': any_key_pattern,
            'label': any_label_pattern
        })
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', dest_label),
                                       self.check('[1].key', entry_key),
                                       self.check('[1].value', updated_value),
                                       self.check('[1].label', dest_label)]).get_output_in_json()
        assert len(deleted_kvs) == 2

        # Not specifying a label or preserve-labels should assign null label and import only one KV and one feature
        self.cmd(
            'appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --src-label {src_label} -y')
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', null_label),
                                       self.check('[1].key', entry_key),
                                       self.check('[1].value', updated_value),
                                       self.check('[1].label', null_label)]).get_output_in_json()
        assert len(deleted_kvs) == 2

        # Preserving labels and importing all kv and all features
        self.cmd(
            'appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --src-label {src_label} --preserve-labels -y')
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', entry_label),
                                       self.check('[1].key', internal_feature_key),
                                       self.check('[1].label', updated_label),
                                       self.check('[2].key', entry_key),
                                       self.check('[2].value', entry_value),
                                       self.check('[2].label', entry_label),
                                       self.check('[3].key', entry_key),
                                       self.check('[3].value', updated_value),
                                       self.check('[3].label', updated_label)]).get_output_in_json()
        assert len(deleted_kvs) == 4

        # Error when both label and preserve-labels is specified
        self.kwargs.update({
            'label': dest_label
        })
        with self.assertRaisesRegex(CLIError, "Import failed! Please provide only one of these arguments: '--label' or '--preserve-labels'."):
            self.cmd('appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --src-label {src_label} --label {label} --preserve-labels -y')

        # Export tests from src config store to dest config store
        # Exporting with a new label should only export one KV and one feature as src labels will be overwritten in dest
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --label {src_label} --dest-label {label} -y')
        # Check kv and features that were exported to dest config store
        # We can check by deleting since its better to clear dest config store for next export test
        self.kwargs.update({
            'label': any_label_pattern
        })
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', dest_label),
                                       self.check('[1].key', entry_key),
                                       self.check('[1].value', updated_value),
                                       self.check('[1].label', dest_label)]).get_output_in_json()
        assert len(deleted_kvs) == 2

        # Not specifying a label or preserve-labels should assign null label and export only one KV and one feature
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --label {src_label} -y')
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', null_label),
                                       self.check('[1].key', entry_key),
                                       self.check('[1].value', updated_value),
                                       self.check('[1].label', null_label)]).get_output_in_json()
        assert len(deleted_kvs) == 2

        # Preserving labels and exporting all kv and all features
        self.cmd(
            'appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --label {src_label} --preserve-labels -y')
        deleted_kvs = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --label {label} -y',
                               checks=[self.check('[0].key', internal_feature_key),
                                       self.check('[0].label', entry_label),
                                       self.check('[1].key', internal_feature_key),
                                       self.check('[1].label', updated_label),
                                       self.check('[2].key', entry_key),
                                       self.check('[2].value', entry_value),
                                       self.check('[2].label', entry_label),
                                       self.check('[3].key', entry_key),
                                       self.check('[3].value', updated_value),
                                       self.check('[3].label', updated_label)]).get_output_in_json()
        assert len(deleted_kvs) == 4

        # Error when both dest-label and preserve-labels is specified
        self.kwargs.update({
            'label': dest_label
        })
        with self.assertRaisesRegex(CLIError, "Export failed! Please provide only one of these arguments: '--dest-label' or '--preserve-labels'."):
            self.cmd('appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --label {src_label} --dest-label {label} --preserve-labels -y')


class AppConfigJsonContentTypeScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_json_content_type(self, resource_group, location):
        src_config_store_name = self.create_random_name(prefix='Source', length=24)
        dest_config_store_name = self.create_random_name(prefix='Destination', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': src_config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        # Get src connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'src_connection_string': credential_list[0]['connectionString'],
            'config_store_name': dest_config_store_name
        })
        _create_config_store(self, self.kwargs)

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
        default_conditions = "{{u\'client_filters\': []}}" if sys.version_info[0] < 3 else "{{\'client_filters\': []}}"
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
        keyvault_value = "{{\"uri\":\"https://fake.vault.azure.net/secrets/fakesecret\"}}"
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


class AppConfigFeatureScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_feature(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='FeatureTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        entry_feature = 'Beta'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + entry_feature
        entry_label = 'v1'
        default_description = ""
        default_conditions = "{{u\'client_filters\': []}}" if sys.version_info[0] < 3 else "{{\'client_filters\': []}}"
        default_locked = False
        default_state = "off"

        self.kwargs.update({
            'feature': entry_feature,
            'description': default_description,
            'label': entry_label
        })

        # add a brand new feature flag entry
        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # update an existing feature flag entry
        updated_entry_description = "Beta Testing Feature Flag"
        updated_requirement_type =  FeatureFlagConstants.REQUIREMENT_TYPE_ANY

        self.kwargs.update({
            'description': updated_entry_description,
            'requirement_type': updated_requirement_type
        })
        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} --description "{description}" --requirement-type {requirement_type} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', updated_entry_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions.client_filters', []),
                         self.check('conditions.requirement_type', updated_requirement_type)])

        # add a new label - this should create a new KV in the config store
        updated_label = 'v2'
        self.kwargs.update({
            'label': updated_label
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', updated_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # set feature flag with connection string - updates the description of existing feature
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })
        self.cmd('appconfig feature set --connection-string {connection_string} --feature {feature} --label {label} --description "{description}" -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', updated_entry_description),
                         self.check('label', updated_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # show a feature flag with all 8 fields
        response_dict = self.cmd('appconfig feature show -n {config_store_name} --feature {feature} --label {label}',
                                 checks=[self.check('locked', default_locked),
                                         self.check('name', entry_feature),
                                         self.check('key', internal_feature_key),
                                         self.check('description', updated_entry_description),
                                         self.check('label', updated_label),
                                         self.check('state', default_state),
                                         self.check('conditions', default_conditions)]).get_output_in_json()
        assert len(response_dict) == 8

        # show a feature flag with field filtering
        response_dict = self.cmd('appconfig feature show -n {config_store_name} --feature {feature} --label {label} --fields key label state locked',
                                 checks=[self.check('locked', default_locked),
                                         self.check('key', internal_feature_key),
                                         self.check('label', updated_label),
                                         self.check('state', default_state)]).get_output_in_json()
        assert len(response_dict) == 4

        # List all features with null labels
        null_label_pattern = "\\0"
        self.kwargs.update({
            'label': null_label_pattern
        })

        self.cmd('appconfig feature list -n {config_store_name} --label "{label}"',
                 checks=NoneCheck())

        # List all features with any label with field filtering
        any_label_pattern = '*'
        self.kwargs.update({
            'label': any_label_pattern
        })

        list_features = self.cmd('appconfig feature list -n {config_store_name} --label {label} --fields key name label state locked',
                                 checks=[self.check('[0].locked', default_locked),
                                         self.check('[0].name', entry_feature),
                                         self.check('[0].key', internal_feature_key),
                                         self.check('[0].label', entry_label),
                                         self.check('[0].state', default_state)]).get_output_in_json()
        assert len(list_features) == 2

        #  List all features with any label
        list_features = self.cmd('appconfig feature list -n {config_store_name}').get_output_in_json()
        assert len(list_features) == 2

        # Add another feature with name starting with Beta, null label
        prefix_feature = 'BetaPrefix'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + prefix_feature
        null_label = None

        self.kwargs.update({
            'feature': prefix_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', prefix_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Add feature with name ending with Beta, null label
        suffix_feature = 'SuffixBeta'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + suffix_feature

        self.kwargs.update({
            'feature': suffix_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', suffix_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Add feature where name contains Beta, null label
        contains_feature = 'ThisBetaVersion'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + contains_feature

        self.kwargs.update({
            'feature': contains_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', contains_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # List any feature with any label
        any_feature_pattern = '*'
        self.kwargs.update({
            'feature': any_feature_pattern
        })

        list_features = self.cmd('appconfig feature list -n {config_store_name} --feature {feature} --label {label}').get_output_in_json()
        assert len(list_features) == 5

        # List all features starting with Beta, any label
        prefix_feature_pattern = 'Beta*'
        self.kwargs.update({
            'feature': prefix_feature_pattern
        })

        list_features = self.cmd('appconfig feature list -n {config_store_name} --feature {feature} --label {label}').get_output_in_json()
        assert len(list_features) == 3

        # List all features starting with Beta, null label
        self.kwargs.update({
            'label': null_label_pattern
        })

        list_features = self.cmd('appconfig feature list -n {config_store_name} --feature {feature} --label "{label}"',
                                 checks=[self.check('[0].name', prefix_feature),
                                         self.check('[0].label', null_label)]).get_output_in_json()
        assert len(list_features) == 1

        # Invalid Pattern - contains comma
        comma_pattern = 'Beta,Alpha'
        self.kwargs.update({
            'feature': comma_pattern
        })

        with self.assertRaisesRegex(CLIError, "Comma separated feature names are not supported"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Invalid Pattern - contains invalid *
        invalid_pattern = 'Beta*ion'
        self.kwargs.update({
            'feature': invalid_pattern
        })

        with self.assertRaisesRegex(CLIError, "Bad Request"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Invalid Pattern - starts with *
        invalid_pattern = '*Beta'
        self.kwargs.update({
            'feature': invalid_pattern
        })

        with self.assertRaisesRegex(CLIError, "Bad Request"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Invalid Pattern - contains multiple **
        invalid_pattern = 'Beta**'
        self.kwargs.update({
            'feature': invalid_pattern
        })

        with self.assertRaisesRegex(CLIError, "Bad Request"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Delete Beta (label v2) feature flag using connection-string
        self.kwargs.update({
            'feature': entry_feature,
            'label': updated_label
        })

        # IN CLI, since we support delete by key/label pattern matching, return is a list of deleted items
        deleted = self.cmd('appconfig feature delete --connection-string {connection_string}  --feature {feature} --label {label} -y',
                           checks=[self.check('[0].locked', default_locked),
                                   self.check('[0].name', entry_feature),
                                   self.check('[0].description', updated_entry_description),
                                   self.check('[0].label', updated_label),
                                   self.check('[0].state', default_state)]).get_output_in_json()
        assert len(deleted) == 1

        # Lock feature - ThisBetaVersion
        self.kwargs.update({
            'feature': contains_feature
        })
        updated_lock = True

        self.cmd('appconfig feature lock -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', updated_lock),
                         self.check('name', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state)])

        # Unlock feature - ThisBetaVersion
        self.cmd('appconfig feature unlock -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state)])

        # Enable feature - ThisBetaVersion
        on_state = 'on'
        self.cmd('appconfig feature enable -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', on_state)])

        # Disable feature - ThisBetaVersion
        self.cmd('appconfig feature disable -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state)])

        # List any feature with any label
        self.kwargs.update({
            'feature': any_feature_pattern,
            'label': any_label_pattern
        })

        list_features = self.cmd('appconfig feature list -n {config_store_name} --feature {feature} --label {label}').get_output_in_json()
        assert len(list_features) == 4

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_feature_namespacing(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='FeatureNamespaceTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        feature_name = 'Beta'
        feature_prefix = 'MyApp:'
        feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature_prefix + feature_name
        entry_label = 'v1'
        default_description = ""
        default_conditions = "{{u\'client_filters\': []}}" if sys.version_info[0] < 3 else "{{\'client_filters\': []}}"
        default_locked = False
        default_state = "off"

        self.kwargs.update({
            'feature': feature_name,
            'key': feature_key,
            'description': default_description,
            'label': entry_label
        })

        # add feature flag with a custom key
        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --key {key}  --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', feature_name),
                         self.check('key', feature_key),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Enable the same feature flag using --key
        on_state = 'on'
        self.cmd('appconfig feature enable -n {config_store_name} --key {key} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', feature_name),
                         self.check('key', feature_key),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', on_state)])

        feature_name_2 = "GlobalFeature"
        feature_key_2 = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature_prefix + feature_name_2
        self.kwargs.update({
            'key': feature_key_2,
            'feature': feature_name_2
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --key {key}  --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', feature_name_2),
                         self.check('key', feature_key_2),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # List features using --key filter
        key_pattern = FeatureFlagConstants.FEATURE_FLAG_PREFIX + feature_prefix + "*"
        any_label_pattern = "*"
        self.kwargs.update({
            'key': key_pattern,
            'label': any_label_pattern
        })
        list_features = self.cmd('appconfig feature list -n {config_store_name} --key {key} --label {label}').get_output_in_json()
        assert len(list_features) == 2

        # Invalid key
        invalid_key = "InvalidFeatureKey"
        self.kwargs.update({
            'key': invalid_key
        })

        with self.assertRaisesRegex(CLIError, "Feature flag key must start with the reserved prefix"):
            self.cmd('appconfig feature set -n {config_store_name} --key {key}')

        # Missing key and feature
        with self.assertRaisesRegex(CLIError, "Please provide either `--key` or `--feature` value."):
            self.cmd('appconfig feature delete -n {config_store_name}')

        # Invalid feature name
        invalid_feature_name = "invalid:feature"
        self.kwargs.update({
            'feature': invalid_feature_name
        })

        with self.assertRaisesRegex(CLIError, "Feature name cannot contain the following characters: '%', ':'"):
            self.cmd('appconfig feature set -n {config_store_name} --feature {feature}')

  
class AppConfigFeatureFilterScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_feature_filter(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='FeatureFilterTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

        entry_feature = 'Color'
        internal_feature_key = FeatureFlagConstants.FEATURE_FLAG_PREFIX + entry_feature
        entry_label = 'Standard'
        default_description = ""
        default_conditions = "{{u\'client_filters\': []}}" if sys.version_info[0] < 3 else "{{\'client_filters\': []}}"
        default_locked = False
        default_state = "off"

        self.kwargs.update({
            'feature': entry_feature,
            'description': default_description,
            'label': entry_label
        })

        # add a brand new feature flag entry
        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        first_filter_name = 'FirstFilter'
        first_filter_params = 'Name1=[\\"Value1\\",\\"Value1.1\\"] Name2=\\"Value2\\" Name3 Name4={\\"key\\":\\"value\\"}'
        first_filter_params_output = {
            "Name1": [
                "Value1",
                "Value1.1"
            ],
            "Name2": "Value2",
            "Name3": "",
            "Name4": {
                "key": "value"
            }
        }

        # Add filters
        self.kwargs.update({
            'filter_name': first_filter_name,
            'filter_parameters': first_filter_params
        })

        self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y',
                 checks=[self.check('name', first_filter_name),
                         self.check('parameters', first_filter_params_output)])

        # Add another unique filter
        second_filter_name = 'SecondFilter'
        second_filter_params = 'Foo=\\"Bar=value\\" name=\\"Foo=Bar\\" {\\"Value\\":\\"50\\",\\"SecondValue\\":\\"75\\"}=\\"ParamNameIsJsonString\\"'
        second_filter_params_output = {
            "Foo": "Bar=value",
            "name": "Foo=Bar",
            "{\"Value\":\"50\",\"SecondValue\":\"75\"}": "ParamNameIsJsonString"
        }

        self.kwargs.update({
            'filter_name': second_filter_name,
            'filter_parameters': second_filter_params
        })

        self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y',
                 checks=[self.check('name', second_filter_name),
                         self.check('parameters', second_filter_params_output)])

        # Add duplicate of FirstFilter without any params
        self.kwargs.update({
            'filter_name': first_filter_name,
            'filter_parameters': ''
        })

        self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y',
                 checks=[self.check('name', first_filter_name),
                         self.check('parameters', {})])

        # Show FirstFilter without index will return both instances of this filter
        filters = self.cmd('appconfig feature filter show -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name}').get_output_in_json()
        assert len(filters) == 2

        # Show FirstFilter with index will return only one instance of this filter at the specified index
        self.cmd('appconfig feature filter show -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --index 2',
                 checks=[self.check('name', first_filter_name),
                         self.check('parameters', {})])

        # List Filters
        list_filters = self.cmd('appconfig feature filter list -n {config_store_name} --feature {feature} --label {label}').get_output_in_json()
        assert len(list_filters) == 3

        # Show feature with all filters
        response_dict = self.cmd('appconfig feature show -n {config_store_name} --feature {feature} --label {label}',
                                 checks=[self.check('locked', default_locked),
                                         self.check('name', entry_feature),
                                         self.check('key', internal_feature_key),
                                         self.check('description', default_description),
                                         self.check('label', entry_label),
                                         self.check('state', default_state)]).get_output_in_json()

        conditions = response_dict.get(FeatureFlagConstants.CONDITIONS)
        list_filters = conditions.get(FeatureFlagConstants.CLIENT_FILTERS)
        assert len(list_filters) == 3

        # Enable feature
        conditional_state = 'conditional'
        self.cmd('appconfig feature enable -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('name', entry_feature),
                         self.check('key', internal_feature_key),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', conditional_state)])

        # Update Filter Tests
        updated_params = 'ArrayParams=[10,20,30]'
        updated_params_output = {
            "ArrayParams": [
                10,
                20,
                30
            ]
        }

        # Update Filter should fail when filter_name does not exist
        non_existent_filter_name = "non_existent_filter"

        self.kwargs.update({
            'filter_parameters': updated_params,
            'filter_name': non_existent_filter_name
        })
        with self.assertRaisesRegex(CLIError, "No filter named '{}' was found for feature".format(non_existent_filter_name)):
            self.cmd(
                'appconfig feature filter update -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} -y --filter-parameters {filter_parameters}')

        # Update Filter without index should throw error when duplicates exist
        self.kwargs.update({
            'filter_name': first_filter_name
        })

        with self.assertRaisesRegex(CLIError, "contains multiple instances of filter"):
            self.cmd(
                'appconfig feature filter update -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} -y --filter-parameters {filter_parameters}')

        # Update Filter with index succeeds when correct index provided
        self.cmd('appconfig feature filter update -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --index 0 -y --filter-parameters {filter_parameters}',
                 checks=[self.check('name', first_filter_name),
                         self.check('parameters', updated_params_output)])


        # Delete Filter without index should throw error when duplicates exist
        with self.assertRaisesRegex(CLIError, "contains multiple instances of filter"):
            self.cmd('appconfig feature filter delete -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} -y')

        # Delete Filter with index succeeds when correct index is provided
        self.cmd('appconfig feature filter delete -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --index 2 -y',
                 checks=[self.check('name', first_filter_name),
                         self.check('parameters', {})])

        # Delete all Filters
        cleared_filters = self.cmd('appconfig feature filter delete -n {config_store_name} --feature {feature} --label {label} --all -y').get_output_in_json()
        assert len(cleared_filters) == 2

        # Delete Filters when no filters present
        self.cmd('appconfig feature filter delete -n {config_store_name} --feature {feature} --label {label} --all -y',
                 checks=NoneCheck())

        # List Filters when no filters present
        self.cmd('appconfig feature filter list -n {config_store_name} --feature {feature} --label {label}',
                 checks=NoneCheck())

        # Error on adding filter parameters with invalid JSON escaped string
        invalid_filter_name = 'InvalidFilter'
        invalid_filter_params = 'Name1=Value1'
        self.kwargs.update({
            'filter_name': invalid_filter_name,
            'filter_parameters': invalid_filter_params
        })
        with self.assertRaisesRegex(CLIError, "Filter parameter value must be a JSON escaped string"):
            self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y')

        # Error on adding duplicate filter parameters
        invalid_filter_params = 'Name1=10 Name1=20'
        self.kwargs.update({
            'filter_parameters': invalid_filter_params
        })
        with self.assertRaisesRegex(CLIError, 'Filter parameter name "Name1" cannot be duplicated.'):
            self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y')

        # Error on filter parameter with empty name
        invalid_filter_params = '=value'
        self.kwargs.update({
            'filter_parameters': invalid_filter_params
        })
        with self.assertRaisesRegex(CLIError, 'Parameter name cannot be empty.'):
            self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y')

        # Test more inputs for filter param value
        filter_name = 'NewFilter'
        filter_params = 'ArrayParam=[1,2,\\"three\\"] BoolParam=true NullParam=null'
        filter_params_output = {
            "ArrayParam": [
                1,
                2,
                "three"
            ],
            # This is the output in python object format - our backend stores the bool and null values in correct JSON format
            "BoolParam": True,
            "NullParam": None
        }

        self.kwargs.update({
            'filter_name': filter_name,
            'filter_parameters': filter_params
        })

        self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y',
                 checks=[self.check('name', filter_name),
                         self.check('parameters', filter_params_output)])

        # Different ways to set empty string as filter param value
        filter_params = 'EmptyStr1 EmptyStr2= EmptyStr3="" EmptyStr4=\\"\\"'
        filter_params_output = {
            "EmptyStr1": "",
            "EmptyStr2": "",
            "EmptyStr3": "",
            "EmptyStr4": ""
        }

        self.kwargs.update({
            'filter_name': filter_name,
            'filter_parameters': filter_params
        })

        self.cmd('appconfig feature filter add -n {config_store_name} --feature {feature} --label {label} --filter-name {filter_name} --filter-parameters {filter_parameters} -y',
                 checks=[self.check('name', filter_name),
                         self.check('parameters', filter_params_output)])


class AppConfigKeyValidationScenarioTest(ScenarioTest):

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_key_validation(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='KVTest', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

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


class AppConfigAadAuthLiveScenarioTest(ScenarioTest):

    @live_only()
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_aad_auth(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='AadTest', length=15)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        _create_config_store(self, self.kwargs)

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
        default_conditions = "{{u\'client_filters\': []}}" if sys.version_info[0] < 3 else "{{\'client_filters\': []}}"
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
        appconfig_keyvault_value = "{{\"uri\":\"https://fake.vault.azure.net/secrets/fakesecret\"}}"
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


class AppconfigReplicaLiveScenarioTest(ScenarioTest):
    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_replica_mgmt(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='ReplicaStore', length=24)
        replica_name = self.create_random_name(prefix='Replica', length=24)

        store_location = 'eastus'
        replica_location = 'westus'
        sku = 'standard'
        tag_key = "key"
        tag_value = "value"
        tag = tag_key + '=' + tag_value
        structured_tag = {tag_key: tag_value}
        system_assigned_identity = '[system]'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'replica_name': replica_name,
            'rg_loc': store_location,
            'replica_loc': replica_location,
            'rg': resource_group,
            'sku': sku,
            'tags': tag,
            'identity': system_assigned_identity,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        store = self.cmd(
            'appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --tags {tags} --assign-identity {identity} --retention-days {retention_days} --enable-purge-protection {enable_purge_protection}',
            checks=[self.check('name', '{config_store_name}'),
                    self.check('location', '{rg_loc}'),
                    self.check('resourceGroup', resource_group),
                    self.check('provisioningState', 'Succeeded'),
                    self.check('sku.name', sku),
                    self.check('tags', structured_tag),
                    self.check('identity.type', 'SystemAssigned'),
                    self.check('softDeleteRetentionInDays', '{retention_days}'),
                    self.check('enablePurgeProtection', '{enable_purge_protection}')]).get_output_in_json()

        self.cmd('appconfig replica create -s {config_store_name} -g {rg} -l {replica_loc} -n {replica_name}',
                 checks=[self.check('name', '{replica_name}'),
                         self.check('location', '{replica_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}',
                 checks=[self.check('name', '{replica_name}'),
                         self.check('location', '{replica_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded')])

        self.cmd('appconfig replica list -s {config_store_name}',
                 checks=[self.check('[0].name', '{replica_name}'),
                         self.check('[0].location', '{replica_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded')])

        self.cmd('appconfig replica delete -s {config_store_name} -g {rg} -n {replica_name} -y')

        with self.assertRaisesRegex(ResourceNotFoundError, f"The replica '{replica_name}' for App Configuration '{config_store_name}' not found."):
            self.cmd('appconfig replica show -s {config_store_name} -g {rg} -n {replica_name}')

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')


class AppConfigSnapshotLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super(AppConfigSnapshotLiveScenarioTest, self).__init__(*args, **kwargs)
    
    
    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_snapshot_mgmt(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='SnapshotStore', length=24)
        snapshot_name = "TestSnapshot"
        store_location = 'francecentral'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'snapshot_name': snapshot_name,
            'rg_loc': store_location,
            'rg': resource_group,
            'sku': sku,
            'retention_days': 1,
            'enable_purge_protection': False
        })

        _create_config_store(self, self.kwargs)

        credential_list =  self.cmd('appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })

        entry_key = "TestKey1"
        entry_value = "TestValue1"
        entry_key2 = "TestKey2"
        entry_value2 = "TestValue2"
        dev_label = "dev"
        entry_key3 = "LastTestKey"
        entry_value3 = "LastTestValue"
        
        # Create 2 keys with a common prefix and label "dev"
        self.kwargs.update({
            "key": entry_key,
            "value": entry_value,
            "label": dev_label
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key2,
            'value': entry_value2,
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key2),
                         self.check('value', entry_value2),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key3,
            'value': entry_value3,
        })

        self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key3),
                         self.check('value', entry_value3),
                         self.check('label', dev_label)])

        # Create a snapshot of all key-values that begin with the prefix 'Test'
        filter_dict = { "key": "Test*", "label": dev_label }
        retention_period = 3600 # Set retention period of 1 hour 
        self.kwargs.update({
            'filter': '\'{}\''.format(json.dumps(filter_dict)),
            'retention_period': retention_period
        })


        self.cmd('appconfig snapshot create --connection-string {connection_string} --snapshot-name {snapshot_name} --filters {filter} --retention-period {retention_period} --composition-type key_label --tags tag1=value1',
                 checks=[self.check('itemsCount', 2),
                         self.check('status', 'ready')])

        
        # Test showing created snapshot
        created_snapshot = self.cmd('appconfig snapshot show --connection-string {connection_string} --snapshot-name {snapshot_name} --fields name status items_count filters').get_output_in_json()
        
        self.assertEqual(created_snapshot['items_count'], 2)
        self.check(created_snapshot['status'], 'ready')
        self.assertDictEqual(created_snapshot['filters'][0], filter_dict)
        self.assertRaises(KeyError, lambda: created_snapshot['created'])
        
        # Test listing snapshots
        created_snapshots = self.cmd('appconfig snapshot list --snapshot-name {snapshot_name} --connection-string {connection_string} --fields name status items_count filters').get_output_in_json()
        self.assertEqual(created_snapshots[0]['items_count'], 2)
        self.assertEqual(created_snapshots[0]['status'], 'ready')
        self.assertDictEqual(created_snapshots[0]['filters'][0], filter_dict)

        # Test snapshot archive
        archived_snapshot = self.cmd('appconfig snapshot archive --connection-string {connection_string} --snapshot-name {snapshot_name}').get_output_in_json()
        self.assertIsNotNone(archived_snapshot['expires'])        
        self.assertEqual(archived_snapshot['status'], 'archived')
        active_snapshots = self.cmd('appconfig snapshot list --connection-string {connection_string} --status ready').get_output_in_json()
        self.assertEqual(len(active_snapshots), 0)
        
        # Test snapshot recovery
        self.cmd('appconfig snapshot recover --connection-string {connection_string} -s {snapshot_name}',
                                     checks=[self.check('itemsCount', 2),
                                             self.check('status', 'ready'),
                                             self.check('expires', None),])
        archived_snapshots = self.cmd('appconfig snapshot list --connection-string {connection_string} --status archived').get_output_in_json()
        self.assertEqual(len(archived_snapshots), 0)

        # Test listing snapshot kvs
        kvs = self.cmd('appconfig kv list --connection-string {connection_string} --snapshot {snapshot_name}').get_output_in_json()
        assert len(kvs) == 2

        # Test error returned for listing kvs in non-existent snapshot
        non_existent_snapshot_name = "non_existent_snapshot"

        self.kwargs.update({
            'snapshot_name': non_existent_snapshot_name
        })

        with self.assertRaisesRegex(CliResourceNotFoundError, f'No snapshot with name \'{non_existent_snapshot_name}\' was found.'):
            self.cmd('appconfig kv list --connection-string {connection_string} --snapshot {snapshot_name}')

        # Test snapshot import/export
        config_store_2_name = self.create_random_name(prefix='SnapshotStore', length=24)

        self.kwargs.update({
            'config_store_name': config_store_2_name,
            'snapshot_name': snapshot_name,
        })

        _create_config_store(self, self.kwargs)

        credential_list_2 =  self.cmd('appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'dest_connection_string': credential_list_2[0]['connectionString']
        })

        # Export snapshot kvs to store
        self.cmd('appconfig kv export -d appconfig --connection-string {connection_string} --dest-connection-string {dest_connection_string} --snapshot {snapshot_name} -y')

        # Export with skip-features should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--snapshot' cannot be specified with '--key',  '--label', '--skip-keyvault' or '--skip-features' arguments."):
            self.cmd('appconfig kv export -d appconfig --connection-string {connection_string} --dest-connection-string {dest_connection_string} --snapshot {snapshot_name} --skip-features -y')

        # Export with skip-keyvault should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--snapshot' cannot be specified with '--key',  '--label', '--skip-keyvault' or '--skip-features' arguments."):
            self.cmd('appconfig kv export -d appconfig --connection-string {connection_string} --dest-connection-string {dest_connection_string} --snapshot {snapshot_name} --skip-keyvault -y')

        # List snapshots in store
        dest_kvs = self.cmd('appconfig kv list --connection-string {dest_connection_string} --key * --label *').get_output_in_json()
        self.assertEqual(len(dest_kvs), 2)

        # Delete all kvs
        self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key * --label * -y')

        # Import snapshot kvs from source
        self.cmd('appconfig kv import -s appconfig --connection-string {dest_connection_string} --src-connection-string {connection_string} --src-snapshot {snapshot_name} -y')

        # Import with skip-features should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--src-snapshot' cannot be specified with '--src-key', '--src-label', or '--skip-features' arguments."):
            self.cmd('appconfig kv import -s appconfig --connection-string {dest_connection_string} --src-connection-string {connection_string} --src-snapshot {snapshot_name} --skip-features -y')

        # List snapshots in store
        current_kvs = self.cmd('appconfig kv list --connection-string {dest_connection_string} --key * --label *').get_output_in_json()
        self.assertEqual(len(current_kvs), 2)

def _create_config_store(test, kwargs):
    if 'retention_days' not in kwargs:
        kwargs.update({
            'retention_days': 1
        })
    test.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --retention-days {retention_days}')


def _create_user_assigned_identity(test, kwargs):
    return test.cmd('identity create -n {identity_name} -g {rg}').get_output_in_json()


def _setup_key_vault(test, kwargs):
    key_vault = test.cmd('keyvault create -n {keyvault_name} -g {rg} -l {rg_loc} --enable-purge-protection --retention-days 7').get_output_in_json()
    test.cmd('keyvault key create --vault-name {keyvault_name} -n {encryption_key}')
    test.cmd('keyvault set-policy -n {keyvault_name} --key-permissions get wrapKey unwrapKey --object-id {identity_id}')

    return key_vault


def _format_datetime(date_string):
    from dateutil.parser import parse
    try:
        return parse(date_string).strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        print("Unable to parse date_string '%s'", date_string)
        return date_string or ' '


class CredentialResponseSanitizer(RecordingProcessor):
    def process_response(self, response):
        if is_json_payload(response):
            try:
                json_data = shell_safe_json_parse(response["body"]["string"])

                if isinstance(json_data["value"], list):
                    for idx, credential in enumerate(json_data["value"]):
                        if "connectionString" in credential:
                            credential["id"] = "sanitized_id{}".format(idx + 1)
                            credential["value"] = "sanitized_secret{}".format(
                                idx + 1)

                            endpoint = next(
                                filter(lambda x: x.startswith("Endpoint="), credential["connectionString"].split(";")))[len("Endpoint="):]

                            credential["connectionString"] = "Endpoint={};Id={};Secret={}".format(
                                endpoint, credential["id"], credential["value"])

                response["body"]["string"] = json.dumps(json_data)

            except Exception:
                pass

        return response
