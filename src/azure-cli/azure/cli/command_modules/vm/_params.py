# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, too-many-lines
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.parameters import get_datetime_type
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_file_or_dict)
from azure.cli.core.commands.parameters import (
    get_location_type, get_resource_name_completion_list, tags_type, get_three_state_flag,
    file_type, get_enum_type, zone_type, zones_type)
from azure.cli.command_modules.vm._actions import _resource_not_exists
from azure.cli.command_modules.vm._completers import (
    get_urn_aliases_completion_list, get_vm_size_completion_list, get_vm_run_command_completion_list)
from azure.cli.command_modules.vm._validators import (
    validate_nsg_name, validate_vm_nics, validate_vm_nic, validate_vm_disk, validate_vmss_disk,
    validate_asg_names_or_ids, validate_keyvault, _validate_proximity_placement_group,
    process_gallery_image_version_namespace, validate_vm_name_for_monitor_metrics)

from azure.cli.command_modules.vm._vm_utils import MSI_LOCAL_ID
from azure.cli.command_modules.vm._image_builder import ScriptType

from azure.cli.command_modules.monitor.validators import validate_metric_dimension
from azure.cli.command_modules.monitor.actions import get_period_type


# pylint: disable=too-many-statements, too-many-branches, too-many-locals, too-many-lines
def load_arguments(self, _):
    # Model imports
    DiskStorageAccountTypes = self.get_models('DiskStorageAccountTypes', operation_group='disks')
    SnapshotStorageAccountTypes = self.get_models('SnapshotStorageAccountTypes', operation_group='snapshots')
    UpgradeMode, CachingTypes, OperatingSystemTypes = self.get_models('UpgradeMode', 'CachingTypes', 'OperatingSystemTypes')
    HyperVGenerationTypes = self.get_models('HyperVGenerationTypes')
    DedicatedHostLicenseTypes = self.get_models('DedicatedHostLicenseTypes')
    OrchestrationServiceNames, OrchestrationServiceStateAction = self.get_models('OrchestrationServiceNames', 'OrchestrationServiceStateAction', operation_group='virtual_machine_scale_sets')
    RebootSetting, VMGuestPatchClassificationWindows, VMGuestPatchClassificationLinux = self.get_models('VMGuestPatchRebootSetting', 'VMGuestPatchClassificationWindows', 'VMGuestPatchClassificationLinux')
    GallerySharingPermissionTypes = self.get_models('GallerySharingPermissionTypes', operation_group='shared_galleries')
    ReplicationMode = self.get_models('ReplicationMode', operation_group='gallery_image_versions')

    # REUSABLE ARGUMENT DEFINITIONS
    name_arg_type = CLIArgumentType(options_list=['--name', '-n'], metavar='NAME')
    multi_ids_type = CLIArgumentType(nargs='+')
    existing_vm_name = CLIArgumentType(overrides=name_arg_type,
                                       configured_default='vm',
                                       help="The name of the Virtual Machine. You can configure the default using `az configure --defaults vm=<name>`",
                                       completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'), id_part='name')
    existing_disk_name = CLIArgumentType(overrides=name_arg_type, help='The name of the managed disk', completer=get_resource_name_completion_list('Microsoft.Compute/disks'), id_part='name')
    existing_snapshot_name = CLIArgumentType(overrides=name_arg_type, help='The name of the snapshot', completer=get_resource_name_completion_list('Microsoft.Compute/snapshots'), id_part='name')
    vmss_name_type = CLIArgumentType(name_arg_type,
                                     configured_default='vmss',
                                     completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'),
                                     help="Scale set name. You can configure the default using `az configure --defaults vmss=<name>`",
                                     id_part='name')

    extension_instance_name_type = CLIArgumentType(help="Name of extension instance, which can be customized. Default: name of the extension.")
    image_template_name_type = CLIArgumentType(overrides=name_arg_type, id_part='name')
    disk_encryption_set_name = CLIArgumentType(overrides=name_arg_type, help='Name of disk encryption set.', id_part='name')
    ephemeral_placement_type = CLIArgumentType(options_list=['--ephemeral-os-disk-placement', '--ephemeral-placement'], arg_type=get_enum_type(['ResourceDisk', 'CacheDisk']), min_api='2019-12-01')

    license_type = CLIArgumentType(
        help="Specifies that the Windows image or disk was licensed on-premises. To enable Azure Hybrid Benefit for "
             "Windows Server, use 'Windows_Server'. To enable Multi-tenant Hosting Rights for Windows 10, "
             "use 'Windows_Client'. For more information see the Azure Windows VM online docs.",
        arg_type=get_enum_type(['Windows_Server', 'Windows_Client', 'RHEL_BYOS', 'SLES_BYOS', 'RHEL_BASE',
                                'RHEL_SAPAPPS', 'RHEL_SAPHA', 'RHEL_EUS', 'RHEL_BASESAPAPPS', 'RHEL_BASESAPHA', 'SLES_STANDARD', 'SLES_SAP', 'SLES_HPC',
                                'None', 'RHEL_ELS_6']))

    # StorageAccountTypes renamed to DiskStorageAccountTypes in 2018_06_01 of azure-mgmt-compute
    DiskStorageAccountTypes = DiskStorageAccountTypes or self.get_models('StorageAccountTypes')

    if DiskStorageAccountTypes:
        disk_sku = CLIArgumentType(arg_type=get_enum_type(DiskStorageAccountTypes))
    else:
        # StorageAccountTypes introduced in api version 2016_04_30_preview of Resource.MGMT.Compute package..
        # However, 2017-03-09-profile targets version 2016-03-30 of compute package.
        disk_sku = CLIArgumentType(arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']))

    if SnapshotStorageAccountTypes:
        snapshot_sku = CLIArgumentType(arg_type=get_enum_type(SnapshotStorageAccountTypes))
    else:
        # SnapshotStorageAccountTypes introduced in api version 2018_04_01 of Resource.MGMT.Compute package..
        # However, 2017-03-09-profile targets version 2016-03-30 of compute package.
        snapshot_sku = CLIArgumentType(arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']))

    # special case for `network nic scale-set list` command alias
    with self.argument_context('network nic scale-set list') as c:
        c.argument('virtual_machine_scale_set_name', options_list=['--vmss-name'], completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')

    HyperVGenerationTypes = HyperVGenerationTypes or self.get_models('HyperVGeneration', operation_group='disks')
    if HyperVGenerationTypes:
        hyper_v_gen_sku = CLIArgumentType(arg_type=get_enum_type(HyperVGenerationTypes, default="V1"))
    else:
        hyper_v_gen_sku = CLIArgumentType(arg_type=get_enum_type(["V1", "V2"], default="V1"))

    ultra_ssd_enabled_type = CLIArgumentType(
        arg_type=get_three_state_flag(), min_api='2018-06-01',
        help='Enables or disables the capability to have 1 or more managed data disks with UltraSSD_LRS storage account')

    scale_in_policy_type = CLIArgumentType(
        nargs='+', arg_type=get_enum_type(self.get_models('VirtualMachineScaleSetScaleInRules')),
        help='Specify the scale-in policy (space delimited) that decides which virtual machines are chosen for removal when a Virtual Machine Scale Set is scaled-in.'
    )

    edge_zone_type = CLIArgumentType(
        help='The name of edge zone.',
        min_api='2020-12-01',
        is_preview=True
    )

    t_shared_to = self.get_models('SharedToValues', operation_group='shared_galleries')
    shared_to_type = CLIArgumentType(
        arg_type=get_enum_type(t_shared_to),
        help='The query parameter to decide what shared galleries to fetch when doing listing operations. '
             'If not specified, list by subscription id.'
    )

    marker_type = CLIArgumentType(
        help='A string value that identifies the portion of the list of containers to be '
             'returned with the next listing operation. The operation returns the NextMarker value within '
             'the response body if the listing operation did not return all containers remaining to be listed '
             'with the current page. If specified, this generator will begin returning results from the point '
             'where the previous generator stopped.')

    enable_vtpm_type = CLIArgumentType(arg_type=get_three_state_flag(), min_api='2020-12-01', help='Enable vTPM.')
    enable_secure_boot_type = CLIArgumentType(arg_type=get_three_state_flag(), min_api='2020-12-01', help='Enable secure boot.')
    security_type = CLIArgumentType(arg_type=get_enum_type(['TrustedLaunch']), min_api='2020-12-01', help='Specify if the VM is Trusted Launch enabled. See https://docs.microsoft.com/azure/virtual-machines/trusted-launch.')

    # region MixedScopes
    for scope in ['vm', 'disk', 'snapshot', 'image', 'sig']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    for scope in ['disk', 'snapshot']:
        with self.argument_context(scope) as c:
            c.ignore('source_blob_uri', 'source_disk', 'source_snapshot')
            c.argument('source_storage_account_id', help='used when source blob is in a different subscription')
            c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB. Max size: 4095 GB (certain preview disks can be larger).', type=int)
            c.argument('duration_in_seconds', help='Time duration in seconds until the SAS access expires', type=int)
            if self.supported_api_version(min_api='2018-09-30', operation_group='disks'):
                c.argument('access_level', arg_type=get_enum_type(['Read', 'Write']), default='Read', help='access level')
                c.argument('for_upload', arg_type=get_three_state_flag(),
                           help='Create the {0} for uploading blobs later on through storage commands. Run "az {0} grant-access --access-level Write" to retrieve the {0}\'s SAS token.'.format(scope))
                c.argument('hyper_v_generation', arg_type=hyper_v_gen_sku, help='The hypervisor generation of the Virtual Machine. Applicable to OS disks only.')
            else:
                c.ignore('access_level', 'for_upload', 'hyper_v_generation')
            c.argument('encryption_type', min_api='2019-07-01', arg_type=get_enum_type(self.get_models('EncryptionType', operation_group='disks')),
                       help='Encryption type. EncryptionAtRestWithPlatformKey: Disk is encrypted with XStore managed key at rest. It is the default encryption type. EncryptionAtRestWithCustomerKey: Disk is encrypted with Customer managed key at rest.')
            c.argument('disk_encryption_set', min_api='2019-07-01', help='Name or ID of disk encryption set that is used to encrypt the disk.')
            c.argument('location', help='Location. Values from: `az account list-locations`. You can configure the default location using `az configure --defaults location=<location>`. If location is not specified and no default location specified, location will be automatically set as same as the resource group.')
            operation_group = 'disks' if scope == 'disk' else 'snapshots'
            c.argument('network_access_policy', min_api='2020-05-01', help='Policy for accessing the disk via network.', arg_type=get_enum_type(self.get_models('NetworkAccessPolicy', operation_group=operation_group)))
            c.argument('disk_access', min_api='2020-05-01', help='Name or ID of the disk access resource for using private endpoints on disks.')
            c.argument('enable_bursting', arg_type=get_three_state_flag(), help='Enable on-demand bursting beyond the provisioned performance target of the disk. On-demand bursting is disabled by default, and it does not apply to Ultra disks.')
            c.argument('public_network_access', arg_type=get_enum_type(['Disabled', 'Enabled']), min_api='2021-04-01', is_preview=True, help='Customers can set on Managed Disks or Snapshots to control the export policy on the disk.')
            c.argument('accelerated_network', arg_type=get_three_state_flag(), min_api='2021-04-01', is_preview=True, help='Customers can set on Managed Disks or Snapshots to enable the accelerated networking if the OS disk image support.')

    for scope in ['disk create', 'snapshot create']:
        with self.argument_context(scope) as c:
            c.argument('source', help='source to create the disk/snapshot from, including unmanaged blob uri, managed disk id or name, or snapshot id or name')
    # endregion

    # region Disks
    with self.argument_context('disk') as c:
        c.argument('zone', zone_type, min_api='2017-03-30', options_list=['--zone'])  # TODO: --size-gb currently has claimed -z. We can do a breaking change later if we want to.
        c.argument('disk_name', existing_disk_name, completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
        c.argument('name', arg_type=name_arg_type)
        c.argument('sku', arg_type=disk_sku, help='Underlying storage SKU')
        c.argument('os_type', arg_type=get_enum_type(OperatingSystemTypes), help='The Operating System type of the Disk.')
        c.argument('disk_iops_read_write', type=int, min_api='2018-06-01', help='The number of IOPS allowed for this disk. Only settable for UltraSSD disks. One operation can transfer between 4k and 256k bytes')
        c.argument('disk_mbps_read_write', type=int, min_api='2018-06-01', help="The bandwidth allowed for this disk. Only settable for UltraSSD disks. MBps means millions of bytes per second with ISO notation of powers of 10")
        c.argument('upload_size_bytes', type=int, min_api='2019-03-01',
                   help='The size (in bytes) of the contents of the upload including the VHD footer. Min value: 20972032. Max value: 35183298347520')
        c.argument('max_shares', type=int, help='The maximum number of VMs that can attach to the disk at the same time. Value greater than one indicates a disk that can be mounted on multiple VMs at the same time')
        c.argument('disk_iops_read_only', type=int, help='The total number of IOPS that will be allowed across all VMs mounting the shared disk as ReadOnly. One operation can transfer between 4k and 256k bytes')
        c.argument('disk_mbps_read_only', type=int, help='The total throughput (MBps) that will be allowed across all VMs mounting the shared disk as ReadOnly. MBps means millions of bytes per second - MB here uses the ISO notation, of powers of 10')
        c.argument('image_reference', help='ID or URN (publisher:offer:sku:version) of the image from which to create a disk')
        c.argument('image_reference_lun', type=int, help='If the disk is created from an image\'s data disk, this is an index that indicates which of the data disks in the image to use. For OS disks, this field is null')
        c.argument('gallery_image_reference', help='ID of the Compute Gallery image version from which to create a disk')
        c.argument('gallery_image_reference_lun', type=int, help='If the disk is created from an image\'s data disk, this is an index that indicates which of the data disks in the image to use. For OS disks, this field is null')
        c.argument('logical_sector_size', type=int, help='Logical sector size in bytes for Ultra disks. Supported values are 512 ad 4096. 4096 is the default.')
        c.argument('tier', help='Performance tier of the disk (e.g, P4, S10) as described here: https://azure.microsoft.com/pricing/details/managed-disks/. Does not apply to Ultra disks.')
        c.argument('edge_zone', edge_zone_type)
        c.argument('security_type', choices=['TrustedLaunch'], help='The security type of the VM. Applicable for OS disks only.', min_api='2020-12-01')
        c.argument('support_hibernation', arg_type=get_three_state_flag(), help='Indicate the OS on a disk supports hibernation.', min_api='2020-12-01')
    # endregion

    # region Snapshots
    with self.argument_context('snapshot', resource_type=ResourceType.MGMT_COMPUTE, operation_group='snapshots') as c:
        c.argument('snapshot_name', existing_snapshot_name, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/snapshots'))
        c.argument('name', arg_type=name_arg_type)
        c.argument('sku', arg_type=snapshot_sku)
        c.argument('incremental', arg_type=get_three_state_flag(), min_api='2019-03-01',
                   help='Whether a snapshot is incremental. Incremental snapshots on the same disk occupy less space than full snapshots and can be diffed')
        c.argument('edge_zone', edge_zone_type)
        c.argument('copy_start', arg_type=get_three_state_flag(), min_api='2021-04-01',
                   help='Create snapshot by using a deep copy process, where the resource creation is considered complete only after all data has been copied from the source.')
    # endregion

    # region Images
    with self.argument_context('image') as c:
        c.argument('os_type', arg_type=get_enum_type(['Windows', 'Linux']))
        c.argument('image_name', arg_type=name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/images'))
        c.argument('tags', tags_type)

    with self.argument_context('image create') as c:
        # here we collpase all difference image sources to under 2 common arguments --os-disk-source --data-disk-sources
        c.argument('name', arg_type=name_arg_type, help='new image name')
        c.argument('source', help='OS disk source from the same region, including a virtual machine ID or name, OS disk blob URI, managed OS disk ID or name, or OS snapshot ID or name')
        c.argument('data_disk_sources', nargs='+', help='Space-separated list of data disk sources, including unmanaged blob URI, managed disk ID or name, or snapshot ID or name')
        c.argument('zone_resilient', min_api='2017-12-01', arg_type=get_three_state_flag(), help='Specifies whether an image is zone resilient or not. '
                   'Default is false. Zone resilient images can be created only in regions that provide Zone Redundant Storage')
        c.argument('storage_sku', arg_type=disk_sku, help='The SKU of the storage account with which to create the VM image. Unused if source VM is specified.')
        c.argument('os_disk_caching', arg_type=get_enum_type(CachingTypes), help="Storage caching type for the image's OS disk.")
        c.argument('data_disk_caching', arg_type=get_enum_type(CachingTypes),
                   help="Storage caching type for the image's data disk.")
        c.argument('hyper_v_generation', arg_type=hyper_v_gen_sku, min_api="2019-03-01", help='The hypervisor generation of the Virtual Machine created from the image.')
        c.ignore('source_virtual_machine', 'os_blob_uri', 'os_disk', 'os_snapshot', 'data_blob_uris', 'data_disks', 'data_snapshots')
        c.argument('edge_zone', edge_zone_type, )
    # endregion

    # region Image Templates
    with self.argument_context('image builder') as c:
        ib_output_name_help = "Name of the image builder run output."

        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('scripts', nargs='+', help="Space-separated list of shell or powershell scripts to customize the image with. Each script must be a publicly accessible URL."
                                              " Infers type of script from file extension ('.sh' or'.ps1') or from source type. More more customizer options and flexibility, see: 'az image template customizer add'")
        c.argument('source', options_list=["--image-source", "-i"], help="The base image to customize. Must be a valid platform image URN, platform image alias, Red Hat ISO image URI, managed image name/ID, or shared image version ID.")
        c.argument('image_template_name', image_template_name_type, help="The name of the image template.")
        c.argument('checksum', help="The SHA256 checksum of the Red Hat ISO image")
        c.argument('managed_image_destinations', nargs='+', help='Managed image output distributor information. Space-separated list of key-value pairs. E.g "image_1=westus2 image_2=westus". Each key is the name or resource ID of the managed image to be created. Each value is the location of the image.')
        c.argument('shared_image_destinations', nargs='+', help='Shared image gallery (sig) output distributor information. Space-separated list of key-value pairs. E.g "my_gallery_1/image_def_1=eastus,westus  my_gallery_2/image_def_2=uksouth,canadaeast,francesouth." '
                                                                'Each key is the sig image definition ID or sig gallery name and sig image definition delimited by a "/". Each value is a comma-delimited list of replica locations.')
        c.argument('output_name', help=ib_output_name_help)
        c.ignore('destinations_lists', 'scripts_list', 'source_dict')

    with self.argument_context('image builder create') as c:
        ib_source_type = CLIArgumentType(arg_group="Image Source")
        ib_customizer_type = CLIArgumentType(arg_group="Customizer")
        ib_cutput_type = CLIArgumentType(arg_group="Output")

        c.argument('build_timeout', type=int, help="The Maximum duration to wait while building the image template, in minutes. Default is 60.")
        c.argument('image_template', help='Local path or URL to an image template file. When using --image-template, all other parameters are ignored except -g and -n. Reference: https://docs.microsoft.com/azure/virtual-machines/linux/image-builder-json')
        c.argument('identity', nargs='+', help='List of user assigned identities (name or ID, space delimited) of the image template.')

        # VM profile
        c.argument('vm_size', help='Size of the virtual machine used to build, customize and capture images. Omit or specify empty string to use the default (Standard_D1_v2)')
        c.argument('os_disk_size', type=int, help='Size of the OS disk in GB. Omit or specify 0 to use Azure\'s default OS disk size')
        c.argument('vnet', help='Name of VNET to deploy the build virtual machine. You should only specify it when subnet is a name')
        c.argument('subnet', help='Name or ID of subnet to deploy the build virtual machine')
        c.argument('proxy_vm_size', help='Size of the virtual machine used to build, customize and capture images (Standard_D1_v2 for Gen1 images and Standard_D2ds_v4 for Gen2 images).')
        c.argument('build_vm_identities', nargs='+', help='Optional configuration of the virtual network to use to deploy the build virtual machine in. Omit if no specific virtual network needs to be used.')

        # Image Source Arguments
        c.argument('source', arg_type=ib_source_type)
        c.argument('checksum', arg_type=ib_source_type)
        c.argument('', arg_type=ib_source_type)

        # Image Customizer Arguments
        c.argument('scripts', arg_type=ib_customizer_type)
        c.argument('', arg_type=ib_customizer_type)
        c.argument('', arg_type=ib_customizer_type)

        # Image Output Arguments
        c.argument('managed_image_destinations', arg_type=ib_cutput_type)
        c.argument('shared_image_destinations', arg_type=ib_cutput_type)
        c.argument('output_name', arg_type=ib_cutput_type)

    with self.argument_context('image builder output') as c:
        ib_sig_regions_help = "Space-separated list of regions to replicate the image version into."
        ib_img_location_help = "Location where the customized image will be created."

        c.argument('gallery_image_definition', arg_group="Shared Image Gallery", help="Name or ID of the existing SIG image definition to create the customized image version with.")
        c.argument('gallery_name', arg_group="Shared Image Gallery", help="Shared image gallery name, if image definition name and not ID was provided.")
        c.argument('gallery_replication_regions', arg_group="Shared Image Gallery", nargs='+', help=ib_sig_regions_help)
        c.argument('managed_image', arg_group="Managed Image", help="Name or ID of the customized managed image to be created.")
        c.argument('managed_image_location', arg_group="Managed Image", help=ib_img_location_help)

    with self.argument_context('image builder output add') as c:
        ib_artifact_tags_help = "Tags that will be applied to the output artifact once it has been created by the distributor. " + tags_type.settings['help']
        ib_artifact_tags_type = CLIArgumentType(overrides=tags_type, help=ib_artifact_tags_help, options_list=["--artifact-tags"])
        ib_default_loc_help = " Defaults to resource group's location."

        c.argument('output_name', help=ib_output_name_help + " Defaults to the name of the managed image or sig image definition.")
        c.argument('gallery_replication_regions', arg_group="Shared Image Gallery", nargs='+', help=ib_sig_regions_help + ib_default_loc_help)
        c.argument('managed_image_location', arg_group="Managed Image", help=ib_img_location_help + ib_default_loc_help)
        c.argument('is_vhd', arg_group="VHD", help="The output is a VHD distributor.", action='store_true')
        c.argument('tags', arg_type=ib_artifact_tags_type)
        c.ignore('location')

    with self.argument_context('image builder customizer') as c:
        ib_win_restart_type = CLIArgumentType(arg_group="Windows Restart")
        ib_win_update_type = CLIArgumentType(arg_group="Windows Update")
        ib_script_type = CLIArgumentType(arg_group="Shell and Powershell")
        ib_powershell_type = CLIArgumentType(arg_group="Powershell")
        ib_file_customizer_type = CLIArgumentType(arg_group="File")

        c.argument('customizer_name', help="Name of the customizer.")
        c.argument('customizer_type', options_list=['--type', '-t'], help="Type of customizer to be added to the image template.", arg_type=get_enum_type(ScriptType))

        # Script Args
        c.argument('script_url', arg_type=ib_script_type, help="URL of script to customize the image with. The URL must be publicly accessible.")
        c.argument('inline_script', arg_type=ib_script_type, nargs='+', help="Space-separated list of inline script lines to customize the image with.")

        # Powershell Specific Args
        c.argument('valid_exit_codes', options_list=['--exit-codes', '-e'], arg_type=ib_powershell_type, nargs='+', help="Space-separated list of valid exit codes, as integers")

        # Windows Restart Specific Args
        c.argument('restart_command', arg_type=ib_win_restart_type, help="Command to execute the restart operation.")
        c.argument('restart_check_command', arg_type=ib_win_restart_type, help="Command to verify that restart succeeded.")
        c.argument('restart_timeout', arg_type=ib_win_restart_type, help="Restart timeout specified as a string consisting of a magnitude and unit, e.g. '5m' (5 minutes) or '2h' (2 hours)", default="5m")

        # Windows Update Specific Args
        c.argument('search_criteria', arg_type=ib_win_update_type, help='Criteria to search updates. Omit or specify empty string to use the default (search all). Refer to above link for examples and detailed description of this field.')
        c.argument('filters', arg_type=ib_win_update_type, nargs='+', help='Space delimited filters to select updates to apply. Omit or specify empty array to use the default (no filter)')
        c.argument('update_limit', arg_type=ib_win_update_type, help='Maximum number of updates to apply at a time. Omit or specify 0 to use the default (1000)')

        # File Args
        c.argument('file_source', arg_type=ib_file_customizer_type, help="The URI of the file to be downloaded into the image. It can be a github link, SAS URI for Azure Storage, etc.")
        c.argument('dest_path', arg_type=ib_file_customizer_type, help="The absolute destination path where the file specified in --file-source will be downloaded to in the image")

    # endregion

    # region AvailabilitySets
    with self.argument_context('vm availability-set') as c:
        c.argument('availability_set_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')

    with self.argument_context('vm availability-set create') as c:
        c.argument('availability_set_name', name_arg_type, validator=get_default_location_from_resource_group, help='Name of the availability set')
        c.argument('platform_update_domain_count', type=int, help='Update Domain count. If unspecified, the server will pick the most optimal number like 5.')
        c.argument('platform_fault_domain_count', type=int, help='Fault Domain count.')
        c.argument('validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')
        c.argument('unmanaged', action='store_true', min_api='2016-04-30-preview', help='contained VMs should use unmanaged disks')

    with self.argument_context('vm availability-set update') as c:
        if self.supported_api_version(max_api='2016-04-30-preview', operation_group='virtual_machines'):
            c.argument('name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')
            c.argument('availability_set_name', options_list=['--availability-set-name'])
    # endregion

    # region VirtualMachines
    with self.argument_context('vm') as c:
        c.argument('vm_name', existing_vm_name)
        c.argument('size', completer=get_vm_size_completion_list)
        c.argument('name', arg_type=name_arg_type)
        c.argument('zone', zone_type, min_api='2017-03-30')
        c.argument('caching', help='Disk caching policy', arg_type=get_enum_type(CachingTypes))
        c.argument('nsg', help='The name to use when creating a new Network Security Group (default) or referencing an existing one. Can also reference an existing NSG by ID or specify "" for none.', arg_group='Network')
        c.argument('nsg_rule', help='NSG rule to create when creating a new NSG. Defaults to open ports for allowing RDP on Windows and allowing SSH on Linux.', arg_group='Network', arg_type=get_enum_type(['RDP', 'SSH']))
        c.argument('application_security_groups', min_api='2017-09-01', nargs='+', options_list=['--asgs'], help='Space-separated list of existing application security groups to associate with the VM.', arg_group='Network')
        c.argument('workspace', is_preview=True, arg_group='Monitor', help='Name or ID of Log Analytics Workspace. If you specify the workspace through its name, the workspace should be in the same resource group with the vm, otherwise a new workspace will be created.')
    with self.argument_context('vm capture') as c:
        c.argument('overwrite', action='store_true')

    with self.argument_context('vm update') as c:
        c.argument('os_disk', min_api='2017-12-01', help="Managed OS disk ID or name to swap to")
        c.argument('write_accelerator', nargs='*', min_api='2017-12-01',
                   help="enable/disable disk write accelerator. Use singular value 'true/false' to apply across, or specify individual disks, e.g.'os=true 1=true 2=true' for os disk and data disks with lun of 1 & 2")
        c.argument('disk_caching', nargs='*', help="Use singular value to apply across, or specify individual disks, e.g. 'os=ReadWrite 0=None 1=ReadOnly' should enable update os disk and 2 data disks")
        c.argument('ultra_ssd_enabled', ultra_ssd_enabled_type)
        c.argument('enable_secure_boot', enable_secure_boot_type)
        c.argument('enable_vtpm', enable_vtpm_type)
        c.argument('size', help='The new size of the virtual machine. See https://azure.microsoft.com/pricing/details/virtual-machines/ for size info.', is_preview=True)
        c.argument('ephemeral_os_disk_placement', arg_type=ephemeral_placement_type,
                   help='Only applicable when used with `--size`. Allows you to choose the Ephemeral OS disk provisioning location.', is_preview=True)
        c.argument('enable_hibernation', arg_type=get_three_state_flag(), min_api='2021-03-01', help='The flag that enable or disable hibernation capability on the VM.')

    with self.argument_context('vm create') as c:
        c.argument('name', name_arg_type, validator=_resource_not_exists(self.cli_ctx, 'Microsoft.Compute/virtualMachines'))
        c.argument('vm_name', name_arg_type, id_part=None, help='Name of the virtual machine.', completer=None)
        c.argument('os_disk_size_gb', type=int, help='the size of the os disk in GB', arg_group='Storage')
        c.argument('availability_set', help='Name or ID of an existing availability set to add the VM to. None by default.')
        c.argument('vmss', help='Name or ID of an existing virtual machine scale set that the virtual machine should be assigned to. None by default.')
        c.argument('nsg', help='The name to use when creating a new Network Security Group (default) or referencing an existing one. Can also reference an existing NSG by ID or specify "" for none (\'""\' in Azure CLI using PowerShell or --% operator).', arg_group='Network')
        c.argument('nsg_rule', help='NSG rule to create when creating a new NSG. Defaults to open ports for allowing RDP on Windows and allowing SSH on Linux. NONE represents no NSG rule', arg_group='Network', arg_type=get_enum_type(['RDP', 'SSH', 'NONE']))
        c.argument('application_security_groups', resource_type=ResourceType.MGMT_NETWORK, min_api='2017-09-01', nargs='+', options_list=['--asgs'], help='Space-separated list of existing application security groups to associate with the VM.', arg_group='Network', validator=validate_asg_names_or_ids)
        c.argument('boot_diagnostics_storage',
                   help='pre-existing storage account name or its blob uri to capture boot diagnostics. Its sku should be one of Standard_GRS, Standard_LRS and Standard_RAGRS')
        c.argument('accelerated_networking', resource_type=ResourceType.MGMT_NETWORK, min_api='2016-09-01', arg_type=get_three_state_flag(), arg_group='Network',
                   help="enable accelerated networking. Unless specified, CLI will enable it based on machine image and size")
        if self.supported_api_version(min_api='2019-03-01', resource_type=ResourceType.MGMT_COMPUTE):
            VirtualMachineEvictionPolicyTypes = self.get_models('VirtualMachineEvictionPolicyTypes', resource_type=ResourceType.MGMT_COMPUTE)
            c.argument('eviction_policy', resource_type=ResourceType.MGMT_COMPUTE, min_api='2019-03-01',
                       arg_type=get_enum_type(VirtualMachineEvictionPolicyTypes, default=None),
                       help="The eviction policy for the Spot priority virtual machine. Default eviction policy is Deallocate for a Spot priority virtual machine")
        c.argument('enable_agent', arg_type=get_three_state_flag(), min_api='2018-06-01',
                   help='Indicates whether virtual machine agent should be provisioned on the virtual machine. When this property is not specified, default behavior is to set it to true. This will ensure that VM Agent is installed on the VM so that extensions can be added to the VM later')
        c.argument('enable_auto_update', arg_type=get_three_state_flag(), min_api='2020-06-01',
                   help='Indicate whether Automatic Updates is enabled for the Windows virtual machine')
        c.argument('patch_mode', arg_type=get_enum_type(['AutomaticByOS', 'AutomaticByPlatform', 'Manual', 'ImageDefault']), min_api='2020-12-01',
                   help='Mode of in-guest patching to IaaS virtual machine. Allowed values for Windows VM: AutomaticByOS, AutomaticByPlatform, Manual. Allowed values for Linux VM: AutomaticByPlatform, ImageDefault. Manual - You control the application of patches to a virtual machine. You do this by applying patches manually inside the VM. In this mode, automatic updates are disabled; the paramater --enable-auto-update must be false. AutomaticByOS - The virtual machine will automatically be updated by the OS. The parameter --enable-auto-update must be true. AutomaticByPlatform - the virtual machine will automatically updated by the OS. ImageDefault - The virtual machine\'s default patching configuration is used. The parameter --enable-agent and --enable-auto-update must be true')
        c.argument('ssh_key_name', help='Use it as public key in virtual machine. It should be an existing SSH key resource in Azure.')
        c.argument('enable_hotpatching', arg_type=get_three_state_flag(), help='Patch VMs without requiring a reboot. --enable-agent must be set and --patch-mode must be set to AutomaticByPlatform', min_api='2020-12-01')
        c.argument('platform_fault_domain', min_api='2020-06-01',
                   help='Specify the scale set logical fault domain into which the virtual machine will be created. By default, the virtual machine will be automatically assigned to a fault domain that best maintains balance across available fault domains. This is applicable only if the virtualMachineScaleSet property of this virtual machine is set. The virtual machine scale set that is referenced, must have platform fault domain count. This property cannot be updated once the virtual machine is created. Fault domain assignment can be viewed in the virtual machine instance view')
        c.argument('count', type=int, is_preview=True,
                   help='Number of virtual machines to create. Value range is [2, 250], inclusive. Don\'t specify this parameter if you want to create a normal single VM. The VMs are created in parallel. The output of this command is an array of VMs instead of one single VM. Each VM has its own public IP, NIC. VNET and NSG are shared. It is recommended that no existing public IP, NIC, VNET and NSG are in resource group. When --count is specified, --attach-data-disks, --attach-os-disk, --boot-diagnostics-storage, --computer-name, --host, --host-group, --nics, --os-disk-name, --private-ip-address, --public-ip-address, --public-ip-address-dns-name, --storage-account, --storage-container-name, --subnet, --use-unmanaged-disk, --vnet-name are not allowed.')
        c.argument('security_type', security_type)
        c.argument('enable_secure_boot', enable_secure_boot_type)
        c.argument('enable_vtpm', enable_vtpm_type)
        c.argument('user_data', help='UserData for the VM. It can be passed in as file or string.', completer=FilesCompleter(), type=file_type, min_api='2021-03-01')
        c.argument('enable_hibernation', arg_type=get_three_state_flag(), min_api='2021-03-01', help='The flag that enable or disable hibernation capability on the VM.')

    with self.argument_context('vm create', arg_group='Storage') as c:
        c.argument('attach_os_disk', help='Attach an existing OS disk to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')
        c.argument('attach_data_disks', nargs='+', help='Attach existing data disks to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')

    with self.argument_context('vm create', arg_group='Dedicated Host', min_api='2019-03-01') as c:
        c.argument('dedicated_host_group', options_list=['--host-group'], is_preview=True, help="Name or ID of the dedicated host group that the VM will reside in. --host and --host-group can't be used together.")
        c.argument('dedicated_host', options_list=['--host'], is_preview=True, help="ID of the dedicated host that the VM will reside in. --host and --host-group can't be used together.")

    with self.argument_context('vm update', arg_group='Dedicated Host', min_api='2019-03-01') as c:
        c.argument('dedicated_host_group', options_list=['--host-group'], is_preview=True, help="Name or ID of the dedicated host group that the VM will reside in. --host and --host-group can't be used together. You should deallocate the VM before update, and start the VM after update. Please check out help for more examples.")
        c.argument('dedicated_host', options_list=['--host'], is_preview=True, help="ID of the dedicated host that the VM will reside in. --host and --host-group can't be used together. You should deallocate the VM before update, and start the VM after update. Please check out help for more examples.")

    with self.argument_context('vm open-port') as c:
        c.argument('vm_name', name_arg_type, help='The name of the virtual machine to open inbound traffic on.')
        c.argument('network_security_group_name', options_list=('--nsg-name',), help='The name of the network security group to create if one does not exist. Ignored if an NSG already exists.', validator=validate_nsg_name)
        c.argument('apply_to_subnet', help='Allow inbound traffic on the subnet instead of the NIC', action='store_true')
        c.argument('port', help="The port or port range (ex: 80-100) to open inbound traffic to. Use '*' to allow traffic to all ports. Use comma separated values to specify more than one port or port range.")
        c.argument('priority', help='Rule priority, between 100 (highest priority) and 4096 (lowest priority). Must be unique for each rule in the collection.', type=int)

    for scope in ['vm show', 'vm list']:
        with self.argument_context(scope) as c:
            c.argument('show_details', action='store_true', options_list=['--show-details', '-d'], help='show public ip address, FQDN, and power states. command will run slow')

    for scope in ['vm show', 'vmss show']:
        with self.argument_context(scope) as c:
            c.argument('include_user_data', action='store_true', options_list=['--include-user-data', '-u'], help='Include the user data properties in the query result.', min_api='2021-03-01')

    for scope in ['vm get-instance-view', 'vm wait', 'vmss wait']:
        with self.argument_context(scope) as c:
            c.ignore('include_user_data')

    with self.argument_context('vm diagnostics') as c:
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'])

    with self.argument_context('vm diagnostics set') as c:
        c.argument('storage_account', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))

    with self.argument_context('vm install-patches') as c:
        c.argument('maximum_duration', type=str, help='Specify the maximum amount of time that the operation will run. It must be an ISO 8601-compliant duration string such as PT4H (4 hours)')
        c.argument('reboot_setting', arg_type=get_enum_type(RebootSetting), help='Define when it is acceptable to reboot a VM during a software update operation.')
        c.argument('classifications_to_include_win', nargs='+', arg_type=get_enum_type(VMGuestPatchClassificationWindows), help='Space-separated list of classifications to include for Windows VM.')
        c.argument('classifications_to_include_linux', nargs='+', arg_type=get_enum_type(VMGuestPatchClassificationLinux), help='Space-separated list of classifications to include for Linux VM.')
        c.argument('kb_numbers_to_include', nargs='+', help='Space-separated list of KBs to include in the patch operation. Applicable to Windows VM only')
        c.argument('kb_numbers_to_exclude', nargs='+', help='Space-separated list of KBs to exclude in the patch operation. Applicable to Windows VM only')
        c.argument('exclude_kbs_requiring_reboot', arg_type=get_three_state_flag(), help="Filter out KBs that don't have a reboot behavior of 'NeverReboots' when this is set. Applicable to Windows VM only")
        c.argument('package_name_masks_to_include', nargs='+', help='Space-separated list of packages to include in the patch operation. Format: packageName_packageVersion. Applicable to Linux VM only')
        c.argument('package_name_masks_to_exclude', nargs='+', help='Space-separated list of packages to exclude in the patch operation. Format: packageName_packageVersion. Applicable to Linux VM only')

    with self.argument_context('vm disk') as c:
        c.argument('vm_name', options_list=['--vm-name'], id_part=None, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'))
        c.argument('new', action='store_true', help='create a new disk')
        c.argument('sku', arg_type=disk_sku, help='Underlying storage SKU')
        c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB. Max size: 4095 GB (certain preview disks can be larger).', type=int)
        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')

    with self.argument_context('vm disk attach') as c:
        c.argument('enable_write_accelerator', min_api='2017-12-01', action='store_true', help='enable write accelerator')
        c.argument('disk', options_list=['--name', '-n', c.deprecate(target='--disk', redirect='--name', hide=True)],
                   help="The name or ID of the managed disk", validator=validate_vm_disk, id_part='name',
                   completer=get_resource_name_completion_list('Microsoft.Compute/disks'))

    with self.argument_context('vm disk detach') as c:
        c.argument('disk_name', arg_type=name_arg_type, help='The data disk name.')

    with self.argument_context('vm encryption enable') as c:
        c.argument('encrypt_format_all', action='store_true', help='Encrypts-formats data disks instead of encrypting them. Encrypt-formatting is a lot faster than in-place encryption but wipes out the partition getting encrypt-formatted. (Only supported for Linux virtual machines.)')
        # Place aad arguments in their own group
        aad_arguments = 'Azure Active Directory'
        c.argument('aad_client_id', arg_group=aad_arguments)
        c.argument('aad_client_secret', arg_group=aad_arguments)
        c.argument('aad_client_cert_thumbprint', arg_group=aad_arguments)

    with self.argument_context('vm extension') as c:
        c.argument('vm_extension_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'), help='Name of the extension.', id_part='child_name_1')
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'], id_part='name')
        c.argument('expand', help='The expand expression to apply on the operation.', deprecate_info=c.deprecate(expiration='3.0.0', hide=True))

    with self.argument_context('vm extension list') as c:
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'], id_part=None)

    with self.argument_context('vm extension show') as c:
        c.argument('instance_view', action='store_true', help='The instance view of a virtual machine extension.')

    with self.argument_context('vm secret') as c:
        c.argument('secrets', multi_ids_type, options_list=['--secrets', '-s'], help='Space-separated list of key vault secret URIs. Perhaps, produced by \'az keyvault secret list-versions --vault-name vaultname -n cert1 --query "[?attributes.enabled].id" -o tsv\'')
        c.argument('keyvault', help='Name or ID of the key vault.', validator=validate_keyvault)
        c.argument('certificate', help='key vault certificate name or its full secret URL')
        c.argument('certificate_store', help='Windows certificate store names. Default: My')

    with self.argument_context('vm secret list') as c:
        c.argument('vm_name', arg_type=existing_vm_name, id_part=None)

    with self.argument_context('vm image') as c:
        c.argument('publisher_name', options_list=['--publisher', '-p'], help='image publisher')
        c.argument('publisher', options_list=['--publisher', '-p'], help='image publisher')
        c.argument('offer', options_list=['--offer', '-f'], help='image offer')
        c.argument('plan', help='image billing plan')
        c.argument('sku', options_list=['--sku', '-s'], help='image sku')
        c.argument('version', help="image sku's version")
        c.argument('urn', help="URN, in format of 'publisher:offer:sku:version' or 'publisher:offer:sku:edge_zone:version'. If specified, other argument values can be omitted")

    with self.argument_context('vm image list') as c:
        c.argument('image_location', get_location_type(self.cli_ctx))
        c.argument('edge_zone', edge_zone_type)

    with self.argument_context('vm image list-offers') as c:
        c.argument('edge_zone', edge_zone_type)

    with self.argument_context('vm image list-skus') as c:
        c.argument('edge_zone', edge_zone_type)

    with self.argument_context('vm image list-publishers') as c:
        c.argument('edge_zone', edge_zone_type)

    with self.argument_context('vm image show') as c:
        c.argument('skus', options_list=['--sku', '-s'])
        c.argument('edge_zone', edge_zone_type)

    with self.argument_context('vm image terms') as c:
        c.argument('urn', help='URN, in the format of \'publisher:offer:sku:version\'. If specified, other argument values can be omitted')
        c.argument('publisher', help='Image publisher')
        c.argument('offer', help='Image offer')
        c.argument('plan', help='Image billing plan')

    with self.argument_context('vm nic') as c:
        c.argument('vm_name', existing_vm_name, options_list=['--vm-name'], id_part=None)
        c.argument('nics', nargs='+', help='Names or IDs of NICs.', validator=validate_vm_nics)
        c.argument('primary_nic', help='Name or ID of the primary NIC. If missing, the first NIC in the list will be the primary.')

    with self.argument_context('vm nic show') as c:
        c.argument('nic', help='NIC name or ID.', validator=validate_vm_nic)

    with self.argument_context('vm unmanaged-disk') as c:
        c.argument('new', action='store_true', help='Create a new disk.')
        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')
        c.argument('vhd_uri', help="Virtual hard disk URI. For example: https://mystorage.blob.core.windows.net/vhds/d1.vhd")

    with self.argument_context('vm unmanaged-disk attach') as c:
        c.argument('disk_name', options_list=['--name', '-n'], help='The data disk name.')
        c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB. Max size: 4095 GB (certain preview disks can be larger).', type=int)

    with self.argument_context('vm unmanaged-disk detach') as c:
        c.argument('disk_name', options_list=['--name', '-n'], help='The data disk name.')

    for scope in ['vm unmanaged-disk attach', 'vm unmanaged-disk detach']:
        with self.argument_context(scope) as c:
            c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'], id_part=None)

    with self.argument_context('vm unmanaged-disk list') as c:
        c.argument('vm_name', options_list=['--vm-name', '--name', '-n'], arg_type=existing_vm_name, id_part=None)

    with self.argument_context('vm user') as c:
        c.argument('username', options_list=['--username', '-u'], help='The user name')
        c.argument('password', options_list=['--password', '-p'], help='The user password')

    with self.argument_context('vm list-skus') as c:
        c.argument('size', options_list=['--size', '-s'], help="size name, partial name is accepted")
        c.argument('zone', options_list=['--zone', '-z'], arg_type=get_three_state_flag(), help="show skus supporting availability zones")
        c.argument('show_all', options_list=['--all'], arg_type=get_three_state_flag(),
                   help="show all information including vm sizes not available under the current subscription")
        c.argument('resource_type', options_list=['--resource-type', '-r'], help='resource types e.g. "availabilitySets", "snapshots", "disks", etc')

    with self.argument_context('vm restart') as c:
        c.argument('force', action='store_true', help='Force the VM to restart by redeploying it. Use if the VM is unresponsive.')

    with self.argument_context('vm host') as c:
        c.argument('host_group_name', options_list=['--host-group'], id_part='name', help="Name of the Dedicated Host Group")
        c.argument('host_name', name_arg_type, id_part='child_name_1', help="Name of the Dedicated Host")
        c.ignore('expand')

    with self.argument_context('vm host create') as c:
        c.argument('platform_fault_domain', options_list=['--platform-fault-domain', '-d'], type=int,
                   help="Fault domain of the host within a group. Allowed values: 0, 1, 2")
        c.argument('auto_replace_on_failure', options_list=['--auto-replace'], arg_type=get_three_state_flag(),
                   help="Replace the host automatically if a failure occurs")
        c.argument('license_type', arg_type=get_enum_type(DedicatedHostLicenseTypes),
                   help="The software license type that will be applied to the VMs deployed on the dedicated host.")
        c.argument('sku', help="SKU of the dedicated host. Available SKUs: https://azure.microsoft.com/pricing/details/virtual-machines/dedicated-host/")

    with self.argument_context('vm host list') as c:
        c.argument('host_group_name', id_part=None)

    with self.argument_context('vm host group') as c:
        c.argument('host_group_name', name_arg_type, id_part='name', help="Name of the Dedicated Host Group")
        c.argument('automatic_placement', arg_type=get_three_state_flag(), min_api='2020-06-01',
                   help='Specify whether virtual machines or virtual machine scale sets can be placed automatically '
                        'on the dedicated host group. Automatic placement means resources are allocated on dedicated '
                        'hosts, that are chosen by Azure, under the dedicated host group. The value is defaulted to '
                        'false when not provided.')

    with self.argument_context('vm host group create') as c:
        c.argument('platform_fault_domain_count', options_list=["--platform-fault-domain-count", "-c"], type=int,
                   help="Number of fault domains that the host group can span.")
        c.argument('zones', zone_type)

    for scope in ["vm host", "vm host group"]:
        with self.argument_context("{} create".format(scope)) as c:
            location_type = get_location_type(self.cli_ctx)
            custom_location_msg = " Otherwise, location will default to the resource group's location"
            custom_location_type = CLIArgumentType(overrides=location_type,
                                                   help=location_type.settings["help"] + custom_location_msg)
            c.argument('location', arg_type=custom_location_type)
    # endregion

    # region VMSS
    scaleset_name_aliases = ['vm_scale_set_name', 'virtual_machine_scale_set_name', 'name']

    with self.argument_context('vmss') as c:
        c.argument('zones', zones_type, min_api='2017-03-30')
        c.argument('instance_id', id_part='child_name_1')
        c.argument('instance_ids', multi_ids_type, help='Space-separated list of IDs (ex: 1 2 3 ...) or * for all instances. If not provided, the action will be applied on the scaleset itself')
        c.argument('tags', tags_type)
        c.argument('caching', help='Disk caching policy', arg_type=get_enum_type(CachingTypes))
        for dest in scaleset_name_aliases:
            c.argument(dest, vmss_name_type)
        c.argument('host_group', min_api='2020-06-01',
                   help='Name or ID of dedicated host group that the virtual machine scale set resides in')

    for scope in ['vmss deallocate', 'vmss delete-instances', 'vmss restart', 'vmss start', 'vmss stop', 'vmss show', 'vmss update-instances', 'vmss simulate-eviction']:
        with self.argument_context(scope) as c:
            for dest in scaleset_name_aliases:
                c.argument(dest, vmss_name_type, id_part=None)  # due to instance-ids parameter

    with self.argument_context('vmss create', operation_group='virtual_machine_scale_sets') as c:
        VirtualMachineEvictionPolicyTypes = self.get_models('VirtualMachineEvictionPolicyTypes', resource_type=ResourceType.MGMT_COMPUTE)

        c.argument('name', name_arg_type)
        c.argument('nat_backend_port', default=None, help='Backend port to open with NAT rules. Defaults to 22 on Linux and 3389 on Windows.')
        c.argument('single_placement_group', arg_type=get_three_state_flag(), help="Limit the scale set to a single placement group."
                   " See https://docs.microsoft.com/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-placement-groups for details.")
        c.argument('platform_fault_domain_count', type=int, help='Fault Domain count for each placement group in the availability zone', min_api='2017-12-01')
        c.argument('vmss_name', name_arg_type, id_part=None, help='Name of the virtual machine scale set.')
        c.argument('instance_count', help='Number of VMs in the scale set.', type=int)
        c.argument('disable_overprovision', help='Overprovision option (see https://azure.microsoft.com/documentation/articles/virtual-machine-scale-sets-overview/ for details).', action='store_true')
        c.argument('upgrade_policy_mode', help=None, arg_type=get_enum_type(UpgradeMode))
        c.argument('health_probe', help='Probe name from the existing load balancer, mainly used for rolling upgrade or automatic repairs')
        c.argument('vm_sku', help='Size of VMs in the scale set. Default to "Standard_DS1_v2". See https://azure.microsoft.com/pricing/details/virtual-machines/ for size info.')
        c.argument('nsg', help='Name or ID of an existing Network Security Group.', arg_group='Network')
        c.argument('eviction_policy', resource_type=ResourceType.MGMT_COMPUTE, min_api='2017-12-01', arg_type=get_enum_type(VirtualMachineEvictionPolicyTypes, default=None),
                   help="The eviction policy for virtual machines in a Spot priority scale set. Default eviction policy is Deallocate for a Spot priority scale set")
        c.argument('application_security_groups', resource_type=ResourceType.MGMT_COMPUTE, min_api='2018-06-01', nargs='+', options_list=['--asgs'], help='Space-separated list of existing application security groups to associate with the VM.', arg_group='Network', validator=validate_asg_names_or_ids)
        c.argument('computer_name_prefix', help='Computer name prefix for all of the virtual machines in the scale set. Computer name prefixes must be 1 to 15 characters long')
        c.argument('orchestration_mode', help='Choose how virtual machines are managed by the scale set. In Uniform mode, you define a virtual machine model and Azure will generate identical instances based on that model. In Flexible mode, you manually create and add a virtual machine of any configuration to the scale set or generate identical instances based on virtual machine model defined for the scale set.',
                   arg_type=get_enum_type(['Uniform', 'Flexible']))
        c.argument('scale_in_policy', scale_in_policy_type)
        c.argument('automatic_repairs_grace_period', min_api='2018-10-01',
                   help='The amount of time (in minutes, between 30 and 90) for which automatic repairs are suspended due to a state change on VM.')
        c.argument('automatic_repairs_action', arg_type=get_enum_type(['Replace', 'Restart', 'Reimage']), min_api='2021-11-01', help='Type of repair action that will be used for repairing unhealthy virtual machines in the scale set.')
        c.argument('user_data', help='UserData for the virtual machines in the scale set. It can be passed in as file or string.', completer=FilesCompleter(), type=file_type, min_api='2021-03-01')
        c.argument('network_api_version', min_api='2021-03-01',
                   help="Specify the Microsoft.Network API version used when creating networking resources in the Network "
                        "Interface Configurations for Virtual Machine Scale Set with orchestration mode 'Flexible'. Default "
                        "value is 2020-11-01.")
        c.argument('enable_spot_restore', arg_type=get_three_state_flag(), min_api='2021-04-01', help='Enable the Spot-Try-Restore feature where evicted VMSS SPOT instances will be tried to be restored opportunistically based on capacity availability and pricing constraints')
        c.argument('spot_restore_timeout', min_api='2021-04-01', help='Timeout value expressed as an ISO 8601 time duration after which the platform will not try to restore the VMSS SPOT instances')
        c.argument('enable_agent', arg_type=get_three_state_flag(), min_api='2018-06-01',
                   help='Indicate whether virtual machine agent should be provisioned on the virtual machine. When this property is not specified, default behavior is to set it to true. This will ensure that VM Agent is installed on the VM so that extensions can be added to the VM later')
        c.argument('enable_auto_update', arg_type=get_three_state_flag(), min_api='2020-06-01',
                   help='Indicate whether Automatic Updates is enabled for the Windows virtual machine')
        c.argument('patch_mode', arg_type=get_enum_type(['AutomaticByOS', 'AutomaticByPlatform', 'Manual', 'ImageDefault']), min_api='2020-12-01',
                   help='Mode of in-guest patching to IaaS virtual machine. Allowed values for Windows VM: AutomaticByOS, AutomaticByPlatform, Manual. Allowed values for Linux VM: AutomaticByPlatform, ImageDefault. Manual - You control the application of patches to a virtual machine. You do this by applying patches manually inside the VM. In this mode, automatic updates are disabled; the paramater --enable-auto-update must be false. AutomaticByOS - The virtual machine will automatically be updated by the OS. The parameter --enable-auto-update must be true. AutomaticByPlatform - the virtual machine will automatically updated by the OS. ImageDefault - The virtual machine\'s default patching configuration is used. The parameter --enable-agent and --enable-auto-update must be true')
        c.argument('security_type', security_type)
        c.argument('enable_secure_boot', enable_secure_boot_type)
        c.argument('enable_vtpm', enable_vtpm_type)

    with self.argument_context('vmss create', arg_group='Network Balancer') as c:
        LoadBalancerSkuName = self.get_models('LoadBalancerSkuName', resource_type=ResourceType.MGMT_NETWORK)
        c.argument('application_gateway', help='Name to use when creating a new application gateway (default) or referencing an existing one. Can also reference an existing application gateway by ID or specify "" for none.', options_list=['--app-gateway'])
        c.argument('app_gateway_capacity', help='The number of instances to use when creating a new application gateway.')
        c.argument('app_gateway_sku', help='SKU when creating a new application gateway.')
        c.argument('app_gateway_subnet_address_prefix', help='The subnet IP address prefix to use when creating a new application gateway in CIDR format.')
        c.argument('backend_pool_name', help='Name to use for the backend pool when creating a new load balancer or application gateway.')
        c.argument('backend_port', help='When creating a new load balancer, backend port to open with NAT rules (Defaults to 22 on Linux and 3389 on Windows). When creating an application gateway, the backend port to use for the backend HTTP settings.', type=int)
        c.argument('load_balancer', help='Name to use when creating a new load balancer (default) or referencing an existing one. Can also reference an existing load balancer by ID or specify "" for none.', options_list=['--load-balancer', '--lb'])
        c.argument('load_balancer_sku', resource_type=ResourceType.MGMT_NETWORK, min_api='2017-08-01', options_list=['--lb-sku'], arg_type=get_enum_type(LoadBalancerSkuName),
                   help="Sku of the Load Balancer to create. Default to 'Standard' when single placement group is turned off; otherwise, default to 'Basic'. The public IP is supported to be created on edge zone only when it is 'Standard'")
        c.argument('nat_pool_name', help='Name to use for the NAT pool when creating a new load balancer.', options_list=['--lb-nat-pool-name', '--nat-pool-name'])

    with self.argument_context('vmss create', min_api='2017-03-30', arg_group='Network') as c:
        c.argument('public_ip_per_vm', action='store_true', help="Each VM instance will have a public ip. For security, you can use '--nsg' to apply appropriate rules")
        c.argument('vm_domain_name', help="domain name of VM instances, once configured, the FQDN is `vm<vm-index>.<vm-domain-name>.<..rest..>`")
        c.argument('dns_servers', nargs='+', help="space-separated IP addresses of DNS servers, e.g. 10.0.0.5 10.0.0.6")
        c.argument('accelerated_networking', arg_type=get_three_state_flag(),
                   help="enable accelerated networking. Unless specified, CLI will enable it based on machine image and size")

    with self.argument_context('vmss update') as c:
        protection_policy_type = CLIArgumentType(overrides=get_three_state_flag(), arg_group="Protection Policy", min_api='2019-03-01')
        c.argument('protect_from_scale_in', arg_type=protection_policy_type, help="Protect the VM instance from scale-in operations.")
        c.argument('protect_from_scale_set_actions', arg_type=protection_policy_type, help="Protect the VM instance from scale set actions (including scale-in).")
        c.argument('enable_terminate_notification', min_api='2019-03-01', arg_type=get_three_state_flag(),
                   help='Enable terminate notification')
        c.argument('ultra_ssd_enabled', ultra_ssd_enabled_type)
        c.argument('scale_in_policy', scale_in_policy_type)
        c.argument('force_deletion', action='store_true', is_preview=True, help='This property allow you to specify if virtual machines chosen for removal have to be force deleted when a virtual machine scale set is being scaled-in.')
        c.argument('user_data', help='UserData for the virtual machines in the scale set. It can be passed in as file or string. If empty string is passed in, the existing value will be deleted.', completer=FilesCompleter(), type=file_type, min_api='2021-03-01')
        c.argument('enable_spot_restore', arg_type=get_three_state_flag(), min_api='2021-04-01',
                   help='Enable the Spot-Try-Restore feature where evicted VMSS SPOT instances will be tried to be restored opportunistically based on capacity availability and pricing constraints')
        c.argument('spot_restore_timeout', min_api='2021-04-01',
                   help='Timeout value expressed as an ISO 8601 time duration after which the platform will not try to restore the VMSS SPOT instances')
        c.argument('vm_sku', help='The new size of the virtual machine instances in the scale set. Default to "Standard_DS1_v2". See https://azure.microsoft.com/pricing/details/virtual-machines/ for size info.', is_preview=True)
        c.argument('ephemeral_os_disk_placement', arg_type=ephemeral_placement_type,
                   help='Only applicable when used with `--vm-sku`. Allows you to choose the Ephemeral OS disk provisioning location.', is_preview=True)
        c.argument('enable_secure_boot', enable_secure_boot_type)
        c.argument('enable_vtpm', enable_vtpm_type)

    with self.argument_context('vmss update', min_api='2018-10-01', arg_group='Automatic Repairs') as c:

        c.argument('enable_automatic_repairs', arg_type=get_three_state_flag(), help='Enable automatic repairs')
        c.argument(
            'automatic_repairs_grace_period',
            help='The amount of time (in minutes, between 30 and 90) for which automatic repairs are suspended due to a state change on VM.'
        )
        c.argument('automatic_repairs_action', arg_type=get_enum_type(['Replace', 'Restart', 'Reimage']), min_api='2021-11-01', help='Type of repair action that will be used for repairing unhealthy virtual machines in the scale set.')

    for scope in ['vmss create', 'vmss update']:
        with self.argument_context(scope) as c:
            c.argument('terminate_notification_time', min_api='2019-03-01',
                       help='Length of time (in minutes, between 5 and 15) a notification to be sent to the VM on the instance metadata server till the VM gets deleted')
            c.argument('max_batch_instance_percent', type=int, min_api='2020-12-01',
                       help='The maximum percent of total virtual machine instances that will be upgraded simultaneously by the rolling upgrade in one batch. Default: 20%')
            c.argument('max_unhealthy_instance_percent', type=int, min_api='2020-12-01',
                       help='The maximum percentage of the total virtual machine instances in the scale set that can be simultaneously unhealthy. Default: 20%')
            c.argument('max_unhealthy_upgraded_instance_percent', type=int, min_api='2020-12-01',
                       help='The maximum percentage of upgraded virtual machine instances that can be found to be in an unhealthy state. Default: 20%')
            c.argument('pause_time_between_batches', min_api='2020-12-01',
                       help='The wait time between completing the update for all virtual machines in one batch and starting the next batch. Default: 0 seconds')
            c.argument('enable_cross_zone_upgrade', arg_type=get_three_state_flag(), min_api='2020-12-01',
                       help='Set this Boolean property will allow VMSS to ignore AZ boundaries when constructing upgrade batches, and only consider Update Domain and maxBatchInstancePercent to determine the batch size')
            c.argument('prioritize_unhealthy_instances', arg_type=get_three_state_flag(), min_api='2020-12-01',
                       help='Set this Boolean property will lead to all unhealthy instances in a scale set getting upgraded before any healthy instances')

    for scope, help_prefix in [('vmss update', 'Update the'), ('vmss wait', 'Wait on the')]:
        with self.argument_context(scope) as c:
            c.argument('instance_id', id_part='child_name_1', help="{0} VM instance with this ID. If missing, {0} VMSS.".format(help_prefix))

    for scope in ['vmss update-instances', 'vmss delete-instances']:
        with self.argument_context(scope) as c:
            c.argument('instance_ids', multi_ids_type, help='Space-separated list of IDs (ex: 1 2 3 ...) or * for all instances.')

    with self.argument_context('vmss diagnostics') as c:
        c.argument('vmss_name', id_part=None, help='Scale set name')

    with self.argument_context('vmss disk') as c:
        options_list = ['--vmss-name'] + [c.deprecate(target=opt, redirect='--vmss-name', hide=True)for opt in name_arg_type.settings['options_list']]
        new_vmss_name_type = CLIArgumentType(overrides=vmss_name_type, options_list=options_list)

        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine instance size.')
        c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB. Max size: 4095 GB (certain preview disks can be larger).', type=int)
        c.argument('vmss_name', new_vmss_name_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))
        c.argument('disk', validator=validate_vmss_disk, help='existing disk name or ID to attach or detach from VM instances',
                   min_api='2017-12-01', completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
        c.argument('instance_id', help='Scale set VM instance id', min_api='2017-12-01')
        c.argument('sku', arg_type=disk_sku, help='Underlying storage SKU')

    with self.argument_context('vmss encryption') as c:
        c.argument('vmss_name', vmss_name_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))

    with self.argument_context('vmss extension') as c:
        c.argument('extension_name', name_arg_type, help='Name of the extension.')
        c.argument('vmss_name', vmss_name_type, options_list=['--vmss-name'], id_part=None)

    with self.argument_context('vmss nic') as c:
        c.argument('virtual_machine_scale_set_name', options_list=['--vmss-name'], help='Scale set name.', completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')
        c.argument('virtualmachine_index', options_list=['--instance-id'], id_part='child_name_1')
        c.argument('network_interface_name', options_list=['--name', '-n'], metavar='NIC_NAME', help='The network interface (NIC).', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'), id_part='child_name_2')

    with self.argument_context('vmss nic list') as c:
        c.argument('virtual_machine_scale_set_name', arg_type=vmss_name_type, options_list=['--vmss-name'], id_part=None)

    with self.argument_context('vmss set-orchestration-service-state') as c:
        c.argument('service_name', arg_type=get_enum_type(OrchestrationServiceNames), help='The name of the orchestration service.')
        c.argument('action', arg_type=get_enum_type(OrchestrationServiceStateAction), help='The action to be performed.')
    # endregion

    # region VM & VMSS Shared
    for scope in ['vm', 'vmss']:
        with self.argument_context(scope) as c:
            c.argument('no_auto_upgrade',
                       options_list=['--no-auto-upgrade-minor-version', c.deprecate(target='--no-auto-upgrade', redirect='--no-auto-upgrade-minor-version')],
                       arg_type=get_three_state_flag(),
                       help='If set, the extension service will not automatically pick or upgrade to the latest minor version, even if the extension is redeployed.')

        with self.argument_context('{} run-command'.format(scope)) as c:
            c.argument('command_id', completer=get_vm_run_command_completion_list, help="The command id. Use 'az {} run-command list' to get the list".format(scope))
            if scope == 'vmss':
                c.argument('vmss_name', vmss_name_type)

        with self.argument_context('{} run-command invoke'.format(scope)) as c:
            c.argument('parameters', nargs='+', help="space-separated parameters in the format of '[name=]value'")
            c.argument('scripts', nargs='+', help="Space-separated script lines. Use @{file} to load script from a file")

        with self.argument_context('{} stop'.format(scope)) as c:
            c.argument('skip_shutdown', action='store_true', help='Skip shutdown and power-off immediately.', min_api='2019-03-01')

    run_cmd_name_type = CLIArgumentType(options_list=['--name', '--run-command-name'], help='The name of the virtual machine run command.')
    run_cmd_vm_name = CLIArgumentType(options_list=['--vm-name'], help='The name of the virtual machine')
    for scope in ['create', 'update']:
        with self.argument_context('vm run-command {}'.format(scope)) as c:
            c.argument('vm_name', run_cmd_vm_name)
            c.argument('run_command_name', run_cmd_name_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                       validator=get_default_location_from_resource_group)
            c.argument('tags', tags_type)
            c.argument('script', help='Contain the powershell or bash script to execute on the VM.')
            c.argument('script_uri', help='Contain a uri to the script to execute on the VM. Uri can be any link accessible from the VM or a storage blob without SAS. If subscription has access to the storage blob, then SAS will be auto-generated. ')
            c.argument('command_id', help='Specify a command id of predefined script. All command ids can be listed using "list" command.')
            c.argument('parameters', nargs='+', help='Set custom parameters in a name-value pair.')
            c.argument('protected_parameters', nargs='+', help='Set custom parameters in a name-value pair. These parameters will be encrypted during transmission and will not be logged.')
            c.argument('async_execution', arg_type=get_three_state_flag(), help='Optional. If set to true, provisioning '
                       'will complete as soon as the script starts and will not wait for script to complete.')
            c.argument('run_as_user', help='By default script process runs under system/root user. Specify custom user to host the process.')
            c.argument('run_as_password', help='Password if needed for using run-as-user parameter. It will be encrypted and not logged. ')
            c.argument('timeout_in_seconds', type=int, help='The timeout in seconds to execute the run command.')
            c.argument('output_blob_uri', help='Specify the Azure storage blob where script output stream will be uploaded.')
            c.argument('error_blob_uri', help='Specify the Azure storage blob where script error stream will be uploaded.')

    with self.argument_context('vm run-command delete') as c:
        c.argument('vm_name', run_cmd_vm_name)
        c.argument('run_command_name', run_cmd_name_type)

    with self.argument_context('vm run-command list') as c:
        c.argument('vm_name', run_cmd_vm_name, id_part=None)
        c.argument('expand', help='The expand expression to apply on the operation.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))

    with self.argument_context('vm run-command show') as c:
        c.argument('vm_name', run_cmd_vm_name)
        c.argument('run_command_name', run_cmd_name_type)
        c.argument('expand', help='The expand expression to apply on the operation.', deprecate_info=c.deprecate(hide=True))
        c.argument('instance_view', action='store_true', help='The instance view of a run command.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('command_id', help='The command id.')

    with self.argument_context('vm run-command wait') as c:
        c.argument('vm_name', run_cmd_vm_name)
        c.argument('run_command_name', run_cmd_name_type)
        c.argument('expand', help='The expand expression to apply on the operation.', deprecate_info=c.deprecate(hide=True))
        c.argument('instance_view', action='store_true', help='The instance view of a run command.')
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('command_id', help='The command id.')

    run_cmd_vmss_name = CLIArgumentType(options_list=['--vmss-name'], help='The name of the VM scale set.')
    for scope in ['create', 'update']:
        with self.argument_context('vmss run-command {}'.format(scope)) as c:
            c.argument('vmss_name', run_cmd_vmss_name)
            c.argument('instance_id', help='The instance ID of the virtual machine.')
            c.argument('run_command_name', run_cmd_name_type)
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                       validator=get_default_location_from_resource_group)
            c.argument('tags', tags_type)
            c.argument('script', help='Contain the powershell or bash script to execute on the VM.')
            c.argument('script_uri',
                       help='Contain a uri to the script to execute on the VM. Uri can be any link accessible from the VM or a storage blob without SAS. If subscription has access to the storage blob, then SAS will be auto-generated. ')
            c.argument('command_id',
                       help='Specify a command id of predefined script. All command ids can be listed using "list" command.')
            c.argument('parameters', nargs='+', help='Set custom parameters in a name-value pair.')
            c.argument('protected_parameters', nargs='+',
                       help='Set custom parameters in a name-value pair. These parameters will be encrypted during transmission and will not be logged.')
            c.argument('async_execution', arg_type=get_three_state_flag(), help='Optional. If set to true, provisioning '
                                                                                'will complete as soon as the script starts and will not wait for script to complete.')
            c.argument('run_as_user',
                       help='By default script process runs under system/root user. Specify custom user to host the process.')
            c.argument('run_as_password',
                       help='Password if needed for using run-as-user parameter. It will be encrypted and not logged. ')
            c.argument('timeout_in_seconds', type=int, help='The timeout in seconds to execute the run command.')
            c.argument('output_blob_uri', help='Uri (without SAS) to an append blob where the script output will be uploaded.')
            c.argument('error_blob_uri', help='Uri (without SAS) to an append blob where the script error stream will be uploaded.')

    with self.argument_context('vmss run-command delete') as c:
        c.argument('vmss_name', run_cmd_vmss_name)
        c.argument('instance_id', help='The instance ID of the virtual machine.')
        c.argument('run_command_name', run_cmd_name_type)

    with self.argument_context('vmss run-command list') as c:
        c.argument('vmss_name', run_cmd_vmss_name, id_part=None)
        c.argument('instance_id', help='The instance ID of the virtual machine.')
        c.argument('expand', help='The expand expression to apply on the operation.')

    with self.argument_context('vmss run-command show') as c:
        c.argument('vmss_name', run_cmd_vmss_name)
        c.argument('instance_id', help='The instance ID of the virtual machine.')
        c.argument('run_command_name', run_cmd_name_type)
        c.argument('expand', help='The expand expression to apply on the operation.', deprecate_info=c.deprecate(hide=True))
        c.argument('instance_view', action='store_true', help='The instance view of a run command.')

    for scope in ['vm identity assign', 'vmss identity assign']:
        with self.argument_context(scope) as c:
            c.argument('assign_identity', options_list=['--identities'], nargs='*', help="Space-separated identities to assign. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm identity remove', 'vmss identity remove']:
        with self.argument_context(scope) as c:
            c.argument('identities', nargs='+', help="Space-separated identities to remove. Use '{0}' to refer to the system assigned identity. Default: '{0}'".format(MSI_LOCAL_ID))
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm identity show', 'vmss identity show']:
        with self.argument_context(scope) as c:
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm application set', 'vmss application set']:
        with self.argument_context(scope) as c:
            c.argument('vm', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)
            c.argument('application_version_ids', options_list=['--app-version-ids'], nargs='*', help="Space-separated application version ids to set to VM.")
            c.argument('order_applications', action='store_true', help='Whether set order index at each gallery applications, the order index starts from 1.')
            c.argument('application_configuration_overrides', options_list=['--app-config-overrides'], nargs='*',
                       help='Space-separated application configuration overrides for each application version ids. '
                       'It should have the same number of items as the application version ids. Null is available for a application '
                       'which does not have a configuration override.')

    for scope in ['vm application list', 'vmss application list']:
        with self.argument_context(scope) as c:
            c.argument('vm_name', options_list=['--vm-name', '--name', '-n'], arg_type=existing_vm_name, id_part=None)
            c.argument('vmss_name', vmss_name_type, id_part=None)

    for scope in ['vm create', 'vmss create']:
        with self.argument_context(scope) as c:
            c.argument('location', get_location_type(self.cli_ctx), help='Location in which to create VM and related resources. If default location is not configured, will default to the resource group\'s location')
            c.argument('tags', tags_type)
            c.argument('no_wait', help='Do not wait for the long-running operation to finish.')
            c.argument('validate', options_list=['--validate'], help='Generate and validate the ARM template without creating any resources.', action='store_true')
            c.argument('size', help='The VM size to be created. See https://azure.microsoft.com/pricing/details/virtual-machines/ for size info.')
            c.argument('image', completer=get_urn_aliases_completion_list)
            c.argument('custom_data', help='Custom init script file or text (cloud-init, cloud-config, etc..)', completer=FilesCompleter(), type=file_type)
            c.argument('secrets', multi_ids_type, help='One or many Key Vault secrets as JSON strings or files via `@{path}` containing `[{ "sourceVault": { "id": "value" }, "vaultCertificates": [{ "certificateUrl": "value", "certificateStore": "cert store name (only on windows)"}] }]`', type=file_type, completer=FilesCompleter())
            c.argument('assign_identity', nargs='*', arg_group='Managed Service Identity', help="accept system or user assigned identities separated by spaces. Use '[system]' to refer system assigned identity, or a resource id to refer user assigned identity. Check out help for more examples")
            c.ignore('aux_subscriptions')
            c.argument('edge_zone', edge_zone_type)

        with self.argument_context(scope, arg_group='Authentication') as c:
            c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory')
            c.argument('admin_username', help='Username for the VM. Default value is current username of OS. If the default value is system reserved, then default value will be set to azureuser. Please refer to https://docs.microsoft.com/rest/api/compute/virtualmachines/createorupdate#osprofile to get a full list of reserved values.')
            c.argument('admin_password', help="Password for the VM if authentication type is 'Password'.")
            c.argument('ssh_key_value', options_list=['--ssh-key-values'], completer=FilesCompleter(), type=file_type, nargs='+')
            c.argument('ssh_dest_key_path', help='Destination file path on the VM for the SSH key. If the file already exists, the specified key(s) are appended to the file. Destination path for SSH public keys is currently limited to its default value "/home/username/.ssh/authorized_keys" due to a known issue in Linux provisioning agent.')
            c.argument('authentication_type', help='Type of authentication to use with the VM. Defaults to password for Windows and SSH public key for Linux. "all" enables both ssh and password authentication. ', arg_type=get_enum_type(['ssh', 'password', 'all']))

        with self.argument_context(scope, arg_group='Storage') as c:
            if DiskStorageAccountTypes:
                allowed_values = ", ".join([sku.value for sku in DiskStorageAccountTypes])
            else:
                allowed_values = ", ".join(['Premium_LRS', 'Standard_LRS'])

            usage = 'Usage: [--storage-sku SKU | --storage-sku ID=SKU ID=SKU ID=SKU...], where each ID is "os" or a 0-indexed lun.'
            allowed_values = 'Allowed values: {}.'.format(allowed_values)
            storage_sku_help = 'The SKU of the storage account with which to persist VM. Use a singular sku that would be applied across all disks, ' \
                               'or specify individual disks. {} {}'.format(usage, allowed_values)

            c.argument('os_disk_name', help='The name of the new VM OS disk.')
            c.argument('os_type', help='Type of OS installed on a custom VHD. Do not use when specifying an URN or URN alias.', arg_type=get_enum_type(['windows', 'linux']))
            c.argument('storage_account', help="Only applicable when used with `--use-unmanaged-disk`. The name to use when creating a new storage account or referencing an existing one. If omitted, an appropriate storage account in the same resource group and location will be used, or a new one will be created.")
            c.argument('storage_sku', nargs='+', help=storage_sku_help)
            c.argument('storage_container_name', help="Only applicable when used with `--use-unmanaged-disk`. Name of the storage container for the VM OS disk. Default: vhds")
            c.ignore('os_publisher', 'os_offer', 'os_sku', 'os_version', 'storage_profile')
            c.argument('use_unmanaged_disk', action='store_true', help='Do not use managed disk to persist VM')
            c.argument('os_disk_size_gb', type=int, help='OS disk size in GB to create.')
            c.argument('data_disk_sizes_gb', nargs='+', type=int, help='space-separated empty managed data disk sizes in GB to create')
            c.ignore('disk_info', 'storage_account_type', 'public_ip_address_type', 'nsg_type', 'nic_type', 'vnet_type', 'load_balancer_type', 'app_gateway_type')
            c.argument('os_caching', options_list=[self.deprecate(target='--storage-caching', redirect='--os-disk-caching', hide=True), '--os-disk-caching'], help='Storage caching type for the VM OS disk. Default: ReadWrite', arg_type=get_enum_type(CachingTypes))
            c.argument('data_caching', options_list=['--data-disk-caching'], nargs='+',
                       help="storage caching type for data disk(s), including 'None', 'ReadOnly', 'ReadWrite', etc. Use a singular value to apply on all disks, or use `<lun>=<vaule1> <lun>=<value2>` to configure individual disk")
            c.argument('ultra_ssd_enabled', ultra_ssd_enabled_type)
            c.argument('ephemeral_os_disk', arg_type=get_three_state_flag(), min_api='2018-06-01',
                       help='Allows you to create an OS disk directly on the host node, providing local disk performance and faster VM/VMSS reimage time.', is_preview=True)
            c.argument('ephemeral_os_disk_placement', arg_type=ephemeral_placement_type,
                       help='Only applicable when used with `--ephemeral-os-disk`. Allows you to choose the Ephemeral OS disk provisioning location.', is_preview=True)
            c.argument('os_disk_encryption_set', min_api='2019-07-01', help='Name or ID of disk encryption set for OS disk.')
            c.argument('data_disk_encryption_sets', nargs='+', min_api='2019-07-01',
                       help='Names or IDs (space delimited) of disk encryption sets for data disks.')
            c.argument('data_disk_iops', min_api='2019-07-01', nargs='+', type=int, help='Specify the Read-Write IOPS (space delimited) for the managed disk. Should be used only when StorageAccountType is UltraSSD_LRS. If not specified, a default value would be assigned based on diskSizeGB.')
            c.argument('data_disk_mbps', min_api='2019-07-01', nargs='+', type=int, help='Specify the bandwidth in MB per second (space delimited) for the managed disk. Should be used only when StorageAccountType is UltraSSD_LRS. If not specified, a default value would be assigned based on diskSizeGB.')
            c.argument('specialized', arg_type=get_three_state_flag(), help='Indicate whether the source image is specialized.')
            c.argument('encryption_at_host', arg_type=get_three_state_flag(), help='Enable Host Encryption for the VM or VMSS. This will enable the encryption for all the disks including Resource/Temp disk at host itself.')
            c.argument('os_disk_delete_option', arg_type=get_enum_type(self.get_models('DiskDeleteOptionTypes')), min_api='2021-03-01',
                       help='Specify the behavior of the managed disk when the VM gets deleted i.e whether the managed disk is deleted or detached.')
            c.argument('data_disk_delete_option', options_list=['--data-disk-delete-option', self.deprecate(target='--data-delete-option', redirect='--data-disk-delete-option', hide=True)],
                       nargs='+', min_api='2021-03-01',
                       help='Specify whether data disk should be deleted or detached upon VM deletion.')

        with self.argument_context(scope, arg_group='Network') as c:
            c.argument('vnet_name', help='Name of the virtual network when creating a new one or referencing an existing one.')
            c.argument('vnet_address_prefix', help='The IP address prefix to use when creating a new VNet in CIDR format.')
            c.argument('subnet', help='The name of the subnet when creating a new VNet or referencing an existing one. Can also reference an existing subnet by ID. If both vnet-name and subnet are omitted, an appropriate VNet and subnet will be selected automatically, or a new one will be created.')
            c.argument('subnet_address_prefix', help='The subnet IP address prefix to use when creating a new VNet in CIDR format.')
            c.argument('nics', nargs='+', help='Names or IDs of existing NICs to attach to the VM. The first NIC will be designated as primary. If omitted, a new NIC will be created. If an existing NIC is specified, do not specify subnet, VNet, public IP or NSG.')
            c.argument('private_ip_address', help='Static private IP address (e.g. 10.0.0.5).')
            c.argument('public_ip_address', help='Name of the public IP address when creating one (default) or referencing an existing one. Can also reference an existing public IP by ID or specify "" for None (\'""\' in Azure CLI using PowerShell or --% operator).')
            c.argument('public_ip_address_allocation', help=None, default=None, arg_type=get_enum_type(['dynamic', 'static']))
            c.argument('public_ip_address_dns_name', help='Globally unique DNS name for a newly created public IP.')
            if self.supported_api_version(min_api='2017-08-01', resource_type=ResourceType.MGMT_NETWORK):
                PublicIPAddressSkuName = self.get_models('PublicIPAddressSkuName', resource_type=ResourceType.MGMT_NETWORK)
                c.argument('public_ip_sku', help='Public IP SKU. It is set to Basic by default. The public IP is supported to be created on edge zone only when it is \'Standard\'',
                           default=None, arg_type=get_enum_type(PublicIPAddressSkuName))
            c.argument('nic_delete_option', nargs='+', min_api='2021-03-01',
                       help='Specify what happens to the network interface when the VM is deleted. Use a singular '
                       'value to apply on all resources, or use <Name>=<Value> to configure '
                       'the delete behavior for individual resources. Possible options are Delete and Detach.')

        with self.argument_context(scope, arg_group='Marketplace Image Plan') as c:
            c.argument('plan_name', help='plan name')
            c.argument('plan_product', help='plan product')
            c.argument('plan_publisher', help='plan publisher')
            c.argument('plan_promotion_code', help='plan promotion code')

    for scope in ['vm create', 'vmss create', 'vm identity assign', 'vmss identity assign']:
        with self.argument_context(scope) as c:
            arg_group = 'Managed Service Identity' if scope.split()[-1] == 'create' else None
            c.argument('identity_scope', options_list=['--scope'], arg_group=arg_group, help="Scope that the system assigned identity can access")
            c.ignore('identity_role_id')

    for scope in ['vm create', 'vmss create']:
        with self.argument_context(scope) as c:
            c.argument('identity_role', options_list=['--role'], arg_group='Managed Service Identity',
                       help='Role name or id the system assigned identity will have. '
                            'Please note that the default value "Contributor" will be removed in the future version 2.35.0, '
                            "so please specify '--role' and '--scope' at the same time when assigning a role to the managed identity")

    for scope in ['vm identity assign', 'vmss identity assign']:
        with self.argument_context(scope) as c:
            c.argument('identity_role', options_list=['--role'], help="Role name or id the system assigned identity will have")

    with self.argument_context('vm auto-shutdown') as c:
        c.argument('off', action='store_true', help='Turn off auto-shutdown for VM. Configuration will be cleared.')
        c.argument('email', help='The email recipient to send notifications to (can be a list of semi-colon separated email addresses)')
        c.argument('time', help='The UTC time of day the schedule will occur every day. Format: hhmm. Example: 1730')
        c.argument('webhook', help='The webhook URL to which the notification will be sent')
        c.argument('location', validator=get_default_location_from_resource_group)

    for scope in ['vm diagnostics', 'vmss diagnostics']:
        with self.argument_context(scope) as c:
            c.argument('version', help='version of the diagnostics extension. Will use the latest if not specfied')
            c.argument('settings', help='json string or a file path, which defines data to be collected.', type=validate_file_or_dict, completer=FilesCompleter())
            c.argument('protected_settings', help='json string or a file path containing private configurations such as storage account keys, etc.', type=validate_file_or_dict, completer=FilesCompleter())
            c.argument('is_windows_os', action='store_true', help='for Windows VMs')

    for scope in ['vm encryption', 'vmss encryption']:
        with self.argument_context(scope) as c:
            c.argument('volume_type', help='Type of volume that the encryption operation is performed on', arg_type=get_enum_type(['DATA', 'OS', 'ALL']))
            c.argument('force', action='store_true', help='continue by ignoring client side validation errors')
            c.argument('disk_encryption_keyvault', help='Name or ID of the key vault where the generated encryption key will be placed.')
            c.argument('key_encryption_key', help='Key vault key name or URL used to encrypt the disk encryption key.')
            c.argument('key_encryption_keyvault', help='Name or ID of the key vault containing the key encryption key used to encrypt the disk encryption key. If missing, CLI will use `--disk-encryption-keyvault`.')

    for scope in ['vm extension', 'vmss extension']:
        with self.argument_context(scope) as c:
            c.argument('publisher', help='The name of the extension publisher.')
            c.argument('settings', type=validate_file_or_dict, help='Extension settings in JSON format. A JSON file path is also accepted.')
            c.argument('protected_settings', type=validate_file_or_dict, help='Protected settings in JSON format for sensitive information like credentials. A JSON file path is also accepted.')
            c.argument('version', help='The version of the extension. To pin extension version to this value, please specify --no-auto-upgrade-minor-version.')
            c.argument('enable_auto_upgrade', arg_type=get_three_state_flag(),
                       help='Indicate the extension should be automatically upgraded by the platform if there is a newer version of the extension available.')

    with self.argument_context('vm extension set') as c:
        c.argument('vm_extension_name', name_arg_type,
                   completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'),
                   help='Name of the extension.', id_part=None)
        c.argument('force_update', action='store_true', help='force to update even if the extension configuration has not changed.')
        c.argument('extension_instance_name', extension_instance_name_type)

    with self.argument_context('vmss extension set', min_api='2017-12-01') as c:
        c.argument('force_update', action='store_true', help='force to update even if the extension configuration has not changed.')
        c.argument('extension_instance_name', extension_instance_name_type)
        c.argument('provision_after_extensions', nargs='+', help='Space-separated list of extension names after which this extension should be provisioned. These extensions must already be set on the vm.')

    for scope in ['vm extension image', 'vmss extension image']:
        with self.argument_context(scope) as c:
            c.argument('image_location', options_list=['--location', '-l'], help='Image location.')
            c.argument('name', help='Image name', id_part=None)
            c.argument('publisher_name', options_list=['--publisher', '-p'], help='Image publisher name')
            c.argument('type', options_list=['--name', '-n'], help='Name of the extension')
            c.argument('latest', action='store_true', help='Show the latest version only.')
            c.argument('version', help='Extension version')
            c.argument('orderby', help="the $orderby odata query option")
            c.argument('top', help='the $top odata query option')

    for scope in ['vm create', 'vm update', 'vmss create', 'vmss update']:
        with self.argument_context(scope) as c:
            c.argument('license_type', license_type)
            c.argument('priority', resource_type=ResourceType.MGMT_COMPUTE, min_api='2019-03-01',
                       arg_type=get_enum_type(self.get_models('VirtualMachinePriorityTypes'), default=None),
                       help="Priority. Use 'Spot' to run short-lived workloads in a cost-effective way. 'Low' enum will be deprecated in the future. Please use 'Spot' to deploy Azure spot VM and/or VMSS. Default to Regular.")
            c.argument('max_price', min_api='2019-03-01', type=float, is_preview=True,
                       help='The maximum price (in US Dollars) you are willing to pay for a Spot VM/VMSS. -1 indicates that the Spot VM/VMSS should not be evicted for price reasons')
            c.argument('capacity_reservation_group', options_list=['--capacity-reservation-group', '--crg'],
                       help='The ID or name of the capacity reservation group that is used to allocate. Pass in "None" to disassociate the capacity reservation group. Please note that if you want to delete a VM/VMSS that has been associated with capacity reservation group, you need to disassociate the capacity reservation group first.',
                       min_api='2021-04-01', is_preview=True)
            c.argument('v_cpus_available', type=int, min_api='2021-11-01', help='Specify the number of vCPUs available')
            c.argument('v_cpus_per_core', type=int, min_api='2021-11-01', help='Specify the ratio of vCPU to physical core. Setting this property to 1 also means that hyper-threading is disabled.')

    with self.argument_context('vm update') as c:
        c.argument('license_type', license_type)
        c.argument('user_data', help='UserData for the VM. It can be passed in as file or string. If empty string is passed in, the existing value will be deleted.', completer=FilesCompleter(), type=file_type, min_api='2021-03-01')

    with self.argument_context('vmss create') as c:
        c.argument('priority', resource_type=ResourceType.MGMT_COMPUTE, min_api='2017-12-01',
                   arg_type=get_enum_type(self.get_models('VirtualMachinePriorityTypes'), default=None),
                   help="Priority. Use 'Spot' to run short-lived workloads in a cost-effective way. 'Low' enum will be deprecated in the future. Please use 'Spot' to deploy Azure spot VM and/or VMSS. Default to Regular.")

    with self.argument_context('sig') as c:
        c.argument('gallery_name', options_list=['--gallery-name', '-r'], help='gallery name')
        c.argument('gallery_image_name', options_list=['--gallery-image-definition', '-i'], help='gallery image definition')
        c.argument('gallery_image_version', options_list=['--gallery-image-version', '-e'], help='gallery image version')

    for scope in ['sig show', 'sig image-definition show', 'sig image-definition delete']:
        with self.argument_context(scope) as c:
            c.argument('gallery_name', options_list=['--gallery-name', '-r'], id_part='name', help='gallery name')
            c.argument('gallery_image_name', options_list=['--gallery-image-definition', '-i'], id_part='child_name_1', help='gallery image definition')

    with self.argument_context('sig list-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx))
        c.argument('shared_to', shared_to_type)

    with self.argument_context('sig show-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), id_part='name')
        c.argument('gallery_unique_name', type=str, help='The unique name of the Shared Gallery.',
                   id_part='child_name_1')

    for scope in ['sig share add', 'sig share remove']:
        with self.argument_context(scope) as c:
            c.argument('gallery_name', type=str, help='The name of the Shared Image Gallery.', id_part='name')
            c.argument('subscription_ids', nargs='+', help='A list of subscription ids to share the gallery.')
            c.argument('tenant_ids', nargs='+', help='A list of tenant ids to share the gallery.')

    with self.argument_context('sig share add') as c:
        c.argument('op_type', default='Add', deprecate_info=c.deprecate(hide=True),
                   help='distinguish add operation and remove operation')

    with self.argument_context('sig share remove') as c:
        c.argument('op_type', default='Remove', deprecate_info=c.deprecate(hide=True),
                   help='distinguish add operation and remove operation')

    with self.argument_context('sig share reset') as c:
        c.argument('gallery_name', type=str, help='The name of the Shared Image Gallery.', id_part='name')

    with self.argument_context('sig image-definition create') as c:
        c.argument('offer', options_list=['--offer', '-f'], help='image offer')
        c.argument('sku', options_list=['--sku', '-s'], help='image sku')
        c.argument('publisher', options_list=['--publisher', '-p'], help='image publisher')
        c.argument('os_type', arg_type=get_enum_type(['Windows', 'Linux']), help='the type of the OS that is included in the disk if creating a VM from user-image or a specialized VHD')
        c.argument('os_state', arg_type=get_enum_type(self.get_models('OperatingSystemStateTypes')), help="This property allows the user to specify whether the virtual machines created under this image are 'Generalized' or 'Specialized'.")
        c.argument('hyper_v_generation', arg_type=get_enum_type(self.get_models('HyperVGenerationTypes')), help='The hypervisor generation of the Virtual Machine. Applicable to OS disks only.')
        c.argument('minimum_cpu_core', type=int, arg_group='Recommendation', help='minimum cpu cores')
        c.argument('maximum_cpu_core', type=int, arg_group='Recommendation', help='maximum cpu cores')
        c.argument('minimum_memory', type=int, arg_group='Recommendation', help='minimum memory in MB')
        c.argument('maximum_memory', type=int, arg_group='Recommendation', help='maximum memory in MB')

        c.argument('plan_publisher', help='plan publisher', arg_group='Purchase plan')
        c.argument('plan_name', help='plan name', arg_group='Purchase plan')
        c.argument('plan_product', help='plan product', arg_group='Purchase plan')

        c.argument('eula', help='The Eula agreement for the gallery image')
        c.argument('privacy_statement_uri', help='The privacy statement uri')
        c.argument('release_note_uri', help='The release note uri')
        c.argument('end_of_life_date', help="the end of life date, e.g. '2020-12-31'")
        c.argument('disallowed_disk_types', nargs='*', help='disk types which would not work with the image, e.g., Standard_LRS')
        c.argument('features', help='A list of gallery image features. E.g. "IsSecureBootSupported=true IsMeasuredBootSupported=false"')

    with self.argument_context('sig image-definition list-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), id_part='name')
        c.argument('gallery_unique_name', type=str, help='The unique name of the Shared Gallery.',
                   id_part='child_name_1')
        c.argument('shared_to', shared_to_type)
        c.argument('marker', arg_type=marker_type)
        c.argument('show_next_marker', action='store_true', help='Show nextMarker in result when specified.')

    with self.argument_context('sig image-definition show-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), id_part='name')
        c.argument('gallery_unique_name', type=str, help='The unique name of the Shared Gallery.',
                   id_part='child_name_1')
        c.argument('gallery_image_name', options_list=['--gallery-image-definition', '-i'], type=str, help='The name '
                   'of the Shared Gallery Image Definition from which the Image Versions are to be listed.',
                   id_part='child_name_2')

    with self.argument_context('sig create') as c:
        c.argument('description', help='the description of the gallery')
        c.argument('permissions', arg_type=get_enum_type(GallerySharingPermissionTypes), arg_group='Sharing Profile',
                   min_api='2020-09-30', is_experimental=True,
                   help='This property allows you to specify the permission of sharing gallery.')
        c.argument('soft_delete', arg_type=get_three_state_flag(), min_api='2021-03-01', is_preview=True,
                   help='Enable soft-deletion for resources in this gallery, '
                        'allowing them to be recovered within retention time.')
    with self.argument_context('sig update') as c:
        c.ignore('gallery')
        c.argument('permissions', arg_type=get_enum_type(GallerySharingPermissionTypes), arg_group='Sharing Profile',
                   min_api='2020-09-30', is_experimental=True,
                   help='This property allows you to specify the permission of sharing gallery.')
        c.argument('soft_delete', arg_type=get_three_state_flag(), min_api='2021-03-01', is_preview=True,
                   help='Enable soft-deletion for resources in this gallery, '
                        'allowing them to be recovered within retention time.')
    with self.argument_context('sig image-definition create') as c:
        c.argument('description', help='the description of the gallery image definition')
    with self.argument_context('sig image-definition update') as c:
        c.ignore('gallery_image')

    with self.argument_context('sig image-version') as c:
        deprecated_option = c.deprecate(target='--gallery-image-version-name', redirect='--gallery-image-version', hide=True, expiration="3.0.0")
        c.argument('gallery_image_version_name', options_list=['--gallery-image-version', '-e', deprecated_option],
                   help='Gallery image version in semantic version pattern. The allowed characters are digit and period. Digits must be within the range of a 32-bit integer, e.g. `<MajorVersion>.<MinorVersion>.<Patch>`')

    with self.argument_context('sig image-version create', resource_type=ResourceType.MGMT_COMPUTE, operation_group='gallery_image_versions') as c:
        c.argument('gallery_image_version', options_list=['--gallery-image-version', '-e'],
                   help='Gallery image version in semantic version pattern. The allowed characters are digit and period. Digits must be within the range of a 32-bit integer, e.g. `<MajorVersion>.<MinorVersion>.<Patch>`')
        c.argument('description', help='the description of the gallery image version')
        c.argument('managed_image', help='image name(if in the same resource group) or resource id')
        c.argument('os_snapshot', help='Name or ID of OS disk snapshot')
        c.argument('data_snapshots', nargs='+', help='Names or IDs (space-delimited) of data disk snapshots')
        c.argument('data_snapshot_luns', nargs='+', help='Logical unit numbers (space-delimited) of data disk snapshots')
        c.argument('exclude_from_latest', arg_type=get_three_state_flag(), help='The flag means that if it is set to true, people deploying VMs with version omitted will not use this version.')
        c.argument('version', help='image version')
        c.argument('end_of_life_date', help="the end of life date, e.g. '2020-12-31'")
        c.argument('storage_account_type', help="The default storage account type to be used per region. To set regional storage account types, use --target-regions",
                   arg_type=get_enum_type(["Standard_LRS", "Standard_ZRS", "Premium_LRS"]), min_api='2019-03-01')
        c.argument('target_region_encryption', nargs='+',
                   help='Space-separated list of customer managed keys for encrypting the OS and data disks in the gallery artifact for each region. Format for each region: `<os_des>,<lun1>,<lun1_des>,<lun2>,<lun2_des>`. Use "null" as a placeholder.')
        c.argument('os_vhd_uri', help='Source VHD URI of OS disk')
        c.argument('os_vhd_storage_account', help='Name or ID of storage account of source VHD URI of OS disk')
        c.argument('data_vhds_uris', nargs='+', help='Source VHD URIs (space-delimited) of data disks')
        c.argument('data_vhds_luns', nargs='+', help='Logical unit numbers (space-delimited) of source VHD URIs of data disks')
        c.argument('data_vhds_storage_accounts', options_list=['--data-vhds-storage-accounts', '--data-vhds-sa'], nargs='+', help='Names or IDs (space-delimited) of storage accounts of source VHD URIs of data disks')
        c.argument('replication_mode', min_api='2021-07-01', arg_type=get_enum_type(ReplicationMode), help='Optional parameter which specifies the mode to be used for replication. This property is not updatable.')

    with self.argument_context('sig image-version list-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), id_part='name')
        c.argument('gallery_unique_name', type=str, help='The unique name of the Shared Gallery.',
                   id_part='child_name_1')
        c.argument('gallery_image_name', options_list=['--gallery-image-definition', '-i'], type=str, help='The name '
                   'of the Shared Gallery Image Definition from which the Image Versions are to be listed.',
                   id_part='child_name_2')
        c.argument('shared_to', shared_to_type)
        c.argument('marker', arg_type=marker_type)
        c.argument('show_next_marker', action='store_true', help='Show nextMarker in result when specified.')

    with self.argument_context('sig image-version show') as c:
        c.argument('expand', help="The expand expression to apply on the operation, e.g. 'ReplicationStatus'")

    with self.argument_context('sig image-version show-shared') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), id_part='name')
        c.argument('gallery_unique_name', type=str, help='The unique name of the Shared Gallery.',
                   id_part='child_name_1')
        c.argument('gallery_image_name', options_list=['--gallery-image-definition', '-i'], type=str, help='The name '
                   'of the Shared Gallery Image Definition from which the Image Versions are to be listed.',
                   id_part='child_name_2')
        c.argument('gallery_image_version_name', options_list=['--gallery-image-version', '-e'], type=str, help='The '
                   'name of the gallery image version to be created. Needs to follow semantic version name pattern: '
                   'The allowed characters are digit and period. Digits must be within the range of a 32-bit integer. '
                   'Format: <MajorVersion>.<MinorVersion>.<Patch>', id_part='child_name_3')

    for scope in ['sig image-version create', 'sig image-version update']:
        with self.argument_context(scope) as c:
            c.argument('target_regions', nargs='*', validator=process_gallery_image_version_namespace,
                       help='Space-separated list of regions and their replica counts. Use `<region>[=<replica count>][=<storage account type>]` to optionally set the replica count and/or storage account type for each region. '
                            'If a replica count is not specified, the default replica count will be used. If a storage account type is not specified, the default storage account type will be used')
            c.argument('replica_count', help='The default number of replicas to be created per region. To set regional replication counts, use --target-regions', type=int)
    # endregion

    # region Gallery applications
    with self.argument_context('sig gallery-application') as c:
        c.argument('gallery_application_name', options_list=['--name', '-n', '--application-name'],
                   help='The name of the gallery Application')

    with self.argument_context('sig gallery-application create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                   validator=get_default_location_from_resource_group)
        c.argument('description', help='The description of this gallery Application Definition resource. '
                   'This property is updatable.')
        c.argument('os_type', arg_type=get_enum_type(['Windows', 'Linux']), help='This property allows you '
                   'to specify the supported type of the OS that application is built for. <br><br> Possible values '
                   'are: <br><br> **Windows** <br><br> **Linux**')

    with self.argument_context('sig gallery-application update') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                   validator=get_default_location_from_resource_group)
        c.argument('description', help='The description of this gallery Application Definition resource. '
                   'This property is updatable.')

    with self.argument_context('sig gallery-application version') as c:
        c.argument('gallery_application_name', options_list=['--application-name'],
                   help='The name of the gallery Application')
        c.argument('gallery_application_version_name', options_list=['--name', '-n', '--version-name'],
                   help='The name of the gallery Application Version')

    for scope in ['create', 'update']:
        with self.argument_context('sig gallery-application version {}'.format(scope)) as c:
            c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                       validator=get_default_location_from_resource_group)
            c.argument('tags', tags_type)
            c.argument('package_file_link', help='The mediaLink of the artifact, must be a readable storage page blob.')
            c.argument('install_command', help='The path and arguments to install the gallery application.')
            c.argument('remove_command', help='The path and arguments to remove the gallery application.')
            c.argument('update_command', help='The path and arguments to update the gallery application. If not present,'
                                              ' then update operation will invoke remove command on the previous version '
                                              'and install command on the current version of the gallery application.')
            c.argument('target_regions', type=validate_file_or_dict, help='The target regions where the Image Version is '
                       'going to be replicated to. This property is updatable. Expected value: '
                       'json-string/json-file/@json-file.')
            c.argument('default_file_link', help='The default configuration link of the artifact, must be a readable storage page blob.')
            c.argument('exclude_from', arg_type=get_three_state_flag(), help='If set to true, Virtual Machines '
                       'deployed from the latest version of the Image Definition won\'t use this Image Version.',
                       arg_group='Publishing Profile')
            c.argument('end_of_life_date', help='The end of life date of the gallery image version. This property can be '
                       'used for decommissioning purposes. This property is updatable.', arg_group='Publishing Profile')
    # endregion

    # region Proximity Placement Group
    with self.argument_context('ppg', min_api='2018-04-01') as c:
        c.argument('proximity_placement_group_name', arg_type=name_arg_type, help="The name of the proximity placement group.")

    with self.argument_context('ppg create', min_api='2018-04-01') as c:
        c.argument('ppg_type', options_list=['--type', '-t'], help="The type of the proximity placement group. Allowed values: Standard.")
        c.argument('tags', tags_type)

    with self.argument_context('ppg show', min_api='2019-07-01') as c:
        c.argument('include_colocation_status', action='store_true', help='Enable fetching the colocation status of all the resources in the proximity placement group.')

    for scope, item in [('vm create', 'VM'), ('vmss create', 'VMSS'),
                        ('vm availability-set create', 'availability set'),
                        ('vm update', 'VM'), ('vmss update', 'VMSS'),
                        ('vm availability-set update', 'availability set')]:
        with self.argument_context(scope, min_api='2018-04-01') as c:
            c.argument('proximity_placement_group', options_list=['--ppg'], help="The name or ID of the proximity placement group the {} should be associated with.".format(item),
                       validator=_validate_proximity_placement_group)    # only availability set does not have a command level validator, so this should be added.
    # endregion

    # region VM Monitor
    with self.argument_context('vm monitor log show') as c:
        c.argument('analytics_query', options_list=['--analytics-query', '-q'], help="Query to execute over Log Analytics data.")
        c.argument('timespan', help="Timespan over which to query. Defaults to querying all available data.")

    with self.argument_context('vm monitor metrics') as c:
        c.argument('metricnamespace', options_list=['--namespace'],
                   help='Namespace to query metric definitions for.')

    with self.argument_context('vm monitor metrics tail') as c:
        from azure.mgmt.monitor.models import AggregationType
        c.extra('resource_group_name', required=True)
        c.argument('resource', arg_type=existing_vm_name, help='Name or ID of a virtual machine', validator=validate_vm_name_for_monitor_metrics, id_part=None)
        c.argument('metadata', action='store_true')
        c.argument('dimension', nargs='*', validator=validate_metric_dimension)
        c.argument('aggregation', arg_type=get_enum_type(t for t in AggregationType if t.name != 'none'), nargs='*')
        c.argument('metrics', nargs='*')
        c.argument('orderby',
                   help='Aggregation to use for sorting results and the direction of the sort. Only one order can be specificed. Examples: sum asc')
        c.argument('top', help='Max number of records to retrieve. Valid only if --filter used.')
        c.argument('filters', options_list=['--filter'])
        c.argument('metric_namespace', options_list=['--namespace'])

    with self.argument_context('vm monitor metrics tail', arg_group='Time') as c:
        c.argument('start_time', arg_type=get_datetime_type(help='Start time of the query.'))
        c.argument('end_time', arg_type=get_datetime_type(help='End time of the query. Defaults to the current time.'))
        c.argument('offset', type=get_period_type(as_timedelta=True))
        c.argument('interval', arg_group='Time', type=get_period_type())

    with self.argument_context('vm monitor metrics list-definitions') as c:
        c.extra('resource_group_name', required=True)
        c.argument('resource_uri', arg_type=existing_vm_name, help='Name or ID of a virtual machine', validator=validate_vm_name_for_monitor_metrics, id_part=None)
    # endregion

    # region disk encryption set
    with self.argument_context('disk-encryption-set') as c:
        c.argument('disk_encryption_set_name', disk_encryption_set_name)
        c.argument('key_url', help='URL pointing to a key or secret in KeyVault.')
        c.argument('source_vault', help='Name or ID of the KeyVault containing the key or secret.')
        c.argument('encryption_type', arg_type=get_enum_type(['EncryptionAtRestWithPlatformKey', 'EncryptionAtRestWithCustomerKey', 'EncryptionAtRestWithPlatformAndCustomerKeys']),
                   help='The type of key used to encrypt the data of the disk. EncryptionAtRestWithPlatformKey: Disk is encrypted at rest with Platform managed key. It is the default encryption type. EncryptionAtRestWithCustomerKey: Disk is encrypted at rest with Customer managed key that can be changed and revoked by a customer. EncryptionAtRestWithPlatformAndCustomerKeys: Disk is encrypted at rest with 2 layers of encryption. One of the keys is Customer managed and the other key is Platform managed.')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)
        c.argument('enable_auto_key_rotation', arg_type=get_three_state_flag(), min_api='2020-12-01',
                   options_list=['--enable-auto-key-rotation', '--auto-rotation'],
                   help='Enable automatic rotation of keys.')
    # endregion

    # region DiskAccess
    with self.argument_context('disk-access', resource_type=ResourceType.MGMT_COMPUTE, operation_group='disk_accesses') as c:
        c.argument('disk_access_name', arg_type=name_arg_type, help='Name of the disk access resource.', id_part='name')
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)
    # endRegion

    # region Capacity
    with self.argument_context('capacity reservation group') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('capacity_reservation_group_name', options_list=['--capacity-reservation-group', '-n'],
                   help='The name of the capacity reservation group.')
        c.argument('tags', tags_type)

    with self.argument_context('capacity reservation group create') as c:
        c.argument('zones', zones_type, help='Availability Zones to use for this capacity reservation group. If not provided, the group supports only regional resources in the region. If provided, enforces each capacity reservation in the group to be in one of the zones.')

    with self.argument_context('capacity reservation group show') as c:
        c.argument('instance_view', action='store_true', options_list=['--instance-view', '-i'], help='Retrieve the list of instance views of the capacity reservations under the capacity reservation group which is a snapshot of the runtime properties of a capacity reservation that is managed by the platform and can change outside of control plane operations.')

    with self.argument_context('capacity reservation group list') as c:
        c.argument('vm_instance', action='store_true', help='Retrieve the Virtual Machine Instance which are associated to capacity reservation group in the response.')
        c.argument('vmss_instance', action='store_true', help='Retrieve the ScaleSet VM Instance which are associated to capacity reservation group in the response.')

    with self.argument_context('capacity reservation') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), validator=get_default_location_from_resource_group)
        c.argument('capacity_reservation_group_name', options_list=['--capacity-reservation-group', '-c'],
                   help='The name of the capacity reservation group.')
        c.argument('capacity_reservation_name', options_list=['--capacity-reservation-name', '-n'],
                   help='The name of the capacity reservation.')
        c.argument('capacity', type=int, help='Specify the number of virtual machines in the scale set.')
        c.argument('tags', tags_type)

    with self.argument_context('capacity reservation create') as c:
        c.argument('zone', zone_type, help='Availability Zone to use for this capacity reservation. The zone has to be single value and also should be part for the list of zones specified during the capacity reservation group creation. If not provided, the reservation supports only non-zonal deployments. If provided, enforces VM/VMSS using this capacity reservation to be in same zone.')
        c.argument('sku_name', options_list=['--sku', '-s'], required=True, help='The SKU of the resource for which capacity needs be reserved. Currently VM Skus with the capability called "CapacityReservationSupported" set to true are supported. Refer to List Microsoft.Compute SKUs in a region (https://docs.microsoft.com/rest/api/compute/resourceskus/list) for supported values.')

    with self.argument_context('capacity reservation show') as c:
        c.argument('instance_view', action='store_true', options_list=['--instance-view', '-i'], help='Retrieve a snapshot of the runtime properties of the capacity reservation that is managed by the platform and can change outside of control plane operations.')
    # endRegion

    # region Restore point
    with self.argument_context('restore-point') as c:
        c.argument('restore_point_collection_name', options_list=['--collection-name'],
                   help='The name of the restore point collection.')

    with self.argument_context('restore-point create') as c:
        c.argument('restore_point_name', options_list=['--name', '-n', '--restore-point-name'],
                   help='The name of the restore point.')
        c.argument('exclude_disks', nargs='+', help='List of disk resource ids that the '
                   'customer wishes to exclude from the restore point. If no disks are specified, all disks will be '
                   'included.')
        c.argument('source_restore_point', help='Resource Id of the source restore point from which a copy needs to be created')

    with self.argument_context('restore-point show') as c:
        c.argument('restore_point_name', options_list=['--name', '-n', '--restore-point-name'],
                   help='The name of the restore point.')
        c.argument('expand', help='The expand expression to apply on the operation.',
                   deprecate_info=c.deprecate(hide=True))
        c.argument('instance_view', action='store_true', help='The instance view of a restore point.')

    with self.argument_context('restore-point delete') as c:
        c.argument('restore_point_name', options_list=['--name', '-n', '--restore-point-name'],
                   help='The name of the restore point.')

    with self.argument_context('restore-point wait') as c:
        c.argument('restore_point_name', options_list=['--name', '-n', '--restore-point-name'],
                   help='The name of the restore point.')
    # endRegion

    # region Restore point collection
    with self.argument_context('restore-point collection create') as c:
        c.argument('location', arg_type=get_location_type(self.cli_ctx), required=False,
                   validator=get_default_location_from_resource_group)
        c.argument('tags', tags_type)
        c.argument('source_id', help='Resource Id of the source resource used to create this restore point collection',
                   arg_group='Source')

    with self.argument_context('restore-point collection update') as c:
        c.argument('tags', tags_type)

    with self.argument_context('restore-point collection show') as c:
        c.argument('expand', help='The expand expression to apply on the operation.',
                   deprecate_info=c.deprecate(hide=True))
        c.argument('restore_points', action='store_true', help='All contained restore points in the restorePointCollection.')

    # endRegion
