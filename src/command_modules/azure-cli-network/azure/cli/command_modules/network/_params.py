# pylint: disable=line-too-long
import argparse

from azure.mgmt.network.models import IPAllocationMethod
from azure.cli.command_modules.network._validators import \
    (process_nic_namespace, process_network_lb_create_namespace, process_public_ip_create_namespace,
     validate_public_ip_type, validate_nsg_name_or_id)
from azure.cli.commands.template_create import register_folded_cli_argument
from azure.cli.commands.arm import is_valid_resource_id
from azure.cli.commands.parameters import (location_type, get_resource_name_completion_list)
from azure.cli.commands import register_cli_argument, CliArgumentType
from azure.cli.commands.parameters import (location_type, get_resource_name_completion_list)
from azure.cli.command_modules.network._actions import LBDNSNameAction, PublicIpDnsNameAction
from azure.cli.command_modules.network._validators import \
    (process_nic_namespace, process_app_gateway_namespace, validate_servers, validate_cert)
from azure.cli.command_modules.network._param_folding import register_folded_cli_argument

# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NSG', help='Name of the network security group.')
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='VNET_NAME', help='The virtual network (VNET) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME', help='The subnet name.')
load_balancer_name_type = CliArgumentType(options_list=('--lb-name',), metavar='LB_NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))

choices_ip_allocation_method = [e.value.lower() for e in IPAllocationMethod]

register_cli_argument('network', 'subnet_name', subnet_name_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network', 'network_security_group_name', nsg_name_type)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'))
register_cli_argument('network application-gateway', 'virtual_network_name', virtual_network_name_type)
register_folded_cli_argument('network application-gateway', 'subnet', 'Microsoft.Network/subnets')
register_folded_cli_argument('network application-gateway', 'public_ip', 'Microsoft.Network/publicIPAddresses')
register_cli_argument('network application-gateway', 'virtual_network_type', help=argparse.SUPPRESS)
register_cli_argument('network application-gateway', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network application-gateway', 'frontend_type', help=argparse.SUPPRESS, validator=process_app_gateway_namespace)
register_cli_argument('network application-gateway', 'servers', nargs='+', validator=validate_servers)
register_cli_argument('network application-gateway', 'cert_data', options_list=('--cert-file',), help='The path to the PFX certificate file.', validator=validate_cert)
register_cli_argument('network application-gateway', 'http_listener_protocol', help=argparse.SUPPRESS)

register_cli_argument('network express-route circuit-auth', 'authorization_name', name_arg_type)
register_cli_argument('network express-route circuit-peering', 'peering_name', name_arg_type)
register_cli_argument('network express-route circuit', 'circuit_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))

register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'))

register_cli_argument('network nic', 'network_interface_name', name_arg_type)
register_cli_argument('network nic', 'subnet_name', options_list=('--subnet-name',))
register_cli_argument('network nic', 'enable_ip_forwarding', options_list=('--ip-forwarding',), action='store_true')
register_cli_argument('network nic', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'network_security_group_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'public_ip_address_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'load_balancer_backend_address_pool_ids', options_list=('--lb-address-pool-ids',), nargs='+', type=lambda val: val if is_valid_resource_id(val, ValueError) else '')
register_cli_argument('network nic', 'load_balancer_inbound_nat_rule_ids', options_list=('--lb-nat-rule-ids',), nargs='+', type=lambda val: val if is_valid_resource_id(val, ValueError) else '')
register_cli_argument('network nic create', 'network_interface_name', name_arg_type, validator=process_nic_namespace)

register_cli_argument('network nic scale-set', 'virtual_machine_scale_set_name', options_list=('--vm-scale-set',), completer=get_resource_name_completion_list('Microsoft.Compute/virtualMachineScaleSets'))
register_cli_argument('network nic scale-set', 'virtualmachine_index', options_list=('--vm-index',))

register_cli_argument('network nsg', 'network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

register_cli_argument('network nsg rule', 'security_rule_name', name_arg_type)
register_cli_argument('network nsg rule', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME', help='Name of the network security group')
register_cli_argument('network nsg rule create', 'priority', default=1000)

register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network public-ip', 'name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

register_cli_argument('network public-ip create', 'name', completer=None)
register_cli_argument('network public-ip create', 'dns_name', CliArgumentType(validator=process_public_ip_create_namespace))
register_cli_argument('network public-ip create', 'public_ip_address_type', CliArgumentType(help=argparse.SUPPRESS))
register_cli_argument('network public-ip create', 'allocation_method', CliArgumentType(choices=choices_ip_allocation_method, type=str.lower))

register_cli_argument('network route-operation', 'route_name', name_arg_type)

register_cli_argument('network route-table', 'route_table_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/routeTables'))

register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'))

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_prefix', options_list=('--subnet-prefix',), metavar='SUBNET_PREFIX', default='10.0.0.0/24')
register_cli_argument('network vnet create', 'subnet_name', options_list=('--subnet-name',), metavar='SUBNET_NAME', default='Subnet1')
register_cli_argument('network vnet create', 'virtual_network_prefix', options_list=('--vnet-prefix',), metavar='VNET_PREFIX', default='10.0.0.0/16')
register_cli_argument('network vnet create', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), required=True, completer=None)

register_cli_argument('network vnet set', 'address_prefixes', nargs='+')

register_cli_argument('network vnet subnet', 'subnet_name', arg_type=subnet_name_type, options_list=('--name', '-n'))
register_cli_argument('network vnet subnet', 'address_prefix', metavar='PREFIX', help='the address prefix in CIDR format.')
register_cli_argument('network vnet subnet', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network vnet subnet', 'network_security_group', validator=validate_nsg_name_or_id)

register_cli_argument('network lb', 'item', help=argparse.SUPPRESS, default=None)
register_cli_argument('network lb', 'lb', help=argparse.SUPPRESS, default=None)
register_cli_argument('network lb', 'load_balancer_name', load_balancer_name_type)
register_cli_argument('network lb', 'frontend_port', help='Port number')
register_cli_argument('network lb', 'frontend_port_range_start', help='Port number')
register_cli_argument('network lb', 'frontend_port_range_end', help='Port number')
register_cli_argument('network lb', 'backend_port', help='Port number')
register_cli_argument('network lb', 'backend_address_pool_name', help='The name of the backend address pool.')
register_cli_argument('network lb', 'frontend_ip_name', help='The name of the frontend IP configuration.')
register_cli_argument('network lb', 'floating_ip', help='Enable floating IP.', choices=['true', 'false'], type=str.lower)
register_cli_argument('network lb', 'idle_timeout', help='Idle timeout in minutes.')
register_cli_argument('network lb', 'protocol', help='', choices=['udp', 'tcp'], type=str.lower)

register_cli_argument('network lb create', 'load_balancer_name', load_balancer_name_type, options_list=('--name', '-n'))
register_cli_argument('network lb delete', 'load_balancer_name', load_balancer_name_type, options_list=('--name', '-n'))
register_cli_argument('network lb show', 'load_balancer_name', load_balancer_name_type, options_list=('--name', '-n'))

register_cli_argument('network lb create', 'public_ip_dns_name', validator=process_network_lb_create_namespace)
register_cli_argument('network lb create', 'dns_name_type', help=argparse.SUPPRESS)
register_cli_argument('network lb create', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network lb create', 'public_ip_address_allocation', choices=choices_ip_allocation_method, default='dynamic', type=str.lower)
register_folded_cli_argument('network lb create', 'public_ip_address', 'Microsoft.Network/publicIPAddresses', validator=validate_public_ip_type)
register_folded_cli_argument('network lb create', 'subnet', 'subnets', parent_name='virtual_network_name', parent_type='Microsoft.Network/virtualNetworks')

register_cli_argument('network lb inbound-nat-rule', 'item_name', options_list=('--name', '-n'), help='The name of the inbound NAT rule.')
register_cli_argument('network lb inbound-nat-pool', 'item_name', options_list=('--name', '-n'), help='The name of the inbound NAT pool.')
register_cli_argument('network lb probe', 'item_name', options_list=('--name', '-n'), help='The name of the health probe.')
register_cli_argument('network lb frontend-ip', 'item_name', options_list=('--name', '-n'), help='The name of the frontend IP configuration.')
register_cli_argument('network lb address-pool', 'item_name', options_list=('--name', '-n'), help='The name of the backend address pool.')
register_cli_argument('network lb rule', 'item_name', options_list=('--name', '-n'), help='The name of the load balancing rule.')

register_cli_argument('network lb frontend-ip', 'private_ip_address', help='Static private IP address to associate with the configuration.')
register_cli_argument('network lb frontend-ip', 'public_ip_address_name', help='Name of the existing public IP to associate with the configuration.')
register_cli_argument('network lb frontend-ip', 'virtual_network_name', arg_type=virtual_network_name_type, help='The VNET name associated with the subnet name.')

register_cli_argument('network lb probe', 'interval', help='Probing time interval in seconds.')
register_cli_argument('network lb probe', 'path', help='The endpoint to interrogate (http only).')
register_cli_argument('network lb probe', 'port', help='The port to interrogate.')
register_cli_argument('network lb probe', 'protocol', help='The protocol to probe.', choices=['http', 'tcp'], type=str.lower)
register_cli_argument('network lb probe', 'threshold', help='The number of consecutive probe failures before an instance is deemed unhealthy.')

register_cli_argument('network lb rule', 'probe_name', help='The name of the health probe associated with the rule.')
register_cli_argument('network lb rule', 'load_distribution', help='Affinity rule settings.', choices=['default', 'sourceip', 'sourceipprotocol'], type=str.lower)

register_cli_argument('network nsg create', 'name', name_arg_type)

register_cli_argument('network vpn-gateway', 'virtual_network_gateway_name', CliArgumentType(options_list=('--name', '-n'), completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways')))

register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--name', '-n'), metavar='NAME'))

register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', CliArgumentType(options_list=('--name', '-n')))
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', CliArgumentType(options_list=('--connection-name',), metavar='NAME'))
