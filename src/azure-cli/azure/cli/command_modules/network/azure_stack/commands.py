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

from azure.cli.command_modules.network.azure_stack._client_factory import (
    cf_application_gateways, cf_express_route_circuit_authorizations,
    cf_express_route_circuit_peerings, cf_express_route_circuits,
    cf_express_route_service_providers,
    cf_network_security_groups, cf_network_watcher, cf_packet_capture,
    cf_dns_mgmt_record_sets, cf_dns_mgmt_zones,
    cf_security_rules,
    cf_connection_monitor, cf_dns_references, cf_private_endpoints,
    cf_express_route_circuit_connections, cf_express_route_gateways, cf_express_route_connections,
    cf_express_route_ports, cf_express_route_port_locations, cf_express_route_links, cf_app_gateway_waf_policy,
    cf_private_link_services, cf_private_endpoint_types, cf_peer_express_route_circuit_connections,
    cf_virtual_router, cf_virtual_router_peering, cf_flow_logs,
    cf_private_dns_zone_groups, cf_virtual_hub,
    cf_custom_ip_prefixes)
from azure.cli.command_modules.network.azure_stack._util import (
    list_network_resource_property, get_network_resource_property_entry, delete_network_resource_property_entry)
from azure.cli.command_modules.network.azure_stack._format import (
    transform_dns_record_set_output,
    transform_dns_record_set_table_output, transform_dns_zone_table_output,
    transform_traffic_manager_create_output,
    transform_nsg_create_output,
    transform_geographic_hierachy_table_output,
    transform_service_community_table_output, transform_waf_rule_sets_table_output,
    transform_nsg_rule_table_output)
from azure.cli.command_modules.network.azure_stack._validators import (
    get_network_watcher_from_location,
    process_ag_create_namespace, process_ag_http_listener_create_namespace, process_ag_listener_create_namespace, process_ag_settings_create_namespace, process_ag_http_settings_create_namespace,
    process_ag_rule_create_namespace, process_ag_routing_rule_create_namespace, process_ag_ssl_policy_set_namespace, process_ag_url_path_map_create_namespace,
    process_ag_url_path_map_rule_create_namespace, process_auth_create_namespace,
    process_lb_create_namespace, process_nw_cm_v2_create_namespace,
    process_nw_cm_v2_endpoint_namespace, process_nw_cm_v2_test_configuration_namespace,
    process_nw_cm_v2_test_group, process_nw_cm_v2_output_namespace,
    process_nw_flow_log_set_namespace, process_nw_flow_log_create_namespace, process_nw_flow_log_show_namespace,
    process_nw_packet_capture_create_namespace, process_nw_test_connectivity_namespace, process_nw_topology_namespace,
    process_nw_troubleshooting_start_namespace, process_nw_troubleshooting_show_namespace,
    process_vpn_connection_create_namespace,
    process_nw_config_diagnostic_namespace,
    process_appgw_waf_policy_update)

NETWORK_VROUTER_DEPRECATION_INFO = 'network routeserver'
NETWORK_VROUTER_PEERING_DEPRECATION_INFO = 'network routeserver peering'


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # region Command Types
    custom_command_type = self.module_kwargs["custom_command_type"]
    custom_operations_tmpl = custom_command_type.settings["operations_tmpl"]

    network_ag_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ApplicationGatewaysOperations.{}',
        client_factory=cf_application_gateways
    )

    network_ag_waf_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#WebApplicationFirewallPoliciesOperations.{}',
        client_factory=cf_app_gateway_waf_policy
    )

    network_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.azure_stack._util#{}',
        client_factory=None
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

    network_nsg_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkSecurityGroupsOperations.{}',
        client_factory=cf_network_security_groups
    )

    network_nsg_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#SecurityRulesOperations.{}',
        client_factory=cf_security_rules
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
        operations_tmpl=custom_operations_tmpl,
        client_factory=cf_flow_logs,
    )

    network_watcher_pc_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#PacketCapturesOperations.{}',
        client_factory=cf_packet_capture
    )

    network_virtual_hub_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualHubsOperations.{}',
        client_factory=cf_virtual_hub,
        min_api='2020-07-01'
    )

    network_virtual_hub_update_sdk = CliCommandType(
        operations_tmpl=custom_operations_tmpl,
        client_factory=cf_virtual_hub,
        min_api='2020-07-01'
    )

    network_vrouter_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualRoutersOperations.{}',
        client_factory=cf_virtual_router,
        min_api='2019-08-01'
    )

    network_vrouter_update_sdk = CliCommandType(
        operations_tmpl=custom_operations_tmpl,
        client_factory=cf_virtual_router,
        min_api='2019-08-01'
    )

    network_vrouter_peering_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualRouterPeeringsOperations.{}',
        client_factory=cf_virtual_router_peering,
        min_api='2019-08-01'
    )

    network_vrouter_peering_update_sdk = CliCommandType(
        operations_tmpl=custom_operations_tmpl,
        client_factory=cf_virtual_router_peering,
        min_api='2019-08-01'
    )

    network_custom_ip_prefix_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#CustomIPPrefixesOperations.{}',
        client_factory=cf_custom_ip_prefixes,
        min_api='2020-06-01'
    )

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
        {'prop': 'http_listeners', 'name': 'http-listener', 'validator': process_ag_http_listener_create_namespace},
        {'prop': 'request_routing_rules', 'name': 'rule', 'validator': process_ag_rule_create_namespace},
        {'prop': 'probes', 'name': 'probe'},
        {'prop': 'url_path_maps', 'name': 'url-path-map', 'validator': process_ag_url_path_map_create_namespace},
        {'prop': 'rewrite_rule_sets', 'name': 'rewrite-rule set'}
    ]
    if self.supported_api_version(min_api='2018-08-01'):
        subresource_properties.append({'prop': 'trusted_root_certificates', 'name': 'root-cert'})
    if self.supported_api_version(min_api='2021-08-01'):
        subresource_properties.append({'prop': 'backend_settings_collection', 'name': 'settings', 'validator': process_ag_settings_create_namespace})
        subresource_properties.append({'prop': 'listeners', 'name': 'listener', 'validator': process_ag_listener_create_namespace})
        subresource_properties.append({'prop': 'routing_rules', 'name': 'routing-rule', 'validator': process_ag_routing_rule_create_namespace})

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
    with self.command_group('network application-gateway waf-policy', min_api='2018-12-01') as g:
        g.custom_command('create', 'create_ag_waf_policy')

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

    with self.command_group('network application-gateway waf-policy managed-rule rule-set', min_api='2019-09-01') as g:
        g.custom_command('add', 'add_waf_managed_rule_set')
        g.custom_command('remove', 'remove_waf_managed_rule_set')
        g.custom_command('list', 'list_waf_managed_rule_set')
        g.custom_command('update', 'update_waf_managed_rule_set', validator=process_appgw_waf_policy_update)

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

    with self.command_group('network application-gateway client-cert', network_ag_sdk, min_api='2020-06-01') as g:
        g.custom_command('add', 'add_trusted_client_certificate')
        g.custom_command('remove', 'remove_trusted_client_certificate')
        g.custom_command('list', 'list_trusted_client_certificate')
        g.custom_show_command('show', 'show_trusted_client_certificate')
        g.custom_command('update', 'update_trusted_client_certificate')

    with self.command_group('network application-gateway ssl-profile', network_ag_sdk, min_api='2020-06-01') as g:
        g.custom_command('add', 'add_ssl_profile')
        g.custom_command('remove', 'remove_ssl_profile')
        g.custom_command('list', 'list_ssl_profile')
        g.custom_show_command('show', 'show_ssl_profile')
        g.custom_command('update', 'update_ssl_profile')

    # endregion

    # region DdosProtectionPlans
    with self.command_group('network ddos-protection', min_api='2018-02-01') as g:
        g.custom_command('create', 'create_ddos_plan')
        g.custom_command('update', 'update_ddos_plan')
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
    with self.command_group('network lb') as g:
        g.custom_command('create', 'create_load_balancer',
                         transform=DeploymentOutputLongRunningOperation(self.cli_ctx),
                         supports_no_wait=True,
                         table_transformer=deployment_validate_table_format,
                         validator=process_lb_create_namespace,
                         exception_handler=handle_template_based_exception)
    # endregion

    # region NetworkSecurityGroups
    with self.command_group('network nsg', network_nsg_sdk) as g:
        g.custom_command('create', 'create_nsg', transform=transform_nsg_create_output)
        g.generic_update_command('update', setter_name='begin_create_or_update')

    with self.command_group('network nsg rule', network_nsg_rule_sdk) as g:
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
        g.custom_command('create', 'create_nw_connection_monitor', validator=process_nw_cm_v2_create_namespace)
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
        g.custom_show_command('show', 'show_nw_flow_logging', validator=process_nw_flow_log_show_namespace)

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

    # region RouteFilters
    from azure.cli.command_modules.network.aaz.latest.network.route_filter.rule import ListServiceCommunities
    self.command_table['network route-filter rule list-service-communities'] = ListServiceCommunities(loader=self, table_transformer=transform_service_community_table_output)
    # endregion

    # region TrafficManagers
    with self.command_group('network traffic-manager profile') as g:
        g.custom_command('create', 'create_traffic_manager_profile', transform=transform_traffic_manager_create_output)
        g.custom_command('update', 'update_traffic_manager_profile')

    with self.command_group('network traffic-manager endpoint') as g:
        g.custom_command('create', 'create_traffic_manager_endpoint')
        g.custom_command('update', 'update_traffic_manager_endpoint')
        g.custom_command('list', 'list_traffic_manager_endpoints')

    from azure.cli.command_modules.network.aaz.latest.network.traffic_manager.endpoint import ShowGeographicHierarchy
    self.command_table['network traffic-manager endpoint show-geographic-hierarchy'] = ShowGeographicHierarchy(loader=self, table_transformer=transform_geographic_hierachy_table_output)
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection') as g:
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
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
        g.custom_command('delete', 'delete_virtual_hub', supports_no_wait=True, confirmation=True)
    # endregion

    # region PrivateLinkResource and PrivateEndpointConnection
    plr_and_pec_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.network.azure_stack.private_link_resource_and_endpoint_connections.custom#{}')
    with self.command_group('network private-link-resource', custom_command_type=plr_and_pec_custom) as g:
        g.custom_show_command('list', 'list_private_link_resource')
    with self.command_group('network private-endpoint-connection', custom_command_type=plr_and_pec_custom) as g:
        g.custom_command('approve', 'approve_private_endpoint_connection')
        g.custom_command('reject', 'reject_private_endpoint_connection')
        g.custom_command('delete', 'remove_private_endpoint_connection', confirmation=True)
        g.custom_show_command('show', 'show_private_endpoint_connection')
        g.custom_command('list', 'list_private_endpoint_connection')
    # endregion
