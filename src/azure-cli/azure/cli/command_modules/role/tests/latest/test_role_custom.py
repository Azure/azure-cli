# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
from unittest import mock

from azure.cli.command_modules.role.custom import _resolve_role_id, _search_role_assignments

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

    def test_search_role_assignments_matches_root_scope_with_empty_assignment_scope(self):
        assignments_client = mock.Mock()
        definitions_client = mock.Mock()
        root_assignment = mock.Mock(scope='', principal_id='principal-id')
        assignments_client.list_for_scope.return_value = [root_assignment]

        result = _search_role_assignments(assignments_client, definitions_client, '/', 'principal-id', None, False, False)

        self.assertEqual([root_assignment], result)

    @mock.patch('azure.cli.command_modules.role.custom._resolve_role_id', autospec=True)
    def test_search_role_assignments_matches_root_role_definition_ids_by_name(self, resolve_role_id_mock):
        assignments_client = mock.Mock()
        definitions_client = mock.Mock()
        role_definition_guid = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
        root_assignment = mock.Mock(
            scope='/',
            principal_id='principal-id',
            role_definition_id='/providers/Microsoft.Authorization/roleDefinitions/{}'.format(role_definition_guid)
        )
        assignments_client.list_for_scope.return_value = [root_assignment]
        resolve_role_id_mock.return_value = (
            '/subscriptions/123/providers/Microsoft.Authorization/roleDefinitions/{}'.format(role_definition_guid)
        )

        result = _search_role_assignments(assignments_client, definitions_client, '/', 'principal-id',
                                          role_definition_guid, False, False)

        self.assertEqual([root_assignment], result)
