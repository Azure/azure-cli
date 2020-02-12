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
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest, LiveScenarioTest)
from azure.cli.testsdk.checkers import NoneCheck
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants, KeyVaultConstants

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
FEATURE_FLAG_PREFIX = ".appconfig.featureflag/"


class AppConfigMgmtScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_mgmt(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='MgmtTest', length=24)

        location = 'eastus'
        sku = 'standard'
        system_assigned_identity = '[system]'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'identity': system_assigned_identity
        })

        store = self.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku} --assign-identity {identity}',
                         checks=[self.check('name', '{config_store_name}'),
                                 self.check('location', '{rg_loc}'),
                                 self.check('resourceGroup', resource_group),
                                 self.check('provisioningState', 'Succeeded'),
                                 self.check('sku.name', sku),
                                 self.check('identity.type', 'SystemAssigned')]).get_output_in_json()
        self.cmd('appconfig list -g {rg}',
                 checks=[self.check('[0].name', '{config_store_name}'),
                         self.check('[0].location', '{rg_loc}'),
                         self.check('[0].resourceGroup', resource_group),
                         self.check('[0].provisioningState', 'Succeeded'),
                         self.check('[0].sku.name', sku),
                         self.check('[0].identity.type', 'SystemAssigned')])
        self.cmd('appconfig show -n {config_store_name} -g {rg}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('identity.type', 'SystemAssigned')])

        tag_key = "Env"
        tag_value = "Prod"
        updated_tag = tag_key + '=' + tag_value
        structered_tag = {tag_key: tag_value}
        self.kwargs.update({
            'updated_tag': updated_tag,
            'update_sku': sku   # we currently only can test on standard sku
        })

        self.cmd('appconfig update -n {config_store_name} -g {rg} --tags {updated_tag} --sku {update_sku}',
                 checks=[self.check('name', '{config_store_name}'),
                         self.check('location', '{rg_loc}'),
                         self.check('resourceGroup', resource_group),
                         self.check('tags', structered_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku)])

        keyvault_name = self.create_random_name(prefix='MgmtTestKeyVault', length=24)
        encryption_key = self.create_random_name(prefix='EncryptionKey', length=24)
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
                         self.check('tags', structered_tag),
                         self.check('provisioningState', 'Succeeded'),
                         self.check('sku.name', sku),
                         self.check('encryption.keyVaultProperties.keyIdentifier', keyvault_uri.strip('/') + "/keys/{}/".format(encryption_key))])

        self.cmd('appconfig delete -n {config_store_name} -g {rg} -y')


class AppConfigCredentialScenarioTest(ScenarioTest):

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
        entry_value = "Red"
        entry_content_type = 'text'
        entry_label = 'v1.0.0'

        self.kwargs.update({
            'key': entry_key,
            'value': entry_value,
            'label': entry_label,
            'content_type': entry_content_type
        })

        # add a new key-value entry
        self.cmd('appconfig kv set -n {config_store_name} --key {key} --value {value} --content-type {content_type} --label {label} -y',
                 checks=[self.check('contentType', entry_content_type),
                         self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', entry_label)])

        # edit a key-value entry
        updated_entry_value = "Green"
        self.kwargs.update({
            'value': updated_entry_value
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


class AppConfigImportExportScenarioTest(ScenarioTest):

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
        exported_file_path = os.path.join(TEST_DIR, 'export.json')
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

        # Feature flags test
        imported_file_path = os.path.join(TEST_DIR, 'import_features.json')
        exported_file_path = os.path.join(TEST_DIR, 'export_features.json')
        key_filtered_features_file_path = os.path.join(TEST_DIR, 'key_filtered_features.json')
        prefix_added_features_file_path = os.path.join(TEST_DIR, 'prefix_added_features.json')
        skipped_features_file_path = os.path.join(TEST_DIR, 'skipped_features.json')
        export_separator_features_file_path = os.path.join(TEST_DIR, 'export_separator_features.json')
        import_separator_features_file_path = os.path.join(TEST_DIR, 'import_separator_features.json')
        import_features_alt_syntax_file_path = os.path.join(TEST_DIR, 'import_features_alt_syntax.json')

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
        self.cmd('appservice plan create -g {} -n {}'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} -p {}'.format(resource_group, webapp_name, plan))

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

        # Export KeyVault ref to AppService
        self.kwargs.update({
            'export_dest': 'appservice',
            'appservice_account': webapp_name
        })
        self.cmd('appconfig kv export --connection-string {connection_string} -d {export_dest} --appservice-account {appservice_account} --label {label} -y')

        app_settings = self.cmd('webapp config appsettings list -g {rg} -n {appservice_account}').get_output_in_json()
        exported_keys = next(x for x in app_settings if x['name'] == keyvault_key)
        self.assertEqual(exported_keys['name'], keyvault_key)
        self.assertEqual(exported_keys['value'], appsvc_keyvault_value)
        self.assertEqual(exported_keys['slotSetting'], False)

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
        exported_file_path = os.path.join(TEST_DIR, 'export_features.json')
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

        # Error if imported file has multiple feature sections
        self.kwargs.update({
            'imported_file_path': import_multiple_feature_sections_path
        })
        with self.assertRaisesRegexp(CLIError, 'Unable to proceed because file contains multiple sections corresponding to "Feature Management".'):
            self.cmd('appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} -y')

        # Error if imported file has "enabled for" in wrong format
        self.kwargs.update({
            'imported_file_path': import_wrong_enabledfor_format_path
        })
        with self.assertRaisesRegexp(CLIError, 'definition or have a true/false value.'):
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


class AppConfigToAppConfigImportExportScenarioTest(ScenarioTest):

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
        internal_feature_key = FEATURE_FLAG_PREFIX + entry_feature
        self.kwargs.update({
            'feature': entry_feature,
            'label': entry_label
        })
        # add a new feature flag entry
        self.cmd('appconfig feature set --connection-string {src_connection_string} --feature {feature} --label {label} -y',
                 checks=[self.check('key', entry_feature),
                         self.check('label', entry_label)])

        # add a new label for same feature
        self.kwargs.update({
            'label': updated_label
        })
        self.cmd('appconfig feature set --connection-string {src_connection_string} --feature {feature} --label {label} -y',
                 checks=[self.check('key', entry_feature),
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
        with self.assertRaisesRegexp(CLIError, "Import failed! Please provide only one of these arguments: '--label' or '--preserve-labels'."):
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
        with self.assertRaisesRegexp(CLIError, "Export failed! Please provide only one of these arguments: '--dest-label' or '--preserve-labels'."):
            self.cmd('appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --label {src_label} --dest-label {label} --preserve-labels -y')


class AppConfigFeatureScenarioTest(ScenarioTest):
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
        entry_label = 'v1'
        default_description = None
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
                         self.check('key', entry_feature),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # update an existing feature flag entry (we can only update description)
        updated_entry_description = "Beta Testing Feature Flag"
        self.kwargs.update({
            'description': updated_entry_description
        })
        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} --description "{description}" -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', entry_feature),
                         self.check('description', updated_entry_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # add a new label - this should create a new KV in the config store
        updated_label = 'v2'
        self.kwargs.update({
            'label': updated_label
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', entry_feature),
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
                         self.check('key', entry_feature),
                         self.check('description', updated_entry_description),
                         self.check('label', updated_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # show a feature flag with all 7 fields
        response_dict = self.cmd('appconfig feature show -n {config_store_name} --feature {feature} --label {label}',
                                 checks=[self.check('locked', default_locked),
                                         self.check('key', entry_feature),
                                         self.check('description', updated_entry_description),
                                         self.check('label', updated_label),
                                         self.check('state', default_state),
                                         self.check('conditions', default_conditions)]).get_output_in_json()
        assert len(response_dict) == 7

        # show a feature flag with field filtering
        response_dict = self.cmd('appconfig feature show -n {config_store_name} --feature {feature} --label {label} --fields key label state locked',
                                 checks=[self.check('locked', default_locked),
                                         self.check('key', entry_feature),
                                         self.check('label', updated_label),
                                         self.check('state', default_state)]).get_output_in_json()
        assert len(response_dict) == 4

        # List all features with null labels
        null_label_pattern = ""
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

        list_features = self.cmd('appconfig feature list -n {config_store_name} --label {label} --fields key label state locked',
                                 checks=[self.check('[0].locked', default_locked),
                                         self.check('[0].key', entry_feature),
                                         self.check('[0].label', entry_label),
                                         self.check('[0].state', default_state)]).get_output_in_json()
        assert len(list_features) == 2

        #  List all features with any label
        list_features = self.cmd('appconfig feature list -n {config_store_name}').get_output_in_json()
        assert len(list_features) == 2

        # Add another feature with name starting with Beta, null label
        prefix_feature = 'BetaPrefix'
        null_label = None

        self.kwargs.update({
            'feature': prefix_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', prefix_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Add feature with name ending with Beta, null label
        suffix_feature = 'SuffixBeta'

        self.kwargs.update({
            'feature': suffix_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', suffix_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        # Add feature where name contains Beta, null label
        contains_feature = 'ThisBetaVersion'

        self.kwargs.update({
            'feature': contains_feature
        })

        self.cmd('appconfig feature set -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', contains_feature),
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
                                 checks=[self.check('[0].key', prefix_feature),
                                         self.check('[0].label', null_label)]).get_output_in_json()
        assert len(list_features) == 1

        # Invalid Pattern - contains comma
        comma_pattern = 'Beta,Alpha'
        self.kwargs.update({
            'feature': comma_pattern
        })

        with self.assertRaisesRegexp(CLIError, "Comma separated feature names are not supported"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Invalid Pattern - contains invalid *
        invalid_pattern = 'Beta*ion'
        self.kwargs.update({
            'feature': invalid_pattern
        })

        with self.assertRaisesRegexp(CLIError, "Bad Request"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Invalid Pattern - contains multiple **
        invalid_pattern = '**ta'
        self.kwargs.update({
            'feature': invalid_pattern
        })

        with self.assertRaisesRegexp(CLIError, "Regular expression error in parsing"):
            self.cmd('appconfig feature list -n {config_store_name} --feature {feature}')

        # Delete Beta (label v2) feature flag using connection-string
        self.kwargs.update({
            'feature': entry_feature,
            'label': updated_label
        })

        # IN CLI, since we support delete by key/label pattern matching, return is a list of deleted items
        deleted = self.cmd('appconfig feature delete --connection-string {connection_string}  --feature {feature} --label {label} -y',
                           checks=[self.check('[0].locked', default_locked),
                                   self.check('[0].key', entry_feature),
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
                         self.check('key', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state)])

        # Unlock feature - ThisBetaVersion
        self.cmd('appconfig feature unlock -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', default_state)])

        # Enable feature - ThisBetaVersion
        on_state = 'on'
        self.cmd('appconfig feature enable -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', contains_feature),
                         self.check('description', default_description),
                         self.check('label', null_label),
                         self.check('state', on_state)])

        # Disable feature - ThisBetaVersion
        self.cmd('appconfig feature disable -n {config_store_name} --feature {feature} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', contains_feature),
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


class AppConfigFeatureFilterScenarioTest(ScenarioTest):
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
        entry_label = 'Standard'
        default_description = None
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
                         self.check('key', entry_feature),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', default_state),
                         self.check('conditions', default_conditions)])

        first_filter_name = 'FirstFilter'
        first_filter_params = 'Name1=Value1 Name2=Value2 Name1=Value1.1 Name3 Name4={\\"key\\":\\"value\\"}'
        first_filter_params_output = {
            "Name1": [
                "Value1",
                "Value1.1"
            ],
            "Name2": "Value2",
            "Name3": "",
            "Name4": "{\"key\":\"value\"}"
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
        second_filter_params = 'Foo=Bar=value name=Foo=Bar {\\"Value\\":\\"50\\",\\"SecondValue\\":\\"75\\"}=ParamNameIsJsonString'
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
                                         self.check('key', entry_feature),
                                         self.check('description', default_description),
                                         self.check('label', entry_label),
                                         self.check('state', default_state)]).get_output_in_json()

        conditions = response_dict.get('conditions')
        list_filters = conditions.get('client_filters')
        assert len(list_filters) == 3

        # Enable feature
        conditional_state = 'conditional'
        self.cmd('appconfig feature enable -n {config_store_name} --feature {feature} --label {label} -y',
                 checks=[self.check('locked', default_locked),
                         self.check('key', entry_feature),
                         self.check('description', default_description),
                         self.check('label', entry_label),
                         self.check('state', conditional_state)])

        # Delete Filter without index should throw error when duplicates exist
        with self.assertRaisesRegexp(CLIError, "contains multiple instances of filter"):
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


class AppConfigKeyValidationScenarioTest(ScenarioTest):

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
        with self.assertRaisesRegexp(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        self.kwargs.update({
            'key': ""
        })
        with self.assertRaisesRegexp(CLIError, "Key cannot be empty."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key "{key}" --value {value} -y')

        self.kwargs.update({
            'key': "."
        })
        with self.assertRaisesRegexp(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        self.kwargs.update({
            'key': FeatureFlagConstants.FEATURE_FLAG_PREFIX
        })
        with self.assertRaisesRegexp(CLIError, "Key is invalid. Key cannot start with the reserved prefix for feature flags."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        self.kwargs.update({
            'key': FeatureFlagConstants.FEATURE_FLAG_PREFIX.upper() + 'test'
        })
        with self.assertRaisesRegexp(CLIError, "Key is invalid. Key cannot start with the reserved prefix for feature flags."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} -y')

        # validate key for KeyVault ref
        self.kwargs.update({
            'key': "%KeyVault",
            'secret_identifier': "https://fake.vault.azure.net/secrets/fakesecret"
        })
        with self.assertRaisesRegexp(CLIError, "Key is invalid. Key cannot be a '.' or '..', or contain the '%' character."):
            self.cmd('appconfig kv set-keyvault --connection-string {connection_string} --key {key} --secret-identifier {secret_identifier} -y')

        # validate content type
        self.kwargs.update({
            'key': "Color",
            'content_type': FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE
        })
        with self.assertRaisesRegexp(CLIError, "Content type is invalid. It's a reserved content type for feature flags."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --content-type {content_type} -y')

        self.kwargs.update({
            'key': "Color",
            'content_type': FeatureFlagConstants.FEATURE_FLAG_CONTENT_TYPE.upper()
        })
        with self.assertRaisesRegexp(CLIError, "Content type is invalid. It's a reserved content type for feature flags."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --content-type {content_type} -y')

        self.kwargs.update({
            'content_type': KeyVaultConstants.KEYVAULT_CONTENT_TYPE
        })
        with self.assertRaisesRegexp(CLIError, "Content type is invalid. It's a reserved content type for KeyVault references."):
            self.cmd('appconfig kv set --connection-string {connection_string} --key {key} --value {value} --content-type {content_type} -y')

        # validate feature name
        self.kwargs.update({
            'feature': 'Bet@'
        })
        with self.assertRaisesRegexp(CLIError, "Feature name is invalid. Only alphanumeric characters, '.', '-' and '_' are allowed."):
            self.cmd('appconfig feature set --connection-string {connection_string} --feature {feature} -y')

        self.kwargs.update({
            'feature': ''
        })
        with self.assertRaisesRegexp(CLIError, "Feature name cannot be empty."):
            self.cmd('appconfig feature set --connection-string {connection_string} --feature "{feature}" -y')

        # validate keys and features during file import
        imported_file_path = os.path.join(TEST_DIR, 'import_invalid_kv_and_features.json')
        expected_export_file_path = os.path.join(TEST_DIR, 'export_valid_kv_and_features.json')
        actual_export_file_path = os.path.join(TEST_DIR, 'export.json')
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


def _create_config_store(test, kwargs):
    test.cmd('appconfig create -n {config_store_name} -g {rg} -l {rg_loc} --sku {sku}')


def _create_user_assigned_identity(test, kwargs):
    return test.cmd('identity create -n {identity_name} -g {rg}').get_output_in_json()


def _setup_key_vault(test, kwargs):
    key_vault = test.cmd('keyvault create -n {keyvault_name} -g {rg} -l {rg_loc} --enable-purge-protection --enable-soft-delete').get_output_in_json()
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
