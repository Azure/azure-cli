# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import register_cli_argument
from azure.cli.core.commands.parameters import (
    resource_group_name_type,
    location_type,
    tags_type,
    deployment_name_type,
    get_resource_name_completion_list
)

from ._constants import (
    ACR_RESOURCE_TYPE,
    STORAGE_RESOURCE_TYPE
)
from ._validators import validate_registry_name

register_cli_argument('acr', 'registry_name', options_list=('--name', '-n'), help='The name of the container registry', completer=get_resource_name_completion_list(ACR_RESOURCE_TYPE))
register_cli_argument('acr', 'storage_account_name', help='The name of an existing storage account', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
register_cli_argument('acr', 'sku', help='The SKU of the container registry', choices=['Basic'])
register_cli_argument('acr', 'password_name', help='The name of password to regenerate', choices=['password', 'password2'])

register_cli_argument('acr', 'resource_group_name', resource_group_name_type)
register_cli_argument('acr', 'location', location_type)
register_cli_argument('acr', 'tags', tags_type)
register_cli_argument('acr create', 'admin_enabled', nargs='?', required=False, const='true', default=None, help='Indicates whether the admin user is enabled', choices=['true', 'false'])
register_cli_argument('acr update', 'admin_enabled', nargs=1, help='Indicates whether the admin user is enabled', choices=['true', 'false'])

register_cli_argument('acr', 'username', options_list=('--username', '-u'), help='The username used to log into a container registry')
register_cli_argument('acr', 'password', options_list=('--password', '-p'), help='The password used to log into a container registry')

register_cli_argument('acr create', 'registry_name', completer=None, validator=validate_registry_name)
register_cli_argument('acr create', 'deployment_name', deployment_name_type, validator=None)
register_cli_argument('acr check-name', 'registry_name', completer=None)
register_cli_argument('acr create', 'storage_account_name', help='Default: A new storage account will be created. Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
register_cli_argument('acr update', 'storage_account_name', help='Provide the name of an existing storage account if you\'re recreating a container registry over a previous registry created storage account.', completer=get_resource_name_completion_list(STORAGE_RESOURCE_TYPE))
