#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse
import getpass
import os

from argcomplete.completers import FilesCompleter

from azure.mgmt.compute.models import (VirtualHardDisk,
                                       CachingTypes,
                                       ContainerServiceOchestratorTypes,
                                       UpgradeMode)
from azure.mgmt.storage.models import SkuName
from azure.cli.core.commands import register_cli_argument, CliArgumentType, register_extra_cli_argument
from azure.cli.core.commands.arm import is_valid_resource_id
from azure.cli.core.commands.template_create import register_folded_cli_argument
from azure.cli.core.commands.parameters import \
    (location_type, get_location_completion_list, get_one_of_subscription_locations,
     get_resource_name_completion_list, tags_type, enum_choice_list)
from azure.cli.command_modules.vm._actions import \
    (VMImageFieldAction, VMSSHFieldAction, VMDNSNameAction, load_images_from_aliases_doc,
     get_vm_sizes, PrivateIpAction, _resource_not_exists)
from azure.cli.command_modules.vm._validators import \
    (validate_nsg_name, validate_vm_nics, validate_default_os_disk, validate_default_vnet, validate_default_storage_account)

def get_urn_aliases_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    images = load_images_from_aliases_doc()
    return [i['urnAlias'] for i in images]

def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]

# REUSABLE ARGUMENT DEFINITIONS

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
multi_ids_type = CliArgumentType(nargs='+')
admin_username_type = CliArgumentType(options_list=('--admin-username',), default=getpass.getuser(), required=False)
existing_vm_name = CliArgumentType(overrides=name_arg_type, help='The name of the virtual machine', completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'), id_part='name')
vmss_name_type = CliArgumentType(name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), help='Scale set name.', id_part='name')

# ARGUMENT REGISTRATION

register_cli_argument('vm', 'vm_name', existing_vm_name)
register_cli_argument('vm', 'size', completer=get_vm_size_completion_list)
register_cli_argument('vm', 'tags', tags_type)
register_cli_argument('vm', 'name', arg_type=name_arg_type)

register_cli_argument('vm disk', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm disk', 'disk_name', options_list=('--name', '-n'), help='The data disk name. If missing, will retrieve from vhd uri')
register_cli_argument('vm disk', 'disk_size', help='Size of disk (GiB)', default=1023, type=int)
register_cli_argument('vm disk', 'lun', type=int, help='0-based logical unit number (LUN). Max value depends on the Virutal Machine size.')
register_cli_argument('vm disk', 'vhd', type=VirtualHardDisk, help='virtual hard disk\'s uri. For example:https://mystorage.blob.core.windows.net/vhds/d1.vhd')
register_cli_argument('vm disk', 'caching', help='Host caching policy', default=CachingTypes.none.value, **enum_choice_list(CachingTypes))

for item in ['attach-existing', 'attach-new', 'detach']:
    register_cli_argument('vm disk {}'.format(item), 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',), id_part=None)

register_cli_argument('vm availability-set', 'availability_set_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')

register_cli_argument('vm access', 'username', options_list=('--username', '-u'), help='The user name')
register_cli_argument('vm access', 'password', options_list=('--password', '-p'), help='The user password')

register_cli_argument('acs', 'name', arg_type=name_arg_type)
register_cli_argument('acs', 'orchestrator_type', **enum_choice_list(ContainerServiceOchestratorTypes))
register_cli_argument('acs', 'admin_username', admin_username_type)
register_cli_argument('acs', 'ssh_key_value', required=False, help='SSH key file value or key file path.', default=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'), completer=FilesCompleter())
register_extra_cli_argument('acs create', 'generate_ssh_keys', action='store_true', help='Generate SSH public and private key files if missing')
register_cli_argument('acs', 'container_service_name', options_list=('--name', '-n'), help='The name of the container service', completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices'))
register_cli_argument('acs create', 'agent_vm_size', completer=get_vm_size_completion_list)
register_cli_argument('acs update', 'agent_count', type=int, help='The number of agents for the cluster')

register_cli_argument('vm capture', 'overwrite', action='store_true')

register_cli_argument('vm diagnostics', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm diagnostics set', 'storage_account', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))

register_cli_argument('vm extension', 'vm_extension_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'), id_part='child_name')
register_cli_argument('vm extension', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',), id_part='name')

register_cli_argument('vm extension image', 'image_location', options_list=('--location', '-l'))
register_cli_argument('vm extension image', 'publisher_name', options_list=('--publisher',))
register_cli_argument('vm extension image', 'type', options_list=('--name', '-n'))
register_cli_argument('vm extension image', 'latest', action='store_true')

for dest in ['vm_scale_set_name', 'virtual_machine_scale_set_name', 'name']:
    register_cli_argument('vmss', dest, vmss_name_type)
    register_cli_argument('vmss deallocate', dest, vmss_name_type, id_part=None) # due to instance-ids parameter
    register_cli_argument('vmss delete-instances', dest, vmss_name_type, id_part=None) # due to instance-ids parameter
    register_cli_argument('vmss restart', dest, vmss_name_type, id_part=None) # due to instance-ids parameter
    register_cli_argument('vmss start', dest, vmss_name_type, id_part=None) # due to instance-ids parameter
    register_cli_argument('vmss stop', dest, vmss_name_type, id_part=None) # due to instance-ids parameter
    register_cli_argument('vmss update-instances', dest, vmss_name_type, id_part=None) # due to instance-ids parameter

register_cli_argument('vmss', 'instance_id', id_part='child_name')
register_cli_argument('vmss', 'instance_ids', multi_ids_type)
register_cli_argument('vmss', 'tags', tags_type)
register_cli_argument('vmss', 'instance_ids', help='Space separated ids such as "0 2 3", or use "*" for all instances')

register_cli_argument('vmss extension', 'extension_name', name_arg_type, help='Name of the extension.')
register_cli_argument('vmss extension', 'vmss_name', id_part=None)
register_cli_argument('vmss diagnostics', 'vmss_name', id_part=None, help='Scale set name')

register_cli_argument('vmss extension image', 'publisher_name', options_list=('--publisher',), help='Image publisher name')
register_cli_argument('vmss extension image', 'type', options_list=('--name', '-n'), help='Extension name')
register_cli_argument('vmss extension image', 'latest', action='store_true')
register_cli_argument('vmss extension image', 'image_name', help='Image name')
register_cli_argument('vmss extension image', 'orderby', help='The sort to apply on the operation')
register_cli_argument('vmss extension image', 'top', help='Return top number of records')
register_cli_argument('vmss extension image', 'version', help='Extension version')

for scope in ['vm diagnostics', 'vmss diagnostics']:
    register_cli_argument(scope, 'version', help='version of the diagnostics extension. Will use the latest if not specfied')
    register_cli_argument(scope, 'settings', help='json string or a file path, which defines data to be collected.')
    register_cli_argument(scope, 'protected_settings', help='json string or a file path containing private configurations such as storage account keys, etc.')

for scope in ['vm', 'vmss']:
    register_cli_argument(scope, 'no_auto_upgrade', action='store_true', help='by doing this, extension system will not pick the highest minor version for the specified version number, and will not auto update to the latest build/revision number on any scale set updates in future.')

register_cli_argument('vm image list', 'image_location', location_type)

register_cli_argument('vm open-port', 'vm_name', name_arg_type, help='The name of the virtual machine to open inbound traffic on.')
register_cli_argument('vm open-port', 'network_security_group_name', options_list=('--nsg-name',), help='The name of the network security group to create if one does not exist. Ignored if an NSG already exists.', validator=validate_nsg_name)
register_cli_argument('vm open-port', 'apply_to_subnet', help='Allow inbound traffic on the subnet instead of the NIC', action='store_true')

register_cli_argument('vm nic', 'vm_name', existing_vm_name, id_part=None)
register_cli_argument('vm nic', 'nic_ids', multi_ids_type)
register_cli_argument('vm nic', 'nic_names', multi_ids_type)

register_cli_argument('vmss nic', 'virtual_machine_scale_set_name', options_list=('--vmss-name',), help='Scale set name.', completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')
register_cli_argument('vmss nic', 'virtualmachine_index', options_list=('--instance-id',), id_part='child_name')
register_cli_argument('vmss nic', 'network_interface_name', options_list=('--name', '-n'), metavar='NIC_NAME', help='The network interface (NIC).', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'), id_part='grandchild_name')

register_cli_argument('network nic scale-set list', 'virtual_machine_scale_set_name', options_list=('--vmss-name',), completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')

# VM CREATE PARAMETER CONFIGURATION

authentication_type = CliArgumentType(
    default=None,
    help='Password or SSH public key authentication. Defaults to password for Windows and SSH public key for Linux.',
    **enum_choice_list(['ssh', 'password'])
)

nsg_rule_type = CliArgumentType(
    default=None,
    help='Network security group rule to create. Defaults open ports for allowing RDP on Windows and allowing SSH on Linux.',
    **enum_choice_list(['RDP', 'SSH'])
)

register_cli_argument('vm create', 'network_interface_type', help=argparse.SUPPRESS)
register_cli_argument('vm create', 'network_interface_ids', options_list=('--nics',), nargs='+', help='Names or IDs of existing NICs to reference.  The first NIC will be the primary NIC.', type=lambda val: val if (not '/' in val or is_valid_resource_id(val, ValueError)) else '', validator=validate_vm_nics)
register_cli_argument('vm create', 'name', name_arg_type, validator=_resource_not_exists('Microsoft.Compute/virtualMachines'))

register_cli_argument('vmss create', 'name', name_arg_type)
register_cli_argument('vmss create', 'nat_backend_port', default=None, help='Backend port to open with NAT rules.  Defaults to 22 on Linux and 3389 on Windows.')

for scope in ['vm create', 'vmss create']:
    register_cli_argument(scope, 'location', completer=get_location_completion_list, help='Location in which to create the VM and related resources. If not specified, defaults to the resource group\'s location.')
    register_cli_argument(scope, 'custom_os_disk_uri', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_disk_type', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_disk_name', validator=validate_default_os_disk)
    register_cli_argument(scope, 'overprovision', action='store_false', default=None, options_list=('--disable-overprovision',))
    register_cli_argument(scope, 'upgrade_policy_mode', help=None, **enum_choice_list(UpgradeMode))
    register_cli_argument(scope, 'os_disk_uri', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_offer', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_publisher', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_sku', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_type', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'os_version', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'dns_name_type', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'admin_username', admin_username_type)
    register_cli_argument(scope, 'storage_type', help='The VM storage type.', **enum_choice_list(SkuName))
    register_cli_argument(scope, 'subnet_name', help='The subnet name.  Creates if creating a new VNet, references if referencing an existing VNet.')
    register_cli_argument(scope, 'admin_password', help='Password for the Virtual Machine if Authentication Type is Password.')
    register_cli_argument(scope, 'ssh_key_value', action=VMSSHFieldAction)
    register_cli_argument(scope, 'ssh_dest_key_path', completer=FilesCompleter())
    register_cli_argument(scope, 'dns_name_for_public_ip', action=VMDNSNameAction, options_list=('--public-ip-address-dns-name',), help='Globally unique DNS Name for the Public IP.')
    register_cli_argument(scope, 'authentication_type', authentication_type)
    register_folded_cli_argument(scope, 'availability_set', 'Microsoft.Compute/availabilitySets', new_flag_value=None, default_value_flag='none')
    register_cli_argument(scope, 'private_ip_address_allocation', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'virtual_network_ip_address_prefix', options_list=('--vnet-ip-address-prefix',))
    register_cli_argument(scope, 'subnet_ip_address_prefix', options_list=('--subnet-ip-address-prefix',))
    register_cli_argument(scope, 'private_ip_address', help='Static private IP address (e.g. 10.0.0.5).', options_list=('--private-ip-address',), action=PrivateIpAction)
    register_cli_argument(scope, 'public_ip_address_allocation', help='', default='dynamic', **enum_choice_list(['dynamic', 'static']))
    register_folded_cli_argument(scope, 'public_ip_address', 'Microsoft.Network/publicIPAddresses')
    register_folded_cli_argument(scope, 'storage_account', 'Microsoft.Storage/storageAccounts', validator=validate_default_storage_account, none_flag_value=None, default_value_flag='existingId')
    register_folded_cli_argument(scope, 'virtual_network', 'Microsoft.Network/virtualNetworks', options_list=('--vnet',), validator=validate_default_vnet, none_flag_value=None, default_value_flag='existingId')
    register_folded_cli_argument(scope, 'network_security_group', 'Microsoft.Network/networkSecurityGroups', options_list=('--nsg',))
    register_folded_cli_argument(scope, 'load_balancer', 'Microsoft.Network/loadBalancers')
    register_cli_argument(scope, 'network_security_group_rule', nsg_rule_type, options_list=('--nsg-rule',))
    register_extra_cli_argument(scope, 'image', options_list=('--image',), action=VMImageFieldAction, completer=get_urn_aliases_completion_list, required=True)

