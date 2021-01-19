# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.translator import client_factory_register


@client_factory_register
def network_client_factory(cli_ctx, **kwargs):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK, **kwargs)


@client_factory_register
def resource_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


@client_factory_register
def cf_application_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).application_gateways


@client_factory_register
def cf_app_gateway_waf_policy(cli_ctx, _):
    return network_client_factory(cli_ctx).web_application_firewall_policies


@client_factory_register
def cf_application_security_groups(cli_ctx, _):
    return network_client_factory(cli_ctx).application_security_groups


@client_factory_register
def cf_connection_monitor(cli_ctx, _):
    return network_client_factory(cli_ctx).connection_monitors


@client_factory_register
def cf_flow_logs(cli_ctx, _):
    return network_client_factory(cli_ctx).flow_logs


@client_factory_register
def cf_ddos_protection_plans(cli_ctx, _):
    return network_client_factory(cli_ctx).ddos_protection_plans


@client_factory_register
def cf_endpoint_services(cli_ctx, _):
    return network_client_factory(cli_ctx).available_endpoint_services


@client_factory_register
def cf_express_route_circuit_authorizations(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuit_authorizations


@client_factory_register
def cf_express_route_circuit_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuit_connections


@client_factory_register
def cf_peer_express_route_circuit_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).peer_express_route_circuit_connections


@client_factory_register
def cf_express_route_circuit_peerings(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuit_peerings


@client_factory_register
def cf_express_route_circuits(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_circuits


@client_factory_register
def cf_express_route_service_providers(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_service_providers


@client_factory_register
def cf_express_route_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_connections


@client_factory_register
def cf_express_route_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_gateways


@client_factory_register
def cf_express_route_ports(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_ports


@client_factory_register
def cf_express_route_port_locations(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_ports_locations


@client_factory_register
def cf_express_route_links(cli_ctx, _):
    return network_client_factory(cli_ctx).express_route_links


@client_factory_register
def cf_private_endpoints(cli_ctx, _):
    return network_client_factory(cli_ctx).private_endpoints


@client_factory_register
def cf_private_dns_zone_groups(cli_ctx, _):
    return network_client_factory(cli_ctx).private_dns_zone_groups


@client_factory_register
def cf_private_endpoint_types(cli_ctx, _):
    return network_client_factory(cli_ctx).available_private_endpoint_types


@client_factory_register
def cf_private_link_services(cli_ctx, _):
    return network_client_factory(cli_ctx).private_link_services


@client_factory_register
def cf_load_balancers(cli_ctx, _):
    return network_client_factory(cli_ctx).load_balancers


@client_factory_register
def cf_load_balancer_backend_pools(cli_ctx, _):
    return network_client_factory(cli_ctx).load_balancer_backend_address_pools


@client_factory_register
def cf_local_network_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).local_network_gateways


@client_factory_register
def cf_network_interfaces(cli_ctx, _):
    return network_client_factory(cli_ctx).network_interfaces


@client_factory_register
def cf_network_profiles(cli_ctx, _):
    return network_client_factory(cli_ctx).network_profiles


@client_factory_register
def cf_network_security_groups(cli_ctx, _):
    return network_client_factory(cli_ctx).network_security_groups


@client_factory_register
def cf_network_watcher(cli_ctx, _):
    return network_client_factory(cli_ctx).network_watchers


@client_factory_register
def cf_packet_capture(cli_ctx, _):
    return network_client_factory(cli_ctx).packet_captures


@client_factory_register
def cf_private_access(cli_ctx, _):
    return network_client_factory(cli_ctx).available_private_access_services


@client_factory_register
def cf_public_ip_addresses(cli_ctx, _):
    return network_client_factory(cli_ctx).public_ip_addresses


@client_factory_register
def cf_public_ip_prefixes(cli_ctx, _):
    return network_client_factory(cli_ctx).public_ip_prefixes


@client_factory_register
def cf_route_tables(cli_ctx, _):
    return network_client_factory(cli_ctx).route_tables


@client_factory_register
def cf_routes(cli_ctx, _):
    return network_client_factory(cli_ctx).routes


@client_factory_register
def cf_security_rules(cli_ctx, _):
    return network_client_factory(cli_ctx).security_rules


@client_factory_register
def cf_service_endpoint_policies(cli_ctx, _):
    return network_client_factory(cli_ctx).service_endpoint_policies


@client_factory_register
def cf_service_endpoint_policy_definitions(cli_ctx, _):
    return network_client_factory(cli_ctx).service_endpoint_policy_definitions


@client_factory_register
def cf_service_tags(cli_ctx, _):
    return network_client_factory(cli_ctx).service_tags


@client_factory_register
def cf_subnets(cli_ctx, _):
    return network_client_factory(cli_ctx).subnets


@client_factory_register
def cf_usages(cli_ctx, _):
    return network_client_factory(cli_ctx).usages


@client_factory_register
def cf_virtual_network_gateway_connections(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateway_connections


@client_factory_register
def cf_virtual_network_gateways(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_gateways


@client_factory_register
def cf_virtual_networks(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_networks


@client_factory_register
def cf_virtual_network_peerings(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_network_peerings


@client_factory_register
def cf_service_aliases(cli_ctx, _):
    return network_client_factory(cli_ctx).available_service_aliases


@client_factory_register
def cf_traffic_manager_mgmt_profiles(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).profiles


@client_factory_register
def cf_traffic_manager_mgmt_endpoints(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).endpoints


@client_factory_register
def cf_tm_geographic(cli_ctx, _):
    from azure.mgmt.trafficmanager import TrafficManagerManagementClient
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, TrafficManagerManagementClient).geographic_hierarchies


@client_factory_register
def cf_dns_references(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).dns_resource_reference


@client_factory_register
def cf_dns_mgmt_zones(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).zones


@client_factory_register
def cf_dns_mgmt_record_sets(cli_ctx, _):
    from azure.cli.core.profiles import ResourceType
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_NETWORK_DNS).record_sets


@client_factory_register
def cf_route_filters(cli_ctx, _):
    return network_client_factory(cli_ctx).route_filters


@client_factory_register
def cf_route_filter_rules(cli_ctx, _):
    return network_client_factory(cli_ctx).route_filter_rules


@client_factory_register
def cf_service_community(cli_ctx, _):
    return network_client_factory(cli_ctx).bgp_service_communities


@client_factory_register
def cf_virtual_router(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_routers


@client_factory_register
def cf_virtual_router_peering(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_router_peerings


@client_factory_register
def cf_bastion_hosts(cli_ctx, _):
    return network_client_factory(cli_ctx).bastion_hosts


@client_factory_register
def cf_security_partner_providers(cli_ctx, _):
    return network_client_factory(cli_ctx).security_partner_providers


@client_factory_register
def cf_network_virtual_appliances(cli_ctx, _):
    return network_client_factory(cli_ctx).network_virtual_appliances


@client_factory_register
def cf_virtual_appliance_skus(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_appliance_skus


@client_factory_register
def cf_virtual_appliance_sites(cli_ctx, _):
    return network_client_factory(cli_ctx).virtual_appliance_sites
