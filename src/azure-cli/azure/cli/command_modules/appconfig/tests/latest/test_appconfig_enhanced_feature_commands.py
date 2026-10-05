# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest
from azure.cli.core.azclierror import ResourceNotFoundError, MutuallyExclusiveArgumentError
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import AppConfigResourceGroupPreparer, create_config_store, CredentialResponseSanitizer, register_appconfig_query_matcher, register_appconfig_recording_processors

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class AppConfigEnhancedFeatureScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
        register_appconfig_query_matcher(self)
        register_appconfig_recording_processors(self)

    @AppConfigResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    # Uses Entra ID auth (store created with local auth disabled). For live recording, set
    # AZURE_CLI_TEST_DEV_RESOURCE_GROUP_NAME to a group where you hold "App Configuration Data Owner".
    def test_azconfig_enhanced_feature(self, resource_group, location):
        config_store_name = self.create_random_name(prefix='enhancedfeature', length=24)

        location = 'eastus'
        sku = 'standard'
        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': location,
            'rg': resource_group,
            'sku': sku,
            'endpoint': 'https://' + config_store_name + '.azconfig.io'
        })
        create_config_store(self, self.kwargs, disable_local_auth=True)

        entry_feature = 'Beta'
        entry_label = 'v1'

        self.kwargs.update({
            'feature_name': entry_feature,
            'label': entry_label
        })

        # Create a brand new enhanced feature flag entry (disabled by default)
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False),
                         self.check('label', entry_label)])

        # Update an existing enhanced feature flag with a description and requirement type
        updated_entry_description = "Beta Testing Feature Flag"
        updated_requirement_type = FeatureFlagConstants.REQUIREMENT_TYPE_ANY
        self.kwargs.update({
            'description': updated_entry_description,
            'requirement_type': updated_requirement_type
        })
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --description "{description}" --requirement-type {requirement_type} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False),
                         self.check('label', entry_label),
                         self.check('description', updated_entry_description),
                         self.check('conditions.requirement_type', updated_requirement_type)])

        # Show the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label}',
                 checks=[self.check('name', entry_feature),
                         self.check('label', entry_label),
                         self.check('description', updated_entry_description)])

        # Show with field filters
        self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --fields name enabled',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False)])

        # Enable the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag enable --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', True)])

        # Update telemetry and tags on the enabled flag - enabled state and description must be preserved
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --telemetry-enabled true --tags tag1=value1 tag2=value2 -y',
                 checks=[self.check('enabled', True),
                         self.check('description', updated_entry_description),
                         self.check('telemetry.enabled', True),
                         self.check('tags.tag1', 'value1'),
                         self.check('tags.tag2', 'value2'),
                         self.check('conditions.requirement_type', updated_requirement_type)])

        # Toggle the enabled state with the top-level --enable argument on set (other properties preserved)
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --enable false -y',
                 checks=[self.check('enabled', False),
                         self.check('description', updated_entry_description),
                         self.check('telemetry.enabled', True)])
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --enable -y',
                 checks=[self.check('enabled', True),
                         self.check('description', updated_entry_description),
                         self.check('telemetry.enabled', True)])

        # Set the entire flag as raw JSON with --flag (full replace of all properties)
        self.kwargs['flag_json'] = '{"name":"Beta","enabled":true,"description":"Set via --flag JSON","conditions":{"requirement_type":"All","filters":[{"name":"Microsoft.TimeWindow","parameters":{"Start":"Wed, 01 Jan 2025 00:00:00 GMT"}}]}}'
        self.cmd("appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --label {label} --flag '{flag_json}' -y",
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', True),
                         self.check('description', 'Set via --flag JSON'),
                         self.check('conditions.requirement_type', 'All'),
                         self.check('conditions.filters[0].name', 'Microsoft.TimeWindow')])

        # Overwrite the same flag with shorthand syntax - full replace drops the previous conditions
        self.kwargs['flag_shorthand'] = "{name:Beta,enabled:true,description:'Set via --flag shorthand'}"
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --label {label} --flag "{flag_shorthand}" -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', True),
                         self.check('description', 'Set via --flag shorthand'),
                         self.check('conditions', None)])

        # --flag is mutually exclusive with content arguments (validated before any request)
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "--flag cannot be combined with --description"):
            self.cmd("appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --label {label} --flag '{flag_json}' --description x -y")

        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "--flag cannot be combined with --enable"):
            self.cmd("appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --label {label} --flag '{flag_json}' --enable -y")

        # The name inside --flag must match --feature-name when both are provided
        self.kwargs['flag_mismatch'] = '{"name":"Delta","enabled":true}'
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "Feature name mismatch"):
            self.cmd("appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} --flag '{flag_mismatch}' -y")

        # Disable the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag disable --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False)])

        # List enhanced feature flags
        self.cmd('appconfig enhanced-feature-flag list --endpoint {endpoint} --auth-mode login',
                 checks=[self.check('[0].name', entry_feature)])

        # Delete the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag delete --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('label', entry_label)])

        # Confirm deletion
        self.cmd('appconfig enhanced-feature-flag list --endpoint {endpoint} --auth-mode login',
                 checks=[self.is_empty()])

        # Show a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' does not exist.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label}')

        # Enable a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' not found.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag enable --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y')

        # Disable a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' not found.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag disable --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y')

        # Delete a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' does not exist.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag delete --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y')

