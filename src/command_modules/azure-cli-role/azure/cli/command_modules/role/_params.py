#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long
import azure.cli.commands.parameters #pylint: disable=unused-import
from azure.cli.commands import CliArgumentType
from azure.cli.commands import register_cli_argument

register_cli_argument('ad app', 'application_object_id', options_list=('--object-id',))
register_cli_argument('ad app', 'display_name', help=' the display name of the application')
register_cli_argument('ad app', 'homepage', help='the url where users can sign in and use your app.')
register_cli_argument('ad app', 'identifier', options_list=('--id',), help='identifier uri, application id, or object id')
register_cli_argument('ad app', 'identifier_uris', nargs='+', help='space separated unique URIs that Azure AD can use for this app.')
register_cli_argument('ad app', 'reply_urls', nargs='+',
                      help='space separated URIs to which Azure AD will redirect in response to an OAuth 2.0 request. The value does not need to be a physical endpoint, but must be a valid URI.')
register_cli_argument('ad app', 'start_date', help='the start date after which password or key would be valid. Default value is current time')
register_cli_argument('ad app', 'end_date', help='the end date till which password or key is valid. Default value is one year after current time')
register_cli_argument('ad app', 'key_value', help='the value for the key credentials associated with the application')
register_cli_argument('ad app', 'key_type', choices=['AsymmetricX509Cert', 'Password', 'Symmetric'], default='AsymmetricX509Cert',
                      help='the type of the key credentials associated with the application')
register_cli_argument('ad app', 'key_usage', choices=['Sign', 'Verify'], default='Verify',
                      help='the usage of the key credentials associated with the application.')

sp_name_type = CliArgumentType(
    options_list=('--name', '-n')
)
register_cli_argument('ad sp', 'identifier', options_list=('--id',), help='service principal name, or object id')
register_cli_argument('ad sp create', 'identifier', options_list=('--id',), help='identifier uri, application id, or object id of the associated application')
register_cli_argument('ad sp create-for-rbac', 'name', sp_name_type)
register_cli_argument('ad sp reset-credentials', 'name', sp_name_type)

register_cli_argument('ad', 'display_name', help='object\'s display name or its prefix')
register_cli_argument('ad', 'identifier_uri',
                      help='graph application identifier, must be in uri format')
register_cli_argument('ad', 'spn', help='service principal name')
register_cli_argument('ad', 'upn', help='user principal name, e.g. john.doe@contoso.com')
register_cli_argument('ad', 'query_filter', options_list=('--filter',), help='OData filter')
register_cli_argument('ad user', 'mail_nickname',
                      help='mail alias. Defaults to user principal name')
register_cli_argument('ad user', 'force_change_password_next_login', action='store_true')

register_cli_argument('role assignment', 'role_assignment_name',
                      options_list=('--role-assignment-name', '-n'))
register_cli_argument('role assignment', 'role', help='role name or id')
register_cli_argument('role assignment', 'show_all', options_list=('--all',), action='store_true',
                      help='show all assignments under the current subscription')
register_cli_argument('role assignment', 'include_inherited', action='store_true',
                      help='include assignments applied on parent scopes')
register_cli_argument('role assignment', 'assignee', help='represent a user, group, or service principal. supported format: object id, user sign-in name, or service principal name')
register_cli_argument('role assignment', 'ids', nargs='+', help='space separated role assignment ids')
register_cli_argument('role', 'role_id', help='the role id')
register_cli_argument('role', 'resource_group_name', options_list=('--resource-group', '-g'),
                      help='use it only if the role or assignment was added at the level of a resource group')
register_cli_argument('role', 'resource_id', help='use it only if the role or assignment was added at the level of a resource')
register_cli_argument('role', 'custom_role_only', action='store_true', help='custom roles only(vs. build-in ones)')
register_cli_argument('role', 'role_definition', help="json formatted content which defines the new role. run 'show-create-template' to get samples")
register_cli_argument('role', 'name', options_list=('--name', '-n'), help="the role's logical name")

