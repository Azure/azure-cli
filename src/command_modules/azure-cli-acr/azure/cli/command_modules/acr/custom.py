# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from subprocess import call, PIPE

from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.containerregistry.v2017_03_01.models import (
    RegistryUpdateParameters as BasicRegistryUpdateParameters,
    StorageAccountParameters
)
from azure.mgmt.containerregistry.v2017_06_01_preview.models import (
    RegistryUpdateParameters as ManagedRegistryUpdateParameters,
    SkuName,
    SkuTier,
    Sku
)

from knack.prompting import prompt, prompt_pass, NoTTYException
from knack.util import CLIError

from ._constants import MANAGED_REGISTRY_API_VERSION
from ._factory import get_acr_service_client
from ._utils import (
    get_resource_group_name_by_registry_name,
    arm_deploy_template_new_storage,
    arm_deploy_template_existing_storage,
    arm_deploy_template_managed_storage,
    random_storage_account_name,
    get_registry_by_name,
    managed_registry_validation,
    validate_sku_update,
    ensure_storage_account_parameter
)
from ._docker_utils import get_login_refresh_token
from .credential import acr_credential_show


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
    client = get_acr_service_client().registries
    admin_user_enabled = admin_enabled == 'true'

    if sku == SkuName.basic.value:
        if storage_account_name is None:
            storage_account_name = random_storage_account_name(registry_name)
            logger.warning(
                "A new storage account '%s' will be created in resource group '%s'.",
                storage_account_name,
                resource_group_name)
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
    else:
        if storage_account_name:
            logger.warning(
                "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
                registry_name, sku)
        LongRunningOperation()(
            arm_deploy_template_managed_storage(
                resource_group_name,
                registry_name,
                location,
                sku,
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
    resource_group_name = get_resource_group_name_by_registry_name(
        registry_name, resource_group_name)
    client = get_acr_service_client().registries

    return client.delete(resource_group_name, registry_name)


def acr_show(registry_name, resource_group_name=None):
    """Gets the properties of the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    resource_group_name = get_resource_group_name_by_registry_name(
        registry_name, resource_group_name)
    client = get_acr_service_client().registries

    return client.get(resource_group_name, registry_name)


def acr_update_get(client,  # pylint: disable=unused-argument
                   registry_name,
                   resource_group_name=None):
    """Returns an empty RegistryUpdateParameters object.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    try:
        managed_registry_validation(registry_name, resource_group_name)
        return ManagedRegistryUpdateParameters()
    except:  # pylint: disable=bare-except
        return BasicRegistryUpdateParameters()


def acr_update_custom(instance,
                      sku=None,
                      storage_account_name=None,
                      admin_enabled=None,
                      tags=None):
    if sku is not None:
        instance.sku = Sku(name=sku)

    if storage_account_name is not None:
        instance.storage_account = StorageAccountParameters(storage_account_name, "")

    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled == 'true'

    if tags is not None:
        instance.tags = tags

    return instance


def acr_update_set(client,
                   registry_name,
                   resource_group_name=None,
                   parameters=None):
    """Sets the properties of the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param RegistryUpdateParameters parameters: The registry update parameters object
    """
    registry, resource_group_name = get_registry_by_name(registry_name, resource_group_name)

    if registry.sku.tier == SkuTier.managed.value:
        if parameters.sku is not None:
            validate_sku_update(parameters.sku)
        if parameters.storage_account is not None:
            parameters.storage_account = None
            logger.warning(
                "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
                registry_name, registry.sku.name)
        client = get_acr_service_client(MANAGED_REGISTRY_API_VERSION).registries
    elif registry.sku.tier == SkuTier.basic.value:
        if hasattr(parameters, 'sku') and parameters.sku is not None:
            parameters.sku = None
            logger.warning(
                "Updating SKU is not supported for registries in Basic SKU. The specified SKU will be ignored.")
        if parameters.storage_account is not None:
            parameters.storage_account = ensure_storage_account_parameter(parameters.storage_account)

    return client.update(resource_group_name, registry_name, parameters)


def acr_login(registry_name, resource_group_name=None, username=None, password=None):
    """Login to a container registry through Docker.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    try:
        call(["docker", "ps"], stdout=PIPE, stderr=PIPE)
    except:
        raise CLIError("Please verify whether docker is installed and running properly")

    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    sku_tier = registry.sku.tier
    login_server = registry.login_server

    # 1. if username was specified, verify that password was also specified
    if username and not password:
        try:
            password = prompt_pass(msg='Password: ')
        except NoTTYException:
            raise CLIError('Please specify both username and password in non-interactive mode.')

    if sku_tier == SkuTier.managed.value:
        # 2. if we don't yet have credentials, attempt to get a refresh token
        if not password:
            try:
                username = "00000000-0000-0000-0000-000000000000"
                password = get_login_refresh_token(login_server)
            except Exception as e:  # pylint: disable=broad-except
                logger.warning("AAD authentication failed with message: %s", str(e))
    else:
        # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
        if not password:
            try:
                cred = acr_credential_show(registry_name)
                username = cred.username
                password = cred.passwords[0].value
            except Exception as e:  # pylint: disable=broad-except
                logger.warning("Admin user authentication failed with message: %s", str(e))

    # 4. if we still don't have credentials, prompt the user
    if not password:
        try:
            username = prompt('Username: ')
            password = prompt_pass(msg='Password: ')
        except NoTTYException:
            raise CLIError(
                'Unable to authenticate using AAD or admin login credentials. ' +
                'Please specify both username and password in non-interactive mode.')

    call(["docker", "login",
          "--username", username,
          "--password", password,
          login_server])


def acr_show_usage(registry_name, resource_group_name=None):
    """Gets the quota usages for the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = managed_registry_validation(
        registry_name, resource_group_name, "Usage is not supported for registries in Basic SKU.")
    client = get_acr_service_client(MANAGED_REGISTRY_API_VERSION).registries

    return client.list_usages(resource_group_name, registry_name)
