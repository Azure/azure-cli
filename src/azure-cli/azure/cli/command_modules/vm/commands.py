# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.vm._client_factory import (cf_vm,
                                                          cf_vm_ext, cf_vm_ext_image,
                                                          cf_vm_image, cf_vm_image_term, cf_usage,
                                                          cf_vmss, cf_images,
                                                          cf_galleries, cf_gallery_images, cf_gallery_image_versions,
                                                          cf_proximity_placement_groups,
                                                          cf_dedicated_hosts, cf_dedicated_host_groups,
                                                          cf_log_analytics_data_plane,
                                                          cf_capacity_reservation_groups, cf_capacity_reservations,
                                                          cf_community_gallery)
from azure.cli.command_modules.vm._format import (
    transform_ip_addresses, transform_vm, transform_vm_create_output, transform_vm_usage_list, transform_vm_list,
    transform_disk_create_table_output, transform_sku_for_table_output, transform_disk_show_table_output,
    transform_extension_show_table_output, get_vmss_table_output_transformer,
    transform_vm_encryption_show_table_output, transform_log_analytics_query_output,
    transform_vmss_list_with_zones_table_output)
from azure.cli.command_modules.vm._validators import (
    process_vm_create_namespace, process_vmss_create_namespace, process_image_create_namespace,
    process_disk_create_namespace, process_snapshot_create_namespace,
    process_disk_encryption_namespace, process_assign_identity_namespace,
    process_remove_identity_namespace, process_vm_secret_format, process_vm_vmss_stop, validate_vmss_update_namespace,
    process_vm_update_namespace, process_set_applications_namespace, process_vm_disk_attach_namespace,
    process_image_version_create_namespace, process_image_version_update_namespace,
    process_image_version_undelete_namespace, process_vm_disk_detach_namespace)

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

    compute_availset_profile = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#AvailabilitySetsOperations.{}',
        operation_group='availability_sets'
    )

    compute_image_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#ImagesOperations.{}',
        client_factory=cf_images
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

    compute_vm_run_profile = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineRunCommandsOperations.{}'
    )

    compute_vmss_run_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineScaleSetVmRunCommandsOperations.{}'
    )

    compute_vmss_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#VirtualMachineScaleSetsOperations.{}',
        client_factory=cf_vmss,
        operation_group='virtual_machine_scale_sets'
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

    compute_gallery_application_profile = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#GalleryApplicationsOperations.{}',
    )

    compute_gallery_application_version_profile = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#GalleryApplicationVersionsOperations.{}',
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

    compute_disk_encryption_set_profile = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#DiskEncryptionSetsOperations.{}'
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

    capacity_reservation_groups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#CapacityReservationGroupsOperations.{}',
        client_factory=cf_capacity_reservation_groups
    )

    capacity_reservations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#CapacityReservationsOperations.{}',
        client_factory=cf_capacity_reservations
    )

    restore_point = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#RestorePointsOperations.{}',
    )

    restore_point_collection = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#RestorePointCollectionsOperations.{}'
    )

    community_gallery_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.compute.operations#CommunityGalleriesOperations.{}',
        client_factory=cf_community_gallery)

    with self.command_group("ppg"):
        from .operations.ppg import PPGShow
        self.command_table["ppg show"] = PPGShow(loader=self)

    with self.command_group('disk', operation_group='disks') as g:
        g.custom_command('create', 'create_managed_disk', supports_no_wait=True, table_transformer=transform_disk_create_table_output, validator=process_disk_create_namespace)
        from .operations.disk import DiskUpdate, DiskGrantAccess
        self.command_table["disk grant-access"] = DiskGrantAccess(loader=self)
        self.command_table["disk update"] = DiskUpdate(loader=self)

        from .aaz.latest.disk import List as DiskList, Show as DiskShow
        self.command_table['disk list'] = DiskList(loader=self, table_transformer='[].' + transform_disk_show_table_output)
        self.command_table['disk show'] = DiskShow(loader=self, table_transformer=transform_disk_show_table_output)

    with self.command_group("disk config"):
        from .operations.disk import DiskConfigUpdate
        self.command_table["disk config update"] = DiskConfigUpdate(loader=self)

    with self.command_group('disk-encryption-set', compute_disk_encryption_set_profile, operation_group='disk_encryption_sets'):
        from .operations.disk_encryption_set import DiskEncryptionSetCreate, DiskEncryptionSetUpdate
        self.command_table['disk-encryption-set create'] = DiskEncryptionSetCreate(loader=self)
        self.command_table['disk-encryption-set update'] = DiskEncryptionSetUpdate(loader=self)

    with self.command_group('disk-encryption-set identity', compute_disk_encryption_set_profile, operation_group='disk_encryption_sets') as g:
        from .operations.disk_encryption_set_identity import DiskEncryptionSetIdentityAssign, DiskEncryptionSetIdentityRemove
        self.command_table['disk-encryption-set identity assign'] = DiskEncryptionSetIdentityAssign(loader=self)
        self.command_table['disk-encryption-set identity remove'] = DiskEncryptionSetIdentityRemove(loader=self)
        g.custom_show_command('show', 'show_disk_encryption_set_identity')

    with self.command_group('image', compute_image_sdk) as g:
        g.custom_command('create', 'create_image', validator=process_image_create_namespace)

    with self.command_group('image builder', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('create', 'create_image_template', supports_no_wait=True, supports_local_cache=True, validator=process_image_template_create_namespace)
        g.custom_command('list', 'list_image_templates')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', supports_local_cache=True)  # todo Update fails for now as service does not support updates
        g.wait_command('wait')
        g.command('run', 'begin_run', supports_no_wait=True)
        g.custom_command('show-runs', 'show_build_output')
        g.command('cancel', 'begin_cancel')

    with self.command_group('image builder identity', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('assign', 'assign_template_identity', supports_local_cache=True)
        g.custom_command('remove', 'remove_template_identity', supports_local_cache=True, confirmation=True)
        g.custom_show_command('show', 'show_template_identity', supports_local_cache=True)

    with self.command_group('image builder customizer', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_customizer', supports_local_cache=True, validator=process_img_tmpl_customizer_add_namespace)
        g.custom_command('remove', 'remove_template_customizer', supports_local_cache=True)
        g.custom_command('clear', 'clear_template_customizer', supports_local_cache=True)

    with self.command_group('image builder output', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_output', supports_local_cache=True, validator=process_img_tmpl_output_add_namespace)
        g.custom_command('remove', 'remove_template_output', supports_local_cache=True)
        g.custom_command('clear', 'clear_template_output', supports_local_cache=True)

    with self.command_group('image builder output versioning', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('set', 'set_template_output_versioning', supports_local_cache=True)
        g.custom_command('remove', 'remove_template_output_versioning', supports_local_cache=True)
        g.custom_show_command('show', 'show_template_output_versioning', supports_local_cache=True)

    with self.command_group('image builder validator', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_validator', supports_local_cache=True)
        g.custom_command('remove', 'remove_template_validator', supports_local_cache=True)
        g.custom_show_command('show', 'show_template_validator', supports_local_cache=True)

    with self.command_group('image builder optimizer', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_or_update_template_optimizer', supports_local_cache=True)
        g.custom_command('update', 'add_or_update_template_optimizer', supports_local_cache=True)
        g.custom_command('remove', 'remove_template_optimizer', supports_local_cache=True)
        g.custom_show_command('show', 'show_template_optimizer', supports_local_cache=True)

    with self.command_group('image builder error-handler', image_builder_image_templates_sdk, custom_command_type=image_builder_custom) as g:
        g.custom_command('add', 'add_template_error_handler', supports_local_cache=True)
        g.custom_command('remove', 'remove_template_error_handler', supports_local_cache=True)
        g.custom_show_command('show', 'show_template_error_handler', supports_local_cache=True)

    with self.command_group('snapshot', operation_group='snapshots') as g:
        g.custom_command('create', 'create_snapshot', validator=process_snapshot_create_namespace, supports_no_wait=True)
        from .operations.snapshot import SnapshotUpdate
        self.command_table['snapshot update'] = SnapshotUpdate(loader=self)

    with self.command_group('vm identity') as g:
        g.custom_command('assign', 'assign_vm_identity', validator=process_assign_identity_namespace)
        g.custom_command('remove', 'remove_vm_identity', validator=process_remove_identity_namespace, min_api='2017-12-01')
        g.custom_show_command('show', 'show_vm_identity')

    with self.command_group('vm', compute_vm_sdk) as g:
        g.custom_command('application set', 'set_vm_applications', validator=process_set_applications_namespace, min_api='2021-07-01')
        g.custom_command('application list', 'list_vm_applications', min_api='2021-07-01')

        g.custom_command('create', 'create_vm', transform=transform_vm_create_output, supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vm_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('get-instance-view', 'get_instance_view', table_transformer='{Name:name, ResourceGroup:resourceGroup, Location:location, ProvisioningState:provisioningState, PowerState:instanceView.statuses[1].displayStatus}')
        g.custom_command('list', 'list_vm', table_transformer=transform_vm_list)
        g.custom_command('list-ip-addresses', 'list_vm_ip_addresses', table_transformer=transform_ip_addresses)
        g.custom_command('list-skus', 'list_skus', table_transformer=transform_sku_for_table_output, min_api='2017-03-30')
        g.command('list-usage', 'list', command_type=compute_vm_usage_sdk, transform=transform_vm_usage_list, table_transformer='[].{Name:localName, CurrentValue:currentValue, Limit:limit}')
        g.custom_command('open-port', 'open_vm_port')
        g.custom_command('resize', 'resize_vm', supports_no_wait=True)
        g.custom_command('restart', 'restart_vm', supports_no_wait=True)
        g.custom_show_command('show', 'show_vm', table_transformer=transform_vm)
        g.command('stop', 'begin_power_off', supports_no_wait=True, validator=process_vm_vmss_stop)
        g.generic_update_command('update', getter_name='get_vm_to_update_by_aaz', setter_name='update_vm', setter_type=compute_custom, command_type=compute_custom, supports_no_wait=True, validator=process_vm_update_namespace)
        g.wait_command('wait', getter_name='get_instance_view', getter_type=compute_custom)
        g.custom_command('auto-shutdown', 'auto_shutdown_vm')
        g.custom_command('list-sizes', 'list_vm_sizes', deprecate_info=g.deprecate(redirect='az vm list-skus'))

        from .operations.vm import VMCapture
        self.command_table['vm capture'] = VMCapture(loader=self)

    with self.command_group('vm', compute_vm_sdk, client_factory=cf_vm) as g:
        g.custom_command('install-patches', 'install_vm_patches', supports_no_wait=True, min_api='2020-12-01')

    with self.command_group('vm availability-set', compute_availset_profile) as g:
        g.custom_command('create', 'create_av_set', table_transformer=deployment_validate_table_format, supports_no_wait=True, exception_handler=handle_template_based_exception)
        from .operations.vm_availability_set import AvailabilitySetUpdate, AvailabilitySetConvert
        self.command_table['vm availability-set update'] = AvailabilitySetUpdate(loader=self)
        self.command_table['vm availability-set convert'] = AvailabilitySetConvert(loader=self)

    with self.command_group('vm boot-diagnostics', compute_vm_sdk) as g:
        g.custom_command('disable', 'disable_boot_diagnostics')
        g.custom_command('enable', 'enable_boot_diagnostics')
        g.custom_command('get-boot-log', 'get_boot_log')

    with self.command_group('vm diagnostics', compute_vm_sdk) as g:
        g.custom_command('set', 'set_diagnostics_extension')
        g.custom_command('get-default-config', 'show_default_diagnostics_configuration')

    with self.command_group('vm disk', compute_vm_sdk, min_api='2017-03-30') as g:
        g.custom_command('attach', 'attach_managed_data_disk', validator=process_vm_disk_attach_namespace)
        g.custom_command('detach', 'detach_managed_data_disk', validator=process_vm_disk_detach_namespace)

    with self.command_group('vm encryption', custom_command_type=compute_disk_encryption_custom) as g:
        g.custom_command('enable', 'encrypt_vm', validator=process_disk_encryption_namespace)
        g.custom_command('disable', 'decrypt_vm')
        g.custom_show_command('show', 'show_vm_encryption_status', table_transformer=transform_vm_encryption_show_table_output)

    with self.command_group('vm extension', compute_vm_extension_sdk) as g:
        g.custom_show_command('show', 'show_extensions', table_transformer=transform_extension_show_table_output)
        g.custom_command('set', 'set_extension', supports_no_wait=True)
        g.custom_command('list', 'list_extensions', table_transformer='[].' + transform_extension_show_table_output)

    with self.command_group('vm extension image', compute_vm_extension_image_sdk) as g:
        g.custom_command('list', 'list_vm_extension_images')

    with self.command_group('vm image', compute_vm_image_sdk) as g:
        g.custom_command('list-offers', 'list_offers')
        g.custom_command('list-publishers', 'list_publishers')
        g.custom_command('list-skus', 'list_sku')
        g.custom_command('list', 'list_vm_images')
        g.custom_show_command('show', 'show_vm_image')
        g.custom_command('accept-terms', 'accept_market_ordering_terms',
                         deprecate_info=g.deprecate(redirect='az vm image terms accept', expiration='3.0.0'))

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

    with self.command_group('vm run-command', compute_vm_run_profile, operation_group='virtual_machine_run_commands') as g:
        g.custom_command('invoke', 'vm_run_command_invoke', supports_no_wait=True)
        g.custom_command('list', 'vm_run_command_list')
        g.custom_show_command('show', 'vm_run_command_show')
        g.custom_command('create', 'vm_run_command_create', supports_no_wait=True)
        g.custom_command('update', 'vm_run_command_update', supports_no_wait=True)
        g.custom_wait_command('wait', 'vm_run_command_show')

    with self.command_group('vm secret', compute_vm_sdk) as g:
        g.custom_command('format', 'get_vm_format_secret', validator=process_vm_secret_format)
        g.custom_command('add', 'add_vm_secret')
        g.custom_command('list', 'list_vm_secrets')
        g.custom_command('remove', 'remove_vm_secret')

    with self.command_group('vm unmanaged-disk', compute_vm_sdk) as g:
        g.custom_command('attach', 'attach_unmanaged_data_disk')
        g.custom_command('detach', 'detach_unmanaged_data_disk')
        g.custom_command('list', 'list_unmanaged_disks')

    with self.command_group('vm user', compute_vm_sdk, supports_no_wait=True) as g:
        g.custom_command('update', 'set_user')
        g.custom_command('delete', 'delete_user')
        g.custom_command('reset-ssh', 'reset_linux_ssh')

    with self.command_group('vm host', compute_dedicated_host_sdk, client_factory=cf_dedicated_hosts,
                            min_api='2019-03-01') as g:
        g.custom_command('get-instance-view', 'get_dedicated_host_instance_view')
        g.custom_command('create', 'create_dedicated_host')
        g.generic_update_command('update', setter_name='begin_create_or_update')

    with self.command_group('vm host group', compute_dedicated_host_groups_sdk, client_factory=cf_dedicated_host_groups,
                            min_api='2019-03-01') as g:
        g.custom_command('get-instance-view', 'get_dedicated_host_group_instance_view', min_api='2020-06-01')
        g.custom_command('create', 'create_dedicated_host_group')
        g.generic_update_command('update')

    with self.command_group('vmss', compute_vmss_sdk, operation_group='virtual_machine_scale_sets') as g:
        g.custom_command('identity assign', 'assign_vmss_identity', validator=process_assign_identity_namespace)
        g.custom_command('identity remove', 'remove_vmss_identity', validator=process_remove_identity_namespace, min_api='2017-12-01', is_preview=True)
        g.custom_show_command('identity show', 'show_vmss_identity')
        g.custom_command('application set', 'set_vmss_applications', validator=process_set_applications_namespace, min_api='2021-07-01')
        g.custom_command('application list', 'list_vmss_applications', min_api='2021-07-01')
        g.custom_command('create', 'create_vmss', transform=DeploymentOutputLongRunningOperation(self.cli_ctx, 'Starting vmss create'), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_vmss_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('deallocate', 'deallocate_vmss', supports_no_wait=True)
        g.custom_command('get-instance-view', 'get_vmss_instance_view', table_transformer='{ProvisioningState:statuses[0].displayStatus, PowerState:statuses[1].displayStatus}')
        g.custom_command('list-instance-connection-info', 'list_vmss_instance_connection_info')
        g.custom_command('list-instance-public-ips', 'list_vmss_instance_public_ips')
        g.custom_command('list-instances', 'get_instances_list')
        g.custom_command('reimage', 'reimage_vmss', supports_no_wait=True, min_api='2017-03-30')
        g.custom_command('restart', 'restart_vmss', supports_no_wait=True)
        g.custom_command('scale', 'scale_vmss', supports_no_wait=True)
        g.custom_show_command('show', 'get_vmss', table_transformer=get_vmss_table_output_transformer(self, False))
        g.custom_command('stop', 'stop_vmss', supports_no_wait=True, validator=process_vm_vmss_stop)
        g.generic_update_command('update', getter_name='get_vmss_modified_by_aaz', setter_name='update_vmss', supports_no_wait=True, command_type=compute_custom, validator=validate_vmss_update_namespace)
        g.custom_command('update-instances', 'update_vmss_instances', supports_no_wait=True)
        g.wait_command('wait', getter_name='get_vmss', getter_type=compute_custom)
        g.custom_command('set-orchestration-service-state', 'set_orchestration_service_state', supports_no_wait=True)

        from .aaz.latest.vmss import List as VMSSList
        self.command_table['vmss list'] = VMSSList(loader=self,
                                                   table_transformer=transform_vmss_list_with_zones_table_output)

        from .operations.vmss_vms import VMSSGetResiliencyView
        self.command_table['vmss get-resiliency-view'] = VMSSGetResiliencyView(loader=self)

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
        g.custom_command('list', 'list_vm_extension_images')

    with self.command_group('vmss run-command', compute_vmss_run_sdk) as g:
        g.custom_command('invoke', 'vmss_run_command_invoke')
        g.custom_show_command('show', 'vmss_run_command_show')
        g.custom_command('create', 'vmss_run_command_create', supports_no_wait=True)
        g.custom_command('update', 'vmss_run_command_update', supports_no_wait=True)

    with self.command_group('sig', compute_galleries_sdk, operation_group='galleries') as g:
        from .operations.sig import SigCreate, SigUpdate, SigShow
        self.command_table['sig create'] = SigCreate(loader=self)
        self.command_table['sig update'] = SigUpdate(loader=self)
        self.command_table['sig show'] = SigShow(loader=self)

    with self.command_group('sig', community_gallery_sdk, client_factory=cf_community_gallery, operation_group='shared_galleries', min_api='2022-01-03') as g:
        g.custom_command('list-community', 'sig_community_gallery_list')

    with self.command_group('sig image-definition', compute_gallery_images_sdk, operation_group='gallery_images', min_api='2018-06-01') as g:
        g.custom_command('create', 'create_gallery_image')
        from .operations.sig_image_definition import SigImageDefinitionUpdate
        self.command_table['sig image-definition update'] = SigImageDefinitionUpdate(loader=self)

    with self.command_group('sig image-definition'):
        from .operations.sig_image_definition import SigImageDefinitionListShared
        self.command_table['sig image-definition list-shared'] = SigImageDefinitionListShared(loader=self)

    with self.command_group('sig image-version', compute_gallery_image_versions_sdk, operation_group='gallery_image_versions', min_api='2018-06-01') as g:
        g.custom_command('create', 'create_image_version', supports_no_wait=True, validator=process_image_version_create_namespace)
        g.custom_command('undelete', 'undelete_image_version', supports_no_wait=True, validator=process_image_version_undelete_namespace, is_preview=True)
        g.generic_update_command('update', getter_name='get_image_version_to_update', setter_arg_name='gallery_image_version', setter_name='update_image_version', setter_type=compute_custom, command_type=compute_custom, supports_no_wait=True, validator=process_image_version_update_namespace)
        from .aaz.latest.sig.image_version import Show as SigImageVersionShow
        self.command_table['sig image-version show'] = SigImageVersionShow(loader=self,
                                                                           table_transformer='{Name:name, ResourceGroup:resourceGroup, ProvisioningState:provisioningState, TargetRegions: publishingProfile.targetRegions && join(`, `, publishingProfile.targetRegions[*].name), EdgeZones: publishingProfile.targetExtendedLocations && join(`, `, publishingProfile.targetExtendedLocations[*].name), ReplicationState:replicationStatus.aggregatedState}')
    with self.command_group('sig image-version'):
        from .operations.sig_image_version import SigImageVersionListShared
        self.command_table['sig image-version list-shared'] = SigImageVersionListShared(loader=self)

    vm_gallery_sharing_profile = CliCommandType(
        operations_tmpl=(
            'azure.mgmt.compute.operations._gallery_sharing_profile_operations#GallerySharingProfileOperations.{}'
        ),
        operation_group='shared_galleries'
    )
    with self.command_group('sig share', vm_gallery_sharing_profile, operation_group='shared_galleries'):
        from .operations.sig_share import SigShareAdd, SigShareRemove, SigShareReset, SigShareEnableCommunity, SigShareWait
        self.command_table['sig share add'] = SigShareAdd(loader=self)
        self.command_table['sig share remove'] = SigShareRemove(loader=self)
        self.command_table['sig share reset'] = SigShareReset(loader=self)
        self.command_table['sig share enable-community'] = SigShareEnableCommunity(loader=self)
        self.command_table['sig share wait'] = SigShareWait(loader=self)

    with self.command_group('sig gallery-application', compute_gallery_application_profile, operation_group='gallery_applications') as g:
        from .operations.sig_gallery_application import SigGalleryApplicationCreate
        self.command_table['sig gallery-application create'] = SigGalleryApplicationCreate(loader=self)

    with self.command_group('sig gallery-application version', compute_gallery_application_version_profile, operation_group='gallery_application_versions'):
        from .operations.sig_gallery_application_version import SigGalleryApplicationVersionCreate, SiggalleryApplicationversionUpdate
        self.command_table['sig gallery-application version create'] = SigGalleryApplicationVersionCreate(loader=self)
        self.command_table['sig gallery-application version update'] = SiggalleryApplicationversionUpdate(loader=self)

    with self.command_group('sig in-vm-access-control-profile-version'):
        from .operations.sig_in_vm_access_control_profile_version import SigInVMAccessControlProfileVersionCreate, SigInVMAccessControlProfileVersionUpdate
        self.command_table['sig in-vm-access-control-profile-version create'] = SigInVMAccessControlProfileVersionCreate(loader=self)
        self.command_table['sig in-vm-access-control-profile-version update'] = SigInVMAccessControlProfileVersionUpdate(loader=self)

    with self.command_group('ppg', compute_proximity_placement_groups_sdk, min_api='2018-04-01', client_factory=cf_proximity_placement_groups) as g:
        from .operations.ppg import PPGCreate, PPGUpdate
        self.command_table['ppg create'] = PPGCreate(loader=self)
        self.command_table['ppg update'] = PPGUpdate(loader=self)

    with self.command_group('vm monitor log', client_factory=cf_log_analytics_data_plane) as g:
        g.custom_command('show', 'execute_query_for_vm', transform=transform_log_analytics_query_output)  # pylint: disable=show-command

    with self.command_group('vm monitor metrics', custom_command_type=monitor_custom, command_type=metric_definitions_sdk, resource_type=ResourceType.MGMT_MONITOR, operation_group='metric_definitions', is_preview=True) as g:
        from azure.cli.command_modules.monitor.transformers import metrics_table, metrics_definitions_table
        from azure.cli.core.profiles._shared import APIVersionException
        try:
            g.custom_command('tail', 'list_metrics', command_type=monitor_custom, table_transformer=metrics_table)
            g.command('list-definitions', 'list', table_transformer=metrics_definitions_table)
        except APIVersionException:
            pass

    with self.command_group('capacity reservation group', capacity_reservation_groups_sdk, min_api='2021-04-01',
                            client_factory=cf_capacity_reservation_groups) as g:
        g.custom_command('create', 'create_capacity_reservation_group')
        g.custom_command('update', 'update_capacity_reservation_group')
        g.custom_show_command('show', 'show_capacity_reservation_group')

    with self.command_group('capacity reservation group'):
        from .operations.capacity_reservation_group import CapacityReservationGroupList
        self.command_table['capacity reservation group list'] = CapacityReservationGroupList(loader=self)

    with self.command_group('capacity reservation', capacity_reservations_sdk, min_api='2021-04-01',
                            client_factory=cf_capacity_reservations) as g:
        from .operations.capacity_reservation import CapacityReservationUpdate, CapacityReservationShow
        self.command_table['capacity reservation update'] = CapacityReservationUpdate(loader=self)
        self.command_table['capacity reservation show'] = CapacityReservationShow(loader=self)

    with self.command_group('restore-point', restore_point) as g:
        g.custom_show_command('show', 'restore_point_show')
        g.custom_command('create', 'restore_point_create', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('restore-point collection', restore_point_collection) as g:
        g.custom_show_command('show', 'restore_point_collection_show')
