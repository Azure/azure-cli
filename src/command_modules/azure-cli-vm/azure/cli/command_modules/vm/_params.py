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
from azure.mgmt.network.models import IPAllocationMethod
from azure.cli.command_modules.vm._actions import (VMImageFieldAction,
                                                   VMSSHFieldAction,
                                                   VMDNSNameAction,
                                                   load_images_from_aliases_doc,
                                                   get_vm_sizes,
                                                   _handle_vm_nics,
                                                   PrivateIpAction,
                                                   _resource_not_exists,
                                                   _os_disk_default,
                                                   _find_default_vnet,
                                                   _find_default_storage_account)
from azure.cli.commands.parameters import (location_type,
                                           get_location_completion_list,
                                           get_one_of_subscription_locations,
                                           get_resource_name_completion_list,
                                           tags_type)
from azure.cli.command_modules.vm._validators import nsg_name_validator
from azure.cli.commands import register_cli_argument, CliArgumentType, register_extra_cli_argument
from azure.cli.commands.arm import is_valid_resource_id
from azure.cli.commands.template_create import register_folded_cli_argument

def get_urn_aliases_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    images = load_images_from_aliases_doc()
    return [i['urn alias'] for i in images]

def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):#pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]

# BASIC PARAMETER CONFIGURATION
choices_caching_types = [e.value for e in CachingTypes]
choices_container_service_orchestrator_types = [e.value for e in ContainerServiceOchestratorTypes]
choices_upgrade_mode = [e.value.lower() for e in UpgradeMode]
choices_ip_allocation_method = [e.value.lower() for e in IPAllocationMethod]

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
multi_ids_type = CliArgumentType(
    nargs='+'
)

admin_username_type = CliArgumentType(options_list=('--admin-username',), default=getpass.getuser(), required=False)
existing_vm_name = CliArgumentType(overrides=name_arg_type, help='The name of the virtual machine', completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines'), id_part='name')
register_cli_argument('vm', 'vm_name', existing_vm_name)
register_cli_argument('vm', 'size', CliArgumentType(completer=get_vm_size_completion_list))
register_cli_argument('vm', 'tags', tags_type)
register_cli_argument('vm', 'name', arg_type=name_arg_type)

register_cli_argument('vmss', 'vm_scale_set_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'), id_part='name')
register_cli_argument('vmss', 'virtual_machine_scale_set_name', name_arg_type)
register_cli_argument('vmss', 'instance_ids', multi_ids_type)
register_cli_argument('vmss', 'tags', tags_type)
register_cli_argument('vmss', 'name', arg_type=name_arg_type)
register_cli_argument('vm disk', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm disk', 'disk_name', CliArgumentType(options_list=('--name', '-n'), help='The data disk name. If missing, will retrieve from vhd uri'))
register_cli_argument('vm disk', 'disk_size', CliArgumentType(help='Size of disk (GiB)', default=1023, type=int))
register_cli_argument('vm disk', 'lun', CliArgumentType(
    type=int, help='0-based logical unit number (LUN). Max value depends on the Virutal Machine size.'))
register_cli_argument('vm disk', 'vhd', CliArgumentType(type=VirtualHardDisk, help='virtual hard disk\'s uri. For example:https://mystorage.blob.core.windows.net/vhds/d1.vhd'))
register_cli_argument('vm disk', 'caching', CliArgumentType(help='Host caching policy', default=CachingTypes.none.value, choices=choices_caching_types))

register_cli_argument('vm availability-set', 'availability_set_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/availabilitySets'), help='Name of the availability set')

register_cli_argument('vm access', 'username', CliArgumentType(options_list=('--username', '-u'), help='The user name'))
register_cli_argument('vm access', 'password', CliArgumentType(options_list=('--password', '-p'), help='The user password'))

register_cli_argument('vm container', 'orchestrator_type', CliArgumentType(choices=choices_container_service_orchestrator_types))
register_cli_argument('vm container', 'admin_username', admin_username_type)
register_cli_argument(
    'vm container', 'ssh_key_value', CliArgumentType(
        required=False,
        help='SSH key file value or key file path.',
        default=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub'),
        completer=FilesCompleter()
    )
)
register_cli_argument('vm container', 'container_service_name', CliArgumentType(overrides=name_arg_type, help='The name of the container service', completer=get_resource_name_completion_list('Microsoft.ContainerService/ContainerServices')))
register_cli_argument('vm container create', 'agent_vm_size', CliArgumentType(completer=get_vm_size_completion_list))

register_cli_argument('vm capture', 'overwrite', CliArgumentType(action='store_true'))
register_cli_argument('vm nic', 'nic_ids', multi_ids_type)
register_cli_argument('vm nic', 'nic_names', multi_ids_type)
register_cli_argument('vm diagnostics', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm diagnostics set', 'storage_account', completer=get_resource_name_completion_list('Microsoft.Storage/storageAccounts'))

register_cli_argument('vm extension', 'vm_extension_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachines/extensions'))
register_cli_argument('vm extension', 'vm_name', arg_type=existing_vm_name, options_list=('--vm-name',))
register_cli_argument('vm extension', 'auto_upgrade_minor_version', CliArgumentType(action='store_true'))

register_cli_argument('vm extension image', 'image_location', CliArgumentType(options_list=('--location', '-l')))
register_cli_argument('vm extension image', 'publisher_name', CliArgumentType(options_list=('--publisher',)))
register_cli_argument('vm extension image', 'type', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('vm extension image', 'latest', CliArgumentType(action='store_true'))

register_cli_argument('vm image list', 'image_location', location_type)

register_cli_argument('vm open-port', 'vm_name', name_arg_type, help='The name of the virtual machine to open inbound traffic on.')
register_cli_argument('vm open-port', 'network_security_group_name', options_list=('--nsg-name',), help='The name of the network security group to create if one does not exist. Ignored if an NSG already exists.', validator=nsg_name_validator)
register_cli_argument('vm open-port', 'apply_to_subnet', help='Allow inbound traffic on the subnet instead of the NIC', action='store_true')

# VM CREATE PARAMETER CONFIGURATION

authentication_type = CliArgumentType(
    choices=['ssh', 'password'], default=None,
    help='Password or SSH public key authentication. Defaults to password for Windows and SSH public key for Linux.',
    type=str.lower
)

nsg_rule_type = CliArgumentType(
    choices=['RDP', 'SSH'], default=None,
    help='Network security group rule to create. Defaults open ports for allowing RDP on Windows and allowing SSH on Linux.',
    type=str.upper
)

register_cli_argument('vm create', 'network_interface_type', help=argparse.SUPPRESS)
register_cli_argument('vm create', 'network_interface_ids', options_list=('--nics',), nargs='+',
                      help='Names or IDs of existing NICs to reference.  The first NIC will be the primary NIC.',
                      type=lambda val: val if (not '/' in val or is_valid_resource_id(val, ValueError)) else '',
                      validator=_handle_vm_nics)

register_cli_argument('vm create', 'name', name_arg_type, validator=_resource_not_exists('Microsoft.Compute/virtualMachines'))
register_cli_argument('vmss create', 'name', name_arg_type, validator=_resource_not_exists('Microsoft.Compute/virtualMachineScaleSets'))
register_cli_argument('vmss', 'vm_scale_set_name', name_arg_type, help='scale set name')
register_cli_argument('vmss', 'instance_ids',
                      help='Space separated ids such as "0 2 3", or use "*" for all instances')

for scope in ['vm create', 'vmss create']:
    register_cli_argument(scope, 'location', CliArgumentType(completer=get_location_completion_list))
    register_cli_argument(scope, 'custom_os_disk_uri', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_disk_type', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_disk_name', CliArgumentType(validator=_os_disk_default))
    register_cli_argument(scope, 'overprovision', CliArgumentType(action='store_false', default=None, options_list=('--disable-overprovision',)))
    register_cli_argument(scope, 'upgrade_policy_mode', CliArgumentType(choices=choices_upgrade_mode, help=None, type=str.lower))
    register_cli_argument(scope, 'os_disk_uri', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_offer', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_publisher', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_sku', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_type', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'os_version', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'dns_name_type', CliArgumentType(help=argparse.SUPPRESS))
    register_cli_argument(scope, 'admin_username', admin_username_type)
    register_cli_argument(scope, 'storage_type', help='The VM storage type.')
    register_cli_argument(scope, 'subnet_name', help='The subnet name.  Creates if creating a new VNet, references if referencing an existing VNet.')
    register_cli_argument(scope, 'admin_password', help='Password for the Virtual Machine if Authentication Type is Password.')
    register_cli_argument(scope, 'ssh_key_value', CliArgumentType(action=VMSSHFieldAction))
    register_cli_argument(scope, 'ssh_dest_key_path', completer=FilesCompleter())
    register_cli_argument(scope, 'dns_name_for_public_ip', CliArgumentType(action=VMDNSNameAction), options_list=('--public-ip-address-dns-name',), help='Globally unique DNS Name for the Public IP.')
    register_cli_argument(scope, 'authentication_type', authentication_type)
    register_folded_cli_argument(scope, 'availability_set', 'Microsoft.Compute/availabilitySets')
    register_cli_argument(scope, 'private_ip_address_allocation', help=argparse.SUPPRESS)
    register_cli_argument(scope, 'virtual_network_ip_address_prefix', options_list=('--vnet-ip-address-prefix',))
    register_cli_argument(scope, 'subnet_ip_address_prefix', options_list=('--subnet-ip-address-prefix',))
    register_cli_argument(scope, 'private_ip_address', help='Static private IP address (e.g. 10.0.0.5).', options_list=('--private-ip-address',), action=PrivateIpAction)
    register_cli_argument(scope, 'public_ip_address_allocation', CliArgumentType(choices=['dynamic', 'static'], help='', default='dynamic', type=str.lower))
    register_folded_cli_argument(scope, 'public_ip_address', 'Microsoft.Network/publicIPAddresses', help='Name or ID of public IP address (creates if doesn\'t exist)')
    register_folded_cli_argument(scope, 'storage_account', 'Microsoft.Storage/storageAccounts', help='Name or ID of storage account (creates if doesn\'t exist).  Chooses an existing storage account if none specified.', validator=_find_default_storage_account)
    register_folded_cli_argument(scope, 'virtual_network', 'Microsoft.Network/virtualNetworks', help='Name or ID of virtual network (creates if doesn\'t exist).  Chooses an existing VNet if none specified.', options_list=('--vnet',), validator=_find_default_vnet)
    register_folded_cli_argument(scope, 'network_security_group', 'Microsoft.Network/networkSecurityGroups', help='Name or ID of network security group (creates if doesn\'t exist)', options_list=('--nsg',))
    register_folded_cli_argument(scope, 'load_balancer', 'Microsoft.Network/loadBalancers', help='Name or ID of load balancer (creates if doesn\'t exist)')
    register_cli_argument(scope, 'network_security_group_rule', nsg_rule_type, options_list=('--nsg-rule',))
    register_extra_cli_argument(scope, 'image', options_list=('--image',), action=VMImageFieldAction, completer=get_urn_aliases_completion_list, default='Win2012R2Datacenter')
