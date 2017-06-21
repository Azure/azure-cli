# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from argcomplete.completers import FilesCompleter

from azure.mgmt.compute.models import (CachingTypes,
                                       UpgradeMode)
from azure.mgmt.storage.models import SkuName

from azure.cli.core.commands import register_cli_argument, CliArgumentType, register_extra_cli_argument
from azure.cli.core.commands.validators import \
    (get_default_location_from_resource_group, validate_file_or_dict)
from azure.cli.core.commands.parameters import \
    (location_type, get_one_of_subscription_locations,
     get_resource_name_completion_list, tags_type, file_type, enum_choice_list, ignore_type)
from azure.cli.command_modules.vm._actions import \
    (load_images_from_aliases_doc, get_vm_sizes, _resource_not_exists)
from azure.cli.command_modules.vm._validators import \
    (validate_nsg_name, validate_vm_nics, validate_vm_nic, process_vm_create_namespace,
     process_vmss_create_namespace, process_image_create_namespace,
     process_disk_or_snapshot_create_namespace, validate_vm_disk,
     process_disk_encryption_namespace)


def get_urn_aliases_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    images = load_images_from_aliases_doc()
    return [i['urnAlias'] for i in images]


def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]


# REUSABLE ARGUMENT DEFINITIONS

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
multi_ids_type = CliArgumentType(nargs='+')
existing_vm_name = CliArgumentType(overrides=name_arg_type,
                                   configured_default='vm',
                                   help="The name of the Virtual Machine. You can configure the default using `az configure --defaults vm=<name>`",
                                   completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'), id_part='name')
vmss_name_type = CliArgumentType(name_arg_type,
                                 configured_default='vmss',
                                 completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'),
                                 help="Scale set name. You can configure the default using `az configure --defaults vmss=<name>`",
                                 id_part='name')
disk_sku = CliArgumentType(required=False, help='underlying storage sku', **enum_choice_list(['Premium_LRS', 'Standard_LRS']))

# ARGUMENT REGISTRATION

register_cli_argument('vm', 'vm_name', existing_vm_name)
register_cli_argument('vm', 'size', completer=get_vm_size_completion_list)
for scope in ['vm', 'disk', 'snapshot', 'image']:
    register_cli_argument(scope, 'tags', tags_type)
register_cli_argument('vm', 'name', arg_type=name_arg_type)

for item in ['show', 'list']:
    register_cli_argument('vm {}'.format(item), 'show_details', action='store_true', options_list=('--show-details', '-d'), help='show public ip address, FQDN, and power states. command will run slow')

register_cli_argument('vm unmanaged-disk', 'vm_name', arg_type=existing_vm_name)
register_cli_argument('vm unmanaged-disk attach', 'disk_name', options_list=('--name', '-n'), help='The data disk name(optional when create a new disk)')
register_cli_argument('vm unmanaged-disk detach', 'disk_name', options_list=('--name', '-n'), help='The data disk name.')
register_cli_argument('vm unmanaged-disk', 'disk_size', help='Size of disk (GiB)', default=1023, type=int)
register_cli_argument('vm unmanaged-disk', 'new', action="store_true", help='create a new disk')
register_cli_argument('vm unmanaged-disk', 'lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')
register_cli_argument('vm unmanaged-disk', 'vhd_uri', help="virtual hard disk's uri. For example:https://mystorage.blob.core.windows.net/vhds/d1.vhd")
register_cli_argument('vm', 'caching', help='Disk caching policy', **enum_choice_list(CachingTypes))

for item in ['attach', 'detach']:
    register_cli_argument('vm unmanaged-disk {}'.format(item), 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',), id_part=None)

register_cli_argument('vm disk', 'vm_name', options_list=('--vm-name',), id_part=None,
                      completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'))
register_cli_argument('vm disk', 'disk', validator=validate_vm_disk, help='disk name or id',
                      completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
register_cli_argument('vm disk detach', 'disk_name', options_list=('--name', '-n'), help='The data disk name.')
register_cli_argument('vm disk', 'new', action="store_true", help='create a new disk')
register_cli_argument('vm disk', 'sku', arg_type=disk_sku)
register_cli_argument('vm disk', 'size_gb', options_list=('--size-gb', '-z'), help='size in GB.')
register_cli_argument('vm disk', 'lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine size.')

register_cli_argument('vm availability-set', 'availability_set_name', name_arg_type, id_part='name',
                      completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')
register_cli_argument('vm availability-set create', 'availability_set_name', name_arg_type, validator=get_default_location_from_resource_group, help='Name of the availability set')
register_cli_argument('vm availability-set create', 'unmanaged', action='store_true', help='contained VMs should use unmanaged disks')
register_cli_argument('vm availability-set create', 'platform_update_domain_count', type=int,
                      help='Update Domain count. If unspecified, server picks the most optimal number like 5. For the latest defaults see https://docs.microsoft.com/en-us/rest/api/compute/availabilitysets/availabilitysets-create')
register_cli_argument('vm availability-set create', 'platform_fault_domain_count', type=int, help='Fault Domain count.')
register_cli_argument('vm availability-set create', 'validate', help='Generate and validate the ARM template without creating any resources.', action='store_true')

register_cli_argument('vm user', 'username', options_list=('--username', '-u'), help='The user name')
register_cli_argument('vm user', 'password', options_list=('--password', '-p'), help='The user password')

register_cli_argument('vm capture', 'overwrite', action='store_true')

register_cli_argument('vm diagnostics', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm diagnostics set', 'storage_account', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))

register_cli_argument('vm extension', 'vm_extension_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'), id_part='child_name')
register_cli_argument('vm extension', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',), id_part='name')

register_cli_argument('vm extension image', 'image_location', options_list=('--location', '-l'))
register_cli_argument('vm extension image', 'publisher_name', options_list=('--publisher', '-p'), help='Image publisher name')
register_cli_argument('vm extension image', 'type', options_list=('--name', '-n'), help='Name of the extension')
register_cli_argument('vm extension image', 'latest', action='store_true')
register_cli_argument('vm extension image', 'version', help='Extension version')

for dest in ['vm_scale_set_name', 'virtual_machine_scale_set_name', 'name']:
    register_cli_argument('vmss', dest, vmss_name_type)
    register_cli_argument('vmss deallocate', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss delete-instances', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss restart', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss start', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss stop', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss show', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter
    register_cli_argument('vmss update-instances', dest, vmss_name_type, id_part=None)  # due to instance-ids parameter

register_cli_argument('vmss', 'instance_id', id_part='child_name')
register_cli_argument('vmss', 'instance_ids', multi_ids_type, help='Space separated list of IDs (ex: 1 2 3 ...) or * for all instances. If not provided, the action will be applied on the scaleset itself')
register_cli_argument('vmss', 'tags', tags_type)
register_cli_argument('vmss', 'caching', help='Disk caching policy', **enum_choice_list(CachingTypes))

register_cli_argument('vmss disk', 'lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virtual Machine instance size.')
register_cli_argument('vmss disk', 'size_gb', options_list=('--size-gb', '-z'), help='size in GB.')
register_cli_argument('vmss disk', 'vmss_name', vmss_name_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))

register_cli_argument('vmss extension', 'extension_name', name_arg_type, help='Name of the extension.')
register_cli_argument('vmss extension', 'vmss_name', id_part=None)
register_cli_argument('vmss diagnostics', 'vmss_name', id_part=None, help='Scale set name')

register_cli_argument('vmss extension image', 'publisher_name', options_list=('--publisher', '-p'), help='Image publisher name')
register_cli_argument('vmss extension image', 'type', options_list=('--name', '-n'), help='Extension name')
register_cli_argument('vmss extension image', 'latest', action='store_true')
register_cli_argument('vmss extension image', 'image_name', help='Image name')
register_cli_argument('vmss extension image', 'orderby', help='The sort to apply on the operation')
register_cli_argument('vmss extension image', 'top', help='Return top number of records')
register_cli_argument('vmss extension image', 'version', help='Extension version')

for scope in ['update-instances', 'delete-instances']:
    register_cli_argument('vmss ' + scope, 'instance_ids', multi_ids_type, help='Space separated list of IDs (ex: 1 2 3 ...) or * for all instances.')

for scope in ['vm diagnostics', 'vmss diagnostics']:
    register_cli_argument(scope, 'version', help='version of the diagnostics extension. Will use the latest if not specfied')
    register_cli_argument(scope, 'settings', help='json string or a file path, which defines data to be collected.', type=validate_file_or_dict, completer=FilesCompleter())
    register_cli_argument(scope, 'protected_settings', help='json string or a file path containing private configurations such as storage account keys, etc.', type=validate_file_or_dict, completer=FilesCompleter())

for scope in ['vm', 'vmss']:
    register_cli_argument(scope, 'no_auto_upgrade', action='store_true', help='by doing this, extension system will not pick the highest minor version for the specified version number, and will not auto update to the latest build/revision number on any scale set updates in future.')
    register_cli_argument('{} create'.format(scope), 'generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing', arg_group='Authentication')
    register_cli_argument('{} extension'.format(scope), 'settings', type=validate_file_or_dict)
    register_cli_argument('{} extension'.format(scope), 'protected_settings', type=validate_file_or_dict)


register_cli_argument('vm image list', 'image_location', location_type)
register_cli_argument('vm image', 'publisher_name', options_list=('--publisher', '-p'))
register_cli_argument('vm image', 'offer', options_list=('--offer', '-f'))
register_cli_argument('vm image', 'sku', options_list=('--sku', '-s'))
# overriding skus from the sdk operation to be a single sku
register_cli_argument('vm image show', 'skus', options_list=('--sku', '-s'))

register_cli_argument('vm open-port', 'vm_name', name_arg_type, help='The name of the virtual machine to open inbound traffic on.')
register_cli_argument('vm open-port', 'network_security_group_name', options_list=('--nsg-name',), help='The name of the network security group to create if one does not exist. Ignored if an NSG already exists.', validator=validate_nsg_name)
register_cli_argument('vm open-port', 'apply_to_subnet', help='Allow inbound traffic on the subnet instead of the NIC', action='store_true')
register_cli_argument('vm open-port', 'port', help="The port or port range (ex: 80-100) to open inbound traffic to. Use '*' to allow traffic to all ports.")
register_cli_argument('vm open-port', 'priority', help='Rule priority, between 100 (highest priority) and 4096 (lowest priority). Must be unique for each rule in the collection.', type=int)

register_cli_argument('vm nic', 'vm_name', existing_vm_name, options_list=('--vm-name',), id_part=None)
register_cli_argument('vm nic', 'nics', nargs='+', help='Names or IDs of NICs.', validator=validate_vm_nics)
register_cli_argument('vm nic show', 'nic', help='NIC name or ID.', validator=validate_vm_nic)

register_cli_argument('vmss nic', 'virtual_machine_scale_set_name', options_list=('--vmss-name',), help='Scale set name.', completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')
register_cli_argument('vmss nic', 'virtualmachine_index', options_list=('--instance-id',), id_part='child_name')
register_cli_argument('vmss nic', 'network_interface_name', options_list=('--name', '-n'), metavar='NIC_NAME', help='The network interface (NIC).', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'), id_part='grandchild_name')

register_cli_argument('network nic scale-set list', 'virtual_machine_scale_set_name', options_list=('--vmss-name',), completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')

# VM CREATE PARAMETER CONFIGURATION
register_cli_argument('vm create', 'name', name_arg_type, validator=_resource_not_exists('Microsoft.Compute/virtualMachines'))

register_cli_argument('vmss create', 'name', name_arg_type)
register_cli_argument('vmss create', 'nat_backend_port', default=None, help='Backend port to open with NAT rules.  Defaults to 22 on Linux and 3389 on Windows.')
register_cli_argument('vmss create', 'single_placement_group', default=None, help="Enable single placement group. This flag will default to True if instance count <=100, and default to False for instance count >100.", **enum_choice_list(['true', 'false']))

for scope in ['vm create', 'vmss create']:
    register_cli_argument(scope, 'location', location_type, help='Location in which to create VM and related resources. If default location is not configured, will default to the resource group\'s location')
    register_cli_argument(scope, 'tags', tags_type)
    register_cli_argument(scope, 'no_wait', help='Do not wait for the long running operation to finish.')
    register_cli_argument(scope, 'validate', options_list=('--validate',), help='Generate and validate the ARM template without creating any resources.', action='store_true')
    register_cli_argument(scope, 'size', help='The VM size to be created. See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.')
    register_cli_argument(scope, 'image', completer=get_urn_aliases_completion_list)

    register_cli_argument(scope, 'admin_username', help='Username for the VM.', arg_group='Authentication')
    register_cli_argument(scope, 'admin_password', help="Password for the VM if authentication type is 'Password'.", arg_group='Authentication')
    register_cli_argument(scope, 'ssh_key_value', help='SSH public key or public key file path.', completer=FilesCompleter(), type=file_type, arg_group='Authentication')
    register_cli_argument(scope, 'custom_data', help='Custom init script file or text (cloud-init, cloud-config, etc..)', completer=FilesCompleter(), type=file_type)
    register_cli_argument(scope, 'ssh_dest_key_path', help='Destination file path on the VM for the SSH key.', arg_group='Authentication')
    register_cli_argument(scope, 'authentication_type', help='Type of authentication to use with the VM. Defaults to password for Windows and SSH public key for Linux.', arg_group='Authentication', **enum_choice_list(['ssh', 'password']))

    register_cli_argument(scope, 'os_disk_name', help='The name of the new VM OS disk.', arg_group='Storage')
    register_cli_argument(scope, 'os_type', help='Type of OS installed on a custom VHD. Do not use when specifying an URN or URN alias.', arg_group='Storage', **enum_choice_list(['windows', 'linux']))
    register_cli_argument(scope, 'storage_account', help="Only applicable when use with '--use-unmanaged-disk'. The name to use when creating a new storage account or referencing an existing one. If omitted, an appropriate storage account in the same resource group and location will be used, or a new one will be created.", arg_group='Storage')
    register_cli_argument(scope, 'storage_sku', help='The sku of storage account to persist VM. By default, only Standard_LRS and Premium_LRS are allowed. Using with --use-unmanaged-disk, all are available.', arg_group='Storage', **enum_choice_list(SkuName))
    register_cli_argument(scope, 'storage_container_name', help="Only applicable when use with '--use-unmanaged-disk'. Name of the storage container for the VM OS disk. Default: vhds", arg_group='Storage')
    register_cli_argument(scope, 'os_publisher', ignore_type)
    register_cli_argument(scope, 'os_offer', ignore_type)
    register_cli_argument(scope, 'os_sku', ignore_type)
    register_cli_argument(scope, 'os_version', ignore_type)
    register_cli_argument(scope, 'storage_profile', ignore_type)
    register_cli_argument(scope, 'use_unmanaged_disk', action='store_true', help='Do not use managed disk to persist VM', arg_group='Storage')
    register_cli_argument(scope, 'data_disk_sizes_gb', nargs='+', type=int, help='space separated empty managed data disk sizes in GB to create', arg_group='Storage')
    register_cli_argument(scope, 'image_data_disks', ignore_type)
    register_cli_argument(scope, 'plan_name', ignore_type)
    register_cli_argument(scope, 'plan_product', ignore_type)
    register_cli_argument(scope, 'plan_publisher', ignore_type)
    for item in ['storage_account', 'public_ip', 'nsg', 'nic', 'vnet', 'load_balancer', 'app_gateway']:
        register_cli_argument(scope, '{}_type'.format(item), ignore_type)

    register_cli_argument(scope, 'vnet_name', help='Name of the virtual network when creating a new one or referencing an existing one.', arg_group='Network')
    register_cli_argument(scope, 'vnet_address_prefix', help='The IP address prefix to use when creating a new VNet in CIDR format.', arg_group='Network')
    register_cli_argument(scope, 'subnet', help='The name of the subnet when creating a new VNet or referencing an existing one. Can also reference an existing subnet by ID. If omitted, an appropriate VNet and subnet will be selected automatically, or a new one will be created.', arg_group='Network')
    register_cli_argument(scope, 'subnet_address_prefix', help='The subnet IP address prefix to use when creating a new VNet in CIDR format.', arg_group='Network')
    register_cli_argument(scope, 'nics', nargs='+', help='Names or IDs of existing NICs to attach to the VM. The first NIC will be designated as primary. If omitted, a new NIC will be created. If an existing NIC is specified, do not specify subnet, vnet, public IP or NSG.', arg_group='Network')
    register_cli_argument(scope, 'nsg', help='The name to use when creating a new Network Security Group (default) or referencing an existing one. Can also reference an existing NSG by ID or specify "" for none.', arg_group='Network')
    register_cli_argument(scope, 'nsg_rule', help='NSG rule to create when creating a new NSG. Defaults to open ports for allowing RDP on Windows and allowing SSH on Linux.', arg_group='Network', **enum_choice_list(['RDP', 'SSH']))
    register_cli_argument(scope, 'private_ip_address', help='Static private IP address (e.g. 10.0.0.5).', arg_group='Network')
    register_cli_argument(scope, 'public_ip_address', help='Name of the public IP address when creating one (default) or referencing an existing one. Can also reference an existing public IP by ID or specify "" for None.', arg_group='Network')
    register_cli_argument(scope, 'public_ip_address_allocation', help=None, arg_group='Network', **enum_choice_list(['dynamic', 'static']))
    register_cli_argument(scope, 'public_ip_address_dns_name', help='Globally unique DNS name for a newly created Public IP.', arg_group='Network')
    register_cli_argument(scope, 'secrets', multi_ids_type, help='One or many Key Vault secrets as JSON strings or files via `@<file path>` containing `[{ "sourceVault": { "id": "value" }, "vaultCertificates": [{ "certificateUrl": "value", "certificateStore": "cert store name (only on windows)"}] }]`', type=file_type, completer=FilesCompleter())
    register_cli_argument(scope, 'os_caching', options_list=['--storage-caching', '--os-disk-caching'], arg_group='Storage', help='Storage caching type for the VM OS disk.', **enum_choice_list([CachingTypes.read_only.value, CachingTypes.read_write.value]))
    register_cli_argument(scope, 'data_caching', options_list=['--data-disk-caching'], arg_group='Storage', help='Storage caching type for the VM data disk(s).', **enum_choice_list(CachingTypes))

    register_cli_argument(scope, 'license_type', help="license type if the Windows image or disk used was licensed on-premises", **enum_choice_list(['Windows_Server', 'Windows_Client']))

register_cli_argument('vm create', 'vm_name', name_arg_type, id_part=None, help='Name of the virtual machine.', validator=process_vm_create_namespace, completer=None)
register_cli_argument('vm create', 'attach_os_disk', help='Attach an existing OS disk to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')
register_cli_argument('vm create', 'attach_data_disks', nargs='+', help='Attach existing data disks to the VM. Can use the name or ID of a managed disk or the URI to an unmanaged disk VHD.')

register_cli_argument('vm create', 'availability_set', help='Name or ID of an existing availability set to add the VM to. None by default.')

register_cli_argument('vmss create', 'vmss_name', name_arg_type, id_part=None, help='Name of the virtual machine scale set.', validator=process_vmss_create_namespace)
register_cli_argument('vmss create', 'load_balancer', help='Name to use when creating a new load balancer (default) or referencing an existing one. Can also reference an existing load balancer by ID or specify "" for none.', options_list=['--load-balancer', '--lb'], arg_group='Network Balancer')
register_cli_argument('vmss create', 'application_gateway', help='Name to use when creating a new application gateway (default) or referencing an existing one. Can also reference an existing application gateway by ID or specify "" for none.', options_list=['--app-gateway'], arg_group='Network Balancer')
register_cli_argument('vmss create', 'backend_pool_name', help='Name to use for the backend pool when creating a new load balancer or application gateway.', arg_group='Network Balancer')
register_cli_argument('vmss create', 'nat_pool_name', help='Name to use for the NAT pool when creating a new load balancer.', options_list=['--lb-nat-pool-name', '--nat-pool-name'], arg_group='Network Balancer')
register_cli_argument('vmss create', 'backend_port', help='When creating a new load balancer, backend port to open with NAT rules (Defaults to 22 on Linux and 3389 on Windows). When creating an application gateway, the backend port to use for the backend HTTP settings.', type=int, arg_group='Network Balancer')
register_cli_argument('vmss create', 'app_gateway_subnet_address_prefix', help='The subnet IP address prefix to use when creating a new application gateway in CIDR format.', arg_group='Network Balancer')
register_cli_argument('vmss create', 'instance_count', help='Number of VMs in the scale set.', type=int)
register_cli_argument('vmss create', 'disable_overprovision', help='Overprovision option (see https://azure.microsoft.com/en-us/documentation/articles/virtual-machine-scale-sets-overview/ for details).', action='store_true')
register_cli_argument('vmss create', 'upgrade_policy_mode', help=None, **enum_choice_list(UpgradeMode))
register_cli_argument('vmss create', 'vm_sku', help='Size of VMs in the scale set.  See https://azure.microsoft.com/en-us/pricing/details/virtual-machines/ for size info.')

register_cli_argument('vm encryption', 'volume_type', help='Type of volume that the encryption operation is performed on', **enum_choice_list(['DATA', 'OS', 'ALL']))
register_cli_argument('vm encryption', 'force', action='store_true', help='continue with encryption operations regardless of the warnings')
register_cli_argument('vm encryption', 'disk_encryption_keyvault', validator=process_disk_encryption_namespace)

existing_disk_name = CliArgumentType(overrides=name_arg_type, help='The name of the managed disk', completer=get_resource_name_completion_list('Microsoft.Compute/disks'), id_part='name')
register_cli_argument('disk', 'disk_name', existing_disk_name, completer=get_resource_name_completion_list('Microsoft.Compute/disks'))
register_cli_argument('disk', 'name', arg_type=name_arg_type)
register_cli_argument('disk', 'sku', arg_type=disk_sku)

existing_snapshot_name = CliArgumentType(overrides=name_arg_type, help='The name of the snapshot', completer=get_resource_name_completion_list('Microsoft.Compute/snapshots'), id_part='name')
register_cli_argument('snapshot', 'snapshot_name', existing_snapshot_name, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/snapshots'))
register_cli_argument('snapshot', 'name', arg_type=name_arg_type)
register_cli_argument('snapshot', 'sku', arg_type=disk_sku)

existing_image_name = CliArgumentType(overrides=name_arg_type, help='The name of the custom image', completer=get_resource_name_completion_list('Microsoft.Compute/images'), id_part='name')
register_cli_argument('image', 'os_type', **enum_choice_list(['Windows', 'Linux']))
register_cli_argument('image', 'image_name', arg_type=name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Compute/images'))
register_cli_argument('image create', 'name', arg_type=name_arg_type, help='new image name')

# here we collpase all difference image sources to under 2 common arguments --os-disk-source --data-disk-sources
register_extra_cli_argument('image create', 'source', validator=process_image_create_namespace,
                            help='OS disk source of the new image, including a virtual machine id or name, sas uri to a os disk blob, managed os disk id or name, or os snapshot id or name')
register_extra_cli_argument('image create', 'data_disk_sources', nargs='+',
                            help='space separated 1 or more data disk sources, including sas uri to a blob, managed disk id or name, or snapshot id or name')
register_cli_argument('image create', 'source_virtual_machine', ignore_type)
register_cli_argument('image create', 'os_blob_uri', ignore_type)
register_cli_argument('image create', 'os_disk', ignore_type)
register_cli_argument('image create', 'os_snapshot', ignore_type)
register_cli_argument('image create', 'data_blob_uris', ignore_type)
register_cli_argument('image create', 'data_disks', ignore_type)
register_cli_argument('image create', 'data_snapshots', ignore_type)

for scope in ['disk', 'snapshot']:
    register_extra_cli_argument(scope + ' create', 'source', validator=process_disk_or_snapshot_create_namespace,
                                help='source to create the disk from, including a sas blob uri to a blob, managed disk id or name, or snapshot id or name')
    register_cli_argument(scope, 'source_blob_uri', ignore_type)
    register_cli_argument(scope, 'source_disk', ignore_type)
    register_cli_argument(scope, 'source_snapshot', ignore_type)
    register_cli_argument(scope, 'source_storage_account_id', help='used when source blob is in a different subscription')
    register_cli_argument(scope, 'size_gb', options_list=('--size-gb', '-z'), help='size in GB.')
    register_cli_argument(scope, 'duration_in_seconds', help='Time duration in seconds until the SAS access expires')

register_cli_argument('vm format-secret', 'secrets', multi_ids_type, options_list=('--secrets', '-s'), help='Space separated list of Key Vault secret URIs. Perhaps, produced by \'az keyvault secret list-versions --vault-name vaultname -n cert1 --query "[?attributes.enabled].id" -o tsv\'')
