# pylint: disable=line-too-long
import argparse

from azure.cli.command_modules.network._actions import LBDNSNameAction, PublicIpDnsNameAction
from azure.cli.command_modules.network._validators import _process_nic_namespace
from azure.cli.commands.parameters import (location_type, get_resource_name_completion_list)
from azure.cli.commands import register_cli_argument, CliArgumentType

# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='VNET_NAME', help='Name of the virtual network.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME')
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NSG', help='Name of the network security group.')

register_cli_argument('network', 'subnet_name', name_arg_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network', 'network_security_group_name', nsg_name_type)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'))

register_cli_argument('network express-route circuit-auth', 'authorization_name', name_arg_type)
register_cli_argument('network express-route circuit-peering', 'peering_name', name_arg_type)
register_cli_argument('network express-route circuit', 'circuit_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))

register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'))

register_cli_argument('network nic', 'network_interface_name', name_arg_type)
register_cli_argument('network nic', 'subnet_name', options_list=('--subnet-name',))
register_cli_argument('network nic', 'enable_ip_forwarding', options_list=('--ip-forwarding',), action='store_true')
register_cli_argument('network nic', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'network_security_group_type', help=argparse.SUPPRESS, validator=_process_nic_namespace)
register_cli_argument('network nic', 'public_ip_address_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'load_balancer_backend_address_pool_ids', options_list=('--lb-address-pool-ids',))
register_cli_argument('network nic', 'load_balancer_incoming_nat_rule_ids', options_list=('--lb-nat-rule-ids',))

register_cli_argument('network nic scale-set', 'virtual_machine_scale_set_name', options_list=('--vm-scale-set',), completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))
register_cli_argument('network nic scale-set', 'virtualmachine_index', options_list=('--vm-index',))

register_cli_argument('network nsg', 'network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

register_cli_argument('network nsg rule', 'security_rule_name', name_arg_type)
register_cli_argument('network nsg rule', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME',
                      help='Name of the network security group')
register_cli_argument('network nsg rule create', 'priority', default=1000)

register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network public-ip', 'name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

register_cli_argument('network public-ip create', 'name', completer=None)
register_cli_argument('network public-ip create', 'dns_name', CliArgumentType(action=PublicIpDnsNameAction))
register_cli_argument('network public-ip create', 'public_ip_address_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network public-ip create', 'allocation_method', CliArgumentType(choices=['dynamic', 'static'], default='dynamic'))

register_cli_argument('network route-operation', 'route_name', name_arg_type)

register_cli_argument('network route-table', 'route_table_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/routeTables'))

register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'))

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_prefix', CliArgumentType(options_list=('--subnet-prefix',), metavar='SUBNET_PREFIX', default='10.0.0.0/24'))
register_cli_argument('network vnet create', 'subnet_name', CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME', default='Subnet1'))
register_cli_argument('network vnet create', 'virtual_network_prefix', CliArgumentType(options_list=('--vnet-prefix',), metavar='VNET_PREFIX', default='10.0.0.0/16'))
register_cli_argument('network vnet create', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), required=True, completer=None)

register_cli_argument('network vnet subnet', 'subnet_name', options_list=('--name', '-n'), help='the subnet name')
register_cli_argument('network vnet subnet', 'address_prefix', metavar='PREFIX', help='the address prefix in CIDR format.', default='10.0.0.0/24')
register_cli_argument('network vnet subnet', 'virtual_network_name', virtual_network_name_type)

register_cli_argument('network lb', 'load_balancer_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))

register_cli_argument('network lb create', 'dns_name_for_public_ip', CliArgumentType(action=LBDNSNameAction))
register_cli_argument('network lb create', 'dns_name_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network lb create', 'private_ip_address_allocation', CliArgumentType(help='', choices=['dynamic', 'static'], default='dynamic'))
register_cli_argument('network lb create', 'public_ip_address_allocation', CliArgumentType(help='', choices=['dynamic', 'static'], default='dynamic'))
register_cli_argument('network lb create', 'public_ip_address_type', CliArgumentType(help='', choices=['new', 'existing', 'none'], default='new'))
register_cli_argument('network lb create', 'subnet_name', CliArgumentType(options_list=('--subnet-name',)))

register_cli_argument('network nsg create', 'name', name_arg_type)

register_cli_argument('network vpn-gateway', 'virtual_network_gateway_name', CliArgumentType(options_list=('--name', '-n'), completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways')))

register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--name', '-n'), metavar='NAME'))

register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--connection-name',), metavar='NAME'))

