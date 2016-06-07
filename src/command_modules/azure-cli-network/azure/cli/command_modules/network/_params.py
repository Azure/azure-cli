# pylint: disable=line-too-long
import argparse

from azure.cli.command_modules.network._actions import LBDNSNameAction
from azure.cli.commands.parameters import location_type
from azure.cli.commands import register_cli_argument, CliArgumentType
# FACTORIES


# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')

virtual_network_name_type = CliArgumentType(options_list=('--virtual-network-name',), metavar='VNET', help='the name of the VNET')

register_cli_argument('network', 'subnet_name', name_arg_type)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type)

register_cli_argument('network express-route circuit-auth', 'authorization_name', name_arg_type)
register_cli_argument('network express-route circuit-peering', 'peering_name', name_arg_type)
register_cli_argument('network express-route circuit', 'circuit_name', name_arg_type)

register_cli_argument('network lb', 'load_balancer_name', name_arg_type)

register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type)

register_cli_argument('network nic', 'network_interface_name', name_arg_type)

register_cli_argument('network nic scale-set', 'virtual_machine_scale_set_name', CliArgumentType(('--vm-scale-set',)))
register_cli_argument('network nic scale-set', 'virtualmachine_index', CliArgumentType(('--vm-index',)))

register_cli_argument('network nsg', 'network_security_group_name', name_arg_type)

register_cli_argument('network nsg-rule', 'security_rule_name', name_arg_type)
register_cli_argument('network nsg-rule', 'network_security_group_name', CliArgumentType(('--nsg-name',), metavar='NSGNAME'))

register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type)

register_cli_argument('network route-operation', 'route_name', name_arg_type)

register_cli_argument('network route-table', 'route_table_name', name_arg_type)

register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'))

# BUG: we are waiting on autorest to support this rename
# (https://github.com/Azure/autorest/issues/941)
register_cli_argument('network vnet create', 'deployment_parameter_location_value', location_type)
register_cli_argument('network vnet create', 'deployment_parameter_subnet_prefix_value', CliArgumentType(
    options_list=('--subnet-prefix',), metavar='SUBNET_PREFIX', default='10.0.0.0/24'))
register_cli_argument('network vnet create', 'deployment_parameter_subnet_name_value', CliArgumentType(
    options_list=('--subnet-name',), metavar='SUBNET_NAME', default='Subnet1'))
register_cli_argument('network vnet create', 'deployment_parameter_virtual_network_prefix_value', CliArgumentType(
    options_list=('--vnet-prefix',), metavar='VNET_PREFIX', default='10.0.0.0/16'))
register_cli_argument('network vnet create', 'deployment_parameter_virtual_network_name_value', CliArgumentType(
    options_list=('--name', '-n'), metavar='VNET_NAME', required=True
))

register_cli_argument('network vnet subnet', 'subnet_name', CliArgumentType(options_list=('--name', '-n'), help='the subnet name'))
register_cli_argument('network vnet subnet', 'address_prefix', CliArgumentType(metavar='PREFIX', help='the address prefix in CIDR format.'))
register_cli_argument('network vnet subnet', 'virtual_network_name', virtual_network_name_type)

register_cli_argument('network lb create', 'dns_name_for_public_ip', CliArgumentType(action=LBDNSNameAction))
register_cli_argument('network lb create', 'dns_name_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network lb create', 'private_ip_address_allocation', CliArgumentType(help='', choices=['dynamic', 'static'], default='dynamic'))
register_cli_argument('network lb create', 'public_ip_address_allocation', CliArgumentType(help='', choices=['dynamic', 'static'], default='dynamic'))

register_cli_argument('network public-ip create', 'public_ip_address_type', CliArgumentType(options_list=('--public-ip-address-type',)), help=argparse.SUPPRESS)

register_cli_argument('network vpn-gateway', 'virtual_network_gateway_name', CliArgumentType(options_list=('--name', '-n')))

register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--name', '-n'), metavar='NAME'))

register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--connection-name',), metavar='NAME'))
