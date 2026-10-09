# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Offline tests of STR requests, responses, polling and irreversible-action confirmation."""

import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote

from azure.core.credentials import AccessToken
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.core.pipeline.transport import RequestsTransportResponse
from knack.prompting import NoTTYException
from knack.util import CLIError
from requests import Response

from azure.cli.core.azclierror import MutuallyExclusiveArgumentError, RequiredArgumentMissingError
from azure.cli.core.mock import DummyCli
from azure.cli.command_modules.sql.custom import (
    get_short_term_retention, get_short_term_retention_mi,
    update_short_term_retention, update_short_term_retention_mi,
)


class SqlShortTermRetentionPolicyTests(unittest.TestCase):
    def setUp(self):
        config = tempfile.TemporaryDirectory()
        self.addCleanup(config.cleanup)
        self._patch(patch.dict(os.environ, {
            'AZURE_CONFIG_DIR': config.name,
            'AZURE_CORE_COLLECT_TELEMETRY': 'no',
        }))
        self.cmd = SimpleNamespace(cli_ctx=DummyCli())
        self._patch(patch('azure.cli.core.commands.client_factory.get_subscription_id',
                          return_value='00000000-0000-0000-0000-000000000000'))
        credential = SimpleNamespace(get_token=lambda *args, **kwargs: AccessToken('test-token', 4102444800))
        self._patch(patch('azure.cli.core.aaz._command_ctx.AAZCommandCtx.get_login_credential',
                          return_value=credential))
        self.prompt = self._patch(patch('knack.prompting.prompt_y_n', return_value=True))
        self.send = self._patch(patch(
            'azure.core.pipeline.transport.RequestsTransport.send', side_effect=self._send))
        self.requests = []
        self.responses = []

    def _patch(self, patcher):
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def _send(self, request, **kwargs):
        self.requests.append(request)
        self.assertTrue(self.responses, 'Unexpected HTTP request: ' + request.url)
        status, body, headers = self.responses.pop(0)
        response = Response()
        response.status_code = status
        response.headers.update({'Content-Type': 'application/json', **headers})
        response._content = json.dumps(body).encode('utf-8')  # pylint: disable=protected-access
        response.encoding = 'utf-8'
        return RequestsTransportResponse(request, response)

    def _respond(self, body=None, status=200, headers=None):
        if body is None:
            body = {
                'id': '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
                      'providers/Microsoft.Sql/servers/server/databases/db/backupShortTermRetentionPolicies/default',
                'name': 'default',
                'type': 'Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies',
                'properties': {'retentionDays': 7, 'diffBackupIntervalInHours': 24,
                               'immutabilityStatus': 'Locked'},
            }
        headers = headers or {}
        if status == 202:
            headers['Retry-After'] = '0'
        self.responses.append((status, body, headers))

    def _set(self, managed=False, **kwargs):
        if managed:
            return update_short_term_retention_mi(
                self.cmd, 'db', 'server', 'rg', kwargs.pop('retention_days', 7), **kwargs)
        return update_short_term_retention(self.cmd, 'db', 'server', 'rg', **kwargs)

    def _get(self, managed=False, **kwargs):
        if managed:
            return get_short_term_retention_mi(self.cmd, 'db', 'server', 'rg', **kwargs)
        return get_short_term_retention(self.cmd, 'db', 'server', 'rg')

    def _properties(self):
        return json.loads(self.requests[-1].body)['properties']

    def _invoke(self, args):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                code = DummyCli().invoke(args, out_file=stdout)
            except SystemExit as ex:
                code = ex.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_sql_str_lock_confirmation_accepted(self):
        for managed in (False, True):
            with self.subTest(managed=managed):
                self.prompt.reset_mock()
                self._respond()
                result = self._set(managed, retention_days=7, lock_immutability=True).result()
                self.prompt.assert_called_once()
                self.assertIn('cannot be reverted', self.prompt.call_args.args[0])
                self.assertEqual(result['immutabilityStatus'], 'Locked')
                self.assertEqual(result['retentionDays'], 7)
                self.assertNotIn('properties', result)
                self.assertEqual(self._properties(), {'retentionDays': 7, 'lockImmutability': True})
                self.assertIn('api-version=2026-08-01-preview', self.requests[-1].url)
                self.assertIn('/managedInstances/' if managed else '/servers/', self.requests[-1].url)

    def test_sql_str_lock_confirmation_declined(self):
        self.prompt.return_value = False
        for managed in (False, True):
            with self.subTest(managed=managed):
                with self.assertRaisesRegex(CLIError, 'Operation cancelled'):
                    self._set(managed, lock_immutability=True)
        self.send.assert_not_called()

    def test_sql_str_lock_without_tty(self):
        self.prompt.side_effect = NoTTYException()
        for managed in (False, True):
            with self.subTest(managed=managed):
                with self.assertRaisesRegex(CLIError, 'Use --yes'):
                    self._set(managed, lock_immutability=True)
        self.send.assert_not_called()

    def test_sql_str_lock_yes_bypasses_confirmation(self):
        for managed in (False, True):
            with self.subTest(managed=managed):
                self._respond()
                self._set(managed, lock_immutability=True, yes=True).result()
                self.assertIs(self._properties()['lockImmutability'], True)
        self.prompt.assert_not_called()

    def test_sql_str_omitted_and_false_do_not_prompt(self):
        for managed in (False, True):
            for lock in (None, False):
                with self.subTest(managed=managed, lock=lock):
                    self._respond()
                    self._set(managed, retention_days=14, lock_immutability=lock).result()
                    expected = {'retentionDays': 14}
                    if lock is False:
                        expected['lockImmutability'] = False
                    self.assertEqual(self._properties(), expected)
        self.prompt.assert_not_called()

    def test_sql_str_db_lock_only_and_diff_only(self):
        for args, properties in [
            ({'lock_immutability': True, 'yes': True}, {'lockImmutability': True}),
            ({'diffbackup_hours': 12}, {'diffBackupIntervalInHours': 12}),
        ]:
            with self.subTest(args=args):
                self._respond()
                self._set(**args).result()
                self.assertEqual(self._properties(), properties)

    def test_sql_str_db_requires_setting(self):
        with self.assertRaises(RequiredArgumentMissingError):
            self._set()
        self.prompt.assert_not_called()
        self.send.assert_not_called()

    def test_sql_str_dropped_mi_rejects_any_lock_value(self):
        for lock in (True, False):
            with self.subTest(lock=lock):
                with self.assertRaisesRegex(MutuallyExclusiveArgumentError, 'restorable dropped'):
                    self._set(True, deleted_time='2026-08-01T00:00:00Z', lock_immutability=lock, yes=True)
        self.prompt.assert_not_called()
        self.send.assert_not_called()

    def test_sql_str_dropped_mi_preserves_zero_and_identifier(self):
        self._respond()
        self._set(True, deleted_time='2026-08-01T00:00:00Z', retention_days=0).result()
        self.assertEqual(self._properties(), {'retentionDays': 0})
        self.assertIn('/restorableDroppedDatabases/db,134300160000000000/', unquote(self.requests[-1].url))
        self.prompt.assert_not_called()

    def test_sql_str_show_status_for_live_and_dropped(self):
        for managed, deleted_time in ((False, None), (True, None), (True, '2026-08-01T00:00:00Z')):
            for status in ('Disabled', 'Enabled', 'Locked'):
                with self.subTest(managed=managed, deleted_time=deleted_time, status=status):
                    self._respond({
                        'name': 'default',
                        'properties': {'retentionDays': 7, 'immutabilityStatus': status},
                    })
                    result = self._get(managed, deleted_time=deleted_time)
                    self.assertEqual(result['immutabilityStatus'], status)
                    self.assertEqual(result['retentionDays'], 7)
                    self.assertEqual(self.requests[-1].method, 'GET')
                    self.assertIn('api-version=2026-08-01-preview', self.requests[-1].url)
                    if deleted_time:
                        self.assertIn('/restorableDroppedDatabases/', self.requests[-1].url)
        self.prompt.assert_not_called()

    def test_sql_str_no_wait_submits_once(self):
        for managed in (False, True):
            with self.subTest(managed=managed):
                self.send.reset_mock()
                self._respond({}, 202, {'Location': 'https://management.azure.com/operations/str'})
                self.assertIsNone(self._set(managed, retention_days=7, lock_immutability=True,
                                            yes=True, no_wait=True))
                self.send.assert_called_once()
        self.prompt.assert_not_called()

    def test_sql_str_location_polling_returns_final_policy(self):
        for managed in (False, True):
            with self.subTest(managed=managed):
                self._respond({}, 202, {'Location': 'https://management.azure.com/operations/str'})
                self._respond()
                result = self._set(managed, retention_days=7, lock_immutability=True, yes=True).result()
                self.assertEqual(result['immutabilityStatus'], 'Locked')
                self.assertEqual(self.requests[-1].method, 'GET')
                self.assertEqual(self.requests[-1].url, 'https://management.azure.com/operations/str')

    def test_sql_str_async_status_then_location_result(self):
        self._respond({}, 202, {
            'Azure-AsyncOperation': 'https://management.azure.com/operations/str/status',
            'Location': 'https://management.azure.com/operations/str/result',
        })
        self._respond({'status': 'Succeeded'})
        self._respond()
        result = self._set(retention_days=7, lock_immutability=True, yes=True).result()
        self.assertEqual(result['immutabilityStatus'], 'Locked')
        self.assertEqual(self.requests[-2].url, 'https://management.azure.com/operations/str/status')
        self.assertEqual(self.requests[-1].url, 'https://management.azure.com/operations/str/result')

    def test_sql_str_system_data_remains_nested(self):
        self._respond({
            'properties': {'retentionDays': 7, 'immutabilityStatus': 'Enabled'},
            'systemData': {'createdBy': 'user', 'createdAt': '2026-08-01T00:00:00Z'},
        })
        result = self._get()
        self.assertEqual(result['systemData']['createdBy'], 'user')
        self.assertNotIn('createdBy', result)

    def test_sql_str_service_rejection_is_propagated(self):
        for managed in (False, True):
            with self.subTest(managed=managed):
                self._respond({'error': {'code': 'BackupRetentionCannotBeReduced',
                                         'message': 'Backup retention cannot be reduced when locked.'}}, 400)
                with self.assertRaisesRegex(HttpResponseError, 'Backup retention cannot be reduced'):
                    self._set(managed, retention_days=1).result()

    def test_sql_str_show_not_found(self):
        self._respond({'error': {'code': 'ResourceNotFound', 'message': 'Database not found.'}}, 404)
        with self.assertRaises(ResourceNotFoundError):
            self._get()

    def test_sql_str_cli_parses_boolean_and_integer_arguments(self):
        for command in (
            'sql db str-policy set -g rg -s server -n db',
            'sql midb short-term-retention-policy set -g rg --mi server -n db',
        ):
            for flag in ('true', 'false'):
                with self.subTest(command=command, flag=flag):
                    self._respond()
                    code, stdout, stderr = self._invoke(command.split() + [
                        '--retention-days', '14', '--lock-immutability', flag, '--yes'])
                    self.assertEqual(code, 0, stderr)
                    self.assertEqual(self._properties(), {'retentionDays': 14, 'lockImmutability': flag == 'true'})
                    self.assertEqual(json.loads(stdout)['immutabilityStatus'], 'Locked')
        self.prompt.assert_not_called()

    def test_sql_str_cli_cancel_has_no_output_or_update(self):
        self.prompt.return_value = False
        for command in (
            'sql db str-policy set -g rg -s server -n db --lock-immutability true',
            'sql midb short-term-retention-policy set -g rg --mi server -n db '
            '--retention-days 7 --lock-immutability true',
        ):
            with self.subTest(command=command):
                code, stdout, stderr = self._invoke(command.split())
                self.assertEqual(code, 1, stderr)
                self.assertEqual(stdout, '')
        self.send.assert_not_called()

    def test_sql_str_cli_dropped_mi_rejection(self):
        for flag in ('true', 'false'):
            with self.subTest(flag=flag):
                code, stdout, stderr = self._invoke(
                    'sql midb short-term-retention-policy set -g rg --mi server -n db '
                    '--retention-days 7 --deleted-time 2026-08-01T00:00:00Z --yes'.split() +
                    ['--lock-immutability', flag])
                self.assertEqual(code, 1, stderr)
                self.assertEqual(stdout, '')
        self.prompt.assert_not_called()
        self.send.assert_not_called()

    def test_sql_str_cli_ids_and_wait(self):
        resource_id = ('/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/'
                       'providers/Microsoft.Sql/servers/server/databases/db')
        self._respond()
        code, stdout, stderr = self._invoke(['sql', 'db', 'str-policy', 'show', '--ids', resource_id])
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)['immutabilityStatus'], 'Locked')
        self._respond()
        code, _, stderr = self._invoke([
            'sql', 'db', 'str-policy', 'wait', '-g', 'rg', '-s', 'server', '-n', 'db',
            '--custom', "immutabilityStatus=='Locked'", '--interval', '1', '--timeout', '1',
        ])
        self.assertEqual(code, 0, stderr)

    def test_sql_str_cli_show_missing_returns_exit_three(self):
        self._respond({'error': {'code': 'ResourceNotFound', 'message': 'Database not found.'}}, 404)
        code, stdout, stderr = self._invoke('sql db str-policy show -g rg -s server -n db'.split())
        self.assertEqual(code, 3, stderr)
        self.assertEqual(stdout, '')

    def test_sql_str_cli_help(self):
        for command in (
            'sql db str-policy set', 'sql db str-policy show', 'sql db str-policy wait',
            'sql midb short-term-retention-policy set', 'sql midb short-term-retention-policy show',
        ):
            with self.subTest(command=command):
                code, stdout, stderr = self._invoke(command.split() + ['--help'])
                self.assertEqual(code, 0, stderr)
                self.assertIn(command, stdout)
                if command.endswith(' set'):
                    self.assertIn('--lock-immutability', stdout)
                    self.assertIn('--yes', stdout)
                else:
                    self.assertNotIn('--lock-immutability', stdout)
        self.send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
