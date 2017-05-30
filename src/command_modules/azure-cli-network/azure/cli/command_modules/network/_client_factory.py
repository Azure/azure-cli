# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def _network_client_factory(**_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(ResourceType.MGMT_NETWORK)


def resource_client_factory(**_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(ResourceType.MGMT_RESOURCE_RESOURCES)


def cf_application_gateways(_):
    return _network_client_factory().application_gateways


def cf_express_route_circuit_authorizations(_):
    return _network_client_factory().express_route_circuit_authorizations


def cf_express_route_circuit_peerings(_):
    return _network_client_factory().express_route_circuit_peerings


def cf_express_route_circuits(_):
    return _network_client_factory().express_route_circuits


def cf_express_route_service_providers(_):
    return _network_client_factory().express_route_service_providers


def cf_load_balancers(_):
    return _network_client_factory().load_balancers


def cf_local_network_gateways(_):
    return _network_client_factory().local_network_gateways


def cf_network_interfaces(_):
    return _network_client_factory().network_interfaces


def cf_network_security_groups(_):
    return _network_client_factory().network_security_groups


def cf_network_watcher(_):
    return _network_client_factory().network_watchers


def cf_packet_capture(_):
    return _network_client_factory().packet_captures


def cf_public_ip_addresses(_):
    return _network_client_factory().public_ip_addresses


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


def cf_virtual_network_gateways(_):
    return _network_client_factory().virtual_network_gateways


def cf_virtual_networks(_):
    return _network_client_factory().virtual_networks


def cf_virtual_network_peerings(_):
    return _network_client_factory().virtual_network_peerings


def cf_traffic_manager_mgmt_profiles(_):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerManagementClient).profiles


def cf_traffic_manager_mgmt_endpoints(_):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerManagementClient).endpoints


def cf_tm_geographic(_):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(TrafficManagerManagementClient).geographic_hierarchies


def cf_dns_mgmt_zones(_):
    from azure.mgmt.dns import DnsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DnsManagementClient).zones


def cf_dns_mgmt_record_sets(_):
    from azure.mgmt.dns import DnsManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(DnsManagementClient).record_sets


def cf_route_filters(_):
    return _network_client_factory().route_filters


def cf_route_filter_rules(_):
    return _network_client_factory().route_filter_rules


def cf_service_community(_):
    return _network_client_factory().bgp_service_communities
