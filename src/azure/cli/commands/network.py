from .._locale import L
from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
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

from ._command_creation import get_mgmt_service_client
from ..commands._auto_command import build_operation, LongRunningOperation
from ..commands import CommandTable

def get_command_table():
    return command_table

command_table = CommandTable()

def _network_client_factory():
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)


# pylint: disable=line-too-long
# Application gateways
build_operation(command_table,
                "network appgateway",
                "application_gateways",
                _network_client_factory,
                [
                    (ApplicationGatewaysOperations.delete, LongRunningOperation(L('Deleting application gateway'), L('Application gateway deleted'))),
                    (ApplicationGatewaysOperations.get, 'ApplicationGateway'),
                    (ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
                    (ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
                    (ApplicationGatewaysOperations.start, LongRunningOperation(L('Starting application gateway'), L('Application gateway started'))),
                    (ApplicationGatewaysOperations.stop, LongRunningOperation(L('Stopping application gateway'), L('Application gateway stopped'))),
                ])

# ExpressRouteCircuitAuthorizationsOperations
build_operation(command_table,
                "network expressroutecircuitauth",
                "express_route_circuit_authorizations",
                _network_client_factory,
                [
                    (ExpressRouteCircuitAuthorizationsOperations.delete, LongRunningOperation(L('Deleting express route authorization'), L('Express route authorization deleted'))),
                    (ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                    (ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                ])

# ExpressRouteCircuitPeeringsOperations
build_operation(command_table,
                "network expressroutecircuitpeering",
                "express_route_circuit_peerings",
                _network_client_factory,
                [
                    (ExpressRouteCircuitPeeringsOperations.delete, LongRunningOperation(L('Deleting express route circuit peering'), L('Express route circuit peering deleted'))),
                    (ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                    (ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                ])

# ExpressRouteCircuitsOperations
build_operation(command_table,
                "network expressroutecircuit",
                "express_route_circuits",
                _network_client_factory,
                [
                    (ExpressRouteCircuitsOperations.delete, LongRunningOperation(L('Deleting express route circuit'), L('Express route circuit deleted'))),
                    (ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit'),
                    (ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]'),
                    (ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]'),
                    (ExpressRouteCircuitsOperations.list_stats, '[ExpressRouteCircuitStats]'),
                    (ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]'),
                    (ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]'),
                ])

# ExpressRouteServiceProvidersOperations
build_operation(command_table,
                "network expressroutesp",
                "express_route_service_providers",
                _network_client_factory,
                [
                    (ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
                ])

# LoadBalancersOperations
build_operation(command_table,
                "network lb",
                "load_balancers",
                _network_client_factory,
                [
                    (LoadBalancersOperations.delete, LongRunningOperation(L('Deleting load balancer'), L('Load balancer deleted'))),
                    (LoadBalancersOperations.get, 'LoadBalancer'),
                    (LoadBalancersOperations.list_all, '[LoadBalancer]'),
                    (LoadBalancersOperations.list, '[LoadBalancer]'),
                ])

# LocalNetworkGatewaysOperations
build_operation(command_table,
                "network localgateways",
                "local_network_gateways",
                _network_client_factory,
                [
                    (LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway'),
                    (LocalNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting local network gateway'), L('Local network gateway deleted'))),
                    (LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                ])


# NetworkInterfacesOperations
build_operation(command_table,
                "network nic",
                "network_interfaces",
                _network_client_factory,
                [
                    (NetworkInterfacesOperations.delete, LongRunningOperation(L('Deleting network interface'), L('Network interface deleted'))),
                    (NetworkInterfacesOperations.get, 'NetworkInterface'),
                    (NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface'),
                    (NetworkInterfacesOperations.list_all, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.list, '[NetworkInterface]'),
                ])

# NetworkSecurityGroupsOperations
build_operation(command_table,
                "network securitygroup",
                "network_security_groups",
                _network_client_factory,
                [
                    (NetworkSecurityGroupsOperations.delete, LongRunningOperation(L('Deleting network security group'), L('Network security group deleted'))),
                    (NetworkSecurityGroupsOperations.delete, 'NetworkSecurityGroup'),
                    (NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]'),
                    (NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]'),
                ])

# PublicIPAddressesOperations
build_operation(command_table,
                "network publicipaddress",
                "public_ip_addresses",
                _network_client_factory,
                [
                    (PublicIPAddressesOperations.delete, LongRunningOperation(L('Deleting public IP address'), L('Public IP address deleted'))),
                    (PublicIPAddressesOperations.get, 'PublicIPAddress'),
                    (PublicIPAddressesOperations.list_all, '[PublicIPAddress]'),
                    (PublicIPAddressesOperations.list, '[PublicIPAddress]'),
                ])

# RouteTablesOperations
build_operation(command_table,
                "network routetable",
                "route_tables",
                _network_client_factory,
                [
                    (RouteTablesOperations.delete, LongRunningOperation(L('Deleting route table'), L('Route table deleted'))),
                    (RouteTablesOperations.get, 'RouteTable'),
                    (RouteTablesOperations.list, '[RouteTable]'),
                    (RouteTablesOperations.list_all, '[RouteTable]'),
                ])

# RoutesOperations
build_operation(command_table,
                "network routeoperation",
                "routes",
                _network_client_factory,
                [
                    (RoutesOperations.delete, LongRunningOperation(L('Deleting route'), L('Route deleted'))),
                    (RoutesOperations.get, 'Route'),
                    (RoutesOperations.list, '[Route]'),
                ])

# SecurityRulesOperations
build_operation(command_table,
                "network securityrules",
                "security_rules",
                _network_client_factory,
                [
                    (SecurityRulesOperations.delete, LongRunningOperation(L('Deleting security rule'), L('Security rule deleted'))),
                    (SecurityRulesOperations.get, 'SecurityRule'),
                    (SecurityRulesOperations.list, '[SecurityRule]'),
                ])

# SubnetsOperations
build_operation(command_table,
                "network subnet",
                "subnets",
                _network_client_factory,
                [
                    (SubnetsOperations.delete, LongRunningOperation(L('Deleting subnet'), L('Subnet deleted'))),
                    (SubnetsOperations.get, 'Subnet'),
                    (SubnetsOperations.list, '[Subnet]'),
                ])

# UsagesOperations
build_operation(command_table,
                "network usage",
                "usages",
                _network_client_factory,
                [
                    (UsagesOperations.list, '[Usage]'),
                ])

# VirtualNetworkGatewayConnectionsOperations
build_operation(command_table,
                "network vnetgatewayconnection",
                "virtual_network_gateway_connections",
                _network_client_factory,
                [
                    (VirtualNetworkGatewayConnectionsOperations.delete, LongRunningOperation(L('Deleting virtual network gateway connection'), L('Virtual network gateway connection deleted'))),
                    (VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection'),
                    (VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult'),
                    (VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]'),
                    (VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey'),
                    (VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey'),
                ])

# VirtualNetworkGatewaysOperations
build_operation(command_table,
                "network vnetgateway",
                "virtual_network_gateways",
                _network_client_factory,
                [
                    (VirtualNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting virtual network gateway'), L('Virtual network gateway deleted'))),
                    (VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway'),
                    (VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]'),
                    (VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway'),
                ])

# VirtualNetworksOperations
build_operation(command_table,
                "network vnet",
                "virtual_networks",
                _network_client_factory,
                [
                    (VirtualNetworksOperations.delete, LongRunningOperation(L('Deleting virtual network'), L('Virtual network deleted'))),
                    (VirtualNetworksOperations.get, 'VirtualNetwork'),
                    (VirtualNetworksOperations.list, '[VirtualNetwork]'),
                    (VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                ])

#@description(L('Create or update a virtual network (VNet)'))
@command_table.option('--resource-group -g', help=L('the resource group name'), required=True)
@command_table.option('--name -n', help=L('the VNet name'), required=True)
@command_table.option('--location -l', help=L('the VNet location'), required=True)
@command_table.option('--address-space -a', metavar='ADDRESS SPACE', help=L('the VNet address-space in CIDR notation or multiple address-spaces, quoted and space-separated'), required=True)
@command_table.option('--dns-servers -d', metavar='DNS SERVERS', help=L('the VNet DNS servers, quoted and space-separated'))
@command_table.command('network vnet create')
def create_update_vnet(args):
    from azure.mgmt.network.models import AddressSpace, DhcpOptions, VirtualNetwork

    resource_group = args.get('resource-group')
    name = args.get('name')
    location = args.get('location')
    address_space = AddressSpace(address_prefixes=args.get('address-space').split())
    dhcp_options = DhcpOptions(dns_servers=args.get('dns-servers').split())

    vnet_settings = VirtualNetwork(location=location,
                                   address_space=address_space,
                                   dhcp_options=dhcp_options)

    op = LongRunningOperation('Creating virtual network', 'Virtual network created')
    smc = _network_client_factory()
    poller = smc.virtual_networks.create_or_update(resource_group, name, vnet_settings)
    return op(poller)

#@description(L('Create or update a virtual network (VNet) subnet'))
@command_table.option('--resource-group -g', help=L('the the resource group name'), required=True)
@command_table.option('--name -n', help=L('the the subnet name'), required=True)
@command_table.option('--vnet -v', help=L('the name of the subnet vnet'), required=True)
@command_table.option('--address-prefix -a', help=L('the the address prefix in CIDR format'), required=True)
@command_table.command('network subnet create')
def create_update_subnet(args):
    from azure.mgmt.network.models import Subnet

    resource_group = args.get('resource-group')
    vnet = args.get('vnet')
    name = args.get('name')
    address_prefix = args.get('address-prefix')

    subnet_settings = Subnet(name=name,
                             address_prefix=address_prefix)

    op = LongRunningOperation('Creating subnet', 'Subnet created')
    smc = _network_client_factory()
    poller = smc.subnets.create_or_update(resource_group, vnet, name, subnet_settings)
    return op(poller)


