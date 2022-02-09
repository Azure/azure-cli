# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long,too-many-lines

from azure.cli.core.commands import DeploymentOutputLongRunningOperation
from azure.cli.core.commands.arm import (
    deployment_validate_table_format, handle_template_based_exception)
from azure.cli.core.commands import CliCommandType
from azure.cli.core.profiles import get_api_version, ResourceType

from azure.cli.command_modules.network._client_factory import (
    cf_application_gateways, cf_express_route_circuit_authorizations,
    cf_express_route_circuit_peerings, cf_express_route_circuits,
    cf_express_route_service_providers, cf_load_balancers, cf_local_network_gateways,
    cf_network_interfaces, cf_network_security_groups, cf_network_watcher, cf_packet_capture,
    cf_route_tables, cf_routes, cf_route_filter_rules, cf_route_filters, cf_virtual_networks,
    cf_virtual_network_peerings, cf_virtual_network_gateway_connections,
    cf_virtual_network_gateways, cf_traffic_manager_mgmt_endpoints,
    cf_traffic_manager_mgmt_profiles, cf_dns_mgmt_record_sets, cf_dns_mgmt_zones,
    cf_tm_geographic, cf_security_rules, cf_subnets, cf_usages, cf_service_community,
    cf_public_ip_addresses, cf_endpoint_services, cf_application_security_groups, cf_connection_monitor,
    cf_ddos_protection_plans, cf_public_ip_prefixes, cf_service_endpoint_policies,
    cf_service_endpoint_policy_definitions, cf_dns_references, cf_private_endpoints, cf_network_profiles,
    cf_express_route_circuit_connections, cf_express_route_gateways, cf_express_route_connections,
    cf_express_route_ports, cf_express_route_port_locations, cf_express_route_links, cf_app_gateway_waf_policy,
    cf_service_tags, cf_private_link_services, cf_private_endpoint_types, cf_peer_express_route_circuit_connections,
    cf_virtual_router, cf_virtual_router_peering, cf_service_aliases, cf_bastion_hosts, cf_flow_logs,
    cf_private_dns_zone_groups, cf_security_partner_providers, cf_load_balancer_backend_pools,
    cf_network_virtual_appliances, cf_virtual_appliance_skus, cf_virtual_appliance_sites, cf_virtual_hub,
    cf_virtual_hub_bgp_connection, cf_virtual_hub_bgp_connections, cf_custom_ip_prefixes)
from azure.cli.command_modules.network._util import (
    list_network_resource_property, get_network_resource_property_entry, delete_network_resource_property_entry,
    delete_lb_resource_property_entry)
from azure.cli.command_modules.network._format import (
    transform_local_gateway_table_output, transform_dns_record_set_output,
    transform_dns_record_set_table_output, transform_dns_zone_table_output,
    transform_vnet_create_output, transform_public_ip_create_output,
    transform_traffic_manager_create_output, transform_nic_create_output,
    transform_nsg_create_output, transform_vnet_gateway_create_output,
    transform_vpn_connection, transform_vpn_connection_list,
    transform_geographic_hierachy_table_output,
    transform_service_community_table_output, transform_waf_rule_sets_table_output,
    transform_network_usage_list, transform_network_usage_table, transform_nsg_rule_table_output,
    transform_vnet_table_output, transform_effective_route_table, transform_effective_nsg,
    transform_vnet_gateway_routes_table, transform_vnet_gateway_bgp_peer_table)
from azure.cli.command_modules.network._validators import (
    get_network_watcher_from_location,
    process_ag_create_namespace, process_ag_listener_create_namespace, process_ag_http_settings_create_namespace,
    process_ag_rule_create_namespace, process_ag_ssl_policy_set_namespace, process_ag_url_path_map_create_namespace,
    process_ag_url_path_map_rule_create_namespace, process_auth_create_namespace, process_nic_create_namespace,
    process_lb_create_namespace, process_lb_frontend_ip_namespace, process_local_gateway_create_namespace,
    process_nw_cm_create_namespace,
    process_nw_cm_v2_endpoint_namespace, process_nw_cm_v2_test_configuration_namespace,
    process_nw_cm_v2_test_group, process_nw_cm_v2_output_namespace,
    process_nw_flow_log_set_namespace, process_nw_flow_log_create_namespace, process_nw_flow_log_show_namespace,
    process_nw_packet_capture_create_namespace, process_nw_test_connectivity_namespace, process_nw_topology_namespace,
    process_nw_troubleshooting_start_namespace, process_nw_troubleshooting_show_namespace,
    process_public_ip_create_namespace, process_tm_endpoint_create_namespace,
    process_vnet_create_namespace, process_vnet_gateway_create_namespace, process_vnet_gateway_update_namespace,
    process_vpn_connection_create_namespace, process_route_table_create_namespace,
    process_lb_outbound_rule_namespace, process_nw_config_diagnostic_namespace, process_list_delegations_namespace,
    process_appgw_waf_policy_update, process_cross_region_lb_frontend_ip_namespace, process_cross_region_lb_create_namespace)

NETWORK_VROUTER_DEPRECATION_INFO = 'network routeserver'
NETWORK_VROUTER_PEERING_DEPRECATION_INFO = 'network routeserver peering'


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # region Command Types
    network_ag_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ApplicationGatewaysOperations.{}',
        client_factory=cf_application_gateways
    )

    network_ag_waf_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#WebApplicationFirewallPoliciesOperations.{}',
        client_factory=cf_app_gateway_waf_policy
    )

    network_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network._util#{}',
        client_factory=None
    )

    network_asg_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ApplicationSecurityGroupsOperations.{}',
        client_factory=cf_application_security_groups
    )

    network_ddos_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#DdosProtectionPlansOperations.{}',
        client_factory=cf_ddos_protection_plans
    )

    network_dns_zone_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations#ZonesOperations.{}',
        client_factory=cf_dns_mgmt_zones,
        resource_type=ResourceType.MGMT_NETWORK_DNS
    )

    network_dns_record_set_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations#RecordSetsOperations.{}',
        client_factory=cf_dns_mgmt_record_sets,
        resource_type=ResourceType.MGMT_NETWORK_DNS
    )

    network_dns_reference_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations#DnsResourceReferenceOperations.{}',
        client_factory=cf_dns_references,
        resource_type=ResourceType.MGMT_NETWORK_DNS,
        min_api='2018-05-01'
    )

    network_endpoint_service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#AvailableEndpointServicesOperations.{}',
        client_factory=cf_endpoint_services,
        min_api='2017-06-01'
    )

    network_er_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteCircuitsOperations.{}',
        client_factory=cf_express_route_circuits,
        min_api='2016-09-01'
    )

    network_er_connection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteConnectionsOperations.{}',
        client_factory=cf_express_route_connections,
        min_api='2018-08-01'
    )

    network_er_gateway_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteGatewaysOperations.{}',
        client_factory=cf_express_route_gateways,
        min_api='2018-08-01'
    )

    network_er_ports_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRoutePortsOperations.{}',
        client_factory=cf_express_route_ports,
        min_api='2018-08-01'
    )

    network_er_port_locations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRoutePortsLocationsOperations.{}',
        client_factory=cf_express_route_port_locations,
        min_api='2018-08-01'
    )

    network_er_links_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteLinksOperations.{}',
        client_factory=cf_express_route_links,
        min_api='2018-08-01'
    )

    network_erca_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteCircuitAuthorizationsOperations.{}',
        client_factory=cf_express_route_circuit_authorizations,
        min_api='2016-09-01'
    )

    network_erconn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteCircuitConnectionsOperations.{}',
        client_factory=cf_express_route_circuit_connections,
        min_api='2018-07-01'
    )

    network_perconn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PeerExpressRouteCircuitConnectionsOperations.{}',
        client_factory=cf_peer_express_route_circuit_connections,
        min_api='2019-02-01'
    )

    network_ersp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteServiceProvidersOperations.{}',
        client_factory=cf_express_route_service_providers,
        min_api='2016-09-01'
    )

    network_er_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ExpressRouteCircuitPeeringsOperations.{}',
        client_factory=cf_express_route_circuit_peerings
    )

    network_private_endpoint_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PrivateEndpointsOperations.{}',
        client_factory=cf_private_endpoints,
        min_api='2020-06-01'
    )

    network_private_endpoint_dns_zone_group_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PrivateDnsZoneGroupsOperations.{}',
        client_factory=cf_private_dns_zone_groups,
        min_api='2020-03-01'
    )

    network_private_link_service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PrivateLinkServicesOperations.{}',
        client_factory=cf_private_link_services,
        min_api='2019-04-01'
    )

    network_lb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#LoadBalancersOperations.{}',
        client_factory=cf_load_balancers
    )

    network_lb_backend_pool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#LoadBalancerBackendAddressPoolsOperations.{}',
        client_factory=cf_load_balancer_backend_pools,
        min_api='2020-04-01'
    )

    network_lgw_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#LocalNetworkGatewaysOperations.{}',
        client_factory=cf_local_network_gateways
    )

    network_nic_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkInterfacesOperations.{}',
        client_factory=cf_network_interfaces
    )

    network_profile_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkProfilesOperations.{}',
        client_factory=cf_network_profiles,
        min_api='2018-08-01'
    )

    network_nsg_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkSecurityGroupsOperations.{}',
        client_factory=cf_network_security_groups
    )

    network_nsg_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#SecurityRulesOperations.{}',
        client_factory=cf_security_rules
    )

    network_public_ip_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PublicIPAddressesOperations.{}',
        client_factory=cf_public_ip_addresses
    )

    network_public_ip_prefix_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PublicIPPrefixesOperations.{}',
        client_factory=cf_public_ip_prefixes,
        min_api='2018-07-01'
    )

    network_rf_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#RouteFiltersOperations.{}',
        client_factory=cf_route_filters,
        min_api='2016-12-01'
    )

    network_rfr_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#RouteFilterRulesOperations.{}',
        client_factory=cf_route_filter_rules,
        min_api='2016-12-01'
    )

    network_rt_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#RouteTablesOperations.{}',
        client_factory=cf_route_tables
    )

    network_service_tags_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ServiceTagsOperations.{}',
        client_factory=cf_service_tags,
        min_api='2019-04-01'
    )

    network_subnet_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#SubnetsOperations.{}',
        client_factory=cf_subnets
    )

    network_tmp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.trafficmanager.operations#ProfilesOperations.{}',
        client_factory=cf_traffic_manager_mgmt_profiles
    )

    network_tme_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.trafficmanager.operations#EndpointsOperations.{}',
        client_factory=cf_traffic_manager_mgmt_endpoints
    )

    network_vgw_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualNetworkGatewaysOperations.{}',
        client_factory=cf_virtual_network_gateways
    )

    network_vnet_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualNetworksOperations.{}',
        client_factory=cf_virtual_networks
    )

    network_vnet_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualNetworkPeeringsOperations.{}',
        client_factory=cf_virtual_network_peerings
    )

    network_vpn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualNetworkGatewayConnectionsOperations.{}',
        client_factory=cf_virtual_network_gateway_connections
    )

    network_watcher_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkWatchersOperations.{}',
        client_factory=cf_network_watcher
    )

    network_watcher_cm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ConnectionMonitorsOperations.{}',
        client_factory=cf_connection_monitor
    )

    network_watcher_flow_log_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#FlowLogsOperations.{}',
        client_factory=cf_flow_logs,
    )

    network_watcher_flow_log_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_flow_logs,
    )

    network_watcher_pc_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PacketCapturesOperations.{}',
        client_factory=cf_packet_capture
    )

    network_sepd_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ServiceEndpointPolicyDefinitionsOperations.{}',
        client_factory=cf_service_endpoint_policy_definitions,
        min_api='2018-07-01'
    )

    network_sepp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ServiceEndpointPoliciesOperations.{}',
        client_factory=cf_service_endpoint_policies,
        min_api='2018-07-01'
    )

    network_virtual_hub_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualHubsOperations.{}',
        client_factory=cf_virtual_hub,
        min_api='2020-07-01'
    )

    network_virtual_hub_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_virtual_hub,
        min_api='2020-07-01'
    )

    network_virtual_hub_bgp_connection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualHubBgpConnectionOperations.{}',
        client_factory=cf_virtual_hub_bgp_connection,
        min_api='2020-07-01'
    )

    network_virtual_hub_bgp_connection_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_virtual_hub_bgp_connection,
        min_api='2020-07-01'
    )

    network_virtual_hub_bgp_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualHubBgpConnectionsOperations.{}',
        client_factory=cf_virtual_hub_bgp_connections,
        min_api='2020-07-01'
    )

    network_virtual_hub_bgp_connections_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_virtual_hub_bgp_connections,
        min_api='2020-07-01'
    )

    network_vrouter_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualRoutersOperations.{}',
        client_factory=cf_virtual_router,
        min_api='2019-08-01'
    )

    network_vrouter_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_virtual_router,
        min_api='2019-08-01'
    )

    network_vrouter_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualRouterPeeringsOperations.{}',
        client_factory=cf_virtual_router_peering,
        min_api='2019-08-01'
    )

    network_vrouter_peering_update_sdk = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_virtual_router_peering,
        min_api='2019-08-01'
    )

    network_service_aliases_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#AvailableServiceAliasesOperations.{}',
        client_factory=cf_service_aliases,
        min_api='2019-08-01'
    )

    network_bastion_hosts_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#BastionHostsOperations.{}',
        client_factory=cf_bastion_hosts,
        min_api='2019-11-01'
    )

    network_security_partner_provider_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#SecurityPartnerProvidersOperations.{}',
        client_factory=cf_security_partner_providers,
        min_api='2020-03-01'
    )

    network_virtual_appliances_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkVirtualAppliancesOperations.{}',
        client_factory=cf_network_virtual_appliances,
        min_api='2020-05-01'
    )

    virtual_appliance_skus_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualApplianceSkusOperations.{}',
        client_factory=cf_virtual_appliance_skus,
        min_api='2020-05-01'
    )

    virtual_appliance_sites_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualApplianceSitesOperations.{}',
        client_factory=cf_virtual_appliance_sites,
        min_api='2020-05-01'
    )

    network_custom_ip_prefix_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#CustomIPPrefixesOperations.{}',
        client_factory=cf_custom_ip_prefixes,
        min_api='2020-06-01'
    )

    network_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.network.custom#{}')

    network_load_balancers_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_load_balancers,
        min_api='2020-08-01'
    )

    network_nic_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_network_interfaces
    )

    # endregion

    # region NetworkRoot
    usage_path = 'azure.mgmt.network.operations#UsagesOperations.{}'
    with self.command_group('network') as g:
        g.command('list-usages', 'list', operations_tmpl=usage_path, client_factory=cf_usages, transform=transform_network_usage_list, table_transformer=transform_network_usage_table)

    with self.command_group('network', network_service_tags_sdk) as g:
        g.command('list-service-tags', 'list')
        g.custom_command('list-service-aliases', 'list_service_aliases', command_type=network_service_aliases_sdk)
    # endregion

    # region ApplicationGateways
    with self.command_group('network application-gateway', network_ag_sdk) as g:
        g.custom_command('create', 'create_application_gateway',
                         transform=DeploymentOutputLongRunningOperation(self.cli_ctx),
                         supports_no_wait=True,
                         table_transformer=deployment_validate_table_format,
                         validator=process_ag_create_namespace,
                         exception_handler=handle_template_based_exception)
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_application_gateways')
        g.command('start', 'begin_start')
        g.command('stop', 'begin_stop')
        g.custom_command('show-backend-health', 'show_ag_backend_health', min_api='2016-09-01', client_factory=cf_application_gateways)
        g.generic_update_command('update', supports_no_wait=True, setter_name='begin_create_or_update', custom_func_name='update_application_gateway')
        g.wait_command('wait')

    subresource_properties = [
        {'prop': 'authentication_certificates', 'name': 'auth-cert'},
        {'prop': 'ssl_certificates', 'name': 'ssl-cert'},
        {'prop': 'frontend_ip_configurations', 'name': 'frontend-ip'},
        {'prop': 'frontend_ports', 'name': 'frontend-port'},
        {'prop': 'backend_address_pools', 'name': 'address-pool'},
        {'prop': 'backend_http_settings_collection', 'name': 'http-settings', 'validator': process_ag_http_settings_create_namespace},
        {'prop': 'http_listeners', 'name': 'http-listener', 'validator': process_ag_listener_create_namespace},
        {'prop': 'request_routing_rules', 'name': 'rule', 'validator': process_ag_rule_create_namespace},
        {'prop': 'probes', 'name': 'probe'},
        {'prop': 'url_path_maps', 'name': 'url-path-map', 'validator': process_ag_url_path_map_create_namespace},
        {'prop': 'rewrite_rule_sets', 'name': 'rewrite-rule set'}
    ]
    if self.supported_api_version(min_api='2018-08-01'):
        subresource_properties.append({'prop': 'trusted_root_certificates', 'name': 'root-cert'})

    def _make_singular(value):
        try:
            if value.endswith('ies'):
                value = value[:-3] + 'y'
            elif value.endswith('s'):
                value = value[:-1]
            return value
        except AttributeError:
            return value

    for kwargs in subresource_properties:
        alias = kwargs['name']
        subresource = kwargs['prop']
        create_validator = kwargs.get('validator', None)
        with self.command_group('network application-gateway {}'.format(alias), network_util) as g:
            g.command('list', list_network_resource_property('application_gateways', subresource))
            g.show_command('show', get_network_resource_property_entry('application_gateways', subresource))
            g.command('delete', delete_network_resource_property_entry('application_gateways', subresource), supports_no_wait=True)
            g.custom_command('create', 'create_ag_{}'.format(_make_singular(subresource)), supports_no_wait=True, validator=create_validator)
            g.generic_update_command('update', command_type=network_ag_sdk, supports_no_wait=True,
                                     setter_name='begin_create_or_update',
                                     custom_func_name='update_ag_{}'.format(_make_singular(subresource)),
                                     child_collection_prop_name=subresource, validator=create_validator)

    with self.command_group('network application-gateway rewrite-rule', network_ag_sdk, min_api='2018-12-01') as g:
        g.custom_command('create', 'create_ag_rewrite_rule', supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_rewrite_rule')
        g.custom_command('list', 'list_ag_rewrite_rules')
        g.custom_command('delete', 'delete_ag_rewrite_rule', supports_no_wait=True)
        g.generic_update_command('update', command_type=network_ag_sdk, supports_no_wait=True,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_ag_rewrite_rule',
                                 child_collection_prop_name='rewrite_rule_sets.rewrite_rules',
                                 child_collection_key='name.name',
                                 child_arg_name='rule_set_name.rule_name')

    with self.command_group('network application-gateway rewrite-rule condition', network_ag_sdk, min_api='2018-12-01') as g:
        g.custom_command('create', 'create_ag_rewrite_rule_condition', supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_rewrite_rule_condition')
        g.custom_command('list', 'list_ag_rewrite_rule_conditions')
        g.custom_command('delete', 'delete_ag_rewrite_rule_condition', supports_no_wait=True)
        g.generic_update_command('update', command_type=network_ag_sdk, supports_no_wait=True,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_ag_rewrite_rule_condition',
                                 child_collection_prop_name='rewrite_rule_sets.rewrite_rules.conditions',
                                 child_collection_key='name.name.variable',
                                 child_arg_name='rule_set_name.rule_name.variable')

    with self.command_group('network application-gateway redirect-config', network_util, min_api='2017-06-01') as g:
        subresource = 'redirect_configurations'
        g.command('list', list_network_resource_property('application_gateways', subresource))
        g.show_command('show', get_network_resource_property_entry('application_gateways', subresource))
        g.command('delete', delete_network_resource_property_entry('application_gateways', subresource), supports_no_wait=True)
        g.custom_command('create', 'create_ag_{}'.format(_make_singular(subresource)), supports_no_wait=True, doc_string_source='ApplicationGatewayRedirectConfiguration')
        g.generic_update_command('update', command_type=network_ag_sdk,
                                 client_factory=cf_application_gateways, supports_no_wait=True,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_ag_{}'.format(_make_singular(subresource)),
                                 child_collection_prop_name=subresource, doc_string_source='ApplicationGatewayRedirectConfiguration')

    with self.command_group('network application-gateway rewrite-rule', network_ag_sdk, min_api='2018-12-01') as g:
        g.command('condition list-server-variables', 'list_available_server_variables')
        g.command('list-request-headers', 'list_available_request_headers')
        g.command('list-response-headers', 'list_available_response_headers')

    with self.command_group('network application-gateway ssl-policy') as g:
        g.custom_command('set', 'set_ag_ssl_policy_2017_06_01', min_api='2017-06-01', supports_no_wait=True, validator=process_ag_ssl_policy_set_namespace, doc_string_source='ApplicationGatewaySslPolicy')
        g.custom_command('set', 'set_ag_ssl_policy_2017_03_01', max_api='2017-03-01', supports_no_wait=True, validator=process_ag_ssl_policy_set_namespace)
        g.custom_show_command('show', 'show_ag_ssl_policy')

    with self.command_group('network application-gateway ssl-policy', network_ag_sdk, min_api='2017-06-01') as g:
        g.command('list-options', 'list_available_ssl_options')
        g.command('predefined list', 'list_available_ssl_predefined_policies')
        g.show_command('predefined show', 'get_ssl_predefined_policy')

    with self.command_group('network application-gateway url-path-map rule') as g:
        g.custom_command('create', 'create_ag_url_path_map_rule', supports_no_wait=True, validator=process_ag_url_path_map_rule_create_namespace)
        g.custom_command('delete', 'delete_ag_url_path_map_rule', supports_no_wait=True)

    with self.command_group('network application-gateway waf-config') as g:
        g.custom_command('set', 'set_ag_waf_config_2017_03_01', min_api='2017-03-01', supports_no_wait=True)
        g.custom_command('set', 'set_ag_waf_config_2016_09_01', max_api='2016-09-01', supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_waf_config')
        g.custom_command('list-rule-sets', 'list_ag_waf_rule_sets', min_api='2017-03-01', client_factory=cf_application_gateways, table_transformer=transform_waf_rule_sets_table_output)

    with self.command_group('network application-gateway identity', command_type=network_ag_sdk, min_api='2018-12-01') as g:
        g.custom_command('assign', 'assign_ag_identity', supports_no_wait=True)
        g.custom_command('remove', 'remove_ag_identity', supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_identity')

    with self.command_group('network application-gateway private-link',
                            command_type=network_ag_sdk,
                            min_api='2020-05-01',
                            is_preview=True) as g:
        g.custom_command('add', 'add_ag_private_link', supports_no_wait=True)
        g.custom_command('remove', 'remove_ag_private_link', confirmation=True, supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_private_link')
        g.custom_command('list', 'list_ag_private_link')
        g.wait_command('wait')

    with self.command_group('network application-gateway private-link ip-config',
                            command_type=network_ag_sdk,
                            min_api='2020-05-01',
                            is_preview=True) as g:
        g.custom_command('add', 'add_ag_private_link_ip', supports_no_wait=True)
        g.custom_command('remove', 'remove_ag_private_link_ip', confirmation=True, supports_no_wait=True)
        g.custom_show_command('show', 'show_ag_private_link_ip')
        g.custom_command('list', 'list_ag_private_link_ip')
        g.wait_command('wait')
    # endregion

    # region ApplicationGatewayWAFPolicy
    with self.command_group('network application-gateway waf-policy', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2018-12-01') as g:
        g.custom_command('create', 'create_ag_waf_policy')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_ag_waf_policies')
        g.generic_update_command('update', custom_func_name='update_ag_waf_policy')
        g.wait_command('wait')

    with self.command_group('network application-gateway waf-policy policy-setting', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2019-09-01') as g:
        g.custom_command('list', 'list_waf_policy_setting')
        g.generic_update_command('update',
                                 command_type=network_ag_waf_sdk,
                                 client_factory=cf_app_gateway_waf_policy,
                                 custom_func_name='update_waf_policy_setting')

    with self.command_group('network application-gateway waf-policy custom-rule', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2018-12-01') as g:
        g.custom_command('create', 'create_waf_custom_rule')
        g.custom_command('delete', 'delete_waf_custom_rule')
        g.custom_command('list', 'list_waf_custom_rules')
        g.custom_show_command('show', 'show_waf_custom_rule')
        g.generic_update_command('update',
                                 command_type=network_ag_waf_sdk,
                                 client_factory=cf_app_gateway_waf_policy,
                                 custom_func_name='update_waf_custom_rule',
                                 child_collection_prop_name='custom_rules',
                                 child_arg_name='rule_name')

    with self.command_group('network application-gateway waf-policy custom-rule match-condition', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2018-12-01') as g:
        g.custom_command('add', 'add_waf_custom_rule_match_cond')
        g.custom_command('list', 'list_waf_custom_rule_match_cond')
        g.custom_command('remove', 'remove_waf_custom_rule_match_cond')

    with self.command_group('network application-gateway waf-policy managed-rule rule-set', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2019-09-01') as g:
        g.custom_command('add', 'add_waf_managed_rule_set')
        g.generic_update_command('update',
                                 command_type=network_ag_waf_sdk,
                                 client_factory=cf_app_gateway_waf_policy,
                                 custom_func_name='update_waf_managed_rule_set',
                                 validator=process_appgw_waf_policy_update)
        g.custom_command('remove', 'remove_waf_managed_rule_set')
        g.custom_command('list', 'list_waf_managed_rule_set')

    with self.command_group('network application-gateway waf-policy managed-rule exclusion', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2019-09-01') as g:
        g.custom_command('add', 'add_waf_managed_rule_exclusion')
        g.custom_command('remove', 'remove_waf_managed_rule_exclusion')
        g.custom_command('list', 'list_waf_managed_rule_exclusion')

    with self.command_group('network application-gateway waf-policy managed-rule exclusion rule-set', network_ag_waf_sdk,
                            client_factory=cf_app_gateway_waf_policy,
                            min_api='2021-05-01') as g:
        g.custom_command('add', 'add_waf_exclusion_rule_set')
        g.custom_command('remove', 'remove_waf_exclusion_rule_set')
        g.custom_command('list', 'list_waf_exclusion_rule_set')

    with self.command_group('network application-gateway client-cert', network_ag_sdk, min_api='2020-06-01', is_preview=True) as g:
        g.custom_command('add', 'add_trusted_client_certificate')
        g.custom_command('remove', 'remove_trusted_client_certificate')
        g.custom_command('list', 'list_trusted_client_certificate')
        g.custom_show_command('show', 'show_trusted_client_certificate')
        g.custom_command('update', 'update_trusted_client_certificate')

    with self.command_group('network application-gateway ssl-profile', network_ag_sdk, min_api='2020-06-01', is_preview=True) as g:
        g.custom_command('add', 'add_ssl_profile')
        g.custom_command('remove', 'remove_ssl_profile')
        g.custom_command('list', 'list_ssl_profile')
        g.custom_show_command('show', 'show_ssl_profile')
        g.custom_command('update', 'update_ssl_profile')

    # endregion

    # region ApplicationSecurityGroups
    with self.command_group('network asg', network_asg_sdk, client_factory=cf_application_security_groups, min_api='2017-09-01') as g:
        g.custom_command('create', 'create_asg')
        g.show_command('show', 'get')
        g.command('list', 'list_all')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_asg')
    # endregion

    # region DdosProtectionPlans
    with self.command_group('network ddos-protection', network_ddos_sdk, min_api='2018-02-01') as g:
        g.custom_command('create', 'create_ddos_plan')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_ddos_plans')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_ddos_plan')
    # endregion

    # region DNS
    with self.command_group('network dns', network_dns_reference_sdk, resource_type=ResourceType.MGMT_NETWORK_DNS) as g:
        g.command('list-references', 'get_by_target_resources')

    with self.command_group('network dns zone', network_dns_zone_sdk) as g:
        g.command('delete', 'begin_delete', confirmation=True)
        g.show_command('show', 'get', table_transformer=transform_dns_zone_table_output)
        g.custom_command('list', 'list_dns_zones', table_transformer=transform_dns_zone_table_output)
        g.custom_command('import', 'import_zone')
        g.custom_command('export', 'export_zone')
        g.custom_command('create', 'create_dns_zone', client_factory=cf_dns_mgmt_zones)
        g.generic_update_command('update', custom_func_name='update_dns_zone')

    with self.command_group('network dns record-set') as g:
        g.custom_command('list', 'list_dns_record_set', client_factory=cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output)

    api_version = str(get_api_version(self.cli_ctx, ResourceType.MGMT_NETWORK_DNS))
    api_version = api_version.replace('-', '_')
    dns_doc_string = 'azure.mgmt.dns.v' + api_version + '.operations#RecordSetsOperations.create_or_update'

    supported_records = ['a', 'aaaa', 'mx', 'ns', 'ptr', 'srv', 'txt']
    if self.supported_api_version(resource_type=ResourceType.MGMT_NETWORK_DNS, min_api='2018-02-01'):
        supported_records.append('caa')
    for record in supported_records:
        with self.command_group('network dns record-set {}'.format(record), network_dns_record_set_sdk, resource_type=ResourceType.MGMT_NETWORK_DNS) as g:
            g.show_command('show', 'get', transform=transform_dns_record_set_output)
            g.command('delete', 'delete', confirmation=True)
            g.custom_command('list', 'list_dns_record_set', client_factory=cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
            g.custom_command('create', 'create_dns_record_set', transform=transform_dns_record_set_output, doc_string_source=dns_doc_string)
            g.custom_command('add-record', 'add_dns_{}_record'.format(record), transform=transform_dns_record_set_output)
            g.custom_command('remove-record', 'remove_dns_{}_record'.format(record), transform=transform_dns_record_set_output)
            g.generic_update_command('update', custom_func_name='update_dns_record_set', transform=transform_dns_record_set_output)

    with self.command_group('network dns record-set soa', network_dns_record_set_sdk) as g:
        g.show_command('show', 'get', transform=transform_dns_record_set_output)
        g.custom_command('update', 'update_dns_soa_record', transform=transform_dns_record_set_output)

    with self.command_group('network dns record-set cname', network_dns_record_set_sdk) as g:
        g.show_command('show', 'get', transform=transform_dns_record_set_output)
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_dns_record_set', client_factory=cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
        g.custom_command('create', 'create_dns_record_set', transform=transform_dns_record_set_output, doc_string_source=dns_doc_string)
        g.custom_command('set-record', 'add_dns_cname_record', transform=transform_dns_record_set_output)
        g.custom_command('remove-record', 'remove_dns_cname_record', transform=transform_dns_record_set_output)
    # endregion

    # region ExpressRoutes
    with self.command_group('network express-route', network_er_sdk) as g:
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('get-stats', 'get_stats')
        g.command('list-arp-tables', 'begin_list_arp_table')
        g.command('list-route-tables', 'begin_list_routes_table', is_preview=True)
        g.command('list-route-tables-summary', 'begin_list_routes_table_summary', is_preview=True)
        g.custom_command('create', 'create_express_route', supports_no_wait=True)
        g.custom_command('list', 'list_express_route_circuits')
        g.command('list-service-providers', 'list', command_type=network_ersp_sdk)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_express_route', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('network express-route auth', network_erca_sdk) as g:
        g.custom_command('create', 'create_express_route_auth', min_api='2019-09-01')
        g.command('create', 'begin_create_or_update', max_api='2019-08-01', validator=process_auth_create_namespace)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('network express-route gateway', network_er_gateway_sdk) as g:
        g.custom_command('create', 'create_express_route_gateway')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_express_route_gateways')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_express_route_gateway', setter_arg_name='put_express_route_gateway_parameters')

    with self.command_group('network express-route gateway connection', network_er_connection_sdk) as g:
        g.custom_command('create', 'create_express_route_connection')
        g.command('delete', 'begin_delete')
        g.command('list', 'list')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_express_route_connection', setter_arg_name='put_express_route_connection_parameters')

    with self.command_group('network express-route peering', network_er_peering_sdk) as g:
        g.custom_command('create', 'create_express_route_peering', client_factory=cf_express_route_circuit_peerings)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('get-stats', 'get_peering_stats', command_type=network_er_sdk, is_preview=True)
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='peering_parameters', custom_func_name='update_express_route_peering')

    with self.command_group('network express-route peering connection', network_erconn_sdk) as g:
        g.custom_command('create', 'create_express_route_peering_connection')
        g.command('delete', 'begin_delete')
        g.show_command('show')
        g.command('list', 'list')

    with self.command_group('network express-route peering connection ipv6-config', network_erconn_sdk) as g:
        g.custom_command('set', 'set_express_route_peering_connection_config')
        g.custom_command('remove', 'remove_express_route_peering_connection_config')

    with self.command_group('network express-route peering peer-connection', network_perconn_sdk, is_preview=True) as g:
        g.show_command('show', is_preview=True)
        g.show_command('list', 'list', is_preview=True)

    with self.command_group('network express-route port', network_er_ports_sdk) as g:
        g.custom_command('create', 'create_express_route_port')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_express_route_ports')
        g.show_command('show')
        g.generic_update_command('update', custom_func_name='update_express_route_port')
        g.custom_command('generate-loa', 'download_generated_loa_as_pdf')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_express_route_port')

    with self.command_group('network express-route port identity', min_api='2019-08-01') as g:
        g.custom_command('assign', 'assign_express_route_port_identity', supports_no_wait=True)
        g.custom_command('remove', 'remove_express_route_port_identity', supports_no_wait=True)
        g.custom_show_command('show', 'show_express_route_port_identity')

    with self.command_group('network express-route port link', network_er_links_sdk) as g:
        g.command('list', 'list')
        g.show_command('show')

    with self.command_group('network express-route port link', network_er_ports_sdk) as g:
        g.generic_update_command('update',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_express_route_port_link',
                                 supports_no_wait=True,
                                 child_collection_prop_name='links',
                                 child_arg_name='link_name',
                                 min_api='2019-08-01')

    with self.command_group('network express-route port location', network_er_port_locations_sdk) as g:
        g.command('list', 'list')
        g.show_command('show')
    # endregion

    # region PrivateEndpoint
    with self.command_group('network private-endpoint', network_private_endpoint_sdk) as g:
        g.custom_command('create', 'create_private_endpoint', min_api='2019-04-01')
        g.command('delete', 'begin_delete', min_api='2019-04-01')
        g.custom_command('list', 'list_private_endpoints')
        g.show_command('show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_private_endpoint', min_api='2019-04-01')
        g.command(
            'list-types', 'list',
            operations_tmpl='azure.mgmt.network.operations#AvailablePrivateEndpointTypesOperations.{}',
            client_factory=cf_private_endpoint_types,
            min_api='2019-04-01'
        )

    with self.command_group('network private-endpoint dns-zone-group', network_private_endpoint_dns_zone_group_sdk, min_api='2020-03-01') as g:
        g.custom_command('create', 'create_private_endpoint_private_dns_zone_group')
        g.custom_command('add', 'add_private_endpoint_private_dns_zone')
        g.custom_command('remove', 'remove_private_endpoint_private_dns_zone')
        g.command('delete', 'begin_delete')
        g.show_command('show')
        g.command('list', 'list')

    with self.command_group('network private-endpoint ip-config', network_private_endpoint_sdk, min_api='2021-05-01') as g:
        g.custom_command('add', 'add_private_endpoint_ip_config')
        g.custom_command('remove', 'remove_private_endpoint_ip_config')
        g.custom_command('list', 'list_private_endpoint_ip_config')

    with self.command_group('network private-endpoint asg', network_private_endpoint_sdk, min_api='2021-05-01') as g:
        g.custom_command('add', 'add_private_endpoint_asg')
        g.custom_command('remove', 'remove_private_endpoint_asg')
        g.custom_command('list', 'list_private_endpoint_asg')
    # endregion

    # region PrivateLinkServices
    with self.command_group('network private-link-service', network_private_link_service_sdk) as g:
        g.custom_command('create', 'create_private_link_service')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_private_link_services')
        g.show_command('show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_private_link_service')

    with self.command_group('network private-link-service connection', network_private_link_service_sdk) as g:
        g.command('delete', 'begin_delete_private_endpoint_connection')
        g.custom_command('update', 'update_private_endpoint_connection')

    # TODO: Due to service limitation.
    # with self.command_group('network private-link-service ip-configs', network_private_link_service_sdk) as g:
    #     g.custom_command('add', 'add_private_link_services_ipconfig')
    #     g.custom_command('remove', 'remove_private_link_services_ipconfig')

    # endregion

    # region LoadBalancers
    with self.command_group('network lb', network_lb_sdk) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_load_balancer', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_lb_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_lbs')
        g.wait_command('wait')
        g.generic_update_command('update', getter_name='lb_get', getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update')
        g.custom_command('list-nic', 'list_load_balancer_nic', min_api='2017-06-01')

    property_map = {
        'frontend_ip_configurations': 'frontend-ip',
        'inbound_nat_rules': 'inbound-nat-rule',
        'inbound_nat_pools': 'inbound-nat-pool',
        'load_balancing_rules': 'rule',
        'probes': 'probe',
    }
    for subresource, alias in property_map.items():
        with self.command_group('network lb {}'.format(alias), network_util) as g:
            g.command('list', list_network_resource_property('load_balancers', subresource))
            g.show_command('show', get_network_resource_property_entry('load_balancers', subresource))
            g.command('delete', delete_lb_resource_property_entry('load_balancers', subresource))

    with self.command_group('network lb frontend-ip', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_frontend_ip_configuration', validator=process_lb_frontend_ip_namespace)
        g.generic_update_command('update', child_collection_prop_name='frontend_ip_configurations',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='update_lb_frontend_ip_configuration_setter',
                                 setter_type=network_load_balancers_custom,
                                 custom_func_name='set_lb_frontend_ip_configuration',
                                 validator=process_lb_frontend_ip_namespace)

    with self.command_group('network lb inbound-nat-rule', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_inbound_nat_rule')
        g.generic_update_command('update', child_collection_prop_name='inbound_nat_rules',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_inbound_nat_rule')

    with self.command_group('network lb inbound-nat-pool', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_inbound_nat_pool')
        g.generic_update_command('update', child_collection_prop_name='inbound_nat_pools',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_inbound_nat_pool')

    with self.command_group('network lb address-pool', network_lb_backend_pool_sdk) as g:
        g.custom_command('create', 'create_lb_backend_address_pool')
        g.generic_update_command('update', setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_backend_address_pool')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('delete', 'delete_lb_backend_address_pool')

    with self.command_group('network lb address-pool', network_lb_sdk, max_api='2020-03-01') as g:
        g.custom_command('create', 'create_lb_backend_address_pool')

    with self.command_group('network lb address-pool', network_util, max_api='2020-03-01') as g:
        g.command('list', list_network_resource_property('load_balancers', 'backend_address_pools'))
        g.show_command('show', get_network_resource_property_entry('load_balancers', 'backend_address_pools'))
        g.command('delete', delete_lb_resource_property_entry('load_balancers', 'backend_address_pools'))

    with self.command_group('network lb address-pool address', network_lb_backend_pool_sdk, is_preview=True) as g:
        g.custom_command('add', 'add_lb_backend_address_pool_address')
        g.custom_command('remove', 'remove_lb_backend_address_pool_address')
        g.custom_command('list', 'list_lb_backend_address_pool_address')

    with self.command_group('network lb address-pool tunnel-interface', network_lb_backend_pool_sdk, min_api='2021-02-01', is_preview=True) as g:
        g.custom_command('add', 'add_lb_backend_address_pool_tunnel_interface')
        g.custom_command('update', 'update_lb_backend_address_pool_tunnel_interface')
        g.custom_command('remove', 'remove_lb_backend_address_pool_tunnel_interface')
        g.custom_command('list', 'list_lb_backend_address_pool_tunnel_interface')

    with self.command_group('network lb rule', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_rule')
        g.generic_update_command('update', child_collection_prop_name='load_balancing_rules',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_rule')

    with self.command_group('network lb probe', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_probe')
        g.generic_update_command('update', child_collection_prop_name='probes',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_probe')

    with self.command_group('network lb outbound-rule', network_lb_sdk, min_api='2018-07-01') as g:
        g.custom_command('create', 'create_lb_outbound_rule', validator=process_lb_outbound_rule_namespace)
        g.generic_update_command('update', child_collection_prop_name='outbound_rules',
                                 getter_name='lb_get',
                                 getter_type=network_load_balancers_custom,
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_outbound_rule', validator=process_lb_outbound_rule_namespace)

    with self.command_group('network lb outbound-rule', network_util, min_api='2018-07-01') as g:
        g.command('list', list_network_resource_property('load_balancers', 'outbound_rules'))
        g.show_command('show', get_network_resource_property_entry('load_balancers', 'outbound_rules'))
        g.command('delete', delete_lb_resource_property_entry('load_balancers', 'outbound_rules'))
    # endregion

    # region cross-region load balancer
    with self.command_group('network cross-region-lb', network_lb_sdk) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_cross_region_load_balancer', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_cross_region_lb_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_lbs')
        g.generic_update_command('update', setter_name='begin_create_or_update')
        g.wait_command('wait')

    cross_region_lb_property_map = {
        'frontend_ip_configurations': 'frontend-ip',
        'load_balancing_rules': 'rule',
        'probes': 'probe',
    }

    for subresource, alias in cross_region_lb_property_map.items():
        with self.command_group('network cross-region-lb {}'.format(alias), network_util) as g:
            g.command('list', list_network_resource_property('load_balancers', subresource))
            g.show_command('show', get_network_resource_property_entry('load_balancers', subresource))
            g.command('delete', delete_lb_resource_property_entry('load_balancers', subresource))

    with self.command_group('network cross-region-lb frontend-ip', network_lb_sdk) as g:
        g.custom_command('create', 'create_cross_region_lb_frontend_ip_configuration', validator=process_cross_region_lb_frontend_ip_namespace)
        g.generic_update_command('update', child_collection_prop_name='frontend_ip_configurations',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_cross_region_lb_frontend_ip_configuration',
                                 validator=process_cross_region_lb_frontend_ip_namespace)

    with self.command_group('network cross-region-lb address-pool', network_lb_backend_pool_sdk) as g:
        g.custom_command('create', 'create_cross_region_lb_backend_address_pool')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('delete', 'delete_cross_region_lb_backend_address_pool')

    with self.command_group('network cross-region-lb address-pool address', network_lb_backend_pool_sdk, is_preview=True) as g:
        g.custom_command('add', 'add_cross_region_lb_backend_address_pool_address')
        g.custom_command('remove', 'remove_lb_backend_address_pool_address')
        g.custom_command('list', 'list_lb_backend_address_pool_address')

    with self.command_group('network cross-region-lb rule', network_lb_sdk) as g:
        g.custom_command('create', 'create_cross_region_lb_rule')
        g.generic_update_command('update', child_collection_prop_name='load_balancing_rules',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_cross_region_lb_rule')

    with self.command_group('network cross-region-lb probe', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_probe')
        g.generic_update_command('update', child_collection_prop_name='probes',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_probe')
    # endregion

    # region LocalGateways
    with self.command_group('network local-gateway', network_lgw_sdk) as g:
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list', table_transformer=transform_local_gateway_table_output)
        g.custom_command('create', 'create_local_gateway', supports_no_wait=True, validator=process_local_gateway_create_namespace)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_local_gateway', supports_no_wait=True)
        g.wait_command('wait')
    # endregion

    # region NetworkInterfaces: (NIC)
    with self.command_group('network nic', network_nic_sdk) as g:
        g.custom_command('create', 'create_nic', transform=transform_nic_create_output, validator=process_nic_create_namespace, supports_no_wait=True)
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_nics')
        g.command('show-effective-route-table', 'begin_get_effective_route_table', min_api='2016-09-01', table_transformer=transform_effective_route_table)
        g.command('list-effective-nsg', 'begin_list_effective_network_security_groups', min_api='2016-09-01', table_transformer=transform_effective_nsg)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_nic', supports_no_wait=True)
        g.wait_command('wait')

    resource = 'network_interfaces'
    subresource = 'ip_configurations'
    with self.command_group('network nic ip-config', network_nic_sdk) as g:
        g.custom_command('create', 'create_nic_ip_config')
        g.generic_update_command('update',
                                 child_collection_prop_name='ip_configurations', child_arg_name='ip_config_name',
                                 setter_name='update_nic_ip_config_setter',
                                 setter_type=network_nic_custom,
                                 custom_func_name='set_nic_ip_config')
        g.command('list', list_network_resource_property(resource, subresource), command_type=network_util)
        g.show_command('show', get_network_resource_property_entry(resource, subresource), command_type=network_util)
        g.command('delete', delete_network_resource_property_entry(resource, subresource), command_type=network_util)

    with self.command_group('network nic ip-config address-pool') as g:
        g.custom_command('add', 'add_nic_ip_config_address_pool')
        g.custom_command('remove', 'remove_nic_ip_config_address_pool')

    with self.command_group('network nic ip-config inbound-nat-rule') as g:
        g.custom_command('add', 'add_nic_ip_config_inbound_nat_rule')
        g.custom_command('remove', 'remove_nic_ip_config_inbound_nat_rule')

    # endregion

    # region NetworkSecurityGroups
    with self.command_group('network nsg', network_nsg_sdk) as g:
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_nsgs')
        g.custom_command('create', 'create_nsg', transform=transform_nsg_create_output)
        g.generic_update_command('update', setter_name='begin_create_or_update')

    with self.command_group('network nsg rule', network_nsg_rule_sdk) as g:
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_nsg_rules', table_transformer=lambda x: [transform_nsg_rule_table_output(i) for i in x])
        g.show_command('show', 'get', table_transformer=transform_nsg_rule_table_output)
        g.custom_command('create', 'create_nsg_rule_2017_06_01', min_api='2017-06-01')
        g.generic_update_command('update', setter_arg_name='security_rule_parameters', min_api='2017-06-01',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_nsg_rule_2017_06_01', doc_string_source='SecurityRule')
        g.custom_command('create', 'create_nsg_rule_2017_03_01', max_api='2017-03-01')
        g.generic_update_command('update', max_api='2017-03-01', setter_arg_name='security_rule_parameters',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='update_nsg_rule_2017_03_01', doc_string_source='SecurityRule')
    # endregion

    # region NetworkProfiles
    with self.command_group('network profile', network_profile_sdk) as g:
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('list', 'list_network_profiles')
        g.show_command('show')
    # endregion

    # region NetworkWatchers
    with self.command_group('network watcher', network_watcher_sdk, client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('configure', 'configure_network_watcher')
        g.command('list', 'list_all')
        g.custom_command('test-ip-flow', 'check_nw_ip_flow', client_factory=cf_network_watcher)
        g.custom_command('test-connectivity', 'check_nw_connectivity', client_factory=cf_network_watcher, validator=process_nw_test_connectivity_namespace, is_preview=True)
        g.custom_command('show-next-hop', 'show_nw_next_hop', client_factory=cf_network_watcher)
        g.custom_command('show-security-group-view', 'show_nw_security_view', client_factory=cf_network_watcher)
        g.custom_command('show-topology', 'show_topology_watcher', validator=process_nw_topology_namespace)
        g.custom_command('run-configuration-diagnostic', 'run_network_configuration_diagnostic', client_factory=cf_network_watcher, min_api='2018-06-01', validator=process_nw_config_diagnostic_namespace)

    with self.command_group('network watcher connection-monitor', network_watcher_cm_sdk, client_factory=cf_connection_monitor, min_api='2018-01-01') as g:
        g.custom_command('create', 'create_nw_connection_monitor', validator=process_nw_cm_create_namespace)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('stop', 'begin_stop')
        g.command('start', 'begin_start')
        g.command('query', 'begin_query')
        g.command('list', 'list')

    with self.command_group('network watcher connection-monitor endpoint',
                            network_watcher_cm_sdk,
                            min_api='2019-11-01',
                            client_factory=cf_connection_monitor,
                            is_preview=True,
                            validator=process_nw_cm_v2_endpoint_namespace) as g:
        g.custom_command('add', 'add_nw_connection_monitor_v2_endpoint')
        g.custom_command('remove', 'remove_nw_connection_monitor_v2_endpoint')
        g.custom_show_command('show', 'show_nw_connection_monitor_v2_endpoint')
        g.custom_command('list', 'list_nw_connection_monitor_v2_endpoint')

    with self.command_group('network watcher connection-monitor test-configuration',
                            network_watcher_cm_sdk,
                            min_api='2019-11-01',
                            client_factory=cf_connection_monitor,
                            is_preview=True,
                            validator=process_nw_cm_v2_test_configuration_namespace) as c:
        c.custom_command('add', 'add_nw_connection_monitor_v2_test_configuration')
        c.custom_command('remove', 'remove_nw_connection_monitor_v2_test_configuration')
        c.custom_show_command('show', 'show_nw_connection_monitor_v2_test_configuration')
        c.custom_command('list', 'list_nw_connection_monitor_v2_test_configuration')

    with self.command_group('network watcher connection-monitor test-group',
                            network_watcher_cm_sdk,
                            min_api='2019-11-01',
                            client_factory=cf_connection_monitor,
                            is_preview=True,
                            validator=process_nw_cm_v2_test_group) as c:
        c.custom_command('add', 'add_nw_connection_monitor_v2_test_group')
        c.custom_command('remove', 'remove_nw_connection_monitor_v2_test_group')
        c.custom_show_command('show', 'show_nw_connection_monitor_v2_test_group')
        c.custom_command('list', 'list_nw_connection_monitor_v2_test_group')

    with self.command_group('network watcher connection-monitor output',
                            network_watcher_cm_sdk,
                            min_api='2019-11-01',
                            client_factory=cf_connection_monitor,
                            is_preview=True,
                            validator=process_nw_cm_v2_output_namespace) as c:
        c.custom_command('add', 'add_nw_connection_monitor_v2_output')
        c.custom_command('remove', 'remove_nw_connection_monitor_v2_output')
        c.custom_command('list', 'list_nw_connection_monitor_v2_output')

    with self.command_group('network watcher packet-capture', network_watcher_pc_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_nw_packet_capture', client_factory=cf_packet_capture, validator=process_nw_packet_capture_create_namespace)
        g.show_command('show', 'get')
        g.command('show-status', 'begin_get_status')
        g.command('delete', 'begin_delete')
        g.command('stop', 'begin_stop')
        g.command('list', 'list')

    with self.command_group('network watcher flow-log', client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('configure',
                         'set_nsg_flow_logging',
                         validator=process_nw_flow_log_set_namespace,
                         deprecate_info=self.deprecate(redirect='network watcher flow-log create', hide=False))
        g.custom_show_command('show', 'show_nsg_flow_logging', validator=process_nw_flow_log_show_namespace)

    with self.command_group('network watcher flow-log',
                            network_watcher_flow_log_sdk,
                            client_factory=cf_flow_logs,
                            min_api='2019-11-01',
                            validator=get_network_watcher_from_location(remove=False)) as g:
        g.custom_command('list', 'list_nw_flow_log', validator=get_network_watcher_from_location(remove=False))
        g.custom_command('delete', 'delete_nw_flow_log', validator=get_network_watcher_from_location(remove=False))
        g.custom_command('create',
                         'create_nw_flow_log',
                         client_factory=cf_flow_logs,
                         validator=process_nw_flow_log_create_namespace)
        g.generic_update_command('update',
                                 getter_name='update_nw_flow_log_getter',
                                 getter_type=network_watcher_flow_log_update_sdk,
                                 setter_name='update_nw_flow_log_setter',
                                 setter_type=network_watcher_flow_log_update_sdk,
                                 custom_func_name='update_nw_flow_log',
                                 validator=process_nw_flow_log_create_namespace)

    with self.command_group('network watcher troubleshooting', client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('start', 'start_nw_troubleshooting', supports_no_wait=True, validator=process_nw_troubleshooting_start_namespace)
        g.custom_show_command('show', 'show_nw_troubleshooting_result', validator=process_nw_troubleshooting_show_namespace)
    # endregion

    # region CustomIpPrefix
    with self.command_group('network custom-ip prefix', network_custom_ip_prefix_sdk, client_factory=cf_custom_ip_prefixes, is_preview=True, min_api='2020-06-01') as g:
        g.custom_command('create', 'create_custom_ip_prefix', supports_no_wait=True)
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_custom_ip_prefixes')
        g.show_command('show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_custom_ip_prefix', supports_no_wait=True)
        g.wait_command('wait')
    # endRegion

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Address:ipAddress, AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'
    public_ip_show_table_transform = public_ip_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if self.supported_api_version(min_api='2017-06-01') else ' ')

    with self.command_group('network public-ip', network_public_ip_sdk) as g:
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get', table_transformer=public_ip_show_table_transform)
        g.custom_command('list', 'list_public_ips', table_transformer='[].' + public_ip_show_table_transform)
        g.custom_command('create', 'create_public_ip', transform=transform_public_ip_create_output, validator=process_public_ip_create_namespace)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_public_ip')

    with self.command_group('network public-ip prefix', network_public_ip_prefix_sdk, client_factory=cf_public_ip_prefixes) as g:
        g.custom_command('create', 'create_public_ip_prefix')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_public_ip_prefixes')
        g.show_command('show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_public_ip_prefix')

    # endregion

    # region RouteFilters
    with self.command_group('network route-filter', network_rf_sdk, min_api='2016-12-01', is_preview=True) as g:
        g.custom_command('create', 'create_route_filter', client_factory=cf_route_filters)
        g.custom_command('list', 'list_route_filters', client_factory=cf_route_filters)
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='route_filter_parameters')

    with self.command_group('network route-filter rule', network_rfr_sdk, min_api='2016-12-01') as g:
        g.custom_command('create', 'create_route_filter_rule', client_factory=cf_route_filter_rules)
        g.command('list', 'list_by_route_filter')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='route_filter_rule_parameters')
        sc_path = 'azure.mgmt.network.operations#BgpServiceCommunitiesOperations.{}'
        g.command('list-service-communities', 'list', operations_tmpl=sc_path, client_factory=cf_service_community, table_transformer=transform_service_community_table_output)

    # endregion

    # region RouteTables
    with self.command_group('network route-table', network_rt_sdk) as g:
        g.custom_command('create', 'create_route_table', validator=process_route_table_create_namespace)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_route_tables')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_route_table')

    network_rtr_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#RoutesOperations.{}',
        client_factory=cf_routes
    )
    with self.command_group('network route-table route', network_rtr_sdk) as g:
        g.custom_command('create', 'create_route')
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='route_parameters', custom_func_name='update_route')

    # endregion

    # region ServiceEndpoint
    with self.command_group('network service-endpoint', network_endpoint_service_sdk) as g:
        g.command('list', 'list')

    with self.command_group('network service-endpoint policy', network_sepp_sdk) as g:
        g.custom_command('create', 'create_service_endpoint_policy')
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_service_endpoint_policies')
        g.show_command('show')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_service_endpoint_policy')

    with self.command_group('network service-endpoint policy-definition', network_sepd_sdk) as g:
        g.custom_command('create', 'create_service_endpoint_policy_definition')
        g.command('delete', 'begin_delete')
        g.command('list', 'list_by_resource_group')
        g.show_command('show')
        g.generic_update_command('update', custom_func_name='update_service_endpoint_policy_definition',
                                 setter_name='begin_create_or_update',
                                 setter_arg_name='service_endpoint_policy_definitions')
    # endregion

    # region TrafficManagers
    with self.command_group('network traffic-manager profile', network_tmp_sdk) as g:
        g.custom_command('check-dns', 'check_traffic_manager_name', client_factory=cf_traffic_manager_mgmt_profiles)
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_traffic_manager_profiles')
        g.custom_command('create', 'create_traffic_manager_profile', transform=transform_traffic_manager_create_output)
        g.generic_update_command('update', custom_func_name='update_traffic_manager_profile')

    with self.command_group('network traffic-manager endpoint', network_tme_sdk) as g:
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('create', 'create_traffic_manager_endpoint', validator=process_tm_endpoint_create_namespace)
        g.custom_command('list', 'list_traffic_manager_endpoints')
        g.generic_update_command('update', custom_func_name='update_traffic_manager_endpoint')

        tm_geographic_path = 'azure.mgmt.trafficmanager.operations#GeographicHierarchiesOperations.{}'
        g.command('show-geographic-hierarchy', 'get_default', client_factory=cf_tm_geographic, operations_tmpl=tm_geographic_path, table_transformer=transform_geographic_hierachy_table_output)

    # endregion

    # region VirtualNetworks
    with self.command_group('network vnet', network_vnet_sdk) as g:
        g.command('delete', 'begin_delete')
        g.custom_command('list', 'list_vnet', table_transformer=transform_vnet_table_output)
        g.show_command('show', 'get')
        g.command('check-ip-address', 'check_ip_address_availability', min_api='2016-09-01')
        g.custom_command('create', 'create_vnet', transform=transform_vnet_create_output, validator=process_vnet_create_namespace, supports_local_cache=True)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_vnet', supports_local_cache=True)
        g.command('list-endpoint-services', 'list', command_type=network_endpoint_service_sdk)
        g.custom_command('list-available-ips', 'list_available_ips', min_api='2016-09-01', is_preview=True)

    with self.command_group('network vnet peering', network_vnet_peering_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_vnet_peering')
        g.custom_command('sync', 'sync_vnet_peering')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'begin_delete')
        g.generic_update_command('update', setter_name='update_vnet_peering', setter_type=network_custom)

    with self.command_group('network vnet subnet', network_subnet_sdk) as g:
        g.custom_command('create', 'create_subnet', supports_local_cache=True)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', setter_name='begin_create_or_update', setter_arg_name='subnet_parameters',
                                 custom_func_name='update_subnet')
        g.custom_command('list-available-delegations', 'list_avail_subnet_delegations', min_api='2018-08-01', validator=process_list_delegations_namespace)
    # endregion

    # region VirtualNetworkGateways
    with self.command_group('network vnet-gateway', network_vgw_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_vnet_gateway', supports_no_wait=True, transform=transform_vnet_gateway_create_output, validator=process_vnet_gateway_create_namespace)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_vnet_gateway', supports_no_wait=True, validator=process_vnet_gateway_update_namespace)
        g.wait_command('wait')
        g.command('delete', 'begin_delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('reset', 'begin_reset')
        g.command('list-bgp-peer-status', 'begin_get_bgp_peer_status', table_transformer=transform_vnet_gateway_bgp_peer_table)
        g.command('list-advertised-routes', 'begin_get_advertised_routes', table_transformer=transform_vnet_gateway_routes_table)
        g.command('list-learned-routes', 'begin_get_learned_routes', table_transformer=transform_vnet_gateway_routes_table)
        g.command('show-supported-devices', 'supported_vpn_devices', is_preview=True, min_api='2017-09-01')
        g.custom_command('disconnect-vpn-connections', 'disconnect_vnet_gateway_vpn_connections', client_factory=cf_virtual_network_gateways, supports_no_wait=True, is_preview=True, min_api='2019-11-01')

    with self.command_group('network vnet-gateway packet-capture', network_vgw_sdk, client_factory=cf_virtual_network_gateways, is_preview=True, min_api='2019-07-01') as g:
        g.custom_command('start', 'start_vnet_gateway_package_capture', supports_no_wait=True)
        g.custom_command('stop', 'stop_vnet_gateway_package_capture', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('network vnet-gateway vpn-client', network_vgw_sdk, client_factory=cf_virtual_network_gateways) as g:
        g.custom_command('generate', 'generate_vpn_client')
        g.command('show-url', 'begin_get_vpn_profile_package_url', min_api='2017-08-01')
        g.command('show-health', 'begin_get_vpnclient_connection_health', is_preview=True, min_api='2019-04-01')

    with self.command_group('network vnet-gateway vpn-client ipsec-policy', network_vgw_sdk, client_factory=cf_virtual_network_gateways, is_preview=True, min_api='2018-02-01') as g:
        g.custom_command('set', 'set_vpn_client_ipsec_policy', supports_no_wait=True)
        g.show_command('show', 'begin_get_vpnclient_ipsec_parameters')
        g.wait_command('wait')

    # with self.command_group

    with self.command_group('network vnet-gateway revoked-cert', network_vgw_sdk) as g:
        g.custom_command('create', 'create_vnet_gateway_revoked_cert')
        g.custom_command('delete', 'delete_vnet_gateway_revoked_cert')

    with self.command_group('network vnet-gateway root-cert', network_vgw_sdk) as g:
        g.custom_command('create', 'create_vnet_gateway_root_cert')
        g.custom_command('delete', 'delete_vnet_gateway_root_cert')

    with self.command_group('network vnet-gateway ipsec-policy', network_vgw_sdk, min_api='2018-02-01') as g:
        g.custom_command('add', 'add_vnet_gateway_ipsec_policy', supports_no_wait=True, doc_string_source='IpsecPolicy')
        g.custom_command('list', 'list_vnet_gateway_ipsec_policies')
        g.custom_command('clear', 'clear_vnet_gateway_ipsec_policies', supports_no_wait=True)

    with self.command_group('network vnet-gateway aad', network_vgw_sdk, min_api='2019-04-01') as g:
        g.custom_command('assign', 'assign_vnet_gateway_aad', supports_no_wait=True)
        g.custom_show_command('show', 'show_vnet_gateway_aad')
        g.custom_command('remove', 'remove_vnet_gateway_aad', supports_no_wait=True)

    with self.command_group('network vnet-gateway nat-rule', network_vgw_sdk, min_api='2021-02-01', is_preview=True) as g:
        g.custom_command('add', 'add_vnet_gateway_nat_rule', supports_no_wait=True)
        g.custom_show_command('list', 'show_vnet_gateway_nat_rule')
        g.custom_command('remove', 'remove_vnet_gateway_nat_rule', supports_no_wait=True)
        g.wait_command('wait')
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection', network_vpn_sdk) as g:
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'begin_delete')
        g.show_command('show', 'get', transform=transform_vpn_connection)
        g.custom_command('list', 'list_vpn_connections', transform=transform_vpn_connection_list)
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_vpn_connection')
        g.command('list-ike-sas', 'begin_get_ike_sas', is_preview=True, min_api='2020-08-01')
        g.custom_command('show-device-config-script', 'show_vpn_connection_device_config_script', client_factory=cf_virtual_network_gateways, is_preview=True, min_api='2017-09-01')

    with self.command_group('network vpn-connection shared-key', network_vpn_sdk, client_factory=cf_virtual_network_gateway_connections) as g:
        g.show_command('show', 'get_shared_key')
        g.custom_command('reset', 'reset_shared_key')
        g.generic_update_command('update',
                                 getter_name='get_shared_key',
                                 custom_func_name='update_shared_key',
                                 setter_name='begin_set_shared_key')

    with self.command_group('network vpn-connection ipsec-policy', network_vpn_sdk, client_factory=cf_virtual_network_gateway_connections, min_api='2017-03-01') as g:
        g.custom_command('add', 'add_vpn_conn_ipsec_policy', supports_no_wait=True, doc_string_source='IpsecPolicy')
        g.custom_command('list', 'list_vpn_conn_ipsec_policies')
        g.custom_command('clear', 'clear_vpn_conn_ipsec_policies', supports_no_wait=True)

    with self.command_group('network vpn-connection packet-capture', network_vpn_sdk, client_factory=cf_virtual_network_gateway_connections, is_preview=True, min_api='2019-07-01') as g:
        g.custom_command('start', 'start_vpn_conn_package_capture', supports_no_wait=True)
        g.custom_command('stop', 'stop_vpn_conn_package_capture', supports_no_wait=True)
        g.wait_command('wait')

    # endregion

    # region VirtualRouter
    with self.command_group('network vrouter', network_vrouter_sdk,
                            deprecate_info=self.deprecate(redirect=NETWORK_VROUTER_DEPRECATION_INFO, hide=True)) as g:
        g.custom_command('create', 'create_virtual_router')
        g.generic_update_command('update',
                                 getter_name='virtual_router_update_getter',
                                 getter_type=network_vrouter_update_sdk,
                                 setter_name='virtual_router_update_setter',
                                 setter_type=network_vrouter_update_sdk,
                                 custom_func_name='update_virtual_router')
        g.custom_command('delete', 'delete_virtual_router')
        g.custom_show_command('show', 'show_virtual_router')
        g.custom_command('list', 'list_virtual_router')

    with self.command_group(
            'network vrouter peering', network_vrouter_peering_sdk,
            deprecate_info=self.deprecate(redirect=NETWORK_VROUTER_PEERING_DEPRECATION_INFO, hide=True)) as g:
        g.custom_command('create', 'create_virtual_router_peering')
        g.generic_update_command('update',
                                 getter_name='virtual_router_peering_update_getter',
                                 getter_type=network_vrouter_peering_update_sdk,
                                 setter_name='virtual_router_peering_update_setter',
                                 setter_type=network_vrouter_peering_update_sdk,
                                 custom_func_name='update_virtual_router_peering')
        g.custom_command('delete', 'delete_virtual_router_peering')
        g.custom_show_command('show', 'show_virtual_router_peering')
        g.custom_command('list', 'list_virtual_router_peering')
    # endregion

    # region VirtualHub
    with self.command_group('network routeserver', network_virtual_hub_sdk,
                            custom_command_type=network_virtual_hub_update_sdk) as g:
        g.custom_command('create', 'create_virtual_hub')
        g.generic_update_command('update',
                                 setter_name='virtual_hub_update_setter',
                                 setter_type=network_virtual_hub_update_sdk,
                                 custom_func_name='update_virtual_hub')
        g.custom_command('delete', 'delete_virtual_hub', supports_no_wait=True, confirmation=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_virtual_hub')
        g.wait_command('wait')

    with self.command_group('network routeserver peering', network_virtual_hub_bgp_connection_sdk,
                            custom_command_type=network_virtual_hub_bgp_connection_update_sdk) as g:
        g.custom_command('create', 'create_virtual_hub_bgp_connection', supports_no_wait=True)
        g.generic_update_command('update',
                                 setter_name='virtual_hub_bgp_connection_update_setter',
                                 setter_type=network_virtual_hub_bgp_connection_update_sdk,
                                 custom_func_name='update_virtual_hub_bgp_connection')
        g.custom_command('delete', 'delete_virtual_hub_bgp_connection', supports_no_wait=True, confirmation=True)
        g.show_command('show', 'get')
        g.wait_command('wait')

    with self.command_group('network routeserver peering', network_virtual_hub_bgp_connections_sdk,
                            custom_command_type=network_virtual_hub_bgp_connections_update_sdk) as g:
        g.command('list', 'list')
        g.custom_command('list-learned-routes', 'list_virtual_hub_bgp_connection_learned_routes')
        g.custom_command('list-advertised-routes', 'list_virtual_hub_bgp_connection_advertised_routes')
    # endregion

    # region Bastion
    with self.command_group('network bastion', network_bastion_hosts_sdk, is_preview=True) as g:
        g.custom_command('create', 'create_bastion_host')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_bastion_host')
        g.custom_command('ssh', 'ssh_bastion_host')
        g.custom_command('rdp', 'rdp_bastion_host')
        g.custom_command('tunnel', 'create_bastion_tunnel')
        g.command('delete', 'begin_delete')
    # endregion

    # region Security Partner Provider
    with self.command_group('network security-partner-provider', network_security_partner_provider_sdk, is_preview=True) as g:
        g.custom_command('create', 'create_security_partner_provider')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_security_partner_provider')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_security_partner_provider')
        g.command('delete', 'begin_delete')
    # endregion

    # region PrivateLinkResource and PrivateEndpointConnection
    plr_and_pec_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.network.private_link_resource_and_endpoint_connections.custom#{}')
    with self.command_group('network private-link-resource', custom_command_type=plr_and_pec_custom) as g:
        g.custom_show_command('list', 'list_private_link_resource')
    with self.command_group('network private-endpoint-connection', custom_command_type=plr_and_pec_custom) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection')
        g.custom_command('reject', 'reject_private_endpoint_connection')
        g.custom_command('delete', 'remove_private_endpoint_connection', confirmation=True)
        g.custom_show_command('show', 'show_private_endpoint_connection')
        g.custom_command('list', 'list_private_endpoint_connection')
    # endregion

    # region Network Virtual Appliance
    with self.command_group('network virtual-appliance', network_virtual_appliances_sdk, client_factory=cf_network_virtual_appliances, is_preview=True) as g:
        g.custom_command('create', 'create_network_virtual_appliance')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_network_virtual_appliance')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_network_virtual_appliance')
        g.command('delete', 'begin_delete', confirmation=True)

    with self.command_group('network virtual-appliance site', virtual_appliance_sites_sdk, client_factory=cf_virtual_appliance_sites, is_preview=True) as g:
        g.custom_command('create', 'create_network_virtual_appliance_site')
        g.generic_update_command('update', setter_name='begin_create_or_update', custom_func_name='update_network_virtual_appliance_site')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.command('list', 'list')

    with self.command_group('network virtual-appliance sku', virtual_appliance_skus_sdk, is_preview=True) as g:
        g.show_command('show', 'get')
        g.command('list', 'list')
    # endregion
