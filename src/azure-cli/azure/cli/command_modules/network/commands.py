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
    cf_application_gateways,
    cf_load_balancers,
    cf_network_interfaces, cf_network_watcher, cf_packet_capture,
    cf_virtual_network_gateway_connections,
    cf_virtual_network_gateways,
    cf_dns_mgmt_record_sets, cf_dns_mgmt_zones,
    cf_connection_monitor,
    cf_dns_references,
    cf_virtual_router, cf_virtual_router_peering, cf_flow_logs,
    cf_load_balancer_backend_pools)
from azure.cli.command_modules.network._util import (
    list_network_resource_property, get_network_resource_property_entry, delete_network_resource_property_entry,
    delete_lb_resource_property_entry)
from azure.cli.command_modules.network._format import (
    transform_local_gateway_table_output, transform_dns_record_set_output,
    transform_dns_record_set_table_output, transform_dns_zone_table_output,
    transform_public_ip_create_output,
    transform_traffic_manager_create_output, transform_nic_create_output,
    transform_vpn_connection, transform_vpn_connection_list,
    transform_geographic_hierachy_table_output,
    transform_service_community_table_output, transform_waf_rule_sets_table_output,
    transform_network_usage_table, transform_nsg_rule_table_output,
    transform_vnet_table_output, transform_effective_route_table, transform_effective_nsg,
    transform_vnet_gateway_routes_table, transform_vnet_gateway_bgp_peer_table)
from azure.cli.command_modules.network._validators import (
    get_network_watcher_from_location,
    process_ag_create_namespace,
    process_nic_create_namespace,
    process_lb_create_namespace, process_nw_cm_v2_create_namespace,
    process_nw_cm_v2_endpoint_namespace, process_nw_cm_v2_test_configuration_namespace,
    process_nw_cm_v2_test_group, process_nw_cm_v2_output_namespace,
    process_nw_flow_log_set_namespace, process_nw_flow_log_create_namespace, process_nw_flow_log_show_namespace,
    process_nw_packet_capture_create_namespace, process_nw_test_connectivity_namespace, process_nw_topology_namespace,
    process_nw_troubleshooting_start_namespace, process_nw_troubleshooting_show_namespace,
    process_public_ip_create_namespace,
    process_vpn_connection_create_namespace,
    process_nw_config_diagnostic_namespace,
    process_appgw_waf_policy_update, process_cross_region_lb_create_namespace)

NETWORK_VROUTER_DEPRECATION_INFO = 'network routeserver'
NETWORK_VROUTER_PEERING_DEPRECATION_INFO = 'network routeserver peering'


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # region Command Types
    network_ag_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#ApplicationGatewaysOperations.{}',
        client_factory=cf_application_gateways
    )

    network_util = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network._util#{}',
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

    network_lb_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#LoadBalancersOperations.{}',
        client_factory=cf_load_balancers
    )

    network_lb_backend_pool_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#LoadBalancerBackendAddressPoolsOperations.{}',
        client_factory=cf_load_balancer_backend_pools,
        min_api='2020-04-01'
    )

    network_nic_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#NetworkInterfacesOperations.{}',
        client_factory=cf_network_interfaces
    )

    network_vgw_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.network.operations#VirtualNetworkGatewaysOperations.{}',
        client_factory=cf_virtual_network_gateways
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

    network_nic_custom = CliCommandType(
        operations_tmpl='azure.cli.command_modules.network.custom#{}',
        client_factory=cf_network_interfaces
    )
    # endregion

    # region NetworkRoot
    with self.command_group('network'):
        from azure.cli.command_modules.network.custom import UsagesList
        self.command_table['network list-usages'] = UsagesList(loader=self,
                                                               table_transformer=transform_network_usage_table)
    # endregion

    # region ApplicationGateways
    with self.command_group("network application-gateway") as g:
        from .custom import ApplicationGatewayUpdate
        self.command_table["network application-gateway update"] = ApplicationGatewayUpdate(loader=self)
        g.custom_command("show-backend-health", "show_ag_backend_health")
        g.custom_command("create", "create_application_gateway",
                         transform=DeploymentOutputLongRunningOperation(self.cli_ctx),
                         supports_no_wait=True,
                         table_transformer=deployment_validate_table_format,
                         validator=process_ag_create_namespace,
                         exception_handler=handle_template_based_exception)

    with self.command_group("network application-gateway address-pool"):
        from .custom import AddressPoolCreate, AddressPoolUpdate
        self.command_table["network application-gateway address-pool create"] = AddressPoolCreate(loader=self)
        self.command_table["network application-gateway address-pool update"] = AddressPoolUpdate(loader=self)

    with self.command_group("network application-gateway auth-cert"):
        from .custom import AuthCertCreate, AuthCertUpdate
        self.command_table["network application-gateway auth-cert create"] = AuthCertCreate(loader=self)
        self.command_table["network application-gateway auth-cert update"] = AuthCertUpdate(loader=self)

    with self.command_group("network application-gateway root-cert"):
        from .custom import RootCertCreate, RootCertUpdate
        self.command_table["network application-gateway root-cert create"] = RootCertCreate(loader=self)
        self.command_table["network application-gateway root-cert update"] = RootCertUpdate(loader=self)

    with self.command_group("network application-gateway client-cert"):
        from .custom import ClientCertAdd, ClientCertRemove, ClientCertUpdate
        self.command_table["network application-gateway client-cert add"] = ClientCertAdd(loader=self)
        self.command_table["network application-gateway client-cert remove"] = ClientCertRemove(loader=self)
        self.command_table["network application-gateway client-cert update"] = ClientCertUpdate(loader=self)

    with self.command_group("network application-gateway frontend-ip"):
        from .custom import FrontedIPCreate, FrontedIPUpdate
        self.command_table["network application-gateway frontend-ip create"] = FrontedIPCreate(loader=self)
        self.command_table["network application-gateway frontend-ip update"] = FrontedIPUpdate(loader=self)

    with self.command_group("network application-gateway settings"):
        from .custom import SettingsCreate, SettingsUpdate
        self.command_table["network application-gateway settings create"] = SettingsCreate(loader=self)
        self.command_table["network application-gateway settings update"] = SettingsUpdate(loader=self)

    with self.command_group("network application-gateway http-settings"):
        from .custom import HTTPSettingsCreate, HTTPSettingsUpdate
        self.command_table["network application-gateway http-settings create"] = HTTPSettingsCreate(loader=self)
        self.command_table["network application-gateway http-settings update"] = HTTPSettingsUpdate(loader=self)

    with self.command_group("network application-gateway listener"):
        from .custom import ListenerCreate, ListenerUpdate
        self.command_table["network application-gateway listener create"] = ListenerCreate(loader=self)
        self.command_table["network application-gateway listener update"] = ListenerUpdate(loader=self)

    with self.command_group("network application-gateway http-listener"):
        from .custom import HTTPListenerCreate, HTTPListenerUpdate
        self.command_table["network application-gateway http-listener create"] = HTTPListenerCreate(loader=self)
        self.command_table["network application-gateway http-listener update"] = HTTPListenerUpdate(loader=self)

    with self.command_group("network application-gateway identity") as g:
        from .custom import IdentityAssign
        self.command_table["network application-gateway identity assign"] = IdentityAssign(loader=self)
        g.custom_command("remove", "remove_ag_identity", supports_no_wait=True)

    with self.command_group("network application-gateway redirect-config"):
        from .custom import RedirectConfigCreate, RedirectConfigUpdate
        self.command_table["network application-gateway redirect-config create"] = RedirectConfigCreate(loader=self)
        self.command_table["network application-gateway redirect-config update"] = RedirectConfigUpdate(loader=self)

    with self.command_group("network application-gateway rewrite-rule"):
        from .custom import AGRewriteRuleCreate, AGRewriteRuleUpdate
        self.command_table["network application-gateway rewrite-rule create"] = AGRewriteRuleCreate(loader=self)
        self.command_table["network application-gateway rewrite-rule update"] = AGRewriteRuleUpdate(loader=self)

    with self.command_group("network application-gateway routing-rule"):
        from .custom import RoutingRuleCreate, RoutingRuleUpdate
        self.command_table["network application-gateway routing-rule create"] = RoutingRuleCreate(loader=self)
        self.command_table["network application-gateway routing-rule update"] = RoutingRuleUpdate(loader=self)

    with self.command_group("network application-gateway rule"):
        from .custom import RuleCreate, RuleUpdate
        self.command_table["network application-gateway rule create"] = RuleCreate(loader=self)
        self.command_table["network application-gateway rule update"] = RuleUpdate(loader=self)

    with self.command_group("network application-gateway ssl-cert"):
        from .custom import SSLCertCreate, SSLCertUpdate
        self.command_table["network application-gateway ssl-cert create"] = SSLCertCreate(loader=self)
        self.command_table["network application-gateway ssl-cert update"] = SSLCertUpdate(loader=self)

    with self.command_group("network application-gateway ssl-policy"):
        from .custom import SSLPolicySet
        self.command_table["network application-gateway ssl-policy set"] = SSLPolicySet(loader=self)

    with self.command_group("network application-gateway ssl-profile"):
        from .custom import SSLProfileAdd, SSLProfileUpdate, SSLProfileRemove
        self.command_table["network application-gateway ssl-profile add"] = SSLProfileAdd(loader=self)
        self.command_table["network application-gateway ssl-profile update"] = SSLProfileUpdate(loader=self)
        self.command_table["network application-gateway ssl-profile remove"] = SSLProfileRemove(loader=self)

    with self.command_group("network application-gateway url-path-map"):
        from .custom import URLPathMapCreate, URLPathMapUpdate, URLPathMapRuleCreate
        self.command_table["network application-gateway url-path-map create"] = URLPathMapCreate(loader=self)
        self.command_table["network application-gateway url-path-map update"] = URLPathMapUpdate(loader=self)
        self.command_table["network application-gateway url-path-map rule create"] = URLPathMapRuleCreate(loader=self)

    with self.command_group("network application-gateway waf-config") as g:
        g.custom_command("list-rule-sets", "list_ag_waf_rule_sets", table_transformer=transform_waf_rule_sets_table_output)
        g.custom_command("set", "set_ag_waf_config", supports_no_wait=True)
        g.custom_show_command("show", "show_ag_waf_config")

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
    with self.command_group("network application-gateway waf-policy"):
        from .custom import WAFCreate
        self.command_table["network application-gateway waf-policy create"] = WAFCreate(loader=self)

    with self.command_group("network application-gateway waf-policy custom-rule match-condition"):
        from .custom import WAFCustomRuleMatchConditionAdd
        self.command_table["network application-gateway waf-policy custom-rule match-condition add"] = WAFCustomRuleMatchConditionAdd(loader=self)

    with self.command_group("network application-gateway waf-policy managed-rule exclusion") as g:
        g.custom_command("remove", "remove_waf_managed_rule_exclusion")
        g.custom_command("list", "list_waf_managed_rules")

    with self.command_group("network application-gateway waf-policy managed-rule exclusion rule-set") as g:
        g.custom_command("add", "add_waf_exclusion_rule_set")
        g.custom_command("remove", "remove_waf_exclusion_rule_set")
        g.custom_command("list", "list_waf_managed_rules")

    with self.command_group("network application-gateway waf-policy managed-rule rule-set") as g:
        g.custom_command("add", "add_waf_managed_rule_set")
        g.custom_command("remove", "remove_waf_managed_rule_set")
        g.custom_command("list", "list_waf_managed_rules")
        g.custom_command("update", "update_waf_managed_rule_set", validator=process_appgw_waf_policy_update)

    with self.command_group("network application-gateway waf-policy policy-setting") as g:
        from .custom import WAFPolicySettingUpdate
        self.command_table["network application-gateway waf-policy policy-setting update"] = WAFPolicySettingUpdate(loader=self)
        g.custom_command("list", "list_waf_policy_setting")
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
    with self.command_group('network express-route'):
        from azure.cli.command_modules.network.custom import ExpressRouteCreate, ExpressRouteUpdate
        self.command_table['network express-route create'] = ExpressRouteCreate(loader=self)
        self.command_table['network express-route update'] = ExpressRouteUpdate(loader=self)

    with self.command_group('network express-route gateway connection'):
        from azure.cli.command_modules.network.custom import ExpressRouteConnectionUpdate, ExpressRouteConnectionCreate
        self.command_table['network express-route gateway connection create'] = ExpressRouteConnectionCreate(loader=self)
        self.command_table['network express-route gateway connection update'] = ExpressRouteConnectionUpdate(loader=self)

    with self.command_group('network express-route peering'):
        from azure.cli.command_modules.network.custom import ExpressRoutePeeringCreate, ExpressRoutePeeringUpdate
        self.command_table['network express-route peering create'] = ExpressRoutePeeringCreate(loader=self)
        self.command_table['network express-route peering update'] = ExpressRoutePeeringUpdate(loader=self)

    with self.command_group('network express-route port') as g:
        from azure.cli.command_modules.network.custom import ExpressRoutePortCreate
        self.command_table['network express-route port create'] = ExpressRoutePortCreate(loader=self)
        g.custom_command('generate-loa', 'download_generated_loa_as_pdf')

    with self.command_group('network express-route port identity'):
        from azure.cli.command_modules.network.custom import ExpressRoutePortIdentityAssign
        self.command_table['network express-route port identity assign'] = ExpressRoutePortIdentityAssign(loader=self)

    with self.command_group('network express-route port link'):
        from azure.cli.command_modules.network.custom import ExpressRoutePortLinkUpdate
        self.command_table['network express-route port link update'] = ExpressRoutePortLinkUpdate(loader=self)
    # endregion

    # region PrivateEndpoint
    with self.command_group('network private-endpoint'):
        from azure.cli.command_modules.network.custom import PrivateEndpointCreate, PrivateEndpointUpdate
        self.command_table['network private-endpoint create'] = PrivateEndpointCreate(loader=self)
        self.command_table['network private-endpoint update'] = PrivateEndpointUpdate(loader=self)

    with self.command_group('network private-endpoint dns-zone-group'):
        from azure.cli.command_modules.network.custom import PrivateEndpointPrivateDnsZoneGroupCreate, \
            PrivateEndpointPrivateDnsZoneAdd, PrivateEndpointPrivateDnsZoneRemove
        self.command_table['network private-endpoint dns-zone-group create'] = \
            PrivateEndpointPrivateDnsZoneGroupCreate(loader=self)
        self.command_table['network private-endpoint dns-zone-group add'] = \
            PrivateEndpointPrivateDnsZoneAdd(loader=self)
        self.command_table['network private-endpoint dns-zone-group remove'] = \
            PrivateEndpointPrivateDnsZoneRemove(loader=self)

    with self.command_group('network private-endpoint ip-config'):
        from azure.cli.command_modules.network.custom import PrivateEndpointIpConfigAdd, PrivateEndpointIpConfigRemove
        self.command_table['network private-endpoint ip-config add'] = PrivateEndpointIpConfigAdd(loader=self)
        self.command_table['network private-endpoint ip-config remove'] = PrivateEndpointIpConfigRemove(loader=self)

    with self.command_group('network private-endpoint asg'):
        from azure.cli.command_modules.network.custom import PrivateEndpointAsgAdd, PrivateEndpointAsgRemove
        self.command_table['network private-endpoint asg add'] = PrivateEndpointAsgAdd(loader=self)
        self.command_table['network private-endpoint asg remove'] = PrivateEndpointAsgRemove(loader=self)
    # endregion

    # region PrivateLinkServices
    with self.command_group('network private-link-service'):
        from azure.cli.command_modules.network.custom import PrivateLinkServiceCreate, PrivateLinkServiceUpdate
        self.command_table['network private-link-service create'] = PrivateLinkServiceCreate(loader=self)
        self.command_table['network private-link-service update'] = PrivateLinkServiceUpdate(loader=self)

    with self.command_group('network private-link-service connection'):
        from azure.cli.command_modules.network.custom import PrivateEndpointConnectionUpdate
        self.command_table['network private-link-service connection update'] = PrivateEndpointConnectionUpdate(loader=self)

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
        g.custom_command('list-mapping', 'list_load_balancer_mapping')

    from .operations.load_balancer import LBFrontendIPCreate, LBFrontendIPUpdate
    self.command_table["network lb frontend-ip create"] = LBFrontendIPCreate(loader=self)
    self.command_table["network lb frontend-ip update"] = LBFrontendIPUpdate(loader=self)

    from .operations.load_balancer import LBInboundNatRuleCreate, LBInboundNatRuleUpdate
    self.command_table["network lb inbound-nat-rule create"] = LBInboundNatRuleCreate(loader=self)
    self.command_table["network lb inbound-nat-rule update"] = LBInboundNatRuleUpdate(loader=self)

    from .operations.load_balancer import LBInboundNatPoolCreate, LBInboundNatPoolUpdate
    self.command_table["network lb inbound-nat-pool create"] = LBInboundNatPoolCreate(loader=self)
    self.command_table["network lb inbound-nat-pool update"] = LBInboundNatPoolUpdate(loader=self)

    from .operations.load_balancer import LBRuleCreate, LBRuleUpdate
    self.command_table["network lb rule create"] = LBRuleCreate(loader=self)
    self.command_table["network lb rule update"] = LBRuleUpdate(loader=self)

    from .operations.load_balancer import LBOutboundRuleCreate, LBOutboundRuleUpdate
    self.command_table["network lb outbound-rule create"] = LBOutboundRuleCreate(loader=self)
    self.command_table["network lb outbound-rule update"] = LBOutboundRuleUpdate(loader=self)

    with self.command_group("network lb probe") as g:
        g.custom_command("create", "create_lb_probe")
        g.custom_command("update", "update_lb_probe")

    with self.command_group('network lb probe', network_util) as g:
        g.command('delete', delete_lb_resource_property_entry('load_balancers', 'probes'))

    with self.command_group('network lb address-pool', network_lb_backend_pool_sdk) as g:
        g.custom_command('create', 'create_lb_backend_address_pool')
        g.generic_update_command('update', setter_name='begin_create_or_update',
                                 custom_func_name='set_lb_backend_address_pool')
        g.show_command('show', 'get')
        g.command('list', 'list')
        g.custom_command('delete', 'delete_lb_backend_address_pool')

    with self.command_group('network lb address-pool address', network_lb_backend_pool_sdk, is_preview=True) as g:
        g.custom_command('add', 'add_lb_backend_address_pool_address')
        g.custom_command('remove', 'remove_lb_backend_address_pool_address')
        g.custom_command('list', 'list_lb_backend_address_pool_address')

    with self.command_group('network lb address-pool tunnel-interface', network_lb_backend_pool_sdk, min_api='2021-02-01', is_preview=True) as g:
        g.custom_command('add', 'add_lb_backend_address_pool_tunnel_interface')
        g.custom_command('update', 'update_lb_backend_address_pool_tunnel_interface')
        g.custom_command('remove', 'remove_lb_backend_address_pool_tunnel_interface')
        g.custom_command('list', 'list_lb_backend_address_pool_tunnel_interface')

    # endregion

    # region cross-region load balancer
    with self.command_group('network cross-region-lb') as g:
        g.custom_command('create', 'create_cross_region_load_balancer', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_cross_region_lb_create_namespace, exception_handler=handle_template_based_exception)

        from .aaz.latest.network.lb import Wait
        from .operations.load_balancer import CrossRegionLoadBalancerShow, CrossRegionLoadBalancerDelete, CrossRegionLoadBalancerUpdate, CrossRegionLoadBalancerList
        self.command_table['network cross-region-lb show'] = CrossRegionLoadBalancerShow(loader=self)
        self.command_table['network cross-region-lb delete'] = CrossRegionLoadBalancerDelete(loader=self)
        self.command_table['network cross-region-lb list'] = CrossRegionLoadBalancerList(loader=self)
        self.command_table['network cross-region-lb update'] = CrossRegionLoadBalancerUpdate(loader=self)
        self.command_table['network cross-region-lb wait'] = Wait(loader=self)

    with self.command_group('network cross-region-lb frontend-ip') as g:
        from .operations.load_balancer import CrossRegionLoadBalancerFrontendIPShow, CrossRegionLoadBalancerFrontendIPList, CrossRegionLoadBalancerFrontendIPDelete, CrossRegionLoadBalancerFrontendIPCreate, CrossRegionLoadBalancerFrontendIPUpdate
        self.command_table['network cross-region-lb frontend-ip show'] = CrossRegionLoadBalancerFrontendIPShow(loader=self)
        self.command_table['network cross-region-lb frontend-ip delete'] = CrossRegionLoadBalancerFrontendIPDelete(loader=self)
        self.command_table['network cross-region-lb frontend-ip list'] = CrossRegionLoadBalancerFrontendIPList(loader=self)
        self.command_table['network cross-region-lb frontend-ip create'] = CrossRegionLoadBalancerFrontendIPCreate(loader=self)
        self.command_table['network cross-region-lb frontend-ip update'] = CrossRegionLoadBalancerFrontendIPUpdate(loader=self)

    with self.command_group('network cross-region-lb rule') as g:
        from .operations.load_balancer import CrossRegionLoadBalancerRuleShow, CrossRegionLoadBalancerRuleDelete, CrossRegionLoadBalancerRuleList, CrossRegionLoadBalancerRuleCreate, CrossRegionLoadBalancerRuleUpdate
        self.command_table['network cross-region-lb rule show'] = CrossRegionLoadBalancerRuleShow(loader=self)
        self.command_table['network cross-region-lb rule delete'] = CrossRegionLoadBalancerRuleDelete(loader=self)
        self.command_table['network cross-region-lb rule list'] = CrossRegionLoadBalancerRuleList(loader=self)
        self.command_table['network cross-region-lb rule create'] = CrossRegionLoadBalancerRuleCreate(loader=self)
        self.command_table['network cross-region-lb rule update'] = CrossRegionLoadBalancerRuleUpdate(loader=self)

    with self.command_group('network cross-region-lb address-pool') as g:
        from .operations.load_balancer import CrossRegionLoadBalancerAddressPoolCreate, CrossRegionLoadBalancerAddressPoolUpdate
        self.command_table['network cross-region-lb address-pool create'] = CrossRegionLoadBalancerAddressPoolCreate(loader=self)
        self.command_table['network cross-region-lb address-pool update'] = CrossRegionLoadBalancerAddressPoolUpdate(loader=self)

    with self.command_group('network cross-region-lb address-pool address') as g:
        from .operations.load_balancer import CrossRegionLoadBalancerAddressPoolAddressAdd, CrossRegionLoadBalancerAddressPoolAddressUpdate, CrossRegionLoadBalancerAddressPoolAddressRemove
        self.command_table['network cross-region-lb address-pool address add'] = CrossRegionLoadBalancerAddressPoolAddressAdd(loader=self)
        self.command_table['network cross-region-lb address-pool address remove'] = CrossRegionLoadBalancerAddressPoolAddressRemove(loader=self)
        self.command_table['network cross-region-lb address-pool address update'] = CrossRegionLoadBalancerAddressPoolAddressUpdate(loader=self)

    cross_region_lb_property_map = {
        'probes': 'probe',
    }

    for subresource, alias in cross_region_lb_property_map.items():
        with self.command_group('network cross-region-lb {}'.format(alias), network_util) as g:
            g.command('list', list_network_resource_property('load_balancers', subresource))
            g.show_command('show', get_network_resource_property_entry('load_balancers', subresource))
            g.command('delete', delete_lb_resource_property_entry('load_balancers', subresource))

    with self.command_group('network cross-region-lb probe', network_lb_sdk) as g:
        g.custom_command('create', 'create_cross_lb_probe')
        g.generic_update_command('update', child_collection_prop_name='probes',
                                 setter_name='begin_create_or_update',
                                 custom_func_name='set_cross_lb_probe')
    # endregion

    # region LocalGateways
    with self.command_group('network local-gateway'):
        from .aaz.latest.network.local_gateway import List
        self.command_table['network local-gateway list'] = List(loader=self, table_transformer=transform_local_gateway_table_output)
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
    with self.command_group("network nsg") as g:
        from .custom import NSGCreate
        self.command_table["network nsg create"] = NSGCreate(loader=self)

    with self.command_group("network nsg rule") as g:
        from .custom import NSGRuleCreate, NSGRuleUpdate
        from .aaz.latest.network.nsg.rule import Show
        self.command_table["network nsg rule create"] = NSGRuleCreate(loader=self)
        self.command_table["network nsg rule update"] = NSGRuleUpdate(loader=self)
        self.command_table["network nsg rule show"] = Show(loader=self, table_transformer=transform_nsg_rule_table_output)
        g.custom_command("list", "list_nsg_rules", table_transformer=lambda x: [transform_nsg_rule_table_output(i) for i in x])
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

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Address:ipAddress, AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'
    public_ip_show_table_transform = public_ip_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ' if self.supported_api_version(min_api='2017-06-01') else ' ')

    with self.command_group('network public-ip') as g:
        from .aaz.latest.network.public_ip import List, Show
        from .custom import PublicIPUpdate
        self.command_table['network public-ip update'] = PublicIPUpdate(loader=self)
        self.command_table['network public-ip list'] = List(loader=self, table_transformer='[].' + public_ip_show_table_transform)
        self.command_table['network public-ip show'] = Show(loader=self, table_transformer=public_ip_show_table_transform)
        g.custom_command('create', 'create_public_ip', transform=transform_public_ip_create_output, validator=process_public_ip_create_namespace)

    with self.command_group('network public-ip prefix'):
        from azure.cli.command_modules.network.custom import PublicIpPrefixCreate
        self.command_table['network public-ip prefix create'] = PublicIpPrefixCreate(loader=self)
    # endregion

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

    # region VirtualNetworks
    with self.command_group("network vnet") as g:
        from .aaz.latest.network.vnet import List
        from .custom import VNetCreate, VNetUpdate
        self.command_table["network vnet create"] = VNetCreate(loader=self)
        self.command_table["network vnet update"] = VNetUpdate(loader=self)
        self.command_table['network vnet list'] = List(loader=self, table_transformer=transform_vnet_table_output)
        g.custom_command("list-available-ips", "list_available_ips", is_preview=True)

    with self.command_group("network vnet peering") as g:
        from .custom import VNetPeeringCreate
        self.command_table["network vnet peering create"] = VNetPeeringCreate(loader=self)
        g.custom_command("sync", "sync_vnet_peering")

    with self.command_group("network vnet subnet") as g:
        from .custom import VNetSubnetCreate, VNetSubnetUpdate
        self.command_table["network vnet subnet create"] = VNetSubnetCreate(loader=self)
        self.command_table["network vnet subnet update"] = VNetSubnetUpdate(loader=self)
        g.custom_command("list-available-ips", "subnet_list_available_ips", is_preview=True)
    # endregion

    # region VirtualNetworkGateways
    with self.command_group('network vnet-gateway'):
        from .custom import VnetGatewayCreate, VnetGatewayUpdate, VnetGatewayVpnConnectionsDisconnect
        from .aaz.latest.network.vnet_gateway import ListBgpPeerStatus, ListAdvertisedRoutes, ListLearnedRoutes
        self.command_table['network vnet-gateway create'] = VnetGatewayCreate(loader=self)
        self.command_table['network vnet-gateway update'] = VnetGatewayUpdate(loader=self)
        self.command_table['network vnet-gateway disconnect-vpn-connections'] = VnetGatewayVpnConnectionsDisconnect(loader=self)
        self.command_table['network vnet-gateway list-bgp-peer-status'] = ListBgpPeerStatus(loader=self, table_transformer=transform_vnet_gateway_bgp_peer_table)
        self.command_table['network vnet-gateway list-advertised-routes'] = ListAdvertisedRoutes(loader=self, table_transformer=transform_vnet_gateway_routes_table)
        self.command_table['network vnet-gateway list-learned-routes'] = ListLearnedRoutes(loader=self, table_transformer=transform_vnet_gateway_routes_table)

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
    with self.command_group('network routeserver') as g:
        g.custom_command('create', 'create_virtual_hub')
        g.custom_command('delete', 'delete_virtual_hub', supports_no_wait=True, confirmation=True)
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
