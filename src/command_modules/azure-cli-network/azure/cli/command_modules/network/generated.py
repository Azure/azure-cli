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
from azure.cli.command_modules.network.mgmt_app_gateway.lib.operations import AppGatewayOperations
from azure.cli.command_modules.network.mgmt_app_gateway.lib \
    import AppGatewayCreationClient as AppGatewayClient
from azure.cli.command_modules.network.mgmt_vnet.lib \
    import ResourceManagementClient as VNetClient
from azure.cli.command_modules.network.mgmt_vnet.lib.operations import VNetOperations
from azure.cli.command_modules.network.mgmt_public_ip.lib \
    import PublicIpCreationClient as PublicIPClient
from azure.cli.command_modules.network.mgmt_public_ip.lib.operations import PublicIpOperations
from azure.cli.command_modules.network.mgmt_lb.lib import LbCreationClient as LBClient
from azure.cli.command_modules.network.mgmt_lb.lib.operations import LbOperations
from azure.cli.command_modules.network.mgmt_nic.lib import NicCreationClient as NicClient
from azure.cli.command_modules.network.mgmt_nic.lib.operations import NicOperations
from azure.cli.command_modules.network.mgmt_nsg.lib import NSGCreationClient as NSGClient
from azure.cli.command_modules.network.mgmt_nsg.lib.operations import NSGOperations

from azure.cli.commands import DeploymentOutputLongRunningOperation, cli_command

from .custom import \
    (update_vnet, update_subnet, create_subnet,
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
     list_network_resource_property, get_network_resource_property_entry,
     delete_network_resource_property_entry,
     set_nic)
from ._factory import _network_client_factory

# pylint: disable=line-too-long
# Application gateways
factory = lambda _: _network_client_factory().application_gateways
cli_command('network application-gateway delete', ApplicationGatewaysOperations.delete, factory)
cli_command('network application-gateway show', ApplicationGatewaysOperations.get, factory)
cli_command('network application-gateway list', ApplicationGatewaysOperations.list, factory)
cli_command('network application-gateway list-all', ApplicationGatewaysOperations.list_all, factory)
cli_command('network application-gateway start', ApplicationGatewaysOperations.start, factory)
cli_command('network application-gateway stop', ApplicationGatewaysOperations.stop, factory)

factory = lambda _: get_mgmt_service_client(AppGatewayClient).app_gateway
cli_command('network application-gateway create', AppGatewayOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network application-gateway create'))

# ExpressRouteCircuitAuthorizationsOperations
factory = lambda _: _network_client_factory().express_route_circuit_authorizations
cli_command('network express-route circuit-auth delete', ExpressRouteCircuitAuthorizationsOperations.delete, factory)
cli_command('network express-route circuit-auth show', ExpressRouteCircuitAuthorizationsOperations.get, factory)
cli_command('network express-route circuit-auth list', ExpressRouteCircuitAuthorizationsOperations.list, factory)

# ExpressRouteCircuitPeeringsOperations
factory = lambda _: _network_client_factory().express_route_circuit_peerings
cli_command('network express-route circuit-peering delete', ExpressRouteCircuitPeeringsOperations.delete, factory)
cli_command('network express-route circuit-peering show', ExpressRouteCircuitPeeringsOperations.get, factory)
cli_command('network express-route circuit-peering list', ExpressRouteCircuitPeeringsOperations.list, factory)

# ExpressRouteCircuitsOperations
factory = lambda _: _network_client_factory().express_route_circuits
cli_command('network express-route circuit delete', ExpressRouteCircuitsOperations.delete, factory)
cli_command('network express-route circuit show', ExpressRouteCircuitsOperations.get, factory)
cli_command('network express-route circuit get-stats', ExpressRouteCircuitsOperations.get_stats, factory)
cli_command('network express-route circuit list-arp', ExpressRouteCircuitsOperations.list_arp_table, factory)
cli_command('network express-route circuit list-routes', ExpressRouteCircuitsOperations.list_routes_table, factory)
cli_command('network express-route circuit list', ExpressRouteCircuitsOperations.list, factory)
cli_command('network express-route circuit list-all', ExpressRouteCircuitsOperations.list_all, factory)

# ExpressRouteServiceProvidersOperations
factory = lambda _: _network_client_factory().express_route_service_providers
cli_command('network express-route service-provider list', ExpressRouteServiceProvidersOperations.list, factory)

# LoadBalancersOperations
factory = lambda _: _network_client_factory().load_balancers
cli_command('network lb delete', LoadBalancersOperations.delete, factory)
cli_command('network lb show', LoadBalancersOperations.get, factory)
cli_command('network lb list', LoadBalancersOperations.list, factory)
cli_command('network lb list-all', LoadBalancersOperations.list_all, factory)

factory = lambda _: get_mgmt_service_client(LBClient).lb
cli_command('network lb create', LbOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network lb create'))

resource = 'load_balancers'
subresource = 'frontend_ip_configurations'
cli_command('network lb frontend-ip create', create_lb_frontend_ip_configuration)
cli_command('network lb frontend-ip set', set_lb_frontend_ip_configuration)
cli_command('network lb frontend-ip list', list_network_resource_property(resource, subresource))
cli_command('network lb frontend-ip show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb frontend-ip delete', delete_network_resource_property_entry(resource, subresource))

subresource = 'inbound_nat_rules'
cli_command('network lb inbound-nat-rule create', create_lb_inbound_nat_rule)
cli_command('network lb inbound-nat-rule set', set_lb_inbound_nat_rule)
cli_command('network lb inbound-nat-rule list', list_network_resource_property(resource, subresource))
cli_command('network lb inbound-nat-rule show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb inbound-nat-rule delete', delete_network_resource_property_entry(resource, subresource))

subresource = 'inbound_nat_pools'
cli_command('network lb inbound-nat-pool create', create_lb_inbound_nat_pool)
cli_command('network lb inbound-nat-pool set', set_lb_inbound_nat_pool)
cli_command('network lb inbound-nat-pool list', list_network_resource_property(resource, subresource))
cli_command('network lb inbound-nat-pool show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb inbound-nat-pool delete', delete_network_resource_property_entry(resource, subresource))

subresource = 'backend_address_pools'
cli_command('network lb address-pool create', create_lb_backend_address_pool)
cli_command('network lb address-pool list', list_network_resource_property(resource, subresource))
cli_command('network lb address-pool show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb address-pool delete', delete_network_resource_property_entry(resource, subresource))

subresource = 'load_balancing_rules'
cli_command('network lb rule create', create_lb_rule)
cli_command('network lb rule set', set_lb_rule)
cli_command('network lb rule list', list_network_resource_property(resource, subresource))
cli_command('network lb rule show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb rule delete', delete_network_resource_property_entry(resource, subresource))

subresource = 'probes'
cli_command('network lb probe create', create_lb_probe)
cli_command('network lb probe set', set_lb_probe)
cli_command('network lb probe list', list_network_resource_property(resource, subresource))
cli_command('network lb probe show', get_network_resource_property_entry(resource, subresource))
cli_command('network lb probe delete', delete_network_resource_property_entry(resource, subresource))

factory = lambda _: get_mgmt_service_client(NSGClient).nsg
cli_command('network nsg create', NSGOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nsg create'))

# LocalNetworkGatewaysOperations
factory = lambda _: _network_client_factory().local_network_gateways
cli_command('network local-gateway delete', LocalNetworkGatewaysOperations.delete, factory)
cli_command('network local-gateway show', LocalNetworkGatewaysOperations.get, factory)
cli_command('network local-gateway list', LocalNetworkGatewaysOperations.list, factory)

# NetworkInterfacesOperations
factory = lambda _: get_mgmt_service_client(NicClient).nic
cli_command('network nic create', NicOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network nic create'))

factory = lambda _: _network_client_factory().network_interfaces
cli_command('network nic delete', NetworkInterfacesOperations.delete, factory)
cli_command('network nic show', NetworkInterfacesOperations.get, factory)
cli_command('network nic list', NetworkInterfacesOperations.list, factory)
cli_command('network nic list-all', NetworkInterfacesOperations.list_all, factory)
cli_command('network nic set', set_nic)

# NetworkInterfacesOperations: scaleset
cli_command('network nic scale-set list-vm-nics', NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, factory)
cli_command('network nic scale-set list', NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, factory)
cli_command('network nic scale-set show', NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, factory)

resource = 'network_interfaces'
subresource = 'ip_configurations'
cli_command('network nic ip-config create', create_nic_ip_config)
cli_command('network nic ip-config set', set_nic_ip_config)
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
cli_command('network nsg list', NetworkSecurityGroupsOperations.list, factory)
cli_command('network nsg list-all', NetworkSecurityGroupsOperations.list_all, factory)

# PublicIPAddressesOperations
factory = lambda _: _network_client_factory().public_ip_addresses
cli_command('network public-ip delete', PublicIPAddressesOperations.delete, factory)
cli_command('network public-ip show', PublicIPAddressesOperations.get, factory)
cli_command('network public-ip list', PublicIPAddressesOperations.list, factory)
cli_command('network public-ip list-all', PublicIPAddressesOperations.list_all, factory)

factory = lambda _: get_mgmt_service_client(PublicIPClient).public_ip
cli_command('network public-ip create', PublicIpOperations.create_or_update, factory, transform=DeploymentOutputLongRunningOperation('Starting network public-ip create'))

# RouteTablesOperations
factory = lambda _: _network_client_factory().route_tables
cli_command('network route-table delete', RouteTablesOperations.delete, factory)
cli_command('network route-table show', RouteTablesOperations.get, factory)
cli_command('network route-table list', RouteTablesOperations.list, factory)
cli_command('network route-table list-all', RouteTablesOperations.list_all, factory)

# RoutesOperations
factory = lambda _: _network_client_factory().routes
cli_command('network route-operation delete', RoutesOperations.delete, factory)
cli_command('network route-operation show', RoutesOperations.get, factory)
cli_command('network route-operation list', RoutesOperations.list, factory)

# SecurityRulesOperations
factory = lambda _: _network_client_factory().security_rules
cli_command('network nsg rule delete', SecurityRulesOperations.delete, factory)
cli_command('network nsg rule show', SecurityRulesOperations.get, factory)
cli_command('network nsg rule list', SecurityRulesOperations.list, factory)
cli_command('network nsg rule create', create_nsg_rule)
cli_command('network nsg rule set', update_nsg_rule)

# SubnetsOperations
factory = lambda _: _network_client_factory().subnets
cli_command('network vnet subnet delete', SubnetsOperations.delete, factory)
cli_command('network vnet subnet show', SubnetsOperations.get, factory)
cli_command('network vnet subnet list', SubnetsOperations.list, factory)
cli_command('network vnet subnet create', create_subnet)
cli_command('network vnet subnet set', update_subnet)

# Usages operations
factory = lambda _: _network_client_factory().usages
cli_command('network list-usages', UsagesOperations.list, factory)

factory = lambda _: _network_client_factory().virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
cli_command('network vpn-connection delete', VirtualNetworkGatewayConnectionsOperations.delete, factory)
cli_command('network vpn-connection show', VirtualNetworkGatewayConnectionsOperations.get, factory)
cli_command('network vpn-connection list', VirtualNetworkGatewayConnectionsOperations.list, factory)
cli_command('network vpn-connection shared-key show', VirtualNetworkGatewayConnectionsOperations.get_shared_key, factory)
cli_command('network vpn-connection shared-key reset', VirtualNetworkGatewayConnectionsOperations.reset_shared_key, factory)
cli_command('network vpn-connection shared-key set', VirtualNetworkGatewayConnectionsOperations.set_shared_key, factory)

# VirtualNetworkGatewaysOperations
factory = lambda _: _network_client_factory().virtual_network_gateways
cli_command('network vpn-gateway delete', VirtualNetworkGatewaysOperations.delete, factory)
cli_command('network vpn-gateway show', VirtualNetworkGatewaysOperations.get, factory)
cli_command('network vpn-gateway list', VirtualNetworkGatewaysOperations.list, factory)

# VirtualNetworksOperations
factory = lambda _: _network_client_factory().virtual_networks
cli_command('network vnet delete', VirtualNetworksOperations.delete, factory)
cli_command('network vnet show', VirtualNetworksOperations.get, factory)
cli_command('network vnet list', VirtualNetworksOperations.list, factory)
cli_command('network vnet list-all', VirtualNetworksOperations.list_all, factory)

cli_command('network vnet set', update_vnet)

factory = lambda _: get_mgmt_service_client(VNetClient).vnet
cli_command('network vnet create', VNetOperations.create, factory, transform=DeploymentOutputLongRunningOperation('Starting network vnet create'))
