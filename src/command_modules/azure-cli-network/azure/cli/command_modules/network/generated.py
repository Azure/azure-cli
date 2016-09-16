#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.mgmt.network.operations import (
    ApplicationGatewaysOperations,
    ExpressRouteCircuitAuthorizationsOperations,
    ExpressRouteCircuitPeeringsOperations,
    ExpressRouteCircuitsOperations,
    ExpressRouteServiceProvidersOperations,
    LoadBalancersOperations,
    LocalNetworkGatewaysOperations,
    NetworkInterfacesOperations,
    NetworkSecurityGroupsOperations,
    PublicIPAddressesOperations,
    RouteTablesOperations,
    RoutesOperations,
    SecurityRulesOperations,
    SubnetsOperations,
    UsagesOperations,
    VirtualNetworkGatewayConnectionsOperations,
    VirtualNetworkGatewaysOperations,
    VirtualNetworksOperations,
    VirtualNetworkPeeringsOperations)

from azure.mgmt.trafficmanager.operations import EndpointsOperations, ProfilesOperations
from azure.mgmt.trafficmanager import TrafficManagerManagementClient
from azure.mgmt.dns.operations import RecordSetsOperations, ZonesOperations
from azure.mgmt.dns import DnsManagementClient

from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.arm import cli_generic_update_command
from azure.cli.command_modules.network.mgmt_app_gateway.lib.operations import AppGatewayOperations
from azure.cli.command_modules.network.mgmt_app_gateway.lib \
    import AppGatewayCreationClient as AppGatewayClient
from azure.cli.command_modules.network.mgmt_vnet.lib \
    import VnetCreationClient as VNetClient
from azure.cli.command_modules.network.mgmt_vnet.lib.operations import VnetOperations
from azure.cli.command_modules.network.mgmt_public_ip.lib \
    import PublicIpCreationClient as PublicIPClient
from azure.cli.command_modules.network.mgmt_public_ip.lib.operations import PublicIpOperations
from azure.cli.command_modules.network.mgmt_lb.lib import LbCreationClient as LBClient
from azure.cli.command_modules.network.mgmt_lb.lib.operations import LbOperations
from azure.cli.command_modules.network.mgmt_nic.lib import NicCreationClient as NicClient
from azure.cli.command_modules.network.mgmt_nic.lib.operations import NicOperations
from azure.cli.command_modules.network.mgmt_nsg.lib import NsgCreationClient as NSGClient
from azure.cli.command_modules.network.mgmt_nsg.lib.operations import NsgOperations
from azure.cli.command_modules.network.mgmt_vnet_gateway.lib.operations \
    import VnetGatewayOperations
from azure.cli.command_modules.network.mgmt_vnet_gateway.lib \
    import VnetGatewayCreationClient as VnetGatewayClient
from azure.cli.command_modules.network.mgmt_local_gateway.lib.operations \
    import LocalGatewayOperations
from azure.cli.command_modules.network.mgmt_local_gateway.lib \
    import LocalGatewayCreationClient as LocalGatewayClient
from azure.cli.command_modules.network.mgmt_route_table.lib.operations import RouteTableOperations
from azure.cli.command_modules.network.mgmt_route_table.lib \
    import RouteTableCreationClient as RouteTableClient
from azure.cli.command_modules.network.mgmt_vpn_connection.lib.operations \
    import VpnConnectionOperations
from azure.cli.command_modules.network.mgmt_vpn_connection.lib \
    import VpnConnectionCreationClient as VpnConnectionClient
from azure.cli.command_modules.network.mgmt_express_route_circuit.lib.operations \
    import ExpressRouteCircuitOperations
from azure.cli.command_modules.network.mgmt_express_route_circuit.lib \
    import ExpressRouteCircuitCreationClient as ExpressRouteCircuitClient
from azure.cli.command_modules.network.mgmt_express_route_peering.lib.operations \
    import ExpressRoutePeeringOperations
from azure.cli.command_modules.network.mgmt_express_route_peering.lib \
    import ExpressRoutePeeringCreationClient as ExpressRoutePeeringClient
from azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib.operations \
    import TrafficManagerProfileOperations
from azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib \
    import TrafficManagerProfileCreationClient as TrafficManagerProfileClient
from azure.cli.command_modules.network.mgmt_dns_zone.lib.operations \
    import DnsZoneOperations
from azure.cli.command_modules.network.mgmt_dns_zone.lib \
    import DnsZoneCreationClient as DnsZoneClient

from azure.cli.core.commands import DeploymentOutputLongRunningOperation, cli_command

from .custom import \
    (update_vnet, update_subnet, create_subnet,
     create_ag_ssl_cert,
     create_ag_address_pool,
     create_ag_frontend_ip,
     create_ag_frontend_port,
     create_ag_http_listener,
     create_ag_http_settings,
     create_ag_probe,
     create_ag_rule,
     create_ag_url_path_map,
     create_ag_url_path_map_rule, delete_ag_url_path_map_rule,
     create_nsg_rule, update_nsg_rule,
     create_lb_inbound_nat_rule, set_lb_inbound_nat_rule,
     create_lb_frontend_ip_configuration, set_lb_frontend_ip_configuration,
     create_lb_inbound_nat_pool, set_lb_inbound_nat_pool,
     create_lb_backend_address_pool,
     create_lb_probe, set_lb_probe,
     create_lb_rule, set_lb_rule,
     create_nic_ip_config, set_nic_ip_config,
     add_nic_ip_config_address_pool, remove_nic_ip_config_address_pool,
     add_nic_ip_config_inbound_nat_rule, remove_nic_ip_config_inbound_nat_rule,
     set_nic,
     list_network_resource_property, get_network_resource_property_entry,
     delete_network_resource_property_entry,
     list_application_gateways, list_express_route_circuits, list_lbs, list_nics, list_nsgs,
     list_public_ips, list_route_tables, list_vnet, create_vnet_peering, create_route,
     update_network_vpn_gateway, create_vpn_gateway_root_cert, delete_vpn_gateway_root_cert,
     create_vpn_gateway_revoked_cert, delete_vpn_gateway_revoked_cert, create_express_route_auth,
     list_traffic_manager_profiles, create_traffic_manager_endpoint, list_dns_zones,
     create_dns_record_set, add_dns_aaaa_record, add_dns_a_record, add_dns_cname_record,
     add_dns_ns_record, add_dns_ptr_record, update_dns_soa_record, add_dns_srv_record,
     add_dns_txt_record, add_dns_mx_record,
     remove_dns_aaaa_record, remove_dns_a_record, remove_dns_cname_record,
     remove_dns_ns_record, remove_dns_ptr_record, remove_dns_srv_record,
     remove_dns_txt_record, remove_dns_mx_record, list_traffic_manager_endpoints,
     export_zone, import_zone)
from ._factory import _network_client_factory

# pylint: disable=line-too-long
# Application gateways
factory = lambda _: _network_client_factory().application_gateways
cli_command('network application-gateway delete', ApplicationGatewaysOperations.delete, factory)
cli_command('network application-gateway show', ApplicationGatewaysOperations.get, factory)
cli_command('network application-gateway list', list_application_gateways)
cli_command('network application-gateway start', ApplicationGatewaysOperations.start, factory)
cli_command('network application-gateway stop', ApplicationGatewaysOperations.stop, factory)
cli_generic_update_command('network application-gateway update', ApplicationGatewaysOperations.get, ApplicationGatewaysOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(AppGatewayClient).app_gateway
cli_command('network application-gateway create', AppGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network application-gateway create'))

property_map = {
    'ssl_certificates': 'ssl-cert',
    'frontend_ip_configurations': 'frontend-ip',
    'frontend_ports': 'frontend-port',
    'backend_address_pools': 'address-pool',
    'backend_http_settings_collection': 'http-settings',
    'http_listeners': 'http-listener',
    'request_routing_rules': 'rule',
    'probes': 'probe',
    'url_path_maps': 'url-path-map'
}
for subresource, alias in property_map.items():
    cli_command('network application-gateway {} list'.format(alias), list_network_resource_property('application_gateways', subresource))
    cli_command('network application-gateway {} show'.format(alias), get_network_resource_property_entry('application_gateways', subresource))
    cli_command('network application-gateway {} delete'.format(alias), delete_network_resource_property_entry('application_gateways', subresource))

cli_command('network application-gateway address-pool create', create_ag_address_pool)
cli_command('network application-gateway frontend-ip create', create_ag_frontend_ip)
cli_command('network application-gateway frontend-port create', create_ag_frontend_port)
cli_command('network application-gateway http-listener create', create_ag_http_listener)
cli_command('network application-gateway http-settings create', create_ag_http_settings)
cli_command('network application-gateway probe create', create_ag_probe)
cli_command('network application-gateway rule create', create_ag_rule)
cli_command('network application-gateway ssl-cert create', create_ag_ssl_cert)
cli_command('network application-gateway url-path-map create', create_ag_url_path_map)
cli_command('network application-gateway url-path-map rule create', create_ag_url_path_map_rule)
cli_command('network application-gateway url-path-map rule delete', delete_ag_url_path_map_rule)

# ExpressRouteCircuitAuthorizationsOperations
factory = lambda _: _network_client_factory().express_route_circuit_authorizations
cli_command('network express-route circuit-auth delete', ExpressRouteCircuitAuthorizationsOperations.delete, factory)
cli_command('network express-route circuit-auth show', ExpressRouteCircuitAuthorizationsOperations.get, factory)
cli_command('network express-route circuit-auth list', ExpressRouteCircuitAuthorizationsOperations.list, factory)
cli_generic_update_command('network express-route circuit-auth update', ExpressRouteCircuitAuthorizationsOperations.get, ExpressRouteCircuitAuthorizationsOperations.create_or_update, factory)
cli_command('network express-route circuit-auth create', create_express_route_auth)

# ExpressRouteCircuitPeeringsOperations
factory = lambda _: _network_client_factory().express_route_circuit_peerings
cli_command('network express-route circuit-peering delete', ExpressRouteCircuitPeeringsOperations.delete, factory)
cli_command('network express-route circuit-peering show', ExpressRouteCircuitPeeringsOperations.get, factory)
cli_command('network express-route circuit-peering list', ExpressRouteCircuitPeeringsOperations.list, factory)
cli_generic_update_command('network express-route circuit-peering update', ExpressRouteCircuitPeeringsOperations.get, ExpressRouteCircuitPeeringsOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(ExpressRoutePeeringClient).express_route_peering
cli_command('network express-route circuit-peering create', ExpressRoutePeeringOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network express-route circuit-peering create'))

# ExpressRouteCircuitsOperations
factory = lambda _: _network_client_factory().express_route_circuits
cli_command('network express-route circuit delete', ExpressRouteCircuitsOperations.delete, factory)
cli_command('network express-route circuit show', ExpressRouteCircuitsOperations.get, factory)
cli_command('network express-route circuit get-stats', ExpressRouteCircuitsOperations.get_stats, factory)
cli_command('network express-route circuit list-arp-tables', ExpressRouteCircuitsOperations.list_arp_table, factory)
cli_command('network express-route circuit list-route-tables', ExpressRouteCircuitsOperations.list_routes_table, factory)
cli_command('network express-route circuit list', list_express_route_circuits)
cli_generic_update_command('network express-route circuit update', ExpressRouteCircuitsOperations.get, ExpressRouteCircuitsOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(ExpressRouteCircuitClient).express_route_circuit
cli_command('network express-route circuit create', ExpressRouteCircuitOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network express-route circuit create'))

# ExpressRouteServiceProvidersOperations
factory = lambda _: _network_client_factory().express_route_service_providers
cli_command('network express-route service-provider list', ExpressRouteServiceProvidersOperations.list, factory)

# LoadBalancersOperations
factory = lambda _: _network_client_factory().load_balancers
cli_command('network lb delete', LoadBalancersOperations.delete, factory)
cli_command('network lb show', LoadBalancersOperations.get, factory)
cli_command('network lb list', list_lbs)
cli_generic_update_command('network lb update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(LBClient).lb
cli_command('network lb create', LbOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network lb create'))

property_map = {
    'frontend_ip_configurations': 'frontend-ip',
    'inbound_nat_rules': 'inbound-nat-rule',
    'inbound_nat_pools': 'inbound-nat-pool',
    'backend_address_pools': 'address-pool',
    'load_balancing_rules': 'rule',
    'probes': 'probe'
}
for subresource, alias in property_map.items():
    cli_command('network lb {} list'.format(alias), list_network_resource_property('load_balancers', subresource))
    cli_command('network lb {} show'.format(alias), get_network_resource_property_entry('load_balancers', subresource))
    cli_command('network lb {} delete'.format(alias), delete_network_resource_property_entry('load_balancers', subresource))

cli_command('network lb frontend-ip create', create_lb_frontend_ip_configuration)
cli_command('network lb inbound-nat-rule create', create_lb_inbound_nat_rule)
cli_command('network lb inbound-nat-pool create', create_lb_inbound_nat_pool)
cli_command('network lb address-pool create', create_lb_backend_address_pool)
cli_command('network lb rule create', create_lb_rule)
cli_command('network lb probe create', create_lb_probe)

factory = lambda _: _network_client_factory().load_balancers
cli_generic_update_command('network lb frontend-ip update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory, child_collection_prop_name='frontend_ip_configurations', custom_function=set_lb_frontend_ip_configuration)
cli_generic_update_command('network lb inbound-nat-rule update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory, child_collection_prop_name='inbound_nat_rules', custom_function=set_lb_inbound_nat_rule)
cli_generic_update_command('network lb inbound-nat-pool update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory, child_collection_prop_name='inbound_nat_pools', custom_function=set_lb_inbound_nat_pool)
cli_generic_update_command('network lb rule update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory, child_collection_prop_name='load_balancing_rules', custom_function=set_lb_rule)
cli_generic_update_command('network lb probe update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory, child_collection_prop_name='probes', custom_function=set_lb_probe)

# LocalNetworkGatewaysOperations
factory = lambda _: _network_client_factory().local_network_gateways
cli_command('network local-gateway delete', LocalNetworkGatewaysOperations.delete, factory)
cli_command('network local-gateway show', LocalNetworkGatewaysOperations.get, factory)
cli_command('network local-gateway list', LocalNetworkGatewaysOperations.list, factory)
cli_generic_update_command('network local-gateway update', LocalNetworkGatewaysOperations.get, LocalNetworkGatewaysOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(LocalGatewayClient).local_gateway
cli_command('network local-gateway create', LocalGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network local-gateway create'))

# NetworkInterfacesOperations
factory = lambda _: get_mgmt_service_client(NicClient).nic
cli_command('network nic create', NicOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nic create'))

factory = lambda _: _network_client_factory().network_interfaces
cli_command('network nic delete', NetworkInterfacesOperations.delete, factory)
cli_command('network nic show', NetworkInterfacesOperations.get, factory)
cli_command('network nic list', list_nics)
cli_generic_update_command('network nic update', NetworkInterfacesOperations.get, NetworkInterfacesOperations.create_or_update, factory, custom_function=set_nic)
cli_command('network nic show-effective-route-table', NetworkInterfacesOperations.get_effective_route_table, factory)
cli_command('network nic list-effective-nsg', NetworkInterfacesOperations.list_effective_network_security_groups, factory)

resource = 'network_interfaces'
subresource = 'ip_configurations'
cli_command('network nic ip-config create', create_nic_ip_config)
cli_generic_update_command('network nic ip-config update', NetworkInterfacesOperations.get, NetworkInterfacesOperations.create_or_update, factory, child_collection_prop_name='ip_configurations', child_arg_name='ip_config_name', custom_function=set_nic_ip_config)
cli_command('network nic ip-config list', list_network_resource_property(resource, subresource))
cli_command('network nic ip-config show', get_network_resource_property_entry(resource, subresource))
cli_command('network nic ip-config delete', delete_network_resource_property_entry(resource, subresource))
cli_command('network nic ip-config address-pool add', add_nic_ip_config_address_pool)
cli_command('network nic ip-config address-pool remove', remove_nic_ip_config_address_pool)
cli_command('network nic ip-config inbound-nat-rule add', add_nic_ip_config_inbound_nat_rule)
cli_command('network nic ip-config inbound-nat-rule remove', remove_nic_ip_config_inbound_nat_rule)

# NetworkSecurityGroupsOperations
factory = lambda _: _network_client_factory().network_security_groups
cli_command('network nsg delete', NetworkSecurityGroupsOperations.delete, factory)
cli_command('network nsg show', NetworkSecurityGroupsOperations.get, factory)
cli_command('network nsg list', list_nsgs)
cli_generic_update_command('network nsg update', NetworkSecurityGroupsOperations.get, NetworkSecurityGroupsOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(NSGClient).nsg
cli_command('network nsg create', NsgOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nsg create'))

# PublicIPAddressesOperations
factory = lambda _: _network_client_factory().public_ip_addresses
cli_command('network public-ip delete', PublicIPAddressesOperations.delete, factory)
cli_command('network public-ip show', PublicIPAddressesOperations.get, factory)
cli_command('network public-ip list', list_public_ips)
cli_generic_update_command('network public-ip update', PublicIPAddressesOperations.get, PublicIPAddressesOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(PublicIPClient).public_ip
cli_command('network public-ip create', PublicIpOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network public-ip create'))

# RouteTablesOperations
factory = lambda _: _network_client_factory().route_tables
cli_command('network route-table delete', RouteTablesOperations.delete, factory)
cli_command('network route-table show', RouteTablesOperations.get, factory)
cli_command('network route-table list', list_route_tables)
cli_generic_update_command('network route-table update', RouteTablesOperations.get, RouteTablesOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(RouteTableClient).route_table
cli_command('network route-table create', RouteTableOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network route-table create'))

# RoutesOperations
factory = lambda _: _network_client_factory().routes
cli_command('network route-table route delete', RoutesOperations.delete, factory)
cli_command('network route-table route show', RoutesOperations.get, factory)
cli_command('network route-table route list', RoutesOperations.list, factory)
cli_generic_update_command('network route-table route update', RoutesOperations.get, RoutesOperations.create_or_update, factory)
cli_command('network route-table route create', create_route)

# SecurityRulesOperations
factory = lambda _: _network_client_factory().security_rules
cli_command('network nsg rule delete', SecurityRulesOperations.delete, factory)
cli_command('network nsg rule show', SecurityRulesOperations.get, factory)
cli_command('network nsg rule list', SecurityRulesOperations.list, factory)
cli_command('network nsg rule create', create_nsg_rule)
cli_generic_update_command('network nsg rule update', SecurityRulesOperations.get, SecurityRulesOperations.create_or_update, factory, setter_arg_name='security_rule_parameters', custom_function=update_nsg_rule)

# SubnetsOperations
factory = lambda _: _network_client_factory().subnets
cli_command('network vnet subnet delete', SubnetsOperations.delete, factory)
cli_command('network vnet subnet show', SubnetsOperations.get, factory)
cli_command('network vnet subnet list', SubnetsOperations.list, factory)
cli_command('network vnet subnet create', create_subnet)
cli_generic_update_command('network vnet subnet update', SubnetsOperations.get, SubnetsOperations.create_or_update, factory, setter_arg_name='subnet_parameters', custom_function=update_subnet)

# Usages operations
factory = lambda _: _network_client_factory().usages
cli_command('network list-usages', UsagesOperations.list, factory)

factory = lambda _: _network_client_factory().virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
cli_command('network vpn-connection delete', VirtualNetworkGatewayConnectionsOperations.delete, factory)
cli_command('network vpn-connection show', VirtualNetworkGatewayConnectionsOperations.get, factory)
cli_command('network vpn-connection list', VirtualNetworkGatewayConnectionsOperations.list, factory)
cli_generic_update_command('network vpn-connection update', VirtualNetworkGatewayConnectionsOperations.get, VirtualNetworkGatewayConnectionsOperations.create_or_update, factory)
cli_command('network vpn-connection shared-key show', VirtualNetworkGatewayConnectionsOperations.get_shared_key, factory)
cli_command('network vpn-connection shared-key reset', VirtualNetworkGatewayConnectionsOperations.reset_shared_key, factory)
cli_generic_update_command('network vpn-connection shared-key update', VirtualNetworkGatewayConnectionsOperations.get, VirtualNetworkGatewayConnectionsOperations.set_shared_key, factory)

factory = lambda _: get_mgmt_service_client(VpnConnectionClient).vpn_connection
cli_command('network vpn-connection create', VpnConnectionOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network vpn-connection create'))

# VirtualNetworkGatewaysOperations
factory = lambda _: _network_client_factory().virtual_network_gateways
cli_command('network vpn-gateway delete', VirtualNetworkGatewaysOperations.delete, factory)
cli_command('network vpn-gateway show', VirtualNetworkGatewaysOperations.get, factory)
cli_command('network vpn-gateway list', VirtualNetworkGatewaysOperations.list, factory)
cli_command('network vpn-gateway reset', VirtualNetworkGatewaysOperations.reset, factory)
cli_generic_update_command('network vpn-gateway update', VirtualNetworkGatewaysOperations.get, VirtualNetworkGatewaysOperations.create_or_update, factory,
                           custom_function=update_network_vpn_gateway)
cli_command('network vpn-gateway root-cert create', create_vpn_gateway_root_cert)
cli_command('network vpn-gateway root-cert delete', delete_vpn_gateway_root_cert)
cli_command('network vpn-gateway revoked-cert create', create_vpn_gateway_revoked_cert)
cli_command('network vpn-gateway revoked-cert delete', delete_vpn_gateway_revoked_cert)

factory = lambda _: get_mgmt_service_client(VnetGatewayClient).vnet_gateway
cli_command('network vpn-gateway create', VnetGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network vnet-gateway create'))

# VirtualNetworksOperations
factory = lambda _: _network_client_factory().virtual_networks
cli_command('network vnet delete', VirtualNetworksOperations.delete, factory)
cli_command('network vnet show', VirtualNetworksOperations.get, factory)
cli_command('network vnet list', list_vnet)
cli_command('network vnet check-ip-address', VirtualNetworksOperations.check_ip_address_availability, factory)
cli_generic_update_command('network vnet update', VirtualNetworksOperations.get, VirtualNetworksOperations.create_or_update, factory,
                           custom_function=update_vnet)

factory = lambda _: get_mgmt_service_client(VNetClient).vnet
cli_command('network vnet create', VnetOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network vnet create'))

# VNET Peering Operations
factory = lambda _: _network_client_factory().virtual_network_peerings
cli_command('network vnet peering create', create_vnet_peering)
cli_command('network vnet peering show', VirtualNetworkPeeringsOperations.get, factory)
cli_command('network vnet peering list', VirtualNetworkPeeringsOperations.list, factory)
cli_command('network vnet peering delete', VirtualNetworkPeeringsOperations.delete, factory)
cli_generic_update_command('network vnet peering update', VirtualNetworkPeeringsOperations.get, VirtualNetworkPeeringsOperations.create_or_update, factory, setter_arg_name='virtual_network_peering_parameters')

# Traffic Manager ProfileOperations
factory = lambda _: get_mgmt_service_client(TrafficManagerManagementClient).profiles
cli_command('network traffic-manager profile check-dns', ProfilesOperations.check_traffic_manager_relative_dns_name_availability, factory)
cli_command('network traffic-manager profile show', ProfilesOperations.get, factory)
cli_command('network traffic-manager profile delete', ProfilesOperations.delete, factory)
cli_command('network traffic-manager profile list', list_traffic_manager_profiles)
cli_generic_update_command('network traffic-manager profile update', ProfilesOperations.get, ProfilesOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(TrafficManagerProfileClient).traffic_manager_profile
cli_command('network traffic-manager profile create', TrafficManagerProfileOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network traffic-manager profile create'))

# Traffic Manager EndpointOperations
factory = lambda _: get_mgmt_service_client(TrafficManagerManagementClient).endpoints
cli_command('network traffic-manager endpoint show', EndpointsOperations.get, factory)
cli_command('network traffic-manager endpoint delete', EndpointsOperations.delete, factory)
cli_command('network traffic-manager endpoint create', create_traffic_manager_endpoint)
cli_command('network traffic-manager endpoint list', list_traffic_manager_endpoints)
cli_generic_update_command('network traffic-manager endpoint update', EndpointsOperations.get, EndpointsOperations.create_or_update, factory)

# DNS ZonesOperations
factory = lambda _: get_mgmt_service_client(DnsManagementClient).zones
cli_command('network dns zone show', ZonesOperations.get, factory)
cli_command('network dns zone delete', ZonesOperations.delete, factory)
cli_command('network dns zone list', list_dns_zones)
cli_generic_update_command('network dns zone update', ZonesOperations.get, ZonesOperations.create_or_update, factory)
cli_command('network dns zone import', import_zone)
cli_command('network dns zone export', export_zone)

factory = lambda _: get_mgmt_service_client(DnsZoneClient).dns_zone
cli_command('network dns zone create', DnsZoneOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network dns zone create'))

# DNS RecordSetsOperations
factory = lambda _: get_mgmt_service_client(DnsManagementClient).record_sets
cli_command('network dns record-set show', RecordSetsOperations.get, factory)
cli_command('network dns record-set delete', RecordSetsOperations.delete, factory)
cli_command('network dns record-set list', RecordSetsOperations.list_all_in_resource_group, factory)
cli_command('network dns record-set create', create_dns_record_set)
cli_generic_update_command('network dns record-set update', RecordSetsOperations.get, RecordSetsOperations.create_or_update, factory)

# DNS RecordOperations
cli_command('network dns record aaaa add', add_dns_aaaa_record)
cli_command('network dns record a add', add_dns_a_record)
cli_command('network dns record cname add', add_dns_cname_record)
cli_command('network dns record ns add', add_dns_ns_record)
cli_command('network dns record mx add', add_dns_mx_record)
cli_command('network dns record ptr add', add_dns_ptr_record)
cli_command('network dns record srv add', add_dns_srv_record)
cli_command('network dns record txt add', add_dns_txt_record)
cli_command('network dns record update-soa', update_dns_soa_record)
cli_command('network dns record aaaa remove', remove_dns_aaaa_record)
cli_command('network dns record a remove', remove_dns_a_record)
cli_command('network dns record cname remove', remove_dns_cname_record)
cli_command('network dns record ns remove', remove_dns_ns_record)
cli_command('network dns record mx remove', remove_dns_mx_record)
cli_command('network dns record ptr remove', remove_dns_ptr_record)
cli_command('network dns record srv remove', remove_dns_srv_record)
cli_command('network dns record txt remove', remove_dns_txt_record)
