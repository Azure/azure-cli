# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Test definitions for deny assignment commands (az role deny-assignment)
# These tests require a subscription with the UserAssignedDenyAssignment feature flag enabled.

import unittest
from unittest import mock

from knack.util import CLIError

from azure.cli.command_modules.role.custom import create_deny_assignment
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk import LiveScenarioTest


class DenyAssignmentListTest(LiveScenarioTest):
    """Tests for az role deny-assignment list — works on any subscription.

    These hit the live Authorization API (no recorded cassettes) so they run only in --live mode
    and are skipped in the standard playback CI pipeline.
    """

    def test_deny_assignment_list(self):
        """List deny assignments at the subscription scope."""
        result = self.cmd('role deny-assignment list').get_output_in_json()
        # Result should be a list (may be empty if no deny assignments exist)
        self.assertIsInstance(result, list)

    def test_deny_assignment_list_with_scope(self):
        """List deny assignments at a specific scope."""
        self.cmd('role deny-assignment list --scope /subscriptions/{sub}',
                 checks=[self.check('type(@)', 'array')])

    def test_deny_assignment_list_with_filter(self):
        """List deny assignments with OData filter."""
        result = self.cmd(
            'role deny-assignment list --filter "atScope()"'
        ).get_output_in_json()
        self.assertIsInstance(result, list)


class DenyAssignmentShowValidationTest(unittest.TestCase):
    """Pure-validation tests for show_deny_assignment that don't require Azure auth.

    Calls show_deny_assignment() directly so the missing-args validation runs before
    any auth client is instantiated.
    """

    def test_deny_assignment_show_missing_args(self):
        """Should raise CLIError if neither --id nor --name+--scope are provided."""
        from azure.cli.command_modules.role.custom import show_deny_assignment
        with self.assertRaisesRegex(CLIError, 'Please provide --id, or both --name and --scope'):
            show_deny_assignment(cmd=None)


class DenyAssignmentCreateTest(unittest.TestCase):

    def setUp(self):
        self.args = {
            'cmd': mock.Mock(cli_ctx=DummyCli()),
            'scope': '/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/test-group',
            'deny_assignment_name': 'Test deny assignment',
            'actions': ['Microsoft.Resources/subscriptions/resourceGroups/write'],
            'assignment_name': '00000000-0000-0000-0000-000000000002',
        }
        patcher = mock.patch('azure.cli.command_modules.role.custom._auth_client_factory', autospec=True)
        self.client_factory = patcher.start()
        self.addCleanup(patcher.stop)
        self.create = self.client_factory.return_value.deny_assignments.create_or_update
        self.create.return_value = mock.sentinel.deny_assignment

    def test_deny_assignment_create_everyone_optional_exclusions(self):
        excluded_id = '00000000-0000-0000-0000-000000000003'
        cases = [
            ({}, []),
            ({'exclude_principal_ids': []}, []),
            ({'exclude_principal_ids': [excluded_id], 'exclude_principal_types': ['User']},
             [{'id': excluded_id, 'type': 'User'}]),
        ]
        for arguments, expected_exclusions in cases:
            with self.subTest(arguments=arguments):
                self.create.reset_mock()
                result = create_deny_assignment(**self.args, **arguments)

                self.assertIs(result, mock.sentinel.deny_assignment)
                self.create.assert_called_once()
                request = self.create.call_args.kwargs
                self.assertEqual(request['scope'], self.args['scope'])
                self.assertEqual(request['deny_assignment_id'], self.args['assignment_name'])
                properties = request['parameters'].as_dict()['properties']
                self.assertEqual(properties['principals'], [
                    {'id': '00000000-0000-0000-0000-000000000000', 'type': 'SystemDefined'}
                ])
                self.assertEqual(properties['excludePrincipals'], expected_exclusions)
                self.assertEqual(properties['permissions'][0]['actions'], self.args['actions'])

    def test_deny_assignment_create_per_principal_optional_exclusions(self):
        principal_id = '00000000-0000-0000-0000-000000000003'
        excluded_id = '00000000-0000-0000-0000-000000000004'
        for excluded_ids in (None, [excluded_id]):
            with self.subTest(excluded_ids=excluded_ids):
                self.create.reset_mock()
                create_deny_assignment(
                    **self.args, principal_id=principal_id, principal_type='ServicePrincipal',
                    exclude_principal_ids=excluded_ids)

                self.create.assert_called_once()
                properties = self.create.call_args.kwargs['parameters'].as_dict()['properties']
                self.assertEqual(properties['principals'], [{'id': principal_id, 'type': 'ServicePrincipal'}])
                expected_exclusions = [{'id': excluded_id, 'type': 'ServicePrincipal'}] if excluded_ids else []
                self.assertEqual(properties['excludePrincipals'], expected_exclusions)

    def test_deny_assignment_create_invalid_principal_arguments(self):
        principal_id = '00000000-0000-0000-0000-000000000003'
        cases = [
            ({'principal_id': principal_id}, '--principal-type is required'),
            ({'principal_type': 'User'}, '--principal-object-id is required'),
            ({'exclude_principal_ids': [principal_id], 'exclude_principal_types': ['User', 'ServicePrincipal']},
             '--exclude-principal-types must have the same number of entries'),
        ]
        for arguments, expected_error in cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(CLIError, expected_error):
                    create_deny_assignment(**self.args, **arguments)
                self.client_factory.assert_not_called()


class DenyAssignmentCrudTest(LiveScenarioTest):
    """Full CRUD tests for user-assigned deny assignments.

    These are LiveScenarioTest because they require:
    - A subscription with UserAssignedDenyAssignment feature flag enabled
    - Real Azure API calls (not in recordings)
    """

    def test_deny_assignment_create_everyone_and_delete(self):
        """Create a deny assignment in Everyone mode (default), show it, then delete it."""
        self.kwargs.update({
            'scope': '/subscriptions/{sub}',
            'name': 'CLI Test Deny Assignment Everyone',
            'action': 'Microsoft.Authorization/roleAssignments/write',
            'exclude_id': self.create_guid()
        })

        # Create in Everyone mode (no --principal-object-id)
        result = self.cmd(
            'role deny-assignment create '
            '--name "{name}" '
            '--scope {scope} '
            '--actions {action} '
            '--exclude-principal-ids {exclude_id} '
            '--exclude-principal-types ServicePrincipal '
            '--description "CLI test deny assignment - Everyone mode"',
            checks=[
                self.check('denyAssignmentName', '{name}'),
                self.exists('name')
            ]
        ).get_output_in_json()

        self.kwargs['da_name'] = result['name']

        # Show by name + scope
        self.cmd(
            'role deny-assignment show --name {da_name} --scope {scope}',
            checks=[
                self.check('denyAssignmentName', '{name}')
            ]
        )

        # List should include our assignment
        list_result = self.cmd(
            'role deny-assignment list --scope {scope}'
        ).get_output_in_json()
        self.assertTrue(any(da.get('name') == self.kwargs['da_name'] for da in list_result))

        # Delete by name + scope
        self.cmd('role deny-assignment delete --name {da_name} --scope {scope} --yes')

    def test_deny_assignment_create_per_principal_and_delete(self):
        """Create a deny assignment targeting a specific User principal, then delete it."""
        self.kwargs.update({
            'scope': '/subscriptions/{sub}',
            'name': 'CLI Test Deny Assignment Per-Principal',
            'action': 'Microsoft.Authorization/roleAssignments/write',
            'principal_id': self.create_guid()
        })

        # Create in per-principal mode
        result = self.cmd(
            'role deny-assignment create '
            '--name "{name}" '
            '--scope {scope} '
            '--actions {action} '
            '--principal-object-id {principal_id} '
            '--principal-type User '
            '--description "CLI test deny assignment - per-principal mode"',
            checks=[
                self.check('denyAssignmentName', '{name}'),
                self.exists('name')
            ]
        ).get_output_in_json()

        self.kwargs['da_name'] = result['name']

        # Delete
        self.cmd('role deny-assignment delete --name {da_name} --scope {scope} --yes')

    def test_deny_assignment_create_per_principal_with_exclusions_and_delete(self):
        """Create a per-principal deny assignment with exclude-principals, then delete it."""
        self.kwargs.update({
            'scope': '/subscriptions/{sub}',
            'name': 'CLI Test Per-Principal With Exclusions',
            'action': 'Microsoft.Authorization/roleAssignments/write',
            'principal_id': self.create_guid(),
            'exclude_id': self.create_guid()
        })

        result = self.cmd(
            'role deny-assignment create '
            '--name "{name}" '
            '--scope {scope} '
            '--actions {action} '
            '--principal-object-id {principal_id} '
            '--principal-type ServicePrincipal '
            '--exclude-principal-ids {exclude_id} '
            '--exclude-principal-types ServicePrincipal '
            '--description "Per-principal with exclusions"',
            checks=[
                self.check('denyAssignmentName', '{name}'),
                self.exists('name')
            ]
        ).get_output_in_json()

        self.kwargs['da_name'] = result['name']

        self.cmd('role deny-assignment delete --name {da_name} --scope {scope} --yes')

    def test_deny_assignment_create_validation_no_actions(self):
        """Should fail if no actions are provided."""
        with self.assertRaises(SystemExit):
            self.cmd(
                'role deny-assignment create '
                '--name "Test" '
                '--scope /subscriptions/{sub} '
                '--exclude-principal-ids 00000000-0000-0000-0000-000000000001'
            )

    def test_deny_assignment_create_validation_read_action(self):
        """Should fail if a read action is provided."""
        with self.assertRaises(SystemExit):
            self.cmd(
                'role deny-assignment create '
                '--name "Test" '
                '--scope /subscriptions/{sub} '
                '--actions "Microsoft.Authorization/roleAssignments/read" '
                '--exclude-principal-ids 00000000-0000-0000-0000-000000000001'
            )

    def test_deny_assignment_create_validation_group_rejected(self):
        """Should fail if Group principal type is specified."""
        with self.assertRaises(SystemExit):
            self.cmd(
                'role deny-assignment create '
                '--name "Test" '
                '--scope /subscriptions/{sub} '
                '--actions "Microsoft.Authorization/roleAssignments/write" '
                '--principal-object-id 00000000-0000-0000-0000-000000000001 '
                '--principal-type Group'
            )

    def test_deny_assignment_create_validation_principal_type_required(self):
        """Should fail if --principal-object-id is given without --principal-type."""
        with self.assertRaises(SystemExit):
            self.cmd(
                'role deny-assignment create '
                '--name "Test" '
                '--scope /subscriptions/{sub} '
                '--actions "Microsoft.Authorization/roleAssignments/write" '
                '--principal-object-id 00000000-0000-0000-0000-000000000001'
            )

    def test_deny_assignment_create_validation_principal_id_required(self):
        """Should fail if --principal-type is given without --principal-object-id."""
        with self.assertRaises(SystemExit):
            self.cmd(
                'role deny-assignment create '
                '--name "Test" '
                '--scope /subscriptions/{sub} '
                '--actions "Microsoft.Authorization/roleAssignments/write" '
                '--principal-type User '
                '--exclude-principal-ids 00000000-0000-0000-0000-000000000001'
            )
