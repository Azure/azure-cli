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

from ._command_creation import get_service_client
from ..commands._auto_command import build_operation, LongRunningOperation

def _network_client_factory():
    return get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# pylint: disable=line-too-long
# Application gateways
build_operation("network",
                "appgateway",
                "application_gateways",
                _network_client_factory,
                [
                    (ApplicationGatewaysOperations.delete, None),
                    (ApplicationGatewaysOperations.get, 'ApplicationGateway'),
                    (ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
                    (ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
                    (ApplicationGatewaysOperations.start, None),
                    (ApplicationGatewaysOperations.stop, LongRunningOperation(L('Starting application gateway'), L('Application gateway started'))),
                ])

# ExpressRouteCircuitAuthorizationsOperations
build_operation("network",
                "expressroutecircuitauth",
                "express_route_circuit_authorizations",
                _network_client_factory,
                [
                    (ExpressRouteCircuitAuthorizationsOperations.delete, None),
                    (ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                    (ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                ])

# ExpressRouteCircuitPeeringsOperations
build_operation("network",
                "expressroutecircuitpeering",
                "express_route_circuit_peerings",
                _network_client_factory,
                [
                    (ExpressRouteCircuitPeeringsOperations.delete, None),
                    (ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                    (ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                ])

# ExpressRouteCircuitsOperations
build_operation("network",
                "expressroutecircuit",
                "express_route_circuits",
                _network_client_factory,
                [
                    (ExpressRouteCircuitsOperations.delete, None),
                    (ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit'),
                    (ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]'),
                    (ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]'),
                    (ExpressRouteCircuitsOperations.list_stats, '[ExpressRouteCircuitStats]'),
                    (ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]'),
                    (ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]'),
                ])

# ExpressRouteServiceProvidersOperations
build_operation("network",
                "expressroutesp",
                "express_route_service_providers",
                _network_client_factory,
                [
                    (ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
                ])

# LoadBalancersOperations
build_operation("network",
                "lb",
                "load_balancers",
                _network_client_factory,
                [
                    (LoadBalancersOperations.delete, None),
                    (LoadBalancersOperations.get, 'LoadBalancer'),
                    (LoadBalancersOperations.list_all, '[LoadBalancer]'),
                    (LoadBalancersOperations.list, '[LoadBalancer]'),
                ])

# LocalNetworkGatewaysOperations
build_operation("network",
                "localgateways",
                "local_network_gateways",
                _network_client_factory,
                [
                    (LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway'),
                    (LocalNetworkGatewaysOperations.delete, None),
                    (LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                ])


# NetworkInterfacesOperations
build_operation("network",
                "nic",
                "network_interfaces",
                _network_client_factory,
                [
                    (NetworkInterfacesOperations.delete, None),
                    (NetworkInterfacesOperations.get, 'NetworkInterface'),
                    (NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface'),
                    (NetworkInterfacesOperations.list_all, '[NetworkInterface]'),
                    (NetworkInterfacesOperations.list, '[NetworkInterface]'),
                ])

# NetworkSecurityGroupsOperations
build_operation("network",
                "securitygroup",
                "network_security_groups",
                _network_client_factory,
                [
                    (NetworkSecurityGroupsOperations.delete, None),
                    (NetworkSecurityGroupsOperations.delete, 'NetworkSecurityGroup'),
                    (NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]'),
                    (NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]'),
                ])

# PublicIPAddressesOperations
build_operation("network",
                "publicipaddress",
                "public_ip_addresses",
                _network_client_factory,
                [
                    (PublicIPAddressesOperations.delete, None),
                    (PublicIPAddressesOperations.get, 'PublicIPAddress'),
                    (PublicIPAddressesOperations.list_all, '[PublicIPAddress]'),
                    (PublicIPAddressesOperations.list, '[PublicIPAddress]'),
                ])

# RouteTablesOperations
build_operation("network",
                "routetable",
                "route_tables",
                _network_client_factory,
                [
                    (RouteTablesOperations.delete, None),
                    (RouteTablesOperations.get, 'RouteTable'),
                    (RouteTablesOperations.list, '[RouteTable]'),
                    (RouteTablesOperations.list_all, '[RouteTable]'),
                ])

# RoutesOperations
build_operation("network",
                "routeoperation",
                "routes",
                _network_client_factory,
                [
                    (RoutesOperations.delete, None),
                    (RoutesOperations.get, 'Route'),
                    (RoutesOperations.list, '[Route]'),
                ])

# SecurityRulesOperations
build_operation("network",
                "securityrules",
                "security_rules",
                _network_client_factory,
                [
                    (SecurityRulesOperations.delete, None),
                    (SecurityRulesOperations.get, 'SecurityRule'),
                    (SecurityRulesOperations.list, '[SecurityRule]'),
                ])

# SubnetsOperations
build_operation("network",
                "subnet",
                "subnets",
                _network_client_factory,
                [
                    (SubnetsOperations.delete, None),
                    (SubnetsOperations.get, 'Subnet'),
                    (SubnetsOperations.list, '[Subnet]'),
                ])

# UsagesOperations
build_operation("network",
                "usage",
                "usages",
                _network_client_factory,
                [
                    (UsagesOperations.list, '[Usage]'),
                ])

# VirtualNetworkGatewayConnectionsOperations
build_operation("network",
                "vnetgatewayconnection",
                "virtual_network_gateway_connections",
                _network_client_factory,
                [
                    (VirtualNetworkGatewayConnectionsOperations.delete, None),
                    (VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection'),
                    (VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult'),
                    (VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]'),
                    (VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey'),
                    (VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey'),
                ])

# VirtualNetworkGatewaysOperations
build_operation("network",
                "vnetgateway",
                "virtual_network_gateways",
                _network_client_factory,
                [
                    (VirtualNetworkGatewaysOperations.delete, None),
                    (VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway'),
                    (VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]'),
                    (VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway'),
                ])

# VirtualNetworksOperations
build_operation("network",
                "vnet",
                "virtual_networks",
                _network_client_factory,
                [
                    (VirtualNetworksOperations.delete, None),
                    (VirtualNetworksOperations.get, 'VirtualNetwork'),
                    (VirtualNetworksOperations.list, '[VirtualNetwork]'),
                    (VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                ])
