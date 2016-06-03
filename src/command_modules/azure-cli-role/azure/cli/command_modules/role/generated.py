# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleAssignmentsOperations, RoleDefinitionsOperations

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command

from ._params import _auth_client_factory

command_table = CommandTable()

factory = lambda _: _auth_client_factory().role_definitions
cli_command(command_table, 'role list', RoleDefinitionsOperations.list, factory)
cli_command(command_table, 'role delete', RoleDefinitionsOperations.delete, factory)
cli_command(command_table, 'role show', RoleDefinitionsOperations.get, factory)
cli_command(command_table, 'role show-by-id', RoleDefinitionsOperations.get_by_id, factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command(command_table, 'role assignment delete', RoleAssignmentsOperations.delete, factory)
cli_command(command_table, 'role assignment delete-by-id', RoleAssignmentsOperations.delete_by_id, factory)
cli_command(command_table, 'role assignment show', RoleAssignmentsOperations.get, factory)
cli_command(command_table, 'role assignment show-by-id', RoleAssignmentsOperations.get_by_id, factory)
cli_command(command_table, 'role assignment list', RoleAssignmentsOperations.list, factory)
cli_command(command_table, 'role assignment list-for-resource', RoleAssignmentsOperations.list_for_resource, factory)
cli_command(command_table, 'role assignment list-for-resource-group', RoleAssignmentsOperations.list_for_resource_group, factory)
cli_command(command_table, 'role assignment list-for-scope', RoleAssignmentsOperations.list_for_scope, factory)
