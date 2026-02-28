# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import javaproperties
import json
import os
import yaml

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest, LiveScenarioTest)
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants, KeyVaultConstants, ImportExportProfiles, AppServiceConstants
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.azclierror import AzureInternalError, MutuallyExclusiveArgumentError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigImportExportScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export(self, resource_group, location):
        store_name_prefix = get_resource_name_prefix('ImportTest')
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

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

        self.assertNotEqual(background_color_kv['etag'], updated_background_color_kv['etag'])

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
        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'True'

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

        # Dry run and yes options should not be used together
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "The '--dry-run' and '--yes' options cannot be specified together."):
            self.cmd('appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} --label {label} --dry-run -y')

        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "The '--dry-run' and '--yes' options cannot be specified together."):
            self.cmd('appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_path}" --format {imported_format} --label {label} --dry-run -y')

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_new_fm_schema(self, resource_group, location):
        # Feature flags test with new ms fm schema
        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'False'

        new_fm_store_prefix = get_resource_name_prefix('NewFmImport')
        config_store_name = self.create_random_name(prefix=new_fm_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'import_source': 'file',
            'imported_format': 'json',
        })
        create_config_store(self, self.kwargs)
       
        # Invalid requirement type should fail import
        import_features_invalid_requirement_type_file_path = os.path.join(TEST_DIR, 'import_features_invalid_requirement_type.json')
        self.kwargs.update({
            'imported_file_path': import_features_invalid_requirement_type_file_path
        })

        with self.assertRaisesRegex(CLIError, "Feature 'Timestamp' must have an Any/All requirement type"):
            self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')

        # Invalid variants import
        invalid_variants_file_path = os.path.join(TEST_DIR, 'import_invalid_variants.json')
        self.kwargs.update({
            'imported_file_path': invalid_variants_file_path
        })
        with self.assertRaisesRegex(CLIError, "Feature variant must contain required 'name' attribute:"):
            self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')
        
        imported_new_fm_schema_file_path = os.path.join(TEST_DIR, 'import_features_new_fm_schema.json')
        exported_new_fm_schema_file_path = os.path.join(TEST_DIR, 'export_features_new_fm_schema.json')

        self.kwargs.update({
            'label': 'KeyValuesWithFeaturesFFV2',
            'imported_file_new_fm_path': imported_new_fm_schema_file_path,
            'exported_file_new_fm_path': exported_new_fm_schema_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_new_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_new_fm_path}" --format {imported_format} --label {label} -y')
        with open(imported_new_fm_schema_file_path) as json_file:
            imported_kvs = json.load(json_file)
        with open(exported_new_fm_schema_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert imported_kvs == exported_kvs
        os.remove(exported_new_fm_schema_file_path)

        # Import/Export new fm yaml file
        imported_new_fm_schema_yaml_file_path = os.path.join(TEST_DIR, 'import_features_new_fm_schema_yaml.json')
        exported_new_fm_schema_yaml_file_path = os.path.join(TEST_DIR, 'export_features_new_fm_schema_yaml.json')
        exported_new_fm_schema_as_yaml_file_path = os.path.join(TEST_DIR, 'export_features_new_fm_schema_as_yaml.json')

        self.kwargs.update({
            'label': 'NewFmSchemaYamlTests',
            'imported_format': 'yaml',
            'imported_ffv2_file_path': imported_new_fm_schema_yaml_file_path,
            'exported_ffv2_file_path': exported_new_fm_schema_yaml_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_ffv2_file_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_ffv2_file_path}" --format {imported_format} --label {label} -y')
        exported_new_fm_yaml_file = {}
        exported_new_fm_as_yaml_file = {}
        with open(exported_new_fm_schema_yaml_file_path) as yaml_file:
            for yaml_data in list(yaml.safe_load_all(yaml_file)):
                exported_new_fm_yaml_file.update(yaml_data)
        with open(exported_new_fm_schema_as_yaml_file_path) as yaml_file:
            for yaml_data in list(yaml.safe_load_all(yaml_file)):
                exported_new_fm_as_yaml_file.update(yaml_data)
        assert exported_new_fm_yaml_file == exported_new_fm_as_yaml_file
        os.remove(exported_new_fm_schema_yaml_file_path)

        # Import/Export properties file
        imported_prop_file_path = os.path.join(TEST_DIR, 'import_features_prop.json')
        exported_prop_file_path = os.path.join(TEST_DIR, 'export_features_prop.json')
        exported_as_kv_prop_file_path = os.path.join(TEST_DIR, 'export_as_kv_prop.json')

        self.kwargs.update({
            'label': 'NewFmSchemaPropertiesTests',
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


    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_kvset(self, resource_group, location):
        kvset_store_prefix = get_resource_name_prefix('KVSetImportTest')
        config_store_name = self.create_random_name(prefix=kvset_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

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
        strict_store_prefix = get_resource_name_prefix('StrictImportTest')
        config_store_name = self.create_random_name(prefix=strict_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

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
        import_export_store_prefix = get_resource_name_prefix('ImportExportTest')
        config_store_name = self.create_random_name(prefix=import_export_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

        # Get connection string
        credential_list = self.cmd(
            'appconfig credential list -n {config_store_name} -g {rg}').get_output_in_json()
        self.kwargs.update({
            'connection_string': credential_list[0]['connectionString']
        })

        # Create AppService plan and webapp
        web_app_prefix = get_resource_name_prefix('WebApp')
        webapp_name = self.create_random_name(prefix=web_app_prefix, length=24)
        plan_prefix = get_resource_name_prefix('Plan')
        plan = self.create_random_name(prefix=plan_prefix, length=24)
        # Require a standard sku to allow for deployment slots
        self.cmd('appservice plan create -g {} -n {} --sku S1'.format(resource_group, plan))
        self.cmd('webapp create -g {} -n {} -p {}'.format(resource_group, webapp_name, plan))

        # Create deployment slot
        slot_prefix = get_resource_name_prefix('Slot')
        slot = self.create_random_name(prefix=slot_prefix, length=24)
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
        self.assertEqual(exported_keys['name'], entry_key)
        self.assertEqual(exported_keys['value'], expected_reference)
        self.assertEqual(exported_keys['slotSetting'], False)

        # Assert second reference is of right format
        exported_keys = next(x for x in app_settings if x['name'] == entry_key2)
        self.assertEqual(exported_keys['name'], entry_key2)
        self.assertEqual(exported_keys['value'], expected_reference2)
        self.assertEqual(exported_keys['slotSetting'], False)


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
        appconfig_keyvault_value = f"{{{json.dumps({'uri': keyvault_id})}}}"
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
        appconfigslot_keyvault_value = f"{{{json.dumps({'uri': slot_keyvault_id})}}}"
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
        appconfig_keyvault_value = f"{{{json.dumps({'uri': 'https://myvault.vault.azure.net/secrets/mysecret/ec96f02080254f109c51a1f14cdb1931'})}}}"
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

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_naming_conventions(self, resource_group, location):
        naming_convention_store_prefix = get_resource_name_prefix('NamingConventionTest')
        config_store_name = self.create_random_name(prefix=naming_convention_store_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku
        })
        create_config_store(self, self.kwargs)

        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'True'
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

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_azconfig_import_export_respect_both_schemas_naming_conventions(self, resource_group, location):
        # Respect both fm schemas in file
        both_schema_test_prefix = get_resource_name_prefix('BothSchemaTest')
        config_store_name = self.create_random_name(prefix=both_schema_test_prefix, length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'import_source': 'file'
        })
        create_config_store(self, self.kwargs)

        # # Camel case naming convention
        os.environ['AZURE_APPCONFIG_FM_COMPATIBLE'] = 'False'

        imported_both_schemas_camel_case_file_path = os.path.join(TEST_DIR, 'respectBothFmSchemaCamelCase.json')
        exported_both_schemas_camel_case_file_path = os.path.join(TEST_DIR, 'export_features_both_schema_camel_case_file_path.json')
        expected_exported_both_schemas_file_path = os.path.join(TEST_DIR, 'expected_export_features_both_schema_file_path.json')

        self.kwargs.update({
            'label': 'RespectBothFmSchemasCamelCase',
            'imported_format': 'json',
            'imported_file_both_schemas_fm_path': imported_both_schemas_camel_case_file_path,
            'exported_file_both_schemas_fm_path': exported_both_schemas_camel_case_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        with open(exported_both_schemas_camel_case_file_path) as json_file:
            exported_camel_case_kvs = json.load(json_file)
        with open(expected_exported_both_schemas_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert exported_camel_case_kvs == exported_kvs
        os.remove(exported_both_schemas_camel_case_file_path)

        # # Pascal case naming convention
        imported_both_schemas_pascal_case_file_path = os.path.join(TEST_DIR, 'respectBothFmSchemaPascalCase.json')
        exported_both_schemas_pascal_case_file_path = os.path.join(TEST_DIR, 'export_features_both_schema_pascal_case_file_path.json')

        self.kwargs.update({
            'label': 'RespectBothFmSchemasPascalCase',
            'imported_format': 'json',
            'imported_file_both_schemas_fm_path': imported_both_schemas_pascal_case_file_path,
            'exported_file_both_schemas_fm_path': exported_both_schemas_pascal_case_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        with open(exported_both_schemas_pascal_case_file_path) as json_file:
            exported_pascal_case_kvs = json.load(json_file)
        with open(expected_exported_both_schemas_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert exported_pascal_case_kvs == exported_kvs
        os.remove(exported_both_schemas_pascal_case_file_path)

        # # Hyphen case naming convention
        imported_both_schemas_hyphen_case_file_path = os.path.join(TEST_DIR, 'respectBothFmSchemaHyphenCase.json')
        exported_both_schemas_hyphen_case_file_path = os.path.join(TEST_DIR, 'export_features_both_schema_hyphen_case_file_path.json')

        self.kwargs.update({
            'label': 'RespectBothFmSchemasHyphenCase',
            'imported_format': 'json',
            'imported_file_both_schemas_fm_path': imported_both_schemas_hyphen_case_file_path,
            'exported_file_both_schemas_fm_path': exported_both_schemas_hyphen_case_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        with open(exported_both_schemas_hyphen_case_file_path) as json_file:
            exported_hyphen_case_kvs = json.load(json_file)
        with open(expected_exported_both_schemas_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert exported_hyphen_case_kvs == exported_kvs
        os.remove(exported_both_schemas_hyphen_case_file_path)


        # # Underscore case naming convention
        imported_both_schemas_underscore_case_file_path = os.path.join(TEST_DIR, 'respectBothFmSchemaUnderscoreCase.json')
        exported_both_schemas_underscore_case_file_path = os.path.join(TEST_DIR, 'export_features_both_schema_underscore_case_file_path.json')

        self.kwargs.update({
            'label': 'RespectBothFmSchemasUnderscoreCase',
            'imported_format': 'json',
            'imported_file_both_schemas_fm_path': imported_both_schemas_underscore_case_file_path,
            'exported_file_both_schemas_fm_path': exported_both_schemas_underscore_case_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        with open(exported_both_schemas_underscore_case_file_path) as json_file:
            exported_underscore_case_kvs = json.load(json_file)
        with open(expected_exported_both_schemas_file_path) as json_file:
            exported_kvs = json.load(json_file)
        assert exported_underscore_case_kvs == exported_kvs
        os.remove(exported_both_schemas_underscore_case_file_path)

        # # Duplicate features in both schemas
        imported_duplicate_features_both_schemas_file_path = os.path.join(TEST_DIR, 'import_duplicate_features_both_schemas.json')
        exported_duplicate_features_both_schemas_file_path = os.path.join(TEST_DIR, 'export_features_duplicate_features_both_schemas_path.json')
        expected_export_duplicate_features_both_schemas_file_path = os.path.join(TEST_DIR, 'expected_export_duplicate_features_both_schemas.json')

        self.kwargs.update({
            'label': 'DuplicateFeaturesBothSchemas',
            'imported_format': 'json',
            'imported_file_both_schemas_fm_path': imported_duplicate_features_both_schemas_file_path,
            'exported_file_both_schemas_fm_path': exported_duplicate_features_both_schemas_file_path
        })
        self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        self.cmd(
            'appconfig kv export -n {config_store_name} -d {import_source} --path "{exported_file_both_schemas_fm_path}" --format {imported_format} --label {label} -y')
        with open(exported_duplicate_features_both_schemas_file_path) as json_file:
            exported_duplicate_features = json.load(json_file)
        with open(expected_export_duplicate_features_both_schemas_file_path) as json_file:
            expected_duplicate_features = json.load(json_file)
        assert exported_duplicate_features == expected_duplicate_features
        os.remove(exported_duplicate_features_both_schemas_file_path)

        # Invalid fm sections should fail import
        invalid_ms_fm_schema_with_both_schemas_file_path = os.path.join(TEST_DIR, 'import_invalid_ms_fm_schema_with_both_schemas.json')
        self.kwargs.update({
            'imported_file_path': invalid_ms_fm_schema_with_both_schemas_file_path,
            'imported_format': 'json'
        })
        with self.assertRaisesRegex(CLIError, "Data contains an already defined section with the key FeatureManagement."):
            self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')


        invalid_fm_sections_file_path = os.path.join(TEST_DIR, 'import_invalid_fm_sections.json')
        self.kwargs.update({
            'imported_file_path': invalid_fm_sections_file_path
        })
        with self.assertRaisesRegex(CLIError, 'Unable to proceed because file contains multiple sections corresponding to "Feature Management".'):
            self.cmd(
            'appconfig kv import -n {config_store_name} -s {import_source} --path "{imported_file_path}" --format {imported_format} -y')


class AppConfigToAppConfigImportExportScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
    
    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_appconfig_to_appconfig_import_export(self, resource_group, location):
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

        # Tag filtering test
        key_tag_test = "TagTestKey"
        tags = {
            "tag1": "value1",
            "tag2": "value2"
        }
        tags_str = ' '.join([f"{k}={v}" for k, v in tags.items()])
        self.kwargs.update({
            'key': key_tag_test,
            'tags': tags_str
        })

        # add a new key-value entry with tags
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --value {value} --tags {tags} -y',
                 checks=[self.check('key', key_tag_test),
                         self.check('tags', tags)])
        
        # create entry without tags
        label_without_tags = "LabelWithoutTags"
        self.kwargs.update({
            'label': label_without_tags
        })

        # add a new key-value entry without tags
        self.cmd('appconfig kv set --connection-string {src_connection_string} --key {key} --label {label} --value {value} -y',
                 checks=[self.check('label', label_without_tags),
                         self.check('tags', {})])
        
        # export only key-value with tags and add new tags
        dest_tags = {
            "tag3": "value3"
        }
        dest_tags_str = ' '.join([f"{k}={v}" for k, v in dest_tags.items()])
        self.kwargs.update({
            'dest_tags': dest_tags_str
        })

        self.cmd('appconfig kv export --connection-string {src_connection_string} -d {import_source} --dest-connection-string {dest_connection_string} --key {key} --tags {tags} --dest-tags {dest_tags} -y')
        deleted_kv_with_tags = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --tags {dest_tags} -y',
                                        checks=[self.check('[0].key', key_tag_test),
                                                self.check('[0].tags', dest_tags)]).get_output_in_json()
        assert(len(deleted_kv_with_tags) == 1)

        # import only key-value with tags and add new tags
        self.cmd('appconfig kv import --connection-string {dest_connection_string} -s {import_source} --src-connection-string {src_connection_string} --src-key {key} --src-tags {tags} --tags {dest_tags} -y')
        deleted_kv_with_tags = self.cmd('appconfig kv delete --connection-string {dest_connection_string} --key {key} --tags {dest_tags} -y',
                                        checks=[self.check('[0].key', key_tag_test),
                                                self.check('[0].tags', dest_tags)]).get_output_in_json()
        assert(len(deleted_kv_with_tags) == 1)



class AppConfigKubernetesConfigMapImportLiveScenarioTest(LiveScenarioTest):
    """Test suite for importing key-values from Kubernetes ConfigMaps using AKS RunCommand."""

    @AllowLargeResponse()
    @ResourceGroupPreparer(parameter_name_for_location='location')
    def test_appconfig_import_from_kubernetes_configmap(self, resource_group, location):
        """Test all scenarios for importing key-values from Kubernetes ConfigMaps using AKS RunCommand."""
        configmap_import_store_prefix = get_resource_name_prefix('ConfigMapImportTest')
        configmap_import_aks_prefix = get_resource_name_prefix('ImportAKSTest')
        config_store_name = self.create_random_name(prefix=configmap_import_store_prefix, length=24)
        
        # Create AKS cluster for testing
        aks_cluster_name = self.create_random_name(prefix=configmap_import_aks_prefix, length=24)
        
        location = 'westus2'
        sku = 'standard'
        namespace = 'default'
        
        self.kwargs.update({
            'config_store_name': config_store_name,
            'aks_cluster_name': aks_cluster_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'namespace': namespace
        })
        
        # Create App Configuration store
        create_config_store(self, self.kwargs)

        aks_created = False
        
        try:
            # Create AKS cluster and wait for completion
            self.cmd('aks create -g {rg} -n {aks_cluster_name} -l {rg_loc} --node-count 1 --generate-ssh-keys --enable-managed-identity --enable-image-cleaner --node-os-upgrade-channel NodeImage')
            
            # Wait for AKS cluster to be ready
            self.cmd('aks wait -g {rg} -n {aks_cluster_name} --created')
            
            aks_created = True

            # try:
            # Scenario 1: Import from a specific ConfigMap
            configmap_name = 'test-config'
            label1 = 'ConfigMapImport'
            prefix = 'test/'
            
            kubectl_create_cmd = f'''kubectl create configmap {configmap_name} --from-literal=database.host=localhost --from-literal=database.port=5432 --from-literal=app.name=testapp -n {namespace}'''
            
            self.kwargs.update({
                'configmap_name': configmap_name,
                'label': label1,
                'prefix': prefix,
                'kubectl_create_cmd': kubectl_create_cmd
            })
            
            # Create ConfigMap using AKS run command
            self.cmd('aks command invoke -g {rg} -n {aks_cluster_name} --command "{kubectl_create_cmd}"')
            
            # Import from specific ConfigMap
            self.cmd('appconfig kv import -n {config_store_name} -s aks --aks-cluster {aks_cluster_name} --configmap-name {configmap_name} --configmap-namespace {namespace} --label {label} --prefix {prefix} -y')

            # Verify imported key-values
            imported_kvs = self.cmd('appconfig kv list -n {config_store_name} --label {label}').get_output_in_json()
            
            # Check that all expected keys were imported
            expected_keys = ['test/database.host', 'test/database.port', 'test/app.name']
            imported_keys = [kv['key'] for kv in imported_kvs]
            
            for expected_key in expected_keys:
                assert expected_key in imported_keys, f"Expected key '{expected_key}' not found in imported keys"
            
            # Verify specific values
            database_host = next(kv for kv in imported_kvs if kv['key'] == 'test/database.host')
            assert database_host['value'] == 'localhost'

            database_port = next(kv for kv in imported_kvs if kv['key'] == 'test/database.port')
            assert database_port['value'] == '5432'
            
            app_name = next(kv for kv in imported_kvs if kv['key'] == 'test/app.name')
            assert app_name['value'] == 'testapp'

            # Scenario 2: Error handling - non-existent ConfigMap
            non_existent_configmap = 'non-existent-config'
            error_label = 'ErrorTest'
            
            self.kwargs.update({
                'non_existent_configmap': non_existent_configmap,
                'error_label': error_label
            })
            
            # This should fail gracefully
            with self.assertRaises(AzureInternalError):
                self.cmd('appconfig kv import -n {config_store_name} -s aks --aks-cluster {aks_cluster_name} --configmap-name {non_existent_configmap} --configmap-namespace {namespace} --label {error_label} -y')
        finally:
            if aks_created:
                try:
                    self.cmd('aks delete -g {rg} -n {aks_cluster_name} --yes --no-wait')
                except Exception as cleanup_error:
                    print(f"Warning: Failed to clean up AKS cluster {aks_cluster_name}: {str(cleanup_error)}")