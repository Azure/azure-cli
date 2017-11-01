# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.containerregistry.v2017_10_01.models import (
    RegistryUpdateParameters,
    StorageAccountProperties,
    SkuName,
    Sku
)

from knack.prompting import prompt, prompt_pass, NoTTYException
from knack.util import CLIError

from ._constants import MANAGED_REGISTRY_SKU
from ._factory import get_acr_service_client
from ._utils import (
    arm_deploy_template_new_storage,
    arm_deploy_template_existing_storage,
    arm_deploy_template_managed_storage,
    random_storage_account_name,
    get_registry_by_name,
    validate_managed_registry,
    validate_sku_update,
    get_resource_group_name_by_registry_name,
    get_resource_id_by_storage_account_name
)
from ._docker_utils import get_login_credentials


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
    if sku == SkuName.basic.value and storage_account_name:
        raise CLIError("Please specify '--sku Basic' without providing an existing storage account "
                       "to create a managed registry, or specify '--sku Classic --storage-account-name {}' "
                       "to create a Classic registry using storage account `{}`."
                       .format(storage_account_name, storage_account_name))

    client = get_acr_service_client().registries
    admin_user_enabled = admin_enabled == 'true'

    if sku == SkuName.classic.value:
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


def acr_update_custom(instance,
                      sku=None,
                      storage_account_name=None,
                      admin_enabled=None,
                      tags=None):
    if sku is not None:
        instance.sku = Sku(name=sku)

    if storage_account_name is not None:
        instance.storage_account = StorageAccountProperties(
            get_resource_id_by_storage_account_name(storage_account_name))

    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled == 'true'

    if tags is not None:
        instance.tags = tags

    return instance


def acr_update_get(client):  # pylint: disable=unused-argument
    """Returns an empty RegistryUpdateParameters object.
    """
    return RegistryUpdateParameters()


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

    validate_sku_update(registry.sku.name, parameters.sku)

    if registry.sku.name in MANAGED_REGISTRY_SKU and parameters.storage_account is not None:
        parameters.storage_account = None
        logger.warning(
            "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
            registry_name, registry.sku.name)

    return client.update(resource_group_name, registry_name, parameters)


def acr_login(registry_name, resource_group_name=None, username=None, password=None):
    """Login to a container registry through Docker.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    from subprocess import PIPE, Popen, CalledProcessError
    docker_not_installed = "Please verify if docker is installed."
    docker_not_available = "Please verify if docker daemon is running properly."

    try:
        p = Popen(["docker", "ps"], stdout=PIPE, stderr=PIPE)
        returncode = p.wait()
    except OSError:
        raise CLIError(docker_not_installed)
    except CalledProcessError:
        raise CLIError(docker_not_available)

    if returncode:
        raise CLIError(docker_not_available)

    login_server, username, password = get_login_credentials(
        registry_name=registry_name,
        resource_group_name=resource_group_name,
        username=username,
        password=password)

    use_password_stdin = False
    try:
        p = Popen(["docker", "login", "--help"], stdout=PIPE, stderr=PIPE)
        stdout, _ = p.communicate()
        if b'--password-stdin' in stdout:
            use_password_stdin = True
    except OSError:
        raise CLIError(docker_not_installed)
    except CalledProcessError:
        raise CLIError(docker_not_available)

    if use_password_stdin:
        p = Popen(["docker", "login",
                   "--username", username,
                   "--password-stdin",
                   login_server], stdin=PIPE)
        p.communicate(input=password.encode())
    else:
        p = Popen(["docker", "login",
                   "--username", username,
                   "--password", password,
                   login_server])
        p.wait()


def acr_show_usage(registry_name, resource_group_name=None):
    """Gets the quota usages for the specified container registry.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    """
    _, resource_group_name = validate_managed_registry(
        registry_name, resource_group_name, "Usage is only supported for managed registries.")
    client = get_acr_service_client().registries

    return client.list_usages(resource_group_name, registry_name)
