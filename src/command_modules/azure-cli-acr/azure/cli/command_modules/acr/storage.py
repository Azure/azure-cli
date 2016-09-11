#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import (
    cli_command,
    LongRunningOperation
)

from ._factory import get_acr_service_client
from ._arm_utils import (
    arm_deploy_template,
    add_tag_storage_account,
    delete_tag_storage_account
)
from ._utils import (
    get_registry_by_name,
    get_resource_group_name_by_resource_id,
    registry_not_found
)
from ._format import output_format

def acr_storage_update(registry_name,
                       storage_account_name,
                       resource_group_name=None):
    '''Update storage account for a container registry.
    :param str registry_name: The name of container registry
    :param str storage_account_name: The name of storage account
    :param str resource_group_name: The name of resource group
    '''
    registry = get_registry_by_name(registry_name)
    if registry is None:
        registry_not_found(registry_name)

    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_resource_id(registry.id)

    old_storage_account_name = registry.properties.storage_account.name

    # Update a container registry
    LongRunningOperation()(
        arm_deploy_template(resource_group_name,
                            registry_name,
                            registry.location,
                            storage_account_name,
                            registry.properties.admin_user_enabled)
    )

    client = get_acr_service_client().registries
    registry = client.get_properties(resource_group_name, registry_name)

    delete_tag_storage_account(old_storage_account_name, registry_name)
    add_tag_storage_account(storage_account_name, registry_name)

    return registry

cli_command('acr storage update', acr_storage_update, table_transformer=output_format)
