# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from azure.cli.command_modules.search._client_factory import cf_search_services, cf_search_private_endpoint_connections, \
        cf_search_private_link_resources, cf_search_shared_private_link_resources, cf_search_admin_keys, cf_search_query_keys

    search_services_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#ServicesOperations.{}',
        client_factory=cf_search_services
    )

    search_private_endpoint_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=cf_search_private_endpoint_connections
    )

    search_private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#PrivateLinkResourcesOperations.{}',
        client_factory=cf_search_private_link_resources
    )

    search_shared_private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#SharedPrivateLinkResourcesOperations.{}',
        client_factory=cf_search_shared_private_link_resources
    )

    search_admin_keys_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#AdminKeysOperations.{}',
        client_factory=cf_search_admin_keys
    )

    search_query_keys_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#QueryKeysOperations.{}',
        client_factory=cf_search_query_keys
    )

    with self.command_group('search service', search_services_sdk) as g:
        # right now list_by_resource_group is the only way to list, so directly map to list_by_resource_group.
        g.command('list', 'list_by_resource_group')
        g.show_command('show', 'get')
        g.command('delete', 'delete', confirmation=True)
        g.generic_update_command('update', supports_no_wait=True, custom_func_name='update_search_service', setter_name='begin_create_or_update', setter_arg_name='service')
        g.custom_command('create', 'create_search_service', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('search private-endpoint-connection', search_private_endpoint_connections_sdk) as g:
        g.command('list', 'list_by_service')
        g.show_command('show', 'get')
        g.command('delete', 'delete', confirmation=True)
        g.custom_command('update', 'update_private_endpoint_connection')

    with self.command_group('search private-link-resource', search_private_link_resources_sdk) as g:
        g.command('list', 'list_supported')

    with self.command_group('search shared-private-link-resource', search_shared_private_link_resources_sdk) as g:
        g.command('list', 'list_by_service')
        g.show_command('show', 'get')
        g.command('delete', 'begin_delete', confirmation=True)
        g.custom_command('create', 'create_shared_private_link_resource', supports_no_wait=True)
        g.custom_command('update', 'update_shared_private_link_resource', supports_no_wait=True)
        g.wait_command('wait')

    with self.command_group('search admin-key', search_admin_keys_sdk) as g:
        g.show_command('show', 'get')
        g.command('renew', 'regenerate')

    with self.command_group('search query-key', search_query_keys_sdk) as g:
        g.command('list', 'list_by_search_service')
        g.command('create', 'create')
        g.command('delete', 'delete')

    with self.command_group('search'):
        pass
