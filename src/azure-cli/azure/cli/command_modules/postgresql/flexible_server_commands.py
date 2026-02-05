# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.postgresql.validators import validate_private_endpoint_connection_id
from azure.cli.core.commands import CliCommandType

from azure.cli.command_modules.postgresql._client_factory import (
    cf_postgres_flexible_servers,
    cf_postgres_flexible_firewall_rules,
    cf_postgres_flexible_config,
    cf_postgres_flexible_db,
    cf_postgres_flexible_location_capabilities,
    cf_postgres_flexible_backups,
    cf_postgres_flexible_ltr_backups,
    cf_postgres_flexible_replica,
    cf_postgres_flexible_admin,
    cf_postgres_flexible_migrations,
    cf_postgres_flexible_private_endpoint_connections,
    cf_postgres_flexible_private_link_resources,
    cf_postgres_flexible_virtual_endpoints,
    cf_postgres_flexible_server_threat_protection_settings,
    cf_postgres_flexible_advanced_threat_protection_settings,
    cf_postgres_flexible_server_log_files)

from ._transformers import (
    table_transform_output,
    table_transform_output_list_servers,
    postgres_table_transform_output_list_skus,
    table_transform_output_parameters,
    transform_backup,
    transform_backups_list)

# from .transformers import table_transform_connection_string
# from .validators import db_up_namespace_processor


# pylint: disable=too-many-locals, too-many-statements, line-too-long
def load_flexibleserver_command_table(self, _):
    # Flexible server SDKs:
    postgres_flexible_servers_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#ServersOperations.{}',
        client_factory=cf_postgres_flexible_servers
    )

    postgres_flexible_firewall_rule_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#FirewallRulesOperations.{}',
        client_factory=cf_postgres_flexible_firewall_rules
    )

    postgres_flexible_config_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#ConfigurationsOperations.{}',
        client_factory=cf_postgres_flexible_config
    )

    postgres_flexible_db_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#DatabasesOperations.{}',
        client_factory=cf_postgres_flexible_db
    )

    postgres_flexible_location_capabilities_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#CapabilitiesByLocationOperations.{}',
        client_factory=cf_postgres_flexible_location_capabilities
    )

    postgres_flexible_backups_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#BackupsAutomaticAndOnDemandOperations.{}',
        client_factory=cf_postgres_flexible_backups
    )

    postgres_flexible_ltr_backup_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#BackupsLongTermRetentionOperations.{}',
        client_factory=cf_postgres_flexible_ltr_backups
    )

    postgres_flexible_replica_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#ReplicasOperations.{}',
        client_factory=cf_postgres_flexible_replica
    )

    postgres_flexible_admin_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#AdministratorsMicrosoftEntraOperations.{}',
        client_factory=cf_postgres_flexible_admin
    )

    postgres_flexible_migrations_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#MigrationsOperations.{}',
        client_factory=cf_postgres_flexible_migrations
    )

    postgres_flexible_virtual_endpoints_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#VirtualEndpointsOperations.{}',
        client_factory=cf_postgres_flexible_virtual_endpoints
    )

    postgres_flexible_server_threat_protection_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#ServerThreatProtectionSettingsOperations.{}',
        client_factory=cf_postgres_flexible_server_threat_protection_settings
    )

    postgres_flexible_advanced_threat_protection_settings_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#AdvancedThreatProtectionSettingsOperations.{}',
        client_factory=cf_postgres_flexible_advanced_threat_protection_settings
    )

    postgres_flexible_server_log_files_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#CapturedLogsOperations.{}',
        client_factory=cf_postgres_flexible_server_log_files
    )

    postgres_flexible_server_private_endpoint_connections_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#PrivateEndpointConnectionsOperations.{}',
        client_factory=cf_postgres_flexible_private_endpoint_connections
    )

    postgres_flexible_server_private_link_resources_sdk = CliCommandType(
        operations_tmpl='azure.mgmt.postgresqlflexibleservers.operations#PrivateLinkResourcesOperations.{}',
        client_factory=cf_postgres_flexible_private_link_resources
    )

    # MERU COMMANDS
    flexible_server_custom_common = CliCommandType(
        operations_tmpl='azure.cli.command_modules.postgresql.flexible_server_custom_common#{}')
    flexible_servers_custom_postgres = CliCommandType(
        operations_tmpl='azure.cli.command_modules.postgresql.flexible_server_custom_postgres#{}')

    # Postgres commands
    with self.command_group('postgres flexible-server', postgres_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_servers) as g:
        g.custom_command('create', 'flexible_server_create', table_transformer=table_transform_output)
        g.custom_command('restore', 'flexible_server_restore', supports_no_wait=True)
        g.custom_command('geo-restore', 'flexible_server_georestore', supports_no_wait=True)
        g.custom_command('revive-dropped', 'flexible_server_revivedropped', supports_no_wait=True)
        g.command('start', 'begin_start', supports_no_wait=True)
        g.custom_command('stop', 'flexible_server_stop', custom_command_type=flexible_server_custom_common, supports_no_wait=True)
        g.custom_command('delete', 'flexible_server_delete')
        g.show_command('show', 'get')
        g.custom_command('list', 'server_list_custom_func', custom_command_type=flexible_server_custom_common, table_transformer=table_transform_output_list_servers)
        g.generic_update_command('update',
                                 getter_name='flexible_server_update_get', getter_type=flexible_server_custom_common,
                                 setter_name='flexible_server_update_set', setter_type=flexible_server_custom_common,
                                 setter_arg_name='parameters',
                                 custom_func_name='flexible_server_update_custom_func')
        g.custom_command('upgrade', 'flexible_server_version_upgrade', custom_command_type=flexible_server_custom_common)
        g.custom_wait_command('wait', 'flexible_server_postgresql_get')
        g.custom_command('restart', 'flexible_server_restart')

    with self.command_group('postgres flexible-server firewall-rule', postgres_flexible_firewall_rule_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_firewall_rules) as g:
        g.custom_command('create', 'firewall_rule_create_func', custom_command_type=flexible_server_custom_common)
        g.custom_command('delete', 'firewall_rule_delete_func', custom_command_type=flexible_server_custom_common)
        g.custom_show_command('show', 'firewall_rule_get_func', custom_command_type=flexible_server_custom_common)
        g.custom_command('list', 'firewall_rule_list_func', custom_command_type=flexible_server_custom_common)
        g.generic_update_command('update',
                                 getter_name='flexible_firewall_rule_custom_getter', getter_type=flexible_server_custom_common,
                                 setter_name='flexible_firewall_rule_custom_setter', setter_type=flexible_server_custom_common,
                                 setter_arg_name='parameters',
                                 custom_func_name='flexible_firewall_rule_update_custom_func',
                                 custom_func_type=flexible_server_custom_common)

    with self.command_group('postgres flexible-server migration', postgres_flexible_migrations_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_migrations) as g:
        g.custom_command('create', 'migration_create_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_show_command('show', 'migration_show_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list', 'migration_list_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('update', 'migration_update_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('check-name-availability', 'migration_check_name_availability', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server virtual-endpoint', postgres_flexible_virtual_endpoints_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_virtual_endpoints) as g:
        g.custom_command('create', 'virtual_endpoint_create_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('delete', 'virtual_endpoint_delete_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_show_command('show', 'virtual_endpoint_show_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list', 'virtual_endpoint_list_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('update', 'virtual_endpoint_update_func', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server parameter', postgres_flexible_config_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_config, table_transformer=table_transform_output_parameters) as g:
        g.custom_command('set', 'flexible_parameter_update')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    with self.command_group('postgres flexible-server', postgres_flexible_location_capabilities_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_location_capabilities) as g:
        g.custom_command('list-skus', 'flexible_list_skus', table_transformer=postgres_table_transform_output_list_skus)
        g.custom_command('show-connection-string', 'flexible_server_connection_string')

    with self.command_group('postgres flexible-server db', postgres_flexible_db_sdk,
                            custom_command_type=flexible_server_custom_common,
                            client_factory=cf_postgres_flexible_db) as g:
        g.custom_command('create', 'database_create_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('delete', 'database_delete_func')
        g.show_command('show', 'get')
        g.command('list', 'list_by_server')

    with self.command_group('postgres flexible-server deploy', postgres_flexible_servers_sdk,
                            custom_command_type=flexible_server_custom_common,
                            client_factory=cf_postgres_flexible_servers) as g:
        g.custom_command('setup', 'github_actions_setup')
        g.custom_command('run', 'github_actions_run')

    with self.command_group('postgres flexible-server backup', postgres_flexible_backups_sdk,
                            client_factory=cf_postgres_flexible_backups) as g:
        g.command('list', 'list_by_server', transform=transform_backups_list)
        g.show_command('show', 'get', transform=transform_backup)
        g.custom_command('create', 'backup_create_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('delete', 'backup_delete_func', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server long-term-retention', postgres_flexible_ltr_backup_sdk,
                            client_factory=cf_postgres_flexible_ltr_backups) as g:
        g.command('list', 'list_by_server', transform=transform_backups_list)
        g.show_command('show', 'get', transform=transform_backup)
        g.custom_command('pre-check', 'ltr_precheck_func', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('start', 'ltr_start_func', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server replica', postgres_flexible_replica_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_replica) as g:
        g.custom_command('list', 'flexible_replica_list_by_server')

    with self.command_group('postgres flexible-server replica', postgres_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_servers) as g:
        g.custom_command('create', 'flexible_replica_create', supports_no_wait=True)
        g.custom_command('promote', 'flexible_replica_promote', confirmation=True)

    with self.command_group('postgres flexible-server identity', postgres_flexible_servers_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_servers) as g:
        g.custom_command('update', 'flexible_server_identity_update', supports_no_wait=True)
        g.custom_command('assign', 'flexible_server_identity_assign', supports_no_wait=True)
        g.custom_command('remove', 'flexible_server_identity_remove', supports_no_wait=True, confirmation=True)
        g.custom_show_command('show', 'flexible_server_identity_show')
        g.custom_command('list', 'flexible_server_identity_list')

    with self.command_group('postgres flexible-server microsoft-entra-admin', postgres_flexible_admin_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_admin) as g:
        g.custom_command('create', 'flexible_server_microsoft_entra_admin_set', supports_no_wait=True)
        g.custom_command('delete', 'flexible_server_microsoft_entra_admin_delete', supports_no_wait=True, confirmation=True)
        g.custom_command('list', 'flexible_server_microsoft_entra_admin_list')
        g.custom_show_command('show', 'flexible_server_microsoft_entra_admin_show')
        g.custom_wait_command('wait', 'flexible_server_microsoft_entra_admin_show')

    with self.command_group('postgres flexible-server advanced-threat-protection-setting', postgres_flexible_advanced_threat_protection_settings_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_advanced_threat_protection_settings) as g:
        g.custom_show_command('show', 'flexible_server_threat_protection_get', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server advanced-threat-protection-setting', postgres_flexible_server_threat_protection_settings_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_server_threat_protection_settings) as g:
        g.custom_command('update', 'flexible_server_threat_protection_update', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server server-logs', postgres_flexible_server_log_files_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_server_log_files) as g:
        g.custom_command('list', 'flexible_server_list_log_files_with_filter', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('download', 'flexible_server_download_log_files', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server private-endpoint-connection', postgres_flexible_server_private_endpoint_connections_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_private_endpoint_connections) as g:
        g.command('list', 'list_by_server')
        g.show_command('show', 'get', validator=validate_private_endpoint_connection_id)
        g.command('delete', 'begin_delete', validator=validate_private_endpoint_connection_id)
        g.custom_command('approve', 'flexible_server_approve_private_endpoint_connection', custom_command_type=flexible_servers_custom_postgres,
                         validator=validate_private_endpoint_connection_id)
        g.custom_command('reject', 'flexible_server_reject_private_endpoint_connection', custom_command_type=flexible_servers_custom_postgres,
                         validator=validate_private_endpoint_connection_id)

    with self.command_group('postgres flexible-server private-link-resource', postgres_flexible_server_private_link_resources_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_private_link_resources) as g:
        g.command('list', 'list_by_server')
        g.custom_show_command('show', 'flexible_server_private_link_resource_get', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server fabric-mirroring', postgres_flexible_config_sdk,
                            custom_command_type=flexible_servers_custom_postgres,
                            client_factory=cf_postgres_flexible_config) as g:
        g.custom_command('start', 'flexible_server_fabric_mirroring_start')
        g.custom_command('stop', 'flexible_server_fabric_mirroring_stop')
        g.custom_command('update-databases', 'flexible_server_fabric_mirroring_update_databases')

    with self.command_group('postgres flexible-server index-tuning', postgres_flexible_config_sdk,
                            client_factory=cf_postgres_flexible_config) as g:
        g.custom_command('update', 'index_tuning_update', custom_command_type=flexible_servers_custom_postgres)
        g.custom_show_command('show', 'index_tuning_show', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list-settings', 'index_tuning_settings_list', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('show-settings', 'index_tuning_settings_get', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('set-settings', 'index_tuning_settings_set', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list-recommendations', 'index_tuning_recommendations_list', custom_command_type=flexible_servers_custom_postgres)

    with self.command_group('postgres flexible-server autonomous-tuning', postgres_flexible_config_sdk,
                            client_factory=cf_postgres_flexible_config) as g:
        g.custom_command('update', 'autonomous_tuning_update', custom_command_type=flexible_servers_custom_postgres)
        g.custom_show_command('show', 'autonomous_tuning_show', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list-settings', 'autonomous_tuning_settings_list', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('show-settings', 'autonomous_tuning_settings_get', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('set-settings', 'autonomous_tuning_settings_set', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list-table-recommendations', 'autonomous_tuning_table_recommendations_list', custom_command_type=flexible_servers_custom_postgres)
        g.custom_command('list-index-recommendations', 'autonomous_tuning_index_recommendations_list', custom_command_type=flexible_servers_custom_postgres)
