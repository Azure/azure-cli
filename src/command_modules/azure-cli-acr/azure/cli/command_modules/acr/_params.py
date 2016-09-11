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

from ._constants import RESOURCE_TYPE
from ._validators import (
    validate_registry_name_create,
    validate_registry_name,
    validate_storage_account_name,
    validate_resource_group_name
)

register_cli_argument('acr', 'registry_name',
                      options_list=('--name', '-n'),
                      help='Name of container registry',
                      completer=get_resource_name_completion_list(RESOURCE_TYPE),
                      validator=validate_registry_name)

register_cli_argument('acr', 'resource_group_name', resource_group_name_type)
register_cli_argument('acr', 'location', location_type)
register_cli_argument('acr', 'tags', tags_type)

register_cli_argument('acr', 'storage_account_name',
                      options_list=('--storage-account-name', '-s'),
                      help='Name of an existing storage account',
                      completer=get_resource_name_completion_list(
                          'Microsoft.Storage/storageAccounts'),
                      validator=validate_storage_account_name)

register_cli_argument('acr', 'username',
                      options_list=('--username', '-u'),
                      help='Username used to log into a container registry')

register_cli_argument('acr', 'password',
                      options_list=('--password', '-p'),
                      help='Password used to log into a container registry')

register_cli_argument('acr', 'tenant_id',
                      options_list=('--tenant-id', '-t'),
                      help='Tenant id for service principal login. ' +\
                      'Warning: Changing tenant id will invalidate ' +\
                      'assigned access of existing service principals.')

register_cli_argument('acr create', 'registry_name', completer=None,
                      validator=validate_registry_name_create)
register_cli_argument('acr create', 'resource_group_name',
                      validator=validate_resource_group_name)
