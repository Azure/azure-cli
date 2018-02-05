# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.commands import LongRunningOperation

from azure.mgmt.containerregistry.v2017_10_01.models import (
    RegistryUpdateParameters,
    StorageAccountProperties,
    SkuName,
    Sku
)

from ._constants import MANAGED_REGISTRY_SKU
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

logger = get_logger(__name__)


def acr_check_name(client, registry_name):
    return client.check_name_availability(registry_name)


def acr_list(client, resource_group_name=None):
    if resource_group_name:
        return client.list_by_resource_group(resource_group_name)
    return client.list()


def acr_create(cmd,
               client,
               registry_name,
               resource_group_name,
               sku,
               location=None,
               storage_account_name=None,
               admin_enabled='false',
               deployment_name=None):
    if sku == SkuName.basic.value and storage_account_name:
        raise CLIError("Please specify '--sku Basic' without providing an existing storage account "
                       "to create a managed registry, or specify '--sku Classic --storage-account-name {}' "
                       "to create a Classic registry using storage account `{}`."
                       .format(storage_account_name, storage_account_name))
    admin_user_enabled = admin_enabled == 'true'

    if sku == SkuName.classic.value:
        if storage_account_name is None:
            storage_account_name = random_storage_account_name(cmd.cli_ctx, registry_name)
            logger.warning(
                "A new storage account '%s' will be created in resource group '%s'.",
                storage_account_name,
                resource_group_name)
            LongRunningOperation(cmd.cli_ctx)(
                arm_deploy_template_new_storage(
                    cmd.cli_ctx,
                    resource_group_name,
                    registry_name,
                    location,
                    sku,
                    storage_account_name,
                    admin_user_enabled,
                    deployment_name)
            )
        else:
            LongRunningOperation(cmd.cli_ctx)(
                arm_deploy_template_existing_storage(
                    cmd.cli_ctx,
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
        LongRunningOperation(cmd.cli_ctx)(
            arm_deploy_template_managed_storage(
                cmd.cli_ctx,
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


def acr_delete(cmd, client, registry_name, resource_group_name=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.delete(resource_group_name, registry_name)


def acr_show(cmd, client, registry_name, resource_group_name=None):
    resource_group_name = get_resource_group_name_by_registry_name(cmd.cli_ctx, registry_name, resource_group_name)
    return client.get(resource_group_name, registry_name)


def acr_update_custom(cmd,
                      instance,
                      sku=None,
                      storage_account_name=None,
                      admin_enabled=None,
                      tags=None):
    if sku is not None:
        instance.sku = Sku(name=sku)

    if storage_account_name is not None:
        instance.storage_account = StorageAccountProperties(
            get_resource_id_by_storage_account_name(cmd.cli_ctx, storage_account_name))

    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled == 'true'

    if tags is not None:
        instance.tags = tags

    return instance


def acr_update_get():
    return RegistryUpdateParameters()


def acr_update_set(cmd,
                   client,
                   registry_name,
                   resource_group_name=None,
                   parameters=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    validate_sku_update(registry.sku.name, parameters.sku)

    if registry.sku.name in MANAGED_REGISTRY_SKU and parameters.storage_account is not None:
        parameters.storage_account = None
        logger.warning(
            "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
            registry_name, registry.sku.name)

    return client.update(resource_group_name, registry_name, parameters)


def acr_login(cmd, registry_name, resource_group_name=None, username=None, password=None):
    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        raise CLIError('This command requires running the docker daemon, which is not supported in Azure Cloud Shell.')

    from subprocess import PIPE, Popen, CalledProcessError
    docker_not_installed = "Please verify if docker is installed."
    docker_not_available = "Please verify if docker daemon is running properly."

    try:
        p = Popen(["docker", "ps"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError:
        raise CLIError(docker_not_installed)
    except CalledProcessError:
        raise CLIError(docker_not_available)

    if stderr:
        raise CLIError(stderr.decode())

    login_server, username, password = get_login_credentials(
        cli_ctx=cmd.cli_ctx,
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
                   login_server], stdin=PIPE, stderr=PIPE)
        _, stderr = p.communicate(input=password.encode())
    else:
        p = Popen(["docker", "login",
                   "--username", username,
                   "--password", password,
                   login_server], stderr=PIPE)
        _, stderr = p.communicate()

    if stderr:
        if b'error storing credentials' in stderr and b'stub received bad data' in stderr \
           and _check_wincred(login_server):
            # Retry once after disabling wincred
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
        else:
            import sys
            output = getattr(sys.stderr, 'buffer', sys.stderr)
            output.write(stderr)


def acr_show_usage(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_managed_registry(cmd.cli_ctx,
                                                       registry_name,
                                                       resource_group_name,
                                                       "Usage is only supported for managed registries.")
    return client.list_usages(resource_group_name, registry_name)


def _check_wincred(login_server):
    import platform
    if platform.system() == 'Windows':
        import json
        from os.path import expanduser, isfile, join
        config_path = join(expanduser('~'), '.docker', 'config.json')
        logger.debug("Docker config file path %s", config_path)
        if isfile(config_path):
            with open(config_path) as input_file:
                content = json.load(input_file)
                input_file.close()
            wincred = content.pop('credsStore', None)
            if wincred and wincred.lower() == 'wincred':
                # Ask for confirmation
                from knack.prompting import prompt_y_n, NoTTYException
                message = "This operation will disable wincred and use file system to store docker credentials." \
                          " All registries that are currently logged in will be logged out." \
                          "\nAre you sure you want to continue?"
                try:
                    if prompt_y_n(message):
                        with open(config_path, 'w') as output_file:
                            json.dump(content, output_file, indent=4)
                            output_file.close()
                            return True
                    return False
                except NoTTYException:
                    return False
            # Don't update config file or retry as this doesn't seem to be a wincred issue
            return False
        else:
            content = {
                "auths": {
                    login_server: {}
                }
            }
            with open(config_path, 'w') as output_file:
                json.dump(content, output_file, indent=4)
                output_file.close()
            return True

    return False
