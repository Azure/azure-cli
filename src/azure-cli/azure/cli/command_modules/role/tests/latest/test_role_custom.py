# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import uuid
import pytest
from unittest import mock

from azure.cli.command_modules.role.custom import (
    _resolve_role_id, _search_role_assignments, _get_role_definition_id
)

# pylint: disable=line-too-long


class TestGetRoleDefinitionId:
    """Tests for _get_role_definition_id helper function."""

    @pytest.mark.parametrize("resource_id,expected", [
        # Tenant-scoped format
        ('/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7',
         uuid.UUID('acdd72a7-3385-48ef-bd42-f606fba81ae7')),
        # Subscription-scoped format
        ('/subscriptions/sub1/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c',
         uuid.UUID('b24988ac-6180-42a0-ab88-20f7382dd24c')),
        # None returns None
        (None, None),
        # Empty string returns None (not a valid GUID)
        ('', None),
        # Invalid GUID in last segment returns None
        ('/providers/Microsoft.Authorization/roleDefinitions/not-a-guid', None),
        # Malformed path with extra segments still extracts last segment if valid GUID
        ('/some/path/acdd72a7-3385-48ef-bd42-f606fba81ae7',
         uuid.UUID('acdd72a7-3385-48ef-bd42-f606fba81ae7')),
    ])
    def test_extracts_guid_from_role_definition_id(self, resource_id, expected):
        """Extracts the GUID from various role definition ID formats."""
        result = _get_role_definition_id(resource_id)
        assert result == expected

    def test_returns_uuid_for_case_insensitive_comparison(self):
        """Returns UUID objects that compare equal regardless of case."""
        lower = _get_role_definition_id('/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7')
        upper = _get_role_definition_id('/providers/Microsoft.Authorization/roleDefinitions/ACDD72A7-3385-48EF-BD42-F606FBA81AE7')
        assert lower == upper
        assert isinstance(lower, uuid.UUID)
        assert isinstance(upper, uuid.UUID)


class TestResolveRoleId:
    """Tests for _resolve_role_id function."""

    @pytest.fixture
    def mock_client(self):
        client = mock.Mock()
        client._config.subscription_id = '00000000-0000-0000-0000-000000000000'
        return client

    @pytest.mark.parametrize("role_input,expected_output", [
        # GUID returns tenant format
        ('b24988ac-6180-42a0-ab88-20f738123456',
         '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f738123456'),
        # Subscription-scoped ID returned as-is
        ('/subscriptions/sub1/providers/Microsoft.Authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456',
         '/subscriptions/sub1/providers/Microsoft.Authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456'),
        # Tenant-scoped ID returned as-is
        ('/providers/Microsoft.Authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456',
         '/providers/Microsoft.Authorization/roleDefinitions/5370bbf4-6b73-4417-969b-8f2e6e123456'),
    ])
    def test_resolve_role_id_formats(self, mock_client, role_input, expected_output):
        """Role IDs (GUID, subscription-scoped, tenant-scoped) are resolved correctly."""
        result = _resolve_role_id(role_input, '/subscriptions/sub1', mock_client)
        assert result == expected_output

    def test_role_name_queries_api(self, mock_client):
        """Role name triggers API lookup and returns the role definition ID from API."""
        mock_role_def = mock.Mock()
        mock_role_def.id = '/subscriptions/123/providers/Microsoft.Authorization/roleDefinitions/acdd72a7'
        mock_client.list.return_value = [mock_role_def]

        result = _resolve_role_id('Reader', '/subscriptions/123', mock_client)

        assert result == mock_role_def.id
        mock_client.list.assert_called_once_with('/subscriptions/123', "roleName eq 'Reader'")

    @pytest.mark.parametrize("api_response,error_contains", [
        ([], "doesn't exist"),  # Not found
        ([mock.Mock(id='id1'), mock.Mock(id='id2')], "More than one role"),  # Multiple matches
    ])
    def test_role_name_error_cases(self, mock_client, api_response, error_contains):
        """Role name lookup raises CLIError for not found or multiple matches."""
        from knack.util import CLIError
        mock_client.list.return_value = api_response

        with pytest.raises(CLIError, match=error_contains):
            _resolve_role_id('SomeRole', '/subscriptions/123', mock_client)


class TestSearchRoleAssignments:
    """Tests for _search_role_assignments function, focusing on role filtering."""

    @pytest.fixture
    def mock_clients(self):
        assignments_client = mock.Mock()
        definitions_client = mock.Mock()
        definitions_client._config.subscription_id = '00000000-0000-0000-0000-000000000000'
        return assignments_client, definitions_client

    @staticmethod
    def _create_assignment(scope, role_definition_id, principal_id='principal-1'):
        assignment = mock.Mock()
        assignment.scope = scope
        assignment.role_definition_id = role_definition_id
        assignment.principal_id = principal_id
        return assignment

    @pytest.mark.parametrize("scope,role_def_format", [
        # Root scope with tenant-format role definition ID
        ('/', '/providers/Microsoft.Authorization/roleDefinitions/{guid}'),
        # Management group scope with tenant-format role definition ID
        ('/providers/Microsoft.Management/managementGroups/my-mg',
         '/providers/Microsoft.Authorization/roleDefinitions/{guid}'),
        # Subscription scope with subscription-format role definition ID
        ('/subscriptions/00000000-0000-0000-0000-000000000000',
         '/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/{guid}'),
    ])
    def test_guid_filter_matches_across_scopes(self, mock_clients, scope, role_def_format):
        """GUID filter matches assignments at various scopes with different roleDefinitionId formats."""
        assignments_client, definitions_client = mock_clients
        role_guid = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
        role_def_id = role_def_format.format(guid=role_guid)

        assignments_client.list_for_scope.return_value = [
            self._create_assignment(scope, role_def_id),
        ]

        result = _search_role_assignments(
            assignments_client, definitions_client,
            scope=scope, assignee_object_id=None, role=role_guid,
            include_inherited=False, include_groups=False
        )

        assert len(result) == 1

    def test_different_role_guid_does_not_match(self, mock_clients):
        """Assignments with different role GUIDs are filtered out."""
        assignments_client, definitions_client = mock_clients
        filter_guid = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'
        other_guid = 'b24988ac-6180-42a0-ab88-20f7382dd24c'

        assignments_client.list_for_scope.return_value = [
            self._create_assignment('/', f'/providers/Microsoft.Authorization/roleDefinitions/{other_guid}'),
        ]

        result = _search_role_assignments(
            assignments_client, definitions_client,
            scope='/', assignee_object_id=None, role=filter_guid,
            include_inherited=False, include_groups=False
        )

        assert len(result) == 0

    def test_none_role_definition_id_is_skipped(self, mock_clients):
        """Assignments with None role_definition_id are skipped when filtering by role."""
        assignments_client, definitions_client = mock_clients
        role_guid = 'acdd72a7-3385-48ef-bd42-f606fba81ae7'

        assignment_with_none = self._create_assignment('/', None)
        assignment_with_role = self._create_assignment(
            '/', f'/providers/Microsoft.Authorization/roleDefinitions/{role_guid}')
        assignments_client.list_for_scope.return_value = [assignment_with_none, assignment_with_role]

        result = _search_role_assignments(
            assignments_client, definitions_client,
            scope='/', assignee_object_id=None, role=role_guid,
            include_inherited=False, include_groups=False
        )

        assert len(result) == 1
        assert result[0].role_definition_id is not None