#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    location_type,
    tags_type,
    get_resource_name_completion_list
)

from ._constants import (
    ACR_RESOURCE_TYPE,
    STORAGE_RESOURCE_TYPE
)
from ._validators import (
    validate_resource_group_name
)

register_cli_argument('acr', 'registry_name',
                      options_list=('--name', '-n'),
                      help='Name of container registry',
                      completer=get_resource_name_completion_list(ACR_RESOURCE_TYPE))
register_cli_argument('acr', 'storage_account_name',
                      help='Name of an existing storage account',
                      completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))

register_cli_argument('acr', 'resource_group_name', resource_group_name_type)
register_cli_argument('acr', 'location', location_type)
register_cli_argument('acr', 'tags', tags_type)
register_cli_argument('acr', 'admin_user_enabled',
                      help='Whether the admin user account is enabled.',
                      choices=['true', 'false'])

register_cli_argument('acr', 'username',
                      options_list=('--username', '-u'),
                      help='Username used to log into a container registry')
register_cli_argument('acr', 'password',
                      options_list=('--password', '-p'),
                      help='Password used to log into a container registry')

register_cli_argument('acr create', 'registry_name', completer=None)
register_cli_argument('acr create', 'resource_group_name',
                      validator=validate_resource_group_name)
