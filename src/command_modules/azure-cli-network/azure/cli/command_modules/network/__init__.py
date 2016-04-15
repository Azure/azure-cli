import time
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

from azure.cli.command_modules.network.mgmt.lib import (ResourceManagementClient as VNetClient,
                                                        ResourceManagementClientConfiguration
                                                        as VNetClientConfig)
from azure.cli.command_modules.network.mgmt.lib.operations import VNetOperations

from azure.cli.commands._command_creation import get_mgmt_service_client
from azure.cli.commands._auto_command import build_operation, AutoCommandDefinition
from azure.cli.commands import CommandTable, LongRunningOperation, COMMON_PARAMETERS
from azure.cli._locale import L

command_table = CommandTable()

def _network_client_factory(_):
    return get_mgmt_service_client(NetworkManagementClient, NetworkManagementClientConfiguration)

# pylint: disable=line-too-long
# Application gateways
build_operation("network appgateway",
                "application_gateways",
                _network_client_factory,
                [
                    AutoCommandDefinition(ApplicationGatewaysOperations.delete, LongRunningOperation(L('Deleting application gateway'), L('Application gateway deleted'))),
                    AutoCommandDefinition(ApplicationGatewaysOperations.get, 'ApplicationGateway'),
                    AutoCommandDefinition(ApplicationGatewaysOperations.list, '[ApplicationGateway]'),
                    AutoCommandDefinition(ApplicationGatewaysOperations.list_all, '[ApplicationGateway]'),
                    AutoCommandDefinition(ApplicationGatewaysOperations.start, LongRunningOperation(L('Starting application gateway'), L('Application gateway started'))),
                    AutoCommandDefinition(ApplicationGatewaysOperations.stop, LongRunningOperation(L('Stopping application gateway'), L('Application gateway stopped'))),
                ],
                command_table)

# ExpressRouteCircuitAuthorizationsOperations
build_operation("network expressroutecircuitauth",
                "express_route_circuit_authorizations",
                _network_client_factory,
                [
                    AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.delete, LongRunningOperation(L('Deleting express route authorization'), L('Express route authorization deleted'))),
                    AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.get, 'ExpressRouteCircuitAuthorization'),
                    AutoCommandDefinition(ExpressRouteCircuitAuthorizationsOperations.list, '[ExpressRouteCircuitAuthorization]'),
                ],
                command_table)

# ExpressRouteCircuitPeeringsOperations
build_operation("network expressroutecircuitpeering",
                "express_route_circuit_peerings",
                _network_client_factory,
                [
                    AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.delete, LongRunningOperation(L('Deleting express route circuit peering'), L('Express route circuit peering deleted'))),
                    AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.get, 'ExpressRouteCircuitPeering'),
                    AutoCommandDefinition(ExpressRouteCircuitPeeringsOperations.list, '[ExpressRouteCircuitPeering]'),
                ],
                command_table)

# ExpressRouteCircuitsOperations
build_operation("network expressroutecircuit",
                "express_route_circuits",
                _network_client_factory,
                [
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.delete, LongRunningOperation(L('Deleting express route circuit'), L('Express route circuit deleted'))),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.get, 'ExpressRouteCircuit'),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.list_arp_table, '[ExpressRouteCircuitArpTable]', 'list-arp'),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.list_routes_table, '[ExpressRouteCircuitRoutesTable]', 'list-routes'),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.list_stats, '[ExpressRouteCircuitStats]'),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.list, '[ExpressRouteCircuit]'),
                    AutoCommandDefinition(ExpressRouteCircuitsOperations.list_all, '[ExpressRouteCircuit]'),
                ],
                command_table)

# ExpressRouteServiceProvidersOperations
build_operation("network expressroutesp",
                "express_route_service_providers",
                _network_client_factory,
                [
                    AutoCommandDefinition(ExpressRouteServiceProvidersOperations.list, '[ExpressRouteServiceProvider]'),
                ],
                command_table)

# LoadBalancersOperations
build_operation("network lb",
                "load_balancers",
                _network_client_factory,
                [
                    AutoCommandDefinition(LoadBalancersOperations.delete, LongRunningOperation(L('Deleting load balancer'), L('Load balancer deleted'))),
                    AutoCommandDefinition(LoadBalancersOperations.get, 'LoadBalancer'),
                    AutoCommandDefinition(LoadBalancersOperations.list_all, '[LoadBalancer]'),
                    AutoCommandDefinition(LoadBalancersOperations.list, '[LoadBalancer]'),
                ],
                command_table)

# LocalNetworkGatewaysOperations
build_operation("network localgateways",
                "local_network_gateways",
                _network_client_factory,
                [
                    AutoCommandDefinition(LocalNetworkGatewaysOperations.get, 'LocalNetworkGateway'),
                    AutoCommandDefinition(LocalNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting local network gateway'), L('Local network gateway deleted'))),
                    AutoCommandDefinition(LocalNetworkGatewaysOperations.list, '[LocalNetworkGateway]'),
                ],
                command_table)


# NetworkInterfacesOperations
build_operation("network nic",
                "network_interfaces",
                _network_client_factory,
                [
                    AutoCommandDefinition(NetworkInterfacesOperations.delete, LongRunningOperation(L('Deleting network interface'), L('Network interface deleted'))),
                    AutoCommandDefinition(NetworkInterfacesOperations.get, 'NetworkInterface'),
                    AutoCommandDefinition(NetworkInterfacesOperations.list_virtual_machine_scale_set_vm_network_interfaces, '[NetworkInterface]', 'list-scaleset-vm-network-interfaces'),
                    AutoCommandDefinition(NetworkInterfacesOperations.list_virtual_machine_scale_set_network_interfaces, '[NetworkInterface]', 'list-scaleset-network-interfaces'),
                    AutoCommandDefinition(NetworkInterfacesOperations.get_virtual_machine_scale_set_network_interface, 'NetworkInterface', 'get-scaleset-network-interface'),
                    AutoCommandDefinition(NetworkInterfacesOperations.list_all, '[NetworkInterface]'),
                    AutoCommandDefinition(NetworkInterfacesOperations.list, '[NetworkInterface]'),
                ],
                command_table)

# NetworkSecurityGroupsOperations
build_operation("network securitygroup",
                "network_security_groups",
                _network_client_factory,
                [
                    AutoCommandDefinition(NetworkSecurityGroupsOperations.delete, LongRunningOperation(L('Deleting network security group'), L('Network security group deleted'))),
                    AutoCommandDefinition(NetworkSecurityGroupsOperations.delete, 'NetworkSecurityGroup'),
                    AutoCommandDefinition(NetworkSecurityGroupsOperations.list_all, '[NetworkSecurityGroup]'),
                    AutoCommandDefinition(NetworkSecurityGroupsOperations.list, '[NetworkSecurityGroup]'),
                ],
                command_table)

# PublicIPAddressesOperations
build_operation("network publicipaddress",
                "public_ip_addresses",
                _network_client_factory,
                [
                    AutoCommandDefinition(PublicIPAddressesOperations.delete, LongRunningOperation(L('Deleting public IP address'), L('Public IP address deleted'))),
                    AutoCommandDefinition(PublicIPAddressesOperations.get, 'PublicIPAddress'),
                    AutoCommandDefinition(PublicIPAddressesOperations.list_all, '[PublicIPAddress]'),
                    AutoCommandDefinition(PublicIPAddressesOperations.list, '[PublicIPAddress]'),
                ],
                command_table)

# RouteTablesOperations
build_operation("network routetable",
                "route_tables",
                _network_client_factory,
                [
                    AutoCommandDefinition(RouteTablesOperations.delete, LongRunningOperation(L('Deleting route table'), L('Route table deleted'))),
                    AutoCommandDefinition(RouteTablesOperations.get, 'RouteTable'),
                    AutoCommandDefinition(RouteTablesOperations.list, '[RouteTable]'),
                    AutoCommandDefinition(RouteTablesOperations.list_all, '[RouteTable]'),
                ],
                command_table)

# RoutesOperations
build_operation("network routeoperation",
                "routes",
                _network_client_factory,
                [
                    AutoCommandDefinition(RoutesOperations.delete, LongRunningOperation(L('Deleting route'), L('Route deleted'))),
                    AutoCommandDefinition(RoutesOperations.get, 'Route'),
                    AutoCommandDefinition(RoutesOperations.list, '[Route]'),
                ],
                command_table)

# SecurityRulesOperations
build_operation("network securityrules",
                "security_rules",
                _network_client_factory,
                [
                    AutoCommandDefinition(SecurityRulesOperations.delete, LongRunningOperation(L('Deleting security rule'), L('Security rule deleted'))),
                    AutoCommandDefinition(SecurityRulesOperations.get, 'SecurityRule'),
                    AutoCommandDefinition(SecurityRulesOperations.list, '[SecurityRule]'),
                ],
                command_table)

# SubnetsOperations
build_operation("network subnet",
                "subnets",
                _network_client_factory,
                [
                    AutoCommandDefinition(SubnetsOperations.delete, LongRunningOperation(L('Deleting subnet'), L('Subnet deleted'))),
                    AutoCommandDefinition(SubnetsOperations.get, 'Subnet'),
                    AutoCommandDefinition(SubnetsOperations.list, '[Subnet]'),
                ],
                command_table)

# UsagesOperations
build_operation("network usage",
                "usages",
                _network_client_factory,
                [
                    AutoCommandDefinition(UsagesOperations.list, '[Usage]'),
                ],
                command_table)

# VirtualNetworkGatewayConnectionsOperations
build_operation("network vnetgatewayconnection",
                "virtual_network_gateway_connections",
                _network_client_factory,
                [
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.delete, LongRunningOperation(L('Deleting virtual network gateway connection'), L('Virtual network gateway connection deleted'))),
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.get, 'VirtualNetworkGatewayConnection'),
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.get_shared_key, 'ConnectionSharedKeyResult'),
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.list, '[VirtualNetworkGatewayConnection]'),
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.reset_shared_key, 'ConnectionResetSharedKey'),
                    AutoCommandDefinition(VirtualNetworkGatewayConnectionsOperations.set_shared_key, 'ConnectionSharedKey'),
                ],
                command_table)

# VirtualNetworkGatewaysOperations
build_operation("network vnetgateway",
                "virtual_network_gateways",
                _network_client_factory,
                [
                    AutoCommandDefinition(VirtualNetworkGatewaysOperations.delete, LongRunningOperation(L('Deleting virtual network gateway'), L('Virtual network gateway deleted'))),
                    AutoCommandDefinition(VirtualNetworkGatewaysOperations.get, 'VirtualNetworkGateway'),
                    AutoCommandDefinition(VirtualNetworkGatewaysOperations.list, '[VirtualNetworkGateway]'),
                    AutoCommandDefinition(VirtualNetworkGatewaysOperations.reset, 'VirtualNetworkGateway'),
                ],
                command_table)

# VirtualNetworksOperations
build_operation("network vnet",
                "virtual_networks",
                _network_client_factory,
                [
                    AutoCommandDefinition(VirtualNetworksOperations.delete, LongRunningOperation(L('Deleting virtual network'), L('Virtual network deleted'))),
                    AutoCommandDefinition(VirtualNetworksOperations.get, 'VirtualNetwork'),
                    AutoCommandDefinition(VirtualNetworksOperations.list, '[VirtualNetwork]'),
                    AutoCommandDefinition(VirtualNetworksOperations.list_all, '[VirtualNetwork]'),
                ],
                command_table)

# BUG: we are waiting on autorest to support this rename (https://github.com/Azure/autorest/issues/941)
VNET_SPECIFIC_PARAMS = {
    'deployment_parameter_virtual_network_name_value': {
        'name': '--vnet-name',
        'metavar': 'VNETNAME',
    },
    'deployment_parameter_virtual_network_prefix_value': {
        'name': '--vnet-prefix',
        'metavar': 'VNETPREFIX',
    },
    'deployment_parameter_subnet_name_value': {
        'name': '--subnet-name',
        'metavar': 'SUBNETNAME',
    },
    'deployment_parameter_subnet_prefix_value': {
        'name': '--subnet-prefix',
        'metavar': 'SUBNETPREFIX',
    }
}

build_operation('network vnet',
                'virtual_networks',
                lambda _: get_mgmt_service_client(VNetClient, VNetClientConfig),
                [
                    AutoCommandDefinition(VNetOperations.create,
                                          LongRunningOperation(L('Creating virtual network'), L('Virtual network created')))
                ],
                command_table,
                VNET_SPECIFIC_PARAMS)

@command_table.command('network subnet create')
@command_table.description(L('Create or update a virtual network (VNet) subnet'))
@command_table.option(**COMMON_PARAMETERS['resource_group_name'])
@command_table.option('--name -n', help=L('the the subnet name'), required=True)
@command_table.option('--vnet -v', help=L('the name of the subnet vnet'), required=True)
@command_table.option('--address-prefix -a', help=L('the the address prefix in CIDR format'), required=True)
def create_update_subnet(args):
    from azure.mgmt.network.models import Subnet

    resource_group = args.get('resource_group')
    vnet = args.get('vnet')
    name = args.get('name')
    address_prefix = args.get('address_prefix')

    subnet_settings = Subnet(name=name,
                             address_prefix=address_prefix)

    op = LongRunningOperation('Creating subnet', 'Subnet created')
    smc = _network_client_factory({})
    poller = smc.subnets.create_or_update(resource_group, vnet, name, subnet_settings)
    return op(poller)
