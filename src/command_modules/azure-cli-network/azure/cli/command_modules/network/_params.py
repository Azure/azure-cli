#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from azure.mgmt.network.models import IPAllocationMethod, RouteNextHopType
from azure.mgmt.network.models.network_management_client_enums import \
    (ApplicationGatewaySkuName, ApplicationGatewayCookieBasedAffinity,
     ApplicationGatewayTier, ApplicationGatewayProtocol,
     ApplicationGatewayRequestRoutingRuleType, ExpressRouteCircuitSkuFamily,
     ExpressRouteCircuitSkuTier, ExpressRouteCircuitPeeringType, IPVersion, LoadDistribution,
     ProbeProtocol, TransportProtocol)
from azure.mgmt.dns.models.dns_management_client_enums import RecordType

from azure.cli.core.commands import CliArgumentType, register_cli_argument, register_extra_cli_argument
from azure.cli.core.commands.parameters import (location_type, get_resource_name_completion_list,
                                                enum_choice_list, tags_type,
                                                get_generic_completion_list)
from azure.cli.core.commands.validators import MarkSpecifiedAction
from azure.cli.core.commands.template_create import register_folded_cli_argument
from azure.cli.command_modules.network._factory import _network_client_factory
from azure.cli.command_modules.network._validators import \
    (process_ag_create_namespace, process_ag_listener_create_namespace,
     process_ag_http_settings_create_namespace, process_ag_url_path_map_create_namespace,
     process_nic_create_namespace, process_lb_create_namespace, process_ag_rule_create_namespace,
     process_ag_url_path_map_rule_create_namespace,
     process_public_ip_create_namespace, validate_public_ip_type, validate_private_ip_address,
     validate_subnet_name_or_id, validate_public_ip_name_or_id, validate_nsg_name_or_id,
     validate_inbound_nat_rule_id_list, validate_address_pool_id_list,
     validate_inbound_nat_rule_name_or_id, validate_address_pool_name_or_id,
     validate_servers, validate_cert, validate_address_prefixes, load_cert_file, vnet_gateway_validator)
from azure.cli.command_modules.network.mgmt_nic.lib.models.nic_creation_client_enums import privateIpAddressVersion
from azure.cli.command_modules.network.mgmt_vnet_gateway.lib.models.vnet_gateway_creation_client_enums import \
    (gatewayType, sku, vpnType)
from azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib.models.traffic_manager_profile_creation_client_enums \
    import routingMethod
from azure.cli.command_modules.network.custom import list_traffic_manager_endpoints

# COMPLETERS

def get_subnet_completion_list():
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _network_client_factory()
        if parsed_args.resource_group_name and parsed_args.virtual_network_name:
            rg = parsed_args.resource_group_name
            vnet = parsed_args.virtual_network_name
            return [r.name for r in client.subnets.list(resource_group_name=rg, virtual_network_name=vnet)]
    return completer

def get_lb_subresource_completion_list(prop):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _network_client_factory()
        try:
            lb_name = parsed_args.load_balancer_name
        except AttributeError:
            lb_name = parsed_args.resource_name
        if parsed_args.resource_group_name and lb_name:
            lb = client.load_balancers.get(parsed_args.resource_group_name, lb_name)
            return [r.name for r in getattr(lb, prop)]
    return completer


def get_ag_subresource_completion_list(prop):
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _network_client_factory()
        try:
            ag_name = parsed_args.application_gateway_name
        except AttributeError:
            ag_name = parsed_args.resource_name
        if parsed_args.resource_group_name and ag_name:
            ag = client.application_gateways.get(parsed_args.resource_group_name, ag_name)
            return [r.name for r in getattr(ag, prop)]
    return completer

def get_ag_url_map_rule_completion_list():
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        client = _network_client_factory()
        try:
            ag_name = parsed_args.application_gateway_name
        except AttributeError:
            ag_name = parsed_args.resource_name
        if parsed_args.resource_group_name and ag_name:
            ag = client.application_gateways.get(parsed_args.resource_group_name, ag_name)
            url_map = next((x for x in ag.url_path_maps if x.name == parsed_args.url_path_map_name), None) # pylint: disable=no-member
            return [r.name for r in url_map.path_rules]
    return completer

def get_tm_endpoint_completion_list():
    def completer(prefix, action, parsed_args, **kwargs): # pylint: disable=unused-argument
        return list_traffic_manager_endpoints(parsed_args.resource_group_name, parsed_args.profile_name) \
            if parsed_args.resource_group_name and parsed_args.profile_name \
            else []
    return completer

# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
nic_type = CliArgumentType(options_list=('--nic-name',), metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NSG', help='Name of the network security group.')
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='VNET_NAME', help='The virtual network (VNET) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='SUBNET_NAME', help='The subnet name.')
load_balancer_name_type = CliArgumentType(options_list=('--lb-name',), metavar='LB_NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
private_ip_address_type = CliArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
cookie_based_affinity_type = CliArgumentType(**enum_choice_list(ApplicationGatewayCookieBasedAffinity))
http_protocol_type = CliArgumentType(**enum_choice_list(ApplicationGatewayProtocol))

register_cli_argument('network', 'subnet_name', subnet_name_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type, id_part='name')
register_cli_argument('network', 'network_security_group_name', nsg_name_type, id_part='name')
register_cli_argument('network', 'private_ip_address', private_ip_address_type)
register_cli_argument('network', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network', 'private_ip_address_version', **enum_choice_list(privateIpAddressVersion))
register_cli_argument('network', 'tags', tags_type)

for item in ['lb', 'nic']:
    register_cli_argument('network {}'.format(item), 'subnet', validator=validate_subnet_name_or_id, help='Name or ID of an existing subnet.')
    register_cli_argument('network {}'.format(item), 'virtual_network_name', help='The virtual network (VNet) associated with the provided subnet name (Omit if supplying a subnet id).', id_part=None)
    register_cli_argument('network {}'.format(item), 'public_ip_address', validator=validate_public_ip_name_or_id)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')
register_cli_argument('network application-gateway', 'sku_name', **enum_choice_list(ApplicationGatewaySkuName))
register_cli_argument('network application-gateway', 'sku_tier', **enum_choice_list(ApplicationGatewayTier))
register_cli_argument('network application-gateway', 'routing_rule_type', **enum_choice_list(ApplicationGatewayRequestRoutingRuleType))
register_cli_argument('network application-gateway', 'virtual_network_name', virtual_network_name_type)
register_folded_cli_argument('network application-gateway', 'subnet', 'subnets', parent_name='virtual_network_name', parent_type='Microsoft.Network/virtualNetworks', none_flag_value=None, validator=validate_address_prefixes, completer=get_subnet_completion_list())
register_folded_cli_argument('network application-gateway', 'public_ip', 'Microsoft.Network/publicIPAddresses', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network application-gateway', 'virtual_network_type', help=argparse.SUPPRESS)
register_cli_argument('network application-gateway', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network application-gateway', 'frontend_type', help=argparse.SUPPRESS, validator=process_ag_create_namespace)
register_cli_argument('network application-gateway', 'servers', nargs='+', validator=validate_servers)
register_cli_argument('network application-gateway', 'cert_data', options_list=('--cert-file',), help='The path to the PFX certificate file.', validator=validate_cert)
register_cli_argument('network application-gateway', 'http_listener_protocol', default=None, help=argparse.SUPPRESS)
register_cli_argument('network application-gateway', 'http_settings_cookie_based_affinity', cookie_based_affinity_type)
register_cli_argument('network application-gateway', 'http_settings_protocol', http_protocol_type)

register_cli_argument('network application-gateway', 'subnet_address_prefix', action=MarkSpecifiedAction)
register_cli_argument('network application-gateway', 'vnet_address_prefix', action=MarkSpecifiedAction)

ag_subresources = [
    {'name': 'ssl-cert', 'display': 'SSL certificate', 'ref': 'ssl_certificates'},
    {'name': 'frontend-ip', 'display': 'frontend IP configuration', 'ref': 'frontend_ip_configurations'},
    {'name': 'frontend-port', 'display': 'frontend port', 'ref': 'frontend_ports'},
    {'name': 'address-pool', 'display': 'backend address pool', 'ref': 'backend_address_pools'},
    {'name': 'http-settings', 'display': 'backed HTTP settings', 'ref': 'backend_http_settings_collection'},
    {'name': 'http-listener', 'display': 'HTTP listener', 'ref': 'http_listeners'},
    {'name': 'rule', 'display': 'request routing rule', 'ref': 'request_routing_rules'},
    {'name': 'probe', 'display': 'probe', 'ref': 'probes'},
    {'name': 'url-path-map', 'display': 'URL path map', 'ref': 'url_path_maps'},
]
for item in ag_subresources:
    register_cli_argument('network application-gateway {}'.format(item['name']), 'item_name', options_list=('--name', '-n'), help='The name of the {}.'.format(item['display']), completer=get_ag_subresource_completion_list(item['ref']))
    register_cli_argument('network application-gateway {} create'.format(item['name']), 'item_name', options_list=('--name', '-n'), help='The name of the {}.'.format(item['display']), completer=None)
    register_cli_argument('network application-gateway {}'.format(item['name']), 'resource_name', options_list=('--gateway-name',), help='The name of the application gateway.')
    register_cli_argument('network application-gateway {}'.format(item['name']), 'application_gateway_name', options_list=('--gateway-name',), help='The name of the application gateway.')
    register_cli_argument('network application-gateway {} list'.format(item['name']), 'resource_name', options_list=('--name', '-n'))

register_cli_argument('network application-gateway frontend-ip', 'subnet', validator=validate_subnet_name_or_id)
register_cli_argument('network application-gateway frontend-ip', 'public_ip_address', validator=validate_public_ip_name_or_id, help='The name or ID of the public IP address.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

for item in ['frontend-port', 'http-settings']:
    register_cli_argument('network application-gateway {}'.format(item), 'port', help='The port number.', type=int)

for item in ['http-settings', 'probe']:
    register_cli_argument('network application-gateway {}'.format(item), 'protocol', http_protocol_type, help='The HTTP settings protocol. (http, https)')

register_cli_argument('network application-gateway http-listener', 'frontend_ip', help='The name or ID of the frontend IP configuration.', validator=process_ag_listener_create_namespace, completer=get_ag_subresource_completion_list('frontend_ip_configurations'))
register_cli_argument('network application-gateway http-listener', 'frontend_port', help='The name or ID of the frontend port.', completer=get_ag_subresource_completion_list('frontend_ports'))
register_cli_argument('network application-gateway http-listener', 'ssl_cert', help='The name or ID of the SSL certificate to use.', completer=get_ag_subresource_completion_list('ssl_certificates'))

register_cli_argument('network application-gateway http-settings', 'cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable cookie based affinity. (Enabled, Disabled)')
register_cli_argument('network application-gateway http-settings', 'timeout', help='Request timeout in seconds.')
register_cli_argument('network application-gateway http-settings', 'probe', help='Name or ID of the probe to associatie with the HTTP settings.', validator=process_ag_http_settings_create_namespace, completer=get_ag_subresource_completion_list('probes'))

register_cli_argument('network application-gateway probe', 'host', help='The name of the host to send the probe.')
register_cli_argument('network application-gateway probe', 'path', help='The relative path of the probe. Valid paths start from "/"')
register_cli_argument('network application-gateway probe', 'interval', help='The time interval in seconds between consecutive probes.')
register_cli_argument('network application-gateway probe', 'threshold', help='The number of failed probes after which the back end server is marked down.')
register_cli_argument('network application-gateway probe', 'timeout', help='The probe timeout in seconds.')

register_cli_argument('network application-gateway rule', 'address_pool', help='The name or ID of the backend address pool.', validator=process_ag_rule_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway rule', 'http_listener', help='The name or ID of the HTTP listener.', completer=get_ag_subresource_completion_list('http_listeners'))
register_cli_argument('network application-gateway rule', 'http_settings', help='The name or ID of the backend HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))
register_cli_argument('network application-gateway rule', 'rule_type', help='The rule type (Basic, PathBasedRouting).')
register_cli_argument('network application-gateway rule', 'url_path_map', help='The name or ID of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'))

register_cli_argument('network application-gateway url-path-map', 'default_address_pool', help='The name or ID of the default backend address pool, if different from --address-pool.', validator=process_ag_url_path_map_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map', 'default_http_settings', help='The name or ID of the default HTTP settings, if different from --http-settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))
register_cli_argument('network application-gateway url-path-map', 'rule_name', help='The name of the url-path-map rule.')
register_cli_argument('network application-gateway url-path-map', 'paths', nargs='+', help='Space separated list of paths to associate with the rule. Valid paths start and end with "/" (ex: "/bar/")')
register_cli_argument('network application-gateway url-path-map', 'address_pool', help='The name or ID of the backend address pool to use with the created rule.', completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map', 'http_settings', help='The name or ID of the HTTP settings to use with the created rule.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))


register_cli_argument('network application-gateway url-path-map rule', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=get_ag_url_map_rule_completion_list(), id_part='grandchild_name')
register_cli_argument('network application-gateway url-path-map rule create', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=None)
register_cli_argument('network application-gateway url-path-map rule', 'url_path_map_name', options_list=('--path-map-name',), help='The name of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'), id_part='child_name')
register_cli_argument('network application-gateway url-path-map rule', 'address_pool', help='The name or ID of the backend address pool. If not specified, the default for the map will be used.', validator=process_ag_url_path_map_rule_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map rule', 'http_settings', help='The name or ID of the HTTP settings. If not specified, the default for the map will be used.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

# Express Route Circuit Auth
register_cli_argument('network express-route circuit-auth', 'authorization_name', name_arg_type, id_part='child_name', help='Authorization name')
register_cli_argument('network express-route circuit-auth', 'circuit_name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'), id_part='name', help='Circuit name.')
register_cli_argument('network express-route circuit-auth', 'authorization_key', help='Authorization key.')

# Express Route Circuit Peering
register_cli_argument('network express-route circuit-peering', 'peering_name', name_arg_type, id_part='child_name')
register_cli_argument('network express-route circuit-peering', 'peering_type', **enum_choice_list(ExpressRouteCircuitPeeringType))
register_cli_argument('network express-route circuit-peering', 'sku_family', **enum_choice_list(ExpressRouteCircuitSkuFamily))
register_cli_argument('network express-route circuit-peering', 'sku_tier', **enum_choice_list(ExpressRouteCircuitSkuTier))

# Express Route Circuit
register_cli_argument('network express-route circuit', 'circuit_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'), id_part='name')
register_cli_argument('network express-route circuit', 'sku_family', **enum_choice_list(ExpressRouteCircuitSkuFamily))
register_cli_argument('network express-route circuit', 'sku_tier', **enum_choice_list(ExpressRouteCircuitSkuTier))

# Local Gateway
register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'), id_part='name')

# NIC
register_cli_argument('network nic', 'network_interface_name', nic_type, options_list=('--name', '-n'))
register_cli_argument('network nic', 'private_ip_address_allocation', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'network_security_group_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'public_ip_address_type', help=argparse.SUPPRESS)
register_cli_argument('network nic', 'internal_dns_name_label', options_list=('--internal-dns-name',))

register_cli_argument('network nic create', 'network_interface_name', nic_type, options_list=('--name', '-n'), validator=process_nic_create_namespace, id_part=None)
register_cli_argument('network nic create', 'enable_ip_forwarding', options_list=('--ip-forwarding',), action='store_true')
register_cli_argument('network nic create', 'use_dns_settings', help=argparse.SUPPRESS)
register_folded_cli_argument('network nic create', 'public_ip_address', 'Microsoft.Network/publicIPAddresses', new_flag_value=None, default_value_flag='none', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_folded_cli_argument('network nic create', 'subnet', 'subnets', none_flag_value=None, new_flag_value=None, default_value_flag='existingId', parent_name='virtual_network_name', parent_type='Microsoft.Network/virtualNetworks', completer=get_subnet_completion_list())
register_folded_cli_argument('network nic create', 'network_security_group', 'Microsoft.Network/networkSecurityGroups', new_flag_value=None, default_value_flag='none', completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

register_cli_argument('network nic update', 'enable_ip_forwarding', options_list=('--ip-forwarding',), **enum_choice_list(['true', 'false']))
register_cli_argument('network nic update', 'network_security_group', validator=validate_nsg_name_or_id, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

for item in ['create', 'ip-config update', 'ip-config create']:
    register_extra_cli_argument('network nic {}'.format(item), 'load_balancer_name', options_list=('--lb-name',), completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), help='The name of the load balancer to use when adding NAT rules or address pools by name (ignored when IDs are specified).')
    register_cli_argument('network nic {}'.format(item), 'load_balancer_backend_address_pool_ids', options_list=('--lb-address-pools',), nargs='+', validator=validate_address_pool_id_list, help='Space separated list of names or IDs of load balancer address pools to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('backendAddresPools'))
    register_cli_argument('network nic {}'.format(item), 'load_balancer_inbound_nat_rule_ids', options_list=('--lb-inbound-nat-rules',), nargs='+', validator=validate_inbound_nat_rule_id_list, help='Space separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('inboundNatRules'))

register_cli_argument('network nic ip-config', 'network_interface_name', options_list=('--nic-name',), metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
register_cli_argument('network nic ip-config', 'ip_config_name', options_list=('--name', '-n'), metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name')
register_cli_argument('network nic ip-config', 'resource_name', options_list=('--nic-name',), metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
register_cli_argument('network nic ip-config', 'item_name', options_list=('--name', '-n'), metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name')

for item in ['address-pool', 'inbound-nat-rule']:
    register_cli_argument('network nic ip-config {}'.format(item), 'ip_config_name', options_list=('--ip-config-name', '-n'), metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name')
    register_cli_argument('network nic ip-config {}'.format(item), 'network_interface_name', nic_type)

register_cli_argument('network nic ip-config address-pool remove', 'network_interface_name', nic_type, id_part=None)
register_cli_argument('network nic ip-config inbound-nat-rule remove', 'network_interface_name', nic_type, id_part=None)

register_cli_argument('network nic ip-config address-pool', 'load_balancer_name', options_list=('--lb-name',), help='The name of the load balancer associated with the address pool (Omit if suppying an address pool ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
register_cli_argument('network nic ip-config inbound-nat-rule', 'load_balancer_name', options_list=('--lb-name',), help='The name of the load balancer associated with the NAT rule (Omit if suppying a NAT rule ID).', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))

register_cli_argument('network nic ip-config address-pool', 'backend_address_pool', options_list=('--address-pool',), help='The name or ID of an existing backend address pool.', validator=validate_address_pool_name_or_id)
register_cli_argument('network nic ip-config inbound-nat-rule', 'inbound_nat_rule', options_list=('--inbound-nat-rule',), help='The name or ID of an existing inbound NAT rule.', validator=validate_inbound_nat_rule_name_or_id)

# NSG
register_cli_argument('network nsg', 'network_security_group_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'), id_part='name')
register_cli_argument('network nsg create', 'name', name_arg_type)

# NSG Rule
register_cli_argument('network nsg rule', 'security_rule_name', name_arg_type, id_part='child_name', help='Name of the network security group rule')
register_cli_argument('network nsg rule', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME', help='Name of the network security group', id_part='name')
register_cli_argument('network nsg rule create', 'priority', default=1000)

# Public IP
register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), id_part='name')
register_cli_argument('network public-ip', 'name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

register_cli_argument('network public-ip create', 'name', completer=None)
register_cli_argument('network public-ip create', 'dns_name', validator=process_public_ip_create_namespace)
register_cli_argument('network public-ip create', 'dns_name_type', help=argparse.SUPPRESS)
register_cli_argument('network public-ip create', 'allocation_method', **enum_choice_list(IPAllocationMethod))
register_cli_argument('network public-ip create', 'version', **enum_choice_list(IPVersion))

# Route Operation
register_cli_argument('network route-table route', 'route_name', name_arg_type, id_part='child_name', help='Route name')
register_cli_argument('network route-table route', 'route_table_name', options_list=('--route-table-name',), help='Route table name')
register_cli_argument('network route-table route', 'next_hop_type', **enum_choice_list(RouteNextHopType))

# Route table
register_cli_argument('network route-table', 'route_table_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/routeTables'), id_part='name')

# VNET
register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), id_part='name')

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_prefix', options_list=('--subnet-prefix',), metavar='SUBNET_PREFIX', default='10.0.0.0/24')
register_cli_argument('network vnet create', 'subnet_name', options_list=('--subnet-name',), metavar='SUBNET_NAME', default='Subnet1')
register_cli_argument('network vnet create', 'virtual_network_prefix', options_list=('--address-prefix',), metavar='PREFIX', default='10.0.0.0/16')
register_cli_argument('network vnet create', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), required=True, completer=None)
register_cli_argument('network vnet create', 'dns_servers', nargs='+')

register_cli_argument('network vnet subnet', 'subnet_name', arg_type=subnet_name_type, options_list=('--name', '-n'), id_part='child_name')
register_cli_argument('network vnet update', 'address_prefixes', nargs='+')

register_cli_argument('network vnet peering', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network vnet peering', 'virtual_network_peering_name', options_list=('--name', '-n'), help='The name of the VNET peering.', id_part='child_name')
register_cli_argument('network vnet peering', 'remote_virtual_network', options_list=('--remote-vnet-id',), help='ID of the remote VNET.')
register_cli_argument('network vnet peering create', 'allow_virtual_network_access', options_list=('--allow-vnet-access',), action='store_true', help='Allows VMs in the remote VNET to access all VMs in the local VNET.')
register_cli_argument('network vnet peering create', 'allow_gateway_transit', action='store_true', help='Allows gateway link to be used in the remote VNET.')
register_cli_argument('network vnet peering create', 'allow_forwarded_traffic', action='store_true', help='Allows forwarded traffic from the VMs in the remote VNET.')
register_cli_argument('network vnet peering create', 'use_remote_gateways', action='store_true', help='Allows VNET to use the remote VNET\'s gateway. Remote VNET gateway must have --allow-gateway-transit enabled for remote peering. Only 1 peering can have this flag enabled. Cannot be set if the VNET already has a gateway.')

register_cli_argument('network vnet subnet', 'address_prefix', metavar='PREFIX', help='the address prefix in CIDR format.')
register_cli_argument('network vnet subnet', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network vnet subnet', 'network_security_group', validator=validate_nsg_name_or_id)
register_cli_argument('network vnet subnet', 'route_table', help='Name or ID of a route table to associate with the subnet.')

lb_subresources = [
    {'name': 'address-pool', 'display': 'backend address pool', 'ref': 'backend_address_pools'},
    {'name': 'frontend-ip', 'display': 'frontend IP configuration', 'ref': 'frontend_ip_configurations'},
    {'name': 'inbound-nat-rule', 'display': 'inbound NAT rule', 'ref': 'inbound_nat_rules'},
    {'name': 'inbound-nat-pool', 'display': 'inbound NAT pool', 'ref': 'inbound_nat_pools'},
    {'name': 'rule', 'display': 'load balancing rule', 'ref': 'load_balancing_rules'},
    {'name': 'probe', 'display': 'probe', 'ref': 'probes'},
]
for item in lb_subresources:
    register_cli_argument('network lb {}'.format(item['name']), 'item_name', options_list=('--name', '-n'), help='The name of the {}'.format(item['display']), completer=get_lb_subresource_completion_list(item['ref']), id_part='child_name')
    register_cli_argument('network lb {}'.format(item['name']), 'resource_name', options_list=('--lb-name',), help='The name of the load balancer.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'))
    register_cli_argument('network lb {}'.format(item['name']), 'load_balancer_name', load_balancer_name_type)

register_cli_argument('network lb', 'load_balancer_name', load_balancer_name_type, options_list=('--name', '-n'))
register_cli_argument('network lb', 'frontend_port', help='Port number')
register_cli_argument('network lb', 'frontend_port_range_start', help='Port number')
register_cli_argument('network lb', 'frontend_port_range_end', help='Port number')
register_cli_argument('network lb', 'backend_port', help='Port number')
register_cli_argument('network lb', 'backend_address_pool_name', options_list=('--backend-pool-name',), help='The name of the backend address pool.', completer=get_lb_subresource_completion_list('backend_address_pools'))
register_cli_argument('network lb', 'frontend_ip_name', help='The name of the frontend IP configuration.', completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
register_cli_argument('network lb', 'floating_ip', help='Enable floating IP.', **enum_choice_list(['true', 'false']))
register_cli_argument('network lb', 'idle_timeout', help='Idle timeout in minutes.')
register_cli_argument('network lb', 'protocol', help='', **enum_choice_list(TransportProtocol))

register_cli_argument('network lb create', 'public_ip_dns_name', validator=process_lb_create_namespace)
register_cli_argument('network lb create', 'dns_name_type', help=argparse.SUPPRESS)
register_cli_argument('network lb create', 'public_ip_address_allocation', default='dynamic', **enum_choice_list(IPAllocationMethod))
register_folded_cli_argument('network lb create', 'public_ip_address', 'Microsoft.Network/publicIPAddresses', validator=validate_public_ip_type)
register_folded_cli_argument('network lb create', 'subnet', 'subnets', parent_name='virtual_network_name', parent_type='Microsoft.Network/virtualNetworks', default_value_flag='none')

register_cli_argument('network lb frontend-ip', 'public_ip_address', help='Name or ID of the existing public IP to associate with the configuration.', validator=validate_public_ip_name_or_id)
register_cli_argument('network lb frontend-ip', 'private_ip_address', help='Static private IP address to associate with the configuration.')
register_cli_argument('network lb frontend-ip', 'virtual_network_name', arg_type=virtual_network_name_type, help='The VNET name associated with the subnet name.')

register_cli_argument('network lb probe', 'interval', help='Probing time interval in seconds.')
register_cli_argument('network lb probe', 'path', help='The endpoint to interrogate (http only).')
register_cli_argument('network lb probe', 'port', help='The port to interrogate.')
register_cli_argument('network lb probe', 'protocol', help='The protocol to probe.', **enum_choice_list(ProbeProtocol))
register_cli_argument('network lb probe', 'threshold', help='The number of consecutive probe failures before an instance is deemed unhealthy.')

register_cli_argument('network lb rule', 'load_distribution', help='Affinity rule settings.', **enum_choice_list(LoadDistribution))

register_cli_argument('network nsg create', 'name', name_arg_type)

# VPN gateway
register_cli_argument('network vpn-gateway', 'virtual_network_gateway_name', options_list=('--name', '-n'), completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
register_cli_argument('network vpn-gateway create', 'gateway_type', **enum_choice_list(gatewayType))
register_cli_argument('network vpn-gateway create', 'sku', **enum_choice_list(sku))
register_cli_argument('network vpn-gateway create', 'vpn_type', **enum_choice_list(vpnType))
register_folded_cli_argument('network vpn-gateway create', 'public_ip_address', 'Microsoft.Network/publicIPAddresses', default_value_flag='existingId', none_flag_value=None, new_flag_value=None, required=True)
register_cli_argument('network vpn-gateway', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vpn-gateway', 'gateway_name', help='Virtual network gateway name')
register_cli_argument('network vpn-gateway root-cert create', 'public_cert_data', help='Base64 contents of the root certificate file or file path.', validator=load_cert_file('public_cert_data'))
register_cli_argument('network vpn-gateway revoked-cert create', 'thumbprint', help='Certificate thumbprint.')
register_extra_cli_argument('network vpn-gateway update', 'address_prefixes', options_list=('--address-prefixes',), help='List of address prefixes for the VPN gateway.  Prerequisite for uploading certificates.', nargs='+')
register_cli_argument('network vpn-gateway root-cert create', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vpn-gateway root-cert create', 'gateway_name', help='Virtual network gateway name')

# VPN connection
register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', options_list=('--name', '-n'), metavar='NAME', id_part='name')
register_cli_argument('network vpn-connection create', 'connection_type', help=argparse.SUPPRESS, validator=vnet_gateway_validator, required=False)
register_cli_argument('network vpn-connection create', 'shared_key', validator=load_cert_file('shared_key'), help='Shared IPSec key, base64 contents of the certificate file or file path.')

# VPN connection shared key
register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', options_list=('--name', '-n'), id_part='name')
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', options_list=('--connection-name',), metavar='NAME', id_part='name')

# Traffic manager profiles
register_cli_argument('network traffic-manager profile', 'traffic_manager_profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile', 'profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile create', 'routing_method', **enum_choice_list(routingMethod))
register_cli_argument('network traffic-manager profile check-dns', 'name', name_arg_type, help='DNS prefix to verify availability for.', required=True)
register_cli_argument('network traffic-manager profile check-dns', 'type', help=argparse.SUPPRESS, default='Microsoft.Network/trafficManagerProfiles')

# Traffic manager endpoints
endpoint_types = ['azureEndpoints', 'externalEndpoints', 'nestedEndpoints']
register_cli_argument('network traffic-manager endpoint', 'endpoint_name', name_arg_type, id_part='child_name', help='Endpoint name.', completer=get_tm_endpoint_completion_list())
register_cli_argument('network traffic-manager endpoint', 'endpoint_type', options_list=('--type',), help='Endpoint type.  Values include: {}.'.format(', '.join(endpoint_types)), completer=get_generic_completion_list(endpoint_types))
register_cli_argument('network traffic-manager endpoint', 'profile_name', help='Name of parent profile.', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'), id_part='name')

# DNS
register_cli_argument('network dns zone', 'zone_name', name_arg_type)
register_cli_argument('network dns', 'record_set_name', name_arg_type, help='The name of the RecordSet, relative to the name of the zone.')
register_cli_argument('network dns', 'relative_record_set_name', name_arg_type, help='The name of the RecordSet, relative to the name of the zone.')
register_cli_argument('network dns', 'zone_name', help='The name of the zone without a terminating dot.')
register_cli_argument('network dns record-set create', 'record_set_type', options_list=('--type',), **enum_choice_list(RecordType))
register_cli_argument('network dns record-set create', 'ttl', default=3600)
register_cli_argument('network dns', 'record_type', options_list=('--type',), **enum_choice_list(RecordType))
register_cli_argument('network dns record', 'record_set_name', options_list=('--record-set-name',))
register_cli_argument('network dns record txt add', 'value', nargs='+')
register_cli_argument('network dns record txt remove', 'value', nargs='+')
register_cli_argument('network dns zone import', 'file_name', help='Path to the DNS zone file to import')
register_cli_argument('network dns zone export', 'file_name', help='Path to the DNS zone file to save')
register_cli_argument('network dns', 'location', help=argparse.SUPPRESS, default='global')
