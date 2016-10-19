#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.compute.operations import (
    AvailabilitySetsOperations,
    VirtualMachineExtensionImagesOperations,
    VirtualMachineExtensionsOperations,
    VirtualMachineImagesOperations,
    UsageOperations,
    VirtualMachineSizesOperations,
    VirtualMachinesOperations,
    VirtualMachineScaleSetsOperations,
    VirtualMachineScaleSetVMsOperations,
    ContainerServiceOperations)
from azure.mgmt.network.operations import NetworkInterfacesOperations
from azure.mgmt.network import NetworkManagementClient
from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.command_modules.vm.mgmt_avail_set.lib import (AvailSetCreationClient
                                                             as AvailSetClient)
from azure.cli.command_modules.vm.mgmt_avail_set.lib.operations import AvailSetOperations
from azure.cli.command_modules.vm.mgmt_vm.lib import VmCreationClient as VMClient
from azure.cli.command_modules.vm.mgmt_vm.lib.operations import VmOperations
from azure.cli.command_modules.vm.mgmt_vmss.lib import VmssCreationClient as VMSSClient
from azure.cli.command_modules.vm.mgmt_vmss.lib.operations import VmssOperations
from azure.cli.command_modules.vm.mgmt_acs.lib import AcsCreationClient as ACSClient
from azure.cli.command_modules.vm.mgmt_acs.lib.operations import AcsOperations
from .custom import (
    list_vm, resize_vm, list_vm_images, list_vm_extension_images, list_ip_addresses,
    attach_new_disk, attach_existing_disk, detach_disk, list_disks, capture_vm, get_instance_view,
    vm_update_nics, vm_delete_nics, vm_add_nics, vm_open_port,
    reset_windows_admin, set_linux_user, delete_linux_user,
    disable_boot_diagnostics, enable_boot_diagnostics, get_boot_log,
    list_extensions, set_extension, set_diagnostics_extension,
    show_default_diagnostics_configuration,
    vmss_start, vmss_restart, vmss_delete_instances, vmss_deallocate, vmss_get_instance_view,
    vmss_stop, vmss_reimage, vmss_scale, vmss_update_instances, vmss_show, vmss_list,
    set_vmss_diagnostics_extension, set_vmss_extension, get_vmss_extension,
    list_vmss_extensions, delete_vmss_extension, update_acs)


from ._factory import _compute_client_factory

# pylint: disable=line-too-long

# VM
factory = lambda _: get_mgmt_service_client(VMClient).vm
cli_command('vm create', VmOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting vm create'))

factory = lambda _: _compute_client_factory().virtual_machines

cli_command('vm delete', VirtualMachinesOperations.delete, factory)
cli_command('vm deallocate', VirtualMachinesOperations.deallocate, factory)
cli_command('vm generalize', VirtualMachinesOperations.generalize, factory)
cli_command('vm show', VirtualMachinesOperations.get, factory)
cli_command('vm list-vm-resize-options', VirtualMachinesOperations.list_available_sizes, factory)
cli_command('vm get-instance-view', get_instance_view)
cli_command('vm stop', VirtualMachinesOperations.power_off, factory)
cli_command('vm restart', VirtualMachinesOperations.restart, factory)
cli_command('vm start', VirtualMachinesOperations.start, factory)
cli_command('vm redeploy', VirtualMachinesOperations.redeploy, factory)
cli_command('vm list-ip-addresses', list_ip_addresses)
cli_command('vm list', list_vm)
cli_command('vm resize', resize_vm)
cli_command('vm capture', capture_vm)
cli_command('vm open-port', vm_open_port)
cli_generic_update_command('vm update', VirtualMachinesOperations.get, VirtualMachinesOperations.create_or_update, factory)

# VM NIC
cli_command('vm nic add', vm_add_nics)
cli_command('vm nic delete', vm_delete_nics)
cli_command('vm nic update', vm_update_nics)

# VMSS NIC
# TODO: Remove hard coded api-version once https://github.com/Azure/azure-rest-api-specs/issues/570
# is fixed.
factory = lambda _: get_mgmt_service_client(NetworkManagementClient, api_version='2016-03-30').network_interfaces
cli_command('vmss nic list', NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, factory)
cli_command('vmss nic list-vm-nics', NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, factory)
cli_command('vmss nic show', NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, factory)

# VM Access
cli_command('vm access set-linux-user', set_linux_user)
cli_command('vm access delete-linux-user', delete_linux_user)
cli_command('vm access reset-windows-admin', reset_windows_admin)

# VM Availability Set
factory = lambda _: get_mgmt_service_client(AvailSetClient).avail_set
cli_command('vm availability-set create', AvailSetOperations.create_or_update, factory)

factory = lambda _: _compute_client_factory().availability_sets
cli_command('vm availability-set delete', AvailabilitySetsOperations.delete, factory)
cli_command('vm availability-set show', AvailabilitySetsOperations.get, factory)
cli_command('vm availability-set list', AvailabilitySetsOperations.list, factory)
cli_command('vm availability-set list-sizes', AvailabilitySetsOperations.list_available_sizes, factory)

# VM Boot Diagnostics
cli_command('vm boot-diagnostics disable', disable_boot_diagnostics)
cli_command('vm boot-diagnostics enable', enable_boot_diagnostics)
cli_command('vm boot-diagnostics get-boot-log', get_boot_log)

# VM Container (ACS)
factory = lambda _: get_mgmt_service_client(ACSClient).acs
cli_command('acs create', AcsOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting container service create'))

factory = lambda _: _compute_client_factory().container_service
#Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
for a in ['id', 'name', 'type', 'location']:
    ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
######
cli_command('acs show', ContainerServiceOperations.get, factory)
cli_command('acs list', ContainerServiceOperations.list, factory)
cli_command('acs delete', ContainerServiceOperations.delete, factory)
cli_generic_update_command('acs update', ContainerServiceOperations.get,
                           ContainerServiceOperations.create_or_update,
                           custom_function=update_acs, factory=factory)

# VM Diagnostics
cli_command('vm diagnostics set', set_diagnostics_extension)
cli_command('vm diagnostics get-default-config', show_default_diagnostics_configuration)

# VMSS Diagnostics
cli_command('vmss diagnostics set', set_vmss_diagnostics_extension)
cli_command('vmss diagnostics get-default-config', show_default_diagnostics_configuration)

# VM Disk
cli_command('vm disk attach-new', attach_new_disk)
cli_command('vm disk attach-existing', attach_existing_disk)
cli_command('vm disk detach', detach_disk)
cli_command('vm disk list', list_disks)

# VM Extension
factory = lambda _: _compute_client_factory().virtual_machine_extensions
cli_command('vm extension delete', VirtualMachineExtensionsOperations.delete, factory)
cli_command('vm extension show', VirtualMachineExtensionsOperations.get, factory)
cli_command('vm extension set', set_extension)
cli_command('vm extension list', list_extensions)

# VMSS Extension
cli_command('vmss extension delete', delete_vmss_extension)
cli_command('vmss extension show', get_vmss_extension)
cli_command('vmss extension set', set_vmss_extension)
cli_command('vmss extension list', list_vmss_extensions)

# VM Extension Image
factory = lambda _: _compute_client_factory().virtual_machine_extension_images
cli_command('vm extension image show', VirtualMachineExtensionImagesOperations.get, factory)
cli_command('vm extension image list-names', VirtualMachineExtensionImagesOperations.list_types, factory)
cli_command('vm extension image list-versions', VirtualMachineExtensionImagesOperations.list_versions, factory)
cli_command('vm extension image list', list_vm_extension_images)

# VMSS Extension Image (convenience copy of VM Extension Image)
factory = lambda _: _compute_client_factory().virtual_machine_extension_images
cli_command('vmss extension image show', VirtualMachineExtensionImagesOperations.get, factory)
cli_command('vmss extension image list-names', VirtualMachineExtensionImagesOperations.list_types, factory)
cli_command('vmss extension image list-versions', VirtualMachineExtensionImagesOperations.list_versions, factory)
cli_command('vmss extension image list', list_vm_extension_images)

# VM Image
factory = lambda _: _compute_client_factory().virtual_machine_images
cli_command('vm image show', VirtualMachineImagesOperations.get, factory)
cli_command('vm image list-offers', VirtualMachineImagesOperations.list_offers, factory)
cli_command('vm image list-publishers', VirtualMachineImagesOperations.list_publishers, factory)
cli_command('vm image list-skus', VirtualMachineImagesOperations.list_skus, factory)
cli_command('vm image list', list_vm_images)

# VM Usage
factory = lambda _: _compute_client_factory().usage
cli_command('vm list-usage', UsageOperations.list, factory)

# VM ScaleSet
factory = lambda _: get_mgmt_service_client(VMSSClient).vmss
cli_command('vmss create', VmssOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting vmss create'))

factory = lambda _: _compute_client_factory().virtual_machine_scale_sets
cli_command('vmss delete', VirtualMachineScaleSetsOperations.delete, factory)
cli_command('vmss list-skus', VirtualMachineScaleSetsOperations.list_skus, factory)

factory = lambda _: _compute_client_factory().virtual_machine_scale_set_vms
cli_command('vmss list-instances', VirtualMachineScaleSetVMsOperations.list, factory)

cli_command('vmss deallocate', vmss_deallocate)
cli_command('vmss delete-instances', vmss_delete_instances)
cli_command('vmss get-instance-view', vmss_get_instance_view)
cli_command('vmss show', vmss_show)
cli_command('vmss list ', vmss_list)
cli_command('vmss stop', vmss_stop)
cli_command('vmss restart', vmss_restart)
cli_command('vmss start', vmss_start)
cli_command('vmss update-instances', vmss_update_instances)
cli_command('vmss reimage', vmss_reimage)
cli_command('vmss scale', vmss_scale)

# VM Size
factory = lambda _: _compute_client_factory().virtual_machine_sizes
cli_command('vm list-sizes', VirtualMachineSizesOperations.list, factory)
