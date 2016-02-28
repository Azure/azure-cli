import azure.mgmt.network

from ._command_creation import get_service_client

from ..commands import _auto_command
from .._profile import Profile

def _network_client_factory():
    return get_service_client(azure.mgmt.network.NetworkManagementClient, azure.mgmt.network.NetworkManagementClientConfiguration)

# Application gateways
_auto_command._operation_builder("network",
                   "appgateway",
                   "application_gateways",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.delete, None),
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.get, 'ApplicationGateway'),
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.start, None),
                    (azure.mgmt.network.operations.ApplicationGatewaysOperations.stop, None),
                    ])

# ExpressRouteCircuitAuthorizationsOperations
_auto_command._operation_builder("network",
                   "expressroutecircuitauth",
                   "express_route_circuit_authorizations",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.ExpressRouteCircuitAuthorizationsOperations.delete, None),
                    (azure.mgmt.network.operations.ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                    ])

# ExpressRouteCircuitPeeringsOperations
_auto_command._operation_builder("network",
                   "expressroutecircuitpeering",
                   "express_route_circuit_peerings",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.ExpressRouteCircuitPeeringsOperations.delete, None),
                    (azure.mgmt.network.operations.ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                    ])

# ExpressRouteCircuitsOperations
_auto_command._operation_builder("network",
                   "expressroutecircuit",
                   "express_route_circuits",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.delete, None),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.list_stats, '[ExpressRouteCircuitStats]'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]'),
                    (azure.mgmt.network.operations.ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]'),
                    ])

# ExpressRouteServiceProvidersOperations
_auto_command._operation_builder("network",
                   "expressroutesp",
                   "express_route_service_providers",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
                    ])

# LoadBalancersOperations
_auto_command._operation_builder("network",
                   "lb",
                   "load_balancers",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.LoadBalancersOperations.delete, None),
                    (azure.mgmt.network.operations.LoadBalancersOperations.get, 'LoadBalancer'),
                    (azure.mgmt.network.operations.LoadBalancersOperations.list_all, '[LoadBalancer]'),
                    (azure.mgmt.network.operations.LoadBalancersOperations.list, '[LoadBalancer]'),
                    ])

# LocalNetworkGatewaysOperations
_auto_command._operation_builder("network",
                   "localgateways",
                   "local_network_gateways",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway'),
                    (azure.mgmt.network.operations.LocalNetworkGatewaysOperations.delete, None),
                    (azure.mgmt.network.operations.LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                    ])


# NetworkInterfacesOperations
_auto_command._operation_builder("network",
                   "nic",
                   "network_interfaces",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.delete, None),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.get, 'NetworkInterface'),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]'),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]'),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface'),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.list_all, '[NetworkInterface]'),
                    (azure.mgmt.network.operations.NetworkInterfacesOperations.list, '[NetworkInterface]'),
                    ])

# NetworkSecurityGroupsOperations
_auto_command._operation_builder("network",
                   "securitygroup",
                   "network_security_groups",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.NetworkSecurityGroupsOperations.delete, None),
                    (azure.mgmt.network.operations.NetworkSecurityGroupsOperations.delete, 'NetworkSecurityGroup'),
                    (azure.mgmt.network.operations.NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]'),
                    (azure.mgmt.network.operations.NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]'),
                    ])

# PublicIPAddressesOperations
_auto_command._operation_builder("network",
                   "publicipaddress",
                   "public_ip_addresses",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.PublicIPAddressesOperations.delete, None),
                    (azure.mgmt.network.operations.PublicIPAddressesOperations.get, 'PublicIPAddress'),
                    (azure.mgmt.network.operations.PublicIPAddressesOperations.list_all, '[PublicIPAddress]'),
                    (azure.mgmt.network.operations.PublicIPAddressesOperations.list, '[PublicIPAddress]'),
                    ])

# RouteTablesOperations
_auto_command._operation_builder("network",
                   "routetable",
                   "route_tables",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.RouteTablesOperations.delete, None),
                    (azure.mgmt.network.operations.RouteTablesOperations.get, 'RouteTable'),
                    (azure.mgmt.network.operations.RouteTablesOperations.list, '[RouteTable]'),
                    (azure.mgmt.network.operations.RouteTablesOperations.list_all, '[RouteTable]'),
                    ])

# RoutesOperations
_auto_command._operation_builder("network",
                   "routeoperation",
                   "routes",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.RoutesOperations.delete, None),
                    (azure.mgmt.network.operations.RoutesOperations.get, 'Route'),
                    (azure.mgmt.network.operations.RoutesOperations.list, '[Route]'),
                    ])

# SecurityRulesOperations
_auto_command._operation_builder("network",
                   "securityrules",
                   "security_rules",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.SecurityRulesOperations.delete, None),
                    (azure.mgmt.network.operations.SecurityRulesOperations.get, 'SecurityRule'),
                    (azure.mgmt.network.operations.SecurityRulesOperations.list, '[SecurityRule]'),
                    ])

# SubnetsOperations
_auto_command._operation_builder("network",
                   "subnet",
                   "subnets",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.SubnetsOperations.delete, None),
                    (azure.mgmt.network.operations.SubnetsOperations.get, 'Subnet'),
                    (azure.mgmt.network.operations.SubnetsOperations.list, '[Subnet]'),
                    ])

# UsagesOperations
_auto_command._operation_builder("network",
                   "usage",
                   "usages",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.UsagesOperations.list, '[Usage]'),
                    ])

# VirtualNetworkGatewayConnectionsOperations
_auto_command._operation_builder("network",
                   "vnetgatewayconnection",
                   "virtual_network_gateway_connections",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.delete, None),
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey'),
                    ])

# VirtualNetworkGatewaysOperations
_auto_command._operation_builder("network",
                   "vnetgateway",
                   "virtual_network_gateways",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.VirtualNetworkGatewaysOperations.delete, None),
                    (azure.mgmt.network.operations.VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]'),
                    (azure.mgmt.network.operations.VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway'),
                    ])

# VirtualNetworksOperations
_auto_command._operation_builder("network",
                   "vnet",
                   "virtual_networks",
                    _network_client_factory,
                    [
                    (azure.mgmt.network.operations.VirtualNetworksOperations.delete, None),
                    (azure.mgmt.network.operations.VirtualNetworksOperations.get, 'VirtualNetwork'),
                    (azure.mgmt.network.operations.VirtualNetworksOperations.list, '[VirtualNetwork]'),
                    (azure.mgmt.network.operations.VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                    ])
