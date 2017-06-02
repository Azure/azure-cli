# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.arm import cli_generic_update_command, cli_generic_wait_command
from azure.cli.core.commands import \
    (DeploymentOutputLongRunningOperation, cli_command)
from azure.cli.core.util import empty_on_404
from azure.cli.core.profiles import supported_api_version, ResourceType

from ._client_factory import (cf_application_gateways, cf_express_route_circuit_authorizations,
                              cf_express_route_circuit_peerings, cf_express_route_circuits,
                              cf_express_route_service_providers, cf_load_balancers, cf_local_network_gateways,
                              cf_network_interfaces, cf_network_security_groups, cf_network_watcher, cf_packet_capture,
                              cf_route_tables, cf_routes, cf_route_filter_rules, cf_route_filters, cf_virtual_networks,
                              cf_virtual_network_peerings, cf_virtual_network_gateway_connections,
                              cf_virtual_network_gateways, cf_traffic_manager_mgmt_endpoints,
                              cf_traffic_manager_mgmt_profiles, cf_dns_mgmt_record_sets, cf_dns_mgmt_zones,
                              cf_tm_geographic, cf_security_rules, cf_subnets, cf_usages, cf_service_community,
                              cf_public_ip_addresses)
from ._util import (list_network_resource_property,
                    get_network_resource_property_entry,
                    delete_network_resource_property_entry)
from ._format import \
    (transform_local_gateway_table_output, transform_dns_record_set_output,
     transform_dns_record_set_table_output, transform_dns_zone_table_output,
     transform_vnet_create_output, transform_public_ip_create_output,
     transform_traffic_manager_create_output, transform_nic_create_output,
     transform_nsg_create_output, transform_vnet_gateway_create_output,
     transform_vpn_connection, transform_vpn_connection_list,
     transform_vpn_connection_create_output, transform_geographic_hierachy_table_output,
     transform_service_community_table_output, transform_waf_rule_sets_table_output,
     transform_network_usage_list, transform_network_usage_table)


custom_path = 'azure.cli.command_modules.network.custom#'

# Application gateways
ag_path = 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.'
cli_command(__name__, 'network application-gateway create', custom_path + 'create_application_gateway', transform=DeploymentOutputLongRunningOperation('Starting network application-gateway create'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway delete', ag_path + 'delete', cf_application_gateways, no_wait_param='raw')
cli_command(__name__, 'network application-gateway show', ag_path + 'get', cf_application_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network application-gateway list', custom_path + 'list_application_gateways')
cli_command(__name__, 'network application-gateway start', ag_path + 'start', cf_application_gateways)
cli_command(__name__, 'network application-gateway stop', ag_path + 'stop', cf_application_gateways)

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network application-gateway show-backend-health', ag_path + 'backend_health', cf_application_gateways)

cli_generic_update_command(__name__, 'network application-gateway update',
                           ag_path + 'get', ag_path + 'create_or_update', cf_application_gateways,
                           no_wait_param='raw', custom_function_op=custom_path + 'update_application_gateway')
cli_generic_wait_command(__name__, 'network application-gateway wait', ag_path + 'get', cf_application_gateways)


property_map = {
    'authentication_certificates': 'auth-cert',
    'ssl_certificates': 'ssl-cert',
    'frontend_ip_configurations': 'frontend-ip',
    'frontend_ports': 'frontend-port',
    'backend_address_pools': 'address-pool',
    'backend_http_settings_collection': 'http-settings',
    'http_listeners': 'http-listener',
    'request_routing_rules': 'rule',
    'probes': 'probe',
    'url_path_maps': 'url-path-map',
}


def _make_singular(value):
    try:
        if value.endswith('ies'):
            value = value[:-3] + 'y'
        elif value.endswith('s'):
            value = value[:-1]
        return value
    except AttributeError:
        return value


for subresource, alias in property_map.items():
    cli_command(__name__, 'network application-gateway {} list'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(list_network_resource_property('application_gateways', subresource)))
    cli_command(__name__, 'network application-gateway {} show'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry('application_gateways', subresource)), exception_handler=empty_on_404)
    cli_command(__name__, 'network application-gateway {} delete'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry('application_gateways', subresource)), no_wait_param='no_wait')
    cli_command(__name__, 'network application-gateway {} create'.format(alias), custom_path + 'create_ag_{}'.format(_make_singular(subresource)), no_wait_param='no_wait')
    cli_generic_update_command(__name__, 'network application-gateway {} update'.format(alias),
                               ag_path + 'get', ag_path + 'create_or_update', cf_application_gateways,
                               no_wait_param='raw',
                               custom_function_op=custom_path + 'update_ag_{}'.format(_make_singular(subresource)),
                               child_collection_prop_name=subresource)

cli_command(__name__, 'network application-gateway ssl-policy set', custom_path + 'set_ag_ssl_policy', no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway ssl-policy show', custom_path + 'show_ag_ssl_policy', exception_handler=empty_on_404)

cli_command(__name__, 'network application-gateway url-path-map rule create', custom_path + 'create_ag_url_path_map_rule')
cli_command(__name__, 'network application-gateway url-path-map rule delete', custom_path + 'delete_ag_url_path_map_rule')

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-03-01'):
    cli_command(__name__, 'network application-gateway waf-config set', custom_path + 'set_ag_waf_config_2017_03_01', no_wait_param='no_wait')
else:
    cli_command(__name__, 'network application-gateway waf-config set', custom_path + 'set_ag_waf_config_2016_09_01', no_wait_param='no_wait')

cli_command(__name__, 'network application-gateway waf-config show', custom_path + 'show_ag_waf_config', exception_handler=empty_on_404)

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2017-03-01'):
    cli_command(__name__, 'network application-gateway waf-config list-rule-sets', custom_path + 'list_ag_waf_rule_sets', cf_application_gateways, table_transformer=transform_waf_rule_sets_table_output)

# ExpressRouteCircuitAuthorizationsOperations
erca_path = 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.'
cli_command(__name__, 'network express-route auth delete', erca_path + 'delete', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth show', erca_path + 'get', cf_express_route_circuit_authorizations, exception_handler=empty_on_404)
cli_command(__name__, 'network express-route auth list', erca_path + 'list', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth create', erca_path + 'create_or_update', cf_express_route_circuit_authorizations)

# ExpressRouteCircuitPeeringsOperations
ercp_path = 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.'
cli_command(__name__, 'network express-route peering delete', ercp_path + 'delete', cf_express_route_circuit_peerings)
cli_command(__name__, 'network express-route peering show', ercp_path + 'get', cf_express_route_circuit_peerings, exception_handler=empty_on_404)
cli_command(__name__, 'network express-route peering list', ercp_path + 'list', cf_express_route_circuit_peerings)
cli_generic_update_command(__name__, 'network express-route peering update',
                           ercp_path + 'get', ercp_path + 'create_or_update', cf_express_route_circuit_peerings,
                           setter_arg_name='peering_parameters', custom_function_op=custom_path + 'update_express_route_peering')
cli_command(__name__, 'network express-route peering create', custom_path + 'create_express_route_peering', cf_express_route_circuit_peerings)

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    # ExpressRouteCircuitsOperations
    erco_path = 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.'
    cli_command(__name__, 'network express-route delete', erco_path + 'delete', cf_express_route_circuits, no_wait_param='raw')
    cli_command(__name__, 'network express-route show', erco_path + 'get', cf_express_route_circuits, exception_handler=empty_on_404)
    cli_command(__name__, 'network express-route get-stats', erco_path + 'get_stats', cf_express_route_circuits)
    cli_command(__name__, 'network express-route list-arp-tables', erco_path + 'list_arp_table', cf_express_route_circuits)
    cli_command(__name__, 'network express-route list-route-tables', erco_path + 'list_routes_table', cf_express_route_circuits)
    cli_command(__name__, 'network express-route create', custom_path + 'create_express_route', no_wait_param='no_wait')
    cli_command(__name__, 'network express-route list', custom_path + 'list_express_route_circuits')
    cli_generic_update_command(__name__, 'network express-route update',
                               erco_path + 'get', erco_path + 'create_or_update', cf_express_route_circuits,
                               custom_function_op=custom_path + 'update_express_route', no_wait_param='raw')
    cli_generic_wait_command(__name__, 'network express-route wait', erco_path + 'get', cf_express_route_circuits)

    # ExpressRouteServiceProvidersOperations
    ersp_path = 'azure.mgmt.network.operations.express_route_service_providers_operations#ExpressRouteServiceProvidersOperations.'
    cli_command(__name__, 'network express-route list-service-providers', ersp_path + 'list', cf_express_route_service_providers)

# LoadBalancersOperations
lb_path = 'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.'
cli_command(__name__, 'network lb create', custom_path + 'create_load_balancer', transform=DeploymentOutputLongRunningOperation('Starting network lb create'), no_wait_param='no_wait')
cli_command(__name__, 'network lb delete', lb_path + 'delete', cf_load_balancers)
cli_command(__name__, 'network lb show', lb_path + 'get', cf_load_balancers, exception_handler=empty_on_404)
cli_command(__name__, 'network lb list', custom_path + 'list_lbs')
cli_generic_update_command(__name__, 'network lb update', lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers)


property_map = {
    'frontend_ip_configurations': 'frontend-ip',
    'inbound_nat_rules': 'inbound-nat-rule',
    'inbound_nat_pools': 'inbound-nat-pool',
    'backend_address_pools': 'address-pool',
    'load_balancing_rules': 'rule',
    'probes': 'probe'
}
for subresource, alias in property_map.items():
    cli_command(__name__, 'network lb {} list'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(list_network_resource_property('load_balancers', subresource)))
    cli_command(__name__, 'network lb {} show'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry('load_balancers', subresource)), exception_handler=empty_on_404)
    cli_command(__name__, 'network lb {} delete'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry('load_balancers', subresource)))

cli_command(__name__, 'network lb frontend-ip create', custom_path + 'create_lb_frontend_ip_configuration')
cli_command(__name__, 'network lb inbound-nat-rule create', custom_path + 'create_lb_inbound_nat_rule')
cli_command(__name__, 'network lb inbound-nat-pool create', custom_path + 'create_lb_inbound_nat_pool')
cli_command(__name__, 'network lb address-pool create', custom_path + 'create_lb_backend_address_pool')
cli_command(__name__, 'network lb rule create', custom_path + 'create_lb_rule')
cli_command(__name__, 'network lb probe create', custom_path + 'create_lb_probe')

cli_generic_update_command(__name__, 'network lb frontend-ip update',
                           lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers,
                           child_collection_prop_name='frontend_ip_configurations',
                           custom_function_op=custom_path + 'set_lb_frontend_ip_configuration')
cli_generic_update_command(__name__, 'network lb inbound-nat-rule update',
                           lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers,
                           child_collection_prop_name='inbound_nat_rules',
                           custom_function_op=custom_path + 'set_lb_inbound_nat_rule')
cli_generic_update_command(__name__, 'network lb inbound-nat-pool update',
                           lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers,
                           child_collection_prop_name='inbound_nat_pools',
                           custom_function_op=custom_path + 'set_lb_inbound_nat_pool')
cli_generic_update_command(__name__, 'network lb rule update',
                           lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers,
                           child_collection_prop_name='load_balancing_rules',
                           custom_function_op=custom_path + 'set_lb_rule')
cli_generic_update_command(__name__, 'network lb probe update',
                           lb_path + 'get', lb_path + 'create_or_update', cf_load_balancers,
                           child_collection_prop_name='probes',
                           custom_function_op=custom_path + 'set_lb_probe')

# LocalNetworkGatewaysOperations
lgw_path = 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.'
cli_command(__name__, 'network local-gateway delete', lgw_path + 'delete', cf_local_network_gateways, no_wait_param='raw')
cli_command(__name__, 'network local-gateway show', lgw_path + 'get', cf_local_network_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network local-gateway list', lgw_path + 'list', cf_local_network_gateways, table_transformer=transform_local_gateway_table_output)
cli_command(__name__, 'network local-gateway create', custom_path + 'create_local_gateway', no_wait_param='no_wait')
cli_generic_update_command(__name__, 'network local-gateway update',
                           lgw_path + 'get', lgw_path + 'create_or_update', cf_local_network_gateways,
                           custom_function_op=custom_path + 'update_local_gateway', no_wait_param='raw')
cli_generic_wait_command(__name__, 'network local-gateway wait', lgw_path + 'get', cf_local_network_gateways)

# NetworkInterfacesOperations
nic_path = 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.'
cli_command(__name__, 'network nic create', custom_path + 'create_nic', transform=transform_nic_create_output)
cli_command(__name__, 'network nic delete', nic_path + 'delete', cf_network_interfaces)
cli_command(__name__, 'network nic show', nic_path + 'get', cf_network_interfaces, exception_handler=empty_on_404)
cli_command(__name__, 'network nic list', custom_path + 'list_nics')
cli_generic_update_command(__name__, 'network nic update',
                           nic_path + 'get', nic_path + 'create_or_update', cf_network_interfaces,
                           custom_function_op=custom_path + 'update_nic')
if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network nic show-effective-route-table', nic_path + 'get_effective_route_table', cf_network_interfaces)
    cli_command(__name__, 'network nic list-effective-nsg', nic_path + 'list_effective_network_security_groups', cf_network_interfaces)

resource = 'network_interfaces'
subresource = 'ip_configurations'
cli_command(__name__, 'network nic ip-config create', custom_path + 'create_nic_ip_config')
cli_generic_update_command(__name__, 'network nic ip-config update',
                           nic_path + 'get', nic_path + 'create_or_update', cf_network_interfaces,
                           child_collection_prop_name='ip_configurations',
                           child_arg_name='ip_config_name',
                           custom_function_op=custom_path + 'set_nic_ip_config')
cli_command(__name__, 'network nic ip-config list', 'azure.cli.command_modules.network._util#{}'.format(list_network_resource_property(resource, subresource)))
cli_command(__name__, 'network nic ip-config show', 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry(resource, subresource)), exception_handler=empty_on_404)
cli_command(__name__, 'network nic ip-config delete', 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry(resource, subresource)))
cli_command(__name__, 'network nic ip-config address-pool add', custom_path + 'add_nic_ip_config_address_pool')
cli_command(__name__, 'network nic ip-config address-pool remove', custom_path + 'remove_nic_ip_config_address_pool')
cli_command(__name__, 'network nic ip-config inbound-nat-rule add', custom_path + 'add_nic_ip_config_inbound_nat_rule')
cli_command(__name__, 'network nic ip-config inbound-nat-rule remove', custom_path + 'remove_nic_ip_config_inbound_nat_rule')

# NetworkSecurityGroupsOperations
nsg_path = 'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.'
cli_command(__name__, 'network nsg delete', nsg_path + 'delete', cf_network_security_groups)
cli_command(__name__, 'network nsg show', nsg_path + 'get', cf_network_security_groups, exception_handler=empty_on_404)
cli_command(__name__, 'network nsg list', custom_path + 'list_nsgs')
cli_command(__name__, 'network nsg create', custom_path + 'create_nsg', transform=transform_nsg_create_output)
cli_generic_update_command(__name__, 'network nsg update', nsg_path + 'get', nsg_path + 'create_or_update', cf_network_security_groups)


# NetworkWatcherOperations
nw_path = 'azure.mgmt.network.operations.network_watchers_operations#NetworkWatchersOperations.'
nw_pc_path = 'azure.mgmt.network.operations.packet_captures_operations#PacketCapturesOperations.'
cli_command(__name__, 'network watcher configure', custom_path + 'configure_network_watcher', cf_network_watcher)
cli_command(__name__, 'network watcher list', nw_path + 'list_all', cf_network_watcher)

cli_command(__name__, 'network watcher test-ip-flow', custom_path + 'check_nw_ip_flow', cf_network_watcher)
cli_command(__name__, 'network watcher test-connectivity', custom_path + 'check_nw_connectivity', cf_network_watcher)
cli_command(__name__, 'network watcher show-next-hop', custom_path + 'show_nw_next_hop', cf_network_watcher)
cli_command(__name__, 'network watcher show-security-group-view', custom_path + 'show_nw_security_view', cf_network_watcher)
cli_command(__name__, 'network watcher show-topology', nw_path + 'get_topology', cf_network_watcher)

cli_command(__name__, 'network watcher packet-capture create', custom_path + 'create_nw_packet_capture', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show', nw_pc_path + 'get', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show-status', nw_pc_path + 'get_status', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture delete', nw_pc_path + 'delete', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture stop', nw_pc_path + 'stop', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture list', nw_pc_path + 'list', cf_packet_capture)

cli_command(__name__, 'network watcher flow-log configure', custom_path + 'set_nsg_flow_logging', cf_network_watcher)
cli_command(__name__, 'network watcher flow-log show', custom_path + 'show_nsg_flow_logging', cf_network_watcher)

cli_command(__name__, 'network watcher troubleshooting start', custom_path + 'start_nw_troubleshooting', cf_network_watcher, no_wait_param='no_wait')
cli_command(__name__, 'network watcher troubleshooting show', custom_path + 'show_nw_troubleshooting_result', cf_network_watcher)

# NetworkWatcherOperations
nw_path = 'azure.mgmt.network.operations.network_watchers_operations#NetworkWatchersOperations.'
nw_pc_path = 'azure.mgmt.network.operations.packet_captures_operations#PacketCapturesOperations.'
cli_command(__name__, 'network watcher configure', custom_path + 'configure_network_watcher', cf_network_watcher)
cli_command(__name__, 'network watcher list', nw_path + 'list_all', cf_network_watcher)

cli_command(__name__, 'network watcher test-ip-flow', custom_path + 'check_nw_ip_flow', cf_network_watcher)
cli_command(__name__, 'network watcher show-next-hop', custom_path + 'show_nw_next_hop', cf_network_watcher)
cli_command(__name__, 'network watcher show-security-group-view', custom_path + 'show_nw_security_view', cf_network_watcher)
cli_command(__name__, 'network watcher show-topology', nw_path + 'get_topology', cf_network_watcher)

cli_command(__name__, 'network watcher packet-capture create', custom_path + 'create_nw_packet_capture', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show', nw_pc_path + 'get', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show-status', nw_pc_path + 'get_status', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture delete', nw_pc_path + 'delete', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture stop', nw_pc_path + 'stop', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture list', nw_pc_path + 'list', cf_packet_capture)

cli_command(__name__, 'network watcher flow-log configure', custom_path + 'set_nsg_flow_logging', cf_network_watcher)
cli_command(__name__, 'network watcher flow-log show', custom_path + 'show_nsg_flow_logging', cf_network_watcher)

cli_command(__name__, 'network watcher troubleshooting start', custom_path + 'start_nw_troubleshooting', cf_network_watcher, no_wait_param='no_wait')
cli_command(__name__, 'network watcher troubleshooting show', custom_path + 'show_nw_troubleshooting_result', cf_network_watcher)

# PublicIPAddressesOperations
public_ip_path = 'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.'
cli_command(__name__, 'network public-ip delete', public_ip_path + 'delete', cf_public_ip_addresses)
cli_command(__name__, 'network public-ip show', public_ip_path + 'get', cf_public_ip_addresses, exception_handler=empty_on_404)
cli_command(__name__, 'network public-ip list', custom_path + 'list_public_ips')
cli_command(__name__, 'network public-ip create', custom_path + 'create_public_ip', transform=transform_public_ip_create_output)
cli_generic_update_command(__name__, 'network public-ip update', public_ip_path + 'get', public_ip_path + 'create_or_update', cf_public_ip_addresses, custom_function_op=custom_path + 'update_public_ip')

# RouteTablesOperations
rt_path = 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.'
cli_command(__name__, 'network route-table create', rt_path + 'create_or_update', cf_route_tables)
cli_command(__name__, 'network route-table delete', rt_path + 'delete', cf_route_tables)
cli_command(__name__, 'network route-table show', rt_path + 'get', cf_route_tables, exception_handler=empty_on_404)
cli_command(__name__, 'network route-table list', custom_path + 'list_route_tables')
cli_generic_update_command(__name__, 'network route-table update', rt_path + 'get', rt_path + 'create_or_update', cf_route_tables, custom_function_op=custom_path + 'update_route_table')

# RoutesOperations
rtr_path = 'azure.mgmt.network.operations.routes_operations#RoutesOperations.'
cli_command(__name__, 'network route-table route delete', rtr_path + 'delete', cf_routes)
cli_command(__name__, 'network route-table route show', rtr_path + 'get', cf_routes, exception_handler=empty_on_404)
cli_command(__name__, 'network route-table route list', rtr_path + 'list', cf_routes)
cli_generic_update_command(__name__, 'network route-table route update',
                           rtr_path + 'get', rtr_path + 'create_or_update', cf_routes,
                           custom_function_op=custom_path + 'update_route', setter_arg_name='route_parameters')
cli_command(__name__, 'network route-table route create', custom_path + 'create_route')

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-12-01'):
    # RouteFiltersOperations
    rf_path = 'azure.mgmt.network.operations#RouteFiltersOperations.'
    cli_command(__name__, 'network route-filter list', custom_path + 'list_route_filters', cf_route_filters)
    cli_command(__name__, 'network route-filter show', rf_path + 'get', cf_route_filters)
    cli_command(__name__, 'network route-filter create', custom_path + 'create_route_filter', cf_route_filters)
    cli_command(__name__, 'network route-filter delete', rf_path + 'delete', cf_route_filters)
    cli_generic_update_command(__name__, 'network route-filter update', rf_path + 'get', rf_path + 'create_or_update', cf_route_filters)

    # RouteFilterRulesOperations
    rfr_path = 'azure.mgmt.network.operations#RouteFilterRulesOperations.'
    cli_command(__name__, 'network route-filter rule list', rfr_path + 'list_by_route_filter', cf_route_filter_rules)
    cli_command(__name__, 'network route-filter rule show', rfr_path + 'get', cf_route_filter_rules)
    cli_command(__name__, 'network route-filter rule create', custom_path + 'create_route_filter_rule', cf_route_filter_rules)
    cli_command(__name__, 'network route-filter rule delete', rfr_path + 'delete', cf_route_filter_rules)
    cli_generic_update_command(__name__, 'network route-filter rule update', rfr_path + 'get', rfr_path + 'create_or_update', cf_route_filter_rules)

    # ServiceCommunitiesOperations
    sc_path = 'azure.mgmt.network.operations#BgpServiceCommunitiesOperations.'
    cli_command(__name__, 'network route-filter rule list-service-communities', sc_path + 'list', cf_service_community, table_transformer=transform_service_community_table_output)

# SecurityRulesOperations
sr_path = 'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.'
cli_command(__name__, 'network nsg rule delete', sr_path + 'delete', cf_security_rules)
cli_command(__name__, 'network nsg rule show', sr_path + 'get', cf_security_rules, exception_handler=empty_on_404)
cli_command(__name__, 'network nsg rule list', sr_path + 'list', cf_security_rules)
cli_command(__name__, 'network nsg rule create', custom_path + 'create_nsg_rule')
cli_generic_update_command(__name__, 'network nsg rule update',
                           sr_path + 'get', sr_path + 'create_or_update', cf_security_rules,
                           setter_arg_name='security_rule_parameters', custom_function_op=custom_path + 'update_nsg_rule')

# SubnetsOperations
subnet_path = 'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.'
cli_command(__name__, 'network vnet subnet delete', subnet_path + 'delete', cf_subnets)
cli_command(__name__, 'network vnet subnet show', subnet_path + 'get', cf_subnets, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet subnet list', subnet_path + 'list', cf_subnets)
cli_command(__name__, 'network vnet subnet create', custom_path + 'create_subnet')
cli_generic_update_command(__name__, 'network vnet subnet update',
                           subnet_path + 'get', subnet_path + 'create_or_update', cf_subnets,
                           setter_arg_name='subnet_parameters', custom_function_op=custom_path + 'update_subnet')

# Usages operations
usage_path = 'azure.mgmt.network.operations.usages_operations#UsagesOperations.'
cli_command(__name__, 'network list-usages', usage_path + 'list', cf_usages, transform=transform_network_usage_list, table_transformer=transform_network_usage_table)

# VirtualNetworkGatewayConnectionsOperations
vpn_conn_path = 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.'
cli_command(__name__, 'network vpn-connection create', custom_path + 'create_vpn_connection', cf_virtual_network_gateway_connections, transform=transform_vpn_connection_create_output)
cli_command(__name__, 'network vpn-connection delete', vpn_conn_path + 'delete', cf_virtual_network_gateway_connections)
cli_command(__name__, 'network vpn-connection show', vpn_conn_path + 'get', cf_virtual_network_gateway_connections, exception_handler=empty_on_404, transform=transform_vpn_connection)
cli_command(__name__, 'network vpn-connection list', vpn_conn_path + 'list', cf_virtual_network_gateway_connections, transform=transform_vpn_connection_list)
cli_generic_update_command(__name__, 'network vpn-connection update',
                           vpn_conn_path + 'get', vpn_conn_path + 'create_or_update', cf_virtual_network_gateway_connections,
                           custom_function_op=custom_path + 'update_vpn_connection')

cli_command(__name__, 'network vpn-connection shared-key show', vpn_conn_path + 'get_shared_key', cf_virtual_network_gateway_connections, exception_handler=empty_on_404)
cli_command(__name__, 'network vpn-connection shared-key reset', vpn_conn_path + 'reset_shared_key', cf_virtual_network_gateway_connections)
cli_generic_update_command(__name__, 'network vpn-connection shared-key update', vpn_conn_path + 'get', vpn_conn_path + 'set_shared_key', cf_virtual_network_gateway_connections)

cli_command(__name__, 'network vpn-connection ipsec-policy add', custom_path + 'add_vpn_conn_ipsec_policy', no_wait_param='no_wait')
cli_command(__name__, 'network vpn-connection ipsec-policy list', custom_path + 'list_vpn_conn_ipsec_policies')
cli_command(__name__, 'network vpn-connection ipsec-policy clear', custom_path + 'clear_vpn_conn_ipsec_policies', no_wait_param='no_wait')

# VirtualNetworkGatewaysOperations
vgw_path = 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.'
cli_command(__name__, 'network vnet-gateway delete', vgw_path + 'delete', cf_virtual_network_gateways, no_wait_param='raw')
cli_command(__name__, 'network vnet-gateway show', vgw_path + 'get', cf_virtual_network_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet-gateway list', vgw_path + 'list', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway reset', vgw_path + 'reset', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway create', custom_path + 'create_vnet_gateway', no_wait_param='no_wait', transform=transform_vnet_gateway_create_output)
cli_generic_update_command(__name__, 'network vnet-gateway update',
                           vgw_path + 'get', vgw_path + 'create_or_update', cf_virtual_network_gateways,
                           custom_function_op=custom_path + 'update_vnet_gateway', no_wait_param='raw')
cli_generic_wait_command(__name__, 'network vnet-gateway wait', vgw_path + 'get', cf_virtual_network_gateways)

cli_command(__name__, 'network vnet-gateway root-cert create', custom_path + 'create_vnet_gateway_root_cert')
cli_command(__name__, 'network vnet-gateway root-cert delete', custom_path + 'delete_vnet_gateway_root_cert')
cli_command(__name__, 'network vnet-gateway revoked-cert create', custom_path + 'create_vnet_gateway_revoked_cert')
cli_command(__name__, 'network vnet-gateway revoked-cert delete', custom_path + 'delete_vnet_gateway_revoked_cert')

# VirtualNetworksOperations
vnet_path = 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.'
cli_command(__name__, 'network vnet delete', vnet_path + 'delete', cf_virtual_networks)
cli_command(__name__, 'network vnet show', vnet_path + 'get', cf_virtual_networks, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet list', custom_path + 'list_vnet')
if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network vnet check-ip-address', vnet_path + 'check_ip_address_availability', cf_virtual_networks)
cli_command(__name__, 'network vnet create', custom_path + 'create_vnet', transform=transform_vnet_create_output)
cli_generic_update_command(__name__, 'network vnet update', vnet_path + 'get', vnet_path + 'create_or_update', cf_virtual_networks, custom_function_op=custom_path + 'update_vnet')

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    # VNET Peering Operations
    vnet_peering_path = 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.'
    cli_command(__name__, 'network vnet peering create', custom_path + 'create_vnet_peering')
    cli_command(__name__, 'network vnet peering show', vnet_peering_path + 'get', cf_virtual_network_peerings, exception_handler=empty_on_404)
    cli_command(__name__, 'network vnet peering list', vnet_peering_path + 'list', cf_virtual_network_peerings)
    cli_command(__name__, 'network vnet peering delete', vnet_peering_path + 'delete', cf_virtual_network_peerings)
    cli_generic_update_command(__name__, 'network vnet peering update', vnet_peering_path + 'get', vnet_peering_path + 'create_or_update', cf_virtual_network_peerings, setter_arg_name='virtual_network_peering_parameters')

# Traffic Manager ProfileOperations
tm_profile_path = 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.'
cli_command(__name__, 'network traffic-manager profile check-dns', tm_profile_path + 'check_traffic_manager_relative_dns_name_availability', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile show', tm_profile_path + 'get', cf_traffic_manager_mgmt_profiles, exception_handler=empty_on_404)
cli_command(__name__, 'network traffic-manager profile delete', tm_profile_path + 'delete', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile list', custom_path + 'list_traffic_manager_profiles')
cli_command(__name__, 'network traffic-manager profile create', custom_path + 'create_traffic_manager_profile', transform=transform_traffic_manager_create_output)
cli_generic_update_command(__name__, 'network traffic-manager profile update',
                           tm_profile_path + 'get', tm_profile_path + 'create_or_update', cf_traffic_manager_mgmt_profiles,
                           custom_function_op=custom_path + 'update_traffic_manager_profile')


# Traffic Manager EndpointOperations
tm_endpoint_path = 'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.'
cli_command(__name__, 'network traffic-manager endpoint show', tm_endpoint_path + 'get', cf_traffic_manager_mgmt_endpoints, exception_handler=empty_on_404)
cli_command(__name__, 'network traffic-manager endpoint delete', tm_endpoint_path + 'delete', cf_traffic_manager_mgmt_endpoints)
cli_command(__name__, 'network traffic-manager endpoint create', custom_path + 'create_traffic_manager_endpoint')
cli_command(__name__, 'network traffic-manager endpoint list', custom_path + 'list_traffic_manager_endpoints')
cli_generic_update_command(__name__, 'network traffic-manager endpoint update',
                           tm_endpoint_path + 'get', tm_endpoint_path + 'create_or_update', cf_traffic_manager_mgmt_endpoints,
                           custom_function_op=custom_path + 'update_traffic_manager_endpoint')

tm_geographic_path = 'azure.mgmt.trafficmanager.operations.geographic_hierarchies_operations#GeographicHierarchiesOperations.'
cli_command(__name__, 'network traffic-manager endpoint show-geographic-hierarchy', tm_geographic_path + 'get_default', cf_tm_geographic, table_transformer=transform_geographic_hierachy_table_output)

# DNS ZonesOperations
dns_zone_path = 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.'
cli_command(__name__, 'network dns zone show', dns_zone_path + 'get', cf_dns_mgmt_zones, table_transformer=transform_dns_zone_table_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns zone delete', dns_zone_path + 'delete', cf_dns_mgmt_zones, confirmation=True)
cli_command(__name__, 'network dns zone show', dns_zone_path + 'get', cf_dns_mgmt_zones, table_transformer=transform_dns_zone_table_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns zone delete', dns_zone_path + 'delete', cf_dns_mgmt_zones, confirmation=True)
cli_command(__name__, 'network dns zone list', custom_path + 'list_dns_zones', table_transformer=transform_dns_zone_table_output)
cli_generic_update_command(__name__, 'network dns zone update', dns_zone_path + 'get', dns_zone_path + 'create_or_update', cf_dns_mgmt_zones)
cli_command(__name__, 'network dns zone import', custom_path + 'import_zone')
cli_command(__name__, 'network dns zone export', custom_path + 'export_zone')
cli_command(__name__, 'network dns zone create', custom_path + 'create_dns_zone', cf_dns_mgmt_zones)

# DNS RecordSetsOperations
dns_record_set_path = 'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.'
cli_command(__name__, 'network dns record-set list', custom_path + 'list_dns_record_set', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output)
for record in ['a', 'aaaa', 'mx', 'ns', 'ptr', 'srv', 'txt']:
    cli_command(__name__, 'network dns record-set {} show'.format(record), dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
    cli_command(__name__, 'network dns record-set {} delete'.format(record), dns_record_set_path + 'delete', cf_dns_mgmt_record_sets, confirmation=True)
    cli_command(__name__, 'network dns record-set {} list'.format(record), custom_path + 'list_dns_record_set', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
    cli_command(__name__, 'network dns record-set {} create'.format(record), custom_path + 'create_dns_record_set', transform=transform_dns_record_set_output)
    cli_command(__name__, 'network dns record-set {} add-record'.format(record), custom_path + 'add_dns_{}_record'.format(record), transform=transform_dns_record_set_output)
    cli_command(__name__, 'network dns record-set {} remove-record'.format(record), custom_path + 'remove_dns_{}_record'.format(record), transform=transform_dns_record_set_output)
    cli_generic_update_command(__name__, 'network dns record-set {} update'.format(record),
                               dns_record_set_path + 'get',
                               dns_record_set_path + 'create_or_update',
                               cf_dns_mgmt_record_sets,
                               custom_function_op=custom_path + 'update_dns_record_set',
                               transform=transform_dns_record_set_output)

cli_command(__name__, 'network dns record-set soa show', dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns record-set soa update', custom_path + 'update_dns_soa_record', transform=transform_dns_record_set_output)

cli_command(__name__, 'network dns record-set cname show', dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns record-set cname delete', dns_record_set_path + 'delete', cf_dns_mgmt_record_sets)
cli_command(__name__, 'network dns record-set cname list', custom_path + 'list_dns_record_set', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
cli_command(__name__, 'network dns record-set cname create', custom_path + 'create_dns_record_set', transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set cname set-record', custom_path + 'add_dns_cname_record', transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set cname remove-record', custom_path + 'remove_dns_cname_record', transform=transform_dns_record_set_output)
