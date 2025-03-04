# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

import json

from azure.cli.testsdk import (ResourceGroupPreparer, ScenarioTest)
from azure.cli.testsdk.scenario_tests import AllowLargeResponse
from azure.cli.core.azclierror import ResourceNotFoundError as CliResourceNotFoundError, MutuallyExclusiveArgumentError
from azure.cli.command_modules.appconfig.tests.latest._test_utils import create_config_store, CredentialResponseSanitizer, get_resource_name_prefix

class AppConfigSnapshotLiveScenarioTest(ScenarioTest):

    def __init__(self, *args, **kwargs):
        kwargs["recording_processors"] = kwargs.get("recording_processors", []) + [CredentialResponseSanitizer()]
        super().__init__(*args, **kwargs)


    @ResourceGroupPreparer(parameter_name_for_location='location')
    @AllowLargeResponse()
    def test_azconfig_snapshot_mgmt(self, resource_group, location):
        store_name_prefix = get_resource_name_prefix('SnapshotStore') 
        config_store_name = self.create_random_name(prefix=store_name_prefix, length=36)
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

        create_config_store(self, self.kwargs)

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
        config_store_2_name = self.create_random_name(prefix=store_name_prefix, length=36)

        self.kwargs.update({
            'config_store_name': config_store_2_name,
            'snapshot_name': snapshot_name,
        })

        create_config_store(self, self.kwargs)

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
