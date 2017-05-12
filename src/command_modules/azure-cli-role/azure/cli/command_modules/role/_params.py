# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
from azure.cli.core.commands import CliArgumentType
from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import enum_choice_list
from .custom import get_role_definition_name_completion_list
from ._validators import validate_group, validate_member_id, validate_cert, VARIANT_GROUP_ID_ARGS

register_cli_argument('ad app', 'application_object_id', options_list=('--object-id',))
register_cli_argument('ad app', 'display_name', help='the display name of the application')
register_cli_argument('ad app', 'homepage', help='the url where users can sign in and use your app.')
register_cli_argument('ad app', 'identifier', options_list=('--id',), help='identifier uri, application id, or object id')
register_cli_argument('ad app', 'identifier_uris', nargs='+', help='space separated unique URIs that Azure AD can use for this app.')
register_cli_argument('ad app', 'reply_urls', nargs='+', help='space separated URIs to which Azure AD will redirect in response to an OAuth 2.0 request. The value does not need to be a physical endpoint, but must be a valid URI.')
register_cli_argument('ad app', 'start_date', help="Date or datetime at which credentials become valid(e.g. '2017-01-01T01:00:00+00:00' or '2017-01-01'). Default value is current time")
register_cli_argument('ad app', 'end_date', help="Date or datetime after which credentials expire(e.g. '2017-12-31T11:59:59+00:00' or '2017-12-31'). Default value is one year after current time")
register_cli_argument('ad app', 'available_to_other_tenants', action='store_true', help='the application can be used from any Azure AD tenants')
register_cli_argument('ad app', 'key_value', help='the value for the key credentials associated with the application')
# TODO: Update these with **enum_choice_list(...) when SDK supports proper enums
register_cli_argument('ad app', 'key_type', default='AsymmetricX509Cert', help='the type of the key credentials associated with the application', **enum_choice_list(['AsymmetricX509Cert', 'Password', 'Symmetric']))
register_cli_argument('ad app', 'key_usage', default='Verify', help='the usage of the key credentials associated with the application.', **enum_choice_list(['Sign', 'Verify']))

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

register_cli_argument('ad sp', 'identifier', options_list=('--id',), help='service principal name, or object id')
register_cli_argument('ad sp create', 'identifier', options_list=('--id',), help='identifier uri, application id, or object id of the associated application')
register_cli_argument('ad sp create-for-rbac', 'scopes', nargs='+')
register_cli_argument('ad sp create-for-rbac', 'role', completer=get_role_definition_name_completion_list)
register_cli_argument('ad sp create-for-rbac', 'skip_assignment', action='store_true', help='do not create default assignment')
register_cli_argument('ad sp create-for-rbac', 'expanded_view', action='store_true', help=argparse.SUPPRESS)

for item in ['create-for-rbac', 'reset-credentials']:
    register_cli_argument('ad sp {}'.format(item), 'name', name_arg_type)
    register_cli_argument('ad sp {}'.format(item), 'cert', arg_group='Credential', validator=validate_cert)
    register_cli_argument('ad sp {}'.format(item), 'password', options_list=('--password', '-p'), arg_group='Credential')
    register_cli_argument('ad sp {}'.format(item), 'years', type=int, default=None, arg_group='Credential')
    register_cli_argument('ad sp {}'.format(item), 'create_cert', action='store_true', arg_group='Credential')
    register_cli_argument('ad sp {}'.format(item), 'keyvault', arg_group='Credential')

register_cli_argument('ad', 'display_name', help='object\'s display name or its prefix')
register_cli_argument('ad', 'identifier_uri', help='graph application identifier, must be in uri format')
register_cli_argument('ad', 'spn', help='service principal name')
register_cli_argument('ad', 'upn', help='user principal name, e.g. john.doe@contoso.com')
register_cli_argument('ad', 'query_filter', options_list=('--filter',), help='OData filter')
register_cli_argument('ad user', 'mail_nickname', help='mail alias. Defaults to user principal name')
register_cli_argument('ad user', 'force_change_password_next_login', action='store_true')

group_help_msg = "group's object id or display name(prefix also works if there is a unique match)"
for arg in VARIANT_GROUP_ID_ARGS:
    register_cli_argument('ad group', arg, options_list=('--group', '-g'), validator=validate_group, help=group_help_msg)

register_cli_argument('ad group get-member-groups', 'security_enabled_only', action='store_true', default=False, required=False)
member_id_help_msg = 'The object ID of the contact, group, user, or service principal'
register_cli_argument('ad group member add', 'url', options_list='--member-id', validator=validate_member_id, help=member_id_help_msg)
register_cli_argument('ad group member', 'member_object_id', options_list='--member-id', help=member_id_help_msg)

register_cli_argument('role', 'scope', help='scope at which the role assignment or definition applies to, e.g., /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333, /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup, or /subscriptions/0b1f6471-1bf0-4dda-aec3-111122223333/resourceGroups/myGroup/providers/Microsoft.Compute/virtualMachines/myVM')
register_cli_argument('role assignment', 'role_assignment_name', options_list=('--name', '-n'))
register_cli_argument('role assignment', 'role', help='role name or id', completer=get_role_definition_name_completion_list)
register_cli_argument('role assignment', 'show_all', options_list=('--all',), action='store_true', help='show all assignments under the current subscription')
register_cli_argument('role assignment', 'include_inherited', action='store_true', help='include assignments applied on parent scopes')
register_cli_argument('role assignment', 'assignee', help='represent a user, group, or service principal. supported format: object id, user sign-in name, or service principal name')
register_cli_argument('role assignment', 'ids', nargs='+', help='space separated role assignment ids')
register_cli_argument('role definition', 'role_definition_id', options_list=('--name', '-n'), help='the role definition name')
register_cli_argument('role', 'resource_group_name', options_list=('--resource-group', '-g'), help='use it only if the role or assignment was added at the level of a resource group')
register_cli_argument('role definition', 'custom_role_only', action='store_true', help='custom roles only(vs. build-in ones)')
register_cli_argument('role definition', 'role_definition', help="json formatted content which defines the new role.")
register_cli_argument('role definition', 'name', arg_type=name_arg_type, completer=get_role_definition_name_completion_list, help="the role's name")
