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
from ..commands import _auto_command

def _network_client_factory():
    return get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# pylint: disable=line-too-long
# Application gateways
_auto_command.operation_builder("network",
                                "appgateway",
                                "application_gateways",
                                _network_client_factory,
                                [
                                    (ApplicationGatewaysOperations.delete, None),
                                    (ApplicationGatewaysOperations.get, 'ApplicationGateway'),
                                    (ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
                                    (ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
                                    (ApplicationGatewaysOperations.start, None),
                                    (ApplicationGatewaysOperations.stop, None),
                                ])

# ExpressRouteCircuitAuthorizationsOperations
_auto_command.operation_builder("network",
                                "expressroutecircuitauth",
                                "express_route_circuit_authorizations",
                                _network_client_factory,
                                [
                                    (ExpressRouteCircuitAuthorizationsOperations.delete, None),
                                    (ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                                    (ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                                ])

# ExpressRouteCircuitPeeringsOperations
_auto_command.operation_builder("network",
                                "expressroutecircuitpeering",
                                "express_route_circuit_peerings",
                                _network_client_factory,
                                [
                                    (ExpressRouteCircuitPeeringsOperations.delete, None),
                                    (ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                                    (ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                                ])

# ExpressRouteCircuitsOperations
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
                                "expressroutesp",
                                "express_route_service_providers",
                                _network_client_factory,
                                [
                                    (ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
                                ])

# LoadBalancersOperations
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
                                "localgateways",
                                "local_network_gateways",
                                _network_client_factory,
                                [
                                    (LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway'),
                                    (LocalNetworkGatewaysOperations.delete, None),
                                    (LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                                ])


# NetworkInterfacesOperations
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
                                "routeoperation",
                                "routes",
                                _network_client_factory,
                                [
                                    (RoutesOperations.delete, None),
                                    (RoutesOperations.get, 'Route'),
                                    (RoutesOperations.list, '[Route]'),
                                ])

# SecurityRulesOperations
_auto_command.operation_builder("network",
                                "securityrules",
                                "security_rules",
                                _network_client_factory,
                                [
                                    (SecurityRulesOperations.delete, None),
                                    (SecurityRulesOperations.get, 'SecurityRule'),
                                    (SecurityRulesOperations.list, '[SecurityRule]'),
                                ])

# SubnetsOperations
_auto_command.operation_builder("network",
                                "subnet",
                                "subnets",
                                _network_client_factory,
                                [
                                    (SubnetsOperations.delete, None),
                                    (SubnetsOperations.get, 'Subnet'),
                                    (SubnetsOperations.list, '[Subnet]'),
                                ])

# UsagesOperations
_auto_command.operation_builder("network",
                                "usage",
                                "usages",
                                _network_client_factory,
                                [
                                    (UsagesOperations.list, '[Usage]'),
                                ])

# VirtualNetworkGatewayConnectionsOperations
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
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
_auto_command.operation_builder("network",
                                "vnet",
                                "virtual_networks",
                                _network_client_factory,
                                [
                                    (VirtualNetworksOperations.delete, None),
                                    (VirtualNetworksOperations.get, 'VirtualNetwork'),
                                    (VirtualNetworksOperations.list, '[VirtualNetwork]'),
                                    (VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                                ])
