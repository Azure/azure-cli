# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger

from azure.cli.command_modules.vm.custom import get_vm
from azure.cli.command_modules.storage.storage_url_helpers import StorageResourceIdentifier
from msrestazure.tools import parse_resource_id

from .repair_utils import (
    _uses_managed_disk,
    _call_az_command,
    _clean_up_resources,
    _fetch_compatible_sku,
    _list_resource_ids_in_rg,
    _get_repair_resource_tag,
    _fetch_compatible_windows_os_urn,
    _is_linux_os
)
from .exceptions import AzCommandError, SkuNotAvailableError, UnmanagedDiskCopyError, WindowsOsNotAvailableError

# pylint: disable=line-too-long, too-many-locals, too-many-statements, broad-except

logger = get_logger(__name__)


def create(cmd, vm_name, resource_group_name, repair_password=None, repair_username=None, repair_vm_name=None, copy_disk_name=None, repair_group_name=None):

    # begin progress reporting for long running operation
    cmd.cli_ctx.get_progress_controller().begin()
    cmd.cli_ctx.get_progress_controller().add(message='Running')

    source_vm = get_vm(cmd, resource_group_name, vm_name)
    is_linux = _is_linux_os(source_vm)
    target_disk_name = source_vm.storage_profile.os_disk.name
    is_managed = _uses_managed_disk(source_vm)

    copy_disk_id = None
    resource_tag = _get_repair_resource_tag(resource_group_name, vm_name)

    # Overall success flag
    command_succeeded = False
    # List of created resouces
    created_resources = []

    # Main command calling block
    try:
        # Fetch OS image urn
        if is_linux:
            os_image_urn = "UbuntuLTS"
        else:
            os_image_urn = _fetch_compatible_windows_os_urn(source_vm)

        # Set up base create vm command
        create_repair_vm_command = 'az vm create -g {g} -n {n} --tag {tag} --image {image} --admin-password {password}' \
                                   .format(g=repair_group_name, n=repair_vm_name, tag=resource_tag, image=os_image_urn, password=repair_password)
        # Add username field only for Windows
        if not is_linux:
            create_repair_vm_command += ' --admin-username {username}'.format(username=repair_username)
        # fetch VM size of repair VM
        sku = _fetch_compatible_sku(source_vm)
        if not sku:
            raise SkuNotAvailableError('Failed to find compatible VM size for source VM\'s OS disk within given region and subscription.')
        create_repair_vm_command += ' --size {sku}'.format(sku=sku)

        # Create new resource group
        create_resource_group_command = 'az group create -l {loc} -n {group_name}' \
                                        .format(loc=source_vm.location, group_name=repair_group_name)
        logger.info('Creating resource group for repair VM and its resources...')
        _call_az_command(create_resource_group_command)

        # MANAGED DISK
        if is_managed:
            logger.info('Source VM uses managed disks. Creating repair VM with managed disks.\n')
            # Copy OS disk command
            copy_disk_command = 'az disk create -g {g} -n {n} --source {s}  --location {loc} --query id -o tsv' \
                                .format(g=resource_group_name, n=copy_disk_name, s=target_disk_name, loc=source_vm.location)
            # Validate create vm create command to validate parameters before runnning copy disk command
            validate_create_vm_command = create_repair_vm_command + ' --validate'

            logger.info('Validating VM template before continuing...')
            _call_az_command(validate_create_vm_command, secure_params=[repair_password])
            logger.info('Copying OS disk of source VM...')
            copy_disk_id = _call_az_command(copy_disk_command).strip('\n')

            attach_disk_command = 'az vm disk attach -g {g} --vm-name {repair} --name {id}' \
                                  .format(g=repair_group_name, repair=repair_vm_name, id=copy_disk_id)

            logger.info('Creating repair VM...')
            _call_az_command(create_repair_vm_command, secure_params=[repair_password])
            logger.info('Attaching copied disk to repair VM...')
            _call_az_command(attach_disk_command)
        # UNMANAGED DISK
        else:
            logger.info('Source VM uses unmanaged disks. Creating repair VM with unmanaged disks.\n')
            os_disk_uri = source_vm.storage_profile.os_disk.vhd.uri
            copy_disk_name = copy_disk_name + '.vhd'
            storage_account = StorageResourceIdentifier(cmd.cli_ctx.cloud, os_disk_uri)
            # Validate create vm create command to validate parameters before runnning copy disk commands
            validate_create_vm_command = create_repair_vm_command + ' --validate'
            logger.info('Validating VM template before continuing...')
            _call_az_command(validate_create_vm_command, secure_params=[repair_password])

            # get storage account connection string
            get_connection_string_command = 'az storage account show-connection-string -g {g} -n {n} --query connectionString -o tsv' \
                                            .format(g=resource_group_name, n=storage_account.account_name)
            logger.debug('Fetching storage account connection string...')
            connection_string = _call_az_command(get_connection_string_command).strip('\n')

            # Create Snapshot of Unmanaged Disk
            make_snapshot_command = 'az storage blob snapshot -c {c} -n {n} --connection-string "{con_string}" --query snapshot -o tsv' \
                                    .format(c=storage_account.container, n=storage_account.blob, con_string=connection_string)
            logger.info('Creating snapshot of OS disk...')
            snapshot_timestamp = _call_az_command(make_snapshot_command, secure_params=[connection_string]).strip('\n')
            snapshot_uri = os_disk_uri + '?snapshot={timestamp}'.format(timestamp=snapshot_timestamp)

            # Copy Snapshot into unmanaged Disk
            copy_snapshot_command = 'az storage blob copy start -c {c} -b {name} --source-uri {source} --connection-string "{con_string}"' \
                                    .format(c=storage_account.container, name=copy_disk_name, source=snapshot_uri, con_string=connection_string)
            logger.info('Creating a copy disk from the snapshot...')
            _call_az_command(copy_snapshot_command, secure_params=[connection_string])
            # Generate the copied disk uri
            copy_disk_id = os_disk_uri.rstrip(storage_account.blob) + copy_disk_name

            # Create new repair VM with copied ummanaged disk command
            create_repair_vm_command = create_repair_vm_command + ' --use-unmanaged-disk'
            logger.info('Creating repair VM while disk copy is in progress...')
            _call_az_command(create_repair_vm_command, secure_params=[repair_password])

            logger.info('Checking if disk copy is done...')
            copy_check_command = 'az storage blob show -c {c} -n {name} --connection-string "{con_string}" --query properties.copy.status -o tsv' \
                                 .format(c=storage_account.container, name=copy_disk_name, con_string=connection_string)
            copy_result = _call_az_command(copy_check_command, secure_params=[connection_string]).strip('\n')
            if copy_result != 'success':
                raise UnmanagedDiskCopyError('Unmanaged disk copy failed.')

            # Attach copied unmanaged disk to new vm
            logger.info('Attaching copied disk to repair VM as data disk...')
            attach_disk_command = "az vm unmanaged-disk attach -g {g} -n {disk_name} --vm-name {vm_name} --vhd-uri {uri}" \
                                  .format(g=repair_group_name, disk_name=copy_disk_name, vm_name=repair_vm_name, uri=copy_disk_id)
            _call_az_command(attach_disk_command)

        command_succeeded = True
        created_resources = _list_resource_ids_in_rg(repair_group_name)

    # Some error happened. Stop command and clean-up resources.
    except KeyboardInterrupt:
        logger.error("Command interrupted by user input. Cleaning up resources.")
    except AzCommandError as azCommandError:
        logger.error(azCommandError)
        logger.error("Repair create failed. Cleaning up created resources.")
    except SkuNotAvailableError as skuNotAvailableError:
        logger.error(skuNotAvailableError)
        logger.error("Please check if the current subscription can create more VM resources. Cleaning up created resources.")
    except UnmanagedDiskCopyError as unmanagedDiskCopyError:
        logger.error(unmanagedDiskCopyError)
        logger.error("Repair create failed. Please try again at another time. Cleaning up created resources.")
    except WindowsOsNotAvailableError:
        logger.error('A compatible Windows OS image is not available at this time, please check subscription.')
    except Exception as exception:
        logger.error('An unexpected error occurred. Try running again with the --debug flag to debug.')
        logger.debug(exception)
    finally:
        # end long running op for process
        cmd.cli_ctx.get_progress_controller().end()

    if not command_succeeded:
        _clean_up_resources(repair_group_name, confirm=False)
        return None

    # Construct return dict
    created_resources.append(copy_disk_id)
    return_dict = {}
    return_dict['message'] = 'Your repair VM \'{n}\' has been created in the resource group \'{repair_rg}\' with disk \'{d}\' attached as data disk. ' \
                             'Please use this VM to troubleshoot and repair. Once the repairs are complete use the command ' \
                             '\'az vm repair restore -n {source_vm} -g {rg} --verbose\' to restore disk to the source VM. ' \
                             'Note that the copied disk is created within the original resource group \'{rg}\'.' \
                             .format(n=repair_vm_name, repair_rg=repair_group_name, d=copy_disk_name, rg=resource_group_name, source_vm=vm_name)
    return_dict['repairVmName'] = repair_vm_name
    return_dict['copiedDiskName'] = copy_disk_name
    return_dict['copiedDiskUri'] = copy_disk_id
    return_dict['repairResouceGroup'] = repair_group_name
    return_dict['resourceTag'] = resource_tag
    return_dict['createdResources'] = created_resources

    logger.info('\n' + return_dict['message'] + '\n')
    return return_dict


def restore(cmd, vm_name, resource_group_name, disk_name=None, repair_vm_id=None, yes=False):

    # begin progress reporting for long running operation
    cmd.cli_ctx.get_progress_controller().begin()
    cmd.cli_ctx.get_progress_controller().add(message='Running')

    source_vm = get_vm(cmd, resource_group_name, vm_name)
    is_managed = _uses_managed_disk(source_vm)

    repair_vm_id = parse_resource_id(repair_vm_id)
    repair_vm_name = repair_vm_id['name']
    repair_resource_group = repair_vm_id['resource_group']

    # Overall success flag
    command_succeeded = False
    source_disk = None
    try:
        if is_managed:
            source_disk = source_vm.storage_profile.os_disk.name
            # Detach repaired data disk command
            detach_disk_command = 'az vm disk detach -g {g} --vm-name {repair} --name {disk}' \
                                  .format(g=repair_resource_group, repair=repair_vm_name, disk=disk_name)
            # Update OS disk with repaired data disk
            attach_fixed_command = 'az vm update -g {g} -n {n} --os-disk {disk}' \
                                   .format(g=resource_group_name, n=vm_name, disk=disk_name)

            # Maybe run attach and delete concurrently
            logger.info('Detaching repaired data disk from repair VM...')
            _call_az_command(detach_disk_command)
            logger.info('Attaching repaired data disk to source VM as an OS disk...')
            _call_az_command(attach_fixed_command)
        else:
            source_disk = source_vm.storage_profile.os_disk.vhd.uri
            # Get disk uri from disk name
            repair_vm = get_vm(cmd, repair_vm_id['resource_group'], repair_vm_id['name'])
            data_disks = repair_vm.storage_profile.data_disks
            # The params went through validator so no need for existence checks
            disk_uri = [disk.vhd.uri for disk in data_disks if disk.name == disk_name][0]

            detach_unamanged_command = 'az vm unmanaged-disk detach -g {g} --vm-name {repair} --name {disk}' \
                                       .format(g=repair_resource_group, repair=repair_vm_name, disk=disk_name)
            # Update OS disk with disk
            # storageProfile.osDisk.name="{disk}"
            attach_unmanaged_command = 'az vm update -g {g} -n {n} --set storageProfile.osDisk.vhd.uri="{uri}"' \
                                       .format(g=resource_group_name, n=vm_name, uri=disk_uri)
            logger.info('Detaching repaired data disk from repair VM...')
            _call_az_command(detach_unamanged_command)
            logger.info('Attaching repaired data disk to source VM as an OS disk...')
            _call_az_command(attach_unmanaged_command)
        # Clean
        _clean_up_resources(repair_resource_group, confirm=not yes)
        command_succeeded = True
    except KeyboardInterrupt:
        logger.error("Command interrupted by user input. If the restore command fails at retry, please rerun the repair process from \'az vm repair create\'.")
    except AzCommandError as azCommandError:
        logger.error(azCommandError)
        logger.error("Repair create failed. If the restore command fails at retry, please rerun the repair process from \'az vm repair create\'.")
    except Exception as exception:
        logger.error('An unexpected error occurred. Try running again with the --debug flag to debug.')
        logger.debug(exception)
    finally:
        # end long running op for process
        cmd.cli_ctx.get_progress_controller().end()

    if not command_succeeded:
        return None

    # Construct return dict
    return_dict = {}
    return_dict['message'] = '\'{disk}\' successfully attached to \'{n}\' as an OS disk. Please test your repairs and once confirmed, ' \
                             'you may choose to delete the source OS disk \'{src_disk}\' within resource group \'{rg}\' manually if you no longer need it, to avoid any undesired costs.' \
                             .format(disk=disk_name, n=vm_name, src_disk=source_disk, rg=resource_group_name)

    logger.info('\n' + return_dict['message'] + '\n')
    return return_dict
