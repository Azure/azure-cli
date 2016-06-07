# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleAssignmentsOperations, RoleDefinitionsOperations

from azure.cli.commands import cli_command

from ._params import _auth_client_factory

factory = lambda _: _auth_client_factory().role_definitions
cli_command('role list', RoleDefinitionsOperations.list, factory)
cli_command('role delete', RoleDefinitionsOperations.delete, factory)
cli_command('role show', RoleDefinitionsOperations.get, factory)
cli_command('role show-by-id', RoleDefinitionsOperations.get_by_id, factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command('role assignment delete', RoleAssignmentsOperations.delete, factory)
cli_command('role assignment delete-by-id', RoleAssignmentsOperations.delete_by_id, factory)
cli_command('role assignment show', RoleAssignmentsOperations.get, factory)
cli_command('role assignment show-by-id', RoleAssignmentsOperations.get_by_id, factory)
cli_command('role assignment list', RoleAssignmentsOperations.list, factory)
cli_command('role assignment list-for-resource', RoleAssignmentsOperations.list_for_resource, factory)
cli_command('role assignment list-for-resource-group', RoleAssignmentsOperations.list_for_resource_group, factory)
cli_command('role assignment list-for-scope', RoleAssignmentsOperations.list_for_scope, factory)
