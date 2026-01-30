# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long,too-many-lines

from azure.cli.core.commands import DeploymentOutputLongRunningOperation
from azure.cli.core.commands.arm import (
    deployment_validate_table_format, handle_template_based_exception)
from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.network._format import (
    transform_local_gateway_table_output, transform_dns_record_set_output,
    transform_dns_zone_table_output, transform_public_ip_create_output,
    transform_traffic_manager_create_output,
    transform_geographic_hierachy_table_output,
    transform_service_community_table_output, transform_waf_rule_sets_table_output,
    transform_network_usage_table, transform_nsg_rule_table_output,
    transform_vnet_table_output, transform_effective_route_table, transform_effective_nsg,
    transform_vnet_gateway_routes_table, transform_vnet_gateway_bgp_peer_table)
from azure.cli.command_modules.network._validators import (
    process_ag_create_namespace,
    process_lb_create_namespace,
    process_nw_flow_log_show_namespace,
    process_public_ip_create_namespace,
    process_vpn_connection_create_namespace,
    process_appgw_waf_policy_update, process_cross_region_lb_create_namespace)

NETWORK_VROUTER_DEPRECATION_INFO = 'network routeserver'
NETWORK_VROUTER_PEERING_DEPRECATION_INFO = 'network routeserver peering'


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):
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
        from .custom import ClientCertAdd, ClientCertUpdate
        self.command_table["network application-gateway client-cert add"] = ClientCertAdd(loader=self)
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

    with self.command_group("network application-gateway private-link"):
        from .custom import AGPrivateLinkAdd, AGPrivateLinkRemove, AGPrivateLinkIPConfigAdd
        self.command_table["network application-gateway private-link add"] = AGPrivateLinkAdd(loader=self)
        self.command_table["network application-gateway private-link remove"] = AGPrivateLinkRemove(loader=self)
        self.command_table["network application-gateway private-link ip-config add"] = AGPrivateLinkIPConfigAdd(loader=self)

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
        from .custom import SSLProfileAdd, SSLProfileUpdate
        self.command_table["network application-gateway ssl-profile add"] = SSLProfileAdd(loader=self)
        self.command_table["network application-gateway ssl-profile update"] = SSLProfileUpdate(loader=self)

    with self.command_group("network application-gateway url-path-map"):
        from .custom import URLPathMapCreate, URLPathMapUpdate, URLPathMapRuleCreate
        self.command_table["network application-gateway url-path-map create"] = URLPathMapCreate(loader=self)
        self.command_table["network application-gateway url-path-map update"] = URLPathMapUpdate(loader=self)
        self.command_table["network application-gateway url-path-map rule create"] = URLPathMapRuleCreate(loader=self)

    with self.command_group("network application-gateway waf-config") as g:
        g.custom_command("list-rule-sets", "list_ag_waf_rule_sets", table_transformer=transform_waf_rule_sets_table_output)
        g.custom_command("set", "set_ag_waf_config", supports_no_wait=True)
        g.custom_show_command("show", "show_ag_waf_config")
    # endregion

    # region ApplicationGatewayWAFPolicy
    with self.command_group("network application-gateway waf-policy"):
        from .custom import WAFCreate
        self.command_table["network application-gateway waf-policy create"] = WAFCreate(loader=self)

    with self.command_group("network application-gateway waf-policy custom-rule match-condition"):
        from .custom import WAFCustomRuleMatchConditionAdd
        self.command_table["network application-gateway waf-policy custom-rule match-condition add"] = WAFCustomRuleMatchConditionAdd(loader=self)

    with self.command_group("network application-gateway waf-policy managed-rule exception") as g:
        g.custom_command("remove", "remove_waf_managed_rule_exception")
        g.custom_command("list", "list_waf_managed_rules")

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
    with self.command_group('network ddos-protection') as g:
        g.custom_command('create', 'create_ddos_plan')
        g.custom_command('update', 'update_ddos_plan')
    # endregion

    # region DNS
    from .operations.dns import DNSListReferences
    self.command_table["network dns list-references"] = DNSListReferences(loader=self)

    with self.command_group('network dns zone') as g:
        g.custom_command('import', 'import_zone')
        g.custom_command('export', 'export_zone')
        g.custom_command('create', 'create_dns_zone', table_transformer=transform_dns_zone_table_output)

    supported_records = ['a', 'aaaa', 'ds', 'mx', 'naptr', 'ns', 'ptr', 'srv', 'tlsa', 'txt', 'caa']
    experimental_records = ['ds', 'naptr', 'tlsa']
    for record in supported_records:
        is_experimental = record in experimental_records
        with self.command_group('network dns record-set {}'.format(record), is_experimental=is_experimental) as g:
            g.custom_command('add-record', 'add_dns_{}_record'.format(record), transform=transform_dns_record_set_output)
            g.custom_command('remove-record', 'remove_dns_{}_record'.format(record), transform=transform_dns_record_set_output)

    with self.command_group('network dns record-set soa') as g:
        g.custom_command('update', 'update_dns_soa_record', transform=transform_dns_record_set_output)

    with self.command_group('network dns record-set cname') as g:
        g.custom_command('set-record', 'add_dns_cname_record', transform=transform_dns_record_set_output)
        g.custom_command('remove-record', 'remove_dns_cname_record', transform=transform_dns_record_set_output)

    from .operations.dns import RecordSetAShow as DNSRecordSetAShow, RecordSetAAAAShow as DNSRecordSetAAAAShow, \
        RecordSetDSShow as DNSRecordSetDSShow, RecordSetMXShow as DNSRecordSetMXShow, \
        RecordSetNAPTRShow as DNSRecordSetNAPTRShow, RecordSetNSShow as DNSRecordSetNSShow, \
        RecordSetPTRShow as DNSRecordSetPTRShow, RecordSetSRVShow as DNSRecordSetSRVShow, \
        RecordSetTLSAShow as DNSRecordSetTLSAShow, RecordSetTXTShow as DNSRecordSetTXTShow, \
        RecordSetCAAShow as DNSRecordSetCAAShow, RecordSetCNAMEShow as DNSRecordSetCNAMEShow, \
        RecordSetSOAShow as DNSRecordSetSOAShow
    self.command_table["network dns record-set a show"] = DNSRecordSetAShow(loader=self)
    self.command_table["network dns record-set aaaa show"] = DNSRecordSetAAAAShow(loader=self)
    self.command_table["network dns record-set ds show"] = DNSRecordSetDSShow(loader=self)
    self.command_table["network dns record-set mx show"] = DNSRecordSetMXShow(loader=self)
    self.command_table["network dns record-set naptr show"] = DNSRecordSetNAPTRShow(loader=self)
    self.command_table["network dns record-set ns show"] = DNSRecordSetNSShow(loader=self)
    self.command_table["network dns record-set ptr show"] = DNSRecordSetPTRShow(loader=self)
    self.command_table["network dns record-set srv show"] = DNSRecordSetSRVShow(loader=self)
    self.command_table["network dns record-set tlsa show"] = DNSRecordSetTLSAShow(loader=self)
    self.command_table["network dns record-set txt show"] = DNSRecordSetTXTShow(loader=self)
    self.command_table["network dns record-set caa show"] = DNSRecordSetCAAShow(loader=self)
    self.command_table["network dns record-set cname show"] = DNSRecordSetCNAMEShow(loader=self)
    self.command_table["network dns record-set soa show"] = DNSRecordSetSOAShow(loader=self)

    from .operations.dns import RecordSetAList as DNSRecordSetAList, RecordSetAAAAList as DNSRecordSetAAAAList, \
        RecordSetDSList as DNSRecordSetDSList, RecordSetMXList as DNSRecordSetMXList, \
        RecordSetNAPTRList as DNSRecordSetNAPTRList, RecordSetNSList as DNSRecordSetNSList, \
        RecordSetPTRList as DNSRecordSetPTRList, RecordSetSRVList as DNSRecordSetSRVList, \
        RecordSetTLSAList as DNSRecordSetTLSAList, RecordSetTXTList as DNSRecordSetTXTList, \
        RecordSetCAAList as DNSRecordSetCAAList, RecordSetCNAMEList as DNSRecordSetCNAMEList
    self.command_table["network dns record-set a list"] = DNSRecordSetAList(loader=self)
    self.command_table["network dns record-set aaaa list"] = DNSRecordSetAAAAList(loader=self)
    self.command_table["network dns record-set ds list"] = DNSRecordSetDSList(loader=self)
    self.command_table["network dns record-set mx list"] = DNSRecordSetMXList(loader=self)
    self.command_table["network dns record-set naptr list"] = DNSRecordSetNAPTRList(loader=self)
    self.command_table["network dns record-set ns list"] = DNSRecordSetNSList(loader=self)
    self.command_table["network dns record-set ptr list"] = DNSRecordSetPTRList(loader=self)
    self.command_table["network dns record-set srv list"] = DNSRecordSetSRVList(loader=self)
    self.command_table["network dns record-set tlsa list"] = DNSRecordSetTLSAList(loader=self)
    self.command_table["network dns record-set txt list"] = DNSRecordSetTXTList(loader=self)
    self.command_table["network dns record-set caa list"] = DNSRecordSetCAAList(loader=self)
    self.command_table["network dns record-set cname list"] = DNSRecordSetCNAMEList(loader=self)

    from .operations.dns import RecordSetACreate as DNSRecordSetACreate, RecordSetAAAACreate as DNSRecordSetAAAACreate, \
        RecordSetDSCreate as DNSRecordSetDSCreate, RecordSetMXCreate as DNSRecordSetMXCreate, \
        RecordSetNAPTRCreate as DNSRecordSetNAPTRCreate, RecordSetNSCreate as DNSRecordSetNSCreate, \
        RecordSetPTRCreate as DNSRecordSetPTRCreate, RecordSetSRVCreate as DNSRecordSetSRVCreate, \
        RecordSetTLSACreate as DNSRecordSetTLSACreate, RecordSetTXTCreate as DNSRecordSetTXTCreate, \
        RecordSetCAACreate as DNSRecordSetCAACreate, RecordSetCNAMECreate as DNSRecordSetCNAMECreate
    self.command_table["network dns record-set a create"] = DNSRecordSetACreate(loader=self)
    self.command_table["network dns record-set aaaa create"] = DNSRecordSetAAAACreate(loader=self)
    self.command_table["network dns record-set ds create"] = DNSRecordSetDSCreate(loader=self)
    self.command_table["network dns record-set mx create"] = DNSRecordSetMXCreate(loader=self)
    self.command_table["network dns record-set naptr create"] = DNSRecordSetNAPTRCreate(loader=self)
    self.command_table["network dns record-set ns create"] = DNSRecordSetNSCreate(loader=self)
    self.command_table["network dns record-set ptr create"] = DNSRecordSetPTRCreate(loader=self)
    self.command_table["network dns record-set srv create"] = DNSRecordSetSRVCreate(loader=self)
    self.command_table["network dns record-set tlsa create"] = DNSRecordSetTLSACreate(loader=self)
    self.command_table["network dns record-set txt create"] = DNSRecordSetTXTCreate(loader=self)
    self.command_table["network dns record-set caa create"] = DNSRecordSetCAACreate(loader=self)
    self.command_table["network dns record-set cname create"] = DNSRecordSetCNAMECreate(loader=self)

    from .operations.dns import RecordSetAUpdate as DNSRecordSetAUpdate, RecordSetAAAAUpdate as DNSRecordSetAAAAUpdate, \
        RecordSetDSUpdate as DNSRecordSetDSUpdate, RecordSetMXUpdate as DNSRecordSetMXUpdate, \
        RecordSetNAPTRUpdate as DNSRecordSetNAPTRUpdate, RecordSetNSUpdate as DNSRecordSetNSUpdate, \
        RecordSetPTRUpdate as DNSRecordSetPTRUpdate, RecordSetSRVUpdate as DNSRecordSetSRVUpdate, \
        RecordSetTLSAUpdate as DNSRecordSetTLSAUpdate, RecordSetTXTUpdate as DNSRecordSetTXTUpdate, \
        RecordSetCAAUpdate as DNSRecordSetCAAUpdate, RecordSetCNAMEUpdate as DNSRecordSetCNAMEUpdate
    self.command_table["network dns record-set a update"] = DNSRecordSetAUpdate(loader=self)
    self.command_table["network dns record-set aaaa update"] = DNSRecordSetAAAAUpdate(loader=self)
    self.command_table["network dns record-set ds update"] = DNSRecordSetDSUpdate(loader=self)
    self.command_table["network dns record-set mx update"] = DNSRecordSetMXUpdate(loader=self)
    self.command_table["network dns record-set naptr update"] = DNSRecordSetNAPTRUpdate(loader=self)
    self.command_table["network dns record-set ns update"] = DNSRecordSetNSUpdate(loader=self)
    self.command_table["network dns record-set ptr update"] = DNSRecordSetPTRUpdate(loader=self)
    self.command_table["network dns record-set srv update"] = DNSRecordSetSRVUpdate(loader=self)
    self.command_table["network dns record-set tlsa update"] = DNSRecordSetTLSAUpdate(loader=self)
    self.command_table["network dns record-set txt update"] = DNSRecordSetTXTUpdate(loader=self)
    self.command_table["network dns record-set caa update"] = DNSRecordSetCAAUpdate(loader=self)
    self.command_table["network dns record-set cname update"] = DNSRecordSetCNAMEUpdate(loader=self)

    from .operations.dns import RecordSetADelete as DNSRecordSetADelete, RecordSetAAAADelete as DNSRecordSetAAAADelete, \
        RecordSetDSDelete as DNSRecordSetDSDelete, RecordSetMXDelete as DNSRecordSetMXDelete, \
        RecordSetNAPTRDelete as DNSRecordSetNAPTRDelete, RecordSetNSDelete as DNSRecordSetNSDelete, \
        RecordSetPTRDelete as DNSRecordSetPTRDelete, RecordSetSRVDelete as DNSRecordSetSRVDelete, \
        RecordSetTLSADelete as DNSRecordSetTLSADelete, RecordSetTXTDelete as DNSRecordSetTXTDelete, \
        RecordSetCAADelete as DNSRecordSetCAADelete, RecordSetCNAMEDelete as DNSRecordSetCNAMEDelete
    self.command_table["network dns record-set a delete"] = DNSRecordSetADelete(loader=self)
    self.command_table["network dns record-set aaaa delete"] = DNSRecordSetAAAADelete(loader=self)
    self.command_table["network dns record-set ds delete"] = DNSRecordSetDSDelete(loader=self)
    self.command_table["network dns record-set mx delete"] = DNSRecordSetMXDelete(loader=self)
    self.command_table["network dns record-set naptr delete"] = DNSRecordSetNAPTRDelete(loader=self)
    self.command_table["network dns record-set ns delete"] = DNSRecordSetNSDelete(loader=self)
    self.command_table["network dns record-set ptr delete"] = DNSRecordSetPTRDelete(loader=self)
    self.command_table["network dns record-set srv delete"] = DNSRecordSetSRVDelete(loader=self)
    self.command_table["network dns record-set tlsa delete"] = DNSRecordSetTLSADelete(loader=self)
    self.command_table["network dns record-set txt delete"] = DNSRecordSetTXTDelete(loader=self)
    self.command_table["network dns record-set caa delete"] = DNSRecordSetCAADelete(loader=self)
    self.command_table["network dns record-set cname delete"] = DNSRecordSetCNAMEDelete(loader=self)
    # endregion

    # region ExpressRoutes
    with self.command_group('network express-route'):
        from .custom import ExpressRouteCreate, ExpressRouteUpdate
        self.command_table['network express-route create'] = ExpressRouteCreate(loader=self)
        self.command_table['network express-route update'] = ExpressRouteUpdate(loader=self)

    with self.command_group('network express-route gateway'):
        from .custom import ExpressRouteGatewayCreate, ExpressRouteGatewayUpdate
        self.command_table['network express-route gateway create'] = ExpressRouteGatewayCreate(loader=self)
        self.command_table['network express-route gateway update'] = ExpressRouteGatewayUpdate(loader=self)

    with self.command_group('network express-route gateway connection'):
        from .custom import ExpressRouteConnectionUpdate, ExpressRouteConnectionCreate
        self.command_table['network express-route gateway connection create'] = ExpressRouteConnectionCreate(loader=self)
        self.command_table['network express-route gateway connection update'] = ExpressRouteConnectionUpdate(loader=self)

    with self.command_group('network express-route peering'):
        from .custom import ExpressRoutePeeringCreate, ExpressRoutePeeringUpdate
        self.command_table['network express-route peering create'] = ExpressRoutePeeringCreate(loader=self)
        self.command_table['network express-route peering update'] = ExpressRoutePeeringUpdate(loader=self)

    with self.command_group('network express-route peering connection'):
        from .custom import ExpressRoutePeeringConnectionCreate
        self.command_table['network express-route peering connection create'] = ExpressRoutePeeringConnectionCreate(loader=self)

    with self.command_group('network express-route port') as g:
        from .custom import ExpressRoutePortCreate
        self.command_table['network express-route port create'] = ExpressRoutePortCreate(loader=self)
        g.custom_command('generate-loa', 'download_generated_loa_as_pdf')

    with self.command_group('network express-route port identity'):
        from .custom import ExpressRoutePortIdentityAssign
        self.command_table['network express-route port identity assign'] = ExpressRoutePortIdentityAssign(loader=self)

    with self.command_group('network express-route port link'):
        from .custom import ExpressRoutePortLinkUpdate
        self.command_table['network express-route port link update'] = ExpressRoutePortLinkUpdate(loader=self)
    # endregion

    # region PrivateEndpoint
    with self.command_group('network private-endpoint'):
        from azure.cli.command_modules.network.custom import PrivateEndpointCreate, PrivateEndpointUpdate
        self.command_table['network private-endpoint create'] = PrivateEndpointCreate(loader=self)
        self.command_table['network private-endpoint update'] = PrivateEndpointUpdate(loader=self)

    with self.command_group('network private-endpoint dns-zone-group'):
        from azure.cli.command_modules.network.custom import PrivateEndpointPrivateDnsZoneGroupCreate, \
            PrivateEndpointPrivateDnsZoneAdd
        self.command_table['network private-endpoint dns-zone-group create'] = \
            PrivateEndpointPrivateDnsZoneGroupCreate(loader=self)
        self.command_table['network private-endpoint dns-zone-group add'] = \
            PrivateEndpointPrivateDnsZoneAdd(loader=self)

    with self.command_group('network private-endpoint ip-config'):
        from azure.cli.command_modules.network.custom import PrivateEndpointIpConfigAdd
        self.command_table['network private-endpoint ip-config add'] = PrivateEndpointIpConfigAdd(loader=self)

    with self.command_group('network private-endpoint asg'):
        from azure.cli.command_modules.network.custom import PrivateEndpointAsgAdd
        self.command_table['network private-endpoint asg add'] = PrivateEndpointAsgAdd(loader=self)
    # endregion

    # region PrivateLinkServices
    with self.command_group('network private-link-service'):
        from azure.cli.command_modules.network.custom import PrivateLinkServiceCreate, PrivateLinkServiceUpdate
        self.command_table['network private-link-service create'] = PrivateLinkServiceCreate(loader=self)
        self.command_table['network private-link-service update'] = PrivateLinkServiceUpdate(loader=self)

    with self.command_group('network private-link-service connection'):
        from azure.cli.command_modules.network.custom import PrivateEndpointConnectionUpdate
        self.command_table['network private-link-service connection update'] = PrivateEndpointConnectionUpdate(loader=self)
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

    from .operations.load_balancer import LBAddressPoolCreate, LBAddressPoolDelete, LBAddressPoolUpdate
    self.command_table["network lb address-pool create"] = LBAddressPoolCreate(loader=self)
    self.command_table["network lb address-pool delete"] = LBAddressPoolDelete(loader=self)
    self.command_table["network lb address-pool update"] = LBAddressPoolUpdate(loader=self)

    from .operations.load_balancer import LBAddressPoolAddressAdd, LBAddressPoolAddressUpdate
    self.command_table["network lb address-pool address add"] = LBAddressPoolAddressAdd(loader=self)
    self.command_table["network lb address-pool address update"] = LBAddressPoolAddressUpdate(loader=self)

    from .operations.load_balancer import LBAddressPoolTunnelInterfaceAdd, LBAddressPoolTunnelInterfaceUpdate
    self.command_table["network lb address-pool tunnel-interface add"] = LBAddressPoolTunnelInterfaceAdd(loader=self)
    self.command_table["network lb address-pool tunnel-interface update"] = LBAddressPoolTunnelInterfaceUpdate(loader=self)

    from .operations.load_balancer import LBProbeCreate, LBProbeUpdate
    self.command_table["network lb probe create"] = LBProbeCreate(loader=self)
    self.command_table["network lb probe update"] = LBProbeUpdate(loader=self)

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
        from .operations.load_balancer import CrossRegionLoadBalancerAddressPoolCreate, CrossRegionLoadBalancerAddressPoolUpdate, CrossRegionLoadBalancerAddressPoolList, CrossRegionLoadBalancerAddressPoolDelete, CrossRegionLoadBalancerAddressPoolShow
        self.command_table['network cross-region-lb address-pool show'] = CrossRegionLoadBalancerAddressPoolShow(loader=self)
        self.command_table['network cross-region-lb address-pool delete'] = CrossRegionLoadBalancerAddressPoolDelete(loader=self)
        self.command_table['network cross-region-lb address-pool list'] = CrossRegionLoadBalancerAddressPoolList(loader=self)
        self.command_table['network cross-region-lb address-pool create'] = CrossRegionLoadBalancerAddressPoolCreate(loader=self)
        self.command_table['network cross-region-lb address-pool update'] = CrossRegionLoadBalancerAddressPoolUpdate(loader=self)

    with self.command_group('network cross-region-lb address-pool address') as g:
        from .operations.load_balancer import CrossRegionLoadBalancerAddressPoolAddressAdd, CrossRegionLoadBalancerAddressPoolAddressUpdate, CrossRegionLoadBalancerAddressPoolAddressRemove, CrossRegionLoadBalancerAddressPoolAddressList, CrossRegionLoadBalancerAddressPoolAddressShow
        self.command_table['network cross-region-lb address-pool address add'] = CrossRegionLoadBalancerAddressPoolAddressAdd(loader=self)
        self.command_table['network cross-region-lb address-pool address remove'] = CrossRegionLoadBalancerAddressPoolAddressRemove(loader=self)
        self.command_table['network cross-region-lb address-pool address update'] = CrossRegionLoadBalancerAddressPoolAddressUpdate(loader=self)
        self.command_table['network cross-region-lb address-pool address list'] = CrossRegionLoadBalancerAddressPoolAddressList(loader=self)
        self.command_table['network cross-region-lb address-pool address show'] = CrossRegionLoadBalancerAddressPoolAddressShow(loader=self)
    # endregion

    # region LocalGateways
    with self.command_group('network local-gateway'):
        from .aaz.latest.network.local_gateway import List
        self.command_table['network local-gateway list'] = List(loader=self, table_transformer=transform_local_gateway_table_output)
    # endregion

    # region NetworkInterfaces: (NIC)
    with self.command_group("network nic"):
        from .aaz.latest.network.nic import ListEffectiveNsg, ShowEffectiveRouteTable
        from .custom import NICCreate, NICUpdate
        self.command_table["network nic create"] = NICCreate(loader=self)
        self.command_table["network nic update"] = NICUpdate(loader=self)
        self.command_table["network nic list-effective-nsg"] = ListEffectiveNsg(loader=self, table_transformer=transform_effective_nsg)
        self.command_table["network nic show-effective-route-table"] = ShowEffectiveRouteTable(loader=self, table_transformer=transform_effective_route_table)

    with self.command_group("network nic ip-config"):
        from .custom import NICIPConfigCreate, NICIPConfigUpdate, NICIPConfigNATAdd, NICIPConfigNATRemove
        self.command_table["network nic ip-config create"] = NICIPConfigCreate(loader=self)
        self.command_table["network nic ip-config update"] = NICIPConfigUpdate(loader=self)
        self.command_table["network nic ip-config inbound-nat-rule add"] = NICIPConfigNATAdd(loader=self)
        self.command_table["network nic ip-config inbound-nat-rule remove"] = NICIPConfigNATRemove(loader=self)

    with self.command_group("network nic ip-config address-pool") as g:
        g.custom_command("add", "add_nic_ip_config_address_pool")
        g.custom_command("remove", "remove_nic_ip_config_address_pool")
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
    with self.command_group("network watcher") as g:
        from .operations.watcher import RunConfigurationDiagnostic, ShowNextHop, ShowSecurityGroupView, ShowTopology, TestConnectivity, TestIPFlow
        self.command_table["network watcher test-ip-flow"] = TestIPFlow(loader=self)
        self.command_table["network watcher show-next-hop"] = ShowNextHop(loader=self)
        self.command_table["network watcher show-security-group-view"] = ShowSecurityGroupView(loader=self)
        self.command_table["network watcher run-configuration-diagnostic"] = RunConfigurationDiagnostic(loader=self)
        self.command_table["network watcher show-topology"] = ShowTopology(loader=self)
        self.command_table["network watcher test-connectivity"] = TestConnectivity(loader=self)
        g.custom_command("configure", "configure_network_watcher")

    from .operations.watcher import WatcherConnectionMonitorStart, WatcherConnectionMonitorStop, \
        WatcherConnectionMonitorList, WatcherConnectionMonitorQuery, WatcherConnectionMonitorShow, \
        WatcherConnectionMonitorDelete, WatcherConnectionMonitorCreate
    self.command_table["network watcher connection-monitor create"] = WatcherConnectionMonitorCreate(loader=self)
    self.command_table["network watcher connection-monitor start"] = WatcherConnectionMonitorStart(loader=self)
    self.command_table["network watcher connection-monitor stop"] = WatcherConnectionMonitorStop(loader=self)
    self.command_table["network watcher connection-monitor list"] = WatcherConnectionMonitorList(loader=self)
    self.command_table["network watcher connection-monitor query"] = WatcherConnectionMonitorQuery(loader=self)
    self.command_table["network watcher connection-monitor delete"] = WatcherConnectionMonitorDelete(loader=self)
    self.command_table["network watcher connection-monitor show"] = WatcherConnectionMonitorShow(loader=self)

    from .operations.watcher import WatcherConnectionMonitorEndpointAdd, WatcherConnectionMonitorEndpointShow, \
        WatcherConnectionMonitorEndpointList, WatcherConnectionMonitorEndpointRemove
    self.command_table["network watcher connection-monitor endpoint add"] = WatcherConnectionMonitorEndpointAdd(
        loader=self)
    self.command_table["network watcher connection-monitor endpoint remove"] = WatcherConnectionMonitorEndpointRemove(
        loader=self)
    self.command_table["network watcher connection-monitor endpoint show"] = WatcherConnectionMonitorEndpointShow(
        loader=self)
    self.command_table["network watcher connection-monitor endpoint list"] = WatcherConnectionMonitorEndpointList(
        loader=self)

    from .operations.watcher import WatcherConnectionMonitorTestConfigurationAdd as WCMTAdd, \
        WatcherConnectionMonitorTestConfigurationShow as WCMTCShow, \
        WatcherConnectionMonitorTestConfigurationList as WCMTCList, \
        WatcherConnectionMonitorTestConfigurationRemove as WCMTRemove
    self.command_table["network watcher connection-monitor test-configuration add"] = WCMTAdd(loader=self)
    self.command_table["network watcher connection-monitor test-configuration remove"] = WCMTRemove(loader=self)
    self.command_table["network watcher connection-monitor test-configuration show"] = WCMTCShow(loader=self)
    self.command_table["network watcher connection-monitor test-configuration list"] = WCMTCList(loader=self)

    with self.command_group('network watcher connection-monitor test-group', is_preview=True) as c:
        from .operations.watcher import WatcherConnectionMonitorTestGroupAdd as WCMTGAdd, \
            WatcherConnectionMonitorTestGroupShow as WCMTGShow, \
            WatcherConnectionMonitorTestGroupList as WCMTGList
        self.command_table["network watcher connection-monitor test-group add"] = WCMTGAdd(loader=self)
        self.command_table["network watcher connection-monitor test-group show"] = WCMTGShow(loader=self)
        self.command_table["network watcher connection-monitor test-group list"] = WCMTGList(loader=self)
        c.custom_command('remove', 'remove_nw_connection_monitor_test_group')

    with self.command_group('network watcher connection-monitor output', is_preview=True) as c:
        from .operations.watcher import WatcherConnectionMonitorOutputAdd, WatcherConnectionMonitorOutputList
        self.command_table["network watcher connection-monitor output add"] = WatcherConnectionMonitorOutputAdd(
            loader=self)
        self.command_table["network watcher connection-monitor output list"] = WatcherConnectionMonitorOutputList(
            loader=self)
        c.custom_command('remove', 'remove_nw_connection_monitor_output')

    with self.command_group("network watcher packet-capture"):
        from .operations.watcher import PacketCaptureCreate, PacketCaptureDelete, PacketCaptureList, PacketCaptureShow, PacketCaptureShowStatus, PacketCaptureStop
        self.command_table["network watcher packet-capture create"] = PacketCaptureCreate(loader=self)
        self.command_table["network watcher packet-capture delete"] = PacketCaptureDelete(loader=self)
        self.command_table["network watcher packet-capture list"] = PacketCaptureList(loader=self)
        self.command_table["network watcher packet-capture show"] = PacketCaptureShow(loader=self)
        self.command_table["network watcher packet-capture show-status"] = PacketCaptureShowStatus(loader=self)
        self.command_table["network watcher packet-capture stop"] = PacketCaptureStop(loader=self)

    with self.command_group('network watcher flow-log') as g:
        from .operations.watcher import NwFlowLogCreate, NwFlowLogUpdate, NwFlowLogList, NwFlowLogDelete
        self.command_table["network watcher flow-log create"] = NwFlowLogCreate(loader=self)
        self.command_table["network watcher flow-log update"] = NwFlowLogUpdate(loader=self)
        self.command_table["network watcher flow-log list"] = NwFlowLogList(loader=self)
        self.command_table["network watcher flow-log delete"] = NwFlowLogDelete(loader=self)
        g.custom_show_command('show', 'show_nw_flow_logging', validator=process_nw_flow_log_show_namespace)

    with self.command_group('network watcher troubleshooting'):
        from .operations.watcher import NwTroubleshootingStart, NwTroubleshootingShow
        self.command_table["network watcher troubleshooting start"] = NwTroubleshootingStart(loader=self)
        self.command_table["network watcher troubleshooting show"] = NwTroubleshootingShow(loader=self)
    # endregion

    # region PublicIPAddresses
    public_ip_show_table_transform = '{Name:name, ResourceGroup:resourceGroup, Location:location, $zone$Address:ipAddress, AddressVersion:publicIpAddressVersion, AllocationMethod:publicIpAllocationMethod, IdleTimeoutInMinutes:idleTimeoutInMinutes, ProvisioningState:provisioningState}'
    public_ip_show_table_transform = public_ip_show_table_transform.replace('$zone$', 'Zones: (!zones && \' \') || join(` `, zones), ')

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
        from .custom import VnetGatewayCreate, VnetGatewayUpdate, VnetGatewayVpnConnectionsDisconnect, VNetGatewayShow, VNetGatewayList
        from .aaz.latest.network.vnet_gateway import ListBgpPeerStatus, ListAdvertisedRoutes, ListLearnedRoutes
        self.command_table['network vnet-gateway create'] = VnetGatewayCreate(loader=self)
        self.command_table['network vnet-gateway update'] = VnetGatewayUpdate(loader=self)
        self.command_table['network vnet-gateway disconnect-vpn-connections'] = VnetGatewayVpnConnectionsDisconnect(loader=self)
        self.command_table["network vnet-gateway show"] = VNetGatewayShow(loader=self)
        self.command_table["network vnet-gateway list"] = VNetGatewayList(loader=self)
        self.command_table['network vnet-gateway list-bgp-peer-status'] = ListBgpPeerStatus(loader=self, table_transformer=transform_vnet_gateway_bgp_peer_table)
        self.command_table['network vnet-gateway list-advertised-routes'] = ListAdvertisedRoutes(loader=self, table_transformer=transform_vnet_gateway_routes_table)
        self.command_table['network vnet-gateway list-learned-routes'] = ListLearnedRoutes(loader=self, table_transformer=transform_vnet_gateway_routes_table)

    with self.command_group('network vnet-gateway migration') as g:
        from .operations.vnet_gateway_migration import VNetGatewayMigrationAbort, VNetGatewayMigrationExecute, \
            VNetGatewayMigrationCommit, VNetGatewayMigrationPrepare
        self.command_table['network vnet-gateway migration abort'] = VNetGatewayMigrationAbort(loader=self)
        self.command_table['network vnet-gateway migration execute'] = VNetGatewayMigrationExecute(loader=self)
        self.command_table['network vnet-gateway migration commit'] = VNetGatewayMigrationCommit(loader=self)
        self.command_table['network vnet-gateway migration prepare'] = VNetGatewayMigrationPrepare(loader=self)

    with self.command_group('network vnet-gateway packet-capture'):
        from .aaz.latest.network.vnet_gateway import Wait
        self.command_table['network vnet-gateway packet-capture wait'] = Wait(loader=self)

    with self.command_group('network vnet-gateway vpn-client') as g:
        g.custom_command('generate', 'generate_vpn_client')

    with self.command_group('network vnet-gateway vpn-client ipsec-policy'):
        from .aaz.latest.network.vnet_gateway import Wait
        self.command_table['network vnet-gateway vpn-client ipsec-policy wait'] = Wait(loader=self)

    with self.command_group('network vnet-gateway revoked-cert'):
        from .custom import VnetGatewayRevokedCertCreate
        self.command_table['network vnet-gateway revoked-cert create'] = VnetGatewayRevokedCertCreate(loader=self)

    with self.command_group('network vnet-gateway root-cert'):
        from .custom import VnetGatewayRootCertCreate
        self.command_table['network vnet-gateway root-cert create'] = VnetGatewayRootCertCreate(loader=self)

    with self.command_group('network vnet-gateway ipsec-policy') as g:
        from .custom import VnetGatewayIpsecPolicyAdd
        self.command_table['network vnet-gateway ipsec-policy add'] = VnetGatewayIpsecPolicyAdd(loader=self)
        g.custom_command('clear', 'clear_vnet_gateway_ipsec_policies', supports_no_wait=True)

    with self.command_group('network vnet-gateway aad') as g:
        from .custom import VnetGatewayAadAssign
        self.command_table['network vnet-gateway aad assign'] = VnetGatewayAadAssign(loader=self)
        g.custom_command('remove', 'remove_vnet_gateway_aad', supports_no_wait=True)

    with self.command_group('network vnet-gateway nat-rule'):
        from .custom import VnetGatewayNatRuleAdd, VnetGatewayNatRuleShow, VnetGatewayNatRuleRemove
        self.command_table['network vnet-gateway nat-rule add'] = VnetGatewayNatRuleAdd(loader=self)
        self.command_table['network vnet-gateway nat-rule list'] = VnetGatewayNatRuleShow(loader=self)
        self.command_table['network vnet-gateway nat-rule remove'] = VnetGatewayNatRuleRemove(loader=self)
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection') as g:
        from .custom import VpnConnectionUpdate, VpnConnectionDeviceConfigScriptShow
        self.command_table['network vpn-connection update'] = VpnConnectionUpdate(loader=self)
        self.command_table['network vpn-connection show-device-config-script'] = VpnConnectionDeviceConfigScriptShow(loader=self)
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('list', 'list_vpn_connections')

    with self.command_group('network vpn-connection shared-key'):
        from .custom import VpnConnSharedKeyUpdate
        self.command_table['network vpn-connection shared-key update'] = VpnConnSharedKeyUpdate(loader=self)

    with self.command_group('network vpn-connection ipsec-policy') as g:
        from .custom import VpnConnIpsecPolicyAdd
        self.command_table['network vpn-connection ipsec-policy add'] = VpnConnIpsecPolicyAdd(loader=self)
        g.custom_command('clear', 'clear_vpn_conn_ipsec_policies', supports_no_wait=True)

    with self.command_group('network vpn-connection packet-capture'):
        from .custom import VpnConnPackageCaptureStop
        from .aaz.latest.network.vpn_connection import Wait
        self.command_table['network vpn-connection packet-capture stop'] = VpnConnPackageCaptureStop(loader=self)
        self.command_table['network vpn-connection packet-capture wait'] = Wait(loader=self)
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

    # region NatGateway
    from .operations.nat import GatewayCreate as NATGatewayCreate, GatewayUpdate as NATGatewayUpdate
    self.command_table["network nat gateway create"] = NATGatewayCreate(loader=self)
    self.command_table["network nat gateway update"] = NATGatewayUpdate(loader=self)
    # endregion

    # region SecurityPartnerProvider
    from .custom import SecurityPartnerProviderCreate, SecurityPartnerProviderUpdate
    self.command_table["network security-partner-provider create"] = SecurityPartnerProviderCreate(loader=self)
    self.command_table["network security-partner-provider update"] = SecurityPartnerProviderUpdate(loader=self)
    # endregion

    # region VirtualAppliance
    from .custom import VirtualApplianceCreate, VirtualApplianceUpdate
    self.command_table["network virtual-appliance create"] = VirtualApplianceCreate(loader=self)
    self.command_table["network virtual-appliance update"] = VirtualApplianceUpdate(loader=self)
    # endregion

    # region CustomIp
    from .custom import CustomIpPrefixCreate, CustomIpPrefixUpdate
    self.command_table["network custom-ip prefix create"] = CustomIpPrefixCreate(loader=self)
    self.command_table["network custom-ip prefix update"] = CustomIpPrefixUpdate(loader=self)
    # endregion

    # region DdosCustomPolicy
    with self.command_group('network ddos-custom-policy') as g:
        g.custom_command('create', 'create_ddos_custom_policy', supports_no_wait=True)
    # endregion
