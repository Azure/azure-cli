# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

#pylint: disable=line-too-long

def _network_client_factory(**_):
    from azure.mgmt.network import NetworkManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(NetworkManagementClient)

def resource_client_factory(**_):
    from azure.mgmt.resource import ResourceManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceManagementClient)

def cf_application_gateways(_):
    return _network_client_factory().application_gateways

def cf_application_gateway_create(_):
    from azure.cli.command_modules.network.mgmt_app_gateway.lib import AppGatewayCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(AppGatewayCreationClient).app_gateway

def cf_express_route_circuit_authorizations(_):
    return _network_client_factory().express_route_circuit_authorizations

def cf_express_route_circuit_peerings(_):
    return _network_client_factory().express_route_circuit_peerings

def cf_express_route_circuits(_):
    return _network_client_factory().express_route_circuits

def cf_express_route_circuit_create(_):
    from azure.cli.command_modules.network.mgmt_express_route_circuit.lib import ExpressRouteCircuitCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ExpressRouteCircuitCreationClient).express_route_circuit

def cf_express_route_service_providers(_):
    return _network_client_factory().express_route_service_providers

def cf_load_balancers(_):
    return _network_client_factory().load_balancers

def cf_load_balancer_create(_):
    from azure.cli.command_modules.network.mgmt_lb.lib import LbCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(LbCreationClient).lb

def cf_local_network_gateways(_):
    return _network_client_factory().local_network_gateways

def cf_local_gateway_create(_):
    from azure.cli.command_modules.network.mgmt_local_gateway.lib import LocalGatewayCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(LocalGatewayCreationClient).local_gateway

def cf_nic_create(_):
    from azure.cli.command_modules.network.mgmt_nic.lib import NicCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(NicCreationClient).nic

def cf_network_interfaces(_):
    return _network_client_factory().network_interfaces

def cf_network_security_groups(_):
    return _network_client_factory().network_security_groups

def cf_nsg_create(_):
    from azure.cli.command_modules.network.mgmt_nsg.lib import NsgCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(NsgCreationClient).nsg

def cf_public_ip_addresses(_):
    return _network_client_factory().public_ip_addresses

def cf_public_ip_create(_):
    from azure.cli.command_modules.network.mgmt_public_ip.lib import PublicIpCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(PublicIpCreationClient).public_ip

def cf_route_tables(_):
    return _network_client_factory().route_tables

def cf_routes(_):
    return _network_client_factory().routes

def cf_security_rules(_):
    return _network_client_factory().security_rules

def cf_subnets(_):
    return _network_client_factory().subnets

def cf_usages(_):
    return _network_client_factory().usages

def cf_virtual_network_gateway_connections(_):
    return _network_client_factory().virtual_network_gateway_connections

def cf_vpn_connection_create(_):
    from azure.cli.command_modules.network.mgmt_vpn_connection.lib import VpnConnectionCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(VpnConnectionCreationClient).vpn_connection

def cf_virtual_network_gateways(_):
    return _network_client_factory().virtual_network_gateways

def cf_virtual_networks(_):
    return _network_client_factory().virtual_networks

def cf_vnet_gateway_create(_):
    from azure.cli.command_modules.network.mgmt_vnet_gateway.lib import VnetGatewayCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(VnetGatewayCreationClient).vnet_gateway

def cf_vnet_create(_):
    from azure.cli.command_modules.network.mgmt_vnet.lib import VnetCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(VnetCreationClient).vnet

def cf_virtual_network_peerings(_):
    return _network_client_factory().virtual_network_peerings

def cf_traffic_manager_mgmt_profiles(_):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerManagementClient).profiles

def cf_traffic_manager_profile_create(_):
    from azure.cli.command_modules.network.mgmt_traffic_manager_profile.lib import TrafficManagerProfileCreationClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerProfileCreationClient).traffic_manager_profile

def cf_traffic_manager_mgmt_endpoints(_):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerManagementClient).endpoints

def cf_dns_mgmt_zones(_):
    from azure.mgmt.dns import DnsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DnsManagementClient).zones

def cf_dns_mgmt_record_sets(_):
    from azure.mgmt.dns import DnsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DnsManagementClient).record_sets
