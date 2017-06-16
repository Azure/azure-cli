# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import ServiceGroup, create_service_adapter
from ._client_factory import cf_cdn

custom_operations = 'azure.cli.command_modules.cdn.custom#{}'

mgmt_operations = create_service_adapter('azure.mgmt.cdn', 'CdnManagementClient')
with ServiceGroup(__name__, cf_cdn, mgmt_operations, custom_operations) as s:
    with s.group('cdn') as c:
        c.command('name-exists', 'check_name_availability')
        c.command('usage', 'check_resource_usage')

endpoint_operations = create_service_adapter('azure.mgmt.cdn.operations.endpoints_operations',
                                             'EndpointsOperations')
with ServiceGroup(__name__, cf_cdn, endpoint_operations, custom_operations) as s:
    with s.group('cdn endpoint') as c:
        for name in ['start', 'stop', 'delete']:
            c.command(name, name)
        c.command('show', 'get')
        c.command('list', 'list_by_profile')
        c.command('load', 'load_content')
        c.command('purge', 'purge_content')
        c.command('validate-custom-domain', 'validate_custom_domain')
        c.custom_command('create', 'create_endpoint')
        c.generic_update_command('update', 'get', 'update', custom_func_name='update_endpoint',
                                 setter_arg_name='endpoint_update_properties')

profile_operations = create_service_adapter('azure.mgmt.cdn.operations.profiles_operations',
                                            'ProfilesOperations')
with ServiceGroup(__name__, cf_cdn, profile_operations, custom_operations) as s:
    with s.group('cdn profile') as c:
        c.command('show', 'get')
        c.command('usage', 'list_resource_usage')
        c.command('delete', 'delete')
        c.custom_command('list', 'list_profiles')
        c.custom_command('create', 'create_profile')
        c.generic_update_command('update', 'get', 'update', custom_func_name='update_profile')

domain_operations = create_service_adapter('azure.mgmt.cdn.operations.custom_domains_operations',
                                           'CustomDomainsOperations')
with ServiceGroup(__name__, cf_cdn, domain_operations, custom_operations) as s:
    with s.group('cdn custom-domain') as c:
        c.command('show', 'get')
        c.command('delete', 'delete')
        c.command('list', 'list_by_endpoint')
        c.custom_command('create', 'create_custom_domain')

origin_operations = create_service_adapter('azure.mgmt.cdn.operations.origins_operations',
                                           'OriginsOperations')
with ServiceGroup(__name__, cf_cdn, origin_operations, custom_operations) as s:
    with s.group('cdn origin') as c:
        c.command('show', 'get')
        c.command('list', 'list_by_endpoint')

edge_operations = create_service_adapter('azure.mgmt.cdn.operations.edge_nodes_operations',
                                         'EdgeNodesOperations')
with ServiceGroup(__name__, cf_cdn, edge_operations, custom_operations) as s:
    with s.group('cdn edge-node') as c:
        c.command('list', 'list')
