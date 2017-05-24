# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
import azure.cli.core.azlogging as azlogging

from azure.mgmt.containerregistry.models import (
    RegistryUpdateParameters,
    StorageAccountParameters
)

from ._factory import get_acr_service_client
from ._utils import (
    get_resource_group_name_by_registry_name,
    get_access_key_by_storage_account_name,
    arm_deploy_template_new_storage,
    arm_deploy_template_existing_storage,
    random_storage_account_name,
    get_location_from_resource_group
)


logger = azlogging.get_az_logger(__name__)


def acr_check_name(registry_name):
    """Checks whether the container registry name is available for use.
    :param str registry_name: The name of container registry
    """
    client = get_acr_service_client().registries

    return client.check_name_availability(registry_name)


def acr_list(resource_group_name=None):
    """Lists all the container registries under the current subscription.
    :param str resource_group_name: The name of resource group
    """
    client = get_acr_service_client().registries

    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)

    return client.list()


def acr_create(registry_name,
               resource_group_name,
               sku,
               location=None,
               storage_account_name=None,
               admin_enabled='false',
               deployment_name=None):
    """Creates a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str sku: The SKU of the container registry
    :param str location: The name of location
    :param str storage_account_name: The name of storage account
    :param str admin_enabled: Indicates whether the admin user is enabled
    :param str deployment_name: The name of the deployment
    """
    if location is None:
        location = get_location_from_resource_group(resource_group_name)
    client = get_acr_service_client().registries
    admin_user_enabled = admin_enabled == 'true'

    if storage_account_name is None:
        storage_account_name = random_storage_account_name(registry_name)
        LongRunningOperation()(
            arm_deploy_template_new_storage(
                resource_group_name,
                registry_name,
                location,
                sku,
                storage_account_name,
                admin_user_enabled,
                deployment_name)
        )
    else:
        LongRunningOperation()(
            arm_deploy_template_existing_storage(
                resource_group_name,
                registry_name,
                location,
                sku,
                storage_account_name,
                admin_user_enabled,
                deployment_name)
        )

    registry = client.get(resource_group_name, registry_name)
    logger.warning('\nCreate a new service principal and assign access:')
    logger.warning(
        '  az ad sp create-for-rbac --scopes %s --role Owner --password <password>',
        registry.id)  # pylint: disable=no-member
    logger.warning('\nUse an existing service principal and assign access:')
    logger.warning(
        '  az role assignment create --scope %s --role Owner --assignee <app-id>',
        registry.id)  # pylint: disable=no-member

    return registry


def acr_delete(registry_name, resource_group_name=None):
    """Deletes a container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    client = get_acr_service_client().registries

    return client.delete(resource_group_name, registry_name)


def acr_show(registry_name, resource_group_name=None):
    """Gets the properties of the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    client = get_acr_service_client().registries

    return client.get(resource_group_name, registry_name)


def acr_update_get(client,
                   registry_name,
                   resource_group_name=None):
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    props = client.get(resource_group_name, registry_name)

    return RegistryUpdateParameters(
        tags=props.tags,
        admin_user_enabled=props.admin_user_enabled,
        storage_account=props.storage_account
    )


def acr_update_custom(instance,
                      admin_enabled=None,
                      storage_account_name=None,
                      tags=None):
    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled == ['true']

    if tags is not None:
        instance.tags = tags

    if storage_account_name is not None:
        storage_account_key = \
            get_access_key_by_storage_account_name(storage_account_name)
        storage_account = StorageAccountParameters(
            storage_account_name,
            storage_account_key
        )
    instance.storage_account = storage_account if storage_account_name else None

    return instance


def acr_update_set(client,
                   registry_name,
                   resource_group_name=None,
                   parameters=None):
    if resource_group_name is None:
        resource_group_name = get_resource_group_name_by_registry_name(registry_name)

    return client.update(resource_group_name, registry_name, parameters)
