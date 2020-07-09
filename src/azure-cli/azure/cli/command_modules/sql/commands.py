# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

from ._format import (
    db_list_transform,
    db_transform,
    db_table_format,
    db_edition_table_format,
    elastic_pool_list_transform,
    elastic_pool_transform,
    elastic_pool_table_format,
    elastic_pool_edition_table_format,
    firewall_rule_table_format,
    instance_pool_table_format,
    server_table_format,
    usage_table_format,
    LongRunningOperationResultTransform,
)

from ._util import (
    get_sql_server_azure_ad_administrators_operations,
    get_sql_capabilities_operations,
    get_sql_databases_operations,
    get_sql_database_blob_auditing_policies_operations,
    get_sql_database_long_term_retention_backups_operations,
    get_sql_database_long_term_retention_policies_operations,
    get_sql_database_sensitivity_labels_operations,
    get_sql_database_operations_operations,
    get_sql_database_threat_detection_policies_operations,
    get_sql_database_transparent_data_encryption_activities_operations,
    get_sql_database_transparent_data_encryptions_operations,
    get_sql_database_usages_operations,
    get_sql_elastic_pools_operations,
    get_sql_elastic_pool_operations_operations,
    get_sql_encryption_protectors_operations,
    get_sql_failover_groups_operations,
    get_sql_firewall_rules_operations,
    get_sql_instance_pools_operations,
    get_sql_managed_databases_operations,
    get_sql_managed_backup_short_term_retention_policies_operations,
    get_sql_managed_database_long_term_retention_policies_operations,
    get_sql_managed_database_long_term_retention_backups_operations,
    get_sql_managed_instance_azure_ad_administrators_operations,
    get_sql_managed_instance_encryption_protectors_operations,
    get_sql_managed_instance_keys_operations,
    get_sql_managed_instance_operations_operations,
    get_sql_managed_instances_operations,
    get_sql_replication_links_operations,
    get_sql_restorable_dropped_databases_operations,
    get_sql_restorable_dropped_managed_databases_operations,
    get_sql_server_connection_policies_operations,
    get_sql_server_dns_aliases_operations,
    get_sql_server_keys_operations,
    get_sql_servers_operations,
    get_sql_server_usages_operations,
    get_sql_subscription_usages_operations,
    get_sql_virtual_clusters_operations,
    get_sql_virtual_network_rules_operations,
    get_sql_instance_failover_groups_operations
)

from ._validators import (
    validate_subnet
)


# pylint: disable=too-many-statements,line-too-long,too-many-locals
def load_command_table(self, _):

    ###############################################
    #                sql list-usages              #
    ###############################################

    subscription_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#SubscriptionUsagesOperations.{}',
        client_factory=get_sql_subscription_usages_operations)

    with self.command_group('sql',
                            subscription_usages_operations,
                            client_factory=get_sql_subscription_usages_operations) as g:

        g.command('list-usages', 'list_by_location',
                  table_transformer=usage_table_format)

        g.command('show-usage', 'get',
                  table_transformer=usage_table_format)

    ###############################################
    #                sql db                       #
    ###############################################

    with self.command_group('sql db') as g:
        g.custom_command('show-connection-string', 'db_show_conn_str')

    database_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#DatabasesOperations.{}',
        client_factory=get_sql_databases_operations)

    database_lro_transform = LongRunningOperationResultTransform(
        self.cli_ctx, db_transform)

    with self.command_group('sql db',
                            database_operations,
                            client_factory=get_sql_databases_operations) as g:

        g.custom_command('create', 'db_create',
                         supports_no_wait=True,
                         transform=database_lro_transform,
                         table_transformer=db_table_format)
        g.custom_command('copy', 'db_copy',
                         supports_no_wait=True,
                         transform=database_lro_transform,
                         table_transformer=db_table_format)
        g.custom_command('restore', 'db_restore',
                         supports_no_wait=True,
                         transform=database_lro_transform,
                         table_transformer=db_table_format)
        g.custom_command('rename', 'db_rename',
                         transform=database_lro_transform,
                         table_transformer=db_table_format)
        g.show_command('show', 'get',
                       transform=db_transform,
                       table_transformer=db_table_format)
        g.custom_command('list', 'db_list',
                         transform=db_list_transform,
                         table_transformer=db_table_format)
        g.command('delete', 'delete',
                  confirmation=True,
                  supports_no_wait=True)
        g.generic_update_command('update',
                                 custom_func_name='db_update',
                                 supports_no_wait=True,
                                 transform=database_lro_transform,
                                 table_transformer=db_table_format)
        g.custom_command('import', 'db_import')
        g.custom_command('export', 'db_export')

    capabilities_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#CapabilitiesOperations.{}',
        client_factory=get_sql_capabilities_operations)

    with self.command_group('sql db',
                            capabilities_operations,
                            client_factory=get_sql_capabilities_operations) as g:

        g.custom_command(
            'list-editions',
            'db_list_capabilities',
            table_transformer=db_edition_table_format)

    with self.command_group('sql db replica',
                            database_operations,
                            client_factory=get_sql_databases_operations) as g:

        g.custom_command('create', 'db_create_replica',
                         supports_no_wait=True,
                         transform=database_lro_transform,
                         table_transformer=db_table_format)

    with self.command_group('sql dw',
                            database_operations,
                            client_factory=get_sql_databases_operations) as g:

        g.custom_command('create', 'dw_create',
                         supports_no_wait=True,
                         transform=database_lro_transform)
        g.show_command('show', 'get',
                       transform=db_transform)
        g.custom_command('list', 'dw_list',
                         transform=db_list_transform)
        g.command('delete', 'delete',
                  confirmation=True,
                  supports_no_wait=True)
        g.custom_command('pause', 'dw_pause')
        g.custom_command('resume', 'dw_resume')
        g.generic_update_command('update',
                                 custom_func_name='dw_update',
                                 supports_no_wait=True,
                                 transform=database_lro_transform)

    database_operations_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#DatabaseOperations.{}',
        client_factory=get_sql_database_operations_operations)

    with self.command_group('sql db op', database_operations_operations) as g:

        g.command('list', 'list_by_database')
        g.command('cancel', 'cancel')

    transparent_data_encryptions_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#TransparentDataEncryptionsOperations.{}',
        client_factory=get_sql_database_transparent_data_encryptions_operations)

    with self.command_group('sql db tde', transparent_data_encryptions_operations) as g:

        g.command('set', 'create_or_update')
        g.show_command('show', 'get')

    transparent_data_encryption_activities_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#TransparentDataEncryptionActivitiesOperations.{}',
        client_factory=get_sql_database_transparent_data_encryption_activities_operations)

    with self.command_group('sql db tde', transparent_data_encryption_activities_operations) as g:

        g.command('list-activity', 'list_by_configuration')

    replication_links_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ReplicationLinksOperations.{}',
        client_factory=get_sql_replication_links_operations)

    with self.command_group('sql db replica',
                            replication_links_operations,
                            client_factory=get_sql_replication_links_operations) as g:

        g.command('list-links', 'list_by_database')
        g.custom_command('delete-link', 'db_delete_replica_link',
                         confirmation=True)
        g.custom_command('set-primary', 'db_failover')

    restorable_dropped_databases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#RestorableDroppedDatabasesOperations.{}',
        client_factory=get_sql_restorable_dropped_databases_operations)

    with self.command_group('sql db', restorable_dropped_databases_operations) as g:

        g.command('list-deleted', 'list_by_server')

    restorable_dropped_managed_databases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#RestorableDroppedManagedDatabasesOperations.{}',
        client_factory=get_sql_restorable_dropped_managed_databases_operations)

    with self.command_group('sql midb',
                            restorable_dropped_managed_databases_operations,
                            client_factory=get_sql_restorable_dropped_managed_databases_operations) as g:

        g.command('list-deleted', 'list_by_instance')

    database_blob_auditing_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#DatabaseBlobAuditingPoliciesOperations.{}',
        client_factory=get_sql_database_blob_auditing_policies_operations)

    with self.command_group('sql db audit-policy',
                            database_blob_auditing_policies_operations,
                            client_factory=get_sql_database_blob_auditing_policies_operations) as g:

        g.show_command('show', 'get')
        g.generic_update_command('update',
                                 custom_func_name='db_audit_policy_update')

    database_long_term_retention_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#BackupLongTermRetentionPoliciesOperations.{}',
        client_factory=get_sql_database_long_term_retention_policies_operations)

    with self.command_group('sql db ltr-policy',
                            database_long_term_retention_policies_operations,
                            client_factory=get_sql_database_long_term_retention_policies_operations,
                            is_preview=True) as g:

        g.custom_command('set', 'update_long_term_retention')
        g.show_command('show', 'get')

    database_long_term_retention_backups_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#LongTermRetentionBackupsOperations.{}',
        client_factory=get_sql_database_long_term_retention_backups_operations)

    with self.command_group('sql db ltr-backup',
                            database_long_term_retention_backups_operations,
                            client_factory=get_sql_database_long_term_retention_backups_operations,
                            is_preview=True) as g:

        g.show_command('show', 'get')
        g.custom_command('list', 'list_long_term_retention_backups')
        g.command('delete', 'delete', confirmation=True)

    with self.command_group('sql db ltr-backup',
                            database_operations,
                            client_factory=get_sql_databases_operations,
                            is_preview=True) as g:
        g.custom_command(
            'restore',
            'restore_long_term_retention_backup',
            supports_no_wait=True)
        g.wait_command('wait')

    database_sensitivity_labels_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#SensitivityLabelsOperations.{}',
        client_factory=get_sql_database_sensitivity_labels_operations)

    with self.command_group('sql db classification',
                            database_sensitivity_labels_operations,
                            client_factory=get_sql_database_sensitivity_labels_operations) as g:

        g.command('list', 'list_current_by_database')
        g.custom_command('show', 'db_sensitivity_label_show')
        g.command('delete', 'delete')
        g.custom_command('update', 'db_sensitivity_label_update')

    with self.command_group('sql db classification recommendation',
                            database_sensitivity_labels_operations,
                            client_factory=get_sql_database_sensitivity_labels_operations) as g:

        g.command('list', 'list_recommended_by_database')
        g.command('enable', 'enable_recommendation')
        g.command('disable', 'disable_recommendation')

    database_threat_detection_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#DatabaseThreatDetectionPoliciesOperations.{}',
        client_factory=get_sql_database_threat_detection_policies_operations)

    with self.command_group('sql db threat-policy',
                            database_threat_detection_policies_operations,
                            client_factory=get_sql_database_threat_detection_policies_operations) as g:

        g.show_command('show', 'get')
        g.generic_update_command('update',
                                 custom_func_name='db_threat_detection_policy_update')

    database_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#DatabaseUsagesOperations.{}',
        client_factory=get_sql_database_usages_operations)

    with self.command_group('sql db', database_usages_operations) as g:

        g.command('list-usages', 'list_by_database')

    ###############################################
    #                sql elastic-pool             #
    ###############################################

    elastic_pools_ops = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ElasticPoolsOperations.{}',
        client_factory=get_sql_elastic_pools_operations)

    elastic_pool_lro_transform = LongRunningOperationResultTransform(
        self.cli_ctx, elastic_pool_transform)

    with self.command_group('sql elastic-pool',
                            elastic_pools_ops,
                            client_factory=get_sql_elastic_pools_operations) as g:

        g.custom_command('create', 'elastic_pool_create',
                         supports_no_wait=True,
                         transform=elastic_pool_lro_transform,
                         table_transformer=elastic_pool_table_format)
        g.command('delete', 'delete',
                  supports_no_wait=True)
        g.show_command('show', 'get',
                       transform=elastic_pool_transform,
                       table_transformer=elastic_pool_table_format)
        g.command('list', 'list_by_server',
                  transform=elastic_pool_list_transform,
                  table_transformer=elastic_pool_table_format)
        g.generic_update_command('update',
                                 custom_func_name='elastic_pool_update',
                                 supports_no_wait=True,
                                 transform=elastic_pool_lro_transform,
                                 table_transformer=elastic_pool_table_format)

    with self.command_group('sql elastic-pool', database_operations) as g:

        g.command('list-dbs', 'list_by_elastic_pool',
                  transform=db_list_transform,
                  table_transformer=db_table_format)

    with self.command_group('sql elastic-pool',
                            capabilities_operations,
                            client_factory=get_sql_capabilities_operations) as g:

        g.custom_command('list-editions', 'elastic_pool_list_capabilities',
                         table_transformer=elastic_pool_edition_table_format)

    elastic_pool_operations_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ElasticPoolOperations.{}',
        client_factory=get_sql_elastic_pool_operations_operations)

    with self.command_group('sql elastic-pool op',
                            elastic_pool_operations_operations,
                            client_factory=get_sql_elastic_pool_operations_operations) as g:

        g.command('list', 'list_by_elastic_pool')
        g.command('cancel', 'cancel')

    ###############################################
    #             sql failover-group              #
    ###############################################

    failover_groups_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#FailoverGroupsOperations.{}',
        client_factory=get_sql_failover_groups_operations)
    with self.command_group('sql failover-group', failover_groups_operations, client_factory=get_sql_failover_groups_operations) as g:
        g.command('show', 'get')
        g.command('list', 'list_by_server')
        g.custom_command('create', 'failover_group_create')
        g.generic_update_command('update', custom_func_name='failover_group_update')
        g.command('delete', 'delete')
        g.custom_command('set-primary', 'failover_group_failover')

    ###############################################
    #             sql instance-pool               #
    ###############################################

    instance_pools_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#InstancePoolsOperations.{}',
        client_factory=get_sql_instance_pools_operations)
    with self.command_group('sql instance-pool', instance_pools_operations, client_factory=get_sql_instance_pools_operations, is_preview=True) as g:
        g.show_command('show', 'get',
                       table_transformer=instance_pool_table_format)
        g.custom_command('list', 'instance_pool_list',
                         table_transformer=instance_pool_table_format)
        g.command('update', 'update')
        g.command('delete', 'delete', supports_no_wait=True, confirmation=True)
        g.custom_command('create', 'instance_pool_create',
                         supports_no_wait=True, table_transformer=instance_pool_table_format)
        g.wait_command('wait')

    ###############################################
    #                sql server                   #
    ###############################################

    servers_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServersOperations.{}',
        client_factory=get_sql_servers_operations)

    with self.command_group('sql server',
                            servers_operations,
                            client_factory=get_sql_servers_operations) as g:

        g.custom_command('create', 'server_create',
                         table_transformer=server_table_format,
                         supports_no_wait=True)
        g.command('delete', 'delete',
                  confirmation=True)
        g.show_command('show', 'get',
                       table_transformer=server_table_format)
        g.custom_command('list', 'server_list',
                         table_transformer=server_table_format)
        g.generic_update_command('update',
                                 custom_func_name='server_update',
                                 supports_no_wait=True)
        g.wait_command('wait')

    server_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServerUsagesOperations.{}',
        client_factory=get_sql_server_usages_operations)

    with self.command_group('sql server', server_usages_operations) as g:
        g.command('list-usages', 'list_by_server')

    firewall_rules_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#FirewallRulesOperations.{}',
        client_factory=get_sql_firewall_rules_operations)

    with self.command_group('sql server firewall-rule',
                            firewall_rules_operations,
                            client_factory=get_sql_firewall_rules_operations) as g:

        g.command('create', 'create_or_update',
                  table_transformer=firewall_rule_table_format)
        g.custom_command('update', 'firewall_rule_update',
                         table_transformer=firewall_rule_table_format)
        g.command('delete', 'delete')
        g.show_command('show', 'get',
                       table_transformer=firewall_rule_table_format)
        g.command('list', 'list_by_server',
                  table_transformer=firewall_rule_table_format)

    aadadmin_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServerAzureADAdministratorsOperations.{}',
        client_factory=get_sql_server_azure_ad_administrators_operations)

    with self.command_group('sql server ad-admin',
                            aadadmin_operations,
                            client_factory=get_sql_server_azure_ad_administrators_operations) as g:
        g.custom_command('create', 'server_ad_admin_set')
        g.command('list', 'list_by_server')
        g.command('delete', 'delete')
        g.generic_update_command('update',
                                 custom_func_name='server_ad_admin_update',
                                 setter_arg_name='parameters')

    server_keys_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServerKeysOperations.{}',
        client_factory=get_sql_server_keys_operations)

    with self.command_group('sql server key',
                            server_keys_operations,
                            client_factory=get_sql_server_keys_operations) as g:

        g.custom_command('create', 'server_key_create')
        g.custom_command('delete', 'server_key_delete')
        g.custom_show_command('show', 'server_key_get')
        g.command('list', 'list_by_server')

    encryption_protectors_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#EncryptionProtectorsOperations.{}',
        client_factory=get_sql_encryption_protectors_operations)

    with self.command_group('sql server tde-key',
                            encryption_protectors_operations,
                            client_factory=get_sql_encryption_protectors_operations) as g:

        g.show_command('show', 'get')
        g.custom_command('set', 'encryption_protector_update')

    virtual_network_rules_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#VirtualNetworkRulesOperations.{}',
        client_factory=get_sql_virtual_network_rules_operations)

    with self.command_group('sql server vnet-rule',
                            virtual_network_rules_operations,
                            client_factory=get_sql_virtual_network_rules_operations) as g:

        g.command('create', 'create_or_update',
                  validator=validate_subnet)
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')
        g.command('delete', 'delete')
        g.generic_update_command('update')

    server_connection_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServerConnectionPoliciesOperations.{}',
        client_factory=get_sql_server_connection_policies_operations)

    with self.command_group('sql server conn-policy',
                            server_connection_policies_operations,
                            client_factory=get_sql_server_connection_policies_operations) as c:

        c.show_command('show', 'get')
        c.generic_update_command('update')

    server_dns_aliases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ServerDnsAliasesOperations.{}',
        client_factory=get_sql_server_dns_aliases_operations)

    with self.command_group('sql server dns-alias',
                            server_dns_aliases_operations,
                            client_factory=get_sql_server_dns_aliases_operations) as c:

        c.show_command('show', 'get')
        c.command('list', 'list_by_server')
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.custom_command('set', 'server_dns_alias_set')

    ###############################################
    #                sql managed instance         #
    ###############################################

    managed_instance_operations_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstanceOperations.{}',
        client_factory=get_sql_managed_instance_operations_operations)

    with self.command_group('sql mi op', managed_instance_operations_operations) as g:

        g.command('list', 'list_by_managed_instance')
        g.command('show', 'get')
        g.command('cancel', 'cancel')

    managed_instances_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstancesOperations.{}',
        client_factory=get_sql_managed_instances_operations)

    with self.command_group('sql mi',
                            managed_instances_operations,
                            client_factory=get_sql_managed_instances_operations) as g:

        g.custom_command('create', 'managed_instance_create', supports_no_wait=True)
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'managed_instance_list')
        g.generic_update_command('update', custom_func_name='managed_instance_update', supports_no_wait=True)
        g.command('failover', 'failover', supports_no_wait=True)

    managed_instance_keys_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstanceKeysOperations.{}',
        client_factory=get_sql_managed_instance_keys_operations)

    with self.command_group('sql mi key',
                            managed_instance_keys_operations,
                            client_factory=get_sql_managed_instance_keys_operations) as g:

        g.custom_command('create', 'managed_instance_key_create')
        g.custom_command('delete', 'managed_instance_key_delete')
        g.custom_show_command('show', 'managed_instance_key_get')
        g.command('list', 'list_by_instance')

    managed_instance_encryption_protectors_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstanceEncryptionProtectorsOperations.{}',
        client_factory=get_sql_managed_instance_encryption_protectors_operations)

    with self.command_group('sql mi tde-key',
                            managed_instance_encryption_protectors_operations,
                            client_factory=get_sql_managed_instance_encryption_protectors_operations) as g:

        g.show_command('show', 'get')
        g.custom_command('set', 'managed_instance_encryption_protector_update')

    managed_instance_aadadmin_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstanceAdministratorsOperations.{}',
        client_factory=get_sql_managed_instance_azure_ad_administrators_operations)

    with self.command_group('sql mi ad-admin',
                            managed_instance_aadadmin_operations,
                            client_factory=get_sql_managed_instance_azure_ad_administrators_operations) as g:

        g.custom_command('create', 'mi_ad_admin_set')
        g.command('list', 'list_by_instance')
        g.custom_command('delete', 'mi_ad_admin_delete')
        g.custom_command('update', 'mi_ad_admin_set')

    ###############################################
    #                sql managed db               #
    ###############################################

    managed_databases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedDatabasesOperations.{}',
        client_factory=get_sql_managed_databases_operations)

    with self.command_group('sql midb',
                            managed_databases_operations,
                            client_factory=get_sql_managed_databases_operations) as g:

        g.custom_command('create', 'managed_db_create', supports_no_wait=True)
        g.custom_command('restore', 'managed_db_restore', supports_no_wait=True)
        g.show_command('show', 'get')
        g.command('list', 'list_by_instance')
        g.command('delete', 'delete', confirmation=True, supports_no_wait=True)

    managed_backup_short_term_retention_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedBackupShortTermRetentionPoliciesOperations.{}',
        client_factory=get_sql_managed_backup_short_term_retention_policies_operations)

    with self.command_group('sql midb short-term-retention-policy',
                            managed_backup_short_term_retention_policies_operations,
                            client_factory=get_sql_managed_backup_short_term_retention_policies_operations) as g:

        g.custom_command(
            'set',
            'update_short_term_retention_mi',
            supports_no_wait=True,
            is_preview=True)
        g.custom_command('show', 'get_short_term_retention_mi', is_preview=True)

    managed_database_long_term_retention_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#ManagedInstanceLongTermRetentionPoliciesOperations.{}',
        client_factory=get_sql_managed_database_long_term_retention_policies_operations)

    with self.command_group('sql midb ltr-policy',
                            managed_database_long_term_retention_policies_operations,
                            client_factory=get_sql_managed_database_long_term_retention_policies_operations) as g:

        g.custom_command('set', 'update_long_term_retention_mi', is_preview=True)
        g.show_command('show', 'get', is_preview=True)

    managed_database_long_term_retention_backups_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#LongTermRetentionManagedInstanceBackupsOperations.{}',
        client_factory=get_sql_managed_database_long_term_retention_backups_operations)

    with self.command_group('sql midb ltr-backup',
                            managed_database_long_term_retention_backups_operations,
                            client_factory=get_sql_managed_database_long_term_retention_backups_operations) as g:
        g.custom_command('show', 'get_long_term_retention_mi_backup', is_preview=True)
        g.custom_command(
            'list',
            'list_long_term_retention_mi_backups', is_preview=True)
        g.custom_command('delete', 'delete_long_term_retention_mi_backup', confirmation=True, is_preview=True)

    with self.command_group('sql midb ltr-backup',
                            managed_databases_operations,
                            client_factory=get_sql_managed_databases_operations) as g:
        g.custom_command(
            'restore',
            'restore_long_term_retention_mi_backup',
            supports_no_wait=True,
            is_preview=True)
        g.wait_command('wait')

    ###############################################
    #                sql virtual cluster         #
    ###############################################

    virtual_clusters_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#VirtualClustersOperations.{}',
        client_factory=get_sql_virtual_clusters_operations)

    with self.command_group('sql virtual-cluster',
                            virtual_clusters_operations,
                            client_factory=get_sql_virtual_clusters_operations) as g:

        g.command('delete', 'delete', supports_no_wait=True)
        g.show_command('show', 'get')
        g.custom_command('list', 'virtual_cluster_list')

    ###############################################
    #             sql instance failover group     #
    ###############################################

    instance_failover_groups_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations#InstanceFailoverGroupsOperations.{}',
        client_factory=get_sql_instance_failover_groups_operations)
    with self.command_group('sql instance-failover-group', instance_failover_groups_operations, client_factory=get_sql_instance_failover_groups_operations) as g:
        g.command('show', 'get')
        g.custom_command('create', 'instance_failover_group_create')
        g.generic_update_command('update', custom_func_name='instance_failover_group_update')
        g.command('delete', 'delete')
        g.custom_command('set-primary', 'instance_failover_group_failover')
