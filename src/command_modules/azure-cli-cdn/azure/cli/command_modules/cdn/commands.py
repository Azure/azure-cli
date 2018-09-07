# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._client_factory import (cf_cdn, cf_custom_domain, cf_endpoints, cf_profiles, cf_origins, cf_resource_usage,
                              cf_edge_nodes)


def load_command_table(self, _):

    def _not_found(message):
        def _inner_not_found(ex):
            from azure.mgmt.cdn.models import ErrorResponseException
            from knack.util import CLIError

            if isinstance(ex, ErrorResponseException) \
                    and ex.response is not None \
                    and ex.response.status_code == 404:
                raise CLIError(message)
            raise ex
        return _inner_not_found

    not_found_msg = "{}(s) not found. Please verify the resource(s), group or it's parent resources " \
                    "exist."
    profile_not_found_msg = not_found_msg.format('Profile')
    endpoint_not_found_msg = not_found_msg.format('Endpoint')
    cd_not_found_msg = not_found_msg.format('Custom Domain')
    origin_not_found_msg = not_found_msg.format('Origin')

    cdn_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn#CdnManagementClient.{}',
        client_factory=cf_cdn
    )

    cdn_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.endpoints_operations#EndpointsOperations.{}',
        client_factory=cf_endpoints,
        exception_handler=_not_found(endpoint_not_found_msg)
    )

    cdn_profiles_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.profiles_operations#ProfilesOperations.{}',
        client_factory=cf_profiles,
        exception_handler=_not_found(profile_not_found_msg)
    )

    cdn_domain_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.custom_domains_operations#CustomDomainsOperations.{}',
        client_factory=cf_custom_domain,
        exception_handler=_not_found(cd_not_found_msg)
    )

    cdn_origin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.origins_operations#OriginsOperations.{}',
        client_factory=cf_origins,
        exception_handler=_not_found(origin_not_found_msg)
    )

    cdn_edge_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.edge_nodes_operations#EdgeNodesOperations.{}',
        client_factory=cf_edge_nodes
    )

    cdn_usage_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.cdn.operations.resource_usage_operations#ResourceUsageOperations.{}',
        client_factory=cf_resource_usage
    )

    with self.command_group('cdn', cdn_sdk) as g:
        g.command('name-exists', 'check_name_availability')

    with self.command_group('cdn', cdn_usage_sdk) as g:
        g.command('usage', 'list')

    with self.command_group('cdn endpoint', cdn_endpoints_sdk) as g:
        for name in ['start', 'stop', 'delete']:
            g.command(name, name)
        g.show_command('show', 'get')
        g.command('list', 'list_by_profile')
        g.command('load', 'load_content')
        g.command('purge', 'purge_content')
        g.command('validate-custom-domain', 'validate_custom_domain')
        g.custom_command('create', 'create_endpoint', client_factory=cf_cdn,
                         doc_string_source='azure.mgmt.cdn.models#Endpoint')
        g.generic_update_command('update', setter_name='update', setter_arg_name='endpoint_update_properties',
                                 custom_func_name='update_endpoint',
                                 doc_string_source='azure.mgmt.cdn.models#EndpointUpdateParameters')

    with self.command_group('cdn profile', cdn_profiles_sdk) as g:
        g.show_command('show', 'get')
        g.command('usage', 'list_resource_usage')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_profiles', client_factory=cf_cdn)
        g.custom_command('create', 'create_profile', client_factory=cf_cdn)
        g.generic_update_command('update', setter_name='update', custom_func_name='update_profile',
                                 doc_string_source='azure.mgmt.cdn.models#ProfileUpdateParameters')

    with self.command_group('cdn custom-domain', cdn_domain_sdk) as g:
        g.show_command('show', 'get')
        g.command('delete', 'delete')
        g.command('list', 'list_by_endpoint')
        g.custom_command('create', 'create_custom_domain', client_factory=cf_cdn)
        g.command('enable-https', 'enable_custom_https')
        g.command('disable-https', 'disable_custom_https')

    with self.command_group('cdn origin', cdn_origin_sdk) as g:
        g.show_command('show', 'get')
        g.command('list', 'list_by_endpoint')

    with self.command_group('cdn edge-node', cdn_edge_sdk) as g:
        g.command('list', 'list')
