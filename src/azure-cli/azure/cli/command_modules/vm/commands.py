# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.vm._client_factory import (cf_vm, cf_avail_set, cf_ni,
                                                          cf_vm_ext, cf_vm_ext_image,
                                                          cf_vm_image, cf_vm_image_term, cf_usage,
                                                          cf_vmss, cf_vmss_vm,
                                                          cf_vm_sizes, cf_disks, cf_snapshots,
                                                          cf_disk_accesses, cf_images, cf_run_commands,
                                                          cf_rolling_upgrade_commands, cf_galleries,
                                                          cf_gallery_images, cf_gallery_image_versions,
                                                          cf_proximity_placement_groups,
                                                          cf_dedicated_hosts, cf_dedicated_host_groups,
                                                          cf_log_analytics_data_plane,
                                                          cf_disk_encryption_set, cf_shared_galleries,
                                                          cf_gallery_sharing_profile, cf_shared_gallery_image,
                                                          cf_shared_gallery_image_version)
from azure.cli.command_modules.vm._format import (
    transform_ip_addresses, transform_vm, transform_vm_create_output, transform_vm_usage_list, transform_vm_list,
    transform_sku_for_table_output, transform_disk_show_table_output, transform_extension_show_table_output,
    get_vmss_table_output_transformer, transform_vm_encryption_show_table_output, transform_log_analytics_query_output)
from azure.cli.command_modules.vm._validators import (
    process_vm_create_namespace, process_vmss_create_namespace, process_image_create_namespace,
    process_disk_or_snapshot_create_namespace, process_disk_encryption_namespace, process_assign_identity_namespace,
    process_remove_identity_namespace, process_vm_secret_format, process_vm_vmss_stop, validate_vmss_update_namespace)

from azure.cli.command_modules.vm._image_builder import (
    process_image_template_create_namespace, process_img_tmpl_output_add_namespace,
    process_img_tmpl_customizer_add_namespace, image_builder_client_factory, cf_img_bldr_image_templates)

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, CliCommandType
from azure.cli.core.commands.arm import deployment_validate_table_format, handle_template_based_exception

from azure.cli.command_modules.monitor._exception_handler import exception_handler as monitor_exception_handler
from azure.cli.command_modules.monitor._client_factory import cf_metric_def
from azure.cli.core.profiles import ResourceType


# pylint: disable=line-too-long, too-many-statements, too-many-locals
def load_command_table(self, _):

    custom_tmpl = 'azure.cli.command_modules.vm.custom#{}'

    compute_custom = CliCommandType(operations_tmpl=custom_tmpl)

    compute_disk_encryption_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.vm.disk_encryption#{}',
        operation_group='virtual_machines'
    )

    image_builder_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.vm._image_builder#{}',
        client_factory=image_builder_client_factory
    )

    compute_availset_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#AvailabilitySetsOperations.{}',
        client_factory=cf_avail_set,
        operation_group='availability_sets'
    )

    compute_disk_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#DisksOperations.{}',
        client_factory=cf_disks,
        operation_group='disks'
    )

    compute_disk_access_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#DiskAccessesOperations.{}',
        client_factory=cf_disk_accesses,
        operation_group='disk_accesses'
    )

    compute_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#ImagesOperations.{}',
        client_factory=cf_images
    )

    compute_snapshot_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#SnapshotsOperations.{}',
        client_factory=cf_snapshots
    )

    compute_vm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachinesOperations.{}',
        client_factory=cf_vm
    )

    compute_vm_extension_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineExtensionsOperations.{}',
        client_factory=cf_vm_ext
    )

    compute_vm_extension_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineExtensionImagesOperations.{}',
        client_factory=cf_vm_ext_image
    )

    compute_vm_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineImagesOperations.{}',
        client_factory=cf_vm_image
    )

    compute_vm_image_term_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.marketplaceordering.operations#MarketplaceAgreementsOperations.{}',
        client_factory=cf_vm_image_term
    )

    compute_vm_usage_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#UsageOperations.{}',
        client_factory=cf_usage
    )

    compute_vm_run_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineRunCommandsOperations.{}',
        client_factory=cf_run_commands
    )

    compute_vm_size_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineSizesOperations.{}',
        client_factory=cf_vm_sizes
    )

    compute_vmss_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineScaleSetsOperations.{}',
        client_factory=cf_vmss,
        operation_group='virtual_machine_scale_sets'
    )

    compute_vmss_rolling_upgrade_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineScaleSetRollingUpgradesOperations.{}',
        client_factory=cf_rolling_upgrade_commands,
        operation_group='virtual_machine_scale_sets'
    )

    compute_vmss_vm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineScaleSetVMsOperations.{}',
        client_factory=cf_vmss_vm,
        operation_group='virtual_machine_scale_sets'
    )

    network_nic_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkInterfacesOperations.{}',
        client_factory=cf_ni
    )

    compute_galleries_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#GalleriesOperations.{}',
        client_factory=cf_galleries,
    )

    compute_gallery_images_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#GalleryImagesOperations.{}',
        client_factory=cf_gallery_images,
    )

    compute_gallery_image_versions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#GalleryImageVersionsOperations.{}',
        client_factory=cf_gallery_image_versions,
    )

    compute_proximity_placement_groups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#ProximityPlacementGroupsOperations.{}',
    )

    compute_dedicated_host_sdk = CliCommandType(
        operations_tmpl="azure.mgmt.compute.operations#DedicatedHostsOperations.{}",
        client_factory=cf_dedicated_hosts,
    )

    compute_dedicated_host_groups_sdk = CliCommandType(
        operations_tmpl="azure.mgmt.compute.operations#DedicatedHostGroupsOperations.{}",
        client_factory=cf_dedicated_host_groups,
    )

    image_builder_image_templates_sdk = CliCommandType(
        operations_tmpl="azure.mgmt.imagebuilder.operations#VirtualMachineImageTemplatesOperations.{}",
        client_factory=cf_img_bldr_image_templates,
    )

    compute_disk_encryption_set_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#DiskEncryptionSetsOperations.{}',
        client_factory=cf_disk_encryption_set
    )

    monitor_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.monitor.custom#{}',
        exception_handler=monitor_exception_handler
    )

    metric_definitions_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.monitor.operations#MetricDefinitionsOperations.{}',
        resource_type=ResourceType.MGMT_MONITOR,
        client_factory=cf_metric_def,
        operation_group='metric_definitions',
        exception_handler=monitor_exception_handler
    )

    with self.command_group('disk', compute_disk_sdk, operation_group='disks', min_api='2017-03-30') as g:
        g.custom_command('create', 'create_managed_disk', supports_no_wait=True, table_transformer=transform_disk_show_table_output, validator=process_disk_or_snapshot_create_namespace)
        g.command('delete', 'begin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('grant-access', 'grant_disk_access')
        g.custom_command('list', 'list_managed_disks', table_transformer='[].' + transform_disk_show_table_output)
        g.command('revoke-access', 'begin_revoke_access')
        g.show_command('show', 'get', table_transformer=transform_disk_show_table_output)
        g.generic_update_command('update', custom_func_name='update_managed_disk', setter_name='begin_create_or_update', setter_arg_name='disk', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('disk-encryption-set', compute_disk_encryption_set_sdk, operation_group='disk_encryption_sets', client_factory=cf_disk_encryption_set, min_api='2019-07-01') as g:
        g.custom_command('create', 'create_disk_encryption_set', supports_no_wait=True)
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', custom_func_name='update_disk_encryption_set', setter_arg_name='disk_encryption_set', setter_name='begin_create_or_update')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_disk_encryption_sets')
        g.command('list-associated-resources', 'list_associated_resources', min_api='2020-06-30')

    with self.command_group('disk-access', compute_disk_access_sdk, operation_group='disk_accesses', client_factory=cf_disk_accesses, min_api='2020-05-01') as g:
        g.custom_command('create', 'create_disk_access', supports_no_wait=True)
        g.generic_update_command('update', setter_name='set_disk_access', setter_type=compute_custom, supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_disk_accesses')
        g.wait_command('wait')
        g.command('delete', 'begin_delete')

    with self.command_group('image', compute_image_sdk, min_api='2016-04-30-preview') as g:
        g.custom_command('create', 'create_image', validator=process_image_create_namespace)
        g.custom_command('list', 'list_images')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_image')

    with self.command_group('image builder', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('create', 'create_image_template', supports_no_wait=True, supports_local_cache=True, validator=process_image_template_create_namespace)
        g.custom_command('list', 'list_image_templates')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.generic_update_command('update', 'create_or_update', supports_local_cache=True)  # todo Update fails for now as service does not support updates
        g.wait_command('wait')
        g.command('run', 'run', supports_no_wait=True)
        g.custom_command('show-runs', 'show_build_output')
        g.command('cancel', 'cancel')

    with self.command_group('image builder customizer', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_customizer', supports_local_cache=True, validator=process_img_tmpl_customizer_add_namespace)
        g.custom_command('remove', 'remove_template_customizer', supports_local_cache=True)
        g.custom_command('clear', 'clear_template_customizer', supports_local_cache=True)

    with self.command_group('image builder output', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_output', supports_local_cache=True, validator=process_img_tmpl_output_add_namespace)
        g.custom_command('remove', 'remove_template_output', supports_local_cache=True)
        g.custom_command('clear', 'clear_template_output', supports_local_cache=True)

    with self.command_group('snapshot', compute_snapshot_sdk, operation_group='snapshots', min_api='2016-04-30-preview') as g:
        g.custom_command('create', 'create_snapshot', validator=process_disk_or_snapshot_create_namespace, supports_no_wait=True)
        g.command('delete', 'begin_delete')
        g.custom_command('grant-access', 'grant_snapshot_access')
        g.custom_command('list', 'list_snapshots')
        g.command('revoke-access', 'begin_revoke_access')
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_snapshot', setter_name='begin_create_or_update', setter_arg_name='snapshot', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('vm', compute_vm_sdk) as g:
        g.custom_command('identity assign', 'assign_vm_identity', validator=process_assign_identity_namespace)
        g.custom_command('identity remove', 'remove_vm_identity', validator=process_remove_identity_namespace, min_api='2017-12-01')
        g.custom_show_command('identity show', 'show_vm_identity')

        g.custom_command('capture', 'capture_vm')
        g.custom_command('create', 'create_vm', transform=transform_vm_create_output, supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vm_create_namespace, exception_handler=handle_template_based_exception)
        g.command('convert', 'begin_convert_to_managed_disks', min_api='2016-04-30-preview')
        g.command('deallocate', 'begin_deallocate', supports_no_wait=True)
        g.command('delete', 'begin_delete', confirmation=True, supports_no_wait=True)
        g.command('generalize', 'generalize', supports_no_wait=True)
        g.custom_command('get-instance-view', 'get_instance_view', table_transformer='{Name:name, ResourceGroup:resourceGroup, Location:location, ProvisioningState:provisioningState, PowerState:instanceView.statuses[1].displayStatus}')
        g.custom_command('list', 'list_vm', table_transformer=transform_vm_list)
        g.custom_command('list-ip-addresses', 'list_vm_ip_addresses', table_transformer=transform_ip_addresses)
        g.command('list-sizes', 'list', command_type=compute_vm_size_sdk)
        g.custom_command('list-skus', 'list_skus', table_transformer=transform_sku_for_table_output, min_api='2017-03-30')
        g.command('list-usage', 'list', command_type=compute_vm_usage_sdk, transform=transform_vm_usage_list, table_transformer='[].{Name:localName, CurrentValue:currentValue, Limit:limit}')
        g.command('list-vm-resize-options', 'list_available_sizes')
        g.custom_command('open-port', 'open_vm_port')
        g.command('perform-maintenance', 'begin_perform_maintenance', min_api='2017-03-30')
        g.command('redeploy', 'begin_redeploy', supports_no_wait=True)
        g.custom_command('resize', 'resize_vm', supports_no_wait=True)
        g.custom_command('restart', 'restart_vm', supports_no_wait=True)
        g.custom_show_command('show', 'show_vm', table_transformer=transform_vm)
        g.command('simulate-eviction', 'simulate_eviction', min_api='2019-12-01')
        g.command('start', 'begin_start', supports_no_wait=True)
        g.command('stop', 'begin_power_off', supports_no_wait=True, validator=process_vm_vmss_stop)
        g.command('reapply', 'begin_reapply', supports_no_wait=True, min_api='2019-07-01')
        g.generic_update_command('update', getter_name='get_vm_to_update', setter_name='update_vm', setter_type=compute_custom, command_type=compute_custom, supports_no_wait=True)
        g.wait_command('wait', getter_name='get_instance_view', getter_type=compute_custom)
        g.custom_command('auto-shutdown', 'auto_shutdown_vm')
        g.command('assess-patches', 'begin_assess_patches', min_api='2020-06-01')

    with self.command_group('vm', compute_vm_sdk, client_factory=cf_vm) as g:
        g.custom_command('install-patches', 'install_vm_patches', supports_no_wait=True, min_api='2020-12-01')

    with self.command_group('vm availability-set', compute_availset_sdk) as g:
        g.custom_command('convert', 'convert_av_set_to_managed_disk', min_api='2016-04-30-preview')
        g.custom_command('create', 'create_av_set', table_transformer=deployment_validate_table_format, supports_no_wait=True, exception_handler=handle_template_based_exception)
        g.command('delete', 'delete')
        g.custom_command('list', 'list_av_sets')
        g.command('list-sizes', 'list_available_sizes')
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_av_set')

    with self.command_group('vm boot-diagnostics', compute_vm_sdk) as g:
        g.custom_command('disable', 'disable_boot_diagnostics')
        g.custom_command('enable', 'enable_boot_diagnostics')
        g.custom_command('get-boot-log', 'get_boot_log')
        g.custom_command('get-boot-log-uris', 'get_boot_log_uris', min_api='2020-06-01')

    with self.command_group('vm diagnostics', compute_vm_sdk) as g:
        g.custom_command('set', 'set_diagnostics_extension')
        g.custom_command('get-default-config', 'show_default_diagnostics_configuration')

    with self.command_group('vm disk', compute_vm_sdk, min_api='2017-03-30') as g:
        g.custom_command('attach', 'attach_managed_data_disk')
        g.custom_command('detach', 'detach_data_disk')

    with self.command_group('vm encryption', custom_command_type=compute_disk_encryption_custom) as g:
        g.custom_command('enable', 'encrypt_vm', validator=process_disk_encryption_namespace)
        g.custom_command('disable', 'decrypt_vm')
        g.custom_show_command('show', 'show_vm_encryption_status', table_transformer=transform_vm_encryption_show_table_output)

    with self.command_group('vm extension', compute_vm_extension_sdk) as g:
        g.command('delete', 'begin_delete', supports_no_wait=True)
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
        g.custom_command('accept-terms', 'accept_market_ordering_terms',
                         deprecate_info=g.deprecate(redirect='az vm image terms accept', expiration='3.0.0'))
        g.custom_show_command('show', 'show_vm_image')

    with self.command_group('vm image terms', compute_vm_image_term_sdk, validator=None) as g:
        g.custom_command('accept', 'accept_terms')
        g.custom_command('cancel', 'cancel_terms')
        g.custom_show_command('show', 'get_terms')

    with self.command_group('vm nic', compute_vm_sdk) as g:
        g.custom_command('add', 'add_vm_nic')
        g.custom_command('remove', 'remove_vm_nic')
        g.custom_command('set', 'set_vm_nic')
        g.custom_show_command('show', 'show_vm_nic')
        g.custom_command('list', 'list_vm_nics')

    with self.command_group('vm run-command', compute_vm_run_sdk, operation_group='virtual_machine_run_commands', min_api='2017-03-30') as g:
        g.custom_command('invoke', 'vm_run_command_invoke')
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

    with self.command_group('vm host', compute_dedicated_host_sdk, client_factory=cf_dedicated_hosts,
                            min_api='2019-03-01') as g:
        g.show_command('show', 'get')
        g.custom_command('get-instance-view', 'get_dedicated_host_instance_view')
        g.custom_command('create', 'create_dedicated_host')
        g.command('list', 'list_by_host_group')
        g.generic_update_command('update', setter_name='begin_create_or_update')
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('vm host group', compute_dedicated_host_groups_sdk, client_factory=cf_dedicated_host_groups,
                            min_api='2019-03-01') as g:
        g.show_command('show', 'get')
        g.custom_command('get-instance-view', 'get_dedicated_host_group_instance_view', min_api='2020-06-01')
        g.custom_command('create', 'create_dedicated_host_group')
        g.custom_command('list', 'list_dedicated_host_groups')
        g.generic_update_command('update')
        g.command('delete', 'delete', confirmation=True)

    with self.command_group('vmss', compute_vmss_sdk, operation_group='virtual_machine_scale_sets') as g:
        g.custom_command('identity assign', 'assign_vmss_identity', validator=process_assign_identity_namespace)
        g.custom_command('identity remove', 'remove_vmss_identity', validator=process_remove_identity_namespace, min_api='2017-12-01', is_preview=True)
        g.custom_show_command('identity show', 'show_vmss_identity')
        g.custom_command('create', 'create_vmss', transform=DeploymentOutputLongRunningOperation(self.cli_ctx, 'Starting vmss create'), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vmss_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('deallocate', 'deallocate_vmss', supports_no_wait=True)
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.custom_command('delete-instances', 'delete_vmss_instances', supports_no_wait=True)
        g.custom_command('get-instance-view', 'get_vmss_instance_view', table_transformer='{ProvisioningState:statuses[0].displayStatus, PowerState:statuses[1].displayStatus}')
        g.custom_command('list', 'list_vmss', table_transformer=get_vmss_table_output_transformer(self))
        g.command('list-instances', 'list', command_type=compute_vmss_vm_sdk)
        g.custom_command('list-instance-connection-info', 'list_vmss_instance_connection_info')
        g.custom_command('list-instance-public-ips', 'list_vmss_instance_public_ips')
        g.command('list-skus', 'list_skus')
        g.custom_command('reimage', 'reimage_vmss', supports_no_wait=True, min_api='2017-03-30')
        g.command('perform-maintenance', 'begin_perform_maintenance', min_api='2017-12-01')
        g.custom_command('restart', 'restart_vmss', supports_no_wait=True)
        g.custom_command('scale', 'scale_vmss', supports_no_wait=True)
        g.custom_show_command('show', 'get_vmss', table_transformer=get_vmss_table_output_transformer(self, False))
        g.command('simulate-eviction', 'simulate_eviction', command_type=compute_vmss_vm_sdk, min_api='2019-12-01')
        g.custom_command('start', 'start_vmss', supports_no_wait=True)
        g.custom_command('stop', 'stop_vmss', supports_no_wait=True, validator=process_vm_vmss_stop)
        g.generic_update_command('update', getter_name='get_vmss_modified', setter_name='update_vmss', supports_no_wait=True, command_type=compute_custom, validator=validate_vmss_update_namespace)
        g.custom_command('update-instances', 'update_vmss_instances', supports_no_wait=True)
        g.wait_command('wait', getter_name='get_vmss', getter_type=compute_custom)
        g.command('get-os-upgrade-history', 'get_os_upgrade_history', min_api='2018-10-01')
        g.custom_command('set-orchestration-service-state', 'set_orchestration_service_state', supports_no_wait=True)

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
        g.custom_command('upgrade', 'upgrade_vmss_extension', min_api='2020-06-01', supports_no_wait=True)

    with self.command_group('vmss extension image', compute_vm_extension_image_sdk) as g:
        g.show_command('show', 'get')
        g.command('list-names', 'list_types')
        g.command('list-versions', 'list_versions')
        g.custom_command('list', 'list_vm_extension_images')

    with self.command_group('vmss nic', network_nic_sdk) as g:
        g.command('list', 'list_virtual_machine_scale_set_network_interfaces')
        g.command('list-vm-nics', 'list_virtual_machine_scale_set_vm_network_interfaces')
        g.show_command('show', 'get_virtual_machine_scale_set_network_interface')

    with self.command_group('vmss run-command', compute_vm_run_sdk, min_api='2018-04-01') as g:
        g.custom_command('invoke', 'vmss_run_command_invoke')
        g.command('list', 'list')
        g.show_command('show', 'get')

    with self.command_group('vmss rolling-upgrade', compute_vmss_rolling_upgrade_sdk, min_api='2017-03-30') as g:
        g.command('cancel', 'begin_cancel')
        g.command('get-latest', 'get_latest')
        g.command('start', 'begin_start_os_upgrade')

    with self.command_group('sig', compute_galleries_sdk, operation_group='galleries', min_api='2018-06-01') as g:
        g.custom_command('create', 'create_image_gallery')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_image_galleries')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_type=compute_custom, setter_name='update_image_galleries', setter_arg_name='gallery')

    with self.command_group('sig image-definition', compute_gallery_images_sdk, operation_group='gallery_images', min_api='2018-06-01') as g:
        g.custom_command('create', 'create_gallery_image')
        g.command('list', 'list_by_gallery')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='gallery_image')

    with self.command_group('sig image-version', compute_gallery_image_versions_sdk, operation_group='gallery_image_versions', min_api='2018-06-01') as g:
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get', table_transformer='{Name:name, ResourceGroup:resourceGroup, ProvisioningState:provisioningState, TargetRegions: publishingProfile.targetRegions && join(`, `, publishingProfile.targetRegions[*].name), ReplicationState:replicationStatus.aggregatedState}')
        g.command('list', 'list_by_gallery_image')
        g.custom_command('create', 'create_image_version', supports_no_wait=True)
        g.generic_update_command('update', getter_name='get_image_version_to_update', setter_arg_name='gallery_image_version', setter_name='update_image_version', setter_type=compute_custom, command_type=compute_custom, supports_no_wait=True)
        g.wait_command('wait')

    vm_shared_gallery = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations._shared_galleries_operations#SharedGalleriesOperations.{}',
        client_factory=cf_shared_galleries,
        operation_group='shared_galleries'
    )
    with self.command_group('sig', vm_shared_gallery) as g:
        g.custom_command('list-shared', 'sig_shared_gallery_list', client_factory=cf_shared_galleries,
                         is_experimental=True, operation_group='shared_galleries', min_api='2020-09-30')
        g.command('show-shared', 'get', is_experimental=True, operation_group='shared_galleries', min_api='2020-09-30')

    vm_gallery_sharing_profile = CliCommandType(
        operations_tmpl=(
            'azure.mgmt.compute.operations._gallery_sharing_profile_operations#GallerySharingProfileOperations.{}'
        ),
        client_factory=cf_gallery_sharing_profile,
        operation_group='shared_galleries'
    )
    with self.command_group('sig share', vm_gallery_sharing_profile,
                            client_factory=cf_gallery_sharing_profile,
                            operation_group='shared_galleries',
                            is_experimental=True, min_api='2020-09-30') as g:
        g.custom_command('add', 'sig_share_update', supports_no_wait=True)
        g.custom_command('remove', 'sig_share_update', supports_no_wait=True)
        g.custom_command('reset', 'sig_share_reset', supports_no_wait=True)
        g.wait_command('wait', getter_name='get_gallery_instance', getter_type=compute_custom)

    vm_shared_gallery_image = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations._shared_gallery_images_operations#SharedGalleryImagesOperations.'
        '{}',
        client_factory=cf_shared_gallery_image,
        operation_group='shared_galleries')
    with self.command_group('sig image-definition', vm_shared_gallery_image, min_api='2020-09-30', operation_group='shared_galleries',
                            client_factory=cf_shared_gallery_image) as g:
        g.custom_command('list-shared', 'sig_shared_image_definition_list', is_experimental=True)
        g.command('show-shared', 'get', is_experimental=True)

    vm_shared_gallery_image_version = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations._shared_gallery_image_versions_operations#SharedGalleryImageVers'
        'ionsOperations.{}',
        client_factory=cf_shared_gallery_image_version,
        operation_group='shared_galleries')
    with self.command_group('sig image-version', vm_shared_gallery_image_version, min_api='2020-09-30',
                            operation_group='shared_galleries',
                            client_factory=cf_shared_gallery_image_version) as g:
        g.custom_command('list-shared', 'sig_shared_image_version_list', is_experimental=True)
        g.command('show-shared', 'get', is_experimental=True)

    with self.command_group('ppg', compute_proximity_placement_groups_sdk, min_api='2018-04-01', client_factory=cf_proximity_placement_groups) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_proximity_placement_group')
        g.custom_command('list', 'list_proximity_placement_groups')
        g.generic_update_command('update')
        g.command('delete', 'delete')

    with self.command_group('vm monitor log', client_factory=cf_log_analytics_data_plane) as g:
        g.custom_command('show', 'execute_query_for_vm', transform=transform_log_analytics_query_output)  # pylint: disable=show-command

    with self.command_group('vm monitor metrics', custom_command_type=monitor_custom, command_type=metric_definitions_sdk, resource_type=ResourceType.MGMT_MONITOR, operation_group='metric_definitions', min_api='2018-01-01', is_preview=True) as g:
        from azure.cli.command_modules.monitor.transformers import metrics_table, metrics_definitions_table
        from azure.cli.core.profiles._shared import APIVersionException
        try:
            g.custom_command('tail', 'list_metrics', command_type=monitor_custom, table_transformer=metrics_table)
            g.command('list-definitions', 'list', table_transformer=metrics_definitions_table)
        except APIVersionException:
            pass
