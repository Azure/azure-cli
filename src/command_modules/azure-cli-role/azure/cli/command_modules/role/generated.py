from __future__ import print_function

from azure.mgmt.authorization.operations import RoleAssignmentsOperations, RoleDefinitionsOperations

from azure.cli.commands import CommandTable
from azure.cli.commands._auto_command import build_operation, CommandDefinition

from ._params import PARAMETER_ALIASES, _auth_client_factory

command_table = CommandTable()

build_operation(
    'role', 'role_definitions', _auth_client_factory,
    [
        CommandDefinition(RoleDefinitionsOperations.list, '[Role]'),
        #CommandDefinition(RoleDefinitionsOperations.create_or_update, 'Result', 'create'),
        #CommandDefinition(RoleDefinitionsOperations.delete, 'Result'),
        CommandDefinition(RoleDefinitionsOperations.get, 'Role', 'show'),
        CommandDefinition(RoleDefinitionsOperations.get_by_id, 'Role', 'show-by-id')
    ], command_table, PARAMETER_ALIASES)

build_operation(
    'role assignment', 'role_assignments', _auth_client_factory,
    [
        #CommandDefinition(RoleAssignmentsOperations.create, 'Result'),
        #CommandDefinition(RoleAssignmentsOperations.create_by_id, 'Result'),
        #CommandDefinition(RoleAssignmentsOperations.delete, 'Result'),
        #CommandDefinition(RoleAssignmentsOperations.delete_by_id, 'Result'),
        CommandDefinition(RoleAssignmentsOperations.get, 'Result', 'show'),
        CommandDefinition(RoleAssignmentsOperations.get_by_id, 'Result', 'show-by-id'),
        CommandDefinition(RoleAssignmentsOperations.list, '[RoleAssignment]'),
        CommandDefinition(RoleAssignmentsOperations.list_for_resource, '[RoleAssignment]'),
        CommandDefinition(RoleAssignmentsOperations.list_for_resource_group, '[RoleAssignment]'),
        CommandDefinition(RoleAssignmentsOperations.list_for_scope, '[RoleAssignment]')
    ], command_table, PARAMETER_ALIASES)
