# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType

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
    get_sql_elastic_pool_operations_operations,
    get_sql_encryption_protectors_operations,
    get_sql_firewall_rules_operations,
    get_sql_replication_links_operations,
    get_sql_restorable_dropped_databases_operations,
    get_sql_server_connection_policies_operations,
    get_sql_server_dns_aliases_operations,
    get_sql_server_keys_operations,
    get_sql_servers_operations,
    get_sql_server_usages_operations,
    get_sql_subscription_usages_operations,
    get_sql_virtual_network_rules_operations,
)
from ._validators import validate_subnet


# pylint: disable=line-too-long,too-many-statements
def load_command_table(self, _):
    ###############################################
    #                sql capabilities             #
    ###############################################
    capabilities_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.capabilities_operations#CapabilitiesOperations.{}',
        client_factory=get_sql_capabilities_operations)

    with self.command_group('sql db', capabilities_operations, client_factory=get_sql_capabilities_operations) as g:
        g.custom_command('list-editions', 'db_list_capabilities')

    with self.command_group('sql elastic-pool', capabilities_operations, client_factory=get_sql_capabilities_operations) as g:
        g.custom_command('list-editions', 'elastic_pool_list_capabilities')

    ###############################################
    #                sql list-usages              #
    ###############################################
    subscription_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.subscription_usages_operations#SubscriptionUsagesOperations.{}',
        client_factory=get_sql_subscription_usages_operations)

    with self.command_group('sql', subscription_usages_operations, client_factory=get_sql_subscription_usages_operations) as g:
        g.command('list-usages', 'list_by_location')
        g.command('show-usage', 'get')

    ###############################################
    #                sql db                       #
    ###############################################
    with self.command_group('sql db') as g:
        g.custom_command('show-connection-string', 'db_show_conn_str')

    database_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.databases_operations#DatabasesOperations.{}',
        client_factory=get_sql_databases_operations)
    with self.command_group('sql db', database_operations, client_factory=get_sql_databases_operations) as g:
        g.custom_command('create', 'db_create', supports_no_wait=True)
        g.custom_command('copy', 'db_copy', supports_no_wait=True)
        g.custom_command('restore', 'db_restore', supports_no_wait=True)
        g.custom_command('rename', 'db_rename')
        g.command('show', 'get')
        g.custom_command('list', 'db_list')
        g.command('delete', 'delete', confirmation=True)
        g.generic_update_command('update', custom_func_name='db_update', supports_no_wait=True)
        g.custom_command('import', 'db_import')
        g.custom_command('export', 'db_export')

    with self.command_group('sql db replica', database_operations, client_factory=get_sql_databases_operations) as g:
        g.custom_command('create', 'db_create_replica', supports_no_wait=True)

    with self.command_group('sql dw', database_operations, client_factory=get_sql_databases_operations) as g:
        g.custom_command('create', 'dw_create', supports_no_wait=True)
        g.command('show', 'get')
        g.custom_command('list', 'dw_list')
        g.command('delete', 'delete', confirmation=True)
        g.command('pause', 'pause')
        g.command('resume', 'resume')
        g.generic_update_command('update', custom_func_name='dw_update', supports_no_wait=True)

    database_operations_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.database_operations#DatabaseOperations.{}',
        client_factory=get_sql_database_operations_operations)

    with self.command_group('sql db op', database_operations_operations) as g:
        g.command('list', 'list_by_database')
        g.command('cancel', 'cancel')

    transparent_data_encryptions_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.transparent_data_encryptions_operations#TransparentDataEncryptionsOperations.{}',
        client_factory=get_sql_database_transparent_data_encryptions_operations)
    with self.command_group('sql db tde', transparent_data_encryptions_operations) as g:
        g.command('set', 'create_or_update')
        g.command('show', 'get')

    transparent_data_encryption_activities_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.transparent_data_encryption_activities_operations#TransparentDataEncryptionActivitiesOperations.{}',
        client_factory=get_sql_database_transparent_data_encryption_activities_operations)
    with self.command_group('sql db tde', transparent_data_encryption_activities_operations) as g:
        g.command('list-activity', 'list_by_configuration')

    replication_links_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.replication_links_operations#ReplicationLinksOperations.{}',
        client_factory=get_sql_replication_links_operations)
    with self.command_group('sql db replica', replication_links_operations, client_factory=get_sql_replication_links_operations) as g:
        g.command('list-links', 'list_by_database')
        g.custom_command('delete-link', 'db_delete_replica_link', confirmation=True)
        g.custom_command('set-primary', 'db_failover')

    restorable_dropped_databases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.restorable_dropped_databases_operations#RestorableDroppedDatabasesOperations.{}',
        client_factory=get_sql_restorable_dropped_databases_operations)
    with self.command_group('sql db', restorable_dropped_databases_operations) as g:
        g.command('list-deleted', 'list_by_server')

    database_blob_auditing_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.database_blob_auditing_policies_operations#DatabaseBlobAuditingPoliciesOperations.{}',
        client_factory=get_sql_database_blob_auditing_policies_operations)
    with self.command_group('sql db audit-policy', database_blob_auditing_policies_operations, client_factory=get_sql_database_blob_auditing_policies_operations) as g:
        g.command('show', 'get')
        g.generic_update_command('update', custom_func_name='db_audit_policy_update')

    database_threat_detection_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.database_threat_detection_policies_operations#DatabaseThreatDetectionPoliciesOperations.{}',
        client_factory=get_sql_database_threat_detection_policies_operations)
    with self.command_group('sql db threat-policy', database_threat_detection_policies_operations, client_factory=get_sql_database_threat_detection_policies_operations) as g:
        g.command('show', 'get')
        g.generic_update_command('update', custom_func_name='db_threat_detection_policy_update')

    database_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.database_usages_operations#DatabaseUsagesOperations.{}',
        client_factory=get_sql_database_usages_operations)
    with self.command_group('sql db', database_usages_operations) as g:
        g.command('list-usages', 'list_by_database')

    ###############################################
    #                sql elastic-pool             #
    ###############################################
    elastic_pools_ops = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.elastic_pools_operations#ElasticPoolsOperations.{}',
        client_factory=get_sql_elastic_pools_operations)
    with self.command_group('sql elastic-pool', elastic_pools_ops, client_factory=get_sql_elastic_pools_operations) as g:
        g.custom_command('create', 'elastic_pool_create')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list_by_server')
        g.generic_update_command('update', custom_func_name='elastic_pool_update')

    with self.command_group('sql elastic-pool', database_operations) as g:
        g.command('list-dbs', 'list_by_elastic_pool')

    elastic_pool_operations_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.elastic_pool_operations#ElasticPoolOperations.{}',
        client_factory=get_sql_elastic_pool_operations_operations)
    with self.command_group('sql elastic-pool op', elastic_pool_operations_operations, client_factory=get_sql_elastic_pool_operations_operations) as g:
        g.command('list', 'list_by_elastic_pool')
        g.command('cancel', 'cancel')

    ###############################################
    #                sql server                   #
    ###############################################
    servers_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.servers_operations#ServersOperations.{}',
        client_factory=get_sql_servers_operations)
    with self.command_group('sql server', servers_operations, client_factory=get_sql_servers_operations) as g:
        g.custom_command('create', 'server_create')
        g.command('delete', 'delete', confirmation=True)
        g.command('show', 'get')
        g.custom_command('list', 'server_list')
        g.generic_update_command('update', custom_func_name='server_update')

    server_usages_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.server_usages_operations#ServerUsagesOperations.{}',
        client_factory=get_sql_server_usages_operations)
    with self.command_group('sql server', server_usages_operations) as g:
        g.command('list-usages', 'list_by_server')

    firewall_rules_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.firewall_rules_operations#FirewallRulesOperations.{}',
        client_factory=get_sql_firewall_rules_operations)
    with self.command_group('sql server firewall-rule', firewall_rules_operations, client_factory=get_sql_firewall_rules_operations) as g:
        g.command('create', 'create_or_update')
        g.custom_command('update', 'firewall_rule_update')
        g.command('delete', 'delete')
        g.command('show', 'get')
        g.command('list', 'list_by_server')

    aadadmin_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.server_azure_ad_administrators_operations#ServerAzureADAdministratorsOperations.{}',
        client_factory=get_sql_server_azure_ad_administrators_operations)
    with self.command_group('sql server ad-admin', aadadmin_operations, client_factory=get_sql_server_azure_ad_administrators_operations) as g:
        g.custom_command('create', 'server_ad_admin_set')
        g.command('list', 'list_by_server')
        g.command('delete', 'delete')
        g.generic_update_command('update', custom_func_name='server_ad_admin_update',
                                 setter_arg_name='properties')

    server_keys_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.server_keys_operations#ServerKeysOperations.{}',
        client_factory=get_sql_server_keys_operations)
    with self.command_group('sql server key', server_keys_operations, client_factory=get_sql_server_keys_operations) as g:
        g.custom_command('create', 'server_key_create')
        g.custom_command('delete', 'server_key_delete')
        g.custom_command('show', 'server_key_get')
        g.command('list', 'list_by_server')

    encryption_protectors_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.encryption_protectors_operations#EncryptionProtectorsOperations.{}',
        client_factory=get_sql_encryption_protectors_operations)
    with self.command_group('sql server tde-key', encryption_protectors_operations, client_factory=get_sql_encryption_protectors_operations) as g:
        g.command('show', 'get')
        g.custom_command('set', 'encryption_protector_update')

    virtual_network_rules_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.virtual_network_rules_operations#VirtualNetworkRulesOperations.{}',
        client_factory=get_sql_virtual_network_rules_operations)
    with self.command_group('sql server vnet-rule', virtual_network_rules_operations, client_factory=get_sql_virtual_network_rules_operations) as g:
        g.command('create', 'create_or_update', validator=validate_subnet)
        g.command('show', 'get')
        g.command('list', 'list_by_server')
        g.command('delete', 'delete')
        g.generic_update_command('update')

    server_connection_policies_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.server_connection_policies_operations#ServerConnectionPoliciesOperations.{}',
        client_factory=get_sql_server_connection_policies_operations)
    with self.command_group('sql server conn-policy', server_connection_policies_operations, client_factory=get_sql_server_connection_policies_operations) as c:
        c.command('show', 'get')
        c.generic_update_command('update')

    server_dns_aliases_operations = CliCommandType(
        operations_tmpl='azure.mgmt.sql.operations.server_dns_aliases_operations#ServerDnsAliasesOperations.{}',
        client_factory=get_sql_server_dns_aliases_operations)
    with self.command_group('sql server dns-alias', server_dns_aliases_operations, client_factory=get_sql_server_dns_aliases_operations) as c:
        c.command('show', 'get')
        c.command('list', 'list_by_server')
        c.command('create', 'create_or_update')
        c.command('delete', 'delete')
        c.custom_command('set', 'server_dns_alias_set')
