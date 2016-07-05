# pylint: disable=line-too-long
import argparse

from azure.mgmt.network.models import IPAllocationMethod
from azure.cli.command_modules.network._actions import LBDNSNameAction, PublicIpDnsNameAction
from azure.cli.command_modules.network._validators import process_nic_namespace
from azure.cli.commands.parameters import (location_type, get_resource_name_completion_list, register_id_parameter)
from azure.cli.commands import register_cli_argument, CliArgumentType

# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='VNET_NAME', help='Name of the virtual network.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME')
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NSG', help='Name of the network security group.')

choices_ip_allocation_method = [e.value.lower() for e in IPAllocationMethod]

register_cli_argument('network', 'subnet_name', name_arg_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network', 'network_security_group_name', nsg_name_type)

# Application-Gateway
register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'))
for name in ('delete',
             'show',
             'start',
             'stop'):
    register_id_parameter('network application-gateway ' + name, 'resource_group_name', 'application_gateway_name')

# Express Route Circuit Auth
register_cli_argument('network express-route circuit-auth', 'authorization_name', name_arg_type)
for name in ('delete',
             'show'):
    register_id_parameter('network express-route circuit-auth ' + name, 'resource_group_name', 'circuit_name', 'authorization_name')

# Express Route Circuit Peering
register_cli_argument('network express-route circuit-peering', 'peering_name', name_arg_type)
for name in ('delete',
             'show'):
    register_id_parameter('network express-route circuit-peering ' + name, 'resource_group_name', 'circuit_name', 'peering_name')

# Express Route Circuit
register_cli_argument('network express-route circuit', 'circuit_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))
for name in ('delete',
             'get-stats',
             'list-arp',
             'list-routes',
             'show'):
    register_id_parameter('network express-route circuit ' + name, 'resource_group_name', 'circuit_name')

# Local Gateway
register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'))
for name in ('delete',
             'show'):
    register_id_parameter('network local-gateway ' + name, 'resource_group_name', 'local_network_gateway_name')

# NIC
register_cli_argument('network nic', 'network_interface_name', name_arg_type)
register_cli_argument('network nic', 'subnet_name', options_list=('--subnet-name',))
register_cli_argument('network nic', 'enable_ip_forwarding', options_list=('--ip-forwarding',), action='store_true')
register_cli_argument('network nic', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'network_security_group_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'public_ip_address_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'load_balancer_backend_address_pool_ids', options_list=('--lb-address-pool-ids',), nargs='+')
register_cli_argument('network nic', 'load_balancer_inbound_nat_rule_ids', options_list=('--lb-nat-rule-ids',), nargs='+')
register_cli_argument('network nic create', 'network_interface_name', name_arg_type, validator=process_nic_namespace)
for name in ('delete',
             'show'):
    register_id_parameter('network nic ' + name, 'resource_group_name', 'network_interface_name')

# NIC ScaleSet
register_cli_argument('network nic scale-set', 'virtual_machine_scale_set_name', options_list=('--vm-scale-set',), completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))
register_cli_argument('network nic scale-set', 'virtualmachine_index', options_list=('--vm-index',))
for name in ('show',):
    register_id_parameter('network nic scale-set ' + name, 'resource_group_name', 'virtual_machine_scale_set_name', 'network_interface_name')
for name in ('list', 'list-vm-nics'):
    register_id_parameter('network nic scale-set ' + name, 'resource_group_name', 'virtual_machine_scale_set_name')

# NSG
register_cli_argument('network nsg', 'network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))
register_cli_argument('network nsg create', 'name', name_arg_type)
for name in ('delete',
             'rule list',
             'show'):
    register_id_parameter('network nsg ' + name, 'resource_group_name', 'network_security_group_name')

# NSG Rule
register_cli_argument('network nsg rule', 'security_rule_name', name_arg_type)
register_cli_argument('network nsg rule', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME',
                      help='Name of the network security group')
register_cli_argument('network nsg rule create', 'priority', default=1000)
for name in ('delete',
             'show'):
    register_id_parameter('network nsg rule ' + name, 'resource_group_name', 'network_security_group_name', 'security_rule_name')

# Public IP
register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network public-ip', 'name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

register_cli_argument('network public-ip create', 'name', completer=None)
register_cli_argument('network public-ip create', 'dns_name', CliArgumentType(action=PublicIpDnsNameAction))
register_cli_argument('network public-ip create', 'public_ip_address_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network public-ip create', 'allocation_method', CliArgumentType(choices=choices_ip_allocation_method, default='dynamic', type=str.lower))
for name in ('delete',
             'show'):
    register_id_parameter('network public-ip ' + name, 'resource_group_name', 'public_ip_address_name')

# Route Operation
register_cli_argument('network route-operation', 'route_name', name_arg_type)
for name in ('delete',
             'show'):
    register_id_parameter('network route-operation ' + name, 'resource_group_name', 'route_table_name', 'route_name')

# Route table
register_cli_argument('network route-table', 'route_table_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/routeTables'))
for name in ('delete',
             'show'):
    register_id_parameter('network route-table ' + name, 'resource_group_name', 'route_table_name')

# VNET
register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'))

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_prefix', CliArgumentType(options_list=('--subnet-prefix',), metavar='SUBNET_PREFIX', default='10.0.0.0/24'))
register_cli_argument('network vnet create', 'subnet_name', CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME', default='Subnet1'))
register_cli_argument('network vnet create', 'virtual_network_prefix', CliArgumentType(options_list=('--vnet-prefix',), metavar='VNET_PREFIX', default='10.0.0.0/16'))
register_cli_argument('network vnet create', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), required=True, completer=None)
for name in ('delete',
             'show',
             'subnet list'):
    register_id_parameter('network vnet ' + name, 'resource_group_name', 'virtual_network_name')

# VNET subnet
register_cli_argument('network vnet subnet', 'subnet_name', options_list=('--name', '-n'), help='the subnet name')
register_cli_argument('network vnet subnet', 'address_prefix', metavar='PREFIX', help='the address prefix in CIDR format.')
register_cli_argument('network vnet subnet', 'virtual_network_name', virtual_network_name_type)
for name in ('delete',
             'show'):
    register_id_parameter('network vnet subnet ' + name, 'resource_group_name', 'virtual_network_name', 'subnet_name')

# LoadBalancer
register_cli_argument('network lb', 'load_balancer_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))

register_cli_argument('network lb create', 'dns_name_for_public_ip', CliArgumentType(action=LBDNSNameAction))
register_cli_argument('network lb create', 'dns_name_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network lb create', 'private_ip_address_allocation', CliArgumentType(help='', choices=choices_ip_allocation_method, type=str.lower))
register_cli_argument('network lb create', 'public_ip_address_allocation', CliArgumentType(help='', choices=choices_ip_allocation_method, type=str.lower))
register_cli_argument('network lb create', 'public_ip_address_type', CliArgumentType(help='', choices=['new', 'existing', 'none'], type=str.lower))
register_cli_argument('network lb create', 'subnet_name', CliArgumentType(options_list=('--subnet-name',)))
for name in ('delete',
             'show'):
    register_id_parameter('network lb ' + name, 'resource_group_name', 'load_balancer_name')

# VPN gateway
register_cli_argument('network vpn-gateway', 'virtual_network_gateway_name', CliArgumentType(options_list=('--name', '-n'), completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways')))
for name in ('delete',
             'show'):
    register_id_parameter('network vpn-gateway ' + name, 'resource_group_name', 'virtual_network_gateway_name')

# VPN connection
register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--name', '-n'), metavar='NAME'))
for name in ('delete',
             'show'):
    register_id_parameter('network vpn-connection ' + name, 'resource_group_name', 'virtual_network_gateway_connection_name')

# VPN connection shared key
register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--connection-name',), metavar='NAME'))
for name in ('show',):
    register_id_parameter('network vpn-connection shared-key ' + name, 'resource_group_name', 'connection_shared_key_name')
for name in ('reset', 'set'):
    register_id_parameter('network vpn-connection shared-key ' + name, 'resource_group_name', 'virtual_network_gateway_connection_name')
