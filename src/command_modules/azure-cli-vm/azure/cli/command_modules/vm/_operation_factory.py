#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

## SDK COMMAND OPERATIONS

# VM

def of_vm_create():
    from azure.cli.command_modules.vm.mgmt_vm.lib.operations import VmOperations
    return VmOperations.create_or_update

def of_vm_delete():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.delete

def of_vm_deallocate():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.deallocate

def of_vm_generalize():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.generalize

def of_vm_get():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.get

def of_vm_list_available_sizes():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.list_available_sizes

def of_vm_power_off():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.power_off

def of_vm_redeploy():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.redeploy

def of_vm_restart():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.restart

def of_vm_start():
    from azure.mgmt.compute.operations import VirtualMachinesOperations
    return VirtualMachinesOperations.start

# VMSS NIC

def of_vmss_list_nics():
    from azure.mgmt.network.operations import NetworkInterfacesOperations
    return NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces

def of_vmss_list_vm_nics():
    from azure.mgmt.network.operations import NetworkInterfacesOperations
    return NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces

def of_vmss_nics_show():
    from azure.mgmt.network.operations import NetworkInterfacesOperations
    return NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface

# VM Availability Set

def of_vm_avail_set_create():
    from azure.cli.command_modules.vm.mgmt_avail_set.lib.operations import AvailSetOperations
    return AvailSetOperations.create_or_update

def of_vm_avail_set_delete():
    from azure.mgmt.compute.operations import AvailabilitySetsOperations
    return AvailabilitySetsOperations.delete

def of_vm_avail_set_get():
    from azure.mgmt.compute.operations import AvailabilitySetsOperations
    return AvailabilitySetsOperations.get

def of_vm_avail_set_list():
    from azure.mgmt.compute.operations import AvailabilitySetsOperations
    return AvailabilitySetsOperations.list

def of_vm_avail_set_list_available_sizes():
    from azure.mgmt.compute.operations import AvailabilitySetsOperations
    return AvailabilitySetsOperations.list_available_sizes

# VM Container (ACS)

def of_vm_acs_create():
    from azure.cli.command_modules.vm.mgmt_acs.lib.operations import AcsOperations
    return AcsOperations.create_or_update

def of_vm_acs_get():
    from azure.mgmt.compute.operations import ContainerServiceOperations
    return ContainerServiceOperations.get

def of_vm_acs_list():
    from azure.mgmt.compute.operations import ContainerServiceOperations
    return ContainerServiceOperations.list

def of_vm_acs_delete():
    from azure.mgmt.compute.operations import ContainerServiceOperations
    return ContainerServiceOperations.delete

# VM Extension

def of_vm_ext_delete():
    from azure.mgmt.compute.operations import VirtualMachineExtensionsOperations
    return VirtualMachineExtensionsOperations.delete

def of_vm_ext_get():
    from azure.mgmt.compute.operations import VirtualMachineExtensionsOperations
    return VirtualMachineExtensionsOperations.get

# VM Extension Image

def of_vm_ext_image_get():
    from azure.mgmt.compute.operations import VirtualMachineExtensionImagesOperations
    return VirtualMachineExtensionImagesOperations.get

def of_vm_ext_image_list_types():
    from azure.mgmt.compute.operations import VirtualMachineExtensionImagesOperations
    return VirtualMachineExtensionImagesOperations.list_types

def of_vm_ext_image_list_versions():
    from azure.mgmt.compute.operations import VirtualMachineExtensionImagesOperations
    return VirtualMachineExtensionImagesOperations.list_versions

# VM Image

def of_vm_image_get():
    from azure.mgmt.compute.operations import VirtualMachineImagesOperations
    return VirtualMachineImagesOperations.get

def of_vm_image_list_offers():
    from azure.mgmt.compute.operations import VirtualMachineImagesOperations
    return VirtualMachineImagesOperations.list_offers

def of_vm_image_list_publishers():
    from azure.mgmt.compute.operations import VirtualMachineImagesOperations
    return VirtualMachineImagesOperations.list_publishers

def of_vm_image_list_skus():
    from azure.mgmt.compute.operations import VirtualMachineImagesOperations
    return VirtualMachineImagesOperations.list_skus

# VM Usage

def of_vm_usage_list():
    from azure.mgmt.compute.operations import UsageOperations
    return UsageOperations.list

# VMSS

def of_vmss_create():
    from azure.cli.command_modules.vm.mgmt_vmss.lib.operations import VmssOperations
    return VmssOperations.create_or_update

def of_vmss_delete():
    from azure.mgmt.compute.operations import VirtualMachineScaleSetsOperations
    return VirtualMachineScaleSetsOperations.delete

def of_vmss_list_skus():
    from azure.mgmt.compute.operations import VirtualMachineScaleSetsOperations
    return VirtualMachineScaleSetsOperations.list_skus

def of_vmss_list():
    from azure.mgmt.compute.operations import VirtualMachineScaleSetVMsOperations
    return VirtualMachineScaleSetVMsOperations.list

# VM Size

def of_vm_size_list():
    from azure.mgmt.compute.operations import VirtualMachineSizesOperations
    return VirtualMachineSizesOperations.list


## CUSTOM COMMAND OPERATIONS

# VM

def of_vm_list_ip_addresses():
    from azure.cli.command_modules.vm.custom import list_ip_addresses
    return list_ip_addresses

def of_vm_list():
    from azure.cli.command_modules.vm.custom import list_vm
    return list_vm

def of_vm_get_instance_view():
    from azure.cli.command_modules.vm.custom import get_instance_view
    return get_instance_view

def of_vm_resize_vm():
    from azure.cli.command_modules.vm.custom import resize_vm
    return resize_vm

def of_vm_capture_vm():
    from azure.cli.command_modules.vm.custom import capture_vm
    return capture_vm

def of_vm_open_port():
    from azure.cli.command_modules.vm.custom import vm_open_port
    return vm_open_port

# VM NIC

def of_vm_add_nics():
    from azure.cli.command_modules.vm.custom import vm_add_nics
    return vm_add_nics

def of_vm_delete_nics():
    from azure.cli.command_modules.vm.custom import vm_delete_nics
    return vm_delete_nics

def of_vm_update_nics():
    from azure.cli.command_modules.vm.custom import vm_update_nics
    return vm_update_nics

# VM Access

def of_vm_access_set_linux_user():
    from azure.cli.command_modules.vm.custom import set_linux_user
    return set_linux_user

def of_vm_access_delete_linux_user():
    from azure.cli.command_modules.vm.custom import delete_linux_user
    return delete_linux_user

def of_vm_access_reset_windows_admin():
    from azure.cli.command_modules.vm.custom import reset_windows_admin
    return reset_windows_admin

# VM Boot Diagnostics

def of_vm_boot_diagnostics_disable():
    from azure.cli.command_modules.vm.custom import disable_boot_diagnostics
    return disable_boot_diagnostics

def of_vm_boot_diagnostics_enable():
    from azure.cli.command_modules.vm.custom import enable_boot_diagnostics
    return enable_boot_diagnostics

def of_vm_get_boot_log():
    from azure.cli.command_modules.vm.custom import get_boot_log
    return get_boot_log

# VM Diagnostics

def of_vm_set_diagnostics_extension():
    from azure.cli.command_modules.vm.custom import set_diagnostics_extension
    return set_diagnostics_extension

def of_vm_show_default_diagnostics_configuration():
    from azure.cli.command_modules.vm.custom import show_default_diagnostics_configuration
    return show_default_diagnostics_configuration

# VMSS Diagnostics

def of_vm_set_vmss_diagnostics_extension():
    from azure.cli.command_modules.vm.custom import set_vmss_diagnostics_extension
    return set_vmss_diagnostics_extension

# VM Disk

def of_vm_attach_new_disk():
    from azure.cli.command_modules.vm.custom import attach_new_disk
    return attach_new_disk

def of_vm_attach_existing_disk():
    from azure.cli.command_modules.vm.custom import attach_existing_disk
    return attach_existing_disk

def of_vm_detach_disk():
    from azure.cli.command_modules.vm.custom import detach_disk
    return detach_disk

def of_vm_list_disks():
    from azure.cli.command_modules.vm.custom import list_disks
    return list_disks

# VM Extension

def of_vm_set_extension():
    from azure.cli.command_modules.vm.custom import set_extension
    return set_extension

def of_vm_list_extensions():
    from azure.cli.command_modules.vm.custom import list_extensions
    return list_extensions

# VMSS Extension

def of_vm_delete_vmss_extension():
    from azure.cli.command_modules.vm.custom import delete_vmss_extension
    return delete_vmss_extension

def of_vm_get_vmss_extension():
    from azure.cli.command_modules.vm.custom import get_vmss_extension
    return get_vmss_extension

def of_vm_set_vmss_extension():
    from azure.cli.command_modules.vm.custom import set_vmss_extension
    return set_vmss_extension

def of_vm_list_vmss_extensions():
    from azure.cli.command_modules.vm.custom import list_vmss_extensions
    return list_vmss_extensions

# VM Extension Image

def of_vm_list_vm_extension_images():
    from azure.cli.command_modules.vm.custom import list_vm_extension_images
    return list_vm_extension_images

# VM Image

def of_vm_list_vm_images():
    from azure.cli.command_modules.vm.custom import list_vm_images
    return list_vm_images

# VMSS

def of_vm_vmss_deallocate():
    from azure.cli.command_modules.vm.custom import vmss_deallocate
    return vmss_deallocate

def of_vm_vmss_delete_instances():
    from azure.cli.command_modules.vm.custom import vmss_delete_instances
    return vmss_delete_instances

def of_vm_vmss_get_instance_view():
    from azure.cli.command_modules.vm.custom import vmss_get_instance_view
    return vmss_get_instance_view

def of_vm_vmss_show():
    from azure.cli.command_modules.vm.custom import vmss_show
    return vmss_show

def of_vm_vmss_list():
    from azure.cli.command_modules.vm.custom import vmss_list
    return vmss_list

def of_vm_vmss_stop():
    from azure.cli.command_modules.vm.custom import vmss_stop
    return vmss_stop

def of_vm_vmss_restart():
    from azure.cli.command_modules.vm.custom import vmss_restart
    return vmss_restart

def of_vm_vmss_start():
    from azure.cli.command_modules.vm.custom import vmss_start
    return vmss_start

def of_vm_vmss_update_instances():
    from azure.cli.command_modules.vm.custom import vmss_update_instances
    return vmss_update_instances

def of_vm_vmss_reimage():
    from azure.cli.command_modules.vm.custom import vmss_reimage
    return vmss_reimage

def of_vm_vmss_scale():
    from azure.cli.command_modules.vm.custom import vmss_scale
    return vmss_scale
