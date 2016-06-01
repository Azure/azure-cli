# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleAssignmentsOperations, RoleDefinitionsOperations

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command

from ._params import _auth_client_factory

command_table = CommandTable()

factory = lambda _: _auth_client_factory().role_definitions
cli_command(command_table, 'role list', RoleDefinitionsOperations.list, '[Role]', factory)
cli_command(command_table, 'role delete', RoleDefinitionsOperations.delete, 'Result', factory)
cli_command(command_table, 'role show', RoleDefinitionsOperations.get, 'Role', factory)
cli_command(command_table, 'role show-by-id', RoleDefinitionsOperations.get_by_id, 'Role', factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command(command_table, 'role assignment delete', RoleAssignmentsOperations.delete, 'Result', factory)
cli_command(command_table, 'role assignment delete-by-id', RoleAssignmentsOperations.delete_by_id, 'Result', factory)
cli_command(command_table, 'role assignment show', RoleAssignmentsOperations.get, 'Result', factory)
cli_command(command_table, 'role assignment show-by-id', RoleAssignmentsOperations.get_by_id, 'Result', factory)
cli_command(command_table, 'role assignment list', RoleAssignmentsOperations.list, '[RoleAssignment]', factory)
cli_command(command_table, 'role assignment list-for-resource', RoleAssignmentsOperations.list_for_resource, '[RoleAssignment]', factory)
cli_command(command_table, 'role assignment list-for-resource-group', RoleAssignmentsOperations.list_for_resource_group, '[RoleAssignment]', factory)
cli_command(command_table, 'role assignment list-for-scope', RoleAssignmentsOperations.list_for_scope, '[RoleAssignment]', factory)
