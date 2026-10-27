# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch


class ReplicaCommandsTest(unittest.TestCase):
    """Unit tests for PostgreSQL flexible-server replica commands."""

    def setUp(self):
        self.resource_group = 'test-rg'
        self.server_name = 'test-replica'
        self.source_server_resource_id = (
            '/subscriptions/sub-id/resourceGroups/test-rg'
            '/providers/Microsoft.DBforPostgreSQL/flexibleServers/source-server'
        )

    def _build_server_object(self, role='AsyncReplica'):
        server = MagicMock()
        server.replica.role = role
        server.source_server_resource_id = self.source_server_resource_id
        return server

    def _make_cmd_mock(self):
        cmd = MagicMock()
        cmd.cli_ctx = MagicMock()
        return cmd

    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.is_citus_cluster', return_value=False)
    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.validate_resource_group')
    def test_flexible_replica_promote_switchover_includes_source_server_resource_id(
            self, mock_validate_rg, mock_is_citus):
        """Regression test for #33776: planned switchover must populate sourceServerResourceId."""
        from azure.cli.command_modules.postgresql.commands.replica_commands import flexible_replica_promote

        mock_client = MagicMock()
        server_object = self._build_server_object(role='AsyncReplica')
        mock_client.get.return_value = server_object

        flexible_replica_promote(
            cmd=self._make_cmd_mock(),
            client=mock_client,
            resource_group_name=self.resource_group,
            name=self.server_name,
            promote_mode='switchover',
            promote_option='planned',
        )

        mock_client.begin_update.assert_called_once()
        # begin_update is called as positional: (resource_group, name, params)
        call_args = mock_client.begin_update.call_args[0]
        params = call_args[2]

        # Verify sourceServerResourceId is included in the PATCH body
        self.assertEqual(
            params['properties']['sourceServerResourceId'],
            self.source_server_resource_id,
        )
        # Verify replica role and promote settings are correct
        self.assertEqual(params['properties']['replica']['role'], 'Primary')
        self.assertEqual(params['properties']['replica']['promoteMode'], 'switchover')
        self.assertEqual(params['properties']['replica']['promoteOption'], 'planned')

    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.is_citus_cluster', return_value=False)
    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.validate_resource_group')
    def test_flexible_replica_promote_standalone_includes_source_server_resource_id(
            self, mock_validate_rg, mock_is_citus):
        """Standalone promote also populates sourceServerResourceId in the PATCH body."""
        from azure.cli.command_modules.postgresql.commands.replica_commands import flexible_replica_promote

        mock_client = MagicMock()
        server_object = self._build_server_object(role='AsyncReplica')
        mock_client.get.return_value = server_object

        flexible_replica_promote(
            cmd=self._make_cmd_mock(),
            client=mock_client,
            resource_group_name=self.resource_group,
            name=self.server_name,
            promote_mode='standalone',
            promote_option='planned',
        )

        mock_client.begin_update.assert_called_once()
        call_args = mock_client.begin_update.call_args[0]
        params = call_args[2]

        self.assertEqual(
            params['properties']['sourceServerResourceId'],
            self.source_server_resource_id,
        )
        self.assertEqual(params['properties']['replica']['role'], 'None')

    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.is_citus_cluster', return_value=False)
    @patch('azure.cli.command_modules.postgresql.commands.replica_commands.validate_resource_group')
    def test_flexible_replica_promote_no_source_server_resource_id_does_not_fail(
            self, mock_validate_rg, mock_is_citus):
        """If source_server_resource_id is absent on the server object, no KeyError is raised."""
        from azure.cli.command_modules.postgresql.commands.replica_commands import flexible_replica_promote

        mock_client = MagicMock()
        server_object = self._build_server_object(role='AsyncReplica')
        server_object.source_server_resource_id = None
        mock_client.get.return_value = server_object

        flexible_replica_promote(
            cmd=self._make_cmd_mock(),
            client=mock_client,
            resource_group_name=self.resource_group,
            name=self.server_name,
            promote_mode='switchover',
            promote_option='forced',
        )

        mock_client.begin_update.assert_called_once()
        call_args = mock_client.begin_update.call_args[0]
        params = call_args[2]

        # sourceServerResourceId should NOT be injected when the server has none
        self.assertNotIn('sourceServerResourceId', params['properties'])


if __name__ == '__main__':
    unittest.main()
