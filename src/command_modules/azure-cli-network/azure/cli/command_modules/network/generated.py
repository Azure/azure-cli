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

from azure.cli.commands import CommandTable, LongRunningOperation
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
cli_command(command_table, 'network application-gateway delete', ApplicationGatewaysOperations.delete, LongRunningOperation('Deleting application gateway'), factory)
cli_command(command_table, 'network application-gateway show', ApplicationGatewaysOperations.get, 'ApplicationGateway', factory)
cli_command(command_table, 'network application-gateway list', ApplicationGatewaysOperations.list, '[ApplicationGateway]', factory)
cli_command(command_table, 'network application-gateway list-all', ApplicationGatewaysOperations.list_all, '[ApplicationGateway]', factory)
cli_command(command_table, 'network application-gateway start', ApplicationGatewaysOperations.start, LongRunningOperation('Starting application gateway'), factory)
cli_command(command_table, 'network application-gateway stop', ApplicationGatewaysOperations.stop, LongRunningOperation('Stopping application gateway'), factory)

# ExpressRouteCircuitAuthorizationsOperations
factory = lambda _: _network_client_factory().express_route_circuit_authorizations
cli_command(command_table, 'network express-route circuit-auth delete', ExpressRouteCircuitAuthorizationsOperations.delete, LongRunningOperation('Deleting express route circuit'), factory)
cli_command(command_table, 'network express-route circuit-auth show', ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization', factory)
cli_command(command_table, 'network express-route circuit-auth list', ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]', factory)

# ExpressRouteCircuitPeeringsOperations
factory = lambda _: _network_client_factory().express_route_circuit_peerings
cli_command(command_table, 'network express-route circuit-peering delete', ExpressRouteCircuitPeeringsOperations.delete, LongRunningOperation('Deleting express route circuit peering'), factory)
cli_command(command_table, 'network express-route circuit-peering show', ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering', factory)
cli_command(command_table, 'network express-route circuit-peering list', ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]', factory)

# ExpressRouteCircuitsOperations
factory = lambda _: _network_client_factory().express_route_circuits
cli_command(command_table, 'network express-route circuit delete', ExpressRouteCircuitsOperations.delete, LongRunningOperation('Deleting express route circuit'), factory)
cli_command(command_table, 'network express-route circuit show', ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit', factory)
cli_command(command_table, 'network express-route circuit get-stats', ExpressRouteCircuitsOperations.get_stats, 'Result', factory)
cli_command(command_table, 'network express-route circuit list-arp', ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]', factory)
cli_command(command_table, 'network express-route circuit list-routes', ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]', factory)
cli_command(command_table, 'network express-route circuit list', ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]', factory)
cli_command(command_table, 'network express-route circuit list-all', ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]', factory)

# ExpressRouteServiceProvidersOperations
factory = lambda _: _network_client_factory().express_route_service_providers
cli_command(command_table, 'network express-route service-provider list', ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]', factory)

# LoadBalancersOperations
factory = lambda _: _network_client_factory().load_balancers
cli_command(command_table, 'network lb delete', LoadBalancersOperations.delete, LongRunningOperation('Deleting load balancer'), factory)
cli_command(command_table, 'network lb show', LoadBalancersOperations.get, 'LoadBalancer', factory)
cli_command(command_table, 'network lb list', LoadBalancersOperations.list, '[LoadBalancer]', factory)
cli_command(command_table, 'network lb list-all', LoadBalancersOperations.list_all, '[LoadBalancer]', factory)

factory = lambda **_: get_mgmt_service_client(LBClient, LBClientConfig).lb
cli_command(command_table, 'network lb create', LBOperations.create_or_update, 'LoadBalancer', factory)

# LocalNetworkGatewaysOperations
factory = lambda _: _network_client_factory().local_network_gateways
cli_command(command_table, 'network local-gateway delete', LocalNetworkGatewaysOperations.delete, LongRunningOperation('Deleting local gateway'), factory)
cli_command(command_table, 'network local-gateway show', LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway', factory)
cli_command(command_table, 'network local-gateway list', LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]', factory)

# NetworkInterfacesOperations
factory = lambda _: _network_client_factory().network_interfaces
cli_command(command_table, 'network nic delete', NetworkInterfacesOperations.delete, LongRunningOperation('Deleting NIC'), factory)
cli_command(command_table, 'network nic show', NetworkInterfacesOperations.get, 'NetworkInterface', factory)
cli_command(command_table, 'network nic list', NetworkInterfacesOperations.list, '[NetworkInterface]', factory)
cli_command(command_table, 'network nic list-all', NetworkInterfacesOperations.list_all, '[NetworkInterface]', factory)

# NetworkInterfacesOperations: scaleset
cli_command(command_table, 'network nic scale-set list-vm-nics', NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]', factory)
cli_command(command_table, 'network nic scale-set list', NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]', factory)
cli_command(command_table, 'network nic scale-set show', NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface', factory)

# NetworkSecurityGroupsOperations
factory = lambda _: _network_client_factory().network_security_groups
cli_command(command_table, 'network nsg delete', NetworkSecurityGroupsOperations.delete, LongRunningOperation('Deleting NSG'), factory)
cli_command(command_table, 'network nsg show', NetworkSecurityGroupsOperations.get, 'NetworkSecurityGroup', factory)
cli_command(command_table, 'network nsg list', NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]', factory)
cli_command(command_table, 'network nsg list-all', NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]', factory)

# PublicIPAddressesOperations
factory = lambda _: _network_client_factory().public_ip_addresses
cli_command(command_table, 'network public-ip delete', PublicIPAddressesOperations.delete, LongRunningOperation('Deleting public IP'), factory)
cli_command(command_table, 'network public-ip show', PublicIPAddressesOperations.get, 'PublicIPAddress', factory)
cli_command(command_table, 'network public-ip list', PublicIPAddressesOperations.list, '[PublicIPAddress]', factory)
cli_command(command_table, 'network public-ip list-all', PublicIPAddressesOperations.list_all, '[PublicIPAddress]', factory)

factory = lambda **_: get_mgmt_service_client(PublicIPClient, PublicIPClientConfig).public_ip
cli_command(command_table, 'network public-ip create', PublicIPOperations.create_or_update, LongRunningOperation('Creating public IP'), factory)

# RouteTablesOperations
factory = lambda _: _network_client_factory().route_tables
cli_command(command_table, 'network route-table delete', RouteTablesOperations.delete, LongRunningOperation('Deleting route table'), factory)
cli_command(command_table, 'network route-table show', RouteTablesOperations.get, 'RouteTable', factory)
cli_command(command_table, 'network route-table list', RouteTablesOperations.list, '[RouteTable]', factory)
cli_command(command_table, 'network route-table list-all', RouteTablesOperations.list_all, '[RouteTable]', factory)

# RoutesOperations
factory = lambda _: _network_client_factory().routes
cli_command(command_table, 'network route-operation delete', RoutesOperations.delete, LongRunningOperation('Deleting route operation'), factory)
cli_command(command_table, 'network route-operation show', RoutesOperations.get, 'Route', factory)
cli_command(command_table, 'network route-operation list', RoutesOperations.list, '[Route]', factory)

# SecurityRulesOperations
factory = lambda _: _network_client_factory().security_rules
cli_command(command_table, 'network nsg-rule delete', SecurityRulesOperations.delete, None, factory)
cli_command(command_table, 'network nsg-rule show', SecurityRulesOperations.get, 'SecurityRule', factory)
cli_command(command_table, 'network nsg-rule list', SecurityRulesOperations.list, '[SecurityRule]', factory)

# SubnetsOperations
factory = lambda _: _network_client_factory().subnets
cli_command(command_table, 'network vnet subnet delete', SubnetsOperations.delete, LongRunningOperation('Deleting NSG rule'), factory)
cli_command(command_table, 'network vnet subnet show', SubnetsOperations.get, 'Subnet', factory)
cli_command(command_table, 'network vnet subnet list', SubnetsOperations.list, '[Subnet]', factory)
cli_command(command_table, 'network vnet subnet create', create_update_subnet, LongRunningOperation('Creating VNET subnet'))

# Usages operations
factory = lambda _: _network_client_factory().usages
cli_command(command_table, 'network list-usages', UsagesOperations.list, '[Usage]', factory)

factory = lambda _: _network_client_factory().virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
cli_command(command_table, 'network vpn-connection delete', VirtualNetworkGatewayConnectionsOperations.delete, LongRunningOperation('Deleting VPN connection'), factory)
cli_command(command_table, 'network vpn-connection show', VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection', factory)
cli_command(command_table, 'network vpn-connection list', VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]', factory)
cli_command(command_table, 'network vpn-connection shared-key show', VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult', factory)
cli_command(command_table, 'network vpn-connection shared-key reset', VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey', factory)
cli_command(command_table, 'network vpn-connection shared-key set', VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey', factory)

# VirtualNetworkGatewaysOperations
factory = lambda _: _network_client_factory().virtual_network_gateways
cli_command(command_table, 'network vpn-gateway delete', VirtualNetworkGatewaysOperations.delete, LongRunningOperation('Deleting VPN gateway'), factory)
cli_command(command_table, 'network vpn-gateway show', VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway', factory)
cli_command(command_table, 'network vpn-gateway list', VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]', factory)
cli_command(command_table, 'network vpn-gateway reset', VirtualNetworkGatewaysOperations.reset, LongRunningOperation('Resetting VPN gateway'), factory)

# VirtualNetworksOperations
factory = lambda _: _network_client_factory().virtual_networks
cli_command(command_table, 'network vnet delete', VirtualNetworksOperations.delete, LongRunningOperation('Deleting VNET'), factory)
cli_command(command_table, 'network vnet show', VirtualNetworksOperations.get, 'VirtualNetwork', factory)
cli_command(command_table, 'network vnet list', VirtualNetworksOperations.list, '[VirtualNetwork]', factory)
cli_command(command_table, 'network vnet list-all', VirtualNetworksOperations.list_all, '[VirtualNetwork]', factory)

factory = lambda **_: get_mgmt_service_client(VNetClient, VNetClientConfig).vnet
cli_command(command_table, 'network vnet create', VNetOperations.create, LongRunningOperation('Creating VNET'), factory)


