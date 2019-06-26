# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from datetime import datetime
from json import loads
from re import match, search
from knack.log import get_logger
from knack.util import CLIError

from azure.cli.command_modules.vm.custom import get_vm
from azure.cli.command_modules.resource._client_factory import _resource_client_factory
from msrestazure.azure_exceptions import CloudError
from msrestazure.tools import parse_resource_id, is_valid_resource_id

from .exceptions import AzCommandError
from .repair_utils import _call_az_command, _get_repair_resource_tag, _uses_encrypted_disk, _resolve_api_version, _is_linux_os

# pylint: disable=line-too-long, broad-except

logger = get_logger(__name__)


def validate_create(cmd, namespace):
    # Check if VM exists and is not classic VM
    source_vm = _validate_and_get_vm(cmd, namespace.resource_group_name, namespace.vm_name)
    is_linux = _is_linux_os(source_vm)

    # Check repair vm name
    if namespace.repair_vm_name:
        _validate_vm_name(namespace.repair_vm_name, is_linux)
    else:
        namespace.repair_vm_name = ('repair-' + namespace.vm_name)[:15]

    # Check copy disk name
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    if namespace.copy_disk_name:
        _validate_disk_name(namespace.copy_disk_name)
    else:
        namespace.copy_disk_name = namespace.vm_name + '-DiskCopy-' + timestamp

    # Check copy resouce group name
    if namespace.repair_group_name:
        if namespace.repair_group_name == namespace.resource_group_name:
            raise CLIError('The repair resource group name cannot be the same as the source VM resource group.')
        _validate_resource_group_name(namespace.repair_group_name)
    else:
        namespace.repair_group_name = 'repair-' + namespace.vm_name + '-' + timestamp

    # Check encrypted disk
    if _uses_encrypted_disk(source_vm):
        # TODO, validate this with encrypted VMs
        logger.warning('The source VM\'s OS disk is encrypted.')

    # Validate Auth Params
    if is_linux and namespace.repair_username:
        logger.warning("Setting admin username property is not allowed for Linux VMs. Ignoring the given repair-username parameter.")
    if not is_linux and not namespace.repair_username:
        _prompt_repair_username(namespace)
    if not namespace.repair_password:
        _prompt_repair_password(namespace)


def validate_restore(cmd, namespace):

    # Check if VM exists and is not classic VM
    _validate_and_get_vm(cmd, namespace.resource_group_name, namespace.vm_name)

    # No repair param given, find repair vm using tags
    if not namespace.repair_vm_id:
        # Find repair VM
        tag = _get_repair_resource_tag(namespace.resource_group_name, namespace.vm_name)
        try:
            find_repair_command = 'az resource list --tag {tag} --query "[?type==\'Microsoft.Compute/virtualMachines\']"' \
                                  .format(tag=tag)
            logger.info('Searching for the repair VM within subscription...')
            output = _call_az_command(find_repair_command)
        except AzCommandError as azCommandError:
            logger.error(azCommandError)
            raise CLIError('Unexpected error occured while locating the repair VM.')
        repair_list = loads(output)

        # No repair VM found
        if not repair_list:
            raise CLIError('Repair VM not found for {vm_name}. Please check if the repair resources were removed.'.format(vm_name=namespace.vm_name))

        # More than one repair VM found
        if len(repair_list) > 1:
            message = 'More than one repair VM found:\n'
            for vm in repair_list:
                message += vm['id'] + '\n'
            message += '\nPlease specify the --repair-vm-id to restore with.'
            raise CLIError(message)

        # One repair VM found
        namespace.repair_vm_id = repair_list[0]['id']
        logger.info('Restoring from repair VM: %s', namespace.repair_vm_id)

    if not is_valid_resource_id(namespace.repair_vm_id):
        raise CLIError('Repair resource id is not valid.')

    repair_vm_id = parse_resource_id(namespace.repair_vm_id)
    # Check if data disk exists on repair VM
    repair_vm = get_vm(cmd, repair_vm_id['resource_group'], repair_vm_id['name'])
    data_disks = repair_vm.storage_profile.data_disks
    if not data_disks:
        raise CLIError('No data disks found on repair VM: {}'.format(repair_vm_id['name']))

    # Populate disk name
    if not namespace.disk_name:
        namespace.disk_name = data_disks[0].name
        logger.info('Disk-name not given. Defaulting to the first data disk attached to the repair VM: %s', data_disks[0].name)
    else:  # check disk name
        if not [disk for disk in data_disks if disk.name == namespace.disk_name]:
            raise CLIError('No data disks found on the repair VM: \'{vm}\' with the disk name: \'{disk}\''.format(vm=repair_vm_id['name'], disk=namespace.disk_name))


def _prompt_repair_username(namespace):

    from knack.prompting import prompt, NoTTYException
    try:
        namespace.repair_username = prompt('Repair VM admin username: ')
    except NoTTYException:
        raise CLIError('Please specify the username parameter in non-interactive mode.')


def _prompt_repair_password(namespace):
    from knack.prompting import prompt_pass, NoTTYException
    try:
        namespace.repair_password = prompt_pass('Repair VM admin password: ', confirm=True)
    except NoTTYException:
        raise CLIError('Please specify the password parameter in non-interactive mode.')


def _classic_vm_exists(cmd, resource_group_name, vm_name):
    classic_vm_provider = 'Microsoft.ClassicCompute'
    vm_resource_type = 'virtualMachines'

    try:
        rcf = _resource_client_factory(cmd.cli_ctx)
        api_version = _resolve_api_version(rcf, classic_vm_provider, None, vm_resource_type)
        resource_client = rcf.resources
        resource_client.get(resource_group_name, classic_vm_provider, '', vm_resource_type, vm_name, api_version)
    except CloudError as cloudError:
        # Resource does not exist or the API failed
        logger.debug(cloudError)
        return False
    except Exception as exception:
        # Unknown error, so return false for default resource not found error message
        logger.debug(exception)
        return False
    return True


def _validate_and_get_vm(cmd, resource_group_name, vm_name):
    # Check if target VM exists
    resource_not_found_error = 'ResourceNotFound'
    source_vm = None
    try:
        source_vm = get_vm(cmd, resource_group_name, vm_name)
    except CloudError as cloudError:
        logger.debug(cloudError)
        if cloudError.error.error == resource_not_found_error and _classic_vm_exists(cmd, resource_group_name, vm_name):
            # Given VM is classic VM (RDFE)
            raise CLIError('The given VM \'{}\' is a classic VM. VM repair commands do not support classic VMs.'.format(vm_name))
        # Unknown Error
        raise CLIError(cloudError.message)

    return source_vm


def _validate_vm_name(vm_name, is_linux):
    if not is_linux:
        win_pattern = r'[\'~!@#$%^&*()=+_[\]{}\\|;:.",<>?]'
        num_pattern = r'[0-9]+$'

        if len(vm_name) > 15 or search(win_pattern, vm_name) or match(num_pattern, vm_name):
            raise CLIError('Windows computer name cannot be more than 15 characters long, be entirely numeric, or contain the following characters: '
                           r'`~!@#$%^&*()=+_[]{}\|; :.\'",<>/?')


def _validate_disk_name(disk_name):
    disk_pattern = r'([a-zA-Z0-9][a-zA-Z0-9_.\-]+[a-zA-Z0-9_])$'
    if not match(disk_pattern, disk_name):
        raise CLIError('Disk name must begin with a letter or number, end with a letter, number or underscore, and may contain only letters, numbers, underscores, periods, or hyphens.')
    if len(disk_name) > 80:
        raise CLIError('Disk name only allow up to 80 characters.')


def _validate_resource_group_name(rg_name):
    rg_pattern = r'[0-9a-zA-Z._\-()]+$'
    # if match is null or ends in period, then raise error
    if not match(rg_pattern, rg_name) or rg_name[-1] == '.':
        raise CLIError('Resource group name only allow alphanumeric characters, periods, underscores, hyphens and parenthesis and cannot end in a period.')

    if len(rg_name) > 90:
        raise CLIError('Resource group name only allow up to 90 characters.')

    # Check for existing dup name
    try:
        list_rg_command = 'az group list --query "[].name"'
        logger.info('Checking for existing resource groups with identical name within subscription...')
        output = _call_az_command(list_rg_command)
    except AzCommandError as azCommandError:
        logger.error(azCommandError)
        raise CLIError('Unexpected error occured while fetching existing resource groups.')
    rg_list = loads(output)

    if rg_name in [rg.lower() for rg in rg_list]:
        raise CLIError('Resource group with name \'{}\' already exists within subscription.'.format(rg_name))
