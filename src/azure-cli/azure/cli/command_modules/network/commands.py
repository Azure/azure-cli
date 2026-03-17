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
    transform_dns_record_set_output,
    transform_dns_zone_table_output, transform_public_ip_create_output,
    transform_traffic_manager_create_output,
    transform_waf_rule_sets_table_output,
    transform_nsg_rule_table_output)
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
    # region ApplicationGateways
    with self.command_group("network application-gateway") as g:
        g.custom_command("show-backend-health", "show_ag_backend_health")
        g.custom_command("create", "create_application_gateway",
                         transform=DeploymentOutputLongRunningOperation(self.cli_ctx),
                         supports_no_wait=True,
                         table_transformer=deployment_validate_table_format,
                         validator=process_ag_create_namespace,
                         exception_handler=handle_template_based_exception)

    with self.command_group("network application-gateway identity") as g:
        g.custom_command("remove", "remove_ag_identity", supports_no_wait=True)

    with self.command_group("network application-gateway waf-config") as g:
        g.custom_command("list-rule-sets", "list_ag_waf_rule_sets", table_transformer=transform_waf_rule_sets_table_output)
        g.custom_command("set", "set_ag_waf_config", supports_no_wait=True)
        g.custom_show_command("show", "show_ag_waf_config")
    # endregion

    # region ApplicationGatewayWAFPolicy
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
        g.custom_command("list", "list_waf_policy_setting")
    # endregion

    # region DdosProtectionPlans
    with self.command_group('network ddos-protection') as g:
        g.custom_command('create', 'create_ddos_plan')
        g.custom_command('update', 'update_ddos_plan')
    # endregion

    # region DNS
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
    # endregion

    # region ExpressRoutes
    with self.command_group('network express-route port') as g:
        g.custom_command('generate-loa', 'download_generated_loa_as_pdf')
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
    # endregion

    # region cross-region load balancer
    with self.command_group('network cross-region-lb') as g:
        g.custom_command('create', 'create_cross_region_load_balancer', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), supports_no_wait=True, table_transformer=deployment_validate_table_format, validator=process_cross_region_lb_create_namespace, exception_handler=handle_template_based_exception)
    # endregion

    # region NetworkInterfaces: (NIC)
    with self.command_group("network nic ip-config address-pool") as g:
        g.custom_command("add", "add_nic_ip_config_address_pool")
        g.custom_command("remove", "remove_nic_ip_config_address_pool")
    # endregion

    # region NetworkSecurityGroups
    with self.command_group("network nsg rule") as g:
        g.custom_command("list", "list_nsg_rules", table_transformer=lambda x: [transform_nsg_rule_table_output(i) for i in x])
    # endregion

    # region NetworkWatchers
    with self.command_group("network watcher") as g:
        g.custom_command("configure", "configure_network_watcher")

    with self.command_group('network watcher connection-monitor test-group', is_preview=True) as c:
        c.custom_command('remove', 'remove_nw_connection_monitor_test_group')

    with self.command_group('network watcher connection-monitor output', is_preview=True) as c:
        c.custom_command('remove', 'remove_nw_connection_monitor_output')

    with self.command_group('network watcher flow-log') as g:
        g.custom_show_command('show', 'show_nw_flow_logging', validator=process_nw_flow_log_show_namespace)
    # endregion

    # region PublicIPAddresses
    with self.command_group('network public-ip') as g:
        g.custom_command('create', 'create_public_ip', transform=transform_public_ip_create_output, validator=process_public_ip_create_namespace)
    # endregion

    # region TrafficManagers
    with self.command_group('network traffic-manager profile') as g:
        g.custom_command('create', 'create_traffic_manager_profile', transform=transform_traffic_manager_create_output)
        g.custom_command('update', 'update_traffic_manager_profile')

    with self.command_group('network traffic-manager endpoint') as g:
        g.custom_command('create', 'create_traffic_manager_endpoint')
        g.custom_command('update', 'update_traffic_manager_endpoint')
        g.custom_command('list', 'list_traffic_manager_endpoints')
    # endregion

    # region VirtualNetworks
    with self.command_group("network vnet") as g:
        g.custom_command("list-available-ips", "list_available_ips", is_preview=True)

    with self.command_group("network vnet peering") as g:
        g.custom_command("sync", "sync_vnet_peering")

    with self.command_group("network vnet subnet") as g:
        g.custom_command("list-available-ips", "subnet_list_available_ips", is_preview=True)
    # endregion

    # region VirtualNetworkGateways
    with self.command_group('network vnet-gateway vpn-client') as g:
        g.custom_command('generate', 'generate_vpn_client')

    with self.command_group('network vnet-gateway ipsec-policy') as g:
        g.custom_command('clear', 'clear_vnet_gateway_ipsec_policies', supports_no_wait=True)

    with self.command_group('network vnet-gateway aad') as g:
        g.custom_command('remove', 'remove_vnet_gateway_aad', supports_no_wait=True)
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection') as g:
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
        g.custom_command('list', 'list_vpn_connections')

    with self.command_group('network vpn-connection ipsec-policy') as g:
        g.custom_command('clear', 'clear_vpn_conn_ipsec_policies', supports_no_wait=True)
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

    # region DdosCustomPolicy
    with self.command_group('network ddos-custom-policy') as g:
        g.custom_command('create', 'create_ddos_custom_policy', supports_no_wait=True)
    # endregion
