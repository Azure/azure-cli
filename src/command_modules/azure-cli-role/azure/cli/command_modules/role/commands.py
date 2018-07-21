# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict

from azure.cli.core.profiles import PROFILE_TYPE
from azure.cli.core.commands import CliCommandType

from ._client_factory import (_auth_client_factory, _graph_client_factory)


def transform_definition_list(result):
    return [OrderedDict([('Name', r['roleName']), ('Type', r['type']),
                         ('Description', r['description'])]) for r in result]


def transform_assignment_list(result):
    return [OrderedDict([('Principal', r['principalName']),
                         ('Role', r['roleDefinitionName']),
                         ('Scope', r['scope'])]) for r in result]


def graph_err_handler(ex):
    from azure.graphrbac.models.graph_error import GraphErrorException
    if isinstance(ex, GraphErrorException):
        from knack.util import CLIError
        raise CLIError(ex.message)
    raise ex


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

    role_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.role.custom#{}')

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

    with self.command_group('ad app', client_factory=get_graph_client_applications, resource_type=PROFILE_TYPE,
                            exception_handler=graph_err_handler) as g:
        g.custom_command('create', 'create_application')
        g.custom_command('delete', 'delete_application')
        g.custom_command('list', 'list_apps')
        g.custom_show_command('show', 'show_application')
        g.generic_update_command('update', setter_name='patch_application', setter_type=role_custom,
                                 getter_name='show_application', getter_type=role_custom,
                                 custom_func_name='update_application', custom_func_type=role_custom)

    with self.command_group('ad sp', resource_type=PROFILE_TYPE, exception_handler=graph_err_handler) as g:
        g.custom_command('create', 'create_service_principal')
        g.custom_command('delete', 'delete_service_principal')
        g.custom_command('list', 'list_sps', client_factory=get_graph_client_service_principals)
        g.custom_show_command('show', 'show_service_principal', client_factory=get_graph_client_service_principals)

    # RBAC related
    with self.command_group('ad sp', exception_handler=graph_err_handler) as g:
        g.custom_command('create-for-rbac', 'create_service_principal_for_rbac')
        g.custom_command('credential reset', 'reset_service_principal_credential')
        g.custom_command('credential list', 'list_service_principal_credentials')
        g.custom_command('credential delete', 'delete_service_principal_credential')

    with self.command_group('ad user', role_users_sdk, exception_handler=graph_err_handler) as g:
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_users', client_factory=get_graph_client_users)
        g.custom_command('create', 'create_user', client_factory=get_graph_client_users, doc_string_source='azure.graphrbac.models#UserCreateParameters')

    with self.command_group('ad group', role_group_sdk, exception_handler=graph_err_handler) as g:
        g.custom_command('create', 'create_group', client_factory=get_graph_client_groups)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('get-member-groups', 'get_member_groups')
        g.custom_command('list', 'list_groups', client_factory=get_graph_client_groups)

    with self.command_group('ad group member', role_group_sdk, exception_handler=graph_err_handler) as g:
        g.command('list', 'get_group_members')
        g.command('add', 'add_member')
        g.command('remove', 'remove_member')
        g.custom_command('check', 'check_group_membership', client_factory=get_graph_client_groups)
