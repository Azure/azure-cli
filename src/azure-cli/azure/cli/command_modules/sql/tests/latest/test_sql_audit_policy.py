# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import unittest
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch

from azure.cli.core.azclierror import ValidationError
from azure.cli.command_modules.sql import custom


class SqlAuditPolicyTest(unittest.TestCase):

    def test_attach_required_fields_reads_raw_response_body(self):
        '''
        The installed SDK's models don't define 'required_fields', so its generic deserializer
        silently drops it. _attach_required_fields is the 'cls' callback that recovers it from
        the raw HTTP response and attaches it to the SDK's own deserialized model instance.
        '''
        deserialized = SimpleNamespace()
        pipeline_response = MagicMock()
        pipeline_response.http_response.json.return_value = {
            'properties': {'requiredFields': ['event_time', 'statement']}
        }

        result = custom._attach_required_fields(pipeline_response, deserialized, {})

        self.assertIs(deserialized, result)
        self.assertEqual(['event_time', 'statement'], result.required_fields)

    def test_attach_required_fields_handles_missing_required_fields(self):
        deserialized = SimpleNamespace()
        pipeline_response = MagicMock()
        pipeline_response.http_response.json.return_value = {'properties': {'state': 'Enabled'}}

        result = custom._attach_required_fields(pipeline_response, deserialized, {})

        self.assertIsNone(result.required_fields)

    def test_get_audit_policy_preview_calls_sdk_client_for_database(self):
        client = MagicMock()
        client.get.return_value = SimpleNamespace(required_fields=['event_time'])

        result = custom._get_audit_policy_preview(
            MagicMock(), client, 'resource-group', 'server', 'database')

        client.get.assert_called_once_with(
            resource_group_name='resource-group',
            server_name='server',
            database_name='database',
            api_version=custom._AUDITING_API_VERSION,
            cls=custom._attach_required_fields)
        self.assertIs(client.get.return_value, result)

    def test_get_audit_policy_preview_calls_sdk_client_for_server(self):
        client = MagicMock()
        client.get.return_value = SimpleNamespace(required_fields=None)

        custom._get_audit_policy_preview(MagicMock(), client, 'resource-group', 'server')

        call_kwargs = client.get.call_args.kwargs
        self.assertNotIn('database_name', call_kwargs)
        self.assertEqual(custom._AUDITING_API_VERSION, call_kwargs['api_version'])
        self.assertIs(custom._attach_required_fields, call_kwargs['cls'])

    @patch('azure.cli.command_modules.sql.custom._get_audit_policy_preview')
    def test_show_commands_use_preview_audit_policy(self, get_audit_policy_preview):
        required_fields = ['event_time', 'action_id']
        get_audit_policy_preview.return_value = SimpleNamespace(
            state='Disabled',
            required_fields=required_fields)

        server_result = custom.server_audit_policy_show(
            MagicMock(), MagicMock(), 'server', 'resource-group')
        get_audit_policy_preview.assert_called_once_with(
            cmd=ANY,
            client=ANY,
            resource_group_name='resource-group',
            server_name='server')
        self.assertEqual(required_fields, server_result.required_fields)

        get_audit_policy_preview.reset_mock()
        database_result = custom.db_audit_policy_show(
            MagicMock(), MagicMock(), 'server', 'resource-group', 'database')
        get_audit_policy_preview.assert_called_once_with(
            cmd=ANY,
            client=ANY,
            resource_group_name='resource-group',
            server_name='server',
            database_name='database')
        self.assertEqual(required_fields, database_result.required_fields)

    def test_set_audit_policy_preview_database_calls_create_or_update(self):
        '''
        Database-level auditing settings PUT is synchronous, so this goes through the SDK's
        plain 'create_or_update', with 'parameters' as raw JSON bytes (a publicly documented
        '@overload' of that method) instead of the typed model, so 'requiredFields' -- which the
        typed model doesn't know about -- still reaches the wire.
        '''
        client = MagicMock()
        parameters = SimpleNamespace(
            required_fields=['event_time', 'action_id', 'statement'],
            serialize=MagicMock(return_value={'properties': {'state': 'Enabled'}}))

        custom._set_audit_policy_preview(
            MagicMock(), client, parameters, 'resource-group', 'server', 'database')

        client.create_or_update.assert_called_once()
        call_kwargs = client.create_or_update.call_args.kwargs
        self.assertEqual('resource-group', call_kwargs['resource_group_name'])
        self.assertEqual('server', call_kwargs['server_name'])
        self.assertEqual('database', call_kwargs['database_name'])
        self.assertEqual(custom._AUDITING_API_VERSION, call_kwargs['api_version'])
        self.assertIs(custom._attach_required_fields, call_kwargs['cls'])
        sent_body = json.loads(call_kwargs['parameters'])
        self.assertEqual(
            ['event_time', 'action_id', 'statement'],
            sent_body['properties']['requiredFields'])

    def test_set_audit_policy_preview_server_calls_begin_create_or_update(self):
        '''
        Server-level auditing settings PUT can be a long-running operation, so this must go
        through 'begin_create_or_update' -- the SDK's own ARMPolling-based poller -- rather than
        any hand-rolled polling loop.
        '''
        client = MagicMock()
        parameters = SimpleNamespace(
            required_fields=['event_time'],
            serialize=MagicMock(return_value={'properties': {'state': 'Enabled'}}))

        custom._set_audit_policy_preview(
            MagicMock(), client, parameters, 'resource-group', 'server')

        client.begin_create_or_update.assert_called_once()
        call_kwargs = client.begin_create_or_update.call_args.kwargs
        self.assertEqual(custom._AUDITING_API_VERSION, call_kwargs['api_version'])
        self.assertIs(custom._attach_required_fields, call_kwargs['cls'])
        self.assertNotIn('polling', call_kwargs)
        sent_body = json.loads(call_kwargs['parameters'])
        self.assertEqual(['event_time'], sent_body['properties']['requiredFields'])

    def test_set_audit_policy_preview_server_no_wait_disables_polling(self):
        client = MagicMock()
        parameters = SimpleNamespace(
            required_fields=['event_time'],
            serialize=MagicMock(return_value={'properties': {'state': 'Enabled'}}))

        custom._set_audit_policy_preview(
            MagicMock(), client, parameters, 'resource-group', 'server', no_wait=True)

        call_kwargs = client.begin_create_or_update.call_args.kwargs
        self.assertEqual(False, call_kwargs['polling'])

    @patch('azure.cli.command_modules.sql.custom._set_audit_policy_preview')
    def test_db_audit_policy_set_routes_to_preview_when_required_fields_present(self, set_preview):
        parameters = SimpleNamespace(required_fields=['event_time'])
        client = MagicMock()
        cmd = MagicMock()

        custom.db_audit_policy_set(cmd, client, 'rg', 'server', 'database', parameters)

        set_preview.assert_called_once_with(cmd, client, parameters, 'rg', 'server', 'database')
        client.create_or_update.assert_not_called()

    @patch('azure.cli.command_modules.sql.custom._set_audit_policy_preview')
    def test_db_audit_policy_set_falls_back_to_sdk_without_required_fields(self, set_preview):
        parameters = SimpleNamespace()  # no 'required_fields' attribute
        client = MagicMock()

        custom.db_audit_policy_set(MagicMock(), client, 'rg', 'server', 'database', parameters)

        set_preview.assert_not_called()
        client.create_or_update.assert_called_once_with(
            resource_group_name='rg', server_name='server', database_name='database',
            parameters=parameters)

    @patch('azure.cli.command_modules.sql.custom._set_audit_policy_preview')
    def test_server_audit_policy_set_routes_to_preview_when_required_fields_present(self, set_preview):
        parameters = SimpleNamespace(required_fields=['event_time'])
        client = MagicMock()
        cmd = MagicMock()

        custom.server_audit_policy_set(cmd, client, 'rg', 'server', parameters, no_wait=True)

        set_preview.assert_called_once_with(cmd, client, parameters, 'rg', 'server', no_wait=True)
        client.begin_create_or_update.assert_not_called()

    @patch('azure.cli.command_modules.sql.custom._set_audit_policy_preview')
    def test_server_audit_policy_set_falls_back_to_sdk_without_required_fields(self, set_preview):
        parameters = SimpleNamespace()  # no 'required_fields' attribute
        client = MagicMock()

        custom.server_audit_policy_set(MagicMock(), client, 'rg', 'server', parameters)

        set_preview.assert_not_called()
        client.begin_create_or_update.assert_called_once()

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_azure_monitor_target_enabled')
    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_blob_storage_details')
    def test_required_fields_are_applied_when_azure_monitor_is_enabled(
            self, _, apply_azure_monitor_target_enabled):
        instance = SimpleNamespace(
            state='Enabled',
            storage_endpoint=None,
            storage_account_access_key=None,
            is_azure_monitor_target_enabled=True,
            audit_actions_and_groups=['BATCH_COMPLETED_GROUP'])

        custom._audit_policy_update_global_settings(
            cmd=MagicMock(),
            instance=instance,
            required_fields=['event_time', 'statement'])

        self.assertEqual(['event_time', 'statement'], instance.required_fields)
        apply_azure_monitor_target_enabled.assert_called_once()

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_azure_monitor_target_enabled')
    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_blob_storage_details')
    def test_required_fields_require_azure_monitor(
            self, _, apply_azure_monitor_target_enabled):
        instance = SimpleNamespace(
            state='Enabled',
            storage_endpoint=None,
            storage_account_access_key=None,
            is_azure_monitor_target_enabled=False,
            audit_actions_and_groups=['BATCH_COMPLETED_GROUP'])

        with self.assertRaisesRegex(ValidationError, 'Azure Monitor target'):
            custom._audit_policy_update_global_settings(
                cmd=MagicMock(),
                instance=instance,
                required_fields=['event_time'])

        apply_azure_monitor_target_enabled.assert_called_once()


if __name__ == '__main__':
    unittest.main()
