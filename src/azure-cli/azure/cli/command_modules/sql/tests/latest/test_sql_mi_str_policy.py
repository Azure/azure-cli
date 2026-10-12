# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""MI STR scenarios. Live recording requires an explicitly supplied existing MI; it is never modified."""

import json
import os
import re
import unittest
from unittest.mock import patch
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

from azure.core.exceptions import HttpResponseError
from azure.core.pipeline.transport import RequestsTransport
from knack.prompting import NoTTYException
from knack.util import CLIError

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError
from azure.cli.testsdk import ScenarioTest
from azure.cli.testsdk.scenario_tests.recording_processors import RecordingProcessor


def _recording_target(environment):
    target = environment.get('AZURE_CLI_TEST_SQL_MI_RESOURCE_ID', '')
    match = re.fullmatch(
        r'/subscriptions/([0-9a-f-]{36})/resourceGroups/([\w.()-]+)/providers/Microsoft.Sql/'
        r'managedInstances/([\w-]+)', target, re.IGNORECASE)
    if not match:
        raise ValueError('Set AZURE_CLI_TEST_SQL_MI_RESOURCE_ID to the full resource ID of an existing test MI.')
    return match.groups()


def _check_write_scope(request, database_id):
    """Reject MI, resource-group and unrelated database writes before they reach the transport."""
    if request.method.upper() in ('GET', 'HEAD'):
        return
    path = unquote(urlsplit(request.url).path).lower()
    database_id = database_id.lower()
    policy_suffix = '/backupshorttermretentionpolicies/default'
    dropped_prefix = database_id.replace('/databases/', '/restorabledroppeddatabases/') + ','
    allowed = (
        (request.method.upper() in ('PUT', 'DELETE') and path == database_id) or
        (request.method.upper() == 'PUT' and path == database_id + policy_suffix) or
        (request.method.upper() == 'PUT' and path.startswith(dropped_prefix) and
         re.fullmatch(r'\d+' + policy_suffix, path[len(dropped_prefix):]) is not None)
    )
    if not allowed:
        raise AssertionError('MI STR scenarios may write only their own newly created database and its STR policy.')


class _SqlStrRecordingSanitizer(RecordingProcessor):
    """Remove signed polling query values and unrelated entries from shared-MI list responses."""

    def __init__(self, database_name, database_moniker):
        self.database_names = (database_name, database_moniker)

    @staticmethod
    def _sanitize_url(url):
        parts = urlsplit(url)
        query = [(key, 'REDACTED' if key.lower() in ('c', 's', 'h', 't', 'sig', 'token') else value)
                 for key, value in parse_qsl(parts.query, keep_blank_values=True)]
        return urlunsplit(parts._replace(query=urlencode(query)))

    def process_request(self, request):
        request.uri = self._sanitize_url(request.uri)
        return request

    def process_response(self, response):
        for header in ('location', 'azure-asyncoperation'):
            self.replace_header_fn(response, header, self._sanitize_url)
        body = response['body']['string']
        if body:
            data = json.loads(body)
            values = data.get('value')
            if isinstance(values, list) and any(
                    item.get('type', '').lower().endswith('/restorabledroppeddatabases') for item in values):
                data['value'] = [item for item in values
                                 if item.get('properties', {}).get('databaseName') in self.database_names]
            response['body']['string'] = json.dumps(data)
        return response


class SqlManagedInstanceDbShortTermRetentionScenarioTest(ScenarioTest):
    def setUp(self):
        if self.in_recording:
            if not self.is_live:
                self.skipTest('Recording is missing. Explicitly enable live mode and supply a test MI to record.')
            try:
                subscription, group, instance = _recording_target(os.environ)
            except ValueError as ex:
                self.skipTest(str(ex))
            if ('immutability' in self._testMethodName and
                    os.environ.get('AZURE_CLI_TEST_SQL_MI_ALLOW_IMMUTABILITY_LOCK', '').lower() != 'true'):
                self.skipTest('Set AZURE_CLI_TEST_SQL_MI_ALLOW_IMMUTABILITY_LOCK=true '
                              'to authorize irreversible locking.')
            self.name_replacer.register_name_pair(group, 'strtestrg')
            self.name_replacer.register_name_pair(instance, 'strtestmi')
        else:
            # Playback never reads live target environment variables or credentials.
            subscription, group, instance = '00000000-0000-0000-0000-000000000000', 'strtestrg', 'strtestmi'

        self.kwargs.update(subscription=subscription, rg=group, mi=instance,
                           db=self.create_random_name('clistr', 24))
        self.database_id = ('/subscriptions/{subscription}/resourceGroups/{rg}/providers/Microsoft.Sql/'
                            'managedInstances/{mi}/databases/{db}').format(**self.kwargs)
        self.kwargs['database_id'] = self.database_id
        self.recording_processors.append(_SqlStrRecordingSanitizer(self.kwargs['db'], 'clistr000001'))
        super().setUp()

        send = RequestsTransport.send

        def guarded_send(transport, request, **kwargs):
            _check_write_scope(request, self.database_id)
            return send(transport, request, **kwargs)

        guard = patch.object(RequestsTransport, 'send', guarded_send)
        guard.start()
        self.addCleanup(guard.stop)
        self.database_created = False
        self.addCleanup(self._delete_database)

    def _create_database(self):
        # Refuse to adopt/delete an existing database even in the event of a random-name collision.
        with self.assertRaises(SystemExit) as missing:
            self.cmd('sql midb show --subscription {subscription} -g {rg} --mi {mi} -n {db}')
        self.assertEqual(missing.exception.code, 3)
        self.cmd('sql midb create --subscription {subscription} -g {rg} --mi {mi} -n {db}', checks=[
            self.check('name', '{db}'), self.check('status', 'Online')])
        self.database_created = True
        return self._show_policy()

    def _delete_database(self):
        if self.database_created:
            self.cmd('sql midb delete --subscription {subscription} -g {rg} --mi {mi} -n {db} --yes',
                     checks=[self.is_empty()])
            self.database_created = False

    def _show_policy(self, dropped=False, days=None, status=None):
        suffix = ' --deleted-time "{deleted_time}"' if dropped else ''
        result = self.cmd('sql midb short-term-retention-policy show --subscription {subscription}'
                          ' -g {rg} --mi {mi} -n {db}' + suffix).get_output_in_json()
        self.assertIn(result['immutabilityStatus'], ('Disabled', 'Enabled', 'Locked'))
        if days is not None:
            self.assertEqual(result['retentionDays'], days)
        if status is not None:
            self.assertEqual(result['immutabilityStatus'], status)
        return result

    def _set_policy(self, days, extra='', dropped=False, expect_failure=False):
        suffix = ' --deleted-time "{deleted_time}"' if dropped else ''
        return self.cmd('sql midb short-term-retention-policy set --subscription {subscription}'
                        ' -g {rg} --mi {mi} -n {db} --retention-days ' + str(days) + suffix + ' ' + extra,
                        expect_failure=expect_failure)

    def _wait_policy(self, days, dropped=False, status=None):
        self.kwargs['policy_id'] = (
            self.kwargs['dropped_id'] if dropped else self.database_id) + '/backupShortTermRetentionPolicies/default'
        condition = 'properties.retentionDays==`' + str(days) + '`'
        if status is not None:
            condition += " && properties.immutabilityStatus=='" + status + "'"
        self.cmd('resource wait --subscription {subscription} --ids "{policy_id}"'
                 ' --api-version 2026-08-01-preview --interval 5 --timeout 300'
                 ' --custom "' + condition + '"')

    def _drop_for_policy_test(self):
        # Use bounded, read-only polling rather than the old unbounded backup-readiness loop.
        self.cmd('resource wait --subscription {subscription} --ids "{database_id}"'
                 ' --api-version 2023-08-01 --custom "properties.earliestRestorePoint!=null"'
                 ' --interval 15 --timeout 900')
        self._delete_database()
        dropped = self.cmd('sql midb list-deleted --subscription {subscription} -g {rg} --mi {mi}'
                           ' --query "[?databaseName==\'{db}\']"').get_output_in_json()
        self.assertEqual(len(dropped), 1)
        self.kwargs.update(deleted_time=dropped[0]['deletionDate'], dropped_id=dropped[0]['id'])

    def _check_dropped_lock_guard(self):
        for value in ('true', 'false'):
            with patch('knack.prompting.prompt_y_n') as prompt, patch.object(RequestsTransport, 'send') as http:
                with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'restorable dropped'):
                    self._set_policy(7, '--lock-immutability ' + value + ' --yes', dropped=True)
                prompt.assert_not_called()
                http.assert_not_called()

    def test_sql_managed_db_short_retention(self):
        initial = self._create_database()
        self.assertEqual(initial['retentionDays'], 7)
        status = initial['immutabilityStatus']
        self.assertIn(status, ('Disabled', 'Enabled'))

        with patch('knack.prompting.prompt_y_n') as prompt:
            self._set_policy(14).assert_with_checks(self.check('retentionDays', 14))
            self._show_policy(days=14, status=status)
            self._set_policy(7, '--lock-immutability false').assert_with_checks(self.check('retentionDays', 7))
            self._show_policy(days=7, status=status)
            self._set_policy(10, '--no-wait').assert_with_checks(self.is_empty())
            self._wait_policy(10)
            self._show_policy(days=10, status=status)
            prompt.assert_not_called()

        self._drop_for_policy_test()
        self._show_policy(dropped=True, days=10, status=status)
        self._check_dropped_lock_guard()
        self._set_policy(7, dropped=True).assert_with_checks(self.check('retentionDays', 7))
        self._show_policy(dropped=True, days=7, status=status)
        self._set_policy(6, '--no-wait', dropped=True).assert_with_checks(self.is_empty())
        self._wait_policy(6, dropped=True)
        self._show_policy(dropped=True, days=6, status=status)

    def test_sql_managed_db_short_retention_immutability(self):
        initial = self._create_database()
        self.assertEqual(initial['immutabilityStatus'], 'Enabled',
                         'Use a feature-enabled MI; this scenario must not pass without exercising locking.')
        self._set_policy(14)
        self._set_policy(7, '--lock-immutability false')
        self._show_policy(days=7, status='Enabled')

        for behavior, message in (({'return_value': False}, 'Operation cancelled'),
                                  ({'side_effect': NoTTYException()}, 'Use --yes')):
            with patch('knack.prompting.prompt_y_n', **behavior) as prompt, \
                    patch.object(RequestsTransport, 'send') as http:
                with self.assertRaisesRegex(CLIError, message):
                    self._set_policy(7, '--lock-immutability true')
                prompt.assert_called_once()
                http.assert_not_called()
        self._show_policy(days=7, status='Enabled')

        # Only confirmation input is controlled; locking and all assertions use real recorded HTTP.
        # The operation-result endpoint can report Disabled after a successful lock. Verify the
        # persisted state through bounded polling of the database policy GET instead; do not
        # assert immutabilityStatus on the SET result or change the CLI's polling behavior.
        with patch('knack.prompting.prompt_y_n', return_value=True) as prompt:
            self._set_policy(7, '--lock-immutability true')
            prompt.assert_called_once()
            self.assertIn('cannot be reverted', prompt.call_args.args[0])
        self._wait_policy(7, status='Locked')
        self._show_policy(days=7, status='Locked')
        with patch('knack.prompting.prompt_y_n') as prompt:
            self._set_policy(8, '--lock-immutability true --yes')
            prompt.assert_not_called()
        self._wait_policy(8, status='Locked')
        self._show_policy(days=8, status='Locked')

        with self.assertRaisesRegex(HttpResponseError, '(?i)retention.*(reduc|decreas)'):
            self._set_policy(7)
        with self.assertRaisesRegex(HttpResponseError, '(?i)(immutability|lock).*(remov|disabl|unlock)'):
            self._set_policy(8, '--lock-immutability false')
        self._show_policy(days=8, status='Locked')
        self._drop_for_policy_test()
        self._wait_policy(8, dropped=True, status='Locked')
        self._show_policy(dropped=True, days=8, status='Locked')
        self._check_dropped_lock_guard()
        with self.assertRaisesRegex(HttpResponseError, '(?i)retention.*(reduc|decreas)'):
            self._set_policy(7, dropped=True)
        self._show_policy(dropped=True, days=8, status='Locked')


class SqlMiStrScenarioSafetyTests(unittest.TestCase):
    def test_sql_mi_str_lock_polling_targets_policy_get(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        scenario = SimpleNamespace(
            database_id='/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/'
                        'managedInstances/mi/databases/testdb',
            kwargs={
                'dropped_id': '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Sql/'
                              'managedInstances/mi/restorableDroppedDatabases/testdb,123',
            },
            cmd=Mock(),
        )
        for dropped in (False, True):
            with self.subTest(dropped=dropped):
                SqlManagedInstanceDbShortTermRetentionScenarioTest._wait_policy(
                    scenario, 8, dropped=dropped, status='Locked')
                command = scenario.cmd.call_args.args[0]
                expected_id = scenario.kwargs['dropped_id'] if dropped else scenario.database_id
                self.assertEqual(scenario.kwargs['policy_id'],
                                 expected_id + '/backupShortTermRetentionPolicies/default')
                self.assertIn('resource wait', command)
                self.assertIn('--interval 5 --timeout 300', command)
                self.assertIn("properties.retentionDays==`8` && properties.immutabilityStatus=='Locked'", command)
                self.assertNotIn('OperationResults', command)

    def test_sql_mi_str_target_is_explicit(self):
        for env in ({}, {'AZURE_CLI_TEST_SQL_MI_RESOURCE_ID': '/invalid'}):
            with self.assertRaises(ValueError):
                _recording_target(env)

    def test_sql_mi_str_write_scope(self):
        from types import SimpleNamespace
        database_id = ('/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
                       'providers/Microsoft.Sql/managedInstances/mi/databases/testdb')
        for method, path in (
            ('PUT', database_id), ('DELETE', database_id),
            ('PUT', database_id + '/backupShortTermRetentionPolicies/default'),
            ('PUT', database_id.replace('/databases/', '/restorableDroppedDatabases/') +
             '%2C123456/backupShortTermRetentionPolicies/default'),
        ):
            _check_write_scope(SimpleNamespace(method=method, url='https://management.azure.com' + path), database_id)
        for method, path in (
            ('DELETE', database_id.rsplit('/databases/', 1)[0]),
            ('PATCH', database_id.rsplit('/databases/', 1)[0]),
            ('PUT', database_id + '-existing'),
            ('DELETE', '/subscriptions/sub/resourceGroups/rg'),
            ('POST', database_id + '/restore'),
        ):
            with self.assertRaises(AssertionError):
                request = SimpleNamespace(method=method, url='https://management.azure.com' + path)
                _check_write_scope(request, database_id)

    def test_sql_mi_str_polling_secrets_are_redacted(self):
        sanitizer = _SqlStrRecordingSanitizer('testdb', 'clistr000001')
        url = 'https://management.azure.com/operation?api-version=2026-08-01-preview'
        url += '&c=certificate&s=secret&h=hash&t=123'
        sanitized = sanitizer._sanitize_url(url)  # pylint: disable=protected-access
        self.assertEqual(dict(parse_qsl(urlsplit(sanitized).query)), {
            'api-version': '2026-08-01-preview', 'c': 'REDACTED', 's': 'REDACTED', 'h': 'REDACTED', 't': 'REDACTED',
        })
