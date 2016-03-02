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
from ..commands import _auto_command
from ..commands import command, description, option
from msrest import Serializer


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

@command('network vnet create')
@description(_('Create or update a virtual network (VNet)'))
@option('--resource-group -g <resourceGroup>', _('the resource group name')) #required
@option('--name -n <vnetName>', _('the VNet name')) #required
@option('--location -l <location>', _('the VNet location')) #required
@option('--address-space -a <vnetAddressSpace>', _('the VNet address-space in CIDR notation')) #required
@option('--dns-servers -d <dnsServers>', _('the VNet DNS servers'))
def create_update_vnet(args, unexpected):
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
    from azure.mgmt.network.models import VirtualNetwork, AddressSpace, DhcpOptions

    resource_group = args.get('resource-group')
    name = args.get('name')
    location = args.get('location')
    address_space = AddressSpace(address_prefixes = [args.get('address-space')])
    dhcp_options =  DhcpOptions(dns_servers = args.get('dns-servers'))

    vnet_settings = VirtualNetwork(location = location, 
                                   address_space = address_space, 
                                   dhcp_options = dhcp_options)

    smc = get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)
    poller = smc.virtual_networks.create_or_update(resource_group, name, vnet_settings)
    return Serializer().serialize_data(poller.result(), "VirtualNetwork")

@command('network subnet create')
@description(_('Create or update a virtual network (VNet) subnet'))
@option('--resource-group -g <resourceGroup>', _('the the resource group name')) #required
@option('--name -n <subnetName>', _('the the subnet name')) #required
@option('--vnet -v <vnetName>', _('the name of the subnet vnet')) #required
@option('--address-prefix -a <addressPrefix>', _('the the address prefix in CIDR format')) #required
@option('--ip-name -ipn <name>', _('the IP address configuration name')) 
@option('--ip-private-address -ippr <ipAddress>', _('the private IP address')) 
@option('--ip-allocation-method -ipa <allocationMethod>', _('the IP address allocation method')) 
@option('--ip-public-address -ippu <ipAddress>', _('the public IP address')) 
def create_update_subnet(args, unexpected):
    from azure.mgmt.network import NetworkManagementClient, NetworkManagementClientConfiguration
    from azure.mgmt.network.models import Subnet, IPConfiguration

    resource_group = args.get('resource-group')
    vnet = args.get('vnet')
    name = args.get('name')
    address_prefix = args.get('address-prefix')
    ip_name = args.get('ip-name')
    ip_private_address = args.get('ip-private-address')
    ip_allocation_method = args.get('ip-allocation-method')
    ip_public_address = args.get('ip-public-address')

    ip_configuration = None
                            #IPConfiguration(subnet = name, 
                            #            name = ip_name,
                            #            private_ip_address = ip_private_address,
                            #            private_ip_allocation_method = ip_allocation_method,
                            #            public_ip_address = ip_public_address)

    subnet_settings = Subnet(name = name, 
                             address_prefix = address_prefix)
                             #ip_configurations = [ip_configuration])

    smc = get_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)
    poller = smc.subnets.create_or_update(resource_group, vnet, name, subnet_settings)
    return Serializer().serialize_data(poller.result(), "Subnet")


