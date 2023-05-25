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
    cf_dns_mgmt_record_sets, cf_dns_mgmt_zones,
    cf_dns_references)
from azure.cli.command_modules.network.azure_stack._format import (
    transform_dns_record_set_output,
    transform_dns_record_set_table_output, transform_dns_zone_table_output)
from azure.cli.command_modules.network.azure_stack._validators import (
    process_lb_create_namespace,
    process_vpn_connection_create_namespace)


# pylint: disable=too-many-locals, too-many-statements
def load_command_table(self, _):

    # region Command Types

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

    # region LoadBalancers
    with self.command_group('network lb') as g:
        g.custom_command('create', 'create_load_balancer',
                         transform=DeploymentOutputLongRunningOperation(self.cli_ctx),
                         supports_no_wait=True,
                         table_transformer=deployment_validate_table_format,
                         validator=process_lb_create_namespace,
                         exception_handler=handle_template_based_exception)
    # endregion

    # region VirtualNetworkGatewayConnections
    with self.command_group('network vpn-connection') as g:
        g.custom_command('create', 'create_vpn_connection', transform=DeploymentOutputLongRunningOperation(self.cli_ctx), table_transformer=deployment_validate_table_format, validator=process_vpn_connection_create_namespace, exception_handler=handle_template_based_exception)
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
