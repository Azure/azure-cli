# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from collections import OrderedDict

from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from .custom import (_auth_client_factory, _graph_client_factory)

def transform_definition_list(result):
    return [OrderedDict([('Name', r['properties']['roleName']), ('Type', r['properties']['type']), ('Descritpion', r['properties']['description'])]) for r in result]

def transform_assignment_list(result):
    return [OrderedDict([('Principal', r['properties']['principalName']), ('Role', r['properties']['roleDefinitionName']), ('Scope', r['properties']['scope'])]) for r in result]

factory = lambda _: _auth_client_factory().role_definitions
cli_command(__name__, 'role definition list', 'azure.cli.command_modules.role.custom#list_role_definitions', table_transformer=transform_definition_list)
cli_command(__name__, 'role definition delete', 'azure.cli.command_modules.role.custom#delete_role_definition')
cli_command(__name__, 'role definition create', 'azure.cli.command_modules.role.custom#create_role_definition')
cli_generic_update_command(__name__, 'role definition update',
                           'azure.mgmt.authorization.operations.role_definitions_operations#RoleDefinitionsOperations.get',
                           'azure.mgmt.authorization.operations.role_definitions_operations#RoleDefinitionsOperations.create_or_update',
                           factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command(__name__, 'role assignment delete', 'azure.cli.command_modules.role.custom#delete_role_assignments')
cli_command(__name__, 'role assignment list', 'azure.cli.command_modules.role.custom#list_role_assignments', table_transformer=transform_assignment_list)
cli_command(__name__, 'role assignment create', 'azure.cli.command_modules.role.custom#create_role_assignment')

factory = lambda _: _graph_client_factory().applications
cli_command(__name__, 'ad app create', 'azure.cli.command_modules.role.custom#create_application', factory)
cli_command(__name__, 'ad app delete', 'azure.cli.command_modules.role.custom#delete_application', factory)
cli_command(__name__, 'ad app list', 'azure.cli.command_modules.role.custom#list_apps', factory)
cli_command(__name__, 'ad app show', 'azure.cli.command_modules.role.custom#show_application', factory)
cli_command(__name__, 'ad app update', 'azure.cli.command_modules.role.custom#update_application', factory)

factory = lambda _: _graph_client_factory().service_principals
cli_command(__name__, 'ad sp create', 'azure.cli.command_modules.role.custom#create_service_principal')
cli_command(__name__, 'ad sp delete', 'azure.cli.command_modules.role.custom#delete_service_principal', factory)
cli_command(__name__, 'ad sp list', 'azure.cli.command_modules.role.custom#list_sps', factory)
cli_command(__name__, 'ad sp show', 'azure.cli.command_modules.role.custom#show_service_principal', factory)
#RBAC related
cli_command(__name__, 'ad sp create-for-rbac', 'azure.cli.command_modules.role.custom#create_service_principal_for_rbac')
cli_command(__name__, 'ad sp reset-credentials', 'azure.cli.command_modules.role.custom#reset_service_principal_credential')

factory = lambda _: _graph_client_factory().users
cli_command(__name__, 'ad user delete', 'azure.graphrbac.operations.users_operations#UsersOperations.delete', factory)
cli_command(__name__, 'ad user show', 'azure.graphrbac.operations.users_operations#UsersOperations.get', factory)
cli_command(__name__, 'ad user list', 'azure.cli.command_modules.role.custom#list_users', factory)
cli_command(__name__, 'ad user create', 'azure.cli.command_modules.role.custom#create_user', factory)

factory = lambda _: _graph_client_factory().groups
cli_command(__name__, 'ad group delete', 'azure.graphrbac.operations.groups_operations#GroupsOperations.delete', factory)
cli_command(__name__, 'ad group show', 'azure.graphrbac.operations.groups_operations#GroupsOperations.get', factory)
cli_command(__name__, 'ad group list', 'azure.cli.command_modules.role.custom#list_groups', factory)
