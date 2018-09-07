# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def network_client_factory(cli_ctx, aux_subscriptions=None, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK,
                                   aux_subscriptions=aux_subscriptions)


def resource_client_factory(cli_ctx, **_):
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def cf_application_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).application_gateways


def cf_application_security_groups(cli_ctx, _):
    return network_client_factory(cli_ctx).application_security_groups


def cf_connection_monitor(cli_ctx, _):
    return network_client_factory(cli_ctx).connection_monitors


def cf_ddos_protection_plans(cli_ctx, _):
    return network_client_factory(cli_ctx).ddos_protection_plans


def cf_endpoint_services(cli_ctx, _):
    return network_client_factory(cli_ctx).available_endpoint_services


def cf_express_route_circuit_authorizations(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuit_authorizations


def cf_express_route_circuit_peerings(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuit_peerings


def cf_express_route_circuits(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuits


def cf_express_route_service_providers(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_service_providers


def cf_load_balancers(cli_ctx, _):
    return network_client_factory(cli_ctx).load_balancers


def cf_local_network_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).local_network_gateways


def cf_network_interfaces(cli_ctx, _):
    return network_client_factory(cli_ctx).network_interfaces


def cf_network_security_groups(cli_ctx, _):
    return network_client_factory(cli_ctx).network_security_groups


def cf_network_watcher(cli_ctx, _):
    return network_client_factory(cli_ctx).network_watchers


def cf_packet_capture(cli_ctx, _):
    return network_client_factory(cli_ctx).packet_captures


def cf_private_access(cli_ctx, _):
    return network_client_factory(cli_ctx).available_private_access_services


def cf_public_ip_addresses(cli_ctx, _):
    return network_client_factory(cli_ctx).public_ip_addresses


def cf_route_tables(cli_ctx, _):
    return network_client_factory(cli_ctx).route_tables


def cf_routes(cli_ctx, _):
    return network_client_factory(cli_ctx).routes


def cf_security_rules(cli_ctx, _):
    return network_client_factory(cli_ctx).security_rules


def cf_subnets(cli_ctx, _):
    return network_client_factory(cli_ctx).subnets


def cf_usages(cli_ctx, _):
    return network_client_factory(cli_ctx).usages


def cf_virtual_network_gateway_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateway_connections


def cf_virtual_network_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateways


def cf_virtual_networks(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_networks


def cf_virtual_network_peerings(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_peerings


def cf_traffic_manager_mgmt_profiles(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).profiles


def cf_traffic_manager_mgmt_endpoints(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).endpoints


def cf_tm_geographic(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).geographic_hierarchies


def cf_dns_mgmt_zones(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).zones


def cf_dns_mgmt_record_sets(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets


def cf_route_filters(cli_ctx, _):
    return network_client_factory(cli_ctx).route_filters


def cf_route_filter_rules(cli_ctx, _):
    return network_client_factory(cli_ctx).route_filter_rules


def cf_service_community(cli_ctx, _):
    return network_client_factory(cli_ctx).bgp_service_communities
