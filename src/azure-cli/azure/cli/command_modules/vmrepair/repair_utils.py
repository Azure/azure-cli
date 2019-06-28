# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import subprocess
import shlex
import os
from json import loads

from knack.log import get_logger
from knack.prompting import prompt_y_n, NoTTYException

from .exceptions import AzCommandError, WindowsOsNotAvailableError
# pylint: disable=line-too-long

logger = get_logger(__name__)


def _uses_managed_disk(vm):
    if vm.storage_profile.os_disk.managed_disk is None:
        return False
    return True


def _call_az_command(command_string, run_async=False, secure_params=None):
    """
    Uses subprocess to run a command string. To hide sensitive parameters from logs, add the
    parameter in secure_params. If run_async is False then function returns the stdout.
    Raises AzCommandError if command fails.
    """

    tokenized_command = shlex.split(command_string)
    # If command does not start with 'az' then raise exception
    if not tokenized_command or tokenized_command[0] != 'az':
        raise AzCommandError("The command string is not an 'az' command!")

    # If run on windows, add 'cmd /c'
    windows_os_name = 'nt'
    if os.name == windows_os_name:
        tokenized_command = ['cmd', '/c'] + tokenized_command

    # Hide sensitive data such as passwords from logs
    if secure_params:
        for param in secure_params:
            command_string = command_string.replace(param, '********')
    logger.debug('Calling: %s', command_string)
    process = subprocess.Popen(tokenized_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    # Wait for process to terminate and fetch stdout and stderror
    if not run_async:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise AzCommandError(stderr)

        logger.debug('Success.\n')

        return stdout
    return None


def _clean_up_resources(resource_group_name, confirm):

    try:
        if confirm:
            message = 'The clean-up will remove the resource group \'{rg}\' and all repair resources within:\n\n{r}' \
                      .format(rg=resource_group_name, r='\n'.join(_list_resource_ids_in_rg(resource_group_name)))
            logger.warning(message)
            if not prompt_y_n('Continue with clean-up and delete resources?'):
                logger.warning('Skipping clean-up')
                return

        delete_resource_group_command = 'az group delete --name {name} --yes --no-wait'.format(name=resource_group_name)
        logger.info('Cleaning up resources by deleting repair resource group \'%s\'...', resource_group_name)
        _call_az_command(delete_resource_group_command)
    # NoTTYException exception only thrown from confirm block
    except NoTTYException:
        logger.warning('Cannot confirm clean-up resouce in non-interactive mode.')
        logger.warning('Skipping clean-up')
        return
    except AzCommandError as azCommandError:
        # Only way to distinguish errors
        resource_not_found_error_string = 'could not be found'
        if resource_not_found_error_string in str(azCommandError):
            logger.info('Resource group not found. Skipping clean up.')
            return
        logger.error(azCommandError)
        logger.error("Clean up failed.")


def _fetch_compatible_sku(source_vm):

    location = source_vm.location
    source_vm_sku = source_vm.hardware_profile.vm_size

    # First get the source_vm sku, if its available go with it
    check_sku_command = 'az vm list-skus -s {sku} -l {loc} --query [].name -o tsv'.format(sku=source_vm_sku, loc=location)

    logger.info('Checking if source VM size is available...')
    sku_check = _call_az_command(check_sku_command).strip('\n')

    if sku_check:
        logger.info('Source VM size \'%s\' is available. Using it to create repair VM.\n', source_vm_sku)
        return source_vm_sku

    logger.info('Source VM size: \'%s\' is NOT available.\n', source_vm_sku)

    # List available standard SKUs
    # TODO, premium IO only when needed
    list_sku_command = 'az vm list-skus -s standard_d -l {loc} --query ' \
                       '"[?capabilities[?name==\'vCPUs\' && to_number(value)<= to_number(\'4\')] && ' \
                       'capabilities[?name==\'MemoryGB\' && to_number(value)<=to_number(\'16\')] && ' \
                       'capabilities[?name==\'MaxDataDiskCount\' && to_number(value)>to_number(\'0\')] && ' \
                       'capabilities[?name==\'PremiumIO\' && value==\'True\']].name"'\
                       .format(loc=location)

    logger.info('Fetching available VM sizes for repair VM...')
    sku_list = loads(_call_az_command(list_sku_command).strip('\n'))

    if sku_list:
        return sku_list[0]

    return None


def _get_repair_resource_tag(resource_group_name, source_vm_name):
    return 'repair_source={rg}/{vm_name}'.format(rg=resource_group_name, vm_name=source_vm_name)


def _list_resource_ids_in_rg(resource_group_name):
    get_resources_command = 'az resource list --resource-group {rg} --query [].id' \
                            .format(rg=resource_group_name)
    logger.debug('Fetching resources in resource group...')
    ids = loads(_call_az_command(get_resources_command))
    return ids


def _uses_encrypted_disk(vm):
    return vm.storage_profile.os_disk.encryption_settings


def _fetch_compatible_windows_os_urn(source_vm):

    fetch_urn_command = 'az vm image list -s "2016-Datacenter" -f WindowsServer -p MicrosoftWindowsServer -l westus2 --verbose --all --query "[?sku==\'2016-Datacenter\'].urn | reverse(sort(@))"'
    logger.info('Fetching compatible Windows OS images from gallery...')
    urns = loads(_call_az_command(fetch_urn_command))

    # No OS images available for Windows2016
    if not urns:
        raise WindowsOsNotAvailableError()

    # temp fix to mitigate Windows disk signature collision error
    if source_vm.storage_profile.image_reference and source_vm.storage_profile.image_reference.version in urns[0]:
        if len(urns) < 2:
            logger.debug('Avoiding Win2016 latest image due to expected disk collision. But no other image available.')
            raise WindowsOsNotAvailableError()
        return urns[1]
    return urns[0]


def _resolve_api_version(rcf, resource_provider_namespace, parent_resource_path, resource_type):

    provider = rcf.providers.get(resource_provider_namespace)
    # If available, we will use parent resource's api-version

    resource_type_str = (parent_resource_path.split('/')[0] if parent_resource_path else resource_type)
    rt = [t for t in provider.resource_types if t.resource_type.lower() == resource_type_str.lower()]
    if not rt:
        raise Exception('Resource type {} not found.'.format(resource_type_str))
    if len(rt) == 1 and rt[0].api_versions:
        npv = [v for v in rt[0].api_versions if 'preview' not in v.lower()]
        return npv[0] if npv else rt[0].api_versions[0]
    raise Exception(
        'API version is required and could not be resolved for resource {}'
        .format(resource_type))


def _is_linux_os(vm):
    os_type = vm.storage_profile.os_disk.os_type.value if vm.storage_profile.os_disk.os_type else None
    if os_type:
        return os_type.lower() == 'linux'
    # the os_type could be None for VM scaleset, let us check out os configurations
    if vm.os_profile.linux_configuration:
        return bool(vm.os_profile.linux_configuration)
    return False
