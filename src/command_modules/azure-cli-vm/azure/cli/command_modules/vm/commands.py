# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.vm._client_factory import (cf_vm, cf_avail_set, cf_ni,
                                                          cf_vm_ext,
                                                          cf_vm_ext_image, cf_vm_image, cf_usage,
                                                          cf_vmss, cf_vmss_vm,
                                                          cf_vm_sizes, cf_disks, cf_snapshots,
                                                          cf_images, cf_run_commands,
                                                          cf_rolling_upgrade_commands,
                                                          cf_msi_user_identities_operations,
                                                          cf_msi_operations_operations)
from azure.cli.command_modules.vm._format import (
    transform_ip_addresses, transform_vm, transform_vm_create_output, transform_vm_usage_list, transform_vm_list,
    transform_sku_for_table_output, transform_disk_show_table_output, transform_extension_show_table_output,
    get_vmss_table_output_transformer)
from azure.cli.command_modules.vm._validators import (
    process_vm_create_namespace, process_vmss_create_namespace, process_image_create_namespace,
    process_disk_or_snapshot_create_namespace, process_disk_encryption_namespace, process_assign_identity_namespace,
    process_msi_namespace, process_remove_identity_namespace, process_vm_secret_format)

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format, handle_template_based_exception


# pylint: disable=line-too-long, too-many-statements
def load_command_table(self, _):

    custom_tmpl = 'azure.cli.command_modules.vm.custom#{}'

    compute_custom = CliCommandType(operations_tmpl=custom_tmpl)

    compute_disk_encryption_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.vm.disk_encryption#{}',
        operation_group='virtual_machines'
    )

    compute_availset_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.availability_sets_operations#AvailabilitySetsOperations.{}',
        client_factory=cf_avail_set,
        operation_group='availability_sets'
    )

    compute_disk_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.disks_operations#DisksOperations.{}',
        client_factory=cf_disks,
        operation_group='disks'
    )

    compute_identity_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.msi.operations.user_assigned_identities_operations#UserAssignedIdentitiesOperations.{}',
        client_factory=cf_msi_user_identities_operations
    )

    compute_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.images_operations#ImagesOperations.{}',
        client_factory=cf_images
    )

    compute_snapshot_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.snapshots_operations#SnapshotsOperations.{}',
        client_factory=cf_snapshots
    )

    compute_vm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machines_operations#VirtualMachinesOperations.{}',
        client_factory=cf_vm
    )

    compute_vm_extension_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_extensions_operations#VirtualMachineExtensionsOperations.{}',
        client_factory=cf_vm_ext
    )

    compute_vm_extension_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_extension_images_operations#VirtualMachineExtensionImagesOperations.{}',
        client_factory=cf_vm_ext_image
    )

    compute_vm_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_images_operations#VirtualMachineImagesOperations.{}',
        client_factory=cf_vm_image
    )

    compute_vm_usage_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.usage_operations#UsageOperations.{}',
        client_factory=cf_usage
    )

    compute_vm_run_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_run_commands_operations#VirtualMachineRunCommandsOperations.{}',
        client_factory=cf_run_commands,
        min_api='2017-03-30'
    )

    compute_vm_size_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_sizes_operations#VirtualMachineSizesOperations.{}',
        client_factory=cf_vm_sizes
    )

    compute_vmss_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_scale_sets_operations#VirtualMachineScaleSetsOperations.{}',
        client_factory=cf_vmss,
        operation_group='virtual_machine_scale_sets'
    )

    compute_vmss_rolling_upgrade_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_scale_set_rolling_upgrades_operations#VirtualMachineScaleSetRollingUpgradesOperations.{}',
        client_factory=cf_rolling_upgrade_commands,
        operation_group='virtual_machine_scale_sets'
    )

    compute_vmss_vm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations.virtual_machine_scale_set_vms_operations#VirtualMachineScaleSetVMsOperations.{}',
        client_factory=cf_vmss_vm,
        operation_group='virtual_machine_scale_sets'
    )

    network_nic_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.{}',
        client_factory=cf_ni
    )

    with self.command_group('disk', compute_disk_sdk, operation_group='disks', min_api='2017-03-30') as g:
        g.custom_command('create', 'create_managed_disk', supports_no_wait=True, table_transformer=transform_disk_show_table_output, validator=process_disk_or_snapshot_create_namespace)
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.custom_command('grant-access', 'grant_disk_access')
        g.custom_command('list', 'list_managed_disks', table_transformer='[].' + transform_disk_show_table_output)
        g.command('revoke-access', 'revoke_access')
        g.show_command('show', 'get', table_transformer=transform_disk_show_table_output)
        g.generic_update_command('update', custom_func_name='update_managed_disk', setter_arg_name='disk', supports_no_wait=True)
        g.wait_command('wait')

    # TODO move to its own command module https://github.com/Azure/azure-cli/issues/5105
    with self.command_group('identity', compute_identity_sdk, min_api='2017-12-01') as g:
        g.command('create', 'create_or_update', validator=process_msi_namespace)
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_user_assigned_identities')
        g.command('list-operations', 'list', operations_tmpl='azure.mgmt.msi.operations.operations#Operations.{}', client_factory=cf_msi_operations_operations)

    with self.command_group('image', compute_image_sdk, min_api='2016-04-30-preview') as g:
        g.custom_command('create', 'create_image', validator=process_image_create_namespace)
        g.custom_command('list', 'list_images')
        g.show_command('show', 'get')
        g.command('delete', 'delete')

    with self.command_group('snapshot', compute_snapshot_sdk, operation_group='snapshots', min_api='2016-04-30-preview') as g:
        g.custom_command('create', 'create_snapshot', validator=process_disk_or_snapshot_create_namespace)
        g.command('delete', 'delete')
        g.custom_command('grant-access', 'grant_snapshot_access')
        g.custom_command('list', 'list_snapshots')
        g.command('revoke-access', 'revoke_access')
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_snapshot', setter_arg_name='snapshot')

    with self.command_group('vm', compute_vm_sdk) as g:
        g.custom_command('identity assign', 'assign_vm_identity', validator=process_assign_identity_namespace)
        g.custom_command('identity remove', 'remove_vm_identity', validator=process_remove_identity_namespace, min_api='2017-12-01')
        g.custom_command('identity show', 'show_vm_identity')

        g.custom_command('capture', 'capture_vm')
        g.custom_command('create', 'create_vm', transform=transform_vm_create_output, supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vm_create_namespace, exception_handler=handle_template_based_exception)
        g.command('convert', 'convert_to_managed_disks', min_api='2016-04-30-preview')
        g.command('deallocate', 'deallocate', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.command('generalize', 'generalize', supports_no_wait=True)
        g.custom_command('get-instance-view', 'get_instance_view', table_transformer='{Name:name, ResourceGroup:resourceGroup, Location:location, ProvisioningState:provisioningState, PowerState:instanceView.statuses[1].displayStatus}')
        g.custom_command('list', 'list_vm', table_transformer=transform_vm_list)
        g.custom_command('list-ip-addresses', 'list_vm_ip_addresses', table_transformer=transform_ip_addresses)
        g.command('list-sizes', 'list', command_type=compute_vm_size_sdk)
        g.custom_command('list-skus', 'list_skus', table_transformer=transform_sku_for_table_output, min_api='2017-03-30')
        g.command('list-usage', 'list', command_type=compute_vm_usage_sdk, transform=transform_vm_usage_list, table_transformer='[].{Name:localName, CurrentValue:currentValue, Limit:limit}')
        g.command('list-vm-resize-options', 'list_available_sizes')
        g.custom_command('open-port', 'open_vm_port')
        g.command('perform-maintenance', 'perform_maintenance', min_api='2017-03-30')
        g.command('redeploy', 'redeploy', supports_no_wait=True)
        g.custom_command('resize', 'resize_vm', supports_no_wait=True)
        g.command('restart', 'restart', supports_no_wait=True)
        g.custom_show_command('show', 'show_vm', table_transformer=transform_vm)
        g.command('start', 'start', supports_no_wait=True)
        g.command('stop', 'power_off', supports_no_wait=True)
        g.generic_update_command('update', setter_name='update_vm', setter_type=compute_custom, supports_no_wait=True)
        g.wait_command('wait', getter_name='get_instance_view', getter_type=compute_custom)

    with self.command_group('vm availability-set', compute_availset_sdk) as g:
        g.custom_command('convert', 'convert_av_set_to_managed_disk', min_api='2016-04-30-preview')
        g.custom_command('create', 'create_av_set', table_transformer=deployment_validate_table_format, supports_no_wait=True, exception_handler=handle_template_based_exception)
        g.command('delete', 'delete')
        g.custom_command('list', 'list_av_sets')
        g.command('list-sizes', 'list_available_sizes')
        g.show_command('show', 'get')
        g.generic_update_command('update')

    with self.command_group('vm boot-diagnostics', compute_vm_sdk) as g:
        g.custom_command('disable', 'disable_boot_diagnostics')
        g.custom_command('enable', 'enable_boot_diagnostics')
        g.custom_command('get-boot-log', 'get_boot_log')

    with self.command_group('vm diagnostics', compute_vm_sdk) as g:
        g.custom_command('set', 'set_diagnostics_extension')
        g.custom_command('get-default-config', 'show_default_diagnostics_configuration')

    with self.command_group('vm disk', compute_vm_sdk, min_api='2017-03-30') as g:
        g.custom_command('attach', 'attach_managed_data_disk')
        g.custom_command('detach', 'detach_data_disk')

    with self.command_group('vm encryption', custom_command_type=compute_disk_encryption_custom) as g:
        g.custom_command('enable', 'encrypt_vm', validator=process_disk_encryption_namespace)
        g.custom_command('disable', 'decrypt_vm')
        g.custom_show_command('show', 'show_vm_encryption_status')

    with self.command_group('vm extension', compute_vm_extension_sdk) as g:
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get', table_transformer=transform_extension_show_table_output)
        g.custom_command('set', 'set_extension', supports_no_wait=True)
        g.custom_command('list', 'list_extensions', table_transformer='[].' + transform_extension_show_table_output)
        g.wait_command('wait')

    with self.command_group('vm extension image', compute_vm_extension_image_sdk) as g:
        g.show_command('show', 'get')
        g.command('list-names', 'list_types')
        g.command('list-versions', 'list_versions')
        g.custom_command('list', 'list_vm_extension_images')

    with self.command_group('vm image', compute_vm_image_sdk) as g:
        g.command('list-offers', 'list_offers')
        g.command('list-publishers', 'list_publishers')
        g.command('list-skus', 'list_skus')
        g.custom_command('list', 'list_vm_images')
        g.custom_command('accept-terms', 'accept_market_ordering_terms')
        g.custom_show_command('show', 'show_vm_image')

    with self.command_group('vm nic', compute_vm_sdk) as g:
        g.custom_command('add', 'add_vm_nic')
        g.custom_command('remove', 'remove_vm_nic')
        g.custom_command('set', 'set_vm_nic')
        g.custom_show_command('show', 'show_vm_nic')
        g.custom_command('list', 'list_vm_nics')

    with self.command_group('vm run-command', compute_vm_run_sdk, operation_group='virtual_machine_run_commands') as g:
        g.custom_command('invoke', 'run_command_invoke')
        g.command('list', 'list')
        g.show_command('show', 'get')

    with self.command_group('vm secret', compute_vm_sdk) as g:
        g.custom_command('format', 'get_vm_format_secret', validator=process_vm_secret_format)
        g.custom_command('add', 'add_vm_secret')
        g.custom_command('list', 'list_vm_secrets')
        g.custom_command('remove', 'remove_vm_secret')

    with self.command_group('vm unmanaged-disk', compute_vm_sdk) as g:
        g.custom_command('attach', 'attach_unmanaged_data_disk')
        g.custom_command('detach', 'detach_data_disk')
        g.custom_command('list', 'list_unmanaged_disks')

    with self.command_group('vm user', compute_vm_sdk, supports_no_wait=True) as g:
        g.custom_command('update', 'set_user')
        g.custom_command('delete', 'delete_user')
        g.custom_command('reset-ssh', 'reset_linux_ssh')

    with self.command_group('vmss', compute_vmss_sdk, operation_group='virtual_machine_scale_sets') as g:
        g.custom_command('identity assign', 'assign_vmss_identity', validator=process_assign_identity_namespace)
        g.custom_command('identity remove', 'remove_vmss_identity', validator=process_remove_identity_namespace, min_api='2017-12-01')
        g.custom_command('identity show', 'show_vmss_identity')
        g.custom_command('create', 'create_vmss', transform=DeploymentOutputLongRunningOperation(self.cli_ctx, 'Starting vmss create'), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vmss_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('deallocate', 'deallocate_vmss', supports_no_wait=True)
        g.command('delete', 'delete', supports_no_wait=True)
        g.custom_command('delete-instances', 'delete_vmss_instances', supports_no_wait=True)
        g.custom_command('get-instance-view', 'get_vmss_instance_view', table_transformer='{ProvisioningState:statuses[0].displayStatus, PowerState:statuses[1].displayStatus}')
        g.custom_command('list', 'list_vmss', table_transformer=get_vmss_table_output_transformer(self))
        g.command('list-instances', 'list', command_type=compute_vmss_vm_sdk)
        g.custom_command('list-instance-connection-info', 'list_vmss_instance_connection_info')
        g.custom_command('list-instance-public-ips', 'list_vmss_instance_public_ips')
        g.command('list-skus', 'list_skus')
        g.custom_command('reimage', 'reimage_vmss', supports_no_wait=True, min_api='2017-03-30')
        g.command('perform-maintenance', 'perform_maintenance', min_api='2017-12-01')
        g.custom_command('restart', 'restart_vmss', supports_no_wait=True)
        g.custom_command('scale', 'scale_vmss', supports_no_wait=True)
        g.custom_show_command('show', 'show_vmss', table_transformer=get_vmss_table_output_transformer(self, False))
        g.custom_command('start', 'start_vmss', supports_no_wait=True)
        g.custom_command('stop', 'stop_vmss', supports_no_wait=True)
        g.generic_update_command('update', getter_name='get_vmss', setter_name='update_vmss', supports_no_wait=True, command_type=compute_custom)
        g.custom_command('update-instances', 'update_vmss_instances', supports_no_wait=True)
        g.wait_command('wait', getter_name='get_vmss', getter_type=compute_custom)

    with self.command_group('vmss diagnostics', compute_vmss_sdk) as g:
        g.custom_command('set', 'set_vmss_diagnostics_extension')
        g.custom_command('get-default-config', 'show_default_diagnostics_configuration')

    with self.command_group('vmss disk', compute_vmss_sdk, min_api='2017-03-30') as g:
        g.custom_command('attach', 'attach_managed_data_disk_to_vmss')
        g.custom_command('detach', 'detach_disk_from_vmss')

    with self.command_group('vmss encryption', custom_command_type=compute_disk_encryption_custom, min_api='2017-03-30') as g:
        g.custom_command('enable', 'encrypt_vmss', validator=process_disk_encryption_namespace)
        g.custom_command('disable', 'decrypt_vmss')
        g.custom_show_command('show', 'show_vmss_encryption_status')

    with self.command_group('vmss extension', compute_vmss_sdk) as g:
        g.custom_command('delete', 'delete_vmss_extension', supports_no_wait=True)
        g.custom_show_command('show', 'get_vmss_extension')
        g.custom_command('set', 'set_vmss_extension', supports_no_wait=True)
        g.custom_command('list', 'list_vmss_extensions')

    with self.command_group('vmss extension image', compute_vm_extension_image_sdk) as g:
        g.show_command('show', 'get')
        g.command('list-names', 'list_types')
        g.command('list-versions', 'list_versions')
        g.custom_command('list', 'list_vm_extension_images')

    with self.command_group('vmss nic', network_nic_sdk) as g:
        g.command('list', 'list_virtual_machine_scale_set_network_interfaces')
        g.command('list-vm-nics', 'list_virtual_machine_scale_set_vm_network_interfaces')
        g.show_command('show', 'get_virtual_machine_scale_set_network_interface')

    with self.command_group('vmss rolling-upgrade', compute_vmss_rolling_upgrade_sdk, min_api='2017-03-30') as g:
        g.command('cancel', 'cancel')
        g.command('get-latest', 'get_latest')
        g.command('start', 'start_os_upgrade')
