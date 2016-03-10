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
from ..commands import command, description, option

def _network_client_factory():
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# pylint: disable=line-too-long
# Application gateways
build_operation("network",
                "appgateway",
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
build_operation("network",
                "expressroutecircuitauth",
                "express_route_circuit_authorizations",
                _network_client_factory,
                [
                    (ExpressRouteCircuitAuthorizationsOperations.delete, LongRunningOperation(L('Deleting express route authorization'), L('Express route authorization deleted'))),
                    (ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                    (ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                ])

# ExpressRouteCircuitPeeringsOperations
build_operation("network",
                "expressroutecircuitpeering",
                "express_route_circuit_peerings",
                _network_client_factory,
                [
                    (ExpressRouteCircuitPeeringsOperations.delete, LongRunningOperation(L('Deleting express route circuit peering'), L('Express route circuit peering deleted'))),
                    (ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                    (ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                ])

# ExpressRouteCircuitsOperations
build_operation("network",
                "expressroutecircuit",
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
                    (LoadBalancersOperations.delete, LongRunningOperation(L('Deleting load balancer'), L('Load balancer deleted'))),
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
                    (LocalNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting local network gateway'), L('Local network gateway deleted'))),
                    (LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                ])


# NetworkInterfacesOperations
build_operation("network",
                "nic",
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
build_operation("network",
                "securitygroup",
                "network_security_groups",
                _network_client_factory,
                [
                    (NetworkSecurityGroupsOperations.delete, LongRunningOperation(L('Deleting network security group'), L('Network security group deleted'))),
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
                    (PublicIPAddressesOperations.delete, LongRunningOperation(L('Deleting public IP address'), L('Public IP address deleted'))),
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
                    (RouteTablesOperations.delete, LongRunningOperation(L('Deleting route table'), L('Route table deleted'))),
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
                    (RoutesOperations.delete, LongRunningOperation(L('Deleting route'), L('Route deleted'))),
                    (RoutesOperations.get, 'Route'),
                    (RoutesOperations.list, '[Route]'),
                ])

# SecurityRulesOperations
build_operation("network",
                "securityrules",
                "security_rules",
                _network_client_factory,
                [
                    (SecurityRulesOperations.delete, LongRunningOperation(L('Deleting security rule'), L('Security rule deleted'))),
                    (SecurityRulesOperations.get, 'SecurityRule'),
                    (SecurityRulesOperations.list, '[SecurityRule]'),
                ])

# SubnetsOperations
build_operation("network",
                "subnet",
                "subnets",
                _network_client_factory,
                [
                    (SubnetsOperations.delete, LongRunningOperation(L('Deleting subnet'), L('Subnet deleted'))),
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
                    (VirtualNetworkGatewayConnectionsOperations.delete, LongRunningOperation(L('Deleting virtual network gateway connection'), L('Virtual network gateway connection deleted'))),
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
                    (VirtualNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting virtual network gateway'), L('Virtual network gateway deleted'))),
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
                    (VirtualNetworksOperations.delete, LongRunningOperation(L('Deleting virtual network'), L('Virtual network deleted'))),
                    (VirtualNetworksOperations.get, 'VirtualNetwork'),
                    (VirtualNetworksOperations.list, '[VirtualNetwork]'),
                    (VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                ])

@command('network vnet create')
@description(L('Create or update a virtual network (VNet)'))
@option('--resource-group -g <resourceGroup>', L('the resource group name'), required=True)
@option('--name -n <vnetName>', L('the VNet name'), required=True)
@option('--location -l <location>', L('the VNet location'), required=True)
@option('--address-space -a <vnetAddressSpace>', L('the VNet address-space in CIDR notation or multiple address-spaces, quoted and space-separated'), required=True)
@option('--dns-servers -d <dnsServers>', L('the VNet DNS servers, quoted and space-separated'))
def create_update_vnet(args, unexpected): #pylint: disable=unused-argument
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

@command('network subnet create')
@description(L('Create or update a virtual network (VNet) subnet'))
@option('--resource-group -g <resourceGroup>', L('the the resource group name'), required=True)
@option('--name -n <subnetName>', L('the the subnet name'), required=True)
@option('--vnet -v <vnetName>', L('the name of the subnet vnet'), required=True)
@option('--address-prefix -a <addressPrefix>', L('the the address prefix in CIDR format'), required=True)
# TODO: setting the IPConfiguration fails, will contact owning team
#@option('--ip-name -ipn <name>', L('the IP address configuration name'))
#@option('--ip-private-address -ippa <ipAddress>', L('the private IP address'))
#@option('--ip-allocation-method -ipam <allocationMethod>', L('the IP address allocation method'))
#@option('--ip-public-address -ipa <ipAddress>', L('the public IP address'))
def create_update_subnet(args, unexpected): #pylint: disable=unused-argument
    from azure.mgmt.network.models import (Subnet,
                                           # TODO: setting the IPConfiguration fails
                                           #IPConfiguration,
                                          )

    resource_group = args.get('resource-group')
    vnet = args.get('vnet')
    name = args.get('name')
    address_prefix = args.get('address-prefix')
    # TODO: setting the IPConfiguration fails, will contact owning team
    #ip_name = args.get('ip-name')
    #ip_private_address = args.get('ip-private-address')
    #ip_allocation_method = args.get('ip-allocation-method')
    #ip_public_address = args.get('ip-public-address')

    # TODO: setting the IPConfiguration fails, will contact owning team
    #ip_configuration = IPConfiguration(subnet = name,
    #                                    name = ip_name,
    #                                    private_ip_address = ip_private_address,
    #                                    private_ip_allocation_method = ip_allocation_method,
    #                                    public_ip_address = ip_public_address)

    subnet_settings = Subnet(name=name,
                             address_prefix=address_prefix)
                             # TODO: setting the IPConfiguration fails, will contact owning team
                             #ip_configurations = [ip_configuration])

    op = LongRunningOperation('Creating subnet', 'Subnet created')
    smc = _network_client_factory()
    poller = smc.subnets.create_or_update(resource_group, vnet, name, subnet_settings)
    return op(poller)


