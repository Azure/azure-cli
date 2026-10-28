# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from unittest.mock import Mock, call, patch

from azure.appconfiguration import FeatureFlag
from azure.core import MatchConditions
from azure.core.paging import ItemPaged
from azure.cli.testsdk import ScenarioTest
from azure.cli.core.azclierror import ResourceNotFoundError, MutuallyExclusiveArgumentError, RequiredArgumentMissingError, InvalidArgumentValueError
from azure.cli.command_modules.appconfig._constants import FeatureFlagConstants
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig.tests.latest._test_utils import AppConfigResourceGroupPreparer, create_config_store, CredentialResponseSanitizer, register_appconfig_query_matcher, register_appconfig_recording_processors

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class AppConfigEnhancedFeatureSetTests(ScenarioTest):

    def test_enhanced_feature_set_requires_name(self):
        for arguments in ('', '--flag "{}"', '--flag "{name:null,enabled:false}"'):
            with self.subTest(arguments=arguments):
                self.kwargs['arguments'] = arguments
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    with self.assertRaisesRegex(RequiredArgumentMissingError, "name.*required"):
                        self.cmd('appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io '
                                 '--auth-mode login -y {arguments}')

                    get_client.assert_not_called()

    def test_enhanced_feature_set_name_sources(self):
        for arguments in (
                '--feature-name Beta',
                '--flag "{name:Beta,enabled:false}"',
                '--feature-name Beta --flag "{enabled:false}"',
                '--feature-name Beta --flag "{name:Beta,enabled:false}"'):
            with self.subTest(arguments=arguments):
                self.kwargs['arguments'] = arguments
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    client = get_client.return_value
                    client.get_feature_flag.return_value = FeatureFlag(name='Beta', enabled=False)
                    client.set_feature_flag.side_effect = lambda flag: flag

                    self.cmd('appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io '
                             '--auth-mode login -y {arguments}',
                             checks=[self.check('name', 'Beta'), self.check('enabled', False)])

                    client.set_feature_flag.assert_called_once()
                    self.assertEqual(client.set_feature_flag.call_args.args[0].name, 'Beta')

    def test_enhanced_feature_set_flag_conflicts(self):
        for arguments, conflicting_options in (
                ('--description updated', '--description'),
                ('--requirement-type All', '--requirement-type'),
                ('--telemetry-enabled true', '--telemetry-enabled'),
                ('--telemetry-enabled false', '--telemetry-enabled'),
                ('--description updated --requirement-type Any --telemetry-enabled false',
                 '--description, --requirement-type, --telemetry-enabled')):
            with self.subTest(arguments=arguments):
                self.kwargs.update({
                    'flag': '{"name":"Beta","enabled":false}',
                    'arguments': arguments
                })
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    with self.assertRaisesRegex(
                            MutuallyExclusiveArgumentError, '--flag cannot be combined with ' + conflicting_options):
                        self.cmd("appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io "
                                 "--auth-mode login --flag '{flag}' -y {arguments}")

                    get_client.assert_not_called()

    def test_enhanced_feature_set_flag_metadata_overrides(self):
        for arguments, expected_label, expected_tags in (
                ('', 'original', {'source': 'flag', 'original': 'value'}),
                ('--label override', 'override', {'source': 'flag', 'original': 'value'}),
                ('--tags source=cli added=value', 'original', {'source': 'cli', 'added': 'value'}),
                ('--label override --tags source=cli added=value',
                 'override', {'source': 'cli', 'added': 'value'})):
            with self.subTest(arguments=arguments):
                self.kwargs.update({
                    'flag': '{"name":"Beta","enabled":true,"label":"original",'
                            '"tags":{"source":"flag","original":"value"}}',
                    'arguments': arguments
                })
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    client = get_client.return_value
                    client.set_feature_flag.side_effect = lambda flag: flag

                    self.cmd("appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io "
                             "--auth-mode login --flag '{flag}' -y {arguments}",
                             checks=[self.check('name', 'Beta'),
                                     self.check('enabled', True),
                                     self.check('label', expected_label),
                                     self.check('tags', expected_tags)])

                    client.get_feature_flag.assert_not_called()
                    client.set_feature_flag.assert_called_once()
                    submitted_flag = client.set_feature_flag.call_args.args[0]
                    self.assertEqual(submitted_flag.label, expected_label)
                    self.assertEqual(submitted_flag.tags, expected_tags)

    def test_enhanced_feature_set_flag_non_object(self):
        for flag in ([], [1], True, 42, 'Beta'):
            with self.subTest(flag=flag):
                self.kwargs['flag'] = json.dumps(flag)
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    with self.assertRaisesRegex(InvalidArgumentValueError, '--flag must be a JSON object'):
                        self.cmd("appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io "
                                 "--auth-mode login --feature-name Beta --flag '{flag}' -y")

                    get_client.assert_not_called()

    def test_enhanced_feature_set_flag_invalid_names(self):
        for feature_name in ('', 'Beta%', 'Beta:Feature'):
            for name_source in ('flag', 'feature-name'):
                with self.subTest(feature_name=feature_name, name_source=name_source):
                    self.kwargs.update({
                        'flag': json.dumps({'name': feature_name} if name_source == 'flag' else {'enabled': False}),
                        'arguments': '--feature-name "{}"'.format(feature_name) if name_source == 'feature-name' else ''
                    })
                    with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                        with self.assertRaisesRegex(InvalidArgumentValueError, 'Feature name cannot'):
                            self.cmd("appconfig enhanced-feature-flag set --endpoint https://example.azconfig.io "
                                     "--auth-mode login --flag '{flag}' -y {arguments}")

                        get_client.assert_not_called()


class AppConfigEnhancedFeatureDeleteTests(ScenarioTest):

    def test_enhanced_feature_delete_requires_feature_name(self):
        with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
            with self.assertRaises(SystemExit) as error:
                self.cmd('appconfig enhanced-feature-flag delete --endpoint https://example.azconfig.io --auth-mode login -y')

            self.assertEqual(error.exception.code, 2)
            get_client.assert_not_called()

    def test_enhanced_feature_delete_explicit_selectors(self):
        for selector in ('Beta', 'Beta*', '*'):
            with self.subTest(selector=selector):
                feature_flag = FeatureFlag(name='Beta', enabled=False)
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    client = get_client.return_value
                    client.list_feature_flags.return_value = [feature_flag]
                    client.delete_feature_flag.return_value = feature_flag

                    self.cmd('appconfig enhanced-feature-flag delete --endpoint https://example.azconfig.io '
                             '--auth-mode login --feature-name "{}" -y'.format(selector),
                             checks=[self.check('[0].name', 'Beta')])

                    client.list_feature_flags.assert_called_once_with(
                        name_filter=selector, label_filter='\\0', tags_filter=None)
                    client.delete_feature_flag.assert_called_once_with(
                        name='Beta', label=None, etag=feature_flag.etag,
                        match_condition=MatchConditions.IfNotModified)


class AppConfigEnhancedFeatureListTests(ScenarioTest):

    def test_enhanced_feature_list_limits_and_pagination(self):
        for arguments, total, expected_count, expected_pages in (
                ('', 137, 100, 3),
                ('--top 1', 137, 1, 1),
                ('--top 55', 137, 55, 2),
                ('--top 120', 137, 120, 3),
                ('--all', 137, 137, 4),
                ('--all --top 1', 137, 137, 4),
                ('', 7, 7, 1),
                ('--top 55', 7, 7, 1),
                ('', 0, 0, 1)):
            with self.subTest(arguments=arguments, total=total):
                feature_flags = [FeatureFlag(name='Beta{}'.format(index), enabled=False)
                                 for index in range(total)]
                pages = [feature_flags[index:index + 40] for index in range(0, total, 40)] or [[]]
                get_next = Mock(side_effect=[
                    (str(index + 1) if index + 1 < len(pages) else None, page)
                    for index, page in enumerate(pages)
                ])
                self.kwargs['arguments'] = arguments
                with patch('azure.cli.command_modules.appconfig.enhanced_feature.get_appconfig_feature_flag_client') as get_client:
                    client = get_client.return_value
                    client.list_feature_flags.return_value = ItemPaged(get_next, lambda response: response)

                    self.cmd('appconfig enhanced-feature-flag list --endpoint https://example.azconfig.io '
                             '--auth-mode login {arguments}',
                             checks=[self.check('length(@)', expected_count),
                                     self.check('[].name', [flag.name for flag in feature_flags[:expected_count]])])

                    client.list_feature_flags.assert_called_once_with(
                        name_filter=None, label_filter=None, tags_filter=None)
                    self.assertEqual(get_next.call_args_list,
                                     [call(None)] + [call(str(index)) for index in range(1, expected_pages)])


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
                 checks=[self.check('[0].name', entry_feature),
                         self.check('[0].label', entry_label)])

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

        # Delete when no enhanced feature flag matches is a no-op that returns an empty result
        self.cmd('appconfig enhanced-feature-flag delete --endpoint {endpoint} --auth-mode login --feature-name {feature_name} --label {label} -y',
                 checks=[self.is_empty()])
