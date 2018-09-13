# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long

from azure.cli.core.commands import DeploymentOutputLongRunningOperation
from azure.cli.core.commands.arm import deployment_validate_table_format, handle_template_based_exception
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
    cf_service_endpoint_policy_definitions, cf_dns_references, cf_interface_endpoints, cf_network_profiles,
    cf_express_route_circuit_connections)
from azure.cli.command_modules.network._util import (
    list_network_resource_property, get_network_resource_property_entry, delete_network_resource_property_entry)
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
    transform_vnet_table_output)
from azure.cli.command_modules.network._validators import (
    process_ag_create_namespace, process_ag_listener_create_namespace, process_ag_http_settings_create_namespace,
    process_ag_rule_create_namespace, process_ag_ssl_policy_set_namespace, process_ag_url_path_map_create_namespace,
    process_ag_url_path_map_rule_create_namespace, process_auth_create_namespace, process_nic_create_namespace,
    process_lb_create_namespace, process_lb_frontend_ip_namespace, process_local_gateway_create_namespace,
    process_nw_cm_create_namespace, process_nw_flow_log_set_namespace, process_nw_flow_log_show_namespace,
    process_nw_packet_capture_create_namespace, process_nw_test_connectivity_namespace, process_nw_topology_namespace,
    process_nw_troubleshooting_start_namespace, process_nw_troubleshooting_show_namespace,
    process_public_ip_create_namespace, process_tm_endpoint_create_namespace,
    process_vnet_create_namespace, process_vnet_gateway_create_namespace, process_vnet_gateway_update_namespace,
    process_vpn_connection_create_namespace, process_route_table_create_namespace,
    process_lb_outbound_rule_namespace, process_nw_config_diagnostic_namespace, process_list_delegations_namespace)


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # region Command Types
    network_ag_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.application_gateways_operations#ApplicationGatewaysOperations.{}',
        client_factory=cf_application_gateways
    )

    network_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network._util#{}',
        client_factory=None
    )

    network_asg_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.application_security_groups_operations#ApplicationSecurityGroupsOperations.{}',
        client_factory=cf_application_security_groups
    )

    network_ddos_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.ddos_protection_plans_operations#DdosProtectionPlansOperations.{}',
        client_factory=cf_ddos_protection_plans
    )

    network_dns_zone_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations.zones_operations#ZonesOperations.{}',
        client_factory=cf_dns_mgmt_zones,
        resource_type=ResourceType.MGMT_NETWORK_DNS
    )

    network_dns_record_set_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations.record_sets_operations#RecordSetsOperations.{}',
        client_factory=cf_dns_mgmt_record_sets,
        resource_type=ResourceType.MGMT_NETWORK_DNS
    )

    network_dns_reference_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.dns.operations.dns_resource_reference_operations#DnsResourceReferenceOperations.{}',
        client_factory=cf_dns_references,
        resource_type=ResourceType.MGMT_NETWORK_DNS,
        min_api='2018-05-01'
    )

    network_endpoint_service_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.available_endpoint_services_operations#AvailableEndpointServicesOperations.{}',
        client_factory=cf_endpoint_services,
        min_api='2017-06-01'
    )

    network_er_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.express_route_circuits_operations#ExpressRouteCircuitsOperations.{}',
        client_factory=cf_express_route_circuits,
        min_api='2016-09-01'
    )

    network_erca_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.express_route_circuit_authorizations_operations#ExpressRouteCircuitAuthorizationsOperations.{}',
        client_factory=cf_express_route_circuit_authorizations,
        min_api='2016-09-01'
    )

    network_erconn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.express_route_circuit_connections_operations#ExpressRouteCircuitConnectionsOperations.{}',
        client_factory=cf_express_route_circuit_connections,
        min_api='2018-07-01'
    )

    network_ersp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.express_route_service_providers_operations#ExpressRouteServiceProvidersOperations.{}',
        client_factory=cf_express_route_service_providers,
        min_api='2016-09-01'
    )

    network_er_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.express_route_circuit_peerings_operations#ExpressRouteCircuitPeeringsOperations.{}',
        client_factory=cf_express_route_circuit_peerings
    )

    network_interface_endpoint_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.interface_endpoints_operations#InterfaceEndpointsOperations.{}',
        client_factory=cf_interface_endpoints,
        min_api='2018-08-01'
    )

    network_lb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.load_balancers_operations#LoadBalancersOperations.{}',
        client_factory=cf_load_balancers
    )

    network_lgw_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.local_network_gateways_operations#LocalNetworkGatewaysOperations.{}',
        client_factory=cf_local_network_gateways
    )

    network_nic_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.network_interfaces_operations#NetworkInterfacesOperations.{}',
        client_factory=cf_network_interfaces
    )

    network_profile_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.network_profiles_operations#NetworkProfilesOperations.{}',
        client_factory=cf_network_profiles,
        min_api='2018-08-01'
    )

    network_nsg_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.network_security_groups_operations#NetworkSecurityGroupsOperations.{}',
        client_factory=cf_network_security_groups
    )

    network_nsg_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.security_rules_operations#SecurityRulesOperations.{}',
        client_factory=cf_security_rules
    )

    network_public_ip_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.public_ip_addresses_operations#PublicIPAddressesOperations.{}',
        client_factory=cf_public_ip_addresses
    )

    network_public_ip_prefix_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.public_ip_prefixes_operations#PublicIPPrefixesOperations.{}',
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
        operations_tmpl='azure.mgmt.network.operations.route_tables_operations#RouteTablesOperations.{}',
        client_factory=cf_route_tables
    )

    network_subnet_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.subnets_operations#SubnetsOperations.{}',
        client_factory=cf_subnets
    )

    network_tmp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.trafficmanager.operations.profiles_operations#ProfilesOperations.{}',
        client_factory=cf_traffic_manager_mgmt_profiles
    )

    network_tme_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.trafficmanager.operations.endpoints_operations#EndpointsOperations.{}',
        client_factory=cf_traffic_manager_mgmt_endpoints
    )

    network_vgw_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.virtual_network_gateways_operations#VirtualNetworkGatewaysOperations.{}',
        client_factory=cf_virtual_network_gateways
    )

    network_vnet_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.virtual_networks_operations#VirtualNetworksOperations.{}',
        client_factory=cf_virtual_networks
    )

    network_vnet_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.virtual_network_peerings_operations#VirtualNetworkPeeringsOperations.{}',
        client_factory=cf_virtual_network_peerings
    )

    network_vpn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.virtual_network_gateway_connections_operations#VirtualNetworkGatewayConnectionsOperations.{}',
        client_factory=cf_virtual_network_gateway_connections
    )

    network_watcher_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.network_watchers_operations#NetworkWatchersOperations.{}',
        client_factory=cf_network_watcher
    )

    network_watcher_cm_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.connection_monitors_operations#ConnectionMonitorsOperations.{}',
        client_factory=cf_connection_monitor
    )

    network_watcher_pc_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.packet_captures_operations#PacketCapturesOperations.{}',
        client_factory=cf_packet_capture
    )

    network_sepd_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.service_endpoint_policy_definitions_operations#ServiceEndpointPolicyDefinitionsOperations.{}',
        client_factory=cf_service_endpoint_policy_definitions,
        min_api='2018-07-01'
    )

    network_sepp_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.service_endpoint_policies_operations#ServiceEndpointPoliciesOperations.{}',
        client_factory=cf_service_endpoint_policies,
        min_api='2018-07-01'
    )

    network_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.network.custom#{}')

    # endregion

    # region NetworkRoot
    usage_path = 'azure.mgmt.network.operations.usages_operations#UsagesOperations.{}'
    with self.command_group('network') as g:
        g.command('list-usages', 'list', operations_tmpl=usage_path, client_factory=cf_usages, transform=transform_network_usage_list, table_transformer=transform_network_usage_table)

    # endregion

    # region ApplicationGateways
    with self.command_group('network application-gateway', network_ag_sdk) as g:
        g.custom_command('create', 'create_application_gateway', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_ag_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_application_gateways')
        g.command('start', 'start')
        g.command('stop', 'stop')
        g.command('show-backend-health', 'backend_health', min_api='2016-09-01')
        g.generic_update_command('update', supports_no_wait=True, custom_func_name='update_application_gateway')
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
        {'prop': 'url_path_maps', 'name': 'url-path-map', 'validator': process_ag_url_path_map_create_namespace}
    ]

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
                                     custom_func_name='update_ag_{}'.format(_make_singular(subresource)),
                                     child_collection_prop_name=subresource, validator=create_validator)

    with self.command_group('network application-gateway redirect-config', network_util, min_api='2017-06-01') as g:
        subresource = 'redirect_configurations'
        g.command('list', list_network_resource_property('application_gateways', subresource))
        g.show_command('show', get_network_resource_property_entry('application_gateways', subresource))
        g.command('delete', delete_network_resource_property_entry('application_gateways', subresource), supports_no_wait=True)
        g.custom_command('create', 'create_ag_{}'.format(_make_singular(subresource)), supports_no_wait=True, doc_string_source='ApplicationGatewayRedirectConfiguration')
        g.generic_update_command('update', command_type=network_ag_sdk,
                                 client_factory=cf_application_gateways, supports_no_wait=True,
                                 custom_func_name='update_ag_{}'.format(_make_singular(subresource)),
                                 child_collection_prop_name=subresource, doc_string_source='ApplicationGatewayRedirectConfiguration')

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

    # endregion

    # region ApplicationSecurityGroups
    with self.command_group('network asg', network_asg_sdk, client_factory=cf_application_security_groups, min_api='2017-09-01') as g:
        g.custom_command('create', 'create_asg')
        g.show_command('show', 'get')
        g.command('list', 'list_all')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='update_asg')

    # endregion

    # region DdosProtectionPlans
    with self.command_group('network ddos-protection', network_ddos_sdk, min_api='2018-02-01') as g:
        g.custom_command('create', 'create_ddos_plan')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_ddos_plans')
        g.show_command('show', 'get')
        g.generic_update_command('update', custom_func_name='update_ddos_plan')
    # endregion

    # region DNS
    with self.command_group('network dns', network_dns_reference_sdk) as g:
        g.command('list-references', 'get_by_target_resources')

    with self.command_group('network dns zone', network_dns_zone_sdk) as g:
        g.command('delete', 'delete', confirmation=True)
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
        g.command('delete', 'delete')
        g.custom_command('list', 'list_dns_record_set', client_factory=cf_dns_mgmt_record_sets, transform=transform_dns_record_set_output, table_transformer=transform_dns_record_set_table_output)
        g.custom_command('create', 'create_dns_record_set', transform=transform_dns_record_set_output, doc_string_source=dns_doc_string)
        g.custom_command('set-record', 'add_dns_cname_record', transform=transform_dns_record_set_output)
        g.custom_command('remove-record', 'remove_dns_cname_record', transform=transform_dns_record_set_output)

    # endregion

    # region ExpressRoutes
    with self.command_group('network express-route', network_er_sdk) as g:
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('get-stats', 'get_stats')
        g.command('list-arp-tables', 'list_arp_table')
        g.command('list-route-tables', 'list_routes_table')
        g.custom_command('create', 'create_express_route', supports_no_wait=True)
        g.custom_command('list', 'list_express_route_circuits')
        g.command('list-service-providers', 'list', command_type=network_ersp_sdk)
        g.generic_update_command('update', custom_func_name='update_express_route', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('network express-route auth', network_erca_sdk) as g:
        g.command('create', 'create_or_update', validator=process_auth_create_namespace)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')

    with self.command_group('network express-route peering', network_er_peering_sdk) as g:
        g.custom_command('create', 'create_express_route_peering', client_factory=cf_express_route_circuit_peerings)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', setter_arg_name='peering_parameters', custom_func_name='update_express_route_peering')

    with self.command_group('network express-route peering connection', network_erconn_sdk) as g:
        g.custom_command('create', 'create_express_route_connection')
        g.command('delete', 'delete')
        g.show_command('show')
    # endregion

    # region InterfaceEndpoint
    with self.command_group('network interface-endpoint', network_interface_endpoint_sdk) as g:
        # TODO: Re-enable when service team asks. See issue #7271
        # g.custom_command('create', 'create_interface_endpoint')
        # g.command('delete', 'delete')
        g.custom_command('list', 'list_interface_endpoints')
        g.show_command('show')
        # g.generic_update_command('update', custom_func_name='update_interface_endpoint')
    # endregion

    # region LoadBalancers
    with self.command_group('network lb', network_lb_sdk) as g:
        g.show_command('show', 'get')
        g.custom_command('create', 'create_load_balancer', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_lb_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'delete')
        g.custom_command('list', 'list_lbs')
        g.generic_update_command('update')

    property_map = {
        'frontend_ip_configurations': 'frontend-ip',
        'inbound_nat_rules': 'inbound-nat-rule',
        'inbound_nat_pools': 'inbound-nat-pool',
        'backend_address_pools': 'address-pool',
        'load_balancing_rules': 'rule',
        'probes': 'probe',
    }
    for subresource, alias in property_map.items():
        with self.command_group('network lb {}'.format(alias), network_util) as g:
            g.command('list', list_network_resource_property('load_balancers', subresource))
            g.show_command('show', get_network_resource_property_entry('load_balancers', subresource))
            g.command('delete', delete_network_resource_property_entry('load_balancers', subresource))

    with self.command_group('network lb frontend-ip', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_frontend_ip_configuration', validator=process_lb_frontend_ip_namespace)
        g.generic_update_command('update', child_collection_prop_name='frontend_ip_configurations',
                                 custom_func_name='set_lb_frontend_ip_configuration',
                                 validator=process_lb_frontend_ip_namespace)

    with self.command_group('network lb inbound-nat-rule', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_inbound_nat_rule')
        g.generic_update_command('update', child_collection_prop_name='inbound_nat_rules',
                                 custom_func_name='set_lb_inbound_nat_rule')

    with self.command_group('network lb inbound-nat-pool', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_inbound_nat_pool')
        g.generic_update_command('update', child_collection_prop_name='inbound_nat_pools',
                                 custom_func_name='set_lb_inbound_nat_pool')

    with self.command_group('network lb address-pool', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_backend_address_pool')

    with self.command_group('network lb rule', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_rule')
        g.generic_update_command('update', child_collection_prop_name='load_balancing_rules',
                                 custom_func_name='set_lb_rule')

    with self.command_group('network lb probe', network_lb_sdk) as g:
        g.custom_command('create', 'create_lb_probe')
        g.generic_update_command('update', child_collection_prop_name='probes',
                                 custom_func_name='set_lb_probe')

    with self.command_group('network lb outbound-rule', network_lb_sdk, min_api='2018-07-01') as g:
        g.custom_command('create', 'create_lb_outbound_rule', validator=process_lb_outbound_rule_namespace)
        g.generic_update_command('update', child_collection_prop_name='outbound_rules',
                                 custom_func_name='set_lb_outbound_rule', validator=process_lb_outbound_rule_namespace)

    with self.command_group('network lb outbound-rule', network_util, min_api='2018-07-01') as g:
        g.command('list', list_network_resource_property('load_balancers', 'outbound_rules'))
        g.show_command('show', get_network_resource_property_entry('load_balancers', 'outbound_rules'))
        g.command('delete', delete_network_resource_property_entry('load_balancers', 'outbound_rules'))
    # endregion

    # region LocalGateways
    with self.command_group('network local-gateway', network_lgw_sdk) as g:
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list', table_transformer=transform_local_gateway_table_output)
        g.custom_command('create', 'create_local_gateway', supports_no_wait=True, validator=process_local_gateway_create_namespace)
        g.generic_update_command('update', custom_func_name='update_local_gateway', supports_no_wait=True)
        g.wait_command('wait')
    # endregion

    # region NetworkInterfaces: (NIC)
    with self.command_group('network nic', network_nic_sdk) as g:
        g.custom_command('create', 'create_nic', transform=transform_nic_create_output, validator=process_nic_create_namespace, supports_no_wait=True)
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'list_nics')
        g.command('show-effective-route-table', 'get_effective_route_table', min_api='2016-09-01')
        g.command('list-effective-nsg', 'list_effective_network_security_groups', min_api='2016-09-01')
        g.generic_update_command('update', custom_func_name='update_nic', supports_no_wait=True)
        g.wait_command('wait')

    resource = 'network_interfaces'
    subresource = 'ip_configurations'
    with self.command_group('network nic ip-config', network_nic_sdk) as g:
        g.custom_command('create', 'create_nic_ip_config')
        g.generic_update_command('update',
                                 child_collection_prop_name='ip_configurations', child_arg_name='ip_config_name',
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
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_nsgs')
        g.custom_command('create', 'create_nsg', transform=transform_nsg_create_output)
        g.generic_update_command('update')

    with self.command_group('network nsg rule', network_nsg_rule_sdk) as g:
        g.command('delete', 'delete')
        g.custom_command('list', 'list_nsg_rules', table_transformer=lambda x: [transform_nsg_rule_table_output(i) for i in x])
        g.show_command('show', 'get', table_transformer=transform_nsg_rule_table_output)
        g.custom_command('create', 'create_nsg_rule_2017_06_01', min_api='2017-06-01')
        g.generic_update_command('update', setter_arg_name='security_rule_parameters', min_api='2017-06-01',
                                 custom_func_name='update_nsg_rule_2017_06_01', doc_string_source='SecurityRule')
        g.custom_command('create', 'create_nsg_rule_2017_03_01', max_api='2017-03-01')
        g.generic_update_command('update', max_api='2017-03-01', setter_arg_name='security_rule_parameters',
                                 custom_func_name='update_nsg_rule_2017_03_01', doc_string_source='SecurityRule')
    # endregion

    # region NetworkProfiles
    with self.command_group('network profile', network_profile_sdk) as g:
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('list', 'list_network_profiles')
        g.show_command('show')
    # endregion

    # region NetworkWatchers
    with self.command_group('network watcher', network_watcher_sdk, client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('configure', 'configure_network_watcher')
        g.command('list', 'list_all')
        g.custom_command('test-ip-flow', 'check_nw_ip_flow', client_factory=cf_network_watcher)
        g.custom_command('test-connectivity', 'check_nw_connectivity', client_factory=cf_network_watcher, validator=process_nw_test_connectivity_namespace)
        g.custom_command('show-next-hop', 'show_nw_next_hop', client_factory=cf_network_watcher)
        g.custom_command('show-security-group-view', 'show_nw_security_view', client_factory=cf_network_watcher)
        g.custom_command('show-topology', 'show_topology_watcher', validator=process_nw_topology_namespace)
        g.custom_command('run-configuration-diagnostic', 'run_network_configuration_diagnostic', client_factory=cf_network_watcher, min_api='2018-06-01', validator=process_nw_config_diagnostic_namespace)

    with self.command_group('network watcher connection-monitor', network_watcher_cm_sdk, client_factory=cf_connection_monitor, min_api='2018-01-01') as g:
        g.custom_command('create', 'create_nw_connection_monitor', validator=process_nw_cm_create_namespace)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('stop', 'stop')
        g.command('start', 'start')
        g.command('query', 'query')
        g.command('list', 'list')

    with self.command_group('network watcher packet-capture', network_watcher_pc_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_nw_packet_capture', client_factory=cf_packet_capture, validator=process_nw_packet_capture_create_namespace)
        g.show_command('show', 'get')
        g.command('show-status', 'get_status')
        g.command('delete', 'delete')
        g.command('stop', 'stop')
        g.command('list', 'list')

    with self.command_group('network watcher flow-log', client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('configure', 'set_nsg_flow_logging', validator=process_nw_flow_log_set_namespace)
        g.custom_show_command('show', 'show_nsg_flow_logging', validator=process_nw_flow_log_show_namespace)

    with self.command_group('network watcher troubleshooting', client_factory=cf_network_watcher, min_api='2016-09-01') as g:
        g.custom_command('start', 'start_nw_troubleshooting', supports_no_wait=True, validator=process_nw_troubleshooting_start_namespace)
        g.custom_show_command('show', 'show_nw_troubleshooting_result', validator=process_nw_troubleshooting_show_namespace)
    # endregion

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'
    public_ip_show_table_transform = public_ip_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if self.supported_api_version(min_api='2017-06-01') else ' ')

    with self.command_group('network public-ip', network_public_ip_sdk) as g:
        g.command('delete', 'delete')
        g.show_command('show', 'get', table_transformer=public_ip_show_table_transform)
        g.custom_command('list', 'list_public_ips', table_transformer='[].' + public_ip_show_table_transform)
        g.custom_command('create', 'create_public_ip', transform=transform_public_ip_create_output, validator=process_public_ip_create_namespace)
        g.generic_update_command('update', custom_func_name='update_public_ip')

    with self.command_group('network public-ip prefix', network_public_ip_prefix_sdk, client_factory=cf_public_ip_prefixes) as g:
        g.custom_command('create', 'create_public_ip_prefix')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_public_ip_prefixes')
        g.show_command('show')
        g.generic_update_command('update', custom_func_name='update_public_ip_prefix')

    # endregion

    # region RouteFilters
    with self.command_group('network route-filter', network_rf_sdk, min_api='2016-12-01') as g:
        g.custom_command('create', 'create_route_filter', client_factory=cf_route_filters)
        g.custom_command('list', 'list_route_filters', client_factory=cf_route_filters)
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.generic_update_command('update', setter_arg_name='route_filter_parameters')

    with self.command_group('network route-filter rule', network_rfr_sdk, min_api='2016-12-01') as g:
        g.custom_command('create', 'create_route_filter_rule', client_factory=cf_route_filter_rules)
        g.command('list', 'list_by_route_filter')
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.generic_update_command('update', setter_arg_name='route_filter_rule_parameters')
        sc_path = 'azure.mgmt.network.operations#BgpServiceCommunitiesOperations.{}'
        g.command('list-service-communities', 'list', operations_tmpl=sc_path, client_factory=cf_service_community, table_transformer=transform_service_community_table_output)

    # endregion

    # region RouteTables
    with self.command_group('network route-table', network_rt_sdk) as g:
        g.custom_command('create', 'create_route_table', validator=process_route_table_create_namespace)
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'list_route_tables')
        g.generic_update_command('update', custom_func_name='update_route_table')

    network_rtr_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations.routes_operations#RoutesOperations.{}',
        client_factory=cf_routes
    )
    with self.command_group('network route-table route', network_rtr_sdk) as g:
        g.custom_command('create', 'create_route')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', setter_arg_name='route_parameters', custom_func_name='update_route')

    # endregion

    # region ServiceEndpoint
    with self.command_group('network service-endpoint', network_endpoint_service_sdk) as g:
        g.command('list', 'list')

    with self.command_group('network service-endpoint policy', network_sepp_sdk) as g:
        g.custom_command('create', 'create_service_endpoint_policy')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_service_endpoint_policies')
        g.show_command('show')
        g.generic_update_command('update', custom_func_name='update_service_endpoint_policy')

    with self.command_group('network service-endpoint policy-definition', network_sepd_sdk) as g:
        g.custom_command('create', 'create_service_endpoint_policy_definition')
        g.command('delete', 'delete')
        g.command('list', 'list_by_resource_group')
        g.show_command('show')
        g.generic_update_command('update', custom_func_name='update_service_endpoint_policy_definition',
                                 setter_arg_name='service_endpoint_policy_definitions')
    # endregion

    # region TrafficManagers
    with self.command_group('network traffic-manager profile', network_tmp_sdk) as g:
        g.command('check-dns', 'check_traffic_manager_relative_dns_name_availability')
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

        tm_geographic_path = 'azure.mgmt.trafficmanager.operations.geographic_hierarchies_operations#GeographicHierarchiesOperations.{}'
        g.command('show-geographic-hierarchy', 'get_default', client_factory=cf_tm_geographic, operations_tmpl=tm_geographic_path, table_transformer=transform_geographic_hierachy_table_output)

    # endregion

    # region VirtualNetworks
    with self.command_group('network vnet', network_vnet_sdk) as g:
        g.command('delete', 'delete')
        g.custom_command('list', 'list_vnet', table_transformer=transform_vnet_table_output)
        g.show_command('show', 'get')
        g.command('check-ip-address', 'check_ip_address_availability', min_api='2016-09-01')
        g.custom_command('create', 'create_vnet', transform=transform_vnet_create_output, validator=process_vnet_create_namespace)
        g.generic_update_command('update', custom_func_name='update_vnet')
        g.command('list-endpoint-services', 'list', command_type=network_endpoint_service_sdk)

    with self.command_group('network vnet peering', network_vnet_peering_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_vnet_peering')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('delete', 'delete')
        g.generic_update_command('update', setter_name='update_vnet_peering', setter_type=network_custom)

    with self.command_group('network vnet subnet', network_subnet_sdk) as g:
        g.custom_command('create', 'create_subnet')
        g.command('delete', 'delete')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.generic_update_command('update', setter_arg_name='subnet_parameters',
                                 custom_func_name='update_subnet')
        g.custom_command('list-available-delegations', 'list_avail_subnet_delegations', min_api='2018-08-01', validator=process_list_delegations_namespace)
    # endregion

    # region VirtualNetworkGateways
    with self.command_group('network vnet-gateway', network_vgw_sdk, min_api='2016-09-01') as g:
        g.custom_command('create', 'create_vnet_gateway', supports_no_wait=True, transform=transform_vnet_gateway_create_output, validator=process_vnet_gateway_create_namespace)
        g.generic_update_command('update', custom_func_name='update_vnet_gateway', supports_no_wait=True, validator=process_vnet_gateway_update_namespace)
        g.wait_command('wait')
        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.command('reset', 'reset')
        g.command('list-bgp-peer-status', 'get_bgp_peer_status')
        g.command('list-advertised-routes', 'get_advertised_routes')
        g.command('list-learned-routes', 'get_learned_routes')

    with self.command_group('network vnet-gateway vpn-client', network_vgw_sdk, client_factory=cf_virtual_network_gateways) as g:
        g.custom_command('generate', 'generate_vpn_client')
        g.command('show-url', 'get_vpn_profile_package_url', min_api='2017-08-01')

    with self.command_group('network vnet-gateway revoked-cert', network_vgw_sdk) as g:
        g.custom_command('create', 'create_vnet_gateway_revoked_cert')
        g.custom_command('delete', 'delete_vnet_gateway_revoked_cert')

    with self.command_group('network vnet-gateway root-cert', network_vgw_sdk) as g:
        g.custom_command('create', 'create_vnet_gateway_root_cert')
        g.custom_command('delete', 'delete_vnet_gateway_root_cert')

    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection', network_vpn_sdk) as g:
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
        g.command('delete', 'delete')
        g.show_command('show', 'get', transform=transform_vpn_connection)
        g.command('list', 'list', transform=transform_vpn_connection_list)
        g.generic_update_command('update', custom_func_name='update_vpn_connection')

    with self.command_group('network vpn-connection shared-key', network_vpn_sdk) as g:
        g.show_command('show', 'get_shared_key')
        g.command('reset', 'reset_shared_key')
        g.generic_update_command('update', setter_name='set_shared_key')

    with self.command_group('network vpn-connection ipsec-policy', network_vpn_sdk, min_api='2017-03-01') as g:
        g.custom_command('add', 'add_vpn_conn_ipsec_policy', supports_no_wait=True, doc_string_source='IpsecPolicy')
        g.custom_command('list', 'list_vpn_conn_ipsec_policies')
        g.custom_command('clear', 'clear_vpn_conn_ipsec_policies', supports_no_wait=True)
    # endregion
