# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from argcomplete.completers import FilesCompleter

from knack.arguments import CLIArgumentType

from azure.cli.core.profiles import ResourceType
from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_file_or_dict)
from azure.cli.core.commands.parameters import (
    get_location_type, get_resource_name_completion_list, tags_type, get_three_state_flag,
    file_type, get_enum_type, zone_type, zones_type)
from azure.cli.command_modules.vm._actions import _resource_not_exists
from azure.cli.command_modules.vm._completers import (
    get_urn_aliases_completion_list, get_vm_size_completion_list, get_vm_run_command_completion_list)
from azure.cli.command_modules.vm._validators import (
    validate_nsg_name, validate_vm_nics, validate_vm_nic, validate_vm_disk,
    validate_vmss_disk, validate_asg_names_or_ids, validate_keyvault)


# pylint: disable=too-many-statements, too-many-branches
def load_arguments(self, _):
    from azure.mgmt.compute.models import CachingTypes, UpgradeMode

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
    if self.supported_api_version(min_api='2018-04-01', operation_group='disks') or self.supported_api_version(min_api='2018-06-01', operation_group='virtual_machines'):
        disk_sku = CLIArgumentType(arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS', 'StandardSSD_LRS']))
    else:
        disk_sku = CLIArgumentType(arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']))

    # special case for `network nic scale-set list` command alias
    with self.argument_context('network nic scale-set list') as c:
        c.argument('virtual_machine_scale_set_name', options_list=['--vmss-name'], completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')

    # region MixedScopes
    for scope in ['vm', 'disk', 'snapshot', 'image']:
        with self.argument_context(scope) as c:
            c.argument('tags', tags_type)

    for scope in ['disk', 'snapshot']:
        with self.argument_context(scope) as c:
            c.ignore('source_blob_uri', 'source_disk', 'source_snapshot')
            c.argument('source_storage_account_id', help='used when source blob is in a different subscription')
            c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB.')
            c.argument('duration_in_seconds', help='Time duration in seconds until the SAS access expires', type=int)

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
    # endregion

    # region Identity
    # TODO move to its own command module https://github.com/Azure/azure-cli/issues/5105
    with self.argument_context('identity') as c:
        c.argument('resource_name', arg_type=name_arg_type, id_part='name')

    with self.argument_context('identity create') as c:
        c.argument('location', get_location_type(self.cli_ctx))
        c.argument('tags', tags_type)
    # endregion

    # region Snapshots
    with self.argument_context('snapshot', resource_type=ResourceType.MGMT_COMPUTE, operation_group='snapshots') as c:
        c.argument('snapshot_name', existing_snapshot_name, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/snapshots'))
        c.argument('name', arg_type=name_arg_type)
        if self.supported_api_version(min_api='2018-04-01', operation_group='snapshots'):
            c.argument('sku', arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS', 'Standard_ZRS']))
        else:
            c.argument('sku', arg_type=get_enum_type(['Premium_LRS', 'Standard_LRS']))
    # endregion

    # region Images
    with self.argument_context('image') as c:
        c.argument('os_type', arg_type=get_enum_type(['Windows', 'Linux']))
        c.argument('image_name', arg_type=name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/images'))

    with self.argument_context('image create') as c:
        # here we collpase all difference image sources to under 2 common arguments --os-disk-source --data-disk-sources
        c.argument('name', arg_type=name_arg_type, help='new image name')
        c.argument('source', help='OS disk source from the same region, including a virtual machine ID or name, OS disk blob URI, managed OS disk ID or name, or OS snapshot ID or name')
        c.argument('data_disk_sources', nargs='+', help='Space-separated list of data disk sources, including unmanaged blob URI, managed disk ID or name, or snapshot ID or name')
        c.argument('zone_resilient', min_api='2017-12-01', arg_type=get_three_state_flag(), help='Specifies whether an image is zone resilient or not. '
                   'Default is false. Zone resilient images can be created only in regions that provide Zone Redundant Storage')
        c.ignore('source_virtual_machine', 'os_blob_uri', 'os_disk', 'os_snapshot', 'data_blob_uris', 'data_disks', 'data_snapshots')
    # endregion

    # region AvailabilitySets
    with self.argument_context('vm availability-set') as c:
        c.argument('availability_set_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')

    with self.argument_context('vm availability-set create') as c:
        c.argument('availability_set_name', name_arg_type, validator=get_default_location_from_resource_group, help='Name of the availability set')
        c.argument('platform_update_domain_count', type=int, help='Update Domain count. If unspecified, server picks the most optimal number like 5. For the latest defaults see https://docs.microsoft.com/en-us/rest/api/compute/availabilitysets/availabilitysets-create')
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

    with self.argument_context('vm capture') as c:
        c.argument('overwrite', action='store_true')

    with self.argument_context('vm update') as c:
        c.argument('os_disk', min_api='2017-12-01', help="Managed OS disk ID or name to swap to. Feature registration for 'Microsoft.Compute/AllowManagedDisksReplaceOSDisk' is needed")
        c.argument('write_accelerator', nargs='*', min_api='2017-12-01',
                   help="enable/disable disk write accelerator. Use singular value 'true/false' to apply across, or specify individual disks, e.g.'os=true 1=true 2=true' for os disk and data disks with lun of 1 & 2")
        c.argument('disk_caching', nargs='*', help="Use singular value to apply across, or specify individual disks, e.g. 'os=ReadWrite 0=None 1=ReadOnly' should enable update os disk and 2 data disks")

    with self.argument_context('vm create') as c:
        c.argument('name', name_arg_type, validator=_resource_not_exists(self.cli_ctx, 'Microsoft.Compute/virtualMachines'))
        c.argument('vm_name', name_arg_type, id_part=None, help='Name of the virtual machine.', completer=None)
        c.argument('os_disk_size_gb', type=int, help='the size of the os disk in GB', arg_group='Storage')
        c.argument('attach_os_disk', help='Attach an existing OS disk to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')
        c.argument('attach_data_disks', nargs='+', help='Attach existing data disks to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')
        c.argument('availability_set', help='Name or ID of an existing availability set to add the VM to. None by default.')
        c.argument('nsg', help='The name to use when creating a new Network Security Group (default) or referencing an existing one. Can also reference an existing NSG by ID or specify "" for none.', arg_group='Network')
        c.argument('nsg_rule', help='NSG rule to create when creating a new NSG. Defaults to open ports for allowing RDP on Windows and allowing SSH on Linux.', arg_group='Network', arg_type=get_enum_type(['RDP', 'SSH']))
        c.argument('application_security_groups', resource_type=ResourceType.MGMT_NETWORK, min_api='2017-09-01', nargs='+', options_list=['--asgs'], help='Space-separated list of existing application security groups to associate with the VM.', arg_group='Network', validator=validate_asg_names_or_ids)
        c.argument('boot_diagnostics_storage',
                   help='pre-existing storage account name or its blob uri to capture boot diagnostics. Its sku should be one of Standard_GRS, Standard_LRS and Standard_RAGRS')
        c.argument('accelerated_networking', resource_type=ResourceType.MGMT_NETWORK, min_api='2016-09-01', arg_type=get_three_state_flag(), arg_group='Network',
                   help="enable accelerated networking. Unless specified, CLI will enable it based on machine image and size")

    with self.argument_context('vm open-port') as c:
        c.argument('vm_name', name_arg_type, help='The name of the virtual machine to open inbound traffic on.')
        c.argument('network_security_group_name', options_list=('--nsg-name',), help='The name of the network security group to create if one does not exist. Ignored if an NSG already exists.', validator=validate_nsg_name)
        c.argument('apply_to_subnet', help='Allow inbound traffic on the subnet instead of the NIC', action='store_true')
        c.argument('port', help="The port or port range (ex: 80-100) to open inbound traffic to. Use '*' to allow traffic to all ports.")
        c.argument('priority', help='Rule priority, between 100 (highest priority) and 4096 (lowest priority). Must be unique for each rule in the collection.', type=int)

    for scope in ['vm show', 'vm list']:
        with self.argument_context(scope) as c:
            c.argument('show_details', action='store_true', options_list=['--show-details', '-d'], help='show public ip address, FQDN, and power states. command will run slow')

    with self.argument_context('vm diagnostics') as c:
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'])

    with self.argument_context('vm diagnostics set') as c:
        c.argument('storage_account', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))

    with self.argument_context('vm disk') as c:
        c.argument('vm_name', options_list=['--vm-name'], id_part=None, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'))
        c.argument('disk', validator=validate_vm_disk, help='disk name or ID', completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
        c.argument('new', action='store_true', help='create a new disk')
        c.argument('sku', arg_type=disk_sku, help='Underlying storage SKU')
        c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB.')
        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')

    with self.argument_context('vm disk attach') as c:
        c.argument('enable_write_accelerator', min_api='2017-12-01', action='store_true', help='enable write accelerator')

    with self.argument_context('vm disk detach') as c:
        c.argument('disk_name', options_list=['--name', '-n'], help='The data disk name.')

    with self.argument_context('vm encryption enable') as c:
        c.argument('encrypt_format_all', action='store_true', help='Encrypts-formats data disks instead of encrypting them. Encrypt-formatting is a lot faster than in-place encryption but wipes out the partition getting encrypt-formatted.')

    with self.argument_context('vm extension') as c:
        c.argument('vm_extension_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'), help='extension name', id_part='child_name_1')
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'], id_part='name')

    with self.argument_context('vm extension list') as c:
        c.argument('vm_name', arg_type=existing_vm_name, options_list=['--vm-name'], id_part=None)

    with self.argument_context('vm secret') as c:
        c.argument('secrets', multi_ids_type, options_list=['--secrets', '-s'], help='Space-separated list of key vault secret URIs. Perhaps, produced by \'az keyvault secret list-versions --vault-name vaultname -n cert1 --query "[?attributes.enabled].id" -o tsv\'')
        c.argument('keyvault', help='Name or ID of the key vault.', validator=validate_keyvault)
        c.argument('certificate', help='key vault certificate name or its full secret URL')
        c.argument('certificate_store', help='Windows certificate store names. Default: My')

    with self.argument_context('vm secret list') as c:
        c.argument('vm_name', arg_type=existing_vm_name, id_part=None)

    with self.argument_context('vm image') as c:
        c.argument('publisher_name', options_list=['--publisher', '-p'])
        c.argument('publisher', options_list=['--publisher', '-p'], help='image publisher')
        c.argument('offer', options_list=['--offer', '-f'], help='image offer')
        c.argument('plan', help='image billing plan')
        c.argument('sku', options_list=['--sku', '-s'], help='image sku')
        c.argument('version', help="image sku's version")
        c.argument('urn', help="URN, in format of 'publisher:offer:sku:version'. If specified, other argument values can be omitted")

    with self.argument_context('vm image list') as c:
        c.argument('image_location', get_location_type(self.cli_ctx))

    with self.argument_context('vm image show') as c:
        c.argument('skus', options_list=['--sku', '-s'])

    with self.argument_context('vm nic') as c:
        c.argument('vm_name', existing_vm_name, options_list=['--vm-name'], id_part=None)
        c.argument('nics', nargs='+', help='Names or IDs of NICs.', validator=validate_vm_nics)
        c.argument('primary_nic', help='Name or ID of the primary NIC. If missing, the first NIC in the list will be the primary.')

    with self.argument_context('vm nic show') as c:
        c.argument('nic', help='NIC name or ID.', validator=validate_vm_nic)

    with self.argument_context('vm run-command') as c:
        c.argument('command_id', completer=get_vm_run_command_completion_list, help="The run command ID")

    with self.argument_context('vm run-command invoke') as c:
        c.argument('parameters', nargs='+', help="space-separated parameters in the format of '[name=]value'")
        c.argument('scripts', nargs='+', help="script lines separated by whites spaces. Use @{file} to load from a file")

    with self.argument_context('vm unmanaged-disk') as c:
        c.argument('disk_size', help='Size of disk (GiB)', default=1023, type=int)
        c.argument('new', action='store_true', help='Create a new disk.')
        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')
        c.argument('vhd_uri', help="Virtual hard disk URI. For example: https://mystorage.blob.core.windows.net/vhds/d1.vhd")

    with self.argument_context('vm unmanaged-disk attach') as c:
        c.argument('disk_name', options_list=['--name', '-n'], help='The data disk name(optional when create a new disk)')

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

    for scope in ['vmss deallocate', 'vmss delete-instances', 'vmss restart', 'vmss start', 'vmss stop', 'vmss show', 'vmss update-instances']:
        with self.argument_context(scope) as c:
            for dest in scaleset_name_aliases:
                c.argument(dest, vmss_name_type, id_part=None)  # due to instance-ids parameter

    with self.argument_context('vmss create') as c:
        VMPriorityTypes = self.get_models('VirtualMachinePriorityTypes', resource_type=ResourceType.MGMT_COMPUTE)
        VirtualMachineEvictionPolicyTypes = self.get_models('VirtualMachineEvictionPolicyTypes', resource_type=ResourceType.MGMT_COMPUTE)
        c.argument('name', name_arg_type)
        c.argument('nat_backend_port', default=None, help='Backend port to open with NAT rules.  Defaults to 22 on Linux and 3389 on Windows.')
        c.argument('single_placement_group', arg_type=get_three_state_flag(), help="Enable replicate using fault domains within the same cluster. Default to 'false' for any zonals, or with 100+ instances"
                   " See https://docs.microsoft.com/en-us/azure/virtual-machine-scale-sets/virtual-machine-scale-sets-placement-groups for details")
        c.argument('platform_fault_domain_count', type=int, help='Fault Domain count for each placement group in the availability zone', min_api='2017-12-01')
        c.argument('vmss_name', name_arg_type, id_part=None, help='Name of the virtual machine scale set.')
        c.argument('instance_count', help='Number of VMs in the scale set.', type=int)
        c.argument('disable_overprovision', help='Overprovision option (see https://azure.microsoft.com/en-us/documentation/articles/virtual-machine-scale-sets-overview/ for details).', action='store_true')
        c.argument('upgrade_policy_mode', help=None, arg_type=get_enum_type(UpgradeMode))
        c.argument('health_probe', help='(Preview) probe name from the existing load balancer, mainly used for rolling upgrade')
        c.argument('vm_sku', help='Size of VMs in the scale set. Default to "Standard_DS1_v2". See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.')
        c.argument('nsg', help='Name or ID of an existing Network Security Group.', arg_group='Network')
        c.argument('priority', resource_type=ResourceType.MGMT_COMPUTE, min_api='2017-12-01', arg_type=get_enum_type(VMPriorityTypes, default=None),
                   help="(PREVIEW)Priority. Use 'Low' to run short-lived workloads in a cost-effective way")
        c.argument('eviction_policy', resource_type=ResourceType.MGMT_COMPUTE, min_api='2017-12-01', arg_type=get_enum_type(VirtualMachineEvictionPolicyTypes, default=None),
                   help="(PREVIEW) the eviction policy for virtual machines in a low priority scale set.")
        c.argument('application_security_groups', resource_type=ResourceType.MGMT_COMPUTE, min_api='2018-06-01', nargs='+', options_list=['--asgs'], help='Space-separated list of existing application security groups to associate with the VM.', arg_group='Network', validator=validate_asg_names_or_ids)

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
                   help="Sku of the Load Balancer to create. Default to 'Standard' when single placement group is turned off; otherwise, default to 'Basic'")
        c.argument('nat_pool_name', help='Name to use for the NAT pool when creating a new load balancer.', options_list=['--lb-nat-pool-name', '--nat-pool-name'])

    with self.argument_context('vmss create', min_api='2017-03-30', arg_group='Network') as c:
        c.argument('public_ip_per_vm', action='store_true', help="Each VM instance will have a public ip. For security, you can use '--nsg' to apply appropriate rules")
        c.argument('vm_domain_name', help="domain name of VM instances, once configured, the FQDN is 'vm<vm-index>.<vm-domain-name>.<..rest..>'")
        c.argument('dns_servers', nargs='+', help="space-separated IP addresses of DNS servers, e.g. 10.0.0.5 10.0.0.6")
        c.argument('accelerated_networking', arg_type=get_three_state_flag(),
                   help="enable accelerated networking. Unless specified, CLI will enable it based on machine image and size")

    for scope in ['vmss update-instances', 'vmss delete-instances']:
        with self.argument_context(scope) as c:
            c.argument('instance_ids', multi_ids_type, help='Space-separated list of IDs (ex: 1 2 3 ...) or * for all instances.')

    with self.argument_context('vmss diagnostics') as c:
        c.argument('vmss_name', id_part=None, help='Scale set name')

    with self.argument_context('vmss disk') as c:
        c.argument('lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine instance size.')
        c.argument('size_gb', options_list=['--size-gb', '-z'], help='size in GB.')
        c.argument('vmss_name', vmss_name_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))
        c.argument('disk', validator=validate_vmss_disk, help='existing disk name or ID to attach or detach from VM instances',
                   min_api='2017-12-01', completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
        c.argument('instance_id', help='Scale set VM instance id', min_api='2017-12-01')

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
    # endregion

    # region VM & VMSS Shared
    for scope in ['vm', 'vmss']:
        with self.argument_context(scope) as c:
            c.argument('no_auto_upgrade', action='store_true', help='by doing this, extension system will not pick the highest minor version for the specified version number, and will not auto update to the latest build/revision number on any scale set updates in future.')

    for scope in ['vm identity assign', 'vmss identity assign']:
        with self.argument_context(scope) as c:
            c.argument('assign_identity', options_list=['--identities'], nargs='*', help="the identities to assign")
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm identity remove', 'vmss identity remove']:
        with self.argument_context(scope) as c:
            c.argument('identities', nargs='+', help="Space-separated identities to remove. Use '[system]' to refer system assigned identity.")
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm identity show', 'vmss identity show']:
        with self.argument_context(scope) as c:
            c.argument('vm_name', existing_vm_name)
            c.argument('vmss_name', vmss_name_type)

    for scope in ['vm create', 'vmss create']:
        with self.argument_context(scope) as c:
            c.argument('location', get_location_type(self.cli_ctx), help='Location in which to create VM and related resources. If default location is not configured, will default to the resource group\'s location')
            c.argument('tags', tags_type)
            c.argument('no_wait', help='Do not wait for the long-running operation to finish.')
            c.argument('validate', options_list=['--validate'], help='Generate and validate the ARM template without creating any resources.', action='store_true')
            c.argument('size', help='The VM size to be created. See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.')
            c.argument('image', completer=get_urn_aliases_completion_list)
            c.argument('custom_data', help='Custom init script file or text (cloud-init, cloud-config, etc..)', completer=FilesCompleter(), type=file_type)
            c.argument('secrets', multi_ids_type, help='One or many Key Vault secrets as JSON strings or files via `@<file path>` containing `[{ "sourceVault": { "id": "value" }, "vaultCertificates": [{ "certificateUrl": "value", "certificateStore": "cert store name (only on windows)"}] }]`', type=file_type, completer=FilesCompleter())
            c.argument('assign_identity', nargs='*', arg_group='Managed Service Identity', help="accept system or user assigned identities separated by spaces. Use '[system]' to refer system assigned identity, or a resource id to refer user assigned identity. Check out help for more examples")

        with self.argument_context(scope, arg_group='Authentication') as c:
            c.argument('generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory')
            c.argument('admin_username', help='Username for the VM.')
            c.argument('admin_password', help="Password for the VM if authentication type is 'Password'.")
            c.argument('ssh_key_value', help='SSH public key or public key file path.', completer=FilesCompleter(), type=file_type)
            c.argument('ssh_dest_key_path', help='Destination file path on the VM for the SSH key.')
            c.argument('authentication_type', help='Type of authentication to use with the VM. Defaults to password for Windows and SSH public key for Linux.', arg_type=get_enum_type(['ssh', 'password']))

        with self.argument_context(scope, arg_group='Storage') as c:
            c.argument('os_disk_name', help='The name of the new VM OS disk.')
            c.argument('os_type', help='Type of OS installed on a custom VHD. Do not use when specifying an URN or URN alias.', arg_type=get_enum_type(['windows', 'linux']))
            c.argument('storage_account', help="Only applicable when used with `--use-unmanaged-disk`. The name to use when creating a new storage account or referencing an existing one. If omitted, an appropriate storage account in the same resource group and location will be used, or a new one will be created.")
            c.argument('storage_sku', arg_type=disk_sku, help='The SKU of the storage account with which to persist VM')
            c.argument('storage_container_name', help="Only applicable when used with `--use-unmanaged-disk`. Name of the storage container for the VM OS disk. Default: vhds")
            c.ignore('os_publisher', 'os_offer', 'os_sku', 'os_version', 'storage_profile')
            c.argument('use_unmanaged_disk', action='store_true', help='Do not use managed disk to persist VM')
            c.argument('data_disk_sizes_gb', nargs='+', type=int, help='space-separated empty managed data disk sizes in GB to create')
            c.ignore('disk_info', 'storage_account_type', 'public_ip_address_type', 'nsg_type', 'nic_type', 'vnet_type', 'load_balancer_type', 'app_gateway_type')
            c.argument('os_caching', options_list=['--storage-caching', '--os-disk-caching'], help='Storage caching type for the VM OS disk. Default: ReadWrite', arg_type=get_enum_type(CachingTypes))
            c.argument('data_caching', options_list=['--data-disk-caching'], nargs='+',
                       help="storage caching type for data disk(s), including 'None', 'ReadOnly', 'ReadWrite', etc. Use a singular value to apply on all disks, or use '<lun>=<vaule1> <lun>=<value2>' to configure individual disk")

        with self.argument_context(scope, arg_group='Network') as c:
            c.argument('vnet_name', help='Name of the virtual network when creating a new one or referencing an existing one.')
            c.argument('vnet_address_prefix', help='The IP address prefix to use when creating a new VNet in CIDR format.')
            c.argument('subnet', help='The name of the subnet when creating a new VNet or referencing an existing one. Can also reference an existing subnet by ID. If omitted, an appropriate VNet and subnet will be selected automatically, or a new one will be created.')
            c.argument('subnet_address_prefix', help='The subnet IP address prefix to use when creating a new VNet in CIDR format.')
            c.argument('nics', nargs='+', help='Names or IDs of existing NICs to attach to the VM. The first NIC will be designated as primary. If omitted, a new NIC will be created. If an existing NIC is specified, do not specify subnet, VNet, public IP or NSG.')
            c.argument('private_ip_address', help='Static private IP address (e.g. 10.0.0.5).')
            c.argument('public_ip_address', help='Name of the public IP address when creating one (default) or referencing an existing one. Can also reference an existing public IP by ID or specify "" for None.')
            c.argument('public_ip_address_allocation', help=None, default=None, arg_type=get_enum_type(['dynamic', 'static']))
            c.argument('public_ip_address_dns_name', help='Globally unique DNS name for a newly created public IP.')
            if self.supported_api_version(min_api='2017-08-01', resource_type=ResourceType.MGMT_NETWORK):
                PublicIPAddressSkuName = self.get_models('PublicIPAddressSkuName', resource_type=ResourceType.MGMT_NETWORK)
                c.argument('public_ip_sku', help='Sku', default=None, arg_type=get_enum_type(PublicIPAddressSkuName))

        with self.argument_context(scope, arg_group='Marketplace Image Plan') as c:
            c.argument('plan_name', help='plan name')
            c.argument('plan_product', help='plan product')
            c.argument('plan_publisher', help='plan publisher')
            c.argument('plan_promotion_code', help='plan promotion code')

    for scope in ['vm create', 'vmss create', 'vm identity assign', 'vmss identity assign']:
        with self.argument_context(scope) as c:
            arg_group = 'Managed Service Identity' if scope.split()[-1] == 'create' else None
            c.argument('identity_scope', options_list=['--scope'], arg_group=arg_group, help="Scope that the system assigned identity can access")
            c.argument('identity_role', options_list=['--role'], arg_group=arg_group, help="Role name or id the system assigned identity will have")
            c.ignore('identity_role_id')

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
            c.argument('disk_encryption_keyvault', help='The key vault where the generated encryption key will be placed.')
            c.argument('key_encryption_key', help='Key vault key name or URL used to encrypt the disk encryption key.')
            c.argument('key_encryption_keyvault', help='The key vault containing the key encryption key used to encrypt the disk encryption key. If missing, CLI will use `--disk-encryption-keyvault`.')

    for scope in ['vm extension', 'vmss extension']:
        with self.argument_context(scope) as c:
            c.argument('publisher', help='The name of the extension publisher.')
            c.argument('settings', type=validate_file_or_dict, help='Extension settings in JSON format. A JSON file path is also accepted.')
            c.argument('protected_settings', type=validate_file_or_dict, help='Protected settings in JSON format for sensitive information like credentials. A JSON file path is also accepted.')
            c.argument('version', help='The version of the extension')

    with self.argument_context('vm extension set') as c:
        c.argument('force_update', action='store_true', help='force to update even if the extension configuration has not changed.')

    with self.argument_context('vmss extension set', min_api='2017-12-01') as c:
        c.argument('force_update', action='store_true', help='force to update even if the extension configuration has not changed.')

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
            c.argument('license_type', help="license type if the Windows image or disk used was licensed on-premises", arg_type=get_enum_type(['Windows_Server', 'Windows_Client', 'None']))

    # endregion
