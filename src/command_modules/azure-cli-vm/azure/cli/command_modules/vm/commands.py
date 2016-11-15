#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command

from azure.cli.core.commands.arm import cli_generic_update_command

from azure.cli.command_modules.vm._client_factory import * #pylint: disable=wildcard-import,unused-wildcard-import

#pylint: disable=line-too-long

# VM

cli_command(__name__, 'vm create', 'azure.cli.command_modules.vm.mgmt_vm.lib.operations.vm_operations#VmOperations.create_or_update', cf_vm_create,
            transform=DeploymentOutputLongRunningOperation('Starting vm create'))

cli_command(__name__, 'vm delete', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.delete', cf_vm)
cli_command(__name__, 'vm deallocate', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.deallocate', cf_vm)
cli_command(__name__, 'vm generalize', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.generalize', cf_vm)
cli_command(__name__, 'vm show', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.get', cf_vm)
cli_command(__name__, 'vm list-vm-resize-options', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.list_available_sizes', cf_vm)
cli_command(__name__, 'vm stop', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.power_off', cf_vm)
cli_command(__name__, 'vm restart', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.restart', cf_vm)
cli_command(__name__, 'vm start', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.start', cf_vm)
cli_command(__name__, 'vm redeploy', 'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.redeploy', cf_vm)
cli_command(__name__, 'vm list-ip-addresses', 'azure.cli.command_modules.vm.custom#list_ip_addresses')
cli_command(__name__, 'vm get-instance-view', 'azure.cli.command_modules.vm.custom#get_instance_view')
cli_command(__name__, 'vm list', 'azure.cli.command_modules.vm.custom#list_vm')
cli_command(__name__, 'vm resize', 'azure.cli.command_modules.vm.custom#resize_vm')
cli_command(__name__, 'vm capture', 'azure.cli.command_modules.vm.custom#capture_vm')
cli_command(__name__, 'vm open-port', 'azure.cli.command_modules.vm.custom#vm_open_port')
cli_generic_update_command(__name__, 'vm update',
                           'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.get',
                           'azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.create_or_update',
                           cf_vm)

# VM NIC
cli_command(__name__, 'vm nic add', 'azure.cli.command_modules.vm.custom#vm_add_nics')
cli_command(__name__, 'vm nic delete', 'azure.cli.command_modules.vm.custom#vm_delete_nics')
cli_command(__name__, 'vm nic update', 'azure.cli.command_modules.vm.custom#vm_update_nics')

# VMSS NIC
cli_command(__name__, 'vmss nic list', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces', cf_ni)
cli_command(__name__, 'vmss nic list-vm-nics', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces', cf_ni)
cli_command(__name__, 'vmss nic show', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface', cf_ni)

# VM Access
cli_command(__name__, 'vm access set-linux-user', 'azure.cli.command_modules.vm.custom#set_linux_user')
cli_command(__name__, 'vm access delete-linux-user', 'azure.cli.command_modules.vm.custom#delete_linux_user')
cli_command(__name__, 'vm access reset-windows-admin', 'azure.cli.command_modules.vm.custom#reset_windows_admin')

# # VM Availability Set
cli_command(__name__, 'vm availability-set create', 'azure.cli.command_modules.vm.mgmt_avail_set.lib.operations.avail_set_operations#AvailSetOperations.create_or_update', cf_avail_set_create)

cli_command(__name__, 'vm availability-set delete', 'azure.mgmt.compute.operations.availability_sets_operations#AvailabilitySetsOperations.delete', cf_avail_set)
cli_command(__name__, 'vm availability-set show', 'azure.mgmt.compute.operations.availability_sets_operations#AvailabilitySetsOperations.get', cf_avail_set)
cli_command(__name__, 'vm availability-set list', 'azure.mgmt.compute.operations.availability_sets_operations#AvailabilitySetsOperations.list', cf_avail_set)
cli_command(__name__, 'vm availability-set list-sizes', 'azure.mgmt.compute.operations.availability_sets_operations#AvailabilitySetsOperations.list_available_sizes', cf_avail_set)

cli_generic_update_command(__name__, 'vm availability-set update',
                           'azure.cli.command_modules.vm.custom#availset_get',
                           'azure.cli.command_modules.vm.custom#availset_set')
cli_generic_update_command(__name__, 'vmss update',
                           'azure.cli.command_modules.vm.custom#vmss_get',
                           'azure.cli.command_modules.vm.custom#vmss_set')

# VM Boot Diagnostics
cli_command(__name__, 'vm boot-diagnostics disable', 'azure.cli.command_modules.vm.custom#disable_boot_diagnostics')
cli_command(__name__, 'vm boot-diagnostics enable', 'azure.cli.command_modules.vm.custom#enable_boot_diagnostics')
cli_command(__name__, 'vm boot-diagnostics get-boot-log', 'azure.cli.command_modules.vm.custom#get_boot_log')

# ACS

#Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
for a in ['id', 'name', 'type', 'location']:
    ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
######
cli_command(__name__, 'acs show', 'azure.mgmt.compute.operations.container_services_operations#ContainerServicesOperations.get', cf_acs)
cli_command(__name__, 'acs list', 'azure.cli.command_modules.vm.custom#list_container_services', cf_acs)
cli_command(__name__, 'acs delete', 'azure.mgmt.compute.operations.container_services_operations#ContainerServicesOperations.delete', cf_acs)
cli_command(__name__, 'acs scale', 'azure.cli.command_modules.vm.custom#update_acs')
#Per conversation with ACS team, hide the update till we have something meaningful to tweak
# from azure.cli.command_modules.vm.custom import update_acs
# cli_generic_update_command(__name__, 'acs update', ContainerServicesOperations.get, ContainerServicesOperations.create_or_update, cf_acs)

# VM Diagnostics
cli_command(__name__, 'vm diagnostics set', 'azure.cli.command_modules.vm.custom#set_diagnostics_extension')
cli_command(__name__, 'vm diagnostics get-default-config', 'azure.cli.command_modules.vm.custom#show_default_diagnostics_configuration')

# VMSS Diagnostics
cli_command(__name__, 'vmss diagnostics set', 'azure.cli.command_modules.vm.custom#set_vmss_diagnostics_extension')
cli_command(__name__, 'vmss diagnostics get-default-config', 'azure.cli.command_modules.vm.custom#show_default_diagnostics_configuration')

# VM Disk
cli_command(__name__, 'vm disk attach-new', 'azure.cli.command_modules.vm.custom#attach_new_disk')
cli_command(__name__, 'vm disk attach-existing', 'azure.cli.command_modules.vm.custom#attach_existing_disk')
cli_command(__name__, 'vm disk detach', 'azure.cli.command_modules.vm.custom#detach_disk')
cli_command(__name__, 'vm disk list', 'azure.cli.command_modules.vm.custom#list_disks')

# VM Extension
cli_command(__name__, 'vm extension delete', 'azure.mgmt.compute.operations.virtual_machine_extensions_operations#VirtualMachineExtensionsOperations.delete', cf_vm_ext)
cli_command(__name__, 'vm extension show', 'azure.mgmt.compute.operations.virtual_machine_extensions_operations#VirtualMachineExtensionsOperations.get', cf_vm_ext)
cli_command(__name__, 'vm extension set', 'azure.cli.command_modules.vm.custom#set_extension')
cli_command(__name__, 'vm extension list', 'azure.cli.command_modules.vm.custom#list_extensions')

# VMSS Extension
cli_command(__name__, 'vmss extension delete', 'azure.cli.command_modules.vm.custom#delete_vmss_extension')
cli_command(__name__, 'vmss extension show', 'azure.cli.command_modules.vm.custom#get_vmss_extension')
cli_command(__name__, 'vmss extension set', 'azure.cli.command_modules.vm.custom#set_vmss_extension')
cli_command(__name__, 'vmss extension list', 'azure.cli.command_modules.vm.custom#list_vmss_extensions')

# VM Extension Image
cli_command(__name__, 'vm extension image show', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.get', cf_vm_ext_image)
cli_command(__name__, 'vm extension image list-names', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.list_types', cf_vm_ext_image)
cli_command(__name__, 'vm extension image list-versions', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.list_versions', cf_vm_ext_image)
cli_command(__name__, 'vm extension image list', 'azure.cli.command_modules.vm.custom#list_vm_extension_images')

# VMSS Extension Image (convenience copy of VM Extension Image)
cli_command(__name__, 'vmss extension image show', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.get', cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list-names', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.list_types', cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list-versions', 'azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.list_versions', cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list', 'azure.cli.command_modules.vm.custom#list_vm_extension_images')

# VM Image
cli_command(__name__, 'vm image show', 'azure.mgmt.compute.operations.virtual_machine_images_operations#VirtualMachineImagesOperations.get', cf_vm_image)
cli_command(__name__, 'vm image list-offers', 'azure.mgmt.compute.operations.virtual_machine_images_operations#VirtualMachineImagesOperations.list_offers', cf_vm_image)
cli_command(__name__, 'vm image list-publishers', 'azure.mgmt.compute.operations.virtual_machine_images_operations#VirtualMachineImagesOperations.list_publishers', cf_vm_image)
cli_command(__name__, 'vm image list-skus', 'azure.mgmt.compute.operations.virtual_machine_images_operations#VirtualMachineImagesOperations.list_skus', cf_vm_image)
cli_command(__name__, 'vm image list', 'azure.cli.command_modules.vm.custom#list_vm_images')

# VM Usage
cli_command(__name__, 'vm list-usage', 'azure.mgmt.compute.operations.usage_operations#UsageOperations.list', cf_usage)

# VMSS
cli_command(__name__, 'vmss create', 'azure.cli.command_modules.vm.mgmt_vmss.lib.operations.vmss_operations#VmssOperations.create_or_update', cf_vmss_create,
            transform=DeploymentOutputLongRunningOperation('Starting vmss create'))

cli_command(__name__, 'vmss delete', 'azure.mgmt.compute.operations.virtual_machine_scale_sets_operations#VirtualMachineScaleSetsOperations.delete', cf_vmss)
cli_command(__name__, 'vmss list-skus', 'azure.mgmt.compute.operations.virtual_machine_scale_sets_operations#VirtualMachineScaleSetsOperations.list_skus', cf_vmss)

cli_command(__name__, 'vmss list-instances', 'azure.mgmt.compute.operations.virtual_machine_scale_set_vms_operations#VirtualMachineScaleSetVMsOperations.list', cf_vmss_vm)

cli_command(__name__, 'vmss deallocate', 'azure.cli.command_modules.vm.custom#vmss_deallocate')
cli_command(__name__, 'vmss delete-instances', 'azure.cli.command_modules.vm.custom#vmss_delete_instances')
cli_command(__name__, 'vmss get-instance-view', 'azure.cli.command_modules.vm.custom#vmss_get_instance_view')
cli_command(__name__, 'vmss show', 'azure.cli.command_modules.vm.custom#vmss_show')
cli_command(__name__, 'vmss list', 'azure.cli.command_modules.vm.custom#vmss_list')
cli_command(__name__, 'vmss stop', 'azure.cli.command_modules.vm.custom#vmss_stop')
cli_command(__name__, 'vmss restart', 'azure.cli.command_modules.vm.custom#vmss_restart')
cli_command(__name__, 'vmss start', 'azure.cli.command_modules.vm.custom#vmss_start')
cli_command(__name__, 'vmss update-instances', 'azure.cli.command_modules.vm.custom#vmss_update_instances')
cli_command(__name__, 'vmss reimage', 'azure.cli.command_modules.vm.custom#vmss_reimage')
cli_command(__name__, 'vmss scale', 'azure.cli.command_modules.vm.custom#vmss_scale')

# VM Size
cli_command(__name__, 'vm list-sizes', 'azure.mgmt.compute.operations.virtual_machine_sizes_operations#VirtualMachineSizesOperations.list', cf_vm_sizes)
