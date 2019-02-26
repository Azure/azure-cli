# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
from knack.log import get_logger

from azure.cli.core.commands import LongRunningOperation

from ._constants import get_classic_sku, get_managed_sku, get_premium_sku
from ._utils import (
    arm_deploy_template_new_storage,
    arm_deploy_template_existing_storage,
    random_storage_account_name,
    get_registry_by_name,
    validate_managed_registry,
    validate_sku_update,
    get_resource_group_name_by_registry_name,
    get_resource_id_by_storage_account_name
)
from ._docker_utils import get_login_credentials
from .network_rule import NETWORK_RULE_NOT_SUPPORTED

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
               admin_enabled=False,
               default_action=None,
               deployment_name=None):
    if default_action and sku not in get_premium_sku(cmd):
        raise CLIError(NETWORK_RULE_NOT_SUPPORTED)

    if sku in get_managed_sku(cmd) and storage_account_name:
        raise CLIError("Please specify '--sku {}' without providing an existing storage account "
                       "to create a managed registry, or specify '--sku Classic --storage-account-name {}' "
                       "to create a Classic registry using storage account `{}`."
                       .format(sku, storage_account_name, storage_account_name))

    if sku in get_classic_sku(cmd):
        result = client.check_name_availability(registry_name)
        if not result.name_available:
            raise CLIError(result.message)

        logger.warning(
            "Due to the planned deprecation of the Classic registry SKU, we recommend using "
            "Basic, Standard, or Premium for all new registries. See https://aka.ms/acr/skus for details.")
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
                    admin_enabled,
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
                    admin_enabled,
                    deployment_name)
            )
        return client.get(resource_group_name, registry_name)
    else:
        if storage_account_name:
            logger.warning(
                "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
                registry_name, sku)
        Registry, Sku, NetworkRuleSet = cmd.get_models('Registry', 'Sku', 'NetworkRuleSet')
        registry = Registry(location=location, sku=Sku(name=sku), admin_user_enabled=admin_enabled)
        if default_action:
            registry.network_rule_set = NetworkRuleSet(default_action=default_action)
        return client.create(resource_group_name, registry_name, registry)


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
                      default_action=None,
                      tags=None):
    if sku is not None:
        Sku = cmd.get_models('Sku')
        instance.sku = Sku(name=sku)

    if storage_account_name is not None:
        StorageAccountProperties = cmd.get_models('StorageAccountProperties')
        instance.storage_account = StorageAccountProperties(
            id=get_resource_id_by_storage_account_name(cmd.cli_ctx, storage_account_name))

    if admin_enabled is not None:
        instance.admin_user_enabled = admin_enabled

    if tags is not None:
        instance.tags = tags

    if default_action is not None:
        NetworkRuleSet = cmd.get_models('NetworkRuleSet')
        instance.network_rule_set = NetworkRuleSet(default_action=default_action)

    return instance


def acr_update_get(cmd):
    """Returns an empty RegistryUpdateParameters object.
    """
    RegistryUpdateParameters = cmd.get_models('RegistryUpdateParameters')
    return RegistryUpdateParameters()


def acr_update_set(cmd,
                   client,
                   registry_name,
                   resource_group_name=None,
                   parameters=None):
    registry, resource_group_name = get_registry_by_name(cmd.cli_ctx, registry_name, resource_group_name)

    if parameters.network_rule_set and registry.sku.name not in get_premium_sku(cmd):
        raise CLIError(NETWORK_RULE_NOT_SUPPORTED)

    validate_sku_update(cmd, registry.sku.name, parameters.sku)

    if registry.sku.name in get_managed_sku(cmd) and parameters.storage_account is not None:
        parameters.storage_account = None
        logger.warning(
            "The registry '%s' in '%s' SKU is a managed registry. The specified storage account will be ignored.",
            registry_name, registry.sku.name)

    return client.update(resource_group_name, registry_name, parameters)


def acr_login(cmd,
              registry_name,
              resource_group_name=None,  # pylint: disable=unused-argument
              tenant_suffix=None,
              username=None,
              password=None):
    from azure.cli.core.util import in_cloud_console
    if in_cloud_console():
        raise CLIError('This command requires running the docker daemon, which is not supported in Azure Cloud Shell.')

    docker_command = _get_docker_command()

    login_server, username, password = get_login_credentials(
        cmd=cmd,
        registry_name=registry_name,
        tenant_suffix=tenant_suffix,
        username=username,
        password=password)

    from subprocess import PIPE, Popen
    p = Popen([docker_command, "login",
               "--username", username,
               "--password", password,
               login_server], stderr=PIPE)
    _, stderr = p.communicate()

    if stderr:
        if b'error storing credentials' in stderr and b'stub received bad data' in stderr \
           and _check_wincred(login_server):
            # Retry once after disabling wincred
            p = Popen([docker_command, "login",
                       "--username", username,
                       "--password", password,
                       login_server])
            p.wait()
        else:
            if b'--password-stdin' in stderr:
                errors = [err for err in stderr.decode().split('\n') if '--password-stdin' not in err]
                stderr = '\n'.join(errors).encode()

            import sys
            output = getattr(sys.stderr, 'buffer', sys.stderr)
            output.write(stderr)


def acr_show_usage(cmd, client, registry_name, resource_group_name=None):
    _, resource_group_name = validate_managed_registry(cmd,
                                                       registry_name,
                                                       resource_group_name,
                                                       "Usage is only supported for managed registries.")
    return client.list_usages(resource_group_name, registry_name)


def _get_docker_command():
    docker_not_installed = "Please verify if docker is installed."
    docker_not_available = "Please verify if docker daemon is running properly."
    docker_command = 'docker'

    from subprocess import PIPE, Popen, CalledProcessError
    try:
        p = Popen([docker_command, "ps"], stdout=PIPE, stderr=PIPE)
        _, stderr = p.communicate()
    except OSError as e:
        logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(e))
        # The executable may not be discoverable in WSL so retry *.exe once
        try:
            docker_command = 'docker.exe'
            p = Popen([docker_command, "ps"], stdout=PIPE, stderr=PIPE)
            _, stderr = p.communicate()
        except OSError as inner:
            logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(inner))
            raise CLIError(docker_not_installed)
        except CalledProcessError as inner:
            logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(inner))
            raise CLIError(docker_not_available)
    except CalledProcessError as e:
        logger.debug("Could not run '%s' command. Exception: %s", docker_command, str(e))
        raise CLIError(docker_not_available)

    if stderr:
        raise CLIError(stderr.decode())

    return docker_command


def _check_wincred(login_server):
    import platform
    if platform.system() == 'Windows':
        import json
        from os.path import expanduser, isfile, join
        docker_directory = join(expanduser('~'), '.docker')
        config_path = join(docker_directory, 'config.json')
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
            import os
            content = {
                "auths": {
                    login_server: {}
                }
            }
            try:
                os.makedirs(docker_directory)
            except OSError as e:
                logger.debug("Could not create docker directory '%s'. Exception: %s", docker_directory, str(e))
            with open(config_path, 'w') as output_file:
                json.dump(content, output_file, indent=4)
                output_file.close()
            return True

    return False
