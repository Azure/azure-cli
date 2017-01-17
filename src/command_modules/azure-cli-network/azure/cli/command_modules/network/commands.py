# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands.arm import cli_generic_update_command, cli_generic_wait_command
from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command
from ._client_factory import * # pylint: disable=wildcard-import, unused-wildcard-import

from ._util import (list_network_resource_property,
                    get_network_resource_property_entry,
                    delete_network_resource_property_entry)
from ._format import \
    (transform_local_gateway_table_output, transform_dns_record_set_output)

custom_path = 'azure.cli.command_modules.network.custom#{}'

# Application gateways
cli_command(__name__, 'network application-gateway delete', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.delete', cf_application_gateways, no_wait_param='raw')
cli_command(__name__, 'network application-gateway show', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get', cf_application_gateways)
cli_command(__name__, 'network application-gateway list', custom_path.format('list_application_gateways'))
cli_command(__name__, 'network application-gateway start', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.start', cf_application_gateways)
cli_command(__name__, 'network application-gateway stop', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.stop', cf_application_gateways)
cli_command(__name__, 'network application-gateway show-backend-health', 'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.backend_health', cf_application_gateways)
cli_generic_update_command(__name__, 'network application-gateway update',
                           'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get',
                           'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.create_or_update',
                           cf_application_gateways, no_wait_param='raw',
                           custom_function_op=custom_path.format('update_application_gateway'))
cli_generic_wait_command(__name__, 'network application-gateway wait',
                         'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get', cf_application_gateways)

cli_command(__name__, 'network application-gateway create',
            'azure.cli.command_modules.network.mgmt_app_gateway.lib.operations.app_gateway_operations#AppGatewayOperations.create_or_update',
            cf_application_gateway_create,
            transform=DeploymentOutputLongRunningOperation('Starting network application-gateway create'),
            no_wait_param='raw')

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
    cli_command(__name__, 'network application-gateway {} show'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry('application_gateways', subresource)))
    cli_command(__name__, 'network application-gateway {} delete'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry('application_gateways', subresource)), no_wait_param='no_wait')
    cli_command(__name__, 'network application-gateway {} create'.format(alias), custom_path.format('create_ag_{}'.format(_make_singular(subresource))), no_wait_param='no_wait')
    cli_generic_update_command(__name__, 'network application-gateway {} update'.format(alias),
                               'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.get',
                               'azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.create_or_update',
                               cf_application_gateways, no_wait_param='raw',
                               custom_function_op=custom_path.format('update_ag_{}'.format(_make_singular(subresource))),
                               child_collection_prop_name=subresource)

cli_command(__name__, 'network application-gateway ssl-policy set', custom_path.format('set_ag_ssl_policy'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway ssl-policy show', custom_path.format('show_ag_ssl_policy'))

cli_command(__name__, 'network application-gateway url-path-map rule create', custom_path.format('create_ag_url_path_map_rule'))
cli_command(__name__, 'network application-gateway url-path-map rule delete', custom_path.format('delete_ag_url_path_map_rule'))

cli_command(__name__, 'network application-gateway waf-config set', custom_path.format('set_ag_waf_config'), no_wait_param='no_wait')
cli_command(__name__, 'network application-gateway waf-config show', custom_path.format('show_ag_waf_config'))

# ExpressRouteCircuitAuthorizationsOperations
cli_command(__name__, 'network express-route auth delete', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.delete', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth show', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.get', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth list', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.list', cf_express_route_circuit_authorizations)
cli_command(__name__, 'network express-route auth create', 'azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.create_or_update', cf_express_route_circuit_authorizations)

# ExpressRouteCircuitPeeringsOperations
cli_command(__name__, 'network express-route peering delete', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.delete', cf_express_route_circuit_peerings)
cli_command(__name__, 'network express-route peering show', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.get', cf_express_route_circuit_peerings)
cli_command(__name__, 'network express-route peering list', 'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.list', cf_express_route_circuit_peerings)
cli_generic_update_command(__name__, 'network express-route peering update',
                           'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.get',
                           'azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.create_or_update',
                           cf_express_route_circuit_peerings, setter_arg_name='peering_parameters',
                           custom_function_op=custom_path.format('update_express_route_peering'))
cli_command(__name__, 'network express-route peering create', custom_path.format('create_express_route_peering'), cf_express_route_circuit_peerings)

# ExpressRouteCircuitsOperations
cli_command(__name__, 'network express-route delete', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.delete', cf_express_route_circuits)
cli_command(__name__, 'network express-route show', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get', cf_express_route_circuits)
cli_command(__name__, 'network express-route get-stats', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get_stats', cf_express_route_circuits)
cli_command(__name__, 'network express-route list-arp-tables', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.list_arp_table', cf_express_route_circuits)
cli_command(__name__, 'network express-route list-route-tables', 'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.list_routes_table', cf_express_route_circuits)
cli_command(__name__, 'network express-route list', custom_path.format('list_express_route_circuits'))
cli_generic_update_command(__name__, 'network express-route update',
                           'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.get',
                           'azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.create_or_update',
                           cf_express_route_circuits,
                           custom_function_op=custom_path.format('update_express_route'))

cli_command(__name__, 'network express-route create', 'azure.cli.command_modules.network.mgmt_express_route_circuit.lib.operations.express_route_circuit_operations#ExpressRouteCircuitOperations.create_or_update', cf_express_route_circuit_create, transform=DeploymentOutputLongRunningOperation('Starting network express-route create'))

# ExpressRouteServiceProvidersOperations
cli_command(__name__, 'network express-route list-service-providers', 'azure.mgmt.network.operations.express_route_service_providers_operations#ExpressRouteServiceProvidersOperations.list', cf_express_route_service_providers)

# LoadBalancersOperations
cli_command(__name__, 'network lb delete', 'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.delete', cf_load_balancers)
cli_command(__name__, 'network lb show', 'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get', cf_load_balancers)
cli_command(__name__, 'network lb list', custom_path.format('list_lbs'))
cli_generic_update_command(__name__, 'network lb update',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.get',
                           'azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.create_or_update', cf_load_balancers)

cli_command(__name__, 'network lb create',
            'azure.cli.command_modules.network.mgmt_lb.lib.operations.lb_operations#LbOperations.create_or_update',
            cf_load_balancer_create,
            transform=DeploymentOutputLongRunningOperation('Starting network lb create'))

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
    cli_command(__name__, 'network lb {} show'.format(alias), 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry('load_balancers', subresource)))
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
cli_command(__name__, 'network local-gateway delete', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.delete', cf_local_network_gateways)
cli_command(__name__, 'network local-gateway show', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.get', cf_local_network_gateways)
cli_command(__name__, 'network local-gateway list', 'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.list', cf_local_network_gateways, table_transformer=transform_local_gateway_table_output)
cli_generic_update_command(__name__, 'network local-gateway update',
                           'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.get',
                           'azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.create_or_update',
                           cf_local_network_gateways,
                           custom_function_op=custom_path.format('update_local_gateway'))

cli_command(__name__, 'network local-gateway create',
            'azure.cli.command_modules.network.mgmt_local_gateway.lib.operations.local_gateway_operations#LocalGatewayOperations.create_or_update',
            cf_local_gateway_create,
            transform=DeploymentOutputLongRunningOperation('Starting network local-gateway create'))

# NetworkInterfacesOperations
cli_command(__name__, 'network nic create',
            'azure.cli.command_modules.network.mgmt_nic.lib.operations.nic_operations#NicOperations.create_or_update',
            cf_nic_create,
            transform=DeploymentOutputLongRunningOperation('Starting network nic create'))

cli_command(__name__, 'network nic delete', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.delete', cf_network_interfaces)
cli_command(__name__, 'network nic show', 'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get', cf_network_interfaces)
cli_command(__name__, 'network nic list', custom_path.format('list_nics'))
cli_generic_update_command(__name__, 'network nic update',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.get',
                           'azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.create_or_update',
                           cf_network_interfaces,
                           custom_function_op=custom_path.format('set_nic'))
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
cli_command(__name__, 'network nic ip-config show', 'azure.cli.command_modules.network._util#{}'.format(get_network_resource_property_entry(resource, subresource)))
cli_command(__name__, 'network nic ip-config delete', 'azure.cli.command_modules.network._util#{}'.format(delete_network_resource_property_entry(resource, subresource)))
cli_command(__name__, 'network nic ip-config address-pool add', custom_path.format('add_nic_ip_config_address_pool'))
cli_command(__name__, 'network nic ip-config address-pool remove', custom_path.format('remove_nic_ip_config_address_pool'))
cli_command(__name__, 'network nic ip-config inbound-nat-rule add', custom_path.format('add_nic_ip_config_inbound_nat_rule'))
cli_command(__name__, 'network nic ip-config inbound-nat-rule remove', custom_path.format('remove_nic_ip_config_inbound_nat_rule'))

# NetworkSecurityGroupsOperations
cli_command(__name__, 'network nsg delete', 'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.delete', cf_network_security_groups)
cli_command(__name__, 'network nsg show', 'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.get', cf_network_security_groups)
cli_command(__name__, 'network nsg list', custom_path.format('list_nsgs'))
cli_generic_update_command(__name__, 'network nsg update',
                           'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.get',
                           'azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.create_or_update',
                           cf_network_security_groups)

cli_command(__name__, 'network nsg create',
            'azure.cli.command_modules.network.mgmt_nsg.lib.operations.nsg_operations#NsgOperations.create_or_update',
            cf_nsg_create,
            transform=DeploymentOutputLongRunningOperation('Starting network nsg create'))

# PublicIPAddressesOperations
cli_command(__name__, 'network public-ip delete', 'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.delete', cf_public_ip_addresses)
cli_command(__name__, 'network public-ip show', 'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.get', cf_public_ip_addresses)
cli_command(__name__, 'network public-ip list', custom_path.format('list_public_ips'))
cli_generic_update_command(__name__, 'network public-ip update',
                           'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.get',
                           'azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.create_or_update',
                           cf_public_ip_addresses,
                           custom_function_op=custom_path.format('update_public_ip'))

cli_command(__name__, 'network public-ip create',
            'azure.cli.command_modules.network.mgmt_public_ip.lib.operations.public_ip_operations#PublicIpOperations.create_or_update',
            cf_public_ip_create,
            transform=DeploymentOutputLongRunningOperation('Starting network public-ip create'))

# RouteTablesOperations
cli_command(__name__, 'network route-table create', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.create_or_update', cf_route_tables)
cli_command(__name__, 'network route-table delete', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.delete', cf_route_tables)
cli_command(__name__, 'network route-table show', 'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.get', cf_route_tables)
cli_command(__name__, 'network route-table list', custom_path.format('list_route_tables'))
cli_generic_update_command(__name__, 'network route-table update',
                           'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.get',
                           'azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.create_or_update',
                           cf_route_tables,
                           custom_function_op=custom_path.format('update_route_table'))

# RoutesOperations
cli_command(__name__, 'network route-table route delete', 'azure.mgmt.network.operations.routes_operations#RoutesOperations.delete', cf_routes)
cli_command(__name__, 'network route-table route show', 'azure.mgmt.network.operations.routes_operations#RoutesOperations.get', cf_routes)
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
cli_command(__name__, 'network nsg rule show', 'azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.get', cf_security_rules)
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
cli_command(__name__, 'network vnet subnet show', 'azure.mgmt.network.operations.subnets_operations#SubnetsOperations.get', cf_subnets)
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
cli_command(__name__, 'network vpn-connection delete', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.delete', cf_virtual_network_gateway_connections)
cli_command(__name__, 'network vpn-connection show', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get', cf_virtual_network_gateway_connections)
cli_command(__name__, 'network vpn-connection list', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.list', cf_virtual_network_gateway_connections)
cli_generic_update_command(__name__, 'network vpn-connection update',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.create_or_update',
                           cf_virtual_network_gateway_connections,
                           custom_function_op=custom_path.format('update_vpn_connection'))
cli_command(__name__, 'network vpn-connection shared-key show', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get_shared_key', cf_virtual_network_gateway_connections)
cli_command(__name__, 'network vpn-connection shared-key reset', 'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.reset_shared_key', cf_virtual_network_gateway_connections)
cli_generic_update_command(__name__, 'network vpn-connection shared-key update',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.set_shared_key',
                           cf_virtual_network_gateway_connections)

cli_command(__name__, 'network vpn-connection create',
            'azure.cli.command_modules.network.mgmt_vpn_connection.lib.operations.vpn_connection_operations#VpnConnectionOperations.create_or_update',
            cf_vpn_connection_create,
            transform=DeploymentOutputLongRunningOperation('Starting network vpn-connection create'))

# VirtualNetworkGatewaysOperations
cli_command(__name__, 'network vnet-gateway delete', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.delete', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway show', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway list', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.list', cf_virtual_network_gateways)
cli_command(__name__, 'network vnet-gateway reset', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.reset', cf_virtual_network_gateways)
cli_generic_update_command(__name__, 'network vnet-gateway update',
                           'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get',
                           'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.create_or_update',
                           cf_virtual_network_gateways,
                           custom_function_op=custom_path.format('update_vnet_gateway'),
                           no_wait_param='raw')
cli_command(__name__, 'network vnet-gateway root-cert create', custom_path.format('create_vnet_gateway_root_cert'))
cli_command(__name__, 'network vnet-gateway root-cert delete', custom_path.format('delete_vnet_gateway_root_cert'))
cli_command(__name__, 'network vnet-gateway revoked-cert create', custom_path.format('create_vnet_gateway_revoked_cert'))
cli_command(__name__, 'network vnet-gateway revoked-cert delete', custom_path.format('delete_vnet_gateway_revoked_cert'))

cli_command(__name__, 'network vnet-gateway create', 'azure.cli.command_modules.network.mgmt_vnet_gateway.lib.operations.vnet_gateway_operations#VnetGatewayOperations.create_or_update', cf_vnet_gateway_create, transform=DeploymentOutputLongRunningOperation('Starting network vnet-gateway create'),
            no_wait_param='raw')
cli_generic_wait_command(__name__, 'network vnet-gateway wait', 'azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.get', cf_virtual_network_gateways)

# VirtualNetworksOperations
cli_command(__name__, 'network vnet delete', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.delete', cf_virtual_networks)
cli_command(__name__, 'network vnet show', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.get', cf_virtual_networks)
cli_command(__name__, 'network vnet list', custom_path.format('list_vnet'))
cli_command(__name__, 'network vnet check-ip-address', 'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.check_ip_address_availability', cf_virtual_networks)
cli_generic_update_command(__name__, 'network vnet update',
                           'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.get',
                           'azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.create_or_update',
                           cf_virtual_networks,
                           custom_function_op=custom_path.format('update_vnet'))

cli_command(__name__, 'network vnet create',
            'azure.cli.command_modules.network.mgmt_vnet.lib.operations.vnet_operations#VnetOperations.create_or_update',
            cf_vnet_create,
            transform=DeploymentOutputLongRunningOperation('Starting network vnet create'))

# VNET Peering Operations
cli_command(__name__, 'network vnet peering create', custom_path.format('create_vnet_peering'))
cli_command(__name__, 'network vnet peering show', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.get', cf_virtual_network_peerings)
cli_command(__name__, 'network vnet peering list', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.list', cf_virtual_network_peerings)
cli_command(__name__, 'network vnet peering delete', 'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.delete', cf_virtual_network_peerings)
cli_generic_update_command(__name__, 'network vnet peering update',
                           'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.get',
                           'azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.create_or_update',
                           cf_virtual_network_peerings,
                           setter_arg_name='virtual_network_peering_parameters')

# Traffic Manager ProfileOperations
cli_command(__name__, 'network traffic-manager profile check-dns', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.check_traffic_manager_relative_dns_name_availability', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile show', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.get', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile delete', 'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.delete', cf_traffic_manager_mgmt_profiles)
cli_command(__name__, 'network traffic-manager profile list', custom_path.format('list_traffic_manager_profiles'))
cli_generic_update_command(__name__, 'network traffic-manager profile update',
                           'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.get',
                           'azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.create_or_update',
                           cf_traffic_manager_mgmt_profiles,
                           custom_function_op=custom_path.format('update_traffic_manager_profile'))

cli_command(__name__, 'network traffic-manager profile create',
            'azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib.operations.traffic_manager_profile_operations#TrafficManagerProfileOperations.create_or_update',
            cf_traffic_manager_profile_create,
            transform=DeploymentOutputLongRunningOperation('Starting network traffic-manager profile create'))

# Traffic Manager EndpointOperations
cli_command(__name__, 'network traffic-manager endpoint show', 'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.get', cf_traffic_manager_mgmt_endpoints)
cli_command(__name__, 'network traffic-manager endpoint delete', 'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.delete', cf_traffic_manager_mgmt_endpoints)
cli_command(__name__, 'network traffic-manager endpoint create', custom_path.format('create_traffic_manager_endpoint'))
cli_command(__name__, 'network traffic-manager endpoint list', custom_path.format('list_traffic_manager_endpoints'))
cli_generic_update_command(__name__, 'network traffic-manager endpoint update',
                           'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.get',
                           'azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.create_or_update',
                           cf_traffic_manager_mgmt_endpoints,
                           custom_function_op=custom_path.format('update_traffic_manager_endpoint'))

# DNS ZonesOperations
cli_command(__name__, 'network dns zone show', 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.get', cf_dns_mgmt_zones)
cli_command(__name__, 'network dns zone delete', 'azure.mgmt.dns.operations.zones_operations#ZonesOperations.delete', cf_dns_mgmt_zones)
cli_command(__name__, 'network dns zone list', custom_path.format('list_dns_zones'))
cli_generic_update_command(__name__, 'network dns zone update',
                           'azure.mgmt.dns.operations.zones_operations#ZonesOperations.get',
                           'azure.mgmt.dns.operations.zones_operations#ZonesOperations.create_or_update',
                           cf_dns_mgmt_zones)
cli_command(__name__, 'network dns zone import', custom_path.format('import_zone'))
cli_command(__name__, 'network dns zone export', custom_path.format('export_zone'))
cli_command(__name__, 'network dns zone create', custom_path.format('create_dns_zone'), cf_dns_mgmt_zones)

# DNS RecordSetsOperations
cli_command(__name__, 'network dns record-set show', 'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.get', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set delete', 'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.delete', cf_dns_mgmt_record_sets)
cli_command(__name__, 'network dns record-set list', 'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.list_all_in_resource_group', cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output)
cli_command(__name__, 'network dns record-set create', custom_path.format('create_dns_record_set'), transform=transform_dns_record_set_output)
cli_generic_update_command(__name__, 'network dns record-set update',
                           'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.get',
                           'azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.create_or_update',
                           cf_dns_mgmt_record_sets,
                           custom_function_op=custom_path.format('update_dns_record_set'),
                           transform=transform_dns_record_set_output)

# DNS RecordOperations
cli_command(__name__, 'network dns record aaaa add', custom_path.format('add_dns_aaaa_record'))
cli_command(__name__, 'network dns record a add', custom_path.format('add_dns_a_record'))
cli_command(__name__, 'network dns record cname add', custom_path.format('add_dns_cname_record'))
cli_command(__name__, 'network dns record ns add', custom_path.format('add_dns_ns_record'))
cli_command(__name__, 'network dns record mx add', custom_path.format('add_dns_mx_record'))
cli_command(__name__, 'network dns record ptr add', custom_path.format('add_dns_ptr_record'))
cli_command(__name__, 'network dns record srv add', custom_path.format('add_dns_srv_record'))
cli_command(__name__, 'network dns record txt add', custom_path.format('add_dns_txt_record'))
cli_command(__name__, 'network dns record update-soa', custom_path.format('update_dns_soa_record'))
cli_command(__name__, 'network dns record aaaa remove', custom_path.format('remove_dns_aaaa_record'))
cli_command(__name__, 'network dns record a remove', custom_path.format('remove_dns_a_record'))
cli_command(__name__, 'network dns record cname remove', custom_path.format('remove_dns_cname_record'))
cli_command(__name__, 'network dns record ns remove', custom_path.format('remove_dns_ns_record'))
cli_command(__name__, 'network dns record mx remove', custom_path.format('remove_dns_mx_record'))
cli_command(__name__, 'network dns record ptr remove', custom_path.format('remove_dns_ptr_record'))
cli_command(__name__, 'network dns record srv remove', custom_path.format('remove_dns_srv_record'))
cli_command(__name__, 'network dns record txt remove', custom_path.format('remove_dns_txt_record'))
