# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from datetime import datetime, timedelta, timezone

from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from azure.cli.command_modules.backup.tests.latest.test_sql_commands import (
    CrossRegionRestoreAccessTokenReplacer,
)


class SqlInstanceSnapshotTests(ScenarioTest):
    # Restore targets must be disposable, with approved, unused target volumes and database names.
    fixture = {
        'sub': '80abcfe3-b410-42b2-983f-df23cba781dc',
        'rg': 'chandrikarg',
        'vault': 'testolr',
        'container': 'VMAppContainer;compute;chandrikarg;testvm2-iws',
        'item': 'SQLInstance;mssqlserver',
        'policy_snapshot_rg': 'chandrikarg',
        'policy_identity_id': (
            '/subscriptions/{sub}/resourceGroups/chandrikarg/providers/'
            'Microsoft.ManagedIdentity/userAssignedIdentities/testsqlmi2'),
        'alr': {
            'target_rg': 'chandrikarg',
            'target_vault': 'testolr',
            'target_container': 'VMAppContainer;compute;chandrikarg;testvm1-iws',
            'target_server': 'TestVM1-iws',
            'target_instance': 'mssqlserver',
            'target_item': '*_cli_snap_20261024',
            'restore_snapshot_rg': 'chandrikarg',
            'restore_identity_id': (
                '/subscriptions/{sub}/resourceGroups/chandrikarg/providers/'
                'Microsoft.ManagedIdentity/userAssignedIdentities/testsqlmi2'),
            'volume_mappings': {'F:\\': 'X:\\', 'G:\\': 'Y:\\'},
        },
        'crr_source': {
            'sub': '935cff54-7d3c-49cc-a1e0-a9aa8bf006f5',
            'rg': 'abhinksql3ccy',
            'vault': 'abhinksql3ccy',
            'container': 'VMAppContainer;compute;abhinksql3ccy;abhinksql3ccy',
            'item': 'SQLInstance;mssqlserver',
        },
        'crr': {
            'target_rg': 'abhinksqlRg',
            'target_vault': 'abhinksql',
            'target_container': 'VMAppContainer;Compute;abhinksqlRg;abhinksql',
            'target_server': 'abhinksql',
            'target_instance': 'mssqlserver',
            'restore_snapshot_rg': 'abhinksqlrg',
            'restore_identity_id': (
                '/subscriptions/{sub}/resourceGroups/abhinksqlRg/providers/'
                'Microsoft.ManagedIdentity/userAssignedIdentities/sqlmi'),
            'volume_mappings': {'F:\\': 'X:\\', 'G:\\': 'Y:\\'},
        },
    }

    def setUp(self):
        super().setUp()
        self.kwargs.update(self.fixture)
        if self._testMethodName == 'test_backup_sql_instance_snapshot_crr_attach':
            self.kwargs.update(self.fixture['crr_source'])
        subscription = self.get_subscription_id()
        if self.in_recording or self.is_live:
            self.assertEqual(self.kwargs['sub'], subscription, 'Select the fixture subscription before recording.')
        self.kwargs['sub'] = subscription
        self.kwargs['policy_identity_id'] = self.kwargs['policy_identity_id'].format(sub=subscription)
        self.kwargs['vault_args'] = (
            '--subscription "{sub}" -g "{rg}" -v "{vault}"'.format(**self.kwargs))
        self.kwargs['instance_args'] = (
            '{vault_args} -c "{container}" --item-name "{item}" '
            '--backup-management-type AzureWorkload --workload-type SQLInstance'.format(**self.kwargs))
        self.recording_processors.insert(0, CrossRegionRestoreAccessTokenReplacer())

    def _write_json(self, prefix, value):
        path = os.path.join(os.path.dirname(__file__), self.create_random_name(prefix, 48) + '.json')
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(value, stream)
        self.addCleanup(os.remove, path)
        return path

    def _wait_for_job(self, job, operation, use_secondary_region=False):
        self.assertEqual(operation, job['properties']['operation'])
        self.assertTrue(job['name'])
        self.kwargs['job'] = job['name']
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        self.cmd('backup job wait {vault_args} -n "{job}" {secondary} --timeout 7200')
        self.cmd('backup job show {vault_args} -n "{job}" {secondary}', checks=[
            self.check('properties.operation', 'Restore (SnapshotFull)' if operation == 'Restore' else operation),
            self.check('properties.status', 'Completed'),
        ])

    def _snapshot_recovery_point(self, use_secondary_region=False):
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        points = self.cmd(
            'backup recoverypoint list {instance_args} --restore-point-query-type Snapshot {secondary}'
        ).get_output_in_json()
        self.assertTrue(points, 'The SQL instance must have a snapshot recovery point in the requested region.')
        self.assertTrue(all(point['properties']['type'] == 'SnapshotFull' for point in points))
        time_field = 'recoveryPointTimeInUtc' if use_secondary_region else 'recoveryPointTimeInUTC'
        self.kwargs['rp'] = max(
            points, key=lambda point: datetime.fromisoformat(
                point['properties'][time_field].replace('Z', '+00:00')))['name']
        point = self.cmd(
            'backup recoverypoint show {instance_args} -n "{rp}" {secondary}', checks=[
                self.check('name', '{rp}'),
                self.check('properties.type', 'SnapshotFull'),
            ]).get_output_in_json()
        self.assertTrue(point['properties']['extendedInfo']['snapshotRecoveryPointInfo']['sourceFilesystemInfo'])
        return point

    def _restore_snapshot(self, target, recovery_mode, use_secondary_region=False):
        target = dict(target, restore_identity_id=target['restore_identity_id'].format(sub=self.kwargs['sub']))
        self.kwargs.update(target)
        self._snapshot_recovery_point(use_secondary_region)
        self.kwargs['recovery_mode'] = recovery_mode
        self.kwargs['target_item_arg'] = (
            '--target-item-name "{target_item}"'.format(**target)
            if recovery_mode == 'SnapshotAttachAndRecover' else '')
        config = self.cmd(
            'backup recoveryconfig show {instance_args} --rp-name "{rp}" '
            '--restore-mode AlternateWorkloadRestore --recovery-mode {recovery_mode} '
            '--target-container-name "{target_container}" --target-server-name "{target_server}" '
            '--target-server-type SQLInstance --target-instance-name "{target_instance}" '
            '--target-resource-group "{target_rg}" --target-vault-name "{target_vault}" '
            '--snapshot-rg "{restore_snapshot_rg}" --identity-arm-id "{restore_identity_id}" '
            '{target_item_arg}'
        ).get_output_in_json()
        self.assertEqual('AlternateLocation', config['restore_mode'])
        self.assertEqual(recovery_mode, config['recovery_mode'])
        self.assertEqual('SQLInstance', config['workload_type'])
        self.assertEqual(self.kwargs['rp'], config['recovery_point_id'])
        self.assertEqual(self.kwargs['rp'], config['base_snapshot_recovery_point_id'])
        self.assertEqual(target['restore_snapshot_rg'], config['snapshot_instance_resource_group'])
        self.assertEqual(target['restore_identity_id'].lower(), config['identity_arm_id'].lower())
        self.assertTrue(config['container_id'].lower().endswith('/' + target['target_container'].lower()))
        self.assertEqual([], config['disks_to_detach_on_clash'])
        self.assertFalse(config['no_recovery_mode'])
        if recovery_mode == 'SnapshotAttachAndRecover':
            instance, database = config['database_name'].split('/', 1)
            self.assertEqual(target['target_instance'].lower(), instance.lower())
            self.assertEqual(target['target_item'], database)
        mappings = config['target_physical_path']
        self.assertTrue(mappings, 'Snapshot metadata must produce volume mappings.')
        self.assertEqual(set(target['volume_mappings']), {mapping['source_path'] for mapping in mappings})
        for mapping in mappings:
            self.assertEqual('Data' if recovery_mode == 'SnapshotAttachAndRecover' else 'DiskDrives',
                             mapping['mapping_type'])
            mapping['target_path'] = target['volume_mappings'][mapping['source_path']]
            self.assertTrue(mapping['target_path'])
        self.kwargs['config_file'] = self._write_json('cli-sql-instance-restore-', config)
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        job = self.cmd(
            'backup restore restore-azurewl {vault_args} --recovery-config "{config_file}" {secondary}'
        ).get_output_in_json()
        self._wait_for_job(job, 'CrossRegionRestore' if use_secondary_region else 'Restore', use_secondary_region)

    @AllowLargeResponse()
    def test_backup_sql_instance_snapshot_log_policy(self):
        identity = self.cmd(
            'identity show --subscription "{sub}" --ids "{policy_identity_id}"'
        ).get_output_in_json()
        self.assertTrue(identity['clientId'])
        self.assertTrue(identity['principalId'])
        schedule_time = '2026-10-15T02:00:00Z'
        policy = {
            'properties': {
                'backupManagementType': 'AzureWorkload',
                'workLoadType': 'SQLInstance',
                'vmWorkloadPolicyType': 'SnapshotV2',
                'settings': {'timeZone': 'UTC', 'issqlcompression': False, 'isCompression': False},
                'subProtectionPolicy': [
                    {
                        'policyType': 'SnapshotFull',
                        'schedulePolicy': {
                            'schedulePolicyType': 'SimpleSchedulePolicy',
                            'scheduleRunFrequency': 'Daily',
                            'scheduleRunTimes': [schedule_time],
                        },
                        'retentionPolicy': {
                            'retentionPolicyType': 'LongTermRetentionPolicy',
                            'dailySchedule': {
                                'retentionTimes': [schedule_time],
                                'retentionDuration': {'count': 7, 'durationType': 'Days'},
                            },
                        },
                        'snapshotBackupAdditionalDetails': {
                            'instantRpRetentionRangeInDays': 5,
                            'instantRPDetails': self.kwargs['policy_snapshot_rg'],
                            'userAssignedManagedIdentityDetails': {
                                'identityArmId': identity['id'],
                                'identityName': identity['name'],
                                'userAssignedIdentityProperties': {
                                    'clientId': identity['clientId'],
                                    'principalId': identity['principalId'],
                                },
                            },
                        },
                    },
                    {
                        'policyType': 'Log',
                        'schedulePolicy': {
                            'schedulePolicyType': 'LogSchedulePolicy',
                            'scheduleFrequencyInMins': 60,
                        },
                        'retentionPolicy': {
                            'retentionPolicyType': 'SimpleRetentionPolicy',
                            'retentionDuration': {'count': 7, 'durationType': 'Days'},
                        },
                    },
                ],
            },
        }
        self.kwargs['policy_file'] = self._write_json('cli-sql-instance-policy-', policy)
        self.kwargs['policy_name'] = self.create_random_name('cli-sql-snapshot-log-', 32)
        self.cmd(
            'backup policy create {vault_args} -n "{policy_name}" --backup-management-type AzureWorkload '
            '--workload-type SQLInstance --policy "{policy_file}"', checks=[
                self.check('name', '{policy_name}'),
                self.check('properties.workLoadType', 'SQLInstance'),
                self.check('properties.vmWorkloadPolicyType', 'SnapshotV2'),
            ])
        self.addCleanup(self.cmd, 'backup policy delete {vault_args} -n "{policy_name}"')
        saved = self.cmd('backup policy show {vault_args} -n "{policy_name}"', checks=[
            self.check('properties.backupManagementType', 'AzureWorkload'),
            self.check('properties.workLoadType', 'SQLInstance'),
            self.check('properties.vmWorkloadPolicyType', 'SnapshotV2'),
            self.check('length(properties.subProtectionPolicy)', 2),
        ]).get_output_in_json()
        subpolicies = {entry['policyType']: entry for entry in saved['properties']['subProtectionPolicy']}
        self.assertEqual({'SnapshotFull', 'Log'}, set(subpolicies))
        snapshot = subpolicies['SnapshotFull']
        self.assertEqual('Daily', snapshot['schedulePolicy']['scheduleRunFrequency'])
        self.assertEqual({'count': 7, 'durationType': 'Days'},
                         snapshot['retentionPolicy']['dailySchedule']['retentionDuration'])
        details = snapshot['snapshotBackupAdditionalDetails']
        self.assertEqual(5, details['instantRpRetentionRangeInDays'])
        self.assertEqual(self.kwargs['policy_snapshot_rg'], details['instantRpDetails'])
        self.assertEqual(identity['id'].lower(),
                         details['userAssignedManagedIdentityDetails']['identityArmId'].lower())
        self.assertEqual(60, subpolicies['Log']['schedulePolicy']['scheduleFrequencyInMins'])
        self.assertEqual({'count': 7, 'durationType': 'Days'},
                         subpolicies['Log']['retentionPolicy']['retentionDuration'])

    @AllowLargeResponse()
    def test_backup_sql_instance_snapshot_full_backup_now(self):
        self.cmd('backup item show {vault_args} -c "{container}" -n "{item}" '
                 '--backup-management-type AzureWorkload --workload-type SQLInstance', checks=[
            self.check('properties.workloadType', 'SQLInstance'),
            self.check('properties.protectionState', 'Protected'),
        ])
        before = self.cmd(
            'backup recoverypoint list {instance_args} --restore-point-query-type Snapshot'
        ).get_output_in_json()
        self.kwargs['retain_until'] = (
            datetime.now(timezone.utc) + timedelta(days=30)).strftime('%d-%m-%Y-%H:%M:%S')
        job = self.cmd(
            'backup protection backup-now {instance_args} --backup-type SnapshotFull '
            '--retain-until "{retain_until}"'
        ).get_output_in_json()
        self._wait_for_job(job, 'Backup (SnapshotFull)')
        point = self._snapshot_recovery_point()
        self.assertNotIn(point['name'], {previous['name'] for previous in before},
                         'A completed on-demand backup must create a new snapshot recovery point.')

    @AllowLargeResponse()
    def test_backup_sql_instance_snapshot_alr_attach_and_recover(self):
        self._restore_snapshot(self.fixture['alr'], 'SnapshotAttachAndRecover')

    @AllowLargeResponse()
    def test_backup_sql_instance_snapshot_crr_attach(self):
        self._restore_snapshot(self.fixture['crr'], 'SnapshotAttach', use_secondary_region=True)
