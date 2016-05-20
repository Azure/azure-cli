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
from azure.cli.commands._auto_command import build_operation, CommandDefinition, sdk_cli_command
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L
from .custom import create_update_subnet

command_table = CommandTable()

# pylint: disable=line-too-long
# Application gateways
factory = lambda **kwargs: _network_client_factory(**kwargs).application_gateways
sdk_cli_command('network application-gateway delete', factory, ApplicationGatewaysOperations.delete, None, command_table)
sdk_cli_command('network application-gateway show', factory, ApplicationGatewaysOperations.get, 'ApplicationGateway', command_table)
sdk_cli_command('network application-gateway list', factory, ApplicationGatewaysOperations.list, '[ApplicationGateway]', command_table)
sdk_cli_command('network application-gateway list-all', factory, ApplicationGatewaysOperations.list_all, '[ApplicationGateway]', command_table)
sdk_cli_command('network application-gateway start', factory, ApplicationGatewaysOperations.start, None, command_table)
sdk_cli_command('network application-gateway stop', factory, ApplicationGatewaysOperations.stop, None, command_table)

# ExpressRouteCircuitAuthorizationsOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).express_route_circuit_authorizations
sdk_cli_command('network express-route circuit-auth delete', factory, ExpressRouteCircuitAuthorizationsOperations.delete, None, command_table)
sdk_cli_command('network express-route circuit-auth show', factory, ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization', command_table)
sdk_cli_command('network express-route circuit-auth list', factory, ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]', command_table)

# ExpressRouteCircuitPeeringsOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).express_route_circuit_peerings
sdk_cli_command('network express-route circuit-peering delete', factory, ExpressRouteCircuitPeeringsOperations.delete, None, command_table)
sdk_cli_command('network express-route circuit-peering show', factory, ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering', command_table)
sdk_cli_command('network express-route circuit-peering list', factory, ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]', command_table)

# ExpressRouteCircuitsOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).express_route_circuits
sdk_cli_command('network express-route circuit delete', factory, ExpressRouteCircuitsOperations.delete, None, command_table)
sdk_cli_command('network express-route circuit show', factory, ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit', command_table)
sdk_cli_command('network express-route circuit list-arp', factory, ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]', command_table)
sdk_cli_command('network express-route circuit list-routes', factory, ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]', command_table)
sdk_cli_command('network express-route circuit list', factory, ExpressRouteCircuitsOperations.delete, '[ExpressRouteCircuit]', command_table)
sdk_cli_command('network express-route circuit list-all', factory, ExpressRouteCircuitsOperations.delete, '[ExpressRouteCircuit]', command_table)

# ExpressRouteServiceProvidersOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).load_balancers
sdk_cli_command('network express-route service-provider list', factory, ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]', command_table)

# LoadBalancersOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).load_balancers
sdk_cli_command('network lb delete', factory, LoadBalancersOperations.delete, None, command_table)
sdk_cli_command('network lb show', factory, LoadBalancersOperations.get, 'LoadBalancer', command_table)
sdk_cli_command('network lb list', factory, LoadBalancersOperations.list_all, '[LoadBalancer]', command_table)
sdk_cli_command('network lb list-all', factory, LoadBalancersOperations.delete, '[LoadBalancer]', command_table)

factory = lambda **_: get_mgmt_service_client(LBClient, LBClientConfig).lb
sdk_cli_command('network lb create', factory, LBOperations.create_or_update, 'LoadBalancer', command_table)

# LocalNetworkGatewaysOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).local_network_gateways
sdk_cli_command('network local-gateway delete', factory, LocalNetworkGatewaysOperations.delete, None, command_table)
sdk_cli_command('network local-gateway show', factory, LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway', command_table)
sdk_cli_command('network local-gateway list', factory, LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]', command_table)

# NetworkInterfacesOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).network_interfaces
sdk_cli_command('network nic delete', factory, NetworkInterfacesOperations.delete, None, command_table)
sdk_cli_command('network nic show', factory, NetworkInterfacesOperations.get, 'NetworkInterface', command_table)
sdk_cli_command('network nic list', factory, NetworkInterfacesOperations.list, '[NetworkInterface]', command_table)
sdk_cli_command('network nic list-all', factory, NetworkInterfacesOperations.list_all, '[NetworkInterface]', command_table)

# NetworkInterfacesOperations: scaleset
sdk_cli_command('network nic scale-set list-vm-nics', factory, NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]', command_table)
sdk_cli_command('network nic scale-set list', factory, NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]', command_table)
sdk_cli_command('network nic scale-set show', factory, NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface', command_table)

# NetworkSecurityGroupsOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).network_security_groups
sdk_cli_command('network nsg delete', factory, NetworkSecurityGroupsOperations.delete, None, command_table)
sdk_cli_command('network nsg show', factory, NetworkSecurityGroupsOperations.get, 'NetworkSecurityGroup', command_table)
sdk_cli_command('network nsg list', factory, NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]', command_table)
sdk_cli_command('network nsg list-all', factory, NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]', command_table)

# PublicIPAddressesOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).public_ip_addresses
sdk_cli_command('network public-ip delete', factory, PublicIPAddressesOperations.delete, None, command_table)
sdk_cli_command('network public-ip show', factory, PublicIPAddressesOperations.get, 'PublicIPAddress', command_table)
sdk_cli_command('network public-ip list', factory, PublicIPAddressesOperations.list, '[PublicIPAddress]', command_table)
sdk_cli_command('network public-ip list-all', factory, PublicIPAddressesOperations.list_all, '[PublicIPAddress]', command_table)

factory = lambda **_: get_mgmt_service_client(PublicIPClient, PublicIPClientConfig).public_ip
sdk_cli_command('network public-ip create', factory, PublicIPOperations.create_or_update, 'PublicIPAddress', command_table)

# RouteTablesOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).route_tables
sdk_cli_command('network route-table delete', factory, RouteTablesOperations.delete, None, command_table)
sdk_cli_command('network route-table show', factory, RouteTablesOperations.get, 'RouteTable', command_table)
sdk_cli_command('network route-table list', factory, RouteTablesOperations.list, '[RouteTable]', command_table)
sdk_cli_command('network route-table list-all', factory, RouteTablesOperations.list_all, '[RouteTable]', command_table)


# RoutesOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).routes
sdk_cli_command('network route-operation delete', factory, RoutesOperations.delete, None, command_table)
sdk_cli_command('network route-operation show', factory, RoutesOperations.get, 'Route', command_table)
sdk_cli_command('network route-operation list', factory, RoutesOperations.delete, '[Route]', command_table)

# SecurityRulesOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).security_rules
sdk_cli_command('network nsg-rule delete', factory, SecurityRulesOperations.delete, None, command_table)
sdk_cli_command('network nsg-rule show', factory, SecurityRulesOperations.get, 'SecurityRule', command_table)
sdk_cli_command('network nsg-rule list', factory, SecurityRulesOperations.list, '[SecurityRule]', command_table)

# SubnetsOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).subnets
sdk_cli_command('network vnet subnet delete', factory, SubnetsOperations.delete, None, command_table)
sdk_cli_command('network vnet subnet show', factory, SubnetsOperations.get, 'Subnet', command_table)
sdk_cli_command('network vnet subnet list', factory, SubnetsOperations.list, '[Subnet]', command_table)
sdk_cli_command('network vnet subnet create', None, create_update_subnet, 'Object', command_table)

# Usages operations
factory = lambda **kwargs: _network_client_factory(**kwargs).usages
sdk_cli_command('network list-usages', factory, UsagesOperations.list, '[Usage]', command_table)

factory = lambda **kwargs: _network_client_factory(**kwargs).virtual_network_gateway_connections
# VirtualNetworkGatewayConnectionsOperations
sdk_cli_command('network vpn-connection delete', factory, VirtualNetworkGatewayConnectionsOperations.delete, None, command_table)
sdk_cli_command('network vpn-connection show', factory, VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection', command_table)
sdk_cli_command('network vpn-connection list', factory, VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]', command_table)
sdk_cli_command('network vpn-connection shared-key show', factory, VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult', command_table)
sdk_cli_command('network vpn-connection shared-key reset', factory, VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey', command_table)
sdk_cli_command('network vpn-connection shared-key set', factory, VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey', command_table)

# VirtualNetworkGatewaysOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).virtual_network_gateways
sdk_cli_command('network vpn-gateway delete', factory, VirtualNetworkGatewaysOperations.delete, None, command_table)
sdk_cli_command('network vpn-gateway show', factory, VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway', command_table)
sdk_cli_command('network vpn-gateway list', factory, VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]', command_table)
sdk_cli_command('network vpn-gateway reset', factory, VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway', command_table)

# VirtualNetworksOperations
factory = lambda **kwargs: _network_client_factory(**kwargs).virtual_networks
sdk_cli_command('network vnet delete', factory, VirtualNetworksOperations.delete, None, command_table)
sdk_cli_command('network vnet show', factory, VirtualNetworksOperations.get, 'VirtualNetwork', command_table)
sdk_cli_command('network vnet list', factory, VirtualNetworksOperations.list, '[VirtualNetwork]', command_table)
sdk_cli_command('network vnet list-all', factory, VirtualNetworksOperations.list_all, '[VirtualNetwork]', command_table)

factory = lambda **_: get_mgmt_service_client(VNetClient, VNetClientConfig).vnet
sdk_cli_command('network vnet create', factory, VNetOperations.create, 'object', command_table)


