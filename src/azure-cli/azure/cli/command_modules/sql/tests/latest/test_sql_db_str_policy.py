# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""SQL Database STR scenarios using new databases on an explicitly supplied existing server."""

import logging
import os
import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import RequestsTransport
from knack.prompting import NoTTYException
from knack.util import CLIError

from azure.cli.testsdk import ScenarioTest
from .test_sql_mi_str_policy import _SqlStrRecordingSanitizer


def _recording_target(environment):
    target = environment.get('AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID', '')
    match = re.fullmatch(
        r'/subscriptions/([0-9a-f-]{36})/resourceGroups/([\w.()-]+)/providers/Microsoft.Sql/'
        r'servers/([\w-]+)', target, re.IGNORECASE)
    if not match:
        raise ValueError('Set AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID to the full ID of an existing test SQL server.')
    return match.groups()


def _check_write_scope(request, database_id):
    if request.method.upper() in ('GET', 'HEAD'):
        return
    path = unquote(urlsplit(request.url).path).lower()
    database_id = database_id.lower()
    allowed = (
        (request.method.upper() in ('PUT', 'DELETE') and path == database_id) or
        (request.method.upper() == 'PUT' and path == database_id + '/backupshorttermretentionpolicies/default')
    )
    if not allowed:
        raise AssertionError('SQL STR scenarios may write only their own newly created database and its STR policy.')


def _existing_recording_target(environment):
    target = environment.get('AZURE_CLI_TEST_SQL_DB_RESOURCE_ID', '')
    server_id, separator, database = target.rpartition('/databases/')
    if not separator or not database or '/' in database:
        raise ValueError('Set AZURE_CLI_TEST_SQL_DB_RESOURCE_ID to the full ID '
                         'of an existing disposable test database.')
    return (*_recording_target({'AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID': server_id}), database)


def _check_policy_only_write_scope(request, policy_id):
    if request.method.upper() in ('GET', 'HEAD'):
        return
    if request.method.upper() != 'PUT' or unquote(urlsplit(request.url).path).lower() != policy_id.lower():
        raise AssertionError('The existing-database scenario may write only the explicitly authorized STR policy.')


class SqlServerDbShortTermRetentionScenarioTest(ScenarioTest):
    def setUp(self):
        if self.in_recording:
            if not self.is_live:
                self.skipTest('Recording missing. Explicitly enable live mode and supply a test server to record.')
            try:
                subscription, group, server = _recording_target(os.environ)
            except ValueError as ex:
                self.skipTest(str(ex))
            if ('immutability' in self._testMethodName and
                    os.environ.get('AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK', '').lower() != 'true'):
                self.skipTest('Set AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK=true '
                              'to authorize irreversible locking.')
            self.name_replacer.register_name_pair(group, 'strtestrg')
            self.name_replacer.register_name_pair(server, 'strtestserver')
        else:
            subscription, group, server = '00000000-0000-0000-0000-000000000000', 'strtestrg', 'strtestserver'
        self.kwargs.update(subscription=subscription, rg=group, server=server,
                           db=self.create_random_name('clisqldbstr', 26))
        self.database_id = ('/subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.Sql/'
                            'servers/{server}/databases/{db}').format(**self.kwargs)
        self.kwargs['policy_id'] = self.database_id + '/backupShortTermRetentionPolicies/default'
        self.recording_processors.append(_SqlStrRecordingSanitizer(self.kwargs['db'], 'clisqldbstr000001'))
        super().setUp()
        send = RequestsTransport.send

        def guarded_send(transport, request, **kwargs):
            _check_write_scope(request, self.database_id)
            return send(transport, request, **kwargs)

        guard = patch.object(RequestsTransport, 'send', guarded_send)
        guard.start()
        self.addCleanup(guard.stop)
        self.database_created = False
        self.addCleanup(self._cleanup_database)

    def _create_database(self):
        with self.assertRaises(SystemExit) as missing:
            self.cmd('sql db show --subscription {subscription} -g {rg} -s {server} -n {db}')
        self.assertEqual(missing.exception.code, 3)
        database = self.cmd('sql db create --subscription {subscription} -g {rg} -s {server} -n {db}'
                            ' --service-objective S0 --backup-storage-redundancy Local --yes').get_output_in_json()
        self.database_created = True
        self.assertEqual(database['name'], self.kwargs['db'])
        self.assertEqual(database['status'], 'Online')
        return self._show_policy()

    def _cleanup_database(self):
        # Cleanup is live-only and excluded from the recording, so KEEP_DATABASES does not affect playback.
        if not self.database_created or not self.in_recording:
            return
        if os.environ.get('AZURE_CLI_TEST_SQL_DB_KEEP_DATABASES', '').lower() == 'true':
            logging.getLogger(__name__).warning('Keeping new test database for inspection: %s', self.database_id)
            return
        previous = self.disable_recording
        self.disable_recording = True
        try:
            self.cmd('sql db delete --subscription {subscription} -g {rg} -s {server} -n {db} --yes',
                     checks=[self.is_empty()])
            self.database_created = False
        finally:
            self.disable_recording = previous

    def _show_policy(self, days=None, hours=None, status=None):
        policy = self.cmd('sql db str-policy show --subscription {subscription}'
                          ' -g {rg} -s {server} -n {db}').get_output_in_json()
        self.assertIn(policy.get('immutabilityStatus'), ('Disabled', 'Enabled', 'Locked'))
        for key, expected in (('retentionDays', days), ('diffBackupIntervalInHours', hours),
                              ('immutabilityStatus', status)):
            if expected is not None:
                self.assertEqual(policy[key], expected)
        return policy

    def _set_policy(self, extra):
        return self.cmd('sql db str-policy set --subscription {subscription}'
                        ' -g {rg} -s {server} -n {db} ' + extra)

    def _wait_policy(self, days, hours=None, status=None, timeout=300):
        condition = 'properties.retentionDays==`' + str(days) + '`'
        if hours is not None:
            condition += ' && properties.diffBackupIntervalInHours==`' + str(hours) + '`'
        if status is not None:
            condition += " && properties.immutabilityStatus=='" + status + "'"
        self.cmd('resource wait --subscription {subscription} --ids "{policy_id}"'
                 ' --api-version 2026-08-01-preview --interval 5 --timeout ' + str(timeout) +
                 ' --custom "' + condition + '"')

    def test_sql_db_short_term_retention(self):
        initial = self._create_database()
        self.assertIn(initial['immutabilityStatus'], ('Disabled', 'Enabled'))
        # New databases can transition from Disabled to Enabled during this scenario without a write.
        with patch('knack.prompting.prompt_y_n') as prompt:
            self._set_policy('--retention-days 7 --diffbackup-hours 24').assert_with_checks([
                self.check('retentionDays', 7), self.check('diffBackupIntervalInHours', 24)])
            self._show_policy(days=7, hours=24)
            self._set_policy('--retention-days 6 --diffbackup-hours 12').assert_with_checks([
                self.check('retentionDays', 6), self.check('diffBackupIntervalInHours', 12)])
            self._show_policy(days=6, hours=12)
            self._set_policy('--retention-days 5').assert_with_checks([
                self.check('retentionDays', 5), self.check('diffBackupIntervalInHours', 12)])
            self._show_policy(days=5, hours=12)
            self._set_policy('--diffbackup-hours 24').assert_with_checks([
                self.check('retentionDays', 5), self.check('diffBackupIntervalInHours', 24)])
            self._show_policy(days=5, hours=24)
            self._set_policy('--retention-days 7 --lock-immutability false').assert_with_checks([
                self.check('retentionDays', 7), self.check('diffBackupIntervalInHours', 24)])
            self._show_policy(days=7, hours=24)
            self._set_policy('--retention-days 8 --no-wait').assert_with_checks(self.is_empty())
            self._wait_policy(8, hours=24)
            final = self._show_policy(days=8, hours=24)
            self.assertIn(final['immutabilityStatus'], ('Disabled', 'Enabled'))
            prompt.assert_not_called()

    def test_sql_db_short_term_retention_immutability(self):
        initial = self._create_database()
        self.assertIn(initial['immutabilityStatus'], ('Disabled', 'Enabled'))
        # Feature initialization can lag database creation. Do not submit a lock until the policy is Enabled.
        self._wait_policy(initial['retentionDays'], status='Enabled', timeout=900)
        self._show_policy(status='Enabled')
        self._set_policy('--retention-days 7 --diffbackup-hours 12').assert_with_checks([
            self.check('retentionDays', 7), self.check('diffBackupIntervalInHours', 12),
            self.check('immutabilityStatus', 'Enabled')])
        self._show_policy(days=7, hours=12, status='Enabled')
        for behavior, message in (({'return_value': False}, 'Operation cancelled'),
                                  ({'side_effect': NoTTYException()}, 'Use --yes')):
            with patch('knack.prompting.prompt_y_n', **behavior) as prompt, \
                    patch.object(RequestsTransport, 'send') as http:
                with self.assertRaisesRegex(CLIError, message):
                    self._set_policy('--retention-days 7 --lock-immutability true')
                prompt.assert_called_once()
                http.assert_not_called()
        self._show_policy(days=7, hours=12, status='Enabled')

        # SET returns the final policy GET; also verify persisted state with independent reads.
        with patch('knack.prompting.prompt_y_n', return_value=True) as prompt:
            self._set_policy('--retention-days 7 --lock-immutability true').assert_with_checks([
                self.check('retentionDays', 7), self.check('diffBackupIntervalInHours', 12),
                self.check('immutabilityStatus', 'Locked')])
            prompt.assert_called_once()
            self.assertIn('cannot be reverted', prompt.call_args.args[0])
        self._wait_policy(7, hours=12, status='Locked')
        self._show_policy(days=7, hours=12, status='Locked')
        with patch('knack.prompting.prompt_y_n') as prompt:
            self._set_policy('--retention-days 8 --lock-immutability true --yes').assert_with_checks([
                self.check('retentionDays', 8), self.check('diffBackupIntervalInHours', 12),
                self.check('immutabilityStatus', 'Locked')])
            prompt.assert_not_called()
        self._wait_policy(8, hours=12, status='Locked')
        self._show_policy(days=8, hours=12, status='Locked')
        # Preserve the lock explicitly to distinguish a retention violation from an attempted unlock.
        with self.assertRaisesRegex(HttpResponseError, 'InvalidImmutableBackupRetentionPeriod'):
            self._set_policy('--retention-days 7 --lock-immutability true --yes')
        with self.assertRaisesRegex(HttpResponseError, 'CannotRemoveLockedPitrImmutability'):
            self._set_policy('--retention-days 8 --lock-immutability false')
        self._show_policy(days=8, hours=12, status='Locked')
        self._set_policy('--diffbackup-hours 24 --no-wait').assert_with_checks(self.is_empty())
        self._wait_policy(8, hours=24, status='Locked')
        self._show_policy(days=8, hours=24, status='Locked')


class SqlServerDbExistingPolicyLockScenarioTest(ScenarioTest):
    """Lock an explicitly authorized, already Enabled test database without provisioning or cleanup."""

    def setUp(self):
        if self.in_recording:
            if not self.is_live:
                self.skipTest('Recording missing. Explicit live mode and an existing test database are required.')
            try:
                subscription, group, server, database = _existing_recording_target(os.environ)
            except ValueError as ex:
                self.skipTest(str(ex))
            if os.environ.get('AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK', '').lower() != 'true':
                self.skipTest('Set AZURE_CLI_TEST_SQL_DB_ALLOW_IMMUTABILITY_LOCK=true '
                              'to authorize irreversible locking of this test database.')
            for real, moniker in ((group, 'strtestrg'), (server, 'strtestserver'), (database, 'strtestdb')):
                self.name_replacer.register_name_pair(real, moniker)
        else:
            subscription, group, server, database = (
                '00000000-0000-0000-0000-000000000000', 'strtestrg', 'strtestserver', 'strtestdb')
        self.kwargs.update(subscription=subscription, rg=group, server=server, db=database)
        self.kwargs['policy_id'] = (
            '/subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.Sql/'
            'servers/{server}/databases/{db}/backupShortTermRetentionPolicies/default').format(**self.kwargs)
        self.recording_processors.append(_SqlStrRecordingSanitizer(database, 'strtestdb'))
        super().setUp()
        send = RequestsTransport.send

        def guarded_send(transport, request, **kwargs):
            _check_policy_only_write_scope(request, self.kwargs['policy_id'])
            return send(transport, request, **kwargs)

        guard = patch.object(RequestsTransport, 'send', guarded_send)
        guard.start()
        self.addCleanup(guard.stop)

    def test_sql_db_existing_policy_immutability(self):
        command = 'sql db str-policy {} --subscription {{subscription}} -g {{rg}} -s {{server}} -n {{db}}'
        initial = self.cmd(command.format('show')).get_output_in_json()
        self.assertEqual(initial['immutabilityStatus'], 'Enabled',
                         'Use an already Enabled disposable test database; no initialization or cleanup is performed.')
        self.kwargs.update(days=initial['retentionDays'], hours=initial['diffBackupIntervalInHours'])
        self.assertGreater(self.kwargs['days'], 1, 'Use retention above one day to test rejected reduction.')
        set_command = command.format('set')
        # Preserve current retention and assert SET's final policy read as well as independent GETs.
        with patch('knack.prompting.prompt_y_n') as prompt:
            self.cmd(set_command + ' --retention-days {days} --lock-immutability true --yes', checks=[
                self.check('retentionDays', self.kwargs['days']),
                self.check('diffBackupIntervalInHours', self.kwargs['hours']),
                self.check('immutabilityStatus', 'Locked'),
            ])
            prompt.assert_not_called()
        self._assert_locked_policy()
        with self.assertRaisesRegex(HttpResponseError, 'InvalidImmutableBackupRetentionPeriod'):
            self.cmd(set_command + ' --retention-days ' + str(self.kwargs['days'] - 1) +
                     ' --lock-immutability true --yes')
        with self.assertRaisesRegex(HttpResponseError, 'CannotRemoveLockedPitrImmutability'):
            self.cmd(set_command + ' --retention-days {days} --lock-immutability false')
        self._assert_locked_policy()
        # Submit no-wait last so subsequent writes cannot race operation completion.
        with patch('knack.prompting.prompt_y_n') as prompt:
            self.cmd(set_command + ' --retention-days {days} --lock-immutability true --yes --no-wait',
                     checks=[self.is_empty()])
            prompt.assert_not_called()
        self._assert_locked_policy()

    def _assert_locked_policy(self):
        self.cmd('resource wait --subscription {subscription} --ids "{policy_id}"'
                 ' --api-version 2026-08-01-preview --interval 5 --timeout 300'
                 ' --custom "properties.immutabilityStatus==\'Locked\' && properties.retentionDays==`{days}`'
                 ' && properties.diffBackupIntervalInHours==`{hours}`"')
        self.cmd('sql db str-policy show --subscription {subscription} -g {rg} -s {server} -n {db}', checks=[
            self.check('immutabilityStatus', 'Locked'),
            self.check('retentionDays', self.kwargs['days']),
            self.check('diffBackupIntervalInHours', self.kwargs['hours']),
        ])


class SqlDbStrScenarioSafetyTests(unittest.TestCase):
    def test_sql_db_str_existing_target_is_explicit(self):
        for target in ('', '/invalid', '/subscriptions/sub/databases/db',
                       '/subscriptions/sub/databases/db/backupShortTermRetentionPolicies/default'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                _existing_recording_target({'AZURE_CLI_TEST_SQL_DB_RESOURCE_ID': target})
        target = ('/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
                  'providers/Microsoft.Sql/servers/server/databases/testdb')
        self.assertEqual(_existing_recording_target({'AZURE_CLI_TEST_SQL_DB_RESOURCE_ID': target}),
                         ('00000000-0000-0000-0000-000000000000', 'rg', 'server', 'testdb'))

    def test_sql_db_str_existing_scope_rejects_database_writes(self):
        database_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/servers/server/databases/db'
        policy_id = database_id + '/backupShortTermRetentionPolicies/default'
        _check_policy_only_write_scope(SimpleNamespace(method='PUT', url='https://management.azure.com' + policy_id),
                                       policy_id)
        for method, path in (('PUT', database_id), ('DELETE', database_id), ('DELETE', policy_id),
                             ('PATCH', policy_id), ('PUT', policy_id.replace('/db/', '/other/'))):
            with self.subTest(method=method, path=path), self.assertRaises(AssertionError):
                _check_policy_only_write_scope(
                    SimpleNamespace(method=method, url='https://management.azure.com' + path), policy_id)

    def test_sql_db_str_polling_uses_policy_and_bounded_timeout(self):
        from unittest.mock import Mock
        scenario = SimpleNamespace(cmd=Mock())
        for status, timeout in (('Enabled', 900), ('Locked', 300)):
            with self.subTest(status=status):
                SqlServerDbShortTermRetentionScenarioTest._wait_policy(
                    scenario, 7, hours=12, status=status, timeout=timeout)
                command = scenario.cmd.call_args.args[0]
                self.assertIn('resource wait', command)
                self.assertIn('--ids "{policy_id}"', command)
                self.assertIn('--interval 5 --timeout ' + str(timeout), command)
                self.assertIn("properties.immutabilityStatus=='" + status + "'", command)
                self.assertIn('properties.retentionDays==`7`', command)
                self.assertIn('properties.diffBackupIntervalInHours==`12`', command)
                self.assertNotIn('OperationResults', command)

    def test_sql_db_str_requires_explicit_target(self):
        with self.assertRaises(ValueError):
            _recording_target({})
        with self.assertRaises(ValueError):
            _recording_target({'AZURE_CLI_TEST_SQL_SERVER_RESOURCE_ID': '/invalid'})

    def test_sql_db_str_rejects_server_and_unrelated_writes(self):
        database_id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/servers/server/databases/newdb'
        for method, path in (('PUT', database_id), ('DELETE', database_id),
                             ('PUT', database_id + '/backupShortTermRetentionPolicies/default')):
            _check_write_scope(SimpleNamespace(method=method, url='https://management.azure.com' + path), database_id)
        for method, path in (('DELETE', database_id.rsplit('/databases/', 1)[0]),
                             ('PUT', database_id + '-existing'), ('PATCH', database_id.rsplit('/databases/', 1)[0]),
                             ('DELETE', '/subscriptions/sub/resourceGroups/rg')):
            with self.assertRaises(AssertionError):
                request = SimpleNamespace(method=method, url='https://management.azure.com' + path)
                _check_write_scope(request, database_id)

    def test_sql_db_str_keep_databases_prevents_cleanup(self):
        from unittest.mock import Mock
        scenario = SimpleNamespace(database_created=True, in_recording=True, database_id='/test/database', cmd=Mock())
        with patch.dict(os.environ, {'AZURE_CLI_TEST_SQL_DB_KEEP_DATABASES': 'true'}):
            SqlServerDbShortTermRetentionScenarioTest._cleanup_database(scenario)
        scenario.cmd.assert_not_called()
