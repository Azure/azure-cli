# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType

from azure.cli.core.commands.parameters import get_enum_type, get_three_state_flag
from azure.cli.core.commands.validators import validate_file_or_dict

from azure.cli.command_modules.role._completers import get_role_definition_name_completion_list
from azure.cli.command_modules.role._validators import validate_group, validate_member_id, validate_cert, VARIANT_GROUP_ID_ARGS

name_arg_type = CLIArgumentType(options_list=('--name', '-n'), metavar='NAME')


# pylint: disable=too-many-statements
def load_arguments(self, _):
    with self.argument_context('ad') as c:
        c.argument('_subscription')  # hide global subscription param

    with self.argument_context('ad app') as c:
        c.argument('app_id', help='application id')
        c.argument('application_object_id', options_list=('--object-id',))
        c.argument('display_name', help='the display name of the application')
        c.argument('homepage', help='the url where users can sign in and use your app.')
        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id')
        c.argument('identifier_uris', nargs='+', help='space-separated unique URIs that Azure AD can use for this app.')
        c.argument('reply_urls', nargs='+', help='space-separated URIs to which Azure AD will redirect in response to an OAuth 2.0 request. The value does not need to be a physical endpoint, but must be a valid URI.')
        c.argument('start_date', help="Date or datetime at which credentials become valid(e.g. '2017-01-01T01:00:00+00:00' or '2017-01-01'). Default value is current time")
        c.argument('end_date', help="Date or datetime after which credentials expire(e.g. '2017-12-31T11:59:59+00:00' or '2017-12-31'). Default value is one year after current time")
        c.argument('available_to_other_tenants', help='the application can be used from any Azure AD tenants', arg_type=get_three_state_flag())
        c.argument('key_value', help='the value for the key credentials associated with the application')
        # TODO: Update these with **enum_choice_list(...) when SDK supports proper enums
        c.argument('key_type', help='the type of the key credentials associated with the application', arg_type=get_enum_type(['AsymmetricX509Cert', 'Password', 'Symmetric'], default='AsymmetricX509Cert'))
        c.argument('key_usage', help='the usage of the key credentials associated with the application.', arg_type=get_enum_type(['Sign', 'Verify'], default='Verify'))
        c.argument('password', help="app password, aka 'client secret'")
        c.argument('oauth2_allow_implicit_flow', arg_type=get_three_state_flag(), help='whether to allow implicit grant flow for OAuth2')
        c.argument('required_resource_accesses', type=validate_file_or_dict,
                   help="resource scopes and roles the application requires access to. Should be in manifest json format. See examples below for details")
        c.argument('native_app', arg_type=get_three_state_flag(), help="an application which can be installed on a user's device or computer")

    with self.argument_context('ad sp') as c:
        c.argument('identifier', options_list=['--id'], help='service principal name, or object id')

    with self.argument_context('ad sp create') as c:
        c.argument('identifier', options_list=['--id'], help='identifier uri, application id, or object id of the associated application')

    with self.argument_context('ad sp create-for-rbac') as c:
        c.argument('scopes', nargs='+')
        c.argument('role', completer=get_role_definition_name_completion_list)
        c.argument('skip_assignment', arg_type=get_three_state_flag(), help='do not create default assignment')
        c.argument('show_auth_for_sdk', options_list='--sdk-auth', help='output result in compatible with Azure SDK auth file', arg_type=get_three_state_flag())

    for item in ['create-for-rbac', 'credential reset']:
        with self.argument_context('ad sp {}'.format(item)) as c:
            c.argument('name', name_arg_type)
            c.argument('cert', arg_group='Credential', validator=validate_cert)
            c.argument('password', options_list=['--password', '-p'], arg_group='Credential')
            c.argument('years', type=int, default=None, arg_group='Credential')
            c.argument('create_cert', action='store_true', arg_group='Credential')
            c.argument('keyvault', arg_group='Credential')
            c.argument('append', action='store_true', help='Append the new credential instead of overwriting.')

    for item in ['delete', 'list']:
        with self.argument_context('ad sp credential {}'.format(item)) as c:
            c.argument('key_id', help='credential key id')
            c.argument('cert', action='store_true', help='a certificate based credential')

    with self.argument_context('ad') as c:
        c.argument('display_name', help='object\'s display name or its prefix')
        c.argument('identifier_uri', help='graph application identifier, must be in uri format')
        c.argument('spn', help='service principal name')
        c.argument('upn', help='user principal name, e.g. john.doe@contoso.com')
        c.argument('query_filter', options_list=['--filter'], help='OData filter')

    with self.argument_context('ad user') as c:
        c.argument('mail_nickname', help='mail alias. Defaults to user principal name')
        c.argument('force_change_password_next_login', arg_type=get_three_state_flag())

    group_help_msg = "group's object id or display name(prefix also works if there is a unique match)"
    with self.argument_context('ad group') as c:
        for arg in VARIANT_GROUP_ID_ARGS:
            c.argument(arg, options_list=['--group', '-g'], validator=validate_group, help=group_help_msg)

    with self.argument_context('ad group show') as c:
        c.extra('cmd')

    member_id_help_msg = 'The object ID of the contact, group, user, or service principal'
    with self.argument_context('ad group get-member-groups') as c:
        c.argument('security_enabled_only', arg_type=get_three_state_flag(), default=False, required=False)
        c.extra('cmd')

    with self.argument_context('ad group member add') as c:
        c.argument('url', options_list='--member-id', validator=validate_member_id, help=member_id_help_msg)

    for item in ['member add', 'member check', 'member list', 'member remove', 'delete']:
        with self.argument_context('ad group {}'.format(item)) as c:
            c.extra('cmd')

    with self.argument_context('ad group member') as c:
        c.argument('member_object_id', options_list='--member-id', help=member_id_help_msg)

    with self.argument_context('role') as c:
        c.argument('scope', help='scope at which the role assignment or definition applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
        c.argument('resource_group_name', options_list=['--resource-group', '-g'], help='use it only if the role or assignment was added at the level of a resource group')

    with self.argument_context('role assignment') as c:
        c.argument('role_assignment_name', options_list=['--name', '-n'])
        c.argument('role', help='role name or id', completer=get_role_definition_name_completion_list)
        c.argument('show_all', options_list=['--all'], action='store_true', help='show all assignments under the current subscription')
        c.argument('include_inherited', action='store_true', help='include assignments applied on parent scopes')
        c.argument('can_delegate', action='store_true', help='when set, the assignee will be able to create further role assignments to the same role')
        c.argument('assignee', help='represent a user, group, or service principal. supported format: object id, user sign-in name, or service principal name')
        c.argument('assignee_object_id', help="assignee's graph object id, such as the 'principal id' from a managed service identity. Use this instead of '--assignee' to bypass graph permission issues")
        c.argument('ids', nargs='+', help='space-separated role assignment ids')
        c.argument('include_classic_administrators', arg_type=get_three_state_flag(), help='list default role assignments for subscription classic administrators, aka co-admins')

    time_help = ('The {} of the query in the format of %Y-%m-%dT%H:%M:%SZ, e.g. 2000-12-31T12:59:59Z. Defaults to {}')
    with self.argument_context('role assignment list-changelogs') as c:
        c.argument('start_time', help=time_help.format('start time', '1 Hour prior to the current time'))
        c.argument('end_time', help=time_help.format('end time', 'the current time'))

    with self.argument_context('role definition') as c:
        c.argument('role_definition_id', options_list=['--name', '-n'], help='the role definition name')
        c.argument('custom_role_only', arg_type=get_three_state_flag(), help='custom roles only(vs. build-in ones)')
        c.argument('role_definition', help="json formatted content which defines the new role.")
        c.argument('name', arg_type=name_arg_type, completer=get_role_definition_name_completion_list, help="the role's name")
