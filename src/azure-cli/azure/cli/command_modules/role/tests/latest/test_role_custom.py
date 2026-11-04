# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.role.custom import _resolve_role_id

# pylint: disable=line-too-long


class TestRoleCustomCommands(unittest.TestCase):

    def test_resolve_role_id(self, ):
        mock_client = mock.Mock()
        mock_client._config.subscription_id = '123'
        test_role_id = 'b24988ac-6180-42a0-ab88-20f738123456'

        # action(using a logical name)
        result = _resolve_role_id(test_role_id, 'foobar', mock_client)

        # assert
        self.assertEqual('/subscriptions/123/providers/Microsoft.Authorization/roleDefinitions/{}'.format(test_role_id), result)

        # action (using a full id)
        test_full_id = '/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272123456/providers/microsoft.authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456'
        self.assertEqual(test_full_id, _resolve_role_id(test_full_id, 'foobar', mock_client))

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client')
    def test_assignment_events_with_start_time_and_default_end_time(self, get_client):
        from azure.cli.command_modules.role.custom import _get_assignment_events

        get_client.return_value.activity_logs.list.return_value = []
        _get_assignment_events(mock.Mock(), start_time='2000-01-01T00:00:00Z')
        event_filter = get_client.return_value.activity_logs.list.call_args.kwargs['filter']
        self.assertIn('eventTimestamp ge 2000-01-01T00:00:00Z', event_filter)

    @mock.patch('azure.cli.core.commands.client_factory.get_mgmt_service_client')
    def test_assignment_events_with_explicit_end_time(self, get_client):
        from azure.cli.command_modules.role.custom import _get_assignment_events

        get_client.return_value.activity_logs.list.return_value = []
        for start_time in [None, '2000-01-01T00:00:00Z']:
            with self.subTest(start_time=start_time):
                _get_assignment_events(mock.Mock(), start_time=start_time, end_time='2000-01-01T01:00:00Z')
                event_filter = get_client.return_value.activity_logs.list.call_args.kwargs['filter']
                self.assertIn('eventTimestamp ge 2000-01-01T00:00:00Z and '
                              'eventTimestamp le 2000-01-01T01:00:00Z', event_filter)
