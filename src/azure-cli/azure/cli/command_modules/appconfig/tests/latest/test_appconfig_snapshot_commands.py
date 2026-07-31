# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.azclierror import ResourceNotFoundError as CliResourceNotFoundError, MutuallyExclusiveArgumentError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix, get_test_resource_group, register_appconfig_query_matcher, register_appconfig_recording_processors

class AppConfigSnapshotLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)
        register_appconfig_query_matcher(self)
        register_appconfig_recording_processors(self)


    @AllowLargeResponse()
    # Uses Entra ID auth (store created with local auth disabled); target a resource group where the
    # recording principal holds "App Configuration Data Owner". Override via AZURE_CLI_APPCONFIG_TEST_RG.
    def test_azconfig_snapshot_mgmt(self):
        store_name_prefix = get_resource_name_prefix('snapshotstore') 
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=24)
        snapshot_name = "TestSnapshot"
        store_location = 'francecentral'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'snapshot_name': snapshot_name,
            'rg_loc': store_location,
            'rg': get_test_resource_group(),
            'sku': sku,
            'retention_days': 1,
            'enable_purge_protection': False,
            'endpoint': 'https://' + config_store_name + '.azconfig.io'
        })

        create_config_store(self, self.kwargs, disable_local_auth=True)

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

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key2,
            'value': entry_value2,
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key2),
                         self.check('value', entry_value2),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key3,
            'value': entry_value3,
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key3),
                         self.check('value', entry_value3),
                         self.check('label', dev_label)])

        # Create a snapshot of all key-values that begin with the prefix 'Test'
        filter_dict = { "key": "Test*", "label": dev_label, "tags": [] }
        retention_period = 3600 # Set retention period of 1 hour
        self.kwargs.update({
            'filter': '\'{}\''.format(json.dumps(filter_dict)),
            'retention_period': retention_period
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter} --retention-period {retention_period} --composition-type key_label --tags tag1=value1',
                 checks=[self.check('itemsCount', 2),
                         self.check('status', 'ready')])


        # Test showing created snapshot
        created_snapshot = self.cmd('appconfig snapshot show --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --fields name status items_count filters').get_output_in_json()

        self.assertEqual(created_snapshot['items_count'], 2)
        self.check(created_snapshot['status'], 'ready')
        self.assertDictEqual(created_snapshot['filters'][0], filter_dict)
        self.assertRaises(KeyError, lambda: created_snapshot['created'])

        # Test listing snapshots
        created_snapshots = self.cmd('appconfig snapshot list --snapshot-name {snapshot_name} --endpoint {endpoint} --auth-mode login --fields name status items_count filters').get_output_in_json()
        self.assertEqual(created_snapshots[0]['items_count'], 2)
        self.assertEqual(created_snapshots[0]['status'], 'ready')
        self.assertDictEqual(created_snapshots[0]['filters'][0], filter_dict)

        # Test snapshot archive
        archived_snapshot = self.cmd('appconfig snapshot archive --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name}').get_output_in_json()
        self.assertIsNotNone(archived_snapshot['expires'])
        self.assertEqual(archived_snapshot['status'], 'archived')
        active_snapshots = self.cmd('appconfig snapshot list --endpoint {endpoint} --auth-mode login --status ready').get_output_in_json()
        self.assertEqual(len(active_snapshots), 0)

        # Test snapshot recovery
        self.cmd('appconfig snapshot recover --endpoint {endpoint} --auth-mode login -s {snapshot_name}',
                                     checks=[self.check('itemsCount', 2),
                                             self.check('status', 'ready'),
                                             self.check('expires', None),])
        archived_snapshots = self.cmd('appconfig snapshot list --endpoint {endpoint} --auth-mode login --status archived').get_output_in_json()
        self.assertEqual(len(archived_snapshots), 0)

        # Test listing snapshot kvs
        kvs = self.cmd('appconfig kv list --endpoint {endpoint} --auth-mode login --snapshot {snapshot_name}').get_output_in_json()
        assert len(kvs) == 2

        # Test error returned for listing kvs in non-existent snapshot
        non_existent_snapshot_name = "non_existent_snapshot"

        self.kwargs.update({
            'snapshot_name': non_existent_snapshot_name
        })

        with self.assertRaisesRegex(CliResourceNotFoundError, f'No snapshot with name \'{non_existent_snapshot_name}\' was found.'):
            self.cmd('appconfig kv list --endpoint {endpoint} --auth-mode login --snapshot {snapshot_name}')

        # Test snapshot import/export
        config_store_2_name = self.create_random_name(prefix=store_name_prefix, length=24)

        self.kwargs.update({
            'config_store_name': config_store_2_name,
            'snapshot_name': snapshot_name,
            'dest_endpoint': 'https://' + config_store_2_name + '.azconfig.io'
        })

        create_config_store(self, self.kwargs, disable_local_auth=True)

        # Export snapshot kvs to store
        self.cmd('appconfig kv export -d appconfig --endpoint {endpoint} --auth-mode login --dest-endpoint {dest_endpoint} --dest-auth-mode login --snapshot {snapshot_name} -y')

        # Export with skip-features should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--snapshot' cannot be specified with '--key',  '--label', '--skip-keyvault' or '--skip-features' arguments."):
            self.cmd('appconfig kv export -d appconfig --endpoint {endpoint} --auth-mode login --dest-endpoint {dest_endpoint} --dest-auth-mode login --snapshot {snapshot_name} --skip-features -y')

        # Export with skip-keyvault should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--snapshot' cannot be specified with '--key',  '--label', '--skip-keyvault' or '--skip-features' arguments."):
            self.cmd('appconfig kv export -d appconfig --endpoint {endpoint} --auth-mode login --dest-endpoint {dest_endpoint} --dest-auth-mode login --snapshot {snapshot_name} --skip-keyvault -y')

        # List snapshots in store
        dest_kvs = self.cmd('appconfig kv list --endpoint {dest_endpoint} --auth-mode login --key * --label *').get_output_in_json()
        self.assertEqual(len(dest_kvs), 2)

        # Delete all kvs
        self.cmd('appconfig kv delete --endpoint {dest_endpoint} --auth-mode login --key * --label * -y')

        # Import snapshot kvs from source
        self.cmd('appconfig kv import -s appconfig --endpoint {dest_endpoint} --auth-mode login --src-endpoint {endpoint} --src-auth-mode login --src-snapshot {snapshot_name} -y')

        # Import with skip-features should fail
        with self.assertRaisesRegex(MutuallyExclusiveArgumentError, "'--src-snapshot' cannot be specified with '--src-key', '--src-label', or '--skip-features' arguments."):
            self.cmd('appconfig kv import -s appconfig --endpoint {dest_endpoint} --auth-mode login --src-endpoint {endpoint} --src-auth-mode login --src-snapshot {snapshot_name} --skip-features -y')

        # List snapshots in store
        current_kvs = self.cmd('appconfig kv list --endpoint {dest_endpoint} --auth-mode login --key * --label *').get_output_in_json()
        self.assertEqual(len(current_kvs), 2)


    @AllowLargeResponse()
    # Uses Entra ID auth (store created with local auth disabled); target a resource group where the
    # recording principal holds "App Configuration Data Owner". Override via AZURE_CLI_APPCONFIG_TEST_RG.
    def test_azconfig_snapshot_filtering(self):
        store_name_prefix = get_resource_name_prefix('snapshotfilters') 
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=36)
        store_location = 'francecentral'
        sku = 'standard'

        self.kwargs.update({
            'config_store_name': config_store_name,
            'rg_loc': store_location,
            'rg': get_test_resource_group(),
            'sku': sku,
            'retention_days': 1,
            'enable_purge_protection': False,
            'endpoint': 'https://' + config_store_name + '.azconfig.io'
        })

        create_config_store(self, self.kwargs, disable_local_auth=True)

        # # Filter by tags test

        # Set key-value with 5 tags
        key_with_tags = "KeyWithTags"
        label_with_tags = "labelWithTags"
        retention_period = 3600 # Set retention period of 1 hour
        tags = {
            "tag1": "value1",
            "tag2": "value2",
            "tag3": "value3",
            "tag4": "value4",
            "tag5": "value5"
        }
        tags_list = [f"{k}={v}" for k, v in tags.items()]
        tags_str = ' '.join(tags_list)

        self.kwargs.update({
            'key': key_with_tags + "1",
            'label': label_with_tags,
            'tags': tags_str,
            'retention_period': retention_period
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --label {label} --tags {tags} -y',
             checks=[self.check('key', key_with_tags + "1"),
             self.check('label', label_with_tags),
            self.check('tags', tags)])

        # Create snapshot with 5 tags filter
        key_with_tags_filter = key_with_tags + "*"
        filter_with_tags = { "key": key_with_tags_filter, "label": label_with_tags, "tags": tags_list }
        self.kwargs.update({
            'filter_with_tags': '\'{}\''.format(json.dumps(filter_with_tags)),
            'snapshot_name': "TestSnapshotWith5Tags"
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter_with_tags} --retention-period {retention_period} --composition-type key_label',
             checks=[self.check('itemsCount', 1),
                 self.check('status', 'ready')])

        # Set key-value with tag1 only
        tag1_dict = {"tag1": "value1"}
        tag1_list = [f"{k}={v}" for k, v in tag1_dict.items()]
        tag1 = ' '.join(tag1_list)
        self.kwargs.update({
            'key': key_with_tags + "2",
            'label': label_with_tags,
            'tag1': tag1
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --label {label} --tags {tag1} -y',
             checks=[self.check('key', key_with_tags + "2"),
                 self.check('label', label_with_tags),
                 self.check('tags', tag1_dict)])

        # Create snapshot with tag1 filter
        filter_with_tag1 = { "key": key_with_tags_filter, "label": label_with_tags, "tags": tag1_list }
        self.kwargs.update({
            'filter_with_tag1': '\'{}\''.format(json.dumps(filter_with_tag1)),
            'snapshot_name': "TestSnapshotWith1Tag"
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter_with_tag1} --retention-period {retention_period} --composition-type key_label',
             checks=[self.check('itemsCount', 2),
                 self.check('status', 'ready')])

        # Set key-value with empty tag value
        empty_tag_value_dict = {"tag1": ""}
        tag_with_empty_value_list = [f"{k}={v}" for k, v in empty_tag_value_dict.items()]
        tag_with_empty_value = ' '.join(tag_with_empty_value_list)
        self.kwargs.update({
            'key': key_with_tags + "3",
            'label': label_with_tags,
            'tag_with_empty_value': tag_with_empty_value
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --label {label} --tags {tag_with_empty_value} -y',
             checks=[self.check('key', key_with_tags + "3"),
                 self.check('label', label_with_tags),
                 self.check('tags', empty_tag_value_dict)])

        # Create snapshot with empty tag value filter
        filter_with_empty_tag_value = { "key": key_with_tags_filter, "label": label_with_tags, "tags": tag_with_empty_value_list }
        self.kwargs.update({
            'filter_with_empty_tag_value': '\'{}\''.format(json.dumps(filter_with_empty_tag_value)),
            'snapshot_name': "TestSnapshotWithEmptyTagValue"
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter_with_empty_tag_value} --retention-period {retention_period} --composition-type key_label',
             checks=[self.check('itemsCount', 1),
             self.check('status', 'ready')])

        # Create snapshot with key-values with any tags
        filter_all_kvs = { "key": key_with_tags_filter, "label": label_with_tags }
        self.kwargs.update({
            'filter_all_kvs': '\'{}\''.format(json.dumps(filter_all_kvs)),
            'snapshot_name': "TestSnapshotWithAllKVs"
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter_all_kvs} --retention-period {retention_period} --composition-type key_label',
             checks=[self.check('itemsCount', 3),
                 self.check('status', 'ready')])

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

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key),
                         self.check('value', entry_value),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key2,
            'value': entry_value2,
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key2),
                         self.check('value', entry_value2),
                         self.check('label', dev_label)])

        self.kwargs.update({
            'key': entry_key3,
            'value': entry_value3,
        })

        self.cmd('appconfig kv set --endpoint {endpoint} --auth-mode login --key {key} --value {value} --label {label} -y',
                 checks=[self.check('key', entry_key3),
                         self.check('value', entry_value3),
                         self.check('label', dev_label)])

        # Create a snapshot of all key-values that begin with the prefix 'Test'
        filter_dict = { "key": "Test*", "label": dev_label }
        self.kwargs.update({
            'filter': '\'{}\''.format(json.dumps(filter_dict)),
            'retention_period': retention_period,
            'snapshot_name': "TestSnapshotWithPrefix"
        })

        self.cmd('appconfig snapshot create --endpoint {endpoint} --auth-mode login --snapshot-name {snapshot_name} --filters {filter} --retention-period {retention_period} --composition-type key_label --tags tag1=value1',
                 checks=[self.check('itemsCount', 2),
                         self.check('status', 'ready')])
