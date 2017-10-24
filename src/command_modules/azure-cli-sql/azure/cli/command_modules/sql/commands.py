# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import cli_command
from azure.cli.core.profiles import supported_api_version, PROFILE_TYPE
from azure.cli.core.sdk.util import (
    create_service_adapter,
    ServiceGroup)
from ._util import (
    get_sql_server_azure_ad_administrators_operations,
    get_sql_capabilities_operations,
    get_sql_databases_operations,
    get_sql_database_blob_auditing_policies_operations,
    get_sql_database_operations_operations,
    get_sql_database_threat_detection_policies_operations,
    get_sql_database_transparent_data_encryption_activities_operations,
    get_sql_database_transparent_data_encryptions_operations,
    get_sql_database_usages_operations,
    get_sql_elastic_pools_operations,
    get_sql_encryption_protectors_operations,
    get_sql_firewall_rules_operations,
    get_sql_replication_links_operations,
    get_sql_restorable_dropped_databases_operations,
    get_sql_server_keys_operations,
    get_sql_servers_operations,
    get_sql_server_usages_operations,
    get_sql_virtual_network_rules_operations
)

if not supported_api_version(PROFILE_TYPE, max_api='2017-03-09-profile'):
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

    cli_command(__name__, 'sql db show-connection-string', custom_path.format('db_show_conn_str'), client_factory=None)

    database_operations = create_service_adapter('azure.mgmt.sql.operations.databases_operations',
                                                 'DatabasesOperations')

    with ServiceGroup(__name__, get_sql_databases_operations, database_operations, custom_path) as s:
        with s.group('sql db') as c:
            c.custom_command('create', 'db_create', no_wait_param='raw')
            c.custom_command('copy', 'db_copy', no_wait_param='raw')
            c.custom_command('restore', 'db_restore', no_wait_param='raw')
            c.command('show', 'get')
            c.custom_command('list', 'db_list')
            c.command('delete', 'delete', confirmation=True)
            c.generic_update_command('update', 'get', 'create_or_update',
                                     custom_func_name='db_update', no_wait_param='raw')
            c.custom_command('import', 'db_import')
            c.custom_command('export', 'db_export')

        with s.group('sql db replica') as c:
            c.custom_command('create', 'db_create_replica', no_wait_param='raw')

        with s.group('sql dw') as c:
            c.custom_command('create', 'dw_create', no_wait_param='raw')
            c.command('show', 'get')
            c.custom_command('list', 'dw_list')
            c.command('delete', 'delete', confirmation=True)
            c.command('pause', 'pause')
            c.command('resume', 'resume')
            c.generic_update_command('update', 'get', 'create_or_update',
                                     custom_func_name='dw_update', no_wait_param='raw')

        # Data Warehouse restore will not be included in the first batch of GA commands
        # (list_restore_points also applies to db, but it's not very useful. It's
        # mainly useful for dw.)
        # with s.group('sql db restore-point') as c:
        #     c.command('list', 'list_restore_points')

        # Service tier advisor will not be included in the first batch of GA commands
        # with s.group('sql db service-tier-advisor') as c:
        #     c.command('list', 'list_service_tier_advisors')
        #     c.command('show', 'get_service_tier_advisor')

    database_operations_operations = create_service_adapter('azure.mgmt.sql.operations.database_operations',
                                                            'DatabaseOperations')
    with ServiceGroup(__name__, get_sql_database_operations_operations,
                      database_operations_operations, custom_path) as s:
        with s.group('sql db op') as c:
            c.command('list', 'list_by_database')
            c.command('cancel', 'cancel')

    transparent_data_encryptions_operations = create_service_adapter(
        'azure.mgmt.sql.operations.transparent_data_encryptions_operations',
        'TransparentDataEncryptionsOperations')
    with ServiceGroup(__name__, get_sql_database_transparent_data_encryptions_operations,
                      transparent_data_encryptions_operations, custom_path) as s:
        with s.group('sql db tde') as c:
            c.command('set', 'create_or_update')
            c.command('show', 'get')

    transparent_data_encryption_activities_operations = create_service_adapter(
        'azure.mgmt.sql.operations.transparent_data_encryption_activities_operations',
        'TransparentDataEncryptionActivitiesOperations')
    with ServiceGroup(__name__, get_sql_database_transparent_data_encryption_activities_operations,
                      transparent_data_encryption_activities_operations, custom_path) as s:
        with s.group('sql db tde') as c:
            c.command('list-activity', 'list_by_configuration')

    replication_links_operations = create_service_adapter('azure.mgmt.sql.operations.replication_links_operations',
                                                          'ReplicationLinksOperations')
    with ServiceGroup(__name__, get_sql_replication_links_operations,
                      replication_links_operations, custom_path) as s:
        with s.group('sql db replica') as c:
            c.command('list-links', 'list_by_database')
            c.custom_command('delete-link', 'db_delete_replica_link', confirmation=True)
            c.custom_command('set-primary', 'db_failover')

    restorable_dropped_databases_operations = create_service_adapter(
        'azure.mgmt.sql.operations.restorable_dropped_databases_operations',
        'RestorableDroppedDatabasesOperations')
    with ServiceGroup(__name__, get_sql_restorable_dropped_databases_operations,
                      restorable_dropped_databases_operations, custom_path) as s:
        with s.group('sql db') as c:
            c.command('list-deleted', 'list_by_server')

    database_blob_auditing_policies_operations = create_service_adapter(
        'azure.mgmt.sql.operations.database_blob_auditing_policies_operations',
        'DatabaseBlobAuditingPoliciesOperations')
    with ServiceGroup(__name__, get_sql_database_blob_auditing_policies_operations,
                      database_blob_auditing_policies_operations, custom_path) as s:
        with s.group('sql db audit-policy') as c:
            c.command('show', 'get')
            c.generic_update_command(
                'update', 'get', 'create_or_update',
                custom_func_name='db_audit_policy_update')

    database_threat_detection_policies_operations = create_service_adapter(
        'azure.mgmt.sql.operations.database_threat_detection_policies_operations',
        'DatabaseThreatDetectionPoliciesOperations')
    with ServiceGroup(__name__, get_sql_database_threat_detection_policies_operations,
                      database_threat_detection_policies_operations, custom_path) as s:
        with s.group('sql db threat-policy') as c:
            c.command('show', 'get')
            c.generic_update_command('update', 'get',
                                     'create_or_update',
                                     custom_func_name='db_threat_detection_policy_update')

    database_usages_operations = create_service_adapter('azure.mgmt.sql.operations.database_usages_operations',
                                                        'DatabaseUsagesOperations')

    with ServiceGroup(__name__, get_sql_database_usages_operations, database_usages_operations, custom_path) as s:
        with s.group('sql db') as c:
            c.command('list-usages', 'list_by_database')

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
            c.generic_update_command(
                'update', 'get', 'create_or_update',
                custom_func_name='elastic_pool_update')

    with ServiceGroup(__name__, get_sql_databases_operations, database_operations, custom_path) as s:
        with s.group('sql elastic-pool') as c:
            c.command('list-dbs', 'list_by_elastic_pool')

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
            c.custom_command('create', 'server_create')
            c.command('delete', 'delete', confirmation=True)
            c.command('show', 'get')
            c.custom_command('list', 'server_list')
            c.generic_update_command('update', 'get', 'create_or_update',
                                     custom_func_name='server_update')

    server_usages_operations = create_service_adapter('azure.mgmt.sql.operations.server_usages_operations',
                                                      'ServerUsagesOperations')

    with ServiceGroup(__name__, get_sql_server_usages_operations, server_usages_operations, custom_path) as s:
        with s.group('sql server') as c:
            c.command('list-usages', 'list_by_server')

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

    aadadmin_operations = create_service_adapter('azure.mgmt.sql.operations.server_azure_ad_administrators_operations',
                                                 'ServerAzureADAdministratorsOperations')

    with ServiceGroup(__name__, get_sql_server_azure_ad_administrators_operations,
                      aadadmin_operations, custom_path) as s:
        with s.group('sql server ad-admin') as c:
            c.custom_command('create', 'server_ad_admin_set')
            c.command('list', 'list_by_server')
            c.command('delete', 'delete')
            c.generic_update_command('update', 'get', 'create_or_update',
                                     custom_func_name='server_ad_admin_update',
                                     setter_arg_name='properties')

    server_keys_operations = create_service_adapter('azure.mgmt.sql.operations.server_keys_operations',
                                                    'ServerKeysOperations')

    with ServiceGroup(__name__, get_sql_server_keys_operations, server_keys_operations, custom_path) as s:
        with s.group('sql server key') as c:
            c.custom_command('create', 'server_key_create')
            c.custom_command('delete', 'server_key_delete')
            c.custom_command('show', 'server_key_get')
            c.command('list', 'list_by_server')

    encryption_protectors_operations = create_service_adapter(
        'azure.mgmt.sql.operations.encryption_protectors_operations',
        'EncryptionProtectorsOperations')

    with ServiceGroup(__name__, get_sql_encryption_protectors_operations, encryption_protectors_operations,
                      custom_path) as s:
        with s.group('sql server tde-key') as c:
            c.command('show', 'get')
            c.custom_command('set', 'encryption_protector_update')

    virtual_network_rules_operations = create_service_adapter(
        'azure.mgmt.sql.operations.virtual_network_rules_operations',
        'VirtualNetworkRulesOperations')

    with ServiceGroup(__name__, get_sql_virtual_network_rules_operations, virtual_network_rules_operations,
                      custom_path) as s:
        with s.group('sql server vnet-rule') as c:
            c.command('create', 'create_or_update')
            c.command('show', 'get')
            c.command('list', 'list_by_server')
            c.command('delete', 'delete')
            c.generic_update_command('update', 'get', 'create_or_update')
