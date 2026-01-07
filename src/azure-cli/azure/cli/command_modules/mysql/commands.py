# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.command_modules.mysql._client_factory import (
    cf_mysql_advanced_threat_protection,
    cf_mysql_flexible_servers,
    cf_mysql_flexible_firewall_rules,
    cf_mysql_flexible_config,
    cf_mysql_flexible_db,
    cf_mysql_flexible_replica,
    cf_mysql_flexible_location_capabilities,
    cf_mysql_flexible_log,
    cf_mysql_flexible_backup,
    cf_mysql_flexible_backups,
    cf_mysql_flexible_adadmin,
    cf_mysql_flexible_export,
    cf_mysql_flexible_maintenances)
from ._transformers import (
    table_transform_output,
    table_transform_output_list_servers,
    mysql_table_transform_output_list_skus,
    table_transform_output_parameters,
    transform_backup,
    transform_backups_list)


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_command_table(self, _):
    # Flexible server SDKs:
    mysql_flexible_servers_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#ServersOperations.{}',
        client_factory=cf_mysql_flexible_servers
    )

    mysql_advanced_threat_protection_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#AdvancedThreatProtectionSettingsOperations.{}',
        client_factory=cf_mysql_advanced_threat_protection
    )

    mysql_flexible_firewall_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#FirewallRulesOperations.{}',
        client_factory=cf_mysql_flexible_firewall_rules
    )

    mysql_flexible_config_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#ConfigurationsOperations.{}',
        client_factory=cf_mysql_flexible_config
    )

    mysql_flexible_db_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#DatabasesOperations.{}',
        client_factory=cf_mysql_flexible_db
    )

    mysql_flexible_replica_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#ReplicasOperations.{}',
        client_factory=cf_mysql_flexible_replica
    )

    mysql_flexible_location_capabilities_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#LocationBasedCapabilitiesOperations.{}',
        client_factory=cf_mysql_flexible_location_capabilities
    )

    mysql_flexible_log_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#LogFilesOperations.{}',
        client_factory=cf_mysql_flexible_log
    )

    mysql_flexible_long_running_backup_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#LongRunningBackupOperations.{}',
        client_factory=cf_mysql_flexible_backup
    )

    mysql_flexible_long_running_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#LongRunningBackupsOperations.{}',
        client_factory=cf_mysql_flexible_backups
    )

    mysql_flexible_export_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#BackupAndExportOperations.{}',
        client_factory=cf_mysql_flexible_export
    )

    mysql_flexible_adadmin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#AzureADAdministratorsOperations.{}',
        client_factory=cf_mysql_flexible_adadmin
    )

    mysql_flexible_maintenance_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.mysqlflexibleservers.operations#MaintenancesOperations.{}',
        client_factory=cf_mysql_flexible_maintenances
    )

    # MERU COMMANDS
    mysql_custom = CliCommandType(operations_tmpl='azure.cli.command_modules.mysql.custom#{}')

    # Advanced Threat Protection
    with self.command_group('mysql flexible-server advanced-threat-protection-setting',
                            mysql_advanced_threat_protection_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_advanced_threat_protection) as g:
        g.custom_command('update', 'flexible_server_advanced_threat_protection_update')
        g.custom_show_command('show', 'flexible_server_advanced_threat_protection_show')

    with self.command_group('mysql flexible-server', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('create', 'flexible_server_create', table_transformer=table_transform_output)
        g.custom_command('restore', 'flexible_server_restore', supports_no_wait=True)
        g.custom_command('geo-restore', 'flexible_server_georestore', supports_no_wait=True)
        g.command('start', 'begin_start', supports_no_wait=True)
        g.custom_command('stop', 'flexible_server_stop', custom_command_type=mysql_custom, supports_no_wait=True)
        g.custom_command('delete', 'server_delete_func')
        g.show_command('show', 'get')
        g.custom_command('list', 'server_list_custom_func', custom_command_type=mysql_custom, table_transformer=table_transform_output_list_servers)
        g.generic_update_command('update',
                                 getter_name='flexible_server_update_get', getter_type=mysql_custom,
                                 setter_name='flexible_server_update_set', setter_type=mysql_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='flexible_server_update_custom_func')
        g.custom_command('upgrade', 'flexible_server_version_upgrade', custom_command_type=mysql_custom)
        g.custom_wait_command('wait', 'flexible_server_mysql_get')
        g.custom_command('restart', 'flexible_server_restart')
        g.custom_command('detach-vnet', 'flexible_server_detach_vnet')

    with self.command_group('mysql flexible-server import', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('create', 'flexible_server_import_create', table_transformer=table_transform_output)
        g.custom_command('stop-replication', 'flexible_server_import_replica_stop', confirmation=True)

    with self.command_group('mysql flexible-server firewall-rule', mysql_flexible_firewall_rule_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_firewall_rules) as g:
        g.custom_command('create', 'firewall_rule_create_func', custom_command_type=mysql_custom)
        g.custom_command('delete', 'firewall_rule_delete_func', custom_command_type=mysql_custom)
        g.custom_show_command('show', 'firewall_rule_get_func', custom_command_type=mysql_custom)
        g.custom_command('list', 'firewall_rule_list_func', custom_command_type=mysql_custom)
        g.generic_update_command('update',
                                 getter_name='flexible_firewall_rule_custom_getter', getter_type=mysql_custom,
                                 setter_name='flexible_firewall_rule_custom_setter', setter_type=mysql_custom,
                                 setter_arg_name='parameters',
                                 custom_func_name='flexible_firewall_rule_update_custom_func',
                                 custom_func_type=mysql_custom)

    with self.command_group('mysql flexible-server parameter', mysql_flexible_config_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_config,
                            table_transformer=table_transform_output_parameters) as g:
        g.custom_command('set', 'flexible_parameter_update')
        g.custom_command('set-batch', 'flexible_parameter_update_batch')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    with self.command_group('mysql flexible-server db', mysql_flexible_db_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_db) as g:
        g.custom_command('create', 'database_create_func', custom_command_type=mysql_custom)
        g.custom_command('delete', 'database_delete_func')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    with self.command_group('mysql flexible-server', mysql_flexible_location_capabilities_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_location_capabilities) as g:
        g.custom_command('list-skus', 'flexible_list_skus', table_transformer=mysql_table_transform_output_list_skus)
        g.custom_command('show-connection-string', 'flexible_server_connection_string')

    with self.command_group('mysql flexible-server replica', mysql_flexible_replica_sdk) as g:
        g.command('list', 'list_by_server')

    with self.command_group('mysql flexible-server replica', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('create', 'flexible_replica_create', supports_no_wait=True)
        g.custom_command('stop-replication', 'flexible_replica_stop', confirmation=True)

    with self.command_group('mysql flexible-server deploy', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('setup', 'github_actions_setup')
        g.custom_command('run', 'github_actions_run')

    with self.command_group('mysql flexible-server server-logs', mysql_flexible_log_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_log) as g:
        g.custom_command('list', 'flexible_server_log_list')
        g.custom_command('download', 'flexible_server_log_download')

    with self.command_group('mysql flexible-server backup', mysql_flexible_long_running_backup_sdk,
                            client_factory=cf_mysql_flexible_backup) as g:
        g.command('create', 'begin_create')
        g.command('delete', 'begin_delete')

    with self.command_group('mysql flexible-server backup', mysql_flexible_long_running_backups_sdk,
                            client_factory=cf_mysql_flexible_backups) as g:
        g.command('list', 'list', transform=transform_backups_list)
        g.show_command('show', 'get', transform=transform_backup)

    with self.command_group('mysql flexible-server export', mysql_flexible_export_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_export,
                            is_preview=True,
                            deprecate_info=self.deprecate(hide=True)) as g:
        g.custom_command('create', 'flexible_server_export_create')

    with self.command_group('mysql flexible-server identity', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('assign', 'flexible_server_identity_assign', supports_no_wait=True)
        g.custom_command('remove', 'flexible_server_identity_remove', supports_no_wait=True, confirmation=True)
        g.custom_show_command('show', 'flexible_server_identity_show')
        g.custom_command('list', 'flexible_server_identity_list')

    with self.command_group('mysql flexible-server ad-admin', mysql_flexible_adadmin_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_adadmin) as g:
        g.custom_command('create', 'flexible_server_ad_admin_set', supports_no_wait=True)
        g.custom_command('delete', 'flexible_server_ad_admin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('list', 'flexible_server_ad_admin_list')
        g.custom_show_command('show', 'flexible_server_ad_admin_show')
        g.custom_wait_command('wait', 'flexible_server_ad_admin_show')

    with self.command_group('mysql flexible-server gtid', mysql_flexible_servers_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_servers) as g:
        g.custom_command('reset', 'flexible_gtid_reset', supports_no_wait=True)

    with self.command_group('mysql flexible-server maintenance', mysql_flexible_maintenance_sdk,
                            custom_command_type=mysql_custom,
                            client_factory=cf_mysql_flexible_maintenances) as g:
        g.custom_command('reschedule', 'flexible_server_maintenance_reschedule')
        g.custom_command('list', 'flexible_server_maintenance_list')
        g.custom_show_command('show', 'flexible_server_maintenance_show')
