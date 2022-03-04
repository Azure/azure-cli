# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from collections import OrderedDict

from azure.cli.core.profiles import PROFILE_TYPE
from azure.cli.core.commands import CliCommandType

from ._client_factory import _auth_client_factory, _graph_client_factory

from ._validators import process_assignment_namespace, validate_change_password


def transform_definition_list(result):
    return [OrderedDict([('Name', r['roleName']), ('Type', r['type']),
                         ('Description', r['description'])]) for r in result]


def transform_assignment_list(result):
    return [OrderedDict([('Principal', r['principalName']),
                         ('Role', r['roleDefinitionName']),
                         ('Scope', r['scope'])]) for r in result]


def get_graph_object_transformer(object_type):
    selected_keys_for_type = {
        'app': ('displayName', 'id', 'appId', 'createdDateTime'),
        'sp': ('displayName', 'id', 'appId', 'createdDateTime')
    }

    selected_keys = selected_keys_for_type[object_type]

    def _transform_graph_object(result):
        # Graph API's id (GUID) is different from ARM's id (/subscriptions/...).
        # It should be shown.
        from knack.output import _TableOutput
        _TableOutput.SKIP_KEYS.remove('id')

        sorted_list = sorted(result, key=lambda app: app['displayName'])
        return [{k: r.get(k) for k in selected_keys} for r in sorted_list]

    return _transform_graph_object


def transform_graph_objects_with_cred(result):
    # here we will convert utf16 encoded custom key id back to the plain text
    # we will handle single object from "show" cmd, object list from "list" cmd, and cred object itself
    if not result:
        return result
    from msrest.paging import Paged
    from azure.graphrbac.models import PasswordCredential

    def _patch_creds(creds):
        for c in creds:
            custom_key_id = getattr(c, 'custom_key_identifier', None)
            if custom_key_id:
                try:
                    c.custom_key_identifier = custom_key_id.decode('utf-16')
                except Exception:  # pylint: disable=broad-except
                    c.custom_key_identifier = None
        return creds

    singular = False
    if isinstance(result, Paged):
        result = list(result)

    if not isinstance(result, list):
        singular = True
        result = [result]

    for r in result:
        if getattr(r, 'password_credentials', None):
            _patch_creds(r.password_credentials)

        if isinstance(r, PasswordCredential):
            _patch_creds([r])
    return result[0] if singular else result


def graph_err_handler(ex):
    from azure.graphrbac.models import GraphErrorException
    if isinstance(ex, GraphErrorException):
        from knack.util import CLIError
        raise CLIError(ex.message)
    raise ex


def get_role_definitions(cli_ctx, _):
    return _auth_client_factory(cli_ctx, ).role_definitions


def get_graph_client(cli_ctx, _):
    return _graph_client_factory(cli_ctx)


# pylint: disable=line-too-long, too-many-statements
def load_command_table(self, _):

    role_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.role.custom#{}')

    with self.command_group('role definition') as g:
        g.custom_command('list', 'list_role_definitions', table_transformer=transform_definition_list)
        g.custom_command('delete', 'delete_role_definition')
        g.custom_command('create', 'create_role_definition')
        g.custom_command('update', 'update_role_definition')

    with self.command_group('role assignment') as g:
        g.custom_command('delete', 'delete_role_assignments', validator=process_assignment_namespace)
        g.custom_command('list', 'list_role_assignments', validator=process_assignment_namespace, table_transformer=transform_assignment_list)
        g.custom_command('create', 'create_role_assignment', validator=process_assignment_namespace)
        g.custom_command('update', 'update_role_assignment', min_api='2020-04-01-preview')
        g.custom_command('list-changelogs', 'list_role_assignment_change_logs')

    with self.command_group('ad app', client_factory=get_graph_client, resource_type=PROFILE_TYPE,
                            exception_handler=graph_err_handler, transform=transform_graph_objects_with_cred) as g:
        g.custom_command('create', 'create_application')
        g.custom_command('delete', 'delete_application')
        g.custom_command('list', 'list_apps', table_transformer=get_graph_object_transformer('app'))
        g.custom_show_command('show', 'show_application')
        g.custom_command('permission grant', 'grant_application')
        g.custom_command('permission list', 'list_permissions')
        g.custom_command('permission add', 'add_permission')
        g.custom_command('permission delete', 'delete_permission')
        g.custom_command('permission list-grants', 'list_permission_grants')
        g.custom_command('permission admin-consent', 'admin_consent')
        g.generic_update_command('update', setter_name='patch_application', setter_type=role_custom,
                                 getter_name='show_application', getter_type=role_custom,
                                 custom_func_name='update_application', custom_func_type=role_custom)
        g.custom_command('credential reset', 'reset_application_credential')
        g.custom_command('credential list', 'list_application_credentials')
        g.custom_command('credential delete', 'delete_application_credential')

    with self.command_group('ad app owner', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('list', 'list_application_owners')
        g.custom_command('add', 'add_application_owner')
        g.custom_command('remove', 'remove_application_owner')

    with self.command_group('ad sp', client_factory=get_graph_client, resource_type=PROFILE_TYPE, exception_handler=graph_err_handler,
                            transform=transform_graph_objects_with_cred) as g:
        g.custom_command('create', 'create_service_principal')
        g.custom_command('delete', 'delete_service_principal')
        g.custom_command('list', 'list_sps', table_transformer=get_graph_object_transformer('sp'))
        g.custom_show_command('show', 'show_service_principal')
        g.generic_update_command('update', getter_name='show_service_principal', getter_type=role_custom,
                                 setter_name='patch_service_principal', setter_type=role_custom)

    with self.command_group('ad sp owner', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('list', 'list_service_principal_owners')

    # RBAC related
    with self.command_group('ad sp', client_factory=get_graph_client, exception_handler=graph_err_handler, transform=transform_graph_objects_with_cred) as g:
        g.custom_command('create-for-rbac', 'create_service_principal_for_rbac')
        g.custom_command('credential reset', 'reset_service_principal_credential')
        g.custom_command('credential list', 'list_service_principal_credentials')
        g.custom_command('credential delete', 'delete_service_principal_credential')

    with self.command_group('ad user', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('delete', 'delete_user')
        g.custom_show_command('show', 'show_user')
        g.custom_command('list', 'list_users')
        g.custom_command('get-member-groups', 'get_user_member_groups')
        g.custom_command('create', 'create_user')
        g.custom_command('update', 'update_user', validator=validate_change_password)

    with self.command_group('ad signed-in-user', client_factory=get_graph_client, exception_handler=graph_err_handler,
                            transform=transform_graph_objects_with_cred) as g:
        g.custom_command('show', 'show_signed_in_user')
        g.custom_command('list-owned-objects', 'list_owned_objects')

    with self.command_group('ad group', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('delete', 'delete_group')
        g.custom_show_command('show', 'get_group')
        g.custom_command('get-member-groups', 'get_member_groups')
        g.custom_command('list', 'list_groups')
        g.custom_command('create', 'create_group')

    with self.command_group('ad group owner', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('list', 'list_group_owners')
        g.custom_command('add', 'add_group_owner')
        g.custom_command('remove', 'remove_group_owner')

    with self.command_group('ad group member', client_factory=get_graph_client, exception_handler=graph_err_handler) as g:
        g.custom_command('list', 'list_group_members')
        g.custom_command('add', 'add_group_member')
        g.custom_command('remove', 'remove_group_member')
        g.custom_command('check', 'check_group_membership')
