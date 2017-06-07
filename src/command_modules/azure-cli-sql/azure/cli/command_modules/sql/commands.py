# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.sdk.util import (
    create_service_adapter,
    ServiceGroup)
from ._util import (
    get_sql_servers_operations,
    get_sql_firewall_rules_operations,
    get_sql_databases_operations,
    get_sql_elastic_pools_operations,
    get_sql_capabilities_operations)

custom_path = 'azure.cli.command_modules.sql.custom#{}'

###############################################
#                sql capabilities             #
###############################################

capabilities_operations = create_service_adapter(
    'azure.mgmt.sql.operations.capabilities_operations',
    'CapabilitiesOperations')

with ServiceGroup(__name__, get_sql_capabilities_operations, capabilities_operations, custom_path) as s:
    with s.group('sql db') as c:
        c.custom_command('list-editions', 'db_list_capabilities')

    with s.group('sql elastic-pool') as c:
        c.custom_command('list-editions', 'elastic_pool_list_capabilities')


###############################################
#                sql db                       #
###############################################

database_operations = create_service_adapter('azure.mgmt.sql.operations.databases_operations',
                                             'DatabasesOperations')

with ServiceGroup(__name__, get_sql_databases_operations, database_operations, custom_path) as s:
    with s.group('sql db') as c:
        c.custom_command('create', 'db_create')
        c.custom_command('copy', 'db_copy')
        c.custom_command('restore', 'db_restore')
        c.command('show', 'get')
        c.custom_command('list', 'db_list')
        c.command('list-usages', 'list_usages')
        c.command('delete', 'delete', confirmation=True)
        c.generic_update_command('update', 'get', 'create_or_update', custom_func_name='db_update')
        c.custom_command('import', 'db_import')
        c.custom_command('export', 'db_export')

    with s.group('sql db replica') as c:
        c.custom_command('create', 'db_create_replica')
        c.command('list-links', 'list_replication_links')
        c.custom_command('delete-link', 'db_delete_replica_link', confirmation=True)
        c.custom_command('set-primary', 'db_failover')

    with s.group('sql dw') as c:
        c.custom_command('create', 'dw_create')
        c.command('show', 'get')
        c.custom_command('list', 'dw_list')
        c.command('delete', 'delete', confirmation=True)
        c.command('pause', 'pause')
        c.command('resume', 'resume')
        c.generic_update_command('update', 'get', 'create_or_update', custom_func_name='dw_update')

    # Data Warehouse restore will not be included in the first batch of GA commands
    # (list_restore_points also applies to db, but it's not very useful. It's
    # mainly useful for dw.)
    # with s.group('sql db restore-point') as c:
    #     c.command('list', 'list_restore_points')

    # TDE will not be included in the first batch of GA commands
    # with s.group('sql db transparent-data-encryption') as c:
    #     c.command('create', 'create_or_update_transparent_data_encryption_configuration')
    #     c.command('show-configuration', 'get_transparent_data_encryption_configuration')
    #     c.command('show-activity', 'list_transparent_data_encryption_activity')

    # Service tier advisor will not be included in the first batch of GA commands
    # with s.group('sql db service-tier-advisor') as c:
    #     c.command('list', 'list_service_tier_advisors')
    #     c.command('show', 'get_service_tier_advisor')

    with s.group('sql db audit-policy') as c:
        c.command('show', 'get_blob_auditing_policy')
        c.generic_update_command(
            'update', 'get_blob_auditing_policy', 'create_or_update_blob_auditing_policy',
            custom_func_name='db_audit_policy_update')

    with s.group('sql db threat-policy') as c:
        c.command('show', 'get_threat_detection_policy')
        c.generic_update_command('update', 'get_threat_detection_policy',
                                 'create_or_update_threat_detection_policy',
                                 custom_func_name='db_threat_detection_policy_update')

###############################################
#                sql elastic-pool             #
###############################################

elastic_pools_ops = create_service_adapter('azure.mgmt.sql.operations.elastic_pools_operations',
                                           'ElasticPoolsOperations')

with ServiceGroup(__name__, get_sql_elastic_pools_operations, elastic_pools_ops, custom_path) as s:
    with s.group('sql elastic-pool') as c:
        c.custom_command('create', 'elastic_pool_create')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_server')
        c.command('list-dbs', 'list_databases')
        c.generic_update_command(
            'update', 'get', 'create_or_update',
            custom_func_name='elastic_pool_update')

recommanded_elastic_pools_ops = \
    create_service_adapter('azure.mgmt.sql.operations.recommended_elastic_pools_operations',
                           'RecommendedElasticPoolsOperations')

# Recommended elastic pools will not be included in the first batch of GA commands
# with ServiceGroup(__name__, get_sql_recommended_elastic_pools_operations,
#                   recommanded_elastic_pools_ops) as s:
#    with s.group('sql elastic-pool recommended') as c:
#        c.command('show', 'get')
#        c.command('show-metrics', 'list_metrics')
#        c.command('list', 'list')

#    with s.group('sql elastic-pool recommended db') as c:
#        c.command('show', 'get_databases')
#        c.command('list', 'list_databases')

###############################################
#                sql server                   #
###############################################

servers_operations = create_service_adapter('azure.mgmt.sql.operations.servers_operations',
                                            'ServersOperations')

with ServiceGroup(__name__, get_sql_servers_operations, servers_operations, custom_path) as s:
    with s.group('sql server') as c:
        c.command('create', 'create_or_update')
        c.command('delete', 'delete', confirmation=True)
        c.command('show', 'get')
        c.command('list-usages', 'list_usages')
        c.command('list', 'list_by_resource_group')
        c.generic_update_command('update', 'get', 'create_or_update',
                                 custom_func_name='server_update')

firewall_rules_operations = create_service_adapter(
    'azure.mgmt.sql.operations.firewall_rules_operations',
    'FirewallRulesOperations')

with ServiceGroup(__name__, get_sql_firewall_rules_operations, firewall_rules_operations,
                  custom_path) as s:
    with s.group('sql server firewall-rule') as c:
        c.command('create', 'create_or_update')
        c.custom_command('update', 'firewall_rule_update')
        c.command('delete', 'delete')
        c.command('show', 'get')
        c.command('list', 'list_by_server')
        # Keeping this command hidden for now. `firewall-rule create` will explain the special
        # 0.0.0.0 rule.
        # c.custom_command('allow-all-azure-ips', 'firewall_rule_allow_all_azure_ips')
