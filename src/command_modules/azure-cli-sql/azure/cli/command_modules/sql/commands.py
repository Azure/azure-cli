# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ._util import (get_sql_servers_operation, get_sql_database_operations,
                    get_sql_elasticpools_operations, get_sql_recommended_elastic_pools_operations,
                    ServiceGroup, create_service_adapter)

server_operations = create_service_adapter('azure.mgmt.sql.operations.servers_operations',
                                           'ServersOperations')

with ServiceGroup(__name__, get_sql_servers_operation, server_operations) as s:
    with s.group('sql server') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get_by_resource_group')
        c.command('show-usage', 'list_usages')
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

database_operations = create_service_adapter('azure.mgmt.sql.operations.databases_operations',
                                             'DatabasesOperations')

with ServiceGroup(__name__, get_sql_database_operations, database_operations) as s:
    with s.group('sql db') as c:
        c.command('create', 'create_or_update')
        c.command('show', 'get')
        c.command('list', 'list_by_server')
        c.command('show-usage', 'list_usages')
        c.command('delete', 'delete')
        c.generic_update_command('update', 'get', 'create_or_update')

    with s.group('sql db replication-link') as c:
        c.command('list', 'list_replication_links')
        c.command('show', 'get_replication_link')
        c.command('delete', 'delete_replication_link')
        c.command('failover', 'failover_replication_link')
        c.command('force-failover', 'failover_replication_link_allow_data_loss')

    with s.group('sql db data-warehouse') as c:
        c.command('pause', 'pause_data_warehouse')
        c.command('resume', 'resume_data_warehouse')

    with s.group('sql db restore-point') as c:
        c.command('list', 'list_restore_points')

    with s.group('sql db transparent-data-encryption') as c:
        c.command('create', 'create_or_update_transparent_data_encryption_configuration')
        c.command('show-configuration', 'get_transparent_data_encryption_configuration')
        c.command('show-activity', 'list_transparent_data_encryption_activity')

    with s.group('sql db service-tier-advisor') as c:
        c.command('list', 'list_service_tier_advisors')
        c.command('show', 'get_service_tier_advisor')

elasticpools_ops = create_service_adapter('azure.mgmt.sql.operations.elastic_pools_operations',
                                          'ElasticPoolsOperations')

with ServiceGroup(__name__, get_sql_elasticpools_operations, elasticpools_ops) as s:
    with s.group('sql elastic-pools') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_server')
        c.generic_update_command('update', 'get', 'create_or_update')

    with s.group('sql elastic-pools database') as c:
        c.command('list', 'list_databases')
        c.command('show', 'get_database')
        c.command('show-activity', 'list_database_activity')

recommanded_elastic_pools_ops = \
    create_service_adapter('azure.mgmt.sql.operations.recommended_elastic_pools_operations',
                           'RecommendedElasticPoolsOperations')

with ServiceGroup(__name__, get_sql_recommended_elastic_pools_operations,
                  recommanded_elastic_pools_ops) as s:
    with s.group('sql elastic-pools recommended') as c:
        c.command('show', 'get')
        c.command('show-metrics', 'list_metrics')
        c.command('list', 'list')

    with s.group('sql elastic-pools recommended database') as c:
        c.command('show', 'get_databases')
        c.command('list', 'list_databases')
