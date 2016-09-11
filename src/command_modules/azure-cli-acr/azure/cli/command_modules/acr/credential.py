#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core._util import CLIError

from ._factory import get_acr_service_client

from ._utils import (
    get_registry_by_name,
    get_resource_group_name_by_resource_id,
    registry_not_found
)

from ._format import output_format

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

def acr_credential_show(registry_name, resource_group_name=None):
    '''Get admin username and password for a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    registry = get_registry_by_name(registry_name)
    if registry is None:
        registry_not_found(registry_name)

    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_resource_id(registry.id)

    client = get_acr_service_client().registries
    if registry.properties.admin_user_enabled:
        return client.get_credentials(resource_group_name, registry_name)
    else:
        raise CLIError(
            'Admin user is not enabled for the container registry with name: {}'\
            .format(registry_name))

cli_command('acr credential show', acr_credential_show, table_transformer=output_format)
