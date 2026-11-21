# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
from datetime import datetime, timedelta, timezone

from azure.cli.testsdk.scenario_tests import AllowLargeResponse

from azure.cli.command_modules.backup.tests.latest.test_sql_commands import (
    CrossRegionRestoreAccessTokenReplacer,
    SqlBackupScenarioTest,
)
from .sql_instance_test_setup import SqlInstanceSnapshotPreparer


class SqlInstanceSnapshotTests(SqlBackupScenarioTest):
    crr_fixture = {
        'sub': '935cff54-7d3c-49cc-a1e0-a9aa8bf006f5',
        'rg': 'abhinksql3ccy',
        'vault': 'abhinksql3ccy',
        'container': 'VMAppContainer;compute;abhinksql3ccy;abhinksql3ccy',
        'item': 'SQLInstance;mssqlserver',
        'target': {
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
        self.recording_processors.insert(0, CrossRegionRestoreAccessTokenReplacer())
        if self._testMethodName == 'test_backup_sql_instance_snapshot_crr_attach':
            self.kwargs.update(self.crr_fixture)
            subscription = self.get_subscription_id()
            if self.in_recording or self.is_live:
                self.assertEqual(self.kwargs['sub'], subscription, 'Select the fixture subscription before recording.')
            self.kwargs['sub'] = subscription
            self.kwargs['vault_args'] = '--subscription "{sub}" -g "{rg}" -v "{vault}"'.format(**self.kwargs)
            self.kwargs['instance_args'] = (
                '{vault_args} -c "{container}" --item-name "{item}" '
                '--backup-management-type AzureWorkload --workload-type SQLInstance'.format(**self.kwargs))

    def _write_json(self, prefix, value):
        path = os.path.join(os.path.dirname(__file__), self.create_random_name(prefix, 48) + '.json')
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(value, stream)
        self.addCleanup(os.remove, path)
        return path

    def _wait_for_job(self, job, operation, use_secondary_region=False, completed_operation=None):
        self.assertEqual(operation, job['properties']['operation'])
        self.assertTrue(job['name'])
        self.kwargs['job'] = job['name']
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        self.cmd('backup job wait {vault_args} -n "{job}" {secondary} --timeout 7200')
        self.cmd('backup job show {vault_args} -n "{job}" {secondary}', checks=[
            self.check('properties.operation', completed_operation or operation),
            self.check('properties.status', 'Completed'),
        ])

    def _snapshot_recovery_point(self, use_secondary_region=False, latest_only=False,
                                 workload='SQLInstance', source_item=None):
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        self.kwargs['recovery_args'] = (
            '{vault_args} -c "{container}" --item-name "{source_item}" '
            '--backup-management-type AzureWorkload --workload-type {workload}'.format(
                **dict(self.kwargs, source_item=source_item or self.kwargs['item'], workload=workload)))
        latest_arg = ' --get-latest-recovery-point-only true' if latest_only else ''
        points = self.cmd(
            'backup recoverypoint list {recovery_args} --restore-point-query-type Snapshot {secondary}' + latest_arg
        ).get_output_in_json()
        self.assertTrue(points, 'The SQL instance must have a snapshot recovery point in the requested region.')
        if latest_only:
            self.assertEqual(1, len(points), 'The latest-only query must return exactly one snapshot.')
        self.assertTrue(all(point['properties']['type'] == 'SnapshotFull' for point in points))
        time_field = 'recoveryPointTimeInUtc' if use_secondary_region else 'recoveryPointTimeInUTC'
        self.kwargs['rp'] = max(
            points, key=lambda point: datetime.fromisoformat(
                point['properties'][time_field].replace('Z', '+00:00')))['name']
        point = self.cmd(
            'backup recoverypoint show {recovery_args} -n "{rp}" {secondary}', checks=[
                self.check('name', '{rp}'),
                self.check('properties.type', 'SnapshotFull'),
            ]).get_output_in_json()
        self.assertTrue(point['properties']['extendedInfo']['snapshotRecoveryPointInfo']['sourceFilesystemInfo'])
        return point

    def _restore_snapshot(self, target, recovery_mode, use_secondary_region=False, log_point_in_time=None,
                          workload='SQLInstance', source_item=None, latest_only=False, completed_operation=None):
        target = dict(target, restore_identity_id=target['restore_identity_id'].format(sub=self.kwargs['sub']))
        self.kwargs.update(target)
        if log_point_in_time is None:
            self._snapshot_recovery_point(use_secondary_region, latest_only, workload, source_item)
        self.kwargs['recovery_mode'] = recovery_mode
        self.kwargs['point_in_time_arg'] = (
            '--log-point-in-time "{}"'.format(log_point_in_time) if log_point_in_time is not None else '')
        self.kwargs['target_item_arg'] = (
            '--target-item-name "{target_item}"'.format(**target)
            if recovery_mode == 'SnapshotAttachAndRecover' else '')
        config = self.cmd(
            'backup recoveryconfig show {recovery_args} --rp-name "{rp}" '
            '--restore-mode AlternateWorkloadRestore --recovery-mode {recovery_mode} '
            '--target-container-name "{target_container}" --target-server-name "{target_server}" '
            '--target-server-type SQLInstance --target-instance-name "{target_instance}" '
            '--target-resource-group "{target_rg}" --target-vault-name "{target_vault}" '
            '--snapshot-rg "{restore_snapshot_rg}" --identity-arm-id "{restore_identity_id}" '
            '{target_item_arg} {point_in_time_arg}'
        ).get_output_in_json()
        self.assertEqual('AlternateLocation', config['restore_mode'])
        self.assertEqual(recovery_mode, config['recovery_mode'])
        self.assertEqual('SQLDataBase' if workload == 'MSSQL' else workload, config['workload_type'])
        self.assertEqual(self.kwargs['rp'], config['recovery_point_id'])
        self.assertEqual(self.kwargs['rp'], config['base_snapshot_recovery_point_id'])
        self.assertEqual(log_point_in_time, config['log_point_in_time'])
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
            self.assertEqual('Data' if recovery_mode == 'SnapshotAttachAndRecover' and log_point_in_time is None
                             else 'DiskDrives',
                             mapping['mapping_type'])
            mapping['target_path'] = target['volume_mappings'][mapping['source_path']]
            self.assertTrue(mapping['target_path'])
        self.kwargs['config_file'] = self._write_json('cli-sql-instance-restore-', config)
        self.kwargs['secondary'] = '--use-secondary-region' if use_secondary_region else ''
        job = self.cmd(
            'backup restore restore-azurewl {vault_args} --recovery-config "{config_file}" {secondary}'
        ).get_output_in_json()
        operation = 'CrossRegionRestore' if use_secondary_region else 'Restore'
        completed_operation = completed_operation or (
            'Restore (Log)' if log_point_in_time is not None else 'Restore (SnapshotFull)')
        self._wait_for_job(job, operation, use_secondary_region, completed_operation=completed_operation)

    def _create_snapshot_policy(self, identity):
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
                            'scheduleFrequencyInMins': 15,
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
        self.assertEqual(15, subpolicies['Log']['schedulePolicy']['scheduleFrequencyInMins'])
        self.assertEqual({'count': 7, 'durationType': 'Days'},
                         subpolicies['Log']['retentionPolicy']['retentionDuration'])
        return saved

    @AllowLargeResponse()
    @SqlInstanceSnapshotPreparer()
    def test_backup_sql_instance_snapshot_primary_region(self, snapshot_environment):
        self._configure_snapshot_protection(snapshot_environment)
        self._backup_snapshot()
        snapshot_environment.run_sql(
            self.kwargs['source_vm_rg'], self.kwargs['protection_server'], 'Write')
        self.kwargs['database_item'] = self._child_items()[0]['name']
        job = self.cmd(
            'backup protection backup-now {vault_args} -c "{container}" -i "{database_item}" '
            '--backup-management-type AzureWorkload --workload-type MSSQL --backup-type Log'
        ).get_output_in_json()
        self.assertTrue(job['properties']['operation'].startswith('Backup'))
        self._wait_for_job(job, job['properties']['operation'])
        self._restore_snapshot(snapshot_environment.target, 'SnapshotAttachAndRecover')
        point = self._snapshot_recovery_point(latest_only=True)
        point_in_time = self._snapshot_log_point(point)
        self.assertIsNotNone(point_in_time,
                             'Both child databases must have a common post-snapshot PIT. '
                             'No additional log backup or coverage wait is performed.')
        target = self._second_restore_target(snapshot_environment)
        snapshot_environment.run_sql(target['target_vm_rg'], target['target_server'], 'SecondTarget')
        self._restore_snapshot(
            target, 'SnapshotAttachAndRecover', log_point_in_time=point_in_time.strftime('%d-%m-%Y-%H:%M:%S'))
        snapshot_environment.delete_backup_data(verify=True)

    @AllowLargeResponse()
    def test_backup_sql_instance_snapshot_crr_attach(self):
        self._restore_snapshot(
            self.crr_fixture['target'], 'SnapshotAttach', use_secondary_region=True,
            completed_operation='CrossRegionRestore')

    def _second_restore_target(self, environment):
        return dict(environment.target, target_item='*_' + self.create_random_name('cli_second_', 24),
                    volume_mappings={'F:\\': 'U:\\', 'G:\\': 'V:\\'})

    def _configure_snapshot_protection(self, environment):
        policy = self._create_snapshot_policy(environment.identity)
        self.kwargs['protection_policy'] = policy['name']
        self._enable_snapshot_protection(environment.child_databases)
        children = self._child_items()
        self.assertEqual(set(environment.child_databases),
                         {item['properties']['friendlyName'] for item in children})
        for item in children:
            self.assertEqual('IRPending', item['properties']['protectionState'])
            self.assertEqual(policy['id'].lower(), item['properties']['policyId'].lower())

    def _child_items(self):
        items = self.cmd(
            'backup item list {vault_args} -c "{container}" '
            '--backup-management-type AzureWorkload --workload-type MSSQL'
        ).get_output_in_json()
        return sorted(items, key=lambda item: item['properties']['friendlyName'])

    def _backup_snapshot(self):
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

    def _enable_snapshot_protection(self, children):
        self.assertTrue(children, 'Seed child databases before enabling SQL instance protection.')
        self.assertEqual(len(children), len({name.lower() for name in children}))
        policy = self.cmd('backup policy show {vault_args} -n "{protection_policy}"', checks=[
            self.check('properties.workLoadType', 'SQLInstance'),
            self.check('properties.vmWorkloadPolicyType', 'SnapshotV2'),
        ]).get_output_in_json()
        policy_id = policy['id']
        instance = self.cmd(
            'backup protectable-item show {vault_args} --workload-type MSSQL '
            '--protectable-item-type SQLInstance --name "{protection_instance}" '
            '--server-name "{protection_server}"', checks=[
                self.check('properties.protectionState', 'NotProtected'),
            ]).get_output_in_json()
        self.kwargs['protection_item'] = instance['name']
        databases = self.cmd(
            'backup protectable-item list {vault_args} --workload-type MSSQL '
            '--protectable-item-type SQLDataBase --server-name "{protection_server}"'
        ).get_output_in_json()
        available = {
            item['properties']['friendlyName'].lower() for item in databases
            if item['properties']['parentName'].lower() == self.kwargs['protection_instance'].lower()
        }
        self.assertTrue({name.lower() for name in children}.issubset(available),
                        'Every selected child database must exist on the requested instance.')
        job = self.cmd(
            'backup protection enable-for-azurewl {vault_args} --workload-type SQLInstance '
            '--policy-name "{protection_policy}" --protectable-item-type SQLInstance '
            '--protectable-item-name "{protection_item}" --server-name "{protection_server}" '
            '--child-database-names {child_database_args}'
        ).get_output_in_json()
        self._wait_for_job(job, 'ConfigureBackup')
        item = self.cmd(
            'backup item show {vault_args} -c "{protection_container}" -n "{protection_item}" '
            '--backup-management-type AzureWorkload --workload-type SQLInstance', checks=[
                self.check('properties.workloadType', 'SQLInstance'),
                self.check('properties.protectionState', 'IRPending'),
            ]).get_output_in_json()
        self.assertEqual(policy_id.lower(), item['properties']['policyId'].lower())
        self.assertEqual(sorted(name.lower() for name in children),
                         sorted(name.lower() for name in item['properties']['childDatabaseNameList']))

    def _snapshot_log_point(self, point):
        source = self.cmd(
            'backup item show {vault_args} -c "{container}" -n "{item}" '
            '--backup-management-type AzureWorkload --workload-type SQLInstance'
        ).get_output_in_json()
        datasource_id = source['properties']['protectedItemDataSourceId']
        self.assertTrue(datasource_id, 'Snapshot log queries require the instance datasource ID.')
        self.kwargs['base_datasource_id'] = datasource_id
        included = point['properties']['extendedInfo']['includedDatabases']
        self.assertTrue(included, 'The base snapshot must include databases for log replay.')
        databases = self.cmd(
            'backup item list {vault_args} -c "{container}" '
            '--backup-management-type AzureWorkload --workload-type MSSQL'
        ).get_output_in_json()
        snapshot_time = datetime.fromisoformat(point['properties']['recoveryPointTimeInUTC'].replace('Z', '+00:00'))
        self.assertIsNotNone(snapshot_time.utcoffset())
        common_ranges = [(snapshot_time, datetime.max.replace(tzinfo=timezone.utc))]
        for database in included:
            matches = [
                item for item in databases
                if item['properties'].get('protectedItemDataSourceId') == database['datasourceId']
            ]
            if not matches:
                matches = [
                    item for item in databases
                    if item['properties'].get('friendlyName') == database['datasourceName']
                ]
            self.assertEqual(1, len(matches), 'Each included database must resolve to one protected item.')
            self.kwargs['database_item'] = matches[0]['name']
            ranges = self.cmd(
                'backup recoverypoint show-log-chain {vault_args} -c "{container}" -i "{database_item}" '
                '--backup-management-type AzureWorkload --workload-type MSSQL '
                '--recovery-mode SnapshotAttachAndRecover --base-snapshot-recovery-point-id "{rp}" '
                '--base-recovery-point-datasource-id "{base_datasource_id}" '
                '--query "[].properties.timeRanges[]"'
            ).get_output_in_json()
            if not ranges:
                return None
            parsed_ranges = []
            for entry in ranges:
                start = datetime.fromisoformat(entry['startTime'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(entry['endTime'].replace('Z', '+00:00'))
                self.assertIsNotNone(start.utcoffset())
                self.assertIsNotNone(end.utcoffset())
                self.assertLessEqual(start, end)
                parsed_ranges.append((start, end))
            common_ranges = [
                (max(common_start, start), min(common_end, end))
                for common_start, common_end in common_ranges for start, end in parsed_ranges
                if max(common_start, start) <= min(common_end, end)
            ]
            if not common_ranges:
                return None
        candidates = [
            end.astimezone(timezone.utc).replace(microsecond=0) for start, end in common_ranges
            if end.astimezone(timezone.utc).replace(microsecond=0) >= start
            and end.astimezone(timezone.utc).replace(microsecond=0) > snapshot_time
        ]
        return max(candidates) if candidates else None
