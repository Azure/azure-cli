#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

import uuid

from azure.cli.core.commands import (
    cli_command,
    LongRunningOperation
)

from azure.cli.command_modules.acr.mgmt_acr.models import (
    Registry,
    RegistryUpdateParameters,
    StorageAccountProperties,
    RegistryNameCheckRequest
)

from ._factory import get_acr_service_client
from ._utils import (
    get_registry_by_name,
    get_access_key_by_storage_account_name,
    get_resource_group_name_by_registry_name,
    arm_deploy_template
)

from ._format import output_format

import azure.cli.core._logging as _logging
logger = _logging.get_az_logger(__name__)

def acr_check_name(registry_name):
    '''Check whether the container registry name is available.
    :param str registry_name: The name of container registry
    '''
    client = get_acr_service_client().registries

    return client.check_name_availability(
        RegistryNameCheckRequest(registry_name))

def acr_list(resource_group_name=None):
    '''List container registries.
    :param str resource_group_name: The name of resource group
    '''
    client = get_acr_service_client().registries

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    else:
        return client.list()

def acr_create(registry_name, #pylint: disable=too-many-arguments
               resource_group_name,
               location,
               storage_account_name=None,
               enable_admin=False):
    '''Create a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str location: The name of location
    :param str storage_account_name: The name of storage account
    :param bool enable_admin: Enable admin user
    '''
    client = get_acr_service_client().registries

    if storage_account_name is None:
        storage_account_name = str(uuid.uuid4()).replace('-', '')[:24]
        LongRunningOperation()(
            arm_deploy_template(resource_group_name,
                                registry_name,
                                location,
                                storage_account_name,
                                enable_admin)
        )
    else:
        storage_account_key = get_access_key_by_storage_account_name(storage_account_name)
        registry = client.create_or_update(
            resource_group_name, registry_name,
            Registry(
                location=location,
                storage_account=StorageAccountProperties(
                    storage_account_name,
                    storage_account_key
                ),
                admin_user_enabled=enable_admin
            )
        )

    registry = client.get_properties(resource_group_name, registry_name)

    logger.warning('\nCreate a new service principal and assign access:')
    logger.warning(
        '  az ad sp create-for-rbac --scopes %s --role Owner --secret <password>',
        registry.id) #pylint: disable=no-member
    logger.warning('\nUse an existing service principal and assign access:')
    logger.warning(
        '  az role assignment create --scope %s --role Owner --assignee <app-id>',
        registry.id) #pylint: disable=no-member

    return registry

def acr_delete(registry_name, resource_group_name=None):
    '''Delete a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    client = get_acr_service_client().registries

    return client.delete(resource_group_name, registry_name)

def acr_show(registry_name, resource_group_name=None):
    '''Get a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    '''
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    client = get_acr_service_client().registries

    return client.get_properties(resource_group_name, registry_name)

def acr_update(registry_name, #pylint: disable=too-many-arguments
               resource_group_name=None,
               storage_account_name=None,
               tags=None,
               enable_admin=False,
               disable_admin=False):
    '''Update a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str storage_account_name: The name of storage account
    :param dict tags: The set of tags
    :param bool enable_admin: Enable admin user
    :param bool disable_admin: Disable admin user
    '''
    registry, resource_group_name = get_registry_by_name(registry_name, resource_group_name)

    # Set admin_user_enabled
    admin_user_enabled = None
    if disable_admin:
        admin_user_enabled = False
    if enable_admin:
        admin_user_enabled = True

    # Set tags
    newTags = registry.tags #pylint: disable=no-member
    if isinstance(tags, dict):
        if tags:
            for key in tags:
                if tags[key]:
                    newTags[key] = tags[key]
                elif key in newTags:
                    del newTags[key]
        else:
            newTags = {}

    # Set storage account
    storage_account = None
    if storage_account_name:
        storage_account_key = get_access_key_by_storage_account_name(storage_account_name)
        storage_account = StorageAccountProperties(
            storage_account_name,
            storage_account_key
        )

    client = get_acr_service_client().registries

    return client.update(
        resource_group_name, registry_name,
        RegistryUpdateParameters(
            tags=newTags,
            admin_user_enabled=admin_user_enabled,
            storage_account=storage_account if storage_account else None
        )
    )

cli_command('acr check-name', acr_check_name)
cli_command('acr list', acr_list, table_transformer=output_format)
cli_command('acr create', acr_create, table_transformer=output_format)
cli_command('acr delete', acr_delete, table_transformer=output_format)
cli_command('acr show', acr_show, table_transformer=output_format)
cli_command('acr update', acr_update, table_transformer=output_format)
