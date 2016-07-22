#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

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
register_cli_argument('role assignment', 'role_assignment_name',
                      options_list=('--role-assignment-name', '-n'))
register_cli_argument('role assignment', 'role', help='role name or id')
register_cli_argument('ad user', 'mail_nickname',
                      help='mail alias. Defaults to user principal name')
register_cli_argument('ad user', 'force_change_password_next_login', action='store_true')
