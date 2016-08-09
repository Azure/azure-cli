#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleDefinitionsOperations
from azure.graphrbac.operations import UsersOperations, GroupsOperations
from azure.cli.commands import cli_command
from azure.cli.commands.arm import register_generic_update

from .custom import (create_role_assignment, list_role_assignments, delete_role_assignments,
                     list_role_definitions, delete_role_definition, create_role_definition,
                     list_sps, list_users, create_user, list_groups, list_apps,
                     create_application, update_application, delete_application, show_application,
                     create_service_principal, show_service_principal, delete_service_principal,
                     create_service_principal_for_rbac, reset_service_principal_credential,
                     _auth_client_factory, _graph_client_factory)

factory = lambda _: _auth_client_factory().role_definitions
simple_output_query = '[*].{Name:properties.roleName, Id:name, Type:properties.type}'
cli_command('role list', list_role_definitions, simple_output_query=simple_output_query)
cli_command('role delete', delete_role_definition)
cli_command('role create', create_role_definition, simple_output_query=simple_output_query)
register_generic_update('role update',
                        RoleDefinitionsOperations.get,
                        RoleDefinitionsOperations.create_or_update,
                        factory)

simple_output_query = '[*].{Name:name, PrincipalName:properties.principalName, Role:properties.roleDefinitionName, Scope:properties.scope}'
factory = lambda _: _auth_client_factory().role_assignments
cli_command('role assignment delete', delete_role_assignments)
cli_command('role assignment list', list_role_assignments,
            simple_output_query='[*].{Name:name, PrincipalName:properties.principalName, Role:properties.roleDefinitionName, Scope:properties.scope}')
cli_command('role assignment create', create_role_assignment,
            simple_output_query="{Name:name, PrincipalId:properties.principalId, Scope:properties.scope}")

factory = lambda _: _graph_client_factory().applications
#for table ouput, display the 1st identifier and replyurl, so all can fit in a row
single_app_table_query = '{DisplayName:displayName, IdentifierUri:identifierUris[0], ObjectId:objectId, ReplyUrl:replyUrls[0]}'
cli_command('ad app create', create_application, factory, simple_output_query=single_app_table_query)
cli_command('ad app delete', delete_application, factory)
cli_command('ad app list', list_apps, factory, simple_output_query='[*].'+ single_app_table_query)
cli_command('ad app show', show_application, factory, simple_output_query=single_app_table_query)
cli_command('ad app update', update_application, factory)

factory = lambda _: _graph_client_factory().service_principals
#for table ouput, display the 1st principal name, so all can fit in a row
single_sp_table_query = '{DisplayName:displayName, ServicePrincipalName:servicePrincipalNames[0], ObjectId:objectId}'
cli_command('ad sp create', create_service_principal, simple_output_query=single_sp_table_query)
cli_command('ad sp delete', delete_service_principal, factory)
#paging is broken at SDK https://github.com/Azure/azure-cli/issues/540
cli_command('ad sp list', list_sps, factory, simple_output_query='[*].'+single_sp_table_query)
cli_command('ad sp show', show_service_principal, factory, simple_output_query=single_sp_table_query)
#RBAC related
cli_command('ad sp create-for-rbac', create_service_principal_for_rbac)
cli_command('ad sp reset-credentials', reset_service_principal_credential)

factory = lambda _: _graph_client_factory().users
cli_command('ad user delete', UsersOperations.delete, factory)
cli_command('ad user show', UsersOperations.get, factory)
#paging is broken at SDK https://github.com/Azure/azure-cli/issues/540
cli_command('ad user list', list_users, factory)
cli_command('ad user create', create_user, factory)

factory = lambda _: _graph_client_factory().groups
cli_command('ad group delete', GroupsOperations.delete, factory)
cli_command('ad group show', GroupsOperations.get, factory)
#paging is broken at SDK https://github.com/Azure/azure-cli/issues/540
cli_command('ad group list', list_groups, factory)
