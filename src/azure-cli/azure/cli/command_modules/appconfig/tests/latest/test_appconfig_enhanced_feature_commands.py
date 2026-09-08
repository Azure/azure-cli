# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os

from azure.cli.testsdk import ScenarioTest
from azure.cli.core.azclierror import ResourceNotFoundError
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
            'feature': entry_feature,
            'label': entry_label
        })

        # Create a brand new enhanced feature flag entry (disabled by default)
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y',
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
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} --description "{description}" --requirement-type {requirement_type} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False),
                         self.check('label', entry_label),
                         self.check('description', updated_entry_description),
                         self.check('conditions.requirement_type', updated_requirement_type)])

        # Show the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature {feature} --label {label}',
                 checks=[self.check('name', entry_feature),
                         self.check('label', entry_label),
                         self.check('description', updated_entry_description)])

        # Show with field filters
        self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} --fields name enabled',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False)])

        # Enable the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag enable --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', True)])

        # Update telemetry and tags on the enabled flag - enabled state and description must be preserved
        self.cmd('appconfig enhanced-feature-flag set --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} --telemetry-enabled true --tags tag1=value1 tag2=value2 -y',
                 checks=[self.check('enabled', True),
                         self.check('description', updated_entry_description),
                         self.check('telemetry.enabled', True),
                         self.check('tags.tag1', 'value1'),
                         self.check('tags.tag2', 'value2'),
                         self.check('conditions.requirement_type', updated_requirement_type)])

        # Disable the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag disable --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('enabled', False)])

        # List enhanced feature flags
        self.cmd('appconfig enhanced-feature-flag list --endpoint {endpoint} --auth-mode login',
                 checks=[self.check('[0].name', entry_feature)])

        # Delete the enhanced feature flag
        self.cmd('appconfig enhanced-feature-flag delete --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y',
                 checks=[self.check('name', entry_feature),
                         self.check('label', entry_label)])

        # Confirm deletion
        self.cmd('appconfig enhanced-feature-flag list --endpoint {endpoint} --auth-mode login',
                 checks=[self.is_empty()])

        # Show a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' does not exist.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag show --endpoint {endpoint} --auth-mode login --feature {feature} --label {label}')

        # Enable a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' not found.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag enable --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y')

        # Disable a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' not found.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag disable --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y')

        # Delete a non-existent enhanced feature flag should fail
        with self.assertRaisesRegex(ResourceNotFoundError, "Enhanced feature flag '{}' with label '{}' does not exist.".format(entry_feature, entry_label)):
            self.cmd('appconfig enhanced-feature-flag delete --endpoint {endpoint} --auth-mode login --feature {feature} --label {label} -y')

