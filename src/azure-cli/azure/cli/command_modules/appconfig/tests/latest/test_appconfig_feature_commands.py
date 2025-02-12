# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from knack.util import CLIError
from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.checkers import NoneCheck
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import _create_config_store, CredentialResponseSanitizer

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class AppConfigFeatureScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

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
        default_conditions = "{{\'client_filters\': []}}"
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
                                         self.check('display_name', None),
                                         self.check('conditions', default_conditions),
                                         self.check('allocation', None),
                                         self.check('variants', None),
                                         self.check('telemetry', None)]).get_output_in_json()
        assert len(response_dict) == 12

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
        default_conditions = "{{\'client_filters\': []}}"
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

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

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
        default_conditions = "{{\'client_filters\': []}}"
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
