﻿#---------------------------------------------------------------------------------------------
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
    VirtualNetworksOperations)

from azure.cli.commands.client_factory import get_mgmt_service_client
from azure.cli.commands.arm import register_generic_update
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


from azure.cli.commands import DeploymentOutputLongRunningOperation, cli_command

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
     list_public_ips, list_route_tables, list_vnet
    )
from ._factory import _network_client_factory

# pylint: disable=line-too-long
# Application gateways
factory = lambda _: _network_client_factory().application_gateways
cli_command('network application-gateway delete', ApplicationGatewaysOperations.delete, factory)
cli_command('network application-gateway show', ApplicationGatewaysOperations.get, factory)
cli_command('network application-gateway list', list_application_gateways, simple_output_query="[*].{Name:name, ResourceGroup:resourceGroup, Location:location, State:provisioningState} | sort_by(@, &Name)")
cli_command('network application-gateway start', ApplicationGatewaysOperations.start, factory)
cli_command('network application-gateway stop', ApplicationGatewaysOperations.stop, factory)
register_generic_update('network application-gateway update', ApplicationGatewaysOperations.get, ApplicationGatewaysOperations.create_or_update, factory)

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
    cli_command('network application-gateway {} list'.format(alias), list_network_resource_property('application_gateways', subresource), simple_output_query="[*].{Name:name} | sort_by(@, &Name)")
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
register_generic_update('network express-route circuit-auth update', ExpressRouteCircuitAuthorizationsOperations.get, ExpressRouteCircuitAuthorizationsOperations.create_or_update, factory)

# ExpressRouteCircuitPeeringsOperations
factory = lambda _: _network_client_factory().express_route_circuit_peerings
cli_command('network express-route circuit-peering delete', ExpressRouteCircuitPeeringsOperations.delete, factory)
cli_command('network express-route circuit-peering show', ExpressRouteCircuitPeeringsOperations.get, factory)
cli_command('network express-route circuit-peering list', ExpressRouteCircuitPeeringsOperations.list, factory)
register_generic_update('network express-route circuit-peering update', ExpressRouteCircuitPeeringsOperations.get, ExpressRouteCircuitPeeringsOperations.create_or_update, factory)

# ExpressRouteCircuitsOperations
factory = lambda _: _network_client_factory().express_route_circuits
cli_command('network express-route circuit delete', ExpressRouteCircuitsOperations.delete, factory)
cli_command('network express-route circuit show', ExpressRouteCircuitsOperations.get, factory)
cli_command('network express-route circuit get-stats', ExpressRouteCircuitsOperations.get_stats, factory)
cli_command('network express-route circuit list-arp', ExpressRouteCircuitsOperations.list_arp_table, factory)
cli_command('network express-route circuit list-routes', ExpressRouteCircuitsOperations.list_routes_table, factory)
cli_command('network express-route circuit list', list_express_route_circuits)
register_generic_update('network express-route circuit update', ExpressRouteCircuitsOperations.get, ExpressRouteCircuitsOperations.create_or_update, factory)

# ExpressRouteServiceProvidersOperations
factory = lambda _: _network_client_factory().express_route_service_providers
cli_command('network express-route service-provider list', ExpressRouteServiceProvidersOperations.list, factory)

# LoadBalancersOperations
factory = lambda _: _network_client_factory().load_balancers
cli_command('network lb delete', LoadBalancersOperations.delete, factory)
cli_command('network lb show', LoadBalancersOperations.get, factory)
cli_command('network lb list', list_lbs)
register_generic_update('network lb update', LoadBalancersOperations.get, LoadBalancersOperations.create_or_update, factory)

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
cli_command('network lb frontend-ip update', set_lb_frontend_ip_configuration)
cli_command('network lb inbound-nat-rule create', create_lb_inbound_nat_rule)
cli_command('network lb inbound-nat-rule update', set_lb_inbound_nat_rule)
cli_command('network lb inbound-nat-pool create', create_lb_inbound_nat_pool)
cli_command('network lb inbound-nat-pool update', set_lb_inbound_nat_pool)
cli_command('network lb address-pool create', create_lb_backend_address_pool)
cli_command('network lb rule create', create_lb_rule)
cli_command('network lb rule update', set_lb_rule)
cli_command('network lb probe create', create_lb_probe)
cli_command('network lb probe update', set_lb_probe)

# LocalNetworkGatewaysOperations
factory = lambda _: _network_client_factory().local_network_gateways
cli_command('network local-gateway delete', LocalNetworkGatewaysOperations.delete, factory)
cli_command('network local-gateway show', LocalNetworkGatewaysOperations.get, factory)
cli_command('network local-gateway list', LocalNetworkGatewaysOperations.list, factory)
register_generic_update('network local-gateway update', LocalNetworkGatewaysOperations.get, LocalNetworkGatewaysOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(LocalGatewayClient).local_gateway
cli_command('network local-gateway create', LocalGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network local-gateway create'))

# NetworkInterfacesOperations
factory = lambda _: get_mgmt_service_client(NicClient).nic
cli_command('network nic create', NicOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nic create'))

factory = lambda _: _network_client_factory().network_interfaces
cli_command('network nic delete', NetworkInterfacesOperations.delete, factory)
cli_command('network nic show', NetworkInterfacesOperations.get, factory)
cli_command('network nic list', list_nics)
cli_command('network nic update', set_nic) # TODO: no tagging

# NetworkInterfacesOperations: scaleset
cli_command('network nic scale-set list-vm-nics', NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, factory)
cli_command('network nic scale-set list', NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, factory)
cli_command('network nic scale-set show', NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, factory)

resource = 'network_interfaces'
subresource = 'ip_configurations'
cli_command('network nic ip-config create', create_nic_ip_config)
cli_command('network nic ip-config update', set_nic_ip_config)
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
register_generic_update('network nsg update', NetworkSecurityGroupsOperations.get, NetworkSecurityGroupsOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(NSGClient).nsg
cli_command('network nsg create', NsgOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nsg create'))

# PublicIPAddressesOperations
factory = lambda _: _network_client_factory().public_ip_addresses
cli_command('network public-ip delete', PublicIPAddressesOperations.delete, factory)
cli_command('network public-ip show', PublicIPAddressesOperations.get, factory)
cli_command('network public-ip list', list_public_ips, simple_output_query="[*].{Name:name, ResourceGroup:resourceGroup, Location:location, IpAddress:ipAddress, FQDN:dnsSettings.fqdn} | sort_by(@, &Name)")
register_generic_update('network public-ip update', PublicIPAddressesOperations.get, PublicIPAddressesOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(PublicIPClient).public_ip
cli_command('network public-ip create', PublicIpOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network public-ip create'))

# RouteTablesOperations
factory = lambda _: _network_client_factory().route_tables
cli_command('network route-table delete', RouteTablesOperations.delete, factory)
cli_command('network route-table show', RouteTablesOperations.get, factory)
cli_command('network route-table list', list_route_tables)
register_generic_update('network route-table update', RouteTablesOperations.get, RouteTablesOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(RouteTableClient).route_table
cli_command('network route-table create', RouteTableOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network route-table create'))

# RoutesOperations
factory = lambda _: _network_client_factory().routes
cli_command('network route-table route delete', RoutesOperations.delete, factory)
cli_command('network route-table route show', RoutesOperations.get, factory)
cli_command('network route-table route list', RoutesOperations.list, factory)
register_generic_update('network route-table route update', RoutesOperations.get, RoutesOperations.create_or_update, factory)

# SecurityRulesOperations
factory = lambda _: _network_client_factory().security_rules
cli_command('network nsg rule delete', SecurityRulesOperations.delete, factory)
cli_command('network nsg rule show', SecurityRulesOperations.get, factory)
cli_command('network nsg rule list', SecurityRulesOperations.list, factory)
cli_command('network nsg rule create', create_nsg_rule)
cli_command('network nsg rule update', update_nsg_rule)

# SubnetsOperations
factory = lambda _: _network_client_factory().subnets
cli_command('network vnet subnet delete', SubnetsOperations.delete, factory)
cli_command('network vnet subnet show', SubnetsOperations.get, factory)
cli_command('network vnet subnet list', SubnetsOperations.list, factory)
cli_command('network vnet subnet create', create_subnet)
cli_command('network vnet subnet update', update_subnet)

# Usages operations
factory = lambda _: _network_client_factory().usages
cli_command('network list-usages', UsagesOperations.list, factory)

factory = lambda _: _network_client_factory().virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
cli_command('network vpn-connection delete', VirtualNetworkGatewayConnectionsOperations.delete, factory)
cli_command('network vpn-connection show', VirtualNetworkGatewayConnectionsOperations.get, factory)
cli_command('network vpn-connection list', VirtualNetworkGatewayConnectionsOperations.list, factory)
register_generic_update('network vpn-connection update', VirtualNetworkGatewayConnectionsOperations.get, VirtualNetworkGatewayConnectionsOperations.create_or_update, factory)
cli_command('network vpn-connection shared-key show', VirtualNetworkGatewayConnectionsOperations.get_shared_key, factory)
cli_command('network vpn-connection shared-key reset', VirtualNetworkGatewayConnectionsOperations.reset_shared_key, factory)
cli_command('network vpn-connection shared-key update', VirtualNetworkGatewayConnectionsOperations.set_shared_key, factory)

# VirtualNetworkGatewaysOperations
factory = lambda _: _network_client_factory().virtual_network_gateways
cli_command('network vpn-gateway delete', VirtualNetworkGatewaysOperations.delete, factory)
cli_command('network vpn-gateway show', VirtualNetworkGatewaysOperations.get, factory)
cli_command('network vpn-gateway list', VirtualNetworkGatewaysOperations.list, factory)
cli_command('network vpn-gateway reset', VirtualNetworkGatewaysOperations.reset, factory)
register_generic_update('network vpn-gateway update', VirtualNetworkGatewaysOperations.get, VirtualNetworkGatewaysOperations.create_or_update, factory)

factory = lambda _: get_mgmt_service_client(VnetGatewayClient).vnet_gateway
cli_command('network vpn-gateway create', VnetGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network vnet-gateway create'))

# VirtualNetworksOperations
factory = lambda _: _network_client_factory().virtual_networks
cli_command('network vnet delete', VirtualNetworksOperations.delete, factory)
cli_command('network vnet show', VirtualNetworksOperations.get, factory)
cli_command('network vnet list', list_vnet)
cli_command('network vnet update', update_vnet) # TODO: no tagging

factory = lambda _: get_mgmt_service_client(VNetClient).vnet
cli_command('network vnet create', VnetOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network vnet create'))
