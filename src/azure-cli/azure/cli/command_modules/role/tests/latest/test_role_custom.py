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

    def test_search_role_assignments_root_scope(self):
        """Test that role assignments at root scope ('/') are correctly matched by role GUID.

        Root-scope role assignments store role_definition_id without a subscription prefix
        (e.g. '/providers/Microsoft.Authorization/roleDefinitions/{guid}'), but _resolve_role_id
        constructs a subscription-prefixed path when given a bare GUID. The comparison must
        normalise both to the GUID segment so the assignment is not silently dropped.
        """
        role_guid = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
        subscription_id = '00000000-0000-0000-0000-000000000000'
        principal_id = 'd7b9e171-ff4e-4deb-9f77-0aa53c66f826'

        # Simulate a role assignment at root scope ('/') — role_definition_id has no subscription prefix
        mock_assignment = mock.Mock()
        mock_assignment.scope = '/'
        mock_assignment.role_definition_id = (
            '/providers/Microsoft.Authorization/roleDefinitions/' + role_guid
        )
        mock_assignment.principal_id = principal_id

        # assignments_client.list_for_scope returns the root-scope assignment
        mock_assignments_client = mock.Mock()
        mock_assignments_client.list_for_scope.return_value = [mock_assignment]

        # definitions_client returns a subscription-prefixed ID (the usual format)
        mock_definitions_client = mock.Mock()
        mock_definitions_client._config.subscription_id = subscription_id

        result = _search_role_assignments(
            mock_assignments_client,
            mock_definitions_client,
            scope='/',
            assignee_object_id=principal_id,
            role=role_guid,
            include_inherited=False,
            include_groups=False,
        )

        self.assertEqual(1, len(result))
        self.assertEqual(mock_assignment, result[0])
