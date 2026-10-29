# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.util import CLIError
from azure.cli.command_modules.sql import custom


class SqlAuditPolicyRequiredFieldsTest(unittest.TestCase):

    def _enabled_instance(self, azure_monitor_enabled):
        return SimpleNamespace(
            state='Enabled',
            storage_endpoint=None,
            storage_account_access_key=None,
            is_azure_monitor_target_enabled=azure_monitor_enabled,
            audit_actions_and_groups=['BATCH_COMPLETED_GROUP'])

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_azure_monitor_target_enabled')
    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_blob_storage_details')
    def test_required_fields_applied_when_azure_monitor_enabled(self, _, apply_azure_monitor):
        instance = self._enabled_instance(azure_monitor_enabled=True)

        custom._audit_policy_update_global_settings(
            cmd=MagicMock(), instance=instance, required_fields=['event_time', 'statement'])

        self.assertEqual(['event_time', 'statement'], instance.required_fields)
        apply_azure_monitor.assert_called_once()

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_azure_monitor_target_enabled')
    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_blob_storage_details')
    def test_required_fields_rejected_without_azure_monitor(self, _, apply_azure_monitor):
        instance = self._enabled_instance(azure_monitor_enabled=False)

        with self.assertRaisesRegex(ValidationError, 'Azure Monitor target'):
            custom._audit_policy_update_global_settings(
                cmd=MagicMock(), instance=instance, required_fields=['event_time'])

        apply_azure_monitor.assert_called_once()

    def test_required_fields_alone_satisfies_argument_validation(self):
        custom._audit_policy_validate_arguments(required_fields=['event_time'])

    def test_no_arguments_still_fails_argument_validation(self):
        with self.assertRaises(CLIError):
            custom._audit_policy_validate_arguments()

    def test_required_fields_rejected_when_state_disabled(self):
        with self.assertRaisesRegex(CLIError, 'state is disabled'):
            custom._audit_policy_validate_arguments(state='Disabled', required_fields=['event_time'])

    def test_show_returns_required_fields_from_sdk(self):
        required_fields = ['event_time', 'action_id']
        client = MagicMock()
        client.get.return_value = SimpleNamespace(state='Disabled', required_fields=required_fields)

        server_result = custom.server_audit_policy_show(MagicMock(), client, 'server', 'resource-group')
        self.assertEqual(required_fields, server_result.required_fields)

        database_result = custom.db_audit_policy_show(MagicMock(), client, 'server', 'resource-group', 'database')
        self.assertEqual(required_fields, database_result.required_fields)


if __name__ == '__main__':
    unittest.main()
