#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------
#pylint: disable=line-too-long
import azure.cli.commands.parameters #pylint: disable=unused-import

from azure.cli.commands import register_cli_argument

register_cli_argument('ad app', 'application_object_id', options_list=('--object-id',))
register_cli_argument('ad app', 'app_id', help='application id')
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

