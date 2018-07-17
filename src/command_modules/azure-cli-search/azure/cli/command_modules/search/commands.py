# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long


def load_command_table(self, _):
    from azure.cli.core.commands import CliCommandType
    from azure.cli.command_modules.search._client_factory import cf_search_services, cf_search_admin_keys, \
        cf_search_query_keys

    search_services_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#ServicesOperations.{}',
        client_factory=cf_search_services
    )

    search_admin_keys_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#AdminKeysOperations.{}',
        client_factory=cf_search_admin_keys
    )

    search_query_keys_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.search.operations#QueryKeysOperations.{}',
        client_factory=cf_search_query_keys
    )

    with self.command_group('search services', search_services_sdk) as g:
        # right now list_by_resource_group is the only way to list, so directly map to list_by_resource_group.
        g.command('list', 'list_by_resource_group')
        g.command('show', 'get')
        g.command('delete', 'delete')
        g.custom_command('update', 'update_search_service')
        g.custom_command('create', 'create_search_service')

    with self.command_group('search adminkeys', search_admin_keys_sdk) as g:
        g.command('show', 'get')
        g.command('renew', 'regenerate')

    with self.command_group('search querykeys', search_query_keys_sdk) as g:
        g.command('list', 'list_by_search_service')
        g.custom_command('create', 'create_search_querykey')
        g.command('delete', 'delete')
