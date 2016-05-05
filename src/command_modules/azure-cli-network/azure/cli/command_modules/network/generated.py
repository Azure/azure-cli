from azure.mgmt.network.operations import (ApplicationGatewaysOperations,
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
from azure.cli.command_modules.network.mgmt.lib import (ResourceManagementClient as VNetClient,
                                                        ResourceManagementClientConfiguration
                                                        as VNetClientConfig)
from azure.cli.command_modules.network.mgmt.lib.operations import VNetOperations
from azure.cli.command_modules.network.custom import ConvenienceNetworkCommands
from azure.cli.command_modules.network._params import VNET_SPECIFIC_PARAMS, _network_client_factory
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation
from azure.cli._locale import L

command_table = CommandTable()

_VNET_PARAM_NAME = '--vnet-name'

# pylint: disable=line-too-long
# Application gateways
build_operation(
    'network application-gateway', 'application_gateways', _network_client_factory,
    [
        AutoCommandDefinition(ApplicationGatewaysOperations.delete, LongRunningOperation(L('Deleting application gateway'), L('Application gateway deleted'))),
        AutoCommandDefinition(ApplicationGatewaysOperations.get, 'ApplicationGateway', command_alias='show'),
        AutoCommandDefinition(ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
        AutoCommandDefinition(ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
        AutoCommandDefinition(ApplicationGatewaysOperations.start, LongRunningOperation(L('Starting application gateway'), L('Application gateway started'))),
        AutoCommandDefinition(ApplicationGatewaysOperations.stop, LongRunningOperation(L('Stopping application gateway'), L('Application gateway stopped'))),
    ],
    command_table,
    {
        'application_gateway_name': {'name': '--name -n'}
    })

# ExpressRouteCircuitAuthorizationsOperations
build_operation(
    'network express-route circuit-auth', 'express_route_circuit_authorizations', _network_client_factory,
    [
        AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.delete, LongRunningOperation(L('Deleting express route authorization'), L('Express route authorization deleted'))),
        AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization', command_alias='show'),
        AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
    ],
    command_table,
    {
        'authorization_name': {'name': '--name -n'}
    })

# ExpressRouteCircuitPeeringsOperations
build_operation(
    'network express-route circuit-peering', 'express_route_circuit_peerings', _network_client_factory,
    [
        AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.delete, LongRunningOperation(L('Deleting express route circuit peering'), L('Express route circuit peering deleted'))),
        AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering', command_alias='show'),
        AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
    ],
    command_table,
    {
        'peering_name': {'name': '--name -n'}
    })

# ExpressRouteCircuitsOperations
build_operation(
    'network express-route circuit', 'express_route_circuits', _network_client_factory,
    [
        AutoCommandDefinition(ExpressRouteCircuitsOperations.delete, LongRunningOperation(L('Deleting express route circuit'), L('Express route circuit deleted'))),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit', command_alias='show'),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]', 'list-arp'),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]', 'list-routes'),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.list_stats, '[ExpressRouteCircuitStats]'),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]'),
        AutoCommandDefinition(ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]'),
    ],
    command_table,
    {
        'circuit_name': {'name': '--name -n'}
    })

# ExpressRouteServiceProvidersOperations
build_operation(
    'network express-route service-provider', 'express_route_service_providers', _network_client_factory,
    [
        AutoCommandDefinition(ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
    ],
    command_table)

# LoadBalancersOperations
build_operation(
    'network lb', 'load_balancers', _network_client_factory,
    [
        AutoCommandDefinition(LoadBalancersOperations.delete, LongRunningOperation(L('Deleting load balancer'), L('Load balancer deleted'))),
        AutoCommandDefinition(LoadBalancersOperations.get, 'LoadBalancer', command_alias='show'),
        AutoCommandDefinition(LoadBalancersOperations.list_all, '[LoadBalancer]'),
        AutoCommandDefinition(LoadBalancersOperations.list, '[LoadBalancer]'),
    ],
    command_table,
    {
        'load_balancer_name': {'name': '--name -n'}
    })

# LocalNetworkGatewaysOperations
build_operation(
    'network local-gateway', 'local_network_gateways', _network_client_factory,
    [
        AutoCommandDefinition(LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway', command_alias='show'),
        AutoCommandDefinition(LocalNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting local network gateway'), L('Local network gateway deleted'))),
        AutoCommandDefinition(LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
    ],
    command_table,
    {
        'local_network_gateway_name': {'name': '--name -n'}
    })


# NetworkInterfacesOperations
build_operation(
    'network nic', 'network_interfaces', _network_client_factory,
    [
        AutoCommandDefinition(NetworkInterfacesOperations.delete, LongRunningOperation(L('Deleting network interface'), L('Network interface deleted'))),
        AutoCommandDefinition(NetworkInterfacesOperations.get, 'NetworkInterface', command_alias='show'),
        AutoCommandDefinition(NetworkInterfacesOperations.list_all, '[NetworkInterface]'),
        AutoCommandDefinition(NetworkInterfacesOperations.list, '[NetworkInterface]'),
    ],
    command_table,
    {
        'network_interface_name': {'name': '--name -n'}
    })

# NetworkInterfacesOperations: scaleset
build_operation(
    'network nic scale-set', 'network_interfaces', _network_client_factory,
    [
        AutoCommandDefinition(NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]', command_alias='list-vm-nics'),
        AutoCommandDefinition(NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]', command_alias='list'),
        AutoCommandDefinition(NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface', command_alias='show'),
    ],
    command_table,
    {
        'virtual_machine_scale_set_name': {'name': '--vm-scale-set'},
        'network_interface_name': {'name': '--name -n'},
        'virtualmachine_index': {'name': '--vm-index'}
    })

# NetworkSecurityGroupsOperations
build_operation(
    'network nsg', 'network_security_groups', _network_client_factory,
    [
        AutoCommandDefinition(NetworkSecurityGroupsOperations.delete, LongRunningOperation(L('Deleting network security group'), L('Network security group deleted'))),
        AutoCommandDefinition(NetworkSecurityGroupsOperations.get, 'NetworkSecurityGroup', command_alias='show'),
        AutoCommandDefinition(NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]'),
        AutoCommandDefinition(NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]'),
    ],
    command_table,
    {
        'network_security_group_name': {'name': '--name -n'}
    })

# PublicIPAddressesOperations
build_operation(
    'network public-ip', 'public_ip_addresses', _network_client_factory,
    [
        AutoCommandDefinition(PublicIPAddressesOperations.delete, LongRunningOperation(L('Deleting public IP address'), L('Public IP address deleted'))),
        AutoCommandDefinition(PublicIPAddressesOperations.get, 'PublicIPAddress', command_alias='show'),
        AutoCommandDefinition(PublicIPAddressesOperations.list_all, '[PublicIPAddress]'),
        AutoCommandDefinition(PublicIPAddressesOperations.list, '[PublicIPAddress]'),
    ],
    command_table,
    {
        'public_ip_address_name': {'name': '--name -n'}
    })

# RouteTablesOperations
build_operation(
    'network route-table', 'route_tables', _network_client_factory,
    [
        AutoCommandDefinition(RouteTablesOperations.delete, LongRunningOperation(L('Deleting route table'), L('Route table deleted'))),
        AutoCommandDefinition(RouteTablesOperations.get, 'RouteTable', command_alias='show'),
        AutoCommandDefinition(RouteTablesOperations.list, '[RouteTable]'),
        AutoCommandDefinition(RouteTablesOperations.list_all, '[RouteTable]'),
    ],
    command_table,
    {
        'route_table_name': {'name': '--name -n'}
    })


# RoutesOperations
build_operation(
    'network route-operation', 'routes', _network_client_factory,
    [
        AutoCommandDefinition(RoutesOperations.delete, LongRunningOperation(L('Deleting route'), L('Route deleted'))),
        AutoCommandDefinition(RoutesOperations.get, 'Route', command_alias='show'),
        AutoCommandDefinition(RoutesOperations.list, '[Route]'),
    ],
    command_table,
    {
        'route_name': {'name': '--name -n'}
    })

# SecurityRulesOperations
build_operation(
    'network nsg-rule', 'security_rules', _network_client_factory,
    [
        AutoCommandDefinition(SecurityRulesOperations.delete, LongRunningOperation(L('Deleting security rule'), L('Security rule deleted'))),
        AutoCommandDefinition(SecurityRulesOperations.get, 'SecurityRule', command_alias='show'),
        AutoCommandDefinition(SecurityRulesOperations.list, '[SecurityRule]'),
    ],
    command_table,
    {
        'security_rule_name': {'name': '--name'},
        'network_security_group_name': {'name': '--nsg-name'}
    })

# SubnetsOperations
build_operation(
    'network vnet subnet', 'subnets', _network_client_factory,
    [
        AutoCommandDefinition(SubnetsOperations.delete, LongRunningOperation(L('Deleting subnet'), L('Subnet deleted'))),
        AutoCommandDefinition(SubnetsOperations.get, 'Subnet', command_alias='show'),
        AutoCommandDefinition(SubnetsOperations.list, '[Subnet]'),
    ],
    command_table,
    {
        'subnet_name': {'name': '--name -n'},
        'virtual_network_name': {'name': _VNET_PARAM_NAME}
    })

# UsagesOperations
build_operation(
    'network', 'usages', _network_client_factory,
    [
        AutoCommandDefinition(UsagesOperations.list, '[Usage]', command_alias='list-usages'),
    ],
    command_table)

# VirtualNetworkGatewayConnectionsOperations
build_operation(
    'network vpn-connection', 'virtual_network_gateway_connections', _network_client_factory,
    [
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.delete, LongRunningOperation(L('Deleting virtual network gateway connection'), L('Virtual network gateway connection deleted'))),
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection', command_alias='show'),
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]'),
    ],
    command_table,
    {
        'virtual_network_gateway_connection_name': {'name': '--name -n'}
    })

# VirtualNetworkGatewayConnectionsOperations: shared-key
build_operation(
    'network vpn-connection shared-key', 'virtual_network_gateway_connections', _network_client_factory,
    [
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult', command_alias='show'),
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey', command_alias='reset'),
        AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey', command_alias='set'),
    ],
    command_table,
    {
        'virtual_network_gateway_connection_name': {'name': '--connection-name'},
        'connection_shared_key_name': {'name': '--name -n'}
    })

# VirtualNetworkGatewaysOperations
build_operation(
    'network vpn-gateway', 'virtual_network_gateways', _network_client_factory,
    [
        AutoCommandDefinition(VirtualNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting virtual network gateway'), L('Virtual network gateway deleted'))),
        AutoCommandDefinition(VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway', command_alias='show'),
        AutoCommandDefinition(VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]'),
        AutoCommandDefinition(VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway'),
    ],
    command_table,
    {
        'virtual_network_gateway_name': {'name': '--name -n'}
    })

# VirtualNetworksOperations
build_operation(
    'network vnet', 'virtual_networks', _network_client_factory,
    [
        AutoCommandDefinition(VirtualNetworksOperations.delete, LongRunningOperation(L('Deleting virtual network'), L('Virtual network deleted'))),
        AutoCommandDefinition(VirtualNetworksOperations.get, 'VirtualNetwork', command_alias='show'),
        AutoCommandDefinition(VirtualNetworksOperations.list, '[VirtualNetwork]'),
        AutoCommandDefinition(VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
    ],
    command_table,
    {
        'virtual_network_name': {'name': '--name -n'}
    })

build_operation(
    'network vnet', 'vnet', lambda _: get_mgmt_service_client(VNetClient, VNetClientConfig),
    [
        AutoCommandDefinition(VNetOperations.create,
                              LongRunningOperation(L('Creating virtual network'), L('Virtual network created')))
    ],
    command_table, VNET_SPECIFIC_PARAMS)

build_operation(
    'network subnet', None, ConvenienceNetworkCommands,
    [
        AutoCommandDefinition(ConvenienceNetworkCommands.create_update_subnet, 'Object', 'create')
    ],
    command_table)
