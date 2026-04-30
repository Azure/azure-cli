# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.command_modules.appconfig._constants import SnapshotReferenceConstants
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix


class AppConfigSnapshotRefScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)

    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_kv_set_snapshot_reference(self, resource_group, location):
        store_name_prefix = get_resource_name_prefix('SnapRefTest')
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=24)
        store_location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': store_location,
            'rg': resource_group,
            'sku': sku
        })

        create_config_store(self, self.kwargs)

        entry_key = "MySnapshotRef"
        entry_label = "MyLabel"
        snapshot_name = "MySnapshot"

        self.kwargs.update({
            'key': entry_key,
            'label': entry_label,
            'snapshot_name': snapshot_name
        })

        # Set a snapshot reference
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --label {label} --snapshot-name {snapshot_name} -y',
                 checks=[self.check('contentType', SnapshotReferenceConstants.SNAPSHOT_REFERENCE_CONTENT_TYPE),
                         self.check('key', entry_key),
                         self.check('label', entry_label)])

        # Verify value contains correct snapshot_name JSON
        result = self.cmd('appconfig kv show -n {config_store_name} --key {key} --label {label}').get_output_in_json()
        value_data = json.loads(result['value'])
        assert value_data['snapshot_name'] == snapshot_name, "Snapshot name in value JSON should match"
        assert result['contentType'] == SnapshotReferenceConstants.SNAPSHOT_REFERENCE_CONTENT_TYPE

        # Update the snapshot reference to point to a different snapshot
        new_snapshot_name = "MySnapshot2"
        self.kwargs.update({'snapshot_name': new_snapshot_name})

        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --label {label} --snapshot-name {snapshot_name} -y',
                 checks=[self.check('contentType', SnapshotReferenceConstants.SNAPSHOT_REFERENCE_CONTENT_TYPE),
                         self.check('key', entry_key),
                         self.check('label', entry_label)])

        result = self.cmd('appconfig kv show -n {config_store_name} --key {key} --label {label}').get_output_in_json()
        value_data = json.loads(result['value'])
        assert value_data['snapshot_name'] == new_snapshot_name, "Snapshot name should be updated"

        # Set a snapshot reference with tags
        self.kwargs.update({
            'key': 'TaggedRef',
            'snapshot_name': 'TaggedSnapshot'
        })
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --snapshot-name {snapshot_name} --tags env=prod team=config -y',
                 checks=[self.check('contentType', SnapshotReferenceConstants.SNAPSHOT_REFERENCE_CONTENT_TYPE),
                         self.check('key', 'TaggedRef'),
                         self.check('tags.env', 'prod'),
                         self.check('tags.team', 'config')])

    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_kv_list_resolve_snapshot_references(self, resource_group, location):
        store_name_prefix = get_resource_name_prefix('SnapRefList')
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=24)
        store_location = 'eastus'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': store_location,
            'rg': resource_group,
            'sku': sku
        })

        create_config_store(self, self.kwargs)

        self.cmd('appconfig kv set -n {config_store_name} --key Color --value red -y')
        self.cmd('appconfig kv set -n {config_store_name} --key Size --value large -y')

        production_snapshot = "production-config-v1"
        production_filter = {"key": "*"}
        retention_period = 86400
        self.kwargs.update({
            'snapshot_name': production_snapshot,
            'filter': '\'{}\''.format(json.dumps(production_filter)),
            'retention_period': retention_period
        })
        self.cmd('appconfig snapshot create -n {config_store_name} -s {snapshot_name} --filters {filter} --retention-period {retention_period}')

        production_ref_key = "ProductionConfigRef"
        self.kwargs.update({'key': production_ref_key})
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --snapshot-name {snapshot_name} -y')

        # List without resolve returns the snapshot reference itself
        result = self.cmd('appconfig kv list -n {config_store_name} --key {key}').get_output_in_json()
        assert len(result) == 1
        assert result[0]['contentType'] == SnapshotReferenceConstants.SNAPSHOT_REFERENCE_CONTENT_TYPE

        # List with resolve returns key-values from the referenced snapshot
        result = self.cmd('appconfig kv list -n {config_store_name} --key {key} --resolve-snapshot-references').get_output_in_json()
        keys = [kv['key'] for kv in result]
        assert 'Color' in keys
        assert 'Size' in keys

        # Non-reference key-values are returned alongside resolved snapshot key-values
        self.cmd('appconfig kv set -n {config_store_name} --key Shape --value circle -y')
        result = self.cmd('appconfig kv list -n {config_store_name} --resolve-snapshot-references').get_output_in_json()
        result_keys = [kv['key'] for kv in result]
        assert 'Shape' in result_keys
        assert 'Color' in result_keys
        assert 'Size' in result_keys
        assert production_ref_key not in result_keys

        # Snapshot resolution does not override live-store values; both appear in sequence
        self.cmd('appconfig kv set -n {config_store_name} --key Color --value green -y')
        result = self.cmd('appconfig kv list -n {config_store_name} --resolve-snapshot-references').get_output_in_json()
        color_values = [kv['value'] for kv in result if kv['key'] == 'Color']
        assert 'green' in color_values
        assert 'red' in color_values

        # Multiple references to the same snapshot are expanded each time (duplicates allowed)
        production_ref_alias_key = "ProductionConfigRefAlias"
        self.kwargs.update({'key': production_ref_alias_key})
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --snapshot-name {snapshot_name} -y')
        result = self.cmd('appconfig kv list -n {config_store_name} --resolve-snapshot-references').get_output_in_json()
        resolved_keys = [kv['key'] for kv in result]
        assert resolved_keys.count('Color') >= 2
        assert resolved_keys.count('Size') >= 2

        # Multiple references with overlapping keys: both contributions appear in sequence
        self.cmd('appconfig kv set -n {config_store_name} --key Color --value blue --label staging -y')
        staging_snapshot = "staging-override-v1"
        staging_filter = {"key": "Color", "label": "staging"}
        self.kwargs.update({
            'snapshot_name': staging_snapshot,
            'filter': '\'{}\''.format(json.dumps(staging_filter))
        })
        self.cmd('appconfig snapshot create -n {config_store_name} -s {snapshot_name} --filters {filter} --retention-period {retention_period}')
        staging_ref_key = "StagingOverrideRef"
        self.kwargs.update({'key': staging_ref_key})
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --snapshot-name {snapshot_name} -y')
        result = self.cmd('appconfig kv list -n {config_store_name} --resolve-snapshot-references').get_output_in_json()
        color_values = [kv['value'] for kv in result if kv['key'] == 'Color']
        assert 'red' in color_values
        assert 'blue' in color_values
        assert 'green' in color_values

        # A reference to a non-existent snapshot is skipped; other kvs are still returned
        archived_ref_key = "ArchivedConfigRef"
        self.kwargs.update({'key': archived_ref_key})
        self.cmd('appconfig kv set-snapshot-reference -n {config_store_name} --key {key} --snapshot-name nonexistent-snapshot -y')
        result = self.cmd('appconfig kv list -n {config_store_name} --resolve-snapshot-references').get_output_in_json()
        result_keys = [kv['key'] for kv in result]
        assert archived_ref_key not in result_keys
        assert 'Shape' in result_keys
