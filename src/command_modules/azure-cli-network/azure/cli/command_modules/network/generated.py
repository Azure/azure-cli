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

from azure.cli.commands import CommandTable
from azure.cli.commands.command_types import cli_command
from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.command_modules.network.mgmt_vnet.lib \
    import (ResourceManagementClient as VNetClient,
            ResourceManagementClientConfiguration as VNetClientConfig)
from azure.cli.command_modules.network.mgmt_vnet.lib.operations import VNetOperations
from azure.cli.command_modules.network.mgmt_public_ip.lib \
    import (PublicIPCreationClient as PublicIPClient,
            PublicIPCreationClientConfiguration as PublicIPClientConfig)
from azure.cli.command_modules.network.mgmt_public_ip.lib.operations import PublicIPOperations
from azure.cli.command_modules.network.mgmt_lb.lib import (LBCreationClient as LBClient,
                                                           LBCreationClientConfiguration
                                                           as LBClientConfig)
from azure.cli.command_modules.network.mgmt_lb.lib.operations import LBOperations
from azure.cli.command_modules.network._params import _network_client_factory
from .custom import create_update_subnet

command_table = CommandTable()

# pylint: disable=line-too-long
# Application gateways
factory = lambda _: _network_client_factory().application_gateways
cli_command(command_table, 'network application-gateway delete', ApplicationGatewaysOperations.delete, factory)
cli_command(command_table, 'network application-gateway show', ApplicationGatewaysOperations.get, factory)
cli_command(command_table, 'network application-gateway list', ApplicationGatewaysOperations.list, factory)
cli_command(command_table, 'network application-gateway list-all', ApplicationGatewaysOperations.list_all, factory)
cli_command(command_table, 'network application-gateway start', ApplicationGatewaysOperations.start, factory)
cli_command(command_table, 'network application-gateway stop', ApplicationGatewaysOperations.stop, factory)

# ExpressRouteCircuitAuthorizationsOperations
factory = lambda _: _network_client_factory().express_route_circuit_authorizations
cli_command(command_table, 'network express-route circuit-auth delete', ExpressRouteCircuitAuthorizationsOperations.delete, factory)
cli_command(command_table, 'network express-route circuit-auth show', ExpressRouteCircuitAuthorizationsOperations.get, factory)
cli_command(command_table, 'network express-route circuit-auth list', ExpressRouteCircuitAuthorizationsOperations.list, factory)

# ExpressRouteCircuitPeeringsOperations
factory = lambda _: _network_client_factory().express_route_circuit_peerings
cli_command(command_table, 'network express-route circuit-peering delete', ExpressRouteCircuitPeeringsOperations.delete, factory)
cli_command(command_table, 'network express-route circuit-peering show', ExpressRouteCircuitPeeringsOperations.get, factory)
cli_command(command_table, 'network express-route circuit-peering list', ExpressRouteCircuitPeeringsOperations.list, factory)

# ExpressRouteCircuitsOperations
factory = lambda _: _network_client_factory().express_route_circuits
cli_command(command_table, 'network express-route circuit delete', ExpressRouteCircuitsOperations.delete, factory)
cli_command(command_table, 'network express-route circuit show', ExpressRouteCircuitsOperations.get, factory)
cli_command(command_table, 'network express-route circuit get-stats', ExpressRouteCircuitsOperations.get_stats, factory)
cli_command(command_table, 'network express-route circuit list-arp', ExpressRouteCircuitsOperations.list_arp_table, factory)
cli_command(command_table, 'network express-route circuit list-routes', ExpressRouteCircuitsOperations.list_routes_table, factory)
cli_command(command_table, 'network express-route circuit list', ExpressRouteCircuitsOperations.list, factory)
cli_command(command_table, 'network express-route circuit list-all', ExpressRouteCircuitsOperations.list_all, factory)

# ExpressRouteServiceProvidersOperations
factory = lambda _: _network_client_factory().express_route_service_providers
cli_command(command_table, 'network express-route service-provider list', ExpressRouteServiceProvidersOperations.list, factory)

# LoadBalancersOperations
factory = lambda _: _network_client_factory().load_balancers
cli_command(command_table, 'network lb delete', LoadBalancersOperations.delete, factory)
cli_command(command_table, 'network lb show', LoadBalancersOperations.get, factory)
cli_command(command_table, 'network lb list', LoadBalancersOperations.list, factory)
cli_command(command_table, 'network lb list-all', LoadBalancersOperations.list_all, factory)

factory = lambda **_: get_mgmt_service_client(LBClient, LBClientConfig).lb
cli_command(command_table, 'network lb create', LBOperations.create_or_update, 'LoadBalancer', factory)

# LocalNetworkGatewaysOperations
factory = lambda _: _network_client_factory().local_network_gateways
cli_command(command_table, 'network local-gateway delete', LocalNetworkGatewaysOperations.delete, factory)
cli_command(command_table, 'network local-gateway show', LocalNetworkGatewaysOperations.get, factory)
cli_command(command_table, 'network local-gateway list', LocalNetworkGatewaysOperations.list, factory)

# NetworkInterfacesOperations
factory = lambda _: _network_client_factory().network_interfaces
cli_command(command_table, 'network nic delete', NetworkInterfacesOperations.delete, factory)
cli_command(command_table, 'network nic show', NetworkInterfacesOperations.get, factory)
cli_command(command_table, 'network nic list', NetworkInterfacesOperations.list, factory)
cli_command(command_table, 'network nic list-all', NetworkInterfacesOperations.list_all, factory)

# NetworkInterfacesOperations: scaleset
cli_command(command_table, 'network nic scale-set list-vm-nics', NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, factory)
cli_command(command_table, 'network nic scale-set list', NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, factory)
cli_command(command_table, 'network nic scale-set show', NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, factory)

# NetworkSecurityGroupsOperations
factory = lambda _: _network_client_factory().network_security_groups
cli_command(command_table, 'network nsg delete', NetworkSecurityGroupsOperations.delete, factory)
cli_command(command_table, 'network nsg show', NetworkSecurityGroupsOperations.get, factory)
cli_command(command_table, 'network nsg list', NetworkSecurityGroupsOperations.list, factory)
cli_command(command_table, 'network nsg list-all', NetworkSecurityGroupsOperations.list_all, factory)

# PublicIPAddressesOperations
factory = lambda _: _network_client_factory().public_ip_addresses
cli_command(command_table, 'network public-ip delete', PublicIPAddressesOperations.delete, factory)
cli_command(command_table, 'network public-ip show', PublicIPAddressesOperations.get, factory)
cli_command(command_table, 'network public-ip list', PublicIPAddressesOperations.list, factory)
cli_command(command_table, 'network public-ip list-all', PublicIPAddressesOperations.list_all, factory)

factory = lambda **_: get_mgmt_service_client(PublicIPClient, PublicIPClientConfig).public_ip
cli_command(command_table, 'network public-ip create', PublicIPOperations.create_or_update, factory)

# RouteTablesOperations
factory = lambda _: _network_client_factory().route_tables
cli_command(command_table, 'network route-table delete', RouteTablesOperations.delete, factory)
cli_command(command_table, 'network route-table show', RouteTablesOperations.get, factory)
cli_command(command_table, 'network route-table list', RouteTablesOperations.list, factory)
cli_command(command_table, 'network route-table list-all', RouteTablesOperations.list_all, factory)

# RoutesOperations
factory = lambda _: _network_client_factory().routes
cli_command(command_table, 'network route-operation delete', RoutesOperations.delete, factory)
cli_command(command_table, 'network route-operation show', RoutesOperations.get, factory)
cli_command(command_table, 'network route-operation list', RoutesOperations.list, factory)

# SecurityRulesOperations
factory = lambda _: _network_client_factory().security_rules
cli_command(command_table, 'network nsg-rule delete', SecurityRulesOperations.delete, factory)
cli_command(command_table, 'network nsg-rule show', SecurityRulesOperations.get, factory)
cli_command(command_table, 'network nsg-rule list', SecurityRulesOperations.list, factory)

# SubnetsOperations
factory = lambda _: _network_client_factory().subnets
cli_command(command_table, 'network vnet subnet delete', SubnetsOperations.delete, factory)
cli_command(command_table, 'network vnet subnet show', SubnetsOperations.get, factory)
cli_command(command_table, 'network vnet subnet list', SubnetsOperations.list, factory)
cli_command(command_table, 'network vnet subnet create', create_update_subnet)

# Usages operations
factory = lambda _: _network_client_factory().usages
cli_command(command_table, 'network list-usages', UsagesOperations.list, factory)

factory = lambda _: _network_client_factory().virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
cli_command(command_table, 'network vpn-connection delete', VirtualNetworkGatewayConnectionsOperations.delete, factory)
cli_command(command_table, 'network vpn-connection show', VirtualNetworkGatewayConnectionsOperations.get, factory)
cli_command(command_table, 'network vpn-connection list', VirtualNetworkGatewayConnectionsOperations.list, factory)
cli_command(command_table, 'network vpn-connection shared-key show', VirtualNetworkGatewayConnectionsOperations.get_shared_key, factory)
cli_command(command_table, 'network vpn-connection shared-key reset', VirtualNetworkGatewayConnectionsOperations.reset_shared_key, factory)
cli_command(command_table, 'network vpn-connection shared-key set', VirtualNetworkGatewayConnectionsOperations.set_shared_key, factory)

# VirtualNetworkGatewaysOperations
factory = lambda _: _network_client_factory().virtual_network_gateways
cli_command(command_table, 'network vpn-gateway delete', VirtualNetworkGatewaysOperations.delete, factory)
cli_command(command_table, 'network vpn-gateway show', VirtualNetworkGatewaysOperations.get, factory)
cli_command(command_table, 'network vpn-gateway list', VirtualNetworkGatewaysOperations.list, factory)
cli_command(command_table, 'network vpn-gateway reset', VirtualNetworkGatewaysOperations.reset, factory)

# VirtualNetworksOperations
factory = lambda _: _network_client_factory().virtual_networks
cli_command(command_table, 'network vnet delete', VirtualNetworksOperations.delete, factory)
cli_command(command_table, 'network vnet show', VirtualNetworksOperations.get, factory)
cli_command(command_table, 'network vnet list', VirtualNetworksOperations.list, factory)
cli_command(command_table, 'network vnet list-all', VirtualNetworksOperations.list_all, factory)

factory = lambda **_: get_mgmt_service_client(VNetClient, VNetClientConfig).vnet
cli_command(command_table, 'network vnet create', VNetOperations.create, factory)
