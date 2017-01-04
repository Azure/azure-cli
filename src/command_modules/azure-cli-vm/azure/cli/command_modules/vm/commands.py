# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command

from azure.cli.core.commands.arm import cli_generic_update_command, cli_generic_wait_command

from azure.cli.command_modules.vm._client_factory import * #pylint: disable=wildcard-import,unused-wildcard-import

#pylint: disable=line-too-long

custom_path = 'azure.cli.command_modules.vm.custom#{}'
mgmt_path = 'azure.mgmt.compute.operations.{}#{}.{}'

# VM

cli_command(__name__, 'vm create', 'azure.cli.command_modules.vm.mgmt_vm.lib.operations.vm_operations#VmOperations.create_or_update', cf_vm_create,
            transform=DeploymentOutputLongRunningOperation('Starting vm create'), no_wait_param='raw')

op_var = 'virtual_machines_operations'
op_class = 'VirtualMachinesOperations'
cli_command(__name__, 'vm delete', mgmt_path.format(op_var, op_class, 'delete'), cf_vm)
cli_command(__name__, 'vm deallocate', mgmt_path.format(op_var, op_class, 'deallocate'), cf_vm)
cli_command(__name__, 'vm generalize', mgmt_path.format(op_var, op_class, 'generalize'), cf_vm)
cli_command(__name__, 'vm show', mgmt_path.format(op_var, op_class, 'get'), cf_vm)
cli_command(__name__, 'vm list-vm-resize-options', mgmt_path.format(op_var, op_class, 'list_available_sizes'), cf_vm)
cli_command(__name__, 'vm stop', mgmt_path.format(op_var, op_class, 'power_off'), cf_vm)
cli_command(__name__, 'vm restart', mgmt_path.format(op_var, op_class, 'restart'), cf_vm)
cli_command(__name__, 'vm start', mgmt_path.format(op_var, op_class, 'start'), cf_vm)
cli_command(__name__, 'vm redeploy', mgmt_path.format(op_var, op_class, 'redeploy'), cf_vm)
cli_command(__name__, 'vm list-ip-addresses', custom_path.format('list_ip_addresses'))
cli_command(__name__, 'vm get-instance-view', custom_path.format('get_instance_view'))
cli_command(__name__, 'vm list', custom_path.format('list_vm'))
cli_command(__name__, 'vm resize', custom_path.format('resize_vm'))
cli_command(__name__, 'vm capture', custom_path.format('capture_vm'))
cli_command(__name__, 'vm open-port', custom_path.format('vm_open_port'))
cli_generic_update_command(__name__, 'vm update',
                           mgmt_path.format(op_var, op_class, 'get'),
                           mgmt_path.format(op_var, op_class, 'create_or_update'),
                           cf_vm,
                           no_wait_param='raw')
cli_generic_wait_command(__name__, 'vm wait', 'azure.cli.command_modules.vm.custom#get_instance_view')

# VM NIC
cli_command(__name__, 'vm nic add', custom_path.format('vm_add_nics'))
cli_command(__name__, 'vm nic remove', custom_path.format('vm_remove_nics'))
cli_command(__name__, 'vm nic set', custom_path.format('vm_set_nics'))
cli_command(__name__, 'vm nic show', custom_path.format('vm_show_nic'))
cli_command(__name__, 'vm nic list', custom_path.format('vm_list_nics'))

# VMSS NIC
cli_command(__name__, 'vmss nic list', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces', cf_ni)
cli_command(__name__, 'vmss nic list-vm-nics', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces', cf_ni)
cli_command(__name__, 'vmss nic show', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface', cf_ni)

# VM Access
cli_command(__name__, 'vm access set-linux-user', custom_path.format('set_linux_user'))
cli_command(__name__, 'vm access delete-linux-user', custom_path.format('delete_linux_user'))
cli_command(__name__, 'vm access reset-windows-admin', custom_path.format('reset_windows_admin'))

# # VM Availability Set
cli_command(__name__, 'vm availability-set create', 'azure.cli.command_modules.vm.mgmt_avail_set.lib.operations.avail_set_operations#AvailSetOperations.create_or_update', cf_avail_set_create)

op_var = 'availability_sets_operations'
op_class = 'AvailabilitySetsOperations'
cli_command(__name__, 'vm availability-set delete', mgmt_path.format(op_var, op_class, 'delete'), cf_avail_set)
cli_command(__name__, 'vm availability-set show', mgmt_path.format(op_var, op_class, 'get'), cf_avail_set)
cli_command(__name__, 'vm availability-set list', mgmt_path.format(op_var, op_class, 'list'), cf_avail_set)
cli_command(__name__, 'vm availability-set list-sizes', mgmt_path.format(op_var, op_class, 'list_available_sizes'), cf_avail_set)

cli_generic_update_command(__name__, 'vm availability-set update',
                           custom_path.format('availset_get'),
                           custom_path.format('availset_set'))
cli_generic_update_command(__name__, 'vmss update',
                           custom_path.format('vmss_get'),
                           custom_path.format('vmss_set'))

# VM Boot Diagnostics
cli_command(__name__, 'vm boot-diagnostics disable', custom_path.format('disable_boot_diagnostics'))
cli_command(__name__, 'vm boot-diagnostics enable', custom_path.format('enable_boot_diagnostics'))
cli_command(__name__, 'vm boot-diagnostics get-boot-log', custom_path.format('get_boot_log'))

# ACS

def transform_acs(r):
    orchestratorType = 'Unknown'
    orchestratorProfile = r.get('orchestratorProfile')
    if orchestratorProfile:
        orchestratorType = orchestratorProfile.get('orchestratorType')
    res = OrderedDict([('Name', r['name']), ('ResourceGroup', r['resourceGroup']), \
        ('Orchestrator', orchestratorType), ('Location', r['location']), \
        ('ProvisioningState', r['provisioningState'])])
    return res

def transform_acs_list(result):
    transformed = []
    for r in result:
        res = transform_acs(r)
        transformed.append(res)
    return transformed

#Remove the hack after https://github.com/Azure/azure-rest-api-specs/issues/352 fixed
from azure.mgmt.compute.models import ContainerService#pylint: disable=wrong-import-position
for a in ['id', 'name', 'type', 'location']:
    ContainerService._attribute_map[a]['type'] = 'str'#pylint: disable=protected-access
ContainerService._attribute_map['tags']['type'] = '{str}'#pylint: disable=protected-access
######
op_var = 'container_services_operations'
op_class = 'ContainerServicesOperations'
cli_command(__name__, 'acs show', mgmt_path.format(op_var, op_class, 'get'), cf_acs, table_transformer=transform_acs)
cli_command(__name__, 'acs list', custom_path.format('list_container_services'), cf_acs, table_transformer=transform_acs_list)
cli_command(__name__, 'acs delete', mgmt_path.format(op_var, op_class, 'delete'), cf_acs)
cli_command(__name__, 'acs scale', custom_path.format('update_acs'))
#Per conversation with ACS team, hide the update till we have something meaningful to tweak
# from azure.cli.command_modules.vm.custom import update_acs
# cli_generic_update_command(__name__, 'acs update', ContainerServicesOperations.get, ContainerServicesOperations.create_or_update, cf_acs)

# VM Diagnostics
cli_command(__name__, 'vm diagnostics set', custom_path.format('set_diagnostics_extension'))
cli_command(__name__, 'vm diagnostics get-default-config', custom_path.format('show_default_diagnostics_configuration'))

# VMSS Diagnostics
cli_command(__name__, 'vmss diagnostics set', custom_path.format('set_vmss_diagnostics_extension'))
cli_command(__name__, 'vmss diagnostics get-default-config', custom_path.format('show_default_diagnostics_configuration'))

# VM Disk
cli_command(__name__, 'vm disk attach-new', custom_path.format('attach_new_disk'))
cli_command(__name__, 'vm disk attach-existing', custom_path.format('attach_existing_disk'))
cli_command(__name__, 'vm disk detach', custom_path.format('detach_disk'))
cli_command(__name__, 'vm disk list', custom_path.format('list_disks'))

# VM Extension
op_var = 'virtual_machine_extensions_operations'
op_class = 'VirtualMachineExtensionsOperations'
cli_command(__name__, 'vm extension delete', mgmt_path.format(op_var, op_class, 'delete'), cf_vm_ext)
cli_command(__name__, 'vm extension show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext)
cli_command(__name__, 'vm extension set', custom_path.format('set_extension'))
cli_command(__name__, 'vm extension list', custom_path.format('list_extensions'))

# VMSS Extension
cli_command(__name__, 'vmss extension delete', custom_path.format('delete_vmss_extension'))
cli_command(__name__, 'vmss extension show', custom_path.format('get_vmss_extension'))
cli_command(__name__, 'vmss extension set', custom_path.format('set_vmss_extension'))
cli_command(__name__, 'vmss extension list', custom_path.format('list_vmss_extensions'))

# VM Extension Image
op_var = 'virtual_machine_extension_images_operations'
op_class = 'VirtualMachineExtensionImagesOperations'
cli_command(__name__, 'vm extension image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext_image)
cli_command(__name__, 'vm extension image list-names', mgmt_path.format(op_var, op_class, 'list_types'), cf_vm_ext_image)
cli_command(__name__, 'vm extension image list-versions', mgmt_path.format(op_var, op_class, 'list_versions'), cf_vm_ext_image)
cli_command(__name__, 'vm extension image list', custom_path.format('list_vm_extension_images'))

# VMSS Extension Image (convenience copy of VM Extension Image)
cli_command(__name__, 'vmss extension image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list-names', mgmt_path.format(op_var, op_class, 'list_types'), cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list-versions', mgmt_path.format(op_var, op_class, 'list_versions'), cf_vm_ext_image)
cli_command(__name__, 'vmss extension image list', custom_path.format('list_vm_extension_images'))

# VM Image
op_var = 'virtual_machine_images_operations'
op_class = 'VirtualMachineImagesOperations'
cli_command(__name__, 'vm image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_image)
cli_command(__name__, 'vm image list-offers', mgmt_path.format(op_var, op_class, 'list_offers'), cf_vm_image)
cli_command(__name__, 'vm image list-publishers', mgmt_path.format(op_var, op_class, 'list_publishers'), cf_vm_image)
cli_command(__name__, 'vm image list-skus', mgmt_path.format(op_var, op_class, 'list_skus'), cf_vm_image)
cli_command(__name__, 'vm image list', custom_path.format('list_vm_images'))

# VM Usage
cli_command(__name__, 'vm list-usage', mgmt_path.format('usage_operations', 'UsageOperations', 'list'), cf_usage)

# VMSS
cli_command(__name__, 'vmss create', 'azure.cli.command_modules.vm.mgmt_vmss.lib.operations.vmss_operations#VmssOperations.create_or_update', cf_vmss_create,
            transform=DeploymentOutputLongRunningOperation('Starting vmss create'))

cli_command(__name__, 'vmss delete', mgmt_path.format('virtual_machine_scale_sets_operations', 'VirtualMachineScaleSetsOperations', 'delete'), cf_vmss)
cli_command(__name__, 'vmss list-skus', mgmt_path.format('virtual_machine_scale_sets_operations', 'VirtualMachineScaleSetsOperations', 'list_skus'), cf_vmss)

cli_command(__name__, 'vmss list-instances', mgmt_path.format('virtual_machine_scale_set_vms_operations', 'VirtualMachineScaleSetVMsOperations', 'list'), cf_vmss_vm)

cli_command(__name__, 'vmss deallocate', custom_path.format('vmss_deallocate'))
cli_command(__name__, 'vmss delete-instances', custom_path.format('vmss_delete_instances'))
cli_command(__name__, 'vmss get-instance-view', custom_path.format('vmss_get_instance_view'))
cli_command(__name__, 'vmss show', custom_path.format('vmss_show'))
cli_command(__name__, 'vmss list', custom_path.format('vmss_list'))
cli_command(__name__, 'vmss stop', custom_path.format('vmss_stop'))
cli_command(__name__, 'vmss restart', custom_path.format('vmss_restart'))
cli_command(__name__, 'vmss start', custom_path.format('vmss_start'))
cli_command(__name__, 'vmss update-instances', custom_path.format('vmss_update_instances'))
cli_command(__name__, 'vmss reimage', custom_path.format('vmss_reimage'))
cli_command(__name__, 'vmss scale', custom_path.format('vmss_scale'))

# VM Size
cli_command(__name__, 'vm list-sizes', mgmt_path.format('virtual_machine_sizes_operations', 'VirtualMachineSizesOperations', 'list'), cf_vm_sizes)

