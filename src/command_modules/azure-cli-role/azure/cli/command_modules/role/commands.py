# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict

from azure.cli.core.profiles import PROFILE_TYPE
from azure.cli.core.commands import CliCommandType

from azure.cli.core.util import empty_on_404

from ._client_factory import (_auth_client_factory, _graph_client_factory)


def transform_definition_list(result):
    return [OrderedDict([('Name', r['roleName']), ('Type', r['type']),
                         ('Description', r['description'])]) for r in result]


def transform_assignment_list(result):
    return [OrderedDict([('Principal', r['principalName']),
                         ('Role', r['roleDefinitionName']),
                         ('Scope', r['scope'])]) for r in result]


def get_role_definition_op(operation_name):
    return 'azure.mgmt.authorization.operations.role_definitions_operations' \
           '#RoleDefinitionsOperations.{}'.format(operation_name)


def get_role_definitions(cli_ctx, _):
    return _auth_client_factory(cli_ctx, ).role_definitions


def get_graph_client_applications(cli_ctx, _):
    return _graph_client_factory(cli_ctx).applications


def get_graph_client_service_principals(cli_ctx, _):
    return _graph_client_factory(cli_ctx).service_principals


def get_graph_client_users(cli_ctx, _):
    return _graph_client_factory(cli_ctx).users


def get_graph_client_groups(cli_ctx, _):
    return _graph_client_factory(cli_ctx).groups


# pylint: disable=line-too-long
def load_command_table(self, _):

    role_users_sdk = CliCommandType(
        operations_tmpl='azure.graphrbac.operations.users_operations#UsersOperations.{}',
        client_factory=get_graph_client_users
    )

    role_group_sdk = CliCommandType(
        operations_tmpl='azure.graphrbac.operations.groups_operations#GroupsOperations.{}',
        client_factory=get_graph_client_groups
    )

    with self.command_group('role definition') as g:
        g.custom_command('list', 'list_role_definitions', table_transformer=transform_definition_list)
        g.custom_command('delete', 'delete_role_definition')
        g.custom_command('create', 'create_role_definition')
        g.custom_command('update', 'update_role_definition')

    with self.command_group('role assignment') as g:
        g.custom_command('delete', 'delete_role_assignments')
        g.custom_command('list', 'list_role_assignments', table_transformer=transform_assignment_list)
        g.custom_command('create', 'create_role_assignment')
        g.custom_command('list-changelogs', 'list_role_assignment_change_logs')

    with self.command_group('ad app', client_factory=get_graph_client_applications, resource_type=PROFILE_TYPE, min_api='2017-03-10') as g:
        g.custom_command('create', 'create_application')
        g.custom_command('delete', 'delete_application')
        g.custom_command('list', 'list_apps')
        g.custom_command('show', 'show_application', exception_handler=empty_on_404)
        g.custom_command('update', 'update_application')

    with self.command_group('ad sp', resource_type=PROFILE_TYPE, min_api='2017-03-10') as g:
        g.custom_command('create', 'create_service_principal')
        g.custom_command('delete', 'delete_service_principal')
        g.custom_command('list', 'list_sps', client_factory=get_graph_client_service_principals)
        g.custom_command('show', 'show_service_principal', client_factory=get_graph_client_service_principals, exception_handler=empty_on_404)

    # RBAC related
    with self.command_group('ad sp') as g:
        g.custom_command('create-for-rbac', 'create_service_principal_for_rbac')
        g.custom_command('reset-credentials', 'reset_service_principal_credential', deprecate_info='ad sp credential reset')
        g.custom_command('credential reset', 'reset_service_principal_credential')
        g.custom_command('credential list', 'list_service_principal_credentials')
        g.custom_command('credential delete', 'delete_service_principal_credential')

    with self.command_group('ad user', role_users_sdk) as g:
        g.command('delete', 'delete')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.custom_command('list', 'list_users', client_factory=get_graph_client_users)
        g.custom_command('create', 'create_user', client_factory=get_graph_client_users, doc_string_source='azure.graphrbac.models#UserCreateParameters')

    with self.command_group('ad group', role_group_sdk) as g:
        g.custom_command('create', 'create_group', client_factory=get_graph_client_groups)
        g.command('delete', 'delete')
        g.command('show', 'get', exception_handler=empty_on_404)
        g.command('get-member-groups', 'get_member_groups')
        g.custom_command('list', 'list_groups', client_factory=get_graph_client_groups)

    with self.command_group('ad group member', role_group_sdk) as g:
        g.command('list', 'get_group_members')
        g.command('add', 'add_member')
        g.command('remove', 'remove_member')
        g.custom_command('check', 'check_group_membership', client_factory=get_graph_client_groups)
