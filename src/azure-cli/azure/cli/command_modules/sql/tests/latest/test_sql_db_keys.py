# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from azure.mgmt.sql import SqlManagementClient

from azure.cli.command_modules.sql.custom import db_get
from azure.cli.command_modules.sql._format import db_transform

from . import test_sql_commands


class SqlDatabaseExpandedKeysTest(unittest.TestCase):
    # The default API changed with SDK 5.0; keep the expanded-key workaround narrow and keys visible.

    @patch('azure.cli.command_modules.sql._util.get_sql_management_client')
    def test_show_without_expansion_keeps_default_client(self, client_factory):
        client = Mock()

        result = db_get(Mock(), client, 'database', 'server', 'resource-group')

        self.assertIs(result, client.get.return_value)
        client.get.assert_called_once_with('resource-group', 'server', 'database', expand=None)
        client_factory.assert_not_called()

    @patch('azure.cli.command_modules.sql._util.get_sql_management_client')
    def test_expanded_keys_use_stable_api_and_preserve_output(self, client_factory):
        key = 'https://vault/keys/key/version'
        response = Mock(status_code=200)
        response.json.return_value = {'properties': {'keys': {key: {'type': 'AzureKeyVault'}}}}
        cmd = Mock()
        for keys_filter in (None, '2026-01-01T00:00:00Z'):
            with self.subTest(keys_filter=keys_filter):
                with SqlManagementClient(
                        Mock(), '00000000-0000-0000-0000-000000000000',
                        api_version='2025-01-01') as sdk_client:
                    client_factory.return_value = sdk_client
                    with patch.object(sdk_client._client._pipeline, 'run') as run:
                        run.return_value = SimpleNamespace(http_response=response)
                        default_client = Mock()

                        result = db_get(
                            cmd, default_client, 'database', 'server', 'resource-group',
                            expand_keys=True, keys_filter=keys_filter)

                        query = parse_qs(urlparse(run.call_args.args[0].url).query)

                client_factory.assert_called_with(cmd.cli_ctx, api_version='2025-01-01')
                default_client.get.assert_not_called()
                self.assertEqual(query['api-version'], ['2025-01-01'])
                expected_expand = "keys($filter=pointInTime('{}'))".format(keys_filter) if keys_filter else 'keys'
                self.assertEqual(query['$expand'], [expected_expand])
                self.assertEqual(db_transform(result)['keys'][key]['type'], 'AzureKeyVault')


class SqlDatabaseKeysTest(unittest.TestCase):
    # Service eventual consistency needs bounded polling without weakening the key-content assertions.

    def setUp(self):
        self.scenario = unittest.TestCase()
        self.scenario.is_live = False
        self.scenario.cmd = Mock()
        self.response = self.scenario.cmd.return_value.get_output_in_json
        self.expected_keys = ['https://vault/keys/key1/version1', 'https://vault/keys/key2/version2']

    def _check_keys(self):
        test_sql_commands.SqlServerDbMgmtScenarioTest._assert_database_keys(
            self.scenario, 'resource-group', 'server', 'database',
            self.expected_keys[0], self.expected_keys)

    @patch('azure.cli.command_modules.sql.tests.latest.test_sql_commands.time.sleep')
    def test_waits_for_missing_and_partial_keys_without_sleeping_in_playback(self, sleep):
        self.response.side_effect = [
            {},
            {'keys': None},
            {'keys': {self.expected_keys[0]: {}}},
            {'keys': dict.fromkeys(self.expected_keys, {})}]

        self._check_keys()

        self.assertEqual(self.scenario.cmd.call_count, 4)
        sleep.assert_not_called()

    @patch('azure.cli.command_modules.sql.tests.latest.test_sql_commands.time.sleep')
    def test_sleeps_between_live_attempts(self, sleep):
        self.scenario.is_live = True
        self.response.side_effect = [
            {'keys': None},
            {'keys': dict.fromkeys(self.expected_keys, {})}]

        self._check_keys()

        sleep.assert_called_once_with(10)

    def test_missing_keys_fail_after_bounded_attempts(self):
        self.response.return_value = {'keys': None}

        with self.assertRaisesRegex(AssertionError, 'Database keys were not returned'):
            self._check_keys()

        self.assertEqual(self.scenario.cmd.call_count, 90)

    def test_wrong_keys_do_not_pass_count_check(self):
        self.response.return_value = {'keys': {self.expected_keys[0]: {}, 'unexpected-key': {}}}

        with self.assertRaisesRegex(AssertionError, 'Database keys did not match'):
            self._check_keys()

        self.assertEqual(self.scenario.cmd.call_count, 90)

    def test_command_errors_are_not_retried(self):
        self.scenario.cmd.side_effect = RuntimeError('command failed')

        with self.assertRaisesRegex(RuntimeError, 'command failed'):
            self._check_keys()

        self.scenario.cmd.assert_called_once()
