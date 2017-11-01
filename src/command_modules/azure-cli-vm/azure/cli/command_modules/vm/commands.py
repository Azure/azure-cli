# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from azure.cli.command_modules.vm._client_factory import (cf_vm, cf_avail_set, cf_ni,
                                                          cf_vm_ext,
                                                          cf_vm_ext_image, cf_vm_image, cf_usage,
                                                          cf_vmss, cf_vmss_vm,
                                                          cf_vm_sizes, cf_disks, cf_snapshots,
                                                          cf_images, cf_run_commands,
                                                          cf_rolling_upgrade_commands)
from azure.cli.command_modules.vm._validators import \
    (process_vm_create_namespace, process_vmss_create_namespace, process_image_create_namespace,
     process_disk_or_snapshot_create_namespace, process_disk_encryption_namespace, process_assign_identity_namespace)

from azure.cli.core.commands import DeploymentOutputLongRunningOperation
from azure.cli.core.commands.arm import handle_long_running_operation_exception, deployment_validate_table_format
from azure.cli.core.util import empty_on_404
from azure.cli.core.profiles import ResourceType
from azure.cli.core.sdk.util import CliCommandType

# pylint: disable=line-too-long

custom_path = 'azure.cli.command_modules.vm.custom#{}'
mgmt_path = 'azure.mgmt.compute.operations.{}#{}.{}'

# VM
def transform_ip_addresses(result):
    transformed = []
    for r in result:
        network = r['virtualMachine']['network']
        public = network.get('publicIpAddresses')
        public_ip_addresses = ','.join([p['ipAddress'] for p in public if p['ipAddress']]) if public else None
        private = network.get('privateIpAddresses')
        private_ip_addresses = ','.join(private) if private else None
        entry = OrderedDict([('virtualMachine', r['virtualMachine']['name']),
                             ('publicIPAddresses', public_ip_addresses),
                             ('privateIPAddresses', private_ip_addresses)])
        transformed.append(entry)

    return transformed


def transform_vm(vm):
    result = OrderedDict([('name', vm['name']),
                          ('resourceGroup', vm['resourceGroup']),
                          ('powerState', vm.get('powerState')),
                          ('publicIps', vm.get('publicIps')),
                          ('fqdns', vm.get('fqdns')),
                          ('location', vm['location'])])
    if 'zones' in vm:
        result['zones'] = ','.join(vm['zones']) if vm['zones'] else ''
    return result


def transform_vm_create_output(result):
    from msrestazure.tools import parse_resource_id
    try:
        output = OrderedDict([('id', result.id),
                              ('resourceGroup', getattr(result, 'resource_group', None) or parse_resource_id(result.id)['resource_group']),
                              ('powerState', result.power_state),
                              ('publicIpAddress', result.public_ips),
                              ('fqdns', result.fqdns),
                              ('privateIpAddress', result.private_ips),
                              ('macAddress', result.mac_addresses),
                              ('location', result.location)])
        if getattr(result, 'identity', None):
            output['identity'] = result.identity
        if hasattr(result, 'zones'):  # output 'zones' column even the property value is None
            output['zones'] = result.zones[0] if result.zones else ''
        return output
    except AttributeError:
        from msrest.pipeline import ClientRawResponse
        return None if isinstance(result, ClientRawResponse) else result


def transform_vm_usage_list(result):
    result = list(result)
    for item in result:
        item.current_value = str(item.current_value)
        item.limit = str(item.limit)
        item.local_name = item.name.localized_value
    return result


def transform_vm_list(vm_list):
    return [transform_vm(v) for v in vm_list]


# flattern out important fields (single member arrays) to be displayed in the table output
def transform_sku_for_table_output(skus):
    result = []
    for k in skus:
        order_dict = OrderedDict()
        order_dict['resourceType'] = k['resourceType']
        order_dict['locations'] = str(k['locations']) if len(k['locations']) > 1 else k['locations'][0]
        order_dict['name'] = k['name']
        order_dict['size'] = k['size']
        order_dict['tier'] = k['tier']
        if k['capabilities']:
            temp = ['{}={}'.format(pair['name'], pair['value']) for pair in k['capabilities']]
            order_dict['capabilities'] = str(temp) if len(temp) > 1 else temp[0]
        else:
            order_dict['capabilities'] = None
        if k['restrictions']:
            reasons = [x['reasonCode'] for x in k['restrictions']]
            order_dict['restrictions'] = str(reasons) if len(reasons) > 1 else reasons[0]
        else:
            order_dict['restrictions'] = None
        result.append(order_dict)
    return result

#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2016-04-30-preview'):
#    g.command('vm convert', mgmt_path.format(op_var, op_class, 'convert_to_managed_disks'), cf_vm)

## VM encryption
#g.command('vm encryption enable', 'azure.cli.command_modules.vm.disk_encryption#encrypt_vm')
#g.command('vm encryption disable', 'azure.cli.command_modules.vm.disk_encryption#decrypt_vm')
#g.command('vm encryption show', 'azure.cli.command_modules.vm.disk_encryption#show_vm_encryption_status', exception_handler=empty_on_404)

## VMSS encryption
#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    g.command('vmss encryption enable', 'azure.cli.command_modules.vm.disk_encryption#encrypt_vmss')
#    g.command('vmss encryption disable', 'azure.cli.command_modules.vm.disk_encryption#decrypt_vmss')
#    g.command('vmss encryption show', 'azure.cli.command_modules.vm.disk_encryption#show_vmss_encryption_status', exception_handler=empty_on_404)

## VM NIC
#g.command('vm nic add', custom_path.format('vm_add_nics'))
#g.command('vm nic remove', custom_path.format('vm_remove_nics'))
#g.command('vm nic set', custom_path.format('vm_set_nics'))
#g.command('vm nic show', custom_path.format('vm_show_nic'), exception_handler=empty_on_404)
#g.command('vm nic list', custom_path.format('vm_list_nics'))

## VMSS NIC
#g.command('vmss nic list', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces', cf_ni)
#g.command('vmss nic list-vm-nics', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces', cf_ni)
#g.command('vmss nic show', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface', cf_ni, exception_handler=empty_on_404)

## VM Access
#g.command('vm user update', custom_path.format('set_user'), no_wait_param='no_wait')
#g.command('vm user delete', custom_path.format('delete_user'), no_wait_param='no_wait')
#g.command('vm user reset-ssh', custom_path.format('reset_linux_ssh'), no_wait_param='no_wait')

## # VM Availability Set
#g.command('vm availability-set create', custom_path.format('create_av_set'), table_transformer=deployment_validate_table_format, no_wait_param='no_wait')

#op_var = 'availability_sets_operations'
#op_class = 'AvailabilitySetsOperations'
#g.command('vm availability-set delete', mgmt_path.format(op_var, op_class, 'delete'), cf_avail_set)
#g.command('vm availability-set show', mgmt_path.format(op_var, op_class, 'get'), cf_avail_set, exception_handler=empty_on_404)
#g.command('vm availability-set list', mgmt_path.format(op_var, op_class, 'list'), cf_avail_set)
#g.command('vm availability-set list-sizes', mgmt_path.format(op_var, op_class, 'list_available_sizes'), cf_avail_set)
#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2016-04-30-preview'):
#    g.command('vm availability-set convert', custom_path.format('convert_av_set_to_managed_disk'))

#_cli_generic_update_command('vm availability-set update',
#                           custom_path.format('availset_get'),
#                           custom_path.format('availset_set'))

#_cli_generic_update_command('vmss update',
#                           custom_path.format('vmss_get'),
#                           custom_path.format('vmss_set'),
#                           no_wait_param='no_wait')
#_cli_generic_wait_command('vmss wait', custom_path.format('vmss_get'))

## VM Boot Diagnostics
#g.command('vm boot-diagnostics disable', custom_path.format('disable_boot_diagnostics'))
#g.command('vm boot-diagnostics enable', custom_path.format('enable_boot_diagnostics'))
#g.command('vm boot-diagnostics get-boot-log', custom_path.format('get_boot_log'))

## VM Diagnostics
#g.command('vm diagnostics set', custom_path.format('set_diagnostics_extension'))
#g.command('vm diagnostics get-default-config', custom_path.format('show_default_diagnostics_configuration'))

## VMSS Diagnostics
#g.command('vmss diagnostics set', custom_path.format('set_vmss_diagnostics_extension'))
#g.command('vmss diagnostics get-default-config', custom_path.format('show_default_diagnostics_configuration'))

#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    g.command('vm disk attach', custom_path.format('attach_managed_data_disk'))
#    g.command('vm disk detach', custom_path.format('detach_data_disk'))

#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    g.command('vmss disk attach', custom_path.format('attach_managed_data_disk_to_vmss'))
#    g.command('vmss disk detach', custom_path.format('detach_disk_from_vmss'))

#g.command('vm unmanaged-disk attach', custom_path.format('attach_unmanaged_data_disk'))
#g.command('vm unmanaged-disk detach', custom_path.format('detach_data_disk'))
#g.command('vm unmanaged-disk list', custom_path.format('list_unmanaged_disks'))

## VM Extension
#op_var = 'virtual_machine_extensions_operations'
#op_class = 'VirtualMachineExtensionsOperations'
#g.command('vm extension delete', mgmt_path.format(op_var, op_class, 'delete'), cf_vm_ext)
#_extension_show_transform = '{Name:name, ProvisioningState:provisioningState, Publisher:publisher, Version:typeHandlerVersion, AutoUpgradeMinorVersion:autoUpgradeMinorVersion}'
#g.command('vm extension show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext, exception_handler=empty_on_404,
#            table_transformer=_extension_show_transform)
#g.command('vm extension set', custom_path.format('set_extension'))
#g.command('vm extension list', custom_path.format('list_extensions'),
#            table_transformer='[].' + _extension_show_transform)

## VMSS Extension
#g.command('vmss extension delete', custom_path.format('delete_vmss_extension'))
#g.command('vmss extension show', custom_path.format('get_vmss_extension'), exception_handler=empty_on_404)
#g.command('vmss extension set', custom_path.format('set_vmss_extension'))
#g.command('vmss extension list', custom_path.format('list_vmss_extensions'))

## VM Extension Image
#op_var = 'virtual_machine_extension_images_operations'
#op_class = 'VirtualMachineExtensionImagesOperations'
#g.command('vm extension image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext_image, exception_handler=empty_on_404)
#g.command('vm extension image list-names', mgmt_path.format(op_var, op_class, 'list_types'), cf_vm_ext_image)
#g.command('vm extension image list-versions', mgmt_path.format(op_var, op_class, 'list_versions'), cf_vm_ext_image)
#g.command('vm extension image list', custom_path.format('list_vm_extension_images'))

## VMSS Extension Image (convenience copy of VM Extension Image)
#g.command('vmss extension image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_ext_image, exception_handler=empty_on_404)
#g.command('vmss extension image list-names', mgmt_path.format(op_var, op_class, 'list_types'), cf_vm_ext_image)
#g.command('vmss extension image list-versions', mgmt_path.format(op_var, op_class, 'list_versions'), cf_vm_ext_image)
#g.command('vmss extension image list', custom_path.format('list_vm_extension_images'))

## VM Image
#op_var = 'virtual_machine_images_operations'
#op_class = 'VirtualMachineImagesOperations'
#g.command('vm image show', mgmt_path.format(op_var, op_class, 'get'), cf_vm_image, exception_handler=empty_on_404)
#g.command('vm image list-offers', mgmt_path.format(op_var, op_class, 'list_offers'), cf_vm_image)
#g.command('vm image list-publishers', mgmt_path.format(op_var, op_class, 'list_publishers'), cf_vm_image)
#g.command('vm image list-skus', mgmt_path.format(op_var, op_class, 'list_skus'), cf_vm_image)
#g.command('vm image list', custom_path.format('list_vm_images'))

## VM Usage
#g.command('vm list-usage', mgmt_path.format('usage_operations', 'UsageOperations', 'list'), cf_usage, transform=transform_vm_usage_list,
#            table_transformer='[].{Name:localName, CurrentValue:currentValue, Limit:limit}')

## VMSS
#vmss_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Capacity:sku.capacity, Overprovision:overprovision, UpgradePolicy:upgradePolicy.mode}'
#vmss_show_table_transform = vmss_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30') else ' ')
#g.command('vmss delete', mgmt_path.format('virtual_machine_scale_sets_operations', 'VirtualMachineScaleSetsOperations', 'delete'), cf_vmss, no_wait_param='raw')
#g.command('vmss list-skus', mgmt_path.format('virtual_machine_scale_sets_operations', 'VirtualMachineScaleSetsOperations', 'list_skus'), cf_vmss)

#g.command('vmss list-instances', mgmt_path.format('virtual_machine_scale_set_vms_operations', 'VirtualMachineScaleSetVMsOperations', 'list'), cf_vmss_vm)

#g.command('vmss create', custom_path.format('create_vmss'), transform=DeploymentOutputLongRunningOperation('Starting vmss create'), no_wait_param='no_wait', table_transformer=deployment_validate_table_format)
#g.command('vmss deallocate', custom_path.format('deallocate_vmss'), no_wait_param='no_wait')
#g.command('vmss delete-instances', custom_path.format('delete_vmss_instances'), no_wait_param='no_wait')
#g.command('vmss get-instance-view', custom_path.format('get_vmss_instance_view'),
#            table_transformer='{ProvisioningState:statuses[0].displayStatus, PowerState:statuses[1].displayStatus}')
#g.command('vmss show', custom_path.format('show_vmss'), exception_handler=empty_on_404,
#            table_transformer=vmss_show_table_transform)
#g.command('vmss list', custom_path.format('list_vmss'), table_transformer='[].' + vmss_show_table_transform)
#g.command('vmss stop', custom_path.format('stop_vmss'), no_wait_param='no_wait')
#g.command('vmss restart', custom_path.format('restart_vmss'), no_wait_param='no_wait')
#g.command('vmss start', custom_path.format('start_vmss'), no_wait_param='no_wait')
#g.command('vmss update-instances', custom_path.format('update_vmss_instances'), no_wait_param='no_wait')
#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    g.command('vmss reimage', custom_path.format('reimage_vmss'), no_wait_param='no_wait')
#g.command('vmss scale', custom_path.format('scale_vmss'), no_wait_param='no_wait')
#g.command('vmss list-instance-connection-info', custom_path.format('list_vmss_instance_connection_info'))
#g.command('vmss list-instance-public-ips', custom_path.format('list_vmss_instance_public_ips'))

## VM Size
#g.command('vm list-sizes', mgmt_path.format('virtual_machine_sizes_operations', 'VirtualMachineSizesOperations', 'list'), cf_vm_sizes)

#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    # VM Disk
#    disk_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Sku:sku.name, OsType:osType, SizeGb:diskSizeGb, ProvisioningState:provisioningState}'
#    disk_show_table_transform = disk_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30') else ' ')
#    op_var = 'disks_operations'
#    op_class = 'DisksOperations'
#    g.command('disk create', custom_path.format('create_managed_disk'), no_wait_param='no_wait', table_transformer=disk_show_table_transform)
#    g.command('disk list', custom_path.format('list_managed_disks'), table_transformer='[].' + disk_show_table_transform)
#    g.command('disk show', mgmt_path.format(op_var, op_class, 'get'), cf_disks, exception_handler=empty_on_404, table_transformer=disk_show_table_transform)
#    g.command('disk delete', mgmt_path.format(op_var, op_class, 'delete'), cf_disks, no_wait_param='raw', confirmation=True)
#    g.command('disk grant-access', custom_path.format('grant_disk_access'))
#    g.command('disk revoke-access', mgmt_path.format(op_var, op_class, 'revoke_access'), cf_disks)
#    _cli_generic_update_command('disk update', 'azure.mgmt.compute.operations.{}#{}.get'.format(op_var, op_class),
#                               'azure.mgmt.compute.operations.{}#{}.create_or_update'.format(op_var, op_class),
#                               custom_function_op=custom_path.format('update_managed_disk'),
#                               setter_arg_name='disk', factory=cf_disks, no_wait_param='raw')
#    _cli_generic_wait_command('disk wait', 'azure.mgmt.compute.operations.{}#{}.get'.format(op_var, op_class), cf_disks)

#    op_var = 'snapshots_operations'
#    op_class = 'SnapshotsOperations'
#    g.command('snapshot create', custom_path.format('create_snapshot'))
#    g.command('snapshot list', custom_path.format('list_snapshots'))
#    g.command('snapshot show', mgmt_path.format(op_var, op_class, 'get'), cf_snapshots, exception_handler=empty_on_404)
#    g.command('snapshot delete', mgmt_path.format(op_var, op_class, 'delete'), cf_snapshots)
#    g.command('snapshot grant-access', custom_path.format('grant_snapshot_access'))
#    g.command('snapshot revoke-access', mgmt_path.format(op_var, op_class, 'revoke_access'), cf_snapshots)
#    _cli_generic_update_command('snapshot update', 'azure.mgmt.compute.operations.{}#{}.get'.format(op_var, op_class),
#                               'azure.mgmt.compute.operations.{}#{}.create_or_update'.format(op_var, op_class),
#                               custom_function_op=custom_path.format('update_snapshot'),
#                               setter_arg_name='snapshot', factory=cf_snapshots)

#op_var = 'images_operations'
#op_class = 'ImagesOperations'
#g.command('image create', custom_path.format('create_image'))
#g.command('image list', custom_path.format('list_images'))
#g.command('image show', mgmt_path.format(op_var, op_class, 'get'), cf_images, exception_handler=empty_on_404)
#g.command('image delete', mgmt_path.format(op_var, op_class, 'delete'), cf_images)

#if supported_api_version(ResourceType.MGMT_COMPUTE, min_api='2017-03-30'):
#    g.command('vm list-skus', custom_path.format('list_skus'), table_transformer=transform_sku_for_table_output)
#    op_var = 'virtual_machine_run_commands_operations'
#    op_class = 'VirtualMachineRunCommandsOperations'
#    g.command('vm run-command show', mgmt_path.format(op_var, op_class, 'get'), cf_run_commands)
#    g.command('vm run-command list', mgmt_path.format(op_var, op_class, 'list'), cf_run_commands)
#    g.command('vm run-command invoke', custom_path.format('run_command_invoke'))

#    op_var = 'virtual_machine_scale_set_rolling_upgrades_operations'
#    op_class = 'VirtualMachineScaleSetRollingUpgradesOperations'
#    g.command('vmss rolling-upgrade cancel', mgmt_path.format(op_var, op_class, 'cancel'), cf_rolling_upgrade_commands)
#    g.command('vmss rolling-upgrade get-latest', mgmt_path.format(op_var, op_class, 'get_latest'), cf_rolling_upgrade_commands)
#    g.command('vmss rolling-upgrade start', mgmt_path.format(op_var, op_class, 'start_os_upgrade'), cf_rolling_upgrade_commands)

## MSI
#g.command('vm assign-identity', custom_path.format('assign_vm_identity'))
#g.command('vmss assign-identity', custom_path.format('assign_vmss_identity'))

def load_command_table(self, args):

    compute_vm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.{}',
        client_factory=cf_vm
    )

    with self.command_group('vm', compute_vm_sdk) as g:
        g.custom_command('create', 'create_vm', transform=transform_vm_create_output, no_wait_param='no_wait', table_transformer=deployment_validate_table_format, validator=process_vm_create_namespace)
        g.command('delete', 'delete', confirmation=True, no_wait_param='raw')
        #g.command('deallocate', 'deallocate', no_wait_param='raw')
        #g.command('generalize', 'generalize', no_wait_param='raw')
        g.custom_command('show', 'show_vm', table_transformer=transform_vm, exception_handler=empty_on_404)
        #g.command('list-vm-resize-options', 'list_available_sizes')
        #g.command('stop', 'power_off', no_wait_param='raw')
        #g.command('restart', 'restart', no_wait_param='raw')
        #g.command('start', 'start', no_wait_param='raw')
        #g.command('redeploy', 'redeploy', no_wait_param='raw')
        #g.custom_command('list-ip-addresses', 'list_ip_addresses', table_transformer=transform_ip_addresses)
        #g.custom_command('get-instance-view', 'get_instance_view', table_transformer='{Name:name, ResourceGroup:resourceGroup, Location:location, ProvisioningState:provisioningState, PowerState:instanceView.statuses[1].displayStatus}')
        #g.custom_command('list', 'list_vm', table_transformer=transform_vm_list)
        #g.custom_command('resize', 'resize_vm', no_wait_param='no_wait')
        #g.custom_command('capture', 'capture_vm')
        #g.custom_command('open-port', 'vm_open_port')
        #g.custom_command('format-secret', 'get_vm_format_secret', deprecate_info='az vm secret format')
        #g.generic_update_command('update', no_wait_param='raw')
        #g.generic_wait_command('wait', 'azure.cli.command_modules.vm.custom#get_instance_view')
        #g.command('perform-maintenance', 'perform_maintenance', min_api='2017-03-30')

    #with self.command_group('vm secret', compute_vm_sdk) as g:
    #    g.custom_command('format', 'get_vm_format_secret')
    #    g.custom_command('add', 'add_vm_secret')
    #    g.custom_command('list', 'list_vm_secrets')
    #    g.custom_command('remove', 'remove_vm_secret')
