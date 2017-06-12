# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from argcomplete.completers import FilesCompleter

from azure.cli.core.commands import \
    (VersionConstraint, CliArgumentType, register_cli_argument, register_extra_cli_argument)
from azure.cli.core.commands.parameters import (location_type, get_resource_name_completion_list,
                                                enum_choice_list, tags_type, ignore_type,
                                                file_type, get_resource_group_completion_list,
                                                three_state_flag, model_choice_list)
from azure.cli.core.commands.validators import \
    (MarkSpecifiedAction, get_default_location_from_resource_group)
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
     process_vnet_gateway_create_namespace, process_vnet_gateway_update_namespace,
     process_vpn_connection_create_namespace,
     process_nw_troubleshooting_start_namespace, process_nw_troubleshooting_show_namespace,
     process_nw_flow_log_set_namespace, process_nw_flow_log_show_namespace,
     process_ag_ssl_policy_set_namespace, process_route_table_create_namespace,
     process_nw_topology_namespace, process_nw_packet_capture_create_namespace,
     process_nw_test_connectivity_namespace,
     validate_auth_cert, validate_cert, validate_inbound_nat_rule_id_list,
     validate_address_pool_id_list, validate_inbound_nat_rule_name_or_id,
     validate_address_pool_name_or_id, validate_servers, load_cert_file, validate_metadata,
     validate_peering_type, validate_dns_record_type, validate_route_filter,
     get_public_ip_validator, get_nsg_validator, get_subnet_validator,
     get_network_watcher_from_vm, get_network_watcher_from_location)
from azure.mgmt.network.models import ApplicationGatewaySslProtocol
from azure.cli.command_modules.network.custom import list_traffic_manager_endpoints
from azure.cli.core.profiles import ResourceType, get_sdk, supported_api_version
from azure.cli.core.util import get_json_object

(ApplicationGatewaySkuName, ApplicationGatewayCookieBasedAffinity, ApplicationGatewayFirewallMode,
 ApplicationGatewayProtocol, ApplicationGatewayRequestRoutingRuleType, ApplicationGatewaySslProtocol,
 ExpressRouteCircuitSkuFamily, ExpressRouteCircuitSkuTier, ExpressRouteCircuitPeeringType, IPVersion, LoadDistribution,
 ProbeProtocol, TransportProtocol, SecurityRuleAccess, SecurityRuleProtocol, SecurityRuleDirection,
 VirtualNetworkGatewayType, VirtualNetworkGatewaySkuName, VpnType, IPAllocationMethod, RouteNextHopType, Direction,
 Protocol, IPVersion) = get_sdk(ResourceType.MGMT_NETWORK,
                                'ApplicationGatewaySkuName',
                                'ApplicationGatewayCookieBasedAffinity',
                                'ApplicationGatewayFirewallMode',
                                'ApplicationGatewayProtocol',
                                'ApplicationGatewayRequestRoutingRuleType',
                                'ApplicationGatewaySslProtocol',
                                'ExpressRouteCircuitSkuFamily',
                                'ExpressRouteCircuitSkuTier',
                                'ExpressRouteCircuitPeeringType',
                                'IPVersion',
                                'LoadDistribution', 'ProbeProtocol',
                                'TransportProtocol',
                                'SecurityRuleAccess',
                                'SecurityRuleProtocol',
                                'SecurityRuleDirection',
                                'VirtualNetworkGatewayType',
                                'VirtualNetworkGatewaySkuName',
                                'VpnType', 'IPAllocationMethod',
                                'RouteNextHopType',
                                'Direction', 'Protocol', 'IPVersion',
                                mod='models')

# CHOICE LISTS

# taken from Xplat. No enums in SDK
routing_registry_values = ['ARIN', 'APNIC', 'AFRINIC', 'LACNIC', 'RIPENCC', 'RADB', 'ALTDB', 'LEVEL3']
device_path_values = ['primary', 'secondary']

# COMPLETERS


def get_subnet_completion_list():
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        client = _network_client_factory()
        if parsed_args.resource_group_name and parsed_args.virtual_network_name:
            rg = parsed_args.resource_group_name
            vnet = parsed_args.virtual_network_name
            return [r.name for r in client.subnets.list(resource_group_name=rg, virtual_network_name=vnet)]
    return completer


def get_lb_subresource_completion_list(prop):
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
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
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
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
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        client = _network_client_factory()
        try:
            ag_name = parsed_args.application_gateway_name
        except AttributeError:
            ag_name = parsed_args.resource_name
        if parsed_args.resource_group_name and ag_name:
            ag = client.application_gateways.get(parsed_args.resource_group_name, ag_name)
            url_map = next((x for x in ag.url_path_maps if x.name == parsed_args.url_path_map_name), None)  # pylint: disable=no-member
            return [r.name for r in url_map.path_rules]
    return completer


def get_tm_endpoint_completion_list():
    def completer(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
        return list_traffic_manager_endpoints(parsed_args.resource_group_name, parsed_args.profile_name) \
            if parsed_args.resource_group_name and parsed_args.profile_name \
            else []
    return completer


# BASIC PARAMETER CONFIGURATION

name_arg_type = CliArgumentType(options_list=('--name', '-n'), metavar='NAME')
nic_type = CliArgumentType(options_list=('--nic-name',), metavar='NAME', help='The network interface (NIC).', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/networkInterfaces'))
nsg_name_type = CliArgumentType(options_list=('--nsg-name',), metavar='NAME', help='Name of the network security group.')
circuit_name_type = CliArgumentType(options_list=('--circuit-name',), metavar='NAME', help='ExpressRoute circuit name.', id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/expressRouteCircuits'))
virtual_network_name_type = CliArgumentType(options_list=('--vnet-name',), metavar='NAME', help='The virtual network (VNet) name.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworks'))
subnet_name_type = CliArgumentType(options_list=('--subnet-name',), metavar='NAME', help='The subnet name.')
load_balancer_name_type = CliArgumentType(options_list=('--lb-name',), metavar='NAME', help='The load balancer name.', completer=get_resource_name_completion_list('Microsoft.Network/loadBalancers'), id_part='name')
private_ip_address_type = CliArgumentType(help='Static private IP address to use.', validator=validate_private_ip_address)
cookie_based_affinity_type = CliArgumentType(**enum_choice_list(ApplicationGatewayCookieBasedAffinity))
http_protocol_type = CliArgumentType(**enum_choice_list(ApplicationGatewayProtocol))

# ARGUMENT REGISTRATION

register_cli_argument('network', 'subnet_name', subnet_name_type)
register_cli_argument('network', 'virtual_network_name', virtual_network_name_type, id_part='name')
register_cli_argument('network', 'network_security_group_name', nsg_name_type, id_part='name')
register_cli_argument('network', 'private_ip_address', private_ip_address_type)
register_cli_argument('network', 'private_ip_address_version', **enum_choice_list(IPVersion))
register_cli_argument('network', 'tags', tags_type)

register_cli_argument('network application-gateway', 'application_gateway_name', name_arg_type, help='The name of the application gateway.', completer=get_resource_name_completion_list('Microsoft.Network/applicationGateways'), id_part='name')
register_cli_argument('network application-gateway', 'sku', arg_group='Gateway', help='The name of the SKU.', **enum_choice_list(ApplicationGatewaySkuName))
register_cli_argument('network application-gateway', 'virtual_network_name', virtual_network_name_type, arg_group='Network')
register_cli_argument('network application-gateway', 'private_ip_address', arg_group='Network')
register_cli_argument('network application-gateway', 'private_ip_address_allocation', ignore_type, arg_group='Network')
register_cli_argument('network application-gateway', 'public_ip_address_allocation', help='The kind of IP allocation to use when creating a new public IP.', arg_group='Network')
register_cli_argument('network application-gateway', 'servers', nargs='+', help='Space separated list of IP addresses or DNS names corresponding to backend servers.', validator=validate_servers, arg_group='Gateway')
register_cli_argument('network application-gateway', 'http_settings_cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable HTTP settings cookie-based affinity.', arg_group='Gateway')
register_cli_argument('network application-gateway', 'http_settings_protocol', http_protocol_type, help='The HTTP settings protocol.', arg_group='Gateway')
register_cli_argument('network application-gateway', 'subnet_address_prefix', help='The CIDR prefix to use when creating a new subnet.', action=MarkSpecifiedAction, arg_group='Network')
register_cli_argument('network application-gateway', 'vnet_address_prefix', help='The CIDR prefix to use when creating a new VNet.', action=MarkSpecifiedAction, arg_group='Network')
register_cli_argument('network application-gateway', 'virtual_network_type', ignore_type, arg_group='Network')

register_cli_argument('network application-gateway create', 'validate', help='Generate and validate the ARM template without creating any resources.', action='store_true', validator=process_ag_create_namespace)
register_cli_argument('network application-gateway create', 'routing_rule_type', arg_group='Gateway', help='The request routing rule type.', **enum_choice_list(ApplicationGatewayRequestRoutingRuleType))
register_cli_argument('network application-gateway create', 'cert_data', options_list=('--cert-file',), type=file_type, completer=FilesCompleter(), help='The path to the PFX certificate file.', arg_group='Gateway')
register_cli_argument('network application-gateway create', 'frontend_type', ignore_type, arg_group='Gateway')
register_cli_argument('network application-gateway create', 'frontend_port', help='The front end port number.', arg_group='Gateway')
register_cli_argument('network application-gateway create', 'capacity', help='The number of instances to use with the application gateway.', arg_group='Gateway')
register_cli_argument('network application-gateway create', 'cert_password', help='The certificate password', arg_group='Gateway')
register_cli_argument('network application-gateway create', 'http_settings_port', help='The HTTP settings port.', arg_group='Gateway')

with VersionConstraint(ResourceType.MGMT_NETWORK, min_api='2016-12-01') as c:
    for item in ['create', 'http-settings']:
        c.register_cli_argument('network application-gateway {}'.format(item), 'connection_draining_timeout', type=int, help='The time in seconds after a backend server is removed during which on open connection remains active. Range: 0 (disabled) to 3600', arg_group='Gateway' if item == 'create' else None)

register_cli_argument('network application-gateway update', 'sku', arg_group=None)

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True, default_none=True)
register_cli_argument('network application-gateway create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'), arg_group='Network')
register_cli_argument('network application-gateway create', 'public_ip_address_type', ignore_type)

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True)
register_cli_argument('network application-gateway create', 'subnet', help=subnet_help, completer=get_subnet_completion_list(), arg_group='Network')
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

register_cli_argument('network application-gateway auth-cert', 'cert_data', options_list=('--cert-file',), type=file_type, completer=FilesCompleter(), validator=validate_auth_cert)

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
register_cli_argument('network application-gateway http-listener', 'host_name', help='Host name to use for multisite gateways.')

# Add help text to clarify the "default if one" policy.
default_existing = 'If only one exists, omit to use as default.'
register_cli_argument('network application-gateway http-listener create', 'frontend_ip', help='The name or ID of the frontend IP configuration. {}'.format(default_existing))
register_cli_argument('network application-gateway rule create', 'address_pool', help='The name or ID of the backend address pool. {}'.format(default_existing))
register_cli_argument('network application-gateway rule create', 'http_settings', help='The name or ID of the HTTP settings. {}'.format(default_existing))
register_cli_argument('network application-gateway rule create', 'http_listener', help='The name or ID of the HTTP listener. {}'.format(default_existing))
register_cli_argument('network lb rule create', 'backend_address_pool_name', help='The name of the backend address pool. {}'.format(default_existing))
register_cli_argument('network lb rule create', 'frontend_ip_name', help='The name of the frontend IP configuration. {}'.format(default_existing))
register_cli_argument('network lb inbound-nat-rule create', 'frontend_ip_name', help='The name of the frontend IP configuration. {}'.format(default_existing))

register_cli_argument('network application-gateway http-settings', 'cookie_based_affinity', cookie_based_affinity_type, help='Enable or disable cookie-based affinity.')
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

register_cli_argument('network application-gateway ssl-cert', 'cert_data', options_list=('--cert-file',), type=file_type, completer=FilesCompleter(), help='The path to the PFX certificate file.', validator=validate_cert)

register_cli_argument('network application-gateway ssl-policy', 'clear', action='store_true', help='Clear SSL policy.', validator=process_ag_ssl_policy_set_namespace)
register_cli_argument('network application-gateway ssl-policy', 'disabled_ssl_protocols', nargs='+', help='Space separated list of protocols to disable.', **enum_choice_list(ApplicationGatewaySslProtocol))

register_cli_argument('network application-gateway url-path-map create', 'default_address_pool', help='The name or ID of the default backend address pool, if different from --address-pool.', validator=process_ag_url_path_map_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map create', 'default_http_settings', help='The name or ID of the default HTTP settings, if different from --http-settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway url-path-map update', 'default_address_pool', help='The name or ID of the default backend address pool.', validator=process_ag_url_path_map_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map update', 'default_http_settings', help='The name or ID of the default HTTP settings.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway url-path-map', 'rule_name', help='The name of the url-path-map rule.', arg_group='First Rule')
register_cli_argument('network application-gateway url-path-map', 'paths', nargs='+', help='Space separated list of paths to associate with the rule. Valid paths start and end with "/" (ex: "/bar/")', arg_group='First Rule')
register_cli_argument('network application-gateway url-path-map', 'address_pool', help='The name or ID of the backend address pool to use with the created rule.', completer=get_ag_subresource_completion_list('backend_address_pools'), arg_group='First Rule')
register_cli_argument('network application-gateway url-path-map', 'http_settings', help='The name or ID of the HTTP settings to use with the created rule.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'), arg_group='First Rule')

register_cli_argument('network application-gateway url-path-map rule', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=get_ag_url_map_rule_completion_list(), id_part='grandchild_name')
register_cli_argument('network application-gateway url-path-map rule create', 'item_name', options_list=('--name', '-n'), help='The name of the url-path-map rule.', completer=None)
register_cli_argument('network application-gateway url-path-map rule', 'url_path_map_name', options_list=('--path-map-name',), help='The name of the URL path map.', completer=get_ag_subresource_completion_list('url_path_maps'), id_part='child_name')
register_cli_argument('network application-gateway url-path-map rule', 'address_pool', help='The name or ID of the backend address pool. If not specified, the default for the map will be used.', validator=process_ag_url_path_map_rule_create_namespace, completer=get_ag_subresource_completion_list('backend_address_pools'))
register_cli_argument('network application-gateway url-path-map rule', 'http_settings', help='The name or ID of the HTTP settings. If not specified, the default for the map will be used.', completer=get_ag_subresource_completion_list('backend_http_settings_collection'))

register_cli_argument('network application-gateway waf-config', 'enabled', help='Specify whether the application firewall is enabled.', **enum_choice_list(['true', 'false']))

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    register_cli_argument('network application-gateway waf-config', 'firewall_mode', help='Web application firewall mode.', default=ApplicationGatewayFirewallMode.detection.value, **enum_choice_list(ApplicationGatewayFirewallMode))
else:
    register_cli_argument('network application-gateway waf-config', 'firewall_mode', ignore_type)

for item in ['ssl-policy', 'waf-config']:
    register_cli_argument('network application-gateway {}'.format(item), 'application_gateway_name', options_list=('--gateway-name',), help='The name of the application gateway.')

register_cli_argument('network application-gateway waf-config', 'disabled_rule_groups', nargs='+')
register_cli_argument('network application-gateway waf-config', 'disabled_rules', nargs='+')
register_cli_argument('network application-gateway waf-config list-rule-sets', '_type', options_list=['--type'])

# ExpressRoutes
register_cli_argument('network express-route', 'circuit_name', circuit_name_type, options_list=('--name', '-n'))
register_cli_argument('network express-route', 'sku_family', help='Chosen SKU family of ExpressRoute circuit.', **enum_choice_list(ExpressRouteCircuitSkuFamily))
register_cli_argument('network express-route', 'sku_tier', help='SKU Tier of ExpressRoute circuit.', **enum_choice_list(ExpressRouteCircuitSkuTier))
register_cli_argument('network express-route', 'bandwidth_in_mbps', options_list=('--bandwidth',), help="Bandwidth in Mbps of the circuit. It must exactly match one of the available bandwidth offers from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'service_provider_name', options_list=('--provider',), help="Name of the ExpressRoute Service Provider. It must exactly match one of the Service Providers from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'peering_location', help="Name of the peering location. It must exactly match one of the available peering locations from the 'list-service-providers' command.")
register_cli_argument('network express-route', 'device_path', options_list=('--path',), **enum_choice_list(device_path_values))
register_cli_argument('network express-route', 'vlan_id', type=int)
register_cli_argument('network express-route', 'location', location_type, validator=get_default_location_from_resource_group)

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

with VersionConstraint(ResourceType.MGMT_NETWORK, min_api='2016-12-01') as c:
    c.register_cli_argument('network express-route peering', 'route_filter', help='Name or ID of a route filter to apply to the peering settings.', validator=validate_route_filter, arg_group='Microsoft Peering')

# Local Gateway
register_cli_argument('network local-gateway', 'local_network_gateway_name', name_arg_type, help='Name of the local network gateway.', completer=get_resource_name_completion_list('Microsoft.Network/localNetworkGateways'), id_part='name')
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
register_cli_argument('network nic', 'internal_dns_name_label', options_list=('--internal-dns-name',), help='The internal DNS name label.', arg_group='DNS')
register_cli_argument('network nic', 'dns_servers', help='Space separated list of DNS server IP addresses.', nargs='+', arg_group='DNS')

register_cli_argument('network nic create', 'enable_ip_forwarding', options_list=('--ip-forwarding',), help='Enable IP forwarding.', action='store_true')
register_cli_argument('network nic create', 'network_interface_name', nic_type, options_list=('--name', '-n'), id_part=None, validator=process_nic_create_namespace)

with VersionConstraint(ResourceType.MGMT_NETWORK, min_api='2016-09-01') as c:
    IPVersion = get_sdk(ResourceType.MGMT_NETWORK, 'IPVersion', mod='models')
    c.register_cli_argument('network nic create', 'private_ip_address_version', help='The private IP address version to use.', default=IPVersion.ipv4.value if IPVersion else '')

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, default_none=True)
register_cli_argument('network nic create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

nsg_help = get_folded_parameter_help_string('network security group', allow_none=True, default_none=True)
register_cli_argument('network nic create', 'network_security_group', help=nsg_help, completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name')
register_cli_argument('network nic create', 'subnet', help=subnet_help, completer=get_subnet_completion_list())

register_cli_argument('network nic update', 'enable_ip_forwarding', options_list=('--ip-forwarding',), **enum_choice_list(['true', 'false']))
register_cli_argument('network nic update', 'network_security_group', help='Name or ID of the associated network security group.', validator=get_nsg_validator(), completer=get_resource_name_completion_list('Microsoft.Network/networkSecurityGroups'))
register_cli_argument('network nic update', 'dns_servers', help='Space separated list of DNS server IP addresses. Use "" to revert to default Azure servers.', nargs='+', arg_group='DNS')

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
register_cli_argument('network nic ip-config', 'public_ip_address', help='Name or ID of the public IP to use.', validator=get_public_ip_validator())
register_cli_argument('network nic ip-config', 'private_ip_address_allocation', ignore_type)
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
register_cli_argument('network nsg create', 'location', location_type, validator=get_default_location_from_resource_group)

# NSG Rule
register_cli_argument('network nsg rule', 'security_rule_name', name_arg_type, id_part='child_name', help='Name of the network security group rule')
register_cli_argument('network nsg rule', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME', help='Name of the network security group', id_part='name')

for item in ['create', 'update']:
    register_cli_argument('network nsg rule {}'.format(item), 'priority', help='Rule priority, between 100 (highest priority) and 4096 (lowest priority). Must be unique for each rule in the collection.', type=int)
    register_cli_argument('network nsg rule {}'.format(item), 'description', help='Rule description')
    register_cli_argument('network nsg rule {}'.format(item), 'access', help=None, **enum_choice_list(SecurityRuleAccess))
    register_cli_argument('network nsg rule {}'.format(item), 'protocol', help='Network protocol this rule applies to.', **enum_choice_list(SecurityRuleProtocol))
    register_cli_argument('network nsg rule {}'.format(item), 'direction', help=None, **enum_choice_list(SecurityRuleDirection))
    register_cli_argument('network nsg rule {}'.format(item), 'source_port_range', help="Port or port range between 0-65535. Use '*' to match all ports.", arg_group='Source')
    register_cli_argument('network nsg rule {}'.format(item), 'source_address_prefix', help="CIDR prefix or IP range. Use '*' to match all IPs. Can also use 'VirtualNetwork', 'AzureLoadBalancer', and 'Internet'.", arg_group='Source')
    register_cli_argument('network nsg rule {}'.format(item), 'destination_port_range', help="Port or port range between 0-65535. Use '*' to match all ports.", arg_group='Destination')
    register_cli_argument('network nsg rule {}'.format(item), 'destination_address_prefix', help="CIDR prefix or IP range. Use '*' to match all IPs. Can also use 'VirtualNetwork', 'AzureLoadBalancer', and 'Internet'.", arg_group='Destination')

register_cli_argument('network nsg rule create', 'network_security_group_name', options_list=('--nsg-name',), metavar='NSGNAME', help='Name of the network security group', id_part=None)

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
    if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
        register_cli_argument('network public-ip {}'.format(item), 'version', help='IP address type.', default=IPVersion.ipv4.value, **enum_choice_list(IPVersion))
    else:
        register_cli_argument('network public-ip {}'.format(item), 'version', ignore_type)

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

# Route Filter
register_cli_argument('network route-filter', 'route_filter_name', name_arg_type, help='Name of the route filter.')
register_cli_argument('network route-filter', 'expand', **enum_choice_list(['peerings']))

register_cli_argument('network route-filter create', 'location', location_type, validator=get_default_location_from_resource_group)

register_cli_argument('network route-filter rule', 'route_filter_name', options_list=['--filter-name'], help='Name of the route filter.', id_part='name')
register_cli_argument('network route-filter rule', 'rule_name', name_arg_type, help='Name of the route filter rule.', id_part='child_name')
register_cli_argument('network route-filter rule', 'access', help='The access type of the rule.', **model_choice_list(ResourceType.MGMT_NETWORK, 'Access'))
register_cli_argument('network route-filter rule', 'communities', nargs='+')

register_cli_argument('network route-filter rule create', 'location', location_type, validator=get_default_location_from_resource_group)

# VNET
register_cli_argument('network vnet', 'virtual_network_name', virtual_network_name_type, options_list=('--name', '-n'), id_part='name')
register_cli_argument('network vnet', 'vnet_prefixes', nargs='+', help='Space separated list of IP address prefixes for the VNet.', options_list=('--address-prefixes',), metavar='PREFIX')
register_cli_argument('network vnet', 'dns_servers', nargs='+', help='Space separated list of DNS server IP addresses.', metavar='IP')

register_cli_argument('network vnet create', 'location', location_type)
register_cli_argument('network vnet create', 'subnet_name', help='Name of a new subnet to create within the VNet.', validator=process_vnet_create_namespace)
register_cli_argument('network vnet create', 'subnet_prefix', help='IP address prefix for the new subnet. If omitted, automatically reserves a /24 (or as large as available) block within the VNet address space.', metavar='PREFIX')
register_cli_argument('network vnet create', 'vnet_name', virtual_network_name_type, options_list=('--name', '-n'), completer=None)

register_cli_argument('network vnet subnet', 'subnet_name', arg_type=subnet_name_type, options_list=('--name', '-n'), id_part='child_name')
register_cli_argument('network vnet update', 'address_prefixes', nargs='+')

register_cli_argument('network vnet peering', 'virtual_network_name', virtual_network_name_type)
register_cli_argument('network vnet peering', 'virtual_network_peering_name', options_list=('--name', '-n'), help='The name of the VNet peering.', id_part='child_name')
register_cli_argument('network vnet peering', 'remote_virtual_network', options_list=('--remote-vnet-id',), help='ID of the remote VNet.')

register_cli_argument('network vnet peering create', 'allow_virtual_network_access', options_list=('--allow-vnet-access',), action='store_true', help='Allows VMs in the remote VNet to access all VMs in the local VNet.')
register_cli_argument('network vnet peering create', 'allow_gateway_transit', action='store_true', help='Allows gateway link to be used in the remote VNet.')
register_cli_argument('network vnet peering create', 'allow_forwarded_traffic', action='store_true', help='Allows forwarded traffic from the VMs in the remote VNet.')
register_cli_argument('network vnet peering create', 'use_remote_gateways', action='store_true', help='Allows VNet to use the remote VNet\'s gateway. Remote VNet gateway must have --allow-gateway-transit enabled for remote peering. Only 1 peering can have this flag enabled. Cannot be set if the VNet already has a gateway.')

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
register_cli_argument('network lb', 'frontend_ip_name', help='The name of the frontend IP configuration.', completer=get_lb_subresource_completion_list('frontend_ip_configurations'))
register_cli_argument('network lb', 'floating_ip', help='Enable floating IP.', **enum_choice_list(['true', 'false']))
register_cli_argument('network lb', 'idle_timeout', help='Idle timeout in minutes.')
register_cli_argument('network lb', 'protocol', help='', **enum_choice_list(TransportProtocol))

for item in ['backend_pool_name', 'backend_address_pool_name']:
    register_cli_argument('network lb', item, options_list=('--backend-pool-name',), help='The name of the backend address pool.', completer=get_lb_subresource_completion_list('backend_address_pools'))

register_cli_argument('network lb create', 'validate', help='Generate and validate the ARM template without creating any resources.', action='store_true', validator=process_lb_create_namespace)
register_cli_argument('network lb create', 'public_ip_address_allocation', **enum_choice_list(IPAllocationMethod))
register_cli_argument('network lb create', 'public_ip_dns_name', help='Globally unique DNS name for a new public IP.')

public_ip_help = get_folded_parameter_help_string('public IP address', allow_none=True, allow_new=True)
register_cli_argument('network lb create', 'public_ip_address', help=public_ip_help, completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))
register_cli_argument('network lb create', 'public_ip_type', ignore_type)

subnet_help = get_folded_parameter_help_string('subnet', other_required_option='--vnet-name', allow_new=True, allow_none=True, default_none=True)
register_cli_argument('network lb create', 'subnet', help=subnet_help, completer=get_subnet_completion_list())
register_cli_argument('network lb create', 'subnet_address_prefix', help='The CIDR address prefix to use when creating a new subnet.')
register_cli_argument('network lb create', 'vnet_name', virtual_network_name_type)
register_cli_argument('network lb create', 'vnet_address_prefix', help='The CIDR address prefix to use when creating a new VNet.')
register_cli_argument('network lb create', 'vnet_type', ignore_type)

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

register_cli_argument('network vnet-gateway', 'virtual_network_gateway_name', options_list=('--name', '-n'), help='Name of the VNet gateway.', completer=get_resource_name_completion_list('Microsoft.Network/virtualNetworkGateways'), id_part='name')
register_cli_argument('network vnet-gateway', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vnet-gateway', 'gateway_name', help='Virtual network gateway name')
register_cli_argument('network vnet-gateway', 'gateway_type', help='The gateway type.', **enum_choice_list(VirtualNetworkGatewayType))
register_cli_argument('network vnet-gateway', 'sku', help='VNet gateway SKU.', **enum_choice_list(VirtualNetworkGatewaySkuName))
register_cli_argument('network vnet-gateway', 'vpn_type', help='VPN routing type.', **enum_choice_list(VpnType))
register_cli_argument('network vnet-gateway', 'bgp_peering_address', arg_group='BGP Peering', help='IP address to use for BGP peering.')
register_cli_argument('network vnet-gateway', 'address_prefixes', help='Space separated list of address prefixes to associate with the VNet gateway.', nargs='+')
register_cli_argument('network vnet-gateway', 'public_ip_address', options_list=['--public-ip-addresses'], nargs='+', help='Specify a single public IP (name or ID) for an active-standby gateway. Specify two space-separated public IPs for an active-active gateway.', completer=get_resource_name_completion_list('Microsoft.Network/publicIPAddresses'))

register_cli_argument('network vnet-gateway create', 'asn', validator=process_vnet_gateway_create_namespace)

register_cli_argument('network vnet-gateway update', 'enable_bgp', help='Enable BGP (Border Gateway Protocol)', arg_group='BGP Peering', **enum_choice_list(['true', 'false']))
register_cli_argument('network vnet-gateway update', 'virtual_network', virtual_network_name_type, options_list=('--vnet',), help="Name or ID of a virtual network that contains a subnet named 'GatewaySubnet'.", validator=process_vnet_gateway_update_namespace)

vnet_help = "Name or ID of an existing virtual network which has a subnet named 'GatewaySubnet'."
register_cli_argument('network vnet-gateway create', 'virtual_network', options_list=('--vnet',), help=vnet_help)

register_cli_argument('network vnet-gateway root-cert create', 'public_cert_data', help='Base64 contents of the root certificate file or file path.', type=file_type, completer=FilesCompleter(), validator=load_cert_file('public_cert_data'))
register_cli_argument('network vnet-gateway root-cert create', 'cert_name', help='Root certificate name', options_list=('--name', '-n'))
register_cli_argument('network vnet-gateway root-cert create', 'gateway_name', help='Virtual network gateway name')

register_cli_argument('network vnet-gateway revoked-cert create', 'thumbprint', help='Certificate thumbprint.')

register_extra_cli_argument('network vnet-gateway update', 'address_prefixes', options_list=('--address-prefixes',), help='List of address prefixes for the VPN gateway.  Prerequisite for uploading certificates.', nargs='+')


# VPN connection
register_cli_argument('network vpn-connection', 'virtual_network_gateway_connection_name', options_list=('--name', '-n'), metavar='NAME', id_part='name', help='Connection name.')
register_cli_argument('network vpn-connection', 'shared_key', help='Shared IPSec key.')
register_cli_argument('network vpn-connection', 'connection_name', help='Connection name.')

with VersionConstraint(ResourceType.MGMT_NETWORK, min_api='2017-03-01') as c:
    c.register_cli_argument('network vpn-connection', 'use_policy_based_traffic_selectors', help='Enable policy-based traffic selectors.', **three_state_flag())

register_cli_argument('network vpn-connection create', 'connection_name', options_list=('--name', '-n'), metavar='NAME', help='Connection name.')
register_cli_argument('network vpn-connection create', 'vnet_gateway1', validator=process_vpn_connection_create_namespace)
register_cli_argument('network vpn-connection create', 'connection_type', ignore_type)

for item in ['vnet_gateway2', 'local_gateway2', 'express_route_circuit2']:
    register_cli_argument('network vpn-connection create', item, arg_group='Destination')

register_cli_argument('network vpn-connection update', 'routing_weight', type=int, help='Connection routing weight')
register_cli_argument('network vpn-connection update', 'enable_bgp', help='Enable BGP (Border Gateway Protocol)', **enum_choice_list(['true', 'false']))

# VPN connection shared key
register_cli_argument('network vpn-connection shared-key', 'connection_shared_key_name', options_list=('--name', '-n'), id_part='name')
register_cli_argument('network vpn-connection shared-key', 'virtual_network_gateway_connection_name', options_list=('--connection-name',), metavar='NAME', id_part='name')
register_cli_argument('network vpn-connection shared-key', 'key_length', type=int)

# VPN connection IPSec policy
param_map = {
    'dh_group': 'DhGroup',
    'ike_encryption': 'IkeEncryption',
    'ike_integrity': 'IkeIntegrity',
    'ipsec_encryption': 'IpsecEncryption',
    'ipsec_integrity': 'IpsecIntegrity',
    'pfs_group': 'PfsGroup'
}
for dest, model_name in param_map.items():
    register_cli_argument('network vpn-connection ipsec-policy', dest, **model_choice_list(ResourceType.MGMT_NETWORK, model_name))
register_cli_argument('network vpn-connection ipsec-policy', 'sa_data_size_kilobytes', options_list=['--sa-max-size'], type=int)
register_cli_argument('network vpn-connection ipsec-policy', 'sa_life_time_seconds', options_list=['--sa-lifetime'], type=int)

# Traffic manager profiles
register_cli_argument('network traffic-manager profile', 'traffic_manager_profile_name', name_arg_type, id_part='name', help='Traffic manager profile name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile', 'profile_name', name_arg_type, id_part='name', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'))
register_cli_argument('network traffic-manager profile', 'monitor_path', help='Path to monitor.')
register_cli_argument('network traffic-manager profile', 'monitor_port', help='Port to monitor.', type=int)
register_cli_argument('network traffic-manager profile', 'monitor_protocol', help='Monitor protocol.')
register_cli_argument('network traffic-manager profile', 'profile_status', options_list=('--status',), help='Status of the Traffic Manager profile.', **enum_choice_list(['Enabled', 'Disabled']))
register_cli_argument('network traffic-manager profile', 'routing_method', help='Routing method.', **enum_choice_list(['Performance', 'Weighted', 'Priority', 'Geographic']))
register_cli_argument('network traffic-manager profile', 'unique_dns_name', help="Relative DNS name for the traffic manager profile. Resulting FQDN will be `<unique-dns-name>.trafficmanager.net` and must be globally unique.")
register_cli_argument('network traffic-manager profile', 'ttl', help='DNS config time-to-live in seconds.', type=int)

register_cli_argument('network traffic-manager profile create', 'status', help='Create an enabled or disabled profile.', **enum_choice_list(['Enabled', 'Disabled']))

register_cli_argument('network traffic-manager profile check-dns', 'name', name_arg_type, help='DNS prefix to verify availability for.', required=True)
register_cli_argument('network traffic-manager profile check-dns', 'type', ignore_type, default='Microsoft.Network/trafficManagerProfiles')

# Traffic manager endpoints
endpoint_types = ['azureEndpoints', 'externalEndpoints', 'nestedEndpoints']
register_cli_argument('network traffic-manager endpoint', 'endpoint_name', name_arg_type, id_part='child_name', help='Endpoint name.', completer=get_tm_endpoint_completion_list())
register_cli_argument('network traffic-manager endpoint', 'endpoint_type', options_list=['--type', '-t'], help='Endpoint type.', id_part='child_name', **enum_choice_list(endpoint_types))
register_cli_argument('network traffic-manager endpoint', 'profile_name', help='Name of parent profile.', completer=get_resource_name_completion_list('Microsoft.Network/trafficManagerProfiles'), id_part='name')
register_cli_argument('network traffic-manager endpoint', 'endpoint_location', help="Location of the external or nested endpoints when using the 'Performance' routing method.")
register_cli_argument('network traffic-manager endpoint', 'endpoint_monitor_status', help='The monitoring status of the endpoint.')
register_cli_argument('network traffic-manager endpoint', 'endpoint_status', help="The status of the endpoint. If enabled the endpoint is probed for endpoint health and included in the traffic routing method.")
register_cli_argument('network traffic-manager endpoint', 'min_child_endpoints', help="The minimum number of endpoints that must be available in the child profile for the parent profile to be considered available. Only applicable to an endpoint of type 'NestedEndpoints'.")
register_cli_argument('network traffic-manager endpoint', 'priority', help="Priority of the endpoint when using the 'Priority' traffic routing method. Values range from 1 to 1000, with lower values representing higher priority.", type=int)
register_cli_argument('network traffic-manager endpoint', 'target', help='Fully-qualified DNS name of the endpoint.')
register_cli_argument('network traffic-manager endpoint', 'target_resource_id', help="The Azure Resource URI of the endpoint. Not applicable for endpoints of type 'ExternalEndpoints'.")
register_cli_argument('network traffic-manager endpoint', 'weight', help="Weight of the endpoint when using the 'Weighted' traffic routing method. Values range from 1 to 1000.", type=int)
register_cli_argument('network traffic-manager endpoint', 'geo_mapping', nargs='+')

register_cli_argument('network traffic-manager endpoint create', 'target', help='Fully-qualified DNS name of the endpoint.', validator=process_tm_endpoint_create_namespace)

# DNS
register_cli_argument('network dns', 'record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
register_cli_argument('network dns', 'relative_record_set_name', name_arg_type, help='The name of the record set, relative to the name of the zone.')
register_cli_argument('network dns', 'zone_name', options_list=('--zone-name', '-z'), help='The name of the zone.', type=dns_zone_name_type)
register_cli_argument('network dns', 'metadata', nargs='+', help='Metadata in space-separated key=value pairs. This overwrites any existing metadata.', validator=validate_metadata)

register_cli_argument('network dns zone', 'zone_name', name_arg_type)
register_cli_argument('network dns zone', 'location', ignore_type)

register_cli_argument('network dns zone import', 'file_name', options_list=('--file-name', '-f'), type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to import')
register_cli_argument('network dns zone export', 'file_name', options_list=('--file-name', '-f'), type=file_type, completer=FilesCompleter(), help='Path to the DNS zone file to save')
register_cli_argument('network dns zone update', 'if_none_match', ignore_type)

for item in ['record_type', 'record_set_type']:
    register_cli_argument('network dns record-set', item, ignore_type, validator=validate_dns_record_type)

register_cli_argument('network dns record-set create', 'ttl', help='Record set TTL (time-to-live)')
register_cli_argument('network dns record-set create', 'if_none_match', help='Create the record set only if it does not already exist.', action='store_true')

for item in ['a', 'aaaa', 'cname', 'mx', 'ns', 'ptr', 'srv', 'txt']:
    register_cli_argument('network dns record-set {} add-record'.format(item), 'record_set_name', options_list=('--record-set-name', '-n'), help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')
    register_cli_argument('network dns record-set {} remove-record'.format(item), 'record_set_name', options_list=('--record-set-name', '-n'), help='The name of the record set relative to the zone.')
    register_cli_argument('network dns record-set {} remove-record'.format(item), 'keep_empty_record_set', action='store_true', help='Keep the empty record set if the last record is removed.')
register_cli_argument('network dns record-set cname set-record', 'record_set_name', options_list=('--record-set-name', '-n'), help='The name of the record set relative to the zone. Creates a new record set if one does not exist.')

register_cli_argument('network dns record-set soa', 'relative_record_set_name', ignore_type, default='@')

register_cli_argument('network dns record-set a', 'ipv4_address', options_list=('--ipv4-address', '-a'), help='IPV4 address in string notation.')
register_cli_argument('network dns record-set aaaa', 'ipv6_address', options_list=('--ipv6-address', '-a'), help='IPV6 address in string notation.')
register_cli_argument('network dns record-set cname', 'cname', options_list=('--cname', '-c'), help='Canonical name.')
register_cli_argument('network dns record-set mx', 'exchange', options_list=('--exchange', '-e'), help='Exchange metric.')
register_cli_argument('network dns record-set mx', 'preference', options_list=('--preference', '-p'), help='Preference metric.')
register_cli_argument('network dns record-set ns', 'dname', options_list=('--nsdname', '-d'), help='Name server domain name.')
register_cli_argument('network dns record-set ptr', 'dname', options_list=('--ptrdname', '-d'), help='PTR target domain name.')
register_cli_argument('network dns record-set soa', 'host', options_list=('--host', '-t'), help='Host name.')
register_cli_argument('network dns record-set soa', 'email', options_list=('--email', '-e'), help='Email address.')
register_cli_argument('network dns record-set soa', 'expire_time', options_list=('--expire-time', '-x'), help='Expire time (seconds).')
register_cli_argument('network dns record-set soa', 'minimum_ttl', options_list=('--minimum-ttl', '-m'), help='Minimum TTL (time-to-live, seconds).')
register_cli_argument('network dns record-set soa', 'refresh_time', options_list=('--refresh-time', '-f'), help='Refresh value (seconds).')
register_cli_argument('network dns record-set soa', 'retry_time', options_list=('--retry-time', '-r'), help='Retry time (seconds).')
register_cli_argument('network dns record-set soa', 'serial_number', options_list=('--serial-number', '-s'), help='Serial number.')
register_cli_argument('network dns record-set srv', 'priority', options_list=('--priority', '-p'), help='Priority metric.')
register_cli_argument('network dns record-set srv', 'weight', options_list=('--weight', '-w'), help='Weight metric.')
register_cli_argument('network dns record-set srv', 'port', options_list=('--port', '-r'), help='Service port.')
register_cli_argument('network dns record-set srv', 'target', options_list=('--target', '-t'), help='Target domain name.')
register_cli_argument('network dns record-set txt', 'value', options_list=('--value', '-v'), nargs='+', help='Space separated list of text values which will be concatenated together.')

# NetworkWatcher commands
register_cli_argument('network watcher', 'network_watcher_name', name_arg_type, help='Name of the Network Watcher.')

register_cli_argument('network watcher configure', 'locations', location_type, options_list=['--locations', '-l'], nargs='+')
register_cli_argument('network watcher configure', 'enabled', **three_state_flag())

register_cli_argument('network watcher show-topology', 'network_watcher_name', ignore_type, options_list=['--watcher'])
register_cli_argument('network watcher show-topology', 'resource_group_name', ignore_type, options_list=['--watcher-resource-group'])
register_cli_argument('network watcher show-topology', 'target_resource_group_name', options_list=['--resource-group', '-g'], completer=get_resource_group_completion_list)
register_extra_cli_argument('network watcher show-topology', 'location', validator=process_nw_topology_namespace)

register_cli_argument('network watcher create', 'location', validator=get_default_location_from_resource_group)

register_cli_argument('network watcher', 'watcher_rg', ignore_type)
register_cli_argument('network watcher', 'watcher_name', ignore_type)

for item in ['test-ip-flow', 'show-next-hop', 'show-security-group-view', 'packet-capture create']:
    register_cli_argument('network watcher {}'.format(item), 'watcher_name', ignore_type, validator=get_network_watcher_from_vm)
    register_cli_argument('network watcher {}'.format(item), 'location', ignore_type)
    register_cli_argument('network watcher {}'.format(item), 'watcher_rg', ignore_type)
    register_cli_argument('network watcher {}'.format(item), 'vm', help='Name or ID of the VM to target.')
    register_cli_argument('network watcher {}'.format(item), 'resource_group_name', help='Name of the resource group the target VM is in. Do not use when supplying VM ID.')
    register_cli_argument('network watcher {}'.format(item), 'nic', help='Name or ID of the NIC resource to test. If the VM has multiple NICs and IP forwarding is enabled on any of them, this parameter is required.')

register_cli_argument('network watcher test-connectivity', 'source_resource', validator=process_nw_test_connectivity_namespace)
register_cli_argument('network watcher test-connectivity', 'source_port', type=int)
register_cli_argument('network watcher test-connectivity', 'dest_resource', arg_group='Destination')
register_cli_argument('network watcher test-connectivity', 'dest_address', arg_group='Destination')
register_cli_argument('network watcher test-connectivity', 'dest_port', type=int, arg_group='Destination')

register_cli_argument('network watcher packet-capture', 'capture_name', name_arg_type, help='Name of the packet capture session.')
register_cli_argument('network watcher packet-capture', 'storage_account', arg_group='Storage')
register_cli_argument('network watcher packet-capture', 'storage_path', arg_group='Storage')
register_cli_argument('network watcher packet-capture', 'file_path', arg_group='Storage')
register_cli_argument('network watcher packet-capture', 'filters', type=get_json_object)

register_cli_argument('network watcher flow-log', 'enabled', validator=process_nw_flow_log_set_namespace, **three_state_flag())

register_cli_argument('network watcher flow-log show', 'nsg', validator=process_nw_flow_log_show_namespace)

for item in ['list', 'stop', 'delete', 'show', 'show-status']:
    register_extra_cli_argument('network watcher packet-capture {}'.format(item), 'location')
    register_cli_argument('network watcher packet-capture {}'.format(item), 'location', location_type, required=True)
    register_cli_argument('network watcher packet-capture {}'.format(item), 'packet_capture_name', name_arg_type)
    register_cli_argument('network watcher packet-capture {}'.format(item), 'network_watcher_name', ignore_type, options_list=['--network-watcher-name'], validator=get_network_watcher_from_location(remove=True, rg_name='resource_group_name', watcher_name='network_watcher_name'))
    register_cli_argument('network watcher packet-capture {}'.format(item), 'resource_group_name', ignore_type)

register_cli_argument('network watcher packet-capture create', 'vm', validator=process_nw_packet_capture_create_namespace)

register_cli_argument('network watcher test-ip-flow', 'direction', **enum_choice_list(Direction))
register_cli_argument('network watcher test-ip-flow', 'protocol', **enum_choice_list(Protocol))

register_cli_argument('network watcher show-next-hop', 'source_ip', help='Source IPv4 address.')
register_cli_argument('network watcher show-next-hop', 'dest_ip', help='Destination IPv4 address.')

register_cli_argument('network watcher troubleshooting', 'resource_type', options_list=['--resource-type', '-t'], id_part='resource_type', **enum_choice_list(['vnetGateway', 'vpnConnection']))
register_cli_argument('network watcher troubleshooting start', 'resource', help='Name or ID of the resource to troubleshoot.', validator=process_nw_troubleshooting_start_namespace)
register_cli_argument('network watcher troubleshooting show', 'resource', help='Name or ID of the resource to troubleshoot.', validator=process_nw_troubleshooting_show_namespace)
