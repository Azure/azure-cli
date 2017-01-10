# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from azure.mgmt.network.models import \
    (IPAllocationMethod, RouteNextHopType)
from azure.mgmt.network.models.network_management_client_enums import \
    (ApplicationGatewaySkuName, ApplicationGatewayCookieBasedAffinity,
     ApplicationGatewayFirewallMode, ApplicationGatewayProtocol,
     ApplicationGatewayRequestRoutingRuleType, ExpressRouteCircuitSkuFamily,
     ExpressRouteCircuitSkuTier, ExpressRouteCircuitPeeringType, IPVersion, LoadDistribution,
     ProbeProtocol, TransportProtocol)
from azure.mgmt.dns.models.dns_management_client_enums import RecordType

from azure.cli.core.commands import \
    (CliArgumentType, register_cli_argument, register_extra_cli_argument)
from azure.cli.core.commands.parameters import (location_type, get_resource_name_completion_list,
                                                enum_choice_list, tags_type, ignore_type,
                                                get_generic_completion_list)
from azure.cli.core.commands.validators import MarkSpecifiedAction
from azure.cli.core.commands.template_create import get_folded_parameter_help_string
from azure.cli.command_modules.network._client_factory import _network_client_factory
from azure.cli.command_modules.network._validators import \
    (dns_zone_name_type,
     process_ag_create_namespace, process_ag_listener_create_namespace,
     process_ag_http_settings_create_namespace, process_ag_url_path_map_create_namespace,
     process_nic_create_namespace, process_lb_create_namespace, process_ag_rule_create_namespace,
     process_ag_url_path_map_rule_create_namespace, process_auth_create_namespace,
     process_public_ip_create_namespace, validate_private_ip_address,
     process_lb_frontend_ip_namespace, process_local_gateway_create_namespace,
     process_tm_endpoint_create_namespace, process_vnet_create_namespace,
     process_vnet_gateway_create_namespace, process_vpn_connection_create_namespace,
     process_ag_ssl_policy_set_namespace, process_route_table_create_namespace,
     validate_auth_cert, validate_cert, validate_inbound_nat_rule_id_list,
     validate_address_pool_id_list, validate_inbound_nat_rule_name_or_id,
     validate_address_pool_name_or_id, validate_servers, load_cert_file, validate_metadata,
     validate_peering_type,
     get_public_ip_validator, get_nsg_validator, get_subnet_validator,
     get_virtual_network_validator)
from azure.mgmt.network.models import ApplicationGatewaySslProtocol
from azure.cli.command_modules.network.mgmt_nic.lib.models.nic_creation_client_enums import privateIpAddressVersion
from azure.cli.command_modules.network.mgmt_vnet_gateway.lib.models.vnet_gateway_creation_client_enums import \
    (gatewayType, sku, vpnType)
from azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib.models.traffic_manager_profile_creation_client_enums \
    import routingMethod, status
from azure.cli.command_modules.network.custom import list_traffic_manager_endpoints

# CHOICE LISTS

# taken from Xplat. No enums in SDK
routing_registry_values = ['ARIN', 'APNIC', 'AFRINIC', 'LACNIC', 'RIPENCC', 'RADB', 'ALTDB', 'LEVEL3']
device_path_values = ['primary', 'secondary']

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
nic_type = CliArgumentType(options_list=('--nic-name',), metavar='NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NAME', help='Name of the network security group.')
circuit_name_type = CliArgumentType(options_list=('--circuit-name',), metavar='NAME', help='ExpressRoute circuit name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='NAME', help='The virtual network (VNET) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='NAME', help='The subnet name.')
load_balancer_name_type = CliArgumentType(options_list=('--lb-name',), metavar='NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
private_ip_address_type = CliArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
cookie_based_affinity_type = CliArgumentType(**enum_choice_list(ApplicationGatewayCookieBasedAffinity))
http_protocol_type = CliArgumentType(**enum_choice_list(ApplicationGatewayProtocol))
modified_record_type = CliArgumentType(options_list=('--type', '-t'), help='The type of DNS records in the record set.', **enum_choice_list([x.value for x in RecordType if x.value != 'SOA']))

# ARGUMENT REGISTRATION

register_cli_argument('network', 'subnet_name', subnet_name_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type, id_part='name')
register_cli_argument('network', 'network_security_group_name', nsg_name_type, id_part='name')
register_cli_argument('network', 'private_ip_address', private_ip_address_type)
register_cli_argument('network', 'private_ip_address_version', **enum_choice_list(privateIpAddressVersion))
register_cli_argument('network', 'tags', tags_type)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')
register_cli_argument('network application-gateway', 'sku_name', options_list=('--sku',), **enum_choice_list(ApplicationGatewaySkuName))
register_cli_argument('network application-gateway', 'sku_tier', ignore_type)
register_cli_argument('network application-gateway', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network application-gateway', 'servers', nargs='+', help='Space separated list of IP addresses or DNS names corresponding to backend servers.', validator=validate_servers)
register_cli_argument('network application-gateway', 'http_settings_cookie_based_affinity', cookie_based_affinity_type)
register_cli_argument('network application-gateway', 'http_settings_protocol', http_protocol_type)
register_cli_argument('network application-gateway', 'subnet_address_prefix', action=MarkSpecifiedAction)
register_cli_argument('network application-gateway', 'vnet_address_prefix', action=MarkSpecifiedAction)
register_cli_argument('network application-gateway', 'virtual_network_type', ignore_type)
register_cli_argument('network application-gateway', 'private_ip_address_allocation', ignore_type)

register_cli_argument('network application-gateway create', 'routing_rule_type', validator=process_ag_create_namespace, **enum_choice_list(ApplicationGatewayRequestRoutingRuleType))
register_cli_argument('network application-gateway create', 'cert_data', options_list=('--cert-file',), help='The path to the PFX certificate file.')
register_cli_argument('network application-gateway create', 'frontend_type', ignore_type)
register_cli_argument('network application-gateway create', 'http_listener_protocol', ignore_type)

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True, default_none=True)
register_cli_argument('network application-gateway create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network application-gateway create', 'public_ip_address_type', ignore_type)

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True)
register_cli_argument('network application-gateway create', 'subnet', help=subnet_help, completer=get_subnet_completion_list())
register_cli_argument('network application-gateway create', 'subnet_type', ignore_type)

ag_subresources = [
    {'name': 'auth-cert', 'display': 'authentication certificate', 'ref': 'authentication_certificates'},
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
    register_cli_argument('network application-gateway {}'.format(item['name']), 'item_name', options_list=('--name', '-n'), help='The name of the {}.'.format(item['display']), completer=get_ag_subresource_completion_list(item['ref']), id_part='child_name')
    register_cli_argument('network application-gateway {} create'.format(item['name']), 'item_name', options_list=('--name', '-n'), help='The name of the {}.'.format(item['display']), completer=None)
    register_cli_argument('network application-gateway {}'.format(item['name']), 'resource_name', options_list=('--gateway-name',), help='The name of the application gateway.')
    register_cli_argument('network application-gateway {}'.format(item['name']), 'application_gateway_name', options_list=('--gateway-name',), help='The name of the application gateway.')
    register_cli_argument('network application-gateway {} list'.format(item['name']), 'resource_name', options_list=('--gateway-name',))

register_cli_argument('network application-gateway auth-cert', 'cert_data', options_list=('--cert-file',), validator=validate_auth_cert)

register_cli_argument('network application-gateway frontend-ip', 'subnet', validator=get_subnet_validator())
register_cli_argument('network application-gateway frontend-ip', 'public_ip_address', validator=get_public_ip_validator(), help='The name or ID of the public IP address.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network application-gateway frontend-ip', 'virtual_network_name', help='The name of the virtual network corresponding to the subnet.', id_part=None)

for item in ['frontend-port', 'http-settings']:
    register_cli_argument('network application-gateway {}'.format(item), 'port', help='The port number.', type=int)

for item in ['http-settings', 'probe']:
    register_cli_argument('network application-gateway {}'.format(item), 'protocol', http_protocol_type, help='The HTTP settings protocol.')

register_cli_argument('network application-gateway http-listener', 'frontend_ip', help='The name or ID of the frontend IP configuration.', validator=process_ag_listener_create_namespace, completer=get_ag_subresource_completion_list('frontend_ip_configurations'))
register_cli_argument('network application-gateway http-listener', 'frontend_port', help='The name or ID of the frontend port.', completer=get_ag_subresource_completion_list('frontend_ports'))
register_cli_argument('network application-gateway http-listener', 'ssl_cert', help='The name or ID of the SSL certificate to use.', completer=get_ag_subresource_completion_list('ssl_certificates'))
register_cli_argument('network application-gateway http-listener', 'protocol', ignore_type)

register_cli_argument('network application-gateway http-settings', 'cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable cookie based affinity.')
register_cli_argument('network application-gateway http-settings', 'timeout', help='Request timeout in seconds.')
register_cli_argument('network application-gateway http-settings', 'probe', help='Name or ID of the probe to associate with the HTTP settings.', validator=process_ag_http_settings_create_namespace, completer=get_ag_subresource_completion_list('probes'))

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

register_cli_argument('network application-gateway ssl-cert', 'cert_data', options_list=('--cert-file',), help='The path to the PFX certificate file.', validator=validate_cert)

register_cli_argument('network application-gateway ssl-policy', 'clear', action='store_true', help='Clear SSL policy.', validator=process_ag_ssl_policy_set_namespace)
register_cli_argument('network application-gateway ssl-policy', 'disabled_ssl_protocols', nargs='+', help='Space separated list of protocols to disable.', **enum_choice_list(ApplicationGatewaySslProtocol))

register_cli_argument('network application-gateway url-path-map create', 'default_address_pool', help='The name or ID of the default backend address pool, if different from --address-pool.', validator=process_ag_url_path_map_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map create', 'default_http_settings', help='The name or ID of the default HTTP settings, if different from --http-settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway url-path-map update', 'default_address_pool', help='The name or ID of the default backend address pool.', validator=process_ag_url_path_map_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map update', 'default_http_settings', help='The name or ID of the default HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway url-path-map', 'rule_name', help='The name of the url-path-map rule.')
register_cli_argument('network application-gateway url-path-map', 'paths', nargs='+', help='Space separated list of paths to associate with the rule. Valid paths start and end with "/" (ex: "/bar/")')
register_cli_argument('network application-gateway url-path-map', 'address_pool', help='The name or ID of the backend address pool to use with the created rule.', completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map', 'http_settings', help='The name or ID of the HTTP settings to use with the created rule.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway url-path-map rule', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=get_ag_url_map_rule_completion_list(), id_part='grandchild_name')
register_cli_argument('network application-gateway url-path-map rule create', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=None)
register_cli_argument('network application-gateway url-path-map rule', 'url_path_map_name', options_list=('--path-map-name',), help='The name of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'), id_part='child_name')
register_cli_argument('network application-gateway url-path-map rule', 'address_pool', help='The name or ID of the backend address pool. If not specified, the default for the map will be used.', validator=process_ag_url_path_map_rule_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map rule', 'http_settings', help='The name or ID of the HTTP settings. If not specified, the default for the map will be used.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway waf-config', 'enabled', help='Specify whether the application firewall is enabled.', **enum_choice_list(['true', 'false']))
register_cli_argument('network application-gateway waf-config', 'firewall_mode', help='Web application firewall mode.', **enum_choice_list(ApplicationGatewayFirewallMode))

for item in ['ssl-policy', 'waf-config']:
    register_cli_argument('network application-gateway {}'.format(item), 'application_gateway_name', options_list=('--gateway-name',), help='The name of the application gateway.')

# ExpressRoutes
register_cli_argument('network express-route', 'circuit_name', circuit_name_type, options_list=('--name', '-n'))
register_cli_argument('network express-route', 'sku_family', help='Chosen SKU family of ExpressRoute circuit.', **enum_choice_list(ExpressRouteCircuitSkuFamily))
register_cli_argument('network express-route', 'sku_tier', help='SKU Tier of ExpressRoute circuit.', **enum_choice_list(ExpressRouteCircuitSkuTier))
register_cli_argument('network express-route', 'bandwidth_in_mbps', options_list=('--bandwidth',), help="Bandwidth in Mbps of the circuit. It must exactly match one of the available bandwidth offers from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'service_provider_name', options_list=('--provider',), help="Name of the ExpressRoute Service Provider. It must exactly match one of the Service Providers from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'peering_location', help="Name of the peering location. It must exactly match one of the available peering locations from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'device_path', options_list=('--path',), **enum_choice_list(device_path_values))
register_cli_argument('network express-route', 'vlan_id', type=int)

register_cli_argument('network express-route auth', 'circuit_name', circuit_name_type)
register_cli_argument('network express-route auth', 'authorization_name', name_arg_type, id_part='child_name', help='Authorization name')

register_cli_argument('network express-route auth create', 'authorization_parameters', ignore_type, validator=process_auth_create_namespace)

register_cli_argument('network express-route peering', 'circuit_name', circuit_name_type)
register_cli_argument('network express-route peering', 'peering_name', name_arg_type, id_part='child_name')
register_cli_argument('network express-route peering', 'peering_type', validator=validate_peering_type, **enum_choice_list(ExpressRouteCircuitPeeringType))
register_cli_argument('network express-route peering', 'sku_family', **enum_choice_list(ExpressRouteCircuitSkuFamily))
register_cli_argument('network express-route peering', 'sku_tier', **enum_choice_list(ExpressRouteCircuitSkuTier))
register_cli_argument('network express-route peering', 'advertised_public_prefixes', arg_group='Microsoft Peering', nargs='+')
register_cli_argument('network express-route peering', 'primary_peer_address_prefix', options_list=('--primary-peer-subnet',))
register_cli_argument('network express-route peering', 'secondary_peer_address_prefix', options_list=('--secondary-peer-subnet',))
register_cli_argument('network express-route peering', 'customer_asn', arg_group='Microsoft Peering')
register_cli_argument('network express-route peering', 'routing_registry_name', arg_group='Microsoft Peering', **enum_choice_list(routing_registry_values))

# Local Gateway
register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'), id_part='name')
register_cli_argument('network local-gateway', 'local_address_prefix', nargs='+', options_list=('--local-address-prefixes',), help='List of CIDR block prefixes representing the address space of the OnPremise VPN\'s subnet.')
register_cli_argument('network local-gateway', 'gateway_ip_address', help='Gateway\'s public IP address. (e.g. 10.1.1.1).')
register_cli_argument('network local-gateway', 'bgp_peering_address', arg_group='BGP Peering', help='IP address from the OnPremise VPN\'s subnet to use for BGP peering.')

register_cli_argument('network local-gateway create', 'use_bgp_settings', ignore_type)
register_cli_argument('network local-gateway create', 'asn', validator=process_local_gateway_create_namespace)


for item in ['local-gateway', 'vnet-gateway']:
    register_cli_argument('network {}'.format(item), 'asn', arg_group='BGP Peering', help='Autonomous System Number to use for the BGP settings.')
    register_cli_argument('network {}'.format(item), 'peer_weight', arg_group='BGP Peering', help='Weight (0-100) added to routes learned through BGP peering.')

# NIC

register_cli_argument('network nic', 'network_interface_name', nic_type, options_list=('--name', '-n'))
register_cli_argument('network nic', 'internal_dns_name_label', options_list=('--internal-dns-name',))

register_cli_argument('network nic create', 'enable_ip_forwarding', options_list=('--ip-forwarding',), action='store_true')
register_cli_argument('network nic create', 'network_interface_name', nic_type, options_list=('--name', '-n'), id_part=None, validator=process_nic_create_namespace)
register_cli_argument('network nic create', 'private_ip_address_allocation', ignore_type)
register_cli_argument('network nic create', 'use_dns_settings', ignore_type)

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, default_none=True)
register_cli_argument('network nic create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network nic create', 'public_ip_address_type', ignore_type)

nsg_help = get_folded_parameter_help_string('network security group', allow_none=True, default_none=True)
register_cli_argument('network nic create', 'network_security_group', help=nsg_help, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))
register_cli_argument('network nic create', 'network_security_group_type', ignore_type)

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name')
register_cli_argument('network nic create', 'subnet', help=subnet_help, completer=get_subnet_completion_list())
register_cli_argument('network nic create', 'subnet_type', ignore_type)

register_cli_argument('network nic update', 'enable_ip_forwarding', options_list=('--ip-forwarding',), **enum_choice_list(['true', 'false']))
register_cli_argument('network nic update', 'network_security_group', validator=get_nsg_validator(), completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

for item in ['create', 'ip-config update', 'ip-config create']:
    register_extra_cli_argument('network nic {}'.format(item), 'load_balancer_name', options_list=('--lb-name',), completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), help='The name of the load balancer to use when adding NAT rules or address pools by name (ignored when IDs are specified).')
    register_cli_argument('network nic {}'.format(item), 'load_balancer_backend_address_pool_ids', options_list=('--lb-address-pools',), nargs='+', validator=validate_address_pool_id_list, help='Space separated list of names or IDs of load balancer address pools to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('backendAddresPools'))
    register_cli_argument('network nic {}'.format(item), 'load_balancer_inbound_nat_rule_ids', options_list=('--lb-inbound-nat-rules',), nargs='+', validator=validate_inbound_nat_rule_id_list, help='Space separated list of names or IDs of load balancer inbound NAT rules to associate with the NIC. If names are used, --lb-name must be specified.', completer=get_lb_subresource_completion_list('inboundNatRules'))

register_cli_argument('network nic ip-config', 'network_interface_name', options_list=('--nic-name',), metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
register_cli_argument('network nic ip-config', 'ip_config_name', options_list=('--name', '-n'), metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name')
register_cli_argument('network nic ip-config', 'resource_name', options_list=('--nic-name',), metavar='NIC_NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
register_cli_argument('network nic ip-config', 'item_name', options_list=('--name', '-n'), metavar='IP_CONFIG_NAME', help='The name of the IP configuration.', id_part='child_name')
register_cli_argument('network nic ip-config', 'subnet', validator=get_subnet_validator(), help='Name or ID of an existing subnet. If name is specified, also specify --vnet-name.')
register_cli_argument('network nic ip-config', 'virtual_network_name', help='The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).', id_part=None, metavar='')
register_cli_argument('network nic ip-config', 'public_ip_address', validator=get_public_ip_validator())
register_cli_argument('network nic ip-config', 'make_primary', action='store_true', help='Set to make this configuration the primary one for the NIC.')

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
register_cli_argument('network nsg rule create', 'priority', default=1000, type=int)

# Public IP
register_cli_argument('network public-ip', 'public_ip_address_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), id_part='name', help='The name of the public IP address.')
register_cli_argument('network public-ip', 'name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), help='The name of the public IP address.')
register_cli_argument('network public-ip', 'reverse_fqdn', help='Reverse FQDN (fully qualified domain name).')
register_cli_argument('network public-ip', 'dns_name', help='Globally unique DNS entry.')
register_cli_argument('network public-ip', 'idle_timeout', help='Idle timeout in minutes.')

register_cli_argument('network public-ip create', 'name', completer=None)
register_cli_argument('network public-ip create', 'dns_name', validator=process_public_ip_create_namespace)
register_cli_argument('network public-ip create', 'dns_name_type', ignore_type)

for item in ['create', 'update']:
    register_cli_argument('network public-ip {}'.format(item), 'allocation_method', help='IP address allocation method', **enum_choice_list(IPAllocationMethod))
    register_cli_argument('network public-ip {}'.format(item), 'version', help='IP address type.', **enum_choice_list(IPVersion))

# Route table
register_cli_argument('network route-table', 'route_table_name', name_arg_type, completer=get_resource_name_completion_list('Microsoft.Network/routeTables'), id_part='name')
register_extra_cli_argument('network route-table create', 'tags')
register_extra_cli_argument('network route-table create', 'location')

register_cli_argument('network route-table create', 'location', location_type, validator=process_route_table_create_namespace)
register_cli_argument('network route-table create', 'parameters', ignore_type)

# Route Operation
register_cli_argument('network route-table route', 'route_name', name_arg_type, id_part='child_name', help='Route name')
register_cli_argument('network route-table route', 'route_table_name', options_list=('--route-table-name',), help='Route table name')
register_cli_argument('network route-table route', 'next_hop_type', help='The type of Azure hop the packet should be sent to.', **enum_choice_list(RouteNextHopType))
register_cli_argument('network route-table route', 'next_hop_ip_address', help='The IP address packets should be forwarded to when using the VirtualAppliance hop type.')
register_cli_argument('network route-table route', 'address_prefix', help='The destination CIDR to which the route applies.')

# VNET
register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), id_part='name')

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_prefix', help='IP address prefix for the new subnet. If omitted, automatically reserves a portion of the VNet address space.')
register_cli_argument('network vnet create', 'subnet_name', help='Name of a new subnet to create within the VNet.')
register_cli_argument('network vnet create', 'virtual_network_prefix', options_list=('--address-prefix',), metavar='PREFIX')
register_cli_argument('network vnet create', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), required=True, completer=None)
register_cli_argument('network vnet create', 'dns_servers', nargs='+', help='Space separated list of DNS server IP addresses.', validator=process_vnet_create_namespace)
register_cli_argument('network vnet create', 'create_subnet', ignore_type)

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
register_cli_argument('network vnet subnet', 'network_security_group', validator=get_nsg_validator())
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
register_cli_argument('network lb create', 'public_ip_address_allocation', default='dynamic', **enum_choice_list(IPAllocationMethod))
register_cli_argument('network lb create', 'private_ip_address_allocation', ignore_type)
register_cli_argument('network lb create', 'dns_name_type', ignore_type)

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
register_cli_argument('network lb create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network lb create', 'public_ip_address_type', ignore_type)

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True, allow_none=True, default_none=True)
register_cli_argument('network lb create', 'subnet', help=subnet_help, completer=get_subnet_completion_list())
register_cli_argument('network lb create', 'subnet_type', ignore_type)

for item in ['create', 'update']:
    register_cli_argument('network lb frontend-ip {}'.format(item), 'public_ip_address', help='Name or ID of the existing public IP to associate with the configuration.', validator=process_lb_frontend_ip_namespace)
    register_cli_argument('network lb frontend-ip {}'.format(item), 'subnet', help='Name or ID of an existing subnet. If name is specified, also specify --vnet-name.')
    register_cli_argument('network lb frontend-ip {}'.format(item), 'virtual_network_name', virtual_network_name_type, help='The virtual network (VNet) associated with the subnet (Omit if supplying a subnet id).', id_part=None, metavar='')
    register_cli_argument('network lb frontend-ip {}'.format(item), 'private_ip_address', help='Static private IP address to associate with the configuration.')
    register_cli_argument('network lb frontend-ip {}'.format(item), 'private_ip_address_allocation', ignore_type)

register_cli_argument('network lb probe', 'interval', help='Probing time interval in seconds.')
register_cli_argument('network lb probe', 'path', help='The endpoint to interrogate (http only).')
register_cli_argument('network lb probe', 'port', help='The port to interrogate.')
register_cli_argument('network lb probe', 'protocol', help='The protocol to probe.', **enum_choice_list(ProbeProtocol))
register_cli_argument('network lb probe', 'threshold', help='The number of consecutive probe failures before an instance is deemed unhealthy.')

register_cli_argument('network lb rule', 'load_distribution', help='Affinity rule settings.', **enum_choice_list(LoadDistribution))

register_cli_argument('network nsg create', 'name', name_arg_type)

# VNET gateway

register_cli_argument('network vnet-gateway', 'virtual_network_gateway_name', options_list=('--name', '-n'), completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
register_cli_argument('network vnet-gateway', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vnet-gateway', 'gateway_name', help='Virtual network gateway name')
register_cli_argument('network vnet-gateway', 'gateway_type', help='The gateway type.', **enum_choice_list(gatewayType))
register_cli_argument('network vnet-gateway', 'sku', help='VNet gateway SKU.', **enum_choice_list(sku))
register_cli_argument('network vnet-gateway', 'vpn_type', help='VPN routing type.', **enum_choice_list(vpnType))
register_cli_argument('network vnet-gateway', 'bgp_peering_address', arg_group='BGP Peering', help='IP address to use for BGP peering.')
register_cli_argument('network vnet-gateway', 'address_prefixes', nargs='+')

register_cli_argument('network vnet-gateway create', 'create_client_configuration', ignore_type)
register_cli_argument('network vnet-gateway create', 'enable_bgp', ignore_type)
register_cli_argument('network vnet-gateway create', 'asn', validator=process_vnet_gateway_create_namespace)

register_cli_argument('network vnet-gateway update', 'enable_bgp', help='Enable BGP (Border Gateway Protocol)', arg_group='BGP Peering', **enum_choice_list(['true', 'false']))
register_cli_argument('network vnet-gateway update', 'public_ip_address', help='Name or ID of a public IP address.', validator=get_public_ip_validator())
register_cli_argument('network vnet-gateway update', 'virtual_network', virtual_network_name_type, options_list=('--vnet',), help="Name or ID of a virtual network that contains a subnet named 'GatewaySubnet'.", validator=get_virtual_network_validator())

public_ip_help = get_folded_parameter_help_string('public IP address')
register_cli_argument('network vnet-gateway create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), validator=get_public_ip_validator(has_type_field=True))
register_cli_argument('network vnet-gateway create', 'public_ip_address_type', ignore_type)

vnet_help = "Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'."
register_cli_argument('network vnet-gateway create', 'virtual_network', options_list=('--vnet',), help=vnet_help, validator=get_virtual_network_validator(has_type_field=True))
register_cli_argument('network vnet-gateway create', 'virtual_network_type', ignore_type)

register_cli_argument('network vnet-gateway root-cert create', 'public_cert_data', help='Base64 contents of the root certificate file or file path.', validator=load_cert_file('public_cert_data'))
register_cli_argument('network vnet-gateway root-cert create', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vnet-gateway root-cert create', 'gateway_name', help='Virtual network gateway name')

register_cli_argument('network vnet-gateway revoked-cert create', 'thumbprint', help='Certificate thumbprint.')

register_extra_cli_argument('network vnet-gateway update', 'address_prefixes', options_list=('--address-prefixes',), help='List of address prefixes for the VPN gateway.  Prerequisite for uploading certificates.', nargs='+')


# VPN connection
register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', options_list=('--name', '-n'), metavar='NAME', id_part='name')
register_cli_argument('network vpn-connection', 'shared_key', validator=load_cert_file('shared_key'), help='Shared IPSec key, base64 contents of the certificate file or file path.')

register_cli_argument('network vpn-connection create', 'vnet_gateway1_id', options_list=('--vnet-gateway1',), validator=process_vpn_connection_create_namespace)
register_cli_argument('network vpn-connection create', 'vnet_gateway2_id', options_list=('--vnet-gateway2',))
register_cli_argument('network vpn-connection create', 'express_route_circuit2_id', options_list=('--express-route-circuit2',))
register_cli_argument('network vpn-connection create', 'local_gateway2_id', options_list=('--local-gateway2',))
register_cli_argument('network vpn-connection create', 'connection_type', ignore_type)

register_cli_argument('network vpn-connection update', 'routing_weight', type=int, help='Connection routing weight')
register_cli_argument('network vpn-connection update', 'enable_bgp', help='Enable BGP (Border Gateway Protocol)', **enum_choice_list(['true', 'false']))

# VPN connection shared key
register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', options_list=('--name', '-n'), id_part='name')
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', options_list=('--connection-name',), metavar='NAME', id_part='name')

# Traffic manager profiles
register_cli_argument('network traffic-manager profile', 'traffic_manager_profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile', 'profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile', 'monitor_path', help='Path to monitor.')
register_cli_argument('network traffic-manager profile', 'monitor_port', help='Port to monitor.', type=int)
register_cli_argument('network traffic-manager profile', 'monitor_protocol', help='Monitor protocol.')
register_cli_argument('network traffic-manager profile', 'profile_status', options_list=('--status',), help='Status of the Traffic Manager profile.', **enum_choice_list(['Enabled', 'Disabled']))
register_cli_argument('network traffic-manager profile', 'routing_method', help='Routing method.', **enum_choice_list(routingMethod))
register_cli_argument('network traffic-manager profile', 'ttl', help='DNS config time-to-live in seconds.', type=int)

register_cli_argument('network traffic-manager profile create', 'status', **enum_choice_list(status))

register_cli_argument('network traffic-manager profile check-dns', 'name', name_arg_type, help='DNS prefix to verify availability for.', required=True)
register_cli_argument('network traffic-manager profile check-dns', 'type', help=argparse.SUPPRESS, default='Microsoft.Network/trafficManagerProfiles')

# Traffic manager endpoints
endpoint_types = ['azureEndpoints', 'externalEndpoints', 'nestedEndpoints']
register_cli_argument('network traffic-manager endpoint', 'endpoint_name', name_arg_type, id_part='child_name', help='Endpoint name.', completer=get_tm_endpoint_completion_list())
register_cli_argument('network traffic-manager endpoint', 'endpoint_type', options_list=('--type',), help='Endpoint type.  Values include: {}.'.format(', '.join(endpoint_types)), completer=get_generic_completion_list(endpoint_types))
register_cli_argument('network traffic-manager endpoint', 'profile_name', help='Name of parent profile.', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'), id_part='name')
register_cli_argument('network traffic-manager endpoint', 'endpoint_location', help="Location of the external or nested endpoints when using the 'Performance' routing method.")
register_cli_argument('network traffic-manager endpoint', 'endpoint_monitor_status', help='The monitoring status of the endpoint.')
register_cli_argument('network traffic-manager endpoint', 'endpoint_status', help="The status of the endpoint. If enabled the endpoint is probed for endpoint health and included in the traffic routing method.")
register_cli_argument('network traffic-manager endpoint', 'min_child_endpoints', help="The minimum number of endpoints that must be available in the child profile for the parent profile to be considered available. Only applicable to an endpoint of type 'NestedEndpoints'.")
register_cli_argument('network traffic-manager endpoint', 'priority', help="Priority of the endpoint when using the 'Priority' traffic routing method. Values range from 1 to 1000, with lower values representing higher priority.", type=int)
register_cli_argument('network traffic-manager endpoint', 'target', help='Fully-qualified DNS name of the endpoint.')
register_cli_argument('network traffic-manager endpoint', 'target_resource_id', help="The Azure Resource URI of the endpoint. Not applicable for endpoints of type 'ExternalEndpoints'.")
register_cli_argument('network traffic-manager endpoint', 'weight', help="Weight of the endpoint when using the 'Weighted' traffic routing method. Values range from 1 to 1000.", type=int)

register_cli_argument('network traffic-manager endpoint create', 'target', help='Fully-qualified DNS name of the endpoint.', validator=process_tm_endpoint_create_namespace)

# DNS
register_cli_argument('network dns', 'location', help=argparse.SUPPRESS, default='global')
register_cli_argument('network dns', 'record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
register_cli_argument('network dns', 'relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
register_cli_argument('network dns', 'zone_name', options_list=('--zone-name', '-z'), help='The name of the zone.', type=dns_zone_name_type)
register_cli_argument('network dns', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)

register_cli_argument('network dns', 'record_type', modified_record_type)
register_cli_argument('network dns', 'location', help=argparse.SUPPRESS, default='global')

register_cli_argument('network dns zone', 'zone_name', name_arg_type)

register_cli_argument('network dns zone import', 'file_name', help='Path to the DNS zone file to import')
register_cli_argument('network dns zone export', 'file_name', help='Path to the DNS zone file to save')
register_cli_argument('network dns zone update', 'if_none_match', ignore_type)

register_cli_argument('network dns record', 'record_set_name', options_list=('--record-set-name',))

register_cli_argument('network dns record txt add', 'value', nargs='+')
register_cli_argument('network dns record txt remove', 'value', nargs='+')

register_cli_argument('network dns record-set create', 'record_set_type', modified_record_type)
register_cli_argument('network dns record-set create', 'ttl', help='Record set TTL (time-to-live)')
register_cli_argument('network dns record-set create', 'if_none_match', help='Create the record set only if it does not already exist.', action='store_true')

for item in ['list', 'show']:
    register_cli_argument('network dns record-set {}'.format(item), 'record_type', options_list=('--type', '-t'), **enum_choice_list(RecordType))
