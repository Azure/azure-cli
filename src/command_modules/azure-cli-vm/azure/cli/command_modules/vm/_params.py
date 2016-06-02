# pylint: disable=line-too-long
import argparse
import getpass
import os

from azure.mgmt.compute.models import VirtualHardDisk

from azure.cli.command_modules.vm._validators import MinMaxValue
from azure.cli.command_modules.vm._actions import (VMImageFieldAction,
                                                   VMSSHFieldAction,
                                                   VMDNSNameAction,
                                                   load_images_from_aliases_doc,
                                                   get_subscription_locations)
from azure.cli.commands.argument_types import register_cli_argument, CliArgumentType, location_type, register_additional_cli_argument

def get_location_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    result = get_subscription_locations()
    return [l.name for l in result]

def get_urn_aliases_completion_list(prefix, **kwargs):#pylint: disable=unused-argument
    images = load_images_from_aliases_doc()
    return [i['urn alias'] for i in images]

# BASIC PARAMETER CONFIGURATION
name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

admin_username_type = CliArgumentType(options_list=('--admin-username',), default=getpass.getuser(), required=False)

register_cli_argument('vm', 'vm_name', name_arg_type)
register_cli_argument('vm', 'vm_scale_set_name', name_arg_type)
register_cli_argument('vm', 'diskname', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('vm', 'disksize', CliArgumentType(help='Size of disk (Gb)', default=1023, type=MinMaxValue(1, 1023)))
register_cli_argument('vm', 'lun', CliArgumentType(
    type=int, help='0-based logical unit number (LUN). Max value depends on the Virutal Machine size.'))
register_cli_argument('vm', 'vhd', CliArgumentType(type=VirtualHardDisk))

register_cli_argument('vm availability-set', 'availability_set_name', name_arg_type)

register_cli_argument('vm create', 'name', name_arg_type)
register_cli_argument('vm create', 'location', CliArgumentType(completer=get_location_completion_list))
register_cli_argument('vm create', 'os_disk_uri', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'os_offer', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'os_publisher', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'os_sku', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'os_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'os_verion', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'dns_name_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('vm create', 'admin_username', admin_username_type)
register_cli_argument('vm create', 'ssh_key_value', CliArgumentType(action=VMSSHFieldAction))
register_cli_argument('vm create', 'dns_name_for_public_ip', CliArgumentType(action=VMDNSNameAction))
register_cli_argument('vm create', 'authentication_type', CliArgumentType(
    choices=['ssh', 'password'], default=None,
    help='Password or SSH public key authentication. Defaults to password for Windows and SSH public key for Linux.'
))
register_cli_argument('vm create', 'availability_set_type', CliArgumentType(choices=['none', 'existing'], help='', default='none'))
register_cli_argument('vm create', 'private_ip_address_allocation', CliArgumentType(
    choices=['dynamic', 'static'], help='', default='dynamic'))
register_cli_argument('vm create', 'public_ip_address_allocation', CliArgumentType(
    choices=['dynamic', 'static'], help='', default='dynamic'))
register_cli_argument('vm create', 'public_ip_address_type', CliArgumentType(
    choices=['none', 'new', 'existing'], help='', default='new'))
register_cli_argument('vm create', 'storage_account_type', CliArgumentType(
    choices=['new', 'existing'], help='', default='new'))
register_cli_argument('vm create', 'virtual_network_type', CliArgumentType(
    choices=['new', 'existing'], help='', default='new'))
register_cli_argument('vm create', 'network_security_group_rule', CliArgumentType(
    choices=['RDP', 'SSH'], default=None,
    help='Network security group rule to create. Defaults to RDP for Windows and SSH for Linux'
))
register_cli_argument('vm create', 'network_security_group_type', CliArgumentType(
    choices=['new', 'existing', 'none'], help='', default='new'))
register_additional_cli_argument('vm create', 'image', options_list=('--image',), action=VMImageFieldAction, completer=get_urn_aliases_completion_list)

register_cli_argument('vm access', 'username', CliArgumentType(options_list=('--username', '-u'), help='The user name'))
register_cli_argument('vm access', 'password', CliArgumentType(options_list=('--password', '-p'), help='The user name'))

register_cli_argument('vm container', 'orchestrator_type', CliArgumentType(choices=['docs', 'swarm']))
register_cli_argument('vm container', 'admin_username', admin_username_type)
register_cli_argument(
    'vm container', 'ssh_key_value', CliArgumentType(
        required=False,
        help='SSH key file value or key file path.',
        default=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')
    )
)

register_cli_argument('vm diagnostics', 'vm_name', CliArgumentType(options_list=('--vm-name',)))

register_cli_argument('vm extension', 'vm_extension_name', name_arg_type)
register_cli_argument('vm extension', 'vm_name', CliArgumentType(options_list=('--vm-name',)))
register_cli_argument('vm extension', 'auto_upgrade_minor_version', CliArgumentType(action='store_true'))

register_cli_argument('vm extension image', 'image_location', CliArgumentType(options_list=('--location', '-l')))
register_cli_argument('vm extension image', 'publisher_name', CliArgumentType(options_list=('--publisher',)))
register_cli_argument('vm extension image', 'type', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('vm extension image', 'latest', CliArgumentType(action='store_true'))

register_cli_argument('vm image list', 'image_location', location_type)

register_additional_cli_argument('vm scaleset create', 'image', options_list=('--image',), action=VMImageFieldAction, completer=get_urn_aliases_completion_list, default='Win2012R2Datacenter')
