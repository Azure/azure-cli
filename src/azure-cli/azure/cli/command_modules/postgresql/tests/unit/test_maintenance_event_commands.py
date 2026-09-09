# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import unittest
from unittest.mock import MagicMock, patch

from azure.cli.command_modules.postgresql.commands.maintenance_event_commands import (
    flexible_server_maintenance_event_list,
    flexible_server_maintenance_event_show,
    flexible_server_maintenance_event_reschedule,
    flexible_server_maintenance_event_apply_now
)


class MaintenanceEventCommandsTest(unittest.TestCase):
    """Unit tests for PostgreSQL maintenance event commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.resource_group = 'test-rg'
        self.server_name = 'test-server'
        self.maintenance_event_id = '9J10-M0G'

    def _build_maintenance_event(self, status='Planned', start_time='2026-06-30T00:00:00+00:00'):
        return {
            'id': '/subscriptions/75a38c1d-5d35-4f26-b143-ad0c818e45a3/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}/maintenanceEvents/{}'.format(
                self.resource_group,
                self.server_name,
                self.maintenance_event_id,
            ),
            'name': self.maintenance_event_id,
            'properties': {
                'deferrable': True,
                'deferralDeadline': '2026-07-12T00:00:00+00:00',
                'description': 'Upcoming scheduled maintenance notification.',
                'endTime': '2026-06-30T01:00:00+00:00',
                'estimatedDowntime': 'PT3600S',
                'lastUpdatedTime': '2026-06-22T20:15:20.785896+00:00',
                'maintenanceEventId': self.maintenance_event_id,
                'maintenanceType': 'PlannedMaintenance',
                'originalStartTime': None,
                'rescheduledFrom': '2026-06-28T00:00:00+00:00',
                'startTime': start_time,
                'status': status,
            },
            'resourceGroup': self.resource_group,
            'systemData': None,
            'type': 'Microsoft.DBforPostgreSQL/flexibleServers/maintenanceEvents',
        }

    def _build_reschedule_result(self, start_time='2026-07-19T11:00:00+00:00'):
        return {
            'appliedNow': False,
            'lastUpdatedTime': '2026-06-26T18:21:26.302659+00:00',
            'maintenanceEventId': self.maintenance_event_id,
            'plannedEndTime': '2026-07-19T12:00:00+00:00',
            'plannedStartTime': start_time,
            'serverId': '/subscriptions/75a38c1d-5d35-4f26-b143-ad0c818e45a3/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}'.format(
                self.resource_group, self.server_name),
            'status': 'Rescheduled',
        }

    def _build_apply_now_result(self):
        return {
            'appliedNow': True,
            'lastUpdatedTime': '2026-06-26T18:24:09.877087+00:00',
            'maintenanceEventId': self.maintenance_event_id,
            'plannedEndTime': '2026-06-26T19:24:09.875518+00:00',
            'plannedStartTime': '2026-06-26T18:24:09.875518+00:00',
            'serverId': '/subscriptions/75a38c1d-5d35-4f26-b143-ad0c818e45a3/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{}'.format(
                self.resource_group, self.server_name),
            'status': 'Rescheduled',
        }

    def test_list_maintenance_events_all(self):
        """Test listing all maintenance events."""
        expected_events = [self._build_maintenance_event()]
        self.mock_client.list.return_value = expected_events

        result = flexible_server_maintenance_event_list(
            self.mock_client,
            self.resource_group,
            self.server_name
        )

        self.assertEqual(result, expected_events)
        self.mock_client.list.assert_called_once_with(
            resource_group_name=self.resource_group,
            server_name=self.server_name,
            maintenance_status=None
        )

    def test_list_maintenance_events_with_status_filter(self):
        """Test listing maintenance events with status filter."""
        expected_events = [self._build_maintenance_event(status='Planned')]
        self.mock_client.list.return_value = expected_events

        result = flexible_server_maintenance_event_list(
            self.mock_client,
            self.resource_group,
            self.server_name,
            maintenance_status='Planned'
        )

        self.assertEqual(result, expected_events)
        self.mock_client.list.assert_called_once_with(
            resource_group_name=self.resource_group,
            server_name=self.server_name,
            maintenance_status='Planned'
        )

    def test_list_maintenance_events_empty(self):
        """Test listing when no maintenance events exist."""
        self.mock_client.list.return_value = []

        result = flexible_server_maintenance_event_list(
            self.mock_client,
            self.resource_group,
            self.server_name
        )

        self.assertEqual(result, [])

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_show_maintenance_event(self, mock_validate):
        """Test showing a specific maintenance event."""
        expected_event = self._build_maintenance_event()
        self.mock_client.get.return_value = expected_event

        result = flexible_server_maintenance_event_show(
            self.mock_client,
            self.resource_group,
            self.server_name,
            self.maintenance_event_id
        )

        self.assertEqual(result, expected_event)
        self.assertEqual(result['name'], self.maintenance_event_id)
        self.assertEqual(result['resourceGroup'], self.resource_group)
        self.assertEqual(result['type'], 'Microsoft.DBforPostgreSQL/flexibleServers/maintenanceEvents')
        self.assertIsNone(result['systemData'])
        props = result['properties']
        self.assertEqual(props['maintenanceEventId'], self.maintenance_event_id)
        self.assertEqual(props['maintenanceType'], 'PlannedMaintenance')
        self.assertEqual(props['status'], 'Planned')
        self.assertEqual(props['startTime'], '2026-06-30T00:00:00+00:00')
        self.assertEqual(props['endTime'], '2026-06-30T01:00:00+00:00')
        self.assertEqual(props['deferralDeadline'], '2026-07-12T00:00:00+00:00')
        self.assertTrue(props['deferrable'])
        self.assertIsNone(props['originalStartTime'])
        self.mock_client.get.assert_called_once_with(
            resource_group_name=self.resource_group,
            server_name=self.server_name,
            maintenance_event_id=self.maintenance_event_id
        )
        mock_validate.assert_called_once_with(self.resource_group)

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.sdk_no_wait')
    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_reschedule_maintenance_event(self, mock_validate, mock_sdk_no_wait):
        """Test rescheduling a maintenance event."""
        new_start_time = '2026-07-19T11:00:00+00:00'
        expected_result = self._build_reschedule_result(start_time=new_start_time)
        mock_sdk_no_wait.return_value = expected_result

        result = flexible_server_maintenance_event_reschedule(
            self.mock_client,
            self.resource_group,
            self.server_name,
            self.maintenance_event_id,
            new_start_time,
            no_wait=False
        )

        self.assertEqual(result, expected_result)
        self.assertEqual(result['appliedNow'], False)
        self.assertEqual(result['status'], 'Rescheduled')
        self.assertEqual(result['plannedStartTime'], new_start_time)
        self.assertEqual(result['maintenanceEventId'], self.maintenance_event_id)
        mock_validate.assert_called_once_with(self.resource_group)
        mock_sdk_no_wait.assert_called_once()

        # Verify the call arguments to sdk_no_wait
        call_args = mock_sdk_no_wait.call_args
        self.assertEqual(call_args[0][0], False)  # no_wait parameter
        self.assertEqual(call_args[1]['resource_group_name'], self.resource_group)
        self.assertEqual(call_args[1]['server_name'], self.server_name)
        self.assertEqual(call_args[1]['maintenance_event_id'], self.maintenance_event_id)
        self.assertEqual(call_args[1]['body']['postponeToDateTime'], new_start_time)

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.sdk_no_wait')
    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_reschedule_maintenance_event_no_wait(self, mock_validate, mock_sdk_no_wait):
        """Test rescheduling a maintenance event with no_wait=True."""
        new_start_time = '2026-07-19T11:00:00+00:00'
        expected_result = self._build_reschedule_result(start_time=new_start_time)
        mock_sdk_no_wait.return_value = expected_result

        result = flexible_server_maintenance_event_reschedule(
            self.mock_client,
            self.resource_group,
            self.server_name,
            self.maintenance_event_id,
            new_start_time,
            no_wait=True
        )

        self.assertEqual(result, expected_result)
        mock_validate.assert_called_once_with(self.resource_group)

        # Verify no_wait=True was passed
        call_args = mock_sdk_no_wait.call_args
        self.assertEqual(call_args[0][0], True)

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.sdk_no_wait')
    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_apply_now_maintenance_event(self, mock_validate, mock_sdk_no_wait):
        """Test applying a maintenance event immediately."""
        expected_result = self._build_apply_now_result()
        mock_sdk_no_wait.return_value = expected_result

        result = flexible_server_maintenance_event_apply_now(
            self.mock_client,
            self.resource_group,
            self.server_name,
            self.maintenance_event_id,
            no_wait=False
        )

        self.assertEqual(result, expected_result)
        self.assertEqual(result['appliedNow'], True)
        self.assertEqual(result['status'], 'Rescheduled')
        self.assertEqual(result['maintenanceEventId'], self.maintenance_event_id)
        mock_validate.assert_called_once_with(self.resource_group)
        mock_sdk_no_wait.assert_called_once()

        # Verify the call arguments
        call_args = mock_sdk_no_wait.call_args
        self.assertEqual(call_args[0][0], False)  # no_wait parameter
        self.assertEqual(call_args[1]['resource_group_name'], self.resource_group)
        self.assertEqual(call_args[1]['server_name'], self.server_name)
        self.assertEqual(call_args[1]['maintenance_event_id'], self.maintenance_event_id)

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.sdk_no_wait')
    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_apply_now_maintenance_event_no_wait(self, mock_validate, mock_sdk_no_wait):
        """Test applying a maintenance event with no_wait=True."""
        expected_result = self._build_apply_now_result()
        mock_sdk_no_wait.return_value = expected_result

        result = flexible_server_maintenance_event_apply_now(
            self.mock_client,
            self.resource_group,
            self.server_name,
            self.maintenance_event_id,
            no_wait=True
        )

        self.assertEqual(result, expected_result)

        # Verify no_wait=True was passed
        call_args = mock_sdk_no_wait.call_args
        self.assertEqual(call_args[0][0], True)

    @patch('azure.cli.command_modules.postgresql.commands.maintenance_event_commands.validate_resource_group')
    def test_list_validates_resource_group(self, mock_validate):
        """Test that list validates resource group."""
        self.mock_client.list.return_value = []

        flexible_server_maintenance_event_list(
            self.mock_client,
            self.resource_group,
            self.server_name
        )

        mock_validate.assert_called_once_with(self.resource_group)


if __name__ == '__main__':
    unittest.main()
