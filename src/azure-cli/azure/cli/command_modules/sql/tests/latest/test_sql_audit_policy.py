# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.cli.core.azclierror import ValidationError
from azure.cli.core.util import CLIError
from azure.cli.command_modules.sql import custom

from azure.mgmt.sql.models import (
    DatabaseBlobAuditingPolicy,
    ServerBlobAuditingPolicy,
    ServerDevOpsAuditingSettings,
)

from azure.cli.command_modules.sql.custom import (
    db_audit_policy_show,
    server_audit_policy_show,
    server_ms_support_audit_policy_show,
)
from azure.cli.core.util import todict

from .test_sql_commands import AUDIT_REQUIRED_FIELDS


class SqlAuditPolicyShowTest(unittest.TestCase):
    # TypeSpec model serialization must not drop the CLI's calculated audit target fields.

    policies = (
        (db_audit_policy_show, DatabaseBlobAuditingPolicy, 'SQLSecurityAuditEvents'),
        (server_audit_policy_show, ServerBlobAuditingPolicy, 'SQLSecurityAuditEvents'),
        (server_ms_support_audit_policy_show, ServerDevOpsAuditingSettings, 'DevOpsOperationsAudit'),
    )

    def _show(self, handler, policy):
        client = Mock()
        client.get.return_value = policy
        kwargs = {'database_name': 'database'} if handler is db_audit_policy_show else {}
        return todict(handler(Mock(), client, 'server', 'resource-group', **kwargs))

    @patch('azure.cli.command_modules.sql.custom._get_diagnostic_settings')
    def test_disabled_policy_preserves_calculated_fields(self, get_settings):
        for handler, model, _ in self.policies:
            with self.subTest(model=model.__name__):
                result = self._show(handler, model(
                    state='Disabled', storage_endpoint='https://storage.blob.core.windows.net',
                    is_azure_monitor_target_enabled=True))

                self.assertEqual(result['state'], 'Disabled')
                self.assertEqual(result['blobStorageTargetState'], 'Disabled')
                self.assertEqual(result['logAnalyticsTargetState'], 'Disabled')
                self.assertEqual(result['eventHubTargetState'], 'Disabled')
        get_settings.assert_not_called()

    @patch('azure.cli.command_modules.sql.custom._get_diagnostic_settings')
    def test_blob_target_without_monitor_preserves_sdk_fields(self, get_settings):
        for handler, model, _ in self.policies:
            for endpoint in (None, 'https://storage.blob.core.windows.net'):
                with self.subTest(model=model.__name__, endpoint=endpoint):
                    result = self._show(handler, model(
                        state='Enabled', storage_endpoint=endpoint,
                        is_azure_monitor_target_enabled=False))

                    self.assertEqual(result['state'], 'Enabled')
                    self.assertEqual(result['storageEndpoint'], endpoint)
                    self.assertFalse(result['isAzureMonitorTargetEnabled'])
                    self.assertEqual(result['blobStorageTargetState'], 'Enabled' if endpoint else 'Disabled')
                    self.assertEqual(result['logAnalyticsTargetState'], 'Disabled')
                    self.assertEqual(result['eventHubTargetState'], 'Disabled')
        get_settings.assert_not_called()

    @patch('azure.cli.command_modules.sql.custom._get_diagnostic_settings')
    def test_monitor_targets_preserve_calculated_details(self, get_settings):
        for handler, model, category in self.policies:
            for workspace, event_hub_rule in ((None, None), ('workspace-id', None),
                                              (None, 'event-hub-rule-id'), ('workspace-id', 'event-hub-rule-id')):
                with self.subTest(model=model.__name__, workspace=workspace, event_hub_rule=event_hub_rule):
                    get_settings.return_value = [SimpleNamespace(
                        name='audit', logs=[SimpleNamespace(enabled=True, category=category)],
                        workspace_id=workspace, event_hub_authorization_rule_id=event_hub_rule,
                        event_hub_name='audit-hub')]

                    result = self._show(handler, model(state='Enabled', is_azure_monitor_target_enabled=True))

                    self.assertEqual(result['blobStorageTargetState'], 'Disabled')
                    self.assertEqual(result['logAnalyticsTargetState'], 'Enabled' if workspace else 'Disabled')
                    self.assertEqual(result['eventHubTargetState'], 'Enabled' if event_hub_rule else 'Disabled')
                    if workspace:
                        self.assertEqual(result['logAnalyticsWorkspaceResourceId'], workspace)
                    else:
                        self.assertNotIn('logAnalyticsWorkspaceResourceId', result)
                    if event_hub_rule:
                        self.assertEqual(result['eventHubAuthorizationRuleId'], event_hub_rule)
                        self.assertEqual(result['eventHubName'], 'audit-hub')
                    else:
                        self.assertNotIn('eventHubAuthorizationRuleId', result)
                        self.assertNotIn('eventHubName', result)


class SqlAuditPolicyRequiredFieldsTest(unittest.TestCase):

    policies = (
        (custom.server_audit_policy_update, ServerBlobAuditingPolicy),
        (custom.db_audit_policy_update, DatabaseBlobAuditingPolicy),
    )

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_diagnostic_settings', return_value=[])
    @patch('azure.cli.command_modules.sql.custom._get_diagnostic_settings', return_value=[])
    def test_required_fields_with_event_hub_log_analytics_and_both_targets(self, _get_settings, _update_settings):
        for handler, model in self.policies:
            for event_hub_state, log_analytics_state in (
                    ('Enabled', 'Disabled'), ('Disabled', 'Enabled'), ('Enabled', 'Enabled')):
                for fields in (['event_time', 'action_id', 'statement'], AUDIT_REQUIRED_FIELDS, ['event_time']):
                    with self.subTest(model=model.__name__, event_hub=event_hub_state,
                                      log_analytics=log_analytics_state, fields=fields):
                        instance = model(state='Enabled', is_azure_monitor_target_enabled=False)
                        kwargs = {'database_name': 'database'} if handler is custom.db_audit_policy_update else {}
                        result = handler(
                            cmd=Mock(), instance=instance, server_name='server', resource_group_name='resource-group',
                            event_hub_target_state=event_hub_state, log_analytics_target_state=log_analytics_state,
                            event_hub_authorization_rule_id=(
                                'event-hub-rule-id' if event_hub_state == 'Enabled' else None),
                            log_analytics_workspace_resource_id=(
                                'workspace-id' if log_analytics_state == 'Enabled' else None),
                            required_fields=fields, **kwargs)

                        self.assertTrue(result.is_azure_monitor_target_enabled)
                        self.assertEqual(result.as_dict()['properties']['requiredFields'], fields)

    @patch('azure.cli.command_modules.sql.custom._audit_policy_update_apply_blob_storage_details')
    def test_required_fields_rejected_without_event_hub_or_log_analytics(self, _apply_blob):
        for _, model in self.policies:
            for event_hub_state, log_analytics_state in (
                    (None, None), ('Disabled', None), (None, 'Disabled'), ('Disabled', 'Disabled')):
                with self.subTest(model=model.__name__, event_hub=event_hub_state,
                                  log_analytics=log_analytics_state):
                    instance = model(
                        state='Enabled', is_azure_monitor_target_enabled=False,
                        storage_endpoint='https://storage.blob.core.windows.net')
                    with self.assertRaisesRegex(ValidationError, 'Azure Monitor target'):
                        custom._audit_policy_update_global_settings(
                            cmd=Mock(), instance=instance, required_fields=['event_time'], diagnostic_settings=[],
                            event_hub_target_state=event_hub_state, log_analytics_target_state=log_analytics_state)
                    self.assertIsNone(instance.required_fields)

    def test_required_fields_alone_satisfies_argument_validation(self):
        custom._audit_policy_validate_arguments(required_fields=['event_time'])

    def test_no_arguments_still_fails_argument_validation(self):
        with self.assertRaises(CLIError):
            custom._audit_policy_validate_arguments()

    def test_required_fields_rejected_when_state_disabled(self):
        with self.assertRaisesRegex(CLIError, 'state is disabled'):
            custom._audit_policy_validate_arguments(state='Disabled', required_fields=['event_time'])

    def test_required_fields_rejected_when_existing_auditing_is_disabled(self):
        for _, model in self.policies:
            with self.subTest(model=model.__name__):
                instance = model(state='Disabled', is_azure_monitor_target_enabled=True)
                with self.assertRaisesRegex(ValidationError, 'auditing and the Azure Monitor target'):
                    custom._audit_policy_update_global_settings(
                        cmd=Mock(), instance=instance, required_fields=['event_time'])
                self.assertIsNone(instance.required_fields)

    def test_show_returns_required_fields_from_sdk(self):
        for handler, model in ((server_audit_policy_show, ServerBlobAuditingPolicy),
                               (db_audit_policy_show, DatabaseBlobAuditingPolicy)):
            with self.subTest(model=model.__name__):
                fields = ['event_time', 'action_id']
                client = Mock()
                client.get.return_value = model(state='Disabled', required_fields=fields)
                kwargs = {'database_name': 'database'} if handler is db_audit_policy_show else {}
                result = handler(Mock(), client, 'server', 'resource-group', **kwargs)
                self.assertEqual(result['requiredFields'], fields)


if __name__ == '__main__':
    unittest.main()
