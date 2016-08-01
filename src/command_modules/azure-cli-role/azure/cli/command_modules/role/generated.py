#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from __future__ import print_function

from azure.mgmt.authorization.operations import RoleAssignmentsOperations, RoleDefinitionsOperations
from azure.graphrbac.operations import (ApplicationsOperations, ServicePrincipalsOperations,
                                        UsersOperations, GroupsOperations)
from azure.cli.commands import cli_command
from azure.cli.commands.arm import register_generic_update

from .custom import (create_role_assignment, list_sps, list_users, create_user, list_groups, list_apps,
                     _auth_client_factory, _graph_client_factory)

factory = lambda _: _auth_client_factory().role_definitions
cli_command('role list', RoleDefinitionsOperations.list, factory)
cli_command('role delete', RoleDefinitionsOperations.delete, factory)
cli_command('role show', RoleDefinitionsOperations.get, factory)
cli_command('role show-by-id', RoleDefinitionsOperations.get_by_id, factory)
register_generic_update('role update',
                        RoleDefinitionsOperations.get,
                        RoleDefinitionsOperations.create_or_update,
                        factory)

factory = lambda _: _auth_client_factory().role_assignments
cli_command('role assignment delete', RoleAssignmentsOperations.delete, factory)
cli_command('role assignment delete-by-id', RoleAssignmentsOperations.delete_by_id, factory)
cli_command('role assignment show', RoleAssignmentsOperations.get, factory)
cli_command('role assignment show-by-id', RoleAssignmentsOperations.get_by_id, factory)
cli_command('role assignment list', RoleAssignmentsOperations.list, factory)
cli_command('role assignment list-for-resource', RoleAssignmentsOperations.list_for_resource, factory)
cli_command('role assignment list-for-resource-group', RoleAssignmentsOperations.list_for_resource_group, factory)
cli_command('role assignment list-for-scope', RoleAssignmentsOperations.list_for_scope, factory)
cli_command('role assignment create', create_role_assignment)

factory = lambda _: _graph_client_factory().applications
cli_command('ad app delete', ApplicationsOperations.delete, factory)
cli_command('ad app show', ApplicationsOperations.get, factory)
cli_command('ad app list', list_apps, factory)

factory = lambda _: _graph_client_factory().service_principals
cli_command('ad sp delete', ServicePrincipalsOperations.delete, factory)
cli_command('ad sp show', ServicePrincipalsOperations.get, factory)
#paging is broken at SDK https://github.com/Azure/azure-cli/issues/540
cli_command('ad sp list', list_sps, factory)

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
