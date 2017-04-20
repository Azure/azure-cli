# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.arm import cli_generic_update_command, cli_generic_wait_command
from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command
from ._client_factory import * # pylint: disable=wildcard-import, unused-wildcard-import
from azure.cli.core.util import empty_on_404

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
     transform_vpn_connection_create_output)

from azure.cli.core.profiles import supported_api_version, ResourceType

custom_path = 'azure.cli.command_modules.network.custom#{}'

# Application gateways
cli_command(__name__, 'network application-gateway create', custom_path.format('create_application_gateway'), transform=DeploymentOutputLongRunningOperation('Starting network application-gateway create'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway delete', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.delete', cf_application_gateways, no_wait_param='raw')
cli_command(__name__, 'network application-gateway show', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get', cf_application_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network application-gateway list', custom_path.format('list_application_gateways'))
cli_command(__name__, 'network application-gateway start', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.start', cf_application_gateways)
cli_command(__name__, 'network application-gateway stop', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.stop', cf_application_gateways)

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network application-gateway show-backend-health', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.backend_health', cf_application_gateways)

cli_generic_update_command(__name__, 'network application-gateway update',
                           'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get',
                           'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.create_or_update',
                           cf_application_gateways, no_wait_param='raw',
                           custom_function_op=custom_path.format('update_application_gateway'))
cli_generic_wait_command(__name__, 'network application-gateway wait',
                         'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get', cf_application_gateways)


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
        return value[:-1] if value.endswith('s') else value
    except AttributeError:
        return value

for subresource, alias in property_map.items():
    cli_command(__name__, 'network application-gateway {} list'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(list_network_resource_property('application_gateways', subresource)))
    cli_command(__name__, 'network application-gateway {} show'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry('application_gateways', subresource)), exception_handler=empty_on_404)
    cli_command(__name__, 'network application-gateway {} delete'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry('application_gateways', subresource)), no_wait_param='no_wait')
    cli_command(__name__, 'network application-gateway {} create'.format(alias), custom_path.format('create_ag_{}'.format(_make_singular(subresource))), no_wait_param='no_wait')
    cli_generic_update_command(__name__, 'network application-gateway {} update'.format(alias),
                               'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get',
                               'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.create_or_update',
                               cf_application_gateways, no_wait_param='raw',
                               custom_function_op=custom_path.format('update_ag_{}'.format(_make_singular(subresource))),
                               child_collection_prop_name=subresource)

cli_command(__name__, 'network application-gateway ssl-policy set', custom_path.format('set_ag_ssl_policy'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway ssl-policy show', custom_path.format('show_ag_ssl_policy'), exception_handler=empty_on_404)

cli_command(__name__, 'network application-gateway url-path-map rule create', custom_path.format('create_ag_url_path_map_rule'))
cli_command(__name__, 'network application-gateway url-path-map rule delete', custom_path.format('delete_ag_url_path_map_rule'))

cli_command(__name__, 'network application-gateway waf-config set', custom_path.format('set_ag_waf_config'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway waf-config show', custom_path.format('show_ag_waf_config'), exception_handler=empty_on_404)

# ExpressRouteCircuitAuthorizationsOperations
cli_command(__name__, 'network express-route auth delete', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.delete', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth show', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.get', cf_express_route_circuit_authorizations, exception_handler=empty_on_404)
cli_command(__name__, 'network express-route auth list', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.list', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth create', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.create_or_update', cf_express_route_circuit_authorizations)

# ExpressRouteCircuitPeeringsOperations
cli_command(__name__, 'network express-route peering delete', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.delete', cf_express_route_circuit_peerings)
cli_command(__name__, 'network express-route peering show', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.get', cf_express_route_circuit_peerings, exception_handler=empty_on_404)
cli_command(__name__, 'network express-route peering list', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.list', cf_express_route_circuit_peerings)
cli_generic_update_command(__name__, 'network express-route peering update',
                           'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.get',
                           'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.create_or_update',
                           cf_express_route_circuit_peerings, setter_arg_name='peering_parameters',
                           custom_function_op=custom_path.format('update_express_route_peering'))
cli_command(__name__, 'network express-route peering create', custom_path.format('create_express_route_peering'), cf_express_route_circuit_peerings)

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    # ExpressRouteCircuitsOperations
    cli_command(__name__, 'network express-route delete', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.delete', cf_express_route_circuits, no_wait_param='raw')
    cli_command(__name__, 'network express-route show', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get', cf_express_route_circuits, exception_handler=empty_on_404)
    cli_command(__name__, 'network express-route get-stats', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get_stats', cf_express_route_circuits)
    cli_command(__name__, 'network express-route list-arp-tables', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.list_arp_table', cf_express_route_circuits)
    cli_command(__name__, 'network express-route list-route-tables', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.list_routes_table', cf_express_route_circuits)
    cli_command(__name__, 'network express-route create', custom_path.format('create_express_route'), no_wait_param='no_wait')
    cli_command(__name__, 'network express-route list', custom_path.format('list_express_route_circuits'))
    cli_generic_update_command(__name__, 'network express-route update',
                               'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get',
                               'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.create_or_update',
                               cf_express_route_circuits,
                               custom_function_op=custom_path.format('update_express_route'),
                               no_wait_param='raw')
    cli_generic_wait_command(__name__, 'network express-route wait', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get', cf_express_route_circuits)

    # ExpressRouteServiceProvidersOperations
    cli_command(__name__, 'network express-route list-service-providers', 'azure.mgmt.network.operations.express_route_service_providers_operations#ExpressRouteServiceProvidersOperations.list', cf_express_route_service_providers)

# LoadBalancersOperations
cli_command(__name__, 'network lb create', custom_path.format('create_load_balancer'), transform=DeploymentOutputLongRunningOperation('Starting network lb create'), no_wait_param='no_wait')
cli_command(__name__, 'network lb delete', 'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.delete', cf_load_balancers)
cli_command(__name__, 'network lb show', 'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get', cf_load_balancers, exception_handler=empty_on_404)
cli_command(__name__, 'network lb list', custom_path.format('list_lbs'))
cli_generic_update_command(__name__, 'network lb update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update', cf_load_balancers)


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

cli_command(__name__, 'network lb frontend-ip create', custom_path.format('create_lb_frontend_ip_configuration'))
cli_command(__name__, 'network lb inbound-nat-rule create', custom_path.format('create_lb_inbound_nat_rule'))
cli_command(__name__, 'network lb inbound-nat-pool create', custom_path.format('create_lb_inbound_nat_pool'))
cli_command(__name__, 'network lb address-pool create', custom_path.format('create_lb_backend_address_pool'))
cli_command(__name__, 'network lb rule create', custom_path.format('create_lb_rule'))
cli_command(__name__, 'network lb probe create', custom_path.format('create_lb_probe'))

cli_generic_update_command(__name__, 'network lb frontend-ip update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update',
                           cf_load_balancers,
                           child_collection_prop_name='frontend_ip_configurations',
                           custom_function_op=custom_path.format('set_lb_frontend_ip_configuration'))
cli_generic_update_command(__name__, 'network lb inbound-nat-rule update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update',
                           cf_load_balancers,
                           child_collection_prop_name='inbound_nat_rules',
                           custom_function_op=custom_path.format('set_lb_inbound_nat_rule'))
cli_generic_update_command(__name__, 'network lb inbound-nat-pool update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update',
                           cf_load_balancers,
                           child_collection_prop_name='inbound_nat_pools',
                           custom_function_op=custom_path.format('set_lb_inbound_nat_pool'))
cli_generic_update_command(__name__, 'network lb rule update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update',
                           cf_load_balancers,
                           child_collection_prop_name='load_balancing_rules',
                           custom_function_op=custom_path.format('set_lb_rule'))
cli_generic_update_command(__name__, 'network lb probe update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update',
                           cf_load_balancers,
                           child_collection_prop_name='probes',
                           custom_function_op=custom_path.format('set_lb_probe'))

# LocalNetworkGatewaysOperations
cli_command(__name__, 'network local-gateway delete', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.delete', cf_local_network_gateways, no_wait_param='raw')
cli_command(__name__, 'network local-gateway show', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.get', cf_local_network_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network local-gateway list', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.list', cf_local_network_gateways, table_transformer=transform_local_gateway_table_output)
cli_command(__name__, 'network local-gateway create', custom_path.format('create_local_gateway'), no_wait_param='no_wait')
cli_generic_update_command(__name__, 'network local-gateway update',
                           'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.get',
                           'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.create_or_update',
                           cf_local_network_gateways,
                           custom_function_op=custom_path.format('update_local_gateway'), no_wait_param='raw')
cli_generic_wait_command(__name__, 'network local-gateway wait', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.get', cf_local_network_gateways)

# NetworkInterfacesOperations
cli_command(__name__, 'network nic create', custom_path.format('create_nic'), transform=transform_nic_create_output)
cli_command(__name__, 'network nic delete', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.delete', cf_network_interfaces)
cli_command(__name__, 'network nic show', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get', cf_network_interfaces, exception_handler=empty_on_404)
cli_command(__name__, 'network nic list', custom_path.format('list_nics'))
cli_generic_update_command(__name__, 'network nic update',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.create_or_update',
                           cf_network_interfaces,
                           custom_function_op=custom_path.format('update_nic'))
if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network nic show-effective-route-table', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get_effective_route_table', cf_network_interfaces)
    cli_command(__name__, 'network nic list-effective-nsg', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.list_effective_network_security_groups', cf_network_interfaces)

resource = 'network_interfaces'
subresource = 'ip_configurations'
cli_command(__name__, 'network nic ip-config create', custom_path.format('create_nic_ip_config'))
cli_generic_update_command(__name__, 'network nic ip-config update',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.create_or_update',
                           cf_network_interfaces,
                           child_collection_prop_name='ip_configurations',
                           child_arg_name='ip_config_name',
                           custom_function_op=custom_path.format('set_nic_ip_config'))
cli_command(__name__, 'network nic ip-config list', 'azure.cli.command_modules.network._util#{}'.format(list_network_resource_property(resource, subresource)))
cli_command(__name__, 'network nic ip-config show', 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry(resource, subresource)), exception_handler=empty_on_404)
cli_command(__name__, 'network nic ip-config delete', 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry(resource, subresource)))
cli_command(__name__, 'network nic ip-config address-pool add', custom_path.format('add_nic_ip_config_address_pool'))
cli_command(__name__, 'network nic ip-config address-pool remove', custom_path.format('remove_nic_ip_config_address_pool'))
cli_command(__name__, 'network nic ip-config inbound-nat-rule add', custom_path.format('add_nic_ip_config_inbound_nat_rule'))
cli_command(__name__, 'network nic ip-config inbound-nat-rule remove', custom_path.format('remove_nic_ip_config_inbound_nat_rule'))

# NetworkSecurityGroupsOperations
cli_command(__name__, 'network nsg delete', 'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.delete', cf_network_security_groups)
cli_command(__name__, 'network nsg show', 'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.get', cf_network_security_groups, exception_handler=empty_on_404)
cli_command(__name__, 'network nsg list', custom_path.format('list_nsgs'))
cli_command(__name__, 'network nsg create', custom_path.format('create_nsg'), transform=transform_nsg_create_output)
cli_generic_update_command(__name__, 'network nsg update',
                           'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.get',
                           'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.create_or_update',
                           cf_network_security_groups)


# NetworkWatcherOperations
nw_path = 'azure.mgmt.network.operations.network_watchers_operations#NetworkWatchersOperations.'
nw_pc_path = 'azure.mgmt.network.operations.packet_captures_operations#PacketCapturesOperations.'
cli_command(__name__, 'network watcher configure', custom_path.format('configure_network_watcher'), cf_network_watcher)
cli_command(__name__, 'network watcher list', nw_path + 'list_all', cf_network_watcher)

cli_command(__name__, 'network watcher test-ip-flow', custom_path.format('check_nw_ip_flow'), cf_network_watcher)
cli_command(__name__, 'network watcher show-next-hop', custom_path.format('show_nw_next_hop'), cf_network_watcher)
cli_command(__name__, 'network watcher show-security-group-view', custom_path.format('show_nw_security_view'), cf_network_watcher)
cli_command(__name__, 'network watcher show-topology', nw_path + 'get_topology', cf_network_watcher)

cli_command(__name__, 'network watcher packet-capture create', custom_path.format('create_nw_packet_capture'), cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show', nw_pc_path + 'get', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture show-status', nw_pc_path + 'get_status', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture delete', nw_pc_path + 'delete', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture stop', nw_pc_path + 'stop', cf_packet_capture)
cli_command(__name__, 'network watcher packet-capture list', nw_pc_path + 'list', cf_packet_capture)

cli_command(__name__, 'network watcher flow-log configure', custom_path.format('set_nsg_flow_logging'), cf_network_watcher)
cli_command(__name__, 'network watcher flow-log show', custom_path.format('show_nsg_flow_logging'), cf_network_watcher)

cli_command(__name__, 'network watcher troubleshooting start', custom_path.format('start_nw_troubleshooting'), cf_network_watcher, no_wait_param='no_wait')
cli_command(__name__, 'network watcher troubleshooting show', custom_path.format('show_nw_troubleshooting_result'), cf_network_watcher)

# PublicIPAddressesOperations
cli_command(__name__, 'network public-ip delete', 'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.delete', cf_public_ip_addresses)
cli_command(__name__, 'network public-ip show', 'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.get', cf_public_ip_addresses, exception_handler=empty_on_404)
cli_command(__name__, 'network public-ip list', custom_path.format('list_public_ips'))
cli_command(__name__, 'network public-ip create', custom_path.format('create_public_ip'), transform=transform_public_ip_create_output)
cli_generic_update_command(__name__, 'network public-ip update',
                           'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.get',
                           'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.create_or_update',
                           cf_public_ip_addresses,
                           custom_function_op=custom_path.format('update_public_ip'))

# RouteTablesOperations
cli_command(__name__, 'network route-table create', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.create_or_update', cf_route_tables)
cli_command(__name__, 'network route-table delete', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.delete', cf_route_tables)
cli_command(__name__, 'network route-table show', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.get', cf_route_tables, exception_handler=empty_on_404)
cli_command(__name__, 'network route-table list', custom_path.format('list_route_tables'))
cli_generic_update_command(__name__, 'network route-table update',
                           'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.get',
                           'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.create_or_update',
                           cf_route_tables,
                           custom_function_op=custom_path.format('update_route_table'))

# RoutesOperations
cli_command(__name__, 'network route-table route delete', 'azure.mgmt.network.operations.routes_operations#RoutesOperations.delete', cf_routes)
cli_command(__name__, 'network route-table route show', 'azure.mgmt.network.operations.routes_operations#RoutesOperations.get', cf_routes, exception_handler=empty_on_404)
cli_command(__name__, 'network route-table route list', 'azure.mgmt.network.operations.routes_operations#RoutesOperations.list', cf_routes)
cli_generic_update_command(__name__, 'network route-table route update',
                           'azure.mgmt.network.operations.routes_operations#RoutesOperations.get',
                           'azure.mgmt.network.operations.routes_operations#RoutesOperations.create_or_update',
                           cf_routes,
                           custom_function_op=custom_path.format('update_route'),
                           setter_arg_name='route_parameters')
cli_command(__name__, 'network route-table route create', custom_path.format('create_route'))

# SecurityRulesOperations
cli_command(__name__, 'network nsg rule delete', 'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.delete', cf_security_rules)
cli_command(__name__, 'network nsg rule show', 'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.get', cf_security_rules, exception_handler=empty_on_404)
cli_command(__name__, 'network nsg rule list', 'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.list', cf_security_rules)
cli_command(__name__, 'network nsg rule create', custom_path.format('create_nsg_rule'))
cli_generic_update_command(__name__, 'network nsg rule update',
                           'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.get',
                           'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.create_or_update',
                           cf_security_rules,
                           setter_arg_name='security_rule_parameters',
                           custom_function_op=custom_path.format('update_nsg_rule'))

# SubnetsOperations
cli_command(__name__, 'network vnet subnet delete', 'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.delete', cf_subnets)
cli_command(__name__, 'network vnet subnet show', 'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.get', cf_subnets, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet subnet list', 'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.list', cf_subnets)
cli_command(__name__, 'network vnet subnet create', custom_path.format('create_subnet'))
cli_generic_update_command(__name__, 'network vnet subnet update',
                           'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.get',
                           'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.create_or_update',
                           cf_subnets,
                           setter_arg_name='subnet_parameters',
                           custom_function_op=custom_path.format('update_subnet'))

# Usages operations
cli_command(__name__, 'network list-usages', 'azure.mgmt.network.operations.usages_operations#UsagesOperations.list', cf_usages)

# VirtualNetworkGatewayConnectionsOperations
cli_command(__name__, 'network vpn-connection create', custom_path.format('create_vpn_connection'), cf_virtual_network_gateway_connections, transform=transform_vpn_connection_create_output)
cli_command(__name__, 'network vpn-connection delete', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.delete', cf_virtual_network_gateway_connections)
cli_command(__name__, 'network vpn-connection show', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get', cf_virtual_network_gateway_connections, exception_handler=empty_on_404, transform=transform_vpn_connection)
cli_command(__name__, 'network vpn-connection list', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.list', cf_virtual_network_gateway_connections, transform=transform_vpn_connection_list)
cli_generic_update_command(__name__, 'network vpn-connection update',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.create_or_update',
                           cf_virtual_network_gateway_connections,
                           custom_function_op=custom_path.format('update_vpn_connection'))
cli_command(__name__, 'network vpn-connection shared-key show', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get_shared_key', cf_virtual_network_gateway_connections, exception_handler=empty_on_404)
cli_command(__name__, 'network vpn-connection shared-key reset', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.reset_shared_key', cf_virtual_network_gateway_connections)
cli_generic_update_command(__name__, 'network vpn-connection shared-key update',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.set_shared_key',
                           cf_virtual_network_gateway_connections)

# VirtualNetworkGatewaysOperations
cli_command(__name__, 'network vnet-gateway delete', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.delete', cf_virtual_network_gateways, no_wait_param='raw')
cli_command(__name__, 'network vnet-gateway show', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get', cf_virtual_network_gateways, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet-gateway list', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.list', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway reset', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.reset', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway create', custom_path.format('create_vnet_gateway'), no_wait_param='no_wait', transform=transform_vnet_gateway_create_output)
cli_generic_update_command(__name__, 'network vnet-gateway update',
                           'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.create_or_update',
                           cf_virtual_network_gateways,
                           custom_function_op=custom_path.format('update_vnet_gateway'),
                           no_wait_param='raw')
cli_generic_wait_command(__name__, 'network vnet-gateway wait', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get', cf_virtual_network_gateways)

cli_command(__name__, 'network vnet-gateway root-cert create', custom_path.format('create_vnet_gateway_root_cert'))
cli_command(__name__, 'network vnet-gateway root-cert delete', custom_path.format('delete_vnet_gateway_root_cert'))
cli_command(__name__, 'network vnet-gateway revoked-cert create', custom_path.format('create_vnet_gateway_revoked_cert'))
cli_command(__name__, 'network vnet-gateway revoked-cert delete', custom_path.format('delete_vnet_gateway_revoked_cert'))

# VirtualNetworksOperations
cli_command(__name__, 'network vnet delete', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.delete', cf_virtual_networks)
cli_command(__name__, 'network vnet show', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.get', cf_virtual_networks, exception_handler=empty_on_404)
cli_command(__name__, 'network vnet list', custom_path.format('list_vnet'))
if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    cli_command(__name__, 'network vnet check-ip-address', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.check_ip_address_availability', cf_virtual_networks)
cli_command(__name__, 'network vnet create', custom_path.format('create_vnet'), transform=transform_vnet_create_output)
cli_generic_update_command(__name__, 'network vnet update',
                           'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.get',
                           'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.create_or_update',
                           cf_virtual_networks,
                           custom_function_op=custom_path.format('update_vnet'))

if supported_api_version(ResourceType.MGMT_NETWORK, min_api='2016-09-01'):
    # VNET Peering Operations
    cli_command(__name__, 'network vnet peering create', custom_path.format('create_vnet_peering'))
    cli_command(__name__, 'network vnet peering show', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.get', cf_virtual_network_peerings, exception_handler=empty_on_404)
    cli_command(__name__, 'network vnet peering list', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.list', cf_virtual_network_peerings)
    cli_command(__name__, 'network vnet peering delete', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.delete', cf_virtual_network_peerings)
    cli_generic_update_command(__name__, 'network vnet peering update',
                               'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.get',
                               'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.create_or_update',
                               cf_virtual_network_peerings,
                               setter_arg_name='virtual_network_peering_parameters')

# Traffic Manager ProfileOperations
cli_command(__name__, 'network traffic-manager profile check-dns', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.check_traffic_manager_relative_dns_name_availability', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile show', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.get', cf_traffic_manager_mgmt_profiles, exception_handler=empty_on_404)
cli_command(__name__, 'network traffic-manager profile delete', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.delete', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile list', custom_path.format('list_traffic_manager_profiles'))
cli_command(__name__, 'network traffic-manager profile create', custom_path.format('create_traffic_manager_profile'), transform=transform_traffic_manager_create_output)
cli_generic_update_command(__name__, 'network traffic-manager profile update',
                           'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.get',
                           'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.create_or_update',
                           cf_traffic_manager_mgmt_profiles,
                           custom_function_op=custom_path.format('update_traffic_manager_profile'))


# Traffic Manager EndpointOperations
cli_command(__name__, 'network traffic-manager endpoint show', 'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.get', cf_traffic_manager_mgmt_endpoints, exception_handler=empty_on_404)
cli_command(__name__, 'network traffic-manager endpoint delete', 'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.delete', cf_traffic_manager_mgmt_endpoints)
cli_command(__name__, 'network traffic-manager endpoint create', custom_path.format('create_traffic_manager_endpoint'))
cli_command(__name__, 'network traffic-manager endpoint list', custom_path.format('list_traffic_manager_endpoints'))
cli_generic_update_command(__name__, 'network traffic-manager endpoint update',
                           'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.get',
                           'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.create_or_update',
                           cf_traffic_manager_mgmt_endpoints,
                           custom_function_op=custom_path.format('update_traffic_manager_endpoint'))

# DNS ZonesOperations
dns_zone_path = 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.'
cli_command(__name__, 'network dns zone show', dns_zone_path + 'get', cf_dns_mgmt_zones, table_transformer=transform_dns_zone_table_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns zone delete', dns_zone_path + 'delete', cf_dns_mgmt_zones, confirmation=True)
cli_command(__name__, 'network dns zone show', 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.get', cf_dns_mgmt_zones, table_transformer=transform_dns_zone_table_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns zone delete', 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.delete', cf_dns_mgmt_zones, confirmation=True)
cli_command(__name__, 'network dns zone list', custom_path.format('list_dns_zones'), table_transformer=transform_dns_zone_table_output)
cli_generic_update_command(__name__, 'network dns zone update',
                           dns_zone_path + 'get',
                           dns_zone_path + 'create_or_update',
                           cf_dns_mgmt_zones)
cli_command(__name__, 'network dns zone import', custom_path.format('import_zone'))
cli_command(__name__, 'network dns zone export', custom_path.format('export_zone'))
cli_command(__name__, 'network dns zone create', custom_path.format('create_dns_zone'), cf_dns_mgmt_zones)

# DNS RecordSetsOperations
dns_record_set_path = 'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.'
cli_command(__name__, 'network dns record-set list', custom_path.format('list_dns_record_set'), cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output)
for record in ['a', 'aaaa', 'mx', 'ns', 'ptr', 'srv', 'txt']:
    cli_command(__name__, 'network dns record-set {} show'.format(record), dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
    cli_command(__name__, 'network dns record-set {} delete'.format(record), dns_record_set_path + 'delete', cf_dns_mgmt_record_sets, confirmation=True)
    cli_command(__name__, 'network dns record-set {} list'.format(record), custom_path.format('list_dns_record_set'), cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
    cli_command(__name__, 'network dns record-set {} create'.format(record), custom_path.format('create_dns_record_set'), transform=transform_dns_record_set_output)
    cli_command(__name__, 'network dns record-set {} add-record'.format(record), custom_path.format('add_dns_{}_record'.format(record)), transform=transform_dns_record_set_output)
    cli_command(__name__, 'network dns record-set {} remove-record'.format(record), custom_path.format('remove_dns_{}_record'.format(record)), transform=transform_dns_record_set_output)
    cli_generic_update_command(__name__, 'network dns record-set {} update'.format(record),
                               dns_record_set_path + 'get',
                               dns_record_set_path + 'create_or_update',
                               cf_dns_mgmt_record_sets,
                               custom_function_op=custom_path.format('update_dns_record_set'),
                               transform=transform_dns_record_set_output)

cli_command(__name__, 'network dns record-set soa show', dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns record-set soa update', custom_path.format('update_dns_soa_record'), transform=transform_dns_record_set_output)

cli_command(__name__, 'network dns record-set cname show', dns_record_set_path + 'get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, exception_handler=empty_on_404)
cli_command(__name__, 'network dns record-set cname delete', dns_record_set_path + 'delete', cf_dns_mgmt_record_sets)
cli_command(__name__, 'network dns record-set cname list', custom_path.format('list_dns_record_set'), cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
cli_command(__name__, 'network dns record-set cname create', custom_path.format('create_dns_record_set'), transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set cname set-record', custom_path.format('add_dns_cname_record'), transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set cname remove-record', custom_path.format('remove_dns_cname_record'), transform=transform_dns_record_set_output)
