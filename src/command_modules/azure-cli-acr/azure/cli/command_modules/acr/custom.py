# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import LongRunningOperation
import azure.cli.core.azlogging as azlogging
from azure.cli.core.util import CLIError
from azure.cli.core.prompting import prompt, prompt_pass, NoTTYException

from azure.mgmt.containerregistry.v2017_10_01.models import (
    RegistryUpdateParameters,
    StorageAccountProperties,
    SkuName,
    SkuTier,
    Sku
)

from ._factory import get_acr_service_client
from ._utils import (
    arm_deploy_template_new_storage,
    arm_deploy_template_existing_storage,
    arm_deploy_template_managed_storage,
    random_storage_account_name,
    get_registry_by_name,
    managed_registry_validation,
    validate_sku_update,
    get_resource_group_name_by_registry_name,
    get_resource_id_by_storage_account_name
)
from ._docker_utils import get_login_refresh_token
from .credential import acr_credential_show


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
    client = get_acr_service_client().registries
    admin_user_enabled = admin_enabled == 'true'

    if sku == 'Basic':
        sku = SkuName.classic.value
        logger.warning("Basic SKU will be deprecated and is converted to Classic SKU.")

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

    if registry.sku.tier == SkuTier.managed.value:
        validate_sku_update(registry.sku.name, parameters.sku)
        if parameters.storage_account is not None:
            parameters.storage_account = None
            logger.warning(
                "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
                registry_name, registry.sku.name)
    elif registry.sku.tier == SkuTier.classic.value:
        validate_sku_update(registry.sku.name, parameters.sku)

    return client.update(resource_group_name, registry_name, parameters)


def _try_aad_token_login(login_server):
    try:
        username = "00000000-0000-0000-0000-000000000000"
        password = get_login_refresh_token(login_server)
        return username, password
    except CLIError as e:
        logger.warning("AAD authentication failed with message: %s", str(e))
        return None, None


def _try_admin_user_login(registry_name):
    try:
        cred = acr_credential_show(registry_name)
        username = cred.username
        password = cred.passwords[0].value
        return username, password
    except CLIError as e:
        logger.warning("Admin user authentication failed with message: %s", str(e))
        return None, None


def acr_login(registry_name, resource_group_name=None, username=None, password=None):
    """Login to a container registry through Docker.
    :param str registry_name: The name of container registry
    :param str resource_group_name: The name of resource group
    :param str username: The username used to log into the container registry
    :param str password: The password used to log into the container registry
    """
    from subprocess import PIPE, Popen, SubprocessError
    docker_not_installed = "Please verify if docker is installed."
    docker_not_available = "Please verify if docker daemon is running properly."

    try:
        p = Popen(["docker", "ps"], stdout=PIPE, stderr=PIPE)
        returncode = p.wait()
    except OSError:
        raise CLIError(docker_not_installed)
    except SubprocessError:
        raise CLIError(docker_not_available)

    if returncode:
        raise CLIError(docker_not_available)

    registry, _ = get_registry_by_name(registry_name, resource_group_name)
    sku_tier = registry.sku.tier
    login_server = registry.login_server

    # 1. if username was specified, verify that password was also specified
    if username and not password:
        try:
            password = prompt_pass(msg='Password: ')
        except NoTTYException:
            raise CLIError('Please specify both username and password in non-interactive mode.')

    # 2. if we don't yet have credentials, attempt to get a refresh token
    if not password and sku_tier == SkuTier.managed.value:
        username, password = _try_aad_token_login(login_server)

    # 3. if we still don't have credentials, attempt to get the admin credentials (if enabled)
    if not password:
        username, password = _try_admin_user_login(registry_name)

    # 4. if we still don't have credentials, prompt the user
    if not password:
        try:
            username = prompt('Username: ')
            password = prompt_pass(msg='Password: ')
        except NoTTYException:
            raise CLIError(
                'Unable to authenticate using AAD or admin login credentials. ' +
                'Please specify both username and password in non-interactive mode.')

    use_password_stdin = False
    try:
        p = Popen(["docker", "login", "--help"], stdout=PIPE, stderr=PIPE)
        stdout, _ = p.communicate()
        if b'--password-stdin' in stdout:
            use_password_stdin = True
    except OSError:
        raise CLIError(docker_not_installed)
    except SubprocessError:
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
    _, resource_group_name = managed_registry_validation(
        registry_name, resource_group_name, "Usage is only supported for managed registries.")
    client = get_acr_service_client().registries

    return client.list_usages(resource_group_name, registry_name)
