#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from importlib import import_module

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command_with_handler

from azure.cli.core.commands.arm import cli_generic_update_command
from azure.mgmt.compute.operations import (
    VirtualMachinesOperations,
    ContainerServiceOperations)

from azure.cli.command_modules.vm._client_factory import *
from azure.cli.command_modules.vm._operation_factory import *

# VM
cli_command_with_handler(__name__, 'vm create', of_vm_create, cf_vm_create,
                         transform=DeploymentOutputLongRunningOperation('Starting vm create'))

cli_command_with_handler(__name__, 'vm delete', of_vm_delete, cf_vm)
cli_command_with_handler(__name__, 'vm deallocate', of_vm_deallocate, cf_vm)
cli_command_with_handler(__name__, 'vm generalize', of_vm_generalize, cf_vm)
cli_command_with_handler(__name__, 'vm show', of_vm_get, cf_vm)
cli_command_with_handler(__name__, 'vm list-vm-resize-options', of_vm_list_available_sizes, cf_vm)
cli_command_with_handler(__name__, 'vm stop', of_vm_power_off, cf_vm)
cli_command_with_handler(__name__, 'vm restart', of_vm_restart, cf_vm)
cli_command_with_handler(__name__, 'vm start', of_vm_start, cf_vm)
cli_command_with_handler(__name__, 'vm redeploy', of_vm_redeploy, cf_vm)
cli_command_with_handler(__name__, 'vm list-ip-addresses', of_vm_list_ip_addresses)
cli_command_with_handler(__name__, 'vm get-instance-view', of_vm_get_instance_view)
cli_command_with_handler(__name__, 'vm list', of_vm_list)
cli_command_with_handler(__name__, 'vm resize', of_vm_resize_vm)
cli_command_with_handler(__name__, 'vm capture', of_vm_capture_vm)
cli_command_with_handler(__name__, 'vm open-port', of_vm_open_port)
cli_generic_update_command('vm update', VirtualMachinesOperations.get, VirtualMachinesOperations.create_or_update, cf_vm)

# VM NIC
cli_command_with_handler(__name__, 'vm nic add', of_vm_add_nics)
cli_command_with_handler(__name__, 'vm nic delete', of_vm_delete_nics)
cli_command_with_handler(__name__, 'vm nic update', of_vm_update_nics)

# VMSS NIC
cli_command_with_handler(__name__, 'vmss nic list', of_vmss_list_nics, cf_ni)
cli_command_with_handler(__name__, 'vmss nic list-vm-nics', of_vmss_list_vm_nics, cf_ni)
cli_command_with_handler(__name__, 'vmss nic show', of_vmss_nics_show, cf_ni)

# VM Access
cli_command_with_handler(__name__, 'vm access set-linux-user', of_vm_access_set_linux_user)
cli_command_with_handler(__name__, 'vm access delete-linux-user', of_vm_access_delete_linux_user)
cli_command_with_handler(__name__, 'vm access reset-windows-admin', of_vm_access_reset_windows_admin)

# VM Availability Set
cli_command_with_handler(__name__, 'vm availability-set create', of_vm_avail_set_create, cf_avail_set_create)

cli_command_with_handler(__name__, 'vm availability-set delete', of_vm_avail_set_delete, cf_avail_set)
cli_command_with_handler(__name__, 'vm availability-set show', of_vm_avail_set_get, cf_avail_set)
cli_command_with_handler(__name__, 'vm availability-set list', of_vm_avail_set_list, cf_avail_set)
cli_command_with_handler(__name__, 'vm availability-set list-sizes', of_vm_avail_set_list_available_sizes, cf_avail_set)

# VM Boot Diagnostics
cli_command_with_handler(__name__, 'vm boot-diagnostics disable', of_vm_boot_diagnostics_disable)
cli_command_with_handler(__name__, 'vm boot-diagnostics enable', of_vm_boot_diagnostics_enable)
cli_command_with_handler(__name__, 'vm boot-diagnostics get-boot-log', of_vm_get_boot_log)

# VM Container (ACS)
cli_command_with_handler(__name__, 'vm container create', of_vm_acs_create, cf_acs_create,
            transform=DeploymentOutputLongRunningOperation('Starting vm container create'))

#Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
for a in ['id', 'name', 'type', 'location']:
    ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
######
cli_command_with_handler(__name__, 'vm container show', of_vm_acs_get, cf_acs)
cli_command_with_handler(__name__, 'vm container list', of_vm_acs_list, cf_acs)
cli_command_with_handler(__name__, 'vm container delete', of_vm_acs_delete, cf_acs)
cli_generic_update_command('vm container update', ContainerServiceOperations.get, ContainerServiceOperations.create_or_update, cf_acs)

# VM Diagnostics
cli_command_with_handler(__name__, 'vm diagnostics set', of_vm_set_diagnostics_extension)
cli_command_with_handler(__name__, 'vm diagnostics get-default-config', of_vm_show_default_diagnostics_configuration)

# VMSS Diagnostics
cli_command_with_handler(__name__, 'vmss diagnostics set', of_vm_set_vmss_diagnostics_extension)
cli_command_with_handler(__name__, 'vmss diagnostics get-default-config', of_vm_show_default_diagnostics_configuration)

# VM Disk
cli_command_with_handler(__name__, 'vm disk attach-new', of_vm_attach_new_disk)
cli_command_with_handler(__name__, 'vm disk attach-existing', of_vm_attach_existing_disk)
cli_command_with_handler(__name__, 'vm disk detach', of_vm_detach_disk)
cli_command_with_handler(__name__, 'vm disk list', of_vm_list_disks)

# VM Extension
cli_command_with_handler(__name__, 'vm extension delete', of_vm_ext_delete, cf_vm_ext)
cli_command_with_handler(__name__, 'vm extension show', of_vm_ext_get, cf_vm_ext)
cli_command_with_handler(__name__, 'vm extension set', of_vm_set_extension)
cli_command_with_handler(__name__, 'vm extension list', of_vm_list_extensions)

# VMSS Extension
cli_command_with_handler(__name__, 'vmss extension delete', of_vm_delete_vmss_extension)
cli_command_with_handler(__name__, 'vmss extension show', of_vm_get_vmss_extension)
cli_command_with_handler(__name__, 'vmss extension set', of_vm_set_vmss_extension)
cli_command_with_handler(__name__, 'vmss extension list', of_vm_list_vmss_extensions)

# VM Extension Image
cli_command_with_handler(__name__, 'vm extension image show', of_vm_ext_image_get, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vm extension image list-names', of_vm_ext_image_list_types, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vm extension image list-versions', of_vm_ext_image_list_versions, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vm extension image list', of_vm_list_vm_extension_images)

# VMSS Extension Image (convenience copy of VM Extension Image)
cli_command_with_handler(__name__, 'vmss extension image show', of_vm_ext_image_get, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vmss extension image list-names', of_vm_ext_image_list_types, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vmss extension image list-versions', of_vm_ext_image_list_versions, cf_vm_ext_image)
cli_command_with_handler(__name__, 'vmss extension image list', of_vm_list_vm_extension_images)

# VM Image
cli_command_with_handler(__name__, 'vm image show', of_vm_image_get, cf_vm_image)
cli_command_with_handler(__name__, 'vm image list-offers', of_vm_image_list_offers, cf_vm_image)
cli_command_with_handler(__name__, 'vm image list-publishers', of_vm_image_list_publishers, cf_vm_image)
cli_command_with_handler(__name__, 'vm image list-skus', of_vm_image_list_skus, cf_vm_image)
cli_command_with_handler(__name__, 'vm image list', of_vm_list_vm_images)

# VM Usage
cli_command_with_handler(__name__, 'vm list-usage', of_vm_usage_list, cf_usage)

# VMSS
cli_command_with_handler(__name__, 'vmss create', of_vmss_create, cf_vmss_create,
            transform=DeploymentOutputLongRunningOperation('Starting vmss create'))

cli_command_with_handler(__name__, 'vmss delete', of_vmss_delete, cf_vmss)
cli_command_with_handler(__name__, 'vmss list-skus', of_vmss_list_skus, cf_vmss)

cli_command_with_handler(__name__, 'vmss list-instances', of_vmss_list, cf_vmss_vm)

cli_command_with_handler(__name__, 'vmss deallocate', of_vm_vmss_deallocate)
cli_command_with_handler(__name__, 'vmss delete-instances', of_vm_vmss_delete_instances)
cli_command_with_handler(__name__, 'vmss get-instance-view', of_vm_vmss_get_instance_view)
cli_command_with_handler(__name__, 'vmss show', of_vm_vmss_show)
cli_command_with_handler(__name__, 'vmss list ', of_vm_vmss_list)
cli_command_with_handler(__name__, 'vmss stop', of_vm_vmss_stop)
cli_command_with_handler(__name__, 'vmss restart', of_vm_vmss_restart)
cli_command_with_handler(__name__, 'vmss start', of_vm_vmss_start)
cli_command_with_handler(__name__, 'vmss update-instances', of_vm_vmss_update_instances)
cli_command_with_handler(__name__, 'vmss reimage', of_vm_vmss_reimage)
cli_command_with_handler(__name__, 'vmss scale', of_vm_vmss_scale)

# VM Size
cli_command_with_handler(__name__, 'vm list-sizes', of_vm_size_list, cf_vm_sizes)
