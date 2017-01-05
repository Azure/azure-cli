# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import get_sql_servers_operation, ServiceGroup, create_service_adapter


server_operations = create_service_adapter('azure.mgmt.sql.operations.servers_operations',
                                           'ServersOperations')

with ServiceGroup(__name__, get_sql_servers_operation, server_operations) as s:
    with s.group('sql server') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get_by_resource_group')
        c.command('usage', 'list_usages')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get_by_resource_group', 'create_or_update')

    with s.group('sql server service-objective') as c:
        c.command('list', 'list_service_objectives')
        c.command('show', 'get_service_objective')

    with s.group('sql server firewall') as c:
        c.command('create', 'create_or_update_firewall_rule')
        c.command('update', 'create_or_update_firewall_rule')
        c.command('delete', 'delete_firewall_rule')
        c.command('show', 'get_firewall_rule')
        c.command('list', 'list_firewall_rules')
