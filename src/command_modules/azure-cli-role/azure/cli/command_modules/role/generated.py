#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleDefinitionsOperations
from azure.graphrbac.operations import UsersOperations, GroupsOperations
from azure.cli.core.commands import cli_command
from azure.cli.core.commands.arm import cli_generic_update_command

from .custom import (create_role_assignment, list_role_assignments, delete_role_assignments,
                     list_role_definitions, delete_role_definition, create_role_definition,
                     list_sps, list_users, create_user, list_groups, list_apps,
                     create_application, update_application, delete_application, show_application,
                     create_service_principal, show_service_principal, delete_service_principal,
                     create_service_principal_for_rbac, reset_service_principal_credential,
                     _auth_client_factory, _graph_client_factory)

factory = lambda _: _auth_client_factory().role_definitions
cli_command('role definition list', list_role_definitions)
cli_command('role definition delete', delete_role_definition)
cli_command('role definition create', create_role_definition)
cli_generic_update_command('role definition update',
                           RoleDefinitionsOperations.get,
                           RoleDefinitionsOperations.create_or_update,
                           factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command('role assignment delete', delete_role_assignments)
cli_command('role assignment list', list_role_assignments)
cli_command('role assignment create', create_role_assignment)

factory = lambda _: _graph_client_factory().applications
cli_command('ad app create', create_application, factory)
cli_command('ad app delete', delete_application, factory)
cli_command('ad app list', list_apps, factory)
cli_command('ad app show', show_application, factory)
cli_command('ad app update', update_application, factory)

factory = lambda _: _graph_client_factory().service_principals
cli_command('ad sp create', create_service_principal)
cli_command('ad sp delete', delete_service_principal, factory)
cli_command('ad sp list', list_sps, factory)
cli_command('ad sp show', show_service_principal, factory)
#RBAC related
cli_command('ad sp create-for-rbac', create_service_principal_for_rbac)
cli_command('ad sp reset-credentials', reset_service_principal_credential)

factory = lambda _: _graph_client_factory().users
cli_command('ad user delete', UsersOperations.delete, factory)
cli_command('ad user show', UsersOperations.get, factory)
cli_command('ad user list', list_users, factory)
cli_command('ad user create', create_user, factory)

factory = lambda _: _graph_client_factory().groups
cli_command('ad group delete', GroupsOperations.delete, factory)
cli_command('ad group show', GroupsOperations.get, factory)
cli_command('ad group list', list_groups, factory)
