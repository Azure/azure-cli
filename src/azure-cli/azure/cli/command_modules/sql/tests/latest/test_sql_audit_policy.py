# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

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
